#!/usr/bin/env python3
"""Blue-probe weight readout — green write (90° side), blue probe (through cuvette).

Blue at 450nm is near the M-state absorption peak (410nm). M-state absorbs MORE
blue than ground state, so blue transmission DECREASES after green write.
Signal should be 10-20× larger than 650nm red probe.

Protocol: green write → green off → blue probe (200ms capture)
M-state = early_blue - late_blue (within-capture differential)

Usage (bench service STOPPED):
  sudo python3 fast_blue_probe_weight.py br-blue /tmp
"""

from __future__ import annotations

import json, os, sys, time, statistics, math, mmap as _mmap, struct as _struct, random
from pathlib import Path
from typing import Any
from ad7606_fast import FastAD7606, to_signed_16

_GPFSEL0, _GPSET0, _GPCLR0 = 0x00, 0x1C, 0x28
_GREEN_PIN = 24
_BLUE_PIN = 14

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

WRITE_DURATIONS_MS = [0, 1, 2, 5, 10, 20, 50]
GAP_US = 100
CAPTURE_MS = 200
BL_N = 40
REPS_PER = 8
RECOVER_MS = 600
SKIP_FRAMES = 8

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "blue"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    n_trials = len(WRITE_DURATIONS_MS) * REPS_PER
    print("=" * 65)
    print("BLUE PROBE WEIGHT SWEEP")
    print(f"Green write (90° side) → Blue probe (through cuvette)")
    print(f"{len(WRITE_DURATIONS_MS)} durations × {REPS_PER} reps = {n_trials} trials")
    print("=" * 65)

    adc = FastAD7606(); adc.open()
    laser = DualLaser(); laser.open()
    for _ in range(20): adc.read_frame()
    laser.off(); time.sleep(0.05)

    rng = random.Random(12345)
    plan = [(d, r) for d in WRITE_DURATIONS_MS for r in range(REPS_PER)]
    rng.shuffle(plan)

    all_trials = []
    t0 = time.perf_counter()

    for idx, (write_ms, rep) in enumerate(plan):
        laser.off(); time.sleep(0.005)
        bl_vals = [to_signed_16(adc.read_frame()[1]) for _ in range(BL_N)]
        bl_mean = statistics.fmean(bl_vals)

        # Green write
        if write_ms > 0:
            laser.green_on()
            tw = time.perf_counter()
            while (time.perf_counter() - tw) * 1000 < write_ms: pass
            laser.green_off()

        # Gap
        tg = time.perf_counter()
        while (time.perf_counter() - tg) * 1_000_000 < GAP_US: pass

        # Blue probe capture
        laser.blue_on()
        cs = time.perf_counter()
        all_cap = []
        while (time.perf_counter() - cs) * 1000 < CAPTURE_MS:
            all_cap.append(to_signed_16(adc.read_frame()[1]))
        laser.blue_off()

        early_blue = statistics.fmean(all_cap[SKIP_FRAMES:SKIP_FRAMES+50]) if len(all_cap) > SKIP_FRAMES+50 else statistics.fmean(all_cap[SKIP_FRAMES:])
        late_blue = statistics.fmean(all_cap[-200:]) if len(all_cap) >= 200 else statistics.fmean(all_cap[-50:])
        mstate = early_blue - late_blue  # negative = M-state absorbs MORE blue

        all_trials.append({"write_ms": write_ms, "rep": rep, "bl_mean": round(bl_mean,2),
                          "early_blue": round(early_blue,2), "late_blue": round(late_blue,2),
                          "mstate": round(mstate,2), "cap_n": len(all_cap)})
        print(f"  [{idx+1:3d}/{n_trials}] w={write_ms:3d}ms  early={early_blue:.0f} late={late_blue:.0f} Δ={mstate:+.1f}")
        if idx < n_trials-1: time.sleep(RECOVER_MS/1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    by_dur = {}
    for t in all_trials: by_dur.setdefault(t["write_ms"], []).append(t["mstate"])

    print(f"\n{'='*65}")
    print(f"BLUE PROBE WEIGHT RESULTS")
    print(f"{'Write ms':>9s} {'n':>4s} {'M-state':>10s} {'std':>8s} {'SEM':>8s} {'SNR':>6s}")
    results = []
    for dur in sorted(by_dur):
        vals = by_dur[dur]; m = statistics.fmean(vals); s = statistics.stdev(vals) if len(vals)>1 else 0
        sem = s/math.sqrt(len(vals)); snr = abs(m)/sem if sem>0 else 0
        print(f"{dur:9d} {len(vals):4d} {m:10.1f} {s:8.1f} {sem:8.1f} {snr:6.1f}")
        results.append({"write_ms": dur, "n": len(vals), "mean": round(m,3), "std": round(s,3),
                        "sem": round(sem,3), "snr": round(snr,2)})

    xs = [r["write_ms"] for r in results]; ys = [r["mean"] for r in results]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den = sum((x-mx)**2 for x in xs)
    if den > 0:
        slope = num/den; r_val = num/math.sqrt(den*sum((y-my)**2 for y in ys))
    else: slope = r_val = 0

    ctrl = results[0] if results else {"mean": 0}
    mx_w = results[-1] if results else {"mean": 0}
    sig_range = abs(mx_w["mean"] - ctrl["mean"])
    noise = statistics.fmean([r["std"] for r in results])
    bits = math.log2(sig_range/noise) if noise>0 and sig_range>0 else 0

    print(f"\nDose-response: r={r_val:.4f}, slope={slope:.3f} ct/ms")
    print(f"Signal range: {sig_range:.1f} ct, noise: {noise:.1f} ct")
    print(f"Effective bits: {bits:.2f} ({2**bits:.0f} levels)")

    output = {"experiment": "blue_probe_weight", "timestamp": ts, "label": label,
              "config": {"write_durations_ms": WRITE_DURATIONS_MS, "reps_per": REPS_PER,
                         "gap_us": GAP_US, "capture_ms": CAPTURE_MS},
              "results": results,
              "summary": {"dose_r": round(r_val,4), "slope": round(slope,3),
                          "signal_range": round(sig_range,1), "noise": round(noise,1),
                          "effective_bits": round(bits,2)},
              "trials": all_trials, "stats": {"dur_s": round(t1-t0,1), "n": len(all_trials)}}
    out_path = out_dir / f"blue_probe_weight_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
