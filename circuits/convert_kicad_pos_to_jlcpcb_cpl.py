#!/usr/bin/env python3
"""Convert KiCad CSV position export to JLCPCB CPL format.

KiCad exports `Ref,Val,Package,PosX,PosY,Rot,Side`, with Y matching the
Gerber coordinate sign. JLCPCB's current CPL parser expects the stricter
`Designator,Mid X,Mid Y,Layer,Rotation` form shown in its sample file.
JLCPCB also expects component coordinates in board-local coordinates, not the
absolute KiCad drawing-sheet coordinates. This script subtracts the Edge.Cuts
minimum X/Y so the top-left board corner is `(0, 0)` in the exported CPL.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


KICAD_COLUMNS = ("Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side")
JLCPCB_COLUMNS = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")


def edge_cuts_minimum(board_path: Path) -> tuple[float, float]:
    text = board_path.read_text()
    points: list[tuple[float, float]] = []
    for match in re.finditer(r"\((?:gr_line|gr_rect|gr_arc)[\s\S]*?\(layer \"Edge\.Cuts\"\)[\s\S]*?\)", text):
        block = match.group(0)
        for x, y in re.findall(r"\((?:start|end|mid)\s+([-0-9.]+)\s+([-0-9.]+)\)", block):
            points.append((float(x), float(y)))
    if not points:
        raise ValueError(f"{board_path}: no Edge.Cuts coordinates found")
    return min(x for x, _ in points), min(y for _, y in points)


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


def convert_rows(rows: list[dict[str, str]], board_min_x: float, board_min_y: float) -> list[dict[str, str]]:
    converted: list[dict[str, str]] = []
    for row in rows:
        pos_x = float(row["PosX"])
        pos_y = -float(row["PosY"])
        converted.append(
            {
                "Designator": row["Ref"],
                "Mid X": mm(pos_x - board_min_x),
                "Mid Y": mm(pos_y - board_min_y),
                "Layer": layer(row["Side"]),
                "Rotation": rotation(row["Rot"]),
            }
        )
    return converted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="KiCad CSV position file")
    parser.add_argument("output", type=Path, help="JLCPCB CPL CSV output")
    parser.add_argument(
        "--board",
        type=Path,
        default=Path("circuits/laser_controller.kicad_pcb"),
        help="KiCad board file used to derive the Edge.Cuts origin",
    )
    args = parser.parse_args()

    with args.input.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != KICAD_COLUMNS:
            raise SystemExit(
                f"expected KiCad POS columns {KICAD_COLUMNS}, found {tuple(reader.fieldnames or ())}"
            )
        rows = list(reader)

    board_min_x, board_min_y = edge_cuts_minimum(args.board)
    converted = convert_rows(rows, board_min_x, board_min_y)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=JLCPCB_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(converted)

    print(f"Wrote JLCPCB CPL with {len(converted)} placements to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
