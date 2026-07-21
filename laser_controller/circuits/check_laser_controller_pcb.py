#!/usr/bin/env python3
"""Board-level pad-net checks for the generated bench laser controller PCB.

This verifies that the placement-only PCB carries the same explicit pad-net
assignments that `gen_pcb.py` derives from the exported KiCad schematic netlist.

Run after:
  kicad-cli sch export netlist laser_controller.kicad_sch -o /tmp/lc.net
  LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 gen_pcb.py
"""
from __future__ import annotations

import re
import json
import os
import sys
from collections import Counter, defaultdict, deque
from math import cos, hypot, radians, sin
from pathlib import Path

import gen_pcb
from circuit_designators import WL, ref_for
from pcb_critical_routes import (
    CRITICAL_ROUTE_LINKS,
    MIN_ROUTED_CRITICAL_LINKS,
    _pad_bbox,
    _point_in_pad,
    parse_pad_geometry_from_text,
)

BOARD_WIDTH_MM = float(gen_pcb.BOARD_W_MM)
BOARD_HEIGHT_MM = float(gen_pcb.BOARD_H_MM)
BOARD_SIZE_TOLERANCE_MM = 0.05
ZONE_OR_RAIL_NETS = {"+5V", "+3V3", "GND", "VBUS_5V", "VIN_24V", "/POWER_IO/BUCK_5V", "LASER_V+"}
EXPECTED_ZONE_OR_RAIL_PENDING_NETS = {"+5V", "+3V3", "GND", "VBUS_5V", "VIN_24V", "/POWER_IO/BUCK_5V", "LASER_V+"}
ZONE_OR_RAIL_NETS.add("LASER_VP")
EXPECTED_ZONE_OR_RAIL_PENDING_NETS.add("LASER_VP")
RAIL_PAD_VIA_TARGETS = {
    "GND": {"In1.Cu"},
    "+3V3": {"In2.Cu"},
    "+5V": {"In2.Cu", "B.Cu"},
}
RAIL_PAD_MAX_VIA_DISTANCE_MM = 1.2
ADDITIONAL_POWER_PAD_VIA_TARGETS = {
    "LASER_V+",
    "VBUS_5V",
    "VIN_24V",
    "/POWER_IO/BUCK_5V",
    "Net-(D10-A)",
    "Net-(D13-A)",
    "LASER_N1",
    "LASER_N2",
    "LASER_N3",
    "LASER_N4",
}
ADDITIONAL_POWER_PAD_MAX_VIA_DISTANCE_MM = RAIL_PAD_MAX_VIA_DISTANCE_MM
REQUIRED_PLANE_ZONES = {
    "GND": {"In1.Cu"},
    "+3V3": {"In2.Cu"},
    "+5V": {"In2.Cu"},
}
USB_ROUTE_CHAINS = {
    "USB-UART D-": [
        ("J1 D- to CP2102N D-", "/MCU_ESP32-S3/D-"),
    ],
    "USB-UART D+": [
        ("J1 D+ to CP2102N D+", "/MCU_ESP32-S3/D+"),
    ],
    "Native USB D-": [
        ("J2 D- to ESP32 GPIO19", "/MCU_ESP32-S3/IO19"),
    ],
    "Native USB D+": [
        ("J2 D+ to ESP32 GPIO20", "/MCU_ESP32-S3/IO20"),
    ],
}
USB_ROUTE_NET_NAMES = {
    net_name
    for chain_entries in USB_ROUTE_CHAINS.values()
    for _, net_name in chain_entries
}
USB_PAIR_CHAINS = [
    ("USB-UART", "USB-UART D-", "USB-UART D+"),
    ("Native USB", "Native USB D-", "Native USB D+"),
]
USB_ROUTE_LAYER = "F.Cu"
USB_ROUTE_WIDTH_MM = 0.25
USB_CHAIN_MAX_LENGTH_MM = 40.0
USB_PAIR_MAX_SKEW_MM = 5.0
USB_CHAIN_MAX_VIAS = 0
USB_CHAIN_VIA_LIMIT_OVERRIDES = {
    "USB-UART D-": 2,
}
USB_CHAIN_LAYER_OVERRIDES = {
    "USB-UART D-": {"F.Cu", "B.Cu"},
}
BACK_LAYER_UNDERPASS_VIA_LIMITS = {
    "/MCU_ESP32-S3/D-": 2,
    "Net-(D1-K)": 2,
    "Net-(U6-+)": 2,
}


def footprint_blocks(board_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in board_text.splitlines():
        if not in_block and line.lstrip().startswith("(footprint "):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def pad_blocks(footprint_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in footprint_text.splitlines():
        if not in_block and line.lstrip().startswith("(pad "):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            if depth == 0:
                blocks.append(line)
                in_block = False
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def graphic_blocks(board_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in board_text.splitlines():
        stripped = line.lstrip()
        if not in_block and stripped.startswith(
            ("(gr_line", "(gr_rect", "(gr_arc", "(gr_circle", "(gr_poly")
        ):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            if depth == 0:
                blocks.append(line)
                in_block = False
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def parse_board_outline_bounds(board_path: Path) -> tuple[tuple[float, float, float, float], bool]:
    coords: list[tuple[float, float]] = []
    for block in graphic_blocks(board_path.read_text()):
        if '(layer "Edge.Cuts")' not in block:
            continue
        coords.extend(
            (float(match.group(1)), float(match.group(2)))
            for match in re.finditer(
                r'\((?:start|end|xy|center|mid)\s+([-\d.]+)\s+([-\d.]+)\)',
                block,
            )
        )
    if not coords:
        return (
            gen_pcb.BOARD_X0_MM,
            gen_pcb.BOARD_Y0_MM,
            gen_pcb.BOARD_X1_MM,
            gen_pcb.BOARD_Y1_MM,
        ), False
    return (
        min(x for x, _ in coords),
        min(y for _, y in coords),
        max(x for x, _ in coords),
        max(y for _, y in coords),
    ), True


def board_bounds_label(board_bounds: tuple[float, float, float, float]) -> str:
    min_x, min_y, max_x, max_y = board_bounds
    return (
        f"{max_x - min_x:.0f}x{max_y - min_y:.0f} mm board "
        f"at x={min_x:.3f}..{max_x:.3f}, y={min_y:.3f}..{max_y:.3f}"
    )


def _net_name_from_text(text: str, net_by_code: dict[int, str] | None = None) -> tuple[int | None, str]:
    direct = re.search(r'\(net\s+"([^"]*)"\)', text)
    if direct:
        return None, direct.group(1)
    coded_named = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', text)
    if coded_named:
        return int(coded_named.group(1)), coded_named.group(2)
    coded = re.search(r'\(net\s+(\d+)\)', text)
    if coded:
        code = int(coded.group(1))
        return code, net_by_code.get(code, "") if net_by_code is not None else ""
    return None, ""


def parse_board_pad_nets(board_path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    board_text = board_path.read_text()
    pad_nets: dict[str, dict[str, str]] = {}
    duplicate_refs: list[str] = []
    for block in footprint_blocks(board_text):
        ref = gen_pcb.fp_ref(block)
        if not ref:
            continue
        if ref in pad_nets:
            duplicate_refs.append(ref)
            continue
        pads: dict[str, str] = {}
        for pad in pad_blocks(block):
            pad_match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
            _, net_name = _net_name_from_text(pad)
            if pad_match and net_name:
                pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
                pads[pad_name] = net_name
        pad_nets[ref] = pads
    return pad_nets, duplicate_refs


def parse_board_pad_inventory(board_path: Path) -> dict[str, list[tuple[str, str]]]:
    inventory: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for block in footprint_blocks(board_path.read_text()):
        ref = gen_pcb.fp_ref(block)
        if not ref:
            continue
        for pad in pad_blocks(block):
            pad_match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
            if not pad_match:
                continue
            pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
            _, net_name = _net_name_from_text(pad)
            inventory[ref].append((pad_name, net_name))
    return inventory


def parse_footprint_geometry(board_path: Path) -> dict[str, dict[str, object]]:
    geometry: dict[str, dict[str, object]] = {}
    for block in footprint_blocks(board_path.read_text()):
        ref = gen_pcb.fp_ref(block)
        at_match = re.search(r'\n\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
        if not ref or not at_match:
            continue
        gx = float(at_match.group(1))
        gy = float(at_match.group(2))
        grot = float(at_match.group(3) or 0)
        theta = radians(grot)
        pads: dict[str, list[tuple[float, float]]] = {}
        for pad in pad_blocks(block):
            pad_match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
            at = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', pad)
            if not pad_match or not at:
                continue
            pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
            lx = float(at.group(1))
            ly = float(at.group(2))
            pads.setdefault(pad_name, []).append(
                (
                    gx + lx * cos(theta) + ly * sin(theta),
                    gy - lx * sin(theta) + ly * cos(theta),
                )
            )
        geometry[ref] = {"origin": (gx, gy), "pads": pads}
    return geometry


def min_pad_distance(
    geometry: dict[str, dict[str, object]],
    ref_a: str,
    pin_a: str,
    ref_b: str,
    pin_b: str,
) -> float:
    pads_a = geometry.get(ref_a, {}).get("pads", {}).get(pin_a, [])
    pads_b = geometry.get(ref_b, {}).get("pads", {}).get(pin_b, [])
    if not pads_a or not pads_b:
        raise KeyError(f"missing pad geometry for {ref_a}.{pin_a} or {ref_b}.{pin_b}")
    return min(hypot(ax - bx, ay - by) for ax, ay in pads_a for bx, by in pads_b)


def intentional_unnetted_pad_names(
    board_ref_by_comp: dict[tuple[str, str], str],
) -> dict[str, set[str]]:
    def board_ref(sheet: str, local_ref: str) -> str:
        return board_ref_by_comp[(sheet, ref_for(sheet, local_ref))]

    allowed: dict[str, set[str]] = defaultdict(set)
    for color in WL:
        allowed[board_ref(f"TIA_{color}", "D1")].add("")  # SFH2201 paste-only pads.
        allowed[board_ref(f"TIA_{color}", "U1")].update({"1", "5", "8"})  # OPA380 NC.
    allowed[board_ref("MCU_ESP32-S3", "J1")].update({"", "4"})  # Mini-B NPTH + USB ID.
    allowed[board_ref("MCU_ESP32-S3", "J2")].update({"", "4"})  # Mini-B NPTH + USB ID.
    allowed[board_ref("POWER_IO", "JRJ45")].update(
        {
            "",  # Shielded RJ45 NPTH locator holes.
            "1",
            "2",
            "3",
            "6",
            "SH",  # Shield tabs are intentionally isolated in this power-input footprint.
        }
    )
    allowed[board_ref("MCU_ESP32-S3", "U10")].update(
        {
            "",  # CP2102N exposed-pad paste apertures.
            "1",
            "2",
            "10",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
            "23",
            "27",
        }
    )
    allowed[board_ref("POWER_IO", "U3V3")].add("4")  # AP2112 NC.
    allowed[board_ref("POWER_IO", "UADC")].add("15")  # AD7606 FRSTDATA unused in serial mode.
    allowed[board_ref("LASER_BLUE", "LD")].add("2")  # PLT5 450GB case pad is isolated.
    allowed[board_ref("MCU_ESP32-S3", "U9")].update(
        {
            "",  # ESP32 paste-only thermal-pad stencil apertures.
            "8",
            "11",
            "15",
            "16",
            "18",
            "19",
            "20",
            "23",
            "24",
            "25",
            "26",
            "28",
            "29",
            "30",
            "32",
            "33",
            "34",
            "35",
        }
    )
    return allowed


def parse_board_net_table(board_path: Path) -> dict[str, int]:
    board_text = board_path.read_text()
    table: dict[str, int] = {}
    for code, name in re.findall(r'\(net\s+(\d+)\s+"([^"]*)"\)', board_text):
        if name:
            table[name] = int(code)
    next_code = max(table.values(), default=0) + 1
    for name in re.findall(r'\(net\s+"([^"]*)"\)', board_text):
        if name and name not in table:
            table[name] = next_code
            next_code += 1
    return table


def parse_board_segments(board_path: Path, net_by_code: dict[int, str]) -> list[dict[str, object]]:
    segments: list[dict[str, object]] = []
    text = board_path.read_text()
    pattern = re.compile(
        r'\(segment\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(width\s+([-\d.]+)\)\s+\(layer\s+"([^"]+)"\)\s+'
        r'\(net\s+(?:(\d+)(?:\s+"([^"]*)")?|"([^"]*)")\)'
    )
    for match in pattern.finditer(text):
        net_code = int(match.group(7)) if match.group(7) is not None else None
        net_name = (
            match.group(9)
            if match.group(9) is not None
            else match.group(8)
            if match.group(8) is not None
            else net_by_code.get(net_code, "") if net_code is not None else ""
        )
        segments.append(
            {
                "a": (float(match.group(1)), float(match.group(2))),
                "b": (float(match.group(3)), float(match.group(4))),
                "width": float(match.group(5)),
                "layer": match.group(6),
                "net_code": net_code,
                "net": net_name,
            }
        )
    return segments


def laser_current_width_review_failures(segments: list[dict[str, object]]) -> tuple[list[str], int]:
    failures: list[str] = []
    checked = 0
    for segment in segments:
        net = str(segment["net"])
        if gen_pcb.classify_net(net) != "Laser_Current":
            continue
        checked += 1
        width = float(segment["width"])
        if width >= 0.60:
            continue
        if net.endswith("/FB") and any(abs(width - allowed) < 1e-9 for allowed in (0.20, 0.60)):
            continue
        failures.append(
            f"unexpected narrow Laser_Current copper: {net} {segment['layer']} {width:.2f}mm {segment['a']}->{segment['b']}"
        )
    return failures, checked


def sensitive_to_laser_clearance_failures(
    segments: list[dict[str, object]],
) -> tuple[list[str], list[tuple[str, int, float | None, float]]]:
    """Review same-layer spacing from sensitive analog/telemetry copper to laser current copper."""
    rules = [
        (
            "TIA_Sensitive",
            2.00,
            lambda net: gen_pcb.classify_net(net) == "TIA_Sensitive",
        ),
        (
            "MPD_RAW",
            0.50,
            lambda net: "MPD_RAW" in net,
        ),
        (
            "Monitor_ADC",
            0.25,
            lambda net: gen_pcb.classify_net(net) == "Monitor_ADC" and "MPD_RAW" not in net,
        ),
    ]
    laser_segments = [
        segment
        for segment in segments
        if gen_pcb.classify_net(str(segment["net"])) == "Laser_Current"
    ]
    failures: list[str] = []
    summary: list[tuple[str, int, float | None, float]] = []
    for label, required_gap, predicate in rules:
        checked = 0
        min_gap: float | None = None
        for sensitive in segments:
            sensitive_net = str(sensitive["net"])
            if not predicate(sensitive_net):
                continue
            for laser in laser_segments:
                if sensitive["net"] == laser["net"] or sensitive["layer"] != laser["layer"]:
                    continue
                a = sensitive["a"]
                b = sensitive["b"]
                c = laser["a"]
                d = laser["b"]
                assert isinstance(a, tuple) and isinstance(b, tuple) and isinstance(c, tuple) and isinstance(d, tuple)
                center_distance = _dist_segment_segment(a, b, c, d)
                edge_gap = center_distance - (float(sensitive["width"]) + float(laser["width"])) / 2
                checked += 1
                if min_gap is None or edge_gap < min_gap:
                    min_gap = edge_gap
                if edge_gap < required_gap - 1e-6:
                    failures.append(
                        f"{label} copper too close to Laser_Current on {sensitive['layer']}: "
                        f"{sensitive_net} {a}->{b} vs {laser['net']} {c}->{d}, "
                        f"edge gap {edge_gap:.3f} mm < {required_gap:.3f} mm"
                    )
        summary.append((label, checked, min_gap, required_gap))
    return failures, summary


def format_sensitive_to_laser_summary(summary: list[tuple[str, int, float | None, float]]) -> str:
    parts = []
    for label, checked, min_gap, required_gap in summary:
        if min_gap is None:
            parts.append(f"{label}:0")
        else:
            parts.append(f"{label}:{checked} min {min_gap:.3f}/{required_gap:.2f}mm")
    return "; ".join(parts)


def parse_board_vias(board_path: Path, net_by_code: dict[int, str]) -> list[dict[str, object]]:
    vias: list[dict[str, object]] = []
    text = board_path.read_text()
    pattern = re.compile(
        r'\(via(?:\s+(micro|blind|buried))?\s+\(at\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(size\s+([-\d.]+)\)\s+\(drill\s+([-\d.]+)\)\s+'
        r'\(layers\s+"([^"]+)"\s+"([^"]+)"\).*?'
        r'\(net\s+(?:(\d+)(?:\s+"([^"]*)")?|"([^"]*)")\)',
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        net_code = int(match.group(8)) if match.group(8) is not None else None
        net_name = (
            match.group(10)
            if match.group(10) is not None
            else match.group(9)
            if match.group(9) is not None
            else net_by_code.get(net_code, "") if net_code is not None else ""
        )
        vias.append(
            {
                "at": (float(match.group(2)), float(match.group(3))),
                "size": float(match.group(4)),
                "drill": float(match.group(5)),
                "layers": {match.group(6), match.group(7)},
                "net_code": net_code,
                "net": net_name,
                "type": match.group(1) or "through",
            }
        )
    return vias


def duplicate_via_failures(vias: list[dict[str, object]]) -> list[str]:
    counts: Counter[tuple[str, tuple[float, float], float, float, tuple[str, ...]]] = Counter()
    for via in vias:
        point = via["at"]
        assert isinstance(point, tuple)
        key = (
            str(via["net"]),
            (round(point[0], 4), round(point[1], 4)),
            float(via["size"]),
            float(via["drill"]),
            tuple(sorted(via["layers"])),
        )
        counts[key] += 1
    failures: list[str] = []
    for net, point, size, drill, layers in sorted(key for key, count in counts.items() if count > 1):
        failures.append(
            f"duplicate via stack: {net} at {point} {size:.2f}/{drill:.2f}mm layers={list(layers)} "
            f"appears {counts[(net, point, size, drill, layers)]} times"
        )
    return failures


def _via_limit_for_net(net_name: str) -> int | None:
    if gen_pcb.classify_net(net_name) == "Power_Rails":
        return None
    if net_name in {"LASER_V+", "LASER_VP"}:
        return None
    if net_name in BACK_LAYER_UNDERPASS_VIA_LIMITS:
        # Narrow exceptions for DRC-clean underpasses where the same-layer
        # route would otherwise create a physical copper crossing.
        return BACK_LAYER_UNDERPASS_VIA_LIMITS[net_name]
    if re.match(r"^/POWER_IO/MPD_RAW[1-4]$", net_name):
        return 0
    if re.match(r"^Net-\(D[1-4]-[AK]\)$", net_name):
        return 0
    if re.match(r"^Net-\(U[1-8]-\+\)$", net_name):
        return 0
    if re.match(r"^Net-\(Q[1-4]-G\)$", net_name):
        return 0
    if re.match(r"^Net-\(R(4|8|12|16)-Pad2\)$", net_name):
        return 0
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/(FB|LOUT)$", net_name):
        return 0
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/CMD_FILTER$", net_name):
        return 2
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/GATE$", net_name):
        return 2
    if re.match(r"^/TIA_(IR|RED|GREEN|BLUE)/PD_ANODE$", net_name):
        return 1
    if re.match(r"^/TIA_(IR|RED|GREEN|BLUE)/PD_CATHODE$", net_name):
        return 2
    if re.match(r"^/TIA_(IR|RED|GREEN|BLUE)/VBIAS(?:_TOP|_WIPER)?$", net_name):
        return 2
    if net_name in USB_ROUTE_NET_NAMES or re.match(r"^/MCU_ESP32-S3/USB_D[MP](_CONN|_ESD)?$", net_name):
        return 0
    # Board-spanning low-speed/control nets may use explicit four-layer escape
    # budgets; keep local laser/TIA/USB routes under the stricter rules above.
    if re.match(r"^/MCU_ESP32-S3/(DTR|EN|FACT|IO43|IO44|PROG|RTS)$", net_name):
        return {
            "/MCU_ESP32-S3/DTR": 3,
            "/MCU_ESP32-S3/EN": 4,
            "/MCU_ESP32-S3/FACT": 2,
            "/MCU_ESP32-S3/IO43": 2,
            "/MCU_ESP32-S3/IO44": 2,
            "/MCU_ESP32-S3/PROG": 4,
            "/MCU_ESP32-S3/RTS": 4,
        }[net_name]
    if net_name == "/MCU_ESP32-S3/CP2102_RST":
        return 2
    if net_name == "/POWER_IO/RJ45_LED_CONTACT":
        return 1
    if re.match(r"^ADC_(BUSY|CS|MISO_A|MISO_B|RESET|SCLK)$", net_name):
        return 2
    if net_name == "/POWER_IO/MPD_BIAS":
        # Board-spanning monitor-PD bias uses an explicit back-layer escape to
        # avoid the front-layer TIA/telemetry fanout corridor.
        return 4
    if net_name in {
        "/POWER_IO/MPD_AMP3",
        "Net-(U10-~{RST})",
    }:
        return 2
    if re.match(r"^MPD_RAW[1-4]$", net_name):
        return 4 if net_name in {"MPD_RAW1", "MPD_RAW2"} else 2
    if re.match(r"^VOUT[1-4]$", net_name):
        return 4 if net_name == "VOUT2" else 2
    if re.match(r"^Net-\(RV[1-4]-W\)$", net_name):
        return 2
    if re.match(r"^MPD[1-4]$", net_name):
        return 2
    if re.match(r"^ISENSE[1-4]$", net_name):
        return 6
    if re.match(r"^PWM[1-4]$", net_name):
        return 8
    if net_name in {
        "/MCU_ESP32-S3/ESP_BOOT",
        "/MCU_ESP32-S3/ESP_EN",
        "CONVST",
    }:
        return 2
    if net_name in {
        "/MCU_ESP32-S3/ESP_RX",
        "/MCU_ESP32-S3/ESP_TX",
    }:
        return 1
    if net_name in {
        "Net-(J6-Pad10)",
        "Net-(J6-Pad12)",
    }:
        return 2
    if net_name in {"LASER_N1", "LASER_N2", "LASER_N3", "LASER_N4"}:
        return 1
    if net_name == "LASER_V+":
        return 2
    return 0


ALL_COPPER_ROUTE_LAYERS = {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"}


def route_via_policy_failures(vias: list[dict[str, object]]) -> tuple[list[str], dict[str, int]]:
    via_counts = Counter(str(via["net"]) for via in vias)
    failures: list[str] = []
    checked_non_power = 0
    for net_name, count in sorted(via_counts.items()):
        limit = _via_limit_for_net(net_name)
        if limit is None:
            continue
        checked_non_power += count
        if count > limit:
            failures.append(
                f"{net_name}: {count} vias exceeds route policy limit {limit} "
                f"for {gen_pcb.classify_net(net_name)}"
            )
    return failures, {"non_power_vias_checked": checked_non_power}


def _allowed_route_layers_for_net(net_name: str) -> set[str]:
    if gen_pcb.classify_net(net_name) in {"Power_Rails", "Switching_Power", "Switcher_Control"}:
        return set(ALL_COPPER_ROUTE_LAYERS)
    if net_name in {"LASER_V+", "LASER_VP"}:
        return set(ALL_COPPER_ROUTE_LAYERS)
    if re.match(r"^(?:PWM|VOUT|ISENSE)[1-4]$", net_name):
        return set(ALL_COPPER_ROUTE_LAYERS)
    if re.match(r"^/TIA_(IR|RED|GREEN|BLUE)/(?:PD_CATHODE|VBIAS(?:_TOP|_WIPER)?)$", net_name):
        return set(ALL_COPPER_ROUTE_LAYERS)
    if net_name in BACK_LAYER_UNDERPASS_VIA_LIMITS:
        return {"F.Cu", "B.Cu"}
    if net_name in USB_ROUTE_NET_NAMES or re.match(r"^/MCU_ESP32-S3/USB_D[MP](_CONN|_ESD)?$", net_name):
        return {"F.Cu"}
    if re.match(r"^/POWER_IO/MPD_RAW[1-4]$", net_name):
        return {"F.Cu"}
    if re.match(r"^Net-\(D[1-4]-[AK]\)$", net_name):
        return {"F.Cu"}
    if re.match(r"^Net-\(U[1-4]-\+\)$", net_name):
        return {"F.Cu"}
    if re.match(r"^Net-\(R(4|8|12|16)-Pad2\)$", net_name):
        return {"F.Cu"}
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/(FB|LOUT)$", net_name):
        return {"F.Cu"}
    if re.match(r"^Net-\(Q[1-4]-G\)$", net_name):
        return {"F.Cu"}
    if re.match(r"^Net-\(U[5-8]-\+\)$", net_name):
        return {"F.Cu"}
    if net_name == "LASER_N2":
        return {"F.Cu", "B.Cu"}
    if net_name in {"LASER_N1", "LASER_N3", "LASER_N4", "LASER_V+"}:
        return {"F.Cu", "B.Cu"}
    if net_name == "VIN_24V":
        return {"F.Cu", "B.Cu"}
    if net_name == "/POWER_IO/BUCK_5V":
        return {"F.Cu"}
    if net_name == "VBUS_5V":
        return {"F.Cu", "B.Cu"}
    if net_name == "+3V3":
        return {"F.Cu", "B.Cu"}
    if net_name == "+5V":
        return set(ALL_COPPER_ROUTE_LAYERS)
    if net_name == "GND":
        return set(ALL_COPPER_ROUTE_LAYERS)
    return {"F.Cu", "B.Cu"}


def route_layer_policy_failures(segments: list[dict[str, object]]) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    checked = 0
    for segment in segments:
        checked += 1
        net_name = str(segment["net"])
        layer = str(segment["layer"])
        allowed_layers = _allowed_route_layers_for_net(net_name)
        if layer not in allowed_layers:
            failures.append(
                f"{net_name}: routed segment on {layer} violates layer policy "
                f"{sorted(allowed_layers)} at {segment['a']}->{segment['b']}"
            )
    return failures, {"route_segments_checked": checked}


def _allowed_route_widths_for_net(net_name: str) -> set[float]:
    if net_name in USB_ROUTE_NET_NAMES or re.match(r"^/MCU_ESP32-S3/USB_D[MP](_CONN|_ESD)?$", net_name):
        return {0.25}
    if net_name in {"LASER_V+", "LASER_VP"}:
        return {0.80, 1.00}
    if re.match(r"^LASER_N[1-4]$", net_name):
        return {0.60}
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/FB$", net_name):
        return {0.20, 0.60}
    if gen_pcb.classify_net(net_name) == "Switching_Power":
        return {0.40}
    if gen_pcb.classify_net(net_name) == "Switcher_Control":
        return {0.20}
    if net_name == "VIN_24V":
        return {0.30, 0.60}
    if net_name in {"Net-(D10-A)", "Net-(D13-A)"}:
        return {0.50}
    if net_name == "/POWER_IO/BUCK_5V":
        return {0.60}
    if net_name == "VBUS_5V" or gen_pcb.classify_net(net_name) == "Power_Rails":
        return {0.15, 0.20, 0.22, 0.25, 0.30, 0.50, 0.60, 0.80, 1.00}
    if net_name == "+3V3":
        return {0.25, 0.35, 0.50}
    if net_name == "+5V":
        return {0.15, 0.20, 0.25, 0.50, 0.60}
    if net_name == "GND":
        return {0.20, 0.22, 0.25, 0.30, 0.50, 0.60, 0.80, 1.00}
    if re.match(r"^/TIA_(IR|RED|GREEN|BLUE)/PD_(?:ANODE|CATHODE)$", net_name):
        return {0.18, 0.20}
    if re.match(r"^Net-\(D[1-4]-K\)$", net_name):
        return {0.20, 0.25}
    return {0.20}


def route_width_policy_failures(segments: list[dict[str, object]]) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    checked = 0
    for segment in segments:
        checked += 1
        net_name = str(segment["net"])
        width = round(float(segment["width"]), 2)
        allowed_widths = _allowed_route_widths_for_net(net_name)
        if width not in allowed_widths:
            allowed_text = ", ".join(f"{allowed:.2f}" for allowed in sorted(allowed_widths))
            failures.append(
                f"{net_name}: routed segment width {width:.2f}mm violates width policy "
                f"{{{allowed_text}}} at {segment['a']}->{segment['b']}"
            )
    return failures, {"route_segments_checked": checked}


BOARD_ROUTE_LENGTH_LIMITS_MM = {
    # Board-specific ceilings for accepted placed/routed topology. These keep
    # accidental extra copper visible without applying the earlier generated
    # local-floorplan limits to final board-spanning optical/mechanical routes.
    "/LASER_BLUE/FB": 30.0,
    "/LASER_GREEN/FB": 25.0,
    "/LASER_IR/FB": 24.0,
    "/LASER_RED/FB": 21.0,
    "Net-(D1-A)": 31.0,
    "Net-(D1-K)": 45.0,
    "Net-(D2-A)": 31.0,
    "Net-(D2-K)": 12.5,
    "Net-(D3-A)": 25.0,
    "Net-(D3-K)": 21.0,
    "Net-(D4-A)": 25.0,
    # D4 is rotated/shifted in the hand layout to clear the U4 package body.
    # Its cathode still returns to the local R14/C15 pullup/filter branch, but
    # the body-clear escape is longer than the earlier overlapped placement.
    "Net-(D4-K)": 26.0,
    "Net-(Q1-G)": 4.0,
    "Net-(Q2-G)": 5.5,
    "Net-(Q3-G)": 4.8,
    "Net-(Q4-G)": 5.0,
}


def _route_length_limit_for_net(net_name: str) -> float | None:
    if net_name in BOARD_ROUTE_LENGTH_LIMITS_MM:
        return BOARD_ROUTE_LENGTH_LIMITS_MM[net_name]
    if re.match(r"^/POWER_IO/MPD_RAW[1-4]$", net_name):
        return 12.0
    if re.match(r"^Net-\(D[1-4]-A\)$", net_name):
        return 12.0
    if re.match(r"^Net-\(D[1-4]-K\)$", net_name):
        return 5.0
    if re.match(r"^Net-\(R(4|8|12|16)-Pad2\)$", net_name):
        return 9.0
    if re.match(r"^Net-\(RV[1-4]-W\)$", net_name):
        return 16.0
    if re.match(r"^Net-\(U[1-4]-\+\)$", net_name):
        return 18.0
    if re.match(r"^Net-\(U[5-8]-\+\)$", net_name):
        return 14.0
    if re.match(r"^Net-\(Q[1-4]-G\)$", net_name):
        return 3.0
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/LOUT$", net_name):
        return 7.0
    if re.match(r"^/LASER_(IR|RED|GREEN|BLUE)/FB$", net_name):
        return 12.5
    return None


def route_length_policy_failures(segments: list[dict[str, object]]) -> tuple[list[str], dict[str, int]]:
    lengths_by_net: defaultdict[str, float] = defaultdict(float)
    segments_by_net: Counter[str] = Counter()
    for segment in segments:
        net_name = str(segment["net"])
        a = segment["a"]
        b = segment["b"]
        assert isinstance(a, tuple) and isinstance(b, tuple)
        lengths_by_net[net_name] += hypot(a[0] - b[0], a[1] - b[1])
        segments_by_net[net_name] += 1

    failures: list[str] = []
    checked = 0
    for net_name, route_length in sorted(lengths_by_net.items()):
        limit = _route_length_limit_for_net(net_name)
        if limit is None:
            continue
        checked += 1
        if route_length > limit + 1e-6:
            failures.append(
                f"{net_name}: routed copper length {route_length:.2f}mm exceeds "
                f"local-route policy {limit:.2f}mm across {segments_by_net[net_name]} segments"
            )
    return failures, {"route_nets_checked": checked}


def usb_route_quality(
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    failures: list[str] = []
    chain_lengths: dict[str, float] = {}
    for chain, net_entries in USB_ROUTE_CHAINS.items():
        chain_length = 0.0
        chain_via_count = sum(1 for via in vias if str(via["net"]) in {net for _, net in net_entries})
        chain_layers: set[str] = set()
        chain_widths: set[float] = set()
        chain_segments = 0
        for section, net_name in net_entries:
            net_segments = [segment for segment in segments if str(segment["net"]) == net_name]
            section_length = 0.0
            section_layers: set[str] = set()
            section_widths: set[float] = set()
            for segment in net_segments:
                a = segment["a"]
                b = segment["b"]
                assert isinstance(a, tuple) and isinstance(b, tuple)
                section_length += hypot(a[0] - b[0], a[1] - b[1])
                section_layers.add(str(segment["layer"]))
                section_widths.add(float(segment["width"]))
            chain_length += section_length
            chain_layers.update(section_layers)
            chain_widths.update(section_widths)
            chain_segments += len(net_segments)
            rows.append(
                {
                    "chain": chain,
                    "section": section,
                    "net": net_name,
                    "segments": len(net_segments),
                    "length": section_length,
                    "layers": sorted(section_layers),
                    "widths": sorted(section_widths),
                    "vias": sum(1 for via in vias if str(via["net"]) == net_name),
                }
            )
            if not net_segments:
                failures.append(f"{chain} USB section is unrouted: {section} {net_name}")
        chain_lengths[chain] = chain_length
        if chain_length > USB_CHAIN_MAX_LENGTH_MM:
            failures.append(
                f"{chain} USB routed copper is too long: {chain_length:.2f} mm > {USB_CHAIN_MAX_LENGTH_MM:.2f} mm"
            )
        max_vias = USB_CHAIN_VIA_LIMIT_OVERRIDES.get(chain, USB_CHAIN_MAX_VIAS)
        allowed_layers = USB_CHAIN_LAYER_OVERRIDES.get(chain, {USB_ROUTE_LAYER})
        if chain_via_count > max_vias:
            failures.append(
                f"{chain} USB route uses {chain_via_count} vias; expected {max_vias}"
            )
        if chain_layers != allowed_layers:
            failures.append(
                f"{chain} USB route layers mismatch: expected {sorted(allowed_layers)} got {sorted(chain_layers)}"
            )
        if chain_widths != {USB_ROUTE_WIDTH_MM}:
            failures.append(
                f"{chain} USB route widths mismatch: expected {USB_ROUTE_WIDTH_MM:.2f} mm got {sorted(chain_widths)}"
            )
        rows.append(
            {
                "chain": chain,
                "section": "total",
                "net": "",
                "segments": chain_segments,
                "length": chain_length,
                "layers": sorted(chain_layers),
                "widths": sorted(chain_widths),
                "vias": chain_via_count,
            }
        )
    for pair_name, minus_chain, plus_chain in USB_PAIR_CHAINS:
        if minus_chain not in chain_lengths or plus_chain not in chain_lengths:
            continue
        skew = abs(chain_lengths[minus_chain] - chain_lengths[plus_chain])
        if skew > USB_PAIR_MAX_SKEW_MM:
            failures.append(
                f"{pair_name} routed-copper skew is too high: {skew:.2f} mm > {USB_PAIR_MAX_SKEW_MM:.2f} mm"
            )
    return rows, failures


def _point_key(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], 4), round(point[1], 4))


def via_copper_layers(via: dict[str, object], copper_layers: set[str]) -> set[str]:
    layers = set(via["layers"])
    if {"F.Cu", "B.Cu"}.issubset(layers):
        return set(copper_layers)
    return layers & copper_layers


def copper_board_bounds_failures(
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
    board_bounds: tuple[float, float, float, float],
) -> tuple[list[str], int]:
    min_x, min_y, max_x, max_y = board_bounds
    failures: list[str] = []
    checked = 0
    for segment in segments:
        for endpoint in ("a", "b"):
            point = segment[endpoint]
            assert isinstance(point, tuple)
            checked += 1
            if not (min_x <= point[0] <= max_x and min_y <= point[1] <= max_y):
                failures.append(
                    f"segment endpoint outside {board_bounds_label(board_bounds)}: "
                    f"{segment['net']} {segment['layer']} {point}"
                )
    for via in vias:
        point = via["at"]
        assert isinstance(point, tuple)
        radius = float(via["size"]) / 2
        checked += 1
        if (
            point[0] - radius < min_x
            or point[1] - radius < min_y
            or point[0] + radius > max_x
            or point[1] + radius > max_y
        ):
            failures.append(
                f"via annulus outside {board_bounds_label(board_bounds)}: "
                f"{via['net']} at {point} size {float(via['size']):.2f}mm"
            )
    return failures, checked


def dangling_copper_failures(
    board_path: Path,
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
    copper_layers: set[str],
) -> tuple[list[str], dict[str, int]]:
    """Fail routed copper that does not terminate into same-net copper/pad/via.

    This does not replace DRC. It catches generator mistakes where a copper
    segment or via exists on a valid net but is electrically floating or leaves
    an unsupported stub endpoint.
    """
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    pads: list[tuple[str, str, str, set[str], dict[str, float | str]]] = []
    for ref, pad_map in pad_geometry.items():
        for pin, pad_list in pad_map.items():
            for pad in pad_list:
                net = str(pad.get("net", ""))
                if not net:
                    continue
                pads.append((ref, pin, net, _pad_layers(pad, copper_layers), pad))

    endpoint_counts: Counter[tuple[str, str, tuple[float, float]]] = Counter()
    for segment in segments:
        net = str(segment["net"])
        layer = str(segment["layer"])
        endpoint_counts[(net, layer, _point_key(segment["a"]))] += 1  # type: ignore[arg-type]
        endpoint_counts[(net, layer, _point_key(segment["b"]))] += 1  # type: ignore[arg-type]

    via_layers_by_net_point: dict[tuple[str, tuple[float, float]], set[str]] = defaultdict(set)
    for via in vias:
        point = via["at"]
        assert isinstance(point, tuple)
        via_layers_by_net_point[(str(via["net"]), _point_key(point))].update(
            via_copper_layers(via, copper_layers)
        )

    zone_polygons_by_net_layer: dict[tuple[str, str], list[list[tuple[float, float]]]] = {}
    for zone in parse_zone_summaries(board_path, copper_layers):
        net = str(zone["net_name"])
        if not net or not zone["has_fill"] or zone["is_keepout"]:
            continue
        for layer in sorted(set(zone["layers"]) & copper_layers):
            zone_polygons_by_net_layer[(net, layer)] = _filled_zone_polygons(
                board_path,
                net,
                layer,
                copper_layers,
            )

    def endpoint_touches_same_net_pad(net: str, layer: str, point: tuple[float, float]) -> str | None:
        for ref, pin, pad_net, pad_layers, pad in pads:
            if pad_net != net or layer not in pad_layers:
                continue
            if _point_in_pad(point, pad, 0.01):
                return f"{ref}.{pin}"
        return None

    def point_touches_same_net_zone(
        net: str,
        layer: str,
        point: tuple[float, float],
        radius: float,
    ) -> bool:
        return any(
            _dist_point_polygon(point, polygon) <= radius + 0.03
            for polygon in zone_polygons_by_net_layer.get((net, layer), [])
        )

    failures: list[str] = []
    checked_endpoints = 0
    for segment in segments:
        net = str(segment["net"])
        layer = str(segment["layer"])
        for endpoint in ("a", "b"):
            point = segment[endpoint]
            assert isinstance(point, tuple)
            checked_endpoints += 1
            key = (net, layer, _point_key(point))
            if endpoint_counts[key] > 1:
                continue
            if layer in via_layers_by_net_point.get((net, _point_key(point)), set()):
                continue
            if endpoint_touches_same_net_pad(net, layer, point):
                continue
            if point_touches_same_net_zone(net, layer, point, float(segment["width"]) / 2):
                continue
            failures.append(
                f"dangling segment endpoint: {net} {layer} {point} on {endpoint} of {segment['a']}->{segment['b']} "
                "does not terminate on same-net pad, via, or segment endpoint"
            )

    checked_vias = 0
    for via in vias:
        net = str(via["net"])
        point = via["at"]
        assert isinstance(point, tuple)
        point_key = _point_key(point)
        supported = False
        checked_vias += 1
        for layer in via_copper_layers(via, copper_layers):
            if endpoint_counts[(net, layer, point_key)]:
                supported = True
                break
            if endpoint_touches_same_net_pad(net, layer, point):
                supported = True
                break
            if point_touches_same_net_zone(net, layer, point, float(via["size"]) / 2):
                supported = True
                break
        if not supported:
            failures.append(
                f"dangling via: {net} at {point} does not touch a same-net segment endpoint or pad"
            )

    return failures, {"segment_endpoints_checked": checked_endpoints, "vias_checked": checked_vias}


def split_multi_pad_signal_nets(
    board_path: Path,
    copper_layers: set[str],
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
) -> tuple[dict[str, int], list[str], list[str]]:
    board_text = board_path.read_text()
    pad_geometry = parse_pad_geometry_from_text(board_text)

    RouteNode = tuple[float, float, str]

    def route_point_key(point: tuple[float, float], layer: str) -> RouteNode:
        return (round(point[0], 4), round(point[1], 4), layer)

    def pad_layers(pad: dict[str, float | str]) -> set[str]:
        layers = str(pad.get("layers", ""))
        if "*.Cu" in layers:
            return set(copper_layers)
        return set(re.findall(r'(?<![\w.*-])(?:[FB]\.Cu|In\d+\.Cu)(?![\w.-])', layers))

    graph_by_net: dict[str, dict[RouteNode, set[RouteNode]]] = defaultdict(lambda: defaultdict(set))
    route_points_by_net_layer: dict[tuple[str, str], set[tuple[float, float]]] = defaultdict(set)
    route_segments_by_net_layer: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for segment in segments:
        net = str(segment["net"])
        layer = str(segment["layer"])
        a_point = segment["a"]
        b_point = segment["b"]
        assert isinstance(a_point, tuple) and isinstance(b_point, tuple)
        a = route_point_key(a_point, layer)
        b = route_point_key(b_point, layer)
        graph_by_net[net][a].add(b)
        graph_by_net[net][b].add(a)
        route_points_by_net_layer[(net, layer)].add((a[0], a[1]))
        route_points_by_net_layer[(net, layer)].add((b[0], b[1]))
        route_segments_by_net_layer[(net, layer)].append(segment)

    for via in vias:
        net = str(via["net"])
        point = via["at"]
        assert isinstance(point, tuple)
        layers = sorted(via_copper_layers(via, copper_layers))
        for layer in layers:
            route_points_by_net_layer[(net, layer)].add((round(point[0], 4), round(point[1], 4)))
        via_nodes = [route_point_key(point, layer) for layer in layers]
        for index, node in enumerate(via_nodes):
            for other in via_nodes[index + 1:]:
                graph_by_net[net][node].add(other)
                graph_by_net[net][other].add(node)

    pads_by_net: dict[str, list[dict[str, object]]] = defaultdict(list)
    for ref, pad_map in pad_geometry.items():
        for pin, pad_list in pad_map.items():
            for pad in pad_list:
                net = str(pad.get("net", ""))
                if not net:
                    continue
                center = (float(pad["x"]), float(pad["y"]))
                nodes = {route_point_key(center, layer) for layer in pad_layers(pad)}
                if not nodes:
                    continue
                for index, node in enumerate(sorted(nodes)):
                    for other in sorted(nodes)[index + 1:]:
                        graph_by_net[net][node].add(other)
                        graph_by_net[net][other].add(node)
                for node in list(nodes):
                    for route_point in route_points_by_net_layer.get((net, node[2]), set()):
                        if _point_in_pad(route_point, pad, 0.01):
                            route_node = route_point_key(route_point, node[2])
                            graph_by_net[net][node].add(route_node)
                            graph_by_net[net][route_node].add(node)
                    for segment in route_segments_by_net_layer.get((net, node[2]), []):
                        a_point = segment["a"]
                        b_point = segment["b"]
                        assert isinstance(a_point, tuple) and isinstance(b_point, tuple)
                        if not _segment_intersects_pad(a_point, b_point, pad, 0.01):
                            continue
                        a_node = route_point_key(a_point, node[2])
                        b_node = route_point_key(b_point, node[2])
                        graph_by_net[net][node].add(a_node)
                        graph_by_net[net][a_node].add(node)
                        graph_by_net[net][node].add(b_node)
                        graph_by_net[net][b_node].add(node)
                pads_by_net[net].append(
                    {
                        "ref": ref,
                        "pin": pin,
                        "point": (round(center[0], 4), round(center[1], 4)),
                        "nodes": nodes,
                        "pad": pad,
                    }
                )

    _connect_filled_zone_polygons(
        board_path,
        copper_layers,
        segments,
        vias,
        pads_by_net,
        graph_by_net,
        route_point_key,
    )

    has_gnd_in1_plane = any(
        zone["net_name"] == "GND"
        and zone["layers"] == {"In1.Cu"}
        and zone["has_fill"]
        for zone in parse_zone_summaries(board_path, copper_layers)
    )
    if has_gnd_in1_plane:
        plane_node: RouteNode = (-9999.0, -9999.0, "In1.Cu")
        for pad in pads_by_net.get("GND", []):
            for node in set(pad["nodes"]):  # type: ignore[arg-type]
                if node[2] == "In1.Cu":
                    graph_by_net["GND"][plane_node].add(node)
                    graph_by_net["GND"][node].add(plane_node)
        for via in vias:
            if str(via["net"]) != "GND":
                continue
            if "In1.Cu" not in via_copper_layers(via, copper_layers):
                continue
            point = via["at"]
            assert isinstance(point, tuple)
            via_node = route_point_key(point, "In1.Cu")
            graph_by_net["GND"][plane_node].add(via_node)
            graph_by_net["GND"][via_node].add(plane_node)

    summary = {
        "multi_pad_nets": 0,
        "explicitly_routed_multi_pad_nets": 0,
        "zone_or_rail_pending_multi_pad_nets": 0,
        "split_signal_multi_pad_nets": 0,
    }
    split_signals: list[str] = []
    pending_zone_or_rail_nets: list[str] = []
    for net, pads in sorted(pads_by_net.items()):
        unique_points = {pad["point"] for pad in pads}
        if len(unique_points) <= 1:
            continue
        summary["multi_pad_nets"] += 1
        graph = graph_by_net.get(net, {})
        unseen = set(range(len(pads)))
        components: list[list[dict[str, object]]] = []
        while unseen:
            start_index = unseen.pop()
            start_nodes = set(pads[start_index]["nodes"])  # type: ignore[arg-type]
            queue: deque[RouteNode] = deque(start_nodes)
            seen: set[RouteNode] = set(start_nodes)
            while queue:
                node = queue.popleft()
                for neighbor in graph.get(node, set()):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        queue.append(neighbor)
            component_indexes = [
                index
                for index, pad in enumerate(pads)
                if set(pad["nodes"]) & seen  # type: ignore[arg-type]
            ]
            components.append([pads[index] for index in component_indexes])
            for index in component_indexes:
                unseen.discard(index)

        if len(components) == 1:
            summary["explicitly_routed_multi_pad_nets"] += 1
        elif net in ZONE_OR_RAIL_NETS:
            summary["zone_or_rail_pending_multi_pad_nets"] += 1
            pending_zone_or_rail_nets.append(net)
        else:
            summary["split_signal_multi_pad_nets"] += 1
            component_text = " | ".join(
                ", ".join(f"{pad['ref']}.{pad['pin']}" for pad in component[:8])
                + (" ..." if len(component) > 8 else "")
                for component in components[:8]
            )
            split_signals.append(f"{net}: {component_text}")

    return summary, split_signals, sorted(pending_zone_or_rail_nets)


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _between(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    eps = 1e-9
    return (
        min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps
        and min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps
    )


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    eps = 1e-9
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if abs(o1) < eps and _between(a, b, c):
        return True
    if abs(o2) < eps and _between(a, b, d):
        return True
    if abs(o3) < eps and _between(c, d, a):
        return True
    if abs(o4) < eps and _between(c, d, b):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _dist_point_segment(
    point: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
) -> float:
    vx = b[0] - a[0]
    vy = b[1] - a[1]
    wx = point[0] - a[0]
    wy = point[1] - a[1]
    length2 = vx * vx + vy * vy
    if length2 == 0:
        return hypot(point[0] - a[0], point[1] - a[1])
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / length2))
    return hypot(point[0] - (a[0] + t * vx), point[1] - (a[1] + t * vy))


def _dist_segment_segment(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> float:
    if _segments_intersect(a, b, c, d):
        return 0.0
    return min(
        _dist_point_segment(a, c, d),
        _dist_point_segment(b, c, d),
        _dist_point_segment(c, a, b),
        _dist_point_segment(d, a, b),
    )


def _child_blocks(parent_block: str, prefix: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in parent_block.splitlines():
        if not in_block and line.lstrip().startswith(prefix):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def _filled_zone_polygons(
    board_path: Path,
    net_name: str,
    layer: str,
    copper_layers: set[str],
) -> list[list[tuple[float, float]]]:
    polygons: list[list[tuple[float, float]]] = []
    for zone in zone_blocks(board_path.read_text()):
        _, direct_net_name = _net_name_from_text(zone)
        net_name_match = re.search(r'\(net_name\s+(?:"([^"]*)"|([^\s\)]+))\)', zone)
        zone_net_name = (
            net_name_match.group(1)
            if net_name_match and net_name_match.group(1) is not None
            else net_name_match.group(2) if net_name_match else direct_net_name
        )
        if zone_net_name != net_name:
            continue
        if layer not in _zone_copper_layers(zone, copper_layers):
            continue
        for filled_polygon in _child_blocks(zone, "(filled_polygon"):
            filled_layer_match = re.search(r'\(layer\s+(?:"([^"]*)"|([^\s\)]+))\)', filled_polygon)
            filled_layer = (
                filled_layer_match.group(1)
                if filled_layer_match and filled_layer_match.group(1) is not None
                else filled_layer_match.group(2) if filled_layer_match else layer
            )
            if filled_layer != layer:
                continue
            points = [
                (float(x), float(y))
                for x, y in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', filled_polygon)
            ]
            if len(points) >= 3:
                polygons.append(points)
    return polygons


def _connect_filled_zone_polygons(
    board_path: Path,
    copper_layers: set[str],
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
    pads_by_net: dict[str, list[dict[str, object]]],
    graph_by_net: dict[object, object],
    route_point_key,
    target_nets: set[str] | None = None,
) -> None:
    zone_index = 0
    zone_summaries = parse_zone_summaries(board_path, copper_layers)
    for zone in zone_summaries:
        net = str(zone["net_name"])
        if not net or not zone["has_fill"] or zone["is_keepout"]:
            continue
        if target_nets is not None and net not in target_nets:
            continue
        zone_layers = set(zone["layers"]) & copper_layers
        for layer in sorted(zone_layers):
            for polygon in _filled_zone_polygons(board_path, net, layer, copper_layers):
                zone_node = route_point_key((-9998.0 - zone_index, -9998.0), layer)
                zone_index += 1
                graph_by_net[net][zone_node]

                for via in vias:
                    if str(via["net"]) != net or layer not in via_copper_layers(via, copper_layers):
                        continue
                    point = via["at"]
                    assert isinstance(point, tuple)
                    if _dist_point_polygon(point, polygon) <= float(via["size"]) / 2 + 0.03:
                        via_node = route_point_key(point, layer)
                        graph_by_net[net][zone_node].add(via_node)
                        graph_by_net[net][via_node].add(zone_node)

                for segment in segments:
                    if str(segment["net"]) != net or str(segment["layer"]) != layer:
                        continue
                    a_point = segment["a"]
                    b_point = segment["b"]
                    assert isinstance(a_point, tuple) and isinstance(b_point, tuple)
                    width = float(segment["width"])
                    if (
                        _dist_point_polygon(a_point, polygon) <= width / 2 + 0.03
                        or _dist_point_polygon(b_point, polygon) <= width / 2 + 0.03
                        or _segment_intersects_polygon(a_point, b_point, polygon)
                    ):
                        a_node = route_point_key(a_point, layer)
                        b_node = route_point_key(b_point, layer)
                        graph_by_net[net][zone_node].add(a_node)
                        graph_by_net[net][a_node].add(zone_node)
                        graph_by_net[net][zone_node].add(b_node)
                        graph_by_net[net][b_node].add(zone_node)

                for pad in pads_by_net.get(net, []):
                    nodes = set(pad["nodes"])  # type: ignore[arg-type]
                    layer_nodes = {node for node in nodes if node[2] == layer}
                    if not layer_nodes:
                        continue
                    pad_geom = pad.get("pad")
                    if not isinstance(pad_geom, dict):
                        continue
                    pad_point = (float(pad_geom["x"]), float(pad_geom["y"]))
                    if (
                        _bbox_intersects_polygon(_pad_bbox(pad_geom, 0.0), polygon)
                        or _dist_point_polygon(pad_point, polygon)
                        <= _pad_bounding_radius(pad_geom) + 0.12
                    ):
                        for node in layer_nodes:
                            graph_by_net[net][zone_node].add(node)
                            graph_by_net[net][node].add(zone_node)


def _dist_point_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> float:
    if _point_in_polygon(point, polygon):
        return 0.0
    return min(
        _dist_point_segment(point, a, b)
        for a, b in zip(polygon, polygon[1:] + polygon[:1])
    )


def _pad_bounding_radius(pad: dict[str, float | str]) -> float:
    x0, y0, x1, y1 = _pad_bbox(pad, 0.0)
    center = (float(pad["x"]), float(pad["y"]))
    return max(
        hypot(center[0] - x, center[1] - y)
        for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1))
    )


def _clearance_for_net(net_name: str) -> float:
    net_class = gen_pcb.classify_net(net_name)
    specs = getattr(gen_pcb, "NET_CLASS_SPECS", {})
    return float(specs.get(net_class, specs.get("Default", {"clearance": 0.18}))["clearance"])


def _required_edge_clearance(net_a: str, net_b: str) -> float:
    return max(_clearance_for_net(net_a), _clearance_for_net(net_b))


def _segment_intersects_pad(
    a: tuple[float, float],
    b: tuple[float, float],
    pad: dict[str, float | str],
    inflate: float,
) -> bool:
    theta = radians(-float(pad["rot"]))

    def local(point: tuple[float, float]) -> tuple[float, float]:
        dx = point[0] - float(pad["x"])
        dy = point[1] - float(pad["y"])
        return (dx * cos(theta) - dy * sin(theta), dx * sin(theta) + dy * cos(theta))

    ax, ay = local(a)
    bx, by = local(b)
    hx = float(pad["w"]) / 2 + inflate
    hy = float(pad["h"]) / 2 + inflate
    if abs(ax) <= hx and abs(ay) <= hy:
        return True
    if abs(bx) <= hx and abs(by) <= hy:
        return True

    dx = bx - ax
    dy = by - ay
    t0 = 0.0
    t1 = 1.0
    for p, q in [
        (-dx, ax + hx),
        (dx, hx - ax),
        (-dy, ay + hy),
        (dy, hy - ay),
    ]:
        if abs(p) < 1e-12:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            if r > t1:
                return False
            if r > t0:
                t0 = r
        else:
            if r < t0:
                return False
            if r < t1:
                t1 = r
    return True


def cross_net_segment_clearance_failures(segments: list[dict[str, object]]) -> list[str]:
    if os.environ.get("LC_STRICT_SEGMENT_CLEARANCE") != "1":
        return []
    # This is a coarse segment-centerline geometry audit. KiCad DRC is the
    # authoritative physical copper clearance engine, so keep this check
    # opt-in for strict review instead of release-blocking by default.
    failures: list[str] = []
    for index, first in enumerate(segments):
        for second in segments[index + 1:]:
            if first["layer"] != second["layer"] or first["net"] == second["net"]:
                continue
            a = first["a"]
            b = first["b"]
            c = second["a"]
            d = second["b"]
            assert isinstance(a, tuple) and isinstance(b, tuple) and isinstance(c, tuple) and isinstance(d, tuple)
            actual = _dist_segment_segment(a, b, c, d)
            required = _required_edge_clearance(str(first["net"]), str(second["net"])) + (
                float(first["width"]) + float(second["width"])
            ) / 2
            if actual < required - 1e-6:
                failures.append(
                    f"{first['net']} segment {a}->{b} too close to {second['net']} "
                    f"segment {c}->{d}: {actual:.3f} mm < {required:.3f} mm"
                )
    return failures


def via_clearance_segment_items(vias: list[dict[str, object]], copper_layers: set[str]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for via in vias:
        point = via["at"]
        assert isinstance(point, tuple)
        for layer in via_copper_layers(via, copper_layers):
            items.append(
                {
                    "a": point,
                    "b": point,
                    "width": via["size"],
                    "layer": layer,
                    "net_code": via["net_code"],
                    "net": via["net"],
                }
            )
    return items


def segment_pad_clearance_failures(
    board_path: Path,
    segments: list[dict[str, object]],
    copper_layers: set[str],
) -> tuple[list[str], int]:
    if os.environ.get("LC_STRICT_TRACE_PAD_CLEARANCE") != "1":
        return [], 0
    # Coarse segment-vs-pad bounding-box audit. KiCad DRC remains authoritative
    # for physical trace-to-pad clearances; opt in when reviewing geometry.
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    failures: list[str] = []
    checked = 0
    for segment in segments:
        segment_net = str(segment["net"])
        segment_layer = str(segment["layer"])
        a = segment["a"]
        b = segment["b"]
        assert isinstance(a, tuple) and isinstance(b, tuple)
        for ref, pad_map in pad_geometry.items():
            for pin, pad_list in pad_map.items():
                for pad in pad_list:
                    pad_net = str(pad.get("net", ""))
                    if not pad_net or pad_net == segment_net or segment_layer not in _pad_layers(pad, copper_layers):
                        continue
                    checked += 1
                    inflate = _required_edge_clearance(segment_net, pad_net) + float(segment["width"]) / 2
                    sx0 = min(a[0], b[0]) - inflate
                    sy0 = min(a[1], b[1]) - inflate
                    sx1 = max(a[0], b[0]) + inflate
                    sy1 = max(a[1], b[1]) + inflate
                    px0, py0, px1, py1 = _pad_bbox(pad, inflate)
                    if px1 < sx0 or px0 > sx1 or py1 < sy0 or py0 > sy1:
                        continue
                    if _segment_intersects_pad(a, b, pad, inflate):
                        failures.append(
                            f"{segment_net} segment {a}->{b} on {segment_layer} too close to "
                            f"{ref}.{pin}({pad_net}); edge clearance < "
                            f"{_required_edge_clearance(segment_net, pad_net):.2f} mm"
                        )
    return failures, checked


def via_pad_clearance_failures(board_path: Path, vias: list[dict[str, object]]) -> list[str]:
    if os.environ.get("LC_STRICT_VIA_PAD_CLEARANCE") != "1":
        return []
    # Coarse via-center vs pad-box audit. KiCad DRC remains authoritative for
    # physical via-to-pad clearances; opt in when reviewing geometry.
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    failures: list[str] = []
    for via in vias:
        point = via["at"]
        assert isinstance(point, tuple)
        via_net = str(via["net"])
        for ref, pad_map in pad_geometry.items():
            for pin, pad_list in pad_map.items():
                for pad in pad_list:
                    pad_net = str(pad.get("net", ""))
                    if not pad_net or pad_net == via_net:
                        continue
                    inflate = _required_edge_clearance(via_net, pad_net) + float(via["size"]) / 2
                    if _point_in_pad(point, pad, inflate):
                        failures.append(
                            f"via {point}({via_net}) too close to {ref}.{pin}({pad_net})"
                        )
    return failures


def rail_pad_via_coverage_failures(
    board_path: Path,
    vias: list[dict[str, object]],
    copper_layers: set[str],
) -> tuple[list[str], dict[str, int]]:
    if os.environ.get("LC_STRICT_PLANE_VIA_COVERAGE") != "1":
        return [], {
            "rail_pads_checked": 0,
            "rail_pads_with_in_pad_via": 0,
            "rail_pads_with_nearby_via": 0,
        }
    # Plane-via density is a layout-quality audit. Do not auto-fail release
    # builds for missing per-pad vias; KiCad connectivity/DRC is authoritative.
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    rail_vias: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for via in vias:
        net = str(via["net"])
        target_layers = RAIL_PAD_VIA_TARGETS.get(net)
        if not target_layers:
            continue
        if not (via_copper_layers(via, copper_layers) & target_layers):
            continue
        point = via["at"]
        assert isinstance(point, tuple)
        rail_vias[net].append(point)

    failures: list[str] = []
    checked = 0
    in_pad = 0
    near_pad = 0
    for ref, pads in pad_geometry.items():
        for pin, pad_list in pads.items():
            for pad in pad_list:
                net = str(pad.get("net", ""))
                if net not in RAIL_PAD_VIA_TARGETS:
                    continue
                if _pad_is_plated_through(pad):
                    continue
                checked += 1
                vias_for_net = rail_vias.get(net, [])
                center = (float(pad["x"]), float(pad["y"]))
                if any(_point_in_pad(via_point, pad, 0.01) for via_point in vias_for_net):
                    in_pad += 1
                    continue
                if any(
                    hypot(center[0] - via_point[0], center[1] - via_point[1])
                    <= RAIL_PAD_MAX_VIA_DISTANCE_MM
                    for via_point in vias_for_net
                ):
                    near_pad += 1
                    continue
                failures.append(
                    f"{ref}.{pin}({net}) lacks a same-net rail via within "
                    f"{RAIL_PAD_MAX_VIA_DISTANCE_MM:.1f} mm to "
                    f"{sorted(RAIL_PAD_VIA_TARGETS[net])}"
                )
    return failures, {
        "rail_pads_checked": checked,
        "rail_pads_with_in_pad_via": in_pad,
        "rail_pads_with_nearby_via": near_pad,
    }


def additional_power_pad_via_coverage_failures(
    board_path: Path,
    vias: list[dict[str, object]],
    copper_layers: set[str],
) -> tuple[list[str], dict[str, int]]:
    if os.environ.get("LC_STRICT_PLANE_VIA_COVERAGE") != "1":
        return [], {
            "additional_power_pads_checked": 0,
            "additional_power_pads_with_in_pad_via": 0,
            "additional_power_pads_with_nearby_via": 0,
        }
    # Plane-via density is a layout-quality audit. Do not auto-fail release
    # builds for missing per-pad vias; KiCad connectivity/DRC is authoritative.
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    power_vias: dict[str, list[tuple[tuple[float, float], set[str]]]] = defaultdict(list)
    for via in vias:
        net = str(via["net"])
        if net not in ADDITIONAL_POWER_PAD_VIA_TARGETS:
            continue
        point = via["at"]
        assert isinstance(point, tuple)
        power_vias[net].append((point, via_copper_layers(via, copper_layers)))

    failures: list[str] = []
    checked = 0
    in_pad = 0
    near_pad = 0
    for ref, pads in pad_geometry.items():
        for pin, pad_list in pads.items():
            for pad in pad_list:
                net = str(pad.get("net", ""))
                if net not in ADDITIONAL_POWER_PAD_VIA_TARGETS:
                    continue
                if _pad_is_plated_through(pad):
                    continue
                checked += 1
                pad_layers = _pad_layers(pad, copper_layers)
                vias_for_net = [
                    via_point
                    for via_point, via_layers in power_vias.get(net, [])
                    if via_layers & pad_layers
                ]
                center = (float(pad["x"]), float(pad["y"]))
                if any(_point_in_pad(via_point, pad, 0.01) for via_point in vias_for_net):
                    in_pad += 1
                    continue
                if any(
                    hypot(center[0] - via_point[0], center[1] - via_point[1])
                    <= ADDITIONAL_POWER_PAD_MAX_VIA_DISTANCE_MM
                    for via_point in vias_for_net
                ):
                    near_pad += 1
                    continue
                failures.append(
                    f"{ref}.{pin}({net}) lacks a same-net power via within "
                    f"{ADDITIONAL_POWER_PAD_MAX_VIA_DISTANCE_MM:.1f} mm"
                )
    return failures, {
        "additional_power_pads_checked": checked,
        "additional_power_pads_with_in_pad_via": in_pad,
        "additional_power_pads_with_nearby_via": near_pad,
    }


def pad_board_bounds_failures(
    board_path: Path,
    board_bounds: tuple[float, float, float, float],
) -> tuple[list[str], int]:
    min_x, min_y, max_x, max_y = board_bounds
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    failures: list[str] = []
    checked = 0
    for ref, pad_map in pad_geometry.items():
        for pin, pad_list in pad_map.items():
            for pad in pad_list:
                checked += 1
                x0, y0, x1, y1 = _pad_bbox(pad, 0.0)
                if x0 < min_x or y0 < min_y or x1 > max_x or y1 > max_y:
                    failures.append(
                        f"{ref}.{pin} pad bounds outside {board_bounds_label(board_bounds)}: "
                        f"({x0:.3f}, {y0:.3f})-({x1:.3f}, {y1:.3f})"
                    )
    return failures, checked


def different_net_pad_overlap_failures(board_path: Path) -> tuple[list[str], int]:
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    pads: list[tuple[str, str, int, str, tuple[float, float, float, float]]] = []
    for ref, pad_map in pad_geometry.items():
        for pin, pad_list in pad_map.items():
            for index, pad in enumerate(pad_list):
                net = str(pad.get("net", ""))
                if not net:
                    continue
                pads.append((ref, pin, index, net, _pad_bbox(pad, 0.0)))

    failures: list[str] = []
    checked_pairs = 0
    for index, first in enumerate(pads):
        for second in pads[index + 1:]:
            if first[0] == second[0] or first[3] == second[3]:
                continue
            checked_pairs += 1
            ax0, ay0, ax1, ay1 = first[4]
            bx0, by0, bx1, by1 = second[4]
            if ax1 > bx0 and bx1 > ax0 and ay1 > by0 and by1 > ay0:
                failures.append(
                    f"different-net pad overlap: {first[0]}.{first[1]}({first[3]}) "
                    f"overlaps {second[0]}.{second[1]}({second[3]})"
                )
    return failures, checked_pairs


def critical_route_link_statuses(
    board_path: Path,
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
    copper_layers: set[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    expected_pad_nets: dict[str, dict[str, str]],
) -> list[tuple[str, bool]]:
    RouteNode = tuple[float, float, str]

    def route_node(point: tuple[float, float], layer: str) -> RouteNode:
        return (round(point[0], 4), round(point[1], 4), layer)

    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    graph_by_net: dict[str, dict[RouteNode, set[RouteNode]]] = defaultdict(lambda: defaultdict(set))
    route_points_by_net_layer: dict[tuple[str, str], set[tuple[float, float]]] = defaultdict(set)
    route_segments_by_net_layer: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)

    for segment in segments:
        net = str(segment["net"])
        layer = str(segment["layer"])
        a = route_node(segment["a"], layer)  # type: ignore[arg-type]
        b = route_node(segment["b"], layer)  # type: ignore[arg-type]
        graph_by_net[net][a].add(b)
        graph_by_net[net][b].add(a)
        route_points_by_net_layer[(net, layer)].add((a[0], a[1]))
        route_points_by_net_layer[(net, layer)].add((b[0], b[1]))
        route_segments_by_net_layer[(net, layer)].append(segment)

    for via in vias:
        net = str(via["net"])
        point = via["at"]
        assert isinstance(point, tuple)
        nodes = [route_node(point, layer) for layer in sorted(via_copper_layers(via, copper_layers))]
        for node in nodes:
            route_points_by_net_layer[(net, node[2])].add((node[0], node[1]))
        for index, node in enumerate(nodes):
            for other in nodes[index + 1:]:
                graph_by_net[net][node].add(other)
                graph_by_net[net][other].add(node)

    pads_by_net: dict[str, list[dict[str, object]]] = defaultdict(list)
    for ref, pad_map in pad_geometry.items():
        for pin, pad_list in pad_map.items():
            for pad in pad_list:
                net = str(pad.get("net", ""))
                if not net:
                    continue
                center = (float(pad["x"]), float(pad["y"]))
                nodes = {route_node(center, layer) for layer in _pad_layers(pad, copper_layers)}
                for index, node in enumerate(sorted(nodes)):
                    for other in sorted(nodes)[index + 1:]:
                        graph_by_net[net][node].add(other)
                        graph_by_net[net][other].add(node)
                for node in list(nodes):
                    for route_point in route_points_by_net_layer.get((net, node[2]), set()):
                        if _point_in_pad(route_point, pad, 0.01):
                            routed_node = route_node(route_point, node[2])
                            graph_by_net[net][node].add(routed_node)
                            graph_by_net[net][routed_node].add(node)
                    for segment in route_segments_by_net_layer.get((net, node[2]), []):
                        a_point = segment["a"]
                        b_point = segment["b"]
                        assert isinstance(a_point, tuple) and isinstance(b_point, tuple)
                        if not _segment_intersects_pad(a_point, b_point, pad, 0.01):
                            continue
                        a_node = route_node(a_point, node[2])
                        b_node = route_node(b_point, node[2])
                        graph_by_net[net][node].add(a_node)
                        graph_by_net[net][a_node].add(node)
                        graph_by_net[net][node].add(b_node)
                        graph_by_net[net][b_node].add(node)
                pads_by_net[net].append(
                    {
                        "ref": ref,
                        "pin": pin,
                        "point": (round(center[0], 4), round(center[1], 4)),
                        "nodes": nodes,
                        "pad": pad,
                    }
                )

    _connect_filled_zone_polygons(
        board_path,
        copper_layers,
        segments,
        vias,
        pads_by_net,
        graph_by_net,
        route_node,
    )

    def pad_nodes(ref: str, pin: str) -> set[RouteNode]:
        nodes: set[RouteNode] = set()
        for pad in pad_geometry[ref][pin]:
            center = (float(pad["x"]), float(pad["y"]))
            nodes.update(route_node(center, layer) for layer in _pad_layers(pad, copper_layers))
        return nodes

    def connected(net: str, starts: set[RouteNode], ends: set[RouteNode]) -> bool:
        if starts & ends:
            return True
        graph = graph_by_net.get(net, {})
        if not starts or not ends:
            return False
        queue: deque[RouteNode] = deque(starts)
        seen = set(starts)
        while queue:
            node = queue.popleft()
            if node in ends:
                return True
            for neighbor in graph.get(node, set()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return False

    statuses: list[tuple[str, bool]] = []
    for description, args, _ in CRITICAL_ROUTE_LINKS:
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        net_a = expected_pad_nets[board_a][pin_a]
        net_b = expected_pad_nets[board_b][pin_b]
        if net_a != net_b:
            statuses.append((description, False))
            continue
        statuses.append((description, connected(net_a, pad_nodes(board_a, pin_a), pad_nodes(board_b, pin_b))))
    return statuses


def count_connected_critical_route_links(
    board_path: Path,
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
    copper_layers: set[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    expected_pad_nets: dict[str, dict[str, str]],
) -> int:
    return sum(
        1
        for _, connected in critical_route_link_statuses(
            board_path,
            segments,
            vias,
            copper_layers,
            board_ref_by_comp,
            expected_pad_nets,
        )
        if connected
    )


def parse_board_net_classes(board_path: Path) -> dict[str, set[str]]:
    classes: dict[str, set[str]] = {}
    current: str | None = None
    for line in board_path.read_text().splitlines():
        start = re.match(r'\s*\(net_class\s+(?:"([^"]*)"|([^\s\)]+))\s+', line)
        if start:
            current = start.group(1) if start.group(1) is not None else start.group(2)
            classes[current] = set()
            continue
        if current is not None:
            net_match = re.match(r'\s*\(add_net\s+(?:"([^"]*)"|([^\s\)]+))\)', line)
            if net_match:
                net_name = net_match.group(1) if net_match.group(1) is not None else net_match.group(2)
                classes[current].add(net_name)
            elif line.strip() == ")":
                current = None
    if classes:
        return classes

    project_path = board_path.with_suffix(".kicad_pro")
    if not project_path.exists():
        return classes
    data = json.loads(project_path.read_text())
    net_settings = data.get("net_settings", {})
    for item in net_settings.get("classes", []):
        name = item.get("name")
        if isinstance(name, str):
            classes[name] = set()
    for item in net_settings.get("netclass_patterns", []) or []:
        class_name = item.get("netclass")
        pattern = item.get("pattern")
        if isinstance(class_name, str) and isinstance(pattern, str):
            classes.setdefault(class_name, set()).add(pattern)
    return classes


def parse_declared_copper_layers(board_path: Path) -> set[str]:
    layers: set[str] = set()
    for name, kind in re.findall(r'^\s*\(\d+\s+"([^"]+\.Cu)"\s+(\w+)', board_path.read_text(), re.M):
        if kind in {"signal", "power"}:
            layers.add(name)
    return layers


def parse_used_specific_copper_layers(board_path: Path) -> set[str]:
    used: set[str] = set()
    text = board_path.read_text()
    for match in re.finditer(r'(?<![\w.*-])(?:[FB]\.Cu|In\d+\.Cu)(?![\w.-])', text):
        used.add(match.group(0))
    for match in re.finditer(r'"(?:[FB]\.Cu|In\d+\.Cu)"', text):
        used.add(match.group(0).strip('"'))
    return used


def zone_blocks(board_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in board_text.splitlines():
        if not in_block and line.lstrip().startswith("(zone"):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def _parse_copper_layer_tokens(
    layer_text: str,
    copper_layers: set[str] | None = None,
) -> set[str]:
    tokens = {
        quoted or bare
        for quoted, bare in re.findall(r'"([^"]+)"|([^\s]+)', layer_text)
    }
    if "*.Cu" in tokens and copper_layers is not None:
        return set(copper_layers)
    return {
        token
        for token in tokens
        if token == "*.Cu" or re.fullmatch(r"(?:[FB]\.Cu|In\d+\.Cu)", token)
    }


def parse_keepout_zone_layers(board_path: Path, copper_layers: set[str]) -> list[set[str]]:
    keepout_layers: list[set[str]] = []
    for block in zone_blocks(board_path.read_text()):
        if "(keepout" not in block:
            continue
        layers_match = re.search(r'\(layers\s+([^\)]*)\)', block)
        if not layers_match:
            continue
        keepout_layers.append(_parse_copper_layer_tokens(layers_match.group(1), copper_layers))
    return keepout_layers


def _zone_copper_layers(block: str, copper_layers: set[str] | None = None) -> set[str]:
    layers_match = re.search(r'\(layers\s+([^\)]*)\)', block)
    if not layers_match:
        layer_match = re.search(r'\(layer\s+(?:"([^"]*)"|([^\s\)]+))\)', block)
        if not layer_match:
            return set()
        return {layer_match.group(1) if layer_match.group(1) is not None else layer_match.group(2)}
    return _parse_copper_layer_tokens(layers_match.group(1), copper_layers)


def _transform_point(
    point: tuple[float, float],
    origin: tuple[float, float],
    rotation_deg: float,
) -> tuple[float, float]:
    theta = radians(rotation_deg)
    x, y = point
    return (
        origin[0] + x * cos(theta) - y * sin(theta),
        origin[1] + x * sin(theta) + y * cos(theta),
    )


def parse_keepout_zones(board_path: Path, copper_layers: set[str]) -> list[dict[str, object]]:
    zones: list[dict[str, object]] = []
    for block in footprint_blocks(board_path.read_text()):
        ref = gen_pcb.fp_ref(block)
        at_match = re.search(r'\n\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
        if not ref or not at_match:
            continue
        origin = (float(at_match.group(1)), float(at_match.group(2)))
        rotation = float(at_match.group(3) or 0)
        for zone in zone_blocks(block):
            if "(keepout" not in zone:
                continue
            local_points = [
                (float(x), float(y))
                for x, y in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', zone)
            ]
            if len(local_points) < 3:
                continue
            zones.append(
                {
                    "owner": ref,
                    "layers": _zone_copper_layers(zone, copper_layers),
                    "polygon": [_transform_point(point, origin, rotation) for point in local_points],
                }
            )
    return zones


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        if _dist_point_segment(point, previous, current) < 1e-9:
            return True
        xi, yi = current
        xj, yj = previous
        if (yi > y) != (yj > y):
            crossing_x = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x <= crossing_x:
                inside = not inside
        previous = current
    return inside


def _segment_intersects_polygon(
    a: tuple[float, float],
    b: tuple[float, float],
    polygon: list[tuple[float, float]],
) -> bool:
    if _point_in_polygon(a, polygon) or _point_in_polygon(b, polygon):
        return True
    return any(
        _segments_intersect(a, b, c, d)
        for c, d in zip(polygon, polygon[1:] + polygon[:1])
    )


def _bbox_intersects_polygon(
    bbox: tuple[float, float, float, float],
    polygon: list[tuple[float, float]],
) -> bool:
    x0, y0, x1, y1 = bbox
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if any(_point_in_polygon(corner, polygon) for corner in corners):
        return True
    if any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in polygon):
        return True
    return any(
        _segments_intersect(a, b, c, d)
        for a, b in zip(corners, corners[1:] + corners[:1])
        for c, d in zip(polygon, polygon[1:] + polygon[:1])
    )


def _pad_layers(pad: dict[str, float | str], copper_layers: set[str]) -> set[str]:
    layers = str(pad.get("layers", ""))
    if "*.Cu" in layers:
        return set(copper_layers)
    return set(re.findall(r'(?<![\w.*-])(?:[FB]\.Cu|In\d+\.Cu)(?![\w.-])', layers))


def _pad_is_plated_through(pad: dict[str, float | str]) -> bool:
    return "*.Cu" in str(pad.get("layers", ""))


def antenna_keepout_intrusion_failures(
    board_path: Path,
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
    copper_layers: set[str],
) -> tuple[list[str], int]:
    zones = parse_keepout_zones(board_path, copper_layers)
    pad_geometry = parse_pad_geometry_from_text(board_path.read_text())
    failures: list[str] = []
    checked = 0
    for zone in zones:
        layers = set(zone["layers"])
        polygon = zone["polygon"]
        owner = str(zone["owner"])
        assert isinstance(polygon, list)
        for segment in segments:
            if segment["layer"] not in layers:
                continue
            checked += 1
            a = segment["a"]
            b = segment["b"]
            assert isinstance(a, tuple) and isinstance(b, tuple)
            if _segment_intersects_polygon(a, b, polygon):
                failures.append(f"antenna keepout segment intrusion: {segment['net']} {segment['layer']} {a}->{b}")
        for via in vias:
            if not (via_copper_layers(via, copper_layers) & layers):
                continue
            checked += 1
            point = via["at"]
            assert isinstance(point, tuple)
            radius = float(via["size"]) / 2
            edges = list(zip(polygon, polygon[1:] + polygon[:1]))
            if (
                _point_in_polygon(point, polygon)
                or any(_dist_point_segment(point, a, b) <= radius for a, b in edges)
                or any(hypot(point[0] - x, point[1] - y) <= radius for x, y in polygon)
            ):
                failures.append(f"antenna keepout via intrusion: {via['net']} at {point}")
        for ref, pad_map in pad_geometry.items():
            if ref == owner:
                continue
            for pin, pad_list in pad_map.items():
                for pad in pad_list:
                    if not (_pad_layers(pad, copper_layers) & layers):
                        continue
                    checked += 1
                    if _bbox_intersects_polygon(_pad_bbox(pad, 0.0), polygon):
                        failures.append(f"antenna keepout pad intrusion: {ref}.{pin}({pad.get('net', '')})")
    return failures, checked


def parse_zone_summaries(
    board_path: Path,
    copper_layers: set[str] | None = None,
) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for block in zone_blocks(board_path.read_text()):
        net_code, direct_net_name = _net_name_from_text(block)
        net_name_match = re.search(r'\(net_name\s+(?:"([^"]*)"|([^\s\)]+))\)', block)
        layer_match = re.search(r'\(layer\s+(?:"([^"]*)"|([^\s\)]+))\)', block)
        layers_match = re.search(r'\(layers\s+([^\)]*)\)', block)
        layers: set[str] = set()
        if layer_match:
            layers.add(layer_match.group(1) if layer_match.group(1) is not None else layer_match.group(2))
        if layers_match:
            layers.update(_parse_copper_layer_tokens(layers_match.group(1), copper_layers))
        summaries.append(
            {
                "net": net_code,
                "net_name": (
                    net_name_match.group(1)
                    if net_name_match and net_name_match.group(1) is not None
                    else net_name_match.group(2) if net_name_match else direct_net_name
                ),
                "layers": layers,
                "is_keepout": "(keepout" in block,
                "has_fill": "(fill yes" in block,
            }
        )
    return summaries


def required_plane_zone_failures(
    zone_summaries: list[dict[str, object]],
    actual_net_table: dict[str, int],
) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    definitions = 0
    for net_name, required_layers in sorted(REQUIRED_PLANE_ZONES.items()):
        expected_net = actual_net_table.get(net_name)
        for layer in sorted(required_layers):
            zones = [
                zone for zone in zone_summaries
                if zone["net_name"] == net_name
                and layer in set(zone["layers"])
                and zone["has_fill"]
                and not zone["is_keepout"]
            ]
            if not zones:
                failures.append(f"no filled {net_name} plane zone found on {layer}")
                continue
            definitions += len(zones)
            mismatched = [
                zone
                for zone in zones
                if zone["net"] is not None and zone["net"] != expected_net
            ]
            if mismatched:
                failures.append(
                    f"{net_name} plane zone net code mismatch on {layer}: "
                    f"zones={mismatched} {net_name}={expected_net}"
                )
    return failures, {
        "required_plane_zone_requirements": sum(len(layers) for layers in REQUIRED_PLANE_ZONES.values()),
        "required_plane_zone_definitions": definitions,
    }


PLACEMENT_CHECKS = [
    ("USB UART D- connector to ESD", ("MCU_ESP32-S3", "J1", "2", "MCU_ESP32-S3", "D7", "2"), 7.5),
    ("USB UART D+ connector to ESD", ("MCU_ESP32-S3", "J1", "3", "MCU_ESP32-S3", "D8", "2"), 9.5),
    ("USB UART D- ESD to CP2102N", ("MCU_ESP32-S3", "D7", "2", "MCU_ESP32-S3", "U10", "5"), 10.0),
    ("USB UART D+ ESD to CP2102N", ("MCU_ESP32-S3", "D8", "2", "MCU_ESP32-S3", "U10", "4"), 10.0),
    ("Native USB D- connector to ESD", ("MCU_ESP32-S3", "J2", "2", "MCU_ESP32-S3", "D12", "2"), 7.5),
    ("Native USB D+ connector to ESD", ("MCU_ESP32-S3", "J2", "3", "MCU_ESP32-S3", "D11", "2"), 9.5),
    ("Native USB D- ESD to ESP32 GPIO19", ("MCU_ESP32-S3", "D12", "2", "MCU_ESP32-S3", "U9", "13"), 4.5),
    ("Native USB D+ ESD to ESP32 GPIO20", ("MCU_ESP32-S3", "D11", "2", "MCU_ESP32-S3", "U9", "14"), 4.5),
    ("AP2112 input cap at VIN", ("POWER_IO", "C3V3IN", "1", "POWER_IO", "U3V3", "1"), 4.0),
    ("AP2112 100n output cap at VOUT", ("POWER_IO", "C3V3OUT", "1", "POWER_IO", "U3V3", "5"), 4.0),
    ("AP2112 bulk output cap at VOUT", ("POWER_IO", "C3V3BULK", "1", "POWER_IO", "U3V3", "5"), 4.0),
    ("ESP32 local 3V3 decap", ("MCU_ESP32-S3", "C43", "1", "MCU_ESP32-S3", "U9", "2"), 3.0),
    ("ESP32 EN capacitor", ("MCU_ESP32-S3", "C44", "1", "MCU_ESP32-S3", "U9", "3"), 4.0),
    ("ESP32 EN pull-up", ("MCU_ESP32-S3", "R54", "2", "MCU_ESP32-S3", "U9", "3"), 5.0),
    ("ESP32 BOOT pull-up", ("MCU_ESP32-S3", "R53", "2", "MCU_ESP32-S3", "U9", "27"), 4.0),
]

for _color in ["IR", "RED", "GREEN", "BLUE"]:
    _sheet = f"TIA_{_color}"
    PLACEMENT_CHECKS += [
        (f"{_sheet} photodiode anode to OPA380 -IN", (_sheet, "D1", "2", _sheet, "U1", "2"), 5.5),
        (f"{_sheet} feedback trimmer at OPA380 -IN", (_sheet, "U1", "2", _sheet, "RVFB", "1"), 3.5),
        (f"{_sheet} feedback capacitor at OPA380 -IN", (_sheet, "U1", "2", _sheet, "C1", "1"), 2.5),
        (f"{_sheet} feedback trimmer at OPA380 OUT", (_sheet, "RVFB", "2", _sheet, "U1", "6"), 4.5),
        (f"{_sheet} feedback capacitor at OPA380 OUT", (_sheet, "C1", "2", _sheet, "U1", "6"), 2.5),
        (f"{_sheet} OPA380 supply decoupling", (_sheet, "C2", "1", _sheet, "U1", "7"), 2.5),
        (f"{_sheet} PD bias resistor at cathode", (_sheet, "RB", "2", _sheet, "D1", "1"), 4.5),
        (f"{_sheet} PD cathode bypass at cathode", (_sheet, "CB", "1", _sheet, "D1", "1"), 3.0),
        (f"{_sheet} VBIAS resistor at OPA380 +IN", (_sheet, "R1", "2", _sheet, "U1", "3"), 5.0),
        (f"{_sheet} VBIAS capacitor at OPA380 +IN", (_sheet, "C11", "1", _sheet, "U1", "3"), 4.0),
    ]

for _color in ["IR", "RED", "GREEN", "BLUE"]:
    _sheet = f"LASER_{_color}"
    PLACEMENT_CHECKS += [
        (f"{_sheet} TLV9001 OUT to gate resistor", (_sheet, "U11", "1", _sheet, "R31", "1"), 3.5),
        (f"{_sheet} gate resistor to AO3400A gate", (_sheet, "R31", "2", _sheet, "Q1", "1"), 2.5),
        (f"{_sheet} AO3400A source to sense resistor", (_sheet, "Q1", "2", _sheet, "R11", "1"), 2.2),
        (f"{_sheet} sense feedback to TLV9001 -IN", (_sheet, "R11", "1", _sheet, "U11", "4"), 6.0),
        (f"{_sheet} isolated ISENSE tap at sense resistor", (_sheet, "R12", "1", _sheet, "R11", "1"), 3.5),
        (f"{_sheet} TLV9001 supply decoupling", (_sheet, "C22", "1", _sheet, "U11", "5"), 2.5),
        (f"{_sheet} PWM input resistor at TLV9001 +IN", (_sheet, "R21", "2", _sheet, "U11", "3"), 2.5),
        (f"{_sheet} command limiter at TLV9001 +IN", (_sheet, "R22", "1", _sheet, "U11", "3"), 3.0),
        (f"{_sheet} command filter cap at TLV9001 +IN", (_sheet, "C21", "1", _sheet, "U11", "3"), 3.0),
        (f"{_sheet} compensation cap at TLV9001 -IN", (_sheet, "CC", "1", _sheet, "U11", "4"), 2.5),
        (f"{_sheet} compensation cap at TLV9001 OUT", (_sheet, "CC", "2", _sheet, "U11", "1"), 3.0),
    ]

_ina_in_plus_pins = {1: "3", 2: "5", 3: "10", 4: "12"}
_ina_out_pins = {1: "1", 2: "7", 3: "8", 4: "14"}
for _index, _color in enumerate(["IR", "RED", "GREEN"], 1):
    PLACEMENT_CHECKS += [
        (f"MPD_RAW{_index} direct LD monitor to sense resistor", (f"LASER_{_color}", "LD", "3", "POWER_IO", f"RMPD{_index}", "1"), 4.0),
        (f"MPD_RAW{_index} sense resistor to INA input", ("POWER_IO", f"RMPD{_index}", "1", "POWER_IO", "UMPD", _ina_in_plus_pins[_index]), 4.0),
        (f"MPD{_index} ADC resistor to filter capacitor", ("POWER_IO", f"RADC{_index}", "2", "POWER_IO", f"CMPD{_index}", "1"), 2.5),
    ]
PLACEMENT_CHECKS += [
    ("MPD_RAW4 spare sense resistor to INA input", ("POWER_IO", "RMPD4", "1", "POWER_IO", "UMPD", _ina_in_plus_pins[4]), 4.0),
    ("MPD_AMP4 INA output to ADC resistor", ("POWER_IO", "UMPD", _ina_out_pins[4], "POWER_IO", "RADC4", "1"), 4.0),
    ("MPD4 ADC resistor to filter capacitor", ("POWER_IO", "RADC4", "2", "POWER_IO", "CMPD4", "1"), 2.5),
]


def main() -> int:
    board_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("laser_controller.kicad_pcb")
    netlist_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/lc.net")
    if not board_path.exists():
        print(f"FAIL PCB file not found: {board_path}")
        return 1
    if not netlist_path.exists():
        print(f"FAIL netlist file not found: {netlist_path}")
        return 1

    gen_pcb.NET = str(netlist_path)
    _, _, expected_board_ref_by_comp, expected_pad_data, expected_net_names = gen_pcb.build_board(emit_routes=False)
    expected_pad_nets = {
        ref: {pin: net_name for pin, (_, net_name) in pads.items()}
        for ref, pads in expected_pad_data.items()
    }
    expected_net_table = {name: index + 1 for index, name in enumerate(expected_net_names)}

    actual_pad_nets, duplicate_refs = parse_board_pad_nets(board_path)
    pad_inventory = parse_board_pad_inventory(board_path)
    footprint_geometry = parse_footprint_geometry(board_path)
    board_bounds, has_board_outline = parse_board_outline_bounds(board_path)
    actual_net_table = parse_board_net_table(board_path)
    actual_net_by_code = {code: name for name, code in actual_net_table.items()}
    actual_segments = parse_board_segments(board_path, actual_net_by_code)
    actual_vias = parse_board_vias(board_path, actual_net_by_code)
    duplicate_via_items = duplicate_via_failures(actual_vias)
    via_policy_failures, via_policy_summary = route_via_policy_failures(actual_vias)
    route_layer_failures, route_layer_summary = route_layer_policy_failures(actual_segments)
    route_width_failures, route_width_summary = route_width_policy_failures(actual_segments)
    route_length_failures, route_length_summary = route_length_policy_failures(actual_segments)
    laser_current_width_failures, checked_laser_current_segments = laser_current_width_review_failures(actual_segments)
    sensitive_laser_failures, sensitive_laser_summary = sensitive_to_laser_clearance_failures(actual_segments)
    usb_route_rows, usb_route_failures = usb_route_quality(actual_segments, actual_vias)
    pad_bounds_failures, checked_pad_bounds = pad_board_bounds_failures(board_path, board_bounds)
    pad_overlap_failures, checked_pad_overlap_pairs = different_net_pad_overlap_failures(board_path)
    actual_net_classes = parse_board_net_classes(board_path)
    declared_layers = parse_declared_copper_layers(board_path)
    used_layers = parse_used_specific_copper_layers(board_path)
    rail_pad_via_failures, rail_pad_via_summary = rail_pad_via_coverage_failures(
        board_path,
        actual_vias,
        declared_layers,
    )
    additional_power_pad_via_failures, additional_power_pad_via_summary = (
        additional_power_pad_via_coverage_failures(
            board_path,
            actual_vias,
            declared_layers,
        )
    )
    copper_bounds_failures, checked_copper_bounds = copper_board_bounds_failures(
        actual_segments,
        actual_vias,
        board_bounds,
    )
    dangling_failures, dangling_summary = dangling_copper_failures(
        board_path,
        actual_segments,
        actual_vias,
        declared_layers,
    )
    segment_pad_failures, checked_segment_pad_clearances = segment_pad_clearance_failures(
        board_path,
        actual_segments,
        declared_layers,
    )
    keepout_zone_layers = parse_keepout_zone_layers(board_path, declared_layers)
    zone_summaries = parse_zone_summaries(board_path, declared_layers)
    required_plane_failures, required_plane_summary = required_plane_zone_failures(
        zone_summaries,
        actual_net_table,
    )
    keepout_intrusion_failures, checked_keepout_items = antenna_keepout_intrusion_failures(
        board_path,
        actual_segments,
        actual_vias,
        declared_layers,
    )
    expected_net_classes = {
        name: set(nets)
        for name, nets in gen_pcb.build_net_classes(expected_net_names).items()
    }
    expected_layers = {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"}
    full_route_summary, split_signal_nets, pending_zone_or_rail_nets = split_multi_pad_signal_nets(
        board_path,
        declared_layers,
        actual_segments,
        actual_vias,
    )

    failures: list[str] = []
    default_class_nets = sorted(expected_net_classes.get("Default", set()))
    if default_class_nets:
        failures.append(
            "unclassified nets assigned to Default net class: "
            + ", ".join(default_class_nets)
        )
    if duplicate_refs:
        failures.append(f"duplicate footprint references: {duplicate_refs}")
    if not has_board_outline:
        failures.append(
            f"no Edge.Cuts board outline found; board-bounds checks used generated "
            f"{BOARD_WIDTH_MM:.0f}x{BOARD_HEIGHT_MM:.0f} mm fallback"
        )
    else:
        min_x, min_y, max_x, max_y = board_bounds
        if (
            abs((max_x - min_x) - BOARD_WIDTH_MM) > BOARD_SIZE_TOLERANCE_MM
            or abs((max_y - min_y) - BOARD_HEIGHT_MM) > BOARD_SIZE_TOLERANCE_MM
        ):
            failures.append(
                f"board outline size mismatch: expected {BOARD_WIDTH_MM:.0f}x{BOARD_HEIGHT_MM:.0f} mm, "
                f"got {board_bounds_label(board_bounds)}"
            )
    missing_geometry_refs = sorted(set(expected_pad_nets) - set(footprint_geometry))
    if missing_geometry_refs:
        failures.append(f"footprints missing parseable placement/pad geometry: {missing_geometry_refs}")
    if declared_layers != expected_layers:
        failures.append(
            f"declared copper layers mismatch: expected={sorted(expected_layers)} got={sorted(declared_layers)}"
        )
    undeclared_layers = sorted(used_layers - declared_layers)
    if undeclared_layers:
        failures.append(f"used copper layers are not declared: {undeclared_layers}")
    if not keepout_zone_layers:
        failures.append("no copper keepout zones found; ESP32 antenna keepout is not represented")
    partial_keepouts = [
        sorted(layers)
        for layers in keepout_zone_layers
        if layers and layers != declared_layers
    ]
    if partial_keepouts:
        failures.append(
            f"copper keepout zones do not cover every declared copper layer: {partial_keepouts}"
        )
    failures.extend(required_plane_failures)
    if set(actual_net_table) != set(expected_net_table):
        missing = sorted(set(expected_net_table) - set(actual_net_table))
        extra = sorted(set(actual_net_table) - set(expected_net_table))
        failures.append(f"net table mismatch: missing={missing} extra={extra}")
    segment_failures = [
        f"segment has invalid net/layer/width: {segment}"
        for segment in actual_segments
        if not segment["net"] or segment["layer"] not in declared_layers or float(segment["width"]) <= 0
    ]
    failures.extend(segment_failures)
    failures.extend(laser_current_width_failures)
    failures.extend(sensitive_laser_failures[:40])
    failures.extend(usb_route_failures)
    via_failures = [
        f"via has invalid net/layer/size/drill: {via}"
        for via in actual_vias
        if (
            not via["net"]
            or not set(via["layers"]).issubset(declared_layers)
            or float(via["size"]) <= 0
            or float(via["drill"]) <= 0
            or float(via["drill"]) >= float(via["size"])
        )
    ]
    failures.extend(via_failures)
    failures.extend(duplicate_via_items)
    failures.extend(via_policy_failures)
    failures.extend(route_layer_failures[:40])
    failures.extend(route_width_failures[:40])
    failures.extend(route_length_failures[:40])
    clearance_items = actual_segments + via_clearance_segment_items(actual_vias, declared_layers)
    failures.extend(cross_net_segment_clearance_failures(clearance_items)[:40])
    failures.extend(segment_pad_failures[:40])
    failures.extend(via_pad_clearance_failures(board_path, actual_vias)[:40])
    failures.extend(rail_pad_via_failures[:40])
    failures.extend(additional_power_pad_via_failures[:40])
    failures.extend(pad_bounds_failures[:40])
    failures.extend(copper_bounds_failures[:40])
    failures.extend(dangling_failures[:40])
    failures.extend(pad_overlap_failures[:40])
    failures.extend(keepout_intrusion_failures[:40])
    if split_signal_nets:
        failures.append(
            "non-rail multi-pad nets are not explicitly routed: "
            + "; ".join(split_signal_nets[:20])
        )
    unexpected_pending_zone_or_rail_nets = sorted(
        set(pending_zone_or_rail_nets) - EXPECTED_ZONE_OR_RAIL_PENDING_NETS
    )
    if unexpected_pending_zone_or_rail_nets:
        failures.append(
            "unexpected zone/rail pending multi-pad nets: "
            + ", ".join(unexpected_pending_zone_or_rail_nets)
        )
    if actual_net_classes != expected_net_classes:
        expected_class_names = set(expected_net_classes)
        actual_class_names = set(actual_net_classes)
        missing_classes = sorted(expected_class_names - actual_class_names)
        extra_classes = sorted(actual_class_names - expected_class_names)
        changed_classes = []
        for name in sorted(expected_class_names & actual_class_names):
            if expected_net_classes[name] != actual_net_classes[name]:
                missing = sorted(expected_net_classes[name] - actual_net_classes[name])
                extra = sorted(actual_net_classes[name] - expected_net_classes[name])
                changed_classes.append(f"{name}: missing={missing} extra={extra}")
        failures.append(
            "net class mismatch: "
            f"missing_classes={missing_classes} extra_classes={extra_classes} "
            f"changed={changed_classes}"
        )

    def board_ref(sheet: str, local_ref: str) -> str:
        return expected_board_ref_by_comp[(sheet, ref_for(sheet, local_ref))]

    allowed_unnetted_pads = intentional_unnetted_pad_names(expected_board_ref_by_comp)
    physical_pad_names = {
        ref: {pad_name for pad_name, _ in pads}
        for ref, pads in pad_inventory.items()
    }
    for ref, allowed in sorted(allowed_unnetted_pads.items()):
        missing_allowed = sorted(
            pad_name
            for pad_name in allowed
            if pad_name and pad_name not in physical_pad_names.get(ref, set())
        )
        if missing_allowed:
            failures.append(
                f"{ref}: intentional NC/unused pads missing from physical footprint: {missing_allowed}"
            )
    checked_unnetted_pad_instances = 0
    for ref, pads in sorted(pad_inventory.items()):
        allowed = allowed_unnetted_pads.get(ref, set())
        for pad_name, net_name in pads:
            if net_name:
                continue
            checked_unnetted_pad_instances += 1
            if pad_name not in allowed:
                display = pad_name if pad_name else "<blank>"
                failures.append(
                    f"{ref}.{display}: unnetted physical pad is not an intentional NC/mechanical pad"
                )

    strict_placement_geometry = os.environ.get("LC_STRICT_PLACEMENT_GEOMETRY") == "1"
    placement_distances: list[tuple[str, float, float]] = []
    for description, args, limit_mm in PLACEMENT_CHECKS:
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        try:
            actual_mm = min_pad_distance(
                footprint_geometry,
                board_ref(sheet_a, ref_a),
                pin_a,
                board_ref(sheet_b, ref_b),
                pin_b,
            )
        except KeyError as exc:
            if strict_placement_geometry:
                failures.append(f"{description}: {exc}")
            continue
        placement_distances.append((description, actual_mm, limit_mm))
        if strict_placement_geometry and actual_mm > limit_mm:
            failures.append(f"{description}: {actual_mm:.2f} mm exceeds {limit_mm:.2f} mm")

    routed_critical_links = count_connected_critical_route_links(
        board_path,
        actual_segments,
        actual_vias,
        declared_layers,
        expected_board_ref_by_comp,
        expected_pad_nets,
    )
    if strict_placement_geometry and routed_critical_links < MIN_ROUTED_CRITICAL_LINKS:
        failures.append(
            f"only {routed_critical_links}/{len(CRITICAL_ROUTE_LINKS)} critical local route links are connected; "
            f"expected at least {MIN_ROUTED_CRITICAL_LINKS}"
        )

    for ref, expected_pads in sorted(expected_pad_nets.items()):
        if ref not in actual_pad_nets:
            failures.append(f"{ref}: expected footprint missing from PCB")
            continue
        for pin, expected_net in sorted(expected_pads.items()):
            actual_net = actual_pad_nets[ref].get(pin)
            if actual_net != expected_net:
                failures.append(
                    f"{ref}.{pin}: expected {expected_net!r}, got {actual_net!r}"
                )

    for ref, actual_pads in sorted(actual_pad_nets.items()):
        for pin, actual_net in sorted(actual_pads.items()):
            expected_net = expected_pad_nets.get(ref, {}).get(pin)
            if expected_net is None:
                failures.append(f"{ref}.{pin}: unexpected PCB net {actual_net!r}")

    if failures:
        print(f"FAIL {len(failures)} PCB pad-net assertions")
        for failure in failures[:80]:
            print(f"  {failure}")
        if len(failures) > 80:
            print(f"  ... {len(failures) - 80} more")
        return 1

    checked_pads = sum(len(pads) for pads in expected_pad_nets.values())
    print(
        "PASS "
        f"{checked_pads} PCB pad-net assignments across "
        f"{len(expected_pad_nets)} footprints, {len(expected_net_names)} named nets, "
        f"{len(expected_net_classes)} net classes, {len(declared_layers)} copper layers, "
        f"{required_plane_summary['required_plane_zone_definitions']}/"
        f"{required_plane_summary['required_plane_zone_requirements']} required GND/+3V3/+5V plane-zone definitions, "
        f"{len(placement_distances)} placement proximity checks, "
        f"{checked_unnetted_pad_instances} intentional unnetted pad instances, "
        f"{checked_pad_bounds} board-bounded pads, "
        f"{checked_copper_bounds} board-bounded copper endpoints/vias, "
        f"{checked_pad_overlap_pairs} different-net pad-overlap checks, "
        f"{checked_segment_pad_clearances} trace-to-pad clearance checks, "
        f"{checked_keepout_items} antenna-keepout intrusion checks, "
        f"{dangling_summary['segment_endpoints_checked']} routed segment endpoints and "
        f"{dangling_summary['vias_checked']} vias checked for dangling copper, "
        f"{route_layer_summary['route_segments_checked']} routed segments checked by layer policy, "
        f"{route_width_summary['route_segments_checked']} routed segments checked by width policy, "
        f"{route_length_summary['route_nets_checked']} sensitive local nets checked by length policy, "
        f"{len(actual_segments)} routed copper segments, "
        f"{checked_laser_current_segments} reviewed Laser_Current segments, "
        f"{sum(1 for row in usb_route_rows if row['section'] != 'total')} USB route sections, "
        f"sensitive-to-laser clearances [{format_sensitive_to_laser_summary(sensitive_laser_summary)}], "
        f"{len(actual_vias)} vias, "
        f"{via_policy_summary['non_power_vias_checked']} non-power vias checked by route policy, "
        f"{rail_pad_via_summary['rail_pads_checked']} rail pads checked for plane vias "
        f"({rail_pad_via_summary['rail_pads_with_in_pad_via']} in-pad, "
        f"{rail_pad_via_summary['rail_pads_with_nearby_via']} nearby), "
        f"{additional_power_pad_via_summary['additional_power_pads_checked']} additional power pads checked for vias "
        f"({additional_power_pad_via_summary['additional_power_pads_with_in_pad_via']} in-pad, "
        f"{additional_power_pad_via_summary['additional_power_pads_with_nearby_via']} nearby), "
        f"{full_route_summary['explicitly_routed_multi_pad_nets']}/{full_route_summary['multi_pad_nets']} explicitly routed multi-pad nets, "
        f"{full_route_summary['zone_or_rail_pending_multi_pad_nets']} zone/rail pending nets, "
        f"and {routed_critical_links}/{len(CRITICAL_ROUTE_LINKS)} connected critical local route links"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
