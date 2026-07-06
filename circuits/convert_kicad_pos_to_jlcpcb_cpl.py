#!/usr/bin/env python3
"""Convert KiCad CSV position export to JLCPCB CPL format.

KiCad exports `Ref,Val,Package,PosX,PosY,Rot,Side`. JLCPCB's current CPL parser
expects the stricter `Designator,Mid X,Mid Y,Layer,Rotation` form shown in its
sample file. Keep the KiCad X/Y/rotation values unchanged except for formatting:
the Gerber upload and CPL then share the same origin, Y sign, and footprint
orientations.
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
                "Mid Y": mm(pos_y),
                "Layer": layer(row["Side"]),
                "Rotation": rotation(row["Rot"]),
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
