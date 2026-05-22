"""bR analog multiplication demo via direct Picamera2 capture.

Stops the RTSP stream, takes over the camera, runs multiple write/read
cycles, and measures the red transmission change to encode A × B.

Usage:
    python3 multiply_demo.py --a 5 --b 5
    python3 multiply_demo.py --sweep     # run a dose-response sweep
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import numpy as np

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

RED_PIN = 23
GREEN_PIN = 24
ROI_SIZE = 512
FRAME_W = 1920
FRAME_H = 1080


def setup_gpio() -> None:
    if GPIO is None:
        raise RuntimeError("RPi.GPIO required")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(GREEN_PIN, GPIO.OUT, initial=GPIO.LOW)


def red_on() -> None:
    GPIO.output(RED_PIN, GPIO.HIGH)


def red_off() -> None:
    GPIO.output(RED_PIN, GPIO.LOW)


def green_on() -> None:
    GPIO.output(GREEN_PIN, GPIO.HIGH)


def green_off() -> None:
    GPIO.output(GREEN_PIN, GPIO.LOW)


def all_off() -> None:
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)


def extract_roi(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    cy, cx = h // 2, w // 2
    half = ROI_SIZE // 2
    return frame[cy - half : cy + half, cx - half : cx + half]


def build_mask(red_roi: np.ndarray, lo: float = 30, hi: float = 220) -> np.ndarray:
    return (red_roi > lo) & (red_roi < hi)


def masked_mean(red_roi: np.ndarray, mask: np.ndarray) -> float:
    if mask.sum() < 10:
        return float(np.mean(red_roi))
    return float(np.mean(red_roi[mask]))


def run_single_cycle(
    cam,
    mask: np.ndarray,
    green_duration_s: float,
    read_settle_s: float = 0.3,
    n_baseline: int = 10,
    n_post: int = 10,
) -> dict:
    """One write/read cycle: baseline → green → read."""
    red_channel = lambda f: extract_roi(f)[:, :, 0].astype(np.float64)

    # Baseline: capture N frames under red only
    red_on()
    green_off()
    time.sleep(read_settle_s)
    baselines = []
    for _ in range(n_baseline):
        frame = cam.capture_array("main")
        baselines.append(masked_mean(red_channel(frame), mask))

    baseline = float(np.median(baselines))
    baseline_std = float(np.std(baselines))

    # Green write
    green_on()
    time.sleep(green_duration_s)
    green_off()

    # Red read: capture N frames
    time.sleep(0.05)
    posts = []
    times_ms = []
    t0 = time.monotonic()
    for _ in range(n_post):
        frame = cam.capture_array("main")
        elapsed_ms = (time.monotonic() - t0) * 1000
        posts.append(masked_mean(red_channel(frame), mask))
        times_ms.append(elapsed_ms)

    post = float(np.median(posts))
    peak = float(np.max(posts))
    delta_pct = 100.0 * (post - baseline) / baseline if baseline > 0 else 0.0
    peak_delta_pct = 100.0 * (peak - baseline) / baseline if baseline > 0 else 0.0

    return {
        "baseline": round(baseline, 3),
        "baseline_std": round(baseline_std, 4),
        "post_median": round(post, 3),
        "post_peak": round(peak, 3),
        "delta_pct": round(delta_pct, 4),
        "peak_delta_pct": round(peak_delta_pct, 4),
        "n_baseline": n_baseline,
        "n_post": n_post,
        "post_values": [round(v, 3) for v in posts],
        "post_times_ms": [round(t, 1) for t in times_ms],
    }


def run_multiply(
    a: float,
    b: float,
    repetitions: int = 10,
    recovery_s: float = 10.0,
    shutter_us: int = 5000,
    gain: float = 1.5,
) -> dict:
    import subprocess

    # Stop RTSP service
    subprocess.run(
        ["systemctl", "--user", "stop", "c1-camera-rtsp"],
        capture_output=True, timeout=10,
    )
    time.sleep(1)

    from picamera2 import Picamera2

    cam = Picamera2()
    config = cam.create_still_configuration(
        main={"size": (FRAME_W, FRAME_H), "format": "RGB888"},
        controls={
            "ExposureTime": shutter_us,
            "AnalogueGain": gain,
            "ColourGains": (1.5, 1.0),
            "AeEnable": False,
            "AwbEnable": False,
            "NoiseReductionMode": 0,
        },
    )
    cam.configure(config)
    cam.start()
    time.sleep(2)

    setup_gpio()
    green_duration_s = max(0.05, b * 0.2)

    try:
        # Calibrate mask
        red_on()
        green_off()
        time.sleep(1)
        cal_frame = cam.capture_array("main")
        cal_roi = extract_roi(cal_frame)[:, :, 0].astype(np.float64)
        mask = build_mask(cal_roi, lo=30, hi=220)
        mask_count = int(mask.sum())
        mask_mean = float(np.mean(cal_roi[mask])) if mask_count > 10 else 0.0
        print(f"Mask: {mask_count} pixels, mean={mask_mean:.1f}", file=sys.stderr)

        # Run cycles
        deltas = []
        peak_deltas = []
        all_cycles = []

        for rep in range(repetitions):
            # Recovery
            red_on()
            green_off()
            time.sleep(recovery_s if rep == 0 else recovery_s / 2)

            cycle = run_single_cycle(
                cam, mask,
                green_duration_s=green_duration_s,
                read_settle_s=0.5,
                n_baseline=15,
                n_post=15,
            )
            cycle["rep"] = rep
            deltas.append(cycle["delta_pct"])
            peak_deltas.append(cycle["peak_delta_pct"])
            all_cycles.append(cycle)
            print(
                f"  Rep {rep+1}/{repetitions}: "
                f"Δ={cycle['delta_pct']:+.4f}% "
                f"peak={cycle['peak_delta_pct']:+.4f}% "
                f"base={cycle['baseline']:.1f}",
                file=sys.stderr,
            )

        median_delta = float(np.median(deltas))
        std_delta = float(np.std(deltas))
        median_peak = float(np.median(peak_deltas))

        result = {
            "a": a,
            "b": b,
            "product": round(a * b, 4),
            "green_duration_s": round(green_duration_s, 3),
            "repetitions": repetitions,
            "mask_pixels": mask_count,
            "mask_mean": round(mask_mean, 1),
            "median_delta_pct": round(median_delta, 4),
            "std_delta_pct": round(std_delta, 4),
            "median_peak_delta_pct": round(median_peak, 4),
            "all_deltas": [round(d, 4) for d in deltas],
            "all_peak_deltas": [round(d, 4) for d in peak_deltas],
            "cycles": all_cycles,
        }
        return result

    finally:
        all_off()
        cam.stop()
        cam.close()
        if GPIO is not None:
            GPIO.cleanup((RED_PIN, GREEN_PIN))
        subprocess.run(
            ["systemctl", "--user", "start", "c1-camera-rtsp"],
            capture_output=True, timeout=15,
        )


def run_sweep(
    repetitions: int = 7,
    recovery_s: float = 10.0,
    shutter_us: int = 5000,
    gain: float = 1.5,
) -> dict:
    """Sweep multiple products to map the dose-response curve."""
    import subprocess

    subprocess.run(
        ["systemctl", "--user", "stop", "c1-camera-rtsp"],
        capture_output=True, timeout=10,
    )
    time.sleep(1)

    from picamera2 import Picamera2

    cam = Picamera2()
    config = cam.create_still_configuration(
        main={"size": (FRAME_W, FRAME_H), "format": "RGB888"},
        controls={
            "ExposureTime": shutter_us,
            "AnalogueGain": gain,
            "ColourGains": (1.5, 1.0),
            "AeEnable": False,
            "AwbEnable": False,
            "NoiseReductionMode": 0,
        },
    )
    cam.configure(config)
    cam.start()
    time.sleep(2)

    setup_gpio()

    results = []
    test_points = [
        (0, 0, "control"),
        (2, 2, "low"),
        (5, 5, "medium"),
        (10, 5, "high_a"),
        (5, 10, "high_b"),
        (10, 10, "maximum"),
    ]

    try:
        # Calibrate mask
        red_on()
        green_off()
        time.sleep(1)
        cal_frame = cam.capture_array("main")
        cal_roi = extract_roi(cal_frame)[:, :, 0].astype(np.float64)
        mask = build_mask(cal_roi, lo=30, hi=220)
        mask_count = int(mask.sum())
        mask_mean = float(np.mean(cal_roi[mask])) if mask_count > 10 else 0.0
        print(f"Mask: {mask_count} pixels, mean={mask_mean:.1f}", file=sys.stderr)

        for a, b, label in test_points:
            green_duration_s = max(0.05, b * 0.2)
            print(
                f"\n=== {label}: a={a}, b={b}, product={a*b}, "
                f"dur={green_duration_s:.2f}s ===",
                file=sys.stderr,
            )

            deltas = []
            peak_deltas = []
            for rep in range(repetitions):
                red_on()
                green_off()
                time.sleep(recovery_s if rep == 0 else recovery_s / 2)

                cycle = run_single_cycle(
                    cam, mask,
                    green_duration_s=green_duration_s,
                    read_settle_s=0.5,
                    n_baseline=15,
                    n_post=15,
                )
                deltas.append(cycle["delta_pct"])
                peak_deltas.append(cycle["peak_delta_pct"])
                print(
                    f"  Rep {rep+1}/{repetitions}: "
                    f"Δ={cycle['delta_pct']:+.4f}% "
                    f"peak={cycle['peak_delta_pct']:+.4f}%",
                    file=sys.stderr,
                )

            results.append({
                "label": label,
                "a": a,
                "b": b,
                "product": a * b,
                "green_duration_s": round(green_duration_s, 3),
                "median_delta_pct": round(float(np.median(deltas)), 4),
                "std_delta_pct": round(float(np.std(deltas)), 4),
                "median_peak_delta_pct": round(float(np.median(peak_deltas)), 4),
                "all_deltas": [round(d, 4) for d in deltas],
            })

        return {
            "mask_pixels": mask_count,
            "mask_mean": round(mask_mean, 1),
            "shutter_us": shutter_us,
            "gain": gain,
            "repetitions": repetitions,
            "recovery_s": recovery_s,
            "results": results,
        }

    finally:
        all_off()
        cam.stop()
        cam.close()
        if GPIO is not None:
            GPIO.cleanup((RED_PIN, GREEN_PIN))
        subprocess.run(
            ["systemctl", "--user", "start", "c1-camera-rtsp"],
            capture_output=True, timeout=15,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="bR analog multiplication demo")
    parser.add_argument("--a", type=float, default=5.0)
    parser.add_argument("--b", type=float, default=5.0)
    parser.add_argument("--reps", type=int, default=10)
    parser.add_argument("--recovery", type=float, default=10.0)
    parser.add_argument("--shutter", type=int, default=5000)
    parser.add_argument("--gain", type=float, default=1.5)
    parser.add_argument("--sweep", action="store_true")
    args = parser.parse_args()

    if args.sweep:
        result = run_sweep(
            repetitions=args.reps,
            recovery_s=args.recovery,
            shutter_us=args.shutter,
            gain=args.gain,
        )
    else:
        result = run_multiply(
            a=args.a,
            b=args.b,
            repetitions=args.reps,
            recovery_s=args.recovery,
            shutter_us=args.shutter,
            gain=args.gain,
        )

    print(json.dumps(result, indent=2))
