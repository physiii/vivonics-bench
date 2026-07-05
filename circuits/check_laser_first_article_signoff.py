#!/usr/bin/env python3
"""Verify the laser first-article bring-up signoff."""
from __future__ import annotations

from pathlib import Path


SIGNOFF = (
    Path(__file__).resolve().parent
    / "review"
    / "signoff"
    / "2026-07-05-laser-first-article-bringup-signoff.md"
)

REQUIRED_PHRASES = (
    "appropriate wavelength-rated laser safety eyewear",
    "enclosed beam stop",
    "Inspect each received laser can against the 2026-07-04 MPN/footprint pin table",
    "Bring up one laser channel at a time.",
    "Start each channel at minimum firmware duty cycle and minimum command.",
    "IR 38.0 mA, red 23.0 mA, green 76.2 mA, blue 105.5 mA",
    "Verify the shared `LASER_V+` rail before enabling any channel",
    "Measure driver/sense-resistor temperature during bring-up for every channel.",
    "Measure optical output with an external optical power meter for every channel.",
    "does not close optical safety",
)


def main() -> int:
    failures: list[str] = []
    if not SIGNOFF.exists():
        failures.append(f"missing laser bring-up signoff: {SIGNOFF}")
    else:
        text = SIGNOFF.read_text()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                failures.append(f"laser bring-up signoff missing phrase: {phrase}")

    if failures:
        print("FAIL laser first-article bring-up signoff")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS laser first-article bring-up signoff: one-channel-at-a-time optical "
        "and temperature measurements are required; electrical current-limit "
        "checks remain separate from optical safety release."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
