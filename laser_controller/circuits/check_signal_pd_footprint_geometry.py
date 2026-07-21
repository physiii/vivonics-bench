#!/usr/bin/env python3
"""Verify signal photodiode footprint geometry on the current PCB.

Native DRC catches clearance and mask collisions, but it will not flag a
photodiode pad that is locally rotated inside an otherwise valid footprint.
This gate locks the SFH2201 copper and paste pad geometry used by D1-D4.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
POSITION_TOLERANCE_MM = 0.001
SIZE_TOLERANCE_MM = 0.001
ANGLE_TOLERANCE_DEG = 0.001


@dataclass(frozen=True)
class PadSpec:
    number: str
    net: str
    pos: tuple[float, float]
    size: tuple[float, float]
    orientation_deg: float


@dataclass(frozen=True)
class PhotodiodeSpec:
    ref: str
    channel: str
    cathode_net: str
    anode_net: str


SIGNAL_PDS = (
    PhotodiodeSpec("D1", "IR", "/TIA_IR/PD_CATHODE", "/TIA_IR/PD_ANODE"),
    PhotodiodeSpec("D2", "RED", "/TIA_RED/PD_CATHODE", "/TIA_RED/PD_ANODE"),
    PhotodiodeSpec("D3", "GREEN", "/TIA_GREEN/PD_CATHODE", "/TIA_GREEN/PD_ANODE"),
    PhotodiodeSpec("D4", "BLUE", "/TIA_BLUE/PD_CATHODE", "/TIA_BLUE/PD_ANODE"),
)

COPPER_PAD_SPECS = (
    PadSpec("1", "", (-2.265, 0.0), (0.8, 3.0), 0.0),
    PadSpec("2", "", (2.265, 0.0), (0.8, 2.5), 180.0),
)
PASTE_PAD_SPECS = (
    PadSpec("", "", (-2.265, -0.8), (0.6, 1.0), 0.0),
    PadSpec("", "", (-2.265, 0.8), (0.6, 1.0), 0.0),
    PadSpec("", "", (2.265, -0.7), (0.6, 1.0), 0.0),
    PadSpec("", "", (2.265, 0.7), (0.6, 1.0), 0.0),
)


def ensure_pcbnew():
    try:
        import pcbnew  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pcbnew Python module not available. Run with system Python, e.g. "
            "`/usr/bin/python3 circuits/check_signal_pd_footprint_geometry.py`."
        ) from exc
    return pcbnew


def close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def angle_close(actual: float, expected: float) -> bool:
    delta = (actual - expected + 180.0) % 360.0 - 180.0
    return abs(delta) <= ANGLE_TOLERANCE_DEG


def check_pad_geometry(failures: list[str], ref: str, pad, spec: PadSpec, label: str) -> None:
    pos = pad.GetFPRelativePosition()
    size = pad.GetSize()
    actual_pos = (pos.x / 1_000_000, pos.y / 1_000_000)
    actual_size = (size.x / 1_000_000, size.y / 1_000_000)
    actual_orientation = float(pad.GetOrientationDegrees())
    if not (
        close(actual_pos[0], spec.pos[0], POSITION_TOLERANCE_MM)
        and close(actual_pos[1], spec.pos[1], POSITION_TOLERANCE_MM)
    ):
        failures.append(
            f"{ref} {label}: local position is ({actual_pos[0]:.3f}, {actual_pos[1]:.3f}), "
            f"expected ({spec.pos[0]:.3f}, {spec.pos[1]:.3f})"
        )
    if not (
        close(actual_size[0], spec.size[0], SIZE_TOLERANCE_MM)
        and close(actual_size[1], spec.size[1], SIZE_TOLERANCE_MM)
    ):
        failures.append(
            f"{ref} {label}: pad size is ({actual_size[0]:.3f}, {actual_size[1]:.3f}), "
            f"expected ({spec.size[0]:.3f}, {spec.size[1]:.3f})"
        )
    if not angle_close(actual_orientation, spec.orientation_deg):
        failures.append(
            f"{ref} {label}: local pad orientation is {actual_orientation:.3f} deg, "
            f"expected {spec.orientation_deg:.3f} deg"
        )


def sorted_paste_pads(fp) -> list:
    paste_pads = [pad for pad in fp.Pads() if not pad.GetNumber()]
    return sorted(
        paste_pads,
        key=lambda pad: (
            round(pad.GetFPRelativePosition().x / 1_000_000, 3),
            round(pad.GetFPRelativePosition().y / 1_000_000, 3),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    if not args.board.exists():
        print(f"FAIL signal-PD footprint geometry: board file not found: {args.board}")
        return 1

    pcbnew = ensure_pcbnew()
    board = pcbnew.LoadBoard(str(args.board))
    failures: list[str] = []

    for pd in SIGNAL_PDS:
        fp = board.FindFootprintByReference(pd.ref)
        if fp is None:
            failures.append(f"{pd.ref}: footprint missing")
            continue
        footprint_id = f"{fp.GetFPID().GetLibNickname()}:{fp.GetFPID().GetLibItemName()}"
        if footprint_id != "OptoDevice:Osram_SFH2201":
            failures.append(f"{pd.ref}: footprint is {footprint_id}, expected OptoDevice:Osram_SFH2201")
            continue

        copper_specs = (
            PadSpec("1", pd.cathode_net, COPPER_PAD_SPECS[0].pos, COPPER_PAD_SPECS[0].size, COPPER_PAD_SPECS[0].orientation_deg),
            PadSpec("2", pd.anode_net, COPPER_PAD_SPECS[1].pos, COPPER_PAD_SPECS[1].size, COPPER_PAD_SPECS[1].orientation_deg),
        )
        for spec in copper_specs:
            pad = fp.FindPadByNumber(spec.number)
            if pad is None:
                failures.append(f"{pd.ref}.{spec.number}: pad missing")
                continue
            if pad.GetNetname() != spec.net:
                failures.append(f"{pd.ref}.{spec.number}: net is {pad.GetNetname()}, expected {spec.net}")
            check_pad_geometry(failures, pd.ref, pad, spec, f"pad {spec.number}")

        paste_pads = sorted_paste_pads(fp)
        if len(paste_pads) != len(PASTE_PAD_SPECS):
            failures.append(f"{pd.ref}: has {len(paste_pads)} paste-only pads, expected {len(PASTE_PAD_SPECS)}")
            continue
        for index, (pad, spec) in enumerate(zip(paste_pads, PASTE_PAD_SPECS), start=1):
            check_pad_geometry(failures, pd.ref, pad, spec, f"paste pad {index}")

    if failures:
        print(f"FAIL signal-PD footprint geometry: {len(failures)} issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS signal-PD footprint geometry: D1-D4 SFH2201 copper/paste pad positions, sizes, orientations, and nets match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
