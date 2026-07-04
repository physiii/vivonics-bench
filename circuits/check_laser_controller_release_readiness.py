#!/usr/bin/env python3
"""Track open fabrication/release blockers for the bench laser controller.

Exit codes:
  0: no open blockers are registered
  1: blocker registry evidence is inconsistent with the repo docs
  2: one or more known blockers remain open

This is not another electrical-rule checker. It makes the unresolved manual,
source, direct-laser, thermal, and manufacturing checks visible in the same wrapper
as the generated schematic and PCB gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Evidence:
    path: str
    phrases: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseBlocker:
    blocker_id: str
    title: str
    detail: str
    required_action: str
    evidence: tuple[Evidence, ...]


BLOCKERS: tuple[ReleaseBlocker, ...] = (
    ReleaseBlocker(
        "KICAD_ERC_DRC_ZONE_SIGNOFF",
        "KiCad ERC and schematic-parity signoff are still open",
        "Available netlist/source/custom PCB checks pass, and a 2026-07-04 GUI DRC screenshot captures refilled-zone DRC with 0 violations and 0 unconnected items. Full fabrication signoff is still not proven because this KiCad 7.0.11 CLI only exposes sch/pcb export commands, not ERC/DRC, and the captured GUI DRC did not run schematic parity. Formal KiCad ERC and native schematic-parity evidence remain unproven.",
        "Run GUI ERC on the regenerated schematic, update PCB from schematic, refill zones, run PCB DRC with schematic parity, or use a KiCad CLI build that supports sch erc and pcb drc, then document any waivers/reports.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-04-kicad-drc-zero-violations.md",
                (
                    "Violations (0)",
                    "Unconnected Items (0)",
                    "Schematic Parity (not run)",
                    "partial CAD signoff only",
                ),
            ),
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "GUI ERC passes on the generated unique-reference schematic.",
                    "Zones are refilled in KiCad.",
                    "PCB DRC with schematic parity passes.",
                ),
            ),
            Evidence(
                "circuits/PCB_LAYOUT.md",
                (
                    "Run **DRC** with refilled zones and schematic parity",
                    "File \u2192 Fabrication Outputs \u2192 Gerbers + Drill",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "VISUAL_RETURN_PATH_REVIEW",
        "GND and sensitive return paths need visual review after zone refill",
        "The graph proves pads are connected, not that laser current, USB ESD, ESP32, and TIA returns have acceptable real copper paths.",
        "After KiCad zone refill, inspect GND islands/stitching and keep laser-current returns away from TIA summing-node return paths.",
        (
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "Mixed analog, digital, USB ESD, buck-switching, and laser-current returns share this net",
                    "`GND` has a visually reviewed return path after zone refill.",
                    "keep laser current return out of TIA summing-node return path.",
                ),
            ),
            Evidence(
                "circuits/PCB_LAYOUT.md",
                (
                    "visual return-path review",
                    "cluster is still a visual review item.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "ACTUAL_LASER_MPN_DIRECT_FOOTPRINT",
        "Actual laser MPN pin tables and direct footprints are not released",
        "The Digikey cart MPNs have mixed pin-code behavior: D7805I, D6505I, and PLT5 520EB_P match the bench monitor front end, while PLT5 450GB has no monitor photodiode and its case pin must not be tied into MPD_RAW4.",
        "Verify the exact per-MPN pin table against the direct LDx footprint wiring, inspect can/case handling, and document that PLT5 450GB has no MPD telemetry before laser bring-up.",
        (
            Evidence(
                "docs/part-notes/PLT5-520B-harness-reference.md",
                (
                    "Every actual laser MPN must be checked against its own pin table",
                    "`PLT5 450GB` has no monitor photodiode",
                ),
            ),
            Evidence(
                "docs/part-notes/laser-harness-pin-code-compatibility.md",
                (
                    "IR `D7805I`, Digikey `38-1028-ND`",
                    "Blue `PLT5 450GB`, Digikey `475-PLT5450GB-ND`",
                    "Do not connect PLT5 450GB case pin 2 to `MPD_RAW4`",
                ),
            ),
            Evidence(
                "circuits/PCB_LAYOUT.md",
                (
                    "confirm every raw laser MPN's LD/PD/common/case pin table",
                    "actual laser direct-footprint MPN review",
                    "PLT5 450GB",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "D7805I",
                    "PLT5 450GB has no monitor photodiode",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "MONITOR_PD_FRONTEND_RANGE_CALIBRATION",
        "Monitor-PD front-end range and calibration are not released",
        "The exported netlist now proves the INA4180/LM4040 monitor topology is connected as intended, and the 240R/gain20 monitor scale covers the captured D7805I/D6505I/PLT5 520EB_P monitor-current range inside the local ADC-headroom guard. PLT5 450GB has no monitor photodiode, so MPD4 is not blue-source telemetry. Optical calibration and safety behavior are still unreleased.",
        "Calibrate each source against an external optical meter and define firmware behavior for MPD telemetry before using it for production APC, normalization, or safety decisions.",
        (
            Evidence(
                "docs/part-notes/INA4180A1IPWR.md",
                (
                    "selected-monitor-typ-9v3",
                    "selected-monitor-worst-9v3",
                    "`600 uA` high-end monitor current maps",
                ),
            ),
            Evidence(
                "docs/part-notes/laser-harness-pin-code-compatibility.md",
                (
                    "`D7805I` monitor current is checked",
                    "selected-monitor-worst-9v3",
                    "MPD still needs optical calibration",
                ),
            ),
            Evidence(
                "circuits/README.md",
                (
                    "D7805I max maps to about 2.88 V",
                    "Selected blue diode `PLT5 450GB` has no monitor",
                    "MPD_RAW4` / `MPD4` is spare/open",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "D7805I 600 uA high-end monitor current maps to about 2.88 V",
                    "It still cannot read monitor telemetry",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "TIA_READOUT_RANGE_CALIBRATION",
        "Signal-PD TIA readout range and optical calibration are not released",
        "The exported netlist now proves the four SFH2201/OPA380 signal-PD channels feed VOUT1..4 into the AD7606 as intended, and the first-order TIA checker shows the present 2 MOhm feedback trim is a high-sensitivity, low-current bench range. At VBIAS = 1.5 V it has about +1.40 uA / -0.70 uA one-sided OPA380 headroom before the guarded output window clips; the SFH2201 1000 lx datasheet short-circuit-current example would need about 152 V of TIA swing at 2 MOhm and is intentionally an expected-fail case.",
        "Define the real Vivonics optical photocurrent range at the SFH2201 under the bench optics, choose RF/VBIAS/firmware scaling for that range, shield or limit ambient light, and calibrate AD7606 counts against known optical/electrical inputs before using the signal-PD path for production measurements.",
        (
            Evidence(
                "docs/part-notes/OPA380AID.md",
                (
                    "`check_tia_readout_budget.py` asserts",
                    "+1.40 uA / -0.70 uA",
                    "optical signal range is still a production calibration blocker",
                ),
            ),
            Evidence(
                "circuits/README.md",
                (
                    "check_tia_readout_budget.py",
                    "+1.40 uA / -0.70 uA",
                    "TIA readout range and optical calibration remain release blockers",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "check_tia_readout_budget.py",
                    "SFH2201 1000 lx short-circuit-current example",
                    "Define the real Vivonics optical photocurrent range",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "PER_DIODE_LASER_THERMAL_BUDGET",
        "Per-diode laser current and heat budget is still open",
        "The selected-diode policies keep the old 10.72 V common rail as an expected-fail comparison for PLT5 450GB at typical current, while the 247.5 mA hardware clamp exceeds every selected laser MPN operating-current maximum.",
        "Lower/rework LASER_V+ or use per-channel drivers, enforce real per-diode current limits before firmware can command the clamp, then measure driver/sense-resistor temperature and optical output during bring-up.",
        (
            Evidence(
                "circuits/LASER_CURRENT_THERMAL_BUDGET.md",
                (
                    "selected-diodes-typ-10v72",
                    "selected-diodes-max-9v3",
                    "selected-diodes-hardware-clamp-10v72",
                    "Use per-channel laser driver/APC topology or per-channel supply/headroom",
                ),
            ),
            Evidence(
                "docs/part-notes/PLT5-520B-harness-reference.md",
                (
                    "fails the conservative continuous AO3400A thermal budget for PLT5 450GB",
                    "Do not let the analog command path or firmware reach the 247.5 mA hardware",
                ),
            ),
            Evidence(
                "docs/part-notes/laser-harness-pin-code-compatibility.md",
                (
                    "selected-diodes-typ-10v72",
                    "selected-diodes-max-9v3",
                    "selected-diodes-hardware-clamp-10v72",
                ),
            ),
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "Each selected diode and `LASER_V+` setting passes the laser current thermal budget.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE",
        "AP2112 bench thermal measurement and production regulator decision are open",
        "The AP2112 is acceptable only for the bench no-RF policy. Sustained ESP32 wireless load fails the current SOT25 LDO budget.",
        "Measure AP2112 package temperature and +3V3 current during bring-up, keep RF disabled for this bench board, or replace the rail before sustained Wi-Fi/BLE.",
        (
            Evidence(
                "circuits/POWER_THERMAL_BUDGET.md",
                (
                    "Measure AP2112 package temperature and +3V3 rail current during first bring-up.",
                    "Replace the SOT25 AP2112 rail with a buck regulator",
                ),
            ),
            Evidence(
                "docs/part-notes/AP2112K-3.3TRG1.md",
                (
                    "temperature result proves more margin.",
                    "Production or sustained Wi-Fi/BLE use should replace this rail with a buck",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT",
        "24 V barrel/RJ45 input protection and buck layout are not released",
        "J5 barrel and J6 RJ45 inputs plus the U15/U16 buck supplies are accepted for bench use only with a selected current-limited adapter and reviewed switch-loop/thermal layout. The VIN24 checker proves the current bench topology is direct J5/J6 to U15/U16 input wiring and intentionally fails production protection because there is no fuse/PTC/TVS/reverse-protection/eFuse/hot-swap component. The AP632 checker passes the selected-diode 9.3 V max-current reference, but the 9.3 V all-channel hardware-clamp case exceeds the 500 mA J5 input budget and the current C64+C65/C67+C68 output capacitor set is below generic AP632 datasheet guidance.",
        "Define the adapter current limit, RJ45 harness current limit, fuse/current-limit element, reverse-polarity strategy, and transient/TVS protection; rework or justify the AP632 output capacitors; then verify AP63205/AP63200 switch-loop routing, copper width, output ripple/transient/stability, and temperature before production.",
        (
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "check_vin24_input_protection.py --policy bench-topology",
                    "production-protection",
                    "no fuse/PTC/TVS/reverse-protection/eFuse stage",
                    "bench-selected-max-9v3",
                    "hardware-clamp-9v3",
                    "datasheet-recommended-components",
                    "C61+C62 now provide 20 uF nominal VIN ceramic",
                ),
            ),
            Evidence(
                "docs/part-notes/AP63200-AP63205.md",
                (
                    "check_vin24_input_protection.py --policy production-protection",
                    "no fuse/PTC/TVS/reverse-protection",
                    "C61+C62 = `20uF`",
                    "`2x22uF` style output capacitance",
                    "input range is `3.8 V` to `32 V`",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "SS14_EXACT_ORDER_DATASHEET",
        "Exact SS14 C2480 manufacturer datasheet and polarity are still order-time checks",
        "The schematic and board assert diode polarity, but the source register still relies on distributor/order evidence plus a family reference.",
        "Confirm the exact C2480 manufacturer datasheet, package polarity, and orderable part before board order.",
        (
            Evidence(
                "docs/part-notes/SS14.md",
                (
                    "Confirm exact C2480 manufacturer datasheet and polarity at order.",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "the exact C2480 manufacturer datasheet should be rechecked at order time.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "BOURNS_TRIMMER_WIPER_VISUAL",
        "Bourns trimmer wiper orientation still needs visual PCB signoff",
        "The schematic and netlist bound the VBIAS range, but the production board still needs a human pin-1/wiper orientation check.",
        "Open the PCB in Pcbnew and verify RV1-RV4 pin-1/wiper orientation against the Bourns 3224 drawing before fabrication.",
        (
            Evidence(
                "docs/part-notes/3224W-1-103E.md",
                (
                    "Confirm the wiper orientation visually in Pcbnew before fabrication.",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "verify pin/wiper orientation visually in PCB before order.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "PASSIVE_PRODUCTION_AVL_AND_DERATING",
        "Production passive AVL, pulse/surge derating, and temperature evidence are open",
        "The current derating gate covers bench steady-state voltage and power, not lifecycle, surge, pulse, or production procurement lock.",
        "Create a production procurement lock with final orderable passive datasheets, lifecycle/AVL state, pulse/surge/current derating, and board-temperature evidence.",
        (
            Evidence(
                "docs/part-notes/passive-bom-source-note.md",
                (
                    "Production still needs a procurement lock file",
                    "pulse/surge/current derating",
                    "board-temperature measurement.",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "Production still needs",
                    "pulse/surge/current derating",
                    "board-temperature evidence.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "AD7606_SYSTEM_INTERFACE",
        "On-board AD7606 firmware and bench-readout validation are still open",
        "The bench board routes VOUT1..4 into the on-board AD7606 and the hardware straps now have a checked 10 MHz / 100 kSPS default interface budget, but firmware implementation, timing on the real ESP32, scaling, and bench ADC readback remain system-level checks.",
        "Implement and scope the ESP32 AD7606 driver, verify RESET/CONVST/BUSY/CS/SCLK timing, confirm +/-5 V range scaling and oversampling assumptions in firmware, and compare readings against known optical/electrical inputs before relying on bench data.",
        (
            Evidence(
                "circuits/README.md",
                (
                    "U14 straps `RANGE` low",
                    "oversampling. Confirm ESP32 timing",
                ),
            ),
            Evidence(
                "docs/part-notes/AD7606BSTZ-4RL.md",
                (
                    "`check_ad7606_interface_budget.py` asserts the hardware straps",
                    "default to 100 kSPS or lower",
                    "152.58 uV/LSB",
                ),
            ),
        ),
    ),
)


def validate_evidence() -> list[str]:
    failures: list[str] = []
    for blocker in BLOCKERS:
        for evidence in blocker.evidence:
            path = REPO_DIR / evidence.path
            if not path.exists():
                failures.append(f"{blocker.blocker_id}: missing evidence file {evidence.path}")
                continue
            text = path.read_text()
            for phrase in evidence.phrases:
                if phrase not in text:
                    failures.append(
                        f"{blocker.blocker_id}: {evidence.path} missing evidence phrase: {phrase}"
                    )
    return failures


def main() -> int:
    failures = validate_evidence()
    if failures:
        print(f"FAIL release-readiness blocker registry: {len(failures)} evidence checks failed")
        for failure in failures:
            print(f"  {failure}")
        return 1

    if not BLOCKERS:
        print("PASS release readiness: no open blockers registered")
        return 0

    print(f"BLOCKED release readiness: {len(BLOCKERS)} open fabrication/release blockers")
    for blocker in BLOCKERS:
        print(f"  [{blocker.blocker_id}] {blocker.title}")
        print(f"    Detail: {blocker.detail}")
        print(f"    Required action: {blocker.required_action}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
