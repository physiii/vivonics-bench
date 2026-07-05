#!/usr/bin/env python3
"""Generate and validate a headless Pcbnew DRC report.

KiCad 7.0.11's `kicad-cli` package in this environment exposes only
schematic/PCB export commands, but the system Python package includes KiCad's
`pcbnew` module. This checker uses that module to refill zones in memory and
write a native Pcbnew DRC report for the current board.

This is still not schematic ERC or native schematic-parity DRC. It is a
stronger PCB-rule artifact than the custom parser gates and keeps documented
warning-only findings visible.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_REPORT = (
    Path(__file__).resolve().parent
    / "review"
    / "generated"
    / "laser_controller_pcbnew_drc_report.rpt"
)
ALLOWED_WARNING_CODES = {"courtyards_overlap"}


@dataclass(frozen=True)
class DrcFinding:
    code: str
    severity: str
    header: str


def ensure_pcbnew():
    try:
        import pcbnew  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pcbnew Python module not available. Run this checker with system "
            "Python, e.g. `/usr/bin/python3 circuits/check_kicad_pcbnew_drc_report.py`."
        ) from exc
    return pcbnew


def parse_findings(report_text: str) -> list[DrcFinding]:
    findings: list[DrcFinding] = []
    current_code: str | None = None
    current_header = ""
    for line in report_text.splitlines():
        match = re.match(r"^\[([^]]+)\]:\s+(.*)$", line)
        if match:
            current_code = match.group(1)
            current_header = match.group(2)
            continue
        if current_code and "Severity:" in line:
            severity_match = re.search(r"Severity:\s*([A-Za-z]+)", line)
            severity = severity_match.group(1).lower() if severity_match else "unknown"
            findings.append(DrcFinding(current_code, severity, current_header))
            current_code = None
            current_header = ""
    return findings


def extract_count(report_text: str, label: str) -> int | None:
    match = re.search(rf"\*\* Found (\d+) {re.escape(label)} \*\*", report_text)
    if not match:
        return None
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    if not args.board.exists():
        raise SystemExit(f"board file not found: {args.board}")

    pcbnew = ensure_pcbnew()
    board = pcbnew.LoadBoard(str(args.board))
    zones = board.Zones()
    fill_ok = pcbnew.ZONE_FILLER(board).Fill(zones)
    if not fill_ok:
        print("FAIL headless Pcbnew DRC: zone refill failed")
        return 1

    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_ok = pcbnew.WriteDRCReport(
        board,
        str(args.report),
        pcbnew.EDA_UNITS_MILLIMETRES,
        True,
    )
    if not write_ok:
        print(f"FAIL headless Pcbnew DRC: could not write report {args.report}")
        return 1

    report_text = args.report.read_text(errors="replace")
    findings = parse_findings(report_text)
    unconnected = extract_count(report_text, "unconnected pads")
    footprint_errors = extract_count(report_text, "Footprint errors")

    failures: list[str] = []
    if unconnected != 0:
        failures.append(f"expected 0 unconnected pads, got {unconnected}")
    if footprint_errors != 0:
        failures.append(f"expected 0 footprint errors, got {footprint_errors}")

    unexpected = [
        finding
        for finding in findings
        if finding.code not in ALLOWED_WARNING_CODES or finding.severity != "warning"
    ]
    if unexpected:
        for finding in unexpected:
            failures.append(
                f"unexpected native DRC finding [{finding.code}] severity={finding.severity}: "
                f"{finding.header}"
            )

    if failures:
        print("FAIL headless Pcbnew DRC report")
        for failure in failures:
            print(f"  - {failure}")
        print(f"  report: {args.report}")
        return 1

    allowed_counts: dict[str, int] = {}
    for finding in findings:
        allowed_counts[finding.code] = allowed_counts.get(finding.code, 0) + 1
    allowed_summary = ", ".join(f"{code}={count}" for code, count in sorted(allowed_counts.items()))
    if not allowed_summary:
        allowed_summary = "none"
    print(
        "PASS headless Pcbnew DRC report: "
        f"zones refilled in memory, unconnected pads=0, footprint errors=0, "
        f"allowed warning findings: {allowed_summary}; report={args.report}"
    )
    print(f"  KiCad pcbnew build: {pcbnew.GetBuildVersion()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
