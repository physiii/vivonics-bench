#!/usr/bin/env python3
"""Classify native Pcbnew courtyard-overlap warnings.

The headless Pcbnew DRC report gives exact courtyard-overlap pairs, but a
warning can mean anything from conservative courtyard padding to likely physical
component-body interference. This checker reads the native report, compares the
same footprint pairs on F.Fab, and writes a triage artifact for layout review.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_DRC_REPORT = (
    Path(__file__).resolve().parent
    / "review"
    / "generated"
    / "laser_controller_pcbnew_drc_report.rpt"
)
DEFAULT_TRIAGE_REPORT = (
    Path(__file__).resolve().parent
    / "review"
    / "generated"
    / "laser_controller_courtyard_overlap_triage.md"
)


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

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class Overlap:
    ref_a: str
    ref_b: str
    fab_overlap: BBox
    courtyard_overlap: BBox


def ensure_pcbnew():
    try:
        import pcbnew  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pcbnew Python module not available. Run with system Python, e.g. "
            "`/usr/bin/python3 circuits/check_courtyard_overlap_triage.py`."
        ) from exc
    return pcbnew


def overlap(a: BBox, b: BBox) -> BBox:
    return BBox(max(a.x1, b.x1), max(a.y1, b.y1), min(a.x2, b.x2), min(a.y2, b.y2))


def fmt_box(box: BBox) -> str:
    return f"{box.width:.3f} mm x {box.height:.3f} mm, area {box.area:.3f} mm^2"


def parse_courtyard_pairs(report_text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    lines = report_text.splitlines()
    index = 0
    while index < len(lines):
        if not lines[index].startswith("[courtyards_overlap]"):
            index += 1
            continue
        refs: list[str] = []
        index += 1
        while index < len(lines) and not lines[index].startswith("["):
            match = re.search(r"Footprint\s+([A-Za-z]+\d+)", lines[index])
            if match:
                refs.append(match.group(1))
            index += 1
        if len(refs) == 2:
            pairs.append((refs[0], refs[1]))
    return pairs


def footprint_bbox(fp, layer_id) -> BBox | None:
    xs: list[float] = []
    ys: list[float] = []
    for item in fp.GraphicalItems():
        if item.GetLayer() != layer_id:
            continue
        bbox = item.GetBoundingBox()
        xs.extend([bbox.GetX() / 1_000_000, (bbox.GetX() + bbox.GetWidth()) / 1_000_000])
        ys.extend([bbox.GetY() / 1_000_000, (bbox.GetY() + bbox.GetHeight()) / 1_000_000])
    if not xs:
        return None
    return BBox(min(xs), min(ys), max(xs), max(ys))


def classify(board, pcbnew, pairs: list[tuple[str, str]]) -> tuple[list[Overlap], list[Overlap], list[str]]:
    body_overlaps: list[Overlap] = []
    courtyard_only: list[Overlap] = []
    failures: list[str] = []
    for ref_a, ref_b in pairs:
        fp_a = board.FindFootprintByReference(ref_a)
        fp_b = board.FindFootprintByReference(ref_b)
        if fp_a is None or fp_b is None:
            failures.append(f"missing footprint for courtyard pair {ref_a}/{ref_b}")
            continue
        fab_a = footprint_bbox(fp_a, pcbnew.F_Fab)
        fab_b = footprint_bbox(fp_b, pcbnew.F_Fab)
        crtyd_a = footprint_bbox(fp_a, pcbnew.F_CrtYd)
        crtyd_b = footprint_bbox(fp_b, pcbnew.F_CrtYd)
        if fab_a is None or fab_b is None or crtyd_a is None or crtyd_b is None:
            failures.append(f"missing F.Fab or F.CrtYd geometry for {ref_a}/{ref_b}")
            continue
        item = Overlap(ref_a, ref_b, overlap(fab_a, fab_b), overlap(crtyd_a, crtyd_b))
        if item.fab_overlap.area > 0:
            body_overlaps.append(item)
        else:
            courtyard_only.append(item)
    return body_overlaps, courtyard_only, failures


def write_report(
    path: Path,
    pairs: list[tuple[str, str]],
    body_overlaps: list[Overlap],
    courtyard_only: list[Overlap],
    failures: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Courtyard Overlap Triage",
        "",
        "Generated from the native Pcbnew DRC report and current PCB F.Fab/F.CrtYd geometry.",
        "This is not a fabrication waiver.",
        "",
        f"Native courtyard-overlap pairs: {len(pairs)}",
        f"F.Fab/body-box overlaps: {len(body_overlaps)}",
        f"Courtyard-only overlaps: {len(courtyard_only)}",
        "",
    ]
    if body_overlaps:
        lines.extend(
            [
                "## F.Fab/Body-Box Overlaps",
                "",
                "These pairs have overlapping F.Fab bounding boxes and require layout review, package change, or reroute before fabrication.",
                "",
            ]
        )
        for item in body_overlaps:
            lines.append(f"- `{item.ref_a}` / `{item.ref_b}`: F.Fab overlap {fmt_box(item.fab_overlap)}; courtyard overlap {fmt_box(item.courtyard_overlap)}.")
        lines.append("")
    if courtyard_only:
        lines.extend(
            [
                "## Courtyard-Only Overlaps",
                "",
                "These pairs do not have overlapping F.Fab bounding boxes in the current footprint geometry, but still need assembly-clearance review or placement adjustment.",
                "",
            ]
        )
        for item in courtyard_only:
            lines.append(f"- `{item.ref_a}` / `{item.ref_b}`: courtyard overlap {fmt_box(item.courtyard_overlap)}.")
        lines.append("")
    if failures:
        lines.extend(["## Parse/Geometry Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
        lines.append("")
    lines.extend(
        [
            "## Required Action",
            "",
            "Resolve with a KiCad layout edit and reroute, or document an explicit assembly waiver after physical package review. Do not treat these native warnings as cleared JLCPCB fabrication evidence.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--drc-report", type=Path, default=DEFAULT_DRC_REPORT)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT)
    args = parser.parse_args()

    if not args.board.exists():
        print(f"FAIL courtyard triage: board file not found: {args.board}")
        return 1
    if not args.drc_report.exists():
        print(
            "FAIL courtyard triage: native Pcbnew DRC report missing; "
            "run `/usr/bin/python3 circuits/check_kicad_pcbnew_drc_report.py` first"
        )
        return 1

    pcbnew = ensure_pcbnew()
    pairs = parse_courtyard_pairs(args.drc_report.read_text(errors="replace"))
    board = pcbnew.LoadBoard(str(args.board))
    body_overlaps, courtyard_only, failures = classify(board, pcbnew, pairs)
    write_report(args.triage_report, pairs, body_overlaps, courtyard_only, failures)

    if failures:
        print("FAIL courtyard-overlap triage")
        for failure in failures:
            print(f"  - {failure}")
        print(f"  report: {args.triage_report}")
        return 1
    if not pairs:
        print(f"PASS courtyard-overlap triage: no native courtyard-overlap warnings; report={args.triage_report}")
        return 0

    print(
        "BLOCKED courtyard-overlap triage: "
        f"{len(pairs)} native courtyard warnings; "
        f"{len(body_overlaps)} F.Fab/body-box overlaps; "
        f"{len(courtyard_only)} courtyard-only overlaps; report={args.triage_report}"
    )
    if body_overlaps:
        print("  F.Fab/body-box overlap candidates:")
        for item in body_overlaps:
            print(f"    - {item.ref_a}/{item.ref_b}: {fmt_box(item.fab_overlap)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
