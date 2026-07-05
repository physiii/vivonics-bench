#!/usr/bin/env python3
"""Generate human-readable net/pin/PCB audit tables from KiCad artifacts."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from collections import deque
from heapq import heappop, heappush
from itertools import permutations
from math import hypot
from pathlib import Path

import gen_pcb
from circuit_designators import WL, ref_for
from check_laser_controller_pcb import (
    PLACEMENT_CHECKS,
    _connect_filled_zone_polygons,
    critical_route_link_statuses,
    count_connected_critical_route_links,
    intentional_unnetted_pad_names,
    min_pad_distance,
    parse_board_pad_inventory,
    parse_board_net_table,
    parse_board_segments,
    parse_board_vias,
    parse_declared_copper_layers,
    parse_footprint_geometry,
    usb_route_quality,
    via_copper_layers,
)
from check_laser_controller_release_gate import (
    LASER_CATHODE_MAX_LENGTH_MM,
    LASER_CATHODE_MIN_WIDTH_MM,
    LASER_SENSE_RETURN_MAX_PATH_MM,
    LASER_SUPPLY_MAX_TOTAL_LENGTH_MM,
    LASER_SUPPLY_MIN_WIDTH_MM,
)
from check_laser_controller_netlist import parse_components, parse_netlist
from pcb_critical_routes import CRITICAL_ROUTE_LINKS, _point_in_pad, parse_pad_geometry_from_text


ZONE_OR_RAIL_NETS = {"+5V", "+3V3", "GND", "VBUS_5V", "VIN_24V", "/POWER_IO/BUCK_5V", "LASER_V+"}
EXPECTED_ZONE_OR_RAIL_PENDING_NETS = {"+5V", "+3V3", "GND", "VBUS_5V", "VIN_24V", "/POWER_IO/BUCK_5V", "LASER_V+"}
RAIL_PENDING_RELEASE_ACTION = {
    "VBUS_5V": "Route protected USB power-entry copper from the copied MCU-sheet VBUS isolation diodes to D5 anode; keep ESD return short.",
    "VIN_24V": "Route the J5 barrel/J6 RJ45 input to the AP63205/AP63200 input capacitors and VIN pins with protected, short 24 V copper.",
    "/POWER_IO/BUCK_5V": "Route the AP63205 output from L1/C64/C65 to D6 anode; keep the switch loop compact and away from analog inputs.",
    "+5V": "Route or pour the post-OR board 5 V rail to every analog, laser-driver, and LDO input load; verify diode drop and current.",
    "+3V3": "Route the AP2112 output rail to ESP32-S3 and strap/decoupling loads; verify LDO thermal margin under radio bursts.",
    "LASER_V+": "Manual wide AP63200 laser-buck output rail from L2/C67/C68 to the direct LDx footprints; size for actual laser current and keep away from TIA/MPD analog nodes.",
    "GND": "Maintain the signed-off In1.Cu GND reference zone and keep laser-current return paths out of TIA summing-node returns after any reroute.",
}


def esc(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def nodes_text(nodes: list[tuple[str, str, str, str]]) -> str:
    return ", ".join(
        f"`{ref}.{pin}`" + (f" `{esc(function)}`" if function else "")
        for ref, pin, function, _ in sorted(nodes)
    )


def intent_for_net(net: str, nodes: list[tuple[str, str, str, str]]) -> str:
    node_pairs = {(ref, pin) for ref, pin, _, _ in nodes}
    if net == "+5V":
        return "Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input."
    if net == "+3V3":
        return "ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling."
    if net == "GND":
        return "Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths."
    if net == "LASER_V+":
        return "AP63200-generated shared bench laser anode / monitor-PD cathode rail to the direct LDx footprints and LM4040 monitor-bias front end."
    if net == "VBUS_5V":
        return "Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing."
    if net == "VIN_24V":
        return "24 V center-positive barrel/RJ45 input after J5/J6, feeding the AP63205 +5 V buck and AP63200 laser buck input pins and local input capacitors."
    if net == "/POWER_IO/BUCK_5V":
        return "AP63205 fixed 5 V buck output after L1 and output capacitors, before D6 OR-ing into the board +5 V rail."
    if re.match(r"Net-\(U15-SW\)$", net):
        return "AP63205 switch node: U15 SW pin, L1 switch-side pin, and the BST capacitor switch-side plate; keep this copper compact."
    if re.match(r"Net-\(U15-BST\)$", net):
        return "AP63205 bootstrap node between U15 BST and the 100 nF capacitor to the switch node."
    if re.match(r"Net-\(U16-SW\)$", net):
        return "AP63200 laser-buck switch node: U16 SW pin, L2 switch-side pin, and the BST capacitor switch-side plate; keep away from MPD/TIA nodes."
    if re.match(r"Net-\(U16-BST\)$", net):
        return "AP63200 bootstrap node between U16 BST and the 100 nF capacitor to the laser-buck switch node."
    if re.match(r"Net-\(U16-FB\)$", net):
        return "AP63200 laser-buck feedback node set by the 237k/22.1k divider and 100 pF feed-forward capacitor for about 9.3 V LASER_V+."
    if re.match(r"Net-\(J6-Pad10\)$", net):
        return "RJ45 LED/contact node copied from the access-controller RJ45 convention: J6 pin 10 current-limited to VIN_24V through R63."
    if re.match(r"Net-\(J6-Pad12\)$", net):
        return "RJ45 LED/contact node copied from the access-controller RJ45 convention: J6 pin 12 current-limited to +3V3 through R64."
    if net.startswith("VOUT"):
        return "OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC."
    if net == "CONVST":
        return "ESP32 GPIO15 conversion-start output to the on-board AD7606-4 CONVSTA/CONVSTB pins."
    if net == "ADC_SCLK":
        return "ESP32 GPIO17 serial clock into the on-board AD7606-4 RD/SCLK pin."
    if net == "ADC_CS":
        return "ESP32 GPIO18 chip-select output into the on-board AD7606-4 CS pin."
    if net == "ADC_MISO_A":
        return "On-board AD7606-4 DOUTA serial data output into ESP32 GPIO21."
    if net == "ADC_MISO_B":
        return "On-board AD7606-4 DOUTB serial data output into ESP32 GPIO38."
    if net == "ADC_BUSY":
        return "On-board AD7606-4 BUSY status output into ESP32 GPIO47."
    if net == "ADC_RESET":
        return "ESP32 GPIO48 reset output into the on-board AD7606-4 RESET pin."
    if re.match(r"Net-\(C5[78]-Pad1\)$", net):
        return "AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin."
    if "REFIN{slash}REFOUT" in net:
        return "AD7606-4 internal/reference output decoupling node at REFIN/REFOUT."
    if "REFCAPA" in net:
        return "AD7606-4 reference-buffer decoupling node tying REFCAPA and REFCAPB to the local reference capacitor."
    if net in {"/MCU_ESP32-S3/D-", "/MCU_ESP32-S3/D+"}:
        return "CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge."
    if net in {"/MCU_ESP32-S3/IO19", "/MCU_ESP32-S3/IO20"}:
        return "ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp."
    if net == "/MCU_ESP32-S3/IO43":
        return "ESP32-S3 UART0 TX into CP2102N RXD for USB-UART console/programming."
    if net == "/MCU_ESP32-S3/IO44":
        return "CP2102N TXD into ESP32-S3 UART0 RX for USB-UART console/programming."
    if net == "/MCU_ESP32-S3/EN":
        return "ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor."
    if net == "/MCU_ESP32-S3/PROG":
        return "ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor."
    if net == "/MCU_ESP32-S3/FACT":
        return "Copied access-controller factory button net on ESP32-S3 GPIO1 with 10 k pull-up."
    if net == "/MCU_ESP32-S3/RTS":
        return "CP2102N RTS output feeding the copied auto-reset transistor network."
    if net == "/MCU_ESP32-S3/DTR":
        return "CP2102N DTR output feeding the copied auto-boot/reset transistor network."
    if re.match(r"/MCU_ESP32-S3/IO(13|14)$", net):
        return "Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up."
    if re.match(r"/MCU_ESP32-S3/IO(17|18|21|3[5-9]|4[0-8])$", net):
        return "Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface."
    if net in {"Net-(D10-A)", "Net-(D13-A)"}:
        return "Copied MCU-sheet Mini-B VBUS before 1N5819HW isolation diode into the board VBUS_5V net."
    if net in {"Net-(Q5-B)", "Net-(Q6-B)"}:
        return "Copied CP2102N RTS/DTR transistor base-drive node for ESP32 EN/GPIO0 auto-reset sequencing."
    if net == "Net-(U10-VBUS)":
        return "CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet."
    if net == "Net-(U10-~{RST})":
        return "CP2102N reset pin pull-up node on the copied MCU sheet."
    if net == "Net-(U10-~{SUSPEND})":
        return "CP2102N active-low suspend status pull network on the copied MCU sheet."
    if net.startswith("PWM"):
        return "ESP32 PWM command into one laser-driver input resistor."
    if net.startswith("ISENSE"):
        return "Laser source-sense telemetry through 1 k isolation into ESP32 ADC."
    if net.startswith("MPD") and net[3:].isdigit():
        return "Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC."
    if "MPD_AMP" in net:
        return "INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter."
    if "MPD_BIAS" in net:
        return "LM4040-derived monitor-PD anode bias node; holds LASER_V+ to MPD_BIAS near 5 V."
    if net == "MPD_RAW4":
        return "Spare/open blue-channel monitor input at INA4180 channel 4; PLT5 450GB has no monitor photodiode."
    if "MPD_RAW" in net:
        return "Raw internal monitor-photodiode anode node from the direct LDx footprint into the 240 ohm high-side sense resistor and INA4180 IN+ pin."
    if net.startswith("LASER_N"):
        return "Laser cathode sink path from the direct LDx footprint to AO3400A drain."
    if net.endswith("/FB"):
        return "Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input."
    if net.endswith("/LOUT"):
        return "TLV9001 output and compensation node before the 1 k MOSFET gate resistor."
    if "USB_DM_CONN" in net:
        return "Legacy USB D- connector-side net from the pre-copied local MCU generator."
    if "USB_DM_ESD" in net:
        return "Legacy protected USB D- net from the pre-copied local MCU generator."
    if "USB_DM" in net:
        return "Legacy native USB D- net to ESP32-S3 GPIO19 / module pin 13."
    if "USB_DP_CONN" in net:
        return "Legacy USB D+ connector-side net from the pre-copied local MCU generator."
    if "USB_DP_ESD" in net:
        return "Legacy protected USB D+ net from the pre-copied local MCU generator."
    if "USB_DP" in net:
        return "Legacy native USB D+ net to ESP32-S3 GPIO20 / module pin 14."
    if "ESP_EN" in net:
        return "ESP32 EN / CHIP_PU reset net: header, 10 k pull-up, POR capacitor, MCU EN pin."
    if "ESP_BOOT" in net:
        return "ESP32 GPIO0 boot-mode net: header, 10 k pull-up, MCU GPIO0 pin."
    if "ESP_TX" in net:
        return "ESP32 UART0 TX to Raspberry Pi / bring-up header."
    if "ESP_RX" in net:
        return "ESP32 UART0 RX from Raspberry Pi / bring-up header."
    if re.match(r"Net-\(U[5-8]-\+\)$", net):
        return "Laser command filter/limiter node into TLV9001 non-inverting input."
    if re.match(r"Net-\(Q[1-4]-G\)$", net):
        return "AO3400A gate node after TLV9001 output resistor."
    if re.match(r"Net-\(D[1-4]-A\)$", net):
        return "TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side."
    if re.match(r"Net-\(D[1-4]-K\)$", net):
        return "SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB."
    if re.match(r"Net-\(U[1-4]-\+\)$", net):
        return "OPA380 non-inverting VBIAS node after trim/filter."
    if re.match(r"Net-\(R\d+-Pad2\)$", net) and any(ref.startswith("RV") and pin == "1" for ref, pin, _, _ in nodes):
        return "TIA VBIAS trim upper node between +5V limiting resistor and trimmer."
    if re.match(r"Net-\(RV\d+-W\)$", net):
        return "TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input."
    if net.startswith("unconnected-"):
        return "Intentional no-connect from generated schematic."
    return "Review required: no specific intent mapping in generator."


def pin_intent_for_node(
    net: str,
    ref: str,
    pin: str,
    function: str,
    pintype: str,
    comp: dict[str, str] | None,
) -> str:
    """Return a component-pin-level reason for a netlist node.

    The net inventory proves what a net does. This pin intent layer proves why a
    specific component pin belongs on that net, which catches ambiguous one-off
    pins that can otherwise hide inside a large rail or connector net.
    """
    value = comp.get("value", "") if comp else ""
    sheet = comp.get("sheet", "") if comp else ""
    footprint = comp.get("footprint", "") if comp else ""
    if re.match(r"Net-\(R\d+-Pad2\)$", net):
        return "TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side."
    net_intent = intent_for_net(net, [(ref, pin, function, pintype)])
    if net_intent.startswith("Review required:"):
        return f"Review required: {ref}.{pin} has no pin-level intent because net `{net}` has no net intent."
    if net.startswith("unconnected-"):
        if "no_connect" in pintype or function in {"NC", "ID"} or ref == "U9" or (ref == "U10" and pin == "12"):
            return f"Intentional no-connect for {value or ref} pin {pin}" + (f" `{function}`." if function else ".")
        return f"Review required: {ref}.{pin} is on an unconnected net without a no-connect pin type."

    if ref == "U9":
        if net == "+3V3":
            return "ESP32-S3 module 3V3 supply input."
        if net == "GND":
            return "ESP32-S3 module ground/return pin."
        if "USB_DM" in net:
            return "ESP32-S3 native USB D- pin GPIO19/module pin 13."
        if "USB_DP" in net:
            return "ESP32-S3 native USB D+ pin GPIO20/module pin 14."
        if net.startswith("PWM"):
            return "ESP32-S3 PWM output for one laser current command channel."
        if net.startswith("ISENSE"):
            return "ESP32-S3 ADC1 input for laser source-sense telemetry."
        if net.startswith("MPD") and net[3:].isdigit():
            return "ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry."
        if net == "CONVST":
            return "ESP32-S3 GPIO15 output for the on-board AD7606-4 conversion-start line."
        if net == "ADC_SCLK":
            return "ESP32-S3 GPIO17 output used as the AD7606-4 serial clock."
        if net == "ADC_CS":
            return "ESP32-S3 GPIO18 output used as the AD7606-4 chip select."
        if net == "ADC_MISO_A":
            return "ESP32-S3 GPIO21 input reading AD7606-4 DOUTA."
        if net == "ADC_MISO_B":
            return "ESP32-S3 GPIO38 input reading AD7606-4 DOUTB."
        if net == "ADC_BUSY":
            return "ESP32-S3 GPIO47 input reading AD7606-4 BUSY."
        if net == "ADC_RESET":
            return "ESP32-S3 GPIO48 output driving AD7606-4 RESET."
        if "ESP_TX" in net:
            return "ESP32-S3 UART0 TX brought to the bench header."
        if "ESP_RX" in net:
            return "ESP32-S3 UART0 RX brought to the bench header."
        if "ESP_EN" in net:
            return "ESP32-S3 EN/CHIP_PU reset pin with pull-up, POR cap, and header access."
        if "ESP_BOOT" in net:
            return "ESP32-S3 GPIO0 boot strap with pull-up and header access."
        if net == "/MCU_ESP32-S3/EN":
            return "ESP32-S3 EN/CHIP_PU reset pin in the copied access-controller reset network."
        if net == "/MCU_ESP32-S3/PROG":
            return "ESP32-S3 GPIO0/BOOT pin in the copied access-controller program/reset network."
        if net == "/MCU_ESP32-S3/FACT":
            return "ESP32-S3 GPIO1 factory button input from the copied access-controller sheet."
        if re.match(r"/MCU_ESP32-S3/IO(13|14|17|18|19|20|21|3[5-9]|4[0-8])$", net):
            return "ESP32-S3 local GPIO pin from the copied access-controller MCU sheet."

    if value == "CP2102N-Axx-xQFN28":
        return {
            "3": "CP2102N ground pin.",
            "4": "CP2102N USB D+ pin on the copied Mini-B USB bridge path.",
            "5": "CP2102N USB D- pin on the copied Mini-B USB bridge path.",
            "6": "CP2102N VDD supply tied to board +3V3.",
            "7": "CP2102N VREGIN tied to board +3V3 for self-powered operation.",
            "8": "CP2102N VBUS sense input from the copied USB VBUS divider/bypass node.",
            "9": "CP2102N reset input with pull-up.",
            "11": "CP2102N active-low suspend status output with pull network.",
            "24": "CP2102N RTS output into the ESP32 auto-reset transistor network.",
            "25": "CP2102N RXD input from ESP32 UART0 TX.",
            "26": "CP2102N TXD output into ESP32 UART0 RX.",
            "28": "CP2102N DTR output into the ESP32 auto-boot/reset transistor network.",
            "29": "CP2102N exposed-pad ground.",
        }.get(pin, f"Intentional copied CP2102N support pin {pin}.")

    if value == "AP2112K-3.3":
        return {
            "1": "AP2112 VIN from post-OR +5V rail.",
            "2": "AP2112 ground return.",
            "3": "AP2112 enable tied high to +5V for always-on bench 3V3.",
            "4": "AP2112 NC pin deliberately left unconnected.",
            "5": "AP2112 regulated +3V3 output.",
        }.get(pin, "Review required: AP2112 unknown pin.")
    if value == "AP63205WU-7 5V BUCK":
        return {
            "1": "AP63205 fixed-output FB pin tied to the BUCK_5V output node after L1.",
            "2": "AP63205 EN tied to VIN_24V for always-on 5 V buck operation when the barrel/RJ45 input is present.",
            "3": "AP63205 VIN from the protected 24 V barrel/RJ45 input.",
            "4": "AP63205 ground return.",
            "5": "AP63205 SW switch node into L1 and the bootstrap capacitor.",
            "6": "AP63205 BST bootstrap pin with 100 nF to SW.",
        }.get(pin, "Review required: AP63205 unknown pin.")
    if value == "AP63200WU-7 9.3V BUCK":
        return {
            "1": "AP63200 feedback pin at the 237k/22.1k divider midpoint for the 9.3 V laser rail.",
            "2": "AP63200 EN tied to VIN_24V for always-on laser buck operation when the barrel/RJ45 input is present.",
            "3": "AP63200 VIN from the protected 24 V barrel/RJ45 input.",
            "4": "AP63200 ground return.",
            "5": "AP63200 SW switch node into L2 and the bootstrap capacitor.",
            "6": "AP63200 BST bootstrap pin with 100 nF to SW.",
        }.get(pin, "Review required: AP63200 unknown pin.")
    if value == "24V DC IN":
        return {
            "1": "Center-positive barrel input pin feeding VIN_24V.",
            "2": "Barrel sleeve ground return.",
            "3": "Barrel jack switch/sleeve contact tied to board ground, matching the access-controller footprint convention.",
        }.get(pin, "Review required: barrel jack unknown pin.")
    if value == "CONN_RJ45":
        return {
            "1": "RJ45 contact intentionally unused on this power-only input.",
            "2": "RJ45 contact intentionally unused on this power-only input.",
            "3": "RJ45 contact intentionally unused on this power-only input.",
            "4": "RJ45 power contact feeding VIN_24V, copied from the access-controller POWER convention.",
            "5": "RJ45 power contact feeding VIN_24V, copied from the access-controller POWER convention.",
            "6": "RJ45 contact intentionally unused on this power-only input.",
            "7": "RJ45 return contact tied to GND, copied from the access-controller return convention.",
            "8": "RJ45 return contact tied to GND, copied from the access-controller return convention.",
            "9": "RJ45 return/shield-related contact tied to GND, copied from the access-controller return convention.",
            "10": "RJ45 LED/contact pin current-limited to VIN_24V through R63, matching the access-controller RJ45 LED-resistor convention.",
            "11": "RJ45 return/shield-related contact tied to GND, copied from the access-controller return convention.",
            "12": "RJ45 LED/contact pin current-limited to +3V3 through R64, matching the access-controller RJ45 LED-resistor convention.",
        }.get(pin, "Review required: RJ45 unknown pin.")
    if value == "C192300":
        return {
            "1": "J7 4x2 SMT utility header ground pin 1.",
            "2": "J7 4x2 SMT utility header ground pin 2.",
            "3": "J7 4x2 SMT utility header +3V3 pin 3.",
            "4": "J7 4x2 SMT utility header +3V3 pin 4.",
            "5": "J7 4x2 SMT utility header +5V pin 5.",
            "6": "J7 4x2 SMT utility header +5V pin 6.",
            "7": "J7 4x2 SMT utility header VIN_24V pin 7.",
            "8": "J7 4x2 SMT utility header VIN_24V pin 8.",
        }.get(pin, "Review required: C192300 utility header unknown pin.")
    if value in {"USB Mini-B", "USB_MINI_B"}:
        return {
            "1": "USB Mini-B VBUS entry into copied MCU-sheet VBUS isolation.",
            "2": "USB Mini-B D- connector pin into the copied USB data path.",
            "3": "USB Mini-B D+ connector pin into the copied USB data path.",
            "4": "USB Mini-B ID pin deliberately unused.",
            "5": "USB Mini-B signal ground.",
            "6": "USB Mini-B shield tied to board GND.",
        }.get(pin, "Review required: USB connector unknown pin.")
    if value == "UART->Pi":
        return {
            "1": "Bring-up header ESP32 UART TX.",
            "2": "Bring-up header ESP32 UART RX.",
            "3": "Bring-up header ESP32 EN/reset access.",
            "4": "Bring-up header ESP32 GPIO0/BOOT access.",
            "5": "Bring-up header ground reference.",
        }.get(pin, "Review required: UART header unknown pin.")
    if value == "AD7606BSTZ-4":
        if net.startswith("VOUT"):
            return "AD7606-4 analog input pin for one OPA380 TIA output channel."
        if net == "+5V":
            return "AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling."
        if net == "+3V3":
            return "AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain."
        if net == "GND":
            return "AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin."
        if net == "CONVST":
            return "AD7606-4 conversion-start input; CONVSTA and CONVSTB are tied together for simultaneous sampling."
        if net == "ADC_SCLK":
            return "AD7606-4 RD/SCLK serial clock input from ESP32 GPIO17."
        if net == "ADC_CS":
            return "AD7606-4 chip-select input from ESP32 GPIO18."
        if net == "ADC_MISO_A":
            return "AD7606-4 DOUTA serial data output to ESP32 GPIO21."
        if net == "ADC_MISO_B":
            return "AD7606-4 DOUTB serial data output to ESP32 GPIO38."
        if net == "ADC_BUSY":
            return "AD7606-4 BUSY conversion-status output to ESP32 GPIO47."
        if net == "ADC_RESET":
            return "AD7606-4 RESET input from ESP32 GPIO48."
        if "REGCAP" in function:
            return "AD7606-4 internal regulator capacitor pin."
        if "REFIN" in function:
            return "AD7606-4 internal/reference output pin decoupled by the local reference capacitor."
        if "REFCAP" in function:
            return "AD7606-4 reference-buffer capacitor pin."
    if value == "LASER PSU":
        return "External laser-anode supply input." if net == "LASER_V+" else "Laser supply connector return ground."
    if value == "EXT 5V":
        return "External 5V input before OR-ing diode." if "EXT5V" in net else "External 5V connector ground."
    if value == "INA4180A1":
        return {
            "1": "INA4180 channel 1 output to the MPD1 ADC RC filter.",
            "2": "INA4180 channel 1 negative input on MPD_BIAS, the load side of the monitor sense resistor.",
            "3": "INA4180 channel 1 positive input on MPD_RAW1, the laser monitor-PD anode side of the sense resistor.",
            "4": "INA4180 3.3 V supply.",
            "5": "INA4180 channel 2 positive input on MPD_RAW2.",
            "6": "INA4180 channel 2 negative input on MPD_BIAS.",
            "7": "INA4180 channel 2 output to the MPD2 ADC RC filter.",
            "8": "INA4180 channel 3 output to the MPD3 ADC RC filter.",
            "9": "INA4180 channel 3 negative input on MPD_BIAS.",
            "10": "INA4180 channel 3 positive input on MPD_RAW3.",
            "11": "INA4180 ground reference for ADC output accuracy.",
            "12": "INA4180 channel 4 positive input on spare/open MPD_RAW4.",
            "13": "INA4180 channel 4 negative input on MPD_BIAS.",
            "14": "INA4180 channel 4 output to the MPD4 ADC RC filter.",
        }.get(pin, "Review required: INA4180 unknown pin.")
    if value == "LM4040C50 5V":
        return {
            "1": "LM4040 cathode tied to LASER_V+ so the reference clamps the high-side monitor-bias drop.",
            "2": "LM4040 anode tied to MPD_BIAS.",
            "3": "LM4040 star pin tied to anode/MPD_BIAS per TI guidance for noisy environments.",
        }.get(pin, "Review required: LM4040 unknown pin.")

    if value == "OPA380AID":
        return {
            "1": "OPA380 datasheet NC pad left unconnected.",
            "2": "OPA380 inverting summing input tied to SFH2201 anode and feedback network.",
            "3": "OPA380 non-inverting VBIAS input.",
            "4": "OPA380 negative supply tied to board GND.",
            "5": "OPA380 datasheet NC pad left unconnected.",
            "6": "OPA380 TIA output to feedback high side and on-board AD7606 input.",
            "7": "OPA380 positive supply tied to +5V with local decoupling.",
            "8": "OPA380 datasheet NC pad left unconnected.",
        }.get(pin, "Review required: OPA380 unknown pin.")
    if value == "TLV9001":
        return {
            "1": "TLV9001 output/loop compensation node before MOSFET gate resistor.",
            "2": "TLV9001 negative supply tied to board GND.",
            "3": "TLV9001 non-inverting command input from PWM RC/limiter.",
            "4": "TLV9001 inverting source-sense feedback input.",
            "5": "TLV9001 positive supply tied to +5V with local decoupling.",
        }.get(pin, "Review required: TLV9001 unknown pin.")
    if value in {
        "D7805I 780nm TO18 STYLE-A LASER+MPD",
        "D6505I 650nm TO18 STYLE-A LASER+MPD",
        "PLT5 520EB_P TO56 LASER+MPD",
    }:
        return {
            "1": "Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.",
            "2": "Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.",
            "3": "Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end.",
        }.get(pin, "Review required: laser-can unknown pin.")
    if value == "PLT5 450GB TO56 LASER CASE":
        return {
            "1": "Direct TO-can PLT5 450GB laser anode tied to LASER_V+.",
            "2": "PLT5 450GB case pin intentionally not tied into the MPD_RAW4 monitor front end.",
            "3": "Direct TO-can PLT5 450GB laser cathode tied to the board low-side current-sink net LASER_N4.",
        }.get(pin, "Review required: PLT5 450GB unknown pin.")
    if value == "AO3400A":
        return {
            "1": "AO3400A gate driven through 1k from TLV9001 loop output.",
            "2": "AO3400A source at the laser current-sense feedback node.",
            "3": "AO3400A drain as low-side laser cathode sink.",
        }.get(pin, "Review required: AO3400A unknown pin.")
    if value == "SFH2201":
        return {
            "1": "SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.",
            "2": "SFH2201 anode into the OPA380 summing node.",
        }.get(pin, "Review required: SFH2201 unknown pin.")
    if value == "SS14":
        if function == "A":
            return "SS14 anode receives one pre-OR 5V source."
        if function == "K":
            return "SS14 cathode feeds the post-OR +5V rail."
    if value in {"4.7uH", "10uH"}:
        if "SW" in net:
            return f"{value} buck inductor switch-side pin."
        if net == "/POWER_IO/BUCK_5V":
            return "4.7uH AP63205 output inductor regulated-output side feeding BUCK_5V."
        if net == "LASER_V+":
            return "10uH AP63200 laser-buck output inductor regulated-output side feeding LASER_V+."
        return f"{value} buck inductor pin."
    if value == "D_1N5819HW":
        return "1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path."
    if value == "SW_PUSH":
        return "Copied MCU pushbutton signal contact." if pin == "1" else "Copied MCU pushbutton ground contact."
    if value in {"Q_L8050QLT1G", "Q_L8550HQLT1G"}:
        return "Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing."
    if value.startswith("VBIAS 10k"):
        return {
            "1": "Bourns trimmer high-side VBIAS adjustment node.",
            "2": "Bourns trimmer wiper feeding the OPA380 VBIAS resistor.",
            "3": "Bourns trimmer low-side return to GND.",
        }.get(pin, "Review required: VBIAS trimmer unknown pin.")
    if value == "RF 2M":
        return {
            "1": "Bourns feedback trimmer low side tied to the OPA380 summing node.",
            "2": "Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.",
            "3": "Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input.",
        }.get(pin, "Review required: feedback trimmer unknown pin.")

    if value.startswith("10R 2W"):
        return "Laser current-sense resistor high side." if net.endswith("/FB") else "Laser current-sense resistor low-side GND return."
    if value.endswith(" LIMIT"):
        return "PWM command limiter node." if re.match(r"Net-\(U[5-8]-\+\)$", net) else "PWM command limiter ground leg."
    if value.startswith("240R MPD sense"):
        return "Monitor-PD sense resistor raw direct-laser side." if "MPD_RAW" in net else "Monitor-PD sense resistor MPD_BIAS side."
    if value.startswith("2.49k MPD bias"):
        return "MPD_BIAS sink resistor high side." if "MPD_BIAS" in net else "MPD_BIAS sink resistor ground return."
    if value.startswith("1k ADC"):
        return "Monitor-PD ADC isolation resistor filtered ADC side." if net.startswith("MPD") and net[3:].isdigit() else "Monitor-PD ADC isolation resistor INA4180 output side."
    if value.startswith("100nF MPD ADC"):
        return "Monitor-PD ADC filter capacitor ADC side." if net.startswith("MPD") and net[3:].isdigit() else "Monitor-PD ADC filter capacitor ground return."
    if value.startswith("100nF MPD bias"):
        return "Monitor-PD bias-reference capacitor participating in the 5V LASER_V+ to MPD_BIAS shunt reference."
    if value in {"10uF VIN", "10uF 5V buck", "10uF laser buck", "100nF BST", "100pF FF"}:
        return f"Power-supply capacitor pin participating in: {net_intent}"
    if value in {"237k FB", "22.1K FB"}:
        return f"AP63200 laser-buck feedback resistor pin participating in: {net_intent}"

    if footprint.startswith("Resistor_SMD"):
        return f"Resistor pin participating in: {net_intent}"
    if footprint.startswith("Capacitor_SMD"):
        return f"Capacitor pin participating in: {net_intent}"
    if footprint.startswith("Connector_PinHeader"):
        return f"Header pin participating in: {net_intent}"
    if footprint.startswith("Diode_SMD"):
        return f"Diode pin participating in: {net_intent}"
    return f"Review required: no component-pin intent rule for {ref}.{pin} ({value}) on `{net}`."


def board_state(board_path: Path) -> dict[str, int]:
    if not board_path.exists():
        return {}
    text = board_path.read_text()
    refs = re.findall(r'\(fp_text reference "?([^"\s\)]+)"?', text)
    copper_layers = re.findall(r'^\s*\(\d+\s+"([^"]+\.Cu)"\s+(?:signal|power)', text, re.M)
    return {
        "footprint_objects": text.count("(footprint "),
        "referenced_footprints": len(refs),
        "unique_references": len(set(refs)),
        "copper_layers": len(copper_layers),
        "segments": text.count("(segment "),
        "vias": text.count("(via "),
        "zones": text.count("(zone "),
        "pad_net_lines": len(re.findall(r'^\s*\(pad .*\(net ', text, re.M)),
        "net_table_entries": len(re.findall(r'^\s*\(net \d+ ', text, re.M)),
    }


def board_intentional_unnetted_pad_count(board_path: Path, netlist_path: Path) -> int | None:
    if not board_path.exists() or not netlist_path.exists():
        return None
    gen_pcb.NET = str(netlist_path)
    _, _, expected_board_ref_by_comp, _, _ = gen_pcb.build_board(emit_routes=False)
    try:
        allowed = intentional_unnetted_pad_names(expected_board_ref_by_comp)
    except KeyError:
        return None
    count = 0
    for ref, pads in parse_board_pad_inventory(board_path).items():
        allowed_for_ref = allowed.get(ref, set())
        for pad_name, net_name in pads:
            if not net_name and pad_name in allowed_for_ref:
                count += 1
    return count


def board_trace_geometry_summary(board_path: Path) -> list[tuple[str, str, str]]:
    if not board_path.exists():
        return []
    net_table = parse_board_net_table(board_path)
    net_by_code = {code: name for name, code in net_table.items()}
    segments = parse_board_segments(board_path, net_by_code)
    vias = parse_board_vias(board_path, net_by_code)
    widths: dict[str, dict[float, int]] = defaultdict(lambda: defaultdict(int))
    via_dims: dict[str, dict[tuple[float, float], int]] = defaultdict(lambda: defaultdict(int))
    for segment in segments:
        net = str(segment["net"])
        widths[gen_pcb.classify_net(net)][float(segment["width"])] += 1
    for via in vias:
        net = str(via["net"])
        via_dims[gen_pcb.classify_net(net)][(float(via["size"]), float(via["drill"]))] += 1

    def format_widths(values: dict[float, int]) -> str:
        return ", ".join(f"{width:.2f}mm x{count}" for width, count in sorted(values.items()))

    def format_vias(values: dict[tuple[float, float], int]) -> str:
        return ", ".join(
            f"{size:.2f}/{drill:.2f}mm x{count}"
            for (size, drill), count in sorted(values.items())
        )

    rows = []
    for class_name in gen_pcb.NET_CLASS_SPECS:
        if class_name not in widths and class_name not in via_dims:
            continue
        rows.append((
            class_name,
            format_widths(widths.get(class_name, {})),
            format_vias(via_dims.get(class_name, {})),
        ))
    return rows


def board_usb_route_detail(board_path: Path) -> tuple[list[tuple[str, str, str, str, str, str, str]], str]:
    if not board_path.exists():
        return [], ""
    net_table = parse_board_net_table(board_path)
    net_by_code = {code: name for name, code in net_table.items()}
    segments = parse_board_segments(board_path, net_by_code)
    vias = parse_board_vias(board_path, net_by_code)
    route_rows, failures = usb_route_quality(segments, vias)
    totals = {
        str(row["chain"]): float(row["length"])
        for row in route_rows
        if row["section"] == "total"
    }
    skew = abs(totals.get("D-", 0.0) - totals.get("D+", 0.0)) if set(totals) == {"D-", "D+"} else 0.0
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for row in route_rows:
        layers = ", ".join(str(layer) for layer in row["layers"]) or "-"
        widths = ", ".join(f"{float(width):.2f} mm" for width in row["widths"]) or "-"
        section = str(row["section"])
        status = (
            "PASS: measured route section is present"
            if section != "total" and int(row["segments"]) > 0
            else "PASS: measured chain is inside generated-board USB limits"
            if section == "total"
            else "BLOCKER: USB route section is missing"
        )
        rows.append(
            (
                str(row["chain"]),
                section,
                str(row["net"]) or "-",
                str(row["segments"]),
                f"{float(row['length']):.2f} mm",
                f"{layers}; widths {widths}; vias {row['vias']}",
                status,
            )
        )
    status = (
        "PASS: USB generated-board route quality gate passed"
        if not failures
        else "BLOCKER: " + "; ".join(failures)
    )
    return rows, f"Pair routed-copper skew: {skew:.2f} mm. {status}"


def board_laser_current_trace_detail(board_path: Path) -> list[tuple[str, str, str, str, str, str, str]]:
    if not board_path.exists():
        return []
    net_table = parse_board_net_table(board_path)
    net_by_code = {code: name for name, code in net_table.items()}
    segments = parse_board_segments(board_path, net_by_code)
    grouped: dict[tuple[str, str, float], dict[str, float | int]] = defaultdict(
        lambda: {"count": 0, "length": 0.0}
    )
    for segment in segments:
        net = str(segment["net"])
        if gen_pcb.classify_net(net) != "Laser_Current":
            continue
        a = segment["a"]
        b = segment["b"]
        assert isinstance(a, tuple) and isinstance(b, tuple)
        key = (net, str(segment["layer"]), float(segment["width"]))
        grouped[key]["count"] = int(grouped[key]["count"]) + 1
        grouped[key]["length"] = float(grouped[key]["length"]) + hypot(a[0] - b[0], a[1] - b[1])

    rows: list[tuple[str, str, str, str, str, str]] = []
    for (net, layer, width), values in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])):
        if net.startswith("LASER_N"):
            role = "laser cathode load path"
            length = float(values["length"])
            if width < LASER_CATHODE_MIN_WIDTH_MM:
                status = "BLOCKER: generated direct-laser route is below the 0.60 mm current-path target"
            elif length > LASER_CATHODE_MAX_LENGTH_MM:
                status = "BLOCKER: generated route is wide enough but too long for the cathode current path"
            else:
                status = "PASS: generated cathode route meets current width/length limits"
        elif net.endswith("/FB"):
            role = "source-sense feedback node"
            status = "REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs"
        elif net == "LASER_V+":
            role = "laser anode supply path"
            length = float(values["length"])
            if width < LASER_SUPPLY_MIN_WIDTH_MM:
                status = "BLOCKER: generated laser-anode rail is below the 0.80 mm current-path target"
            elif length > LASER_SUPPLY_MAX_TOTAL_LENGTH_MM:
                status = "BLOCKER: generated laser-anode route is too long for the board-spanning common-rail target"
            else:
                status = "PASS: generated laser-anode rail meets current width/length limits"
        else:
            role = "laser current net"
            status = "REVIEW"
        rows.append(
            (
                net,
                layer,
                f"{width:.2f} mm",
                str(int(values["count"])),
                f"{float(values['length']):.2f} mm",
                role,
                status,
            )
        )
    return rows


def _point_key(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], 4), round(point[1], 4))


def _shortest_gnd_path_lengths(
    start: tuple[float, float],
    segments: list[dict[str, object]],
) -> dict[tuple[float, float], float]:
    graph: dict[tuple[float, float], list[tuple[float, tuple[float, float]]]] = defaultdict(list)
    for segment in segments:
        if str(segment["net"]) != "GND":
            continue
        a = _point_key(segment["a"])  # type: ignore[arg-type]
        b = _point_key(segment["b"])  # type: ignore[arg-type]
        length = hypot(a[0] - b[0], a[1] - b[1])
        graph[a].append((length, b))
        graph[b].append((length, a))

    start_key = _point_key(start)
    distances: dict[tuple[float, float], float] = {start_key: 0.0}
    queue: list[tuple[float, tuple[float, float]]] = [(0.0, start_key)]
    while queue:
        distance, point = heappop(queue)
        if distance != distances.get(point):
            continue
        for length, neighbor in graph.get(point, []):
            candidate = distance + length
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                heappush(queue, (candidate, neighbor))
    return distances


def board_laser_sense_return_detail(board_path: Path) -> list[tuple[str, str, str, str, str, str]]:
    if not board_path.exists():
        return []
    net_table = parse_board_net_table(board_path)
    net_by_code = {code: name for name, code in net_table.items()}
    segments = parse_board_segments(board_path, net_by_code)
    vias = parse_board_vias(board_path, net_by_code)
    if not segments and not vias:
        return []
    geometry = parse_footprint_geometry(board_path)
    high_current_gnd_vias = [
        via
        for via in vias
        if str(via["net"]) == "GND"
        and float(via["size"]) >= 0.60
        and float(via["drill"]) >= 0.30
    ]
    via_points = [_point_key(via["at"]) for via in high_current_gnd_vias]  # type: ignore[arg-type]
    pad_details: list[tuple[str, str, dict[int, float]]] = []
    rows: list[tuple[str, str, str, str, str, str]] = []
    for color in WL:
        sheet = f"LASER_{color}"
        ref = ref_for(sheet, "R11")
        pad_points = geometry.get(ref, {}).get("pads", {}).get("2", [])
        if not pad_points:
            rows.append((sheet, f"{ref}.2", "-", "-", "-", "BLOCKER: sense resistor GND pad geometry missing"))
            continue
        distances = _shortest_gnd_path_lengths(pad_points[0], segments)
        pad_details.append(
            (
                sheet,
                f"{ref}.2",
                {
                    index: distances.get(via_point, float("inf"))
                    for index, via_point in enumerate(via_points)
                },
            )
        )

    if rows or not pad_details:
        return rows
    if not high_current_gnd_vias:
        return [
            (sheet, pad_name, "-", "-", "-", "BLOCKER: no high-current GND vias")
            for sheet, pad_name, _ in pad_details
        ]

    assignment: tuple[int, ...] | None = None
    assignment_distance = float("inf")
    for candidate in permutations(range(len(high_current_gnd_vias)), len(pad_details)):
        distances = [pad_details[index][2][via_index] for index, via_index in enumerate(candidate)]
        if any(distance > LASER_SENSE_RETURN_MAX_PATH_MM for distance in distances):
            continue
        total = sum(distances)
        if total < assignment_distance:
            assignment_distance = total
            assignment = candidate

    for index, (sheet, pad_name, distances) in enumerate(pad_details):
        via_index = assignment[index] if assignment is not None else min(distances, key=distances.get)
        distance = distances[via_index]
        via = high_current_gnd_vias[via_index]
        if distance == float("inf"):
            rows.append((sheet, pad_name, "-", "-", "-", "BLOCKER: no routed GND path to a high-current via"))
            continue
        status = (
            "PASS: routed sense return reaches an assigned high-current GND via"
            if distance <= LASER_SENSE_RETURN_MAX_PATH_MM
            else "BLOCKER: routed sense return path is too long"
        )
        rows.append(
            (
                sheet,
                pad_name,
                f"{distance:.2f} mm",
                f"({float(via['at'][0]):.2f}, {float(via['at'][1]):.2f})",  # type: ignore[index]
                f"{float(via['size']):.2f}/{float(via['drill']):.2f} mm",
                status,
            )
        )
    return rows


def board_copper_layers(board_path: Path) -> list[str]:
    if not board_path.exists():
        return []
    order: list[str] = []
    for name in re.findall(r'^\s*\(\d+\s+"([^"]+\.Cu)"\s+(?:signal|power)', board_path.read_text(), re.M):
        if name not in order:
            order.append(name)
    return order


def board_net_classes(board_path: Path) -> dict[str, int]:
    if not board_path.exists():
        return {}
    classes: dict[str, int] = {}
    current: str | None = None
    for line in board_path.read_text().splitlines():
        start = re.match(r'\s*\(net_class\s+(?:"([^"]*)"|([^\s\)]+))\s+', line)
        if start:
            current = start.group(1) if start.group(1) is not None else start.group(2)
            classes[current] = 0
            continue
        if current is not None:
            if re.match(r'\s*\(add_net\s+(?:"([^"]*)"|([^\s\)]+))\)', line):
                classes[current] += 1
            elif line.strip() == ")":
                current = None
    return classes


def board_zone_summary(board_path: Path) -> dict[str, int]:
    if not board_path.exists():
        return {}
    text = board_path.read_text()
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_zone = False
    for line in text.splitlines():
        if not in_zone and line.lstrip().startswith("(zone "):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_zone = True
            continue
        if in_zone:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_zone = False
    return {
        "keepout_zones": sum(1 for block in blocks if "(keepout " in block),
        "gnd_reference_zone_defs": sum(
            1
            for block in blocks
            if '(net_name "GND")' in block
            and '(layer "In1.Cu")' in block
            and "(fill yes" in block
        ),
    }


def board_placement_summary(
    board_path: Path,
    netlist_path: Path,
) -> list[tuple[str, float | None, float, str]]:
    if not board_path.exists() or not netlist_path.exists():
        return []

    gen_pcb.NET = str(netlist_path)
    _, _, expected_board_ref_by_comp, _, _ = gen_pcb.build_board(emit_routes=False)
    geometry = parse_footprint_geometry(board_path)

    def board_ref(sheet: str, local_ref: str) -> str:
        return expected_board_ref_by_comp[(sheet, ref_for(sheet, local_ref))]

    rows: list[tuple[str, float | None, float, str]] = []
    for description, args, limit_mm in PLACEMENT_CHECKS:
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        try:
            actual_mm = min_pad_distance(
                geometry,
                board_ref(sheet_a, ref_a),
                pin_a,
                board_ref(sheet_b, ref_b),
                pin_b,
            )
        except KeyError as exc:
            rows.append((description, None, limit_mm, f"MISSING: {exc}"))
            continue
        status = "PASS" if actual_mm <= limit_mm else "REVIEW"
        rows.append((description, actual_mm, limit_mm, status))
    return rows


def board_critical_route_summary(board_path: Path, netlist_path: Path) -> tuple[int, int, int] | None:
    if not board_path.exists() or not netlist_path.exists():
        return None

    gen_pcb.NET = str(netlist_path)
    _, _, expected_board_ref_by_comp, expected_pad_data, _ = gen_pcb.build_board(emit_routes=False)
    expected_pad_nets = {
        ref: {pin: net_name for pin, (_, net_name) in pads.items()}
        for ref, pads in expected_pad_data.items()
    }
    net_table = parse_board_net_table(board_path)
    segments = parse_board_segments(board_path, {code: name for name, code in net_table.items()})
    if not segments:
        return len(segments), 0, len(CRITICAL_ROUTE_LINKS)
    vias = parse_board_vias(board_path, {code: name for name, code in net_table.items()})
    copper_layers = parse_declared_copper_layers(board_path)
    try:
        connected = count_connected_critical_route_links(
            board_path,
            segments,
            vias,
            copper_layers,
            expected_board_ref_by_comp,
            expected_pad_nets,
        )
    except KeyError:
        connected = 0
    return len(segments), connected, len(CRITICAL_ROUTE_LINKS)


def board_critical_route_details(board_path: Path, netlist_path: Path) -> list[tuple[str, str]]:
    if not board_path.exists() or not netlist_path.exists():
        return []

    gen_pcb.NET = str(netlist_path)
    _, _, expected_board_ref_by_comp, expected_pad_data, _ = gen_pcb.build_board(emit_routes=False)
    expected_pad_nets = {
        ref: {pin: net_name for pin, (_, net_name) in pads.items()}
        for ref, pads in expected_pad_data.items()
    }
    net_table = parse_board_net_table(board_path)
    segments = parse_board_segments(board_path, {code: name for name, code in net_table.items()})
    if not segments:
        return []
    rows: list[tuple[str, str]] = []
    vias = parse_board_vias(board_path, {code: name for name, code in net_table.items()})
    copper_layers = parse_declared_copper_layers(board_path)
    try:
        statuses = critical_route_link_statuses(
            board_path,
            segments,
            vias,
            copper_layers,
            expected_board_ref_by_comp,
            expected_pad_nets,
        )
    except KeyError as exc:
        rows.append(("critical local route data", f"MISSING REF/PAD: {exc}"))
        return rows
    for description, connected in statuses:
        rows.append((description, "ROUTED" if connected else "UNROUTED"))
    return rows


def board_full_route_connectivity(board_path: Path) -> tuple[dict[str, int], list[dict[str, object]]]:
    if not board_path.exists():
        return {}, []

    board_text = board_path.read_text()
    copper_layers = set(board_copper_layers(board_path))
    pad_geometry = parse_pad_geometry_from_text(board_text)
    net_table = parse_board_net_table(board_path)
    net_by_code = {code: name for name, code in net_table.items()}
    segments = parse_board_segments(board_path, net_by_code)
    vias = parse_board_vias(board_path, net_by_code)

    RouteNode = tuple[float, float, str]

    def point_key(point: tuple[float, float], layer: str) -> RouteNode:
        return (round(point[0], 4), round(point[1], 4), layer)

    def pad_layers(pad: dict[str, float | str]) -> set[str]:
        layers = str(pad.get("layers", ""))
        if "*.Cu" in layers:
            return set(copper_layers)
        return set(re.findall(r'(?<![\w.*-])(?:[FB]\.Cu|In\d+\.Cu)(?![\w.-])', layers))

    graph_by_net: dict[str, dict[RouteNode, set[RouteNode]]] = defaultdict(lambda: defaultdict(set))
    route_points_by_net_layer: dict[tuple[str, str], set[tuple[float, float]]] = defaultdict(set)
    for segment in segments:
        net = str(segment["net"])
        layer = str(segment["layer"])
        a_point = segment["a"]
        b_point = segment["b"]
        assert isinstance(a_point, tuple) and isinstance(b_point, tuple)
        a = point_key(a_point, layer)
        b = point_key(b_point, layer)
        graph_by_net[net][a].add(b)
        graph_by_net[net][b].add(a)
        route_points_by_net_layer[(net, layer)].add((a[0], a[1]))
        route_points_by_net_layer[(net, layer)].add((b[0], b[1]))

    for via in vias:
        net = str(via["net"])
        point = via["at"]
        assert isinstance(point, tuple)
        layers = sorted(via_copper_layers(via, copper_layers))
        for layer in layers:
            route_points_by_net_layer[(net, layer)].add((round(point[0], 4), round(point[1], 4)))
        via_nodes = [point_key(point, layer) for layer in layers]
        for index, node in enumerate(via_nodes):
            for other in via_nodes[index + 1:]:
                graph_by_net[net][node].add(other)
                graph_by_net[net][other].add(node)

    pads_by_net: dict[str, list[dict[str, object]]] = defaultdict(list)
    for ref, pad_map in pad_geometry.items():
        for pin, pad_list in pad_map.items():
            for pad in pad_list:
                net = str(pad.get("net", ""))
                if not net:
                    continue
                center = (float(pad["x"]), float(pad["y"]))
                nodes = {point_key(center, layer) for layer in pad_layers(pad)}
                if not nodes:
                    continue
                for index, node in enumerate(sorted(nodes)):
                    for other in sorted(nodes)[index + 1:]:
                        graph_by_net[net][node].add(other)
                        graph_by_net[net][other].add(node)
                for node in list(nodes):
                    for route_point in route_points_by_net_layer.get((net, node[2]), set()):
                        if _point_in_pad(route_point, pad, 0.01):
                            route_node = point_key(route_point, node[2])
                            graph_by_net[net][node].add(route_node)
                            graph_by_net[net][route_node].add(node)
                pads_by_net[net].append(
                    {
                        "ref": ref,
                        "pin": pin,
                        "point": (round(center[0], 4), round(center[1], 4)),
                        "nodes": nodes,
                        "pad": pad,
                    }
                )

    _connect_filled_zone_polygons(
        board_path,
        copper_layers,
        segments,
        vias,
        pads_by_net,
        graph_by_net,
        point_key,
        ZONE_OR_RAIL_NETS,
    )

    has_gnd_in1_plane = board_zone_summary(board_path).get("gnd_reference_zone_defs", 0) > 0
    if has_gnd_in1_plane:
        plane_node: RouteNode = (-9999.0, -9999.0, "In1.Cu")
        for pad in pads_by_net.get("GND", []):
            for node in set(pad["nodes"]):  # type: ignore[arg-type]
                if node[2] == "In1.Cu":
                    graph_by_net["GND"][plane_node].add(node)
                    graph_by_net["GND"][node].add(plane_node)
        for via in vias:
            if str(via["net"]) != "GND":
                continue
            if "In1.Cu" not in via_copper_layers(via, copper_layers):
                continue
            point = via["at"]
            assert isinstance(point, tuple)
            via_node = point_key(point, "In1.Cu")
            graph_by_net["GND"][plane_node].add(via_node)
            graph_by_net["GND"][via_node].add(plane_node)

    rows: list[dict[str, object]] = []
    summary = {
        "multi_pad_nets": 0,
        "explicitly_routed_multi_pad_nets": 0,
        "unrouted_multi_pad_nets": 0,
        "zone_or_rail_pending_multi_pad_nets": 0,
    }
    for net, pads in sorted(pads_by_net.items()):
        unique_points = {pad["point"] for pad in pads}
        if len(unique_points) <= 1:
            continue
        summary["multi_pad_nets"] += 1
        graph = graph_by_net.get(net, {})
        unseen = set(range(len(pads)))
        components: list[list[dict[str, object]]] = []
        while unseen:
            start_index = unseen.pop()
            start_nodes = set(pads[start_index]["nodes"])  # type: ignore[arg-type]
            queue: deque[RouteNode] = deque(start_nodes)
            seen: set[RouteNode] = set(start_nodes)
            while queue:
                node = queue.popleft()
                for neighbor in graph.get(node, set()):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        queue.append(neighbor)
            component_indexes = [
                index
                for index, pad in enumerate(pads)
                if set(pad["nodes"]) & seen  # type: ignore[arg-type]
            ]
            component = [pads[index] for index in component_indexes]
            for index in component_indexes:
                unseen.discard(index)
            components.append(component)

        if len(components) == 1:
            status = "EXPLICITLY_ROUTED"
            summary["explicitly_routed_multi_pad_nets"] += 1
        elif net in ZONE_OR_RAIL_NETS:
            status = "ZONE_OR_RAIL_PENDING"
            summary["zone_or_rail_pending_multi_pad_nets"] += 1
        else:
            status = "UNROUTED"
            summary["unrouted_multi_pad_nets"] += 1
        component_text = " | ".join(
            ", ".join(f"{pad['ref']}.{pad['pin']}" for pad in component[:8])
            + (" ..." if len(component) > 8 else "")
            for component in components[:8]
        )
        if len(components) > 8:
            component_text += f" | ... {len(components) - 8} more"
        rows.append(
            {
                "net": net,
                "pad_count": len(pads),
                "components": len(components),
                "status": status,
                "component_text": component_text,
            }
        )
    rows.sort(key=lambda row: (row["status"] == "EXPLICITLY_ROUTED", row["status"], str(row["net"])))
    return summary, rows


def main() -> int:
    netlist_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lc.net")
    board_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("laser_controller.kicad_pcb")
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    nets = parse_netlist(netlist_path)
    comps = parse_components(netlist_path)
    comp_by_ref = {comp["ref"]: comp for comp in comps}

    pin_to_nets: dict[tuple[str, str], list[str]] = defaultdict(list)
    pin_functions: dict[tuple[str, str], str] = {}
    pin_intents: dict[tuple[str, str, str], str] = {}
    missing_pin_intents: list[str] = []
    for net, nodes in nets.items():
        for ref, pin, function, pintype in nodes:
            pin_to_nets[(ref, pin)].append(net)
            if function:
                pin_functions[(ref, pin)] = function
            role = pin_intent_for_node(net, ref, pin, function, pintype, comp_by_ref.get(ref))
            pin_intents[(net, ref, pin)] = role
            if role.startswith("Review required:"):
                missing_pin_intents.append(f"{ref}.{pin} on {net}: {role}")

    lines: list[str] = []
    lines.append("# Laser Controller Full Net/Pin Inventory")
    lines.append("")
    lines.append("Generated from KiCad exported netlist and the current generated PCB artifact.")
    lines.append("")
    lines.append("Schematic references are generated globally unique before KiCad netlist export. Logical route names such as `LASER_GREEN/R12` are resolved through `circuit_designators.py`; physical net nodes use unique refs such as `R29` and `Q3`.")
    lines.append("")
    lines.append("## PCB Trace State")
    lines.append("")
    state = board_state(board_path)
    if state:
        classes = board_net_classes(board_path)
        zones = board_zone_summary(board_path)
        placements = board_placement_summary(board_path, netlist_path)
        critical_routes = board_critical_route_summary(board_path, netlist_path)
        unnetted_pad_count = board_intentional_unnetted_pad_count(board_path, netlist_path)
        trace_geometry = board_trace_geometry_summary(board_path)
        laser_current_trace_detail = board_laser_current_trace_detail(board_path)
        laser_sense_return_detail = board_laser_sense_return_detail(board_path)
        full_route_summary, full_route_rows = board_full_route_connectivity(board_path)
        lines.append("| Metric | Value |")
        lines.append("|---|---:|")
        for key in ["footprint_objects", "referenced_footprints", "unique_references", "copper_layers", "segments", "vias", "zones", "pad_net_lines", "net_table_entries"]:
            lines.append(f"| `{key}` | {state[key]} |")
        if zones:
            for key in ["keepout_zones", "gnd_reference_zone_defs"]:
                lines.append(f"| `{key}` | {zones[key]} |")
        if classes:
            lines.append(f"| `net_classes` | {len(classes)} |")
            lines.append(f"| `classified_nets` | {sum(classes.values())} |")
        if placements:
            passed_placements = sum(1 for _, actual, _, status in placements if actual is not None and status == "PASS")
            lines.append(f"| `placement_proximity_checks` | {passed_placements}/{len(placements)} PASS |")
        if unnetted_pad_count is not None:
            lines.append(f"| `intentional_unnetted_pad_instances` | {unnetted_pad_count} |")
        if critical_routes:
            segment_count, connected_routes, total_routes = critical_routes
            lines.append(f"| `connected_critical_local_route_links` | {connected_routes}/{total_routes} |")
        if full_route_summary:
            for key in [
                "multi_pad_nets",
                "explicitly_routed_multi_pad_nets",
                "unrouted_multi_pad_nets",
                "zone_or_rail_pending_multi_pad_nets",
            ]:
                lines.append(f"| `{key}` | {full_route_summary[key]} |")
        lines.append("")
        if classes:
            lines.append("| Net Class | Nets |")
            lines.append("|---|---:|")
            for class_name, count in classes.items():
                lines.append(f"| `{esc(class_name)}` | {count} |")
            lines.append("")
        if trace_geometry:
            lines.append("### Routed Copper Geometry By Net Class")
            lines.append("")
            lines.append("This table reports the generated routed copper that exists in the current PCB artifact. It does not waive KiCad zone refill, DRC, or manual current-path review.")
            lines.append("")
            lines.append("| Net Class | Segment Widths | Via Size/Drill |")
            lines.append("|---|---|---|")
            for class_name, segment_widths, via_sizes in trace_geometry:
                lines.append(
                    f"| `{esc(class_name)}` | {esc(segment_widths) or '-'} | {esc(via_sizes) or '-'} |"
                )
            lines.append("")
        usb_route_detail, usb_route_status = board_usb_route_detail(board_path)
        if usb_route_detail:
            lines.append("### USB Route Detail")
            lines.append("")
            lines.append(
                "USB is checked as the copied MCU-sheet connector-to-endpoint routed copper "
                "chain for each D+/D- leg. The PCB checker "
                "fails if either chain exceeds the generated-board length limit, uses vias, "
                "leaves F.Cu, changes width, or exceeds the pair-skew limit."
            )
            lines.append("")
            lines.append(esc(usb_route_status))
            lines.append("")
            lines.append("| Chain | Section | Net | Segments | Length | Geometry | Status |")
            lines.append("|---|---|---|---:|---:|---|---|")
            for chain, section, net, segments, length, geometry, status in usb_route_detail:
                lines.append(
                    f"| `{esc(chain)}` | {esc(section)} | `{esc(net)}` | {segments} | "
                    f"{esc(length)} | {esc(geometry)} | {esc(status)} |"
                )
            lines.append("")
        if laser_current_trace_detail:
            lines.append("### Laser Current Trace Detail")
            lines.append("")
            lines.append(
                "This table separates the high-current laser cathode/load paths from source-sense feedback copper. "
                "Any `BLOCKER` row is routed connectivity evidence only; it is not accepted current-path layout."
            )
            lines.append("")
            lines.append("| Net | Layer | Width | Segments | Total Length | Role | Status |")
            lines.append("|---|---|---:|---:|---:|---|---|")
            for net, layer, width, count, length, role, status in laser_current_trace_detail:
                lines.append(
                    f"| `{esc(net)}` | `{esc(layer)}` | {esc(width)} | {count} | {esc(length)} | {esc(role)} | {esc(status)} |"
                )
            lines.append("")
        if laser_sense_return_detail:
            lines.append("### Laser Sense Return Detail")
            lines.append("")
            lines.append(
                "Each 10 ohm 2512 source-sense resistor must return into the GND reference plane through "
                f"a distinct high-current 0.60/0.30 mm via within {LASER_SENSE_RETURN_MAX_PATH_MM:.1f} mm of routed GND copper."
            )
            lines.append("")
            lines.append("| Channel | Sense GND Pad | Routed GND Path | Via | Via Size/Drill | Status |")
            lines.append("|---|---|---:|---|---|---|")
            for channel, pad, path_length, via, via_size, status in laser_sense_return_detail:
                lines.append(
                    f"| `{esc(channel)}` | `{esc(pad)}` | {esc(path_length)} | `{esc(via)}` | {esc(via_size)} | {esc(status)} |"
                )
            lines.append("")
        if state["segments"] == 0 and state["vias"] == 0:
            lines.append("PCB pad-net assignment, stackup, net classes, and footprint-internal keepouts are present and auditable, but trace-level electrical review is still blocked until placement, routing, board-level zones, and KiCad DRC exist. Current board evidence has no routed segments, no vias, and no board-level zones.")
        else:
            unrouted_rows = [
                row for row in full_route_rows
                if row["status"] == "UNROUTED"
            ]
            pending_rail_rows = [
                row for row in full_route_rows
                if row["status"] == "ZONE_OR_RAIL_PENDING"
            ]
            if unrouted_rows or pending_rail_rows:
                unrouted_nets = ", ".join(f"`{row['net']}`" for row in unrouted_rows) or "none"
                pending_nets = ", ".join(f"`{row['net']}`" for row in pending_rail_rows) or "none"
                lines.append(
                    "PCB has explicit pad-net assignments and generated copper for bounded critical-local routes plus "
                    "selected low-speed board-level routes, but the current artifact is not fully connected by explicit "
                    f"copper. Unrouted signal/control nets: {unrouted_nets}. Rail/zone pending nets: {pending_nets}. "
                    "Full-board release still requires routing fixes and native KiCad DRC/parity review."
                )
            else:
                lines.append(
                    "PCB has explicit pad-net assignments and generated F.Cu/B.Cu copper for bounded critical-local "
                    "routes plus selected low-speed board-level routes. All multi-pad nets are explicitly connected "
                    "in the generated artifact; full-board release still requires native KiCad DRC/parity review."
                )
        if full_route_rows:
            pending_rail_rows = [
                row for row in full_route_rows
                if row["status"] == "ZONE_OR_RAIL_PENDING"
            ]
            if pending_rail_rows:
                lines.append("")
                lines.append("### Reviewed Rail/Zone Pending Nets")
                lines.append("")
                lines.append(
                    "These are the only multi-pad nets currently allowed to remain route/zone pending in the current PCB. "
                    "The PCB checker fails if a different rail or any signal/control net enters this state."
                )
                lines.append("")
                lines.append("| Net | Pads | Copper Components | Review Status | Required Release Action | Component Groups |")
                lines.append("|---|---:|---:|---|---|---|")
                for row in pending_rail_rows:
                    net = str(row["net"])
                    review_status = (
                        "REVIEWED_PENDING"
                        if net in EXPECTED_ZONE_OR_RAIL_PENDING_NETS
                        else "UNEXPECTED_PENDING"
                    )
                    release_action = RAIL_PENDING_RELEASE_ACTION.get(net, "Review required; no release action text is defined.")
                    lines.append(
                        f"| `{esc(net)}` | {row['pad_count']} | {row['components']} | "
                        f"{esc(review_status)} | {esc(release_action)} | {esc(str(row['component_text']))} |"
                    )
        if placements:
            lines.append("")
            lines.append("### Placement Proximity Checks")
            lines.append("")
            lines.append(
                "These generated-board checks keep USB protection, ESP32-S3 support parts, "
                "AP2112 decoupling, every TIA input/feedback/decoupling/bias cluster, every "
                "laser gate/sense/control/compensation cluster, and every monitor-PD "
                "sense/reference/ADC-isolation cluster close to the pins they serve."
            )
            lines.append(
                "Rows marked `REVIEW` exceed generated ideal-placement targets; release "
                "gating is handled by the focused geometry, package, DRC, and connectivity checks."
            )
            lines.append("")
            lines.append("| Check | Actual | Limit | Status |")
            lines.append("|---|---:|---:|---|")
            for description, actual_mm, limit_mm, status in placements:
                actual_text = f"{actual_mm:.2f} mm" if actual_mm is not None else "n/a"
                lines.append(f"| {esc(description)} | {actual_text} | {limit_mm:.2f} mm | {esc(status)} |")
        route_details = board_critical_route_details(board_path, netlist_path)
        if route_details:
            lines.append("")
            lines.append("### Critical Local Route Connectivity")
            lines.append("")
            lines.append("These route-link checks use routed segments, vias, pad copper, and filled zones for the same local clusters. Any `UNROUTED` entries are the next routing targets; they are not waived.")
            lines.append("")
            lines.append("| Route Link | Status |")
            lines.append("|---|---|")
            for description, status in route_details:
                lines.append(f"| {esc(description)} | {esc(status)} |")
        if full_route_rows:
            lines.append("")
            lines.append("### Whole-Board Explicit Route Connectivity")
            lines.append("")
            lines.append(
                "This table checks whether every pad on each multi-pad PCB net is connected by explicit routed copper segments. "
                "`ZONE_OR_RAIL_PENDING` nets are expected to rely on planes/zones or rail trunks that still require KiCad refill/DRC. "
                "`UNROUTED` nets still need board-level routing; critical local links passing does not waive these."
            )
            lines.append("")
            lines.append("| Net | Pads | Copper Components | Status | Component Groups |")
            lines.append("|---|---:|---:|---|---|")
            for row in full_route_rows:
                lines.append(
                    f"| `{esc(str(row['net']))}` | {row['pad_count']} | {row['components']} | "
                    f"{esc(str(row['status']))} | {esc(str(row['component_text']))} |"
                )
    else:
        lines.append("PCB file not found; trace-level review is blocked.")
    lines.append("")
    lines.append("## Pin Intent Coverage")
    lines.append("")
    lines.append(
        "Every exported netlist node is assigned a component-pin-level role. "
        "This is stricter than net-level intent: it explains why each specific pin belongs on its net."
    )
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| `exported_netlist_nodes` | {sum(len(nodes) for nodes in nets.values())} |")
    lines.append(f"| `pin_intent_roles` | {len(pin_intents)} |")
    lines.append(f"| `missing_pin_intent_roles` | {len(missing_pin_intents)} |")
    if missing_pin_intents:
        lines.append("")
        lines.append("| Missing Pin Intent |")
        lines.append("|---|")
        for missing in missing_pin_intents:
            lines.append(f"| {esc(missing)} |")
    lines.append("")
    lines.append("## Net Inventory")
    lines.append("")
    lines.append(f"Total exported nets: **{len(nets)}**.")
    lines.append("")
    lines.append("| Net | Nodes | Intent / Review Note |")
    lines.append("|---|---|---|")
    for net, nodes in sorted(nets.items(), key=lambda item: (item[0].startswith("unconnected-"), item[0])):
        lines.append(f"| `{esc(net)}` | {nodes_text(nodes)} | {esc(intent_for_net(net, nodes))} |")

    lines.append("")
    lines.append("## Component Instance Inventory")
    lines.append("")
    lines.append(f"Total schematic components: **{len(comps)}**.")
    lines.append("")
    lines.append("| Ref | Sheet | Value | Footprint | LCSC | MPN |")
    lines.append("|---|---|---|---|---|---|")
    for comp in sorted(comps, key=lambda c: (c["sheet"], c["ref"])):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{esc(comp['ref'])}`",
                    f"`{esc(comp['sheet'])}`",
                    esc(comp["value"]),
                    f"`{esc(comp['footprint'])}`",
                    f"`{esc(comp['lcsc'])}`" if comp["lcsc"] else "",
                    f"`{esc(comp['mpn'])}`" if comp["mpn"] else "",
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Pin Coverage By Physical Reference")
    lines.append("")
    lines.append("Each row is a globally unique schematic/PCB designator. No repeated hierarchical local references are expected in the exported netlist.")
    lines.append("")
    lines.append("| Ref | Sheet | Value(s) | Footprint(s) | Pin Nets | Pin Intent |")
    lines.append("|---|---|---|---|---|---|")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for comp in comps:
        grouped[comp["ref"]].append(comp)
    for ref, ref_comps in sorted(grouped.items()):
        sheets = sorted({comp["sheet"] for comp in ref_comps})
        values = sorted({comp["value"] for comp in ref_comps})
        footprints = sorted({comp["footprint"] for comp in ref_comps})
        pins = []
        roles = []
        for (pin_ref, pin), net_names in sorted(pin_to_nets.items(), key=lambda item: (item[0][0], item[0][1])):
            if pin_ref != ref:
                continue
            function = pin_functions.get((pin_ref, pin), "")
            label = f"`{pin}`"
            if function:
                label += f" `{esc(function)}`"
            label += " -> " + ", ".join(f"`{esc(name)}`" for name in sorted(net_names))
            pins.append(label)
            role_parts = []
            for net_name in sorted(net_names):
                role_parts.append(f"`{pin}` / `{esc(net_name)}`: {esc(pin_intents[(net_name, pin_ref, pin)])}")
            roles.append("<br>".join(role_parts))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{esc(ref)}`",
                    ", ".join(f"`{esc(sheet)}`" for sheet in sheets),
                    ", ".join(esc(value) for value in values),
                    ", ".join(f"`{esc(footprint)}`" for footprint in footprints),
                    "<br>".join(pins),
                    "<br>".join(roles),
                ]
            )
            + " |"
        )

    text = "\n".join(lines) + "\n"
    if out_path:
        out_path.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
