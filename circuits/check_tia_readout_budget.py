#!/usr/bin/env python3
"""SFH2201/OPA380 signal-photodiode TIA range and topology check.

This is a first-order schematic/readout contract. It proves the four on-board
signal photodiodes are wired into OPA380 transimpedance amplifiers and into the
AD7606, and it quantifies the output headroom before the OPA380 clips. It does
not prove optical calibration, noise, stability, or the final routed PCB.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from circuit_designators import WL, ref_for


ADC_REF = "U14"
SUPPLY_V = 5.0
OPA380_COMMON_MODE_HIGH_MARGIN_V = 1.8
OPA380_LINEAR_OUT_LOW_V = 0.1
OPA380_LINEAR_OUT_HIGH_V = 4.3  # 5 V supply minus 0.7 V AOL/output-swing guard.
AD7606_RANGE_LOW_V = -5.0
AD7606_RANGE_HIGH_V = 5.0
SFH2201_REVERSE_MAX_V = 16.0
SFH2201_1000_LUX_SHORT_CIRCUIT_UA = 76.0
DEFAULT_VBIAS_TARGET_V = 1.5
MIN_SYMMETRIC_RANGE_UA = 0.5


@dataclass(frozen=True)
class Channel:
    color: str
    vout_net: str
    adc_pin: str


CHANNELS = (
    Channel("IR", "VOUT1", "49"),
    Channel("RED", "VOUT2", "51"),
    Channel("GREEN", "VOUT3", "57"),
    Channel("BLUE", "VOUT4", "59"),
)


def canon_net(net: str | None) -> str | None:
    aliases = {
        "Net-(D1-A)": "/TIA_IR/PD_ANODE",
        "Net-(D1-K)": "/TIA_IR/PD_CATHODE",
        "Net-(U1-+)": "/TIA_IR/VBIAS",
        "Net-(R4-Pad2)": "/TIA_IR/VBIAS_TOP",
        "Net-(RV1-W)": "/TIA_IR/VBIAS_WIPER",
        "Net-(D2-A)": "/TIA_RED/PD_ANODE",
        "Net-(D2-K)": "/TIA_RED/PD_CATHODE",
        "Net-(U2-+)": "/TIA_RED/VBIAS",
        "Net-(R8-Pad2)": "/TIA_RED/VBIAS_TOP",
        "Net-(RV2-W)": "/TIA_RED/VBIAS_WIPER",
        "Net-(D3-A)": "/TIA_GREEN/PD_ANODE",
        "Net-(D3-K)": "/TIA_GREEN/PD_CATHODE",
        "Net-(U3-+)": "/TIA_GREEN/VBIAS",
        "Net-(R12-Pad2)": "/TIA_GREEN/VBIAS_TOP",
        "Net-(RV3-W)": "/TIA_GREEN/VBIAS_WIPER",
        "Net-(D4-A)": "/TIA_BLUE/PD_ANODE",
        "Net-(D4-K)": "/TIA_BLUE/PD_CATHODE",
        "Net-(U4-+)": "/TIA_BLUE/VBIAS",
        "Net-(R16-Pad2)": "/TIA_BLUE/VBIAS_TOP",
        "Net-(RV4-W)": "/TIA_BLUE/VBIAS_WIPER",
    }
    return aliases.get(net, net)


def node_set(nets: dict[str, list[tuple[str, str, str, str]]], net: str) -> set[tuple[str, str]]:
    wanted = canon_net(net)
    return {
        (ref, pin)
        for raw_net, nodes in nets.items()
        if canon_net(raw_net) == wanted
        for ref, pin, _, _ in nodes
    }


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
    expected: set[tuple[str, str]],
) -> None:
    actual = node_set(nets, net)
    missing = sorted(expected - actual)
    if missing:
        errors.append(f"{net}: missing {missing}; actual {sorted(actual)}")


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
    expected_nc_net = f"unconnected-({ref}-NC-Pad{pin})"
    if any(net != expected_nc_net for net in connected):
        errors.append(f"{ref}.{pin}: expected intentional no-connect, got net(s) {connected}")


def component_by_ref(path: Path) -> dict[str, dict[str, str]]:
    return {comp["ref"]: comp for comp in parse_components(path)}


def expect_component(
    errors: list[str],
    comps: dict[str, dict[str, str]],
    ref: str,
    value: str,
    footprint: str,
    mpn: str,
    lcsc: str,
) -> None:
    comp = comps.get(ref)
    if comp is None:
        errors.append(f"{ref}: component missing")
        return
    expected = {
        "value": value,
        "footprint": footprint,
        "mpn": mpn,
        "lcsc": lcsc,
    }
    actual = {key: comp.get(key, "") for key in expected}
    if actual != expected:
        errors.append(f"{ref}: expected {expected}, got {actual}")


def expected_vbias_max_v() -> float:
    # +5V -> RT 10k -> RV11 10k -> GND, with the wiper feeding OPA380 +IN
    # through R1. OPA380 input bias is negligible for this first-order bound.
    return SUPPLY_V * 10_000.0 / (10_000.0 + 10_000.0)


def photocurrent_ua(voltage_delta_v: float, feedback_ohm: float) -> float:
    return voltage_delta_v / feedback_ohm * 1_000_000.0


def check_topology(
    nets: dict[str, list[tuple[str, str, str, str]]],
    comps: dict[str, dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    for channel in CHANNELS:
        sheet = f"TIA_{channel.color}"
        pd = ref_for(sheet, "D1")
        opa = ref_for(sheet, "U1")
        rf = ref_for(sheet, "RVFB")
        cf = ref_for(sheet, "C1")
        rb = ref_for(sheet, "RB")
        cb = ref_for(sheet, "CB")
        rtop = ref_for(sheet, "RT")
        rvbias = ref_for(sheet, "RV11")
        rbias = ref_for(sheet, "R1")
        cbias = ref_for(sheet, "C11")

        expect_component(
            errors,
            comps,
            pd,
            "SFH2201",
            "OptoDevice:Osram_SFH2201",
            "SFH2201",
            "C2900216",
        )
        expect_component(
            errors,
            comps,
            opa,
            "OPA380AID",
            "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "OPA380AID",
            "C201677",
        )
        expect_component(
            errors,
            comps,
            rf,
            "RF 2M",
            "Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical",
            "3224W-1-205E",
            "C116323",
        )
        expect_component(
            errors,
            comps,
            rvbias,
            "VBIAS 10k",
            "Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical",
            "3224W-1-103E",
            "C81348",
        )

        require_exact(
            errors,
            nets,
            f"/TIA_{channel.color}/PD_ANODE",
            {(cf, "1"), (pd, "2"), (rf, "1"), (opa, "2")},
        )
        require_exact(
            errors,
            nets,
            f"/TIA_{channel.color}/PD_CATHODE",
            {(cb, "1"), (pd, "1"), (rb, "2")},
        )
        require_exact(
            errors,
            nets,
            channel.vout_net,
            {(cf, "2"), (rf, "2"), (rf, "3"), (opa, "6"), (ADC_REF, channel.adc_pin)},
        )
        require_exact(
            errors,
            nets,
            f"/TIA_{channel.color}/VBIAS",
            {(cbias, "1"), (rbias, "2"), (opa, "3")},
        )
        require_exact(
            errors,
            nets,
            f"/TIA_{channel.color}/VBIAS_TOP",
            {(rtop, "2"), (rvbias, "1")},
        )
        require_exact(
            errors,
            nets,
            f"/TIA_{channel.color}/VBIAS_WIPER",
            {(rvbias, "2"), (rbias, "1")},
        )
        require_contains(errors, nets, "+5V", {(opa, "7"), (rb, "1"), (rtop, "1")})
        require_contains(errors, nets, "GND", {(opa, "4"), (cb, "2"), (cbias, "2"), (rvbias, "3")})
        for pin in ("1", "5", "8"):
            require_unconnected_pin(errors, nets, opa, pin)
    return errors


def check_range(policy: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    cm_max_v = SUPPLY_V - OPA380_COMMON_MODE_HIGH_MARGIN_V
    vbias_max_v = expected_vbias_max_v()
    feedback_ohm = 2_000_000.0
    pos_headroom_v = OPA380_LINEAR_OUT_HIGH_V - DEFAULT_VBIAS_TARGET_V
    neg_headroom_v = DEFAULT_VBIAS_TARGET_V - OPA380_LINEAR_OUT_LOW_V
    positive_range_ua = photocurrent_ua(pos_headroom_v, feedback_ohm)
    negative_range_ua = photocurrent_ua(neg_headroom_v, feedback_ohm)
    symmetric_range_ua = min(positive_range_ua, negative_range_ua)
    sfh_1000_lux_output_v = SFH2201_1000_LUX_SHORT_CIRCUIT_UA * feedback_ohm / 1_000_000.0

    if vbias_max_v > cm_max_v:
        errors.append(
            f"VBIAS network can reach {vbias_max_v:.2f} V, above OPA380 common-mode guard {cm_max_v:.2f} V"
        )
    if not (AD7606_RANGE_LOW_V <= OPA380_LINEAR_OUT_LOW_V and OPA380_LINEAR_OUT_HIGH_V <= AD7606_RANGE_HIGH_V):
        errors.append(
            f"OPA380 guarded output window {OPA380_LINEAR_OUT_LOW_V:.2f}..{OPA380_LINEAR_OUT_HIGH_V:.2f} V "
            f"is outside AD7606 +/-5 V range"
        )
    if SUPPLY_V > SFH2201_REVERSE_MAX_V:
        errors.append(f"SFH2201 reverse bias {SUPPLY_V:.2f} V exceeds {SFH2201_REVERSE_MAX_V:.2f} V max")
    if not (0.0 <= DEFAULT_VBIAS_TARGET_V <= vbias_max_v):
        errors.append(f"default VBIAS target {DEFAULT_VBIAS_TARGET_V:.2f} V is outside 0..{vbias_max_v:.2f} V trim range")
    if symmetric_range_ua < MIN_SYMMETRIC_RANGE_UA:
        errors.append(
            f"at VBIAS={DEFAULT_VBIAS_TARGET_V:.2f} V and RF=2 MOhm only +/-{symmetric_range_ua:.2f} uA "
            f"symmetric photocurrent headroom remains, below {MIN_SYMMETRIC_RANGE_UA:.2f} uA policy"
        )

    if policy == "sfh2201-1000lx-example":
        if DEFAULT_VBIAS_TARGET_V + sfh_1000_lux_output_v > OPA380_LINEAR_OUT_HIGH_V:
            errors.append(
                "SFH2201 1000 lx short-circuit-current example is not measurable at RF=2 MOhm: "
                f"{SFH2201_1000_LUX_SHORT_CIRCUIT_UA:.1f} uA would need {sfh_1000_lux_output_v:.1f} V of TIA swing"
            )
    elif policy != "bench-range":
        errors.append(f"unknown policy {policy!r}")

    notes.append(
        f"VBIAS trim range: 0.00..{vbias_max_v:.2f} V; OPA380 common-mode guard max={cm_max_v:.2f} V"
    )
    notes.append(
        f"guarded output/readout window: OPA380 {OPA380_LINEAR_OUT_LOW_V:.2f}..{OPA380_LINEAR_OUT_HIGH_V:.2f} V "
        f"inside AD7606 +/-5 V range"
    )
    notes.append(
        f"at VBIAS={DEFAULT_VBIAS_TARGET_V:.2f} V, RF=2 MOhm: +{positive_range_ua:.2f}/-{negative_range_ua:.2f} uA "
        f"one-sided headroom, +/-{symmetric_range_ua:.2f} uA symmetric headroom"
    )
    notes.append(
        f"SFH2201 reverse bias is {SUPPLY_V:.2f} V versus {SFH2201_REVERSE_MAX_V:.2f} V maximum"
    )
    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=Path("/tmp/lc.net"))
    parser.add_argument(
        "--policy",
        choices=("bench-range", "sfh2201-1000lx-example"),
        default="bench-range",
        help="Range policy to evaluate. The 1000 lx policy is intentionally expected to fail.",
    )
    args = parser.parse_args()

    nets = parse_netlist(args.netlist)
    comps = component_by_ref(args.netlist)
    errors = check_topology(nets, comps)
    range_errors, notes = check_range(args.policy)
    errors.extend(range_errors)

    if errors:
        print(f"FAIL TIA readout budget ({args.policy}): {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        for note in notes:
            print(f"  note: {note}")
        return 1

    print(f"PASS TIA readout budget ({args.policy})")
    print("  topology: SFH2201 cathode +5V bias, anode to OPA380 summing node, 2M/10pF feedback, VOUT1..4 into AD7606")
    for note in notes:
        print(f"  {note}")
    print("  production caveat: optical signal range and calibration are still not proven by this first-order check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
