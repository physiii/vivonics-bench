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
from dataclasses import dataclass


PWM_FULL_SCALE_V = 3.3
PWM_TOP_OHMS = 10_000.0
PWM_PULLDOWN_OHMS = 30_000.0
SENSE_OHMS = 10.0
SENSE_RESISTOR_RATING_W = 2.0
AO3400A_THETA_JA_C_PER_W = 125.0
DEFAULT_TARGET_JUNCTION_C = 125.0
DEFAULT_MOSFET_HEADROOM_V = 0.50


@dataclass(frozen=True)
class Policy:
    name: str
    laser_vplus_v: float
    diode_vf_max_v: float
    ambient_c: float
    description: str


POLICIES = {
    "green-high-vf-10v5": Policy(
        name="green-high-vf-10v5",
        laser_vplus_v=10.5,
        diode_vf_max_v=7.0,
        ambient_c=85.0,
        description=(
            "High-forward-voltage green reference using 7.0 V diode headroom "
            "and a 10.5 V laser rail. This is a thermal policy reference, not "
            "an approval to drive the selected Digikey-cart lasers at the "
            "247.5 mA hardware command clamp."
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
    command_v = PWM_FULL_SCALE_V * PWM_PULLDOWN_OHMS / (PWM_TOP_OHMS + PWM_PULLDOWN_OHMS)
    return command_v / SENSE_OHMS


def max_mosfet_power_w(ambient_c: float, target_junction_c: float) -> float:
    return max(0.0, (target_junction_c - ambient_c) / AO3400A_THETA_JA_C_PER_W)


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="green-high-vf-10v5")
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

    policy = policy_from_args(args)
    current_a = command_limit_current_a()
    sense_drop_v = current_a * SENSE_OHMS
    sense_power_w = current_a * current_a * SENSE_OHMS
    mosfet_vds_v = policy.laser_vplus_v - policy.diode_vf_max_v - sense_drop_v
    mosfet_power_w = max(0.0, mosfet_vds_v * current_a)
    mosfet_power_limit_w = max_mosfet_power_w(policy.ambient_c, args.target_junction_c)
    min_laser_vplus_v = policy.diode_vf_max_v + sense_drop_v + args.mosfet_headroom_v
    max_laser_vplus_v = policy.diode_vf_max_v + sense_drop_v + (mosfet_power_limit_w / current_a)

    failures: list[str] = []
    if sense_power_w > SENSE_RESISTOR_RATING_W:
        failures.append(
            f"sense resistor dissipates {sense_power_w:.3f}W, above {SENSE_RESISTOR_RATING_W:.1f}W rating"
        )
    if mosfet_vds_v < args.mosfet_headroom_v:
        failures.append(
            f"AO3400A Vds headroom is {mosfet_vds_v:.2f}V, below {args.mosfet_headroom_v:.2f}V target"
        )
    if mosfet_power_w > mosfet_power_limit_w:
        failures.append(
            f"AO3400A dissipates {mosfet_power_w:.3f}W, above {mosfet_power_limit_w:.3f}W "
            f"continuous budget at {policy.ambient_c:.1f}degC"
        )

    print(f"Laser current-loop policy: {policy.name}")
    print(f"  {policy.description}")
    print(
        f"  command clamp: {PWM_FULL_SCALE_V:.2f}V * 30k/(10k+30k) / "
        f"{SENSE_OHMS:.1f}ohm = {current_a * 1000.0:.1f}mA"
    )
    print(
        f"  sense resistor: drop={sense_drop_v:.3f}V, power={sense_power_w:.3f}W, "
        f"rating={SENSE_RESISTOR_RATING_W:.1f}W"
    )
    print(
        f"  laser rail={policy.laser_vplus_v:.2f}V, diode Vf(max)={policy.diode_vf_max_v:.2f}V, "
        f"AO3400A Vds={mosfet_vds_v:.2f}V, power={mosfet_power_w:.3f}W"
    )
    print(
        f"  at ambient={policy.ambient_c:.1f}degC and target Tj={args.target_junction_c:.1f}degC, "
        f"AO3400A continuous power budget={mosfet_power_limit_w:.3f}W"
    )
    print(
        f"  estimated safe laser rail window at this diode Vf/current: "
        f"{min_laser_vplus_v:.2f}V to {max_laser_vplus_v:.2f}V"
    )

    if failures:
        print("FAIL laser current-loop policy")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS laser current-loop policy for this diode/supply assumption. "
        "Actual laser MPN and direct-footprint pinout still require release review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
