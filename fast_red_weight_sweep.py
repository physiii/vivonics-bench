#!/usr/bin/env python3
"""Maximum weight throughput benchmark — full write-duration sweep + recovery timing.

Measures:
  1. Weight resolution: M-state signal vs write duration (0-100ms, 12 levels)
  2. Weight persistence: how long the M-state lasts (recovery time)
  3. Max update rate: how many weight writes per second

Protocol per trial:
  1. Dark baseline
  2. Green ON for write_ms
  3. Green OFF, immediate red probe capture (200ms to catch full decay)
  4. Recovery wait
  
Shuffled trial order, 8 reps per duration for statistical power.

Usage (bench service STOPPED):
  sudo python3 fast_red_weight_sweep.py br-max-throughput /tmp
"""

from __future__ import annotations

import json, os, sys, time, statistics, math, mmap as _mmap, struct as _struct, random
from pathlib import Path
from typing import Any
from ad7606_fast import FastAD7606, to_signed_16

_GPFSEL0, _GPSET0, _GPCLR0 = 0x00, 0x1C, 0x28
_RED_PIN, _GREEN_PIN = 15, 24

class DualLaser:
    def __init__(self): self._fd = None; self._map = None
    def open(self):
        self._fd = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
        self._map = _mmap.mmap(self._fd, 4096, _mmap.MAP_SHARED, _mmap.PROT_READ | _mmap.PROT_WRITE)
        for pin in (_RED_PIN, _GREEN_PIN):
            reg = _GPFSEL0 + (pin // 10) * 4; shift = (pin % 10) * 3
            val = _struct.unpack_from('<I', self._map, reg)[0] & ~(0b111 << shift)
            val |= (0b001 << shift); self._map[reg:reg+4] = _struct.pack('<I', val)
        self.off()
    def _set(self, pin, on):
        if on: self._map[_GPSET0:_GPSET0+4] = _struct.pack('<I', 1 << pin)
        else:  self._map[_GPCLR0:_GPCLR0+4] = _struct.pack('<I', 1 << pin)
    def red_on(self): self._set(_RED_PIN, True)
    def red_off(self): self._set(_RED_PIN, False)
    def green_on(self): self._set(_GREEN_PIN, True)
    def green_off(self): self._set(_GREEN_PIN, False)
    def off(self): self.red_off(); self.green_off()
    def close(self): self.off(); self._map.close(); os.close(self._fd)

# ── Full sweep parameters ──
WRITE_DURATIONS_MS = [0, 10, 50, 100]  # focused: 4 levels for multi-bit demo
GAP_US = 100
CAPTURE_MS = 250
BL_N = 40
REPS_PER = 16  # 4 × 16 = 64 trials, targets ~2.4 bits
RECOVER_MS = 600
SKIP_FRAMES = 8  # skip first 8 frames (~640μs) to avoid red turn-on transient

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "max"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    n_trials = len(WRITE_DURATIONS_MS) * REPS_PER
    est_time_min = n_trials * (max(WRITE_DURATIONS_MS)/1000 + CAPTURE_MS/1000 + RECOVER_MS/1000) / 60
    
    print("=" * 65)
    print("MAX WEIGHT THROUGHPUT BENCHMARK")
    print(f"{len(WRITE_DURATIONS_MS)} durations × {REPS_PER} reps = {n_trials} trials")
    print(f"Est. duration: {est_time_min:.0f} min")
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
        # 1. Dark baseline
        laser.off(); time.sleep(0.005)
        bl_vals = []
        for _ in range(BL_N):
            raw = adc.read_frame()
            bl_vals.append(to_signed_16(raw[1]))

        # 2. Green write
        if write_ms > 0:
            laser.green_on()
            tw = time.perf_counter()
            while (time.perf_counter() - tw) * 1000 < write_ms: pass
            laser.green_off()

        # 3. Precise gap
        tg = time.perf_counter()
        while (time.perf_counter() - tg) * 1_000_000 < GAP_US: pass

        # 4. Red probe capture — long to see full decay
        laser.red_on()
        cs = time.perf_counter()
        cap_vals = []
        cap_times = []
        while (time.perf_counter() - cs) * 1000 < CAPTURE_MS:
            fs = time.perf_counter()
            raw = adc.read_frame()
            cap_vals.append(to_signed_16(raw[1]))
            cap_times.append((fs - cs) * 1_000_000)
        laser.red_off()
        ce = time.perf_counter()

        bl_mean = statistics.fmean(bl_vals)
        bl_std = statistics.stdev(bl_vals) if len(bl_vals) > 1 else 0
        
        # Skip transient frames, compute early (M-state) vs late (recovered) response
        if len(cap_vals) > SKIP_FRAMES + 50:
            # Early: frames SKIP_FRAMES to SKIP_FRAMES+10 (~1ms window)
            early_vals = cap_vals[SKIP_FRAMES:SKIP_FRAMES+15]
            # Late: last 100 frames (~10ms window)
            late_vals = cap_vals[-100:]
            # Mid: for decay time estimation
            mid_vals = cap_vals[SKIP_FRAMES:SKIP_FRAMES+200] if len(cap_vals) > SKIP_FRAMES+200 else cap_vals[SKIP_FRAMES:]
            
            early_red = statistics.fmean(early_vals)
            late_red = statistics.fmean(late_vals)
            red_baseline = late_red - bl_mean
            mstate_signal = early_red - late_red
            
            # Estimate decay half-life: find when signal reaches 50% of initial
            # Simple approach: time when cumulative exceeds half the total recovery
            total_recovery = late_red - early_red
            half_target = early_red + total_recovery * 0.5
            half_time_us = None
            for j, v in enumerate(mid_vals):
                if total_recovery > 0 and v >= half_target:
                    half_time_us = cap_times[SKIP_FRAMES + j]
                    break
                elif total_recovery < 0 and v <= half_target:
                    half_time_us = cap_times[SKIP_FRAMES + j]
                    break
        else:
            early_red = late_red = red_baseline = mstate_signal = 0
            half_time_us = None

        rate = len(cap_vals) / ((ce - cs)) if (ce - cs) > 0 else 0

        all_trials.append({
            "write_ms": write_ms, "rep": rep,
            "bl_mean": round(bl_mean, 2), "bl_std": round(bl_std, 2),
            "early_red": round(early_red, 2), "late_red": round(late_red, 2),
            "red_baseline": round(red_baseline, 2),
            "mstate_signal": round(mstate_signal, 2),
            "half_time_us": round(half_time_us, 1) if half_time_us else None,
            "cap_n": len(cap_vals), "rate_hz": round(rate, 1),
        })

        # Progress
        elapsed = time.perf_counter() - t0
        remaining = (elapsed / (idx + 1)) * (n_trials - idx - 1) if idx > 0 else 0
        print(f"  [{idx+1:3d}/{n_trials}] w={write_ms:3d}ms  "
              f"M-state={mstate_signal:+.1f} ct  t½={half_time_us/1000 if half_time_us else 0:.1f}ms  "
              f"rem={remaining/60:.0f}m")

        if idx < n_trials - 1:
            time.sleep(RECOVER_MS / 1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    # ── Analysis ──
    by_dur = {}
    for t in all_trials:
        by_dur.setdefault(t["write_ms"], []).append(t)

    print(f"\n{'='*80}")
    print(f"WEIGHT READOUT RESULTS — {REPS_PER} reps per level")
    print(f"{'Write':>6s} {'n':>4s} {'M-state':>10s} {'SEM':>8s} {'SNR':>6s} {'t½(ms)':>8s} {'Red Δ':>8s}")
    print(f"{'─'*6} {'─'*4} {'─'*10} {'─'*8} {'─'*6} {'─'*8} {'─'*8}")
    
    results = []
    for dur in sorted(by_dur):
        trials = by_dur[dur]
        sigs = [t["mstate_signal"] for t in trials]
        halves = [t["half_time_us"] for t in trials if t["half_time_us"]]
        reds = [t["red_baseline"] for t in trials]
        
        m = statistics.fmean(sigs); s = statistics.stdev(sigs) if len(sigs) > 1 else 0
        sem = s / math.sqrt(len(sigs)); snr = abs(m) / sem if sem > 0 else 0
        half_avg = statistics.fmean(halves) / 1000 if halves else 0
        red_avg = statistics.fmean(reds)
        
        print(f"{dur:6d} {len(trials):4d} {m:10.2f} {sem:8.2f} {snr:6.1f} {half_avg:8.1f} {red_avg:8.0f}")
        
        results.append({
            "write_ms": dur, "mstate_mean": round(m, 3), "mstate_sem": round(sem, 3),
            "mstate_std": round(s, 3), "snr": round(snr, 1), "n": len(trials),
            "half_time_ms": round(half_avg, 2) if halves else None,
            "red_baseline": round(red_avg, 1),
        })

    # Dose-response linearity
    xs = [r["write_ms"] for r in results]
    ys = [r["mstate_mean"] for r in results]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    den = sum((x-mx)**2 for x in xs)
    slope = num/den if den else 0; intercept = my - slope*mx
    r = num / math.sqrt(den * sum((y-my)**2 for y in ys)) if den else 0

    # Weight resolution: if slope is S ct/ms and noise is σ, then distinguishable levels = range / σ
    signal_range = abs(max(ys) - min(ys))
    avg_noise = statistics.fmean([r["mstate_std"] for r in results])
    distinguishable_levels = signal_range / avg_noise if avg_noise > 0 else 0

    # Max update rate: write_time + recovery_time
    max_recovery_ms = max([r.get("half_time_ms", 20) or 20 for r in results]) * 3  # 3× half-life for full recovery
    min_write_ms = 1  # minimum useful write
    max_update_hz = 1000 / (min_write_ms + max_recovery_ms)

    print(f"\n{'='*80}")
    print(f"PERFORMANCE SUMMARY")
    print(f"  Dose-response r:        {r:.4f}")
    print(f"  Slope:                  {slope:.3f} ct/ms")
    print(f"  Signal range:           {signal_range:.1f} counts")
    print(f"  Avg per-level noise:    {avg_noise:.1f} counts")
    print(f"  Distinguishable levels: {distinguishable_levels:.0f}")
    print(f"  Recovery time (3× t½):  {max_recovery_ms:.0f} ms")
    print(f"  Max weight update rate: {max_update_hz:.0f} Hz")
    print(f"  Readout resolution:     {abs(slope):.2f} ct/ms = {abs(slope)*1000:.0f} ct/sensitivity per second of write")

    output = {"experiment": "max_weight_throughput", "timestamp": ts, "label": label,
              "config": {"write_durations_ms": WRITE_DURATIONS_MS, "reps_per": REPS_PER,
                         "capture_ms": CAPTURE_MS, "gap_us": GAP_US, "skip_frames": SKIP_FRAMES},
              "results": results,
              "summary": {"dose_r": round(r,4), "slope_ct_per_ms": round(slope,3),
                          "signal_range_ct": round(signal_range,1),
                          "distinguishable_levels": round(distinguishable_levels, 0),
                          "max_update_hz": round(max_update_hz, 0),
                          "recovery_ms": round(max_recovery_ms, 0)},
              "trials": all_trials,
              "stats": {"duration_s": round(t1-t0, 1), "n_trials": len(all_trials),
                        "avg_rate_hz": round(statistics.fmean([t["rate_hz"] for t in all_trials]), 0)}}
    out_path = out_dir / f"max_weight_throughput_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
