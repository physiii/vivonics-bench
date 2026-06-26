#!/usr/bin/env python3
"""Sub-ms weight precision — μs green pulses for partial M-state populations.

Green pulse durations below saturation threshold (~2ms) create partial M-state
populations, giving analog weight levels without needing analog PWM.

Pulse durations: 50μs, 100μs, 200μs, 500μs, 1ms, 2ms, 5ms, 10ms
Control: 0μs (no green)
Red probe: 200ms continuous capture, within-capture differential

Usage (bench service STOPPED):
  sudo python3 fast_red_weight_us.py br-us-pulses /tmp
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

# Sub-ms pulse durations in microseconds
PULSE_DURATIONS_US = [0, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
GAP_US = 100
CAPTURE_MS = 200
BL_N = 40
REPS_PER = 12
RECOVER_MS = 600
SKIP_FRAMES = 8

def busy_wait_us(us):
    """Busy-wait for microseconds."""
    end = time.perf_counter() + us / 1_000_000
    while time.perf_counter() < end: pass

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "us"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    n_trials = len(PULSE_DURATIONS_US) * REPS_PER
    est_min = n_trials * (max(PULSE_DURATIONS_US)/1e6 + CAPTURE_MS/1000 + RECOVER_MS/1000) / 60
    print("=" * 65)
    print(f"SUB-ms WEIGHT SWEEP — {len(PULSE_DURATIONS_US)} durations × {REPS_PER} reps")
    print(f"Pulses: {[f'{p}μs' if p<1000 else f'{p/1000}ms' for p in PULSE_DURATIONS_US]}")
    print(f"Est: {est_min:.0f} min")
    print("=" * 65)

    adc = FastAD7606(); adc.open()
    laser = DualLaser(); laser.open()
    for _ in range(20): adc.read_frame()
    laser.off(); time.sleep(0.05)

    rng = random.Random(12345)
    plan = [(d, r) for d in PULSE_DURATIONS_US for r in range(REPS_PER)]
    rng.shuffle(plan)

    all_trials = []
    t0 = time.perf_counter()

    for idx, (pulse_us, rep) in enumerate(plan):
        laser.off(); time.sleep(0.005)
        bl_vals = [to_signed_16(adc.read_frame()[1]) for _ in range(BL_N)]
        bl_mean = statistics.fmean(bl_vals)

        # Green pulse (sub-ms via busy-wait)
        if pulse_us > 0:
            laser.green_on()
            busy_wait_us(pulse_us)
            laser.green_off()

        # Gap
        busy_wait_us(GAP_US)

        # Red probe capture
        laser.red_on()
        cs = time.perf_counter()
        all_cap = []
        while (time.perf_counter() - cs) * 1000 < CAPTURE_MS:
            all_cap.append(to_signed_16(adc.read_frame()[1]))
        laser.off()

        early_red = statistics.fmean(all_cap[SKIP_FRAMES:SKIP_FRAMES+50]) if len(all_cap) > SKIP_FRAMES+50 else statistics.fmean(all_cap[SKIP_FRAMES:])
        late_red = statistics.fmean(all_cap[-200:]) if len(all_cap) >= 200 else statistics.fmean(all_cap[-50:])
        mstate = early_red - late_red

        all_trials.append({"pulse_us": pulse_us, "rep": rep, "bl_mean": round(bl_mean,2),
                          "early_red": round(early_red,2), "late_red": round(late_red,2),
                          "mstate": round(mstate,2), "cap_n": len(all_cap)})
        
        label_str = f"{pulse_us}μs" if pulse_us < 1000 else f"{pulse_us/1000:.0f}ms"
        print(f"  [{idx+1:3d}/{n_trials}] pulse={label_str:>6s}  early={early_red:.0f} late={late_red:.0f} Δ={mstate:+.1f}")
        if idx < n_trials-1: time.sleep(RECOVER_MS/1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    # Analysis
    by_dur = {}
    for t in all_trials: by_dur.setdefault(t["pulse_us"], []).append(t["mstate"])

    print(f"\n{'='*65}")
    print(f"SUB-ms WEIGHT RESULTS")
    print(f"{'Pulse':>8s} {'n':>4s} {'M-state':>10s} {'std':>8s} {'SEM':>8s} {'SNR':>6s}")
    results = []
    for dur in sorted(by_dur):
        vals = by_dur[dur]; m = statistics.fmean(vals); s = statistics.stdev(vals) if len(vals)>1 else 0
        sem = s/math.sqrt(len(vals)); snr = abs(m)/sem if sem>0 else 0
        label_str = f"{dur}μs" if dur < 1000 else f"{dur/1000:.0f}ms"
        print(f"{label_str:>8s} {len(vals):4d} {m:10.1f} {s:8.1f} {sem:8.1f} {snr:6.1f}")
        results.append({"pulse_us": dur, "n": len(vals), "mean": round(m,3), "std": round(s,3),
                        "sem": round(sem,3), "snr": round(snr,2)})

    xs = [r["pulse_us"] for r in results]; ys = [r["mean"] for r in results]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den = sum((x-mx)**2 for x in xs)
    if den > 0:
        slope = num/den; r_val = num/math.sqrt(den*sum((y-my)**2 for y in ys))
    else: slope = r_val = 0

    ctrl = results[0]; mx_w = results[-1]
    sig_range = abs(mx_w["mean"] - ctrl["mean"])
    noise = statistics.fmean([r["std"] for r in results])
    bits = math.log2(sig_range/noise) if noise>0 and sig_range>0 else 0

    # Bit precision vs averaging
    print(f"\nDose-response: r={r_val:.4f}, slope={slope:.6f} ct/μs")
    print(f"Signal range: {sig_range:.1f} ct, noise: {noise:.1f} ct")
    print(f"\nBit precision vs averaging:")
    for avg_n in [1, 4, 12, 24, 48, 96, 192]:
        noise_n = noise / math.sqrt(avg_n)
        b = math.log2(sig_range/noise_n) if noise_n>0 and sig_range>0 else 0
        print(f"  {avg_n:4d} reps → {b:.2f} bits ({2**b:.0f} levels)")
    print(f"\n  At 12 reps (current): {bits:.2f} bits ({2**bits:.0f} levels)")

    output = {"experiment": "sub_ms_weight", "timestamp": ts, "label": label,
              "config": {"pulse_durations_us": PULSE_DURATIONS_US, "reps_per": REPS_PER,
                         "gap_us": GAP_US, "capture_ms": CAPTURE_MS},
              "results": results,
              "summary": {"dose_r": round(r_val,4), "slope_ct_per_us": round(slope,6),
                          "signal_range": round(sig_range,1), "noise": round(noise,1),
                          "effective_bits_12rep": round(bits,2)},
              "trials": all_trials, "stats": {"dur_s": round(t1-t0,1), "n": len(all_trials)}}
    out_path = out_dir / f"sub_ms_weight_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
