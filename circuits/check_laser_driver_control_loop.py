#!/usr/bin/env python3
"""Laser-driver analog control-loop topology and gate-drive budget check.

This complements check_laser_current_budget.py. That checker asks whether the
selected diode/rail/current cases are thermally acceptable. This one asks
whether the PWM divider, TLV9001 input/output range, AO3400A gate drive, sense
tap, and schematic topology match the intended low-side current loop.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from circuit_designators import ref_for


ESP32_REF = "U9"
PWM_FULL_SCALE_V = 3.3
PWM_TOP_OHMS = 10_000.0
PWM_PULLDOWN_OHMS = 30_000.0
SENSE_OHMS = 10.0
TLV_SUPPLY_V = 5.0
TLV_INPUT_LOW_V = -0.1
TLV_INPUT_HIGH_V = TLV_SUPPLY_V + 0.1
TLV_OUTPUT_HIGH_LIGHT_LOAD_V = TLV_SUPPLY_V - 0.020
AO3400A_VGS_ABS_MAX_V = 12.0
AO3400A_RDS_ON_CHARACTERIZED_VGS_V = 2.5
DEFAULT_GATE_DRIVE_MARGIN_V = 0.25
SELECTED_MAX_CURRENT_A = 0.120


@dataclass(frozen=True)
class Channel:
    color: str
    pwm_net: str
    pwm_pin: str
    isense_net: str
    isense_pin: str
    laser_n_net: str
    laser_vplus_pin: str
    laser_n_pin: str


CHANNELS = (
    Channel("IR", "PWM1", "18", "ISENSE1", "4", "LASER_N1", "2", "1"),
    Channel("RED", "PWM2", "19", "ISENSE2", "5", "LASER_N2", "2", "1"),
    Channel("GREEN", "PWM3", "20", "ISENSE3", "6", "LASER_N3", "2", "1"),
    Channel("BLUE", "PWM4", "9", "ISENSE4", "7", "LASER_N4", "1", "3"),
)


def component_by_ref(path: Path) -> dict[str, dict[str, str]]:
    return {comp["ref"]: comp for comp in parse_components(path)}


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
    expected: set[tuple[str, str]],
) -> None:
    actual = node_set(nets, net)
    missing = sorted(expected - actual)
    if missing:
        errors.append(f"{net}: missing {missing}; actual {sorted(actual)}")


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
    expected = {"value": value, "footprint": footprint, "mpn": mpn, "lcsc": lcsc}
    actual = {key: comp.get(key, "") for key in expected}
    if actual != expected:
        errors.append(f"{ref}: expected {expected}, got {actual}")


def command_voltage_v() -> float:
    return PWM_FULL_SCALE_V * PWM_PULLDOWN_OHMS / (PWM_TOP_OHMS + PWM_PULLDOWN_OHMS)


def command_current_a() -> float:
    return command_voltage_v() / SENSE_OHMS


def check_topology(
    nets: dict[str, list[tuple[str, str, str, str]]],
    comps: dict[str, dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    for channel in CHANNELS:
        sheet = f"LASER_{channel.color}"
        ld = ref_for(sheet, "LD")
        tlv = ref_for(sheet, "U11")
        mosfet = ref_for(sheet, "Q1")
        gate_r = ref_for(sheet, "R31")
        sense_r = ref_for(sheet, "R11")
        isense_r = ref_for(sheet, "R12")
        decouple_c = ref_for(sheet, "C22")
        pwm_r = ref_for(sheet, "R21")
        pulldown_r = ref_for(sheet, "R22")
        pwm_c = ref_for(sheet, "C21")
        comp_c = ref_for(sheet, "CC")

        expect_component(
            errors,
            comps,
            tlv,
            "TLV9001",
            "Package_TO_SOT_SMD:SOT-23-5",
            "TLV9001IDBVR",
            "C398363",
        )
        expect_component(
            errors,
            comps,
            mosfet,
            "AO3400A",
            "Package_TO_SOT_SMD:SOT-23",
            "AO3400A",
            "C20917",
        )
        expect_component(
            errors,
            comps,
            sense_r,
            "10R 2W",
            "Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder",
            "HoCR2512-2W-10R-1%",
            "C5123624",
        )
        expect_component(
            errors,
            comps,
            pulldown_r,
            "30k LIMIT",
            "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder",
            "0603WAF3002T5E",
            "C22984",
        )

        require_exact(errors, nets, channel.pwm_net, {(ESP32_REF, channel.pwm_pin), (pwm_r, "1")})
        require_exact(errors, nets, f"Net-({tlv}-+)", {(pwm_c, "1"), (pwm_r, "2"), (pulldown_r, "1"), (tlv, "3")})
        require_exact(errors, nets, f"/LASER_{channel.color}/LOUT", {(comp_c, "2"), (gate_r, "1"), (tlv, "1")})
        require_exact(errors, nets, f"Net-({mosfet}-G)", {(gate_r, "2"), (mosfet, "1")})
        require_exact(
            errors,
            nets,
            f"/LASER_{channel.color}/FB",
            {(comp_c, "1"), (mosfet, "2"), (sense_r, "1"), (isense_r, "1"), (tlv, "4")},
        )
        require_exact(errors, nets, channel.isense_net, {(ESP32_REF, channel.isense_pin), (isense_r, "2")})
        require_exact(errors, nets, channel.laser_n_net, {(ld, channel.laser_n_pin), (mosfet, "3")})
        require_contains(errors, nets, "LASER_V+", {(ld, channel.laser_vplus_pin)})
        require_contains(errors, nets, "+5V", {(tlv, "5"), (decouple_c, "1")})
        require_contains(errors, nets, "GND", {(tlv, "2"), (decouple_c, "2"), (sense_r, "2"), (pulldown_r, "2"), (pwm_c, "2")})
    return errors


def check_budget(policy: str, gate_drive_margin_v: float) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    command_v = command_voltage_v()
    clamp_current_a = command_current_a()
    checked_current_a = SELECTED_MAX_CURRENT_A if policy == "selected-max-current" else clamp_current_a
    source_v = checked_current_a * SENSE_OHMS
    vgs_available_v = TLV_OUTPUT_HIGH_LIGHT_LOAD_V - source_v
    vgs_characterized_margin_v = vgs_available_v - AO3400A_RDS_ON_CHARACTERIZED_VGS_V

    if policy not in {"selected-max-current", "hardware-clamp-gate-margin"}:
        errors.append(f"unknown policy {policy!r}")
    if not (TLV_INPUT_LOW_V <= command_v <= TLV_INPUT_HIGH_V):
        errors.append(f"PWM command clamp {command_v:.3f} V is outside TLV9001 input range")
    if not (TLV_INPUT_LOW_V <= source_v <= TLV_INPUT_HIGH_V):
        errors.append(f"sense feedback voltage {source_v:.3f} V is outside TLV9001 input range")
    if TLV_OUTPUT_HIGH_LIGHT_LOAD_V > AO3400A_VGS_ABS_MAX_V:
        errors.append("TLV9001 output could exceed AO3400A absolute gate-source maximum")
    if policy == "hardware-clamp-gate-margin" and vgs_characterized_margin_v < gate_drive_margin_v:
        errors.append(
            f"hardware clamp leaves only {vgs_characterized_margin_v:.3f} V above the AO3400A 2.5 V "
            f"RDS(on) characterization point; required margin is {gate_drive_margin_v:.3f} V"
        )

    notes.append(
        f"PWM divider clamp: 3.30 V * 30k/(10k+30k) = {command_v:.3f} V -> {clamp_current_a * 1000.0:.1f} mA"
    )
    notes.append(
        f"{policy}: checked current={checked_current_a * 1000.0:.1f} mA, sense feedback={source_v:.3f} V"
    )
    notes.append(
        f"TLV9001 input range policy: {TLV_INPUT_LOW_V:.1f}..{TLV_INPUT_HIGH_V:.1f} V on a 5 V rail"
    )
    notes.append(
        f"available AO3400A Vgs at checked current ~= {vgs_available_v:.3f} V; "
        f"margin vs 2.5 V characterized point={vgs_characterized_margin_v:.3f} V"
    )
    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=Path("/tmp/lc.net"))
    parser.add_argument(
        "--policy",
        choices=("selected-max-current", "hardware-clamp-gate-margin"),
        default="selected-max-current",
    )
    parser.add_argument("--gate-drive-margin-v", type=float, default=DEFAULT_GATE_DRIVE_MARGIN_V)
    args = parser.parse_args()

    nets = parse_netlist(args.netlist)
    comps = component_by_ref(args.netlist)
    errors = check_topology(nets, comps)
    budget_errors, notes = check_budget(args.policy, args.gate_drive_margin_v)
    errors.extend(budget_errors)

    if errors:
        print(f"FAIL laser-driver control-loop budget ({args.policy}): {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        for note in notes:
            print(f"  note: {note}")
        return 1

    print(f"PASS laser-driver control-loop budget ({args.policy})")
    print("  topology: PWM divider -> TLV9001 +IN, sense resistor high side -> -IN, OUT -> AO3400A gate, drain -> LASER_Nx")
    for note in notes:
        print(f"  {note}")
    print("  production caveat: this does not waive diode current limits, MOSFET SOA/heat, optical safety, or firmware clamps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
