#!/usr/bin/env python3
"""Multi-bit weight via green pulse train — counts pulses instead of intensity.

Since laser modules are binary (on/off only, no analog PWM), weight levels
are achieved by varying the NUMBER of green write pulses. Each pulse creates
additional M-states, building up the weight value.

Protocol:
  1. Dark baseline
  2. N green pulses (each: ON 5ms, OFF 5ms) — N = weight value
  3. Single continuous red probe capture (200ms)
  4. M-state signal = early_red - late_red (within-capture differential)

Tests N = 0, 1, 2, 4, 8, 16 pulses to see if M-state signal scales with N.

Usage (bench service STOPPED):
  sudo python3 fast_red_weight_pulses.py br-pulses /tmp
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

PULSE_COUNTS = [0, 1, 2, 4, 8, 16]
PULSE_ON_MS = 5
PULSE_OFF_MS = 5
GAP_US = 100
CAPTURE_MS = 200
BL_N = 40
REPS_PER = 12
RECOVER_MS = 800
SKIP_FRAMES = 8

def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "pulses"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    n_trials = len(PULSE_COUNTS) * REPS_PER
    print("=" * 65)
    print(f"RED WEIGHT — Pulse count sweep ({PULSE_ON_MS}ms on, {PULSE_OFF_MS}ms off)")
    print(f"{len(PULSE_COUNTS)} levels × {REPS_PER} reps = {n_trials} trials")
    print("=" * 65)

    adc = FastAD7606(); adc.open()
    laser = DualLaser(); laser.open()
    for _ in range(20): adc.read_frame()
    laser.off(); time.sleep(0.05)

    rng = random.Random(12345)
    plan = [(n, r) for n in PULSE_COUNTS for r in range(REPS_PER)]
    rng.shuffle(plan)

    all_trials = []
    t0 = time.perf_counter()

    for idx, (npulses, rep) in enumerate(plan):
        laser.off(); time.sleep(0.005)
        bl_vals = [to_signed_16(adc.read_frame()[1]) for _ in range(BL_N)]
        bl_mean = statistics.fmean(bl_vals)

        # Green pulse train
        for _ in range(npulses):
            laser.green_on()
            tw = time.perf_counter()
            while (time.perf_counter() - tw) * 1000 < PULSE_ON_MS: pass
            laser.green_off()
            tw2 = time.perf_counter()
            while (time.perf_counter() - tw2) * 1000 < PULSE_OFF_MS: pass

        # Gap
        tg = time.perf_counter()
        while (time.perf_counter() - tg) * 1_000_000 < GAP_US: pass

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

        all_trials.append({"npulses": npulses, "rep": rep, "bl_mean": round(bl_mean,2),
                          "early_red": round(early_red,2), "late_red": round(late_red,2),
                          "mstate": round(mstate,2), "cap_n": len(all_cap)})
        print(f"  [{idx+1:3d}/{n_trials}] N={npulses:2d}  early={early_red:.0f} late={late_red:.0f} Δ={mstate:+.1f}")
        if idx < n_trials-1: time.sleep(RECOVER_MS/1000.0)

    t1 = time.perf_counter()
    laser.off(); laser.close(); adc.close()

    by_n = {}
    for t in all_trials: by_n.setdefault(t["npulses"], []).append(t["mstate"])

    print(f"\n{'='*65}")
    print(f"PULSE COUNT WEIGHT RESULTS")
    print(f"{'Pulses':>7s} {'n':>4s} {'M-state':>10s} {'std':>8s} {'SEM':>8s} {'SNR':>6s}")
    results = []
    for n in sorted(by_n):
        vals = by_n[n]; m = statistics.fmean(vals); s = statistics.stdev(vals) if len(vals)>1 else 0
        sem = s/math.sqrt(len(vals)); snr = abs(m)/sem if sem>0 else 0
        print(f"{n:7d} {len(vals):4d} {m:10.1f} {s:8.1f} {sem:8.1f} {snr:6.1f}")
        results.append({"npulses": n, "n": len(vals), "mean": round(m,3), "std": round(s,3),
                        "sem": round(sem,3), "snr": round(snr,2)})

    xs = [r["npulses"] for r in results]; ys = [r["mean"] for r in results]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den = sum((x-mx)**2 for x in xs)
    slope = num/den if den else 0; r_val = num/math.sqrt(den*sum((y-my)**2 for y in ys)) if den else 0
    sig_range = abs(results[-1]["mean"] - results[0]["mean"])
    noise = statistics.fmean([r["std"] for r in results])
    bits = math.log2(sig_range/noise) if noise>0 and sig_range>0 else 0

    print(f"\nDose-response: r={r_val:.4f}, slope={slope:.3f} ct/pulse")
    print(f"Signal range: {sig_range:.1f} ct, noise: {noise:.1f} ct")
    print(f"Effective bits: {bits:.2f} ({2**bits:.0f} levels)")

    output = {"experiment": "red_weight_pulses", "timestamp": ts, "label": label,
              "config": {"pulse_counts": PULSE_COUNTS, "pulse_on_ms": PULSE_ON_MS,
                         "pulse_off_ms": PULSE_OFF_MS, "reps_per": REPS_PER},
              "results": results,
              "summary": {"dose_r": round(r_val,4), "slope": round(slope,3),
                          "signal_range": round(sig_range,1), "noise": round(noise,1),
                          "effective_bits": round(bits,2)},
              "trials": all_trials, "stats": {"dur_s": round(t1-t0,1), "n": len(all_trials)}}
    out_path = out_dir / f"red_weight_pulses_{label}_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
