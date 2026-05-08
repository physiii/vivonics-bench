"""CLI runner for X1 camera + sensor smoke-test measurements.

Use this on the Raspberry Pi when you want a file-backed run without the
dashboard service. The service and this CLI share the same projector, camera,
and I2C sensor modules.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from capture import Capture, CaptureConfig
from projector import Projector, ProjectorConfig
from sensors import SensorSuite


DEFAULT_RED_LEVELS = (0, 32, 64, 96, 128, 160, 192)


def parse_levels(value: str) -> tuple[int, ...]:
    levels = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    for level in levels:
        if level < 0 or level > 255:
            raise argparse.ArgumentTypeError("levels must be 0-255")
    return levels


def snapshot(
    label: str,
    capture: Capture,
    sensors: SensorSuite,
    frames_per_average: int,
    include_camera: bool,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "label": label,
        "timestamp_s": time.time(),
        "sensors": sensors.read_all(),
    }
    if include_camera:
        frame, path = capture.grab_averaged(frames_per_average, label)
        frame_ds = capture.subtract_dark(frame)
        record["camera"] = {
            "frame_path": str(path),
            "red_mean": capture.red_channel_mean(frame_ds),
            "roi_mean": float(np.mean(frame_ds)),
        }
    return record


def flatten_scalar_channels(record: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    camera = record.get("camera")
    if isinstance(camera, dict):
        values["camera.red_mean"] = float(camera.get("red_mean", 0.0))
        values["camera.roi_mean"] = float(camera.get("roi_mean", 0.0))

    for reading in record.get("sensors", {}).get("readings", []):
        if not reading.get("ok"):
            continue
        name = reading.get("name", "sensor")
        channels = reading.get("channels", {})
        for channel, value in channels.items():
            values[f"{name}.{channel}"] = float(value)
    return values


def fit_linearity(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) < 2:
        return {}
    x = np.array([record["red_code"] for record in records], dtype=np.float64)
    keys = sorted({key for record in records for key in flatten_scalar_channels(record)})
    fits: dict[str, Any] = {}
    for key in keys:
        y = np.array([flatten_scalar_channels(record).get(key, 0.0) for record in records])
        if float(np.max(y) - np.min(y)) <= 0:
            continue
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        fits[key] = {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": r_squared,
            "passed": r_squared >= 0.99,
        }
    return fits


def run_sensor_check(args: argparse.Namespace) -> int:
    sensors = SensorSuite()
    payload = sensors.read_all()
    write_json(Path(args.output), payload)
    print(json.dumps(payload, indent=2))
    return 0


def run_linearity(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    capture = Capture(CaptureConfig(output_dir=output_dir / "frames", use_rtsp_grab=args.rtsp))
    sensors = SensorSuite()
    projector = Projector(ProjectorConfig(settle_time_s=args.settle_time_s))
    records: list[dict[str, Any]] = []

    projector.open()
    try:
        if args.camera:
            projector.off()
            capture.capture_dark_reference()

        for red_code in args.red_levels:
            projector.show_red(red_code)
            record = snapshot(
                label=f"red{red_code:03d}",
                capture=capture,
                sensors=sensors,
                frames_per_average=args.frames_per_average,
                include_camera=args.camera,
            )
            record["red_code"] = red_code
            records.append(record)
            append_jsonl(output_dir / "linearity_records.jsonl", record)
    finally:
        projector.off()
        projector.close()

    summary = {
        "protocol": "x1_red_linearity",
        "red_levels": list(args.red_levels),
        "frames_per_average": args.frames_per_average,
        "sensor_availability": sensors.availability(),
        "fits": fit_linearity(records),
        "records_path": str(output_dir / "linearity_records.jsonl"),
    }
    write_json(output_dir / "linearity_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vivonics X1 Pi measurement runner")
    sub = parser.add_subparsers(dest="command", required=True)

    sensor_check = sub.add_parser("sensor-check", help="Read TSL2591/AS7341 availability and values")
    sensor_check.add_argument("--output", default="/tmp/vivonics_sensor_check.json")
    sensor_check.set_defaults(func=run_sensor_check)

    linearity = sub.add_parser("linearity", help="Run red-code linearity with camera and I2C sensors")
    linearity.add_argument("--output-dir", default="/tmp/vivonics_x1_linearity")
    linearity.add_argument("--red-levels", type=parse_levels, default=DEFAULT_RED_LEVELS)
    linearity.add_argument("--frames-per-average", type=int, default=4)
    linearity.add_argument("--settle-time-s", type=float, default=0.5)
    linearity.add_argument("--camera", action=argparse.BooleanOptionalAction, default=True)
    linearity.add_argument("--rtsp", action=argparse.BooleanOptionalAction, default=True)
    linearity.set_defaults(func=run_linearity)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
