#!/usr/bin/env python3
"""USB/VBUS entry and programming-interface topology check.

This gate focuses on the copied access-controller MCU support block:
two Mini-B connectors, CP2102N USB-UART, ESP32-S3 native USB, discrete
ESD clamps, VBUS isolation diodes, and the CP2102N VBUS sense divider.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist


def node_set(nets: dict[str, list[tuple[str, str, str, str]]], net: str) -> set[tuple[str, str]]:
    return {(ref, pin) for ref, pin, _, _ in nets.get(net, [])}


def require_exact(
    errors: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
    expected: set[tuple[str, str]],
) -> None:
    actual = node_set(nets, net)
    if actual != expected:
        errors.append(f"{net}: expected {sorted(expected)}, got {sorted(actual)}")


def require_members(
    errors: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
    required: set[tuple[str, str]],
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

    for ref in ("J1", "J2"):
        require_comp(
            errors,
            comps,
            ref,
            value="USB_MINI_B",
            footprint="Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal",
            mpn="65100516121",
            lcsc="C5120592",
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
        "U9",
        value="ESP32-S3-WROOM-1",
        footprint="Espressif:ESP32-S3-WROOM-1",
        mpn="ESP32-S3-WROOM-1-N16",
        lcsc="C2913199",
    )
    for ref in ("D7", "D8", "D9", "D11", "D12", "D14"):
        require_comp(
            errors,
            comps,
            ref,
            value="ESD_5V",
            footprint="Diode_SMD:D_SOD-523",
            mpn="LESD5D5.0CT1G(UMW)",
            lcsc="C5199850",
        )
    for ref in ("D10", "D13"):
        require_comp(
            errors,
            comps,
            ref,
            value="D_1N5819HW",
            footprint="Diode_SMD:D_SOD-123",
            mpn="1N5819HW-7-F",
            lcsc="C82544",
        )
    require_comp(
        errors,
        comps,
        "D5",
        value="SS14",
        footprint="Diode_SMD:D_SMA",
        mpn="SS14",
        lcsc="C2480",
    )
    require_comp(
        errors,
        comps,
        "R55",
        value="22.1K",
        footprint="Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder",
        mpn="FRC0402F2212TS",
        lcsc="C2929993",
    )
    require_comp(
        errors,
        comps,
        "R56",
        value="47.5K",
        footprint="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
        mpn="0603WAF4752T5E",
        lcsc="C23061",
    )
    require_comp(
        errors,
        comps,
        "C45",
        value="1uF",
        footprint="Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder",
        mpn="HGC0402R5105K250NTEJ",
        lcsc="C7472946",
    )

    require_exact(errors, nets, "/MCU_ESP32-S3/D-", {("J1", "2"), ("D7", "2"), ("U10", "5")})
    require_exact(errors, nets, "/MCU_ESP32-S3/D+", {("J1", "3"), ("D8", "2"), ("U10", "4")})
    require_exact(errors, nets, "/MCU_ESP32-S3/IO19", {("J2", "2"), ("D12", "2"), ("U9", "13")})
    require_exact(errors, nets, "/MCU_ESP32-S3/IO20", {("J2", "3"), ("D11", "2"), ("U9", "14")})

    require_exact(errors, nets, "Net-(D10-A)", {("J1", "1"), ("D10", "2")})
    require_exact(errors, nets, "Net-(D13-A)", {("J2", "1"), ("D13", "2")})
    require_members(
        errors,
        nets,
        "VBUS_5V",
        {
            ("D10", "1"),
            ("D13", "1"),
            ("D9", "2"),
            ("D14", "2"),
            ("D5", "1"),
            ("R55", "2"),
            ("C41", "1"),
            ("C42", "1"),
        },
    )
    require_members(errors, nets, "+5V", {("D5", "2")})

    require_exact(errors, nets, "Net-(U10-VBUS)", {("R55", "1"), ("R56", "2"), ("C45", "1"), ("U10", "8")})
    require_members(errors, nets, "GND", {("R56", "1"), ("C45", "2")})
    require_members(errors, nets, "+3V3", {("U10", "6"), ("U10", "7"), ("U9", "2")})

    require_members(
        errors,
        nets,
        "GND",
        {
            ("D7", "1"),
            ("D8", "1"),
            ("D9", "1"),
            ("D11", "1"),
            ("D12", "1"),
            ("D14", "1"),
            ("J1", "5"),
            ("J1", "6"),
            ("J2", "5"),
            ("J2", "6"),
            ("U10", "3"),
            ("U10", "29"),
            ("U9", "1"),
            ("U9", "40"),
            ("U9", "41"),
        },
    )

    require_exact(errors, nets, "Net-(U10-~{RST})", {("R57", "2"), ("U10", "9")})
    require_members(errors, nets, "+3V3", {("R57", "1")})
    require_exact(errors, nets, "/MCU_ESP32-S3/IO43", {("U9", "37"), ("U10", "25")})
    require_exact(errors, nets, "/MCU_ESP32-S3/IO44", {("U9", "36"), ("U10", "26")})
    require_members(errors, nets, "/MCU_ESP32-S3/DTR", {("U10", "28"), ("Q6", "3"), ("R50", "1")})
    require_members(errors, nets, "/MCU_ESP32-S3/RTS", {("U10", "24"), ("Q5", "2"), ("R51", "1")})
    require_members(errors, nets, "/MCU_ESP32-S3/EN", {("U9", "3"), ("R54", "2"), ("C44", "1"), ("SW1", "1"), ("Q5", "3")})
    require_members(errors, nets, "/MCU_ESP32-S3/PROG", {("U9", "27"), ("R53", "2"), ("C46", "1"), ("SW2", "1"), ("Q6", "2")})

    require_exact(errors, nets, "unconnected-(J1-ID-Pad4)", {("J1", "4")})
    require_exact(errors, nets, "unconnected-(J2-ID-Pad4)", {("J2", "4")})
    return errors


def check_connector_source_match(netlist: Path) -> list[str]:
    errors: list[str] = []
    comps = {comp["ref"]: comp for comp in parse_components(netlist)}
    for ref in ("J1", "J2"):
        comp = comps.get(ref)
        if comp is None:
            errors.append(f"{ref}: component missing")
            continue
        footprint = comp.get("footprint", "")
        mpn = comp.get("mpn", "")
        lcsc = comp.get("lcsc", "")
        if "65100516121" in footprint and (mpn != "65100516121" or lcsc != "C5120592"):
            errors.append(
                f"{ref}: footprint is Wuerth 65100516121 but BOM metadata is "
                f"MPN={mpn!r}, LCSC={lcsc!r}; expected MPN='65100516121', LCSC='C5120592'"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=Path("/tmp/lc.net"))
    parser.add_argument(
        "--policy",
        choices=("topology", "connector-source-match"),
        default="topology",
    )
    args = parser.parse_args()

    if args.policy == "topology":
        errors = check_topology(args.netlist)
        label = "USB/VBUS topology"
    else:
        errors = check_connector_source_match(args.netlist)
        label = "USB connector source/footprint match"

    if errors:
        print(f"FAIL {label}")
        for error in errors:
            print(f"  - {error}")
        return 1

    if args.policy == "topology":
        print(
            "PASS USB/VBUS topology: J1 USB-UART, J2 native USB, ESD clamps, "
            "1N5819 VBUS isolation, D5 +5V OR-ing, CP2102N VBUS divider, "
            "UART, EN/BOOT, and ID/shield nets match the exported schematic"
        )
    else:
        print("PASS USB connector source/footprint match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
