#!/usr/bin/env python3
"""Convert KiCad CSV position export to JLCPCB CPL format.

KiCad exports `Ref,Val,Package,PosX,PosY,Rot,Side`, with Y matching the
Gerber coordinate sign. JLCPCB's current CPL parser expects the stricter
`Designator,Mid X,Mid Y,Layer,Rotation` form shown in its sample file.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


KICAD_COLUMNS = ("Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side")
JLCPCB_COLUMNS = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")


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


def convert_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    converted: list[dict[str, str]] = []
    for row in rows:
        pos_x = float(row["PosX"])
        pos_y = float(row["PosY"])
        converted.append(
            {
                "Designator": row["Ref"],
                "Mid X": mm(pos_x),
                "Mid Y": mm(-pos_y),
                "Layer": layer(row["Side"]),
                "Rotation": rotation(row["Rot"]),
            }
        )
    return converted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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

    converted = convert_rows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=JLCPCB_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(converted)

    print(f"Wrote JLCPCB CPL with {len(converted)} placements to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
