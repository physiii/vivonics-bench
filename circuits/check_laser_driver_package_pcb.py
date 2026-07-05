#!/usr/bin/env python3
"""Check TLV9001/AO3400A laser-driver package nets against current PCB pads.

`check_laser_driver_control_loop.py` covers first-order control-loop topology
and gate-drive budget. This checker covers the package-risk layer: TLV9001 and
AO3400A pin nets, local driver support components, current PCB pad-net
assignments, and installed KiCad footprint geometry for the package-sensitive
parts.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_pcb_staging import blocks_named, board_pad_nets, footprint_ref
from circuit_designators import ref_for
from laser_command_limits import limiter_for_color


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")
SOT23_5_FOOTPRINT = Path("/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod")
SOT23_FOOTPRINT = Path("/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod")
R2512_FOOTPRINT = Path(
    "/usr/share/kicad/footprints/Resistor_SMD.pretty/R_2512_6332Metric_Pad1.40x3.35mm_HandSolder.kicad_mod"
)
R0603_FOOTPRINT = Path(
    "/usr/share/kicad/footprints/Resistor_SMD.pretty/R_0603_1608Metric_Pad0.98x0.95mm_HandSolder.kicad_mod"
)
C0402_FOOTPRINT = Path(
    "/usr/share/kicad/footprints/Capacitor_SMD.pretty/C_0402_1005Metric_Pad0.74x0.62mm_HandSolder.kicad_mod"
)
C0603_FOOTPRINT = Path(
    "/usr/share/kicad/footprints/Capacitor_SMD.pretty/C_0603_1608Metric_Pad1.08x0.95mm_HandSolder.kicad_mod"
)


@dataclass(frozen=True)
class Channel:
    color: str
    pwm_net: str
    pwm_pin: str
    isense_net: str
    isense_pin: str
    laser_n_net: str
    laser_vplus_pin: str
    laser_n_pin: str


CHANNELS = (
    Channel("IR", "PWM1", "18", "ISENSE1", "4", "LASER_N1", "2", "1"),
    Channel("RED", "PWM2", "19", "ISENSE2", "5", "LASER_N2", "2", "1"),
    Channel("GREEN", "PWM3", "20", "ISENSE3", "6", "LASER_N3", "2", "1"),
    Channel("BLUE", "PWM4", "9", "ISENSE4", "7", "LASER_N4", "1", "3"),
)


EXPECTED_BOARD_FOOTPRINTS: dict[str, str] = {}
EXPECTED_COMPONENTS: dict[str, dict[str, str]] = {}
EXPECTED_PIN_NETS: dict[str, dict[str, str]] = {}
EXPECTED_EXACT_NETS: dict[str, set[tuple[str, str]]] = {}
EXPECTED_REQUIRED_NET_MEMBERS: dict[str, set[tuple[str, str]]] = {
    "+5V": set(),
    "GND": set(),
    "LASER_V+": set(),
}


def add_component(
    ref: str,
    *,
    sheet: str,
    value: str,
    footprint: str,
    mpn: str,
    lcsc: str,
    board_footprint: str,
) -> None:
    EXPECTED_COMPONENTS[ref] = {
        "sheet": sheet,
        "value": value,
        "footprint": footprint,
        "mpn": mpn,
        "lcsc": lcsc,
    }
    EXPECTED_BOARD_FOOTPRINTS[ref] = board_footprint


for channel in CHANNELS:
    sheet_name = f"LASER_{channel.color}"
    sheet_path = f"/{sheet_name}/"
    tlv = ref_for(sheet_name, "U11")
    mosfet = ref_for(sheet_name, "Q1")
    gate_r = ref_for(sheet_name, "R31")
    sense_r = ref_for(sheet_name, "R11")
    isense_r = ref_for(sheet_name, "R12")
    decouple_c = ref_for(sheet_name, "C22")
    pwm_r = ref_for(sheet_name, "R21")
    pulldown_r = ref_for(sheet_name, "R22")
    limiter = limiter_for_color(channel.color)
    pwm_c = ref_for(sheet_name, "C21")
    comp_c = ref_for(sheet_name, "CC")
    ld = ref_for(sheet_name, "LD")
    plus_net = f"Net-({tlv}-+)"
    lout_net = f"/{sheet_name}/LOUT"
    fb_net = f"/{sheet_name}/FB"
    gate_net = f"Net-({mosfet}-G)"

    add_component(
        tlv,
        sheet=sheet_path,
        value="TLV9001",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
        mpn="TLV9001IDBVR",
        lcsc="C398363",
        board_footprint="SOT-23-5",
    )
    add_component(
        mosfet,
        sheet=sheet_path,
        value="AO3400A",
        footprint="Package_TO_SOT_SMD:SOT-23",
        mpn="AO3400A",
        lcsc="C20917",
        board_footprint="SOT-23",
    )
    add_component(
        gate_r,
        sheet=sheet_path,
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        mpn="FRC0603F1001TS",
        lcsc="C2907002",
        board_footprint="R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
    )
    add_component(
        sense_r,
        sheet=sheet_path,
        value="10R 2W",
        footprint="Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder",
        mpn="HoCR2512-2W-10R-1%",
        lcsc="C5123624",
        board_footprint="R_2512_6332Metric_Pad1.40x3.35mm_HandSolder",
    )
    add_component(
        isense_r,
        sheet=sheet_path,
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        mpn="FRC0603F1001TS",
        lcsc="C2907002",
        board_footprint="R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
    )
    add_component(
        decouple_c,
        sheet=sheet_path,
        value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        mpn="0402B104K160CT",
        lcsc="C83056",
        board_footprint="C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
    )
    add_component(
        pwm_r,
        sheet=sheet_path,
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        mpn="CRCW060310K0FKEA",
        lcsc="C844918",
        board_footprint="R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
    )
    add_component(
        pulldown_r,
        sheet=sheet_path,
        value=limiter.value,
        footprint="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        mpn=limiter.mpn,
        lcsc=limiter.lcsc,
        board_footprint="R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
    )
    add_component(
        pwm_c,
        sheet=sheet_path,
        value="1uF",
        footprint="Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        mpn="HGC0402R5105K250NTEJ",
        lcsc="C7472946",
        board_footprint="C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
    )
    add_component(
        comp_c,
        sheet=sheet_path,
        value="10pF C0G",
        footprint="Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder",
        mpn="CC0603JRNPO9BN100",
        lcsc="C106245",
        board_footprint="C_0603_1608Metric_Pad1.08x0.95mm_HandSolder",
    )

    EXPECTED_PIN_NETS[tlv] = {
        "1": lout_net,
        "2": "GND",
        "3": plus_net,
        "4": fb_net,
        "5": "+5V",
    }
    EXPECTED_PIN_NETS[mosfet] = {"1": gate_net, "2": fb_net, "3": channel.laser_n_net}
    EXPECTED_PIN_NETS[gate_r] = {"1": lout_net, "2": gate_net}
    EXPECTED_PIN_NETS[sense_r] = {"1": fb_net, "2": "GND"}
    EXPECTED_PIN_NETS[isense_r] = {"1": fb_net, "2": channel.isense_net}
    EXPECTED_PIN_NETS[decouple_c] = {"1": "+5V", "2": "GND"}
    EXPECTED_PIN_NETS[pwm_r] = {"1": channel.pwm_net, "2": plus_net}
    EXPECTED_PIN_NETS[pulldown_r] = {"1": plus_net, "2": "GND"}
    EXPECTED_PIN_NETS[pwm_c] = {"1": plus_net, "2": "GND"}
    EXPECTED_PIN_NETS[comp_c] = {"1": fb_net, "2": lout_net}

    EXPECTED_EXACT_NETS[channel.pwm_net] = {("U9", channel.pwm_pin), (pwm_r, "1")}
    EXPECTED_EXACT_NETS[plus_net] = {(pwm_c, "1"), (pwm_r, "2"), (pulldown_r, "1"), (tlv, "3")}
    EXPECTED_EXACT_NETS[lout_net] = {(comp_c, "2"), (gate_r, "1"), (tlv, "1")}
    EXPECTED_EXACT_NETS[gate_net] = {(gate_r, "2"), (mosfet, "1")}
    EXPECTED_EXACT_NETS[fb_net] = {(comp_c, "1"), (mosfet, "2"), (sense_r, "1"), (isense_r, "1"), (tlv, "4")}
    EXPECTED_EXACT_NETS[channel.isense_net] = {("U9", channel.isense_pin), (isense_r, "2")}
    EXPECTED_EXACT_NETS[channel.laser_n_net] = {(ld, channel.laser_n_pin), (mosfet, "3")}
    EXPECTED_REQUIRED_NET_MEMBERS["+5V"].update({(tlv, "5"), (decouple_c, "1")})
    EXPECTED_REQUIRED_NET_MEMBERS["GND"].update({(tlv, "2"), (decouple_c, "2"), (sense_r, "2"), (pulldown_r, "2"), (pwm_c, "2")})
    EXPECTED_REQUIRED_NET_MEMBERS["LASER_V+"].add((ld, channel.laser_vplus_pin))


EXPECTED_SOT23_5_PADS = {
    "1": ("smd", (-1.1375, -0.95), (1.325, 0.6)),
    "2": ("smd", (-1.1375, 0.0), (1.325, 0.6)),
    "3": ("smd", (-1.1375, 0.95), (1.325, 0.6)),
    "4": ("smd", (1.1375, 0.95), (1.325, 0.6)),
    "5": ("smd", (1.1375, -0.95), (1.325, 0.6)),
}
EXPECTED_SOT23_PADS = {
    "1": ("smd", (-0.9375, -0.95), (1.475, 0.6)),
    "2": ("smd", (-0.9375, 0.95), (1.475, 0.6)),
    "3": ("smd", (0.9375, 0.0), (1.475, 0.6)),
}
EXPECTED_R2512_PADS = {
    "1": ("smd", (-3.05, 0.0), (1.4, 3.35)),
    "2": ("smd", (3.05, 0.0), (1.4, 3.35)),
}
EXPECTED_R0603_PADS = {
    "1": ("smd", (-0.9125, 0.0), (0.975, 0.95)),
    "2": ("smd", (0.9125, 0.0), (0.975, 0.95)),
}
EXPECTED_C0402_PADS = {
    "1": ("smd", (-0.5675, 0.0), (0.735, 0.62)),
    "2": ("smd", (0.5675, 0.0), (0.735, 0.62)),
}
EXPECTED_C0603_PADS = {
    "1": ("smd", (-0.8625, 0.0), (1.075, 0.95)),
    "2": ("smd", (0.8625, 0.0), (1.075, 0.95)),
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
    check_footprint_geometry(failures, SOT23_5_FOOTPRINT, EXPECTED_SOT23_5_PADS)
    check_footprint_geometry(failures, SOT23_FOOTPRINT, EXPECTED_SOT23_PADS)
    check_footprint_geometry(failures, R2512_FOOTPRINT, EXPECTED_R2512_PADS)
    check_footprint_geometry(failures, R0603_FOOTPRINT, EXPECTED_R0603_PADS)
    check_footprint_geometry(failures, C0402_FOOTPRINT, EXPECTED_C0402_PADS)
    check_footprint_geometry(failures, C0603_FOOTPRINT, EXPECTED_C0603_PADS)

    if failures:
        print(f"FAIL laser-driver package/PCB guard: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS laser-driver package/PCB guard: TLV9001/AO3400A schematic pin nets, local driver "
        "sense/command/gate/compensation component identities, current PCB pad nets, and KiCad "
        "SOT-23-5/SOT-23/2512/0603/0402/0603-cap geometry agree."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
