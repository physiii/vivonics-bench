#!/usr/bin/env python3
"""Passive voltage and power derating checks for the bench laser controller.

Run after:
  kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net

This is a bench-design electrical check. It verifies that every assembled R/C
or trimmer MPN in the exported netlist has an explicit rating entry and that
the design's conservative steady-state stress assumptions stay below the local
derating policy. It is not a lifecycle, pulse, surge, or production procurement
approval.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from check_laser_controller_netlist import parse_components


CAP_VOLTAGE_UTIL_LIMIT = 0.80
RESISTOR_POWER_UTIL_LIMIT = 0.50
RESISTOR_VOLTAGE_UTIL_LIMIT = 0.80


@dataclass(frozen=True)
class CapacitorRating:
    value: str
    voltage_v: float
    dielectric: str
    package: str
    source: str


@dataclass(frozen=True)
class ResistorRating:
    value: str
    power_w: float
    voltage_v: float
    tolerance: str
    package: str
    source: str


@dataclass(frozen=True)
class CapacitorStress:
    voltage_v: float
    reason: str


@dataclass(frozen=True)
class ResistorStress:
    power_w: float
    voltage_v: float
    reason: str


CAP_RATINGS = {
    "0402B104K160CT": CapacitorRating(
        value="100nF",
        voltage_v=16.0,
        dielectric="X7R",
        package="0402",
        source="LCSC C83056 / Walsin 0402B104K160CT page: 100nF +/-10%, X7R, 16Vdc.",
    ),
    "HGC0402R5105K250NTEJ": CapacitorRating(
        value="1uF",
        voltage_v=25.0,
        dielectric="X5R",
        package="0402",
        source="LCSC C7472946 / Chinocera HGC0402R5105K250NTEJ page: 1uF +/-10%, X5R, 25Vdc.",
    ),
    "CL21A106KAYNNNG": CapacitorRating(
        value="10uF",
        voltage_v=25.0,
        dielectric="X5R",
        package="0805",
        source="LCSC C318691 / Samsung CL21A106KAYNNNG page: 10uF +/-10%, X5R, 25Vdc.",
    ),
    "CL21A226MAQNNNE": CapacitorRating(
        value="22uF",
        voltage_v=25.0,
        dielectric="X5R",
        package="0805",
        source="JLCPCB/LCSC C45783 / Samsung CL21A226MAQNNNE page: 22uF +/-20%, X5R, 25Vdc.",
    ),
    "CL31B105KCHNNNE": CapacitorRating(
        value="1uF",
        voltage_v=100.0,
        dielectric="X7R",
        package="1206",
        source="LCSC C13832 / Samsung CL31B105KCHNNNE page: 1uF +/-10%, X7R, 100Vdc.",
    ),
    "CL31B106KBHNNNE": CapacitorRating(
        value="10uF",
        voltage_v=50.0,
        dielectric="X7R",
        package="1206",
        source="JLCPCB/LCSC C89632 / Samsung CL31B106KBHNNNE page: 10uF +/-10%, X7R, 50Vdc.",
    ),
    "RVT2A220M0810": CapacitorRating(
        value="22uF",
        voltage_v=100.0,
        dielectric="aluminum electrolytic",
        package="8x10.2mm SMD can",
        source="LCSC C90264 / ROQANG RVT2A220M0810 page: 22uF, 100Vdc aluminum electrolytic.",
    ),
    "CC0603JRNPO9BN100": CapacitorRating(
        value="10pF",
        voltage_v=50.0,
        dielectric="C0G/NP0",
        package="0603",
        source="Yageo CC0603JRNPO9BN100 specsheet: 10pF +/-5%, C0G, 50Vdc.",
    ),
    "0402CG101J500NT": CapacitorRating(
        value="100pF",
        voltage_v=50.0,
        dielectric="C0G/NP0",
        package="0402",
        source="LCSC C1546 / Fenghua 0402CG101J500NT page: 100pF +/-5%, C0G, 50Vdc.",
    ),
}


RES_RATINGS = {
    "FRC0603F1001TS": ResistorRating(
        value="1k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C2907002 / FOJAN FRC0603F1001TS page: 1k, 100mW, 75V, +/-1%, +/-100ppm/C.",
    ),
    "CRCW060310K0FKEA": ResistorRating(
        value="10k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C844918 / Vishay CRCW060310K0FKEA page: 10k, 100mW, 75V, +/-1%, +/-100ppm/C.",
    ),
    "0603WAF220JT5E": ResistorRating(
        value="22R",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="JLCPCB/LCSC C23345 data: 22 ohm, 0.1W, 75V, +/-1%, +/-100ppm/C.",
    ),
    "0603WAF3002T5E": ResistorRating(
        value="30k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="Royalohm 0603WAF 0603 family data: 0.1W, 75V, +/-1%.",
    ),
    "0603WAF7500T5E": ResistorRating(
        value="750R",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C23241 / UNI-ROYAL 0603WAF7500T5E page: 750 ohm, 100mW, 75V, +/-1%.",
    ),
    "0603WAF1301T5E": ResistorRating(
        value="1.3k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C22767 / UNI-ROYAL 0603WAF1301T5E page: 1.3k, 100mW, 75V, +/-1%.",
    ),
    "0603WAF3001T5E": ResistorRating(
        value="3k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C4211 / UNI-ROYAL 0603WAF3001T5E page: 3k, 100mW, 75V, +/-1%.",
    ),
    "0603WAF4701T5E": ResistorRating(
        value="4.7k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C23162 / UNI-ROYAL 0603WAF4701T5E page: 4.7k, 100mW, 75V, +/-1%.",
    ),
    "CRCW06032K49FKEAHP": ResistorRating(
        value="2.49k",
        power_w=0.333,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C2099849 / Vishay CRCW06032K49FKEAHP page: 2.49k, 333mW, 75V, +/-1%, +/-100ppm/C.",
    ),
    "RC0603FR-07240RL": ResistorRating(
        value="240R",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="Yageo RC0603FR-07240RL specsheet and LCSC C114613 page: 240 ohm, 100mW, 75V, +/-1%, +/-100ppm/C.",
    ),
    "RT0402BRD071KL": ResistorRating(
        value="1k",
        power_w=0.0625,
        voltage_v=50.0,
        tolerance="+/-0.1%",
        package="0402",
        source="LCSC C852624 / Yageo RT0402BRD071KL page: 1k, 62.5mW, 50V, +/-0.1%, +/-25ppm/C.",
    ),
    "ERJ2RKF1002X": ResistorRating(
        value="10k",
        power_w=0.10,
        voltage_v=50.0,
        tolerance="+/-1%",
        package="0402",
        source="LCSC C191123 / Panasonic ERJ2RKF1002X page: 10k, 100mW, 50V, +/-1%, +/-100ppm/C.",
    ),
    "FRC0402F2212TS": ResistorRating(
        value="22.1k",
        power_w=0.0625,
        voltage_v=50.0,
        tolerance="+/-1%",
        package="0402",
        source="LCSC C2929993 / FOJAN FRC0402F2212TS page: 22.1k, 62.5mW, 50V, +/-1%.",
    ),
    "FRC0603F2373TS": ResistorRating(
        value="237k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="JLCPCB/LCSC C2998117 / FOJAN FRC0603F2373TS page: 237k, 100mW, 75V, +/-1%.",
    ),
    "0603WAF4752T5E": ResistorRating(
        value="47.5k",
        power_w=0.10,
        voltage_v=75.0,
        tolerance="+/-1%",
        package="0603",
        source="LCSC C23061 / UNI-ROYAL 0603WAF4752T5E page: 47.5k, 100mW, 75V, +/-1%.",
    ),
    "HoCR2512-2W-10R-1%": ResistorRating(
        value="10R",
        power_w=2.00,
        voltage_v=250.0,
        tolerance="+/-1%",
        package="2512",
        source="JLCPCB/Milliohm C5123624 page: 10 ohm, 250V, 2W, +/-1%.",
    ),
    "3224W-1-103E": ResistorRating(
        value="10k trimmer",
        power_w=0.25,
        voltage_v=300.0,
        tolerance="+/-10%",
        package="4mm SMD trimmer",
        source="Bourns 3224 datasheet: 0.25W at 85C, 300V max, +/-10%, +/-100ppm/C.",
    ),
    "3224W-1-205E": ResistorRating(
        value="2M trimmer",
        power_w=0.25,
        voltage_v=300.0,
        tolerance="+/-10%",
        package="4mm SMD trimmer",
        source="Bourns 3224 datasheet and LCSC C116323 order source: 2M, 0.25W at 85C, 300V max.",
    ),
}


def capacitor_stress(comp: dict[str, str]) -> CapacitorStress:
    value = comp["value"]
    if value == "100nF MPD bias":
        return CapacitorStress(
            voltage_v=5.05,
            reason="LM4040 monitor-PD bias reference capacitor is across the nominal 5V LASER_V+ to MPD_BIAS reference",
        )
    if value in {"1uF 100V", "10uF 50V", "22uF 100V"}:
        return CapacitorStress(
            voltage_v=24.0,
            reason="24V barrel/RJ45 input capacitor on VIN_24V",
        )
    if value in {"10uF laser buck", "22uF laser buck"}:
        return CapacitorStress(
            voltage_v=9.38,
            reason="AP63200 laser-buck output capacitor at the 237k/22.1k LASER_V+ setting",
        )
    if value in {"10uF 5V buck", "22uF 5V buck", "10uF +5V bulk"}:
        return CapacitorStress(
            voltage_v=5.1,
            reason="5V buck/post-OR board rail bulk capacitor",
        )
    if value == "100nF BST":
        return CapacitorStress(
            voltage_v=5.0,
            reason="AP63200/AP63205 bootstrap capacitor charged from the internal high-side gate-drive supply",
        )
    if value == "100pF FF":
        return CapacitorStress(
            voltage_v=9.38 - 0.8,
            reason="AP63200 feed-forward capacitor across the top feedback resistor from LASER_V+ to the 0.8V FB node",
        )
    if value == "100nF MPD ADC":
        return CapacitorStress(
            voltage_v=3.3,
            reason="ADC-side monitor-PD output filter is limited by the INA4180 output on the ESP32 3.3V ADC domain",
        )
    if value == "10pF C0G":
        return CapacitorStress(
            voltage_v=5.0,
            reason="op-amp feedback/loop compensation node in the 5V analog domain",
        )
    return CapacitorStress(
        voltage_v=5.0,
        reason="worst-case 5V bench rail stress for local decoupling/filter capacitors",
    )


def resistor_stress(comp: dict[str, str]) -> ResistorStress:
    value = comp["value"]
    mpn = comp["mpn"]
    if comp["ref"] == "R63":
        return ResistorStress(
            power_w=(24.0 - 2.0) * (24.0 - 2.0) / 10_000.0,
            voltage_v=24.0 - 2.0,
            reason="RJ45 24V-side LED/contact resistor; assumes about 2V internal LED drop on the access-controller connector LED pin convention",
        )
    if comp["ref"] == "R64":
        return ResistorStress(
            power_w=3.3 * 3.3 / 10_000.0,
            voltage_v=3.3,
            reason="RJ45 3V3-side LED/contact resistor copied from the access-controller connector LED pin convention",
        )
    if mpn == "HoCR2512-2W-10R-1%":
        return ResistorStress(
            power_w=0.613,
            voltage_v=2.475,
            reason="248mA current clamp through 10 ohm laser source-sense resistor",
        )
    if mpn == "3224W-1-103E":
        return ResistorStress(
            power_w=5.0 * 5.0 / 10_000.0,
            voltage_v=5.0,
            reason="conservative full 5V across 10k VBIAS trim element",
        )
    if mpn == "3224W-1-205E":
        return ResistorStress(
            power_w=5.0 * 5.0 / 2_000_000.0,
            voltage_v=5.0,
            reason="conservative full 5V across 2M TIA feedback trim element",
        )
    if value == "22R USB":
        return ResistorStress(
            power_w=0.0,
            voltage_v=3.6,
            reason="USB series damping resistor; no intentional DC load, checked for steady-state signal voltage only",
        )
    if value == "240R MPD sense":
        return ResistorStress(
            power_w=0.00009,
            voltage_v=0.15,
            reason="monitor-PD sense resistor at the selected D7805I 600uA high-end monitor current; INA4180 gain/output headroom is checked separately",
        )
    if value == "2.49k MPD bias":
        return ResistorStress(
            power_w=(9.38 - 5.0) * (9.38 - 5.0) / 2490.0,
            voltage_v=9.38 - 5.0,
            reason="LM4040 shunt-reference sink from MPD_BIAS to GND at the 237k/22.1k LASER_V+ setting",
        )
    if value == "237k FB":
        return ResistorStress(
            power_w=(9.38 - 0.8) * (9.38 - 0.8) / 237_000.0,
            voltage_v=9.38 - 0.8,
            reason="AP63200 top feedback resistor from LASER_V+ to the 0.8V FB node at the 237k/22.1k setting",
        )
    if value == "22.1K FB":
        return ResistorStress(
            power_w=0.8 * 0.8 / 22_100.0,
            voltage_v=0.8,
            reason="AP63200 bottom feedback resistor from FB to GND",
        )
    resistance_ohms = {
        "1k": 1_000.0,
        "1K": 1_000.0,
        "1k ADC": 1_000.0,
        "750R LIMIT": 750.0,
        "1.3k LIMIT": 1_300.0,
        "3k LIMIT": 3_000.0,
        "4.7k LIMIT": 4_700.0,
        "10k": 10_000.0,
        "10K": 10_000.0,
        "10k BOOT": 10_000.0,
        "22.1K": 22_100.0,
        "47.5K": 47_500.0,
    }.get(value)
    if resistance_ohms is None:
        return ResistorStress(
            power_w=-1.0,
            voltage_v=-1.0,
            reason=f"no stress rule for resistor value {value!r}",
        )
    stress_voltage = 3.3 if value in {"10k BOOT"} else 5.0
    return ResistorStress(
        power_w=stress_voltage * stress_voltage / resistance_ohms,
        voltage_v=stress_voltage,
        reason=f"conservative {stress_voltage:.1f}V DC across {value} resistor",
    )


def is_capacitor(comp: dict[str, str]) -> bool:
    return comp["footprint"].startswith("Capacitor_SMD:")


def is_resistor_or_trimmer(comp: dict[str, str]) -> bool:
    return comp["footprint"].startswith(("Resistor_SMD:", "Potentiometer_SMD:"))


def main() -> int:
    netlist_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lc.net")
    comps = parse_components(netlist_path)
    failures: list[str] = []
    cap_utils: list[tuple[float, str, str, str]] = []
    resistor_power_utils: list[tuple[float, str, str, str]] = []
    resistor_voltage_utils: list[tuple[float, str, str, str]] = []

    for comp in comps:
        if is_capacitor(comp):
            rating = CAP_RATINGS.get(comp["mpn"])
            if rating is None:
                failures.append(f"{comp['ref']} capacitor MPN {comp['mpn']!r} has no rating entry")
                continue
            stress = capacitor_stress(comp)
            util = stress.voltage_v / rating.voltage_v
            cap_utils.append((util, comp["ref"], comp["value"], stress.reason))
            if util > CAP_VOLTAGE_UTIL_LIMIT:
                failures.append(
                    f"{comp['ref']} {comp['value']} uses {stress.voltage_v:.2f}V on "
                    f"{rating.voltage_v:.1f}V {comp['mpn']} "
                    f"({util * 100.0:.1f}% > {CAP_VOLTAGE_UTIL_LIMIT * 100.0:.0f}%): {stress.reason}"
                )
        elif is_resistor_or_trimmer(comp):
            rating = RES_RATINGS.get(comp["mpn"])
            if rating is None:
                failures.append(f"{comp['ref']} resistor/trimmer MPN {comp['mpn']!r} has no rating entry")
                continue
            stress = resistor_stress(comp)
            if stress.power_w < 0 or stress.voltage_v < 0:
                failures.append(f"{comp['ref']} {comp['value']}: {stress.reason}")
                continue
            power_util = stress.power_w / rating.power_w if rating.power_w else float("inf")
            voltage_util = stress.voltage_v / rating.voltage_v if rating.voltage_v else float("inf")
            resistor_power_utils.append((power_util, comp["ref"], comp["value"], stress.reason))
            resistor_voltage_utils.append((voltage_util, comp["ref"], comp["value"], stress.reason))
            if power_util > RESISTOR_POWER_UTIL_LIMIT:
                failures.append(
                    f"{comp['ref']} {comp['value']} dissipates {stress.power_w:.4f}W on "
                    f"{rating.power_w:.2f}W {comp['mpn']} "
                    f"({power_util * 100.0:.1f}% > {RESISTOR_POWER_UTIL_LIMIT * 100.0:.0f}%): {stress.reason}"
                )
            if voltage_util > RESISTOR_VOLTAGE_UTIL_LIMIT:
                failures.append(
                    f"{comp['ref']} {comp['value']} sees {stress.voltage_v:.2f}V on "
                    f"{rating.voltage_v:.1f}V {comp['mpn']} "
                    f"({voltage_util * 100.0:.1f}% > {RESISTOR_VOLTAGE_UTIL_LIMIT * 100.0:.0f}%): {stress.reason}"
                )

    if failures:
        print(f"FAIL {len(failures)} passive derating checks")
        for failure in failures:
            print(f"  {failure}")
        return 1

    max_cap = max(cap_utils, default=(0.0, "", "", ""))
    max_res_power = max(resistor_power_utils, default=(0.0, "", "", ""))
    max_res_voltage = max(resistor_voltage_utils, default=(0.0, "", "", ""))
    print(
        f"PASS passive derating: checked {len(cap_utils)} capacitors and "
        f"{len(resistor_power_utils)} resistors/trimmers"
    )
    print(
        f"  max capacitor voltage utilization: {max_cap[0] * 100.0:.1f}% "
        f"at {max_cap[1]} ({max_cap[2]})"
    )
    print(
        f"  max resistor power utilization: {max_res_power[0] * 100.0:.1f}% "
        f"at {max_res_power[1]} ({max_res_power[2]})"
    )
    print(
        f"  max resistor voltage utilization: {max_res_voltage[0] * 100.0:.1f}% "
        f"at {max_res_voltage[1]} ({max_res_voltage[2]})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
