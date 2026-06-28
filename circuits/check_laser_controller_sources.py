#!/usr/bin/env python3
"""Source-register coverage checks for the generated bench laser controller.

Run after:
  kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net
"""
from __future__ import annotations

import sys
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from generate_laser_controller_audit_tables import intent_for_net, pin_intent_for_node


PROJECT_DIR = Path(__file__).resolve().parent
REPO_DIR = PROJECT_DIR.parent
SOURCE_REGISTER = REPO_DIR / "docs" / "source-register.md"
PART_NOTES_DIR = REPO_DIR / "docs" / "part-notes"


CRITICAL_PART_NOTES = [
    "ESP32-S3-WROOM-1-N16.md",
    "OPA380AID.md",
    "TLV9001IDBVR.md",
    "AP2112K-3.3TRG1.md",
    "USBLC6-2SC6.md",
    "AO3400A.md",
    "SFH2201.md",
    "SS14.md",
    "65100516121.md",
    "3224W-1-103E.md",
    "INA4180A1IPWR.md",
    "LM4040C50IDBZR.md",
    "PLT5-520B-harness-reference.md",
    "laser-harness-pin-code-compatibility.md",
    "passive-bom-source-note.md",
]

DOCUMENTATION_DESIGNATOR_GUARDS = [
    (
        SOURCE_REGISTER,
        [
            "| ST `USBLC6-2SC6`, LCSC `C7519` | U10 |",
            "| Diodes Inc. `AP2112K-3.3TRG1`, LCSC `C51118` | U11 |",
            "| Würth `65100516121` Mini-B, LCSC `C5120592` | J1 |",
        ],
        [
            "| ST `USBLC6-2SC6`, LCSC `C7519` | U12 |",
            "| Diodes Inc. `AP2112K-3.3TRG1`, LCSC `C51118` | U10 |",
        ],
    ),
    (
        PROJECT_DIR / "review" / "2026-06-25_datasheet_pin_matrix.md",
        [
            "| USB Mini-B `J1` |",
            "| USBLC6 `U10` |",
            "| AP2112K-3.3 `U11` |",
            "| SS14 `D5/D6` |",
        ],
        [
            "| USB Mini-B `J6` |",
            "| USBLC6 `U12` |",
            "| AP2112K-3.3 `U10` |",
            "| SS14 `D10/D11` |",
        ],
    ),
    (
        PROJECT_DIR / "README.md",
        [
            "| U10 | USBLC6-2SC6",
            "| U11 | AP2112K-3.3",
            "| J1 | USB Mini-B receptacle",
            "| J2 | 1×05 THT header",
            "| J6 | 1×02 THT header | external +5V in.",
        ],
        [
            "| U12 | USBLC6-2SC6",
            "| U10 | AP2112K-3.3",
            "| J6 | USB Mini-B receptacle",
        ],
    ),
    (
        PART_NOTES_DIR / "ESP32-S3-WROOM-1-N16.md",
        [
            "GPIO0/BOOT has a pull-up and is exposed on J2",
        ],
        [
            "GPIO0/BOOT has a pull-up and is exposed on J3",
        ],
    ),
]


def main() -> int:
    netlist_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lc.net")
    failures: list[str] = []

    if not SOURCE_REGISTER.exists():
        failures.append(f"missing source register: {SOURCE_REGISTER}")
        register_text = ""
    else:
        register_text = SOURCE_REGISTER.read_text()

    part_note_text = ""
    for note in CRITICAL_PART_NOTES:
        path = PART_NOTES_DIR / note
        if not path.exists():
            failures.append(f"missing part note: {path}")
            continue
        part_note_text += "\n" + path.read_text()

    searchable = register_text + "\n" + part_note_text
    comps = parse_components(netlist_path)
    nets = parse_netlist(netlist_path)
    comp_by_ref = {comp["ref"]: comp for comp in comps}
    sourced: dict[str, set[str]] = {}
    for comp in comps:
        for field in ("mpn", "lcsc"):
            value = comp.get(field, "")
            if value:
                sourced.setdefault(value, set()).add(comp["ref"])

    for token, refs in sorted(sourced.items()):
        if token not in searchable:
            failures.append(f"{token} from {', '.join(sorted(refs))} is not represented in docs/source-register.md or docs/part-notes")

    missing_net_intent = [
        net
        for net, nodes in sorted(nets.items())
        if intent_for_net(net, nodes).startswith("Review required:")
    ]
    if missing_net_intent:
        failures.append(
            "exported nets without a specific intent mapping: "
            + ", ".join(missing_net_intent)
        )

    missing_pin_intent = []
    for net, nodes in sorted(nets.items()):
        for ref, pin, function, pintype in nodes:
            role = pin_intent_for_node(net, ref, pin, function, pintype, comp_by_ref.get(ref))
            if role.startswith("Review required:"):
                missing_pin_intent.append(f"{ref}.{pin} on {net}: {role}")
    if missing_pin_intent:
        failures.append(
            "exported component pins without a specific pin-intent mapping: "
            + "; ".join(missing_pin_intent[:40])
            + (f"; ... {len(missing_pin_intent) - 40} more" if len(missing_pin_intent) > 40 else "")
        )

    for required in [
        "JLCPCB PCB capabilities",
        "Espressif",
        "Texas Instruments",
        "ams OSRAM",
        "Diodes",
        "ST",
        "Alpha & Omega",
        "Bourns",
        "Würth",
        "Official Würth product-data URL",
        "Commodity passive voltage ratings",
        "AP2112 3V3 rail thermal policy",
        "sustained Wi-Fi/BLE",
        "Laser current-loop thermal policy",
        "common high `LASER_V+` rail",
        "D7805I",
        "D6505I",
        "PLT5 520EB_P",
        "PLT5 450GB",
        "no monitor photodiode",
        "MPD_RAW4",
        "Part-note completeness guardrail",
        "Review/CI wrapper",
    ]:
        if required not in searchable:
            failures.append(f"required source/risk phrase missing: {required}")

    for path, required_phrases, forbidden_phrases in DOCUMENTATION_DESIGNATOR_GUARDS:
        if not path.exists():
            failures.append(f"missing documentation designator guard target: {path}")
            continue
        text = path.read_text()
        for phrase in required_phrases:
            if phrase not in text:
                failures.append(f"{path} missing required final designator phrase: {phrase}")
        for phrase in forbidden_phrases:
            if phrase in text:
                failures.append(f"{path} contains stale local/wrong designator phrase: {phrase}")

    if failures:
        print(f"FAIL {len(failures)} source-register coverage checks")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        f"PASS source-register coverage for {len(sourced)} MPN/LCSC tokens across "
        f"{len(comps)} components, intent coverage for {len(nets)} exported nets, "
        f"{sum(len(nodes) for nodes in nets.values())} component-pin intent roles, "
        f"and {len(DOCUMENTATION_DESIGNATOR_GUARDS)} documentation designator guard files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
