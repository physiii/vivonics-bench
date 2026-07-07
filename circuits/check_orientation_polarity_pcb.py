#!/usr/bin/env python3
"""Hard orientation/polarity gates for release-critical assembled parts.

This check exists because schematic/netlist correctness is not enough for SMT
assembly: a mirrored footprint can preserve numeric pad-to-net assignments while
placing every real package lead on the wrong copper.  The contracts below check
physical pad geometry against datasheet top-view pin order.
"""
from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path


OPA380_SOURCE = "TI OPA380 datasheet, Pin Assignments, SO-8/MSOP-8 top view"
PAD_TOL_MM = 0.006


@dataclass(frozen=True)
class Opa380Contract:
    ref: str
    channel: str
    vout: str


@dataclass(frozen=True)
class PotContract:
    ref: str
    value: str
    lcsc: str
    expected_nets: dict[str, str]


OPA380_CONTRACTS = (
    Opa380Contract("U1", "IR", "VOUT1"),
    Opa380Contract("U2", "RED", "VOUT2"),
    Opa380Contract("U3", "GREEN", "VOUT3"),
    Opa380Contract("U4", "BLUE", "VOUT4"),
)

POT_CONTRACTS = (
    PotContract(
        "RV1",
        "VBIAS 10k",
        "C81348",
        {"1": "/TIA_IR/VBIAS_TOP", "2": "/TIA_IR/VBIAS_WIPER", "3": "GND"},
    ),
    PotContract(
        "RV2",
        "VBIAS 10k",
        "C81348",
        {"1": "/TIA_RED/VBIAS_TOP", "2": "/TIA_RED/VBIAS_WIPER", "3": "GND"},
    ),
    PotContract(
        "RV3",
        "VBIAS 10k",
        "C81348",
        {"1": "/TIA_GREEN/VBIAS_TOP", "2": "/TIA_GREEN/VBIAS_WIPER", "3": "GND"},
    ),
    PotContract(
        "RV4",
        "VBIAS 10k",
        "C81348",
        {"1": "/TIA_BLUE/VBIAS_TOP", "2": "/TIA_BLUE/VBIAS_WIPER", "3": "GND"},
    ),
    PotContract(
        "RV5",
        "RF 2M",
        "C116323",
        {"1": "/TIA_IR/PD_ANODE", "2": "VOUT1", "3": "VOUT1"},
    ),
    PotContract(
        "RV6",
        "RF 2M",
        "C116323",
        {"1": "/TIA_RED/PD_ANODE", "2": "VOUT2", "3": "VOUT2"},
    ),
    PotContract(
        "RV7",
        "RF 2M",
        "C116323",
        {"1": "/TIA_GREEN/PD_ANODE", "2": "VOUT3", "3": "VOUT3"},
    ),
    PotContract(
        "RV8",
        "RF 2M",
        "C116323",
        {"1": "/TIA_BLUE/PD_ANODE", "2": "VOUT4", "3": "VOUT4"},
    ),
)

EXPECTED_OPA380_LOCAL = {
    "1": (-2.475, -1.905),
    "2": (-2.475, -0.635),
    "3": (-2.475, 0.635),
    "4": (-2.475, 1.905),
    "5": (2.475, 1.905),
    "6": (2.475, 0.635),
    "7": (2.475, -0.635),
    "8": (2.475, -1.905),
}

EXPECTED_3224W_LOCAL = {
    "1": (1.25, -1.45),
    "2": (0.0, 1.45),
    "3": (-1.25, -1.45),
}


def balanced_blocks(text: str, prefix: str) -> list[str]:
    blocks: list[str] = []
    index = 0
    while True:
        start = text.find(prefix, index)
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
        blocks.append(text[start:end])
        index = end
    return blocks


def ref_of(block: str) -> str | None:
    match = re.search(r'\(property "Reference" "([^"]+)"', block)
    return match.group(1) if match else None


def value_of(block: str) -> str:
    match = re.search(r'\(property "Value" "([^"]+)"', block)
    return match.group(1) if match else ""


def property_of(block: str, name: str) -> str:
    match = re.search(rf'\(property "{re.escape(name)}" "([^"]*)"', block)
    return match.group(1) if match else ""


def footprint_id(block: str) -> str:
    match = re.match(r'\(footprint\s+"?([^"\s\)]+)"?', block)
    return match.group(1) if match else ""


def footprint_at(block: str) -> tuple[float, float, float]:
    match = re.search(r"\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+([-0-9.]+))?\)", block)
    if not match:
        raise ValueError("footprint missing at")
    return float(match.group(1)), float(match.group(2)), float(match.group(3) or 0.0)


def rotate_point(x: float, y: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return x * math.cos(radians) + y * math.sin(radians), -x * math.sin(radians) + y * math.cos(radians)


def pad_map(block: str) -> dict[str, dict[str, object]]:
    pads: dict[str, dict[str, object]] = {}
    fp_x, fp_y, fp_rot = footprint_at(block)
    for pad in balanced_blocks(block, "(pad "):
        number = re.match(r'\(pad\s+"?([^"\s\)]+)"?', pad)
        at = re.search(r"\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+[-0-9.]+)?\)", pad)
        if not number or not at:
            continue
        local = float(at.group(1)), float(at.group(2))
        dx, dy = rotate_point(local[0], local[1], fp_rot)
        net = re.search(r'\(net\s+"([^"]+)"\)', pad)
        pads[number.group(1)] = {
            "local": local,
            "global": (fp_x + dx, fp_y + dy),
            "net": net.group(1) if net else "",
        }
    return pads


def nearly_equal(actual: tuple[float, float], expected: tuple[float, float]) -> bool:
    return math.hypot(actual[0] - expected[0], actual[1] - expected[1]) <= PAD_TOL_MM


def expected_opa380_nets(contract: Opa380Contract) -> dict[str, str]:
    return {
        "1": "",
        "2": f"/TIA_{contract.channel}/PD_ANODE",
        "3": f"/TIA_{contract.channel}/VBIAS",
        "4": "GND",
        "5": "",
        "6": contract.vout,
        "7": "+5V",
        "8": "",
    }


def check_opa380(blocks_by_ref: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for contract in OPA380_CONTRACTS:
        block = blocks_by_ref.get(contract.ref)
        if block is None:
            errors.append(f"{contract.ref}: OPA380 footprint missing")
            continue
        if footprint_id(block) != "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm":
            errors.append(f"{contract.ref}: unexpected footprint {footprint_id(block)!r}")
        if value_of(block) != "OPA380AID" or property_of(block, "LCSC") != "C201677":
            errors.append(
                f"{contract.ref}: expected OPA380AID/C201677, got value={value_of(block)!r} "
                f"LCSC={property_of(block, 'LCSC')!r}"
            )
        _, _, rotation = footprint_at(block)
        if abs((rotation % 360.0) - 180.0) > 0.001:
            errors.append(f"{contract.ref}: expected repaired 180 degree package orientation, got {rotation:g}")

        pads = pad_map(block)
        expected_nets = expected_opa380_nets(contract)
        for pin, expected_local in EXPECTED_OPA380_LOCAL.items():
            actual = pads.get(pin)
            if actual is None:
                errors.append(f"{contract.ref}.{pin}: pad missing")
                continue
            if not nearly_equal(actual["local"], expected_local):  # type: ignore[arg-type]
                errors.append(
                    f"{contract.ref}.{pin}: mirrored/wrong local pad coordinate "
                    f"{actual['local']}, expected {expected_local} from stock SOIC-8 geometry"
                )
            actual_net = actual["net"]
            if actual_net != expected_nets[pin]:
                errors.append(
                    f"{contract.ref}.{pin}: expected net {expected_nets[pin] or 'NC'}, got {actual_net or 'NC'}"
                )

        if all(pin in pads for pin in EXPECTED_OPA380_LOCAL):
            y = {pin: pads[pin]["global"][1] for pin in EXPECTED_OPA380_LOCAL}  # type: ignore[index]
            x = {pin: pads[pin]["global"][0] for pin in EXPECTED_OPA380_LOCAL}  # type: ignore[index]
            # With the actual package rotated 180 degrees on this board, TI top-view pin 1 is
            # physically bottom-right and pin 4 is top-right.  This is a rotation, not a mirror.
            if not (x["4"] > x["5"] and y["4"] < y["3"] < y["2"] < y["1"]):
                errors.append(
                    f"{contract.ref}: right-side physical order must be 4,3,2,1 top-to-bottom "
                    f"for the 180 degree {OPA380_SOURCE}"
                )
            if not (x["5"] < x["4"] and y["5"] < y["6"] < y["7"] < y["8"]):
                errors.append(
                    f"{contract.ref}: left-side physical order must be 5,6,7,8 top-to-bottom "
                    f"for the 180 degree {OPA380_SOURCE}"
                )
    return errors


def check_bourns_3224w(blocks_by_ref: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for contract in POT_CONTRACTS:
        block = blocks_by_ref.get(contract.ref)
        if block is None:
            errors.append(f"{contract.ref}: Bourns 3224W footprint missing")
            continue
        if footprint_id(block) != "Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical":
            errors.append(f"{contract.ref}: unexpected footprint {footprint_id(block)!r}")
        if value_of(block) != contract.value or property_of(block, "LCSC") != contract.lcsc:
            errors.append(
                f"{contract.ref}: expected {contract.value}/{contract.lcsc}, got "
                f"value={value_of(block)!r} LCSC={property_of(block, 'LCSC')!r}"
            )
        pads = pad_map(block)
        for pin, expected_local in EXPECTED_3224W_LOCAL.items():
            actual = pads.get(pin)
            if actual is None:
                errors.append(f"{contract.ref}.{pin}: pad missing")
                continue
            if not nearly_equal(actual["local"], expected_local):  # type: ignore[arg-type]
                errors.append(
                    f"{contract.ref}.{pin}: mirrored/wrong local pad coordinate "
                    f"{actual['local']}, expected {expected_local} from Bourns 3224W footprint geometry"
                )
            actual_net = actual["net"]
            expected_net = contract.expected_nets[pin]
            if actual_net != expected_net:
                errors.append(f"{contract.ref}.{pin}: expected net {expected_net}, got {actual_net or 'NC'}")
        if all(pin in pads for pin in EXPECTED_3224W_LOCAL):
            y1 = pads["1"]["local"][1]  # type: ignore[index]
            y2 = pads["2"]["local"][1]  # type: ignore[index]
            y3 = pads["3"]["local"][1]  # type: ignore[index]
            if not (y1 < 0 and y3 < 0 and y2 > 0):
                errors.append(
                    f"{contract.ref}: Bourns 3224W physical order must put pin 2/wiper on the opposite "
                    "side from pins 1 and 3, matching the datasheet/stock footprint"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=Path("circuits/laser_controller.kicad_pcb"))
    args = parser.parse_args()

    text = args.board.read_text()
    blocks_by_ref = {
        ref: block
        for block in balanced_blocks(text, "(footprint ")
        if (ref := ref_of(block))
    }
    errors = check_opa380(blocks_by_ref)
    errors.extend(check_bourns_3224w(blocks_by_ref))
    if errors:
        print("FAIL orientation/polarity PCB gate:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        "PASS orientation/polarity PCB gate: U1-U4 OPA380AID SOIC-8 physical pad order and "
        "RV1-RV8 Bourns 3224W wiper geometry/nets match their datasheet footprint contracts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
