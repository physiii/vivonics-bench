#!/usr/bin/env python3
"""Focused PCB layout-geometry release review for hand-routed risk areas.

This complements `check_laser_controller_pcb.py`. The default PCB checker proves
net membership and explicit connectivity; this gate keeps high-risk physical
layout distances visible for the human layout review bucket.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
import sys

from check_laser_controller_pcb import parse_board_pad_nets, parse_footprint_geometry


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"


@dataclass(frozen=True)
class PadRef:
    ref: str
    pad: str


@dataclass(frozen=True)
class GeometryCheck:
    category: str
    title: str
    a: PadRef
    b: PadRef
    max_mm: float
    rationale: str


CHECKS: tuple[GeometryCheck, ...] = (
    GeometryCheck(
        "buck-input",
        "AP63205 local VIN ceramic near U15",
        PadRef("U15", "3"),
        PadRef("C61", "1"),
        8.0,
        "Buck VIN ceramic should be local to the regulator VIN/GND loop, not only near the power connector.",
    ),
    GeometryCheck(
        "buck-input",
        "AP63200 local VIN ceramic near U16",
        PadRef("U16", "3"),
        PadRef("C62", "1"),
        8.0,
        "Laser buck VIN ceramic should be local to the AP63200 VIN/GND loop.",
    ),
    GeometryCheck(
        "buck-output",
        "AP63200 inductor-to-output-cap loop",
        PadRef("L2", "2"),
        PadRef("C68", "1"),
        7.0,
        "Laser buck output capacitor should sit close to the inductor output node.",
    ),
    # The full PCB checker owns USB route length, skew, layer, width, and via
    # policy. This focused gate only keeps the surge clamp close to the connector.
    GeometryCheck(
        "usb-esd",
        "Native USB D- connector-to-ESD distance",
        PadRef("J2", "2"),
        PadRef("D12", "2"),
        7.5,
        "USB ESD clamp should be near the connector before the trace enters the board.",
    ),
    GeometryCheck(
        "tia-sensitive",
        "IR signal photodiode anode to OPA380 summing node",
        PadRef("D1", "2"),
        PadRef("U1", "2"),
        6.0,
        "Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.",
    ),
    GeometryCheck(
        "tia-sensitive",
        "Red signal photodiode anode to OPA380 summing node",
        PadRef("D2", "2"),
        PadRef("U2", "2"),
        6.0,
        "Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.",
    ),
    GeometryCheck(
        "tia-sensitive",
        "Green signal photodiode anode to OPA380 summing node",
        PadRef("D3", "2"),
        PadRef("U3", "2"),
        6.0,
        "Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.",
    ),
    GeometryCheck(
        "tia-sensitive",
        "Blue signal photodiode anode to OPA380 summing node",
        PadRef("D4", "2"),
        PadRef("U4", "2"),
        6.0,
        "Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.",
    ),
    GeometryCheck(
        "monitor-pd",
        "IR monitor-PD raw path from LD1 to sense resistor",
        PadRef("LD1", "3"),
        PadRef("R42", "1"),
        25.0,
        "Raw monitor-PD current should not cross the board before the current-sense resistor.",
    ),
    GeometryCheck(
        "monitor-pd",
        "Red monitor-PD raw path from LD2 to sense resistor",
        PadRef("LD2", "3"),
        PadRef("R44", "1"),
        25.0,
        "Raw monitor-PD current should not cross the board before the current-sense resistor.",
    ),
    GeometryCheck(
        "monitor-pd",
        "Green monitor-PD raw path from LD3 to sense resistor",
        PadRef("LD3", "3"),
        PadRef("R46", "1"),
        25.0,
        "Raw monitor-PD current should not cross the board before the current-sense resistor.",
    ),
    GeometryCheck(
        "laser-current",
        "IR laser FET source to sense resistor",
        PadRef("Q1", "2"),
        PadRef("R18", "1"),
        3.0,
        "Laser current sense loop should be tight to avoid injecting error and current-loop noise.",
    ),
    GeometryCheck(
        "laser-current",
        "Red laser FET source to sense resistor",
        PadRef("Q2", "2"),
        PadRef("R23", "1"),
        3.0,
        "Laser current sense loop should be tight to avoid injecting error and current-loop noise.",
    ),
    GeometryCheck(
        "laser-current",
        "Green laser FET source to sense resistor",
        PadRef("Q3", "2"),
        PadRef("R28", "1"),
        3.0,
        "Laser current sense loop should be tight to avoid injecting error and current-loop noise.",
    ),
    GeometryCheck(
        "laser-current",
        "Blue laser FET source to sense resistor",
        PadRef("Q4", "2"),
        PadRef("R33", "1"),
        3.0,
        "Laser current sense loop should be tight to avoid injecting error and current-loop noise.",
    ),
)


def pad_point(
    geometry: dict[str, dict[str, object]],
    pad_ref: PadRef,
) -> tuple[float, float]:
    try:
        pads = geometry[pad_ref.ref]["pads"]  # type: ignore[index]
        point = pads[pad_ref.pad][0]  # type: ignore[index]
    except KeyError as exc:
        raise KeyError(f"missing pad {pad_ref.ref}.{pad_ref.pad}") from exc
    return float(point[0]), float(point[1])


def pad_net(
    pad_nets: dict[str, dict[str, str]],
    pad_ref: PadRef,
) -> str:
    return pad_nets.get(pad_ref.ref, {}).get(pad_ref.pad, "")


def main() -> int:
    board_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BOARD
    geometry = parse_footprint_geometry(board_path)
    pad_nets, _ = parse_board_pad_nets(board_path)

    failures: list[str] = []
    for check in CHECKS:
        try:
            ax, ay = pad_point(geometry, check.a)
            bx, by = pad_point(geometry, check.b)
        except KeyError as exc:
            failures.append(f"{check.category}: {check.title}: {exc}")
            continue
        distance = hypot(ax - bx, ay - by)
        net_a = pad_net(pad_nets, check.a) or "<unnetted>"
        net_b = pad_net(pad_nets, check.b) or "<unnetted>"
        if distance > check.max_mm:
            failures.append(
                f"[{check.category}] {check.title}: {distance:.2f} mm exceeds "
                f"{check.max_mm:.2f} mm; {check.a.ref}.{check.a.pad} ({net_a}) "
                f"at ({ax:.3f},{ay:.3f}) -> {check.b.ref}.{check.b.pad} ({net_b}) "
                f"at ({bx:.3f},{by:.3f}). {check.rationale}"
            )

    if failures:
        print(f"BLOCKED layout geometry review: {len(failures)} high-risk layout distances exceed targets")
        for failure in failures:
            print(f"  {failure}")
        return 2

    print(f"PASS layout geometry review: {len(CHECKS)} high-risk layout distances within targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
