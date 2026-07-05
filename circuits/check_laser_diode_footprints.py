#!/usr/bin/env python3
"""Check direct laser-can pinout, PCB pad nets, and KiCad pad geometry.

This is intentionally separate from the analog/current budget checks.  It
answers a narrower fabrication-risk question: if LD1-LD4 are soldered directly
into the board, do the selected diode pin meanings, exported schematic pins,
current PCB pad nets, and installed KiCad TO18/TO56 pad numbering agree?
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_pcb_staging import blocks_named, board_pad_nets, footprint_ref


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")
FOOTPRINT_ROOT = Path("/usr/share/kicad/footprints/OptoDevice.pretty")


@dataclass(frozen=True)
class LaserCan:
    ref: str
    sheet: str
    mpn: str
    value: str
    schematic_footprint: str
    board_footprint: str
    expected_pin_nets: dict[str, str | None]
    required_exact_net_members: dict[str, set[tuple[str, str]]]


LASER_CANS = (
    LaserCan(
        ref="LD1",
        sheet="/LASER_IR/",
        mpn="D7805I",
        value="D7805I 780nm TO18 STYLE-A LASER+MPD",
        schematic_footprint="OptoDevice:LaserDiode_TO18-D5.6-3",
        board_footprint="LaserDiode_TO18-D5.6-3",
        expected_pin_nets={"1": "LASER_N1", "2": "LASER_V+", "3": "MPD_RAW1"},
        required_exact_net_members={
            "LASER_N1": {("LD1", "1"), ("Q1", "3")},
            "MPD_RAW1": {("LD1", "3"), ("R42", "1"), ("U12", "3")},
        },
    ),
    LaserCan(
        ref="LD2",
        sheet="/LASER_RED/",
        mpn="D6505I",
        value="D6505I 650nm TO18 STYLE-A LASER+MPD",
        schematic_footprint="OptoDevice:LaserDiode_TO18-D5.6-3",
        board_footprint="LaserDiode_TO18-D5.6-3",
        expected_pin_nets={"1": "LASER_N2", "2": "LASER_V+", "3": "MPD_RAW2"},
        required_exact_net_members={
            "LASER_N2": {("LD2", "1"), ("Q2", "3")},
            "MPD_RAW2": {("LD2", "3"), ("R44", "1"), ("U12", "5")},
        },
    ),
    LaserCan(
        ref="LD3",
        sheet="/LASER_GREEN/",
        mpn="PLT5 520EB_P",
        value="PLT5 520EB_P TO56 LASER+MPD",
        schematic_footprint="OptoDevice:LaserDiode_TO56-3",
        board_footprint="LaserDiode_TO56-3",
        expected_pin_nets={"1": "LASER_N3", "2": "LASER_V+", "3": "MPD_RAW3"},
        required_exact_net_members={
            "LASER_N3": {("LD3", "1"), ("Q3", "3")},
            "MPD_RAW3": {("LD3", "3"), ("R46", "1"), ("U12", "10")},
        },
    ),
    LaserCan(
        ref="LD4",
        sheet="/LASER_BLUE/",
        mpn="PLT5 450GB",
        value="PLT5 450GB TO56 LASER CASE",
        schematic_footprint="OptoDevice:LaserDiode_TO56-3",
        board_footprint="LaserDiode_TO56-3",
        expected_pin_nets={"1": "LASER_V+", "2": None, "3": "LASER_N4"},
        required_exact_net_members={
            "LASER_N4": {("LD4", "3"), ("Q4", "3")},
            "MPD_RAW4": {("R48", "1"), ("U12", "12")},
        },
    ),
)


EXPECTED_FOOTPRINT_GEOMETRY = {
    "LaserDiode_TO18-D5.6-3": {
        "path": FOOTPRINT_ROOT / "LaserDiode_TO18-D5.6-3.kicad_mod",
        "pads": {
            "1": ("thru_hole", (0.0, 0.0), 0.6),
            "2": ("thru_hole", (1.0, 1.0), 0.6),
            "3": ("thru_hole", (2.0, 0.0), 0.6),
        },
    },
    "LaserDiode_TO56-3": {
        "path": FOOTPRINT_ROOT / "LaserDiode_TO56-3.kicad_mod",
        "pads": {
            "1": ("thru_hole", (0.0, 0.0), 0.7),
            "2": ("thru_hole", (1.0, 1.0), 0.7),
            "3": ("thru_hole", (2.0, 0.0), 0.7),
        },
    },
}


def node_pin_set(nodes: list[tuple[str, str, str, str]]) -> set[tuple[str, str]]:
    return {(ref, pin) for ref, pin, _function, _type in nodes}


def canon_net(net: str | None) -> str | None:
    if net in {"LASER_V+", "LASER_VP"}:
        return "LASER_V+"
    return net


def net_nodes(
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
) -> list[tuple[str, str, str, str]]:
    if canon_net(net) == "LASER_V+":
        return [*nets.get("LASER_V+", []), *nets.get("LASER_VP", [])]
    return nets.get(net, [])


def pin_net_map(nets: dict[str, list[tuple[str, str, str, str]]]) -> dict[tuple[str, str], str]:
    by_pin: dict[tuple[str, str], str] = {}
    for net, nodes in nets.items():
        for ref, pin, _function, _type in nodes:
            by_pin[(ref, pin)] = canon_net(net) or net
    return by_pin


def component_by_ref(netlist_path: Path) -> dict[str, dict[str, str]]:
    return {component["ref"]: component for component in parse_components(netlist_path)}


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


def parse_footprint_pad_geometry(text: str) -> dict[str, tuple[str, tuple[float, float], float]]:
    pads: dict[str, tuple[str, tuple[float, float], float]] = {}
    for pad in blocks_named(text, "pad"):
        pad_match = re.search(r'\(pad\s+(?:"([^"]+)"|([^\s\)]+))\s+([^\s\)]+)', pad)
        at_match = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)', pad)
        drill_match = re.search(r'\(drill\s+([-\d.]+)\)', pad)
        if not pad_match or not at_match or not drill_match:
            continue
        pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
        pad_type = pad_match.group(3)
        pads[pad_name] = (
            pad_type,
            (round(float(at_match.group(1)), 4), round(float(at_match.group(2)), 4)),
            round(float(drill_match.group(1)), 4),
        )
    return pads


def check_components(
    failures: list[str],
    components: dict[str, dict[str, str]],
    cans: tuple[LaserCan, ...],
) -> None:
    for can in cans:
        component = components.get(can.ref)
        if component is None:
            failures.append(f"{can.ref}: missing from exported schematic netlist")
            continue
        expected = {
            "sheet": can.sheet,
            "mpn": can.mpn,
            "value": can.value,
            "footprint": can.schematic_footprint,
        }
        actual = {key: component[key] for key in expected}
        if actual != expected:
            failures.append(f"{can.ref}: expected component identity {expected}, got {actual}")


def check_schematic_nets(
    failures: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    cans: tuple[LaserCan, ...],
) -> None:
    by_pin = pin_net_map(nets)
    for can in cans:
        for pin, expected_net in can.expected_pin_nets.items():
            actual = by_pin.get((can.ref, pin))
            if expected_net is None:
                if actual is None or actual.startswith("unconnected-"):
                    continue
                failures.append(f"{can.ref}.{pin}: expected schematic no-connect, got {actual}")
            elif actual != expected_net:
                failures.append(f"{can.ref}.{pin}: expected schematic net {expected_net}, got {actual or '<missing>'}")

        for net, expected_members in can.required_exact_net_members.items():
            actual_members = node_pin_set(net_nodes(nets, net))
            if actual_members != expected_members:
                failures.append(f"{net}: expected members {sorted(expected_members)}, got {sorted(actual_members)}")

    laser_vplus_members = node_pin_set(net_nodes(nets, "LASER_V+"))
    for ref, pin in [("LD1", "2"), ("LD2", "2"), ("LD3", "2"), ("LD4", "1")]:
        if (ref, pin) not in laser_vplus_members:
            failures.append(f"LASER_V+: missing {ref}.{pin}")
    if ("LD4", "2") in node_pin_set(nets.get("MPD_RAW4", [])):
        failures.append("MPD_RAW4: LD4 case pin is incorrectly tied to the monitor input")


def check_board_pad_nets(
    failures: list[str],
    board_text: str,
    cans: tuple[LaserCan, ...],
) -> None:
    footprints = board_footprints(board_text)
    pad_nets = board_pad_nets(board_text)
    for can in cans:
        block = footprints.get(can.ref)
        if block is None:
            failures.append(f"{can.ref}: missing from PCB")
            continue
        actual_footprint = footprint_name(block)
        if actual_footprint != can.board_footprint:
            failures.append(f"{can.ref}: expected PCB footprint {can.board_footprint}, got {actual_footprint}")
        for pin, expected_net in can.expected_pin_nets.items():
            actual_nets = {canon_net(net) or net for net in pad_nets.get(can.ref, {}).get(pin, set())}
            if expected_net is None:
                if actual_nets:
                    failures.append(f"{can.ref}.{pin}: expected PCB pad to be unnetted, got {sorted(actual_nets)}")
            elif actual_nets != {expected_net}:
                failures.append(f"{can.ref}.{pin}: expected PCB pad net {expected_net}, got {sorted(actual_nets)}")


def check_footprint_geometry(failures: list[str]) -> None:
    for footprint, spec in EXPECTED_FOOTPRINT_GEOMETRY.items():
        path = spec["path"]
        if not path.exists():
            failures.append(f"{footprint}: missing installed KiCad footprint {path}")
            continue
        text = path.read_text()
        if "(attr through_hole)" not in text:
            failures.append(f"{footprint}: expected through-hole footprint")
        actual_pads = parse_footprint_pad_geometry(text)
        if actual_pads != spec["pads"]:
            failures.append(f"{footprint}: expected pad geometry {spec['pads']}, got {actual_pads}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    if not args.netlist.exists():
        print(f"FAIL netlist not found: {args.netlist}")
        return 1
    if not args.board.exists():
        print(f"FAIL PCB not found: {args.board}")
        return 1

    failures: list[str] = []
    components = component_by_ref(args.netlist)
    nets = parse_netlist(args.netlist)
    board_text = args.board.read_text()

    check_components(failures, components, LASER_CANS)
    check_schematic_nets(failures, nets, LASER_CANS)
    check_board_pad_nets(failures, board_text, LASER_CANS)
    check_footprint_geometry(failures)

    if failures:
        print(f"FAIL {len(failures)} laser diode footprint/pinout checks")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS laser diode footprint pinout: LD1/LD2 Style-A TO18, "
        "LD3 PLT5 520EB_P TO56, LD4 PLT5 450GB case NC; schematic nets, "
        "current PCB pad nets, and KiCad TO18/TO56 pad geometry agree"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
