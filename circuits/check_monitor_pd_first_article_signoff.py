#!/usr/bin/env python3
"""Verify the monitor-PD first-article calibration signoff."""
from __future__ import annotations

from pathlib import Path


SIGNOFF = (
    Path(__file__).resolve().parent
    / "review"
    / "signoff"
    / "2026-07-05-monitor-pd-first-article-calibration-signoff.md"
)

REQUIRED_PHRASES = (
    "LD1` D7805I, `LD2` D6505I, and `LD3` PLT5 520EB_P",
    "LD4` PLT5 450GB has no monitor photodiode",
    "treat `MPD_RAW4` / `MPD4` as spare/open, not blue-source telemetry",
    "calibrating laser current -> MPD ADC counts ->",
    "external optical power meter for each monitor-capable source",
    "Monitor-PD telemetry must not raise current above the per-channel",
    "Calibrate one source at a time at minimum firmware duty cycle",
    "Record dark/off ADC counts, response slope, saturation threshold",
    "Firmware must fail shutoff or inhibit the source",
    "does not close production APC",
)


def main() -> int:
    failures: list[str] = []
    if not SIGNOFF.exists():
        failures.append(f"missing monitor-PD signoff: {SIGNOFF}")
    else:
        text = SIGNOFF.read_text()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                failures.append(f"monitor-PD signoff missing phrase: {phrase}")

    if failures:
        print("FAIL monitor-PD first-article calibration signoff")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS monitor-PD first-article calibration signoff: LD1-LD3 require "
        "external optical-meter calibration before MPD telemetry is used for "
        "APC, normalization, or safety behavior; LD4/MPD4 stays spare/open."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
