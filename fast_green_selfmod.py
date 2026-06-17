#!/usr/bin/env python3
"""Green self-modulation M-state decay — pure mmap GPIO, no HTTP.

Protocol (all via mmap, sub-μs timing):
  1. Dark baseline
  2. Green ON (write, 10ms) — creates M-states, protein bleaches
  3. Green OFF (100μs dark gap — minimal M-state decay)
  4. Green ON (probe) — capture transmission at 10+ kHz for 150ms
  5. Recovery

The green transmission starts HIGH (M-state absorbs less at 520nm, +300%
effect from May 22 data) and decays DOWN as M-states relax to ground state.
All at 10+ kHz with per-frame timestamps for μs-scale decay fitting.

Usage (on Pi):
  sudo python3 fast_green_selfmod.py br-green-1 /tmp
"""

from __future__ import annotations

import json, os, sys, time, statistics, math, mmap as _mmap, struct as _struct
from pathlib import Path
from typing import Any

from ad7606_fast import FastAD7606, to_signed_16

# ── mmap GPIO for laser control (no PWM, just on/off) ──
_GPFSEL0, _GPSET0, _GPCLR0 = 0x00, 0x1C, 0x28
_GREEN_PIN = 24

class GreenLaser:
    def __init__(self):
        self._fd = None; self._map = None
    def open(self):
        self._fd = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
        self._map = _mmap.mmap(self._fd, 4096, _mmap.MAP_SHARED,
                               _mmap.PROT_READ | _mmap.PROT_WRITE)
        reg = _GPFSEL0 + (_GREEN_PIN // 10) * 4
        shift = (_GREEN_PIN % 10) * 3
        val = _struct.unpack_from('<I', self._map, reg)[0] & ~(0b111 << shift)
        val |= (0b001 << shift)
        self._map[reg:reg+4] = _struct.pack('<I', val)
        self.off()
    def on(self):
        self._map[_GPSET0:_GPSET0+4] = _struct.pack('<I', 1 << _GREEN_PIN)
    def off(self):
        self._map[_GPCLR0:_GPCLR0+4] = _struct.pack('<I', 1 << _GREEN_PIN)
    def close(self):
        self.off()
        if self._map: self._map.close(); self._map = None
        if self._fd: os.close(self._fd); self._fd = None

# ── config ──
WRITE_MS = int(os.environ.get("GREEN_SELFMOD_WRITE_MS", "10"))
DARK_GAP_US = int(os.environ.get("GREEN_SELFMOD_DARK_GAP_US", "100"))
CAPTURE_MS = int(os.environ.get("GREEN_SELFMOD_CAPTURE_MS", "150"))
BASELINE_N = int(os.environ.get("GREEN_SELFMOD_BASELINE_FRAMES", "50"))
REPS = int(os.environ.get("GREEN_SELFMOD_REPS", "10"))
RECOVER_MS = int(os.environ.get("GREEN_SELFMOD_RECOVER_MS", "500"))

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "green"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    print("=" * 60)
    print("GREEN SELF-MODULATION M-STATE DECAY")
    print(f"Write: {WRITE_MS}ms  Dark gap: {DARK_GAP_US}μs  Capture: {CAPTURE_MS}ms × {REPS}")
    print("=" * 60)

    adc = FastAD7606(); adc.open()
    laser = GreenLaser(); laser.open()
    for _ in range(10): adc.read_frame()
    print("Ready.\n")

    all_reps = []
    t0 = time.perf_counter()
    for rep in range(REPS):
        # 1. Dark baseline
        laser.off(); time.sleep(0.005)
        bl_frames = []
        for _ in range(BASELINE_N):
            raw = adc.read_frame()
            bl_frames.append({f"ch{i+1}": to_signed_16(raw[i]) for i in range(8)})

        # 2. Green write
        laser.on()
        t_write = time.perf_counter()
        while (time.perf_counter() - t_write) * 1000 < WRITE_MS:
            pass
        laser.off()

        # 3. Dark gap (busy-wait for precise timing)
        t_gap = time.perf_counter()
        while (time.perf_counter() - t_gap) * 1_000_000 < DARK_GAP_US:
            pass

        # 4. Green probe capture
        laser.on()
        cap_start = time.perf_counter()
        cap_frames = []
        while (time.perf_counter() - cap_start) * 1000 < CAPTURE_MS:
            fs = time.perf_counter()
            raw = adc.read_frame()
            fe = time.perf_counter()
            cap_frames.append({
                "elapsed_us": round((fs - cap_start) * 1_000_000, 1),
                "read_us": round((fe - fs) * 1_000_000, 1),
                **{f"ch{i+1}": to_signed_16(raw[i]) for i in range(8)},
            })
        laser.off()
        actual_ms = (time.perf_counter() - cap_start) * 1000

        bl_vals = [f["ch2"] for f in bl_frames]
        cap_vals = [f["ch2"] for f in cap_frames]
        bl_m = statistics.fmean(bl_vals); bl_s = statistics.stdev(bl_vals) if len(bl_vals)>1 else 0
        rate = len(cap_frames)/(actual_ms/1000) if actual_ms>0 else 0

        all_reps.append({"rep": rep, "baseline_mean": round(bl_m,3), "baseline_std": round(bl_s,3),
                         "capture_n": len(cap_frames), "capture_ms": round(actual_ms,3),
                         "rate_hz": round(rate,1),
                         "bl_frames": bl_frames, "cap_frames": cap_frames})
        print(f"  rep {rep+1:2d}/{REPS}: {len(cap_frames)} frames @ {rate:.0f} Hz  dark={bl_m:.1f}±{bl_s:.1f}")
        if rep < REPS-1:
            time.sleep(RECOVER_MS/1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    rates = [r["rate_hz"] for r in all_reps]
    output = {"experiment": "green_selfmod_decay", "timestamp": ts, "sample_label": label,
              "config": {"write_ms": WRITE_MS, "dark_gap_us": DARK_GAP_US, "capture_ms": CAPTURE_MS,
                         "baseline_frames": BASELINE_N, "reps": REPS, "recover_ms": RECOVER_MS},
              "protocol": {"hypothesis": "Green self-modulation: write creates M-states (bleaches ground state), probe measures transmission recovery. M-state absorbs less at 520nm → transmission starts HIGH and decays DOWN."},
              "statistics": {"rep_count": REPS, "duration_s": round(t1-t0,3),
                             "avg_rate_hz": round(statistics.fmean(rates),1),
                             "total_frames": sum(r["capture_n"] for r in all_reps)},
              "reps": all_reps}
    out_path = out_dir / f"green_selfmod_decay_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Avg rate: {output['statistics']['avg_rate_hz']:.0f} Hz  Wrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
