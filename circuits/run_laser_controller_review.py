#!/usr/bin/env python3
"""Run the available bench laser-controller review gates.

This wrapper is intentionally explicit about what it proves and what it cannot
prove in this environment.  It runs the custom source, netlist, PCB, generated
copper, thermal, open-release-blocker, headless Pcbnew DRC, native courtyard
triage, and availability gates.  It also attempts KiCad CLI ERC/DRC and marks
them as release blockers when the installed KiCad CLI does not expose those
commands. Use --release to make blockers produce a nonzero exit code.
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
        "circuits/check_schematic_pcb_parity.py",
        "circuits/check_laser_controller_release_gate.py",
        "circuits/check_layout_review_geometry.py",
        "circuits/check_kicad_pcbnew_drc_report.py",
        "circuits/check_courtyard_overlap_triage.py",
        "circuits/check_laser_controller_release_readiness.py",
        "circuits/check_schematic_hierarchy_labels.py",
        "circuits/check_schematic_presentation.py",
        "circuits/check_power_thermal_budget.py",
        "circuits/check_power_bringup_template.py",
        "circuits/check_ap2112_first_article_signoff.py",
        "circuits/check_ad7606_package_pcb.py",
        "circuits/check_ad7606_interface_budget.py",
        "circuits/check_ad7606_first_article_signoff.py",
        "circuits/check_optical_calibration_template.py",
        "circuits/check_tia_readout_budget.py",
        "circuits/check_tia_first_article_signoff.py",
        "circuits/check_ap6320x_package_pcb.py",
        "circuits/check_buck_input_power_budget.py",
        "circuits/check_ap632_first_article_signoff.py",
        "circuits/check_vin24_input_protection.py",
        "circuits/check_usb_vbus_interface.py",
        "circuits/check_esp32_reset_boot_controls.py",
        "circuits/check_laser_driver_control_loop.py",
        "circuits/check_laser_driver_package_pcb.py",
        "circuits/check_laser_diode_footprints.py",
        "circuits/check_monitor_pd_package_pcb.py",
        "circuits/check_monitor_pd_first_article_signoff.py",
        "circuits/check_laser_first_article_signoff.py",
        "circuits/check_laser_bringup_template.py",
        "circuits/check_laser_current_budget.py",
        "circuits/check_laser_monitor_pd_budget.py",
        "circuits/check_passive_derating.py",
        "circuits/check_passive_avl_lock.py",
        "circuits/generate_laser_controller_audit_tables.py",
        "circuits/circuit_designators.py",
        "circuits/check_laser_controller_sources.py",
        "circuits/check_part_notes_completeness.py",
        "circuits/check_source_documents.py",
        "circuits/check_jlcpcb_order_package.py",
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
        ("Passive first-article AVL lock", ["python3", "circuits/check_passive_avl_lock.py", "--netlist", str(NETLIST_PATH)], {}),
        ("USB/VBUS topology", ["python3", "circuits/check_usb_vbus_interface.py", "--netlist", str(NETLIST_PATH)], {}),
        (
            "ESP32 reset/boot controls",
            ["python3", "circuits/check_esp32_reset_boot_controls.py", "--netlist", str(NETLIST_PATH)],
            {},
        ),
        (
            "USB connector footprint/source match",
            [
                "python3",
                "circuits/check_usb_vbus_interface.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "connector-source-match",
            ],
            {},
        ),
        (
            "AD7606 package/PCB pinout",
            [
                "python3",
                "circuits/check_ad7606_package_pcb.py",
                "--netlist",
                str(NETLIST_PATH),
                "--board",
                "circuits/laser_controller.kicad_pcb",
            ],
            {},
        ),
        ("AD7606 interface budget", ["python3", "circuits/check_ad7606_interface_budget.py", str(NETLIST_PATH)], {}),
        ("AD7606 first-article firmware/readback signoff", ["python3", "circuits/check_ad7606_first_article_signoff.py"], {}),
        ("Optical/readout calibration template", ["python3", "circuits/check_optical_calibration_template.py"], {}),
        (
            "TIA readout budget",
            ["python3", "circuits/check_tia_readout_budget.py", "--netlist", str(NETLIST_PATH)],
            {},
        ),
        ("TIA first-article calibration signoff", ["python3", "circuits/check_tia_first_article_signoff.py"], {}),
        (
            "TIA bright-ambient expected fail",
            [
                "python3",
                "circuits/check_tia_readout_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "sfh2201-1000lx-example",
            ],
            {"expected_codes": {1}},
        ),
        (
            "AP6320x package/PCB pinout",
            [
                "python3",
                "circuits/check_ap6320x_package_pcb.py",
                "--netlist",
                str(NETLIST_PATH),
                "--board",
                "circuits/laser_controller.kicad_pcb",
            ],
            {},
        ),
        (
            "Buck/input selected-diode max-current reference",
            [
                "python3",
                "circuits/check_buck_input_power_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "bench-selected-max-9v3",
            ],
            {},
        ),
        (
            "Buck/input all-channel analog-limit budget",
            [
                "python3",
                "circuits/check_buck_input_power_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "hardware-clamp-9v3",
            ],
            {},
        ),
        (
            "Buck datasheet capacitor recommendation",
            [
                "python3",
                "circuits/check_buck_input_power_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "datasheet-recommended-components",
            ],
            {},
        ),
        ("AP632 first-article buck validation signoff", ["python3", "circuits/check_ap632_first_article_signoff.py"], {}),
        ("Power/input bring-up measurement template", ["python3", "circuits/check_power_bringup_template.py"], {}),
        (
            "VIN24 bench input topology",
            [
                "python3",
                "circuits/check_vin24_input_protection.py",
                "--netlist",
                str(NETLIST_PATH),
            ],
            {},
        ),
        (
            "VIN24 bench external-protection signoff",
            [
                "python3",
                "circuits/check_vin24_input_protection.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "bench-external-protection",
            ],
            {},
        ),
        (
            "VIN24 production input-protection expected fail",
            [
                "python3",
                "circuits/check_vin24_input_protection.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "production-protection",
            ],
            {"expected_codes": {1}},
        ),
        (
            "Laser-driver selected-current control-loop budget",
            [
                "python3",
                "circuits/check_laser_driver_control_loop.py",
                "--netlist",
                str(NETLIST_PATH),
            ],
            {},
        ),
        (
            "Laser-driver package/PCB pinout",
            [
                "python3",
                "circuits/check_laser_driver_package_pcb.py",
                "--netlist",
                str(NETLIST_PATH),
                "--board",
                "circuits/laser_controller.kicad_pcb",
            ],
            {},
        ),
        (
            "Laser-driver per-channel limiter gate-margin",
            [
                "python3",
                "circuits/check_laser_driver_control_loop.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "hardware-clamp-gate-margin",
            ],
            {},
        ),
        (
            "Direct laser-can footprint pinout",
            [
                "python3",
                "circuits/check_laser_diode_footprints.py",
                "--netlist",
                str(NETLIST_PATH),
                "--board",
                "circuits/laser_controller.kicad_pcb",
            ],
            {},
        ),
        (
            "Monitor-PD package/PCB pinout",
            [
                "python3",
                "circuits/check_monitor_pd_package_pcb.py",
                "--netlist",
                str(NETLIST_PATH),
                "--board",
                "circuits/laser_controller.kicad_pcb",
            ],
            {},
        ),
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
            "Schematic/PCB parity",
            [
                "python3",
                "circuits/check_schematic_pcb_parity.py",
                "--netlist",
                str(NETLIST_PATH),
                "--board",
                "circuits/laser_controller.kicad_pcb",
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
                    "The current PCB artifact has hand placement recovered, but routing/zones "
                    "or native KiCad DRC/parity evidence still block fabrication."
                ),
            },
        ),
        (
            "Focused layout-geometry review",
            ["python3", "circuits/check_layout_review_geometry.py", "circuits/laser_controller.kicad_pcb"],
            {
                "blocked_codes": {2},
                "blocked_note": (
                    "The board still has high-risk physical layout distances in buck, USB ESD, "
                    "TIA summing-node, monitor-PD, or laser-current local loops."
                ),
            },
        ),
        (
            "Headless Pcbnew DRC report",
            ["/usr/bin/python3", "circuits/check_kicad_pcbnew_drc_report.py"],
            {},
        ),
        (
            "Native courtyard-overlap triage",
            ["/usr/bin/python3", "circuits/check_courtyard_overlap_triage.py"],
            {
                "blocked_codes": {2},
                "blocked_note": (
                    "Native Pcbnew reports courtyard overlaps that require KiCad layout review, "
                    "package/placement changes, or explicit assembly waivers before fabrication."
                ),
            },
        ),
        ("AP2112 bench thermal policy", ["python3", "circuits/check_power_thermal_budget.py", "--policy", "bench-uart-usb"], {}),
        ("AP2112 first-article no-RF signoff", ["python3", "circuits/check_ap2112_first_article_signoff.py"], {}),
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
            "Selected-diode max-current 9.3V laser-current reference",
            ["python3", "circuits/check_laser_current_budget.py", "--policy", "selected-diodes-max-9v3"],
            {},
        ),
        (
            "PLT5 520EB_P monitor-PD high-side bias policy",
            [
                "python3",
                "circuits/check_laser_monitor_pd_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "plt5-520ebp-green-10v5",
            ],
            {},
        ),
        (
            "MPD ADC-scale-only policy",
            [
                "python3",
                "circuits/check_laser_monitor_pd_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "adc-scale-only-10v5",
            ],
            {},
        ),
        (
            "Selected-laser monitor-PD typical",
            [
                "python3",
                "circuits/check_laser_monitor_pd_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "selected-monitor-typ-9v3",
            ],
            {},
        ),
        (
            "Selected-laser monitor-PD high-end",
            [
                "python3",
                "circuits/check_laser_monitor_pd_budget.py",
                "--netlist",
                str(NETLIST_PATH),
                "--policy",
                "selected-monitor-worst-9v3",
            ],
            {},
        ),
        (
            "Monitor-PD first-article calibration signoff",
            ["python3", "circuits/check_monitor_pd_first_article_signoff.py"],
            {},
        ),
        (
            "Green high-Vf 12V laser-current expected fail",
            ["python3", "circuits/check_laser_current_budget.py", "--policy", "green-high-vf-12v"],
            {"expected_codes": {1}},
        ),
        (
            "Selected-diode 9.3V typical (production gate, must PASS)",
            ["python3", "circuits/check_laser_current_budget.py", "--policy", "selected-diodes-typ-9v3"],
            {},
        ),
        (
            "Selected-diode per-channel analog-limit gate",
            [
                "python3",
                "circuits/check_laser_current_budget.py",
                "--policy",
                "selected-diodes-hardware-clamp-9v3",
            ],
            {},
        ),
        ("Laser bring-up measurement template", ["python3", "circuits/check_laser_bringup_template.py"], {}),
        ("Laser first-article bring-up signoff", ["python3", "circuits/check_laser_first_article_signoff.py"], {}),
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
        ("JLCPCB order package", ["python3", "circuits/check_jlcpcb_order_package.py"], {}),
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
