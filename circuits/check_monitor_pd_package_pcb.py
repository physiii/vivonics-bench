#!/usr/bin/env python3
"""Check INA4180/LM4040 monitor-PD package nets against the current PCB pads.

`check_laser_monitor_pd_budget.py` covers the first-order bias/current/ADC
range policy. This checker covers the package-risk layer: U12/U13 identity,
datasheet pin nets, local support components, current PCB pad-net assignments,
and installed KiCad footprint geometry for the package-sensitive parts.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_pcb_staging import blocks_named, board_pad_nets, footprint_ref


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")
TSSOP14_FOOTPRINT = Path("/usr/share/kicad/footprints/Package_SO.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod")
SOT23_FOOTPRINT = Path("/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod")
R0603_FOOTPRINT = Path(
    "/usr/share/kicad/footprints/Resistor_SMD.pretty/R_0603_1608Metric_Pad0.98x0.95mm_HandSolder.kicad_mod"
)
C0402_FOOTPRINT = Path(
    "/usr/share/kicad/footprints/Capacitor_SMD.pretty/C_0402_1005Metric_Pad0.74x0.62mm_HandSolder.kicad_mod"
)


EXPECTED_COMPONENTS = {
    "U12": {
        "sheet": "/POWER_IO/",
        "value": "INA4180A1",
        "footprint": "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
        "mpn": "INA4180A1IPWR",
        "lcsc": "C2057528",
    },
    "U13": {
        "sheet": "/POWER_IO/",
        "value": "LM4040C50 5V",
        "footprint": "Package_TO_SOT_SMD:SOT-23",
        "mpn": "LM4040C50IDBZR",
        "lcsc": "C69316",
    },
    "R41": {
        "sheet": "/POWER_IO/",
        "value": "2.49k MPD bias",
        "footprint": "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        "mpn": "RTT032491FTP",
        "lcsc": "C103460",
    },
    "C35": {
        "sheet": "/POWER_IO/",
        "value": "100nF",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C36": {
        "sheet": "/POWER_IO/",
        "value": "100nF MPD bias",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
}

for ref in ("R42", "R44", "R46", "R48"):
    EXPECTED_COMPONENTS[ref] = {
        "sheet": "/POWER_IO/",
        "value": "240R MPD sense",
        "footprint": "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        "mpn": "RTT032400FTP",
        "lcsc": "C103446",
    }
for ref in ("R43", "R45", "R47", "R49"):
    EXPECTED_COMPONENTS[ref] = {
        "sheet": "/POWER_IO/",
        "value": "1k ADC",
        "footprint": "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        "mpn": "FRC0603F1001TS",
        "lcsc": "C2907002",
    }
for ref in ("C37", "C38", "C39", "C40"):
    EXPECTED_COMPONENTS[ref] = {
        "sheet": "/POWER_IO/",
        "value": "100nF MPD ADC",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    }


EXPECTED_PIN_NETS = {
    "U12": {
        "1": "/POWER_IO/MPD_AMP1",
        "2": "/POWER_IO/MPD_BIAS",
        "3": "MPD_RAW1",
        "4": "+3V3",
        "5": "MPD_RAW2",
        "6": "/POWER_IO/MPD_BIAS",
        "7": "/POWER_IO/MPD_AMP2",
        "8": "/POWER_IO/MPD_AMP3",
        "9": "/POWER_IO/MPD_BIAS",
        "10": "MPD_RAW3",
        "11": "GND",
        "12": "MPD_RAW4",
        "13": "/POWER_IO/MPD_BIAS",
        "14": "/POWER_IO/MPD_AMP4",
    },
    "U13": {
        "1": "LASER_V+",
        "2": "/POWER_IO/MPD_BIAS",
        "3": "/POWER_IO/MPD_BIAS",
    },
    "R41": {"1": "/POWER_IO/MPD_BIAS", "2": "GND"},
    "C35": {"1": "+3V3", "2": "GND"},
    "C36": {"1": "LASER_V+", "2": "/POWER_IO/MPD_BIAS"},
    "R42": {"1": "MPD_RAW1", "2": "/POWER_IO/MPD_BIAS"},
    "R43": {"1": "/POWER_IO/MPD_AMP1", "2": "MPD1"},
    "R44": {"1": "MPD_RAW2", "2": "/POWER_IO/MPD_BIAS"},
    "R45": {"1": "/POWER_IO/MPD_AMP2", "2": "MPD2"},
    "R46": {"1": "MPD_RAW3", "2": "/POWER_IO/MPD_BIAS"},
    "R47": {"1": "/POWER_IO/MPD_AMP3", "2": "MPD3"},
    "R48": {"1": "MPD_RAW4", "2": "/POWER_IO/MPD_BIAS"},
    "R49": {"1": "/POWER_IO/MPD_AMP4", "2": "MPD4"},
    "C37": {"1": "MPD1", "2": "GND"},
    "C38": {"1": "MPD2", "2": "GND"},
    "C39": {"1": "MPD3", "2": "GND"},
    "C40": {"1": "MPD4", "2": "GND"},
}


EXPECTED_EXACT_NETS = {
    "MPD_RAW1": {("LD1", "3"), ("R42", "1"), ("U12", "3")},
    "MPD_RAW2": {("LD2", "3"), ("R44", "1"), ("U12", "5")},
    "MPD_RAW3": {("LD3", "3"), ("R46", "1"), ("U12", "10")},
    "MPD_RAW4": {("R48", "1"), ("U12", "12")},
    "/POWER_IO/MPD_BIAS": {
        ("C36", "2"),
        ("R41", "1"),
        ("R42", "2"),
        ("R44", "2"),
        ("R46", "2"),
        ("R48", "2"),
        ("U12", "2"),
        ("U12", "6"),
        ("U12", "9"),
        ("U12", "13"),
        ("U13", "2"),
        ("U13", "3"),
    },
    "/POWER_IO/MPD_AMP1": {("R43", "1"), ("U12", "1")},
    "/POWER_IO/MPD_AMP2": {("R45", "1"), ("U12", "7")},
    "/POWER_IO/MPD_AMP3": {("R47", "1"), ("U12", "8")},
    "/POWER_IO/MPD_AMP4": {("R49", "1"), ("U12", "14")},
    "MPD1": {("C37", "1"), ("R43", "2"), ("U9", "38")},
    "MPD2": {("C38", "1"), ("R45", "2"), ("U9", "15")},
    "MPD3": {("C39", "1"), ("R47", "2"), ("U9", "12")},
    "MPD4": {("C40", "1"), ("R49", "2"), ("U9", "17")},
}


EXPECTED_REQUIRED_NET_MEMBERS = {
    "LASER_V+": {("C36", "1"), ("LD1", "2"), ("LD2", "2"), ("LD3", "2"), ("LD4", "1"), ("U13", "1")},
    "+3V3": {("C35", "1"), ("U12", "4")},
    "GND": {("C35", "2"), ("C37", "2"), ("C38", "2"), ("C39", "2"), ("C40", "2"), ("R41", "2"), ("U12", "11")},
}


EXPECTED_BOARD_FOOTPRINTS = {
    "U12": "TSSOP-14_4.4x5mm_P0.65mm",
    "U13": "SOT-23",
    "R41": "R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
    "C35": "C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
    "C36": "C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
}
for ref in ("R42", "R43", "R44", "R45", "R46", "R47", "R48", "R49"):
    EXPECTED_BOARD_FOOTPRINTS[ref] = "R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
for ref in ("C37", "C38", "C39", "C40"):
    EXPECTED_BOARD_FOOTPRINTS[ref] = "C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"


EXPECTED_TSSOP14_PADS = {
    "1": ("smd", (-2.8625, -1.95), (1.475, 0.4)),
    "2": ("smd", (-2.8625, -1.3), (1.475, 0.4)),
    "3": ("smd", (-2.8625, -0.65), (1.475, 0.4)),
    "4": ("smd", (-2.8625, 0.0), (1.475, 0.4)),
    "5": ("smd", (-2.8625, 0.65), (1.475, 0.4)),
    "6": ("smd", (-2.8625, 1.3), (1.475, 0.4)),
    "7": ("smd", (-2.8625, 1.95), (1.475, 0.4)),
    "8": ("smd", (2.8625, 1.95), (1.475, 0.4)),
    "9": ("smd", (2.8625, 1.3), (1.475, 0.4)),
    "10": ("smd", (2.8625, 0.65), (1.475, 0.4)),
    "11": ("smd", (2.8625, 0.0), (1.475, 0.4)),
    "12": ("smd", (2.8625, -0.65), (1.475, 0.4)),
    "13": ("smd", (2.8625, -1.3), (1.475, 0.4)),
    "14": ("smd", (2.8625, -1.95), (1.475, 0.4)),
}
EXPECTED_SOT23_PADS = {
    "1": ("smd", (-0.9375, -0.95), (1.475, 0.6)),
    "2": ("smd", (-0.9375, 0.95), (1.475, 0.6)),
    "3": ("smd", (0.9375, 0.0), (1.475, 0.6)),
}
EXPECTED_R0603_PADS = {
    "1": ("smd", (-0.9125, 0.0), (0.975, 0.95)),
    "2": ("smd", (0.9125, 0.0), (0.975, 0.95)),
}
EXPECTED_C0402_PADS = {
    "1": ("smd", (-0.5675, 0.0), (0.735, 0.62)),
    "2": ("smd", (0.5675, 0.0), (0.735, 0.62)),
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
        actual_members = node_pin_set(net_nodes(nets, net))
        if actual_members != expected_members:
            failures.append(f"{net}: expected exact members {sorted(expected_members)}, got {sorted(actual_members)}")

    for net, required_members in EXPECTED_REQUIRED_NET_MEMBERS.items():
        actual_members = node_pin_set(net_nodes(nets, net))
        missing = sorted(required_members - actual_members)
        if missing:
            failures.append(f"{net}: missing required member(s) {missing}")

    ld4_case_net = by_pin.get(("LD4", "2"))
    if ld4_case_net is not None and not ld4_case_net.startswith("unconnected-"):
        failures.append(f"LD4.2: selected PLT5 450GB case must stay unconnected, got {ld4_case_net}")


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
            actual_nets = {canon_net(net) or net for net in pads.get(ref, {}).get(pin, set())}
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
    check_footprint_geometry(failures, TSSOP14_FOOTPRINT, EXPECTED_TSSOP14_PADS)
    check_footprint_geometry(failures, SOT23_FOOTPRINT, EXPECTED_SOT23_PADS)
    check_footprint_geometry(failures, R0603_FOOTPRINT, EXPECTED_R0603_PADS)
    check_footprint_geometry(failures, C0402_FOOTPRINT, EXPECTED_C0402_PADS)

    if failures:
        print(f"FAIL monitor-PD package/PCB guard: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS monitor-PD package/PCB guard: U12/U13 schematic pin nets, local MPD sense/filter/bias "
        "component identities, current PCB pad nets, LD4 case no-connect, and KiCad package geometry agree."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
