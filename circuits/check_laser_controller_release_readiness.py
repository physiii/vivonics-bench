#!/usr/bin/env python3
"""Track open first-article and production-release blockers.

Exit codes:
  0: no open blockers are registered
  1: blocker registry evidence is inconsistent with the repo docs
  2: one or more known first-article/production blockers remain open

This is not another electrical-rule checker and it is not a Gerber-package
validator. It makes unresolved manual calibration, firmware, thermal,
protection, procurement, and production-release checks visible next to the
generated schematic and PCB gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Evidence:
    path: str
    phrases: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseBlocker:
    blocker_id: str
    title: str
    detail: str
    required_action: str
    evidence: tuple[Evidence, ...]


BLOCKERS: tuple[ReleaseBlocker, ...] = (
    ReleaseBlocker(
        "MONITOR_PD_FRONTEND_RANGE_CALIBRATION",
        "Monitor-PD front-end range and calibration are not released",
        "The exported netlist now proves the INA4180/LM4040 monitor topology is connected as intended, and the 240R/gain20 monitor scale covers the captured D7805I/D6505I/PLT5 520EB_P monitor-current range inside the local ADC-headroom guard. The first-article signoff requires external optical-meter calibration before MPD telemetry is used for APC, normalization, or safety behavior. PLT5 450GB has no monitor photodiode, so MPD4 is not blue-source telemetry. Measured optical calibration and firmware behavior are still unreleased.",
        "Calibrate each monitor-capable source against an external optical meter, record dark/off counts, response slope, saturation threshold, setpoint, and optical-power reading, and verify firmware fail-shutoff behavior before using MPD telemetry for production APC, normalization, or safety decisions.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-05-monitor-pd-first-article-calibration-signoff.md",
                (
                    "LD4` PLT5 450GB has no monitor photodiode",
                    "treat `MPD_RAW4` / `MPD4` as spare/open, not blue-source telemetry",
                    "external optical power meter for each monitor-capable source",
                    "Monitor-PD telemetry must not raise current above the per-channel",
                    "Record dark/off ADC counts, response slope, saturation threshold",
                    "Firmware must fail shutoff or inhibit the source",
                    "does not close production APC",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_optical_calibration_template.csv",
                (
                    "monitor_pd,LD1,INFRARED,MPD_RAW1->MPD1",
                    "monitor_pd,LD2,RED,MPD_RAW2->MPD2",
                    "monitor_pd,LD3,GREEN,MPD_RAW3->MPD3",
                    "monitor_pd,LD4,BLUE,MPD_RAW4->MPD4",
                    "firmware fail-shutoff",
                    "no blue optical telemetry",
                ),
            ),
            Evidence(
                "docs/part-notes/INA4180A1IPWR.md",
                (
                    "selected-monitor-typ-9v3",
                    "selected-monitor-worst-9v3",
                    "`600 uA` high-end monitor current maps",
                ),
            ),
            Evidence(
                "docs/part-notes/laser-harness-pin-code-compatibility.md",
                (
                    "`D7805I` monitor current is checked",
                    "selected-monitor-worst-9v3",
                    "MPD still needs optical calibration",
                ),
            ),
            Evidence(
                "circuits/README.md",
                (
                    "D7805I max maps to about 2.88 V",
                    "Selected blue diode `PLT5 450GB` has no monitor",
                    "MPD_RAW4` / `MPD4` is spare/open",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "D7805I 600 uA high-end monitor current maps to about 2.88 V",
                    "read monitor telemetry from `PLT5 450GB`",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "TIA_READOUT_RANGE_CALIBRATION",
        "Signal-PD TIA readout range and optical calibration are not released",
        "The exported netlist now proves the four SFH2201/OPA380 signal-PD channels feed VOUT1..4 into the AD7606 as intended, and the first-order TIA checker shows the present 2 MOhm feedback trim is a high-sensitivity, low-current bench range. At VBIAS = 1.5 V it has about +1.40 uA / -0.70 uA one-sided OPA380 headroom before the guarded output window clips; the SFH2201 1000 lx datasheet short-circuit-current example would need about 152 V of TIA swing at 2 MOhm and is intentionally an expected-fail case. The first-article signoff now requires dark-offset capture, ambient shielding, known-input calibration, RF/VBIAS recording, and AD7606 scaling checks.",
        "Define the real Vivonics optical photocurrent range at the SFH2201 under the bench optics, choose RF/VBIAS/firmware scaling for that range, shield or limit ambient light, calibrate AD7606 counts against known optical/electrical inputs, and verify firmware saturation/out-of-range behavior before using the signal-PD path for production measurements.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-05-tia-first-article-calibration-signoff.md",
                (
                    "2 Mohm feedback trim as a high-sensitivity, low-current",
                    "Start with VBIAS target 1.5 V",
                    "covered or optically shielded during dark-offset",
                    "Calibrate `VOUT1..4` one channel at a time",
                    "known electrical current injection or a calibrated optical input",
                    "Confirm AD7606 +/-5 V scaling for `VOUT1..4`",
                    "Firmware must flag saturation, out-of-range counts, dark-offset drift",
                    "does not close production measurement release",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_optical_calibration_template.csv",
                (
                    "signal_pd,D1,PD CH1,SFH2201->OPA380->VOUT1",
                    "signal_pd,D2,PD CH2,SFH2201->OPA380->VOUT2",
                    "signal_pd,D3,PD CH3,SFH2201->OPA380->VOUT3",
                    "signal_pd,D4,PD CH4,SFH2201->OPA380->VOUT4",
                    "RF trim; VBIAS; dark ADC counts",
                    "saturation threshold; ambient condition",
                ),
            ),
            Evidence(
                "docs/part-notes/OPA380AID.md",
                (
                    "`check_tia_readout_budget.py` asserts",
                    "+1.40 uA / -0.70 uA",
                    "optical signal range is still a production calibration blocker",
                ),
            ),
            Evidence(
                "circuits/README.md",
                (
                    "check_tia_readout_budget.py",
                    "+1.40 uA / -0.70 uA",
                    "TIA readout range and optical calibration remain release blockers",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "check_tia_readout_budget.py",
                    "SFH2201 1000 lx short-circuit-current example",
                    "Define the real Vivonics optical photocurrent range",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "PER_DIODE_LASER_THERMAL_BUDGET",
        "Per-diode laser bring-up temperature and optical-output signoff are still open",
        "The selected-diode policies now pass on the 9.3 V common rail at typical current, max current, and the per-channel analog command limits. The first-article bring-up signoff requires one laser channel at a time, laser safety controls, external optical-power measurement, and driver/sense-resistor temperature measurement. Physical driver/sense-resistor temperature, optical output, duty cycle, and firmware safety behavior still need measured bring-up evidence.",
        "Measure driver/sense-resistor temperature and optical output during bring-up, verify firmware current/duty-cycle clamps stay at or below the per-channel analog limits, and keep any future laser/rail/current change behind the same current, gate-drive, input-power, and optical safety review.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-05-laser-first-article-bringup-signoff.md",
                (
                    "Bring up one laser channel at a time.",
                    "IR 38.0 mA, red 23.0 mA, green 76.2 mA, blue 105.5 mA",
                    "Measure driver/sense-resistor temperature during bring-up for every channel.",
                    "Measure optical output with an external optical power meter for every channel.",
                    "does not close optical safety",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_laser_bringup_template.csv",
                (
                    "LD1,INFRARED,D7805I,38.0",
                    "LD2,RED,D6505I,23.0",
                    "LD3,GREEN,PLT5 520EB_P,76.2",
                    "LD4,BLUE,PLT5 450GB,105.5",
                    "driver/sense-resistor temperature",
                    "external optical power",
                    "shutoff behavior",
                ),
            ),
            Evidence(
                "circuits/LASER_CURRENT_THERMAL_BUDGET.md",
                (
                    "per-channel analog command limits",
                    "selected-diodes-typ-9v3",
                    "selected-diodes-max-9v3",
                    "selected-diodes-hardware-clamp-9v3",
                    "board-temperature signoff",
                ),
            ),
            Evidence(
                "docs/part-notes/PLT5-520B-harness-reference.md",
                (
                    "green PLT5 520EB_P is limited to about 76.2 mA",
                    "Firmware limits and optical safety behavior still need bring-up validation.",
                ),
            ),
            Evidence(
                "docs/part-notes/laser-harness-pin-code-compatibility.md",
                (
                    "selected-diodes-typ-9v3",
                    "selected-diodes-max-9v3",
                    "selected-diodes-hardware-clamp-9v3",
                ),
            ),
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "Each selected diode and `LASER_V+` setting passes the laser current thermal budget.",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE",
        "AP2112 measurement and sustained-wireless regulator decision are open",
        "The AP2112 is accepted for first-article USB/UART bench use only under the no-RF signoff: ESP32 Wi-Fi/BLE disabled, continuous +3V3 current no higher than 120 mA, and no added 3.3 V loads without rerunning the thermal budget. Sustained ESP32 wireless load still fails the current SOT25 LDO budget.",
        "Measure AP2112 package temperature and +3V3 current during bring-up; keep RF disabled for this bench board, or replace/prove the rail before sustained Wi-Fi/BLE.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-05-ap2112-first-article-signoff.md",
                (
                    "Keep ESP32 Wi-Fi/BLE disabled on this board.",
                    "Keep continuous +3V3 current no higher than 120 mA.",
                    "Measure AP2112 package temperature and +3V3 rail current during first bring-up.",
                    "does not close production regulator decision",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_power_bringup_template.csv",
                (
                    "ldo,U11,+3V3,\"<=120 mA continuous, RF disabled\"",
                    "USB/UART control firmware only; Wi-Fi/BLE disabled",
                    "measure +3V3 rail current; AP2112 package temperature",
                ),
            ),
            Evidence(
                "circuits/POWER_THERMAL_BUDGET.md",
                (
                    "Measure AP2112 package temperature and +3V3 rail current during first bring-up.",
                    "Replace the SOT25 AP2112 rail with a buck regulator",
                ),
            ),
            Evidence(
                "docs/part-notes/AP2112K-3.3TRG1.md",
                (
                    "temperature result proves more margin.",
                    "Production or sustained Wi-Fi/BLE use should replace this rail with a buck",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT",
        "24 V barrel/RJ45 input protection and buck layout are not released",
        "J5 barrel and J6 RJ45 inputs plus the U15/U16 buck supplies are accepted for first-article bench use only under the 2026-07-05 external current-limit signoff: J5 barrel, 24.0 V, current limit no higher than 300 mA, no RJ45 power injection, no hot-plug, and verified center-positive polarity. The AP632 first-article signoff now requires rail verification, startup/ripple/load-step measurement, and buck component temperature measurement before trusting VIN24 buck rails. The VIN24 checker proves the current bench topology is direct J5/J6 to U15/U16 input wiring and intentionally fails production protection because there is no onboard fuse/PTC/TVS/reverse-protection/eFuse/hot-swap component. The AP632 checker passes the selected-diode 9.3 V max-current reference, the all-channel per-channel analog-limit case, and the local 2x22 uF output-capacitance guard.",
        "Define the adapter current limit, RJ45 harness current limit, fuse/current-limit element, reverse-polarity strategy, and transient/TVS protection; then measure AP63205/AP63200 startup, ripple, load-step transient/stability, copper/current path behavior, and temperature before production.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-05-ap632-first-article-buck-validation-signoff.md",
                (
                    "J5 barrel input only",
                    "external current limit no higher than 300 mA",
                    "Verify `/POWER_IO/BUCK_5V`, post-OR `+5V`, and `LASER_V+`",
                    "Treat `LASER_V+` as a 9.3 V-class rail",
                    "Measure startup overshoot, steady ripple, and load-step transient",
                    "Measure U15, U16, L1, L2, D6, C64-C65, and C67-C68 temperature",
                    "does not close production input protection",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_power_bringup_template.csv",
                (
                    "input,J5,VIN_24V,\"24.0 V, <=300 mA current limit\"",
                    "input_gap,VIN24_PROTECTION,VIN_24V,production not released",
                    "buck,U15,/POWER_IO/BUCK_5V,5 V rail verification",
                    "rail,D5/D6,+5V,post-OR rail verification",
                    "buck,U16,LASER_V+,9.3 V-class rail verification",
                    "define fuse/current-limit; reverse-polarity; transient/TVS; RJ45 harness limit",
                ),
            ),
            Evidence(
                "circuits/POWER_TREE.md",
                (
                    "check_vin24_input_protection.py --policy bench-topology",
                    "bench-external-protection",
                    "production-protection",
                    "no fuse/PTC/TVS/reverse-protection/eFuse stage",
                    "bench-selected-max-9v3",
                    "hardware-clamp-9v3",
                    "datasheet-recommended-components",
                    "C61+C62 provide 20 uF nominal",
                ),
            ),
            Evidence(
                "circuits/review/signoff/2026-07-05-vin24-bench-input-signoff.md",
                (
                    "current limit set no higher than 300 mA",
                    "Keep RJ45 power injection disabled",
                    "does not close production input protection",
                ),
            ),
            Evidence(
                "docs/part-notes/AP63200-AP63205.md",
                (
                    "check_vin24_input_protection.py --policy production-protection",
                    "no fuse/PTC/TVS/reverse-protection",
                    "C61+C62 = `20uF`",
                    "C64+C65 = `44uF`",
                    "input range is `3.8 V` to `32 V`",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "PASSIVE_PRODUCTION_AVL_AND_DERATING",
        "Passive quote-time lifecycle, pulse/surge derating, and temperature evidence are open",
        "The first-article passive MPN/LCSC set is now locked against the exported netlist, and the steady-state voltage/power derating gate passes. This still does not prove current JLCPCB/LCSC stock/lifecycle state, field pulse/surge/current derating, substitute approval, or board-temperature measurement.",
        "At order time, verify every locked passive C-code in the JLCPCB quote, reject or explicitly review substitutions, then capture production pulse/surge/current derating and board-temperature evidence before field or production release.",
        (
            Evidence(
                "docs/part-notes/passive-bom-source-note.md",
                (
                    "First-article passive AVL lock",
                    "pulse/surge/current derating",
                    "board-temperature measurement.",
                ),
            ),
            Evidence(
                "docs/part-notes/passive-first-article-avl-lock.md",
                (
                    "Quote-time lifecycle/stock check required",
                    "Board-temperature measurement remains required",
                    "Pulse/surge/current derating remains required",
                    "Production release still needs current quote evidence",
                ),
            ),
            Evidence(
                "circuits/review/calibration/quote_time_procurement_release_template.csv",
                (
                    "current quote timestamp; every C-code accepted by JLCPCB",
                    "BOM/POS accepted together; top-side SMT placement accepted",
                    "24 passive MPN/LCSC pairs checked against quote lifecycle/stock",
                    "reject substitutions or create checkpoint commit",
                    "pulse/surge/current derating for 24 V input and laser-current paths",
                    "measured board temperature at accepted duty cycle",
                    "Gerber zip plus BOM plus POS archived with order number and commit hash",
                ),
            ),
            Evidence(
                "docs/source-register.md",
                (
                    "check_passive_avl_lock.py",
                    "24 passive MPN/LCSC pairs",
                    "quote-time lifecycle/stock",
                ),
            ),
        ),
    ),
    ReleaseBlocker(
        "AD7606_SYSTEM_INTERFACE",
        "On-board AD7606 firmware and bench-readout validation are still open",
        "The bench board routes VOUT1..4 into the on-board AD7606 and the hardware straps now have a checked 10 MHz / 100 kSPS default interface budget. The first-article signoff requires read-after-conversion firmware, RESET/CONVST/BUSY/CS/SCLK timing validation, two-DOUT readback, +/-5 V scaling, and known-input readback before bench ADC data is trusted. Firmware implementation, scoped timing, analog accuracy, and bench ADC readback data remain open.",
        "Implement and scope the ESP32 AD7606 driver, verify RESET/CONVST/BUSY/CS/SCLK timing, confirm +/-5 V range scaling and no-oversampling assumptions in firmware, verify both DOUT lines and channel ordering, and compare readings against known optical/electrical inputs before relying on bench data.",
        (
            Evidence(
                "circuits/review/signoff/2026-07-05-ad7606-first-article-readback-signoff.md",
                (
                    "Keep nominal SCLK at or below 10 MHz",
                    "Default target sample rate is 100 kSPS or lower",
                    "Use read-after-conversion firmware until scoped otherwise.",
                    "Wait for BUSY to fall before asserting CS",
                    "Read 32 SCLK edges per DOUT line",
                    "Read both ADC_MISO_A and ADC_MISO_B",
                    "Confirm RANGE=0 +/-5 V scaling",
                    "16-bit twos-complement with 152.59 uV/LSB",
                    "Apply known voltages or known TIA calibration inputs to VOUT1..4",
                    "does not close firmware implementation",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_firmware_validation_template.csv",
                (
                    "ad7606_timing,U14_CONTROL,RESET/CONVST/BUSY/CS/SCLK,\"SCLK <=10 MHz, sample <=100 kSPS\"",
                    "ad7606_readback,ADC_MISO_A,DOUTA,32 SCLK edges per sample",
                    "ad7606_readback,ADC_MISO_B,DOUTB,32 SCLK edges per sample",
                    "ad7606_scaling,RANGE_OS,\"+/-5 V, no oversampling\",152.59 uV/LSB",
                    "ad7606_channel_order,VOUT1..4,AD7606 V1/V2/V3/V4,known channel ordering",
                    "ad7606_known_input,VOUT1..4,known voltage or TIA input,counts match expected value",
                ),
            ),
            Evidence(
                "circuits/review/calibration/first_article_optical_calibration_template.csv",
                (
                    "adc_readback,U14 V1,PD CH1,VOUT1->AD7606 V1",
                    "adc_readback,U14 V2,PD CH2,VOUT2->AD7606 V2",
                    "adc_readback,U14 V3,PD CH3,VOUT3->AD7606 V3",
                    "adc_readback,U14 V4,PD CH4,VOUT4->AD7606 V4",
                    "+/-5 V scaling; known-input counts",
                ),
            ),
            Evidence(
                "circuits/README.md",
                (
                    "U14 straps `RANGE` low",
                    "oversampling. Confirm ESP32 timing",
                ),
            ),
            Evidence(
                "docs/part-notes/AD7606BSTZ-4RL.md",
                (
                    "`check_ad7606_interface_budget.py` asserts the hardware straps",
                    "default to 100 kSPS or lower",
                    "152.59 uV/LSB",
                ),
            ),
        ),
    ),
)


def validate_evidence() -> list[str]:
    failures: list[str] = []
    for blocker in BLOCKERS:
        for evidence in blocker.evidence:
            path = REPO_DIR / evidence.path
            if not path.exists():
                failures.append(f"{blocker.blocker_id}: missing evidence file {evidence.path}")
                continue
            text = path.read_text()
            for phrase in evidence.phrases:
                if phrase not in text:
                    failures.append(
                        f"{blocker.blocker_id}: {evidence.path} missing evidence phrase: {phrase}"
                    )
    return failures


def main() -> int:
    failures = validate_evidence()
    if failures:
        print(f"FAIL release-readiness blocker registry: {len(failures)} evidence checks failed")
        for failure in failures:
            print(f"  {failure}")
        return 1

    if not BLOCKERS:
        print("PASS release readiness: no open blockers registered")
        return 0

    print(f"BLOCKED production release readiness: {len(BLOCKERS)} open first-article/production blockers")
    for blocker in BLOCKERS:
        print(f"  [{blocker.blocker_id}] {blocker.title}")
        print(f"    Detail: {blocker.detail}")
        print(f"    Required action: {blocker.required_action}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
