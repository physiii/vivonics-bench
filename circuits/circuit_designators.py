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
        "RVFB": "RV5",
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
        "RVFB": "RV6",
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
        "RVFB": "RV7",
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
        "RVFB": "RV8",
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
    ref: ref
    for ref in [
        "C41", "C42", "C43", "C44", "C45", "C46", "C47",
        "D7", "D8", "D9", "D10", "D11", "D12", "D13", "D14",
        "J1", "J2",
        "Q5", "Q6",
        "R50", "R51", "R52", "R53", "R54", "R55", "R56", "R57", "R58", "R59", "R60",
        "SW1", "SW2", "SW3",
        "U9", "U10",
    ]
}

POWER_REF_MAP = {
    "JDC": "J5",
    "CIN12A": "C61",
    "CIN12B": "C62",
    "U5V": "U15",
    "L5V": "L1",
    "CBST5V": "C63",
    "C5VOUT1": "C64",
    "C5VOUT2": "C65",
    "ULASER": "U16",
    "LLASER": "L2",
    "CBSTLASER": "C66",
    "CLASEROUT1": "C67",
    "CLASEROUT2": "C68",
    "RFBTOP": "R61",
    "RFBBOT": "R62",
    "CFFLASER": "C69",
    "UADC": "U14",
    "CADCAV1": "C51",
    "CADCAV2": "C52",
    "CADCAV3": "C53",
    "CADCAV4": "C54",
    "CADCDRV": "C55",
    "CADCBULK": "C56",
    "CREG1": "C57",
    "CREG2": "C58",
    "CREFIN": "C59",
    "CREFCAP": "C60",
    "D10": "D5",
    "D11": "D6",
    "C50": "C34",
    "U3V3": "U11",
    "C3V3IN": "C48",
    "C3V3OUT": "C49",
    "C3V3BULK": "C50",
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
