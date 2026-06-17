#!/usr/bin/env python3
"""Optimized M-state decay — HTTP laser control (PWM) + mmap ADC (fast).

Uses bench service HTTP API for precise laser power levels (0-255 PWM),
and direct /dev/gpiomem mmap for 10+ kHz ADC sampling. This keeps the
photodiode in its linear range while capturing at maximum time resolution.

Usage (on the Pi, bench service must be running):
  sudo python3 fast_decay_http_laser.py br-linear-1 /tmp
  RED_LEVEL=96 GREEN_LEVEL=255 REPS=10 python3 fast_decay_http_laser.py br-linear-1 /tmp
"""

from __future__ import annotations

import json, os, sys, time, statistics, math
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from ad7606_fast import FastAD7606, to_signed_16


# ── configuration ─────────────────────────────────────────────────
BENCH_URL = os.environ.get("VIVONICS_BENCH_URL", "http://127.0.0.1:8090")
RED_LEVEL = int(os.environ.get("FAST_DECAY_RED_LEVEL", "128"))      # keep photodiode linear
GREEN_LEVEL = int(os.environ.get("FAST_DECAY_GREEN_LEVEL", "255"))
GREEN_WRITE_MS = int(os.environ.get("FAST_DECAY_GREEN_WRITE_MS", "10"))
CAPTURE_DURATION_MS = int(os.environ.get("FAST_DECAY_CAPTURE_DURATION_MS", "150"))
BASELINE_FRAMES = int(os.environ.get("FAST_DECAY_BASELINE_FRAMES", "50"))
REPS = int(os.environ.get("FAST_DECAY_REPS", "10"))
RECOVER_MS = int(os.environ.get("FAST_DECAY_RECOVER_MS", "500"))
SAMPLE_CH = int(os.environ.get("FAST_DECAY_SAMPLE_CH", "2"))
REF_CH = int(os.environ.get("FAST_DECAY_REF_CH", "1"))


def _http_post(path: str, body: dict) -> None:
    data = json.dumps(body).encode()
    req = Request(f"{BENCH_URL.rstrip('/')}/{path.lstrip('/')}", data=data,
                  headers={"Content-Type": "application/json"})
    urlopen(req, timeout=10).read()


def _set_light(red: int, green: int) -> None:
    _http_post("/light", {"red_level": red, "green_level": green, "infrared_level": 0, "blue_level": 0})


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "linear"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())

    red_level = int(os.environ.get("FAST_DECAY_RED_LEVEL", str(RED_LEVEL)))
    green_level = int(os.environ.get("FAST_DECAY_GREEN_LEVEL", str(GREEN_LEVEL)))
    green_write_ms = int(os.environ.get("FAST_DECAY_GREEN_WRITE_MS", str(GREEN_WRITE_MS)))
    capture_ms = int(os.environ.get("FAST_DECAY_CAPTURE_DURATION_MS", str(CAPTURE_DURATION_MS)))
    baseline_n = int(os.environ.get("FAST_DECAY_BASELINE_FRAMES", str(BASELINE_FRAMES)))
    reps = int(os.environ.get("FAST_DECAY_REPS", str(REPS)))
    recover_ms = int(os.environ.get("FAST_DECAY_RECOVER_MS", str(RECOVER_MS)))

    print("=" * 60)
    print("M-STATE DECAY — HTTP laser + mmap ADC")
    print(f"Red probe: level={red_level}  Green write: level={green_level} {green_write_ms}ms")
    print(f"Capture: {capture_ms}ms × {reps} reps")
    print(f"ADC: ch{REF_CH} (ref), ch{SAMPLE_CH} (sample)")
    print("=" * 60)

    # Init fast ADC
    print("\nInit mmap ADC...")
    adc = FastAD7606()
    adc.open()
    for _ in range(10):
        adc.read_frame()

    # Ensure lasers off via HTTP
    _set_light(0, 0)
    time.sleep(0.1)
    print("Ready.\n")

    all_reps = []
    total_start = time.perf_counter()

    for rep in range(reps):
        # ── 1. Dark baseline ──
        _set_light(0, 0)
        time.sleep(0.01)
        baseline_frames = []
        for _ in range(baseline_n):
            raw = adc.read_frame()
            baseline_frames.append({f"ch{i+1}": to_signed_16(raw[i]) for i in range(8)})

        # ── 2. Green write ──
        _set_light(0, green_level)
        time.sleep(green_write_ms / 1000.0)
        _set_light(0, 0)

        # ── 3. Red probe capture ──
        _set_light(red_level, 0)
        capture_start = time.perf_counter()
        capture_frames = []
        while (time.perf_counter() - capture_start) * 1000 < capture_ms:
            frame_start = time.perf_counter()
            raw = adc.read_frame()
            frame_end = time.perf_counter()
            elapsed_us = (frame_start - capture_start) * 1_000_000
            capture_frames.append({
                "elapsed_us": round(elapsed_us, 1),
                "read_us": round((frame_end - frame_start) * 1_000_000, 1),
                **{f"ch{i+1}": to_signed_16(raw[i]) for i in range(8)},
            })
        _set_light(0, 0)
        actual_capture_ms = (time.perf_counter() - capture_start) * 1000

        # Stats
        ch_keys = [f"ch{i+1}" for i in range(8)]
        sample_key = ch_keys[SAMPLE_CH - 1]
        baseline_vals = [f[sample_key] for f in baseline_frames]
        capture_vals = [f[sample_key] for f in capture_frames]
        bl_mean = statistics.fmean(baseline_vals) if baseline_vals else 0
        bl_std = statistics.stdev(baseline_vals) if len(baseline_vals) > 1 else 0
        rate = len(capture_frames) / (actual_capture_ms / 1000) if actual_capture_ms > 0 else 0

        all_reps.append({
            "rep": rep,
            "baseline_mean_sample": round(bl_mean, 3),
            "baseline_std_sample": round(bl_std, 3),
            "capture_frame_count": len(capture_frames),
            "actual_capture_ms": round(actual_capture_ms, 3),
            "capture_rate_hz": round(rate, 1),
            "sample_channel": sample_key,
            "ref_channel": ch_keys[REF_CH - 1],
            "baseline_frames": baseline_frames,
            "capture_frames": capture_frames,
        })
        print(f"  rep {rep+1:2d}/{reps}: {len(capture_frames)} frames @ {rate:.0f} Hz  baseline={bl_mean:.1f}±{bl_std:.1f}")
        if rep < reps - 1:
            time.sleep(recover_ms / 1000.0)

    total_end = time.perf_counter()
    _set_light(0, 0)
    adc.close()

    all_rates = [r["capture_rate_hz"] for r in all_reps]
    output = {
        "experiment": "fast_decay_http_laser",
        "timestamp": timestamp, "sample_label": label,
        "config": {
            "bench_url": BENCH_URL, "red_level": red_level, "green_level": green_level,
            "green_write_ms": green_write_ms, "capture_duration_ms": capture_ms,
            "baseline_frames": baseline_n, "reps": reps, "recover_ms": recover_ms,
            "sample_channel": SAMPLE_CH, "ref_channel": REF_CH,
        },
        "protocol": {
            "hypothesis": "At reduced red power (linear photodiode range), M-state decay may be visible as a small Δ in red transmission after green write.",
        },
        "statistics": {
            "rep_count": reps,
            "total_duration_s": round(total_end - total_start, 3),
            "avg_capture_rate_hz": round(statistics.fmean(all_rates), 1) if all_rates else 0,
            "total_capture_frames": sum(r["capture_frame_count"] for r in all_reps),
        },
        "reps": all_reps,
    }
    out_path = out_dir / f"fast_decay_http_{label}_{timestamp}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Avg rate: {output['statistics']['avg_capture_rate_hz']:.0f} Hz")
    print(f"  Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
