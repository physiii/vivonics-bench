"""Critical local route generation and geometry helpers for laser_controller.

This intentionally routes only short, local, layout-critical links. It is not a
full-board autorouter and does not claim the PCB is complete.
"""
from __future__ import annotations

import os
import re
from heapq import heappop, heappush
from math import cos, hypot, radians, sin

from circuit_designators import ref_for

# Must match gen_pcb.py's BOARD_X0_MM/BOARD_Y0_MM/BOARD_X1_MM/BOARD_Y1_MM. Duplicated
# here (rather than imported) because gen_pcb.py imports this module.
BOARD_X0_MM = 30.975
BOARD_Y0_MM = 79.875
BOARD_X1_MM = 204.0
BOARD_Y1_MM = 141.0
BOARD_EDGE_KEEPOUT_MM = 0.7
# Minimum clearance a via must keep from a pad on its OWN net. Vias must never
# sit on/overlap any pad copper -- including same-net pads -- so fanout stays
# off pads (short escape stub + offset via instead of via-in-pad).
SAME_NET_VIA_PAD_CLEARANCE_MM = 0.15

CRITICAL_ROUTE_LINKS = [
    ("USB UART D- connector to ESD", ("MCU_ESP32-S3", "J1", "2", "MCU_ESP32-S3", "D7", "2"), 7.5),
    ("USB UART D+ connector to ESD", ("MCU_ESP32-S3", "J1", "3", "MCU_ESP32-S3", "D8", "2"), 9.5),
    ("USB UART D- ESD to CP2102N", ("MCU_ESP32-S3", "D7", "2", "MCU_ESP32-S3", "U10", "5"), 10.0),
    ("USB UART D+ ESD to CP2102N", ("MCU_ESP32-S3", "D8", "2", "MCU_ESP32-S3", "U10", "4"), 10.0),
    ("Native USB D- connector to ESD", ("MCU_ESP32-S3", "J2", "2", "MCU_ESP32-S3", "D12", "2"), 7.5),
    ("Native USB D+ connector to ESD", ("MCU_ESP32-S3", "J2", "3", "MCU_ESP32-S3", "D11", "2"), 9.5),
    ("Native USB D- ESD to ESP32 GPIO19", ("MCU_ESP32-S3", "D12", "2", "MCU_ESP32-S3", "U9", "13"), 4.5),
    ("Native USB D+ ESD to ESP32 GPIO20", ("MCU_ESP32-S3", "D11", "2", "MCU_ESP32-S3", "U9", "14"), 4.5),
    ("AP2112 input cap at VIN", ("POWER_IO", "C3V3IN", "1", "POWER_IO", "U3V3", "1"), 4.0),
    ("AP2112 100n output cap at VOUT", ("POWER_IO", "C3V3OUT", "1", "POWER_IO", "U3V3", "5"), 4.0),
    ("AP2112 bulk output cap at VOUT", ("POWER_IO", "C3V3BULK", "1", "POWER_IO", "U3V3", "5"), 4.0),
    ("ESP32 local 3V3 decap", ("MCU_ESP32-S3", "C43", "1", "MCU_ESP32-S3", "U9", "2"), 3.0),
    ("ESP32 EN capacitor", ("MCU_ESP32-S3", "C44", "1", "MCU_ESP32-S3", "U9", "3"), 4.0),
    ("ESP32 EN pull-up", ("MCU_ESP32-S3", "R54", "2", "MCU_ESP32-S3", "U9", "3"), 5.0),
    ("ESP32 BOOT pull-up", ("MCU_ESP32-S3", "R53", "2", "MCU_ESP32-S3", "U9", "27"), 4.0),
]

for _color in ["IR", "RED", "GREEN", "BLUE"]:
    _sheet = f"TIA_{_color}"
    CRITICAL_ROUTE_LINKS += [
        (f"{_sheet} photodiode anode to OPA380 -IN", (_sheet, "D1", "2", _sheet, "U1", "2"), 5.5),
        (f"{_sheet} feedback trimmer at OPA380 -IN", (_sheet, "U1", "2", _sheet, "RVFB", "1"), 3.5),
        (f"{_sheet} feedback capacitor at OPA380 -IN", (_sheet, "U1", "2", _sheet, "C1", "1"), 2.5),
        (f"{_sheet} feedback trimmer at OPA380 OUT", (_sheet, "RVFB", "2", _sheet, "U1", "6"), 4.5),
        (f"{_sheet} feedback capacitor at OPA380 OUT", (_sheet, "C1", "2", _sheet, "U1", "6"), 2.5),
        (f"{_sheet} OPA380 supply decoupling", (_sheet, "C2", "1", _sheet, "U1", "7"), 2.5),
        (f"{_sheet} PD bias resistor at cathode", (_sheet, "RB", "2", _sheet, "D1", "1"), 4.5),
        (f"{_sheet} PD cathode bypass at cathode", (_sheet, "CB", "1", _sheet, "D1", "1"), 3.0),
        (f"{_sheet} VBIAS resistor at OPA380 +IN", (_sheet, "R1", "2", _sheet, "U1", "3"), 5.0),
        (f"{_sheet} VBIAS capacitor at OPA380 +IN", (_sheet, "C11", "1", _sheet, "U1", "3"), 4.0),
    ]

for _color in ["IR", "RED", "GREEN", "BLUE"]:
    _sheet = f"LASER_{_color}"
    CRITICAL_ROUTE_LINKS += [
        (f"{_sheet} TLV9001 OUT to gate resistor", (_sheet, "U11", "1", _sheet, "R31", "1"), 3.5),
        (f"{_sheet} gate resistor to AO3400A gate", (_sheet, "R31", "2", _sheet, "Q1", "1"), 2.5),
        (f"{_sheet} AO3400A source to sense resistor", (_sheet, "Q1", "2", _sheet, "R11", "1"), 2.2),
        (f"{_sheet} sense feedback to TLV9001 -IN", (_sheet, "R11", "1", _sheet, "U11", "4"), 6.0),
        (f"{_sheet} isolated ISENSE tap at sense resistor", (_sheet, "R12", "1", _sheet, "R11", "1"), 3.5),
        (f"{_sheet} TLV9001 supply decoupling", (_sheet, "C22", "1", _sheet, "U11", "5"), 2.5),
        (f"{_sheet} PWM input resistor at TLV9001 +IN", (_sheet, "R21", "2", _sheet, "U11", "3"), 2.5),
        (f"{_sheet} command limiter at TLV9001 +IN", (_sheet, "R22", "1", _sheet, "U11", "3"), 3.0),
        (f"{_sheet} command filter cap at TLV9001 +IN", (_sheet, "C21", "1", _sheet, "U11", "3"), 3.0),
        (f"{_sheet} compensation cap at TLV9001 -IN", (_sheet, "CC", "1", _sheet, "U11", "4"), 2.5),
        (f"{_sheet} compensation cap at TLV9001 OUT", (_sheet, "CC", "2", _sheet, "U11", "1"), 3.0),
    ]

_ina_in_plus_pins = {1: "3", 2: "5", 3: "10", 4: "12"}
_ina_out_pins = {1: "1", 2: "7", 3: "8", 4: "14"}
for _index, _color in enumerate(["IR", "RED", "GREEN"], 1):
    CRITICAL_ROUTE_LINKS += [
        (f"MPD_RAW{_index} direct LD monitor to sense resistor", (f"LASER_{_color}", "LD", "3", "POWER_IO", f"RMPD{_index}", "1"), 4.0),
        (f"MPD_RAW{_index} sense resistor to INA input", ("POWER_IO", f"RMPD{_index}", "1", "POWER_IO", "UMPD", _ina_in_plus_pins[_index]), 4.0),
        (f"MPD{_index} ADC resistor to filter capacitor", ("POWER_IO", f"RADC{_index}", "2", "POWER_IO", f"CMPD{_index}", "1"), 2.5),
    ]
CRITICAL_ROUTE_LINKS += [
    ("MPD_RAW4 spare sense resistor to INA input", ("POWER_IO", "RMPD4", "1", "POWER_IO", "UMPD", _ina_in_plus_pins[4]), 4.0),
    ("MPD_AMP4 INA output to ADC resistor", ("POWER_IO", "UMPD", _ina_out_pins[4], "POWER_IO", "RADC4", "1"), 4.0),
    ("MPD4 ADC resistor to filter capacitor", ("POWER_IO", "RADC4", "2", "POWER_IO", "CMPD4", "1"), 2.5),
]

MIN_ROUTED_CRITICAL_LINKS = 109
PREROUTE_ROUTE_DESCRIPTIONS = {
    "MPD_RAW2 direct LD monitor to sense resistor",
    "MPD_RAW3 direct LD monitor to sense resistor",
    "MPD_RAW4 spare sense resistor to INA input",
}
PREROUTE_USB_ROUTE_DESCRIPTIONS = {
    "USB UART D- connector to ESD",
    "USB UART D+ connector to ESD",
    "USB UART D- ESD to CP2102N",
    "USB UART D+ ESD to CP2102N",
    "Native USB D- connector to ESD",
    "Native USB D+ connector to ESD",
    "Native USB D- ESD to ESP32 GPIO19",
    "Native USB D+ ESD to ESP32 GPIO20",
}
EXTRA_SIGNAL_ROUTE_LINKS = [
    ("LASER_RED cathode sink to direct LD", ("LASER_RED", "Q1", "3", "LASER_RED", "LD", "1")),
    ("LASER_GREEN cathode sink to direct LD", ("LASER_GREEN", "Q1", "3", "LASER_GREEN", "LD", "1")),
    ("LASER_IR cathode sink to direct LD", ("LASER_IR", "Q1", "3", "LASER_IR", "LD", "1")),
    ("LASER_BLUE cathode sink to direct LD", ("LASER_BLUE", "Q1", "3", "LASER_BLUE", "LD", "3")),
    ("AD7606 CONVST from ESP32 to U14", ("MCU_ESP32-S3", "U9", "8", "POWER_IO", "UADC", "9")),
    ("TIA_IR trim upper node", ("TIA_IR", "RT", "2", "TIA_IR", "RV11", "1")),
    ("TIA_RED trim upper node", ("TIA_RED", "RT", "2", "TIA_RED", "RV11", "1")),
    ("TIA_GREEN trim upper node", ("TIA_GREEN", "RT", "2", "TIA_GREEN", "RV11", "1")),
    ("TIA_BLUE trim upper node", ("TIA_BLUE", "RT", "2", "TIA_BLUE", "RV11", "1")),
    ("TIA_IR VBIAS wiper route", ("TIA_IR", "RV11", "2", "TIA_IR", "R1", "1")),
    ("TIA_RED VBIAS wiper route", ("TIA_RED", "RV11", "2", "TIA_RED", "R1", "1")),
    ("TIA_GREEN VBIAS wiper route", ("TIA_GREEN", "RV11", "2", "TIA_GREEN", "R1", "1")),
    ("TIA_BLUE VBIAS wiper route", ("TIA_BLUE", "RV11", "2", "TIA_BLUE", "R1", "1")),
]
BOTTOM_SIGNAL_ROUTE_LINKS = [
    ("LASER_IR PWM command route", ("MCU_ESP32-S3", "U9", "18", "LASER_IR", "R21", "1")),
    ("LASER_RED PWM command route", ("MCU_ESP32-S3", "U9", "19", "LASER_RED", "R21", "1")),
    ("LASER_GREEN PWM command route", ("MCU_ESP32-S3", "U9", "20", "LASER_GREEN", "R21", "1")),
    ("LASER_BLUE PWM command route", ("MCU_ESP32-S3", "U9", "9", "LASER_BLUE", "R21", "1")),
    ("AD7606 CONVST bottom route", ("MCU_ESP32-S3", "U9", "8", "POWER_IO", "UADC", "9")),
    ("MPD1 telemetry route", ("POWER_IO", "RADC1", "1", "MCU_ESP32-S3", "U9", "38")),
    ("MPD2 telemetry route", ("POWER_IO", "RADC2", "1", "MCU_ESP32-S3", "U9", "15")),
    ("MPD3 telemetry route", ("POWER_IO", "RADC3", "1", "MCU_ESP32-S3", "U9", "12")),
    ("MPD4 telemetry route", ("POWER_IO", "RADC4", "1", "MCU_ESP32-S3", "U9", "17")),
    ("LASER_IR ISENSE telemetry route", ("LASER_IR", "R12", "2", "MCU_ESP32-S3", "U9", "4")),
    ("LASER_RED ISENSE telemetry route", ("LASER_RED", "R12", "2", "MCU_ESP32-S3", "U9", "5")),
    ("LASER_GREEN ISENSE telemetry route", ("LASER_GREEN", "R12", "2", "MCU_ESP32-S3", "U9", "6")),
    ("LASER_BLUE ISENSE telemetry route", ("LASER_BLUE", "R12", "2", "MCU_ESP32-S3", "U9", "7")),
    ("VOUT4 TIA output to AD7606", ("TIA_BLUE", "U1", "6", "POWER_IO", "UADC", "59")),
    ("VOUT1 TIA output to AD7606", ("TIA_IR", "U1", "6", "POWER_IO", "UADC", "49")),
    ("VOUT2 TIA output to AD7606", ("TIA_RED", "U1", "6", "POWER_IO", "UADC", "51")),
    ("VOUT3 TIA output to AD7606", ("TIA_GREEN", "U1", "6", "POWER_IO", "UADC", "57")),
    ("TIA_IR VBIAS wiper route", ("TIA_IR", "RV11", "2", "TIA_IR", "R1", "1")),
    ("TIA_RED VBIAS wiper route", ("TIA_RED", "RV11", "2", "TIA_RED", "R1", "1")),
    ("TIA_GREEN VBIAS wiper route", ("TIA_GREEN", "RV11", "2", "TIA_GREEN", "R1", "1")),
    ("TIA_BLUE VBIAS wiper route", ("TIA_BLUE", "RV11", "2", "TIA_BLUE", "R1", "1")),
]
INNER_SIGNAL_ROUTE_LINKS = [
    ("LASER_BLUE PWM inner route", ("MCU_ESP32-S3", "U9", "22", "LASER_BLUE", "R21", "1")),
    ("MPD4 telemetry inner route", ("POWER_IO", "RADC4", "1", "MCU_ESP32-S3", "U9", "17")),
    ("MPD3 telemetry inner route", ("POWER_IO", "RADC3", "1", "MCU_ESP32-S3", "U9", "12")),
    ("AD7606 CONVST inner route", ("MCU_ESP32-S3", "U9", "8", "POWER_IO", "UADC", "9")),
    ("LASER_IR PWM inner route", ("MCU_ESP32-S3", "U9", "9", "LASER_IR", "R21", "1")),
    ("LASER_RED PWM inner route", ("MCU_ESP32-S3", "U9", "31", "LASER_RED", "R21", "1")),
    ("LASER_IR ISENSE inner route", ("LASER_IR", "R12", "2", "MCU_ESP32-S3", "U9", "4")),
    ("LASER_RED ISENSE inner route", ("LASER_RED", "R12", "2", "MCU_ESP32-S3", "U9", "5")),
    ("LASER_GREEN ISENSE inner route", ("LASER_GREEN", "R12", "2", "MCU_ESP32-S3", "U9", "6")),
    ("LASER_BLUE ISENSE inner route", ("LASER_BLUE", "R12", "2", "MCU_ESP32-S3", "U9", "7")),
    ("LASER_GREEN PWM inner route", ("MCU_ESP32-S3", "U9", "21", "LASER_GREEN", "R21", "1")),
]
PREROUTE_INNER_ROUTE_DESCRIPTIONS = {
    "LASER_IR ISENSE inner route",
    "LASER_RED ISENSE inner route",
    "LASER_GREEN ISENSE inner route",
    "LASER_BLUE ISENSE inner route",
}
INNER_LAYER_ROUTE_OVERRIDES = {
    "LASER_IR ISENSE inner route": "B.Cu",
    "LASER_RED ISENSE inner route": "B.Cu",
    "LASER_GREEN ISENSE inner route": "B.Cu",
    "LASER_BLUE ISENSE inner route": "B.Cu",
    "MPD4 telemetry inner route": "In2.Cu",
}
BOTTOM_ROUTE_SKIP_DESCRIPTIONS = {
    "AD7606 CONVST bottom route",
    "LASER_IR PWM command route",
    "LASER_RED PWM command route",
    "LASER_IR ISENSE telemetry route",
    "LASER_RED ISENSE telemetry route",
    "LASER_GREEN ISENSE telemetry route",
    "LASER_BLUE ISENSE telemetry route",
    "LASER_GREEN PWM command route",
    "LASER_BLUE PWM command route",
    "MPD3 telemetry route",
    "MPD4 telemetry route",
}
VIA_IN_PAD_INNER_ROUTE_DESCRIPTIONS = {
    "LASER_IR ISENSE inner route",
    "LASER_RED ISENSE inner route",
    "LASER_GREEN ISENSE inner route",
    "LASER_BLUE ISENSE inner route",
    "MPD3 telemetry inner route",
    "LASER_IR PWM inner route",
    "LASER_RED PWM inner route",
    "LASER_GREEN PWM inner route",
    "LASER_BLUE PWM inner route",
}
VIA_IN_PAD_SIGNAL_FALLBACK_ROUTE_DESCRIPTIONS = set(VIA_IN_PAD_INNER_ROUTE_DESCRIPTIONS)
LAST_RESORT_GND_PLANE_ROUTE_DESCRIPTIONS: set[str] = set()
POWER_ROUTE_LINKS = [
    ("USB-UART VBUS connector to isolation diode", ("MCU_ESP32-S3", "J1", "1", "MCU_ESP32-S3", "D10", "2"), 0.50),
    ("USB-UART isolation diode to board VBUS", ("MCU_ESP32-S3", "D10", "1", "POWER_IO", "D10", "1"), 0.50),
    ("Native USB VBUS connector to isolation diode", ("MCU_ESP32-S3", "J2", "1", "MCU_ESP32-S3", "D13", "2"), 0.50),
    ("Native USB isolation diode to board VBUS", ("MCU_ESP32-S3", "D13", "1", "POWER_IO", "D10", "1"), 0.50),
    ("VIN24 barrel to 5V buck input", ("POWER_IO", "JDC", "1", "POWER_IO", "U5V", "3"), 0.60),
    ("VIN24 RJ45 to 5V buck input", ("POWER_IO", "JRJ45", "4", "POWER_IO", "U5V", "3"), 0.60),
    ("VIN24 barrel to laser buck input", ("POWER_IO", "JDC", "1", "POWER_IO", "ULASER", "3"), 0.60),
    ("VIN24 RJ45 to laser buck input", ("POWER_IO", "JRJ45", "4", "POWER_IO", "ULASER", "3"), 0.60),
    ("5V buck output to OR-ing diode", ("POWER_IO", "L5V", "2", "POWER_IO", "D11", "1"), 0.60),
    ("USB OR-ing diode cathode to +5V bulk", ("POWER_IO", "D10", "2", "POWER_IO", "C50", "1"), 0.60),
    ("5V buck OR-ing diode cathode to +5V bulk", ("POWER_IO", "D11", "2", "POWER_IO", "C50", "1"), 0.60),
    ("+5V bulk to AP2112 VIN", ("POWER_IO", "C50", "1", "POWER_IO", "U3V3", "1"), 0.50),
    ("+5V AP2112 VIN to EN", ("POWER_IO", "U3V3", "1", "POWER_IO", "U3V3", "3"), 0.25),
    ("+5V bulk to laser IR op amp rail", ("POWER_IO", "C50", "1", "LASER_IR", "C22", "1"), 0.25),
    ("+5V laser IR to RED op amp rail", ("LASER_IR", "C22", "1", "LASER_RED", "C22", "1"), 0.25),
    ("+5V laser RED to GREEN op amp rail", ("LASER_RED", "C22", "1", "LASER_GREEN", "C22", "1"), 0.25),
    ("+5V laser GREEN to BLUE op amp rail", ("LASER_GREEN", "C22", "1", "LASER_BLUE", "C22", "1"), 0.25),
    ("+5V bulk to TIA IR op amp rail", ("POWER_IO", "C50", "1", "TIA_IR", "U1", "7"), 0.25),
    ("+5V TIA IR to RED op amp rail", ("TIA_IR", "U1", "7", "TIA_RED", "U1", "7"), 0.25),
    ("+5V TIA RED to GREEN op amp rail", ("TIA_RED", "U1", "7", "TIA_GREEN", "U1", "7"), 0.25),
    ("+5V TIA GREEN to BLUE op amp rail", ("TIA_GREEN", "U1", "7", "TIA_BLUE", "U1", "7"), 0.25),
    ("+5V TIA IR rail to PD bias", ("TIA_IR", "U1", "7", "TIA_IR", "RB", "1"), 0.25),
    ("+5V TIA RED rail to PD bias", ("TIA_RED", "U1", "7", "TIA_RED", "RB", "1"), 0.25),
    ("+5V TIA GREEN rail to PD bias", ("TIA_GREEN", "U1", "7", "TIA_GREEN", "RB", "1"), 0.25),
    ("+5V TIA BLUE rail to PD bias", ("TIA_BLUE", "U1", "7", "TIA_BLUE", "RB", "1"), 0.25),
    ("+5V TIA IR rail to trim top", ("TIA_IR", "U1", "7", "TIA_IR", "RT", "1"), 0.25),
    ("+5V TIA RED rail to trim top", ("TIA_RED", "U1", "7", "TIA_RED", "RT", "1"), 0.25),
    ("+5V TIA GREEN rail to trim top", ("TIA_GREEN", "U1", "7", "TIA_GREEN", "RT", "1"), 0.25),
    ("+5V TIA BLUE rail to trim top", ("TIA_BLUE", "U1", "7", "TIA_BLUE", "RT", "1"), 0.25),
    ("AP2112 3V3 output to 100n cap", ("POWER_IO", "U3V3", "5", "POWER_IO", "C3V3OUT", "1"), 0.50),
    ("AP2112 3V3 output to bulk cap", ("POWER_IO", "U3V3", "5", "POWER_IO", "C3V3BULK", "1"), 0.50),
    ("3V3 AP2112 output decap to ESP32 local decap", ("POWER_IO", "C3V3OUT", "1", "MCU_ESP32-S3", "C43", "1"), 0.35),
    ("ESP32 3V3 pin to local decap", ("MCU_ESP32-S3", "U9", "2", "MCU_ESP32-S3", "C43", "1"), 0.25),
    ("ESP32 local 3V3 decap to EN pull-up", ("MCU_ESP32-S3", "C43", "1", "MCU_ESP32-S3", "R54", "1"), 0.25),
    ("3V3 bulk cap to BOOT pull-up", ("POWER_IO", "C3V3BULK", "1", "MCU_ESP32-S3", "R53", "1"), 0.25),
    ("Laser buck output to direct LD rail", ("POWER_IO", "LLASER", "2", "LASER_BLUE", "LD", "1"), 0.80),
    # LASER_V+ is a shared common-anode rail across all 4 direct laser
    # footprints (POWER_TREE.md: "LD1-LD4 common laser anode"). The buck only
    # seeds LASER_BLUE above; daisy-chain the other 3 in off the nearest
    # already-seeded channel (round-robin around the 2x2 channel layout:
    # BLUE top-left -> RED top-right -> GREEN bottom-right -> IR bottom-left)
    # so every LDx anode has an explicit routed path, not just a zone pour.
    ("LASER_V+ blue to red LD rail", ("LASER_BLUE", "LD", "1", "LASER_RED", "LD", "2"), 0.80),
    ("LASER_V+ red to green LD rail", ("LASER_RED", "LD", "2", "LASER_GREEN", "LD", "2"), 0.80),
    ("LASER_V+ green to IR LD rail", ("LASER_GREEN", "LD", "2", "LASER_IR", "LD", "2"), 0.80),
]
GND_LOCAL_ROUTE_LINKS = [
    ("ESP32 pin 1 ground to local decap ground", ("MCU_ESP32-S3", "U9", "1", "MCU_ESP32-S3", "C43", "2"), 0.20),
    ("MPD4 filter ground to sense-bias return", ("POWER_IO", "CMPD4", "2", "POWER_IO", "RMPD4", "2"), 0.20),
]
PREROUTE_POWER_ROUTE_DESCRIPTIONS = {
    "USB-UART VBUS connector to isolation diode",
    "USB-UART isolation diode to board VBUS",
    "Native USB VBUS connector to isolation diode",
    "Native USB isolation diode to board VBUS",
    "3V3 AP2112 output decap to ESP32 local decap",
    "ESP32 local 3V3 decap to EN pull-up",
    "VIN24 barrel to 5V buck input",
    "VIN24 RJ45 to 5V buck input",
    "VIN24 barrel to laser buck input",
    "VIN24 RJ45 to laser buck input",
    "Laser buck output to direct LD rail",
    "LASER_V+ blue to red LD rail",
    "LASER_V+ red to green LD rail",
    "LASER_V+ green to IR LD rail",
}
DEFERRED_POWER_ROUTE_DESCRIPTIONS: set[str] = set()
LOW_CURRENT_POWER_DOGBONE_ROUTE_DESCRIPTIONS = {
    "+5V bulk to laser IR op amp rail",
    "+5V laser IR to RED op amp rail",
    "+5V laser RED to GREEN op amp rail",
    "+5V laser GREEN to BLUE op amp rail",
}
POWER_LAYER_ROUTE_OVERRIDES = {
    "USB-UART VBUS connector to isolation diode": "B.Cu",
    "USB-UART isolation diode to board VBUS": "B.Cu",
    "Native USB VBUS connector to isolation diode": "B.Cu",
    "Native USB isolation diode to board VBUS": "B.Cu",
    "5V buck OR-ing diode cathode to +5V bulk": "In2.Cu",
    "+5V bulk to AP2112 VIN": "In2.Cu",
    "+5V bulk to laser IR op amp rail": "In2.Cu",
    "+5V laser IR to RED op amp rail": "In2.Cu",
    "+5V laser RED to GREEN op amp rail": "In2.Cu",
    "+5V laser GREEN to BLUE op amp rail": "In2.Cu",
    "+5V bulk to TIA IR op amp rail": "In2.Cu",
    "+5V TIA RED to GREEN op amp rail": "In2.Cu",
    "+5V TIA GREEN to BLUE op amp rail": "In2.Cu",
    "+5V TIA IR rail to PD bias": "In2.Cu",
    "+5V TIA RED rail to PD bias": "In2.Cu",
    "+5V TIA GREEN rail to PD bias": "In2.Cu",
    "+5V TIA BLUE rail to PD bias": "In2.Cu",
    "+5V TIA IR rail to trim top": "In2.Cu",
    "+5V TIA RED rail to trim top": "In2.Cu",
    "+5V TIA GREEN rail to trim top": "In2.Cu",
    "+5V TIA BLUE rail to trim top": "In2.Cu",
    "3V3 AP2112 output decap to ESP32 local decap": "In2.Cu",
    "ESP32 3V3 pin to local decap": "In2.Cu",
    "ESP32 local 3V3 decap to EN pull-up": "In2.Cu",
    "3V3 bulk cap to BOOT pull-up": "In2.Cu",
    "VIN24 barrel to 5V buck input": "In2.Cu",
    "VIN24 RJ45 to 5V buck input": "In2.Cu",
    "VIN24 barrel to laser buck input": "In2.Cu",
    "VIN24 RJ45 to laser buck input": "In2.Cu",
    "Laser buck output to direct LD rail": "In2.Cu",
    "LASER_V+ blue to red LD rail": "In2.Cu",
    "LASER_V+ red to green LD rail": "In2.Cu",
    "LASER_V+ green to IR LD rail": "In2.Cu",
}
VIA_SIZE = 0.60
VIA_DRILL = 0.30
GND_FANOUT_WIDTH = 0.20
GND_FANOUT_VIA_SIZE = 0.45
GND_FANOUT_VIA_DRILL = 0.20
HIGH_CURRENT_GND_FANOUT_WIDTH = 0.60
STRICT_ROUTE_CLEARANCE = os.environ.get("LC_STRICT_ROUTE_CLEARANCE") in {"1", "true", "TRUE", "yes", "YES"}
MAX_ROUTE_SEARCH_CELLS = int(os.environ.get("LC_MAX_ROUTE_SEARCH_CELLS", "20000"))
FORCED_DIRECT_ROUTE_DESCRIPTIONS = {
    "TIA_IR photodiode anode to OPA380 -IN",
    "TIA_IR PD bias resistor at cathode",
    "TIA_RED photodiode anode to OPA380 -IN",
    "TIA_RED PD bias resistor at cathode",
    "TIA_GREEN photodiode anode to OPA380 -IN",
    "TIA_GREEN PD bias resistor at cathode",
    "TIA_BLUE photodiode anode to OPA380 -IN",
    "TIA_BLUE PD bias resistor at cathode",
}
FORCED_ROUTE_SHAPES = {
}
LASER_CATHODE_INNER_LAYER_NETS = {
    # The direct laser footprints sit near the MPD feedback passives, so keep
    # the crowded current sinks off the GND reference layer. Most cathodes use
    # the otherwise-unpoured In2.Cu layer; LASER_N2 uses B.Cu so it does not
    # form a horizontal barrier across lower cathode escapes.
    "LASER_N1": "In2.Cu",
    "LASER_N2": "B.Cu",
    "LASER_N3": "In2.Cu",
    "LASER_N4": "In2.Cu",
}
EXTRA_LAYER_ROUTE_OVERRIDES = {}


def fp_ref(block: str) -> str:
    match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    if match:
        return match.group(1)
    match = re.search(r'\(fp_text reference "?([^"\s\)]+)"?', block)
    return match.group(1) if match else ""


def footprint_blocks(board_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in board_text.splitlines():
        if not in_block and line.lstrip().startswith("(footprint "):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def pad_blocks(footprint_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in footprint_text.splitlines():
        if not in_block and line.lstrip().startswith("(pad "):
            current = [line]
            depth = line.count("(") - line.count(")")
            in_block = True
            if depth == 0:
                blocks.append(line)
                in_block = False
            continue
        if in_block:
            current.append(line)
            depth += line.count("(") - line.count(")")
            if depth == 0:
                blocks.append("\n".join(current))
                in_block = False
    return blocks


def parse_pad_geometry_from_text(board_text: str) -> dict[str, dict[str, list[dict[str, float | str]]]]:
    geometry: dict[str, dict[str, list[dict[str, float | str]]]] = {}
    for block in footprint_blocks(board_text):
        ref = fp_ref(block)
        at_match = re.search(r'\n\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
        if not ref or not at_match:
            continue
        gx = float(at_match.group(1))
        gy = float(at_match.group(2))
        grot = float(at_match.group(3) or 0)
        theta = radians(grot)
        pads: dict[str, list[dict[str, float | str]]] = {}
        for pad in pad_blocks(block):
            pad_match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad)
            pad_at = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', pad)
            size_match = re.search(r'\(size\s+([-\d.]+)\s+([-\d.]+)\)', pad)
            net_match = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', pad)
            layers_match = re.search(r'\(layers\s+([^\)]*)\)', pad)
            if not pad_match or not pad_at or not size_match:
                continue
            pad_name = pad_match.group(1) if pad_match.group(1) is not None else pad_match.group(2)
            lx = float(pad_at.group(1))
            ly = float(pad_at.group(2))
            lrot = float(pad_at.group(3)) if pad_at.group(3) is not None else None
            pads.setdefault(pad_name, []).append(
                {
                    "x": gx + lx * cos(theta) + ly * sin(theta),
                    "y": gy - lx * sin(theta) + ly * cos(theta),
                    "w": float(size_match.group(1)),
                    "h": float(size_match.group(2)),
                    "rot": lrot if lrot is not None else grot,
                    "net": net_match.group(2) if net_match else "",
                    "layers": layers_match.group(1) if layers_match else "",
                }
            )
        geometry[ref] = pads
    return geometry


def _pad_on_layer(pad: dict[str, float | str], route_layer: str) -> bool:
    layers = str(pad.get("layers", ""))
    return "*.Cu" in layers or route_layer in layers


def route_width_for_link(description: str, net_name: str) -> float:
    if net_name.startswith("LASER_N") and "cathode sink to direct LD" in description:
        return 0.60
    if net_name.startswith("LASER_N"):
        return 0.60
    if "AO3400A source to sense resistor" in description:
        return 0.60
    if "USB" in description:
        return 0.25
    if "AP2112" in description or "supply decoupling" in description or "3V3 decap" in description:
        return 0.25
    if "PD bias resistor" in description:
        return 0.25
    if "sense feedback" in description or "isolated ISENSE" in description or "compensation" in description:
        return 0.20
    if net_name in {"+5V", "+3V3"}:
        return 0.25
    return 0.20


def route_order_for_link(description: str) -> int:
    if "TLV9001 OUT to gate resistor" in description:
        return 10
    if "gate resistor to AO3400A gate" in description:
        return 11
    if "sense feedback to TLV9001 -IN" in description:
        return 12
    if "compensation cap" in description:
        return 13
    if "TLV9001 supply decoupling" in description:
        return 40
    return 20


def _grid(value: float, step: float) -> int:
    return int(round(value / step))


def _coord(cell: tuple[int, int], step: float) -> tuple[float, float]:
    return (cell[0] * step, cell[1] * step)


def _point_in_pad(point: tuple[float, float], pad: dict[str, float | str], inflate: float) -> bool:
    theta = radians(-float(pad["rot"]))
    dx = point[0] - float(pad["x"])
    dy = point[1] - float(pad["y"])
    lx = dx * cos(theta) - dy * sin(theta)
    ly = dx * sin(theta) + dy * cos(theta)
    return abs(lx) <= float(pad["w"]) / 2 + inflate and abs(ly) <= float(pad["h"]) / 2 + inflate


def _pad_bbox(pad: dict[str, float | str], inflate: float) -> tuple[float, float, float, float]:
    theta = radians(float(pad["rot"]))
    c = abs(cos(theta))
    s = abs(sin(theta))
    hx = (float(pad["w"]) / 2 + inflate) * c + (float(pad["h"]) / 2 + inflate) * s
    hy = (float(pad["w"]) / 2 + inflate) * s + (float(pad["h"]) / 2 + inflate) * c
    return (float(pad["x"]) - hx, float(pad["y"]) - hy, float(pad["x"]) + hx, float(pad["y"]) + hy)


def _dist_point_segment(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    vx = b[0] - a[0]
    vy = b[1] - a[1]
    wx = point[0] - a[0]
    wy = point[1] - a[1]
    length2 = vx * vx + vy * vy
    if length2 == 0:
        return hypot(point[0] - a[0], point[1] - a[1])
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / length2))
    return hypot(point[0] - (a[0] + t * vx), point[1] - (a[1] + t * vy))


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _between(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    eps = 1e-9
    return (
        min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps
        and min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps
    )


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    eps = 1e-9
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if abs(o1) < eps and _between(a, b, c):
        return True
    if abs(o2) < eps and _between(a, b, d):
        return True
    if abs(o3) < eps and _between(c, d, a):
        return True
    if abs(o4) < eps and _between(c, d, b):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _dist_segment_segment(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> float:
    if _segments_intersect(a, b, c, d):
        return 0.0
    return min(
        _dist_point_segment(a, c, d),
        _dist_point_segment(b, c, d),
        _dist_point_segment(c, a, b),
        _dist_point_segment(d, a, b),
    )


def _clearance_for_net(net_name: str) -> float:
    """Return the KiCad net-class edge clearance used by the PCB checker.

    `gen_pcb` owns the net-class table, but importing it at module load would
    create a circular dependency. Import lazily when route generation is already
    running inside the fully-loaded generator.
    """
    if not STRICT_ROUTE_CLEARANCE:
        return 0.18
    try:
        import gen_pcb  # pylint: disable=import-outside-toplevel

        net_class = gen_pcb.classify_net(net_name)
        specs = getattr(gen_pcb, "NET_CLASS_SPECS", {})
        return float(specs.get(net_class, specs.get("Default", {"clearance": 0.18}))["clearance"])
    except Exception:
        return 0.18


def _required_edge_clearance(net_a: str, net_b: str) -> float:
    return max(_clearance_for_net(net_a), _clearance_for_net(net_b))


def _build_blocked_cells(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    route_net: str,
    width: float,
    bbox: tuple[float, float, float, float],
    step: float,
    route_layer: str,
) -> set[tuple[int, int]]:
    minx, miny, maxx, maxy = bbox
    blocked: set[tuple[int, int]] = set()
    default_pad_inflate = 0.18 + width / 2
    ix0 = _grid(minx, step)
    ix1 = _grid(maxx, step)
    iy0 = _grid(miny, step)
    iy1 = _grid(maxy, step)
    if not STRICT_ROUTE_CLEARANCE:
        inflate = 0.18 + width / 2
        for pad_map in pads.values():
            for pad_list in pad_map.values():
                for pad in pad_list:
                    if not _pad_on_layer(pad, route_layer):
                        continue
                    if pad["net"] == route_net:
                        continue
                    bx0, by0, bx1, by1 = _pad_bbox(pad, inflate)
                    if bx1 < minx or bx0 > maxx or by1 < miny or by0 > maxy:
                        continue
                    for ix in range(max(ix0, int(bx0 // step) - 1), min(ix1, int(bx1 // step) + 1) + 1):
                        for iy in range(max(iy0, int(by0 // step) - 1), min(iy1, int(by1 // step) + 1) + 1):
                            if _point_in_pad((ix * step, iy * step), pad, inflate):
                                blocked.add((ix, iy))
        for segment in existing_segments:
            segment_layer = str(segment.get("layer", "F.Cu"))
            if segment_layer not in {route_layer, "*.Cu"}:
                continue
            if segment["net"] == route_net:
                continue
            a = segment["a"]
            b = segment["b"]
            assert isinstance(a, tuple) and isinstance(b, tuple)
            clearance = 0.18 + (width + float(segment["w"])) / 2
            sx0 = min(a[0], b[0]) - clearance
            sx1 = max(a[0], b[0]) + clearance
            sy0 = min(a[1], b[1]) - clearance
            sy1 = max(a[1], b[1]) + clearance
            if sx1 < minx or sx0 > maxx or sy1 < miny or sy0 > maxy:
                continue
            for ix in range(max(ix0, int(sx0 // step) - 1), min(ix1, int(sx1 // step) + 1) + 1):
                for iy in range(max(iy0, int(sy0 // step) - 1), min(iy1, int(sy1 // step) + 1) + 1):
                    if _dist_point_segment((ix * step, iy * step), a, b) <= clearance:
                        blocked.add((ix, iy))
        return blocked
    for pad_map in pads.values():
        for pad_list in pad_map.values():
            for pad in pad_list:
                pad_net = str(pad.get("net", ""))
                if not pad_net:
                    continue
                if not _pad_on_layer(pad, route_layer):
                    continue
                if pad_net == route_net:
                    continue
                inflate = (
                    _required_edge_clearance(route_net, pad_net) + width / 2
                    if STRICT_ROUTE_CLEARANCE
                    else default_pad_inflate
                )
                bx0, by0, bx1, by1 = _pad_bbox(pad, inflate)
                if bx1 < minx or bx0 > maxx or by1 < miny or by0 > maxy:
                    continue
                for ix in range(max(ix0, int(bx0 // step) - 1), min(ix1, int(bx1 // step) + 1) + 1):
                    for iy in range(max(iy0, int(by0 // step) - 1), min(iy1, int(by1 // step) + 1) + 1):
                        if _point_in_pad((ix * step, iy * step), pad, inflate):
                            blocked.add((ix, iy))
    for segment in existing_segments:
        segment_layer = str(segment.get("layer", "F.Cu"))
        if segment_layer not in {route_layer, "*.Cu"}:
            continue
        if segment["net"] == route_net:
            continue
        a = segment["a"]
        b = segment["b"]
        assert isinstance(a, tuple) and isinstance(b, tuple)
        clearance = (
            _required_edge_clearance(route_net, str(segment["net"])) + (width + float(segment["w"])) / 2
            if STRICT_ROUTE_CLEARANCE
            else 0.18 + (width + float(segment["w"])) / 2
        )
        sx0 = min(a[0], b[0]) - clearance
        sx1 = max(a[0], b[0]) + clearance
        sy0 = min(a[1], b[1]) - clearance
        sy1 = max(a[1], b[1]) + clearance
        if sx1 < minx or sx0 > maxx or sy1 < miny or sy0 > maxy:
            continue
        for ix in range(max(ix0, int(sx0 // step) - 1), min(ix1, int(sx1 // step) + 1) + 1):
            for iy in range(max(iy0, int(sy0 // step) - 1), min(iy1, int(sy1 // step) + 1) + 1):
                if _dist_point_segment((ix * step, iy * step), a, b) <= clearance:
                    blocked.add((ix, iy))
    return blocked


def _simplify_route(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(points) <= 2:
        return points
    simplified = [points[0]]
    for index in range(1, len(points) - 1):
        a = simplified[-1]
        b = points[index]
        c = points[index + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-7:
            simplified.append(b)
    simplified.append(points[-1])
    return simplified


CHAMFER_FRACTION = 0.4
MAX_CHAMFER_MM = 1.0


def _chamfer_polyline(
    points: list[tuple[float, float]],
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    net_name: str,
    width: float,
    route_layer: str,
) -> list[tuple[float, float]]:
    """Cut hard 90-degree bends into two 45-degree legs where there is room.

    Grid-search routing only ever turns at right angles; this is a purely
    cosmetic pass that shaves a small chamfer off each square corner, and
    only keeps the chamfer when the two new legs stay clear of other copper.
    A corner that has no room (tight pad-to-pad escapes) is left square.
    """
    if len(points) < 3:
        return points
    result = [points[0]]
    index = 1
    while index < len(points) - 1:
        a = result[-1]
        b = points[index]
        c = points[index + 1]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        len1 = hypot(*v1)
        len2 = hypot(*v2)
        is_right_angle = (
            len1 > 1e-6
            and len2 > 1e-6
            and abs(v1[0] * v2[0] + v1[1] * v2[1]) < 1e-6
        )
        if is_right_angle:
            chamfer = min(len1, len2, width * 2.5, MAX_CHAMFER_MM) * CHAMFER_FRACTION
            if 0.05 < chamfer < len1 and chamfer < len2:
                p1 = (b[0] - v1[0] / len1 * chamfer, b[1] - v1[1] / len1 * chamfer)
                p2 = (b[0] + v2[0] / len2 * chamfer, b[1] + v2[1] / len2 * chamfer)
                if _route_shape_clear(pads, existing_segments, net_name, [a, p1, p2, c], width, route_layer):
                    result.append(p1)
                    result.append(p2)
                    index += 1
                    continue
        result.append(b)
        index += 1
    result.append(points[-1])
    return result


def _route_search_limits(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    step: float,
) -> tuple[int, int, int, int]:
    xs: list[float] = []
    ys: list[float] = []
    for pad_map in pads.values():
        for pad_list in pad_map.values():
            for pad in pad_list:
                xs.append(float(pad["x"]))
                ys.append(float(pad["y"]))
    for segment in existing_segments:
        a = segment.get("a")
        b = segment.get("b")
        if isinstance(a, tuple):
            xs.append(float(a[0]))
            ys.append(float(a[1]))
        if isinstance(b, tuple):
            xs.append(float(b[0]))
            ys.append(float(b[1]))
    if not xs or not ys:
        return (_grid(0.25, step), _grid(89.75, step), _grid(0.25, step), _grid(49.75, step))
    margin = 2.0
    return (
        _grid(min(xs) - margin, step),
        _grid(max(xs) + margin, step),
        _grid(min(ys) - margin, step),
        _grid(max(ys) + margin, step),
    )


def _route_one(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    net_name: str,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    width: float,
    step: float = 0.25,
    route_layer: str = "F.Cu",
) -> list[tuple[float, float]] | None:
    start = (_grid(start_point[0], step), _grid(start_point[1], step))
    goal = (_grid(end_point[0], step), _grid(end_point[1], step))
    limit_ix0, limit_ix1, limit_iy0, limit_iy1 = _route_search_limits(pads, existing_segments, step)
    for margin in [1.0, 2.0, 3.5, 5.0, 8.0, 12.0, 20.0, 35.0]:
        ix0 = max(limit_ix0, _grid(min(start_point[0], end_point[0]) - margin, step))
        ix1 = min(limit_ix1, _grid(max(start_point[0], end_point[0]) + margin, step))
        iy0 = max(limit_iy0, _grid(min(start_point[1], end_point[1]) - margin, step))
        iy1 = min(limit_iy1, _grid(max(start_point[1], end_point[1]) + margin, step))
        blocked = _build_blocked_cells(
            pads,
            existing_segments,
            net_name,
            width,
            (ix0 * step, iy0 * step, ix1 * step, iy1 * step),
            step,
            route_layer,
        )
        blocked.discard(start)
        blocked.discard(goal)
        heap: list[tuple[float, float, tuple[int, int], tuple[int, int] | None]] = [(0.0, 0.0, start, None)]
        came_from: dict[tuple[int, int], tuple[tuple[int, int], tuple[int, int]]] = {}
        cost: dict[tuple[int, int], float] = {start: 0.0}
        seen: set[tuple[int, int]] = set()
        found = False
        while heap:
            _, route_cost, cell, previous_direction = heappop(heap)
            if cell in seen:
                continue
            seen.add(cell)
            if STRICT_ROUTE_CLEARANCE and len(seen) > MAX_ROUTE_SEARCH_CELLS:
                break
            if cell == goal:
                found = True
                break
            x, y = cell
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor = (x + dx, y + dy)
                if neighbor[0] < ix0 or neighbor[0] > ix1 or neighbor[1] < iy0 or neighbor[1] > iy1 or neighbor in blocked:
                    continue
                direction = (dx, dy)
                turn_cost = 0.0 if previous_direction in (None, direction) else 0.05
                # Soft per-layer axis preference: F.Cu favors horizontal runs,
                # B.Cu favors vertical runs, so a net that must pick a layer
                # for a leg tends to keep horizontal/vertical traffic apart.
                # Small relative to turn_cost/step cost -- a tie-breaker, not
                # a hard rule, so it never blocks the router from finding a
                # path when the preferred axis is unavailable.
                if route_layer == "F.Cu":
                    axis_bias = 0.0 if dy == 0 else 0.03
                elif route_layer == "B.Cu":
                    axis_bias = 0.0 if dx == 0 else 0.03
                else:
                    axis_bias = 0.0
                new_cost = route_cost + 1.0 + turn_cost + axis_bias
                if new_cost < cost.get(neighbor, 1e18):
                    cost[neighbor] = new_cost
                    came_from[neighbor] = (cell, direction)
                    heuristic = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                    heappush(heap, (new_cost + heuristic, new_cost, neighbor, direction))
        if not found:
            continue
        cells: list[tuple[int, int]] = []
        cell = goal
        while cell != start:
            cells.append(cell)
            cell = came_from[cell][0]
        cells.append(start)
        cells.reverse()
        simplified = _simplify_route([start_point] + [_coord(cell, step) for cell in cells[1:-1]] + [end_point])
        return _chamfer_polyline(simplified, pads, existing_segments, net_name, width, route_layer)
    return None


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _forced_route_points(
    description: str,
    start: tuple[float, float],
    end: tuple[float, float],
) -> list[tuple[float, float]] | None:
    if description in FORCED_DIRECT_ROUTE_DESCRIPTIONS:
        return [start, end]
    shape = FORCED_ROUTE_SHAPES.get(description)
    if shape == "vertical_then_horizontal":
        return [start, (start[0], end[1]), end]
    if shape == "horizontal_then_vertical":
        return [start, (end[0], start[1]), end]
    return None


def _via_clear(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    net_name: str,
) -> bool:
    return _via_clear_sized(pads, existing_segments, point, net_name, VIA_SIZE)


def _via_clear_sized(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    net_name: str,
    via_size: float,
) -> bool:
    if (
        point[0] < BOARD_X0_MM + BOARD_EDGE_KEEPOUT_MM
        or point[0] > BOARD_X1_MM - BOARD_EDGE_KEEPOUT_MM
        or point[1] < BOARD_Y0_MM + BOARD_EDGE_KEEPOUT_MM
        or point[1] > BOARD_Y1_MM - BOARD_EDGE_KEEPOUT_MM
    ):
        return False
    if not STRICT_ROUTE_CLEARANCE:
        pad_inflate = 0.18 + via_size / 2
        same_net_pad_inflate = SAME_NET_VIA_PAD_CLEARANCE_MM + via_size / 2
        for pad_map in pads.values():
            for pad_list in pad_map.values():
                for pad in pad_list:
                    inflate = same_net_pad_inflate if pad["net"] == net_name else pad_inflate
                    if _point_in_pad(point, pad, inflate):
                        return False
        for segment in existing_segments:
            if segment["net"] == net_name:
                continue
            a = segment["a"]
            b = segment["b"]
            assert isinstance(a, tuple) and isinstance(b, tuple)
            clearance = 0.18 + (via_size + float(segment["w"])) / 2
            if _dist_point_segment(point, a, b) <= clearance:
                return False
        return True
    default_pad_inflate = 0.18 + via_size / 2
    same_net_pad_inflate = SAME_NET_VIA_PAD_CLEARANCE_MM + via_size / 2
    for pad_map in pads.values():
        for pad_list in pad_map.values():
            for pad in pad_list:
                pad_net = str(pad.get("net", ""))
                if not pad_net:
                    continue
                if pad_net == net_name:
                    if _point_in_pad(point, pad, same_net_pad_inflate):
                        return False
                    continue
                pad_inflate = (
                    _required_edge_clearance(net_name, pad_net) + via_size / 2
                    if STRICT_ROUTE_CLEARANCE
                    else default_pad_inflate
                )
                if _point_in_pad(point, pad, pad_inflate):
                    return False
    for segment in existing_segments:
        if segment["net"] == net_name:
            continue
        a = segment["a"]
        b = segment["b"]
        assert isinstance(a, tuple) and isinstance(b, tuple)
        clearance = (
            _required_edge_clearance(net_name, str(segment["net"])) + (via_size + float(segment["w"])) / 2
            if STRICT_ROUTE_CLEARANCE
            else 0.18 + (via_size + float(segment["w"])) / 2
        )
        if _dist_point_segment(point, a, b) <= clearance:
            return False
    return True


def _via_candidates(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    toward: tuple[float, float],
    net_name: str,
) -> list[tuple[float, float]]:
    return _via_candidates_sized(pads, existing_segments, point, toward, net_name, VIA_SIZE)


def _via_candidates_sized(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    toward: tuple[float, float],
    net_name: str,
    via_size: float,
) -> list[tuple[float, float]]:
    offsets: list[tuple[float, float]] = []
    distances = (
        [0.75, 0.90, 1.05, 1.20, 1.50, 1.80, 2.50, 3.20, 4.20, 5.50]
        if via_size < VIA_SIZE
        else [1.20, 1.80, 2.50, 3.20, 4.20, 5.50]
    )
    for distance in distances:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
            norm = hypot(dx, dy)
            offsets.append((dx * distance / norm, dy * distance / norm))
    candidates = [
        (round(point[0] + dx, 4), round(point[1] + dy, 4))
        for dx, dy in offsets
    ]
    unique = sorted(set(candidates), key=lambda p: hypot(p[0] - toward[0], p[1] - toward[1]))
    return [
        candidate
        for candidate in unique
        if _via_clear_sized(pads, existing_segments, candidate, net_name, via_size)
    ]


def _emit_segment(
    emitted: list[str],
    existing_segments: list[dict[str, object]],
    a: tuple[float, float],
    b: tuple[float, float],
    width: float,
    layer: str,
    net_code: int,
    net_name: str,
    uuid_func,
) -> None:
    if a == b:
        return
    emitted.append(
        f'  (segment (start {_fmt(a[0])} {_fmt(a[1])}) (end {_fmt(b[0])} {_fmt(b[1])}) '
        f'(width {_fmt(width)}) (layer "{layer}") (net {net_code}) (tstamp {uuid_func()}))'
    )
    existing_segments.append({"net": net_name, "a": a, "b": b, "w": width, "layer": layer})


def _emit_via(
    emitted: list[str],
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    net_code: int,
    net_name: str,
    uuid_func,
) -> None:
    if _via_already_emitted(existing_segments, point, net_name):
        return
    emitted.append(
        f'  (via (at {_fmt(point[0])} {_fmt(point[1])}) (size {_fmt(VIA_SIZE)}) '
        f'(drill {_fmt(VIA_DRILL)}) (layers "F.Cu" "B.Cu") (net {net_code}) (tstamp {uuid_func()}))'
    )
    existing_segments.append({"net": net_name, "a": point, "b": point, "w": VIA_SIZE, "layer": "*.Cu"})


def _emit_sized_via(
    emitted: list[str],
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    net_code: int,
    net_name: str,
    via_size: float,
    via_drill: float,
    uuid_func,
) -> None:
    if _via_already_emitted(existing_segments, point, net_name):
        return
    emitted.append(
        f'  (via (at {_fmt(point[0])} {_fmt(point[1])}) (size {_fmt(via_size)}) '
        f'(drill {_fmt(via_drill)}) (layers "F.Cu" "B.Cu") (net {net_code}) (tstamp {uuid_func()}))'
    )
    existing_segments.append({"net": net_name, "a": point, "b": point, "w": via_size, "layer": "*.Cu"})


def _via_already_emitted(
    existing_segments: list[dict[str, object]],
    point: tuple[float, float],
    net_name: str,
) -> bool:
    key = (round(point[0], 4), round(point[1], 4))
    for segment in existing_segments:
        if segment.get("layer") != "*.Cu" or segment.get("net") != net_name:
            continue
        a = segment.get("a")
        b = segment.get("b")
        if not isinstance(a, tuple) or not isinstance(b, tuple) or a != b:
            continue
        if (round(a[0], 4), round(a[1], 4)) == key:
            return True
    return False


def emit_ground_plane_fanout_segments(
    footprint_blocks_with_nets: list[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    pad_nets_by_ref: dict[str, dict[str, tuple[int, str]]],
    existing_segments: list[dict[str, object]],
    uuid_func,
) -> tuple[list[str], list[str]]:
    """Fan F.Cu-only GND pads into the In1.Cu reference plane with short vias.

    The generated PCB has an In1.Cu GND zone, but F.Cu-only SMD pads do not
    magically touch that inner plane. Emit short, auditable fanout traces and
    vias so the zone has an actual return-current entry at every local ground.
    """
    board_text = "\n".join(footprint_blocks_with_nets)
    pads = parse_pad_geometry_from_text(board_text)
    emitted: list[str] = []
    fanned_out: list[str] = []

    high_current_ground_pads: set[tuple[str, str]] = set()
    for color in ["IR", "RED", "GREEN", "BLUE"]:
        sheet = f"LASER_{color}"
        board_ref = board_ref_by_comp.get((sheet, ref_for(sheet, "R11")))
        if board_ref:
            high_current_ground_pads.add((board_ref, "2"))
    forced_gnd_fanout_offsets: dict[tuple[str, str], tuple[float, float]] = {}
    for sheet, local_ref in [
        ("LASER_IR", "C17"),
        ("LASER_RED", "C20"),
    ]:
        board_ref = board_ref_by_comp.get((sheet, ref_for(sheet, local_ref)))
        if board_ref:
            forced_gnd_fanout_offsets[(board_ref, "2")] = (1.0, 0.25)

    route_items: list[tuple[int, float, str, str, dict[str, float | str]]] = []
    seen_points: set[tuple[str, str, float, float]] = set()
    for ref, pad_map in sorted(pads.items()):
        for pin, pad_list in sorted(pad_map.items()):
            for pad in pad_list:
                if pad.get("net") != "GND":
                    continue
                if not _pad_on_layer(pad, "F.Cu") or _pad_on_layer(pad, "In1.Cu"):
                    continue
                point_key = (ref, pin, round(float(pad["x"]), 4), round(float(pad["y"]), 4))
                if point_key in seen_points:
                    continue
                seen_points.add(point_key)
                high_current = (ref, pin) in high_current_ground_pads
                # Route high-current laser sense returns first so they keep the
                # cleanest local fanouts into the reference plane.
                priority = 0 if high_current else 10
                route_items.append((priority, float(pad["y"]), ref, pin, pad))

    for priority, _, ref, pin, pad in sorted(route_items, key=lambda item: (item[0], item[1], item[2], item[3])):
        start = (round(float(pad["x"]), 4), round(float(pad["y"]), 4))
        high_current = priority == 0
        width = HIGH_CURRENT_GND_FANOUT_WIDTH if high_current else GND_FANOUT_WIDTH
        via_size = VIA_SIZE if high_current else GND_FANOUT_VIA_SIZE
        via_drill = VIA_DRILL if high_current else GND_FANOUT_VIA_DRILL
        toward = (start[0] + 1.0, start[1])
        committed: tuple[tuple[float, float], list[tuple[float, float]]] | None = None
        forced_offset = forced_gnd_fanout_offsets.get((ref, pin))
        if forced_offset is not None:
            forced_via = (round(start[0] + forced_offset[0], 4), round(start[1] + forced_offset[1], 4))
            forced_escape = [start, forced_via]
            if _via_clear_sized(pads, existing_segments, forced_via, "GND", via_size) and _route_shape_clear(
                pads,
                existing_segments,
                "GND",
                forced_escape,
                width,
                "F.Cu",
            ):
                committed = (forced_via, forced_escape)
        for via in _via_candidates_sized(pads, existing_segments, start, toward, "GND", via_size)[:12]:
            if committed is not None:
                break
            escape = _route_one(
                pads,
                existing_segments,
                "GND",
                start,
                via,
                width,
                step=0.25,
                route_layer="F.Cu",
            )
            if not escape:
                continue
            if not _route_shape_clear(pads, existing_segments, "GND", escape, width, "F.Cu"):
                continue
            committed = (via, escape)
            break
        if committed is None:
            continue
        via, escape = committed
        net_code, net_name = pad_nets_by_ref[ref][pin]
        for a, b in zip(escape, escape[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", net_code, net_name, uuid_func)
        _emit_sized_via(emitted, existing_segments, via, net_code, net_name, via_size, via_drill, uuid_func)
        fanned_out.append(f"{ref}.{pin}")

    for description, args, width in GND_LOCAL_ROUTE_LINKS:
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != "GND" or net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (round(float(start_pad["x"]), 4), round(float(start_pad["y"]), 4))
        end = (round(float(end_pad["x"]), 4), round(float(end_pad["y"]), 4))
        points = _route_one(pads, existing_segments, net_a, start, end, width, route_layer="F.Cu")
        if not points or not _route_shape_clear(pads, existing_segments, net_a, points, width, "F.Cu"):
            continue
        for a, b in zip(points, points[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
        fanned_out.append(description)

    return emitted, fanned_out


def _route_front_pad_to_layer(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    net_name: str,
    start: tuple[float, float],
    end: tuple[float, float],
    width: float,
    route_layer: str,
) -> tuple[tuple[float, float], list[tuple[float, float]], list[tuple[float, float]]] | None:
    candidates: list[
        tuple[
            float,
            tuple[float, float],
            list[tuple[float, float]],
            list[tuple[float, float]],
        ]
    ] = []
    for start_via in _via_candidates(pads, existing_segments, start, end, net_name)[:20]:
        start_escape = _route_one(pads, existing_segments, net_name, start, start_via, width, route_layer="F.Cu")
        if not start_escape or not _route_shape_clear(pads, existing_segments, net_name, start_escape, width, "F.Cu"):
            continue
        temp_after_start = existing_segments + [
            {"net": net_name, "a": a, "b": b, "w": width, "layer": "F.Cu"}
            for a, b in zip(start_escape, start_escape[1:])
            if a != b
        ] + [{"net": net_name, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
        layer_route = _route_one(
            pads,
            temp_after_start,
            net_name,
            start_via,
            end,
            width,
            step=0.25,
            route_layer=route_layer,
        )
        if not layer_route or not _route_shape_clear(
            pads,
            temp_after_start,
            net_name,
            layer_route,
            width,
            route_layer,
        ):
            continue
        length = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(start_escape, start_escape[1:]))
        length += sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(layer_route, layer_route[1:]))
        candidates.append((length, start_via, start_escape, layer_route))
    if not candidates:
        return None
    _, start_via, start_escape, layer_route = min(candidates, key=lambda item: item[0])
    return start_via, start_escape, layer_route


def _route_front_pad_to_front_pad_layer(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    net_name: str,
    start: tuple[float, float],
    end: tuple[float, float],
    width: float,
    route_layer: str,
    via_size: float = VIA_SIZE,
) -> tuple[
    tuple[float, float],
    tuple[float, float],
    list[tuple[float, float]],
    list[tuple[float, float]],
    list[tuple[float, float]],
] | None:
    candidates: list[
        tuple[
            float,
            tuple[float, float],
            tuple[float, float],
            list[tuple[float, float]],
            list[tuple[float, float]],
            list[tuple[float, float]],
        ]
    ] = []
    for start_via in _via_candidates_sized(pads, existing_segments, start, end, net_name, via_size)[:20]:
        start_escape = _route_one(pads, existing_segments, net_name, start, start_via, width, route_layer="F.Cu")
        if not start_escape or not _route_shape_clear(pads, existing_segments, net_name, start_escape, width, "F.Cu"):
            continue
        temp_after_start = existing_segments + [
            {"net": net_name, "a": a, "b": b, "w": width, "layer": "F.Cu"}
            for a, b in zip(start_escape, start_escape[1:])
            if a != b
        ] + [{"net": net_name, "a": start_via, "b": start_via, "w": via_size, "layer": "*.Cu"}]
        for end_via in _via_candidates_sized(pads, temp_after_start, end, start, net_name, via_size)[:20]:
            layer_route = _route_one(
                pads,
                temp_after_start,
                net_name,
                start_via,
                end_via,
                width,
                step=0.50,
                route_layer=route_layer,
            )
            if not layer_route or not _route_shape_clear(
                pads,
                temp_after_start,
                net_name,
                layer_route,
                width,
                route_layer,
            ):
                continue
            temp_after_layer = temp_after_start + [
                {"net": net_name, "a": a, "b": b, "w": width, "layer": route_layer}
                for a, b in zip(layer_route, layer_route[1:])
                if a != b
            ] + [{"net": net_name, "a": end_via, "b": end_via, "w": via_size, "layer": "*.Cu"}]
            end_escape = _route_one(pads, temp_after_layer, net_name, end_via, end, width, route_layer="F.Cu")
            if not end_escape or not _route_shape_clear(
                pads,
                temp_after_layer,
                net_name,
                end_escape,
                width,
                "F.Cu",
            ):
                continue
            length = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(start_escape, start_escape[1:]))
            length += sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(layer_route, layer_route[1:]))
            length += sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(end_escape, end_escape[1:]))
            candidates.append((length, start_via, end_via, start_escape, layer_route, end_escape))
    if not candidates:
        return None
    _, start_via, end_via, start_escape, layer_route, end_escape = min(candidates, key=lambda item: item[0])
    return start_via, end_via, start_escape, layer_route, end_escape


def _forced_power_front_pad_to_front_pad_layer(
    description: str,
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[
    tuple[float, float],
    tuple[float, float],
    list[tuple[float, float]],
    list[tuple[float, float]],
    list[tuple[float, float]],
] | None:
    if description == "USB-UART VBUS connector to isolation diode":
        start_via = (round(start[0], 4), round(start[1] + 1.2, 4))
        end_via = (round(end[0] + 1.2, 4), round(end[1], 4))
        corridor_y = round(start_via[1], 4)
        return (
            start_via,
            end_via,
            [start, start_via],
            [start_via, (round(start_via[0] + 0.6, 4), corridor_y), (end_via[0], corridor_y), end_via],
            [end_via, end],
        )
    # "USB-UART isolation diode to board VBUS" and "Laser buck output to
    # direct LD rail" used to have hand-tuned forced shapes here with
    # absolute corridor_y values (3.5 and 18.0) from the board's original
    # 90x50mm-at-origin layout. On the current 173x61mm board (y=80..141)
    # those corridors sit entirely off the board -- and because a route
    # only needs to clear *other copper/pads*, not the board outline, the
    # clearance check happily accepted a path routed through empty space
    # off the board edge instead of failing. That produced literally
    # unmanufacturable copper that passed generation silently; it only
    # showed up as `copper_board_bounds_failures` in the release checker.
    # Removed rather than re-tuned: both fall through to the general
    # via-search layer-hop path below, which is board-bounds safe by
    # construction (see BOARD_EDGE_KEEPOUT_MM in _via_clear_sized).
    return None


def _forced_extra_front_pad_to_layer(
    description: str,
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[tuple[float, float], list[tuple[float, float]], list[tuple[float, float]]] | None:
    if description == "LASER_IR cathode sink to direct LD":
        start_via = (50.4375, round(start[1], 4))
        return (
            start_via,
            [
                start,
                (45.25, round(start[1], 4)),
                (50.25, round(start[1], 4)),
                start_via,
            ],
            [
                start_via,
                (50.75, 16.0),
                (50.75, 14.5),
                (83.5, 14.5),
                (83.5, 12.5),
                (89.0, 12.5),
                (89.0, 26.0),
                end,
            ],
        )
    if description == "LASER_RED cathode sink to direct LD":
        start_via = (49.1375, round(start[1], 4))
        return (
            start_via,
            [
                start,
                (45.25, round(start[1], 4)),
                (49.0, round(start[1], 4)),
                start_via,
            ],
            [
                start_via,
                (49.25, 24.25),
                (49.25, 24.5),
                (82.5, 24.5),
                (82.5, 25.75),
                end,
            ],
        )
    if description == "LASER_GREEN cathode sink to direct LD":
        start_via = (44.0, round(start[1], 4))
        return (
            start_via,
            [
                start,
                start_via,
            ],
            [
                start_via,
                (44.0, 29.0),
                (77.34, 29.0),
                end,
            ],
        )
    if description == "LASER_BLUE cathode sink to direct LD":
        start_via = (42.75, round(start[1], 4))
        return (
            start_via,
            [
                start,
                start_via,
            ],
            [
                start_via,
                (42.75, 27.5),
                (72.26, 27.5),
                end,
            ],
        )
    return None


def _route_shape_clear(
    pads: dict[str, dict[str, list[dict[str, float | str]]]],
    existing_segments: list[dict[str, object]],
    net_name: str,
    points: list[tuple[float, float]],
    width: float,
    route_layer: str,
) -> bool:
    default_inflate = 0.18 + width / 2
    if not STRICT_ROUTE_CLEARANCE:
        inflate = default_inflate
        for a, b in zip(points, points[1:]):
            length = hypot(b[0] - a[0], b[1] - a[1])
            steps = max(2, int(length / 0.10) + 1)
            seg_x0 = min(a[0], b[0]) - inflate
            seg_x1 = max(a[0], b[0]) + inflate
            seg_y0 = min(a[1], b[1]) - inflate
            seg_y1 = max(a[1], b[1]) + inflate
            for pad_map in pads.values():
                for pad_list in pad_map.values():
                    for pad in pad_list:
                        if not _pad_on_layer(pad, route_layer):
                            continue
                        if pad["net"] == net_name:
                            continue
                        px0, py0, px1, py1 = _pad_bbox(pad, inflate)
                        if px1 < seg_x0 or px0 > seg_x1 or py1 < seg_y0 or py0 > seg_y1:
                            continue
                        for index in range(steps + 1):
                            t = index / steps
                            point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                            if _point_in_pad(point, pad, inflate):
                                return False
            for segment in existing_segments:
                segment_layer = str(segment.get("layer", "F.Cu"))
                if segment_layer not in {route_layer, "*.Cu"}:
                    continue
                if segment["net"] == net_name:
                    continue
                sa = segment["a"]
                sb = segment["b"]
                assert isinstance(sa, tuple) and isinstance(sb, tuple)
                clearance = 0.18 + (width + float(segment["w"])) / 2
                sx0 = min(sa[0], sb[0]) - clearance
                sx1 = max(sa[0], sb[0]) + clearance
                sy0 = min(sa[1], sb[1]) - clearance
                sy1 = max(sa[1], sb[1]) + clearance
                if sx1 < min(a[0], b[0]) - clearance or sx0 > max(a[0], b[0]) + clearance:
                    continue
                if sy1 < min(a[1], b[1]) - clearance or sy0 > max(a[1], b[1]) + clearance:
                    continue
                if _dist_segment_segment(a, b, sa, sb) <= clearance:
                    return False
        return True
    for a, b in zip(points, points[1:]):
        length = hypot(b[0] - a[0], b[1] - a[1])
        steps = max(2, int(length / 0.10) + 1)
        for pad_map in pads.values():
            for pad_list in pad_map.values():
                for pad in pad_list:
                    pad_net = str(pad.get("net", ""))
                    if not pad_net:
                        continue
                    if not _pad_on_layer(pad, route_layer):
                        continue
                    if pad_net == net_name:
                        continue
                    inflate = (
                        _required_edge_clearance(net_name, pad_net) + width / 2
                        if STRICT_ROUTE_CLEARANCE
                        else default_inflate
                    )
                    seg_x0 = min(a[0], b[0]) - inflate
                    seg_x1 = max(a[0], b[0]) + inflate
                    seg_y0 = min(a[1], b[1]) - inflate
                    seg_y1 = max(a[1], b[1]) + inflate
                    px0, py0, px1, py1 = _pad_bbox(pad, inflate)
                    if px1 < seg_x0 or px0 > seg_x1 or py1 < seg_y0 or py0 > seg_y1:
                        continue
                    for index in range(steps + 1):
                        t = index / steps
                        point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                        if _point_in_pad(point, pad, inflate):
                            return False
        for segment in existing_segments:
            segment_layer = str(segment.get("layer", "F.Cu"))
            if segment_layer not in {route_layer, "*.Cu"}:
                continue
            if segment["net"] == net_name:
                continue
            sa = segment["a"]
            sb = segment["b"]
            assert isinstance(sa, tuple) and isinstance(sb, tuple)
            clearance = (
                _required_edge_clearance(net_name, str(segment["net"])) + (width + float(segment["w"])) / 2
                if STRICT_ROUTE_CLEARANCE
                else 0.18 + (width + float(segment["w"])) / 2
            )
            sx0 = min(sa[0], sb[0]) - clearance
            sx1 = max(sa[0], sb[0]) + clearance
            sy0 = min(sa[1], sb[1]) - clearance
            sy1 = max(sa[1], sb[1]) + clearance
            if sx1 < min(a[0], b[0]) - clearance or sx0 > max(a[0], b[0]) + clearance:
                continue
            if sy1 < min(a[1], b[1]) - clearance or sy0 > max(a[1], b[1]) + clearance:
                continue
            if _dist_segment_segment(a, b, sa, sb) <= clearance:
                return False
    return True


def _corridor_positions(lo: float, hi: float, step: float) -> list[float]:
    """Evenly spaced candidate corridor lanes across the real board extent.

    Was previously a hardcoded absolute list (x in 8..87, y in 3..47) tuned
    for the board's original 90x50mm-at-origin layout. On the current
    173x61mm board (x=31..204, y=80..141) those literal values either fall
    off the board entirely or land on top of components that didn't exist
    at those coordinates on the old floorplan -- rebuilding a long cross-
    board route (PWM/VOUT/ISENSE/ADC-bus links) then has only the 3 direct/
    L-shaped fallback candidates to try, which routinely can't clear ~170
    other footprints over 100+mm. Generating lanes from the board's own
    bounds keeps this correct regardless of future resizes/re-placements.
    """
    if hi <= lo:
        return []
    count = max(1, int((hi - lo) / step))
    return [lo + (i + 0.5) * (hi - lo) / count for i in range(count)]


def _bottom_route_shapes(start: tuple[float, float], end: tuple[float, float]) -> list[list[tuple[float, float]]]:
    shapes = [
        [start, end],
        [start, (end[0], start[1]), end],
        [start, (start[0], end[1]), end],
    ]
    margin = 8.0
    for x in _corridor_positions(BOARD_X0_MM, BOARD_X1_MM, 12.0):
        if min(start[0], end[0]) - margin <= x <= max(start[0], end[0]) + margin:
            shapes.append([start, (x, start[1]), (x, end[1]), end])
    for y in _corridor_positions(BOARD_Y0_MM, BOARD_Y1_MM, 4.0):
        if min(start[1], end[1]) - margin <= y <= max(start[1], end[1]) + margin:
            shapes.append([start, (start[0], y), (end[0], y), end])
    return shapes


def emit_critical_route_segments(
    footprint_blocks_with_nets: list[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    pad_nets_by_ref: dict[str, dict[str, tuple[int, str]]],
    uuid_func,
    initial_existing_segments: list[dict[str, object]] | None = None,
    pre_routed_descriptions: list[str] | None = None,
    only_descriptions: set[str] | None = None,
    skip_descriptions: set[str] | None = None,
) -> tuple[list[str], list[str], list[dict[str, object]]]:
    board_text = "\n".join(footprint_blocks_with_nets)
    pads = parse_pad_geometry_from_text(board_text)
    existing_segments = [] if initial_existing_segments is None else initial_existing_segments
    emitted: list[str] = []
    routed_descriptions: list[str] = list(pre_routed_descriptions or [])
    route_items: list[tuple[float, str, str, tuple[float, float], tuple[float, float], float, int]] = []
    for description, args, _ in CRITICAL_ROUTE_LINKS:
        if only_descriptions is not None and description not in only_descriptions:
            continue
        if skip_descriptions is not None and description in skip_descriptions:
            continue
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        end = (float(end_pad["x"]), float(end_pad["y"]))
        width = route_width_for_link(description, net_a)
        forced_points = _forced_route_points(description, start, end)
        if forced_points is not None:
            forced_points = _chamfer_polyline(forced_points, pads, existing_segments, net_a, width, "F.Cu")
            for a, b in zip(forced_points, forced_points[1:]):
                if a == b:
                    continue
                emitted.append(
                    f'  (segment (start {_fmt(a[0])} {_fmt(a[1])}) (end {_fmt(b[0])} {_fmt(b[1])}) '
                    f'(width {_fmt(width)}) (layer "F.Cu") (net {code_a}) (tstamp {uuid_func()}))'
                )
                existing_segments.append({"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"})
            routed_descriptions.append(description)
            continue
        route_items.append((route_order_for_link(description), hypot(start[0] - end[0], start[1] - end[1]), description, net_a, start, end, width, code_a))

    for _, _, description, net_name, start, end, width, net_code in sorted(route_items):
        points = _route_one(pads, existing_segments, net_name, start, end, width)
        if points is None:
            continue
        if not _route_shape_clear(pads, existing_segments, net_name, points, width, "F.Cu"):
            continue
        routed_descriptions.append(description)
        for a, b in zip(points, points[1:]):
            if a == b:
                continue
            emitted.append(
                f'  (segment (start {_fmt(a[0])} {_fmt(a[1])}) (end {_fmt(b[0])} {_fmt(b[1])}) '
                f'(width {_fmt(width)}) (layer "F.Cu") (net {net_code}) (tstamp {uuid_func()}))'
            )
            existing_segments.append({"net": net_name, "a": a, "b": b, "w": width, "layer": "F.Cu"})
    return emitted, routed_descriptions, existing_segments


def emit_extra_signal_route_segments(
    footprint_blocks_with_nets: list[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    pad_nets_by_ref: dict[str, dict[str, tuple[int, str]]],
    existing_segments: list[dict[str, object]],
    uuid_func,
    *,
    cathode_only: bool = False,
    skip_cathodes: bool = False,
) -> tuple[list[str], list[str]]:
    board_text = "\n".join(footprint_blocks_with_nets)
    pads = parse_pad_geometry_from_text(board_text)
    emitted: list[str] = []
    routed_descriptions: list[str] = []
    route_items: list[tuple[float, float, str, tuple[str, str, str, str, str, str]]] = []

    for description, args in EXTRA_SIGNAL_ROUTE_LINKS:
        is_cathode_route = "cathode sink to direct LD" in description
        if cathode_only and not is_cathode_route:
            continue
        if skip_cathodes and is_cathode_route:
            continue
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        priority = 0.0 if "cathode sink to direct LD" in description else 10.0
        cathode_order = {"LASER_N4": 0.0, "LASER_N3": 1.0, "LASER_N2": 2.0, "LASER_N1": 3.0}
        secondary = cathode_order.get(net_a, -start[1]) if "cathode sink to direct LD" in description else -start[1]
        route_items.append((priority, secondary, description, args))

    for _, _, description, args in sorted(route_items):
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        end = (float(end_pad["x"]), float(end_pad["y"]))
        width = route_width_for_link(description, net_a)
        routed_descriptions.append(description)
        extra_layer = EXTRA_LAYER_ROUTE_OVERRIDES.get(description)
        if extra_layer:
            forced_layer_route = _forced_extra_front_pad_to_layer(description, start, end)
            if forced_layer_route is not None:
                start_via, start_escape, layer_route = forced_layer_route
                if not (
                    _via_clear(pads, existing_segments, start_via, net_a)
                    and _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu")
                ):
                    routed_descriptions.pop()
                    continue
                temp_after_start = existing_segments + [
                    {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                    for a, b in zip(start_escape, start_escape[1:])
                    if a != b
                ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                if not _route_shape_clear(pads, temp_after_start, net_a, layer_route, width, extra_layer):
                    routed_descriptions.pop()
                    continue
            else:
                layered_route = _route_front_pad_to_layer(pads, existing_segments, net_a, start, end, width, extra_layer)
                if layered_route is None:
                    routed_descriptions.pop()
                    continue
                start_via, start_escape, layer_route = layered_route
            for a, b in zip(start_escape, start_escape[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
            _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
            for a, b in zip(layer_route, layer_route[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, extra_layer, code_a, net_a, uuid_func)
            continue

        inner_layer = LASER_CATHODE_INNER_LAYER_NETS.get(net_a) if "cathode sink to direct LD" in description else None
        if inner_layer:
            forced_layer_route = _forced_extra_front_pad_to_layer(description, start, end)
            if forced_layer_route is not None:
                start_via, start_escape, layer_route = forced_layer_route
                if (
                    _via_clear(pads, existing_segments, start_via, net_a)
                    and _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu")
                ):
                    temp_after_start = existing_segments + [
                        {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                        for a, b in zip(start_escape, start_escape[1:])
                        if a != b
                    ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                    if _route_shape_clear(pads, temp_after_start, net_a, layer_route, width, inner_layer):
                        for a, b in zip(start_escape, start_escape[1:]):
                            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                        _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
                        for a, b in zip(layer_route, layer_route[1:]):
                            _emit_segment(emitted, existing_segments, a, b, width, inner_layer, code_a, net_a, uuid_func)
                        continue
            layered_route = _route_front_pad_to_layer(pads, existing_segments, net_a, start, end, width, inner_layer)
            if layered_route is None:
                routed_descriptions.pop()
                continue
            start_via, start_escape, layer_route = layered_route
            for a, b in zip(start_escape, start_escape[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
            _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
            for a, b in zip(layer_route, layer_route[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, inner_layer, code_a, net_a, uuid_func)
            continue

        points = _route_one(pads, existing_segments, net_a, start, end, width)
        if points is None:
            routed_descriptions.pop()
            continue
        if not _route_shape_clear(pads, existing_segments, net_a, points, width, "F.Cu"):
            routed_descriptions.pop()
            continue
        for a, b in zip(points, points[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
    return emitted, routed_descriptions


def emit_bottom_signal_route_segments(
    footprint_blocks_with_nets: list[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    pad_nets_by_ref: dict[str, dict[str, tuple[int, str]]],
    existing_segments: list[dict[str, object]],
    uuid_func,
    *,
    skip_descriptions: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    board_text = "\n".join(footprint_blocks_with_nets)
    pads = parse_pad_geometry_from_text(board_text)
    emitted: list[str] = []
    routed_descriptions: list[str] = []
    route_items: list[tuple[float, float, str, tuple[str, str, str, str, str, str]]] = []

    for description, args in BOTTOM_SIGNAL_ROUTE_LINKS:
        if skip_descriptions is not None and description in skip_descriptions:
            continue
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        end = (float(end_pad["x"]), float(end_pad["y"]))
        if "cathode sink to direct LD" in description:
            priority = -1.0
        elif "ISENSE" in description:
            priority = 0.0
        elif "MPD" in description:
            priority = 0.4
        elif "PWM" in description:
            priority = 1.0
        elif description.startswith("ESP32"):
            priority = 2.0
        elif "CONVST" in description:
            priority = 3.0
        else:
            priority = 5.0
        route_items.append((priority, -start[1], description, args))

    for _, _, description, args in sorted(route_items):
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        end = (float(end_pad["x"]), float(end_pad["y"]))
        width = route_width_for_link(description, net_a)
        start_candidates = _via_candidates(pads, existing_segments, start, end, net_a)[:10]
        end_candidates = _via_candidates(pads, existing_segments, end, start, net_a)[:10]
        committed: tuple[
            tuple[float, float],
            tuple[float, float] | None,
            list[tuple[float, float]],
            list[tuple[float, float]],
            list[tuple[float, float]],
        ] | None = None
        for start_via in start_candidates:
            start_escape = _route_one(pads, existing_segments, net_a, start, start_via, width, route_layer="F.Cu")
            if not start_escape:
                continue
            if not _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu"):
                continue
            temp_after_start = existing_segments + [
                {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                for a, b in zip(start_escape, start_escape[1:])
                if a != b
            ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
            if _pad_on_layer(end_pad, "B.Cu"):
                bottom_route = next(
                    (
                        shape
                        for shape in _bottom_route_shapes(start_via, end)
                        if _route_shape_clear(pads, temp_after_start, net_a, shape, width, "B.Cu")
                    ),
                    None,
                )
                if bottom_route is None and width <= 0.25:
                    bottom_route = _route_one(
                        pads,
                        temp_after_start,
                        net_a,
                        start_via,
                        end,
                        width,
                        step=0.50,
                        route_layer="B.Cu",
                    )
                    if bottom_route is not None and not _route_shape_clear(
                        pads,
                        temp_after_start,
                        net_a,
                        bottom_route,
                        width,
                        "B.Cu",
                    ):
                        bottom_route = None
                if bottom_route:
                    committed = (start_via, None, start_escape, bottom_route, [])
                    break
            for end_via in end_candidates:
                if not _via_clear(pads, temp_after_start, end_via, net_a):
                    continue
                bottom_route = next(
                    (
                        shape
                        for shape in _bottom_route_shapes(start_via, end_via)
                        if _route_shape_clear(pads, temp_after_start, net_a, shape, width, "B.Cu")
                    ),
                    None,
                )
                if bottom_route is None and width <= 0.25:
                    bottom_route = _route_one(
                        pads,
                        temp_after_start,
                        net_a,
                        start_via,
                        end_via,
                        width,
                        step=0.50,
                        route_layer="B.Cu",
                    )
                    if bottom_route is not None and not _route_shape_clear(
                        pads,
                        temp_after_start,
                        net_a,
                        bottom_route,
                        width,
                        "B.Cu",
                    ):
                        bottom_route = None
                if not bottom_route:
                    continue
                temp_after_bottom = temp_after_start + [
                    {"net": net_a, "a": a, "b": b, "w": width, "layer": "B.Cu"}
                    for a, b in zip(bottom_route, bottom_route[1:])
                    if a != b
                ] + [{"net": net_a, "a": end_via, "b": end_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                end_escape = _route_one(pads, temp_after_bottom, net_a, end_via, end, width, route_layer="F.Cu")
                if not end_escape:
                    continue
                if not _route_shape_clear(pads, temp_after_bottom, net_a, end_escape, width, "F.Cu"):
                    continue
                committed = (start_via, end_via, start_escape, bottom_route, end_escape)
                break
            if committed is not None:
                break
        if committed is None:
            continue

        start_via, end_via, start_escape, bottom_route, end_escape = committed
        routed_descriptions.append(description)
        for a, b in zip(start_escape, start_escape[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
        _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
        for a, b in zip(bottom_route, bottom_route[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "B.Cu", code_a, net_a, uuid_func)
        if end_via is not None:
            _emit_via(emitted, existing_segments, end_via, code_a, net_a, uuid_func)
            for a, b in zip(end_escape, end_escape[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
    return emitted, routed_descriptions


def emit_inner_signal_route_segments(
    footprint_blocks_with_nets: list[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    pad_nets_by_ref: dict[str, dict[str, tuple[int, str]]],
    existing_segments: list[dict[str, object]],
    uuid_func,
    *,
    only_descriptions: set[str] | None = None,
    skip_descriptions: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    board_text = "\n".join(footprint_blocks_with_nets)
    pads = parse_pad_geometry_from_text(board_text)
    emitted: list[str] = []
    routed_descriptions: list[str] = []

    for description, args in INNER_SIGNAL_ROUTE_LINKS:
        if only_descriptions is not None and description not in only_descriptions:
            continue
        if skip_descriptions is not None and description in skip_descriptions:
            continue
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        end = (float(end_pad["x"]), float(end_pad["y"]))
        width = route_width_for_link(description, net_a)
        if description == "LASER_IR PWM inner route":
            forced_route = [
                start,
                (55.0, 11.75),
                (52.75, 11.75),
                (52.75, 46.0),
                (36.0, 46.0),
                (36.0, 28.5),
                (35.0, 28.5),
                (35.0, 18.25),
                end,
            ]
            if _route_shape_clear(pads, existing_segments, net_a, forced_route, width, "F.Cu"):
                routed_descriptions.append(description)
                for a, b in zip(forced_route, forced_route[1:]):
                    _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                continue
        if description == "LASER_RED PWM inner route":
            start_via = (67.25, 12.92)
            end_via = (37.6485, 22.239)
            start_escape = [
                start,
                (72.75, 13.25),
                (72.75, 17.0),
                (81.5, 17.0),
                (81.5, 18.5),
                (83.25, 18.5),
                (83.25, 11.5),
                (85.5, 11.5),
                (85.5, 7.25),
                (83.75, 7.25),
                (83.75, 6.0),
                (79.75, 6.0),
                (79.75, 0.5),
                (67.25, 0.5),
                (67.25, 12.75),
                start_via,
            ]
            forced_route = [
                start_via,
                (67.5, 13.0),
                (76.5, 13.0),
                (76.5, 12.5),
                (79.0, 12.5),
                (79.0, 11.0),
                (84.0, 11.0),
                (84.0, 11.5),
                (89.75, 11.5),
                (89.75, 45.5),
                (40.0, 45.5),
                (40.0, 22.0),
                (38.0, 22.0),
                end_via,
            ]
            temp_after_start = existing_segments + [
                {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                for a, b in zip(start_escape, start_escape[1:])
                if a != b
            ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
            end_escape = [end_via, (37.5, 22.25), (36.75, 22.25), (36.75, 22.75), end]
            if (
                _via_clear(pads, existing_segments, start_via, net_a)
                and _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu")
                and _via_clear(pads, temp_after_start, end_via, net_a)
                and _route_shape_clear(pads, temp_after_start, net_a, forced_route, width, "In2.Cu")
            ):
                temp_after_inner = temp_after_start + [
                    {"net": net_a, "a": a, "b": b, "w": width, "layer": "In2.Cu"}
                    for a, b in zip(forced_route, forced_route[1:])
                    if a != b
                ] + [{"net": net_a, "a": end_via, "b": end_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                if _route_shape_clear(pads, temp_after_inner, net_a, end_escape, width, "F.Cu"):
                    routed_descriptions.append(description)
                    for a, b in zip(start_escape, start_escape[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                    _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
                    for a, b in zip(forced_route, forced_route[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "In2.Cu", code_a, net_a, uuid_func)
                    _emit_via(emitted, existing_segments, end_via, code_a, net_a, uuid_func)
                    for a, b in zip(end_escape, end_escape[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                    continue
        if description == "LASER_BLUE PWM inner route":
            start_via = (62.9352, 22.2198)
            end_via = (35.0875, 36.5)
            start_escape = [
                start,
                (65.75, 19.25),
                (65.5, 19.25),
                (65.5, 22.25),
                (63.25, 22.25),
                start_via,
            ]
            forced_route = [
                start_via,
                (62.5, 22.0),
                (49.5, 22.0),
                (49.5, 10.5),
                (56.0, 10.5),
                (56.0, 7.0),
                (35.0, 7.0),
                (35.0, 36.0),
                end_via,
            ]
            temp_after_start = existing_segments + [
                {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                for a, b in zip(start_escape, start_escape[1:])
                if a != b
            ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
            end_escape = [end_via, (35.0, 36.75), (35.0, 41.75), end]
            if (
                _via_clear(pads, existing_segments, start_via, net_a)
                and _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu")
                and _via_clear(pads, temp_after_start, end_via, net_a)
                and _route_shape_clear(pads, temp_after_start, net_a, forced_route, width, "In2.Cu")
            ):
                temp_after_inner = temp_after_start + [
                    {"net": net_a, "a": a, "b": b, "w": width, "layer": "In2.Cu"}
                    for a, b in zip(forced_route, forced_route[1:])
                    if a != b
                ] + [{"net": net_a, "a": end_via, "b": end_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                if not _route_shape_clear(pads, temp_after_inner, net_a, end_escape, width, "F.Cu"):
                    pass
                else:
                    routed_descriptions.append(description)
                    for a, b in zip(start_escape, start_escape[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                    _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
                    for a, b in zip(forced_route, forced_route[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "In2.Cu", code_a, net_a, uuid_func)
                    _emit_via(emitted, existing_segments, end_via, code_a, net_a, uuid_func)
                    for a, b in zip(end_escape, end_escape[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                    continue
        if description == "LASER_GREEN PWM inner route":
            start_via = (62.835, 19.25)
            end_via = (34.239, 33.1515)
            start_escape = [start, (64.5, 19.25), (63.0, 19.25), start_via]
            forced_route = [
                start_via,
                (62.5, 19.0),
                (60.5, 19.0),
                (60.5, 23.0),
                (48.0, 23.0),
                (48.0, 44.0),
                (42.0, 44.0),
                (42.0, 33.0),
                (34.5, 33.0),
                end_via,
            ]
            temp_after_start = existing_segments + [
                {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                for a, b in zip(start_escape, start_escape[1:])
                if a != b
            ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
            end_escape = [end_via, (34.25, 33.5), (34.25, 34.0), (34.75, 34.0), end]
            if (
                _via_clear(pads, existing_segments, start_via, net_a)
                and _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu")
                and _via_clear(pads, temp_after_start, end_via, net_a)
                and _route_shape_clear(pads, temp_after_start, net_a, forced_route, width, "B.Cu")
            ):
                temp_after_inner = temp_after_start + [
                    {"net": net_a, "a": a, "b": b, "w": width, "layer": "B.Cu"}
                    for a, b in zip(forced_route, forced_route[1:])
                    if a != b
                ] + [{"net": net_a, "a": end_via, "b": end_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                if _route_shape_clear(pads, temp_after_inner, net_a, end_escape, width, "F.Cu"):
                    routed_descriptions.append(description)
                    for a, b in zip(start_escape, start_escape[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                    _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
                    for a, b in zip(forced_route, forced_route[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "B.Cu", code_a, net_a, uuid_func)
                    _emit_via(emitted, existing_segments, end_via, code_a, net_a, uuid_func)
                    for a, b in zip(end_escape, end_escape[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                    continue
        if description == "ESP32 UART TX forced inner route":
            forced_route = [
                start,
                (72.75, 5.5),
                (72.75, 5.75),
                (71.5, 5.75),
                (71.5, 10.75),
                (72.5, 10.75),
                (72.75, 10.8),
                (72.5, 11.0),
                (71.0, 11.0),
                (71.0, 28.0),
                (72.0, 28.0),
                (72.0, 30.0),
                (71.5, 30.0),
                (71.1109, 30.1109),
                (71.0, 30.25),
                (71.0, 34.0),
                end,
            ]
            if _route_shape_clear(pads, existing_segments, net_a, forced_route, width, "F.Cu"):
                routed_descriptions.append(description)
                for a, b in zip(forced_route, forced_route[1:]):
                    _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                continue
        if description == "ESP32 EN forced inner route":
            forced_route = [
                start,
                (55.25, 4.25),
                (35.75, 4.25),
                (35.75, 45.5),
                (76.25, 45.5),
                (76.25, 39.0),
                (75.25, 39.0),
                end,
            ]
            temp_after_start = existing_segments + [
                {"net": net_a, "a": start, "b": start, "w": VIA_SIZE, "layer": "*.Cu"}
            ]
            if (
                _via_clear(pads, existing_segments, start, net_a)
                and _route_shape_clear(pads, temp_after_start, net_a, forced_route, width, "In2.Cu")
            ):
                routed_descriptions.append(description)
                _emit_via(emitted, existing_segments, start, code_a, net_a, uuid_func)
                for a, b in zip(forced_route, forced_route[1:]):
                    _emit_segment(emitted, existing_segments, a, b, width, "In2.Cu", code_a, net_a, uuid_func)
                continue
        override_layer = INNER_LAYER_ROUTE_OVERRIDES.get(description)
        if override_layer:
            override_route = _route_front_pad_to_front_pad_layer(
                pads,
                existing_segments,
                net_a,
                start,
                end,
                width,
                override_layer,
            )
            if override_route is not None:
                start_via, end_via, start_escape, layer_route, end_escape = override_route
                routed_descriptions.append(description)
                for a, b in zip(start_escape, start_escape[1:]):
                    _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
                for a, b in zip(layer_route, layer_route[1:]):
                    _emit_segment(emitted, existing_segments, a, b, width, override_layer, code_a, net_a, uuid_func)
                _emit_via(emitted, existing_segments, end_via, code_a, net_a, uuid_func)
                for a, b in zip(end_escape, end_escape[1:]):
                    _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                continue
        start_candidates = _via_candidates(pads, existing_segments, start, end, net_a)[:10]
        end_candidates = _via_candidates(pads, existing_segments, end, start, net_a)[:10]
        committed: tuple[
            tuple[float, float],
            tuple[float, float],
            list[tuple[float, float]],
            list[tuple[float, float]],
            list[tuple[float, float]],
            str,
        ] | None = None
        for start_via in start_candidates:
            start_escape = _route_one(pads, existing_segments, net_a, start, start_via, width, route_layer="F.Cu")
            if not start_escape or not _route_shape_clear(pads, existing_segments, net_a, start_escape, width, "F.Cu"):
                continue
            temp_after_start = existing_segments + [
                {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                for a, b in zip(start_escape, start_escape[1:])
                if a != b
            ] + [{"net": net_a, "a": start_via, "b": start_via, "w": VIA_SIZE, "layer": "*.Cu"}]
            for end_via in end_candidates:
                if not _via_clear(pads, temp_after_start, end_via, net_a):
                    continue
                inner_route = None
                inner_layer = ""
                for candidate_layer in ["In2.Cu", "F.Cu"]:
                    candidate_route = _route_one(
                        pads,
                        temp_after_start,
                        net_a,
                        start_via,
                        end_via,
                        width,
                        step=0.50,
                        route_layer=candidate_layer,
                    )
                    if candidate_route and _route_shape_clear(
                        pads,
                        temp_after_start,
                        net_a,
                        candidate_route,
                        width,
                        candidate_layer,
                    ):
                        inner_route = candidate_route
                        inner_layer = candidate_layer
                        break
                if not inner_route:
                    continue
                temp_after_inner = temp_after_start + [
                    {"net": net_a, "a": a, "b": b, "w": width, "layer": inner_layer}
                    for a, b in zip(inner_route, inner_route[1:])
                    if a != b
                ] + [{"net": net_a, "a": end_via, "b": end_via, "w": VIA_SIZE, "layer": "*.Cu"}]
                end_escape = _route_one(pads, temp_after_inner, net_a, end_via, end, width, route_layer="F.Cu")
                if not end_escape or not _route_shape_clear(pads, temp_after_inner, net_a, end_escape, width, "F.Cu"):
                    continue
                committed = (start_via, end_via, start_escape, inner_route, end_escape, inner_layer)
                break
            if committed is not None:
                break
        if committed is None:
            if description in VIA_IN_PAD_INNER_ROUTE_DESCRIPTIONS:
                if _via_clear(pads, existing_segments, start, net_a):
                    temp_after_start = existing_segments + [
                        {"net": net_a, "a": start, "b": start, "w": VIA_SIZE, "layer": "*.Cu"}
                    ]
                    if _via_clear(pads, temp_after_start, end, net_a):
                        route_layers = ["In2.Cu", "F.Cu"]
                        if description in VIA_IN_PAD_SIGNAL_FALLBACK_ROUTE_DESCRIPTIONS:
                            route_layers.append("B.Cu")
                        if description in LAST_RESORT_GND_PLANE_ROUTE_DESCRIPTIONS:
                            route_layers.append("In1.Cu")
                        inner_route = None
                        inner_layer = ""
                        for candidate_layer in route_layers:
                            candidate_route = _route_one(
                                pads,
                                temp_after_start,
                                net_a,
                                start,
                                end,
                                width,
                                step=0.50,
                                route_layer=candidate_layer,
                            )
                            if candidate_route and _route_shape_clear(
                                pads,
                                temp_after_start,
                                net_a,
                                candidate_route,
                                width,
                                candidate_layer,
                            ):
                                inner_route = candidate_route
                                inner_layer = candidate_layer
                                break
                        if inner_route:
                            routed_descriptions.append(description)
                            _emit_via(emitted, existing_segments, start, code_a, net_a, uuid_func)
                            for a, b in zip(inner_route, inner_route[1:]):
                                _emit_segment(emitted, existing_segments, a, b, width, inner_layer, code_a, net_a, uuid_func)
                            _emit_via(emitted, existing_segments, end, code_a, net_a, uuid_func)
                            continue
            continue

        start_via, end_via, start_escape, inner_route, end_escape, inner_layer = committed
        routed_descriptions.append(description)
        for a, b in zip(start_escape, start_escape[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
        _emit_via(emitted, existing_segments, start_via, code_a, net_a, uuid_func)
        for a, b in zip(inner_route, inner_route[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, inner_layer, code_a, net_a, uuid_func)
        _emit_via(emitted, existing_segments, end_via, code_a, net_a, uuid_func)
        for a, b in zip(end_escape, end_escape[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
    return emitted, routed_descriptions


def emit_power_route_segments(
    footprint_blocks_with_nets: list[str],
    board_ref_by_comp: dict[tuple[str, str], str],
    pad_nets_by_ref: dict[str, dict[str, tuple[int, str]]],
    existing_segments: list[dict[str, object]],
    uuid_func,
    *,
    only_descriptions: set[str] | None = None,
    skip_descriptions: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    board_text = "\n".join(footprint_blocks_with_nets)
    pads = parse_pad_geometry_from_text(board_text)
    emitted: list[str] = []
    routed_descriptions: list[str] = []

    for description, args, width in POWER_ROUTE_LINKS:
        if only_descriptions is not None and description not in only_descriptions:
            continue
        if skip_descriptions is not None and description in skip_descriptions:
            continue
        sheet_a, ref_a, pin_a, sheet_b, ref_b, pin_b = args
        board_a = board_ref_by_comp[(sheet_a, ref_for(sheet_a, ref_a))]
        board_b = board_ref_by_comp[(sheet_b, ref_for(sheet_b, ref_b))]
        code_a, net_a = pad_nets_by_ref[board_a][pin_a]
        code_b, net_b = pad_nets_by_ref[board_b][pin_b]
        if net_a != net_b or code_a != code_b:
            continue
        start_pad = pads[board_a][pin_a][0]
        end_pad = pads[board_b][pin_b][0]
        start = (float(start_pad["x"]), float(start_pad["y"]))
        end = (float(end_pad["x"]), float(end_pad["y"]))
        routed_descriptions.append(description)
        route_layer = POWER_LAYER_ROUTE_OVERRIDES.get(description)
        if route_layer:
            forced_route = _forced_power_front_pad_to_front_pad_layer(description, start, end)
            if forced_route is not None:
                start_via, end_via, start_escape, layer_route, end_escape = forced_route
                via_size = GND_FANOUT_VIA_SIZE if description in LOW_CURRENT_POWER_DOGBONE_ROUTE_DESCRIPTIONS else VIA_SIZE
                via_drill = GND_FANOUT_VIA_DRILL if description in LOW_CURRENT_POWER_DOGBONE_ROUTE_DESCRIPTIONS else VIA_DRILL
                if _via_clear_sized(pads, existing_segments, start_via, net_a, via_size) and _route_shape_clear(
                    pads, existing_segments, net_a, start_escape, width, "F.Cu"
                ):
                    temp_after_start = existing_segments + [
                        {"net": net_a, "a": a, "b": b, "w": width, "layer": "F.Cu"}
                        for a, b in zip(start_escape, start_escape[1:])
                        if a != b
                    ] + [{"net": net_a, "a": start_via, "b": start_via, "w": via_size, "layer": "*.Cu"}]
                    if _via_clear_sized(pads, temp_after_start, end_via, net_a, via_size) and _route_shape_clear(
                        pads, temp_after_start, net_a, layer_route, width, route_layer
                    ):
                        temp_after_layer = temp_after_start + [
                            {"net": net_a, "a": a, "b": b, "w": width, "layer": route_layer}
                            for a, b in zip(layer_route, layer_route[1:])
                            if a != b
                        ] + [{"net": net_a, "a": end_via, "b": end_via, "w": via_size, "layer": "*.Cu"}]
                        if _route_shape_clear(pads, temp_after_layer, net_a, end_escape, width, "F.Cu"):
                            for a, b in zip(start_escape, start_escape[1:]):
                                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                            _emit_sized_via(emitted, existing_segments, start_via, code_a, net_a, via_size, via_drill, uuid_func)
                            for a, b in zip(layer_route, layer_route[1:]):
                                _emit_segment(emitted, existing_segments, a, b, width, route_layer, code_a, net_a, uuid_func)
                            _emit_sized_via(emitted, existing_segments, end_via, code_a, net_a, via_size, via_drill, uuid_func)
                            for a, b in zip(end_escape, end_escape[1:]):
                                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
                            continue

            if _pad_on_layer(start_pad, route_layer) and _pad_on_layer(end_pad, route_layer):
                points = _route_one(pads, existing_segments, net_a, start, end, width, route_layer=route_layer)
                if points is not None and _route_shape_clear(pads, existing_segments, net_a, points, width, route_layer):
                    for a, b in zip(points, points[1:]):
                        _emit_segment(emitted, existing_segments, a, b, width, route_layer, code_a, net_a, uuid_func)
                    continue

            layered_route = _route_front_pad_to_front_pad_layer(
                pads,
                existing_segments,
                net_a,
                start,
                end,
                width,
                route_layer,
                GND_FANOUT_VIA_SIZE if description in LOW_CURRENT_POWER_DOGBONE_ROUTE_DESCRIPTIONS else VIA_SIZE,
            )
            if layered_route is None:
                routed_descriptions.pop()
                continue
            start_via, end_via, start_escape, layer_route, end_escape = layered_route
            via_size = GND_FANOUT_VIA_SIZE if description in LOW_CURRENT_POWER_DOGBONE_ROUTE_DESCRIPTIONS else VIA_SIZE
            via_drill = GND_FANOUT_VIA_DRILL if description in LOW_CURRENT_POWER_DOGBONE_ROUTE_DESCRIPTIONS else VIA_DRILL
            for a, b in zip(start_escape, start_escape[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
            _emit_sized_via(emitted, existing_segments, start_via, code_a, net_a, via_size, via_drill, uuid_func)
            for a, b in zip(layer_route, layer_route[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, route_layer, code_a, net_a, uuid_func)
            _emit_sized_via(emitted, existing_segments, end_via, code_a, net_a, via_size, via_drill, uuid_func)
            for a, b in zip(end_escape, end_escape[1:]):
                _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
            continue

        points = _route_one(pads, existing_segments, net_a, start, end, width)
        if points is None:
            routed_descriptions.pop()
            continue
        if not _route_shape_clear(pads, existing_segments, net_a, points, width, "F.Cu"):
            routed_descriptions.pop()
            continue
        for a, b in zip(points, points[1:]):
            _emit_segment(emitted, existing_segments, a, b, width, "F.Cu", code_a, net_a, uuid_func)
    return emitted, routed_descriptions
