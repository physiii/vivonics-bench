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
            "GPIO0/BOOT has a 10 k pull-up, 1 uF capacitor, and local PROG button",
            "EN has a 10 k pull-up, 1 uF POR/reset-delay capacitor",
            "`check_esp32_reset_boot_controls.py` asserts the exported U9/U10/Q5/Q6/SW1-SW3",
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
            "`check_tia_readout_budget.py` asserts this topology",
            "+1.40 uA / -0.70 uA",
            "optical signal range is still a production calibration blocker",
            "2026-07-07 re-audit found the previous local PCB footprint was mirrored",
            "`check_orientation_polarity_pcb.py` asserts the physical SOIC-8 pad order",
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
            "`check_laser_driver_control_loop.py` asserts the TLV9001 control loop",
            "`check_laser_driver_package_pcb.py` asserts the U5-U8 TLV9001 schematic pin",
            "hardware-clamp-gate-margin",
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
            "`check_laser_driver_package_pcb.py` asserts Q1-Q4 AO3400A gate/source/drain",
            "`check_laser_current_budget.py` checks the AO3400A dissipation",
            "`check_laser_driver_control_loop.py` checks AO3400A gate/source/drain",
            "available AO3400A gate-source drive",
            "per-channel analog command limits",
            "selected-diodes-typ-9v3",
            "selected-diodes-max-9v3",
            "selected-diodes-hardware-clamp-9v3",
        ),
    ),
    NoteCheck(
        "SFH2201.md",
        (
            "Pin 1 is cathode",
            "Pin 2 is anode",
            "Cathode is reverse-biased from +5 V through 1 kOhm",
            "Anode goes to the OPA380 inverting summing node",
            "1000 lx short-circuit-current example is 76 uA",
            "would require about 152 V of swing",
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
            "D6 anode receives onboard AP63205 `/POWER_IO/BUCK_5V`",
            "D5/D6 cathodes OR into `+5V`",
            "2026-07-04 order-source signoff",
            "MDD(Microdiode Semiconductor) `SS14`",
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
            "Connector identity is resolved",
            "Shield pad 6 ties to board GND",
            "Official Würth footprint/drawing source",
            "CP2102N VBUS sense uses the copied-sheet 22.1 k / 47.5 k divider",
            "`check_usb_vbus_interface.py --policy topology` asserts",
            "`check_usb_vbus_interface.py --policy connector-source-match` passes",
        ),
    ),
    NoteCheck(
        "3224W-1-103E.md",
        (
            "VBIAS trim element",
            "TIA feedback trim element",
            "wiper tied to the output side",
            "0.25 W at 85 C",
            "Pin/orientation signoff",
            "RV1-RV4 pad 2 on the `Net-(RVx-W)` VBIAS wiper",
            "2026-07-07 re-audit found RV5-RV8 mirrored",
            "`check_orientation_polarity_pcb.py` confirms RV1-RV8 physical Bourns 3224W",
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
            "Each channel is `MPD_RAWx -> 240R MPD sense -> MPD_BIAS`",
            "INA4180 `IN+x` connects to `MPD_RAWx`",
            "INA4180 `IN-x` connects to `MPD_BIAS`",
            "A1 gain option is `20 V/V`",
            "`OUT1..4` drive `MPD_AMP1..4`",
            "powered from `+3V3` with local `100nF` decoupling",
            "selected-monitor-typ-9v3",
            "selected-monitor-worst-9v3",
            "D7805I `600 uA` high-end monitor current maps",
            "`check_monitor_pd_package_pcb.py` asserts the U12 schematic pin nets",
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
            "selected-monitor typical case",
            "selected high-end case still leaves about `0.68 mA`",
            "`check_monitor_pd_package_pcb.py` asserts U13 cathode/anode/pin-3",
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
            "DB15/BYTE_SEL pin 33 is tied low",
            "RANGE pin 8 is tied low",
            "OS0/OS1/OS2 pins 3/4/5 are tied low",
            "REGCAP pins 36 and 39 each have a local 1 uF capacitor",
            "REFIN/REFOUT pin 42 has a local 10 uF capacitor",
            "REFCAPA pin 44 and REFCAPB pin 45 share a local 10 uF capacitor",
            "REFGND pins 43 and 46",
            "FRSTDATA pin 15 is intentionally no-connect",
            "C51-C60 AVCC/VDRIVE/REGCAP/reference capacitor",
            "`check_tia_readout_budget.py` asserts that the OPA380 guarded output window",
            "use two DOUT lines",
            "32 SCLK edges per DOUT line",
            "152.59 uV/LSB",
            "RESET high for at least 50 ns",
            "CONVST low and high",
            "`check_laser_controller_netlist.py` asserts the AD7606 package pinout",
            "`check_ad7606_package_pcb.py` asserts the U14 schematic pin nets",
            "`check_ad7606_interface_budget.py` asserts the hardware straps",
        ),
    ),
    NoteCheck(
        "AP63200-AP63205.md",
        (
            "`AP63205WU-7` is U15",
            "`AP63200WU-7` is U16",
            "TSOT-23-6 pin 1 is `FB`",
            "Pin 2 is `EN`",
            "Pin 3 is `IN`",
            "Pin 4 is `GND`",
            "Pin 5 is `SW`",
            "Pin 6 is `BST`",
            "`IN` and `EN` pins are tied to `VIN_24V`",
            "`check_ap6320x_package_pcb.py` asserts the exported U15/U16 schematic pin nets",
            "`0.8 V * (1 + 237k/22.1k) = 9.38 V`",
            "input range is `3.8 V` to `32 V`",
            "MWSA0503S-4R7MT",
            "WPN4020H100MT",
            "bench-selected-max-9v3",
            "hardware-clamp-9v3",
            "datasheet-recommended-components",
            "check_vin24_input_protection.py --policy production-protection",
            "no fuse/PTC/TVS/reverse-protection",
            "C61+C62 = `20uF`",
            "C64+C65 = `44uF`",
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
            "PLT5-style `150 uA` monitor current gives about `0.72 V`",
            "PLT5 450GB",
            "pin 1 = LD Anode",
            "pin 2 = Case",
            "pin 3 = LD Cathode",
            "Direct footprint `LD4` is `OptoDevice:LaserDiode_TO56-3`",
            "`MPD_RAW4` remains a spare/open monitor front-end input",
            "2026-07-04 direct-laser MPN/footprint signoff",
            "physical pin orientation",
            "`PLT5 450GB` has no monitor photodiode",
            "green PLT5 520EB_P is limited to about 76.2 mA",
            "selected-diodes-max-9v3",
            "selected-diodes-hardware-clamp-9v3",
            "run `check_laser_current_budget.py`",
        ),
    ),
    NoteCheck(
        "laser-harness-pin-code-compatibility.md",
        (
            "`LASER_V+ -> laser diode -> LASER_Nx -> AO3400A",
            "`MPD_RAWx -> 240R MPD sense -> MPD_BIAS`",
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
            "D6505I` is checked conservatively",
            "selected-diodes-typ-9v3",
            "selected-diodes-max-9v3",
            "selected-diodes-hardware-clamp-9v3",
            "`D7805I` monitor current is checked",
            "selected-monitor-typ-9v3",
            "selected-monitor-worst-9v3",
            "`MPD_RAW4` is spare/open unless a different blue source",
            "Do not connect PLT5 450GB case pin 2 to `MPD_RAW4`",
            "The 2026-07-04 direct-laser MPN/footprint signoff closes",
            "`check_laser_diode_footprints.py` asserts",
        ),
    ),
    NoteCheck(
        "passive-bom-source-note.md",
        (
            "Generated BOM",
            "value, footprint, `Part Number`, and `LCSC`",
            "10 ohm 2512 2 W laser sense resistors",
            "every assembled capacitor, resistor, and SMD trimmer MPN",
            "First-article passive AVL lock",
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
