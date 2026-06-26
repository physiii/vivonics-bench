#!/usr/bin/env python3
"""Fabrication release gate for the generated bench laser-controller PCB.

This is intentionally stricter than check_laser_controller_pcb.py.  The PCB
checker proves generated pad/net/routing consistency; this script fails while
generated-copper blockers such as split multi-pad nets, pending rail/zone nets,
or unacceptable laser cathode geometry remain.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from heapq import heappop, heappush
from pathlib import Path

from circuit_designators import WL, ref_for
from check_laser_controller_pcb import (
    parse_board_net_table,
    parse_board_segments,
    parse_board_vias,
    parse_declared_copper_layers,
    parse_footprint_geometry,
    split_multi_pad_signal_nets,
)


LASER_CATHODE_MIN_WIDTH_MM = 0.60
LASER_CATHODE_MAX_LENGTH_MM = 70.0
LASER_SUPPLY_MIN_WIDTH_MM = 0.80
LASER_SUPPLY_MAX_LENGTH_MM = 45.0
LASER_SUPPLY_MIN_VIAS = 2
LASER_SENSE_RETURN_MAX_PATH_MM = 6.0


def laser_cathode_geometry_failures(segments: list[dict[str, object]]) -> list[str]:
    by_net: dict[str, list[dict[str, object]]] = defaultdict(list)
    for segment in segments:
        net = str(segment["net"])
        if net.startswith("LASER_N"):
            by_net[net].append(segment)

    failures: list[str] = []
    for net, net_segments in sorted(by_net.items()):
        widths = sorted({float(segment["width"]) for segment in net_segments})
        total_length = 0.0
        for segment in net_segments:
            ax, ay = segment["a"]  # type: ignore[misc]
            bx, by = segment["b"]  # type: ignore[misc]
            total_length += ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
        narrow_widths = [width for width in widths if width < LASER_CATHODE_MIN_WIDTH_MM]
        if narrow_widths:
            width_text = ", ".join(f"{width:.2f}mm" for width in narrow_widths)
            failures.append(
                f"{net}: {len(net_segments)} cathode/load-path segments include copper below "
                f"{LASER_CATHODE_MIN_WIDTH_MM:.2f}mm ({width_text}), "
                f"{total_length:.2f}mm total cathode route length"
            )
        if total_length > LASER_CATHODE_MAX_LENGTH_MM:
            failures.append(
                f"{net}: {total_length:.2f}mm cathode/load-path route exceeds "
                f"{LASER_CATHODE_MAX_LENGTH_MM:.2f}mm generated-layout limit"
            )
    return failures


def _segment_length(segment: dict[str, object]) -> float:
    ax, ay = segment["a"]  # type: ignore[misc]
    bx, by = segment["b"]  # type: ignore[misc]
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def laser_supply_geometry_failures(
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
) -> list[str]:
    net_segments = [segment for segment in segments if str(segment["net"]) == "LASER_V+"]
    net_vias = [via for via in vias if str(via["net"]) == "LASER_V+"]
    failures: list[str] = []
    if not net_segments:
        return ["LASER_V+: no routed laser-anode supply copper found"]

    widths = sorted({float(segment["width"]) for segment in net_segments})
    total_length = sum(_segment_length(segment) for segment in net_segments)
    narrow_widths = [width for width in widths if width < LASER_SUPPLY_MIN_WIDTH_MM]
    if narrow_widths:
        width_text = ", ".join(f"{width:.2f}mm" for width in narrow_widths)
        failures.append(
            f"LASER_V+: {len(net_segments)} laser-anode supply segments include copper below "
            f"{LASER_SUPPLY_MIN_WIDTH_MM:.2f}mm ({width_text}), "
            f"{total_length:.2f}mm total supply route length"
        )
    if total_length > LASER_SUPPLY_MAX_LENGTH_MM:
        failures.append(
            f"LASER_V+: {total_length:.2f}mm laser-anode supply route exceeds "
            f"{LASER_SUPPLY_MAX_LENGTH_MM:.2f}mm generated-layout limit"
        )
    if len(net_vias) < LASER_SUPPLY_MIN_VIAS:
        failures.append(
            f"LASER_V+: only {len(net_vias)} supply vias; expected at least "
            f"{LASER_SUPPLY_MIN_VIAS} via transitions for the generated F.Cu/In2.Cu trunk"
        )
    for via in net_vias:
        if float(via["size"]) < 0.60 or float(via["drill"]) < 0.30:
            failures.append(
                f"LASER_V+: undersized supply via at {via['at']} "
                f"{float(via['size']):.2f}/{float(via['drill']):.2f}mm"
            )
    return failures


def _point_key(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], 4), round(point[1], 4))


def _shortest_gnd_path_lengths(
    start: tuple[float, float],
    segments: list[dict[str, object]],
) -> dict[tuple[float, float], float]:
    graph: dict[tuple[float, float], list[tuple[float, tuple[float, float]]]] = defaultdict(list)
    for segment in segments:
        if str(segment["net"]) != "GND":
            continue
        a = _point_key(segment["a"])  # type: ignore[arg-type]
        b = _point_key(segment["b"])  # type: ignore[arg-type]
        length = _segment_length(segment)
        graph[a].append((length, b))
        graph[b].append((length, a))

    start_key = _point_key(start)
    distances: dict[tuple[float, float], float] = {start_key: 0.0}
    queue: list[tuple[float, tuple[float, float]]] = [(0.0, start_key)]
    while queue:
        distance, point = heappop(queue)
        if distance != distances.get(point):
            continue
        for length, neighbor in graph.get(point, []):
            candidate = distance + length
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                heappush(queue, (candidate, neighbor))
    return distances


def _can_assign_distinct_vias(
    pad_to_vias: dict[str, set[tuple[float, float]]],
) -> bool:
    assigned: dict[tuple[float, float], str] = {}

    def assign(pad_name: str, seen: set[tuple[float, float]]) -> bool:
        for via_point in sorted(pad_to_vias[pad_name]):
            if via_point in seen:
                continue
            seen.add(via_point)
            if via_point not in assigned or assign(assigned[via_point], seen):
                assigned[via_point] = pad_name
                return True
        return False

    for pad_name in sorted(pad_to_vias):
        if not assign(pad_name, set()):
            return False
    return True


def laser_sense_return_failures(
    board_path: Path,
    segments: list[dict[str, object]],
    vias: list[dict[str, object]],
) -> list[str]:
    geometry = parse_footprint_geometry(board_path)
    high_current_gnd_vias = [
        via
        for via in vias
        if str(via["net"]) == "GND"
        and float(via["size"]) >= 0.60
        and float(via["drill"]) >= 0.30
    ]
    via_points = [_point_key(via["at"]) for via in high_current_gnd_vias]  # type: ignore[arg-type]
    failures: list[str] = []
    if len(via_points) < len(WL):
        failures.append(
            f"laser sense returns: only {len(via_points)} high-current GND vias, expected at least {len(WL)}"
        )

    pad_to_vias: dict[str, set[tuple[float, float]]] = {}
    for color in WL:
        sheet = f"LASER_{color}"
        ref = ref_for(sheet, "R11")
        pad_points = geometry.get(ref, {}).get("pads", {}).get("2", [])
        if not pad_points:
            failures.append(f"{sheet} sense resistor {ref}.2 GND pad geometry missing")
            continue
        pad_point = pad_points[0]
        distances = _shortest_gnd_path_lengths(pad_point, segments)
        reachable = {
            via_point
            for via_point in via_points
            if distances.get(via_point, float("inf")) <= LASER_SENSE_RETURN_MAX_PATH_MM
        }
        if not reachable:
            nearest = min(
                (distances.get(via_point, float("inf")) for via_point in via_points),
                default=float("inf"),
            )
            nearest_text = "unrouted" if nearest == float("inf") else f"{nearest:.2f}mm"
            failures.append(
                f"{sheet} sense resistor {ref}.2 lacks a routed high-current GND via within "
                f"{LASER_SENSE_RETURN_MAX_PATH_MM:.2f}mm; nearest routed path {nearest_text}"
            )
        pad_to_vias[f"{sheet}:{ref}.2"] = reachable

    if pad_to_vias and not _can_assign_distinct_vias(pad_to_vias):
        failures.append(
            "laser sense returns cannot be assigned to distinct high-current GND vias "
            f"within {LASER_SENSE_RETURN_MAX_PATH_MM:.2f}mm"
        )
    return failures


def main() -> int:
    board_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("laser_controller.kicad_pcb")
    netlist_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/lc.net")
    if not board_path.exists():
        print(f"FAIL release gate: PCB file not found: {board_path}")
        return 1
    if not netlist_path.exists():
        print(f"FAIL release gate: netlist file not found: {netlist_path}")
        return 1

    net_table = parse_board_net_table(board_path)
    net_by_code = {code: name for name, code in net_table.items()}
    segments = parse_board_segments(board_path, net_by_code)
    vias = parse_board_vias(board_path, net_by_code)
    declared_layers = parse_declared_copper_layers(board_path)
    full_route_summary, split_signal_nets, pending_zone_or_rail_nets = split_multi_pad_signal_nets(
        board_path,
        declared_layers,
        segments,
        vias,
    )

    failures: list[str] = []
    if split_signal_nets:
        failures.append(
            "signal/control multi-pad nets are not explicitly routed: "
            + "; ".join(split_signal_nets[:20])
        )
    if pending_zone_or_rail_nets:
        failures.append(
            "rail/zone multi-pad nets still require pour/trunk routing and KiCad refill/DRC: "
            + ", ".join(pending_zone_or_rail_nets)
        )
    failures.extend(laser_cathode_geometry_failures(segments))
    failures.extend(laser_supply_geometry_failures(segments, vias))
    failures.extend(laser_sense_return_failures(board_path, segments, vias))

    if failures:
        print("FAIL fabrication release gate")
        for failure in failures:
            print(f"  {failure}")
        print(
            "  This does not mean the audit checker failed; it means the board still has "
            "known release blockers."
        )
        return 1

    print(
        "PASS fabrication release gate: "
        f"{full_route_summary['explicitly_routed_multi_pad_nets']}/"
        f"{full_route_summary['multi_pad_nets']} multi-pad nets explicitly routed, "
        "no pending rail/zone nets, laser cathode/anode routes meet generated width targets, "
        "and laser sense returns have distinct high-current GND vias. "
        "This does not replace GUI ERC/DRC with zone refill."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
