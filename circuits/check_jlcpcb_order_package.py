#!/usr/bin/env python3
"""Verify the JLCPCB prototype order package.

This is narrower than full hardware release readiness. It checks that the
current upload artifacts are internally consistent for a JLCPCB bench prototype
order, while first-article calibration and production blockers remain owned by
check_laser_controller_release_readiness.py.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from pathlib import Path

from convert_kicad_pos_to_jlcpcb_cpl import (
    JLCPCB_ROTATION_OVERRIDES,
    footprint_cpl_midpoints,
    jlcpcb_origin_overrides,
)


CIRCUITS_DIR = Path(__file__).resolve().parent
FAB_DIR = CIRCUITS_DIR / "fab"
BOARD_PATH = CIRCUITS_DIR / "laser_controller.kicad_pcb"
BOM_PATH = CIRCUITS_DIR / "laser_controller_bom_jlcpcb.csv"
POS_PATH = FAB_DIR / "laser_controller_pos.csv"
FULL_PROC_PATH = FAB_DIR / "laser_controller_full_procurement.csv"
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
JLCPCB_CPL_COLUMNS = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")
REQUIRED_OPTICAL_LABELS = {
    "RED",
    "GREEN",
    "BLUE",
    "INFRARED",
    "PD CH1",
    "PD CH2",
    "PD CH3",
    "PD CH4",
}
ALLOWED_BOTTOM_REFS = {"D1", "D2", "D3", "D4", "LD1", "LD2", "LD3", "LD4"}
REQUIRED_TOP_TIA_REFS = {
    "U1", "U2", "U3", "U4",
    "RV5", "RV6", "RV7", "RV8",
    "C1", "C2", "C5", "C6", "C9", "C10", "C13", "C14",
}
JLCPCB_ASSEMBLY_TYPES = {"JLCPCB SMT", "JLCPCB THT"}
REQUIRED_THT_ASSEMBLY = {
    "J5": ("JLCPCB THT", "DC-470-2.1GP", "C194407"),
    "J6": ("JLCPCB THT", "R-RJ45R08P-C000", "C386757"),
}
REQUIRED_HAND_PROCUREMENT = {
    "LD1": ("Hand install optical", "D7805I", ""),
    "LD2": ("Hand install optical", "D6505I", ""),
    "LD3": ("Hand install optical", "PLT5 520EB_P", ""),
    "LD4": ("Hand install optical", "PLT5 450GB", ""),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_cpl(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    failures: list[str] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        if columns != JLCPCB_CPL_COLUMNS:
            failures.append(
                f"{path.name}: expected JLCPCB CPL columns {list(JLCPCB_CPL_COLUMNS)}, "
                f"found {list(columns)}"
            )
        rows = list(reader)
    return rows, failures


def parse_mm_cell(value: str, field: str, ref: str) -> tuple[float | None, str | None]:
    text = value.strip()
    if not text.lower().endswith("mm"):
        return None, f"{ref}: CPL {field} value {value!r} must include mm suffix"
    number = text[:-2]
    try:
        parsed = float(number)
    except ValueError:
        return None, f"{ref}: CPL {field} value {value!r} is not numeric"
    return parsed, None


def board_bounds() -> tuple[float, float, float, float]:
    text = BOARD_PATH.read_text()
    points: list[tuple[float, float]] = []
    for match in re.finditer(r"\((?:gr_line|gr_rect|gr_arc)[\s\S]*?\(layer \"Edge\.Cuts\"\)[\s\S]*?\)", text):
        block = match.group(0)
        for x, y in re.findall(r"\((?:start|end|mid)\s+([-0-9.]+)\s+([-0-9.]+)\)", block):
            points.append((float(x), float(y)))
    if not points:
        raise ValueError("no Edge.Cuts coordinates found in board")
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return min(xs), max(xs), min(ys), max(ys)


def footprint_blocks() -> list[tuple[str, str, str]]:
    text = BOARD_PATH.read_text()
    blocks: list[tuple[str, str, str]] = []
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
            blocks.append((ref.group(1), "top" if layer.group(1) == "F" else "bottom", block))
    return blocks


def footprint_layers() -> dict[str, str]:
    layers: dict[str, str] = {}
    for ref, side, _ in footprint_blocks():
        layers[ref] = side
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
    pos_rows, cpl_failures = read_cpl(POS_PATH)
    failures.extend(cpl_failures)
    try:
        min_x, max_x, min_y, max_y = board_bounds()
        coordinate_bounds = {
            "Mid X": (min_x, max_x),
            "Mid Y": (-max_y, -min_y),
        }
    except ValueError as exc:
        failures.append(str(exc))
        coordinate_bounds = {}
    try:
        expected_midpoints = footprint_cpl_midpoints(BOARD_PATH)
    except Exception as exc:
        failures.append(f"could not calculate PCB footprint midpoints for CPL audit: {exc}")
        expected_midpoints = {}
    try:
        expected_origins = jlcpcb_origin_overrides(BOARD_PATH)
    except Exception as exc:
        failures.append(f"could not calculate JLCPCB connector origins for CPL audit: {exc}")
        expected_origins = {}
    bom_refs = bom_designators(bom_rows)
    pos_refs = {row.get("Designator", "") for row in pos_rows}
    pcb_sides = footprint_layers()
    missing = sorted(bom_refs - pos_refs)
    extra = sorted(pos_refs - bom_refs)
    if missing:
        failures.append(f"BOM designators missing from POS: {', '.join(missing)}")
    if extra:
        failures.append(f"POS designators missing from BOM: {', '.join(extra)}")

    for row in pos_rows:
        ref = row.get("Designator", "")
        layer = row.get("Layer", "")
        expected_side = {"top": "Top", "bottom": "Bottom"}.get(pcb_sides.get(ref, ""))
        if expected_side is None:
            failures.append(f"POS designator {ref} is missing from PCB footprints")
        elif layer != expected_side:
            failures.append(
                f"POS layer for {ref} is {layer}, expected {expected_side} from PCB layer"
            )
        parsed_coordinates: dict[str, float] = {}
        for field in ("Mid X", "Mid Y"):
            parsed, error = parse_mm_cell(row.get(field, ""), field, ref)
            if error:
                failures.append(error)
            elif parsed is not None and field in coordinate_bounds:
                parsed_coordinates[field] = parsed
                lower, upper = coordinate_bounds[field]
                if parsed < lower - 0.05 or parsed > upper + 0.05:
                    failures.append(
                        f"{ref}: CPL {field} value {parsed:.4f}mm is outside "
                        f"Gerber coordinate bounds {lower:.4f}..{upper:.4f}mm"
                    )
        if ref in expected_origins and {"Mid X", "Mid Y"} <= parsed_coordinates.keys():
            expected_x, expected_y, expected_rotation = expected_origins[ref]
            actual_x = parsed_coordinates["Mid X"]
            actual_y = parsed_coordinates["Mid Y"]
            if abs(actual_x - expected_x) > 0.025 or abs(actual_y - expected_y) > 0.025:
                failures.append(
                    f"{ref}: CPL JLCPCB origin is ({actual_x:.4f}, {actual_y:.4f})mm, "
                    f"expected JLCPCB library origin ({expected_x:.4f}, {expected_y:.4f})mm"
                )
            if row.get("Rotation") != str(expected_rotation):
                failures.append(
                    f"{ref}: CPL Rotation is {row.get('Rotation')}, expected "
                    f"{expected_rotation} from JLCPCB library-pad alignment"
                )
        elif ref in expected_midpoints and {"Mid X", "Mid Y"} <= parsed_coordinates.keys():
            expected_x, expected_y = expected_midpoints[ref]
            actual_x = parsed_coordinates["Mid X"]
            actual_y = parsed_coordinates["Mid Y"]
            if abs(actual_x - expected_x) > 0.025 or abs(actual_y - expected_y) > 0.025:
                failures.append(
                    f"{ref}: CPL midpoint is ({actual_x:.4f}, {actual_y:.4f})mm, "
                    f"expected footprint midpoint ({expected_x:.4f}, {expected_y:.4f})mm"
                )
        try:
            rotation = float(row.get("Rotation", ""))
        except ValueError:
            failures.append(f"{ref}: CPL Rotation value {row.get('Rotation', '')!r} is not numeric")
        else:
            if not 0.0 <= rotation < 360.0:
                failures.append(f"{ref}: CPL Rotation value {rotation:g} must be in [0, 360)")
            expected_rotation = JLCPCB_ROTATION_OVERRIDES.get(ref)
            if expected_rotation is not None and row.get("Rotation") != str(expected_rotation):
                failures.append(
                    f"{ref}: CPL Rotation is {row.get('Rotation')}, expected "
                    f"{expected_rotation} for JLCPCB package orientation"
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

    j7_pos = [row for row in pos_rows if row.get("Designator") == "J7"]
    if len(j7_pos) != 1:
        failures.append(f"expected exactly one J7 POS row, found {len(j7_pos)}")
    else:
        row = j7_pos[0]
        if row.get("Layer") != "Top":
            failures.append(f"J7 POS layer is {row.get('Layer')}, expected Top")

    required_connectors = {
        "J1": ("C53207143", "Top", "270"),
        "J2": ("C53207143", "Top", "270"),
        "J5": ("C194407", "Top"),
        "J6": ("C386757", "Top", "270"),
        "J7": ("C192300", "Top", "270"),
    }
    for ref, expected in required_connectors.items():
        lcsc, expected_layer, *expected_rotation = expected
        bom_matches = [
            row
            for row in bom_rows
            if ref in {item.strip() for item in row["Designator"].split(",")}
        ]
        if len(bom_matches) != 1:
            failures.append(f"expected exactly one {ref} BOM row, found {len(bom_matches)}")
        elif bom_matches[0]["LCSC"] != lcsc:
            failures.append(f"{ref} BOM LCSC is {bom_matches[0]['LCSC']}, expected {lcsc}")
        pos_matches = [row for row in pos_rows if row.get("Designator") == ref]
        if len(pos_matches) != 1:
            failures.append(f"expected exactly one {ref} POS row, found {len(pos_matches)}")
        elif pos_matches[0].get("Layer") != expected_layer:
            failures.append(f"{ref} POS layer is {pos_matches[0].get('Layer')}, expected {expected_layer}")
        elif expected_rotation and pos_matches[0].get("Rotation") != expected_rotation[0]:
            failures.append(
                f"{ref} POS rotation is {pos_matches[0].get('Rotation')}, expected {expected_rotation[0]}"
            )

    return failures, len(bom_refs), len(pos_refs)


def verify_full_procurement_manifest() -> list[str]:
    failures: list[str] = []
    if not FULL_PROC_PATH.exists():
        return [f"missing full procurement manifest: {FULL_PROC_PATH}"]
    if not BOM_PATH.exists():
        return failures

    bom_refs = bom_designators(read_csv(BOM_PATH))
    rows = read_csv(FULL_PROC_PATH)
    jlc_refs: set[str] = set()
    jlc_rows: dict[str, dict[str, str]] = {}
    hand_rows: dict[str, dict[str, str]] = {}
    for row in rows:
        refs = [ref.strip() for ref in row["Designator"].split(",") if ref.strip()]
        if row["Assembly"] in JLCPCB_ASSEMBLY_TYPES:
            jlc_refs.update(refs)
            for ref in refs:
                jlc_rows[ref] = row
        else:
            for ref in refs:
                hand_rows[ref] = row

    missing_jlc = sorted(bom_refs - jlc_refs)
    extra_jlc = sorted(jlc_refs - bom_refs)
    if missing_jlc:
        failures.append(
            "full procurement manifest is missing JLCPCB assembly BOM refs: "
            + ", ".join(missing_jlc)
        )
    if extra_jlc:
        failures.append(
            "full procurement manifest has extra JLCPCB assembly refs outside BOM: "
            + ", ".join(extra_jlc)
        )

    for ref, (assembly, mpn, lcsc) in REQUIRED_THT_ASSEMBLY.items():
        row = jlc_rows.get(ref)
        if row is None:
            failures.append(f"full procurement manifest missing JLCPCB THT row for {ref}")
            continue
        if row["Assembly"] != assembly:
            failures.append(
                f"full procurement manifest {ref} assembly is {row['Assembly']}, expected {assembly}"
            )
        if row["MPN"] != mpn:
            failures.append(f"full procurement manifest {ref} MPN is {row['MPN']}, expected {mpn}")
        if row["LCSC"] != lcsc:
            failures.append(f"full procurement manifest {ref} LCSC is {row['LCSC']}, expected {lcsc}")

    for ref, (assembly, mpn, lcsc) in REQUIRED_HAND_PROCUREMENT.items():
        row = hand_rows.get(ref)
        if row is None:
            failures.append(f"full procurement manifest missing hand-install row for {ref}")
            continue
        if row["Assembly"] != assembly:
            failures.append(
                f"full procurement manifest {ref} assembly is {row['Assembly']}, expected {assembly}"
            )
        if row["MPN"] != mpn:
            failures.append(f"full procurement manifest {ref} MPN is {row['MPN']}, expected {mpn}")
        if row["LCSC"] != lcsc:
            failures.append(f"full procurement manifest {ref} LCSC is {row['LCSC']}, expected {lcsc}")

    unexpected_hand = sorted(set(hand_rows) - set(REQUIRED_HAND_PROCUREMENT))
    if unexpected_hand:
        failures.append(
            "full procurement manifest has unexpected non-JLC hand refs: "
            + ", ".join(unexpected_hand)
        )
    return failures


def verify_board_text() -> list[str]:
    failures: list[str] = []
    text = BOARD_PATH.read_text()
    for label in sorted(REQUIRED_OPTICAL_LABELS):
        pattern = rf'\(gr_text "{re.escape(label)}".*?\(layer "[FB]\.SilkS"\)'
        if not re.search(pattern, text, flags=re.DOTALL):
            failures.append(f"missing optical board text {label!r} on a silkscreen layer")
    if not re.search(
        r'\(gr_text "vivonics".*?\(layer "B\.SilkS"\).*?'
        r'\(size 12 12\).*?\(thickness 1\.4\).*?\(justify mirror\)',
        text,
        flags=re.DOTALL,
    ):
        failures.append("backside vivonics mark is missing expected large mirrored 12 mm text")
    return failures


def verify_optical_side_placement() -> list[str]:
    failures: list[str] = []
    blocks = footprint_blocks()
    layers = {ref: side for ref, side, _ in blocks}
    bottom_refs = {ref for ref, side in layers.items() if side == "bottom"}
    bottom_paste_refs = {
        ref
        for ref, _, block in blocks
        if '"B.Paste"' in block
    }

    unexpected_bottom = sorted(bottom_refs - ALLOWED_BOTTOM_REFS)
    missing_bottom = sorted(ALLOWED_BOTTOM_REFS - bottom_refs)
    unexpected_bottom_paste = sorted(bottom_paste_refs - {"D1", "D2", "D3", "D4"})
    if unexpected_bottom:
        failures.append(
            "unexpected bottom-side footprints outside optical PD/LD set: "
            + ", ".join(unexpected_bottom)
        )
    if unexpected_bottom_paste:
        failures.append(
            "unexpected bottom-paste SMT footprints outside signal PD set: "
            + ", ".join(unexpected_bottom_paste)
        )
    if missing_bottom:
        failures.append(
            "optical PD/LD footprints not on bottom side: "
            + ", ".join(missing_bottom)
        )

    wrong_top = sorted(
        ref for ref in REQUIRED_TOP_TIA_REFS
        if layers.get(ref) != "top"
    )
    if wrong_top:
        failures.append(
            "TIA SMT footprints must be top-side for single-sided SMT assembly: "
            + ", ".join(wrong_top)
        )
    wrong_internal_layers = sorted(
        ref
        for ref, _, block in blocks
        if ref in REQUIRED_TOP_TIA_REFS
        and any(
            token in block
            for token in ('"B.Cu"', '"B.Mask"', '"B.Paste"', '"B.SilkS"', '"B.Fab"', '"B.CrtYd"')
        )
    )
    if wrong_internal_layers:
        failures.append(
            "TIA SMT footprints still contain bottom-side pads or drawings: "
            + ", ".join(wrong_internal_layers)
        )
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

    for path in (BOARD_PATH, BOM_PATH, POS_PATH, FULL_PROC_PATH):
        if not path.exists():
            failures.append(f"missing required artifact: {path}")

    failures.extend(verify_zip(GERBER_ZIP_PATH, files, source_paths))
    failures.extend(
        verify_zip(PACKAGE_ZIP_PATH, files + PACKAGE_ONLY_FILES, source_paths)
    )
    bom_pos_failures, bom_count, pos_count = verify_bom_pos()
    failures.extend(bom_pos_failures)
    failures.extend(verify_full_procurement_manifest())
    failures.extend(verify_board_text())
    failures.extend(verify_optical_side_placement())

    if failures:
        print(f"FAIL JLCPCB order package: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS JLCPCB order package: "
        f"{len(files)} Gerber/drill files, package archive includes BOM/POS, "
        f"{bom_count}/{pos_count} BOM/CPL designators match, CPL is JLCPCB five-column mm format, "
        "CPL coordinates match PCB footprint midpoints except connector rows use JLCPCB library origins, "
        "J1/J2 use stocked C53207143 Mini-B assembly, "
        "full procurement manifest separates JLC SMT/THT from hand-installed optical parts, "
        "J5/J6 are included for THT connector assembly, J7 is C192300 2x4 SMD, "
        "only PD/LD footprints are bottom-side, PD/laser labels and backside vivonics mark are present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
