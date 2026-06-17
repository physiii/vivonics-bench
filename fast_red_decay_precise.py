#!/usr/bin/env python3
"""Precision M-state decay — mmap GPIO for both red probe + green write.

Protocol (all mmap, sub-μs timing):
  1. Dark baseline (both off)
  2. Green ON (write, 10ms)
  3. Green OFF, Red ON (100μs gap)
  4. Red probe capture at 10+ kHz for 200ms
  5. Recovery

Red is full-ON DC (stable, no PWM jitter). 3x red-pass filters installed.
Green bleed reduced. Red at ~85% ADC — slight nonlinearity but time-dependent
M-state signal should still be visible if present.

Usage (on Pi, bench service STOPPED):
  sudo python3 fast_red_decay_precise.py br-3xfilter /tmp
"""

from __future__ import annotations

import json, os, sys, time, statistics, math, mmap as _mmap, struct as _struct
from pathlib import Path
from typing import Any
from ad7606_fast import FastAD7606, to_signed_16

# ── mmap GPIO laser control ──
_GPFSEL0, _GPSET0, _GPCLR0 = 0x00, 0x1C, 0x28
_RED_PIN, _GREEN_PIN = 15, 24

class DualLaser:
    def __init__(self): self._fd = None; self._map = None
    def open(self):
        self._fd = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
        self._map = _mmap.mmap(self._fd, 4096, _mmap.MAP_SHARED,
                               _mmap.PROT_READ | _mmap.PROT_WRITE)
        for pin in (_RED_PIN, _GREEN_PIN):
            reg = _GPFSEL0 + (pin // 10) * 4
            shift = (pin % 10) * 3
            val = _struct.unpack_from('<I', self._map, reg)[0] & ~(0b111 << shift)
            val |= (0b001 << shift)
            self._map[reg:reg+4] = _struct.pack('<I', val)
        self.off()
    def _set(self, pin, on):
        if on: self._map[_GPSET0:_GPSET0+4] = _struct.pack('<I', 1 << pin)
        else:  self._map[_GPCLR0:_GPCLR0+4] = _struct.pack('<I', 1 << pin)
    def red_on(self): self._set(_RED_PIN, True)
    def red_off(self): self._set(_RED_PIN, False)
    def green_on(self): self._set(_GREEN_PIN, True)
    def green_off(self): self._set(_GREEN_PIN, False)
    def off(self): self._set(_RED_PIN, False); self._set(_GREEN_PIN, False)
    def close(self): self.off()
    def __del__(self):
        if self._map: self._map.close()
        if self._fd: os.close(self._fd)

# ── config ──
WRITE_MS = int(os.environ.get("DECAY_WRITE_MS", "10"))
GAP_US = int(os.environ.get("DECAY_GAP_US", "100"))
CAPTURE_MS = int(os.environ.get("DECAY_CAPTURE_MS", "200"))
BL_N = int(os.environ.get("DECAY_BL_FRAMES", "50"))
REPS = int(os.environ.get("DECAY_REPS", "10"))
RECOVER_MS = int(os.environ.get("DECAY_RECOVER_MS", "500"))

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "decay"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    print("=" * 60)
    print(f"PRECISION M-STATE DECAY — Red probe, 3x filter")
    print(f"Write: {WRITE_MS}ms  Gap: {GAP_US}μs  Capture: {CAPTURE_MS}ms × {REPS}")
    print("=" * 60)

    adc = FastAD7606(); adc.open()
    laser = DualLaser(); laser.open()
    for _ in range(10): adc.read_frame()
    laser.off(); time.sleep(0.05)
    print("Ready.\n")

    all_reps = []
    t0 = time.perf_counter()
    for rep in range(REPS):
        # 1. Dark baseline
        laser.off(); time.sleep(0.005)
        bl_frames = []
        for _ in range(BL_N):
            raw = adc.read_frame()
            bl_frames.append({f"ch{i+1}": to_signed_16(raw[i]) for i in range(8)})

        # 2. Green write
        laser.green_on()
        tw = time.perf_counter()
        while (time.perf_counter() - tw) * 1000 < WRITE_MS: pass
        laser.green_off()

        # 3. Gap (busy-wait)
        tg = time.perf_counter()
        while (time.perf_counter() - tg) * 1_000_000 < GAP_US: pass

        # 4. Red probe capture
        laser.red_on()
        cs = time.perf_counter()
        cap_frames = []
        while (time.perf_counter() - cs) * 1000 < CAPTURE_MS:
            fs = time.perf_counter()
            raw = adc.read_frame()
            fe = time.perf_counter()
            cap_frames.append({
                "elapsed_us": round((fs - cs) * 1_000_000, 1),
                "read_us": round((fe - fs) * 1_000_000, 1),
                **{f"ch{i+1}": to_signed_16(raw[i]) for i in range(8)},
            })
        laser.red_off()
        actual_ms = (time.perf_counter() - cs) * 1000

        bl_vals = [f["ch2"] for f in bl_frames]
        bl_m = statistics.fmean(bl_vals); bl_s = statistics.stdev(bl_vals) if len(bl_vals)>1 else 0
        rate = len(cap_frames)/(actual_ms/1000) if actual_ms>0 else 0

        all_reps.append({"rep": rep, "bl_mean": round(bl_m,3), "bl_std": round(bl_s,3),
                         "cap_n": len(cap_frames), "cap_ms": round(actual_ms,3),
                         "rate_hz": round(rate,1), "bl_frames": bl_frames, "cap_frames": cap_frames})
        print(f"  rep {rep+1:2d}/{REPS}: {len(cap_frames)} fr @ {rate:.0f} Hz  dark={bl_m:.1f}±{bl_s:.1f}")
        if rep < REPS-1: time.sleep(RECOVER_MS/1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    rates = [r["rate_hz"] for r in all_reps]
    output = {"experiment": "red_decay_precise", "timestamp": ts, "label": label,
              "config": {"write_ms": WRITE_MS, "gap_us": GAP_US, "capture_ms": CAPTURE_MS,
                         "bl_frames": BL_N, "reps": REPS, "recover_ms": RECOVER_MS},
              "stats": {"reps": REPS, "dur_s": round(t1-t0,3),
                        "avg_hz": round(statistics.fmean(rates),1),
                        "total_fr": sum(r["cap_n"] for r in all_reps)},
              "reps": all_reps}
    out_path = out_dir / f"red_decay_precise_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Avg: {output['stats']['avg_hz']:.0f} Hz  Wrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
