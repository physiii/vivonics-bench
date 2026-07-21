#!/usr/bin/env python3
"""Verify the first-article power/input bring-up measurement template."""
from __future__ import annotations

import csv
from pathlib import Path


TEMPLATE = (
    Path(__file__).resolve().parent
    / "review"
    / "calibration"
    / "first_article_power_bringup_template.csv"
)

REQUIRED_COLUMNS = (
    "category",
    "target",
    "node_or_rail",
    "accepted_limit",
    "bringup_boundary",
    "required_measurements",
    "release_blocker",
)

REQUIRED_ROWS = {
    ("input", "J5", "VIN_24V", "24.0 V, <=300 mA current limit", "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT"),
    ("input_gap", "VIN24_PROTECTION", "VIN_24V", "production not released", "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT"),
    ("buck", "U15", "/POWER_IO/BUCK_5V", "5 V rail verification", "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT"),
    ("rail", "D5/D6", "+5V", "post-OR rail verification", "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT"),
    ("buck", "U16", "LASER_V+", "9.3 V-class rail verification", "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT"),
    ("ldo", "U11", "+3V3", "<=120 mA continuous, RF disabled", "AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE"),
}

REQUIRED_TEXT = {
    ("input", "J5"): ("J5 barrel input only", "center-positive", "no hot-plug", "RJ45 power disabled"),
    ("input_gap", "VIN24_PROTECTION"): (
        "fuse/current-limit",
        "reverse-polarity",
        "transient/TVS",
        "RJ45 harness",
    ),
    ("buck", "U15"): ("startup overshoot", "steady ripple", "load-step transient", "temperature"),
    ("rail", "D5/D6"): ("diode drop", "post-OR +5V", "temperature"),
    ("buck", "U16"): ("startup overshoot", "steady ripple", "load-step transient", "temperature"),
    ("ldo", "U11"): ("USB/UART control firmware", "Wi-Fi/BLE disabled", "+3V3 rail current", "AP2112 package temperature"),
}


def row_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["category"].strip(),
        row["target"].strip(),
        row["node_or_rail"].strip(),
        row["accepted_limit"].strip(),
        row["release_blocker"].strip(),
    )


def main() -> int:
    failures: list[str] = []
    if not TEMPLATE.exists():
        print(f"FAIL power bring-up template: missing {TEMPLATE}")
        return 1

    with TEMPLATE.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            failures.append(
                f"expected columns {REQUIRED_COLUMNS}, got {tuple(reader.fieldnames or ())}"
            )
            rows: list[dict[str, str]] = []
        else:
            rows = list(reader)

    keys = [row_key(row) for row in rows]
    key_set = set(keys)
    duplicate_keys = sorted(key for key in key_set if keys.count(key) > 1)
    if duplicate_keys:
        failures.append(f"duplicate power bring-up rows: {duplicate_keys}")

    missing = sorted(REQUIRED_ROWS - key_set)
    extra = sorted(key_set - REQUIRED_ROWS)
    if missing:
        failures.append(f"missing required power bring-up rows: {missing}")
    if extra:
        failures.append(f"unexpected power bring-up rows: {extra}")

    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row[column].strip():
                failures.append(f"line {index}: empty {column}")
        key = (row["category"].strip(), row["target"].strip())
        text = f"{row['bringup_boundary']} {row['required_measurements']}"
        for phrase in REQUIRED_TEXT.get(key, ()):
            if phrase not in text:
                failures.append(f"line {index}: missing required phrase {phrase!r}")

    if failures:
        print("FAIL power bring-up template")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS power bring-up template: VIN24, AP632, +5V, LASER_V+, and AP2112 "
        "first-article measurement rows are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
