#!/usr/bin/env python3
"""Verify the quote-time procurement and production-derating evidence template."""
from __future__ import annotations

import csv
from pathlib import Path


TEMPLATE = (
    Path(__file__).resolve().parent
    / "review"
    / "calibration"
    / "quote_time_procurement_release_template.csv"
)

REQUIRED_COLUMNS = (
    "category",
    "target",
    "artifact_or_scope",
    "required_evidence",
    "release_blocker",
)

REQUIRED_ROWS = {
    ("jlcpcb_quote", "assembled_bom", "laser_controller_bom_jlcpcb.csv", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
    ("jlcpcb_quote", "placement", "fab/laser_controller_pos.csv", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
    ("passive_avl", "locked_passives", "docs/part-notes/passive-first-article-avl-lock.md", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
    ("substitution_review", "all_c_codes", "BOM quote substitutions", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
    ("production_derating", "24V_and_laser_paths", "pulse/surge/current derating", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
    ("thermal_evidence", "board_temperature", "accepted duty cycle", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
    ("order_archive", "jlcpcb_package", "laser_controller_jlcpcb_package.zip", "PASSIVE_PRODUCTION_AVL_AND_DERATING"),
}

REQUIRED_TEXT = {
    ("jlcpcb_quote", "assembled_bom"): ("current quote timestamp", "every C-code accepted", "no automatic substitution"),
    ("jlcpcb_quote", "placement"): ("BOM/POS accepted together", "top-side SMT", "manual parts excluded"),
    ("passive_avl", "locked_passives"): ("24 passive MPN/LCSC pairs", "lifecycle/stock", "assembly tier"),
    ("substitution_review", "all_c_codes"): ("reject substitutions", "checkpoint commit", "rerun passive checks"),
    ("production_derating", "24V_and_laser_paths"): ("pulse/surge/current", "24 V input", "laser-current paths"),
    ("thermal_evidence", "board_temperature"): ("measured board temperature", "accepted duty cycle", "hot components"),
    ("order_archive", "jlcpcb_package"): ("Gerber", "BOM", "POS", "commit hash"),
}


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row["category"].strip(),
        row["target"].strip(),
        row["artifact_or_scope"].strip(),
        row["release_blocker"].strip(),
    )


def main() -> int:
    failures: list[str] = []
    if not TEMPLATE.exists():
        print(f"FAIL procurement release template: missing {TEMPLATE}")
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
        failures.append(f"duplicate procurement rows: {duplicate_keys}")

    missing = sorted(REQUIRED_ROWS - key_set)
    extra = sorted(key_set - REQUIRED_ROWS)
    if missing:
        failures.append(f"missing required procurement rows: {missing}")
    if extra:
        failures.append(f"unexpected procurement rows: {extra}")

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
        print("FAIL procurement release template")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS procurement release template: quote-time BOM/POS, substitution, "
        "derating, temperature, and order-archive evidence rows are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
