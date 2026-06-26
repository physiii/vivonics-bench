#!/usr/bin/env python3
"""Blue-probe M-state decay with optimized frame selection.

Long capture (500ms) to see: blue turn-on transient → steady state → M-state decay.
Skips transient, uses all remaining frames for maximum averaging precision.

Usage (bench service STOPPED):
  sudo python3 fast_blue_decay.py br-blue-precise /tmp
"""

from __future__ import annotations

import json, os, sys, time, statistics, math, mmap as _mmap, struct as _struct
from pathlib import Path
from typing import Any
from ad7606_fast import FastAD7606, to_signed_16

_GPFSEL0, _GPSET0, _GPCLR0 = 0x00, 0x1C, 0x28
_GREEN_PIN, _BLUE_PIN = 24, 14

class DualLaser:
    def __init__(self): self._fd = None; self._map = None
    def open(self):
        self._fd = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
        self._map = _mmap.mmap(self._fd, 4096, _mmap.MAP_SHARED, _mmap.PROT_READ | _mmap.PROT_WRITE)
        for pin in (_GREEN_PIN, _BLUE_PIN):
            reg = _GPFSEL0 + (pin // 10) * 4; shift = (pin % 10) * 3
            val = _struct.unpack_from('<I', self._map, reg)[0] & ~(0b111 << shift)
            val |= (0b001 << shift); self._map[reg:reg+4] = _struct.pack('<I', val)
        self.off()
    def _set(self, pin, on):
        if on: self._map[_GPSET0:_GPSET0+4] = _struct.pack('<I', 1 << pin)
        else:  self._map[_GPCLR0:_GPCLR0+4] = _struct.pack('<I', 1 << pin)
    def green_on(self): self._set(_GREEN_PIN, True)
    def green_off(self): self._set(_GREEN_PIN, False)
    def blue_on(self): self._set(_BLUE_PIN, True)
    def blue_off(self): self._set(_BLUE_PIN, False)
    def off(self): self.green_off(); self.blue_off()
    def close(self): self.off(); self._map.close(); os.close(self._fd)

WRITE_MS = 10
GAP_US = 100
CAPTURE_MS = 500  # long capture to see full transient + decay
BL_N = 40
REPS = 10
RECOVER_MS = 800

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "blue"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    print("=" * 65)
    print(f"BLUE PROBE DECAY — {CAPTURE_MS}ms capture, {REPS} reps")
    print(f"Green write {WRITE_MS}ms → Blue probe")
    print("=" * 65)

    adc = FastAD7606(); adc.open()
    laser = DualLaser(); laser.open()
    for _ in range(20): adc.read_frame()
    laser.off(); time.sleep(0.05)
    print("Ready.\n")

    all_reps = []
    t0 = time.perf_counter()
    for rep in range(REPS):
        laser.off(); time.sleep(0.005)
        bl_vals = [to_signed_16(adc.read_frame()[1]) for _ in range(BL_N)]
        bl_mean = statistics.fmean(bl_vals)

        # Green write
        laser.green_on()
        tw = time.perf_counter()
        while (time.perf_counter() - tw) * 1000 < WRITE_MS: pass
        laser.green_off()

        # Gap
        tg = time.perf_counter()
        while (time.perf_counter() - tg) * 1_000_000 < GAP_US: pass

        # Blue probe — long capture
        laser.blue_on()
        cs = time.perf_counter()
        all_cap = []
        all_times = []
        while (time.perf_counter() - cs) * 1000 < CAPTURE_MS:
            fs = time.perf_counter()
            raw = adc.read_frame()
            all_cap.append(to_signed_16(raw[1]))
            all_times.append((fs - cs) * 1_000_000)
        laser.blue_off()
        actual_ms = (time.perf_counter() - cs) * 1000

        all_reps.append({"rep": rep, "bl_mean": round(bl_mean,2),
                        "cap_vals": all_cap, "cap_times_us": all_times,
                        "cap_n": len(all_cap), "cap_ms": round(actual_ms,3)})
        
        rate = len(all_cap)/(actual_ms/1000) if actual_ms>0 else 0
        print(f"  rep {rep+1:2d}: {len(all_cap)} fr @ {rate:.0f} Hz  dark={bl_mean:.1f}")

        if rep < REPS-1: time.sleep(RECOVER_MS/1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    # ── Time-aligned analysis ──
    # For each rep, compute blue baseline from last 200ms
    # Then compute M-state signal at various skip amounts
    
    print(f"\n{'='*65}")
    print(f"M-STATE SIGNAL vs TRANSIENT SKIP")
    print(f"{'Skip ms':>8s} {'M-state':>10s} {'SEM':>8s} {'SNR':>6s}")
    
    for skip_ms in [0, 5, 10, 20, 50, 100, 200]:
        skip_frames = int(skip_ms * 10)  # ~10 kHz → ~10 frames/ms
        mstate_vals = []
        for rd in all_reps:
            vals = rd["cap_vals"]
            if len(vals) < skip_frames + 100:
                continue
            early_end = skip_frames + 100 if skip_frames + 100 < len(vals) else len(vals)
            early = statistics.fmean(vals[skip_frames:early_end])
            late = statistics.fmean(vals[-500:]) if len(vals) >= 500 else statistics.fmean(vals[-100:])
            mstate_vals.append(early - late)
        
        if mstate_vals:
            m = statistics.fmean(mstate_vals); s = statistics.stdev(mstate_vals)
            sem = s/math.sqrt(len(mstate_vals)); snr = abs(m)/sem if sem>0 else 0
            marker = " ***" if snr>5 else (" **" if snr>3 else (" *" if snr>2 else ""))
            print(f"{skip_ms:8d} {m:10.1f} {sem:8.1f} {snr:6.1f}{marker}")

    output = {"experiment": "blue_probe_decay", "timestamp": ts, "label": label,
              "config": {"write_ms": WRITE_MS, "gap_us": GAP_US, "capture_ms": CAPTURE_MS, "reps": REPS},
              "reps": all_reps, "stats": {"dur_s": round(t1-t0,1)}}
    out_path = out_dir / f"blue_decay_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
