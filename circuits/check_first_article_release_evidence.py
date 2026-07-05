#!/usr/bin/env python3
"""Verify first-article and production-release evidence closure rows.

The template checkers prove that required measurement templates exist. This
checker is the stronger release ledger: every blocker must have explicit closure
rows, and a row can only be marked CLOSED when an evidence file exists and
contains the required tokens.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
LEDGER = (
    Path(__file__).resolve().parent
    / "review"
    / "calibration"
    / "first_article_release_evidence.csv"
)

REQUIRED_COLUMNS = (
    "blocker_id",
    "evidence_id",
    "severity",
    "evidence_status",
    "evidence_path",
    "required_tokens",
    "closure_criteria",
)

REQUIRED_ROWS = {
    ("AD7606_SYSTEM_INTERFACE", "digital_timing"),
    ("AD7606_SYSTEM_INTERFACE", "dout_readback"),
    ("AD7606_SYSTEM_INTERFACE", "scaling_channel_order_known_input"),
    ("AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE", "no_rf_current_temp"),
    ("AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE", "regulator_decision"),
    ("MONITOR_PD_FRONTEND_RANGE_CALIBRATION", "monitor_pd_calibration"),
    ("MONITOR_PD_FRONTEND_RANGE_CALIBRATION", "mpd4_blue_spare_open"),
    ("PASSIVE_PRODUCTION_AVL_AND_DERATING", "passive_derating"),
    ("PASSIVE_PRODUCTION_AVL_AND_DERATING", "quote_acceptance"),
    ("PER_DIODE_LASER_THERMAL_BUDGET", "laser_bringup"),
    ("PER_DIODE_LASER_THERMAL_BUDGET", "laser_safety_fixture"),
    ("TIA_READOUT_RANGE_CALIBRATION", "ambient_saturation_policy"),
    ("TIA_READOUT_RANGE_CALIBRATION", "signal_pd_calibration"),
    ("VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT", "buck_rail_measurement"),
    ("VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT", "first_power_limits"),
    ("VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT", "production_protection"),
}

ALLOWED_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM"}
ALLOWED_STATUSES = {"OPEN", "CLOSED"}
PLACEHOLDERS = {"", "TBD", "TODO", "NONE", "N/A"}


@dataclass(frozen=True)
class LedgerCheck:
    failures: tuple[str, ...]
    open_rows: tuple[tuple[str, str], ...]
    closed_rows: tuple[tuple[str, str], ...]


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return row["blocker_id"].strip(), row["evidence_id"].strip()


def tokens(row: dict[str, str]) -> list[str]:
    return [token.strip() for token in row["required_tokens"].split(";") if token.strip()]


def validate_closed_row(row: dict[str, str]) -> list[str]:
    failures: list[str] = []
    key = row_key(row)
    evidence_path = row["evidence_path"].strip()
    if evidence_path.upper() in PLACEHOLDERS:
        return [f"{key[0]}/{key[1]}: CLOSED row must name an evidence file"]
    path = REPO_DIR / evidence_path
    if not path.exists():
        return [f"{key[0]}/{key[1]}: evidence file does not exist: {evidence_path}"]
    text = path.read_text(errors="replace").casefold()
    for token in tokens(row):
        if token.casefold() not in text:
            failures.append(f"{key[0]}/{key[1]}: evidence file missing token {token!r}")
    return failures


def validate_ledger(path: Path = LEDGER) -> LedgerCheck:
    failures: list[str] = []
    if not path.exists():
        return LedgerCheck((f"missing {path}",), (), ())

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            failures.append(f"expected columns {REQUIRED_COLUMNS}, got {tuple(reader.fieldnames or ())}")
            rows: list[dict[str, str]] = []
        else:
            rows = list(reader)

    keys = [row_key(row) for row in rows]
    key_set = set(keys)
    duplicate_keys = sorted(key for key in key_set if keys.count(key) > 1)
    if duplicate_keys:
        failures.append(f"duplicate evidence rows: {duplicate_keys}")

    missing = sorted(REQUIRED_ROWS - key_set)
    extra = sorted(key_set - REQUIRED_ROWS)
    if missing:
        failures.append(f"missing required evidence rows: {missing}")
    if extra:
        failures.append(f"unexpected evidence rows: {extra}")

    open_rows: list[tuple[str, str]] = []
    closed_rows: list[tuple[str, str]] = []
    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row[column].strip():
                failures.append(f"line {index}: empty {column}")
        key = row_key(row)
        if row["severity"].strip() not in ALLOWED_SEVERITIES:
            failures.append(f"line {index}: invalid severity {row['severity']!r}")
        status = row["evidence_status"].strip()
        if status not in ALLOWED_STATUSES:
            failures.append(f"line {index}: invalid evidence_status {status!r}")
            continue
        if not tokens(row):
            failures.append(f"line {index}: required_tokens must contain at least one token")
        if status == "OPEN":
            open_rows.append(key)
        elif status == "CLOSED":
            closed_rows.append(key)
            failures.extend(validate_closed_row(row))

    return LedgerCheck(tuple(failures), tuple(open_rows), tuple(closed_rows))


def main() -> int:
    check = validate_ledger()
    if check.failures and any(failure.startswith("missing ") for failure in check.failures):
        print(f"FAIL first-article release evidence: {check.failures[0]}")
        return 1

    failures = list(check.failures)
    open_rows = list(check.open_rows)

    if failures:
        print("FAIL first-article release evidence ledger")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    if open_rows:
        print(
            "DEFERRED first-article release evidence: "
            f"{len(open_rows)} evidence row(s) still OPEN"
        )
        for blocker_id, evidence_id in open_rows:
            print(f"  - {blocker_id}/{evidence_id}")
        return 2

    print(
        "PASS first-article release evidence: all blocker evidence rows are CLOSED "
        "and linked evidence files contain required tokens"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
