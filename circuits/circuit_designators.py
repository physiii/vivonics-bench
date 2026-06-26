"""Canonical schematic designators for the generated laser controller.

The route/check code intentionally talks in logical per-sheet names such as
`LASER_GREEN` / `R12`.  KiCad netlists and fabrication artifacts must use
globally unique references.  This module is the only translation table between
those two views.
"""
from __future__ import annotations

from collections import defaultdict


WL = ["IR", "RED", "GREEN", "BLUE"]

TIA_REF_MAP = {
    "TIA_IR": {
        "D1": "D1",
        "U1": "U1",
        "R2": "R1",
        "C1": "C1",
        "C2": "C2",
        "RB": "R2",
        "CB": "C3",
        "R1": "R3",
        "C11": "C4",
        "RV11": "RV1",
        "RT": "R4",
    },
    "TIA_RED": {
        "D1": "D2",
        "U1": "U2",
        "R2": "R5",
        "C1": "C5",
        "C2": "C6",
        "RB": "R6",
        "CB": "C7",
        "R1": "R7",
        "C11": "C8",
        "RV11": "RV2",
        "RT": "R8",
    },
    "TIA_GREEN": {
        "D1": "D3",
        "U1": "U3",
        "R2": "R9",
        "C1": "C9",
        "C2": "C10",
        "RB": "R10",
        "CB": "C11",
        "R1": "R11",
        "C11": "C12",
        "RV11": "RV3",
        "RT": "R12",
    },
    "TIA_BLUE": {
        "D1": "D4",
        "U1": "U4",
        "R2": "R13",
        "C1": "C13",
        "C2": "C14",
        "RB": "R14",
        "CB": "C15",
        "R1": "R15",
        "C11": "C16",
        "RV11": "RV4",
        "RT": "R16",
    },
}

LASER_REF_MAP = {
    "LASER_IR": {
        "LD": "LD1",
        "U11": "U5",
        "R31": "R17",
        "Q1": "Q1",
        "R11": "R18",
        "R12": "R19",
        "C22": "C17",
        "R21": "R20",
        "R22": "R21",
        "C21": "C18",
        "CC": "C19",
    },
    "LASER_RED": {
        "LD": "LD2",
        "U11": "U6",
        "R31": "R22",
        "Q1": "Q2",
        "R11": "R23",
        "R12": "R24",
        "C22": "C20",
        "R21": "R25",
        "R22": "R26",
        "C21": "C21",
        "CC": "C22",
    },
    "LASER_GREEN": {
        "LD": "LD3",
        "U11": "U7",
        "R31": "R27",
        "Q1": "Q3",
        "R11": "R28",
        "R12": "R29",
        "C22": "C23",
        "R21": "R30",
        "R22": "R31",
        "C21": "C24",
        "CC": "C25",
    },
    "LASER_BLUE": {
        "LD": "LD4",
        "U11": "U8",
        "R31": "R32",
        "Q1": "Q4",
        "R11": "R33",
        "R12": "R34",
        "C22": "C26",
        "R21": "R35",
        "R22": "R36",
        "C21": "C27",
        "CC": "C28",
    },
}

MCU_REF_MAP = {
    "J6": "J1",
    "J3": "J2",
    "U9": "U9",
    "U12": "U10",
    "U10": "U11",
    "RUSBM": "R37",
    "RUSBP": "R38",
    "REN": "R39",
    "RBOOT": "R40",
    "C44": "C29",
    "C41": "C30",
    "C42": "C31",
    "C43": "C32",
    "CEN": "C33",
}

POWER_REF_MAP = {
    "J1": "J3",
    "J4": "J4",
    "J5": "J5",
    "J2": "J6",
    "D10": "D5",
    "D11": "D6",
    "C50": "C34",
    "UMPD": "U12",
    "UREF": "U13",
    "CINA": "C35",
    "CREF": "C36",
    "RBIAS": "R41",
    "RMPD1": "R42",
    "RADC1": "R43",
    "CMPD1": "C37",
    "RMPD2": "R44",
    "RADC2": "R45",
    "CMPD2": "C38",
    "RMPD3": "R46",
    "RADC3": "R47",
    "CMPD3": "C39",
    "RMPD4": "R48",
    "RADC4": "R49",
    "CMPD4": "C40",
}

LOCAL_TO_ACTUAL = {
    **TIA_REF_MAP,
    **LASER_REF_MAP,
    "MCU_ESP32-S3": MCU_REF_MAP,
    "POWER_IO": POWER_REF_MAP,
}

ACTUAL_TO_LOCAL: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
for sheet, refs in LOCAL_TO_ACTUAL.items():
    for local_ref, actual_ref in refs.items():
        ACTUAL_TO_LOCAL[sheet][actual_ref].append(local_ref)


def normalize_sheet(sheet: str) -> str:
    return sheet.strip("/")


def ref_for(sheet: str, local_ref: str) -> str:
    normalized = normalize_sheet(sheet)
    return LOCAL_TO_ACTUAL.get(normalized, {}).get(local_ref, local_ref)


def aliases_for_actual(sheet: str, actual_ref: str) -> list[str]:
    normalized = normalize_sheet(sheet)
    return list(ACTUAL_TO_LOCAL.get(normalized, {}).get(actual_ref, []))


def actualize_parts(sheet: str, parts: dict[str, tuple]) -> dict[str, tuple]:
    return {ref_for(sheet, ref): value for ref, value in parts.items()}
