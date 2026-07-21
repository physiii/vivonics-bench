#!/usr/bin/env python3
"""Laser current-loop electrical/thermal budget for the bench controller.

This checks the analog current-command limit, the 10 ohm sense resistor power,
and the AO3400A linear-pass MOSFET dissipation for a selected laser supply and
diode forward-voltage assumption.  It does not approve a real laser pinout;
each diode MPN still needs its own pin table, forward-voltage range, current
limit, optical safety limit, and monitor-PD polarity checked.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace

from laser_command_limits import (
    PWM_FULL_SCALE_V,
    PWM_TOP_OHMS,
    SENSE_OHMS,
    all_channel_command_limit_current_a,
    all_channel_worst_case_command_limit_current_a,
    limiter_for_color,
)

SENSE_RESISTOR_RATING_W = 2.0
AO3400A_THETA_JA_C_PER_W = 125.0
DEFAULT_TARGET_JUNCTION_C = 125.0
DEFAULT_MOSFET_HEADROOM_V = 0.50
EPSILON = 1e-9


@dataclass(frozen=True)
class Policy:
    name: str
    laser_vplus_v: float
    diode_vf_max_v: float
    ambient_c: float
    description: str


@dataclass(frozen=True)
class SelectedLaserSpec:
    channel: str
    ref: str
    mpn: str
    optical_power_mw: float
    typ_current_ma: float
    max_current_ma: float
    typ_vf_v: float
    max_vf_v: float
    source_note: str


@dataclass(frozen=True)
class SelectedLaserCase:
    spec: SelectedLaserSpec
    laser_vplus_v: float
    current_ma: float
    diode_vf_v: float
    case_note: str


@dataclass(frozen=True)
class SelectedLaserPolicy:
    name: str
    description: str
    cases: tuple[SelectedLaserCase, ...]


@dataclass(frozen=True)
class Budget:
    current_a: float
    sense_drop_v: float
    sense_power_w: float
    mosfet_vds_v: float
    mosfet_power_w: float
    mosfet_power_limit_w: float
    min_laser_vplus_v: float
    max_laser_vplus_v: float


SELECTED_LASER_SPECS = (
    SelectedLaserSpec(
        channel="IR",
        ref="LD1",
        mpn="D7805I",
        optical_power_mw=5.0,
        typ_current_ma=35.0,
        max_current_ma=50.0,
        typ_vf_v=2.1,
        max_vf_v=2.5,
        source_note="US-Lasers D7805I 780nm 5mW datasheet",
    ),
    SelectedLaserSpec(
        channel="RED",
        ref="LD2",
        mpn="D6505I",
        optical_power_mw=5.0,
        typ_current_ma=20.0,
        max_current_ma=25.0,
        typ_vf_v=2.2,
        max_vf_v=2.6,
        source_note=(
            "Digikey D650-5I 650nm 5mW datasheet; lower-current source used "
            "conservatively because the US-Lasers mirror gives a conflicting "
            "40mA typ / 60mA max operating-current table"
        ),
    ),
    SelectedLaserSpec(
        channel="GREEN",
        ref="LD3",
        mpn="PLT5 520EB_P",
        optical_power_mw=20.0,
        typ_current_ma=65.0,
        max_current_ma=78.0,
        typ_vf_v=5.4,
        max_vf_v=6.1,
        source_note="ams OSRAM PLT5 520EB_P datasheet",
    ),
    SelectedLaserSpec(
        channel="BLUE",
        ref="LD4",
        mpn="PLT5 450GB",
        optical_power_mw=100.0,
        typ_current_ma=87.0,
        max_current_ma=120.0,
        typ_vf_v=5.2,
        max_vf_v=6.5,
        source_note="ams OSRAM PLT5 450GB datasheet",
    ),
)


POLICIES = {
    "green-high-vf-10v5": Policy(
        name="green-high-vf-10v5",
        laser_vplus_v=10.5,
        diode_vf_max_v=7.0,
        ambient_c=85.0,
        description=(
            "High-forward-voltage green reference using 7.0 V diode headroom "
            "and a 10.5 V laser rail. This is a thermal policy reference, not "
            "an optical-safety or board-temperature release."
        ),
    ),
    "green-high-vf-12v": Policy(
        name="green-high-vf-12v",
        laser_vplus_v=12.0,
        diode_vf_max_v=7.0,
        ambient_c=85.0,
        description=(
            "High-forward-voltage green reference at a 12 V laser rail; this is "
            "expected to fail the conservative continuous AO3400A thermal budget."
        ),
    ),
    "low-vf-diode-on-10v5": Policy(
        name="low-vf-diode-on-10v5",
        laser_vplus_v=10.5,
        diode_vf_max_v=2.5,
        ambient_c=85.0,
        description=(
            "Low-forward-voltage red/IR-style diode on the green-sized 10.5 V "
            "common laser rail; this is expected to fail unless current is reduced."
        ),
    ),
}


def command_limit_current_a() -> float:
    return max(limiter_for_color(spec.channel).command_current_a for spec in SELECTED_LASER_SPECS)


def channel_command_limit_current_a(channel: str) -> float:
    return limiter_for_color(channel).command_current_a


def make_selected_policy(name: str, description: str, laser_vplus_v: float, point: str) -> SelectedLaserPolicy:
    if point not in {"typ", "max", "clamp"}:
        raise ValueError(f"unsupported selected-laser policy point: {point}")
    cases: list[SelectedLaserCase] = []
    for spec in SELECTED_LASER_SPECS:
        if point == "typ":
            current_ma = spec.typ_current_ma
            diode_vf_v = spec.typ_vf_v
            case_note = "datasheet typical operating point"
        elif point == "max":
            current_ma = spec.max_current_ma
            diode_vf_v = spec.max_vf_v
            case_note = "datasheet maximum operating-current point"
        else:
            current_ma = limiter_for_color(spec.channel).worst_case_current_a * 1000.0
            diode_vf_v = spec.max_vf_v
            case_note = "per-channel analog command limit worst-case with datasheet max Vf"
        cases.append(
            SelectedLaserCase(
                spec=spec,
                laser_vplus_v=laser_vplus_v,
                current_ma=current_ma,
                diode_vf_v=diode_vf_v,
                case_note=case_note,
            )
        )
    return SelectedLaserPolicy(name=name, description=description, cases=tuple(cases))


SELECTED_LASER_POLICIES = {
    "selected-diodes-typ-9v3": make_selected_policy(
        name="selected-diodes-typ-9v3",
        laser_vplus_v=9.30,
        point="typ",
        description=(
            "Actual LD1-LD4 MPNs at datasheet typical operating current/voltage "
            "on the production AP63200 LASER_V+ setting (~9.3V). This is the "
            "primary production thermal gate for the common-rail architecture."
        ),
    ),
    "selected-diodes-max-9v3": make_selected_policy(
        name="selected-diodes-max-9v3",
        laser_vplus_v=9.30,
        point="max",
        description=(
            "Actual LD1-LD4 MPNs at datasheet maximum operating current/voltage "
            "on the production 9.3V common LASER_V+ reference. All selected "
            "diodes must pass this gate before production release."
        ),
    ),
    "selected-diodes-hardware-clamp-9v3": make_selected_policy(
        name="selected-diodes-hardware-clamp-9v3",
        laser_vplus_v=9.30,
        point="clamp",
        description=(
            "Actual LD1-LD4 MPNs driven to the per-channel analog command limits "
            "on the production 9.3V LASER_V+ setting. This proves the schematic "
            "divider values no longer expose every source to the old 247.5mA "
            "common limiter."
        ),
    ),
}


def max_mosfet_power_w(ambient_c: float, target_junction_c: float) -> float:
    return max(0.0, (target_junction_c - ambient_c) / AO3400A_THETA_JA_C_PER_W)


def evaluate_budget(
    *,
    laser_vplus_v: float,
    diode_vf_v: float,
    current_a: float,
    ambient_c: float,
    target_junction_c: float,
    mosfet_headroom_v: float,
) -> Budget:
    sense_drop_v = current_a * SENSE_OHMS
    sense_power_w = current_a * current_a * SENSE_OHMS
    mosfet_vds_v = laser_vplus_v - diode_vf_v - sense_drop_v
    mosfet_power_w = max(0.0, mosfet_vds_v * current_a)
    mosfet_power_limit_w = max_mosfet_power_w(ambient_c, target_junction_c)
    min_laser_vplus_v = diode_vf_v + sense_drop_v + mosfet_headroom_v
    max_laser_vplus_v = diode_vf_v + sense_drop_v + (mosfet_power_limit_w / current_a)
    return Budget(
        current_a=current_a,
        sense_drop_v=sense_drop_v,
        sense_power_w=sense_power_w,
        mosfet_vds_v=mosfet_vds_v,
        mosfet_power_w=mosfet_power_w,
        mosfet_power_limit_w=mosfet_power_limit_w,
        min_laser_vplus_v=min_laser_vplus_v,
        max_laser_vplus_v=max_laser_vplus_v,
    )


def policy_from_args(args: argparse.Namespace) -> Policy:
    policy = POLICIES[args.policy]
    if args.laser_vplus_v is None and args.diode_vf_max_v is None and args.ambient_c is None:
        return policy
    return Policy(
        name=f"{policy.name}-custom",
        laser_vplus_v=args.laser_vplus_v if args.laser_vplus_v is not None else policy.laser_vplus_v,
        diode_vf_max_v=args.diode_vf_max_v if args.diode_vf_max_v is not None else policy.diode_vf_max_v,
        ambient_c=args.ambient_c if args.ambient_c is not None else policy.ambient_c,
        description=policy.description + " Custom override applied.",
    )


def selected_policy_from_args(args: argparse.Namespace) -> SelectedLaserPolicy:
    policy = SELECTED_LASER_POLICIES[args.policy]
    if args.laser_vplus_v is None:
        return policy
    return replace(
        policy,
        name=f"{policy.name}-custom",
        description=policy.description + " Custom LASER_V+ override applied.",
        cases=tuple(replace(case, laser_vplus_v=args.laser_vplus_v) for case in policy.cases),
    )


def selected_policy_failures(
    case: SelectedLaserCase,
    budget: Budget,
    ambient_c: float,
    mosfet_headroom_v: float,
) -> list[str]:
    spec = case.spec
    failures: list[str] = []
    if case.current_ma > spec.max_current_ma + EPSILON:
        failures.append(
            f"{spec.ref} {spec.mpn}: commanded {case.current_ma:.1f}mA exceeds "
            f"datasheet operating-current max {spec.max_current_ma:.1f}mA"
        )
    if budget.sense_power_w > SENSE_RESISTOR_RATING_W + EPSILON:
        failures.append(
            f"{spec.ref} {spec.mpn}: sense resistor dissipates {budget.sense_power_w:.3f}W, "
            f"above {SENSE_RESISTOR_RATING_W:.1f}W rating"
        )
    if budget.mosfet_vds_v + EPSILON < mosfet_headroom_v:
        failures.append(
            f"{spec.ref} {spec.mpn}: AO3400A Vds headroom is {budget.mosfet_vds_v:.2f}V, "
            f"below {mosfet_headroom_v:.2f}V target"
        )
    if budget.mosfet_power_w > budget.mosfet_power_limit_w + EPSILON:
        failures.append(
            f"{spec.ref} {spec.mpn}: AO3400A dissipates {budget.mosfet_power_w:.3f}W, "
            f"above {budget.mosfet_power_limit_w:.3f}W continuous budget at {ambient_c:.1f}degC"
        )
    return failures


def run_selected_policy(args: argparse.Namespace) -> int:
    if args.diode_vf_max_v is not None:
        raise SystemExit("--diode-vf-max-v is only valid with the generic single-diode policies")

    policy = selected_policy_from_args(args)
    ambient_c = args.ambient_c if args.ambient_c is not None else 85.0
    failures: list[str] = []

    print(f"Selected laser current-loop policy: {policy.name}")
    print(f"  {policy.description}")
    print(
        f"  all-channel analog command limit sum={all_channel_command_limit_current_a() * 1000.0:.1f}mA nominal, "
        f"{all_channel_worst_case_command_limit_current_a() * 1000.0:.1f}mA at 1% high-current tolerance corner"
    )
    print(
        f"  AO3400A continuous budget={max_mosfet_power_w(ambient_c, args.target_junction_c):.3f}W "
        f"at ambient={ambient_c:.1f}degC, target Tj={args.target_junction_c:.1f}degC"
    )

    for case in policy.cases:
        budget = evaluate_budget(
            laser_vplus_v=case.laser_vplus_v,
            diode_vf_v=case.diode_vf_v,
            current_a=case.current_ma / 1000.0,
            ambient_c=ambient_c,
            target_junction_c=args.target_junction_c,
            mosfet_headroom_v=args.mosfet_headroom_v,
        )
        spec = case.spec
        print(
            f"  {spec.ref} {spec.channel} {spec.mpn}: {case.case_note}; "
            f"Popt={spec.optical_power_mw:g}mW, I={case.current_ma:.1f}mA "
            f"(datasheet max {spec.max_current_ma:.1f}mA), Vf={case.diode_vf_v:.2f}V, "
            f"LASER_V+={case.laser_vplus_v:.2f}V"
        )
        if policy.name.endswith("hardware-clamp-9v3"):
            limiter = limiter_for_color(spec.channel)
            print(
                f"    limiter {limiter.value} ({limiter.mpn}, {limiter.lcsc}) sets "
                f"Vcmd={limiter.command_voltage_v:.3f}V / Icmd={limiter.command_current_a * 1000.0:.1f}mA nominal, "
                f"{limiter.worst_case_current_a * 1000.0:.1f}mA worst case"
            )
        print(
            f"    sense drop={budget.sense_drop_v:.3f}V, sense power={budget.sense_power_w:.3f}W, "
            f"AO3400A Vds={budget.mosfet_vds_v:.2f}V, AO3400A power={budget.mosfet_power_w:.3f}W"
        )
        print(
            f"    safe rail window at this current/Vf: {budget.min_laser_vplus_v:.2f}V "
            f"to {budget.max_laser_vplus_v:.2f}V; source: {spec.source_note}"
        )
        failures.extend(selected_policy_failures(case, budget, ambient_c, args.mosfet_headroom_v))

    if failures:
        print("FAIL selected laser current-loop policy")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS selected laser current-loop policy for the checked current/rail assumptions. "
        "This does not waive optical safety, duty-cycle, firmware clamp, or temperature measurement."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        choices=sorted(set(POLICIES) | set(SELECTED_LASER_POLICIES)),
        default="green-high-vf-10v5",
    )
    parser.add_argument("--laser-vplus-v", type=float, help="Override laser supply voltage.")
    parser.add_argument("--diode-vf-max-v", type=float, help="Override diode forward voltage at current limit.")
    parser.add_argument("--ambient-c", type=float, help="Override ambient temperature.")
    parser.add_argument(
        "--target-junction-c",
        type=float,
        default=DEFAULT_TARGET_JUNCTION_C,
        help="Conservative AO3400A junction target for continuous operation.",
    )
    parser.add_argument(
        "--mosfet-headroom-v",
        type=float,
        default=DEFAULT_MOSFET_HEADROOM_V,
        help="Minimum Vds headroom target for current-loop regulation.",
    )
    args = parser.parse_args()

    if args.policy in SELECTED_LASER_POLICIES:
        return run_selected_policy(args)

    policy = policy_from_args(args)
    green_limiter = limiter_for_color("GREEN")
    current_a = green_limiter.command_current_a
    budget = evaluate_budget(
        laser_vplus_v=policy.laser_vplus_v,
        diode_vf_v=policy.diode_vf_max_v,
        current_a=current_a,
        ambient_c=policy.ambient_c,
        target_junction_c=args.target_junction_c,
        mosfet_headroom_v=args.mosfet_headroom_v,
    )

    failures: list[str] = []
    if budget.sense_power_w > SENSE_RESISTOR_RATING_W:
        failures.append(
            f"sense resistor dissipates {budget.sense_power_w:.3f}W, above {SENSE_RESISTOR_RATING_W:.1f}W rating"
        )
    if budget.mosfet_vds_v < args.mosfet_headroom_v:
        failures.append(
            f"AO3400A Vds headroom is {budget.mosfet_vds_v:.2f}V, below {args.mosfet_headroom_v:.2f}V target"
        )
    if budget.mosfet_power_w > budget.mosfet_power_limit_w:
        failures.append(
            f"AO3400A dissipates {budget.mosfet_power_w:.3f}W, above {budget.mosfet_power_limit_w:.3f}W "
            f"continuous budget at {policy.ambient_c:.1f}degC"
        )

    print(f"Laser current-loop policy: {policy.name}")
    print(f"  {policy.description}")
    print(
        f"  green command limit: {PWM_FULL_SCALE_V:.2f}V * {green_limiter.resistance_ohms:g}/"
        f"({PWM_TOP_OHMS:g}+{green_limiter.resistance_ohms:g}) / "
        f"{SENSE_OHMS:.1f}ohm = {current_a * 1000.0:.1f}mA"
    )
    print(
        f"  sense resistor: drop={budget.sense_drop_v:.3f}V, power={budget.sense_power_w:.3f}W, "
        f"rating={SENSE_RESISTOR_RATING_W:.1f}W"
    )
    print(
        f"  laser rail={policy.laser_vplus_v:.2f}V, diode Vf(max)={policy.diode_vf_max_v:.2f}V, "
        f"AO3400A Vds={budget.mosfet_vds_v:.2f}V, power={budget.mosfet_power_w:.3f}W"
    )
    print(
        f"  at ambient={policy.ambient_c:.1f}degC and target Tj={args.target_junction_c:.1f}degC, "
        f"AO3400A continuous power budget={budget.mosfet_power_limit_w:.3f}W"
    )
    print(
        f"  estimated safe laser rail window at this diode Vf/current: "
        f"{budget.min_laser_vplus_v:.2f}V to {budget.max_laser_vplus_v:.2f}V"
    )

    if failures:
        print("FAIL laser current-loop policy")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS laser current-loop policy for this diode/supply assumption. "
        "Direct laser MPN/footprint mapping is covered by the 2026-07-04 signoff; "
        "current/thermal and optical-safety limits still require release review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
