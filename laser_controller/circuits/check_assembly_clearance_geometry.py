#!/usr/bin/env python3
"""Check package geometry that native DRC can miss when footprints lie.

KiCad DRC can only be as good as each footprint's courtyard/body geometry. This
gate adds a gross pad-vs-courtyard check and a strict local assembly-clearance
check for the JLCPCB C192300 2x4 SMT header used at J7.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
GROSS_PAD_COURTYARD_TOLERANCE_MM = 0.35
STRICT_PAD_COURTYARD_TOLERANCE_MM = 0.05
J7_NEIGHBOR_MIN_COURTYARD_CLEARANCE_MM = 0.25
J7_NEIGHBOR_MIN_PAD_CLEARANCE_MM = 1.00
STRICT_REFS = {"J7"}
J7_NEIGHBORS = {"L2", "RV4"}


@dataclass(frozen=True)
class BBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    def outside_amount(self, other: "BBox") -> float:
        return max(
            other.x1 - self.x1,
            other.y1 - self.y1,
            self.x2 - other.x2,
            self.y2 - other.y2,
            0.0,
        )

    def distance_to(self, other: "BBox") -> float:
        dx = max(other.x1 - self.x2, self.x1 - other.x2, 0.0)
        dy = max(other.y1 - self.y2, self.y1 - other.y2, 0.0)
        return math.hypot(dx, dy)

    @staticmethod
    def union(boxes: list["BBox"]) -> "BBox | None":
        if not boxes:
            return None
        return BBox(
            min(box.x1 for box in boxes),
            min(box.y1 for box in boxes),
            max(box.x2 for box in boxes),
            max(box.y2 for box in boxes),
        )


def ensure_pcbnew():
    try:
        import pcbnew  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pcbnew Python module not available. Run with system Python, e.g. "
            "`/usr/bin/python3 circuits/check_assembly_clearance_geometry.py`."
        ) from exc
    return pcbnew


def bbox_mm(item) -> BBox:
    box = item.GetBoundingBox()
    return BBox(
        box.GetX() / 1_000_000,
        box.GetY() / 1_000_000,
        (box.GetX() + box.GetWidth()) / 1_000_000,
        (box.GetY() + box.GetHeight()) / 1_000_000,
    )


def shape_layer_bbox(fp, layer_id) -> BBox | None:
    boxes: list[BBox] = []
    for item in fp.GraphicalItems():
        if item.GetLayer() != layer_id:
            continue
        if item.GetClass() != "PCB_SHAPE":
            continue
        boxes.append(bbox_mm(item))
    return BBox.union(boxes)


def smd_pad_boxes(fp, pcbnew) -> list[BBox]:
    return [bbox_mm(pad) for pad in fp.Pads() if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]


def footprint_side_layers(fp, pcbnew) -> tuple[int, int] | None:
    layer = fp.GetLayer()
    if layer == pcbnew.F_Cu:
        return pcbnew.F_CrtYd, pcbnew.F_Fab
    if layer == pcbnew.B_Cu:
        return pcbnew.B_CrtYd, pcbnew.B_Fab
    return None


def check_pad_courtyards(board, pcbnew) -> list[str]:
    failures: list[str] = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        layers = footprint_side_layers(fp, pcbnew)
        if layers is None:
            continue
        courtyard_layer, _ = layers
        courtyard = shape_layer_bbox(fp, courtyard_layer)
        if courtyard is None:
            continue
        tolerance = (
            STRICT_PAD_COURTYARD_TOLERANCE_MM
            if ref in STRICT_REFS
            else GROSS_PAD_COURTYARD_TOLERANCE_MM
        )
        for index, pad_box in enumerate(smd_pad_boxes(fp, pcbnew), start=1):
            outside = pad_box.outside_amount(courtyard)
            if outside > tolerance:
                failures.append(
                    f"{ref} SMD pad {index} protrudes {outside:.3f} mm outside "
                    f"its courtyard; tolerance is {tolerance:.3f} mm"
                )
    return failures


def check_j7_clearance(board, pcbnew) -> list[str]:
    failures: list[str] = []
    j7 = board.FindFootprintByReference("J7")
    if j7 is None:
        return ["J7 footprint missing"]
    j7_footprint = str(j7.GetFPID().GetLibItemName())
    if "PinHeader_2x04_P2.54mm_SMD_Vertical_C192300" not in j7_footprint:
        failures.append(f"J7 footprint is {j7_footprint}, expected C192300 2x4 SMT header")

    j7_layers = footprint_side_layers(j7, pcbnew)
    if j7_layers is None:
        return failures + ["J7 is not on a copper assembly side"]
    j7_courtyard_layer, j7_fab_layer = j7_layers
    j7_courtyard = shape_layer_bbox(j7, j7_courtyard_layer)
    j7_fab = shape_layer_bbox(j7, j7_fab_layer)
    j7_pads = BBox.union(smd_pad_boxes(j7, pcbnew))
    if j7_courtyard is None:
        failures.append("J7 has no shape geometry on F.CrtYd")
    if j7_fab is None or j7_fab.width < 4.0 or j7_fab.height < 4.0:
        failures.append("J7 has no realistic F.Fab body outline; text-only F.Fab cannot prove assembly clearance")
    if j7_pads is None:
        failures.append("J7 has no SMD pad geometry")
    if j7_courtyard is None or j7_pads is None:
        return failures

    for ref in sorted(J7_NEIGHBORS):
        neighbor = board.FindFootprintByReference(ref)
        if neighbor is None:
            failures.append(f"{ref} footprint missing for J7 clearance check")
            continue
        neighbor_layers = footprint_side_layers(neighbor, pcbnew)
        if neighbor_layers is None:
            continue
        neighbor_courtyard_layer, _ = neighbor_layers
        neighbor_courtyard = shape_layer_bbox(neighbor, neighbor_courtyard_layer)
        neighbor_pads = BBox.union(smd_pad_boxes(neighbor, pcbnew))
        if neighbor_courtyard is not None:
            courtyard_gap = j7_courtyard.distance_to(neighbor_courtyard)
            if courtyard_gap < J7_NEIGHBOR_MIN_COURTYARD_CLEARANCE_MM:
                failures.append(
                    f"J7 courtyard clearance to {ref} is {courtyard_gap:.3f} mm; "
                    f"minimum is {J7_NEIGHBOR_MIN_COURTYARD_CLEARANCE_MM:.3f} mm"
                )
        if neighbor_pads is not None:
            pad_gap = j7_pads.distance_to(neighbor_pads)
            if pad_gap < J7_NEIGHBOR_MIN_PAD_CLEARANCE_MM:
                failures.append(
                    f"J7 pad clearance to {ref} pads is {pad_gap:.3f} mm; "
                    f"minimum is {J7_NEIGHBOR_MIN_PAD_CLEARANCE_MM:.3f} mm"
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()
    if not args.board.exists():
        print(f"FAIL assembly-clearance geometry: board file not found: {args.board}")
        return 1

    pcbnew = ensure_pcbnew()
    board = pcbnew.LoadBoard(str(args.board))
    failures = check_pad_courtyards(board, pcbnew)
    failures.extend(check_j7_clearance(board, pcbnew))
    if failures:
        print(f"FAIL assembly-clearance geometry: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS assembly-clearance geometry: gross SMD pad/courtyard geometry is valid, "
        "J7 has a real F.Fab body outline, and J7 clears L2/RV4 assembly envelopes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
