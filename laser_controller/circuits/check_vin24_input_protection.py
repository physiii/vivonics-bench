#!/usr/bin/env python3
"""VIN_24V input topology and production-protection policy checks.

This checker separates two questions:

* Is the current bench 24 V input topology wired as documented?
* Is that topology acceptable as a production power input?

The current schematic intentionally passes the first question and fails the
second.  J5/J6 feed VIN_24V directly into the AP63205/AP63200 buck inputs with
no fuse, TVS, reverse-polarity element, or defined harness/adaptor current limit
encoded in the schematic.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from circuit_designators import ref_for


DEFAULT_NETLIST = Path("/tmp/lc.net")
REPO_DIR = Path(__file__).resolve().parent.parent
BENCH_SIGNOFF = REPO_DIR / "circuits" / "review" / "signoff" / "2026-07-05-vin24-bench-input-signoff.md"
VIN_NOMINAL_V = 24.0
AP632_VIN_MAX_V = 32.0
BARREL_RATING_V = 30.0
BARREL_RATING_A = 0.5
RJ45_OPERATING_TEMP = "0C..70C"


def component_map(path: Path) -> dict[str, dict[str, str]]:
    return {comp["ref"]: comp for comp in parse_components(path)}


def node_map(path: Path) -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    for net_name, nodes in parse_netlist(path).items():
        for ref, pin, _, _ in nodes:
            mapping[(ref, pin)] = net_name
    return mapping


def require_component(
    failures: list[str],
    comps: dict[str, dict[str, str]],
    ref: str,
    *,
    value: str,
    footprint: str,
    mpn: str,
    lcsc: str,
) -> None:
    comp = comps.get(ref)
    if comp is None:
        failures.append(f"{ref}: missing component")
        return
    expected = {"value": value, "footprint": footprint, "mpn": mpn, "lcsc": lcsc}
    actual = {key: comp.get(key, "") for key in expected}
    if actual != expected:
        failures.append(f"{ref}: expected {expected}, got {actual}")


def require_net(
    failures: list[str],
    pins: dict[tuple[str, str], str],
    ref: str,
    pin: str,
    expected: str,
) -> None:
    actual = pins.get((ref, pin))
    if actual != expected:
        failures.append(f"{ref}.{pin}: expected {expected}, got {actual or '<missing>'}")


def validate_current_topology(netlist_path: Path) -> list[str]:
    failures: list[str] = []
    comps = component_map(netlist_path)
    pins = node_map(netlist_path)

    j5 = ref_for("POWER_IO", "JDC")
    j6 = ref_for("POWER_IO", "JRJ45")
    u15 = ref_for("POWER_IO", "U5V")
    u16 = ref_for("POWER_IO", "ULASER")

    require_component(
        failures,
        comps,
        j5,
        value="24V DC IN",
        footprint="Open_Automation:BarrelJack_OD5.5_ID2.5",
        mpn="DC-470-2.1GP",
        lcsc="C194407",
    )
    require_component(
        failures,
        comps,
        j6,
        value="CONN_RJ45",
        footprint="Connector_RJ:RJ45_Amphenol_RJHSE538X",
        mpn="R-RJ45R08P-C000",
        lcsc="C386757",
    )
    require_component(
        failures,
        comps,
        u15,
        value="AP63205WU-7 5V BUCK",
        footprint="Package_TO_SOT_SMD:TSOT-23-6",
        mpn="AP63205WU-7",
        lcsc="C2071056",
    )
    require_component(
        failures,
        comps,
        u16,
        value="AP63200WU-7 9.3V BUCK",
        footprint="Package_TO_SOT_SMD:TSOT-23-6",
        mpn="AP63200WU-7",
        lcsc="C2071868",
    )

    for ref, pin in [
        (j5, "1"),
        (j6, "4"),
        (j6, "5"),
        (u15, "2"),
        (u15, "3"),
        (u16, "2"),
        (u16, "3"),
        (ref_for("POWER_IO", "CIN24A"), "1"),
        (ref_for("POWER_IO", "CIN24B"), "1"),
        (ref_for("POWER_IO", "CIN24BULK"), "1"),
        (ref_for("POWER_IO", "RJR45PWR"), "1"),
    ]:
        require_net(failures, pins, ref, pin, "VIN_24V")

    for ref, pin in [
        (j5, "2"),
        (j5, "3"),
        (j6, "7"),
        (j6, "8"),
        (j6, "9"),
        (j6, "11"),
        (u15, "4"),
        (u16, "4"),
        (ref_for("POWER_IO", "CIN24A"), "2"),
        (ref_for("POWER_IO", "CIN24B"), "2"),
        (ref_for("POWER_IO", "CIN24BULK"), "2"),
    ]:
        require_net(failures, pins, ref, pin, "GND")

    require_net(failures, pins, ref_for("POWER_IO", "RJR45LED"), "1", "+3V3")
    require_net(failures, pins, ref_for("POWER_IO", "RJR45PWR"), "2", "/POWER_IO/RJ45_PWR_DETECT")
    require_net(failures, pins, ref_for("POWER_IO", "RJR45LED"), "2", "/POWER_IO/RJ45_LED_CONTACT")
    return failures


def likely_protection_components(comps: dict[str, dict[str, str]]) -> list[str]:
    tokens = (
        "fuse",
        "ptc",
        "polyfuse",
        "tvs",
        "transient",
        "suppressor",
        "reverse",
        "ideal diode",
        "efuse",
        "hot swap",
    )
    matches: list[str] = []
    for ref, comp in sorted(comps.items()):
        text = " ".join(
            [
                ref,
                comp.get("value", ""),
                comp.get("mpn", ""),
                comp.get("footprint", ""),
            ]
        ).lower()
        if any(token in text for token in tokens):
            matches.append(ref)
    return matches


def production_policy_failures(netlist_path: Path) -> list[str]:
    failures = validate_current_topology(netlist_path)
    comps = component_map(netlist_path)
    pins = node_map(netlist_path)
    protection_refs = likely_protection_components(comps)

    j5 = ref_for("POWER_IO", "JDC")
    j6 = ref_for("POWER_IO", "JRJ45")
    u15 = ref_for("POWER_IO", "U5V")
    u16 = ref_for("POWER_IO", "ULASER")
    direct_input_pins = [
        (j5, "1"),
        (j6, "4"),
        (j6, "5"),
        (u15, "3"),
        (u16, "3"),
    ]
    direct_vin = all(pins.get(pin) == "VIN_24V" for pin in direct_input_pins)

    if direct_vin:
        failures.append(
            "J5/J6 connector power pins and U15/U16 buck IN pins are on the same VIN_24V net; "
            "there is no schematic fuse/current-limit/reverse-protection/TVS stage between field input and bucks"
        )
    if not protection_refs:
        failures.append("no fuse/PTC/TVS/reverse-protection/eFuse/hot-swap component is present in the schematic BOM")
    if VIN_NOMINAL_V >= BARREL_RATING_V * 0.8:
        failures.append(
            f"24 V nominal input uses {VIN_NOMINAL_V / BARREL_RATING_V * 100.0:.0f}% of the "
            f"{BARREL_RATING_V:.0f} V J5 barrel voltage rating before adapter/harness/hot-plug transients"
        )
    if VIN_NOMINAL_V >= AP632_VIN_MAX_V * 0.75:
        failures.append(
            f"24 V nominal input uses {VIN_NOMINAL_V / AP632_VIN_MAX_V * 100.0:.0f}% of the "
            f"{AP632_VIN_MAX_V:.0f} V AP632 absolute input limit before transients"
        )
    return failures


def bench_external_protection_failures(netlist_path: Path) -> list[str]:
    failures = validate_current_topology(netlist_path)
    if not BENCH_SIGNOFF.exists():
        failures.append(f"missing bench input signoff: {BENCH_SIGNOFF}")
        return failures
    text = BENCH_SIGNOFF.read_text()
    required = (
        "Use J5 barrel input only for first article power.",
        "current limit set no higher than 300 mA",
        "Keep RJ45 power injection disabled for first article bring-up.",
        "Verify center-positive barrel polarity before every power application.",
        "Do not hot-plug under load.",
        "no onboard reverse protection element",
        "does not close production input protection",
    )
    for phrase in required:
        if phrase not in text:
            failures.append(f"bench input signoff missing phrase: {phrase}")
    return failures


def print_context(policy: str, protection_refs: list[str]) -> None:
    print(f"VIN_24V input policy: {policy}")
    print(
        f"  J5 barrel source: {VIN_NOMINAL_V:.0f} V nominal into a {BARREL_RATING_V:.0f} V / "
        f"{BARREL_RATING_A * 1000.0:.0f} mA connector rating"
    )
    print(f"  J6 RJ45 source: access-controller pin convention, connector operating temp {RJ45_OPERATING_TEMP}")
    print(f"  AP632 VIN range guard used here: 3.8 V operating minimum to {AP632_VIN_MAX_V:.0f} V maximum")
    if protection_refs:
        print(f"  candidate protection refs found: {', '.join(protection_refs)}")
    else:
        print("  candidate protection refs found: none")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument(
        "--policy",
        choices=("bench-topology", "bench-external-protection", "production-protection"),
        default="bench-topology",
    )
    args = parser.parse_args()

    if not args.netlist.exists():
        raise SystemExit(f"netlist not found: {args.netlist}")

    protection_refs = likely_protection_components(component_map(args.netlist))
    print_context(args.policy, protection_refs)
    if args.policy == "bench-topology":
        failures = validate_current_topology(args.netlist)
    elif args.policy == "bench-external-protection":
        failures = bench_external_protection_failures(args.netlist)
    else:
        failures = production_policy_failures(args.netlist)

    if failures:
        print("FAIL VIN_24V input policy")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print("PASS VIN_24V input policy for the checked assumptions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
