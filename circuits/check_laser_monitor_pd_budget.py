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
from pathlib import Path

from check_laser_controller_netlist import parse_components, parse_netlist


ESP32_ADC_RAIL_V = 3.3
ESP32_ADC_ATTEN_11DB_LIMIT_V = 3.10
ESP32_ADC_PRODUCTION_GUARD_V = 2.90
INA4180_OUTPUT_HIGH_MARGIN_V = 0.03
INA4180_INPUT_CM_MIN_V = -0.2
INA4180_INPUT_CM_MAX_V = 26.0
MPD_SENSE_OHMS = 240.0
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
DEFAULT_NETLIST = Path("/tmp/lc.net")


def canon_net(net: str | None) -> str | None:
    if net in {"LASER_V+", "LASER_VP"}:
        return "LASER_V+"
    return net


@dataclass(frozen=True)
class MonitorChannel:
    name: str
    raw_net: str
    adc_net: str
    monitor_current_typ_a: float | None
    monitor_current_max_a: float | None
    reference_vrpd_v: float
    has_monitor_pd: bool = True


@dataclass(frozen=True)
class Policy:
    name: str
    laser_vplus_v: float
    channels: tuple[MonitorChannel, ...]
    current_point: str
    require_reference_bias: bool
    description: str


PLT5_STYLE_CHANNELS = tuple(
    MonitorChannel(
        name=f"PLT5-style CH{channel}",
        raw_net=f"MPD_RAW{channel}",
        adc_net=f"MPD{channel}",
        monitor_current_typ_a=PLT5_520EBP_MONITOR_CURRENT_TYP_A,
        monitor_current_max_a=None,
        reference_vrpd_v=PLT5_520EBP_MONITOR_REFERENCE_VRPD_V,
    )
    for channel in range(1, 5)
)

SELECTED_LASER_CHANNELS = (
    MonitorChannel(
        name="LD1 D7805I",
        raw_net="MPD_RAW1",
        adc_net="MPD1",
        monitor_current_typ_a=200e-6,
        monitor_current_max_a=600e-6,
        reference_vrpd_v=5.0,
    ),
    MonitorChannel(
        name="LD2 D6505I",
        raw_net="MPD_RAW2",
        adc_net="MPD2",
        monitor_current_typ_a=150e-6,
        monitor_current_max_a=300e-6,
        reference_vrpd_v=5.0,
    ),
    MonitorChannel(
        name="LD3 PLT5 520EB_P",
        raw_net="MPD_RAW3",
        adc_net="MPD3",
        monitor_current_typ_a=150e-6,
        monitor_current_max_a=None,
        reference_vrpd_v=5.0,
    ),
    MonitorChannel(
        name="LD4 PLT5 450GB",
        raw_net="MPD_RAW4",
        adc_net="MPD4",
        monitor_current_typ_a=None,
        monitor_current_max_a=None,
        reference_vrpd_v=5.0,
        has_monitor_pd=False,
    ),
)


POLICIES = {
    "plt5-520ebp-green-10v5": Policy(
        name="plt5-520ebp-green-10v5",
        laser_vplus_v=10.5,
        channels=PLT5_STYLE_CHANNELS,
        current_point="typ",
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
        channels=PLT5_STYLE_CHANNELS,
        current_point="typ",
        require_reference_bias=False,
        description=(
            "ADC headroom check only for the high-side monitor front end. This "
            "does not approve any real laser MPN without its own pinout and "
            "reverse-bias review."
        ),
    ),
    "selected-monitor-typ-9v3": Policy(
        name="selected-monitor-typ-9v3",
        laser_vplus_v=9.30,
        channels=SELECTED_LASER_CHANNELS,
        current_point="typ",
        require_reference_bias=True,
        description=(
            "Selected Digikey-cart monitor-current typical case. LD1 D7805I "
            "is 200uA typ, LD2 D6505I is 150uA typ, LD3 PLT5 520EB_P is "
            "150uA typ, and LD4 PLT5 450GB has no monitor photodiode. This "
            "case should fit the local production ADC-headroom guard after "
            "the sense resistor was reduced to 240R."
        ),
    ),
    "selected-monitor-worst-9v3": Policy(
        name="selected-monitor-worst-9v3",
        laser_vplus_v=9.30,
        channels=SELECTED_LASER_CHANNELS,
        current_point="max",
        require_reference_bias=True,
        description=(
            "Selected Digikey-cart monitor-current high-end case. D7805I "
            "max monitor current is 600uA and D6505I max monitor current is "
            "300uA; PLT5 520EB_P has only a typical 150uA monitor-current "
            "value in the captured table and PLT5 450GB has no monitor PD. "
            "This high-end case should fit the local production ADC-headroom "
            "guard with the 240R/gain20 front end. It still needs optical "
            "calibration before MPD can be used as production feedback."
        ),
    ),
    "selected-monitor-typ-10v72": Policy(
        name="selected-monitor-typ-10v72",
        laser_vplus_v=10.72,
        channels=SELECTED_LASER_CHANNELS,
        current_point="typ",
        require_reference_bias=True,
        description=(
            "Legacy 10.72V selected Digikey-cart monitor-current typical case "
            "kept as a high-rail comparison."
        ),
    ),
    "selected-monitor-worst-10v72": Policy(
        name="selected-monitor-worst-10v72",
        laser_vplus_v=10.72,
        channels=SELECTED_LASER_CHANNELS,
        current_point="max",
        require_reference_bias=True,
        description=(
            "Legacy 10.72V selected Digikey-cart monitor-current high-end case "
            "kept as a high-rail comparison."
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
        channels=policy.channels,
        current_point=policy.current_point,
        require_reference_bias=policy.require_reference_bias,
        description=policy.description + " Custom laser rail override applied.",
    )


def node_map(netlist_path: Path) -> dict[tuple[str, str], str]:
    pin_nets: dict[tuple[str, str], str] = {}
    for net_name, nodes in parse_netlist(netlist_path).items():
        for ref, pin, _pin_name, _sheet in nodes:
            pin_nets[(ref, pin)] = canon_net(net_name) or net_name
    return pin_nets


def component_map(netlist_path: Path) -> dict[str, dict[str, str]]:
    return {comp["ref"]: comp for comp in parse_components(netlist_path)}


def require_comp(
    failures: list[str],
    comps: dict[str, dict[str, str]],
    ref: str,
    *,
    mpn: str,
    footprint_suffix: str | None = None,
    value_contains: str | None = None,
) -> None:
    comp = comps.get(ref)
    if comp is None:
        failures.append(f"{ref}: missing from exported netlist")
        return
    if comp["mpn"] != mpn:
        failures.append(f"{ref}: expected MPN {mpn}, got {comp['mpn']}")
    if footprint_suffix and not comp["footprint"].endswith(footprint_suffix):
        failures.append(f"{ref}: expected footprint ending {footprint_suffix}, got {comp['footprint']}")
    if value_contains and value_contains not in comp["value"]:
        failures.append(f"{ref}: expected value containing {value_contains}, got {comp['value']}")


def require_pin_net(
    failures: list[str],
    pin_nets: dict[tuple[str, str], str],
    ref: str,
    pin: str,
    expected_net: str,
) -> None:
    actual = pin_nets.get((ref, pin))
    if actual != canon_net(expected_net):
        failures.append(f"{ref}.{pin}: expected {expected_net}, got {actual or '<unconnected>'}")


def validate_schematic(netlist_path: Path) -> list[str]:
    failures: list[str] = []
    comps = component_map(netlist_path)
    pin_nets = node_map(netlist_path)

    require_comp(failures, comps, "U12", mpn="INA4180A1IPWR", footprint_suffix="TSSOP-14_4.4x5mm_P0.65mm")
    require_comp(failures, comps, "U13", mpn="LM4040C50IDBZR", footprint_suffix="SOT-23")
    require_comp(failures, comps, "R41", mpn="CRCW06032K49FKEAHP", value_contains="2.49k")
    require_comp(failures, comps, "C35", mpn="0402B104K160CT", value_contains="100nF")
    require_comp(failures, comps, "C36", mpn="0402B104K160CT", value_contains="100nF MPD bias")
    require_comp(failures, comps, "LD1", mpn="D7805I", footprint_suffix="LaserDiode_TO18-D5.6-3")
    require_comp(failures, comps, "LD2", mpn="D6505I", footprint_suffix="LaserDiode_TO18-D5.6-3")
    require_comp(failures, comps, "LD3", mpn="PLT5 520EB_P", footprint_suffix="LaserDiode_TO56-3")
    require_comp(failures, comps, "LD4", mpn="PLT5 450GB", footprint_suffix="LaserDiode_TO56-3")

    for ref in ("R42", "R44", "R46", "R48"):
        require_comp(failures, comps, ref, mpn="RC0603FR-07240RL", value_contains="240R MPD sense")
    for ref in ("R43", "R45", "R47", "R49"):
        require_comp(failures, comps, ref, mpn="FRC0603F1001TS", value_contains="1k ADC")
    for ref in ("C37", "C38", "C39", "C40"):
        require_comp(failures, comps, ref, mpn="0402B104K160CT", value_contains="100nF MPD ADC")

    expected_pin_nets = {
        ("U12", "1"): "/POWER_IO/MPD_AMP1",
        ("U12", "2"): "/POWER_IO/MPD_BIAS",
        ("U12", "3"): "MPD_RAW1",
        ("U12", "4"): "+3V3",
        ("U12", "5"): "MPD_RAW2",
        ("U12", "6"): "/POWER_IO/MPD_BIAS",
        ("U12", "7"): "/POWER_IO/MPD_AMP2",
        ("U12", "8"): "/POWER_IO/MPD_AMP3",
        ("U12", "9"): "/POWER_IO/MPD_BIAS",
        ("U12", "10"): "MPD_RAW3",
        ("U12", "11"): "GND",
        ("U12", "12"): "MPD_RAW4",
        ("U12", "13"): "/POWER_IO/MPD_BIAS",
        ("U12", "14"): "/POWER_IO/MPD_AMP4",
        ("U13", "1"): "LASER_V+",
        ("U13", "2"): "/POWER_IO/MPD_BIAS",
        ("U13", "3"): "/POWER_IO/MPD_BIAS",
        ("R41", "1"): "/POWER_IO/MPD_BIAS",
        ("R41", "2"): "GND",
        ("C35", "1"): "+3V3",
        ("C35", "2"): "GND",
        ("C36", "1"): "LASER_V+",
        ("C36", "2"): "/POWER_IO/MPD_BIAS",
        ("LD1", "2"): "LASER_V+",
        ("LD1", "3"): "MPD_RAW1",
        ("LD2", "2"): "LASER_V+",
        ("LD2", "3"): "MPD_RAW2",
        ("LD3", "2"): "LASER_V+",
        ("LD3", "3"): "MPD_RAW3",
        ("LD4", "1"): "LASER_V+",
        ("LD4", "3"): "LASER_N4",
        ("U9", "38"): "MPD1",
        ("U9", "15"): "MPD2",
        ("U9", "12"): "MPD3",
        ("U9", "17"): "MPD4",
    }
    for channel, sense_ref, adc_ref, cap_ref in (
        (1, "R42", "R43", "C37"),
        (2, "R44", "R45", "C38"),
        (3, "R46", "R47", "C39"),
        (4, "R48", "R49", "C40"),
    ):
        expected_pin_nets[(sense_ref, "1")] = f"MPD_RAW{channel}"
        expected_pin_nets[(sense_ref, "2")] = "/POWER_IO/MPD_BIAS"
        expected_pin_nets[(adc_ref, "1")] = f"/POWER_IO/MPD_AMP{channel}"
        expected_pin_nets[(adc_ref, "2")] = f"MPD{channel}"
        expected_pin_nets[(cap_ref, "1")] = f"MPD{channel}"
        expected_pin_nets[(cap_ref, "2")] = "GND"

    for (ref, pin), expected_net in sorted(expected_pin_nets.items()):
        require_pin_net(failures, pin_nets, ref, pin, expected_net)

    ld4_case_net = pin_nets.get(("LD4", "2"))
    if ld4_case_net is not None and not ld4_case_net.startswith("unconnected-"):
        failures.append(f"LD4.2: PLT5 450GB case must stay unconnected, got {ld4_case_net}")
    if "MPD_RAW4" in parse_netlist(netlist_path) and any(
        ref == "LD4" for ref, _pin, _pin_name, _sheet in parse_netlist(netlist_path)["MPD_RAW4"]
    ):
        failures.append("MPD_RAW4: selected PLT5 450GB must not connect to the spare monitor input")

    return failures


def channel_current(channel: MonitorChannel, policy: Policy) -> float:
    if not channel.has_monitor_pd:
        return 0.0
    if policy.current_point == "typ":
        if channel.monitor_current_typ_a is None:
            raise ValueError(f"{channel.name} has no typical monitor current")
        return channel.monitor_current_typ_a
    if policy.current_point == "max":
        if channel.monitor_current_max_a is not None:
            return channel.monitor_current_max_a
        if channel.monitor_current_typ_a is not None:
            return channel.monitor_current_typ_a
        raise ValueError(f"{channel.name} has no monitor current")
    raise ValueError(f"unknown monitor current point: {policy.current_point}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="plt5-520ebp-green-10v5")
    parser.add_argument("--laser-vplus-v", type=float, help="Override laser anode/monitor cathode rail voltage.")
    parser.add_argument(
        "--netlist",
        type=Path,
        help=f"Optional KiCad netlist to validate U12/U13/LD/ESP32 monitor-PD connectivity, e.g. {DEFAULT_NETLIST}",
    )
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
    adc_linear_limit_v = ESP32_ADC_RAIL_V - INA4180_OUTPUT_HIGH_MARGIN_V
    monitor_current_adc_limit_a = adc_linear_limit_v / (MPD_SENSE_OHMS * INA4180_GAIN)
    monitor_current_esp32_limit_a = ESP32_ADC_ATTEN_11DB_LIMIT_V / (MPD_SENSE_OHMS * INA4180_GAIN)
    monitor_current_guard_limit_a = ESP32_ADC_PRODUCTION_GUARD_V / (MPD_SENSE_OHMS * INA4180_GAIN)
    filter_tau_s = ADC_SERIES_OHMS * MPD_FILTER_F
    vrpd_dark_v = policy.laser_vplus_v - mpd_bias_v
    bias_sink_current_a = mpd_bias_v / MPD_BIAS_SINK_OHMS if mpd_bias_v > 0 else 0.0
    lm4040_current_no_mpd_a = bias_sink_current_a

    failures: list[str] = []
    if args.netlist:
        if not args.netlist.exists():
            raise SystemExit(f"netlist not found: {args.netlist}")
        failures.extend(validate_schematic(args.netlist))

    channel_rows: list[tuple[MonitorChannel, float, float, float, float]] = []
    active_monitor_current_a = 0.0
    for channel in policy.channels:
        current_a = channel_current(channel, policy)
        active_monitor_current_a += current_a
        sense_v = current_a * MPD_SENSE_OHMS
        adc_v = sense_v * INA4180_GAIN
        mpd_raw_v = mpd_bias_v + sense_v
        vrpd_v = policy.laser_vplus_v - mpd_raw_v
        channel_rows.append((channel, current_a, sense_v, adc_v, vrpd_v))

        if not channel.has_monitor_pd:
            continue
        if adc_v > adc_linear_limit_v:
            failures.append(
                f"{channel.name}: {policy.current_point} MPD ADC voltage is {adc_v:.2f}V, above the "
                f"{adc_linear_limit_v:.2f}V INA4180 3.3V output-headroom limit"
            )
        if adc_v > ESP32_ADC_ATTEN_11DB_LIMIT_V:
            failures.append(
                f"{channel.name}: {policy.current_point} MPD ADC voltage is {adc_v:.2f}V, above the "
                f"{ESP32_ADC_ATTEN_11DB_LIMIT_V:.2f}V ESP32-S3 ADC 11dB measurable-range limit"
            )
        if adc_v > ESP32_ADC_PRODUCTION_GUARD_V:
            failures.append(
                f"{channel.name}: {policy.current_point} MPD ADC voltage is {adc_v:.2f}V, above the "
                f"{ESP32_ADC_PRODUCTION_GUARD_V:.2f}V local production guard for ADC calibration/headroom"
            )
        if sense_v > channel.reference_vrpd_v:
            failures.append(
                f"{channel.name}: {policy.current_point} sense drop is {sense_v:.2f}V, larger than the target "
                f"{channel.reference_vrpd_v:.2f}V monitor-PD reverse bias"
            )
        if not (INA4180_INPUT_CM_MIN_V <= mpd_bias_v <= INA4180_INPUT_CM_MAX_V):
            failures.append(
                f"{channel.name}: MPD_BIAS common-mode {mpd_bias_v:.2f}V is outside "
                f"{INA4180_INPUT_CM_MIN_V:.1f}..{INA4180_INPUT_CM_MAX_V:.1f}V"
            )
        if not (INA4180_INPUT_CM_MIN_V <= mpd_raw_v <= INA4180_INPUT_CM_MAX_V):
            failures.append(
                f"{channel.name}: MPD_RAW common-mode {mpd_raw_v:.2f}V is outside "
                f"{INA4180_INPUT_CM_MIN_V:.1f}..{INA4180_INPUT_CM_MAX_V:.1f}V"
            )
        if policy.require_reference_bias:
            delta_v = abs(vrpd_v - channel.reference_vrpd_v)
            if delta_v > args.vrpd_tolerance_v:
                failures.append(
                    f"{channel.name}: {policy.current_point} monitor-PD reverse bias is {vrpd_v:.2f}V, not the "
                    f"{channel.reference_vrpd_v:.2f}V datasheet monitor-current condition"
                )

    lm4040_current_active_a = bias_sink_current_a - active_monitor_current_a
    if policy.require_reference_bias:
        reference_vrpd_v = max(channel.reference_vrpd_v for channel in policy.channels)
        if abs(vrpd_dark_v - reference_vrpd_v) > args.vrpd_tolerance_v:
            failures.append(
                f"dark/off monitor-PD reverse bias is {vrpd_dark_v:.2f}V while LASER_V+ is present; "
                f"the LM4040/MPD_BIAS path does not hold VRPD near {reference_vrpd_v:.2f}V"
            )
        if lm4040_current_active_a < LM4040_MIN_CATHODE_CURRENT_A:
            failures.append(
                f"LM4040 cathode current with active monitor currents is "
                f"{lm4040_current_active_a * 1e6:.0f}uA, below the {LM4040_MIN_CATHODE_CURRENT_A * 1e6:.0f}uA "
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
    if args.netlist:
        print(f"  schematic connectivity checked against {args.netlist}")
    for channel, current_a, sense_v, adc_v, vrpd_v in channel_rows:
        if channel.has_monitor_pd:
            print(
                f"  {channel.name}: {policy.current_point} monitor current={current_a * 1e6:.0f}uA -> "
                f"sense={sense_v:.3f}V, ADC={adc_v:.2f}V, VRPD={vrpd_v:.2f}V"
            )
        else:
            print(f"  {channel.name}: no monitor photodiode; {channel.raw_net}/{channel.adc_net} is spare/open")
    print(
        f"  LASER_V+={policy.laser_vplus_v:.2f}V, MPD_BIAS={mpd_bias_v:.2f}V -> monitor-PD reverse bias "
        f"dark/off={vrpd_dark_v:.2f}V; RC tau={filter_tau_s * 1000.0:.2f}ms"
    )
    print(
        f"  LM4040 current: no-MPD={lm4040_current_no_mpd_a * 1000.0:.2f}mA, "
        f"active MPD={lm4040_current_active_a * 1000.0:.2f}mA; "
        f"INA linear monitor-current limit about {monitor_current_adc_limit_a * 1e6:.0f}uA, "
        f"ESP32 11dB limit about {monitor_current_esp32_limit_a * 1e6:.0f}uA, "
        f"production guard about {monitor_current_guard_limit_a * 1e6:.0f}uA"
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
