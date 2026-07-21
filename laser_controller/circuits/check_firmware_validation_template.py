#!/usr/bin/env python3
"""Verify the first-article firmware/readback validation template."""
from __future__ import annotations

import csv
from pathlib import Path


TEMPLATE = (
    Path(__file__).resolve().parent
    / "review"
    / "calibration"
    / "first_article_firmware_validation_template.csv"
)

REQUIRED_COLUMNS = (
    "category",
    "target",
    "interface_or_signal",
    "accepted_limit",
    "required_evidence",
    "release_blocker",
)

REQUIRED_ROWS = {
    ("ad7606_timing", "U14_CONTROL", "RESET/CONVST/BUSY/CS/SCLK", "SCLK <=10 MHz, sample <=100 kSPS", "AD7606_SYSTEM_INTERFACE"),
    ("ad7606_stage_a_readback", "ADC_MISO_A", "DOUTA", "64 SCLK edges per sample", "AD7606_SYSTEM_INTERFACE"),
    ("ad7606_stage_b_readback", "ADC_MISO_A", "DOUTA", "32 SCLK edges per sample", "AD7606_SYSTEM_INTERFACE"),
    ("ad7606_stage_b_readback", "ADC_MISO_B", "DOUTB", "32 SCLK edges per sample", "AD7606_SYSTEM_INTERFACE"),
    ("ad7606_scaling", "RANGE_OS", "+/-5 V, no oversampling", "152.59 uV/LSB", "AD7606_SYSTEM_INTERFACE"),
    ("ad7606_channel_order", "VOUT1..4", "AD7606 V1/V2/V3/V4", "known channel ordering", "AD7606_SYSTEM_INTERFACE"),
    ("ad7606_known_input", "VOUT1..4", "known voltage or TIA input", "counts match expected value", "AD7606_SYSTEM_INTERFACE"),
}

REQUIRED_TEXT = {
    ("ad7606_timing", "U14_CONTROL"): ("scope capture", "BUSY fall before CS", "read-after-conversion"),
    ("ad7606_stage_a_readback", "ADC_MISO_A"): ("DOUTA", "64 SCLK", "V1 V2 V3 V4", "raw bytes"),
    ("ad7606_stage_b_readback", "ADC_MISO_A"): ("DOUTA", "32 SCLK", "firmware sample log"),
    ("ad7606_stage_b_readback", "ADC_MISO_B"): ("DOUTB", "32 SCLK", "firmware sample log"),
    ("ad7606_scaling", "RANGE_OS"): ("RANGE=0", "OS[2:0]=000", "152.59 uV/LSB"),
    ("ad7606_channel_order", "VOUT1..4"): ("VOUT1", "VOUT2", "VOUT3", "VOUT4"),
    ("ad7606_known_input", "VOUT1..4"): ("known-input counts", "expected value", "error limit"),
}


def row_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["category"].strip(),
        row["target"].strip(),
        row["interface_or_signal"].strip(),
        row["accepted_limit"].strip(),
        row["release_blocker"].strip(),
    )


def main() -> int:
    failures: list[str] = []
    if not TEMPLATE.exists():
        print(f"FAIL firmware validation template: missing {TEMPLATE}")
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
        failures.append(f"duplicate firmware validation rows: {duplicate_keys}")

    missing = sorted(REQUIRED_ROWS - key_set)
    extra = sorted(key_set - REQUIRED_ROWS)
    if missing:
        failures.append(f"missing required firmware validation rows: {missing}")
    if extra:
        failures.append(f"unexpected firmware validation rows: {extra}")

    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row[column].strip():
                failures.append(f"line {index}: empty {column}")
        key = (row["category"].strip(), row["target"].strip())
        text = row["required_evidence"]
        for phrase in REQUIRED_TEXT.get(key, ()):
            if phrase not in text:
                failures.append(f"line {index}: missing required phrase {phrase!r}")

    if failures:
        print("FAIL firmware validation template")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS firmware validation template: AD7606 timing, DOUT, scaling, "
        "channel-order, and known-input evidence rows are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
