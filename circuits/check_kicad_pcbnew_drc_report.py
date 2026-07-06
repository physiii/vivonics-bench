#!/usr/bin/env python3
"""Generate and validate a headless KiCad PCB DRC report.

This is still not schematic ERC or native schematic-parity DRC. It is a
stronger PCB-rule artifact than the custom parser gates and keeps documented
warning-only findings visible.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
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


def run_kicad_drc(board: Path, report: Path) -> subprocess.CompletedProcess[str]:
    kicad_cli = shutil.which("kicad-cli") or "/usr/bin/kicad-cli"
    command = [
        kicad_cli,
        "pcb",
        "drc",
        "--refill-zones",
        "--all-track-errors",
        "--format",
        "report",
        "--output",
        str(report),
        str(board),
    ]
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    if not args.board.exists():
        raise SystemExit(f"board file not found: {args.board}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    result = run_kicad_drc(args.board, args.report)
    if result.returncode != 0:
        print("FAIL headless KiCad DRC: kicad-cli pcb drc failed")
        print(result.stdout.strip())
        return 1

    report_text = args.report.read_text(errors="replace")
    findings = parse_findings(report_text)
    drc_violations = extract_count(report_text, "DRC violations")
    unconnected = extract_count(report_text, "unconnected pads")
    footprint_errors = extract_count(report_text, "Footprint errors")

    failures: list[str] = []
    if drc_violations != 0:
        failures.append(f"expected 0 DRC violations, got {drc_violations}")
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
        print("FAIL headless KiCad DRC report")
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
        "PASS headless KiCad DRC report: "
        f"zones refilled, DRC violations=0, unconnected pads=0, footprint errors=0, "
        f"allowed warning findings: {allowed_summary}; report={args.report}"
    )
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
