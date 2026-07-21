#!/usr/bin/env python3
"""Repair confirmed mirrored orientation-sensitive footprints in the PCB.

Confirmed stop-ship mirrors repaired here:
- U1-U4 OPA380AID SOIC-8 TIA amplifiers.
- RV5-RV8 Bourns 3224W feedback trimmers.

The script is idempotent and intentionally narrow.  It mirrors only local
footprint graphics/pad geometry for affected references that are still in the
bad state, then moves the directly attached local escape segment endpoints to
the repaired physical pads.
"""
from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
TOL = 0.004


@dataclass(frozen=True)
class Opa:
    ref: str
    channel: str
    center: tuple[float, float]
    vout: str


@dataclass(frozen=True)
class Pot:
    ref: str
    channel: str
    center: tuple[float, float]
    vout: str


OPAS = (
    Opa("U1", "IR", (146.8, 103.085), "VOUT1"),
    Opa("U2", "RED", (130.8, 103.06), "VOUT2"),
    Opa("U3", "GREEN", (146.8, 119.085), "VOUT3"),
    Opa("U4", "BLUE", (130.8, 119.085), "VOUT4"),
)

POTS = (
    Pot("RV5", "IR", (146.8, 94.5), "VOUT1"),
    Pot("RV6", "RED", (130.8, 94.5), "VOUT2"),
    Pot("RV7", "GREEN", (146.8, 110.0), "VOUT3"),
    Pot("RV8", "BLUE", (130.8, 110.0), "VOUT4"),
)


def blocks(text: str, prefix: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    index = 0
    while True:
        start = text.find(prefix, index)
        if start < 0:
            break
        depth = 0
        end = start
        in_string = False
        escaped = False
        while end < len(text):
            char = text[end]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        found.append((start, end, text[start:end]))
        index = end
    return found


def fmt(value: float) -> str:
    value = 0.0 if abs(value) < 0.0005 else value
    return f"{value:.6f}".rstrip("0").rstrip(".")


def close(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= TOL


def ref_of(block: str) -> str | None:
    match = re.search(r'\(property "Reference" "([^"]+)"', block)
    return match.group(1) if match else None


def pad_y(block: str, pad: str) -> float | None:
    match = re.search(
        rf'\(pad "{re.escape(pad)}"[\s\S]*?\(at\s+[-0-9.]+\s+([-0-9.]+)(?:\s+[-0-9.]+)?\)',
        block,
    )
    return float(match.group(1)) if match else None


def mirror_coord(match: re.Match[str]) -> str:
    return f"({match.group(1)} {match.group(2)} {fmt(-float(match.group(3)))}"


def mirror_at(match: re.Match[str]) -> str:
    x = match.group(1)
    y = fmt(-float(match.group(2)))
    rotation = match.group(3)
    if rotation is None:
        return f"(at {x} {y})"
    return f"(at {x} {y} {fmt((-float(rotation)) % 360.0)})"


def mirror_primitive_y(block: str) -> str:
    block = re.sub(r"\((start|end|mid|center|xy)\s+([-0-9.]+)\s+([-0-9.]+)", mirror_coord, block)
    return re.sub(r"\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+([-0-9.]+))?\)", mirror_at, block)


def mirror_footprint_primitives(block: str) -> str:
    replacements: list[tuple[int, int, str]] = []
    for prefix in ("(fp_line", "(fp_rect", "(fp_circle", "(fp_arc", "(fp_poly", "(fp_text", "(pad "):
        for start, end, primitive in blocks(block, prefix):
            replacements.append((start, end, mirror_primitive_y(primitive)))
    for start, end, replacement in sorted(replacements, reverse=True):
        block = block[:start] + replacement + block[end:]
    return block


def repair_footprints(text: str) -> str:
    mirrored_refs = {opa.ref for opa in OPAS} | {pot.ref for pot in POTS}
    replacements: list[tuple[int, int, str]] = []
    for start, end, block in blocks(text, "(footprint "):
        ref = ref_of(block)
        if ref not in mirrored_refs:
            continue
        y = pad_y(block, "1")
        # Bad U1-U4/RV5-RV8 all have pad 1 at positive local Y.  Good stock
        # SOIC-8/3224W footprints put pad 1 at negative local Y.
        if y is not None and y > 0:
            replacements.append((start, end, mirror_footprint_primitives(block)))
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def segment_points(block: str) -> tuple[tuple[float, float], tuple[float, float]] | None:
    start = re.search(r"\(start\s+([-0-9.]+)\s+([-0-9.]+)\)", block)
    end = re.search(r"\(end\s+([-0-9.]+)\s+([-0-9.]+)\)", block)
    if not start or not end:
        return None
    return (float(start.group(1)), float(start.group(2))), (float(end.group(1)), float(end.group(2)))


def net_of(block: str) -> str | None:
    match = re.search(r'\(net\s+"([^"]+)"\)', block)
    return match.group(1) if match else None


def replace_point(block: str, old: tuple[float, float], new: tuple[float, float]) -> str:
    points = segment_points(block)
    if points is None:
        return block
    start, end = points
    if close(start, old):
        return re.sub(r"\(start\s+[-0-9.]+\s+[-0-9.]+\)", f"(start {fmt(new[0])} {fmt(new[1])})", block, count=1)
    if close(end, old):
        return re.sub(r"\(end\s+[-0-9.]+\s+[-0-9.]+\)", f"(end {fmt(new[0])} {fmt(new[1])})", block, count=1)
    return block


def opa_points(opa: Opa) -> dict[str, tuple[float, float]]:
    cx, cy = opa.center
    repaired_gnd_via = (cx - 0.2, cy - 1.905) if opa.ref == "U4" else (cx + 0.9, cy - 1.905)
    return {
        "old_pd": (cx + 2.475, cy - 0.635),
        "new_pd": (cx + 2.475, cy + 0.635),
        "old_vbias": (cx + 2.475, cy + 0.635),
        "new_vbias": (cx + 2.475, cy - 0.635),
        "old_gnd": (cx + 2.475, cy + 1.905),
        "new_gnd": (cx + 2.475, cy - 1.905),
        "old_out": (cx - 2.475, cy + 0.635),
        "new_out": (cx - 2.475, cy - 0.635),
        "old_5v": (cx - 2.475, cy - 0.635),
        "new_5v": (cx - 2.475, cy + 0.635),
        "old_5v_via": (cx - 1.2, cy - 0.635),
        "new_5v_via": (cx - 1.2, cy + 0.635),
        "old_gnd_via": (cx + 2.475, cy + 3.905),
        "bad_gnd_via": (cx + 4.05, cy - 1.905),
        "mid_gnd_via": (cx + 0.9, cy - 1.905),
        "new_gnd_via": repaired_gnd_via,
    }


def pot_points(pot: Pot) -> dict[str, tuple[float, float]]:
    cx, cy = pot.center
    return {
        "old_1": (cx + 1.25, cy + 1.45),
        "new_1": (cx + 1.25, cy - 1.45),
        "old_2": (cx, cy - 1.45),
        "new_2": (cx, cy + 1.45),
        "old_3": (cx - 1.25, cy + 1.45),
        "new_3": (cx - 1.25, cy - 1.45),
    }


def rewrite_segments(text: str) -> str:
    replacements: list[tuple[int, int, str]] = []
    removals: list[tuple[int, int]] = []
    for start, end, block in blocks(text, "\n\t(segment"):
        points = segment_points(block)
        net = net_of(block)
        if points is None or net is None:
            continue
        replacement = block
        remove = False
        for opa in OPAS:
            p = opa_points(opa)
            if net == "GND" and (close(points[0], p["old_gnd"]) or close(points[1], p["old_gnd"])):
                remove = True
                break
            if net == "GND":
                replacement = replace_point(replacement, p["bad_gnd_via"], p["new_gnd_via"])
                replacement = replace_point(replacement, p["mid_gnd_via"], p["new_gnd_via"])
            if net == "+5V":
                replacement = replace_point(replacement, p["old_5v_via"], p["new_5v_via"])
            moves = {
                f"/TIA_{opa.channel}/PD_ANODE": ("old_pd", "new_pd"),
                f"/TIA_{opa.channel}/VBIAS": ("old_vbias", "new_vbias"),
                opa.vout: ("old_out", "new_out"),
                "+5V": ("old_5v", "new_5v"),
            }
            if net in moves:
                old, new = moves[net]
                replacement = replace_point(replacement, p[old], p[new])
        if remove:
            removals.append((start, end))
            continue
        for pot in POTS:
            p = pot_points(pot)
            moves = {
                f"/TIA_{pot.channel}/PD_ANODE": ("old_1", "new_1"),
                pot.vout: (("old_2", "new_2"), ("old_3", "new_3")),
            }
            if net not in moves:
                continue
            move = moves[net]
            if isinstance(move[0], tuple):
                for old, new in move:  # type: ignore[assignment]
                    replacement = replace_point(replacement, p[old], p[new])
            else:
                old, new = move  # type: ignore[misc]
                replacement = replace_point(replacement, p[old], p[new])
        if replacement != block:
            replacements.append((start, end, replacement))

    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    for start, end in sorted(removals, reverse=True):
        text = text[:start] + text[end:]
    return text


def via_point(block: str) -> tuple[float, float] | None:
    match = re.search(r"\(at\s+([-0-9.]+)\s+([-0-9.]+)\)", block)
    return (float(match.group(1)), float(match.group(2))) if match else None


def remove_old_opa_gnd_vias(text: str) -> str:
    old = [opa_points(opa)["old_gnd_via"] for opa in OPAS]
    removals: list[tuple[int, int]] = []
    for start, end, block in blocks(text, "\n\t(via"):
        point = via_point(block)
        if point is not None and net_of(block) == "GND" and any(close(point, target) for target in old):
            removals.append((start, end))
    for start, end in sorted(removals, reverse=True):
        text = text[:start] + text[end:]
    return text


def move_existing_vias(text: str) -> str:
    replacements: list[tuple[int, int, str]] = []
    for start, end, block in blocks(text, "\n\t(via"):
        point = via_point(block)
        net = net_of(block)
        if point is None or net is None:
            continue
        replacement = block
        for opa in OPAS:
            p = opa_points(opa)
            if net == "+5V" and close(point, p["old_5v_via"]):
                replacement = re.sub(
                    r"\(at\s+[-0-9.]+\s+[-0-9.]+\)",
                    f"(at {fmt(p['new_5v_via'][0])} {fmt(p['new_5v_via'][1])})",
                    replacement,
                    count=1,
                )
            if net == "GND" and close(point, p["bad_gnd_via"]):
                replacement = re.sub(
                    r"\(at\s+[-0-9.]+\s+[-0-9.]+\)",
                    f"(at {fmt(p['new_gnd_via'][0])} {fmt(p['new_gnd_via'][1])})",
                    replacement,
                    count=1,
                )
            if net == "GND" and close(point, p["mid_gnd_via"]):
                replacement = re.sub(
                    r"\(at\s+[-0-9.]+\s+[-0-9.]+\)",
                    f"(at {fmt(p['new_gnd_via'][0])} {fmt(p['new_gnd_via'][1])})",
                    replacement,
                    count=1,
                )
        if replacement != block:
            replacements.append((start, end, replacement))
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def segment_block(net: str, start: tuple[float, float], end: tuple[float, float], width: float = 0.2) -> str:
    return (
        "\t(segment\n"
        f"\t\t(start {fmt(start[0])} {fmt(start[1])})\n"
        f"\t\t(end {fmt(end[0])} {fmt(end[1])})\n"
        f"\t\t(width {fmt(width)})\n"
        "\t\t(layer \"F.Cu\")\n"
        f"\t\t(net \"{net}\")\n"
        f"\t\t(uuid \"{uuid.uuid4()}\")\n"
        "\t)"
    )


def repair_u4_vbias_escape(text: str) -> str:
    bad_segments = (
        ((133.275, 118.45), (134.45, 119.72)),
        ((134.45, 119.72), (134.45, 132.59)),
    )
    removals: list[tuple[int, int]] = []
    for start, end, block in blocks(text, "\n\t(segment"):
        if net_of(block) != "/TIA_BLUE/VBIAS":
            continue
        points = segment_points(block)
        if points is None:
            continue
        if any(
            (close(points[0], a) and close(points[1], b)) or (close(points[0], b) and close(points[1], a))
            for a, b in bad_segments
        ):
            removals.append((start, end))
    for start, end in sorted(removals, reverse=True):
        text = text[:start] + text[end:]
    if "(start 133.275 118.45)\n\t\t(end 131.7 118.45)" in text:
        return text
    new_segments = "\n".join(
        [
            segment_block("/TIA_BLUE/VBIAS", (133.275, 118.45), (131.7, 118.45)),
            segment_block("/TIA_BLUE/VBIAS", (131.7, 118.45), (131.7, 122.0)),
            segment_block("/TIA_BLUE/VBIAS", (131.7, 122.0), (134.45, 122.0)),
            segment_block("/TIA_BLUE/VBIAS", (134.45, 122.0), (134.45, 132.59)),
        ]
    )
    insert_at = text.find("\n\t(zone")
    if insert_at < 0:
        raise RuntimeError("could not find insertion point for U4 VBIAS repair")
    return text[:insert_at] + "\n" + new_segments + "\n" + text[insert_at:]


def new_opa_gnd_blocks(text: str) -> str:
    result: list[str] = []
    for opa in OPAS:
        p = opa_points(opa)
        via = p["new_gnd_via"]
        if f"(at {fmt(via[0])} {fmt(via[1])})" in text:
            continue
        pad = p["new_gnd"]
        result.append(
            "\t(segment\n"
            f"\t\t(start {fmt(pad[0])} {fmt(pad[1])})\n"
            f"\t\t(end {fmt(via[0])} {fmt(via[1])})\n"
            "\t\t(width 0.22)\n"
            "\t\t(layer \"F.Cu\")\n"
            "\t\t(net \"GND\")\n"
            f"\t\t(uuid \"{uuid.uuid4()}\")\n"
            "\t)"
        )
        result.append(
            "\t(via\n"
            f"\t\t(at {fmt(via[0])} {fmt(via[1])})\n"
            "\t\t(size 0.6)\n"
            "\t\t(drill 0.3)\n"
            "\t\t(layers \"F.Cu\" \"B.Cu\")\n"
            "\t\t(capping no)\n"
            "\t\t(covering\n"
            "\t\t\t(front no)\n"
            "\t\t\t(back no)\n"
            "\t\t)\n"
            "\t\t(plugging\n"
            "\t\t\t(front no)\n"
            "\t\t\t(back no)\n"
            "\t\t)\n"
            "\t\t(filling no)\n"
            "\t\t(net \"GND\")\n"
            f"\t\t(uuid \"{uuid.uuid4()}\")\n"
            "\t)"
        )
    return "\n".join(result)


def add_new_opa_gnd(text: str) -> str:
    addition = new_opa_gnd_blocks(text)
    if not addition:
        return text
    insert_at = text.find("\n\t(zone")
    if insert_at < 0:
        insert_at = text.find("\n\t(gr_line")
    if insert_at < 0:
        raise RuntimeError("could not find insertion point for new OPA380 GND escapes")
    return text[:insert_at] + "\n" + addition + "\n" + text[insert_at:]


def main() -> int:
    text = BOARD.read_text()
    repaired = repair_footprints(text)
    repaired = rewrite_segments(repaired)
    repaired = remove_old_opa_gnd_vias(repaired)
    repaired = move_existing_vias(repaired)
    repaired = repair_u4_vbias_escape(repaired)
    repaired = add_new_opa_gnd(repaired)
    if repaired == text:
        print("No mirrored U1-U4/RV5-RV8 repairs were needed.")
        return 0
    BOARD.write_text(repaired)
    print("Repaired mirrored U1-U4 OPA380 and RV5-RV8 Bourns 3224W footprint geometry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
