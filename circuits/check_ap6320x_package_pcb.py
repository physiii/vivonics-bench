#!/usr/bin/env python3
"""Check AP63205/AP63200 package pin nets against the current PCB pads.

`check_buck_input_power_budget.py` covers first-order current, feedback, and
component-sizing policy.  This checker covers the package-risk layer: U15/U16
identity, datasheet pin nets, current PCB pad-net assignments, and the local
TSOT-23-6 plus L1/L2 inductor footprint geometry.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_pcb_staging import blocks_named, board_pad_nets, footprint_ref


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")
TSOT23_6_FOOTPRINT = Path("/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/TSOT-23-6.kicad_mod")
L1_FOOTPRINT = Path(__file__).resolve().parent / "lib" / "Open_Automation.pretty" / "L_5.4x5.3_H3.kicad_mod"
L2_FOOTPRINT = Path(__file__).resolve().parent / "lib" / "Open_Automation.pretty" / "L_4x4.kicad_mod"


EXPECTED_COMPONENTS = {
    "U15": {
        "sheet": "/POWER_IO/",
        "value": "AP63205WU-7 5V BUCK",
        "footprint": "Package_TO_SOT_SMD:TSOT-23-6",
        "mpn": "AP63205WU-7",
        "lcsc": "C2071056",
    },
    "U16": {
        "sheet": "/POWER_IO/",
        "value": "AP63200WU-7 9.3V BUCK",
        "footprint": "Package_TO_SOT_SMD:TSOT-23-6",
        "mpn": "AP63200WU-7",
        "lcsc": "C2071868",
    },
    "L1": {
        "sheet": "/POWER_IO/",
        "value": "4.7uH",
        "footprint": "Open_Automation:L_5.4x5.3_H3",
        "mpn": "MWSA0503S-4R7MT",
        "lcsc": "C408410",
    },
    "L2": {
        "sheet": "/POWER_IO/",
        "value": "10uH",
        "footprint": "Open_Automation:L_4x4",
        "mpn": "WPN4020H100MT",
        "lcsc": "C98364",
    },
    "C63": {
        "sheet": "/POWER_IO/",
        "value": "100nF BST",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C66": {
        "sheet": "/POWER_IO/",
        "value": "100nF BST",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "R61": {
        "sheet": "/POWER_IO/",
        "value": "237k FB",
        "footprint": "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        "mpn": "FRC0603F2373TS",
        "lcsc": "C2998117",
    },
    "R62": {
        "sheet": "/POWER_IO/",
        "value": "22.1K FB",
        "footprint": "Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder",
        "mpn": "FRC0402F2212TS",
        "lcsc": "C2929993",
    },
    "C69": {
        "sheet": "/POWER_IO/",
        "value": "100pF FF",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402CG101J500NT",
        "lcsc": "C1546",
    },
}


EXPECTED_PIN_NETS = {
    "U15": {
        "1": "/POWER_IO/BUCK_5V",
        "2": "VIN_24V",
        "3": "VIN_24V",
        "4": "GND",
        "5": "/POWER_IO/BUCK5_SW",
        "6": "/POWER_IO/BUCK5_BST",
    },
    "U16": {
        "1": "/POWER_IO/LASER_BUCK_FB",
        "2": "VIN_24V",
        "3": "VIN_24V",
        "4": "GND",
        "5": "/POWER_IO/LASER_BUCK_SW",
        "6": "/POWER_IO/LASER_BUCK_BST",
    },
    "L1": {
        "1": "/POWER_IO/BUCK5_SW",
        "2": "/POWER_IO/BUCK_5V",
    },
    "L2": {
        "1": "/POWER_IO/LASER_BUCK_SW",
        "2": "LASER_VP",
    },
    "C61": {"1": "VIN_24V", "2": "GND"},
    "C62": {"1": "VIN_24V", "2": "GND"},
    "C63": {"1": "/POWER_IO/BUCK5_SW", "2": "/POWER_IO/BUCK5_BST"},
    "C64": {"1": "/POWER_IO/BUCK_5V", "2": "GND"},
    "C65": {"1": "/POWER_IO/BUCK_5V", "2": "GND"},
    "C66": {"1": "/POWER_IO/LASER_BUCK_SW", "2": "/POWER_IO/LASER_BUCK_BST"},
    "C67": {"1": "LASER_VP", "2": "GND"},
    "C68": {"1": "LASER_VP", "2": "GND"},
    "C69": {"1": "LASER_VP", "2": "/POWER_IO/LASER_BUCK_FB"},
    "C70": {"1": "VIN_24V", "2": "GND"},
    "R61": {"1": "LASER_VP", "2": "/POWER_IO/LASER_BUCK_FB"},
    "R62": {"1": "/POWER_IO/LASER_BUCK_FB", "2": "GND"},
    "D6": {"1": "/POWER_IO/BUCK_5V", "2": "+5V"},
}


EXPECTED_EXACT_NETS = {
    "/POWER_IO/BUCK5_SW": {("U15", "5"), ("C63", "1"), ("L1", "1")},
    "/POWER_IO/BUCK5_BST": {("U15", "6"), ("C63", "2")},
    "/POWER_IO/LASER_BUCK_SW": {("U16", "5"), ("C66", "1"), ("L2", "1")},
    "/POWER_IO/LASER_BUCK_BST": {("U16", "6"), ("C66", "2")},
    "/POWER_IO/LASER_BUCK_FB": {("U16", "1"), ("R61", "2"), ("R62", "1"), ("C69", "2")},
    "/POWER_IO/BUCK_5V": {("U15", "1"), ("L1", "2"), ("C64", "1"), ("C65", "1"), ("D6", "1")},
}


EXPECTED_REQUIRED_NET_MEMBERS = {
    "VIN_24V": {
        ("U15", "2"),
        ("U15", "3"),
        ("U16", "2"),
        ("U16", "3"),
        ("C61", "1"),
        ("C62", "1"),
        ("C70", "1"),
        ("J5", "1"),
        ("J6", "4"),
        ("J6", "5"),
    },
    "LASER_VP": {
        ("L2", "2"),
        ("C67", "1"),
        ("C68", "1"),
        ("C69", "1"),
        ("R61", "1"),
    },
    "GND": {
        ("U15", "4"),
        ("U16", "4"),
        ("C61", "2"),
        ("C62", "2"),
        ("C64", "2"),
        ("C65", "2"),
        ("C67", "2"),
        ("C68", "2"),
        ("C70", "2"),
        ("R62", "2"),
    },
    "+5V": {("D6", "2")},
}


EXPECTED_BOARD_FOOTPRINTS = {
    "U15": "TSOT-23-6",
    "U16": "TSOT-23-6",
    "L1": "L_5.4x5.3_H3",
    "L2": "L_4x4",
}


EXPECTED_TSOT23_6_PADS = {
    "1": ("smd", (-1.1375, -0.95), (1.325, 0.6)),
    "2": ("smd", (-1.1375, 0.0), (1.325, 0.6)),
    "3": ("smd", (-1.1375, 0.95), (1.325, 0.6)),
    "4": ("smd", (1.1375, 0.95), (1.325, 0.6)),
    "5": ("smd", (1.1375, 0.0), (1.325, 0.6)),
    "6": ("smd", (1.1375, -0.95), (1.325, 0.6)),
}


EXPECTED_INDUCTOR_PADS = {
    L1_FOOTPRINT: {
        "1": ("smd", (-2.75, 0.0), (1.5, 2.4)),
        "2": ("smd", (1.45, 0.0), (1.5, 2.4)),
    },
    L2_FOOTPRINT: {
        "1": ("smd", (-1.5, 0.01), (1.1, 3.7)),
        "2": ("smd", (1.5, 0.0), (1.1, 3.7)),
    },
}


def node_pin_set(nodes: list[tuple[str, str, str, str]]) -> set[tuple[str, str]]:
    return {(ref, pin) for ref, pin, _function, _type in nodes}


def pin_net_map(nets: dict[str, list[tuple[str, str, str, str]]]) -> dict[tuple[str, str], str]:
    by_pin: dict[tuple[str, str], str] = {}
    for net, nodes in nets.items():
        for ref, pin, _function, _type in nodes:
            by_pin[(ref, pin)] = net
    return by_pin


def footprint_name(block: str) -> str:
    match = re.match(r'\s*\(footprint\s+(?:"([^"]+)"|([^\s\)]+))', block)
    if not match:
        return ""
    name = match.group(1) if match.group(1) is not None else match.group(2)
    return name.split(":", 1)[-1]


def board_footprints(board_text: str) -> dict[str, str]:
    footprints: dict[str, str] = {}
    for block in blocks_named(board_text, "footprint"):
        ref = footprint_ref(block)
        if ref:
            footprints[ref] = block
    return footprints


def parse_footprint_pads(text: str) -> dict[str, tuple[str, tuple[float, float], tuple[float, float]]]:
    pads: dict[str, tuple[str, tuple[float, float], tuple[float, float]]] = {}
    for pad in blocks_named(text, "pad"):
        pad_match = re.search(r'\(pad\s+(?:"([^"]+)"|([^\s\)]+))\s+([^\s\)]+)', pad)
        at_match = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)', pad)
        size_match = re.search(r'\(size\s+([-\d.]+)\s+([-\d.]+)\)', pad)
        if not pad_match or not at_match or not size_match:
            continue
        pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
        pads[pad_name] = (
            pad_match.group(3),
            (round(float(at_match.group(1)), 4), round(float(at_match.group(2)), 4)),
            (round(float(size_match.group(1)), 4), round(float(size_match.group(2)), 4)),
        )
    return pads


def check_components(failures: list[str], netlist_path: Path) -> None:
    components = {component["ref"]: component for component in parse_components(netlist_path)}
    for ref, expected in EXPECTED_COMPONENTS.items():
        component = components.get(ref)
        if component is None:
            failures.append(f"{ref}: missing from exported netlist")
            continue
        actual = {key: component[key] for key in ("sheet", "value", "footprint", "mpn", "lcsc")}
        if actual != expected:
            failures.append(f"{ref}: expected component identity {expected}, got {actual}")


def check_schematic_nets(
    failures: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
) -> None:
    by_pin = pin_net_map(nets)
    for ref, pin_nets in EXPECTED_PIN_NETS.items():
        for pin, expected_net in pin_nets.items():
            actual = by_pin.get((ref, pin))
            if actual != expected_net:
                failures.append(f"{ref}.{pin}: expected schematic net {expected_net}, got {actual or '<missing>'}")

    for net, expected_members in EXPECTED_EXACT_NETS.items():
        actual_members = node_pin_set(nets.get(net, []))
        if actual_members != expected_members:
            failures.append(f"{net}: expected exact members {sorted(expected_members)}, got {sorted(actual_members)}")

    for net, required_members in EXPECTED_REQUIRED_NET_MEMBERS.items():
        actual_members = node_pin_set(nets.get(net, []))
        missing = sorted(required_members - actual_members)
        if missing:
            failures.append(f"{net}: missing required member(s) {missing}")


def check_board(failures: list[str], board_path: Path) -> None:
    board_text = board_path.read_text()
    footprints = board_footprints(board_text)
    pads = board_pad_nets(board_text)

    for ref, expected_footprint in EXPECTED_BOARD_FOOTPRINTS.items():
        block = footprints.get(ref)
        if block is None:
            failures.append(f"{ref}: missing from PCB")
            continue
        actual_footprint = footprint_name(block)
        if actual_footprint != expected_footprint:
            failures.append(f"{ref}: expected PCB footprint {expected_footprint}, got {actual_footprint}")

    for ref, pin_nets in EXPECTED_PIN_NETS.items():
        for pin, expected_net in pin_nets.items():
            actual_nets = pads.get(ref, {}).get(pin, set())
            if actual_nets != {expected_net}:
                failures.append(f"{ref}.{pin}: expected PCB pad net {expected_net}, got {sorted(actual_nets)}")


def check_footprint_geometry(
    failures: list[str],
    footprint_path: Path,
    expected_pads: dict[str, tuple[str, tuple[float, float], tuple[float, float]]],
) -> None:
    if not footprint_path.exists():
        failures.append(f"missing local footprint: {footprint_path}")
        return
    pads = parse_footprint_pads(footprint_path.read_text())
    if pads != expected_pads:
        failures.append(f"{footprint_path}: expected pad geometry {expected_pads}, got {pads}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    failures: list[str] = []
    if not args.netlist.exists():
        failures.append(f"netlist not found: {args.netlist}")
    if not args.board.exists():
        failures.append(f"PCB file not found: {args.board}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    nets = parse_netlist(args.netlist)
    check_components(failures, args.netlist)
    check_schematic_nets(failures, nets)
    check_board(failures, args.board)
    check_footprint_geometry(failures, TSOT23_6_FOOTPRINT, EXPECTED_TSOT23_6_PADS)
    for footprint_path, expected_pads in EXPECTED_INDUCTOR_PADS.items():
        check_footprint_geometry(failures, footprint_path, expected_pads)

    if failures:
        print(f"FAIL AP6320x package/PCB guard: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS AP6320x package/PCB guard: U15/U16 schematic pin nets, current PCB pad nets, "
        "TSOT-23-6 geometry, and L1/L2 local inductor footprints match the datasheet-derived contract."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
