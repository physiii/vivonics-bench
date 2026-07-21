#!/usr/bin/env python3
"""Verify the first-article laser bring-up measurement template.

The electrical current-loop checks prove the selected limits on paper. This
template gate makes the required first-article laser safety, current, optical,
and thermal measurement rows explicit for LD1-LD4.
"""
from __future__ import annotations

import csv
from pathlib import Path

from check_laser_current_budget import SELECTED_LASER_SPECS
from laser_command_limits import limiter_for_color


TEMPLATE = (
    Path(__file__).resolve().parent
    / "review"
    / "calibration"
    / "first_article_laser_bringup_template.csv"
)

REQUIRED_COLUMNS = (
    "channel_ref",
    "color",
    "laser_mpn",
    "nominal_current_limit_ma",
    "tolerance_corner_current_ma",
    "laser_vplus_check",
    "fixture_required",
    "required_measurements",
    "release_blocker",
)

COLOR_LABELS = {
    "IR": "INFRARED",
    "RED": "RED",
    "GREEN": "GREEN",
    "BLUE": "BLUE",
}

REQUIRED_PHRASES = (
    "wavelength-rated eyewear",
    "enclosed beam stop",
    "received-can pinout",
    "one-channel-at-a-time",
    "firmware duty/command",
    "measured current",
    "driver/sense-resistor temperature",
    "external optical power",
    "shutoff",
)


def expected_rows() -> set[tuple[str, str, str, str, str, str]]:
    rows: set[tuple[str, str, str, str, str, str]] = set()
    for spec in SELECTED_LASER_SPECS:
        limiter = limiter_for_color(spec.channel)
        rows.add(
            (
                spec.ref,
                COLOR_LABELS[spec.channel],
                spec.mpn,
                f"{limiter.command_current_a * 1000.0:.1f}",
                f"{limiter.worst_case_current_a * 1000.0:.1f}",
                "PER_DIODE_LASER_THERMAL_BUDGET",
            )
        )
    return rows


def row_key(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    return (
        row["channel_ref"].strip(),
        row["color"].strip(),
        row["laser_mpn"].strip(),
        row["nominal_current_limit_ma"].strip(),
        row["tolerance_corner_current_ma"].strip(),
        row["release_blocker"].strip(),
    )


def main() -> int:
    failures: list[str] = []
    if not TEMPLATE.exists():
        print(f"FAIL laser bring-up template: missing {TEMPLATE}")
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
        failures.append(f"duplicate laser bring-up rows: {duplicate_keys}")

    required_rows = expected_rows()
    missing = sorted(required_rows - key_set)
    extra = sorted(key_set - required_rows)
    if missing:
        failures.append(f"missing required laser bring-up rows: {missing}")
    if extra:
        failures.append(f"unexpected laser bring-up rows: {extra}")

    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row[column].strip():
                failures.append(f"line {index}: empty {column}")
        combined_text = f"{row['laser_vplus_check']} {row['fixture_required']} {row['required_measurements']}"
        for phrase in REQUIRED_PHRASES:
            if phrase not in combined_text:
                failures.append(f"line {index}: missing required phrase {phrase!r}")

    if failures:
        print("FAIL laser bring-up template")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS laser bring-up template: LD1-LD4 current-limit, optical-output, "
        "temperature, and firmware-shutoff measurement rows are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
