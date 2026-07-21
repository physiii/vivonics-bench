#!/usr/bin/env python3
"""Verify the AP632 first-article buck validation signoff."""
from __future__ import annotations

from pathlib import Path


SIGNOFF = (
    Path(__file__).resolve().parent
    / "review"
    / "signoff"
    / "2026-07-05-ap632-first-article-buck-validation-signoff.md"
)

REQUIRED_PHRASES = (
    "J5 barrel input only",
    "external current limit no higher than 300 mA",
    "RJ45 power disabled",
    "Verify `/POWER_IO/BUCK_5V`, post-OR `+5V`, and `LASER_V+`",
    "Treat `LASER_V+` as a 9.3 V-class rail",
    "Measure startup overshoot, steady ripple, and load-step transient",
    "Measure U15, U16, L1, L2, D6, C64-C65, and C67-C68 temperature",
    "Do not run all laser channels at maximum command",
    "Rerun `check_buck_input_power_budget.py` before changing the input voltage",
    "does not close production input protection",
)


def main() -> int:
    failures: list[str] = []
    if not SIGNOFF.exists():
        failures.append(f"missing AP632 buck signoff: {SIGNOFF}")
    else:
        text = SIGNOFF.read_text()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                failures.append(f"AP632 buck signoff missing phrase: {phrase}")

    if failures:
        print("FAIL AP632 first-article buck validation signoff")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS AP632 first-article buck validation signoff: J5/current-limit "
        "bring-up, rail verification, ripple/transient capture, and buck "
        "temperature measurement are required before trusting VIN24 buck rails."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
