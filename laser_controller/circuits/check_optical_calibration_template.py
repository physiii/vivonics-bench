#!/usr/bin/env python3
"""Verify the first-article optical/readout calibration template.

This does not validate measured calibration data. It locks the required
monitor-PD, signal-PD, and AD7606 known-input rows so first-article bring-up
cannot skip a channel when real measurements are captured.
"""
from __future__ import annotations

import csv
from pathlib import Path


TEMPLATE = (
    Path(__file__).resolve().parent
    / "review"
    / "calibration"
    / "first_article_optical_calibration_template.csv"
)

REQUIRED_COLUMNS = (
    "category",
    "target_ref",
    "channel_label",
    "signal_path",
    "fixture_input",
    "required_measurements",
    "release_blocker",
)

REQUIRED_ROWS = {
    ("monitor_pd", "LD1", "INFRARED", "MPD_RAW1->MPD1", "MONITOR_PD_FRONTEND_RANGE_CALIBRATION"),
    ("monitor_pd", "LD2", "RED", "MPD_RAW2->MPD2", "MONITOR_PD_FRONTEND_RANGE_CALIBRATION"),
    ("monitor_pd", "LD3", "GREEN", "MPD_RAW3->MPD3", "MONITOR_PD_FRONTEND_RANGE_CALIBRATION"),
    ("monitor_pd", "LD4", "BLUE", "MPD_RAW4->MPD4", "MONITOR_PD_FRONTEND_RANGE_CALIBRATION"),
    ("signal_pd", "D1", "PD CH1", "SFH2201->OPA380->VOUT1", "TIA_READOUT_RANGE_CALIBRATION"),
    ("signal_pd", "D2", "PD CH2", "SFH2201->OPA380->VOUT2", "TIA_READOUT_RANGE_CALIBRATION"),
    ("signal_pd", "D3", "PD CH3", "SFH2201->OPA380->VOUT3", "TIA_READOUT_RANGE_CALIBRATION"),
    ("signal_pd", "D4", "PD CH4", "SFH2201->OPA380->VOUT4", "TIA_READOUT_RANGE_CALIBRATION"),
    ("adc_readback", "U14 V1", "PD CH1", "VOUT1->AD7606 V1", "AD7606_SYSTEM_INTERFACE"),
    ("adc_readback", "U14 V2", "PD CH2", "VOUT2->AD7606 V2", "AD7606_SYSTEM_INTERFACE"),
    ("adc_readback", "U14 V3", "PD CH3", "VOUT3->AD7606 V3", "AD7606_SYSTEM_INTERFACE"),
    ("adc_readback", "U14 V4", "PD CH4", "VOUT4->AD7606 V4", "AD7606_SYSTEM_INTERFACE"),
}

REQUIRED_TEXT = {
    ("monitor_pd", "LD1"): ("external optical power meter", "firmware fail-shutoff"),
    ("monitor_pd", "LD2"): ("external optical power meter", "firmware fail-shutoff"),
    ("monitor_pd", "LD3"): ("external optical power meter", "firmware fail-shutoff"),
    ("monitor_pd", "LD4"): ("no monitor photodiode", "spare/open"),
    ("signal_pd", "D1"): ("dark ADC counts", "RF trim", "VBIAS"),
    ("signal_pd", "D2"): ("dark ADC counts", "RF trim", "VBIAS"),
    ("signal_pd", "D3"): ("dark ADC counts", "RF trim", "VBIAS"),
    ("signal_pd", "D4"): ("dark ADC counts", "RF trim", "VBIAS"),
    ("adc_readback", "U14 V1"): ("known-input counts", "+/-5 V scaling"),
    ("adc_readback", "U14 V2"): ("known-input counts", "+/-5 V scaling"),
    ("adc_readback", "U14 V3"): ("known-input counts", "+/-5 V scaling"),
    ("adc_readback", "U14 V4"): ("known-input counts", "+/-5 V scaling"),
}


def row_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["category"].strip(),
        row["target_ref"].strip(),
        row["channel_label"].strip(),
        row["signal_path"].strip(),
        row["release_blocker"].strip(),
    )


def main() -> int:
    failures: list[str] = []
    if not TEMPLATE.exists():
        print(f"FAIL optical calibration template: missing {TEMPLATE}")
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
        failures.append(f"duplicate calibration rows: {duplicate_keys}")

    missing = sorted(REQUIRED_ROWS - key_set)
    extra = sorted(key_set - REQUIRED_ROWS)
    if missing:
        failures.append(f"missing required calibration rows: {missing}")
    if extra:
        failures.append(f"unexpected calibration rows: {extra}")

    for row in rows:
        key = (row["category"].strip(), row["target_ref"].strip())
        text = f"{row['fixture_input']} {row['required_measurements']}"
        for phrase in REQUIRED_TEXT.get(key, ()):
            if phrase not in text:
                failures.append(f"{key}: missing required phrase {phrase!r}")

    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row[column].strip():
                failures.append(f"line {index}: empty {column}")

    if failures:
        print("FAIL optical calibration template")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS optical calibration template: 12 first-article monitor-PD, "
        "signal-PD, and AD7606 readback rows are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
