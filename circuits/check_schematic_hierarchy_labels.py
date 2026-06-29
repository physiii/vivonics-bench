#!/usr/bin/env python3
"""Schematic hierarchy and label guardrails for the bench laser controller.

This catches the class of regression where a generated sheet interface is
quietly changed, a child sheet gets an accidental global label, or root global
labels no longer match the intended board-level interconnect whitelist.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from circuit_designators import WL


PROJECT_DIR = Path(__file__).resolve().parent
ROOT = PROJECT_DIR / "laser_controller.kicad_sch"


TIA_CHILD_LABELS = {"V_OUT": "output"}
LASER_CHILD_LABELS = {"PWM_IN": "input", "LASER_N": "output", "ISENSE": "output", "MPD_RAW": "output"}
LASER_BLUE_CHILD_LABELS = {"PWM_IN": "input", "LASER_N": "output", "ISENSE": "output"}
MCU_CHILD_LABELS = {
    "IO47": "input",
    "IO38": "input",
    "IO17": "output",
    "IO48": "output",
    "IO18": "output",
    "IO21": "input",
    "IO9": "input",
    "IO10": "output",
    "I2C_DATA": "input",
    "IO6": "input",
    "IO8": "input",
    "IO11": "output",
    "IO16": "output",
    "I2C_CLK": "input",
    "IO15": "output",
    "IO7": "input",
    "3V3": "input",
    "IO2": "input",
    "IO12": "output",
    "IO5": "input",
    "5V": "output",
    "IO4": "input",
    "IO3": "input",
}
MCU_ROOT_PINS = {
    "IO10": "output",
    "IO11": "output",
    "IO12": "output",
    "IO16": "output",
    "IO4": "input",
    "IO5": "input",
    "IO6": "input",
    "IO7": "input",
    "IO2": "input",
    "IO3": "input",
    "IO8": "input",
    "IO9": "input",
    "IO15": "output",
    "5V": "output",
    "3V3": "input",
    "IO17": "output",
    "IO18": "output",
    "IO21": "input",
    "IO38": "input",
    "IO47": "input",
    "IO48": "output",
}
POWER_IO_CHILD_LABELS = {
    **{f"VOUT{i}": "input" for i in range(1, 5)},
    "CONVST": "input",
    "VBUS_5V": "input",
    "ADC_SCLK": "input",
    "ADC_CS": "input",
    "ADC_MISO_A": "output",
    "ADC_MISO_B": "output",
    "ADC_BUSY": "output",
    "ADC_RESET": "input",
    **{f"MPD_RAW{i}": "input" for i in range(1, 5)},
    **{f"MPD{i}": "output" for i in range(1, 5)},
}


EXPECTED_CHILD_LABELS = {
    **{f"tia_{color.lower()}.kicad_sch": TIA_CHILD_LABELS for color in WL},
    **{
        f"laser_{color.lower()}.kicad_sch": (
            LASER_BLUE_CHILD_LABELS if color == "BLUE" else LASER_CHILD_LABELS
        )
        for color in WL
    },
    "mcu.kicad_sch": MCU_CHILD_LABELS,
    "power_io.kicad_sch": POWER_IO_CHILD_LABELS,
}


EXPECTED_ROOT_SHEETS = {
    **{
        f"TIA_{color}": (f"tia_{color.lower()}.kicad_sch", TIA_CHILD_LABELS)
        for color in WL
    },
    **{
        f"LASER_{color}": (
            f"laser_{color.lower()}.kicad_sch",
            LASER_BLUE_CHILD_LABELS if color == "BLUE" else LASER_CHILD_LABELS,
        )
        for color in WL
    },
    "MCU_ESP32-S3": ("mcu.kicad_sch", MCU_ROOT_PINS),
    "POWER_IO": ("power_io.kicad_sch", POWER_IO_CHILD_LABELS),
}


EXPECTED_ROOT_GLOBAL_COUNTS = Counter(
    {
        **{f"VOUT{i}": 2 for i in range(1, 5)},
        **{f"PWM{i}": 2 for i in range(1, 5)},
        **{f"ISENSE{i}": 2 for i in range(1, 5)},
        **{f"LASER_N{i}": 1 for i in range(1, 5)},
        **{f"MPD_RAW{i}": 2 for i in range(1, 4)},
        "MPD_RAW4": 1,
        **{f"MPD{i}": 2 for i in range(1, 5)},
        "CONVST": 2,
        "VBUS_5V": 2,
        "+3V3": 1,
        "ADC_SCLK": 2,
        "ADC_CS": 2,
        "ADC_MISO_A": 2,
        "ADC_MISO_B": 2,
        "ADC_BUSY": 2,
        "ADC_RESET": 2,
    }
)


LOCAL_LABEL_DENYLIST = set(EXPECTED_ROOT_GLOBAL_COUNTS)
ALLOWED_LOCAL_LABEL_COLLISIONS = {
    "power_io.kicad_sch": {f"MPD_RAW{i}" for i in range(1, 5)},
}

SCHEMATIC_TEXT_DENYLIST = {
    "mcu.kicad_sch": {
        "USBLC6": "copied MCU sheet uses discrete ESD diodes, not USBLC6",
        "22R series": "copied MCU sheet has no USB data-line series resistors",
        "UART/EN/BOOT -> J": "copied MCU sheet has local reset/program/factory buttons and CP2102N USB-UART",
        "exposed on J": "GPIO0/EN are local button nets, not a bring-up header",
    },
    "power_io.kicad_sch": {
        "J2 = ext +5V": "external 5 V final schematic header reference is J6",
        "J2 OR-ed": "external 5 V final schematic header reference is J6",
        "D10/D11": "5 V OR-ing diode final schematic references are D5/D6",
    },
}


def block_iter(text: str, prefix: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in text.splitlines():
        if not in_block and line.lstrip().startswith(prefix):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            if depth == 0:
                blocks.append(line)
                in_block = False
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def root_sheets(root_text: str) -> dict[str, tuple[str, dict[str, str]]]:
    sheets: dict[str, tuple[str, dict[str, str]]] = {}
    for block in block_iter(root_text, "(sheet "):
        name_match = re.search(r'\(property "Sheetname" "([^"]+)"', block)
        file_match = re.search(r'\(property "Sheetfile" "([^"]+)"', block)
        if not name_match or not file_match:
            continue
        pins = dict(re.findall(r'\(pin "([^"]+)"\s+(\w+)\s+\(at ', block))
        sheets[name_match.group(1)] = (file_match.group(1), pins)
    return sheets


def labels_of(kind: str, text: str) -> list[str]:
    return re.findall(rf'\({kind} "([^"]+)"', text)


def hierarchical_labels_with_shapes(text: str) -> dict[str, str]:
    return dict(re.findall(r'\(hierarchical_label "([^"]+)" \(shape (\w+)\)', text))


def main() -> int:
    root_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    root_dir = root_path.resolve().parent
    failures: list[str] = []

    root_text = root_path.read_text()
    sheets = root_sheets(root_text)
    if sheets != EXPECTED_ROOT_SHEETS:
        failures.append(f"root sheet interface mismatch: got {sheets}, expected {EXPECTED_ROOT_SHEETS}")

    global_counts = Counter(labels_of("global_label", root_text))
    if global_counts != EXPECTED_ROOT_GLOBAL_COUNTS:
        failures.append(
            f"root global-label whitelist mismatch: got {dict(global_counts)}, "
            f"expected {dict(EXPECTED_ROOT_GLOBAL_COUNTS)}"
        )

    root_hierarchical_labels = labels_of("hierarchical_label", root_text)
    if root_hierarchical_labels:
        failures.append(f"root sheet should not contain hierarchical labels: {root_hierarchical_labels}")

    for child_file, expected_labels in sorted(EXPECTED_CHILD_LABELS.items()):
        path = root_dir / child_file
        if not path.exists():
            failures.append(f"missing child sheet {child_file}")
            continue
        text = path.read_text()
        child_globals = labels_of("global_label", text)
        if child_globals:
            failures.append(f"{child_file} contains accidental global labels: {child_globals}")
        child_labels = hierarchical_labels_with_shapes(text)
        if child_labels != expected_labels:
            failures.append(
                f"{child_file} hierarchical labels mismatch: got {child_labels}, "
                f"expected {expected_labels}"
            )
        allowed_local_collisions = ALLOWED_LOCAL_LABEL_COLLISIONS.get(child_file, set())
        local_label_collisions = sorted(
            (set(labels_of("label", text)) & LOCAL_LABEL_DENYLIST) - allowed_local_collisions
        )
        if local_label_collisions:
            failures.append(
                f"{child_file} uses board-level global names as local labels: {local_label_collisions}"
            )
        for denied, reason in sorted(SCHEMATIC_TEXT_DENYLIST.get(child_file, {}).items()):
            if denied in text:
                failures.append(f"{child_file} schematic text uses stale local designator `{denied}`: {reason}")

    if failures:
        print(f"FAIL {len(failures)} schematic hierarchy/label checks")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS schematic hierarchy/label guardrails: "
        f"{len(EXPECTED_ROOT_SHEETS)} root sheets, "
        f"{sum(EXPECTED_ROOT_GLOBAL_COUNTS.values())} whitelisted root global labels, "
        f"{sum(len(labels) for labels in EXPECTED_CHILD_LABELS.values())} child hierarchical labels, "
        "typed sheet pins, zero child-sheet global labels, and checked schematic annotation designators"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
