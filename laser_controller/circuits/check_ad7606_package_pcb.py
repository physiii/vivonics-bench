#!/usr/bin/env python3
"""Check AD7606-4 package pin nets against the current PCB pads.

`check_ad7606_interface_budget.py` covers the firmware/timing contract.  This
checker covers the package-risk layer: AD7606BSTZ-4RL identity, all U14
schematic pin nets, the current PCB pad-net assignments, and the installed
KiCad LQFP-64 footprint pad geometry.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_pcb_staging import blocks_named, board_pad_nets, footprint_ref


ADC_REF = "U14"
DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")
LQFP64_FOOTPRINT = Path("/usr/share/kicad/footprints/Package_QFP.pretty/LQFP-64_10x10mm_P0.5mm.kicad_mod")


EXPECTED_COMPONENT = {
    "ref": ADC_REF,
    "sheet": "/POWER_IO/",
    "value": "AD7606BSTZ-4",
    "footprint": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
    "mpn": "AD7606BSTZ-4RL",
    "lcsc": "C51512",
}


EXPECTED_SUPPORT_COMPONENTS = {
    "C51": {
        "value": "100nF ADC AVCC",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C52": {
        "value": "100nF ADC AVCC",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C53": {
        "value": "100nF ADC AVCC",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C54": {
        "value": "100nF ADC AVCC",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C55": {
        "value": "100nF ADC VDRIVE",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "0402B104K160CT",
        "lcsc": "C83056",
    },
    "C56": {
        "value": "10uF ADC AVCC",
        "footprint": "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
        "mpn": "CL21A106KAYNNNG",
        "lcsc": "C318691",
    },
    "C57": {
        "value": "1uF ADC REGCAP",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "HGC0402R5105K250NTEJ",
        "lcsc": "C7472946",
    },
    "C58": {
        "value": "1uF ADC REGCAP",
        "footprint": "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        "mpn": "HGC0402R5105K250NTEJ",
        "lcsc": "C7472946",
    },
    "C59": {
        "value": "10uF ADC REF",
        "footprint": "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
        "mpn": "CL21A106KAYNNNG",
        "lcsc": "C318691",
    },
    "C60": {
        "value": "10uF ADC REFCAP",
        "footprint": "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
        "mpn": "CL21A106KAYNNNG",
        "lcsc": "C318691",
    },
}


EXPECTED_PIN_NETS = {
    "1": "+5V",
    "2": "GND",
    "3": "GND",
    "4": "GND",
    "5": "GND",
    "6": "+3V3",
    "7": "+3V3",
    "8": "GND",
    "9": "CONVST",
    "10": "CONVST",
    "11": "ADC_RESET",
    "12": "ADC_SCLK",
    "13": "ADC_CS",
    "14": "ADC_BUSY",
    "15": None,
    "16": "GND",
    "17": "GND",
    "18": "GND",
    "19": "GND",
    "20": "GND",
    "21": "GND",
    "22": "GND",
    "23": "+3V3",
    "24": "ADC_MISO_A",
    "25": "ADC_MISO_B",
    "26": "GND",
    "27": "GND",
    "28": "GND",
    "29": "GND",
    "30": "GND",
    "31": "GND",
    "32": "GND",
    "33": "GND",
    "34": "+3V3",
    "35": "GND",
    "36": "/POWER_IO/ADC_CREG1",
    "37": "+5V",
    "38": "+5V",
    "39": "/POWER_IO/ADC_CREG2",
    "40": "GND",
    "41": "GND",
    "42": "/POWER_IO/ADC_CREFIN",
    "43": "GND",
    "44": "/POWER_IO/ADC_REFCAP",
    "45": "/POWER_IO/ADC_REFCAP",
    "46": "GND",
    "47": "GND",
    "48": "+5V",
    "49": "VOUT1",
    "50": "GND",
    "51": "VOUT2",
    "52": "GND",
    "53": "GND",
    "54": "GND",
    "55": "GND",
    "56": "GND",
    "57": "VOUT3",
    "58": "GND",
    "59": "VOUT4",
    "60": "GND",
    "61": "GND",
    "62": "GND",
    "63": "GND",
    "64": "GND",
}


EXPECTED_SUPPORT_PIN_NETS = {
    ("C51", "1"): "+5V",
    ("C51", "2"): "GND",
    ("C52", "1"): "+5V",
    ("C52", "2"): "GND",
    ("C53", "1"): "+5V",
    ("C53", "2"): "GND",
    ("C54", "1"): "+5V",
    ("C54", "2"): "GND",
    ("C55", "1"): "+3V3",
    ("C55", "2"): "GND",
    ("C56", "1"): "+5V",
    ("C56", "2"): "GND",
    ("C57", "1"): "/POWER_IO/ADC_CREG1",
    ("C57", "2"): "GND",
    ("C58", "1"): "/POWER_IO/ADC_CREG2",
    ("C58", "2"): "GND",
    ("C59", "1"): "/POWER_IO/ADC_CREFIN",
    ("C59", "2"): "GND",
    ("C60", "1"): "/POWER_IO/ADC_REFCAP",
    ("C60", "2"): "GND",
}


EXPECTED_EXACT_NETS = {
    "CONVST": {("U14", "9"), ("U14", "10"), ("U9", "8")},
    "ADC_RESET": {("U14", "11"), ("U9", "25")},
    "ADC_SCLK": {("U14", "12"), ("U9", "10")},
    "ADC_CS": {("U14", "13"), ("U9", "11")},
    "ADC_BUSY": {("U14", "14"), ("U9", "24")},
    "ADC_MISO_A": {("U14", "24"), ("U9", "23")},
    "ADC_MISO_B": {("U14", "25"), ("U9", "31")},
    "VOUT1": {("C1", "2"), ("RV5", "2"), ("RV5", "3"), ("U1", "6"), ("U14", "49")},
    "VOUT2": {("C5", "2"), ("RV6", "2"), ("RV6", "3"), ("U2", "6"), ("U14", "51")},
    "VOUT3": {("C9", "2"), ("RV7", "2"), ("RV7", "3"), ("U3", "6"), ("U14", "57")},
    "VOUT4": {("C13", "2"), ("RV8", "2"), ("RV8", "3"), ("U4", "6"), ("U14", "59")},
    "/POWER_IO/ADC_CREG1": {("C57", "1"), ("U14", "36")},
    "/POWER_IO/ADC_CREG2": {("C58", "1"), ("U14", "39")},
    "/POWER_IO/ADC_CREFIN": {("C59", "1"), ("U14", "42")},
    "/POWER_IO/ADC_REFCAP": {("C60", "1"), ("U14", "44"), ("U14", "45")},
}


def node_pin_set(nodes: list[tuple[str, str, str, str]]) -> set[tuple[str, str]]:
    return {(ref, pin) for ref, pin, _function, _type in nodes}


def canon_net(net: str | None) -> str | None:
    aliases = {
        "Net-(C57-Pad1)": "/POWER_IO/ADC_CREG1",
        "Net-(C58-Pad1)": "/POWER_IO/ADC_CREG2",
        "Net-(U14-REFIN{slash}REFOUT)": "/POWER_IO/ADC_CREFIN",
        "Net-(U14-REFCAPA)": "/POWER_IO/ADC_REFCAP",
    }
    return aliases.get(net, net)


def net_nodes(
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
) -> list[tuple[str, str, str, str]]:
    wanted = canon_net(net)
    return [
        node
        for raw_net, nodes in nets.items()
        if canon_net(raw_net) == wanted
        for node in nodes
    ]


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


def expected_lqfp64_pad_geometry() -> dict[str, tuple[str, tuple[float, float], tuple[float, float]]]:
    expected: dict[str, tuple[str, tuple[float, float], tuple[float, float]]] = {}
    for pin in range(1, 65):
        if 1 <= pin <= 16:
            at = (-5.675, -3.75 + (pin - 1) * 0.5)
            size = (1.55, 0.3)
        elif 17 <= pin <= 32:
            at = (-3.75 + (pin - 17) * 0.5, 5.675)
            size = (0.3, 1.55)
        elif 33 <= pin <= 48:
            at = (5.675, 3.75 - (pin - 33) * 0.5)
            size = (1.55, 0.3)
        else:
            at = (3.75 - (pin - 49) * 0.5, -5.675)
            size = (0.3, 1.55)
        expected[str(pin)] = ("smd", (round(at[0], 4), round(at[1], 4)), size)
    return expected


def check_component(failures: list[str], netlist_path: Path) -> None:
    components = {component["ref"]: component for component in parse_components(netlist_path)}
    component = components.get(ADC_REF)
    if component is None:
        failures.append(f"{ADC_REF}: missing from exported netlist")
        return
    actual = {key: component[key] for key in ("ref", "sheet", "value", "footprint", "mpn", "lcsc")}
    if actual != EXPECTED_COMPONENT:
        failures.append(f"{ADC_REF}: expected component identity {EXPECTED_COMPONENT}, got {actual}")

    for ref, expected in EXPECTED_SUPPORT_COMPONENTS.items():
        support = components.get(ref)
        if support is None:
            failures.append(f"{ref}: missing AD7606 support capacitor from exported netlist")
            continue
        actual_support = {key: support.get(key, "") for key in expected}
        if actual_support != expected:
            failures.append(f"{ref}: expected AD7606 support identity {expected}, got {actual_support}")


def check_schematic_nets(
    failures: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
) -> None:
    by_pin = pin_net_map(nets)
    for pin, expected_net in EXPECTED_PIN_NETS.items():
        actual = by_pin.get((ADC_REF, pin))
        if expected_net is None:
            if actual is None or actual.startswith("unconnected-"):
                continue
            failures.append(f"{ADC_REF}.{pin}: expected schematic no-connect, got {actual}")
        elif actual != canon_net(expected_net):
            failures.append(f"{ADC_REF}.{pin}: expected schematic net {expected_net}, got {actual or '<missing>'}")

    for net, expected_members in EXPECTED_EXACT_NETS.items():
        actual_members = node_pin_set(net_nodes(nets, net))
        if actual_members != expected_members:
            failures.append(f"{net}: expected members {sorted(expected_members)}, got {sorted(actual_members)}")

    for node, expected_net in EXPECTED_SUPPORT_PIN_NETS.items():
        actual = by_pin.get(node)
        if actual != canon_net(expected_net):
            ref, pin = node
            failures.append(f"{ref}.{pin}: expected schematic support net {expected_net}, got {actual or '<missing>'}")


def check_board(failures: list[str], board_path: Path) -> None:
    board_text = board_path.read_text()
    footprints = board_footprints(board_text)
    block = footprints.get(ADC_REF)
    if block is None:
        failures.append(f"{ADC_REF}: missing from PCB")
        return
    actual_footprint = footprint_name(block)
    if actual_footprint != "LQFP-64_10x10mm_P0.5mm":
        failures.append(f"{ADC_REF}: expected PCB footprint LQFP-64_10x10mm_P0.5mm, got {actual_footprint}")

    pads = board_pad_nets(board_text).get(ADC_REF, {})
    for pin, expected_net in EXPECTED_PIN_NETS.items():
        actual_nets = pads.get(pin, set())
        if expected_net is None:
            if actual_nets:
                failures.append(f"{ADC_REF}.{pin}: expected PCB pad to be unnetted, got {sorted(actual_nets)}")
        elif {canon_net(net) or net for net in actual_nets} != {canon_net(expected_net) or expected_net}:
            failures.append(f"{ADC_REF}.{pin}: expected PCB pad net {expected_net}, got {sorted(actual_nets)}")

    all_pads = board_pad_nets(board_text)
    for (ref, pin), expected_net in EXPECTED_SUPPORT_PIN_NETS.items():
        actual_nets = all_pads.get(ref, {}).get(pin, set())
        if {canon_net(net) or net for net in actual_nets} != {canon_net(expected_net) or expected_net}:
            failures.append(f"{ref}.{pin}: expected PCB pad net {expected_net}, got {sorted(actual_nets)}")


def check_lqfp64_geometry(failures: list[str]) -> None:
    if not LQFP64_FOOTPRINT.exists():
        failures.append(f"missing installed KiCad footprint: {LQFP64_FOOTPRINT}")
        return
    text = LQFP64_FOOTPRINT.read_text()
    if "(attr smd)" not in text:
        failures.append("LQFP-64 footprint is not marked SMD")
    actual = parse_footprint_pads(text)
    expected = expected_lqfp64_pad_geometry()
    if actual != expected:
        missing = sorted(set(expected) - set(actual), key=int)
        extra = sorted(set(actual) - set(expected), key=int)
        wrong = sorted(
            pin for pin in set(expected) & set(actual)
            if expected[pin] != actual[pin]
        )
        failures.append(
            "LQFP-64 pad geometry mismatch: "
            f"missing={missing}, extra={extra}, wrong={wrong[:20]}"
        )


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
    nets = parse_netlist(args.netlist)
    check_component(failures, args.netlist)
    check_schematic_nets(failures, nets)
    check_board(failures, args.board)
    check_lqfp64_geometry(failures)

    if failures:
        print(f"FAIL {len(failures)} AD7606 package/PCB checks")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS AD7606 package/PCB pinout: U14 AD7606BSTZ-4RL schematic pin nets, "
        "C51-C60 decoupling/reference support, current PCB pad nets, FRSTDATA no-connect, "
        "and KiCad LQFP-64 pad geometry agree"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
