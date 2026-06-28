#!/usr/bin/env python3
"""Monitor-photodiode bias and ADC-scale checks for the bench laser controller.

This checks the high-side internal monitor-PD front end against a selected
laser/rail assumption. It is intentionally separate from the laser current-loop
budget: the current loop can be thermally acceptable while the monitor
photodiode interface is wrong for the laser-diode datasheet condition.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass


ESP32_ADC_RAIL_V = 3.3
INA4180_OUTPUT_HIGH_MARGIN_V = 0.03
MPD_SENSE_OHMS = 750.0
INA4180_GAIN = 20.0
ADC_SERIES_OHMS = 1_000.0
MPD_FILTER_F = 100e-9
LM4040_REFERENCE_V = 5.0
MPD_BIAS_SINK_OHMS = 2_490.0
LM4040_MIN_CATHODE_CURRENT_A = 80e-6
LM4040_MAX_CATHODE_CURRENT_A = 15e-3
MPD_CHANNELS = 4
PLT5_520EBP_MONITOR_CURRENT_TYP_A = 150e-6
PLT5_520EBP_MONITOR_REFERENCE_VRPD_V = 5.0


@dataclass(frozen=True)
class Policy:
    name: str
    laser_vplus_v: float
    monitor_current_typ_a: float
    reference_vrpd_v: float
    require_reference_bias: bool
    description: str


POLICIES = {
    "plt5-520ebp-green-10v5": Policy(
        name="plt5-520ebp-green-10v5",
        laser_vplus_v=10.5,
        monitor_current_typ_a=PLT5_520EBP_MONITOR_CURRENT_TYP_A,
        reference_vrpd_v=PLT5_520EBP_MONITOR_REFERENCE_VRPD_V,
        require_reference_bias=True,
        description=(
            "PLT5 520EB_P monitor-current reference case. The datasheet "
            "monitor current is specified at VRPD=5V and is not guaranteed as "
            "an accurate absolute power measurement. The bench circuit uses a "
            "high-side INA4180 sense path and LM4040-derived MPD_BIAS node. "
            "PLT5 450GB has no monitor photodiode, so MPD_RAW4 is only a "
            "spare/open front-end input."
        ),
    ),
    "adc-scale-only-10v5": Policy(
        name="adc-scale-only-10v5",
        laser_vplus_v=10.5,
        monitor_current_typ_a=PLT5_520EBP_MONITOR_CURRENT_TYP_A,
        reference_vrpd_v=PLT5_520EBP_MONITOR_REFERENCE_VRPD_V,
        require_reference_bias=False,
        description=(
            "ADC headroom check only for the high-side monitor front end. This "
            "does not approve any real laser MPN without its own pinout and "
            "reverse-bias review."
        ),
    ),
}


def policy_from_args(args: argparse.Namespace) -> Policy:
    policy = POLICIES[args.policy]
    if args.laser_vplus_v is None:
        return policy
    return Policy(
        name=f"{policy.name}-custom",
        laser_vplus_v=args.laser_vplus_v,
        monitor_current_typ_a=policy.monitor_current_typ_a,
        reference_vrpd_v=policy.reference_vrpd_v,
        require_reference_bias=policy.require_reference_bias,
        description=policy.description + " Custom laser rail override applied.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="plt5-520ebp-green-10v5")
    parser.add_argument("--laser-vplus-v", type=float, help="Override laser anode/monitor cathode rail voltage.")
    parser.add_argument(
        "--vrpd-tolerance-v",
        type=float,
        default=0.5,
        help="Allowed difference from the datasheet monitor-current reverse-bias condition.",
    )
    args = parser.parse_args()

    policy = policy_from_args(args)
    if policy.laser_vplus_v <= LM4040_REFERENCE_V:
        mpd_bias_v = 0.0
    else:
        mpd_bias_v = policy.laser_vplus_v - LM4040_REFERENCE_V
    sense_typ_v = policy.monitor_current_typ_a * MPD_SENSE_OHMS
    adc_typ_v = sense_typ_v * INA4180_GAIN
    adc_linear_limit_v = ESP32_ADC_RAIL_V - INA4180_OUTPUT_HIGH_MARGIN_V
    monitor_current_adc_limit_a = adc_linear_limit_v / (MPD_SENSE_OHMS * INA4180_GAIN)
    filter_tau_s = ADC_SERIES_OHMS * MPD_FILTER_F
    vrpd_typ_v = policy.laser_vplus_v - (mpd_bias_v + sense_typ_v)
    vrpd_dark_v = policy.laser_vplus_v - mpd_bias_v
    bias_sink_current_a = mpd_bias_v / MPD_BIAS_SINK_OHMS if mpd_bias_v > 0 else 0.0
    lm4040_current_no_mpd_a = bias_sink_current_a
    lm4040_current_typ_all_a = bias_sink_current_a - MPD_CHANNELS * policy.monitor_current_typ_a

    failures: list[str] = []
    if adc_typ_v > adc_linear_limit_v:
        failures.append(
            f"typical MPD ADC voltage is {adc_typ_v:.2f}V, above the {adc_linear_limit_v:.2f}V "
            "linear output/ADC headroom limit"
        )
    if sense_typ_v > policy.reference_vrpd_v:
        failures.append(
            f"typical sense drop is {sense_typ_v:.2f}V, larger than the target "
            f"{policy.reference_vrpd_v:.2f}V monitor-PD reverse bias"
        )
    if policy.require_reference_bias:
        delta_v = abs(vrpd_typ_v - policy.reference_vrpd_v)
        if delta_v > args.vrpd_tolerance_v:
            failures.append(
                f"typical monitor-PD reverse bias is {vrpd_typ_v:.2f}V, not the "
                f"{policy.reference_vrpd_v:.2f}V datasheet monitor-current condition"
            )
        if abs(vrpd_dark_v - policy.reference_vrpd_v) > args.vrpd_tolerance_v:
            failures.append(
                f"dark/off monitor-PD reverse bias is {vrpd_dark_v:.2f}V while LASER_V+ is present; "
                f"the LM4040/MPD_BIAS path does not hold VRPD near {policy.reference_vrpd_v:.2f}V"
            )
        if lm4040_current_typ_all_a < LM4040_MIN_CATHODE_CURRENT_A:
            failures.append(
                f"LM4040 cathode current with {MPD_CHANNELS} channels at typical monitor current is "
                f"{lm4040_current_typ_all_a * 1e6:.0f}uA, below the {LM4040_MIN_CATHODE_CURRENT_A * 1e6:.0f}uA "
                "minimum design guard"
            )
        if lm4040_current_no_mpd_a > LM4040_MAX_CATHODE_CURRENT_A:
            failures.append(
                f"LM4040 no-monitor cathode current is {lm4040_current_no_mpd_a * 1000.0:.2f}mA, above "
                f"the {LM4040_MAX_CATHODE_CURRENT_A * 1000.0:.1f}mA maximum"
            )

    print(f"Monitor-PD policy: {policy.name}")
    print(f"  {policy.description}")
    print(
        f"  front end: MPD_RAWx -> {MPD_SENSE_OHMS:.0f} ohm sense -> MPD_BIAS; "
        f"INA4180 gain={INA4180_GAIN:.0f}; {ADC_SERIES_OHMS / 1000.0:.0f}k/"
        f"{MPD_FILTER_F * 1e9:.0f}nF ADC-side RC"
    )
    print(
        f"  typical monitor current={policy.monitor_current_typ_a * 1e6:.0f}uA -> "
        f"sense={sense_typ_v:.3f}V, ADC={adc_typ_v:.2f}V, RC tau={filter_tau_s * 1000.0:.2f}ms"
    )
    print(
        f"  LASER_V+={policy.laser_vplus_v:.2f}V, MPD_BIAS={mpd_bias_v:.2f}V -> monitor-PD reverse bias "
        f"typ={vrpd_typ_v:.2f}V, dark/off={vrpd_dark_v:.2f}V"
    )
    print(
        f"  LM4040 current: no-MPD={lm4040_current_no_mpd_a * 1000.0:.2f}mA, "
        f"{MPD_CHANNELS}x typ MPD={lm4040_current_typ_all_a * 1000.0:.2f}mA; "
        f"ADC linear monitor-current limit about {monitor_current_adc_limit_a * 1e6:.0f}uA"
    )

    if failures:
        print("FAIL monitor-PD policy")
        for failure in failures:
            print(f"  {failure}")
        print(
            "  Required fix: adjust the sense resistor, bias sink, rail assumption, or monitor front-end "
            "topology before treating MPD as usable feedback."
        )
        return 1

    print(
        "PASS monitor-PD policy for this scope. This does not replace per-laser datasheet "
        "pinout, reverse-bias, optical safety, and calibration review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
