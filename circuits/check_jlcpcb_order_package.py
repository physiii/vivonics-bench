#!/usr/bin/env python3
"""Verify the JLCPCB prototype order package.

This is narrower than full hardware release readiness. It checks that the
current upload artifacts are internally consistent for a top-side SMT bench
prototype order, while first-article calibration and production blockers remain
owned by check_laser_controller_release_readiness.py.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from pathlib import Path


CIRCUITS_DIR = Path(__file__).resolve().parent
FAB_DIR = CIRCUITS_DIR / "fab"
BOARD_PATH = CIRCUITS_DIR / "laser_controller.kicad_pcb"
BOM_PATH = CIRCUITS_DIR / "laser_controller_bom_jlcpcb.csv"
POS_PATH = FAB_DIR / "laser_controller_pos.csv"
GERBER_ZIP_PATH = CIRCUITS_DIR / "laser_controller_gerbers.zip"
PACKAGE_ZIP_PATH = CIRCUITS_DIR / "laser_controller_jlcpcb_package.zip"

GERBER_JOB_FILE = "laser_controller-job.gbrjob"
DRILL_FILES = (
    "laser_controller-NPTH.drl",
    "laser_controller-PTH.drl",
)
PACKAGE_ONLY_FILES = (
    "laser_controller_bom_jlcpcb.csv",
    "laser_controller_pos.csv",
)
REQUIRED_BOARD_TEXT = {
    ("vivonics", "B.SilkS"),
    ("RED", "F.SilkS"),
    ("GREEN", "F.SilkS"),
    ("BLUE", "F.SilkS"),
    ("INFRARED", "F.SilkS"),
    ("PD CH1", "F.SilkS"),
    ("PD CH2", "F.SilkS"),
    ("PD CH3", "F.SilkS"),
    ("PD CH4", "F.SilkS"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def footprint_layers() -> dict[str, str]:
    text = BOARD_PATH.read_text()
    layers: dict[str, str] = {}
    index = 0
    while True:
        start = text.find("(footprint ", index)
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

        block = text[start:end]
        index = end
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        layer = re.search(r'\(layer "([FB])\.Cu"\)', block)
        if ref and layer:
            layers[ref.group(1)] = "top" if layer.group(1) == "F" else "bottom"
    return layers


def gerber_files() -> tuple[str, ...]:
    job_path = FAB_DIR / GERBER_JOB_FILE
    if not job_path.exists():
        raise FileNotFoundError(f"missing Gerber job file: {job_path}")

    with job_path.open() as handle:
        job = json.load(handle)

    plotted_files = tuple(
        entry["Path"]
        for entry in job.get("FilesAttributes", [])
        if isinstance(entry, dict) and entry.get("Path")
    )
    if len(plotted_files) != 11:
        raise ValueError(
            f"{job_path.name}: expected 11 plotted Gerber layers, found {len(plotted_files)}"
        )

    return plotted_files + (GERBER_JOB_FILE,) + DRILL_FILES


def bom_designators(rows: list[dict[str, str]]) -> set[str]:
    refs: set[str] = set()
    for row in rows:
        for ref in row["Designator"].split(","):
            ref = ref.strip()
            if ref:
                refs.add(ref)
    return refs


def verify_zip(path: Path, expected_names: tuple[str, ...], source_paths: dict[str, Path]) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return [f"missing archive: {path}"]
    try:
        with zipfile.ZipFile(path) as archive:
            names = tuple(sorted(archive.namelist()))
            expected = tuple(sorted(expected_names))
            if names != expected:
                failures.append(
                    f"{path.name}: expected entries {list(expected)}, found {list(names)}"
                )
            bad = archive.testzip()
            if bad is not None:
                failures.append(f"{path.name}: corrupt archive member {bad}")
            for name in expected_names:
                source = source_paths[name]
                if not source.exists():
                    failures.append(f"{path.name}: source file missing for {name}: {source}")
                    continue
                try:
                    archived = archive.read(name)
                except KeyError:
                    continue
                if archived != source.read_bytes():
                    failures.append(f"{path.name}: archived {name} is stale vs {source}")
    except zipfile.BadZipFile as exc:
        failures.append(f"{path.name}: invalid zip file: {exc}")
    return failures


def verify_bom_pos() -> tuple[list[str], int, int]:
    failures: list[str] = []
    if not BOM_PATH.exists():
        failures.append(f"missing BOM: {BOM_PATH}")
        return failures, 0, 0
    if not POS_PATH.exists():
        failures.append(f"missing POS: {POS_PATH}")
        return failures, 0, 0

    bom_rows = read_csv(BOM_PATH)
    pos_rows = read_csv(POS_PATH)
    bom_refs = bom_designators(bom_rows)
    pos_refs = {row["Ref"] for row in pos_rows}
    pcb_sides = footprint_layers()
    missing = sorted(bom_refs - pos_refs)
    extra = sorted(pos_refs - bom_refs)
    if missing:
        failures.append(f"BOM designators missing from POS: {', '.join(missing)}")
    if extra:
        failures.append(f"POS designators missing from BOM: {', '.join(extra)}")

    for row in pos_rows:
        ref = row["Ref"]
        side = row["Side"]
        expected_side = pcb_sides.get(ref)
        if expected_side is None:
            failures.append(f"POS designator {ref} is missing from PCB footprints")
        elif side != expected_side:
            failures.append(
                f"POS side for {ref} is {side}, expected {expected_side} from PCB layer"
            )

    bad_lcsc = sorted(
        {
            row["LCSC"]
            for row in bom_rows
            if not re.fullmatch(r"C\d+", row.get("LCSC", ""))
        }
    )
    if bad_lcsc:
        failures.append(f"BOM has invalid LCSC codes: {', '.join(bad_lcsc)}")

    j7_bom = [
        row
        for row in bom_rows
        if "J7" in {ref.strip() for ref in row["Designator"].split(",")}
    ]
    if len(j7_bom) != 1:
        failures.append(f"expected exactly one J7 BOM row, found {len(j7_bom)}")
    else:
        row = j7_bom[0]
        if row["LCSC"] != "C192300":
            failures.append(f"J7 BOM LCSC is {row['LCSC']}, expected C192300")
        if "PinHeader_2x04_P2.54mm_SMD_Vertical_C192300" not in row["Footprint"]:
            failures.append(f"J7 BOM footprint is not the 2x4 SMD C192300 header: {row['Footprint']}")

    j7_pos = [row for row in pos_rows if row["Ref"] == "J7"]
    if len(j7_pos) != 1:
        failures.append(f"expected exactly one J7 POS row, found {len(j7_pos)}")
    else:
        row = j7_pos[0]
        if row["Val"] != "C192300":
            failures.append(f"J7 POS value is {row['Val']}, expected C192300")
        if row["Package"] != "PinHeader_2x04_P2.54mm_SMD_Vertical_C192300":
            failures.append(f"J7 POS package is {row['Package']}, expected C192300 2x4 SMD header")
        if row["Side"] != "top":
            failures.append(f"J7 POS side is {row['Side']}, expected top")

    return failures, len(bom_refs), len(pos_refs)


def verify_board_text() -> list[str]:
    failures: list[str] = []
    text = BOARD_PATH.read_text()
    for label, layer in sorted(REQUIRED_BOARD_TEXT):
        pattern = rf'\(gr_text "{re.escape(label)}".*?\(layer "{re.escape(layer)}"\)'
        if not re.search(pattern, text, flags=re.DOTALL):
            failures.append(f"missing board text {label!r} on {layer}")
    if not re.search(
        r'\(gr_text "vivonics".*?\(layer "B\.SilkS"\).*?'
        r'\(size 12 12\).*?\(thickness 1\.4\).*?\(justify mirror\)',
        text,
        flags=re.DOTALL,
    ):
        failures.append("backside vivonics mark is missing expected large mirrored 12 mm text")
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        files = gerber_files()
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        files = ()
        failures.append(str(exc))

    source_paths = {name: FAB_DIR / name for name in files}
    source_paths.update(
        {
            "laser_controller_bom_jlcpcb.csv": BOM_PATH,
            "laser_controller_pos.csv": POS_PATH,
        }
    )

    for path in (BOARD_PATH, BOM_PATH, POS_PATH):
        if not path.exists():
            failures.append(f"missing required artifact: {path}")

    failures.extend(verify_zip(GERBER_ZIP_PATH, files, source_paths))
    failures.extend(
        verify_zip(PACKAGE_ZIP_PATH, files + PACKAGE_ONLY_FILES, source_paths)
    )
    bom_pos_failures, bom_count, pos_count = verify_bom_pos()
    failures.extend(bom_pos_failures)
    failures.extend(verify_board_text())

    if failures:
        print(f"FAIL JLCPCB order package: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS JLCPCB order package: "
        f"{len(files)} Gerber/drill files, package archive includes BOM/POS, "
        f"{bom_count}/{pos_count} BOM/POS designators match, J7 is C192300 2x4 SMD, "
        "PD/laser labels and backside vivonics mark are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
