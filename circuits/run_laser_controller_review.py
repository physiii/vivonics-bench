#!/usr/bin/env python3
"""Run the available bench laser-controller review gates.

This wrapper is intentionally explicit about what it proves and what it cannot
prove in this environment.  It runs the custom source, netlist, PCB, generated
copper, thermal, open-release-blocker, and availability gates.  It also attempts
KiCad ERC/DRC and marks them as release blockers when the installed KiCad CLI
does not expose those commands. Use --release to make blockers produce a
nonzero exit code.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
CIRCUITS_DIR = REPO_DIR / "circuits"
REPORT_DIR = CIRCUITS_DIR / "review" / "generated"
REPORT_PATH = REPORT_DIR / "laser_controller_review_gate.md"
NETLIST_PATH = Path("/tmp/lc.net")
POS_PATH = Path("/tmp/lc_pos.csv")
GENERATED_PCB_PATH = Path("/tmp/lc_generated_staging.kicad_pcb")
REPORT_OUTPUT_TAIL_CHARS = 12000


@dataclass
class StepResult:
    name: str
    command: list[str]
    status: str
    returncode: int
    output: str
    note: str = ""


def run_step(
    name: str,
    command: list[str],
    *,
    expected_codes: set[int] | None = None,
    blocked_codes: set[int] | None = None,
    blocked_note: str = "",
    unavailable_if_export_only: bool = False,
) -> StepResult:
    expected_codes = expected_codes or {0}
    blocked_codes = blocked_codes or set()
    completed = subprocess.run(
        command,
        cwd=REPO_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout.strip()
    if completed.returncode in expected_codes:
        return StepResult(name, command, "PASS", completed.returncode, output)
    if completed.returncode in blocked_codes:
        return StepResult(name, command, "BLOCKED", completed.returncode, output, blocked_note)
    if unavailable_if_export_only and (
        "Subcommands:" in output and "export" in output and "erc" not in output and "drc" not in output
    ):
        return StepResult(
            name,
            command,
            "BLOCKED",
            completed.returncode,
            output,
            "Installed KiCad CLI exposes only export here; run KiCad GUI ERC/DRC or a fuller KiCad CLI before fabrication.",
        )
    return StepResult(name, command, "FAIL", completed.returncode, output)


def command_text(command: list[str]) -> str:
    return " ".join(command)


def write_report(results: list[StepResult], release_blocked: bool) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Laser Controller Review Gate",
        "",
        f"Generated: {now}",
        "",
        "This is a generated local audit artifact. It proves only the checks listed below.",
        "Fabrication remains blocked if any row is `FAIL` or `BLOCKED`.",
        "",
        f"Overall release status: {'BLOCKED' if release_blocked else 'AVAILABLE_GATES_PASS'}",
        "",
        "| Status | Step | Return | Command |",
        "|---|---|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.status} | {result.name} | {result.returncode} | `{command_text(result.command)}` |"
        )
    lines.append("")
    for result in results:
        lines.append(f"## {result.status}: {result.name}")
        lines.append("")
        lines.append(f"Command: `{command_text(result.command)}`")
        if result.note:
            lines.append("")
            lines.append(result.note)
        if result.output:
            lines.append("")
            lines.append("```text")
            lines.extend(line.rstrip() for line in result.output[-REPORT_OUTPUT_TAIL_CHARS:].splitlines())
            lines.append("```")
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    REPORT_PATH.write_text("\n".join(line.rstrip() for line in lines) + "\n")


def normalize_existing_report() -> None:
    if not REPORT_PATH.exists():
        return
    lines = [line.rstrip() for line in REPORT_PATH.read_text().splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release",
        action="store_true",
        help="Return nonzero when full release gates are blocked, including open blockers or missing KiCad ERC/DRC.",
    )
    args = parser.parse_args()
    normalize_existing_report()

    py_files = [
        "circuits/run_laser_controller_review.py",
        "circuits/gen_laser_controller.py",
        "circuits/adapt_mcu.py",
        "circuits/gen_pcb.py",
        "circuits/pcb_critical_routes.py",
        "circuits/check_laser_controller_netlist.py",
        "circuits/check_laser_controller_pcb.py",
        "circuits/check_pcb_staging.py",
        "circuits/check_laser_controller_release_gate.py",
        "circuits/check_laser_controller_release_readiness.py",
        "circuits/check_schematic_hierarchy_labels.py",
        "circuits/check_schematic_presentation.py",
        "circuits/check_power_thermal_budget.py",
        "circuits/check_laser_current_budget.py",
        "circuits/check_laser_monitor_pd_budget.py",
        "circuits/check_passive_derating.py",
        "circuits/generate_laser_controller_audit_tables.py",
        "circuits/circuit_designators.py",
        "circuits/check_laser_controller_sources.py",
        "circuits/check_part_notes_completeness.py",
        "circuits/check_source_documents.py",
    ]

    steps: list[tuple[str, list[str], dict[str, object]]] = [
        ("Python compile", ["python3", "-m", "py_compile", *py_files], {}),
        ("Generate schematic/BOM", ["python3", "circuits/gen_laser_controller.py"], {}),
        (
            "Export schematic netlist",
            [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                "circuits/laser_controller.kicad_sch",
                "-o",
                str(NETLIST_PATH),
            ],
            {},
        ),
        ("Netlist assertions", ["python3", "circuits/check_laser_controller_netlist.py", str(NETLIST_PATH)], {}),
        (
            "Schematic hierarchy/label assertions",
            ["python3", "circuits/check_schematic_hierarchy_labels.py", "circuits/laser_controller.kicad_sch"],
            {},
        ),
        (
            "Schematic presentation assertions",
            ["python3", "circuits/check_schematic_presentation.py", "circuits/laser_controller.kicad_sch"],
            {},
        ),
        ("Source-register assertions", ["python3", "circuits/check_laser_controller_sources.py", str(NETLIST_PATH)], {}),
        ("Part-note completeness assertions", ["python3", "circuits/check_part_notes_completeness.py"], {}),
        ("Source-document evidence", ["python3", "circuits/check_source_documents.py"], {}),
        ("Passive derating assertions", ["python3", "circuits/check_passive_derating.py"], {}),
        (
            "Generate staging PCB to temp file",
            [
                "env",
                "LC_STRICT_ROUTE_CLEARANCE=1",
                "LC_MAX_ROUTE_SEARCH_CELLS=2500",
                "python3",
                "circuits/gen_pcb.py",
                "--output",
                str(GENERATED_PCB_PATH),
            ],
            {},
        ),
        (
            "PCB staging assertions",
            [
                "python3",
                "circuits/check_pcb_staging.py",
                str(GENERATED_PCB_PATH),
                str(NETLIST_PATH),
            ],
            {},
        ),
        (
            "Generated-copper release gate",
            [
                "python3",
                "circuits/check_laser_controller_release_gate.py",
                "circuits/laser_controller.kicad_pcb",
                str(NETLIST_PATH),
            ],
            {
                "blocked_codes": {1},
                "blocked_note": (
                    "The current PCB artifact has hand placement recovered, but routing, zones, "
                    "KiCad refill, DRC, and return-path review remain future fabrication work."
                ),
            },
        ),
        ("AP2112 bench thermal policy", ["python3", "circuits/check_power_thermal_budget.py", "--policy", "bench-uart-usb"], {}),
        (
            "AP2112 sustained Wi-Fi expected fail",
            ["python3", "circuits/check_power_thermal_budget.py", "--policy", "wifi-tx-100-duty"],
            {"expected_codes": {1}},
        ),
        (
            "Green high-Vf laser-current thermal reference",
            ["python3", "circuits/check_laser_current_budget.py", "--policy", "green-high-vf-10v5"],
            {},
        ),
        (
            "PLT5 520EB_P monitor-PD high-side bias policy",
            ["python3", "circuits/check_laser_monitor_pd_budget.py", "--policy", "plt5-520ebp-green-10v5"],
            {},
        ),
        (
            "MPD ADC-scale-only policy",
            ["python3", "circuits/check_laser_monitor_pd_budget.py", "--policy", "adc-scale-only-10v5"],
            {},
        ),
        (
            "Green high-Vf 12V laser-current expected fail",
            ["python3", "circuits/check_laser_current_budget.py", "--policy", "green-high-vf-12v"],
            {"expected_codes": {1}},
        ),
        (
            "Low-Vf diode on green rail expected fail",
            ["python3", "circuits/check_laser_current_budget.py", "--policy", "low-vf-diode-on-10v5"],
            {"expected_codes": {1}},
        ),
        (
            "Open fabrication/release blockers",
            ["python3", "circuits/check_laser_controller_release_readiness.py"],
            {
                "blocked_codes": {2},
                "blocked_note": (
                    "The release-readiness registry has unresolved source, direct-laser, "
                    "thermal, manufacturing, and human-inspection blockers."
                ),
            },
        ),
        (
            "Regenerate audit inventory",
            [
                "python3",
                "circuits/generate_laser_controller_audit_tables.py",
                str(NETLIST_PATH),
                "circuits/laser_controller.kicad_pcb",
                "circuits/review/2026-06-25_full_net_pin_inventory.md",
            ],
            {},
        ),
        (
            "Export placement",
            ["kicad-cli", "pcb", "export", "pos", "circuits/laser_controller.kicad_pcb", "-o", str(POS_PATH)],
            {},
        ),
        (
            "KiCad ERC availability",
            ["kicad-cli", "sch", "erc", "circuits/laser_controller.kicad_sch", "-o", "/tmp/lc_erc.rpt"],
            {"unavailable_if_export_only": True},
        ),
        (
            "KiCad DRC availability",
            ["kicad-cli", "pcb", "drc", "circuits/laser_controller.kicad_pcb", "-o", "/tmp/lc_drc.rpt"],
            {"unavailable_if_export_only": True},
        ),
        ("Git diff whitespace", ["git", "diff", "--check"], {}),
        (
            "Trailing whitespace scan",
            [
                "rg",
                "-n",
                r"[ \t]+$",
                "circuits",
                "docs",
                "-g",
                "*.md",
                "-g",
                "*.py",
                "-g",
                "*.kicad_sch",
                "-g",
                "*.kicad_pcb",
            ],
            {"expected_codes": {1}},
        ),
    ]

    results: list[StepResult] = []
    for name, command, kwargs in steps:
        result = run_step(name, command, **kwargs)
        results.append(result)
        print(f"{result.status}: {name}")
        if result.status == "FAIL":
            break

    release_blocked = any(result.status in {"FAIL", "BLOCKED"} for result in results)
    write_report(results, release_blocked)
    print(f"Review report: {REPORT_PATH}")

    if any(result.status == "FAIL" for result in results):
        return 1
    if args.release and release_blocked:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
