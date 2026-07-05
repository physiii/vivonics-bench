#!/usr/bin/env python3
"""Verify that the passive first-article AVL lock matches the exported netlist."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from check_laser_controller_netlist import parse_components
from check_passive_derating import is_capacitor, is_resistor_or_trimmer


DEFAULT_NETLIST = Path("/tmp/lc.net")
DEFAULT_LOCK = Path(__file__).resolve().parent.parent / "docs" / "part-notes" / "passive-first-article-avl-lock.md"


def passive_counts(netlist_path: Path) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for component in parse_components(netlist_path):
        if is_capacitor(component) or is_resistor_or_trimmer(component):
            counts[(component["mpn"], component["lcsc"])] += 1
    return counts


def parse_lock_table(lock_text: str) -> dict[tuple[str, str], int]:
    rows: dict[tuple[str, str], int] = {}
    for line in lock_text.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        mpn_match = re.fullmatch(r"`([^`]+)`", cells[0])
        lcsc_match = re.fullmatch(r"`(C\d+)`", cells[1])
        if not mpn_match or not lcsc_match:
            continue
        try:
            count = int(cells[2])
        except ValueError:
            continue
        rows[(mpn_match.group(1), lcsc_match.group(1))] = count
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()

    failures: list[str] = []
    if not args.netlist.exists():
        failures.append(f"netlist file not found: {args.netlist}")
    if not args.lock.exists():
        failures.append(f"passive AVL lock file not found: {args.lock}")
    if failures:
        print("FAIL passive AVL lock")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    expected = passive_counts(args.netlist)
    actual = parse_lock_table(args.lock.read_text())
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    wrong_counts = sorted(
        key for key in set(expected) & set(actual)
        if expected[key] != actual[key]
    )
    if missing:
        failures.append("passive MPN/LCSC pairs missing from lock: " + ", ".join(f"{m}/{c}" for m, c in missing))
    if extra:
        failures.append("passive MPN/LCSC pairs in lock but not netlist: " + ", ".join(f"{m}/{c}" for m, c in extra))
    for key in wrong_counts:
        failures.append(f"{key[0]}/{key[1]} count mismatch: netlist={expected[key]} lock={actual[key]}")

    lock_text = args.lock.read_text()
    required_phrases = (
        "Quote-time lifecycle/stock check required",
        "Board-temperature measurement remains required",
        "Pulse/surge/current derating remains required",
        "Production release still needs current quote evidence",
    )
    for phrase in required_phrases:
        if phrase not in lock_text:
            failures.append(f"lock missing production-risk phrase: {phrase}")

    if failures:
        print("FAIL passive AVL lock")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS passive AVL lock: "
        f"{len(expected)} passive MPN/LCSC pairs and {sum(expected.values())} placements match "
        f"{args.lock}; quote-time lifecycle/stock and board-temperature evidence remain required."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
