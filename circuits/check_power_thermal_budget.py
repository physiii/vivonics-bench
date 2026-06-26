#!/usr/bin/env python3
"""AP2112 3V3 rail thermal policy check for the bench laser controller.

The AP2112 can supply 600 mA electrically, but in the current SOT-25/SOT-23-5
bench layout its 5 V to 3.3 V dissipation is the limiting factor.  This script
keeps the bench/no-RF assumption explicit and makes sustained RF scenarios fail
until the regulator is changed or the load is otherwise proven.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass


VIN_V = 5.0
VOUT_V = 3.3
AP2112_IQ_MAX_A = 80e-6
AP2112_THETA_JA_SOT25_C_PER_W = 184.0
DEFAULT_TARGET_JUNCTION_C = 125.0


@dataclass(frozen=True)
class Scenario:
    name: str
    load_current_ma: float
    ambient_c: float
    description: str


SCENARIOS = {
    "bench-uart-usb": Scenario(
        name="bench-uart-usb",
        load_current_ma=120.0,
        ambient_c=85.0,
        description=(
            "Bench policy: RF disabled, USB/UART control, ESP32 active current "
            "plus reset/boot pulls kept below 120 mA continuous at 85 degC."
        ),
    ),
    "esp32-dual-core-typ": Scenario(
        name="esp32-dual-core-typ",
        load_current_ma=108.0,
        ambient_c=85.0,
        description=(
            "Espressif ESP32-S3 dual-core active current with peripheral clocks "
            "enabled, rounded from the 107.9 mA typical datasheet value."
        ),
    ),
    "wifi-tx-100-duty": Scenario(
        name="wifi-tx-100-duty",
        load_current_ma=355.0,
        ambient_c=25.0,
        description=(
            "Espressif ESP32-S3-WROOM-1 Wi-Fi 802.11b 1 Mbps TX current at "
            "100 percent duty cycle, 20.5 dBm."
        ),
    ),
    "ble-tx-20dbm": Scenario(
        name="ble-tx-20dbm",
        load_current_ma=344.0,
        ambient_c=25.0,
        description="Espressif ESP32-S3-WROOM-1 Bluetooth LE TX current at 20 dBm.",
    ),
}


def ldo_power_w(load_current_ma: float) -> float:
    load_current_a = load_current_ma / 1000.0
    return (VIN_V - VOUT_V) * load_current_a + VIN_V * AP2112_IQ_MAX_A


def junction_temperature_c(load_current_ma: float, ambient_c: float) -> float:
    return ambient_c + ldo_power_w(load_current_ma) * AP2112_THETA_JA_SOT25_C_PER_W


def max_continuous_current_ma(ambient_c: float, target_junction_c: float) -> float:
    allowed_power_w = (target_junction_c - ambient_c) / AP2112_THETA_JA_SOT25_C_PER_W
    allowed_load_power_w = allowed_power_w - VIN_V * AP2112_IQ_MAX_A
    return max(0.0, allowed_load_power_w / (VIN_V - VOUT_V) * 1000.0)


def scenario_from_args(args: argparse.Namespace) -> Scenario:
    scenario = SCENARIOS[args.policy]
    if args.load_current_ma is None and args.ambient_c is None:
        return scenario
    return Scenario(
        name=f"{scenario.name}-custom",
        load_current_ma=args.load_current_ma if args.load_current_ma is not None else scenario.load_current_ma,
        ambient_c=args.ambient_c if args.ambient_c is not None else scenario.ambient_c,
        description=scenario.description + " Custom current/ambient override applied.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        choices=sorted(SCENARIOS),
        default="bench-uart-usb",
        help="Thermal scenario to check.",
    )
    parser.add_argument("--load-current-ma", type=float, help="Override scenario load current.")
    parser.add_argument("--ambient-c", type=float, help="Override scenario ambient temperature.")
    parser.add_argument(
        "--target-junction-c",
        type=float,
        default=DEFAULT_TARGET_JUNCTION_C,
        help="Design target junction temperature, not thermal shutdown.",
    )
    args = parser.parse_args()

    scenario = scenario_from_args(args)
    power_w = ldo_power_w(scenario.load_current_ma)
    temp_rise_c = power_w * AP2112_THETA_JA_SOT25_C_PER_W
    junction_c = scenario.ambient_c + temp_rise_c
    margin_c = args.target_junction_c - junction_c
    max_current_ma = max_continuous_current_ma(scenario.ambient_c, args.target_junction_c)

    print(f"AP2112 thermal policy: {scenario.name}")
    print(f"  {scenario.description}")
    print(
        f"  constants: Vin={VIN_V:.2f}V, Vout={VOUT_V:.2f}V, "
        f"Iq(max)={AP2112_IQ_MAX_A * 1_000_000:.0f}uA, "
        f"thetaJA={AP2112_THETA_JA_SOT25_C_PER_W:.0f}degC/W"
    )
    print(
        f"  load={scenario.load_current_ma:.1f}mA, ambient={scenario.ambient_c:.1f}degC, "
        f"dissipation={power_w:.3f}W, rise={temp_rise_c:.1f}degC, "
        f"Tj={junction_c:.1f}degC"
    )
    print(
        f"  target Tj={args.target_junction_c:.1f}degC, "
        f"margin={margin_c:.1f}degC, max continuous current at this ambient="
        f"{max_current_ma:.1f}mA"
    )

    if margin_c < 0:
        print(
            "FAIL AP2112 thermal policy: this 3V3 load needs a buck regulator, "
            "larger thermal package, lower ambient/current, or measured duty-cycle proof."
        )
        return 1

    print(
        "PASS AP2112 thermal policy: acceptable for the checked bench/no-RF "
        "continuous-current assumption. Sustained Wi-Fi/BLE remains a separate fail case."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
