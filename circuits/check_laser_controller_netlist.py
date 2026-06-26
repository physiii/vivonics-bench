#!/usr/bin/env python3
"""Pad-level netlist checks for the generated bench laser controller.

Run after:
  kicad-cli sch export netlist laser_controller.kicad_sch -o /tmp/lc.net
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from circuit_designators import WL, ref_for

ACCESS_CONTROLLER_MCU = Path("/home/andy/projects/access-controller/circuits/controller/microcontroller.kicad_sch")
PROJECT_DIR = Path(__file__).resolve().parent
ESPRESSIF_SYMBOL = "Espressif:ESP32-S3-WROOM-1"


def parse_netlist(path: Path) -> dict[str, list[tuple[str, str, str, str]]]:
    nets: dict[str, list[tuple[str, str, str, str]]] = {}
    current: str | None = None
    for line in path.read_text().splitlines():
        text = line.strip()
        if text.startswith("(net "):
            match = re.search(r'\(name "([^"]*)"\)', text)
            current = match.group(1) if match else ""
            nets[current] = []
        elif current is not None and text.startswith("(node "):
            fields = dict(re.findall(r'\((ref|pin|pinfunction|pintype) "([^"]*)"\)', text))
            nets[current].append(
                (
                    fields.get("ref", ""),
                    fields.get("pin", ""),
                    fields.get("pinfunction", ""),
                    fields.get("pintype", ""),
                )
            )
        elif current is not None and text == ")":
            current = None
    return nets


def parse_components(path: Path) -> list[dict[str, str]]:
    comps: list[dict[str, str]] = []
    in_comp = False
    depth = 0
    block: list[str] = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not in_comp and text.startswith("(comp (ref "):
            in_comp = True
            block = [line]
            depth = line.count("(") - line.count(")")
        elif in_comp:
            block.append(line)
            depth += line.count("(") - line.count(")")
        if in_comp and depth == 0:
            joined = "\n".join(block)
            def match(pattern: str) -> str:
                found = re.search(pattern, joined)
                return found.group(1) if found else ""
            comps.append(
                {
                    "ref": match(r'\(comp \(ref "([^"]+)"\)'),
                    "value": match(r'\(value "([^"]*)"\)'),
                    "footprint": match(r'\(footprint "([^"]*)"\)'),
                    "lcsc": match(r'\(field \(name "LCSC"\) "([^"]*)"\)'),
                    "mpn": match(r'\(field \(name "Part Number"\) "([^"]*)"\)'),
                    "sheet": match(r'\(sheetpath \(names "([^"]*)"\)'),
                }
            )
            in_comp = False
    return comps


def extract_lib_symbol_block(text: str, symbol_name: str) -> str:
    token = f'    (symbol "{symbol_name}"'
    start = text.find(token)
    if start < 0:
        return ""
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def main() -> int:
    netlist_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lc.net")
    nets = parse_netlist(netlist_path)
    comps = parse_components(netlist_path)
    checks: list[tuple[bool, str, str]] = []

    def has(net: str, ref: str, pin: str, pinfunction: str | None = None) -> None:
        nodes = nets.get(net, [])
        ok = any(
            node_ref == ref
            and node_pin == pin
            and (pinfunction is None or node_function == pinfunction)
            for node_ref, node_pin, node_function, _ in nodes
        )
        suffix = f" ({pinfunction})" if pinfunction is not None else ""
        checks.append((ok, net, f"{ref}.{pin}{suffix}"))

    covered_exact_nets: set[str] = set()

    def exact(net: str, expected: list[tuple[str, str]]) -> None:
        covered_exact_nets.add(net)
        actual = {(ref, pin) for ref, pin, _, _ in nets.get(net, [])}
        checks.append((actual == set(expected), net, f"expected {expected}, got {sorted(actual)}"))

    def sig(items: list[tuple[str, str]] | set[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(items))

    def add_expected(
        counter: Counter[tuple[tuple[str, str], ...]],
        items: list[tuple[str, str]] | set[tuple[str, str]],
        count: int = 1,
    ) -> None:
        counter[sig(items)] += count

    comp_by_key = {(comp["sheet"], comp["ref"]): comp for comp in comps}

    source_symbol = ""
    generated_symbol = ""
    if ACCESS_CONTROLLER_MCU.exists():
        source_symbol = extract_lib_symbol_block(ACCESS_CONTROLLER_MCU.read_text(), ESPRESSIF_SYMBOL)
        source_symbol = source_symbol.replace(
            '(property "Footprint" "Espressif:ESP32-S3-WROOM-1"',
            '(property "Footprint" "RF_Module:ESP32-S3-WROOM-1"',
        )
    mcu_sheet = PROJECT_DIR / "mcu.kicad_sch"
    if mcu_sheet.exists():
        generated_symbol = extract_lib_symbol_block(mcu_sheet.read_text(), ESPRESSIF_SYMBOL)
    checks.append(
        (
            bool(source_symbol) and generated_symbol == source_symbol,
            "ESP32-S3 symbol source",
            "generated MCU sheet must use access-controller Espressif symbol block with only footprint-library substitution",
        )
    )

    def expect_component(
        sheet: str,
        ref: str,
        value: str,
        footprint: str,
        mpn: str,
        lcsc: str,
    ) -> None:
        comp = comp_by_key.get((sheet, ref))
        expected = {
            "value": value,
            "footprint": footprint,
            "mpn": mpn,
            "lcsc": lcsc,
        }
        if comp is None:
            checks.append((False, f"{sheet}{ref}", "component missing"))
            return
        actual = {key: comp[key] for key in expected}
        checks.append((actual == expected, f"{sheet}{ref}", f"got {actual}, expected {expected}"))

    pin_defs: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for nodes in nets.values():
        for ref, pin, function, pintype in nodes:
            pin_defs.setdefault((ref, pin), set()).add((function, pintype))

    def expect_pin(ref: str, pin: str, function: str, pintype: str) -> None:
        actual = pin_defs.get((ref, pin), set())
        expected = {(function, pintype)}
        checks.append((actual == expected, f"{ref}.{pin} pin definition", f"got {actual}, expected {expected}"))

    # Exact component identity: value, footprint, MPN, and LCSC. This catches
    # wrong package variants before the net-level checks can silently pass.
    tia_components = {
        "C1": ("10pF C0G", "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder", "CC0603JRNPO9BN100", "C106245"),
        "C11": ("10uF", "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder", "CL21A106KAYNNNE", "C15850"),
        "C2": ("100nF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "CB": ("1uF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05A105KA5NQNC", "C52923"),
        "D1": ("SFH2201", "OptoDevice:Osram_SFH2201", "SFH2201", "C2900216"),
        "R1": ("10k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1002T5E", "C269701"),
        "R2": ("10M", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1005T5E", "C57129"),
        "RB": ("1k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1001T5E", "C21190"),
        "RT": ("10k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1002T5E", "C269701"),
        "RV11": ("VBIAS 10k", "Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical", "3224W-1-103E", "C81348"),
        "U1": ("OPA380AID", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "OPA380AID", "C201677"),
    }
    laser_components = {
        "C21": ("1uF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05A105KA5NQNC", "C52923"),
        "C22": ("100nF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "CC": ("10pF C0G", "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder", "CC0603JRNPO9BN100", "C106245"),
        "LD": ("OFFBOARD LASER+MPD", "", "", ""),
        "Q1": ("AO3400A", "Package_TO_SOT_SMD:SOT-23", "AO3400A", "C20917"),
        "R11": ("10R 2W", "Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder", "HoCR2512-2W-10R-1%", "C5123624"),
        "R12": ("1k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1001T5E", "C21190"),
        "R21": ("10k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1002T5E", "C269701"),
        "R22": ("30k LIMIT", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF3002T5E", "C22984"),
        "R31": ("1k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1001T5E", "C21190"),
        "U11": ("TLV9001", "Package_TO_SOT_SMD:SOT-23-5", "TLV9001IDBVR", "C398363"),
    }
    mcu_components = {
        "C41": ("100nF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "C42": ("10uF", "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder", "CL21A106KAYNNNE", "C15850"),
        "C43": ("100nF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "C44": ("1uF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05A105KA5NQNC", "C52923"),
        "CEN": ("100nF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "J3": ("UART->Pi", "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "", ""),
        "J6": ("USB Mini-B", "Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal", "65100516121", "C5120592"),
        "RBOOT": ("10k BOOT", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "RMC060310KFN", "C269701"),
        "REN": ("10k", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "RMC060310KFN", "C269701"),
        "RUSBM": ("22R USB", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF220JT5E", "C23345"),
        "RUSBP": ("22R USB", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF220JT5E", "C23345"),
        "U10": ("AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", "AP2112K-3.3TRG1", "C51118"),
        "U12": ("USBLC6", "Package_TO_SOT_SMD:SOT-23-6", "USBLC6-2SC6", "C7519"),
        "U9": ("ESP32-S3-WROOM-1", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N16R8", "C2913199"),
    }
    power_io_components = {
        "CINA": ("100nF", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "CREF": ("100nF MPD bias", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525"),
        "C50": ("10uF", "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder", "CL21A106KAYNNNE", "C15850"),
        "D10": ("SS14", "Diode_SMD:D_SMA", "SS14", "C2480"),
        "D11": ("SS14", "Diode_SMD:D_SMA", "SS14", "C2480"),
        "J1": ("AD7606 out", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "", ""),
        "J2": ("EXT 5V", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "", ""),
        "J4": ("LASER+MPD out", "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical", "", ""),
        "J5": ("LASER PSU", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "", ""),
        "RBIAS": ("2.49k MPD bias", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF2491T5E", "C22908"),
        "UMPD": ("INA4180A1", "Package_SO:TSSOP-14_4.4x5mm_P0.65mm", "INA4180A1IPWR", "C2057528"),
        "UREF": ("LM4040C50 5V", "Package_TO_SOT_SMD:SOT-23", "LM4040C50IDBZR", "C69316"),
    }
    for index in range(1, 5):
        power_io_components[f"CMPD{index}"] = ("100nF MPD ADC", "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder", "CL05B104KO5NNNC", "C1525")
        power_io_components[f"RADC{index}"] = ("1k ADC", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603WAF1001T5E", "C21190")
        power_io_components[f"RMPD{index}"] = ("750R MPD sense", "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "RC0603FR-07750RL", "C114635")
    for color in WL:
        for ref, fields in tia_components.items():
            expect_component(f"/TIA_{color}/", ref_for(f"TIA_{color}", ref), *fields)
        for ref, fields in laser_components.items():
            expect_component(f"/LASER_{color}/", ref_for(f"LASER_{color}", ref), *fields)
    for ref, fields in mcu_components.items():
        expect_component("/MCU_ESP32-S3/", ref_for("MCU_ESP32-S3", ref), *fields)
    for ref, fields in power_io_components.items():
        expect_component("/POWER_IO/", ref_for("POWER_IO", ref), *fields)

    # Datasheet package pin functions for every package-sensitive symbol. For
    # passive R/C symbols, empty pin names are expected and asserted through
    # the whole-net signature coverage below.
    for ref in [ref_for(f"TIA_{color}", "U1") for color in WL]:
        for pin, function, pintype in [
            ("1", "NC", "passive+no_connect"),
            ("2", "-", "input"),
            ("3", "+", "input"),
            ("4", "V-", "power_in"),
            ("5", "NC", "passive+no_connect"),
            ("6", "", "output"),
            ("7", "V+", "power_in"),
            ("8", "NC", "passive+no_connect"),
        ]:
            expect_pin(ref, pin, function, pintype)
    for ref in [ref_for(f"LASER_{color}", "U11") for color in WL]:
        for pin, function, pintype in [
            ("1", "", "output"),
            ("2", "V-", "power_in"),
            ("3", "+", "input"),
            ("4", "-", "input"),
            ("5", "V+", "power_in"),
        ]:
            expect_pin(ref, pin, function, pintype)
    for ref in [ref_for(f"LASER_{color}", "LD") for color in WL]:
        for pin, function, pintype in [
            ("1", "LD_K", "passive"),
            ("2", "LD_A/PD_K/CASE", "passive"),
            ("3", "PD_A", "passive"),
        ]:
            expect_pin(ref, pin, function, pintype)
    for pin, function, pintype in [
        ("1", "VIN", "power_in"),
        ("2", "GND", "power_in"),
        ("3", "EN", "input"),
        ("4", "NC", "passive+no_connect"),
        ("5", "VOUT", "power_out"),
    ]:
        expect_pin(ref_for("MCU_ESP32-S3", "U10"), pin, function, pintype)
    for pin, function in [("1", "IO1"), ("2", "GND"), ("3", "IO2"), ("4", "IO2"), ("5", "VBUS"), ("6", "IO1")]:
        expect_pin(ref_for("MCU_ESP32-S3", "U12"), pin, function, "passive")
    for pin, function, pintype in [
        ("1", "OUT1", "output"),
        ("2", "IN-1", "input"),
        ("3", "IN+1", "input"),
        ("4", "VS", "power_in"),
        ("5", "IN+2", "input"),
        ("6", "IN-2", "input"),
        ("7", "OUT2", "output"),
        ("8", "OUT3", "output"),
        ("9", "IN-3", "input"),
        ("10", "IN+3", "input"),
        ("11", "GND", "power_in"),
        ("12", "IN+4", "input"),
        ("13", "IN-4", "input"),
        ("14", "OUT4", "output"),
    ]:
        expect_pin(ref_for("POWER_IO", "UMPD"), pin, function, pintype)
    for pin, function in [("1", "K"), ("2", "A"), ("3", "*")]:
        expect_pin(ref_for("POWER_IO", "UREF"), pin, function, "passive")
    for pin, function, pintype in [
        ("1", "GND", "power_in"),
        ("2", "3V3", "power_in"),
        ("3", "EN", "input"),
        ("4", "GPIO4/TOUCH4/ADC1_CH3", "bidirectional"),
        ("5", "GPIO5/TOUCH5/ADC1_CH4", "bidirectional"),
        ("6", "GPIO6/TOUCH6/ADC1_CH5", "bidirectional"),
        ("7", "GPIO7/TOUCH7/ADC1_CH6", "bidirectional"),
        ("9", "GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N", "bidirectional"),
        ("10", "GPIO17/U1TXD/ADC2_CH6", "bidirectional"),
        ("12", "GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1", "bidirectional"),
        ("13", "GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-", "bidirectional"),
        ("14", "GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+", "bidirectional"),
        ("17", "GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD", "bidirectional"),
        ("21", "GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ", "bidirectional"),
        ("22", "GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP", "bidirectional"),
        ("27", "GPIO0/BOOT", "bidirectional"),
        ("31", "GPIO38/FSPIWP/SUBSPIWP", "bidirectional"),
        ("36", "U0RXD/GPIO44/CLK_OUT2", "bidirectional"),
        ("37", "U0TXD/GPIO43/CLK_OUT1", "bidirectional"),
        ("38", "GPIO2/TOUCH2/ADC1_CH1", "bidirectional"),
        ("39", "GPIO1/TOUCH1/ADC1_CH0", "bidirectional"),
        ("40", "GND", "passive"),
        ("41", "GND", "passive"),
    ]:
        expect_pin("U9", pin, function, pintype)
    for pin in ["8", "11", "15", "16", "18", "19", "20", "23", "24", "25", "26", "28", "29", "30", "32", "33", "34", "35"]:
        actual = pin_defs.get(("U9", pin), set())
        ok = len(actual) == 1 and next(iter(actual))[1] == "bidirectional+no_connect"
        checks.append((ok, f"U9.{pin} deliberate no-connect", f"got {actual}"))
    package_pin_expectations = {
        **{
            ref_for(f"LASER_{color}", "Q1"): [("1", "G", "input"), ("2", "S", "passive"), ("3", "D", "passive")]
            for color in WL
        },
        **{
            ref_for(f"TIA_{color}", "D1"): [("1", "K", "passive"), ("2", "A", "passive")]
            for color in WL
        },
        ref_for("POWER_IO", "D10"): [("1", "A", "passive"), ("2", "K", "passive")],
        ref_for("POWER_IO", "D11"): [("1", "A", "passive"), ("2", "K", "passive")],
    }
    for ref, pins in package_pin_expectations.items():
        for pin, function, pintype in pins:
            expect_pin(ref, pin, function, pintype)
    for pin, function, pintype in [
        ("1", "VBUS", "passive"),
        ("2", "D-", "passive"),
        ("3", "D+", "passive"),
        ("4", "ID", "passive+no_connect"),
        ("5", "GND", "passive"),
        ("6", "SHLD", "passive"),
    ]:
        expect_pin(ref_for("MCU_ESP32-S3", "J6"), pin, function, pintype)

    # Datasheet package pinouts and exact electrical intent.
    ldo = ref_for("MCU_ESP32-S3", "U10")
    usblc = ref_for("MCU_ESP32-S3", "U12")
    usb_j = ref_for("MCU_ESP32-S3", "J6")
    uart_j = ref_for("MCU_ESP32-S3", "J3")
    ad7606_j = ref_for("POWER_IO", "J1")
    ext5_j = ref_for("POWER_IO", "J2")
    d_usb = ref_for("POWER_IO", "D10")
    d_ext = ref_for("POWER_IO", "D11")
    ina_mpd = ref_for("POWER_IO", "UMPD")
    mpd_ref = ref_for("POWER_IO", "UREF")

    for item in [(ldo, "1", "VIN"), (ldo, "3", "EN")]:
        has("+5V", *item)
    for color in WL:
        has("+5V", ref_for(f"TIA_{color}", "U1"), "7", "V+")
        has("+5V", ref_for(f"LASER_{color}", "U11"), "5", "V+")
    for item in [(ldo, "5", "VOUT"), ("U9", "2", "3V3")]:
        has("+3V3", *item)
    for item in [(ldo, "2", "GND"), (usblc, "2", "GND")]:
        has("GND", *item)

    for color in WL:
        sheet = f"LASER_{color}"
        exact(f"/{sheet}/FB", [
            (ref_for(sheet, "CC"), "1"),
            (ref_for(sheet, "Q1"), "2"),
            (ref_for(sheet, "R11"), "1"),
            (ref_for(sheet, "R12"), "1"),
            (ref_for(sheet, "U11"), "4"),
        ])
        exact(f"/{sheet}/LOUT", [
            (ref_for(sheet, "CC"), "2"),
            (ref_for(sheet, "R31"), "1"),
            (ref_for(sheet, "U11"), "1"),
        ])
        exact(f"Net-({ref_for(sheet, 'Q1')}-G)", [
            (ref_for(sheet, "Q1"), "1"),
            (ref_for(sheet, "R31"), "2"),
        ])
        exact(f"Net-({ref_for(sheet, 'U11')}-+)", [
            (ref_for(sheet, "C21"), "1"),
            (ref_for(sheet, "R21"), "2"),
            (ref_for(sheet, "R22"), "1"),
            (ref_for(sheet, "U11"), "3"),
        ])

    for index, (color, j4_pin) in enumerate(zip(WL, ["1", "3", "5", "7"]), 1):
        exact(f"LASER_N{index}", [
            ("J4", j4_pin),
            (ref_for(f"LASER_{color}", "LD"), "1"),
            (ref_for(f"LASER_{color}", "Q1"), "3"),
        ])

    # Native USB path: connector -> USBLC6 -> 22R -> ESP32-S3 GPIO19/20.
    exact("/MCU_ESP32-S3/USB_DM_CONN", [(usb_j, "2"), (usblc, "1")])
    exact("/MCU_ESP32-S3/USB_DM_ESD", [(usblc, "6"), (ref_for("MCU_ESP32-S3", "RUSBM"), "1")])
    exact("/MCU_ESP32-S3/USB_DM", [(ref_for("MCU_ESP32-S3", "RUSBM"), "2"), ("U9", "13")])
    exact("/MCU_ESP32-S3/USB_DP_CONN", [(usb_j, "3"), (usblc, "3")])
    exact("/MCU_ESP32-S3/USB_DP_ESD", [(usblc, "4"), (ref_for("MCU_ESP32-S3", "RUSBP"), "1")])
    exact("/MCU_ESP32-S3/USB_DP", [(ref_for("MCU_ESP32-S3", "RUSBP"), "2"), ("U9", "14")])
    exact("/MCU_ESP32-S3/ESP_TX", [(uart_j, "1"), ("U9", "37")])
    exact("/MCU_ESP32-S3/ESP_RX", [(uart_j, "2"), ("U9", "36")])
    exact("/MCU_ESP32-S3/ESP_EN", [(ref_for("MCU_ESP32-S3", "CEN"), "1"), (uart_j, "3"), (ref_for("MCU_ESP32-S3", "REN"), "2"), ("U9", "3")])
    exact("/MCU_ESP32-S3/ESP_BOOT", [(uart_j, "4"), (ref_for("MCU_ESP32-S3", "RBOOT"), "2"), ("U9", "27")])

    # Internal laser monitor PD feedback: PLT5-style monitor-PD anode into a
    # high-side sense resistor, INA4180A1 gain=20, then ADC-side RC filtering.
    ina_in_plus = {1: "3", 2: "5", 3: "10", 4: "12"}
    ina_in_minus = {1: "2", 2: "6", 3: "9", 4: "13"}
    ina_out = {1: "1", 2: "7", 3: "8", 4: "14"}
    for index, j4_pin in enumerate(["2", "4", "6", "8"], 1):
        exact(
            f"MPD_RAW{index}",
            [
                ("J4", j4_pin),
                (ref_for(f"LASER_{WL[index - 1]}", "LD"), "3"),
                (ref_for("POWER_IO", f"RMPD{index}"), "1"),
                (ina_mpd, ina_in_plus[index]),
            ],
        )
        exact(
            f"/POWER_IO/MPD_AMP{index}",
            [
                (ina_mpd, ina_out[index]),
                (ref_for("POWER_IO", f"RADC{index}"), "1"),
            ],
        )
    for index, esp_pin in enumerate(["38", "39", "12", "17"], 1):
        exact(
            f"MPD{index}",
            [
                (ref_for("POWER_IO", f"CMPD{index}"), "1"),
                (ref_for("POWER_IO", f"RADC{index}"), "2"),
                ("U9", esp_pin),
            ],
        )
    mpd_bias_nodes: list[tuple[str, str]] = [
        (mpd_ref, "2"),
        (mpd_ref, "3"),
        (ref_for("POWER_IO", "CREF"), "2"),
        (ref_for("POWER_IO", "RBIAS"), "1"),
    ]
    for index in range(1, 5):
        mpd_bias_nodes.append((ref_for("POWER_IO", f"RMPD{index}"), "2"))
        mpd_bias_nodes.append((ina_mpd, ina_in_minus[index]))
    exact("/POWER_IO/MPD_BIAS", sorted(mpd_bias_nodes))
    for index, (color, esp_pin) in enumerate(zip(WL, ["4", "5", "6", "7"]), 1):
        exact(f"ISENSE{index}", [(ref_for(f"LASER_{color}", "R12"), "2"), ("U9", esp_pin)])
    for index, (color, esp_pin) in enumerate(zip(WL, ["9", "31", "21", "22"]), 1):
        exact(f"PWM{index}", [(ref_for(f"LASER_{color}", "R21"), "1"), ("U9", esp_pin)])

    # Board interfaces: external ADC, laser harness, laser PSU, and 5V input OR-ing.
    for index, (color, j1_pin) in enumerate(zip(WL, ["1", "2", "3", "4"]), 1):
        sheet = f"TIA_{color}"
        exact(f"VOUT{index}", [
            (ref_for(sheet, "C1"), "2"),
            (ad7606_j, j1_pin),
            (ref_for(sheet, "R2"), "2"),
            (ref_for(sheet, "U1"), "6"),
        ])
    exact("CONVST", [(ad7606_j, "5"), ("U9", "10")])
    laser_vplus_nodes = [("J4", "9"), ("J5", "1"), (mpd_ref, "1"), (ref_for("POWER_IO", "CREF"), "1")]
    for color in WL:
        laser_vplus_nodes.append((ref_for(f"LASER_{color}", "LD"), "2"))
    exact("LASER_V+", sorted(laser_vplus_nodes))
    exact("VBUS_5V", [(d_usb, "1"), (usb_j, "1"), (usblc, "5")])
    exact("/POWER_IO/EXT5V", [(d_ext, "1"), (ext5_j, "1")])

    # Full rail-membership guards. These are intentionally exact because a
    # stray power pin hidden on a broad rail is just as dangerous as a signal
    # net short.
    plus5_nodes: set[tuple[str, str]] = {
        (d_usb, "2"),
        (d_ext, "2"),
        (ref_for("POWER_IO", "C50"), "1"),
        (ref_for("MCU_ESP32-S3", "C44"), "1"),
        (ldo, "1"),
        (ldo, "3"),
    }
    plus3v3_nodes: set[tuple[str, str]] = {
        ("U9", "2"),
        (ldo, "5"),
        (ref_for("MCU_ESP32-S3", "C41"), "1"),
        (ref_for("MCU_ESP32-S3", "C42"), "1"),
        (ref_for("MCU_ESP32-S3", "C43"), "1"),
        (ref_for("MCU_ESP32-S3", "REN"), "1"),
        (ref_for("MCU_ESP32-S3", "RBOOT"), "1"),
        (ina_mpd, "4"),
        (ref_for("POWER_IO", "CINA"), "1"),
    }
    gnd_nodes: set[tuple[str, str]] = {
        (usb_j, "5"),
        (usb_j, "6"),
        (uart_j, "5"),
        ("U9", "1"),
        ("U9", "40"),
        ("U9", "41"),
        (usblc, "2"),
        (ldo, "2"),
        (ref_for("MCU_ESP32-S3", "C41"), "2"),
        (ref_for("MCU_ESP32-S3", "C42"), "2"),
        (ref_for("MCU_ESP32-S3", "C43"), "2"),
        (ref_for("MCU_ESP32-S3", "C44"), "2"),
        (ref_for("MCU_ESP32-S3", "CEN"), "2"),
        (ad7606_j, "6"),
        (ext5_j, "2"),
        ("J4", "10"),
        ("J5", "2"),
        (ref_for("POWER_IO", "C50"), "2"),
        (ina_mpd, "11"),
        (ref_for("POWER_IO", "CINA"), "2"),
        (ref_for("POWER_IO", "RBIAS"), "2"),
    }
    for color in WL:
        tia_sheet = f"TIA_{color}"
        plus5_nodes.update({
            (ref_for(tia_sheet, "U1"), "7"),
            (ref_for(tia_sheet, "C2"), "1"),
            (ref_for(tia_sheet, "RB"), "1"),
            (ref_for(tia_sheet, "RT"), "1"),
        })
        gnd_nodes.update({
            (ref_for(tia_sheet, "U1"), "4"),
            (ref_for(tia_sheet, "C2"), "2"),
            (ref_for(tia_sheet, "CB"), "2"),
            (ref_for(tia_sheet, "C11"), "2"),
            (ref_for(tia_sheet, "RV11"), "3"),
        })

        laser_sheet = f"LASER_{color}"
        plus5_nodes.update({
            (ref_for(laser_sheet, "U11"), "5"),
            (ref_for(laser_sheet, "C22"), "1"),
        })
        gnd_nodes.update({
            (ref_for(laser_sheet, "U11"), "2"),
            (ref_for(laser_sheet, "C21"), "2"),
            (ref_for(laser_sheet, "C22"), "2"),
            (ref_for(laser_sheet, "R11"), "2"),
            (ref_for(laser_sheet, "R22"), "2"),
        })

    for index in range(1, 5):
        gnd_nodes.update({
            (ref_for("POWER_IO", f"CMPD{index}"), "2"),
        })

    exact("+5V", sorted(plus5_nodes))
    exact("+3V3", sorted(plus3v3_nodes))
    exact("GND", sorted(gnd_nodes))

    # On-board sample photodiode TIA orientation.
    for color in WL:
        sheet = f"TIA_{color}"
        exact(f"Net-({ref_for(sheet, 'D1')}-A)", [
            (ref_for(sheet, "C1"), "1"),
            (ref_for(sheet, "D1"), "2"),
            (ref_for(sheet, "R2"), "1"),
            (ref_for(sheet, "U1"), "2"),
        ])
        exact(f"Net-({ref_for(sheet, 'D1')}-K)", [
            (ref_for(sheet, "CB"), "1"),
            (ref_for(sheet, "D1"), "1"),
            (ref_for(sheet, "RB"), "2"),
        ])
        exact(f"Net-({ref_for(sheet, 'U1')}-+)", [
            (ref_for(sheet, "R1"), "2"),
            (ref_for(sheet, "C11"), "1"),
            (ref_for(sheet, "U1"), "3"),
        ])
        exact(f"Net-({ref_for(sheet, 'RT')}-Pad2)", [
            (ref_for(sheet, "RT"), "2"),
            (ref_for(sheet, "RV11"), "1"),
        ])
        exact(f"Net-({ref_for(sheet, 'RV11')}-W)", [
            (ref_for(sheet, "RV11"), "2"),
            (ref_for(sheet, "R1"), "1"),
        ])

    allowed_single_node_pins: set[tuple[str, str]] = {
        (usb_j, "4"),  # USB Mini-B ID pin is unused for device mode.
        (ldo, "4"),  # AP2112 SOT-23-5 NC pin.
    }
    for color in WL:
        tia_ref = ref_for(f"TIA_{color}", "U1")
        allowed_single_node_pins.update({(tia_ref, "1"), (tia_ref, "5"), (tia_ref, "8")})
    for pin in [
        "8",
        "11",
        "15",
        "16",
        "18",
        "19",
        "20",
        "23",
        "24",
        "25",
        "26",
        "28",
        "29",
        "30",
        "32",
        "33",
        "34",
        "35",
    ]:
        allowed_single_node_pins.add(("U9", pin))
    single_node_pins: dict[tuple[str, str], tuple[str, str, str, str, str]] = {}
    unexpected_single_node_nets = {}
    for net, nodes in sorted(nets.items()):
        if len(nodes) != 1:
            continue
        ref, pin, function, pintype = nodes[0]
        single_node_pins[(ref, pin)] = (net, ref, pin, function, pintype)
        if (ref, pin) not in allowed_single_node_pins or not pintype.endswith("+no_connect") or not net.startswith("unconnected-"):
            unexpected_single_node_nets[net] = nodes[0]
    missing_single_node_pins = sorted(allowed_single_node_pins - set(single_node_pins))
    checks.append(
        (
            not unexpected_single_node_nets,
            "all single-node nets intentionally no-connect",
            f"unexpected {unexpected_single_node_nets}",
        )
    )
    checks.append(
        (
            not missing_single_node_pins,
            "expected no-connect pins export as single-node nets",
            f"missing {missing_single_node_pins}",
        )
    )

    unexpected_multipin_nets = {
        net: sorted((ref, pin) for ref, pin, _, _ in nodes)
        for net, nodes in nets.items()
        if len(nodes) > 1 and net not in covered_exact_nets
    }
    checks.append(
        (
            not unexpected_multipin_nets,
            "all multi-pin nets explicitly asserted",
            f"unexpected {unexpected_multipin_nets}",
        )
    )

    pin_nets: dict[tuple[str, str], set[str]] = defaultdict(set)
    for net, nodes in nets.items():
        for ref, pin, _, _ in nodes:
            pin_nets[(ref, pin)].add(net)
    multi_net_pins = {
        f"{ref}.{pin}": sorted(net_names)
        for (ref, pin), net_names in pin_nets.items()
        if len(net_names) > 1
    }
    checks.append((not multi_net_pins, "physical pin appears on one net only", f"{multi_net_pins}"))

    hand_add_refs = {ad7606_j, uart_j, "J4", "J5", ext5_j} | {
        ref_for(f"LASER_{color}", "LD") for color in WL
    }
    assembled = [comp for comp in comps if comp["ref"] not in hand_add_refs]
    missing_fields = [
        comp
        for comp in assembled
        if not comp["lcsc"] or not comp["mpn"] or not comp["footprint"]
    ]
    hand_with_fields = [
        comp
        for comp in comps
        if comp["ref"] in hand_add_refs and (comp["lcsc"] or comp["mpn"])
    ]
    checks.append((len(comps) == 126, "component count", f"got {len(comps)}, expected 126"))
    checks.append((len(assembled) == 117, "assembled component count", f"got {len(assembled)}, expected 117"))
    checks.append((not missing_fields, "assembled component fields", f"missing {missing_fields}"))
    checks.append((not hand_with_fields, "hand-add field exclusion", f"unexpected fields {hand_with_fields}"))

    expected_lcsc_counts = {
        "C106245": 8,
        "C1525": 17,
        "C15850": 6,
        "C201677": 4,
        "C20917": 4,
        "C21190": 16,
        "C22984": 4,
        "C22908": 1,
        "C23345": 2,
        "C2480": 2,
        "C269701": 14,
        "C2900216": 4,
        "C2913199": 1,
        "C398363": 4,
        "C2057528": 1,
        "C114635": 4,
        "C69316": 1,
        "C51118": 1,
        "C5120592": 1,
        "C5123624": 4,
        "C52923": 9,
        "C57129": 4,
        "C7519": 1,
        "C81348": 4,
    }
    actual_lcsc_counts = Counter(comp["lcsc"] for comp in assembled)
    checks.append(
        (
            actual_lcsc_counts == Counter(expected_lcsc_counts),
            "assembled LCSC counts",
            f"got {dict(actual_lcsc_counts)}, expected {expected_lcsc_counts}",
        )
    )

    failed = [check for check in checks if not check[0]]
    if failed:
        print(f"FAIL {len(failed)} / {len(checks)} netlist assertions")
        for _, net, detail in failed:
            print(f"  {net}: {detail}")
        return 1

    print(f"PASS {len(checks)} netlist assertions across {len(nets)} nets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
