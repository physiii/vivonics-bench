#!/usr/bin/env python3
"""Compare the exported schematic netlist against the current PCB pad nets.

This is a headless parity guard for environments where KiCad's native
schematic-parity DRC is not available from `kicad-cli`. It does not replace
native KiCad ERC/DRC, but it does catch stale footprints, stale pad nets, and
unexpected PCB-only electrical footprints.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_pcb_staging import (
    BOARD_ONLY_FOOTPRINT_REFS,
    blocks_named,
    board_net_table,
    board_pad_nets,
    footprint_ref,
    pad_blocks,
)


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")


def footprint_name(block: str) -> str:
    match = re.match(r'\s*\(footprint\s+(?:"([^"]+)"|([^\s\)]+))', block)
    if not match:
        return ""
    return match.group(1) if match.group(1) is not None else match.group(2)


def footprint_basename(lib_id: str) -> str:
    return lib_id.split(":", 1)[-1]


def board_footprints(board_text: str) -> dict[str, str]:
    footprints: dict[str, str] = {}
    for block in blocks_named(board_text, "footprint"):
        ref = footprint_ref(block)
        if ref:
            footprints.setdefault(ref, block)
    return footprints


def board_pad_names(footprints: dict[str, str]) -> dict[str, set[str]]:
    names: dict[str, set[str]] = defaultdict(set)
    for ref, block in footprints.items():
        for pad in pad_blocks(block):
            match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
            if match:
                names[ref].add(match.group(1) if match.group(1) is not None else match.group(2))
    return names


def schematic_pin_nets(netlist_path: Path) -> dict[tuple[str, str], str]:
    pins: dict[tuple[str, str], str] = {}
    for net_name, nodes in parse_netlist(netlist_path).items():
        for ref, pin, _function, _type in nodes:
            pins[(ref, pin)] = net_name
    return pins


def check_parity(netlist_path: Path, board_path: Path) -> list[str]:
    if not netlist_path.exists():
        return [f"netlist file not found: {netlist_path}"]
    if not board_path.exists():
        return [f"PCB file not found: {board_path}"]

    board_text = board_path.read_text()
    components = parse_components(netlist_path)
    expected_physical = {
        component["ref"]: component
        for component in components
        if component["footprint"]
    }
    expected_empty = {
        component["ref"]
        for component in components
        if not component["footprint"]
    }

    footprint_blocks = [
        (footprint_ref(block), block)
        for block in blocks_named(board_text, "footprint")
        if footprint_ref(block)
    ]
    actual_refs = [ref for ref, _block in footprint_blocks]
    duplicate_refs = sorted(ref for ref, count in Counter(actual_refs).items() if count > 1)
    actual_ref_set = set(actual_refs)
    footprints = board_footprints(board_text)
    pad_names = board_pad_names(footprints)
    pad_nets = board_pad_nets(board_text)
    pin_nets = schematic_pin_nets(netlist_path)

    failures: list[str] = []
    if duplicate_refs:
        failures.append(f"duplicate PCB footprint references: {duplicate_refs}")

    allowed_refs = set(expected_physical) | BOARD_ONLY_FOOTPRINT_REFS
    missing_refs = sorted(set(expected_physical) - actual_ref_set)
    extra_refs = sorted(actual_ref_set - allowed_refs)
    if missing_refs:
        failures.append(f"schematic physical refs missing from PCB: {missing_refs}")
    if extra_refs:
        failures.append(f"unexpected electrical PCB refs not in schematic: {extra_refs}")

    unexpected_empty_refs = sorted(expected_empty & actual_ref_set)
    if unexpected_empty_refs:
        failures.append(f"no-footprint schematic refs unexpectedly placed on PCB: {unexpected_empty_refs}")

    for ref, component in sorted(expected_physical.items()):
        block = footprints.get(ref)
        if block is None:
            continue
        expected_names = {component["footprint"], footprint_basename(component["footprint"])}
        actual_name = footprint_name(block)
        if actual_name not in expected_names:
            failures.append(f"{ref} footprint mismatch: schematic={component['footprint']} pcb={actual_name}")

    expected_net_names = set(parse_netlist(netlist_path))
    actual_net_names = set(board_net_table(board_text))
    missing_real_nets = sorted(
        name
        for name in expected_net_names - actual_net_names
        if not name.startswith("unconnected-")
    )
    extra_nets = sorted(actual_net_names - expected_net_names)
    if missing_real_nets:
        failures.append(f"PCB net table missing schematic nets: {missing_real_nets}")
    if extra_nets:
        failures.append(f"PCB net table has non-schematic nets: {extra_nets}")

    expected_pins_by_ref: dict[str, set[str]] = defaultdict(set)
    for (ref, pin), expected_net in sorted(pin_nets.items()):
        if ref not in expected_physical:
            continue
        expected_pins_by_ref[ref].add(pin)
        if ref not in footprints:
            continue
        if pin not in pad_names.get(ref, set()):
            failures.append(f"{ref}.{pin} schematic pin missing from PCB footprint pads")
            continue
        actual_nets = pad_nets.get(ref, {}).get(pin, set())
        if expected_net.startswith("unconnected-"):
            if actual_nets:
                failures.append(
                    f"{ref}.{pin} should be unconnected in PCB but has nets {sorted(actual_nets)}"
                )
        elif actual_nets != {expected_net}:
            failures.append(
                f"{ref}.{pin} pad net mismatch: schematic={expected_net} pcb={sorted(actual_nets)}"
            )

    for ref, actual_pads in sorted(pad_nets.items()):
        if ref not in expected_physical:
            continue
        extra_netted_pins = sorted(set(actual_pads) - expected_pins_by_ref.get(ref, set()))
        if extra_netted_pins:
            failures.append(f"{ref} has netted PCB pads not present in schematic: {extra_netted_pins}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    failures = check_parity(args.netlist, args.board)
    if failures:
        print("FAIL schematic/PCB parity")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    components = parse_components(args.netlist)
    board_text = args.board.read_text()
    physical_count = sum(1 for component in components if component["footprint"])
    expected_physical_refs = {
        component["ref"]
        for component in components
        if component["footprint"]
    }
    board_ref_count = len(board_footprints(board_text))
    board_only_refs = sorted((set(board_footprints(board_text)) - expected_physical_refs) & BOARD_ONLY_FOOTPRINT_REFS)
    net_count = len(board_net_table(board_text))
    board_only_clause = (
        f" plus {len(board_only_refs)} board-only mechanical refs"
        if board_only_refs
        else ""
    )
    print(
        "PASS schematic/PCB parity: "
        f"{physical_count} schematic footprints match {board_ref_count} PCB footprints{board_only_clause}; "
        f"{net_count} real PCB nets match exported schematic pad nets, with unconnected pins left unnetted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
