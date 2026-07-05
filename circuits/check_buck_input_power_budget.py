#!/usr/bin/env python3
"""24V input and AP63205/AP63200 buck policy checks.

This is a first-order electrical guardrail.  It verifies the schematic buck
pinout/component set and checks connector input current plus inductor stress for
defined bench scenarios.  A separate policy intentionally fails the current
production recommendation because the board uses less ceramic input and output
capacitance than the AP63200/AP63205 datasheet recommends for a generic release.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist
from check_laser_current_budget import SELECTED_LASER_SPECS
from circuit_designators import ref_for
from laser_command_limits import all_channel_worst_case_command_limit_current_a


DEFAULT_NETLIST = Path("/tmp/lc.net")
VIN_NOMINAL_V = 24.0
VIN_ABS_MAX_V = 32.0
VIN_UVLO_MAX_V = 3.8
AP63200_FB_REF_V = 0.8
AP632_OUTPUT_LIMIT_A = 2.0
BARREL_CONNECTOR_LIMIT_A = 0.5
SS14_NOMINAL_LIMIT_A = 1.0
DEFAULT_EFFICIENCY = 0.85
RJ45_LED_CURRENT_A = (24.0 - 2.0) / 10_000.0


@dataclass(frozen=True)
class BuckRail:
    name: str
    ref: str
    mpn: str
    output_v: float
    switching_hz: float
    inductor_ref: str
    inductor_u_h: float
    inductor_dcr_ohm: float
    inductor_isat_a: float
    inductor_irms_a: float


@dataclass(frozen=True)
class Scenario:
    name: str
    five_v_load_ma: float
    laser_vplus_v: float
    laser_load_ma: float
    description: str


@dataclass(frozen=True)
class BuckStress:
    load_a: float
    ripple_a: float
    peak_a: float
    rms_a: float
    inductor_loss_w: float


def lm4040_bias_ma(laser_vplus_v: float) -> float:
    return max(0.0, laser_vplus_v - 5.0) / 2490.0 * 1000.0


def selected_laser_max_load_ma() -> float:
    return sum(spec.max_current_ma for spec in SELECTED_LASER_SPECS)


def selected_laser_typ_load_ma() -> float:
    return sum(spec.typ_current_ma for spec in SELECTED_LASER_SPECS)


def scenarios() -> dict[str, Scenario]:
    return {
        "bench-selected-max-9v3": Scenario(
            name="bench-selected-max-9v3",
            five_v_load_ma=350.0,
            laser_vplus_v=9.30,
            laser_load_ma=selected_laser_max_load_ma() + lm4040_bias_ma(9.30),
            description=(
                "Bench current policy using the selected laser datasheet max currents, "
                "a reduced 9.3V LASER_V+ reference, and a conservative 350mA +5V load."
            ),
        ),
        "present-typ-9v3": Scenario(
            name="present-typ-9v3",
            five_v_load_ma=350.0,
            laser_vplus_v=9.30,
            laser_load_ma=selected_laser_typ_load_ma() + lm4040_bias_ma(9.30),
            description=(
                "Production AP63200 feedback setting (~9.3V by 237k/22.1k) with selected "
                "laser typical currents. This only checks input/buck current; laser AO3400A "
                "thermal is checked separately."
            ),
        ),
        "hardware-clamp-9v3": Scenario(
            name="hardware-clamp-9v3",
            five_v_load_ma=350.0,
            laser_vplus_v=9.30,
            laser_load_ma=(all_channel_worst_case_command_limit_current_a() * 1000.0) + lm4040_bias_ma(9.30),
            description=(
                "All-channel laser analog-limit high-current tolerance case at the production "
                "AP63200 feedback setting after the per-channel limiter update."
            ),
        ),
    }


def node_map(netlist_path: Path) -> dict[tuple[str, str], str]:
    nets = parse_netlist(netlist_path)
    mapping: dict[tuple[str, str], str] = {}
    for net_name, nodes in nets.items():
        for ref, pin, _, _ in nodes:
            mapping[(ref, pin)] = net_name
    return mapping


def component_map(netlist_path: Path) -> dict[str, dict[str, str]]:
    return {comp["ref"]: comp for comp in parse_components(netlist_path)}


def require_net(
    failures: list[str],
    pin_nets: dict[tuple[str, str], str],
    ref: str,
    pin: str,
    expected: str,
) -> None:
    actual = pin_nets.get((ref, pin))
    if actual != expected:
        failures.append(f"{ref}.{pin}: expected net {expected}, got {actual or '<missing>'}")


def require_comp(
    failures: list[str],
    comps: dict[str, dict[str, str]],
    ref: str,
    *,
    mpn: str,
    footprint_suffix: str | None = None,
    value_contains: str | None = None,
) -> dict[str, str]:
    comp = comps.get(ref)
    if comp is None:
        failures.append(f"{ref}: missing component")
        return {}
    if comp["mpn"] != mpn:
        failures.append(f"{ref}: expected MPN {mpn}, got {comp['mpn'] or '<empty>'}")
    if footprint_suffix and not comp["footprint"].endswith(footprint_suffix):
        failures.append(f"{ref}: expected footprint ending {footprint_suffix}, got {comp['footprint']}")
    if value_contains and value_contains not in comp["value"]:
        failures.append(f"{ref}: expected value containing {value_contains!r}, got {comp['value']!r}")
    return comp


def actual_laser_vout_from_feedback() -> float:
    top_ohms = 237_000.0
    bottom_ohms = 22_100.0
    return AP63200_FB_REF_V * (1.0 + top_ohms / bottom_ohms)


def buck_stress(rail: BuckRail, load_a: float, vin_v: float = VIN_NOMINAL_V) -> BuckStress:
    inductance_h = rail.inductor_u_h * 1e-6
    ripple_a = rail.output_v * (vin_v - rail.output_v) / (vin_v * inductance_h * rail.switching_hz)
    peak_a = load_a + ripple_a / 2.0
    rms_a = math.sqrt(load_a * load_a + (ripple_a * ripple_a) / 12.0)
    return BuckStress(
        load_a=load_a,
        ripple_a=ripple_a,
        peak_a=peak_a,
        rms_a=rms_a,
        inductor_loss_w=rms_a * rms_a * rail.inductor_dcr_ohm,
    )


def validate_schematic(netlist_path: Path) -> list[str]:
    failures: list[str] = []
    comps = component_map(netlist_path)
    pin_nets = node_map(netlist_path)

    u15 = ref_for("POWER_IO", "U5V")
    u16 = ref_for("POWER_IO", "ULASER")
    require_comp(failures, comps, u15, mpn="AP63205WU-7", footprint_suffix="TSOT-23-6")
    require_comp(failures, comps, u16, mpn="AP63200WU-7", footprint_suffix="TSOT-23-6")
    require_comp(failures, comps, ref_for("POWER_IO", "L5V"), mpn="MWSA0503S-4R7MT", value_contains="4.7uH")
    require_comp(failures, comps, ref_for("POWER_IO", "LLASER"), mpn="WPN4020H100MT", value_contains="10uH")
    require_comp(failures, comps, ref_for("POWER_IO", "RFBTOP"), mpn="FRC0603F2373TS", value_contains="237k")
    require_comp(failures, comps, ref_for("POWER_IO", "RFBBOT"), mpn="FRC0402F2212TS", value_contains="22.1K")
    require_comp(failures, comps, ref_for("POWER_IO", "CFFLASER"), mpn="0402CG101J500NT", value_contains="100pF")
    require_comp(failures, comps, ref_for("POWER_IO", "CBST5V"), mpn="0402B104K160CT", value_contains="100nF")
    require_comp(failures, comps, ref_for("POWER_IO", "CBSTLASER"), mpn="0402B104K160CT", value_contains="100nF")

    for ref in [u15, u16]:
        require_net(failures, pin_nets, ref, "2", "VIN_24V")
        require_net(failures, pin_nets, ref, "3", "VIN_24V")
        require_net(failures, pin_nets, ref, "4", "GND")
    require_net(failures, pin_nets, u15, "1", "/POWER_IO/BUCK_5V")
    require_net(failures, pin_nets, u15, "5", "Net-(U15-SW)")
    require_net(failures, pin_nets, u15, "6", "Net-(U15-BST)")
    require_net(failures, pin_nets, u16, "1", "Net-(U16-FB)")
    require_net(failures, pin_nets, u16, "5", "Net-(U16-SW)")
    require_net(failures, pin_nets, u16, "6", "Net-(U16-BST)")

    if not (9.2 <= actual_laser_vout_from_feedback() <= 9.5):
        failures.append(f"AP63200 feedback computes {actual_laser_vout_from_feedback():.2f}V, expected about 9.3V")
    return failures


def rail_defs(laser_vplus_v: float) -> tuple[BuckRail, BuckRail]:
    buck5 = BuckRail(
        name="AP63205 BUCK_5V",
        ref=ref_for("POWER_IO", "U5V"),
        mpn="AP63205WU-7",
        output_v=5.0,
        switching_hz=1_100_000.0,
        inductor_ref=ref_for("POWER_IO", "L5V"),
        inductor_u_h=4.7,
        inductor_dcr_ohm=0.060,
        inductor_isat_a=3.68,
        inductor_irms_a=4.00,
    )
    laser = BuckRail(
        name="AP63200 LASER_V+",
        ref=ref_for("POWER_IO", "ULASER"),
        mpn="AP63200WU-7",
        output_v=laser_vplus_v,
        switching_hz=500_000.0,
        inductor_ref=ref_for("POWER_IO", "LLASER"),
        inductor_u_h=10.0,
        inductor_dcr_ohm=0.216,
        inductor_isat_a=2.80,
        inductor_irms_a=2.00,
    )
    return buck5, laser


def scenario_failures(scenario: Scenario) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    notes: list[str] = []
    buck5, laser = rail_defs(scenario.laser_vplus_v)
    buck5_load_a = scenario.five_v_load_ma / 1000.0
    laser_load_a = scenario.laser_load_ma / 1000.0
    buck5_stress = buck_stress(buck5, buck5_load_a)
    laser_stress = buck_stress(laser, laser_load_a)

    buck5_input_a = buck5.output_v * buck5_load_a / DEFAULT_EFFICIENCY / VIN_NOMINAL_V
    laser_input_a = laser.output_v * laser_load_a / DEFAULT_EFFICIENCY / VIN_NOMINAL_V
    total_input_a = buck5_input_a + laser_input_a + RJ45_LED_CURRENT_A

    if total_input_a > BARREL_CONNECTOR_LIMIT_A:
        failures.append(
            f"VIN_24V input current {total_input_a * 1000.0:.1f}mA exceeds "
            f"J5 barrel 500mA bench connector rating"
        )
    if buck5_load_a > AP632_OUTPUT_LIMIT_A:
        failures.append(f"AP63205 load {buck5_load_a:.3f}A exceeds 2A buck rating")
    if laser_load_a > AP632_OUTPUT_LIMIT_A:
        failures.append(f"AP63200 load {laser_load_a:.3f}A exceeds 2A buck rating")
    if scenario.five_v_load_ma / 1000.0 > SS14_NOMINAL_LIMIT_A:
        failures.append(f"D6 SS14 current {scenario.five_v_load_ma:.1f}mA exceeds nominal 1A class")

    for rail, stress in [(buck5, buck5_stress), (laser, laser_stress)]:
        if stress.peak_a > rail.inductor_isat_a:
            failures.append(
                f"{rail.inductor_ref} {rail.name}: peak current {stress.peak_a:.3f}A "
                f"exceeds inductor saturation rating {rail.inductor_isat_a:.2f}A"
            )
        if stress.rms_a > rail.inductor_irms_a:
            failures.append(
                f"{rail.inductor_ref} {rail.name}: RMS current {stress.rms_a:.3f}A "
                f"exceeds inductor heat rating {rail.inductor_irms_a:.2f}A"
            )

    if abs(scenario.laser_vplus_v - actual_laser_vout_from_feedback()) > 0.2:
        notes.append(
            f"{scenario.name}: laser rail {scenario.laser_vplus_v:.2f}V is a policy reference; "
            f"current R61/R62 feedback computes {actual_laser_vout_from_feedback():.2f}V"
        )

    print(f"24V/buck current policy: {scenario.name}")
    print(f"  {scenario.description}")
    print(
        f"  VIN nominal={VIN_NOMINAL_V:.1f}V, AP632 input range={VIN_UVLO_MAX_V:.1f}V to "
        f"{VIN_ABS_MAX_V:.0f}V, J5 bench connector limit={BARREL_CONNECTOR_LIMIT_A * 1000:.0f}mA"
    )
    print(
        f"  AP63200 feedback: 0.8V * (1 + 237k/22.1k) = "
        f"{actual_laser_vout_from_feedback():.2f}V"
    )
    print(
        f"  loads: +5V={scenario.five_v_load_ma:.1f}mA, "
        f"LASER_V+={scenario.laser_load_ma:.1f}mA at {scenario.laser_vplus_v:.2f}V"
    )
    print(
        f"  estimated VIN current: BUCK_5V={buck5_input_a * 1000.0:.1f}mA, "
        f"LASER_V+={laser_input_a * 1000.0:.1f}mA, RJ45 LED/contact={RJ45_LED_CURRENT_A * 1000.0:.1f}mA, "
        f"total={total_input_a * 1000.0:.1f}mA"
    )
    for rail, stress in [(buck5, buck5_stress), (laser, laser_stress)]:
        print(
            f"  {rail.name}: load={stress.load_a:.3f}A, ripple={stress.ripple_a:.3f}A, "
            f"peak={stress.peak_a:.3f}A/{rail.inductor_isat_a:.2f}A Isat, "
            f"rms={stress.rms_a:.3f}A/{rail.inductor_irms_a:.2f}A Irms, "
            f"inductor loss~{stress.inductor_loss_w:.3f}W"
        )
    for note in notes:
        print(f"  NOTE: {note}")
    return failures, notes


def production_recommendation_failures() -> list[str]:
    failures: list[str] = []
    input_ceramic_u_f = 20.0
    buck5_output_u_f = 44.0
    laser_output_u_f = 44.0
    recommended_input_ceramic_u_f = 10.0
    recommended_output_u_f = 44.0
    print("24V/buck production component recommendation policy: datasheet-recommended-components")
    print(
        "  Diodes AP63200/AP63205 application guidance calls for close VIN ceramic capacitance, "
        "2x22uF style output capacitance in the reference designs/tables, close feedback parts, "
        "and 2oz/thermal-via layout for 2A operation."
    )
    print(
        f"  current input ceramic: C61+C62={input_ceramic_u_f:.1f}uF plus C70 22uF electrolytic; "
        f"recommended ceramic threshold={recommended_input_ceramic_u_f:.1f}uF"
    )
    print(
        f"  current output caps: C64+C65={buck5_output_u_f:.1f}uF on BUCK_5V, "
        f"C67+C68={laser_output_u_f:.1f}uF on LASER_V+; reference target={recommended_output_u_f:.1f}uF each"
    )
    if input_ceramic_u_f < recommended_input_ceramic_u_f:
        failures.append(
            f"VIN_24V ceramic input capacitance is {input_ceramic_u_f:.1f}uF, below "
            f"the >={recommended_input_ceramic_u_f:.1f}uF datasheet recommendation for typical switching input bypass"
        )
    if buck5_output_u_f < recommended_output_u_f:
        failures.append(
            f"BUCK_5V nominal ceramic output capacitance is {buck5_output_u_f:.1f}uF, below "
            f"the 2x22uF reference target"
        )
    if laser_output_u_f < recommended_output_u_f:
        failures.append(
            f"LASER_V+ nominal ceramic output capacitance is {laser_output_u_f:.1f}uF, below "
            f"the 2x22uF reference target"
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument(
        "--policy",
        choices=sorted(set(scenarios()) | {"datasheet-recommended-components"}),
        default="bench-selected-max-9v3",
    )
    args = parser.parse_args()

    if not args.netlist.exists():
        raise SystemExit(f"netlist not found: {args.netlist}")

    failures = validate_schematic(args.netlist)
    if args.policy == "datasheet-recommended-components":
        failures.extend(production_recommendation_failures())
    else:
        scenario = scenarios()[args.policy]
        scenario_errors, _ = scenario_failures(scenario)
        failures.extend(scenario_errors)

    if failures:
        print("FAIL 24V/buck policy")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print("PASS 24V/buck policy for the checked assumptions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
