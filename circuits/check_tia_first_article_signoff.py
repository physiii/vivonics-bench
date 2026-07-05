#!/usr/bin/env python3
"""Verify the TIA readout first-article calibration signoff."""
from __future__ import annotations

from pathlib import Path


SIGNOFF = (
    Path(__file__).resolve().parent
    / "review"
    / "signoff"
    / "2026-07-05-tia-first-article-calibration-signoff.md"
)

REQUIRED_PHRASES = (
    "2 Mohm feedback trim as a high-sensitivity, low-current",
    "Start with VBIAS target 1.5 V",
    "covered or optically shielded during dark-offset",
    "SFH2201 1000 lx example is an",
    "Calibrate `VOUT1..4` one channel at a time",
    "known electrical current injection or a calibrated optical input",
    "Record RF/trim state, VBIAS, dark ADC counts",
    "Confirm AD7606 +/-5 V scaling for `VOUT1..4`",
    "Firmware must flag saturation, out-of-range counts, dark-offset drift",
    "does not close production measurement release",
)


def main() -> int:
    failures: list[str] = []
    if not SIGNOFF.exists():
        failures.append(f"missing TIA signoff: {SIGNOFF}")
    else:
        text = SIGNOFF.read_text()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                failures.append(f"TIA signoff missing phrase: {phrase}")

    if failures:
        print("FAIL TIA first-article calibration signoff")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS TIA first-article calibration signoff: VOUT1..4 require dark "
        "offset, known-input calibration, ambient shielding, and AD7606 scaling "
        "checks before production measurement use."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
