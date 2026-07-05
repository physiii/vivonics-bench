#!/usr/bin/env python3
"""Verify the AP2112 first-article no-RF operating signoff."""
from __future__ import annotations

from pathlib import Path


SIGNOFF = (
    Path(__file__).resolve().parent
    / "review"
    / "signoff"
    / "2026-07-05-ap2112-first-article-signoff.md"
)

REQUIRED_PHRASES = (
    "Use USB/UART control firmware only during first-article bring-up.",
    "Keep ESP32 Wi-Fi/BLE disabled on this board.",
    "Keep continuous +3V3 current no higher than 120 mA.",
    "Measure AP2112 package temperature and +3V3 rail current during first bring-up.",
    "Sustained Wi-Fi/BLE requires a buck regulator",
    "does not close production regulator decision",
)


def main() -> int:
    failures: list[str] = []
    if not SIGNOFF.exists():
        failures.append(f"missing AP2112 signoff: {SIGNOFF}")
    else:
        text = SIGNOFF.read_text()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                failures.append(f"AP2112 signoff missing phrase: {phrase}")

    if failures:
        print("FAIL AP2112 first-article signoff")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS AP2112 first-article signoff: USB/UART no-RF operation is capped at "
        "120 mA continuous +3V3; package temperature, rail current, and sustained "
        "Wi-Fi/BLE remain release risks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
