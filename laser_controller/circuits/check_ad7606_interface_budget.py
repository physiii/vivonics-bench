#!/usr/bin/env python3
"""AD7606-4 hardware strap and ESP32 serial-read budget check.

This is a firmware-interface contract for the current bench board. It proves
the schematic is wired for the intended AD7606-4 serial mode and that the
default firmware timing target has margin against the datasheet timing path.
It does not prove analog accuracy, final PCB layout, or working firmware.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist


ADC_REF = "U14"
ESP32_REF = "U9"
ADC_BITS = 16
ADC_CHANNELS = 4
DOUT_LINES = 2
INPUT_SPAN_V = 10.0  # +/-5 V range strap.
INPUT_LSB_UV = INPUT_SPAN_V / (2**ADC_BITS) * 1_000_000
DEFAULT_SPI_MHZ = 10.0
DEFAULT_TARGET_KSPS = 100.0
AD7606_4_NO_OS_CONV_US = 2.0
RESET_HIGH_MIN_NS = 50.0
RESET_TO_CONVST_MIN_NS = 25.0
CONVST_LOW_MIN_NS = 25.0
CONVST_HIGH_MIN_NS = 25.0
BUSY_TO_CS_MIN_NS = 0.0
READ_DURING_BUSY_T6_GUARD_NS = 25.0
DATASHEET_NO_OS_MAX_KSPS = 200.0
CONSERVATIVE_SPI_MAX_MHZ = 10.0


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw in (None, ""):
        return default
    return float(raw)


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


def require_contains(
    errors: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    net: str,
    expected_nodes: set[tuple[str, str]],
) -> None:
    actual = node_set(nets, net)
    missing = sorted(expected_nodes - actual)
    if missing:
        errors.append(f"{net}: missing expected node(s) {missing}; actual {sorted(actual)}")


def require_unconnected_pin(
    errors: list[str],
    nets: dict[str, list[tuple[str, str, str, str]]],
    ref: str,
    pin: str,
) -> None:
    connected = [
        net
        for net, nodes in sorted(nets.items())
        if any(node_ref == ref and node_pin == pin for node_ref, node_pin, _, _ in nodes)
    ]
    if any(not net.startswith("unconnected-") for net in connected):
        errors.append(f"{ref}.{pin}: expected intentional no-connect, got net(s) {connected}")


def main() -> int:
    netlist_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lc.net")
    nets = parse_netlist(netlist_path)
    comps = parse_components(netlist_path)
    errors: list[str] = []

    comp = next((item for item in comps if item["ref"] == ADC_REF), None)
    if not comp:
        errors.append(f"{ADC_REF}: AD7606 component missing")
    elif comp["mpn"] != "AD7606BSTZ-4RL" or comp["footprint"] != "Package_QFP:LQFP-64_10x10mm_P0.5mm":
        errors.append(
            f"{ADC_REF}: expected AD7606BSTZ-4RL on LQFP-64 footprint, got "
            f"{comp['mpn']} / {comp['footprint']}"
        )

    require_exact(errors, nets, "VOUT1", {("C1", "2"), ("RV5", "2"), ("RV5", "3"), ("U1", "6"), (ADC_REF, "49")})
    require_exact(errors, nets, "VOUT2", {("C5", "2"), ("RV6", "2"), ("RV6", "3"), ("U2", "6"), (ADC_REF, "51")})
    require_exact(errors, nets, "VOUT3", {("C9", "2"), ("RV7", "2"), ("RV7", "3"), ("U3", "6"), (ADC_REF, "57")})
    require_exact(errors, nets, "VOUT4", {("C13", "2"), ("RV8", "2"), ("RV8", "3"), ("U4", "6"), (ADC_REF, "59")})

    require_exact(errors, nets, "CONVST", {(ADC_REF, "9"), (ADC_REF, "10"), (ESP32_REF, "8")})
    require_exact(errors, nets, "ADC_RESET", {(ADC_REF, "11"), (ESP32_REF, "25")})
    require_exact(errors, nets, "ADC_SCLK", {(ADC_REF, "12"), (ESP32_REF, "10")})
    require_exact(errors, nets, "ADC_CS", {(ADC_REF, "13"), (ESP32_REF, "11")})
    require_exact(errors, nets, "ADC_BUSY", {(ADC_REF, "14"), (ESP32_REF, "24")})
    require_exact(errors, nets, "ADC_MISO_A", {(ADC_REF, "24"), (ESP32_REF, "23")})
    require_exact(errors, nets, "ADC_MISO_B", {(ADC_REF, "25"), (ESP32_REF, "31")})

    require_contains(errors, nets, "+5V", {(ADC_REF, "1"), (ADC_REF, "37"), (ADC_REF, "38"), (ADC_REF, "48")})
    require_contains(errors, nets, "+3V3", {(ADC_REF, "6"), (ADC_REF, "7"), (ADC_REF, "23"), (ADC_REF, "34")})
    require_contains(
        errors,
        nets,
        "GND",
        {
            (ADC_REF, "3"),  # OS0
            (ADC_REF, "4"),  # OS1
            (ADC_REF, "5"),  # OS2
            (ADC_REF, "8"),  # RANGE: +/-5 V when low
            (ADC_REF, "16"), (ADC_REF, "17"), (ADC_REF, "18"), (ADC_REF, "19"),
            (ADC_REF, "20"), (ADC_REF, "21"), (ADC_REF, "22"),
            (ADC_REF, "27"), (ADC_REF, "28"), (ADC_REF, "29"), (ADC_REF, "30"),
            (ADC_REF, "31"), (ADC_REF, "32"), (ADC_REF, "33"),  # DB15/BYTE_SEL low: serial, not byte mode
            (ADC_REF, "35"), (ADC_REF, "40"), (ADC_REF, "41"),
            (ADC_REF, "43"), (ADC_REF, "46"),
            (ADC_REF, "47"), (ADC_REF, "50"), (ADC_REF, "52"), (ADC_REF, "53"),
            (ADC_REF, "54"), (ADC_REF, "55"), (ADC_REF, "56"), (ADC_REF, "58"),
            (ADC_REF, "60"), (ADC_REF, "61"), (ADC_REF, "62"), (ADC_REF, "63"), (ADC_REF, "64"),
        },
    )
    require_exact(errors, nets, "/POWER_IO/ADC_CREG1", {("C57", "1"), (ADC_REF, "36")})
    require_exact(errors, nets, "/POWER_IO/ADC_CREG2", {("C58", "1"), (ADC_REF, "39")})
    require_exact(errors, nets, "/POWER_IO/ADC_CREFIN", {("C59", "1"), (ADC_REF, "42")})
    require_exact(errors, nets, "/POWER_IO/ADC_REFCAP", {("C60", "1"), (ADC_REF, "44"), (ADC_REF, "45")})
    require_unconnected_pin(errors, nets, ADC_REF, "15")

    spi_mhz = env_float("LC_AD7606_SPI_MHZ", DEFAULT_SPI_MHZ)
    target_ksps = env_float("LC_AD7606_TARGET_KSPS", DEFAULT_TARGET_KSPS)
    bits_per_dout = ADC_BITS * ((ADC_CHANNELS + DOUT_LINES - 1) // DOUT_LINES)
    read_us = bits_per_dout / spi_mhz
    read_after_cycle_us = AD7606_4_NO_OS_CONV_US + read_us
    target_period_us = 1000.0 / target_ksps
    cycle_margin_us = target_period_us - read_after_cycle_us
    max_read_after_ksps = min(1000.0 / read_after_cycle_us, DATASHEET_NO_OS_MAX_KSPS)

    if spi_mhz > CONSERVATIVE_SPI_MAX_MHZ:
        errors.append(
            f"firmware SPI clock {spi_mhz:.2f} MHz exceeds conservative {CONSERVATIVE_SPI_MAX_MHZ:.2f} MHz policy "
            "for nominal 3.3 V VDRIVE; prove rail/timing margin before raising it"
        )
    if target_ksps > max_read_after_ksps:
        errors.append(
            f"target sample rate {target_ksps:.2f} kSPS exceeds read-after-conversion budget {max_read_after_ksps:.2f} kSPS"
        )
    if cycle_margin_us < 1.0:
        errors.append(f"target sample period leaves only {cycle_margin_us:.2f} us margin; keep at least 1 us firmware slack")

    if errors:
        print(f"FAIL AD7606 interface budget: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("PASS AD7606 interface budget")
    print("  hardware: AD7606BSTZ-4RL LQFP-64, AVCC=+5V, VDRIVE=+3V3, internal reference, serial mode")
    print("  straps: RANGE=0 (+/-5V), OS[2:0]=000 (no oversampling), STBY=1, REF_SELECT=1, DB15/BYTE_SEL=0")
    print("  ESP32: CONVST=GPIO15, SCLK=GPIO17, CS=GPIO18, BUSY=GPIO47, RESET=GPIO48, DOUTA=GPIO21, DOUTB=GPIO38")
    print(
        f"  read policy: {ADC_CHANNELS} channels, {DOUT_LINES} DOUT lines, {bits_per_dout:.0f} SCLK edges per DOUT line, "
        f"{spi_mhz:.2f}MHz SCLK -> {read_us:.2f}us read"
    )
    print(
        f"  timing budget: conversion={AD7606_4_NO_OS_CONV_US:.2f}us, read-after cycle={read_after_cycle_us:.2f}us, "
        f"target={target_ksps:.1f}kSPS period={target_period_us:.2f}us, margin={cycle_margin_us:.2f}us"
    )
    print(
        f"  firmware requirements: RESET high >= {RESET_HIGH_MIN_NS:.0f}ns, RESET-low to CONVST >= {RESET_TO_CONVST_MIN_NS:.0f}ns, "
        f"CONVST low/high >= {CONVST_LOW_MIN_NS:.0f}/{CONVST_HIGH_MIN_NS:.0f}ns, CS after BUSY fall >= {BUSY_TO_CS_MIN_NS:.0f}ns, "
        f"avoid reading on BUSY falling edge and keep >= {READ_DURING_BUSY_T6_GUARD_NS:.0f}ns guard if reading during conversion"
    )
    print(f"  scale: 16-bit twos-complement, +/-5V range, {INPUT_LSB_UV:.2f}uV/LSB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
