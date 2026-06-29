#!/usr/bin/env python3
"""Verify the placement-staging PCB contract.

This checker is for the intentional "fresh placement" state:

* the 90 x 50 mm Edge.Cuts outline is preserved,
* physical schematic footprints are loaded outside the outline,
* every physical schematic footprint is loaded onto the staged PCB,
* no board-level traces, vias, or zones are emitted,
* footprint pad nets match the exported schematic netlist, and
* staged footprints do not overlap each other.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from math import cos, hypot, radians, sin
from pathlib import Path

import gen_pcb
from check_laser_controller_netlist import parse_components


BOARD_WIDTH_MM = 90.0
BOARD_HEIGHT_MM = 50.0
OUTSIDE_MARGIN_MM = 5.0
EXPECTED_EMPTY_FOOTPRINT_REFS: set[str] = set()
SHEET_ORDER = [
    "TIA_IR",
    "TIA_RED",
    "TIA_GREEN",
    "TIA_BLUE",
    "LASER_IR",
    "LASER_RED",
    "LASER_GREEN",
    "LASER_BLUE",
    "MCU_ESP32-S3",
    "POWER_IO",
]

BBox = tuple[float, float, float, float]


def blocks_named(text: str, name: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    prefix = f"({name} "
    for line in text.splitlines():
        if not in_block and line.lstrip().startswith(prefix):
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


def top_level_count(text: str, name: str) -> int:
    count = 0
    depth = 0
    prefix = f"({name} "
    for line in text.splitlines():
        if depth == 1 and line.lstrip().startswith(prefix):
            count += 1
        depth += line.count("(") - line.count(")")
    return count


def top_level_edge_lines(text: str) -> set[tuple[tuple[float, float], tuple[float, float]]]:
    lines: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    depth = 0
    pattern = re.compile(
        r'\(gr_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(end\s+([-\d.]+)\s+([-\d.]+)\).*?\(layer\s+"Edge.Cuts"\)'
    )
    for line in text.splitlines():
        if depth == 1 and line.lstrip().startswith("(gr_line "):
            match = pattern.search(line)
            if match:
                start = (round(float(match.group(1)), 4), round(float(match.group(2)), 4))
                end = (round(float(match.group(3)), 4), round(float(match.group(4)), 4))
                lines.add((start, end))
        depth += line.count("(") - line.count(")")
    return lines


def footprint_ref(block: str) -> str:
    match = re.search(r'\(fp_text\s+reference\s+"?([^"\s\)]+)"?', block)
    return match.group(1) if match else ""


def pad_blocks(footprint_text: str) -> list[str]:
    return blocks_named(footprint_text, "pad")


def board_pad_nets(board_text: str) -> dict[str, dict[str, set[str]]]:
    inventory: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for block in blocks_named(board_text, "footprint"):
        ref = footprint_ref(block)
        if not ref:
            continue
        for pad in pad_blocks(block):
            pad_match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
            net_match = re.search(r'\(net\s+\d+\s+"([^"]*)"\)', pad)
            if not pad_match or not net_match:
                continue
            pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
            inventory[ref][pad_name].add(net_match.group(1))
    return inventory


def board_net_table(board_text: str) -> dict[str, int]:
    table: dict[str, int] = {}
    for code, name in re.findall(r'^\s*\(net\s+(\d+)\s+"([^"]*)"\)', board_text, re.M):
        if name:
            table[name] = int(code)
    return table


def transform_point(x: float, y: float, ox: float, oy: float, rot: float) -> tuple[float, float]:
    theta = radians(rot)
    return (
        ox + x * cos(theta) - y * sin(theta),
        oy + x * sin(theta) + y * cos(theta),
    )


def bbox_from_points(points: list[tuple[float, float]]) -> BBox:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def footprint_bbox(block: str) -> BBox | None:
    at = re.search(r'^\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block, re.M)
    if not at:
        return None
    ox = float(at.group(1))
    oy = float(at.group(2))
    rot = float(at.group(3) or 0)

    points: list[tuple[float, float]] = []
    line_pattern = re.compile(
        r'\(fp_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(end\s+([-\d.]+)\s+([-\d.]+)\)[\s\S]*?\(layer\s+"?[FB]\.CrtYd"?\)'
    )
    for match in line_pattern.finditer(block):
        points.append(transform_point(float(match.group(1)), float(match.group(2)), ox, oy, rot))
        points.append(transform_point(float(match.group(3)), float(match.group(4)), ox, oy, rot))

    circle_pattern = re.compile(
        r'\(fp_circle\s+\(center\s+([-\d.]+)\s+([-\d.]+)\)\s+'
        r'\(end\s+([-\d.]+)\s+([-\d.]+)\)[\s\S]*?\(layer\s+"?[FB]\.CrtYd"?\)'
    )
    for match in circle_pattern.finditer(block):
        cx = float(match.group(1))
        cy = float(match.group(2))
        ex = float(match.group(3))
        ey = float(match.group(4))
        radius = hypot(ex - cx, ey - cy)
        gx, gy = transform_point(cx, cy, ox, oy, rot)
        points.append((gx - radius, gy - radius))
        points.append((gx + radius, gy + radius))

    if points:
        return bbox_from_points(points)

    for pad in pad_blocks(block):
        pad_at = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)', pad)
        size = re.search(r'\(size\s+([-\d.]+)\s+([-\d.]+)\)', pad)
        if not pad_at or not size:
            continue
        px = float(pad_at.group(1))
        py = float(pad_at.group(2))
        sx = float(size.group(1))
        sy = float(size.group(2))
        for dx in (-sx / 2, sx / 2):
            for dy in (-sy / 2, sy / 2):
                points.append(transform_point(px + dx, py + dy, ox, oy, rot))

    return bbox_from_points(points) if points else None


def bboxes_overlap(a: BBox, b: BBox) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def zone_bboxes(footprint_text: str) -> list[BBox]:
    bboxes: list[BBox] = []
    for zone in blocks_named(footprint_text, "zone"):
        points = [
            (float(x), float(y))
            for x, y in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', zone)
        ]
        if points:
            bboxes.append(bbox_from_points(points))
    return bboxes


def bbox_outside_outline(bbox: BBox) -> bool:
    return (
        bbox[0] >= BOARD_WIDTH_MM + OUTSIDE_MARGIN_MM
        or bbox[2] <= -OUTSIDE_MARGIN_MM
        or bbox[1] >= BOARD_HEIGHT_MM + OUTSIDE_MARGIN_MM
        or bbox[3] <= -OUTSIDE_MARGIN_MM
    )


def main() -> int:
    board_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
    netlist_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/lc.net")
    if not board_path.exists():
        print(f"FAIL PCB file not found: {board_path}")
        return 1
    if not netlist_path.exists():
        print(f"FAIL netlist file not found: {netlist_path}")
        return 1

    board_text = board_path.read_text()
    gen_pcb.NET = str(netlist_path)
    _, _, _, expected_pad_data, expected_net_names = gen_pcb.build_board(emit_routes=False)
    expected_net_table = {name: index + 1 for index, name in enumerate(expected_net_names)}

    components = parse_components(netlist_path)
    refs_by_sheet: dict[str, set[str]] = defaultdict(set)
    expected_refs: set[str] = set()
    empty_refs: set[str] = set()
    footprint_resolution_failures: list[str] = []
    for comp in components:
        sheet = comp["sheet"].strip("/")
        ref = comp["ref"]
        refs_by_sheet[sheet].add(ref)
        if comp["footprint"]:
            expected_refs.add(ref)
            if gen_pcb.get_fp(comp["footprint"]) is None:
                footprint_resolution_failures.append(f"{ref}: {comp['footprint']}")
        else:
            empty_refs.add(ref)

    footprint_blocks = blocks_named(board_text, "footprint")
    actual_refs = [footprint_ref(block) for block in footprint_blocks]
    actual_ref_set = set(actual_refs)
    duplicate_refs = sorted(ref for ref, count in Counter(actual_refs).items() if count > 1)

    edge_lines = top_level_edge_lines(board_text)
    expected_edge_lines = {
        ((0.0, 0.0), (90.0, 0.0)),
        ((90.0, 0.0), (90.0, 50.0)),
        ((90.0, 50.0), (0.0, 50.0)),
        ((0.0, 50.0), (0.0, 0.0)),
    }
    board_segments = top_level_count(board_text, "segment")
    board_vias = top_level_count(board_text, "via")
    board_zones = top_level_count(board_text, "zone")
    footprint_zones = len(blocks_named(board_text, "zone")) - board_zones

    expected_pad_nets = {
        ref: {pin: net_name for pin, (_, net_name) in pads.items()}
        for ref, pads in expected_pad_data.items()
        if ref in expected_refs
    }
    actual_pad_nets = board_pad_nets(board_text)
    actual_net_table = board_net_table(board_text)

    bboxes: dict[str, BBox] = {}
    esp32_keepout_bboxes: dict[str, list[BBox]] = {}
    geometry_failures: list[str] = []
    for block in footprint_blocks:
        ref = footprint_ref(block)
        bbox = footprint_bbox(block)
        if not ref or bbox is None:
            geometry_failures.append(ref or "<unknown>")
            continue
        bboxes[ref] = bbox
        if "ESP32-S3-WROOM-1" in block:
            esp32_keepout_bboxes[ref] = [
                zone_bbox
                for zone_bbox in zone_bboxes(block)
                if zone_bbox
            ]

    failures: list[str] = []
    if footprint_resolution_failures:
        failures.append("unresolved non-empty footprints: " + ", ".join(footprint_resolution_failures))
    if edge_lines != expected_edge_lines:
        failures.append(f"Edge.Cuts outline mismatch: expected={sorted(expected_edge_lines)} got={sorted(edge_lines)}")
    if board_segments:
        failures.append(f"unexpected board-level routed segments: {board_segments}")
    if board_vias:
        failures.append(f"unexpected board-level vias: {board_vias}")
    if board_zones:
        failures.append(f"unexpected board-level zones: {board_zones}")
    if empty_refs != EXPECTED_EMPTY_FOOTPRINT_REFS:
        failures.append(f"empty-footprint refs changed: expected={sorted(EXPECTED_EMPTY_FOOTPRINT_REFS)} got={sorted(empty_refs)}")
    if duplicate_refs:
        failures.append(f"duplicate footprint references: {duplicate_refs}")
    missing_refs = sorted(expected_refs - actual_ref_set)
    extra_refs = sorted(actual_ref_set - expected_refs)
    if missing_refs:
        failures.append(f"missing physical footprints: {missing_refs}")
    if extra_refs:
        failures.append(f"unexpected footprints not in physical schematic refs: {extra_refs}")
    if geometry_failures:
        failures.append(f"footprints missing parseable bbox geometry: {sorted(geometry_failures)}")
    if actual_net_table != expected_net_table:
        missing = sorted(set(expected_net_table) - set(actual_net_table))
        extra = sorted(set(actual_net_table) - set(expected_net_table))
        wrong_codes = sorted(
            name
            for name in set(expected_net_table) & set(actual_net_table)
            if expected_net_table[name] != actual_net_table[name]
        )
        failures.append(f"net table mismatch: missing={missing} extra={extra} wrong_codes={wrong_codes}")

    for ref, expected_pads in sorted(expected_pad_nets.items()):
        actual_pads = actual_pad_nets.get(ref, {})
        for pin, expected_net in sorted(expected_pads.items()):
            actual_nets = actual_pads.get(pin, set())
            if actual_nets != {expected_net}:
                failures.append(f"{ref}.{pin} pad net mismatch: expected={expected_net} got={sorted(actual_nets)}")
        extra_netted_pins = sorted(set(actual_pads) - set(expected_pads))
        if extra_netted_pins:
            failures.append(f"{ref} has unexpected netted pads: {extra_netted_pins}")

    outside_failures = [
        f"{ref} bbox={tuple(round(value, 3) for value in bbox)}"
        for ref, bbox in sorted(bboxes.items())
        if not bbox_outside_outline(bbox)
    ]
    if outside_failures:
        failures.append("footprints not staged outside outline: " + "; ".join(outside_failures[:20]))

    refs = sorted(bboxes)
    overlap_failures: list[str] = []
    for index, ref_a in enumerate(refs):
        for ref_b in refs[index + 1 :]:
            if bboxes_overlap(bboxes[ref_a], bboxes[ref_b]):
                overlap_failures.append(f"{ref_a}/{ref_b}")
    if overlap_failures:
        failures.append("overlapping footprint courtyards/bboxes: " + ", ".join(overlap_failures[:40]))

    for ref, zone_bbox_list in sorted(esp32_keepout_bboxes.items()):
        if not zone_bbox_list:
            failures.append(f"{ref} ESP32 antenna keepout zone missing")
            continue
        detached = [
            tuple(round(value, 3) for value in zone_bbox)
            for zone_bbox in zone_bbox_list
            if not bboxes_overlap(zone_bbox, bboxes[ref])
        ]
        if detached:
            failures.append(f"{ref} ESP32 antenna keepout detached from footprint bbox: {detached}")

    sheet_bboxes: dict[str, BBox] = {}
    for sheet in SHEET_ORDER:
        sheet_refs = refs_by_sheet.get(sheet, set()) & actual_ref_set
        if not sheet_refs:
            failures.append(f"sheet has no staged physical footprints: {sheet}")
            continue
        present_bboxes = [bboxes[ref] for ref in sheet_refs if ref in bboxes]
        if not present_bboxes:
            continue
        sheet_bboxes[sheet] = (
            min(bbox[0] for bbox in present_bboxes),
            min(bbox[1] for bbox in present_bboxes),
            max(bbox[2] for bbox in present_bboxes),
            max(bbox[3] for bbox in present_bboxes),
        )
    sheet_overlap_failures: list[str] = []
    for index, first in enumerate(SHEET_ORDER):
        for second in SHEET_ORDER[index + 1 :]:
            if (
                first in sheet_bboxes
                and second in sheet_bboxes
                and bboxes_overlap(sheet_bboxes[first], sheet_bboxes[second])
            ):
                first_bbox = tuple(round(value, 3) for value in sheet_bboxes[first])
                second_bbox = tuple(round(value, 3) for value in sheet_bboxes[second])
                sheet_overlap_failures.append(f"{first} {first_bbox} vs {second} {second_bbox}")
    if sheet_overlap_failures:
        failures.append("sheet staging groups overlap: " + "; ".join(sheet_overlap_failures[:20]))

    if failures:
        print("FAIL PCB staging")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    sheet_counts = ", ".join(
        f"{sheet}:{len(refs_by_sheet.get(sheet, set()) & actual_ref_set)}" for sheet in SHEET_ORDER
    )
    print(
        "PASS PCB staging: "
        f"{len(actual_ref_set)} physical footprints loaded, "
        f"{len(empty_refs)} empty-footprint symbols skipped, "
        f"0 board-level segments/vias/zones, "
        f"{footprint_zones} footprint-internal zone/keepout block(s), "
        f"{len(bboxes)} non-overlapping staged bboxes outside the {BOARD_WIDTH_MM:.0f} x {BOARD_HEIGHT_MM:.0f} mm outline; "
        f"sections {sheet_counts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
