#!/usr/bin/env python3
"""Verify PCB footprint 3D model coverage for visual assembly review."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_KICAD_3DMODELS = Path("/usr/share/kicad/3dmodels")
J7_EXPECTED_MODEL = "packages3d/Connector_PinHeader.3dshapes/PinHeader_2x04_P2.54mm_SMD_Vertical_C192300.wrl"
J7_EXPECTED_OFFSET = (0.0, 0.0, 0.0)
J7_EXPECTED_SCALE = (1.0, 1.0, 1.0)
J7_EXPECTED_ROTATION = (0.0, 0.0, 0.0)
OFFSET_TOLERANCE_MM = 0.001
FOOT_CENTER_TOLERANCE_MM = 0.01


def ensure_pcbnew():
    try:
        import pcbnew  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pcbnew Python module not available. Run with system Python, e.g. "
            "`/usr/bin/python3 circuits/check_3d_model_coverage.py`."
        ) from exc
    return pcbnew


def model_env(board_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    project_dir = str(board_path.resolve().parent)
    env.setdefault("KIPRJMOD", project_dir)
    if DEFAULT_KICAD_3DMODELS.exists():
        default_models = str(DEFAULT_KICAD_3DMODELS)
        for key in (
            "KICAD7_3DMODEL_DIR",
            "KICAD8_3DMODEL_DIR",
            "KICAD9_3DMODEL_DIR",
            "KICAD10_3DMODEL_DIR",
            "KISYS3DMOD",
        ):
            env.setdefault(key, default_models)
    return env


def footprint_id(fp) -> tuple[str, str]:
    fpid = fp.GetFPID()
    return str(fpid.GetLibNickname()), str(fpid.GetLibItemName())


def is_model_exempt(fp) -> bool:
    lib, item = footprint_id(fp)
    return lib == "MountingHole" or item.startswith("MountingHole")


def expand_model_path(raw: str, env: dict[str, str], board_path: Path) -> tuple[Path | None, str | None]:
    missing: list[str] = []

    def replace_braced(match: re.Match[str]) -> str:
        key = match.group(1)
        value = env.get(key)
        if value is None:
            missing.append(key)
            return match.group(0)
        return value

    expanded = re.sub(r"\$\{([^}]+)\}", replace_braced, raw)
    expanded = os.path.expandvars(expanded)
    if "$" in expanded:
        return None, f"unresolved variable in model path {raw!r}"
    path = Path(expanded)
    if not path.is_absolute():
        path = board_path.resolve().parent / path
    if missing:
        return None, f"unresolved model variable(s) {', '.join(sorted(set(missing)))} in {raw!r}"
    return path, None


def wrl_smt_foot_centers(path: Path) -> dict[str, tuple[float, float]]:
    centers: dict[str, tuple[float, float]] = {}
    text = path.read_text(errors="replace")
    marker_re = re.compile(
        r"^\s*#\s*SMT_FOOT\s+pad=(\d+)\s+center=\("
        r"([-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?|[-+]?\.\d+(?:[Ee][-+]?\d+)?),"
        r"([-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?|[-+]?\.\d+(?:[Ee][-+]?\d+)?)\)",
        re.MULTILINE,
    )
    for match in marker_re.finditer(text):
        centers[match.group(1)] = (float(match.group(2)), float(match.group(3)))
    return centers


def j7_pad_centers_mm(fp) -> dict[str, tuple[float, float]]:
    centers: dict[str, tuple[float, float]] = {}
    for pad in fp.Pads():
        pos = pad.GetFPRelativePosition()
        centers[str(pad.GetNumber())] = (float(pos.x) / 1_000_000.0, float(pos.y) / 1_000_000.0)
    return centers


def check_j7_model(fp, env: dict[str, str], board_path: Path) -> list[str]:
    failures: list[str] = []
    models = list(fp.Models())
    if not models:
        return ["J7 has no 3D model"]
    matching = [model for model in models if J7_EXPECTED_MODEL in model.m_Filename.replace("\\", "/")]
    if not matching:
        failures.append(
            "J7 3D model is not the project-local C192300 2x04 vertical SMT header visual model "
            f"({J7_EXPECTED_MODEL})"
        )
        return failures
    model = matching[0]
    offset = (float(model.m_Offset.x), float(model.m_Offset.y), float(model.m_Offset.z))
    if any(abs(actual - expected) > OFFSET_TOLERANCE_MM for actual, expected in zip(offset, J7_EXPECTED_OFFSET)):
        failures.append(
            "J7 3D model offset is "
            f"({offset[0]:.3f}, {offset[1]:.3f}, {offset[2]:.3f}); "
            f"expected ({J7_EXPECTED_OFFSET[0]:.3f}, {J7_EXPECTED_OFFSET[1]:.3f}, {J7_EXPECTED_OFFSET[2]:.3f})"
        )
    scale = (float(model.m_Scale.x), float(model.m_Scale.y), float(model.m_Scale.z))
    if any(abs(actual - expected) > OFFSET_TOLERANCE_MM for actual, expected in zip(scale, J7_EXPECTED_SCALE)):
        failures.append(
            "J7 3D model scale is "
            f"({scale[0]:.3f}, {scale[1]:.3f}, {scale[2]:.3f}); "
            f"expected ({J7_EXPECTED_SCALE[0]:.3f}, {J7_EXPECTED_SCALE[1]:.3f}, {J7_EXPECTED_SCALE[2]:.3f})"
        )
    rotation = (float(model.m_Rotation.x), float(model.m_Rotation.y), float(model.m_Rotation.z))
    if any(abs(actual - expected) > OFFSET_TOLERANCE_MM for actual, expected in zip(rotation, J7_EXPECTED_ROTATION)):
        failures.append(
            "J7 3D model rotation is "
            f"({rotation[0]:.3f}, {rotation[1]:.3f}, {rotation[2]:.3f}); "
            f"expected ({J7_EXPECTED_ROTATION[0]:.3f}, {J7_EXPECTED_ROTATION[1]:.3f}, {J7_EXPECTED_ROTATION[2]:.3f})"
        )
    resolved, error = expand_model_path(model.m_Filename, env, board_path)
    if error is not None or resolved is None:
        failures.append(f"J7: {error or 'could not resolve model path'}")
        return failures
    model_centers = wrl_smt_foot_centers(resolved)
    pad_centers = j7_pad_centers_mm(fp)
    if sorted(model_centers) != sorted(pad_centers):
        failures.append(
            "J7 C192300 visual model SMT feet are defined for pads "
            f"{', '.join(sorted(model_centers)) or 'none'}; "
            f"expected pads {', '.join(sorted(pad_centers))}"
        )
        return failures
    for pad, expected in sorted(pad_centers.items(), key=lambda item: int(item[0])):
        actual = model_centers[pad]
        if any(abs(a - e) > FOOT_CENTER_TOLERANCE_MM for a, e in zip(actual, expected)):
            failures.append(
                f"J7 C192300 visual model SMT foot {pad} is centered at "
                f"({actual[0]:.2f}, {actual[1]:.2f}); expected footprint pad center "
                f"({expected[0]:.2f}, {expected[1]:.2f})"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    if not args.board.exists():
        print(f"FAIL 3D model coverage: board file not found: {args.board}")
        return 1

    pcbnew = ensure_pcbnew()
    board = pcbnew.LoadBoard(str(args.board))
    env = model_env(args.board)
    failures: list[str] = []
    checked = 0
    exempt = 0

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        models = list(fp.Models())
        if is_model_exempt(fp):
            exempt += 1
            continue
        if not models:
            lib, item = footprint_id(fp)
            failures.append(f"{ref} ({lib}:{item}) has no 3D model")
            continue
        checked += 1
        for model in models:
            resolved, error = expand_model_path(model.m_Filename, env, args.board)
            if error is not None:
                failures.append(f"{ref}: {error}")
                continue
            if resolved is None or not resolved.exists():
                failures.append(f"{ref}: missing 3D model file {model.m_Filename}")

    j7 = board.FindFootprintByReference("J7")
    if j7 is None:
        failures.append("J7 footprint missing")
    else:
        failures.extend(check_j7_model(j7, env, args.board))

    if failures:
        print(f"FAIL 3D model coverage: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS 3D model coverage: "
        f"{checked} modeled footprints, {exempt} mounting-hole footprint(s) exempt, "
        "all model files resolve, J7 SMT header visual model is aligned to pad centers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
