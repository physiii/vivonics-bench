#!/usr/bin/env python3
"""Red weight bit precision — fast mmap GPIO, no HTTP. THE way to measure.

Per trial: green write (0-100ms) → early red read → decay wait → late red read.
M-state signal = early_red - late_red (differential, cancels baseline drift).
Reports bit precision at 1/2/4/8/16/32/64 rep averaging.

Usage (on Pi, bench service STOPPED):
  sudo python3 fast_red_weight_precision.py br-weight /tmp
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

# ── config ──
WRITE_DURATIONS_MS = [0, 2, 5, 10, 20, 50, 100]
GAP_US = 100
DECAY_WAIT_MS = 200
CAPTURE_MS = 200  # long capture for within-trial early-vs-late comparison
BL_N = 40
REPS_PER = 8  # 7 durations × 8 = 56 trials
RECOVER_MS = 600
SKIP_FRAMES = 8

def read_probe_frames(adc, laser, pin_func, duration_ms):
    """Capture ADC frames for duration_ms with laser on via pin_func."""
    pin_func()
    cs = time.perf_counter()
    frames = []
    while (time.perf_counter() - cs) * 1000 < duration_ms:
        raw = adc.read_frame()
        frames.append(to_signed_16(raw[1]))  # ch2
    laser.off()
    return frames

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "weight"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    n_trials = len(WRITE_DURATIONS_MS) * REPS_PER
    print("=" * 65)
    print("RED WEIGHT BIT PRECISION — fast mmap")
    print(f"{len(WRITE_DURATIONS_MS)} durations × {REPS_PER} reps = {n_trials} trials")
    print("=" * 65)

    adc = FastAD7606(); adc.open()
    laser = DualLaser(); laser.open()
    for _ in range(20): adc.read_frame()
    laser.off(); time.sleep(0.05)

    rng = random.Random(42)
    plan = [(d, r) for d in WRITE_DURATIONS_MS for r in range(REPS_PER)]
    rng.shuffle(plan)

    all_trials = []
    t0 = time.perf_counter()

    for idx, (write_ms, rep) in enumerate(plan):
        laser.off(); time.sleep(0.005)

        # Dark baseline
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

        # Single continuous red probe capture — compares early vs late WITHIN capture
        laser.red_on()
        cs = time.perf_counter()
        all_cap = []
        while (time.perf_counter() - cs) * 1000 < CAPTURE_MS:
            raw = adc.read_frame()
            all_cap.append(to_signed_16(raw[1]))
        laser.off()

        # Early = frames SKIP_FRAMES to SKIP_FRAMES+50 (first ~5ms after transient)
        # Late = last 200 frames (~20ms at end, M-state fully decayed)
        early_red = statistics.fmean(all_cap[SKIP_FRAMES:SKIP_FRAMES+50]) if len(all_cap) > SKIP_FRAMES+50 else statistics.fmean(all_cap[SKIP_FRAMES:])
        late_red = statistics.fmean(all_cap[-200:]) if len(all_cap) >= 200 else statistics.fmean(all_cap[-50:])
        mstate = early_red - late_red

        all_trials.append({
            "write_ms": write_ms, "rep": rep,
            "bl_mean": round(bl_mean, 2),
            "early_red": round(early_red, 2), "late_red": round(late_red, 2),
            "mstate_signal": round(mstate, 2),
            "cap_n": len(all_cap),
        })

        print(f"  [{idx+1:3d}/{n_trials}] w={write_ms:3d}ms  "
              f"early={early_red:.0f}  late={late_red:.0f}  M-state={mstate:+.1f}")

        if idx < n_trials - 1:
            time.sleep(RECOVER_MS / 1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    # ── Analysis ──
    by_dur = {}
    for t in all_trials:
        by_dur.setdefault(t["write_ms"], []).append(t["mstate_signal"])

    print(f"\n{'='*65}")
    print(f"BIT PRECISION RESULTS")
    print(f"{'Write':>6s} {'n':>4s} {'M-state':>10s} {'std':>8s} {'SEM':>8s} {'SNR':>6s}")

    results = []
    for dur in sorted(by_dur):
        vals = by_dur[dur]
        m = statistics.fmean(vals); s = statistics.stdev(vals) if len(vals) > 1 else 0
        sem = s / math.sqrt(len(vals)); snr = abs(m) / sem if sem > 0 else 0
        print(f"{dur:6d} {len(vals):4d} {m:10.1f} {s:8.1f} {sem:8.1f} {snr:6.1f}")
        results.append({"write_ms": dur, "n": len(vals), "mean": round(m,3),
                        "std": round(s,3), "sem": round(sem,3), "snr": round(snr,2)})

    # Bit precision
    control = next((r for r in results if r["write_ms"] == 0), None)
    max_write = next((r for r in results if r["write_ms"] == max(WRITE_DURATIONS_MS)), None)
    signal_range = abs(max_write["mean"] - control["mean"]) if control and max_write else 0
    per_trial_noise = statistics.fmean([r["std"] for r in results])

    bit_precisions = {}
    for avg_n in [1, 2, 4, 8, 16, 32, 64, 128]:
        noise_at_n = per_trial_noise / math.sqrt(avg_n)
        bits = math.log2(signal_range / noise_at_n) if noise_at_n > 0 and signal_range > 0 else 0
        levels = 2 ** bits
        bit_precisions[f"avg_{avg_n}"] = {
            "reps": avg_n, "effective_noise": round(noise_at_n, 3),
            "effective_bits": round(bits, 2),
            "distinguishable_levels": round(levels, 0),
        }

    # Dose-response
    xs = [r["write_ms"] for r in results]; ys = [r["mean"] for r in results]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den = sum((x-mx)**2 for x in xs)
    slope = num/den if den else 0; intercept = my - slope*mx
    r_val = num / math.sqrt(den * sum((y-my)**2 for y in ys)) if den else 0

    print(f"\nDose-response: r={r_val:.4f}, slope={slope:.3f} ct/ms")
    print(f"Signal range: {signal_range:.1f} ct, noise: {per_trial_noise:.1f} ct\n")
    print("Bit precision vs averaging:")
    for key in sorted(bit_precisions.keys(), key=lambda k: bit_precisions[k]["reps"]):
        bp = bit_precisions[key]
        print(f"  {bp['reps']:4d} reps → {bp['effective_bits']:.2f} bits ({bp['distinguishable_levels']:.0f} levels)")

    output = {"experiment": "red_weight_bit_precision_mmap", "timestamp": ts, "label": label,
              "config": {"write_durations_ms": WRITE_DURATIONS_MS, "reps_per": REPS_PER,
                         "gap_us": GAP_US, "decay_wait_ms": DECAY_WAIT_MS, "capture_ms": CAPTURE_MS},
              "results": results,
              "summary": {"dose_r": round(r_val,4), "slope_ct_per_ms": round(slope,3),
                          "signal_range_ct": round(signal_range,1),
                          "per_trial_noise_ct": round(per_trial_noise,1)},
              "bit_precision": bit_precisions,
              "trials": all_trials,
              "stats": {"duration_s": round(t1-t0,1), "n_trials": len(all_trials)}}
    out_path = out_dir / f"red_weight_precision_mmap_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
