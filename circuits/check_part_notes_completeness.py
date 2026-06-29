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
        "ESP32-S3-WROOM-1-N16.md",
        (
            "Real `Espressif:ESP32-S3-WROOM-1` symbol block",
            "GPIO19/pin 13 = D-",
            "GPIO20/pin 14 = D+",
            "`ISENSE1..4` on GPIO4/5/6/7",
            "`MPD1..4` on GPIO2/3/8/9",
            "GPIO0/BOOT has a pull-up and local PROG button",
            "EN has a pull-up and 100 nF",
            "module antenna keepout",
            "Wi-Fi/BLE disabled",
        ),
        (
            "inline `viv:ESP32S3`",
            "GPIO0/BOOT has a pull-up and is exposed on J2",
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
            "Feedback is a Bourns 3224W 2 M trimmer in parallel with 10 pF",
            "wiper tied to the OPA380 output side",
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
        "AO3400A.md",
        (
            "SOT-23 pin 1 = gate",
            "Pin 2 = source",
            "Pin 3 = drain",
            "linear low-side current-sink pass device",
            "Drain connects to the direct laser cathode net `LASER_Nx`",
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
            "Resolve the connector identity before fabrication",
            "Shield pad 6 ties to board GND",
        ),
    ),
    NoteCheck(
        "3224W-1-103E.md",
        (
            "VBIAS trim element",
            "TIA feedback trim element",
            "wiper tied to the output side",
            "0.25 W at 85 C",
            "Confirm the wiper orientation visually in Pcbnew",
            "Keep VBIAS routing quiet",
            "`check_passive_derating.py` checks the trimmer",
        ),
    ),
    NoteCheck(
        "INA4180A1IPWR.md",
        (
            "`INA4180A1IPWR` is the PW TSSOP-14 quad current-sense amplifier",
            "Pin 1 = `OUT1`",
            "pin 4 = `VS`",
            "pin 11 = `GND`",
            "Each channel is `MPD_RAWx -> 750R MPD sense -> MPD_BIAS`",
            "INA4180 `IN+x` connects to `MPD_RAWx`",
            "INA4180 `IN-x` connects to `MPD_BIAS`",
            "A1 gain option is `20 V/V`",
            "`OUT1..4` drive `MPD_AMP1..4`",
            "powered from `+3V3` with local `100nF` decoupling",
        ),
    ),
    NoteCheck(
        "LM4040C50IDBZR.md",
        (
            "`LM4040C50IDBZR` is the DBZ SOT-23-3 5.0 V shunt reference",
            "Pin 1 = cathode",
            "pin 2 = anode",
            "pin 3 = `*`",
            "holding `LASER_V+ - MPD_BIAS` near `5 V`",
            "U13 pin 1 cathode connects to `LASER_V+`",
            "U13 pin 2 anode and pin 3 `*` connect to `MPD_BIAS`",
            "R41 is the `2.49k MPD bias` sink",
            "C36 is the `100nF MPD bias` local capacitor",
            "four PLT5-style channels at `150 uA` monitor current",
        ),
    ),
    NoteCheck(
        "AD7606BSTZ-4RL.md",
        (
            "`AD7606BSTZ-4RL` is the LQFP-64 4-channel option used as U14",
            "V1/V2/V3/V4 pins 49/51/57/59 connect to `VOUT1..4`",
            "CONVSTA pin 9 and CONVSTB pin 10 are tied together on `CONVST`",
            "RD/SCLK pin 12 connects to ESP32 GPIO17 as `ADC_SCLK`",
            "CS pin 13 connects to ESP32 GPIO18 as `ADC_CS`",
            "DOUTA pin 24 connects to ESP32 GPIO21 as `ADC_MISO_A`",
            "DOUTB pin 25 connects to ESP32 GPIO38 as `ADC_MISO_B`",
            "BUSY pin 14 connects to ESP32 GPIO47 as `ADC_BUSY`",
            "RESET pin 11 connects to ESP32 GPIO48 as `ADC_RESET`",
            "AVCC pins 1, 37, 38, and 48 connect to +5 V",
            "VDRIVE pin 23 connects to +3V3",
            "PAR/SER/BYTE_SEL pin 6 is tied high for serial mode",
            "RANGE pin 8 is tied low",
            "OS0/OS1/OS2 pins 3/4/5 are tied low",
            "REGCAP pins 36 and 39 each have a local 1 uF capacitor",
            "REFIN/REFOUT pin 42 has a local 10 uF capacitor",
            "REFCAPA pin 44 and REFCAPB pin 45 share a local 10 uF capacitor",
            "REFGND pins 43 and 46",
            "FRSTDATA pin 15 is intentionally no-connect",
            "`check_laser_controller_netlist.py` asserts the AD7606 package pinout",
        ),
    ),
    NoteCheck(
        "PLT5-520B-harness-reference.md",
        (
            "PLT5 520EB_P",
            "pin 1 = LD Cathode",
            "pin 2 = LD Anode, PD",
            "pin 3 = PD Anode",
            "one monitor-PD anode",
            "direct `LDx` through-hole footprints expose the same",
            "Direct footprint `LD3` is `OptoDevice:LaserDiode_TO56-3`",
            "PLT5 520EB_P monitor current is specified at `VRPD = 5 V`",
            "high-side INA4180/LM4040 monitor front end",
            "PLT5-style `150 uA` monitor current gives about `2.25 V`",
            "PLT5 450GB",
            "pin 1 = LD Anode",
            "pin 2 = Case",
            "pin 3 = LD Cathode",
            "Direct footprint `LD4` is `OptoDevice:LaserDiode_TO56-3`",
            "`MPD_RAW4` remains a spare/open monitor front-end input",
            "Every actual laser MPN must be checked against its own pin table",
            "`PLT5 450GB` has no monitor photodiode",
            "run `check_laser_current_budget.py`",
        ),
    ),
    NoteCheck(
        "laser-harness-pin-code-compatibility.md",
        (
            "`LASER_V+ -> laser diode -> LASER_Nx -> AO3400A",
            "`MPD_RAWx -> 750R MPD sense -> MPD_BIAS`",
            "INA4180A1 gain 20",
            "`LM4040C50` holds `LASER_V+ - MPD_BIAS` near `5 V`",
            "monitor photodiode cathode at the laser common high node",
            "IR `D7805I`, Digikey `38-1028-ND`",
            "Red `D6505I`, Digikey `38-1007-ND`",
            "Green `PLT5 520EB_P`, Digikey `475-PLT5520EB_P-ND`",
            "Blue `PLT5 450GB`, Digikey `475-PLT5450GB-ND`",
            "Direct footprint `LD1` is",
            "Direct footprint `LD2` is",
            "Direct footprint `LD3` is `OptoDevice:LaserDiode_TO56-3`",
            "old laser/MPD harness header is removed",
            "`MPD_RAW4` is spare/open unless a different blue source",
            "Do not connect PLT5 450GB case pin 2 to `MPD_RAW4`",
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
