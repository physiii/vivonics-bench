#!/usr/bin/env python3
"""Verify the AD7606 first-article firmware/readback signoff."""
from __future__ import annotations

from pathlib import Path


SIGNOFF = (
    Path(__file__).resolve().parent
    / "review"
    / "signoff"
    / "2026-07-05-ad7606-first-article-readback-signoff.md"
)

REQUIRED_PHRASES = (
    "Keep nominal SCLK at or below 10 MHz",
    "Default target sample rate is 100 kSPS or lower",
    "Use read-after-conversion firmware until scoped otherwise.",
    "Pulse RESET high for at least 50 ns",
    "Wait for BUSY to fall before asserting CS",
    "Read 32 SCLK edges per DOUT line",
    "Read both ADC_MISO_A and ADC_MISO_B",
    "Confirm RANGE=0 +/-5 V scaling",
    "16-bit twos-complement with 152.59 uV/LSB",
    "Apply known voltages or known TIA calibration inputs to VOUT1..4",
    "Rerun `check_ad7606_interface_budget.py` before raising SCLK",
    "does not close firmware implementation",
)


def main() -> int:
    failures: list[str] = []
    if not SIGNOFF.exists():
        failures.append(f"missing AD7606 signoff: {SIGNOFF}")
    else:
        text = SIGNOFF.read_text()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                failures.append(f"AD7606 signoff missing phrase: {phrase}")

    if failures:
        print("FAIL AD7606 first-article firmware/readback signoff")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS AD7606 first-article firmware/readback signoff: firmware timing, "
        "two-DOUT readback, +/-5 V scaling, and known-input validation are "
        "required before bench ADC data is trusted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
