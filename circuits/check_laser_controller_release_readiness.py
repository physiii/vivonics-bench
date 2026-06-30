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
        "GENERATED_COPPER_NETCLASS_CLEARANCE",
        "PCB placement, routing, and rail/zone signoff remain open",
        "The current PCB artifact has recovered hand-placement coordinates and pad nets, not a routed fabrication layout. The PCB checker still fails while final board-boundary/proximity limits are not met, USB routes are missing, no filled In1.Cu GND reference plane exists, and routing is absent. The generated-copper release gate also fails because signal/control multi-pad nets, rails, pours, laser-anode copper, and high-current laser sense returns are not routed.",
        "Finish placement inside the 90 x 50 mm outline, route USB/signal/control nets, add and refill rail/GND zones, add reviewed laser-current and high-current GND return copper, run PCB DRC with schematic parity, and review +5V/GND rail and return-path copper before fabrication.",
        (
            Evidence(
                "circuits/README.md",
                (
                    "The current board artifact is not routed",
                    "`check_laser_controller_pcb.py` currently fails",
                    "release gate also fails because signal/control",
                ),
            ),
            Evidence(
                "circuits/PCB_LAYOUT.md",
                (
                    "160 physical footprints match the schematic reference set",
                    "Current blocker: the PCB is not release-clean",
                    "The custom PCB and generated-copper release gates do not pass",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "KICAD_ERC_DRC_ZONE_SIGNOFF",
        "KiCad ERC, zone refill, and DRC signoff are still open",
        "Available netlist/source checks pass, but the current generated PCB is not release-clean and this KiCad 7.0.11 CLI only exposes sch/pcb export commands, not ERC/DRC. Formal KiCad ERC, refilled-zone copper, and board-rule DRC remain unproven.",
        "Run GUI ERC on the regenerated schematic, update PCB from schematic, refill zones, run PCB DRC with schematic parity, or use a KiCad CLI build that supports sch erc and pcb drc, then document any waivers.",
        (
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
        "PER_DIODE_LASER_THERMAL_BUDGET",
        "Per-diode laser current and heat budget is still open",
        "A single LASER_V+ rail can be safe for one diode class and unsafe for another because AO3400A heat is set by rail headroom.",
        "Run the laser-current budget for every selected diode, intended LASER_V+, current setpoint, and duty cycle; measure driver/sense-resistor temperature during bring-up.",
        (
            Evidence(
                "circuits/LASER_CURRENT_THERMAL_BUDGET.md",
                (
                    "Set `LASER_V+` from the actual diode forward-voltage table",
                    "Do not run all four colors at the clamp from one high rail without thermal",
                    "Use per-channel laser driver/APC topology or per-channel supply/headroom",
                ),
            ),
            Evidence(
                "docs/part-notes/PLT5-520B-harness-reference.md",
                (
                    "For every actual laser MPN, run `check_laser_current_budget.py`",
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
        "J5 barrel and J6 RJ45 inputs plus the U15/U16 buck supplies are accepted for bench use only with a selected current-limited adapter and reviewed switch-loop/thermal layout.",
        "Define the adapter current limit, RJ45 harness current limit, and input protection, then verify AP63205/AP63200 switch-loop routing, copper width, and temperature before production.",
        (
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "Select the adapter current limit",
                    "AP63205/AP63200 buck placement, switch-loop routing, thermal behavior",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "USB_CONNECTOR_OFFICIAL_DRAWING",
        "Official current Wuerth USB connector drawing still needs release verification",
        "The design uses a local KiCad footprint and a distributor mirror because the official exact drawing was not reachable from this shell.",
        "Verify the current 65100516121 manufacturer drawing, pin order, shield pads, and footprint orientation before fabrication.",
        (
            Evidence(
                "docs/part-notes/65100516121.md",
                (
                    "Resolve the connector identity before fabrication",
                    "orderable connector must be mechanically checked",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "Mini-B orderable connector identity must be resolved before release",
                    "mechanical fit and ordering source still need signoff",
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
        "MANUFACTURING_CLASS_AND_FAB_TIER",
        "Manufacturing class, fab tier, and release package constraints are not selected",
        "The generated geometry is conservative, but IPC/J-STD class, final fabricator settings, and order-tier constraints are still not locked.",
        "Select IPC/J-STD class, fab tier, stackup/rule settings, assembly assumptions, and release notes before ordering.",
        (
            Evidence(
                "docs/source-register.md",
                (
                    "IPC/J-STD class and final fabricator order tier are not selected.",
                    "board setup and release notes still",
                ),
            ),
            Evidence(
                "circuits/PCB_LAYOUT.md",
                (
                    "File \u2192 Fabrication Outputs \u2192 Gerbers + Drill",
                    "only after ERC, DRC, rail review, and visual return-path review pass.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "AD7606_SYSTEM_INTERFACE",
        "On-board AD7606 range and firmware assumptions are still open",
        "The bench board routes VOUT1..4 into the on-board AD7606 and connects its serial/control interface to the ESP32, but range, timing, oversampling, and firmware configuration remain system-level checks.",
        "Verify the AD7606 variant/range pin, firmware timing, oversampling straps, and expected input range before relying on bench readings.",
        (
            Evidence(
                "circuits/README.md",
                (
                    "U14 straps `RANGE` low",
                    "oversampling. Confirm ESP32 timing",
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
