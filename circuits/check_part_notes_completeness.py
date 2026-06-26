#!/usr/bin/env python3
"""Fail-closed completeness checks for critical datasheet part notes.

This is intentionally not a substitute for reading the datasheets. It prevents
the source register from passing with a part note that merely exists but has
lost the package pinout, layout-critical decision, release risk, or checker
evidence needed to audit the generated schematic and PCB.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


REPO_DIR = Path(__file__).resolve().parent.parent
PART_NOTES_DIR = REPO_DIR / "docs" / "part-notes"


@dataclass(frozen=True)
class NoteCheck:
    filename: str
    required: tuple[str, ...]
    forbidden: tuple[str, ...] = ()


NOTE_CHECKS: tuple[NoteCheck, ...] = (
    NoteCheck(
        "ESP32-S3-WROOM-1-N16R8.md",
        (
            "Real `Espressif:ESP32-S3-WROOM-1` symbol block",
            "GPIO19/pin 13 = D-",
            "GPIO20/pin 14 = D+",
            "`ISENSE1..4` on GPIO4/5/6/7",
            "`MPD1..4` on GPIO2/1/8/9",
            "GPIO0/BOOT has a pull-up and is exposed on J2",
            "EN has a pull-up and 100 nF",
            "module antenna keepout",
            "Wi-Fi/BLE disabled",
        ),
        (
            "inline `viv:ESP32S3`",
            "GPIO0/BOOT has a pull-up and is exposed on J3",
        ),
    ),
    NoteCheck(
        "OPA380AID.md",
        (
            "SOIC-8 pins 1, 5, and 8 are no-connects",
            "Pin 2 is the inverting/summing input",
            "Pin 3 is the non-inverting VBIAS input",
            "Pin 6 is output",
            "Pin 7 is positive supply / board +5 V",
            "Feedback is fixed 10 MOhm in parallel with 10 pF",
            "summing node must stay short",
            "PCB checker enforces photodiode/input/feedback/decoupling/bias proximity",
        ),
    ),
    NoteCheck(
        "TLV9001IDBVR.md",
        (
            "non-U DBV SOT-23-5 pinout: OUT=1, V-=2, IN+=3",
            "IN-=4, V+=5",
            "Do not substitute a TLV9001U",
            "IN+ receives filtered/limited PWM command",
            "IN- senses the MOSFET source/sense-resistor high side",
            "OUT drives the AO3400A gate",
            "Keep source-sense feedback short",
        ),
    ),
    NoteCheck(
        "AP2112K-3.3TRG1.md",
        (
            "SOT25 pin 1 = VIN",
            "Pin 2 = GND",
            "Pin 3 = EN",
            "Pin 4 = NC",
            "Pin 5 = VOUT",
            "120 mA",
            "SOT25 thetaJA is 184 degC/W",
            "sustained Wi-Fi/BLE use should replace this rail with a buck",
            "PCB checker enforces AP2112 input/output capacitor proximity",
        ),
    ),
    NoteCheck(
        "USBLC6-2SC6.md",
        (
            "Pins 1 and 6 are IO1 line pair",
            "Pin 2 is GND",
            "Pins 3 and 4 are IO2 line pair",
            "Pin 5 is VBUS clamp reference",
            "D- enters U10 IO1",
            "D+ enters U10 IO2",
            "Keep USBLC6 near the connector",
            "PCB checker enforces connector/USBLC6/series-resistor proximity",
        ),
    ),
    NoteCheck(
        "AO3400A.md",
        (
            "SOT-23 pin 1 = gate",
            "Pin 2 = source",
            "Pin 3 = drain",
            "linear low-side current-sink pass device",
            "Drain connects to the laser cathode harness net `LASER_Nx`",
            "Thermal/SOA must be checked",
            "`check_laser_current_budget.py` checks the AO3400A dissipation",
        ),
    ),
    NoteCheck(
        "SFH2201.md",
        (
            "Pin 1 is cathode",
            "Pin 2 is anode",
            "Cathode is reverse-biased from +5 V through 1 kOhm",
            "Anode goes to the OPA380 inverting summing node",
            "not as the internal laser monitor photodiode",
            "PCB checker enforces photodiode/TIA input-feedback-bias proximity",
        ),
    ),
    NoteCheck(
        "SS14.md",
        (
            "KiCad `D_SMA` pad 1 is anode",
            "Pad 2 is cathode",
            "D5 anode receives USB `VBUS_5V`",
            "D6 anode receives external `/POWER_IO/EXT5V`",
            "D5/D6 cathodes OR into `+5V`",
            "Confirm exact C2480 manufacturer datasheet and polarity at order",
        ),
    ),
    NoteCheck(
        "65100516121.md",
        (
            "Pin 1 = VBUS",
            "Pin 2 = D-",
            "Pin 3 = D+",
            "Pin 4 = ID",
            "Pin 5 = GND",
            "Shield pads tie to GND",
            "ID is an intentional no-connect",
            "Verify the current manufacturer drawing before fabrication",
        ),
    ),
    NoteCheck(
        "3224W-1-103E.md",
        (
            "VBIAS trim element",
            "0.25 W at 85 C",
            "Confirm the wiper orientation visually in Pcbnew",
            "Keep VBIAS routing quiet",
            "`check_passive_derating.py` checks the trimmer",
        ),
    ),
    NoteCheck(
        "PLT5-520B-harness-reference.md",
        (
            "one laser cathode",
            "common laser anode /",
            "monitor-PD cathode",
            "one monitor-PD anode",
            "J4 exposes `LASER_Nx`, `MPD_RAWx`, common `LASER_V+`, and GND",
            "Every actual laser MPN must be checked against its own pin table",
            "`L785P090` C-code monitor",
            "`L450G2` has no monitor photodiode",
            "run `check_laser_current_budget.py`",
        ),
    ),
    NoteCheck(
        "laser-harness-pin-code-compatibility.md",
        (
            "`LASER_V+ -> laser diode -> LASER_Nx -> AO3400A",
            "`MPD_RAWx -> 10k to GND || 100 nF to GND -> 1k -> ESP32 ADC1`",
            "monitor photodiode cathode at the laser common high node",
            "`PLT5 520B` style",
            "Thorlabs A-code",
            "`L785P090` is a C-code diode",
            "`L450G2` is a G-code diode with no monitor photodiode",
            "Do not wire",
        ),
    ),
    NoteCheck(
        "passive-bom-source-note.md",
        (
            "Generated BOM",
            "value, footprint, `Part Number`, and `LCSC`",
            "10 ohm 2512 2 W laser sense resistors",
            "every assembled capacitor, resistor, and SMD trimmer MPN",
            "Production still needs a procurement lock file",
            "pulse/surge/current derating",
        ),
    ),
)


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    failures: list[str] = []
    for check in NOTE_CHECKS:
        path = PART_NOTES_DIR / check.filename
        if not path.exists():
            failures.append(f"{check.filename}: missing part note")
            continue
        text = path.read_text()
        searchable = normalized(text)
        for phrase in check.required:
            if normalized(phrase) not in searchable:
                failures.append(f"{check.filename}: missing required phrase: {phrase}")
        for phrase in check.forbidden:
            if normalized(phrase) in searchable:
                failures.append(f"{check.filename}: contains forbidden stale phrase: {phrase}")

    if failures:
        print(f"FAIL part-note completeness: {len(failures)} checks failed")
        for failure in failures:
            print(f"  {failure}")
        return 1

    required_count = sum(len(check.required) for check in NOTE_CHECKS)
    forbidden_count = sum(len(check.forbidden) for check in NOTE_CHECKS)
    print(
        f"PASS part-note completeness: {len(NOTE_CHECKS)} notes, "
        f"{required_count} required phrases, {forbidden_count} stale-phrase guards"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
