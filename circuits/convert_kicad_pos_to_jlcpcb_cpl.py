#!/usr/bin/env python3
"""Convert KiCad CSV position export to JLCPCB CPL format.

KiCad exports `Ref,Val,Package,PosX,PosY,Rot,Side`. JLCPCB's current CPL parser
expects the stricter `Designator,Mid X,Mid Y,Layer,Rotation` form shown in its
sample file.

KiCad's POS export reports the footprint anchor. That is the package midpoint
for normal passives and ICs, but not for some connector footprints whose origin
is pad 1 or a mechanical feature. JLCPCB's column is explicitly `Mid X/Mid Y`,
so when the source PCB is available this converter moves the exported coordinate
to the footprint courtyard/fab midpoint before formatting the CPL row.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


KICAD_COLUMNS = ("Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side")
JLCPCB_COLUMNS = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")
COORD_RE = r"([-+]?\d+(?:\.\d+)?)"

# JLCPCB's CPL file is named "Mid X/Mid Y", but the web PCBA preview places
# stocked connectors against the origin of JLC's own library footprint. For
# connector packages where the KiCad footprint origin/centroid differs from the
# JLC library origin, align a small set of known pads and emit that JLC origin.
JLCPCB_LOCAL_PADS: dict[str, dict[str, tuple[float, float]]] = {
    # C91144 is JLCPCB's stocked U-M-M5SS-W-2 Mini-B SMT assembly part. The
    # signal pins align with KiCad's Wuerth Mini-B land pattern at 270 degrees;
    # the shield pads are slightly narrower, so the solved origin splits the
    # harmless ~0.19 mm shell-pad mismatch across the oversized KiCad pads.
    "C91144": {
        "1": (-1.61, -2.92),
        "2": (-0.81, -2.92),
        "3": (-0.01, -2.92),
        "4": (0.79, -2.92),
        "5": (1.59, -2.92),
        "SH_UL": (-4.45, 2.92),
        "SH_UR": (-4.45, -2.58),
        "SH_LL": (4.45, 2.92),
        "SH_LR": (4.45, -2.58),
    },
    "C194407": {
        "1": (3.10, -2.35),
        "2": (-3.10, -2.35),
        "3": (0.10, 2.35),
    },
    "C386757": {
        "1": (3.57, 3.30),
        "2": (2.55, 1.51),
        "3": (1.53, 3.30),
        "4": (0.51, 1.51),
        "5": (-0.51, 3.30),
        "6": (-1.53, 1.51),
        "7": (-2.55, 3.30),
        "8": (-3.57, 1.51),
        "13": (8.13, 2.27),
        "14": (-8.13, 2.27),
    },
}

PadSelector = tuple[str, int] | str

JLCPCB_ORIGIN_ALIGNMENT: dict[
    str, tuple[str, tuple[tuple[PadSelector, str], ...], tuple[int, ...], float]
] = {
    "J1": (
        "C91144",
        (
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            (("6", 0), "SH_UR"),
            (("6", 1), "SH_UL"),
            (("6", 2), "SH_LR"),
            (("6", 3), "SH_LL"),
        ),
        (270,),
        0.20,
    ),
    "J2": (
        "C91144",
        (
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            (("6", 0), "SH_UR"),
            (("6", 1), "SH_UL"),
            (("6", 2), "SH_LR"),
            (("6", 3), "SH_LL"),
        ),
        (270,),
        0.20,
    ),
}

JLCPCB_ROTATION_OVERRIDES = {
    # C127509's JLC footprint has the switch legs on the north/south sides.
    # The KiCad SPST footprint is electrically equivalent with duplicated
    # pads, but JLC's model/package orientation needs a 90-degree CPL rotation.
    "SW1": 90,
    "SW2": 90,
    "SW3": 90,
}

JLCPCB_KICAD_ANCHOR_REFS = {
    # JLCPCB's THT connector preview follows the KiCad/access-controller anchor
    # convention for these large parts. Do not recenter them to courtyard or to
    # the EasyEDA library origin; that shifts the visible RJ45/barrel bodies.
    "J5",
    "J6",
}


def mm(value: float) -> str:
    return f"{value:.4f}mm"


def rotation(value: str) -> str:
    degrees = float(value) % 360.0
    if abs(degrees - round(degrees)) < 0.0001:
        return str(int(round(degrees)) % 360)
    return f"{degrees:.4f}".rstrip("0").rstrip(".")


def layer(value: str) -> str:
    lowered = value.strip().lower()
    if lowered == "top":
        return "Top"
    if lowered == "bottom":
        return "Bottom"
    raise ValueError(f"unsupported KiCad side {value!r}")


def balanced_blocks(text: str, prefix: str) -> list[str]:
    blocks: list[str] = []
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
        blocks.append(text[start:end])
        index = end
    return blocks


def bbox_center(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    if not points:
        return None
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0


def primitive_points(item: str) -> list[tuple[float, float]]:
    circle = re.search(
        rf"\(center\s+{COORD_RE}\s+{COORD_RE}\).*?\(end\s+{COORD_RE}\s+{COORD_RE}\)",
        item,
        re.S,
    )
    if item.startswith("(fp_circle") and circle:
        cx, cy, ex, ey = (float(value) for value in circle.groups())
        radius = math.hypot(ex - cx, ey - cy)
        return [
            (cx - radius, cy - radius),
            (cx + radius, cy + radius),
        ]

    return [
        (float(x), float(y))
        for x, y in re.findall(rf"\((?:start|end|mid|center|xy)\s+{COORD_RE}\s+{COORD_RE}\)", item)
    ]


def footprint_layer_points(block: str, layers: tuple[str, ...]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for prefix in ("(fp_line", "(fp_rect", "(fp_circle", "(fp_arc", "(fp_poly"):
        for item in balanced_blocks(block, prefix):
            layer_match = re.search(r'\(layer "([^"]+)"\)', item)
            if not layer_match or layer_match.group(1) not in layers:
                continue
            points.extend(primitive_points(item))
    return points


def rotate_point(x: float, y: float, degrees: float) -> tuple[float, float]:
    # KiCad PCB coordinates are Y-down, so positive footprint rotation is
    # clockwise in the file coordinate frame rather than Cartesian CCW.
    radians = math.radians(degrees)
    return (
        x * math.cos(radians) + y * math.sin(radians),
        -x * math.sin(radians) + y * math.cos(radians),
    )


def pad_bbox_points(block: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for pad in balanced_blocks(block, "(pad "):
        at = re.search(rf"\(at\s+{COORD_RE}\s+{COORD_RE}(?:\s+{COORD_RE})?", pad)
        size = re.search(rf"\(size\s+{COORD_RE}\s+{COORD_RE}\)", pad)
        if not at or not size:
            continue
        x, y = float(at.group(1)), float(at.group(2))
        pad_rot = float(at.group(3) or 0.0)
        width, height = float(size.group(1)), float(size.group(2))
        for dx in (-width / 2.0, width / 2.0):
            for dy in (-height / 2.0, height / 2.0):
                rx, ry = rotate_point(dx, dy, pad_rot)
                points.append((x + rx, y + ry))
    return points


def footprint_local_center(block: str, side: str) -> tuple[float, float]:
    prefix = "F" if side == "top" else "B"
    layer_priorities = (
        (f"{prefix}.CrtYd",),
        ("F.CrtYd", "B.CrtYd"),
        (f"{prefix}.Fab",),
        ("F.Fab", "B.Fab"),
    )
    for layers in layer_priorities:
        center = bbox_center(footprint_layer_points(block, layers))
        if center is not None:
            return center

    center = bbox_center(pad_bbox_points(block))
    if center is not None:
        return center

    return 0.0, 0.0


def footprint_midpoint_offsets(pcb_path: Path) -> dict[str, tuple[float, float]]:
    offsets: dict[str, tuple[float, float]] = {}
    text = pcb_path.read_text()
    for block in balanced_blocks(text, "(footprint "):
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
        layer_match = re.search(r'\(layer "([FB])\.Cu"\)', block)
        if not ref_match or not layer_match:
            continue
        side = "top" if layer_match.group(1) == "F" else "bottom"
        offsets[ref_match.group(1)] = footprint_local_center(block, side)
    return offsets


def footprint_pad_centers(pcb_path: Path) -> dict[str, list[tuple[str, float, float]]]:
    centers: dict[str, list[tuple[str, float, float]]] = {}
    text = pcb_path.read_text()
    for block in balanced_blocks(text, "(footprint "):
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
        at_match = re.search(rf"\(at\s+{COORD_RE}\s+{COORD_RE}(?:\s+{COORD_RE})?", block)
        if not ref_match or not at_match:
            continue
        at_x, at_y = float(at_match.group(1)), float(at_match.group(2))
        fp_rot = float(at_match.group(3) or 0.0)
        pads: list[tuple[str, float, float]] = []
        for pad in balanced_blocks(block, "(pad "):
            number_match = re.match(r'\(pad\s+"?([^"\s\)]+)"?', pad)
            at = re.search(rf"\(at\s+{COORD_RE}\s+{COORD_RE}(?:\s+{COORD_RE})?", pad)
            if not number_match or not at:
                continue
            local_x, local_y = float(at.group(1)), float(at.group(2))
            dx, dy = rotate_point(local_x, local_y, fp_rot)
            pads.append((number_match.group(1), at_x + dx, at_y + dy))
        centers[ref_match.group(1)] = pads
    return centers


def select_pad(
    pads: list[tuple[str, float, float]],
    selector: PadSelector,
) -> tuple[float, float]:
    if isinstance(selector, tuple):
        number, index = selector
        matches = [(x, y) for pad_number, x, y in pads if pad_number == number]
        if index >= len(matches):
            raise ValueError(f"missing duplicate pad {number}[{index}]")
        return matches[index]
    for pad_number, x, y in pads:
        if pad_number == selector:
            return x, y
    raise ValueError(f"missing pad {selector}")


def solve_jlcpcb_origin(
    board_pads: list[tuple[str, float, float]],
    lcsc: str,
    pad_pairs: tuple[tuple[PadSelector, str], ...],
    rotations: tuple[int, ...],
    max_error_mm: float,
) -> tuple[float, float, int]:
    local_pads = JLCPCB_LOCAL_PADS[lcsc]
    best: tuple[float, float, int, float, float] | None = None
    for rot in rotations:
        deltas: list[tuple[float, float]] = []
        for board_selector, jlc_pad in pad_pairs:
            board_x, board_y = select_pad(board_pads, board_selector)
            local_x, local_y = rotate_point(*local_pads[jlc_pad], rot)
            deltas.append((board_x - local_x, board_y - local_y))
        origin_x = sum(x for x, _ in deltas) / len(deltas)
        origin_y = sum(y for _, y in deltas) / len(deltas)
        errors: list[float] = []
        for board_selector, jlc_pad in pad_pairs:
            board_x, board_y = select_pad(board_pads, board_selector)
            local_x, local_y = rotate_point(*local_pads[jlc_pad], rot)
            errors.append(math.hypot(origin_x + local_x - board_x, origin_y + local_y - board_y))
        rms = math.sqrt(sum(error * error for error in errors) / len(errors))
        worst = max(errors)
        candidate = (origin_x, origin_y, rot, rms, worst)
        if best is None or (rms, worst) < (best[3], best[4]):
            best = candidate
    if best is None:
        raise ValueError("no candidate rotations")
    if best[4] > max_error_mm:
        raise ValueError(
            f"JLC footprint alignment worst pad error is {best[4]:.3f} mm, "
            f"above {max_error_mm:.3f} mm"
        )
    return best[0], -best[1], best[2]


def jlcpcb_origin_overrides(pcb_path: Path) -> dict[str, tuple[float, float, int]]:
    board_pads_by_ref = footprint_pad_centers(pcb_path)
    overrides: dict[str, tuple[float, float, int]] = {}
    for ref, (lcsc, pad_pairs, rotations, max_error_mm) in JLCPCB_ORIGIN_ALIGNMENT.items():
        if ref not in board_pads_by_ref:
            continue
        overrides[ref] = solve_jlcpcb_origin(
            board_pads_by_ref[ref],
            lcsc,
            pad_pairs,
            rotations,
            max_error_mm,
        )
    return overrides


def footprint_cpl_midpoints(pcb_path: Path) -> dict[str, tuple[float, float]]:
    midpoints: dict[str, tuple[float, float]] = {}
    text = pcb_path.read_text()
    for block in balanced_blocks(text, "(footprint "):
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
        layer_match = re.search(r'\(layer "([FB])\.Cu"\)', block)
        at_match = re.search(rf"\(at\s+{COORD_RE}\s+{COORD_RE}(?:\s+{COORD_RE})?", block)
        if not ref_match or not layer_match or not at_match:
            continue
        side = "top" if layer_match.group(1) == "F" else "bottom"
        offset_x, offset_y = footprint_local_center(block, side)
        rot = float(at_match.group(3) or 0.0)
        dx, dy = rotate_point(offset_x, offset_y, rot)
        at_x, at_y = float(at_match.group(1)), float(at_match.group(2))
        midpoints[ref_match.group(1)] = at_x + dx, -(at_y + dy)
    return midpoints


def convert_rows(
    rows: list[dict[str, str]],
    midpoint_offsets: dict[str, tuple[float, float]] | None = None,
    origin_overrides: dict[str, tuple[float, float, int]] | None = None,
) -> list[dict[str, str]]:
    converted: list[dict[str, str]] = []
    for row in rows:
        cpl_rotation: str | int = row["Rot"]
        if origin_overrides and row["Ref"] in origin_overrides:
            pos_x, pos_y, cpl_rotation = origin_overrides[row["Ref"]]
        else:
            pos_x = float(row["PosX"])
            pos_y = float(row["PosY"])
            if (
                row["Ref"] not in JLCPCB_KICAD_ANCHOR_REFS
                and midpoint_offsets
                and row["Ref"] in midpoint_offsets
            ):
                dx, dy = rotate_point(*midpoint_offsets[row["Ref"]], float(row["Rot"]))
                pos_x += dx
                pos_y -= dy
            if row["Ref"] in JLCPCB_ROTATION_OVERRIDES:
                cpl_rotation = JLCPCB_ROTATION_OVERRIDES[row["Ref"]]
        converted.append(
            {
                "Designator": row["Ref"],
                "Mid X": mm(pos_x),
                "Mid Y": mm(pos_y),
                "Layer": layer(row["Side"]),
                "Rotation": rotation(str(cpl_rotation)),
            }
        )
    return converted


def bom_refs(path: Path) -> set[str]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if "Designator" not in (reader.fieldnames or ()):
            raise SystemExit(f"{path}: expected a Designator column")
        refs: set[str] = set()
        for row in reader:
            refs.update(ref.strip() for ref in row["Designator"].split(",") if ref.strip())
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bom",
        type=Path,
        help="Optional JLCPCB BOM CSV; when set, only placement rows whose Ref is in the BOM are emitted.",
    )
    parser.add_argument(
        "--pcb",
        type=Path,
        help="Optional KiCad PCB source; when set, JLCPCB Mid X/Mid Y are corrected to the footprint midpoint.",
    )
    parser.add_argument("input", type=Path, help="KiCad CSV position file")
    parser.add_argument("output", type=Path, help="JLCPCB CPL CSV output")
    args = parser.parse_args()

    with args.input.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != KICAD_COLUMNS:
            raise SystemExit(
                f"expected KiCad POS columns {KICAD_COLUMNS}, found {tuple(reader.fieldnames or ())}"
            )
        rows = list(reader)

    if args.bom is not None:
        allowed_refs = bom_refs(args.bom)
        input_refs = {row["Ref"] for row in rows}
        missing = sorted(allowed_refs - input_refs)
        if missing:
            raise SystemExit(
                "BOM designators missing from KiCad position export: " + ", ".join(missing)
            )
        rows = [row for row in rows if row["Ref"] in allowed_refs]

    midpoint_offsets = footprint_midpoint_offsets(args.pcb) if args.pcb is not None else None
    origin_overrides = jlcpcb_origin_overrides(args.pcb) if args.pcb is not None else None
    converted = convert_rows(rows, midpoint_offsets, origin_overrides)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=JLCPCB_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(converted)

    print(f"Wrote JLCPCB CPL with {len(converted)} placements to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
