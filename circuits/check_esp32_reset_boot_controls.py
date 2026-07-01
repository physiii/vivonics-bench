#!/usr/bin/env python3
"""ESP32-S3 reset, boot, factory-button, and auto-programming topology check.

This gate covers the copied access-controller MCU control block around the
ESP32-S3 module and CP2102N: EN reset RC/button, GPIO0/BOOT programming
RC/button, GPIO1 factory button, CP2102N DTR/RTS transistor auto-reset network,
CP2102N RST/SUSPEND pulls, and the copied IO13/IO14 support pulls.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist


Node = tuple[str, str]


def node_set(nets: dict[str, list[tuple[str, str, str, str]]], net: str) -> set[Node]:
    return {(ref, pin) for ref, pin, _, _ in nets.get(net, [])}


def require_exact(
    errors: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
    expected: set[Node],
) -> None:
    actual = node_set(nets, net)
    if actual != expected:
        errors.append(f"{net}: expected {sorted(expected)}, got {sorted(actual)}")


def require_members(
    errors: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
    required: set[Node],
) -> None:
    actual = node_set(nets, net)
    missing = sorted(required - actual)
    if missing:
        errors.append(f"{net}: missing required node(s) {missing}; got {sorted(actual)}")


def require_comp(
    errors: list[str],
    comps: dict[str, dict[str, str]],
    ref: str,
    *,
    value: str,
    footprint: str,
    mpn: str,
    lcsc: str,
) -> None:
    actual = comps.get(ref)
    expected = {
        "value": value,
        "footprint": footprint,
        "mpn": mpn,
        "lcsc": lcsc,
    }
    if actual is None:
        errors.append(f"{ref}: component missing")
        return
    got = {key: actual.get(key, "") for key in expected}
    if got != expected:
        errors.append(f"{ref}: expected {expected}, got {got}")


def check_topology(netlist: Path) -> list[str]:
    errors: list[str] = []
    nets = parse_netlist(netlist)
    comps = {comp["ref"]: comp for comp in parse_components(netlist)}

    require_comp(
        errors,
        comps,
        "U9",
        value="ESP32-S3-WROOM-1",
        footprint="Espressif:ESP32-S3-WROOM-1",
        mpn="ESP32-S3-WROOM-1-N16",
        lcsc="C2913199",
    )
    require_comp(
        errors,
        comps,
        "U10",
        value="CP2102N-Axx-xQFN28",
        footprint="Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm",
        mpn="CP2102N-A02-GQFN28R",
        lcsc="C964632",
    )
    require_comp(
        errors,
        comps,
        "Q5",
        value="Q_L8050QLT1G",
        footprint="Package_TO_SOT_SMD:SOT-23",
        mpn="L8050QLT1G",
        lcsc="C49581",
    )
    require_comp(
        errors,
        comps,
        "Q6",
        value="Q_L8550HQLT1G",
        footprint="Package_TO_SOT_SMD:SOT-23",
        mpn="L8550HQLT1G",
        lcsc="C39282",
    )
    for ref in ("SW1", "SW2", "SW3"):
        require_comp(
            errors,
            comps,
            ref,
            value="SW_PUSH",
            footprint="Button_Switch_SMD:SW_SPST_PTS645",
            mpn="K2-1102SP-C4SC-04",
            lcsc="C127509",
        )
    for ref in ("R50", "R51", "R52", "R53", "R54", "R58", "R59", "R60"):
        require_comp(
            errors,
            comps,
            ref,
            value="10K",
            footprint="Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder",
            mpn="ERJ2RKF1002X",
            lcsc="C191123",
        )
    require_comp(
        errors,
        comps,
        "R57",
        value="1K",
        footprint="Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder",
        mpn="RT0402BRD071KL",
        lcsc="C852624",
    )
    for ref in ("C44", "C46"):
        require_comp(
            errors,
            comps,
            ref,
            value="1uF",
            footprint="Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
            mpn="HGC0402R5105K250NTEJ",
            lcsc="C7472946",
        )

    require_exact(errors, nets, "/MCU_ESP32-S3/EN", {("U9", "3"), ("R54", "2"), ("C44", "1"), ("SW1", "1"), ("Q5", "3")})
    require_exact(errors, nets, "/MCU_ESP32-S3/PROG", {("U9", "27"), ("R53", "2"), ("C46", "1"), ("SW2", "1"), ("Q6", "2")})
    require_exact(errors, nets, "/MCU_ESP32-S3/FACT", {("U9", "39"), ("R52", "2"), ("SW3", "1")})

    require_exact(errors, nets, "/MCU_ESP32-S3/DTR", {("U10", "28"), ("R50", "1"), ("Q6", "3")})
    require_exact(errors, nets, "/MCU_ESP32-S3/RTS", {("U10", "24"), ("R51", "1"), ("Q5", "2")})
    require_exact(errors, nets, "Net-(Q5-B)", {("Q5", "1"), ("R50", "2")})
    require_exact(errors, nets, "Net-(Q6-B)", {("Q6", "1"), ("R51", "2")})

    require_exact(errors, nets, "Net-(U10-~{RST})", {("U10", "9"), ("R57", "2")})
    require_exact(errors, nets, "Net-(U10-~{SUSPEND})", {("U10", "11"), ("R58", "1")})
    require_exact(errors, nets, "/MCU_ESP32-S3/IO13", {("U9", "21"), ("R60", "1")})
    require_exact(errors, nets, "/MCU_ESP32-S3/IO14", {("U9", "22"), ("R59", "2")})

    require_members(
        errors,
        nets,
        "+3V3",
        {
            ("U9", "2"),
            ("U10", "6"),
            ("U10", "7"),
            ("R52", "1"),
            ("R53", "1"),
            ("R54", "1"),
            ("R57", "1"),
            ("R59", "1"),
            ("R60", "2"),
        },
    )
    require_members(
        errors,
        nets,
        "GND",
        {
            ("C44", "2"),
            ("C46", "2"),
            ("R58", "2"),
            ("SW1", "2"),
            ("SW2", "2"),
            ("SW3", "2"),
            ("U9", "1"),
            ("U9", "40"),
            ("U9", "41"),
            ("U10", "3"),
            ("U10", "29"),
        },
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=Path("/tmp/lc.net"))
    args = parser.parse_args()

    errors = check_topology(args.netlist)
    if errors:
        print("FAIL ESP32 reset/boot controls")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        "PASS ESP32 reset/boot controls: EN 10k/1uF/reset, "
        "GPIO0 BOOT 10k/1uF/PROG, GPIO1 FACT, CP2102N DTR/RTS "
        "auto-reset transistors, RST/SUSPEND pulls, and IO13/IO14 pulls "
        "match the exported schematic"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
