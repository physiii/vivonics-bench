#!/usr/bin/env python3
"""Hierarchical schematic generator for the Laser Controller board.

Source of truth — DO NOT hand-edit the .kicad_sch files; edit this and re-run.
Produces (1 channel, 4 wavelengths):
  laser_controller.kicad_sch       — root (sheet symbols + global-label interconnect)
  tia_ir/red/green/blue.kicad_sch  — four on-board signal PD + OPA380 TIA sheets
  laser_ir/red/green/blue.kicad_sch — four constant-current laser sink sheets
  mcu.kicad_sch                    — imported access-controller ESP32-S3 MCU sheet
  power_io.kicad_sch               — 24V barrel/RJ45 input, onboard 5V/laser bucks, AD7606-4 ADC, laser outputs, MPD feedback
  laser_controller_bom_jlcpcb.csv  — consolidated JLCPCB BOM
  laser_controller_full_procurement.csv — SMT + hand-install procurement manifest
  laser_controller.kicad_pro       — minimal project file (written once if absent)

Architecture: ONE optical channel, FOUR wavelengths (IR / RED / GREEN / BLUE). Each
wavelength has a constant-current laser driver with current-sense feedback, and one
on-board single clear Si PIN photodiode (Osram SFH2201, 300–1100 nm — covers blue→IR)
reverse-biased into an OPA380 TIA → on-board AD7606-4 ADC read by the ESP32. (Single-PD
intensity read = the bench proxy for the
production Gpixel per-pixel intensity reader; see DUAL_PINHOLE / INDEX_READ_PRODUCTION
docs.) Control: copied access-controller ESP32-S3-WROOM-1 MCU sheet with
CP2102N USB-UART, native USB Mini-B, reset/program/factory buttons, and
discrete USB/VBUS ESD/isolation; 4× PWM → 4 laser drivers; 4 laser I-sense
and 4 monitor-PD current-sense outputs → ESP32 ADC pins.
Power: USB VBUS (5V) and a 24V barrel/RJ45 input feed the board; AP63205 makes the +5V rail,
AP2112K-3.3 makes +3V3, and AP63200 makes the shared bench LASER_V+ rail. Every SMT part carries visible-on-
click LCSC + Part Number fields (same convention as the access-controller project).

Run:  python3 gen_laser_controller.py
"""
from __future__ import annotations
import csv
import os
import re
from io import StringIO
from pathlib import Path
from circuit_designators import WL, actualize_parts
from laser_command_limits import limiter_for_sheet

PROJECT = "laser_controller"
ROOT_UUID = "c1d2e3f4-6000-4000-a000-000000000001"
SCHEMATIC_UUIDS = {
    "TIA IR Channel": "c1d2e3f4-5000-4000-a000-000000000001",
    "TIA RED Channel": "c1d2e3f4-5000-4000-a000-000000000002",
    "TIA GREEN Channel": "c1d2e3f4-5000-4000-a000-000000000003",
    "TIA BLUE Channel": "c1d2e3f4-5000-4000-a000-000000000004",
    "Laser IR Driver": "c1d2e3f4-5000-4000-a000-000000000005",
    "Laser RED Driver": "c1d2e3f4-5000-4000-a000-000000000006",
    "Laser GREEN Driver": "c1d2e3f4-5000-4000-a000-000000000007",
    "Laser BLUE Driver": "c1d2e3f4-5000-4000-a000-000000000008",
    "Power & IO": "c1d2e3f4-5000-4000-a000-000000000009",
}
ACCESS_CONTROLLER_MCU = Path("/home/andy/projects/access-controller/circuits/controller/microcontroller.kicad_sch")
ACCESS_CONTROLLER_ETHERNET = Path("/home/andy/projects/access-controller/circuits/controller/ethernet.kicad_sch")
OUT_DIR = Path(__file__).resolve().parent
GRID_MM = 1.27
_ctr = [0]
_pwr_ctr = [200]
def uid(): _ctr[0]+=1; return f"c1d2e3f4-6000-4000-a000-{_ctr[0]:012d}"
def fmt(v): return f"{v:.4f}".rstrip("0").rstrip(".")
def snap(v): return round(round(v / GRID_MM) * GRID_MM, 4)
def snap_point(point): return (snap(point[0]), snap(point[1]))
def grid_parts(parts):
    return {
        ref: (sym, val, fp, mpn, lcsc, snap(x), snap(y))
        for ref, (sym, val, fp, mpn, lcsc, x, y) in parts.items()
    }

def extract_symbol_block(path: Path, symbol_name: str) -> str:
    """Return a top-level KiCad lib_symbol block from a reference schematic."""
    text = path.read_text()
    token = f'    (symbol "{symbol_name}"'
    start = text.find(token)
    if start < 0:
        raise RuntimeError(f"{symbol_name} not found in {path}")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                block = text[start:i + 1]
                return block.replace(
                    '(property "Footprint" "Espressif:ESP32-S3-WROOM-1"',
                    '(property "Footprint" "RF_Module:ESP32-S3-WROOM-1"',
                )
    raise RuntimeError(f"unterminated {symbol_name} block in {path}")

# ═══ Symbols ═══════════════════════════════════════════════════════
SYM = {}
CONNS = ("CONN2","CONN3","CONN4","CONN5","CONN6","CONN8","CONN10","open_automation:CONN_RJ45","USB_MINIB","ESD_USB")
def S(name, pins, glyph, texts=None, power=False, hide_nums=None, roff=(5.6,-1.4), voff=(5.6,1.4)):
    SYM[name] = {"pins":pins, "glyph":glyph, "texts":texts or [], "power":power, "roff":roff, "voff":voff,
                 "hide_nums": hide_nums if hide_nums is not None else (name not in CONNS)}

S("R_H", {"1":(-3.81,0,0,"~","passive",1.27),"2":(3.81,0,180,"~","passive",1.27)},
  [[(-2.54,1.016),(2.54,1.016),(2.54,-1.016),(-2.54,-1.016),(-2.54,1.016)]])
S("R_H_RJ45", {"1":(-3.81,0,0,"~","passive",1.27),"2":(3.81,0,180,"~","passive",1.27)},
  [[(-2.54,1.016),(2.54,1.016),(2.54,-1.016),(-2.54,-1.016),(-2.54,1.016)]],
  roff=(-2.5,-3.2), voff=(-2.5,3.2))
S("R_V", {"1":(0,3.81,270,"~","passive",1.27),"2":(0,-3.81,90,"~","passive",1.27)},
  [[(-1.016,2.54),(1.016,2.54),(1.016,-2.54),(-1.016,-2.54),(-1.016,2.54)]])
S("POT_H", {"1":(-3.81,0,0,"~","passive",1.27),"2":(0,3.81,270,"W","passive",1.27),"3":(3.81,0,180,"~","passive",1.27)},
  [[(-2.54,1.016),(2.54,1.016),(2.54,-1.016),(-2.54,-1.016),(-2.54,1.016)],
   [(0,2.794),(0,1.016)],[(-0.762,1.778),(0,1.016),(0.762,1.778)]])
S("POT_V", {"1":(0,3.81,270,"~","passive",1.27),"2":(3.81,0,180,"W","passive",1.27),"3":(0,-3.81,90,"~","passive",1.27)},
  [[(-1.016,2.54),(1.016,2.54),(1.016,-2.54),(-1.016,-2.54),(-1.016,2.54)],
   [(2.794,0),(1.016,0)],[(1.778,0.762),(1.016,0),(1.778,-0.762)]])
S("C_H", {"1":(-2.54,0,0,"~","passive",1.905),"2":(2.54,0,180,"~","passive",1.905)},
  [[(-0.635,-1.778),(-0.635,1.778)],[(0.635,-1.778),(0.635,1.778)]])
S("C_V", {"1":(0,2.54,270,"~","passive",1.905),"2":(0,-2.54,90,"~","passive",1.905)},
  [[(-1.778,-0.635),(1.778,-0.635)],[(-1.778,0.635),(1.778,0.635)]])
S("C_POL_V", {"1":(0,2.54,270,"+","passive",1.905),"2":(0,-2.54,90,"-","passive",1.905)},
  [[(-1.778,-0.635),(1.778,-0.635)],[(-1.778,0.635),(1.778,0.635)],[(-2.54,1.524),(-1.27,1.524)],[(-1.905,0.889),(-1.905,2.159)]])
# Photodiode (Osram SFH2201 clear Si PIN, KiCad D_Photo convention): cathode (pin1, left) -> +5V bias ; anode (pin2, right) -> TIA -IN
S("PHOTODIODE", {"1":(-2.54,0,0,"K","passive",0),"2":(2.54,0,180,"A","passive",0)},
  [[(2.54,1.524),(2.54,-1.524),(-2.54,0),(2.54,1.524)],       # diode triangle (anode base right → apex left)
   [(-2.54,1.524),(-2.54,-1.524)],                            # cathode bar (left), coincident with the K connection point
   [(0.6,3.0),(-0.4,1.8)],[(-0.4,1.8),(0.32,1.82)],[(-0.4,1.8),(-0.28,2.5)],   # incoming-light arrow 1
   [(2.1,3.0),(1.1,1.8)],[(1.1,1.8),(1.82,1.82)],[(1.1,1.8),(1.22,2.5)]],      # incoming-light arrow 2
  hide_nums=True, roff=(6,2.2), voff=(6,4.2))
# OPA380AID SOIC-8: 1/5/8 are NC, 2=IN-, 3=IN+, 4=V-, 6=OUT, 7=V+.
S("OPA_N", {"1":(-10.16,5.08,0,"NC","passive",2.54),
            "2":(-7.62,2.54,0,"-","input",2.54),"3":(-7.62,-2.54,0,"+","input",2.54),
            "4":(0,-7.62,90,"V-","power_in",5.08),
            "5":(10.16,-5.08,180,"NC","passive",2.54),
            "6":(7.62,0,180,"","output",2.54),"7":(0,7.62,270,"V+","power_in",5.08),
            "8":(10.16,5.08,180,"NC","passive",2.54)},
  [[(-5.08,-5.08),(5.08,0),(-5.08,5.08),(-5.08,-5.08)]],[("+",-3.81,-2.54,1.0),("-",-3.81,2.54,1.0)])
# TLV9001IDBVR, DBV SOT-23-5 package: 1=OUT, 2=V-, 3=IN+, 4=IN-, 5=V+.
S("TLV9001_SOT23_5", {"4":(-7.62,2.54,0,"-","input",2.54),"3":(-7.62,-2.54,0,"+","input",2.54),
            "1":(7.62,0,180,"","output",2.54),"5":(0,7.62,270,"V+","power_in",5.08),"2":(0,-7.62,90,"V-","power_in",5.08)},
  [[(-5.08,-5.08),(5.08,0),(-5.08,5.08),(-5.08,-5.08)]],[("+",-3.81,-2.54,1.0),("-",-3.81,2.54,1.0)])
# AO3400A SOT-23 N-MOSFET: 1=gate, 2=source, 3=drain.
S("NMOS", {"3":(0,5.08,270,"D","passive",2.54),"1":(-5.08,0,0,"G","input",2.54),"2":(0,-5.08,90,"S","passive",2.54)},
  [[(-2.54,2.54),(-2.54,-2.54)],[(-0.635,2.032),(0,0),(-0.635,-2.032)],[(0,2.54),(0,1.524)],[(0,-1.524),(0,-2.54)],[(-0.762,-0.762),(0,-1.524),(0.762,-0.762)]])
# Schottky diode (SS14): anode left, cathode right
S("SCHOTTKY", {"1":(-3.81,0,0,"A","passive",1.27),"2":(3.81,0,180,"K","passive",1.27)},
  [[(-3.81,0),(-1.27,0)],[(1.27,0),(3.81,0)],[(-1.27,1.27),(1.27,0),(-1.27,-1.27),(-1.27,1.27)],
   [(1.27,1.27),(1.27,-1.27)],[(1.27,1.27),(0.508,1.27)],[(1.27,-1.27),(2.032,-1.27)]])
# Two-pin buck output inductor. Pin 1 is the switch-node side; pin 2 is the regulated rail.
S("L_H", {"1":(-5.08,0,0,"1","passive",1.27),"2":(5.08,0,180,"2","passive",1.27)},
  [[(-3.81,0),(-3.175,0.762),(-2.54,0),(-1.905,0.762),(-1.27,0),
    (-0.635,0.762),(0,0),(0.635,0.762),(1.27,0),(1.905,0.762),
    (2.54,0),(3.81,0)]],
  hide_nums=True, roff=(-4.5,-3.0), voff=(-4.5,3.0))
# Access-controller 24V barrel jack switch: pin 1 center-positive input, pins 2/3 sleeve/switch to GND.
S("BARREL_JACK_SWITCH",
  {"1":(7.62,2.54,180,"1","passive",2.54),
   "3":(7.62,0,180,"3","passive",2.54),
   "2":(7.62,-2.54,180,"2","passive",2.54)},
  [[(-5.08,3.81),(5.08,3.81),(5.08,-3.81),(-5.08,-3.81),(-5.08,3.81)],
   [(5.08,2.54),(1.27,2.54)],
   [(5.08,0),(1.27,0),(1.27,-2.286),(0.635,-1.651)],
   [(-3.81,-2.54),(-2.54,-2.54),(-1.27,-1.27),(0,-2.54),(5.08,-2.54)],
   [(1.27,-2.286),(1.905,-1.651)]],
  hide_nums=False, roff=(-4.5,-6.8), voff=(-4.5,6.4))
S("open_automation:CONN_RJ45",
  {"1":(10.16,-7.62,180,"~","passive",2.54),
   "2":(10.16,-5.08,180,"~","passive",2.54),
   "3":(10.16,-2.54,180,"~","passive",2.54),
   "4":(10.16,0,180,"~","passive",2.54),
   "5":(10.16,2.54,180,"~","passive",2.54),
   "6":(10.16,5.08,180,"~","passive",2.54),
   "7":(10.16,7.62,180,"~","passive",2.54),
   "8":(10.16,10.16,180,"~","passive",2.54),
   "9":(-10.16,10.16,0,"~","passive",2.54),
   "10":(-10.16,7.62,0,"~","passive",2.54),
   "11":(-10.16,-5.08,0,"~","passive",2.54),
   "12":(-10.16,-7.62,0,"~","passive",2.54)},
  [[(-7.62,12.7),(7.62,12.7),(7.62,-10.16),(-7.62,-10.16),(-7.62,12.7)]],
  hide_nums=False, roff=(0,-18.03), voff=(0,-15.49))
# ESP32-S3-WROOM-1: pin positions extracted from the official Espressif library symbol.
# Symbol is 91mm wide (x=-45.7..45.7), 81mm tall (y=-40.6..40.6).
# Left-side pins (x=-45.7, rot=0): EN(p3@35.6), JTAG(p32-35@12.7-20.3), flash(p28-30@-30.5..-35.6)
# Right-side pins (x=45.7, rot=180): TXD0(p37@35.6), RXD0(p36@33.0), USB(p13/14@25-28),
#   IO0(p27@20.3), IO1(p39@17.8), IO2(p38@15.2), IO3(p15@12.7), IO4(p4@10.2),
#   IO5(p5@7.6), IO6(p6@5.1), IO7(p7@2.5), IO8(p12@0),
#   FSPI(p17-22@-2.5..-15.2), IO17(p10@-17.8), IO18(p11@-20.3),
#   IO21(p23@-22.9), IO38(p31@-25.4), IO45(p26@-27.9), IO46(p16@-30.5),
#   IO47(p24@-33.0), IO48(p25@-35.6).
# Top: 3V3(p2@0,40.6). Bottom: GND(p1,40,41@0,-40.6)
ESP_PIN = {}; _ep = {}
# Our functional pin mapping → ESP32 pin numbers
ESP_PIN.update({
    "EN":"3", "U0TXD":"37", "U0RXD":"36", "GPIO21":"23", "GPIO0":"27", "BOOT":"27",
    "USB_DM":"13", "USB_DP":"14",
    # Keep analog telemetry on ADC1-capable pins where possible. The copied
    # access-controller MCU sheet exposes generic IO labels; the root sheet maps
    # bench PWM to IO10/IO11/IO12/IO16.
    "PWM1":"18", "PWM2":"19", "PWM3":"20", "PWM4":"9",
    "ISENSE1":"4", "ISENSE2":"5", "ISENSE3":"6", "ISENSE4":"7",
    "MPD1":"38", "MPD2":"15", "MPD3":"12", "MPD4":"17",
    "CONVST":"10", "VDD3P3":"2", "GND":"1",
})
# Actual pin positions from the Espressif library symbol (used by pin() for wiring)
_ep = {
    "1":(0,-40.64,90,"GND","power_in",2.54),
    "2":(0,40.64,270,"3V3","power_in",2.54),
    "3":(-45.72,35.56,0,"EN","input",2.54),
    "4":(45.72,10.16,180,"IO4","bidirectional",2.54),
    "5":(45.72,7.62,180,"IO5","bidirectional",2.54),
    "6":(45.72,5.08,180,"IO6","bidirectional",2.54),
    "7":(45.72,2.54,180,"IO7","bidirectional",2.54),
    "10":(45.72,-17.78,180,"IO17","bidirectional",2.54),
    "11":(45.72,-20.32,180,"IO18","bidirectional",2.54),
    "12":(45.72,0,180,"IO8","bidirectional",2.54),
    "13":(45.72,25.4,180,"IO19","bidirectional",2.54),
    "14":(45.72,27.94,180,"IO20","bidirectional",2.54),
    "15":(45.72,12.7,180,"IO3","bidirectional",2.54),
    "16":(45.72,-30.48,180,"IO46","bidirectional",2.54),
    "17":(45.72,-2.54,180,"IO9","bidirectional",2.54),
    "18":(45.72,-5.08,180,"IO10","bidirectional",2.54),
    "19":(45.72,-7.62,180,"IO11","bidirectional",2.54),
    "20":(45.72,-10.16,180,"IO12","bidirectional",2.54),
    "21":(45.72,-12.7,180,"IO13","bidirectional",2.54),
    "22":(45.72,-15.24,180,"IO14","bidirectional",2.54),
    "23":(45.72,-22.86,180,"IO21","bidirectional",2.54),
    "24":(45.72,-33.02,180,"IO47","bidirectional",2.54),
    "25":(45.72,-35.56,180,"IO48","bidirectional",2.54),
    "26":(45.72,-27.94,180,"IO45","bidirectional",2.54),
    "27":(45.72,20.32,180,"IO0_BOOT","bidirectional",2.54),
    "28":(-45.72,-30.48,0,"GPIO35","bidirectional",2.54),
    "29":(-45.72,-33.02,0,"GPIO36","bidirectional",2.54),
    "30":(-45.72,-35.56,0,"GPIO37","bidirectional",2.54),
    "31":(45.72,-25.4,180,"IO38","bidirectional",2.54),
    "32":(-45.72,20.32,0,"GPIO39","bidirectional",2.54),
    "33":(-45.72,17.78,0,"GPIO40","bidirectional",2.54),
    "34":(-45.72,15.24,0,"GPIO41","bidirectional",2.54),
    "35":(-45.72,12.7,0,"GPIO42","bidirectional",2.54),
    "36":(45.72,33.02,180,"RXD0","bidirectional",2.54),
    "37":(45.72,35.56,180,"TXD0","bidirectional",2.54),
    "38":(45.72,15.24,180,"IO2","bidirectional",2.54),
    "39":(45.72,17.78,180,"IO1","bidirectional",2.54),
    "8":(-45.72,27.94,0,"IO15","bidirectional",2.54),
    "9":(-45.72,25.4,0,"IO16","bidirectional",2.54),
    "40":(0,-40.64,90,"GND","passive",2.54),
    "41":(0,-40.64,90,"GND","passive",2.54),
}

SYM["Espressif:ESP32-S3-WROOM-1"] = {"pins": _ep, "power": False, "hide_nums": False, "roff": (-46,-82), "voff": (2,-82)}
# ESP32-S3-WROOM-1 uses the official Espressif symbol extracted from the
# access-controller schematic.  This SYM entry is only the pin-coordinate map
# used by the generator when drawing wires.
# AP2112K-3.3 low-dropout LDO (SOT-23-5): 1=VIN 2=GND 3=EN 4=NC 5=VOUT  (250mV dropout — USB-VBUS friendly)
S("LDO5",{"1":(0,3.81,270,"VIN","power_in",2.54),"2":(0,-3.81,90,"GND","power_in",2.54),
          "5":(5.08,0,180,"VOUT","power_out",2.54),"3":(-5.08,1.27,0,"EN","input",2.54),"4":(-5.08,-1.27,0,"NC","passive",2.54)},
  [[(-2.54,3.81),(2.54,3.81),(2.54,-3.81),(-2.54,-3.81),(-2.54,3.81)]])
# AP63200/AP63205 TSOT-23-6 buck regulator family: 1=FB, 2=EN, 3=IN, 4=GND, 5=SW, 6=BST.
S("AP6320X_TSOT6",
  {"3":(-10.16,5.08,0,"IN","power_in",2.54),
   "2":(-10.16,0,0,"EN","input",2.54),
   "4":(-10.16,-5.08,0,"GND","power_in",2.54),
   "5":(10.16,5.08,180,"SW","power_out",2.54),
   "6":(10.16,0,180,"BST","passive",2.54),
   "1":(10.16,-5.08,180,"FB","input",2.54)},
  [[(-7.62,7.62),(7.62,7.62),(7.62,-7.62),(-7.62,-7.62),(-7.62,7.62)]],
  [("AP6320x",0,0,1.2)], hide_nums=False, roff=(-7.2,-10.5), voff=(-7.2,10.2))
# PWR_FLAG — declares an external supply node as a power source (silences ERC "no power source")
S("PWR_FLAG",{"1":(0,0,90,"~","power_out",0)},
  [[(0,0),(0,1.27)],[(0,1.27),(-1.016,1.905),(0,2.54),(1.016,1.905),(0,1.27)]],power=True)
# USB Mini-B receptacle (JLCPCB C46391): 1=VBUS 2=D− 3=D+ 4=ID 5=GND 6=shell
S("USB_MINIB",{"1":(-7.62,5.08,0,"VBUS","passive",2.54),"2":(-7.62,2.54,0,"D-","passive",2.54),
               "3":(-7.62,0,0,"D+","passive",2.54),"4":(-7.62,-2.54,0,"ID","passive",2.54),
               "5":(-7.62,-5.08,0,"GND","passive",2.54),"6":(-7.62,-8.89,0,"SHLD","passive",2.54)},
  [[(-5.08,7.62),(2.54,7.62),(2.54,-11.43),(-5.08,-11.43),(-5.08,7.62)]],[("USB",-1.27,0,1.4)])
# Legacy local USBLC6 symbol kept only so old generated schematics can still be parsed.
# The active bench schematic uses the copied access-controller MCU sheet with
# discrete LESD5D5.0CT1G clamps and 1N5819HW VBUS isolation diodes.
S("ESD_USB",{"1":(-7.62,2.54,0,"IO1","passive",2.54),"6":(7.62,2.54,180,"IO1","passive",2.54),
             "3":(-7.62,-2.54,0,"IO2","passive",2.54),"4":(7.62,-2.54,180,"IO2","passive",2.54),
             "5":(0,7.62,270,"VBUS","passive",2.54),"2":(0,-7.62,90,"GND","passive",2.54)},
  [[(-5.08,5.08),(5.08,5.08),(5.08,-5.08),(-5.08,-5.08),(-5.08,5.08)]],[("ESD",0,0,1.2)], roff=(-4,-9), voff=(-4,10))
# INA4180A1IPWR, PW TSSOP-14: quad high/low-side current-sense amplifier.
# Pinout from TI INAx180 datasheet: 1 OUT1, 2 IN-1, 3 IN+1, 4 VS, 5 IN+2,
# 6 IN-2, 7 OUT2, 8 OUT3, 9 IN-3, 10 IN+3, 11 GND, 12 IN+4, 13 IN-4, 14 OUT4.
S("INA4180_TSSOP14",
  {"1":(12.7,15.24,180,"OUT1","output",2.54),
   "2":(-12.7,12.7,0,"IN-1","input",2.54),"3":(-12.7,17.78,0,"IN+1","input",2.54),
   "4":(0,22.86,270,"VS","power_in",2.54),
   "5":(-12.7,7.62,0,"IN+2","input",2.54),"6":(-12.7,2.54,0,"IN-2","input",2.54),
   "7":(12.7,5.08,180,"OUT2","output",2.54),
   "8":(12.7,-5.08,180,"OUT3","output",2.54),
   "9":(-12.7,-7.62,0,"IN-3","input",2.54),"10":(-12.7,-2.54,0,"IN+3","input",2.54),
   "11":(0,-22.86,90,"GND","power_in",2.54),
   "12":(-12.7,-12.7,0,"IN+4","input",2.54),"13":(-12.7,-17.78,0,"IN-4","input",2.54),
   "14":(12.7,-15.24,180,"OUT4","output",2.54)},
  [[(-10.16,20.32),(10.16,20.32),(10.16,-20.32),(-10.16,-20.32),(-10.16,20.32)]],
  [("INA4180",0,0,1.3)], hide_nums=False, roff=(-10.0,-25.5), voff=(-10.0,24.5))
# LM4040C50IDBZR, DBZ SOT-23-3: pin 1 cathode, pin 2 anode, pin 3 "*" must float or tie to anode.
S("LM4040_DBZ",
  {"1":(0,5.08,270,"K","passive",2.54),"2":(0,-5.08,90,"A","passive",2.54),"3":(5.08,-5.08,180,"*","passive",1.27)},
  [[(-1.27,1.27),(1.27,1.27),(0,-1.27),(-1.27,1.27)], [(-1.8,2.54),(1.8,2.54)],
   [(-1.27,-2.54),(1.27,-2.54)], [(3.81,-5.08),(1.27,-2.54)]],
  [("5.0V",0,0,1.0)], hide_nums=False, roff=(6,-6), voff=(6,6))
# AD7606BSTZ-4, LQFP-64: 4-channel simultaneous-sampling ADC in serial mode.
# Pinout follows the AD7606/AD7606-6/AD7606-4 datasheet RL-64 package table.
S("AD7606_4",
  {
   "49":(-25.4,15.24,0,"V1","input",2.54),
   "51":(-25.4,10.16,0,"V2","input",2.54),
   "57":(-25.4,5.08,0,"V3","input",2.54),
   "59":(-25.4,0,0,"V4","input",2.54),
   "9":(25.4,17.78,180,"CONVSTA","input",2.54),
   "10":(25.4,15.24,180,"CONVSTB","input",2.54),
   "11":(25.4,12.7,180,"RESET","input",2.54),
   "12":(25.4,10.16,180,"RD/SCLK","input",2.54),
   "13":(25.4,7.62,180,"CS","input",2.54),
   "14":(25.4,5.08,180,"BUSY","output",2.54),
   "15":(25.4,2.54,180,"FRSTDATA","output",2.54),
   "24":(25.4,0,180,"DB7/DOUTA","output",2.54),
   "25":(25.4,-2.54,180,"DB8/DOUTB","output",2.54),
   "1":(-12.7,25.4,270,"AVCC","power_in",2.54),
   "37":(-7.62,25.4,270,"AVCC","power_in",2.54),
   "38":(-2.54,25.4,270,"AVCC","power_in",2.54),
   "48":(2.54,25.4,270,"AVCC","power_in",2.54),
   "23":(10.16,25.4,270,"VDRIVE","power_in",2.54),
   "6":(15.24,25.4,270,"PAR/SER/BYTE SEL","input",2.54),
   "7":(20.32,25.4,270,"STBY","input",2.54),
   "34":(25.4,-10.16,180,"REF SELECT","input",2.54),
   "3":(-20.32,-25.4,90,"OS0","input",2.54),
   "4":(-17.78,-25.4,90,"OS1","input",2.54),
   "5":(-15.24,-25.4,90,"OS2","input",2.54),
   "8":(-12.7,-25.4,90,"RANGE","input",2.54),
   "16":(-10.16,-25.4,90,"DB0","input",2.54),
   "17":(-7.62,-25.4,90,"DB1","input",2.54),
   "18":(-5.08,-25.4,90,"DB2","input",2.54),
   "19":(-2.54,-25.4,90,"DB3","input",2.54),
   "20":(0,-25.4,90,"DB4","input",2.54),
   "21":(2.54,-25.4,90,"DB5","input",2.54),
   "22":(5.08,-25.4,90,"DB6","input",2.54),
   "27":(7.62,-25.4,90,"DB9","input",2.54),
   "28":(10.16,-25.4,90,"DB10","input",2.54),
   "29":(12.7,-25.4,90,"DB11","input",2.54),
   "30":(15.24,-25.4,90,"DB12","input",2.54),
   "31":(17.78,-25.4,90,"DB13","input",2.54),
   "32":(20.32,-25.4,90,"DB14/HBEN","input",2.54),
   "33":(22.86,-25.4,90,"DB15/BYTE SEL","input",2.54),
   "36":(-25.4,-7.62,0,"REGCAP","passive",2.54),
   "39":(-25.4,-12.7,0,"REGCAP","passive",2.54),
   "42":(-25.4,-17.78,0,"REFIN/REFOUT","passive",2.54),
   "44":(-25.4,-22.86,0,"REFCAPA","passive",2.54),
   "45":(-25.4,-25.4,0,"REFCAPB","passive",2.54),
   "2":(-25.4,-33.02,90,"AGND","power_in",2.54),
   "26":(-22.86,-33.02,90,"AGND","power_in",2.54),
   "35":(-20.32,-33.02,90,"AGND","power_in",2.54),
   "40":(-17.78,-33.02,90,"AGND","power_in",2.54),
   "41":(-15.24,-33.02,90,"AGND","power_in",2.54),
   "43":(-12.7,-33.02,90,"REFGND","power_in",2.54),
   "46":(-10.16,-33.02,90,"REFGND","power_in",2.54),
   "47":(-7.62,-33.02,90,"AGND","power_in",2.54),
   "50":(-5.08,-33.02,90,"V1GND","power_in",2.54),
   "52":(-2.54,-33.02,90,"V2GND","power_in",2.54),
   "53":(0,-33.02,90,"AGND","power_in",2.54),
   "54":(2.54,-33.02,90,"AGND","power_in",2.54),
   "55":(5.08,-33.02,90,"AGND","power_in",2.54),
   "56":(7.62,-33.02,90,"AGND","power_in",2.54),
   "58":(10.16,-33.02,90,"V3GND","power_in",2.54),
   "60":(12.7,-33.02,90,"V4GND","power_in",2.54),
   "61":(15.24,-33.02,90,"AGND","power_in",2.54),
   "62":(17.78,-33.02,90,"AGND","power_in",2.54),
   "63":(20.32,-33.02,90,"AGND","power_in",2.54),
   "64":(22.86,-33.02,90,"AGND","power_in",2.54),
  },
  [[(-22.86,22.86),(22.86,22.86),(22.86,-22.86),(-22.86,-22.86),(-22.86,22.86)],
   [(-22.86,-22.86),(-22.86,-25.4)],
   [(-25.4,-30.48),(22.86,-30.48)]],
  [("AD7606-4",0,0,1.4)], hide_nums=False, roff=(-22,-26), voff=(-22,25))
SYM["AD7606_4"]["body_box"] = (-22.86, 22.86, 22.86, -22.86)
S("LASER_CAN_MON_PD",
  {"1":(-12.7,0,0,"LD_K","passive",4.7),
   "2":(0,-12.7,90,"LD_A/PD_K/CASE","passive",4.7),
   "3":(12.7,5.08,180,"PD_A","passive",4.7)},
  [[(-8.0,-8.0),(8.0,-8.0),(8.0,10.0),(-8.0,10.0),(-8.0,-8.0)],
   [(-5.0,-2.5),(1.0,0.0),(-5.0,2.5),(-5.0,-2.5)],
   [(1.0,-3.2),(1.0,3.2)],
   [(-2.5,6.8),(2.5,6.8),(0.0,9.2),(-2.5,6.8)],
   [(2.5,6.0),(2.5,9.6)]],
  [("LD",-2.5,-5.5,1.0),("MPD",-1.0,4.2,1.0)],
  hide_nums=False, roff=(-14,-16), voff=(-14,14))
S("LASER_CAN_DIODE_CASE",
  {"1":(0,-12.7,90,"LD_A","passive",4.7),
   "2":(12.7,5.08,180,"CASE","passive",4.7),
   "3":(-12.7,0,0,"LD_K","passive",4.7)},
  [[(-8.0,-8.0),(8.0,-8.0),(8.0,10.0),(-8.0,10.0),(-8.0,-8.0)],
   [(-5.0,-2.5),(1.0,0.0),(-5.0,2.5),(-5.0,-2.5)],
   [(1.0,-3.2),(1.0,3.2)],
   [(4.0,5.5),(7.0,5.5),(7.0,8.5),(4.0,8.5),(4.0,5.5)]],
  [("LD",-2.5,-5.5,1.0),("CASE",2.5,4.2,1.0)],
  hide_nums=False, roff=(-14,-16), voff=(-14,14))
for sn,ys in [("CONN4",[3.81,1.27,-1.27,-3.81]),("CONN2",[1.27,-1.27]),("CONN3",[2.54,0,-2.54]),
              ("CONN5",[5.08,2.54,0,-2.54,-5.08]),("CONN6",[6.35,3.81,1.27,-1.27,-3.81,-6.35]),
              ("CONN8",[8.89,6.35,3.81,1.27,-1.27,-3.81,-6.35,-8.89]),
              ("CONN10",[11.43,8.89,6.35,3.81,1.27,-1.27,-3.81,-6.35,-8.89,-11.43])]:
    h=abs(ys[0])+1.27; S(sn,{str(i+1):(-5.08,y,0,str(i+1),"passive",2.54) for i,y in enumerate(ys)},
      [[(-2.54,h),(2.54,h),(2.54,-h),(-2.54,-h),(-2.54,h)]],hide_nums=False)
S("+5V",{"1":(0,0,90,"+5V","power_in",0)},[[(0,0),(0,2.54)],[(-1.27,1.524),(0,2.54),(1.27,1.524)]],power=True)
S("+3V3",{"1":(0,0,90,"+3V3","power_in",0)},[[(0,0),(0,2.54)],[(-1.27,1.524),(0,2.54),(1.27,1.524)]],power=True)
S("LASER_VP",{"1":(0,0,90,"LASER_V+","power_in",0)},[[(0,0),(0,2.54)],[(-1.27,1.524),(0,2.54),(1.27,1.524)]],power=True)
S("VIN_24V",{"1":(0,0,90,"VIN_24V","power_in",0)},[[(0,0),(0,2.54)],[(-1.27,1.524),(0,2.54),(1.27,1.524)]],power=True)
S("GND",{"1":(0,0,270,"GND","power_in",0)},[[(0,0),(0,-2.032)],[(-2.032,-2.032),(2.032,-2.032)],
  [(-1.27,-2.794),(1.27,-2.794)],[(-0.508,-3.556),(0.508,-3.556)]],power=True)
S("MOUNTING_HOLE_PAD", {"1":(0,0,90,"1","passive",0)},
  [[(-1.27,0),(1.27,0)],[(0,-1.27),(0,1.27)],[(-1.27,1.27),(1.27,1.27),(1.27,-1.27),(-1.27,-1.27),(-1.27,1.27)]],
  hide_nums=False, roff=(-3.2,-5.2), voff=(-3.2,4.4))

REFLET={"R_H":"R","R_H_RJ45":"R","R_V":"R","POT_H":"RV","POT_V":"RV","C_H":"C","C_V":"C","C_POL_V":"C","PHOTODIODE":"D","OPA_N":"U",
        "TLV9001_SOT23_5":"U",
        "INA4180_TSSOP14":"U","LM4040_DBZ":"U","AD7606_4":"U",
        "LASER_CAN_MON_PD":"LD",
        "LASER_CAN_DIODE_CASE":"LD",
        "MOUNTING_HOLE_PAD":"H",
        "CONN2":"J","CONN3":"J","CONN4":"J","CONN5":"J","CONN6":"J","CONN8":"J","CONN10":"J",
        "BARREL_JACK_SWITCH":"J","L_H":"L","AP6320X_TSOT6":"U","NMOS":"Q",
        "Espressif:ESP32-S3-WROOM-1":"U",
        "LDO5":"U","SCHOTTKY":"D","USB_MINIB":"J","ESD_USB":"U"}
# Hand-add exclusions: only legacy/generic THT headers. J5/J6 are explicitly
# kept in the JLCPCB BOM/CPL as THT connector assembly rows.
HAND={"CONN2","CONN3","CONN4","CONN5","CONN6","CONN8","CONN10"}
JLCPCB_THT_ASSEMBLY={"open_automation:CONN_RJ45","BARREL_JACK_SWITCH"}
NON_SMT_ASSEMBLY={"LASER_CAN_MON_PD","LASER_CAN_DIODE_CASE"}
PASSIVE_GLYPH_NUMS=("R_H","R_H_RJ45","R_V","POT_H","POT_V","C_H","C_V","PHOTODIODE","OPA_N","TLV9001_SOT23_5","NMOS","SCHOTTKY")

FP_R="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_R0402="Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder"
FP_R2512="Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder"
FP_603="Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_402="Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"
FP_805="Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_1206="Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
FP_CELEC_8X10="Capacitor_SMD:C_Elec_8x10.2"
FP_SO8="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_TSSOP14="Package_SO:TSSOP-14_4.4x5mm_P0.65mm"
FP_AD7606="Package_QFP:LQFP-64_10x10mm_P0.5mm"
FP_POT_SMD="Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical"   # SMD trimmer (JLCPCB-mountable)
FP_SOT235="Package_TO_SOT_SMD:SOT-23-5"
FP_TSOT236="Package_TO_SOT_SMD:TSOT-23-6"
FP_SOT23="Package_TO_SOT_SMD:SOT-23"
FP_SMA="Diode_SMD:D_SMA"
FP_ESP32S3="RF_Module:ESP32-S3-WROOM-1"   # stock KiCad footprint available here; access-controller uses Espressif lib name for same module
FP_USB="Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal"  # access-controller Mini-B placement footprint
FP_PD="OptoDevice:Osram_SFH2201"          # clear broadband Si PIN PD; in-tree KiCad footprint (pad1=K, pad2=A)
FP_LASER_TO18="OptoDevice:LaserDiode_TO18-D5.6-3"
FP_LASER_TO56="OptoDevice:LaserDiode_TO56-3"
FP_BARREL="Open_Automation:BarrelJack_OD5.5_ID2.5"
FP_RJ45="Connector_RJ:RJ45_Amphenol_RJHSE538X"
FP_IND_4R7="Open_Automation:L_5.4x5.3_H3"
FP_IND_10="Open_Automation:L_4x4"
FP_H2="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_H5="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
FP_H6="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
FP_H10="Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical"

# ── Verified LCSC numbers (parts agent, 2026-06-28) ───────────────────
LCSC_10K="C844918"    # 10k 0603 1% Vishay CRCW060310K0FKEA (in stock)
LCSC_22R="C23345"     # 22Ω 0603 1% UNI-ROYAL 0603WAF220JT5E (Basic) — USB D+/D− series damping
LCSC_10R="C5123624"  # 10Ω 2512 2W 1% Milliohm HoCR2512-2W-10R-1% — laser source sense
LCSC_1K="C2907002"; LCSC_10PF="C106245"; LCSC_10UF="C318691"; LCSC_1UF="C7472946"; LCSC_100NF="C83056"
LCSC_22UF_25V="C45783"  # Samsung CL21A226MAQNNNE 22uF 25V X5R 0805, JLCPCB Basic
LCSC_1UF_100V="C13832" # Samsung CL31B105KCHNNNE 1uF 100V X7R 1206, copied from access-controller PoE input filtering
LCSC_22UF_100V="C242011" # SUNCON 100CE22FS+P 22uF 100V SMD electrolytic, JLCPCB SMT order candidate
LCSC_240R="C103446"  # 240Ω 0603 1% RALEC RTT032400FTP — monitor-PD sense shunt
LCSC_249K="C22908" # 2.49k 0603 1% UNI-ROYAL 0603WAF2491T5E — LM4040 shunt-reference sink
LCSC_221K="C2929993" # 22.1k 0402 1% FOJAN FRC0402F2212TS — AP63200 laser feedback bottom resistor
LCSC_237K="C2998117" # 237k 0603 1% FOJAN FRC0603F2373TS — AP63200 laser feedback top resistor
LCSC_10UF_50V="C89632"  # 10uF 50V X7R 1206 Samsung CL31B106KBHNNNE — AP632 input ceramic bypass
LCSC_100PF="C1546"   # 100pF 0402 C0G Fenghua 0402CG101J500NT — AP63200 optional feed-forward cap
LCSC_POT10K="C81348" # Bourns 3224W-1-103 10k SMD trimmer (Extended) — replaces THT 3296W VBIAS pot
LCSC_POT2M="C116323" # Bourns 3224W-1-205E 2M SMD trimmer (Extended) — TIA feedback rheostat
LCSC_OPA="C201677"   # OPA380AID (Extended, low stock — buy buffer)
LCSC_TLV="C398363"; LCSC_NMOS="C20917" # AO3400A N-MOSFET, SOT-23, Basic
LCSC_INA4180="C2057528" # INA4180A1IPWR quad current-sense amplifier, TSSOP-14
LCSC_LM4040="C69316"    # LM4040C50IDBZR 5.0V shunt reference, SOT-23-3
LCSC_ESP="C2913199"  # ESP32-S3-WROOM-1 (exact C-number used on the access-controller); native USB D-=GPIO19 D+=GPIO20
LCSC_LDO="C51118"    # AP2112K-3.3 SOT-23-5, 250mV dropout (was AMS1117 C6186 — too much dropout off USB VBUS)
LCSC_ESD="C7519"     # legacy inactive USBLC6-2SC6 local-MCU generator path
LCSC_SCH="C2480"     # SS14 SMA Schottky 40V/1A (Basic)
LCSC_USB="C46391"  # JLCPCB USB Mini-B SMD 920-462A2021S10101 on the same placed footprint
LCSC_PD="C2900216"   # Osram SFH2201 clear broadband Si PIN PD (Extended); 300–1100nm covers 450/520/650/780nm
LCSC_AD7606="C51512" # Analog Devices AD7606BSTZ-4RL 4ch 16-bit simultaneous-sampling ADC, LQFP-64
LCSC_BARREL="C194407" # GANGYUAN DC-470-2.1GP barrel jack, 2.1mm ID/6.3mm OD, 30V/500mA, same access-controller footprint
LCSC_RJ45="C386757" # Ckmtw R-RJ45R08P-C000 RJ45 jack, same access-controller footprint and pin/power convention
LCSC_AP63205="C2071056" # Diodes AP63205WU-7 fixed 5V, 3.8-32V input, 2A synchronous buck, TSOT-23-6
LCSC_AP63200="C2071868" # Diodes AP63200WU-7 adjustable, 3.8-32V input, 2A synchronous buck, TSOT-23-6
LCSC_L4R7="C408410"  # Sunlord MWSA0503S-4R7MT 4.7uH buck inductor, access-controller/Open_Automation footprint
LCSC_L10UH="C98364"  # Sunlord WPN4020H100MT 10uH buck inductor, access-controller/Open_Automation footprint

LASER_MPN = {
    "LASER_IR": {
        "symbol": "LASER_CAN_MON_PD",
        "value": "D7805I 780nm TO18 STYLE-A LASER+MPD",
        "footprint": FP_LASER_TO18,
        "mpn": "D7805I",
        "ld_k": "1",
        "ld_a": "2",
        "mpd": "3",
    },
    "LASER_RED": {
        "symbol": "LASER_CAN_MON_PD",
        "value": "D6505I 650nm TO18 STYLE-A LASER+MPD",
        "footprint": FP_LASER_TO18,
        "mpn": "D6505I",
        "ld_k": "1",
        "ld_a": "2",
        "mpd": "3",
    },
    "LASER_GREEN": {
        "symbol": "LASER_CAN_MON_PD",
        "value": "PLT5 520EB_P TO56 LASER+MPD",
        "footprint": FP_LASER_TO56,
        "mpn": "PLT5 520EB_P",
        "ld_k": "1",
        "ld_a": "2",
        "mpd": "3",
    },
    "LASER_BLUE": {
        "symbol": "LASER_CAN_DIODE_CASE",
        "value": "PLT5 450GB TO56 LASER CASE",
        "footprint": FP_LASER_TO56,
        "mpn": "PLT5 450GB",
        "ld_k": "3",
        "ld_a": "1",
        "case": "2",
    },
}

def pin(parts,ref,num):
    sym,*_,x,y=parts[ref]; lx,ly=SYM[sym]["pins"][num][:2]; return snap_point((x+lx,y-ly))

def add_stub(wires,labels,p,side,name,dist=5.08,shape="passive"):
    """Short stub + label off a pin.  side: 'left'|'right'.  name may start 'H:' (hierarchical)."""
    p = snap_point(p)
    d = -dist if side=="left" else dist
    end=snap_point((p[0]+d, p[1]))
    wires.append([p,end]); labels.append((name,end[0],end[1],"right" if d<0 else "left",shape))

def add_label(labels,p,name,justify="left",shape="passive"):
    p = snap_point(p)
    labels.append((name,p[0],p[1],justify,shape))

def add_bent_label(wires,labels,start,bends,name,justify="left",shape="passive"):
    points=[snap_point(start),*[snap_point(bend) for bend in bends]]
    wires.append(points)
    add_label(labels,points[-1],name,justify=justify,shape=shape)

def add_rail(power,wires,kind,p):
    """Drop a power symbol on a pin via a short vertical stub (rail above, GND below)."""
    p = snap_point(p)
    sp=snap_point((p[0], p[1]+ (5.08 if kind=="GND" else -5.08)))
    power.append((kind,sp[0],sp[1])); wires.append([p,sp])

def add_rail_dn(power,wires,kind,p):
    """Place a rail symbol BELOW a pin (for bottom-of-connector supply pins)."""
    p = snap_point(p)
    sp=snap_point((p[0], p[1]+6.35)); power.append((kind,sp[0],sp[1])); wires.append([p,sp])

def add_bus_rail(power,wires,kind,pins,bus_y=None,bus_x=None,symbol_at=None):
    """Tie a group of pins to one visible power symbol through a shared bus."""
    points = [snap_point(point) for point in pins]
    if not points:
        return
    if (bus_y is None) == (bus_x is None):
        raise ValueError("add_bus_rail needs exactly one of bus_y or bus_x")
    if bus_y is not None:
        bus_y = snap(bus_y)
        symbol = snap_point(symbol_at) if symbol_at else snap_point((
            (min(point[0] for point in points) + max(point[0] for point in points)) / 2,
            bus_y + (5.08 if kind == "GND" else -5.08),
        ))
        tap = snap_point((symbol[0], bus_y))
        bus_points = sorted({(point[0], bus_y) for point in points} | {tap})
        wires.append(bus_points)
        for point in points:
            wires.append([point, (point[0], bus_y)])
        wires.append([tap, symbol])
    else:
        bus_x = snap(bus_x)
        symbol = snap_point(symbol_at) if symbol_at else snap_point((
            bus_x + (5.08 if kind != "GND" else -5.08),
            (min(point[1] for point in points) + max(point[1] for point in points)) / 2,
        ))
        tap = snap_point((bus_x, symbol[1]))
        bus_points = sorted({(bus_x, point[1]) for point in points} | {tap}, key=lambda point: point[1])
        wires.append(bus_points)
        for point in points:
            wires.append([point, (bus_x, point[1])])
        wires.append([tap, symbol])
    power.append((kind, symbol[0], symbol[1]))

def declare_source(power,wires,kind,x,y):
    """Isolated rail-symbol + PWR_FLAG pair → tells ERC this externally-supplied net has a source."""
    x, y = snap(x), snap(y)
    flag = snap_point((x, y-5.08))
    power.append((kind,x,y)); power.append(("PWR_FLAG",flag[0],flag[1])); wires.append([(x,y),flag])

def ortho(poly):
    """Manhattanize a polyline: insert an L-bend corner so no segment is ever diagonal."""
    poly = [snap_point(point) for point in poly]
    out=[poly[0]]
    for a,b in zip(poly,poly[1:]):
        if abs(a[0]-b[0])>1e-6 and abs(a[1]-b[1])>1e-6:
            out.append(snap_point((b[0],a[1])))
        out.append(b)
    return out

def sym_def(name):
    if name == "Espressif:ESP32-S3-WROOM-1":
        return extract_symbol_block(ACCESS_CONTROLLER_MCU, name)
    if name == "open_automation:CONN_RJ45":
        return extract_symbol_block(ACCESS_CONTROLLER_ETHERNET, name)
    if ":" in name: return ""  # library symbol, not defined inline
    s=SYM[name]
    ref = "#PWR" if s["power"] else REFLET[name]
    ref_y = 3.6 if s["power"] else 6.6
    val_y = 3.0 if s["power"] else -6.6
    ref_hide = " hide" if s["power"] else ""
    o=[f'  (symbol "viv:{name}"']
    if s["power"]: o.append("    (power)")
    if s["hide_nums"]: o.append("    (pin_numbers hide)")
    o+=["    (pin_names (offset 1.016) hide)",
        f"    (in_bom {'no' if s['power'] or name in NON_SMT_ASSEMBLY else 'yes'}) (on_board yes)",
        f'    (property "Reference" "{ref}" (at 0 {fmt(ref_y)} 0) (effects (font (size 1.27 1.27)){ref_hide}))',
        f'    (property "Value" "{name}" (at 0 {fmt(val_y)} 0) (effects (font (size 1.27 1.27))))',
        '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
        '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
        f'    (symbol "{name}_0_1"']
    for poly in s["glyph"]:
        pts=' '.join(f'(xy {fmt(x)} {fmt(y)})' for x,y in poly)
        o.append(f"      (polyline (pts {pts}) (stroke (width 0.1524) (type default)) (fill (type none)))")
    for t,x,y,sz in s["texts"]: o.append(f'      (text "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size {sz} {sz}))))')
    o.append("    )"); o.append(f'    (symbol "{name}_1_1"')
    hn=s["power"] or name in PASSIVE_GLYPH_NUMS
    num_hide = " hide" if hn else ""
    for num,(lx,ly,ang,pn,et,ln) in s["pins"].items():
        o.append(f'      (pin {et} line (at {fmt(lx)} {fmt(ly)} {ang}) (length {fmt(ln)}) '
                 f'(name "{pn}" (effects (font (size 1.0 1.0)))) '
                 f'(number "{num}" (effects (font (size 1.0 1.0)){num_hide})))')
    o+=["    )","  )"]; return "\n".join(o)

def build_viv_symbol_library():
    blocks = []
    for name in sorted(SYM):
        block = sym_def(name)
        if not block:
            continue
        blocks.append(block.replace(f'  (symbol "viv:{name}"', f'  (symbol "{name}"', 1))
    text = "(kicad_symbol_lib (version 20220914) (generator gen_laser_controller)\n"
    text += "\n".join(blocks)
    text += "\n)\n"
    return text

def emit_part(ref,sym,val,fp,mpn,lcsc,x,y):
    x, y = snap(x), snap(y)
    rx,ry=SYM[sym]["roff"]; vx,vy=SYM[sym]["voff"]
    lib_id = sym if ":" in sym else f"viv:{sym}"
    in_bom = "no" if sym in NON_SMT_ASSEMBLY else "yes"
    on_board = "yes"
    L=[f'  (symbol (lib_id "{lib_id}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
       f"    (in_bom {in_bom}) (on_board {on_board}) (dnp no)",f"    (uuid {uid()})",
       f'    (property "Reference" "{ref}" (at {fmt(x+rx)} {fmt(y+ry)} 0) (effects (font (size 1.0 1.0)) (justify left)))',
       f'    (property "Value" "{val}" (at {fmt(x+vx)} {fmt(y+vy)} 0) (effects (font (size 1.0 1.0)) (justify left)))',
       f'    (property "Footprint" "{fp}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))',
       f'    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))',
       f'    (property "Part Number" "{mpn}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))',
       f'    (property "LCSC" "{lcsc}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))']
    for num in SYM[sym]["pins"]: L.append(f'    (pin "{num}" (uuid {uid()}))')
    L+=["    (instances",f'      (project "{PROJECT}"',f'        (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))',"      )","    )","  )"]
    return "\n".join(L)

def emit_power(kind,x,y,n):
    x, y = snap(x), snap(y)
    ry=y+3.0 if kind=="GND" else y-3.0; vy=y+4.2 if kind=="GND" else y-3.2
    _pwr_ctr[0] += 1
    ref = f"#PWR{_pwr_ctr[0]:04d}"
    return "\n".join([
        f'  (symbol (lib_id "viv:{kind}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
        "    (in_bom no) (on_board yes) (dnp no)",f"    (uuid {uid()})",
        f'    (property "Reference" "{ref}" (at {fmt(x)} {fmt(ry)} 0) (effects (font (size 1.0 1.0)) hide))',
        f'    (property "Value" "{kind}" (at {fmt(x)} {fmt(vy)} 0) (effects (font (size 1.27 1.27))))',
        '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.0 1.0)) hide))',
        '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.0 1.0)) hide))',
        f'    (pin "1" (uuid {uid()}))',"    (instances",f'      (project "{PROJECT}"',
        f'        (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))',"      )","    )","  )"])

BOM_REG = {}
def build_sch_content(title,date,rev,parts,power,wires,junctions,labels,texts,mult=1,ncs=None,paper="A3"):
    parts = grid_parts(parts)
    power = [(kind, snap(x), snap(y)) for kind, x, y in power]
    junctions = [snap_point(point) for point in junctions]
    ncs = [snap_point(point) for point in (ncs or [])]
    labels = [
        (label[0], snap(label[1]), snap(label[2]), *label[3:])
        for label in labels
    ]
    BOM_REG[title]=(mult,parts)
    P=["(kicad_sch","  (version 20230121)","  (generator eeschema)",f"  (uuid {SCHEMATIC_UUIDS[title]})",
       f'  (paper "{paper}")',"  (title_block",f'    (title "{title}")',f'    (date "{date}")',f'    (rev "{rev}")',
       '    (company "Vivonics")',"  )","  (lib_symbols"]
    used=sorted({t[0] for t in parts.values()} | {k for k,_,_ in power})
    for name in used:
        block = sym_def(name)
        if block:
            P.append(block)
    P.append("  )")
    for ref,t in parts.items(): P.append(emit_part(ref,*t))
    for i,(kind,x,y) in enumerate(power,1): P.append(emit_power(kind,x,y,i))
    for poly in wires:
        poly=ortho(poly)
        for a,b in zip(poly,poly[1:]):
            if a==b: continue
            P.append(f"  (wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})) (stroke (width 0) (type default)) (uuid {uid()}))")
    for x,y in junctions: P.append(f"  (junction (at {fmt(x)} {fmt(y)}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))")
    for x,y in ncs: P.append(f"  (no_connect (at {fmt(x)} {fmt(y)}) (uuid {uid()}))")
    for label in labels:
        if len(label) == 4:
            t,x,y,j = label
            shape = "passive"
            size = 1.27
        elif len(label) == 5:
            t,x,y,j,shape = label
            size = 1.27
        else:
            t,x,y,j,shape,size = label
        if t.startswith("H:"):
            P.append(f'  (hierarchical_label "{t[2:]}" (shape {shape}) (at {fmt(x)} {fmt(y)} 0) (effects (font (size {fmt(size)} {fmt(size)})) (justify {j})) (uuid {uid()}))')
        else:
            P.append(f'  (label "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size {fmt(size)} {fmt(size)})) (justify {j} bottom)) (uuid {uid()}))')
    for t,x,y,sz in texts: P.append(f'  (text "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size {sz} {sz})) (justify left)) (uuid {uid()}))')
    P+=['  (sheet_instances','    (path "/" (page "1"))',"  )",")"]
    txt="\n".join(P)+"\n"
    assert sum((c=="(")-(c==")") for c in txt)==0,f"paren imbalance in {title}"
    return txt

# ═══ SUB-SHEET: tia_<wavelength>.kicad_sch  (on-board PD + OPA380 TIA) ═══
def build_tia_channel(sheet_name: str):
    oy=150; ux=215
    RfY,CfY = 124, 130
    pdcx,pdcy=188,131                                # PD cluster sits ABOVE the VBIAS chain (own clear column)
    pd_kx = pdcx - 2.54                              # Put the bypass tap on the diode cathode glyph.
    parts={
        "D1":("PHOTODIODE","SFH2201",FP_PD,"SFH2201",LCSC_PD,pdcx,pdcy),       # on-board signal PD (one wavelength)
        "RB":("R_H","1k",FP_R,"FRC0603F1001TS",LCSC_1K,pdcx-16,pdcy),          # PD cathode → +5V bias
        "CB":("C_V","1uF",FP_402,"HGC0402R5105K250NTEJ",LCSC_1UF,pd_kx,pdcy+6),     # PD cathode bypass → GND
        "U1":("OPA_N","OPA380AID",FP_SO8,"OPA380AID",LCSC_OPA,ux,oy),
        "RVFB":("POT_H","RF 2M",FP_POT_SMD,"3224W-1-205E",LCSC_POT2M,215,RfY), # feedback trim, wiper tied to output side
        "C1":("C_H","10pF C0G",FP_603,"CC0603JRNPO9BN100",LCSC_10PF,215,CfY),
        "RT":("R_V","10k",FP_R,"CRCW060310K0FKEA",LCSC_10K,165,140),          # bounds VBIAS ≤2.5V (OPA380 CM)
        "RV11":("POT_V","VBIAS 10k",FP_POT_SMD,"3224W-1-103E",LCSC_POT10K,165,oy+2.54),  # SMD trimmer
        "R1":("R_H","10k",FP_R,"CRCW060310K0FKEA",LCSC_10K,181,oy+2.54),
        "C11":("C_V","10uF",FP_805,"CL21A106KAYNNNG",LCSC_10UF,191,oy+12),
        "C2":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,246,oy+10),    # V+ decoupling (clear space)
    }
    parts = grid_parts(parts)
    nIN=pin(parts,"U1","2"); pIN=pin(parts,"U1","3"); OUT=pin(parts,"U1","6")
    oy = parts["U1"][6]
    LRX,RRX = nIN[0], OUT[0]                          # feedback rails rise from −IN / out
    RfY=pin(parts,"RVFB","1")[1]; CfY=pin(parts,"C1","1")[1]
    power=[]; wires=[]; labels=[]
    add_rail(power,wires,"+5V",pin(parts,"U1","7")); add_rail(power,wires,"GND",pin(parts,"U1","4"))
    add_rail(power,wires,"+5V",pin(parts,"C2","1")); add_rail(power,wires,"GND",pin(parts,"C2","2"))
    # PD: anode (pin2) → −IN summing node ; cathode (pin1) → +5V via RB ; CB bypasses cathode to GND
    anode=pin(parts,"D1","2"); cathode=pin(parts,"D1","1")
    wires += [[anode,(anode[0],nIN[1]),nIN], [pin(parts,"RB","2"),cathode], [cathode,pin(parts,"CB","1")]]
    add_rail(power,wires,"+5V",pin(parts,"RB","1"))
    add_rail(power,wires,"GND",pin(parts,"CB","2"))
    add_stub(wires, labels, anode, "right", "PD_ANODE", dist=10.16)
    cathode_label = pin(parts,"CB","1")
    labels.append(("PD_CATHODE", cathode_label[0], cathode_label[1], "right", "passive", 0.7))
    # feedback: −IN → left rail up ; out → right rail up ; RVFB (Rf trim) ∥ C1 (Cf) bridge across the top
    rvfb_w = pin(parts,"RVFB","2")
    wires += [
        [nIN,(LRX,CfY),(LRX,RfY)],                             # left rail (−IN → Cf row → Rf row ; vertices = endpoints)
        [OUT,(RRX,oy),(RRX,CfY),(RRX,RfY)],                    # right rail (out → Cf row → Rf row)
        [pin(parts,"RVFB","1"),(LRX,RfY)],
        [pin(parts,"RVFB","3"),(RRX,RfY)],
        [rvfb_w,(RRX,rvfb_w[1]),(RRX,RfY)],                   # rheostat: wiper tied to output side
        [pin(parts,"C1","1"),(LRX,CfY)], [pin(parts,"C1","2"),(RRX,CfY)],
        [OUT,(OUT[0]+10.16,oy)],                               # → V_OUT
    ]
    junctions=[nIN,cathode,(LRX,RfY),(LRX,CfY),(RRX,RfY),(RRX,CfY),OUT]
    # VBIAS chain (at +IN level): +5V → RT → RV11 → wiper → R1 → node → C11→GND ; node → +IN
    node=(pin(parts,"C11","1")[0],pIN[1])
    add_rail(power,wires,"+5V",pin(parts,"RT","1")); add_rail(power,wires,"GND",pin(parts,"RV11","3"))
    add_rail(power,wires,"GND",pin(parts,"C11","2"))
    wiper_anchor = snap_point(((pin(parts,"RV11","2")[0] + pin(parts,"R1","1")[0]) / 2, pin(parts,"RV11","2")[1]))
    wires += [[pin(parts,"RT","2"),pin(parts,"RV11","1")],
              [pin(parts,"RV11","2"),wiper_anchor,pin(parts,"R1","1")],
              [pin(parts,"R1","2"),node], [node,pin(parts,"C11","1")], [node,pIN]]
    junctions.append(node)
    add_stub(wires, labels, pin(parts,"RT","2"), "right", "VBIAS_TOP", dist=10.16)
    wiper_label = snap_point((wiper_anchor[0], wiper_anchor[1] + 7.62))
    wires.append([wiper_anchor, wiper_label])
    junctions.append(wiper_anchor)
    labels.append(("VBIAS_WIPER", wiper_label[0], wiper_label[1], "left"))
    add_label(labels, node, "VBIAS", justify="left")
    labels.append(("H:V_OUT",OUT[0]+10.16,oy,"left","output"))
    texts=[
        ("TIA Channel  —  on-board SFH2201 signal PD → OPA380AID transimpedance amp  ·  reused 4× (IR / RED / GREEN / BLUE)",150,104,2.0),
        ("PD reverse-biased: cathode → +5V via RB (1k) + CB bypass ; anode → OPA380 −IN summing node.  Rf = RVFB (2M trim) ∥ Cf = C1 (10pF).",150,110,1.3),
        ("VBIAS: +5V → RT(10k) → RV11 trim → RC(R1,C11) → +IN (held ≤2.5V).  V_OUT = VBIAS ± I_pd·Rf → on-board AD7606-4.",150,116,1.3),
    ]
    color = sheet_name.removeprefix("TIA_")
    opamp_ncs = [pin(parts, "U1", num) for num in ("1", "5", "8")]
    return build_sch_content(
        f"TIA {color} Channel",
        "2026-06-24",
        "v9",
        actualize_parts(sheet_name, parts),
        power,
        wires,
        junctions,
        labels,
        texts,
        mult=1,
        ncs=opamp_ncs,
    )

# ═══ SUB-SHEET: laser_<wavelength>.kicad_sch  (ONE constant-current sink) ═══
def build_laser_driver(sheet_name: str):
    oy=152; ux=210                                  # op-amp center
    laser = LASER_MPN[sheet_name]
    limiter = limiter_for_sheet(sheet_name)
    parts={
        "U11":("TLV9001_SOT23_5","TLV9001",FP_SOT235,"TLV9001IDBVR",LCSC_TLV,ux,oy),
        "LD":(laser["symbol"],laser["value"],laser["footprint"],laser["mpn"],"",315,150),
        "R21":("R_H","10k",FP_R,"CRCW060310K0FKEA",LCSC_10K,172,oy+2.54),
        "R22":("R_V",limiter.value,FP_R,limiter.mpn,limiter.lcsc,198,oy+6.35),
        "C21":("C_V","1uF",FP_402,"HGC0402R5105K250NTEJ",LCSC_1UF,188,oy+13),
        "C22":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,235,oy+16),         # V+ decoupling (open lower-middle)
        "R31":("R_H","1k",FP_R,"FRC0603F1001TS",LCSC_1K,232,oy),
        "Q1":("NMOS","AO3400A",FP_SOT23,"AO3400A",LCSC_NMOS,254,oy),
        "R11":("R_V","10R 2W",FP_R2512,"HoCR2512-2W-10R-1%",LCSC_10R,254,oy+16),   # source sense
        "R12":("R_H","1k",FP_R,"FRC0603F1001TS",LCSC_1K,274,oy+13.46),             # isolates ISENSE tap
        "CC":("C_V","10pF C0G",FP_603,"CC0603JRNPO9BN100",LCSC_10PF,165,oy+15),    # loop comp (FB↔LOUT)
    }
    parts = grid_parts(parts)
    nIN=pin(parts,"U11","4"); pIN=pin(parts,"U11","3"); OUT=pin(parts,"U11","1")
    oy = parts["U11"][6]
    power=[]; wires=[]; labels=[]; ncs=[]
    add_rail(power,wires,"+5V",pin(parts,"U11","5")); add_rail(power,wires,"GND",pin(parts,"U11","2"))
    add_rail(power,wires,"+5V",pin(parts,"C22","1")); add_rail(power,wires,"GND",pin(parts,"C22","2"))
    pnode=(pin(parts,"C21","1")[0],pIN[1])
    wires += [[pin(parts,"R21","2"),pnode,pIN], [pnode,pin(parts,"C21","1")], [pnode,pin(parts,"R22","1")]]
    add_rail(power,wires,"GND",pin(parts,"C21","2"))
    add_rail(power,wires,"GND",pin(parts,"R22","2"))
    lout_anchor = snap_point(((OUT[0] + pin(parts,"R31","1")[0]) / 2, OUT[1]))
    gate_anchor = snap_point(((pin(parts,"R31","2")[0] + pin(parts,"Q1","1")[0]) / 2, pin(parts,"Q1","1")[1]))
    wires += [[OUT,lout_anchor,pin(parts,"R31","1")], [pin(parts,"R31","2"),gate_anchor,pin(parts,"Q1","1")],
              [pin(parts,"Q1","2"),pin(parts,"R11","1")]]
    add_rail(power,wires,"GND",pin(parts,"R11","2"))
    sense=pin(parts,"R11","1")
    wires += [[sense,pin(parts,"R12","1")]]
    junctions=[pnode,sense,OUT]
    add_label(labels, pnode, "CMD_FILTER", justify="left")
    lout_label = snap_point((lout_anchor[0], lout_anchor[1] - 7.62))
    wires.append([lout_anchor, lout_label])
    junctions.append(lout_anchor)
    labels.append(("LOUT", lout_label[0], lout_label[1], "left"))
    gate_label = snap_point((gate_anchor[0], gate_anchor[1] - 7.62))
    wires.append([gate_anchor, gate_label])
    junctions.append(gate_anchor)
    labels.append(("GATE", gate_label[0], gate_label[1], "left"))
    add_stub(wires,labels,pin(parts,"R21","1"),"left","H:PWM_IN",shape="input")
    add_stub(wires,labels,pin(parts,"R12","2"),"right","H:ISENSE",shape="output")
    cN=pin(parts,"Q1","3"); top=snap_point((cN[0],cN[1]-6.35))            # drain -> LASER_N and direct LD cathode
    ld_k=pin(parts,"LD",laser["ld_k"])
    wires.append([cN,top,(ld_k[0],top[1]),ld_k]); labels.append(("H:LASER_N",top[0],top[1],"left","output"))
    add_rail_dn(power,wires,"LASER_VP",pin(parts,"LD",laser["ld_a"]))
    if "mpd" in laser:
        add_stub(wires,labels,pin(parts,"LD",laser["mpd"]),"right","H:MPD_RAW",dist=10,shape="output")
    else:
        ncs.append(pin(parts,"LD",laser["case"]))
    cc_top=pin(parts,"CC","1"); cc_bot=pin(parts,"CC","2")
    fb_x=snap(nIN[0]-8.89); fb_y=snap(OUT[1]-6.35); fb_right=snap(sense[0]+6.35)
    wires.append([nIN,(fb_x,nIN[1]),(fb_x,fb_y),(fb_right,fb_y),(fb_right,sense[1]),sense])
    wires.append([cc_top,(cc_top[0],fb_y),(fb_x,fb_y)])
    labels.append(("FB",fb_x,fb_y,"right"))
    junctions.append((fb_x,fb_y))

    lout_x=snap(OUT[0]+5.08); lout_y=snap(cc_bot[1]+11.43)
    lout_left=snap(cc_bot[0]-7.62)
    wires.append([OUT,(lout_x,OUT[1]),(lout_x,lout_y),(lout_left,lout_y),(lout_left,cc_bot[1]),cc_bot])
    labels.append(("LOUT",lout_x,lout_y,"left"))
    junctions.append((lout_x,OUT[1]))
    texts=[
        ("Laser Driver  —  TLV9001 + AO3400A constant-current sink  ·  I = V_ctrl / 10Ω  ·  reused 4× (IR / RED / GREEN / BLUE)",150,114,2.0),
        (f"PWM_IN → R21/C21 with R22 {limiter.value} → +IN (full-scale ≈{limiter.command_voltage_v:.2f}V, ≈{limiter.command_current_a * 1000.0:.0f}mA) ;  −IN = FB (sense top).",150,120,1.3),
        ("TLV9001 out → R31 → Q1 gate ; source → 10Ω 2W sense → GND.  CC = loop comp (FB↔LOUT, tune in bring-up).",150,125,1.3),
        ("Direct TO-can footprint is the board-mounted laser source connection; no separate laser/MPD harness header is populated.",150,130,1.3),
        ("Digikey-cart MPNs: IR/red are US-Lasers Style-A TO18 monitor cans; green is PLT5 520EB_P TO56 monitor can; blue PLT5 450GB has no monitor PD.",150,135,1.3),
    ]
    color = sheet_name.removeprefix("LASER_")
    return build_sch_content(
        f"Laser {color} Driver",
        "2026-06-24",
        "v9",
        actualize_parts(sheet_name, parts),
        power,
        wires,
        junctions,
        labels,
        texts,
        mult=1,
        ncs=ncs,
    )

# ═══ LEGACY INACTIVE LOCAL MCU GENERATOR ═══
# The active `mcu.kicad_sch` is copied from the access-controller project and
# is not produced by this helper. Keep the helper out of `main()` so the copied
# CP2102N/buttons/discrete-ESD topology is not overwritten.
def build_mcu():
    # ESP32 centered on page (A3=420x297), large 91x81mm symbol needs room
    ex,ey = 230, 180
    # Left-side components (power + USB + UART) well clear of ESP32 left edge (ex-46 = 184)
    lx = 60   # left column x
    parts={
        "U9":("Espressif:ESP32-S3-WROOM-1","ESP32-S3-WROOM-1",FP_ESP32S3,"ESP32-S3-WROOM-1-N16",LCSC_ESP,ex,ey),
        # Power zone (top-left corner)
        "U10":("LDO5","AP2112K-3.3",FP_SOT235,"AP2112K-3.3TRG1",LCSC_LDO,lx+20,90),
        "C44":("C_V","1uF",FP_402,"HGC0402R5105K250NTEJ",LCSC_1UF,lx,90),
        "C41":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,lx+40,90),
        "C42":("C_V","10uF",FP_805,"CL21A106KAYNNNG",LCSC_10UF,lx+55,90),
        # USB zone (mid-left)
        "J6":("USB_MINIB","USB Mini-B",FP_USB,"920-462A2021S10101",LCSC_USB,lx,160),
        "U12":("ESD_USB","USBLC6",FP_SOT236,"USBLC6-2SC6",LCSC_ESD,lx+60,160),
        "RUSBM":("R_H","22R USB",FP_R,"0603WAF220JT5E",LCSC_22R,lx+96,157.46),
        "RUSBP":("R_H","22R USB",FP_R,"0603WAF220JT5E",LCSC_22R,lx+96,162.54),
        # UART (bottom-left)
        "J3":("CONN5","UART->Pi",FP_H5,"","",lx,230),
        # EN network (between LDO and ESP32, clear of symbol)
        "REN":("R_V","10k",FP_R,"CRCW060310K0FKEA",LCSC_10K,lx+80,100),
        "CEN":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,lx+100,100),
        "RBOOT":("R_V","10k BOOT",FP_R,"CRCW060310K0FKEA",LCSC_10K,lx+120,100),
        # ESP VDD decoupling (near ESP32 top)
        "C43":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,ex-20,ey-55),
    }
    parts = grid_parts(parts)
    power=[]; wires=[]; labels=[]; ncs=[]
    # ── LDO: 5V→3V3 ──
    add_rail(power,wires,"+5V",pin(parts,"U10","1")); add_rail(power,wires,"+5V",pin(parts,"U10","3"))
    add_rail(power,wires,"GND",pin(parts,"U10","2")); add_rail(power,wires,"+3V3",pin(parts,"U10","5"))
    ncs.append(pin(parts,"U10","4"))
    add_rail(power,wires,"+5V",pin(parts,"C44","1")); add_rail(power,wires,"GND",pin(parts,"C44","2"))
    for c in ("C41","C42","C43"):
        add_rail(power,wires,"+3V3",pin(parts,c,"1")); add_rail(power,wires,"GND",pin(parts,c,"2"))
    # ── EN pull-up + POR cap ──
    add_rail(power,wires,"+3V3",pin(parts,"REN","1"))
    ren_en = pin(parts,"REN","2")
    ren_en_label = (ren_en[0], round(ren_en[1]+8,4))
    wires.append([ren_en, ren_en_label])
    add_label(labels,ren_en_label,"ESP_EN",justify="left")
    cen_en = pin(parts,"CEN","1")
    cen_en_label = (cen_en[0], round(cen_en[1]-8,4))
    wires.append([cen_en, cen_en_label])
    add_label(labels,cen_en_label,"ESP_EN",justify="left")
    add_rail(power,wires,"GND",pin(parts,"CEN","2"))
    add_rail(power,wires,"+3V3",pin(parts,"RBOOT","1"))
    boot = pin(parts,"RBOOT","2")
    boot_label = (boot[0], round(boot[1]+8,4))
    wires.append([boot, boot_label])
    add_label(labels,boot_label,"ESP_BOOT",justify="left")
    # ── ESP32 power ──
    add_rail(power,wires,"+3V3",pin(parts,"U9",ESP_PIN["VDD3P3"]))
    add_rail(power,wires,"GND",pin(parts,"U9",ESP_PIN["GND"]))
    # ── USB: J6 → USBLC6 ESD → 22R series resistors → ESP32 native USB ──
    add_stub(wires,labels,pin(parts,"J6","2"),"left","USB_DM_CONN",dist=10)
    add_stub(wires,labels,pin(parts,"U12","1"),"left","USB_DM_CONN",dist=8)
    usb_dm_esd = pin(parts,"U12","6")
    usb_dm_r = pin(parts,"RUSBM","1")
    wires.append([usb_dm_esd, usb_dm_r])
    add_label(labels,(usb_dm_esd[0]+2, usb_dm_esd[1]),"USB_DM_ESD",justify="left")
    add_stub(wires,labels,pin(parts,"RUSBM","2"),"right","USB_DM",dist=6)
    add_stub(wires,labels,pin(parts,"U9",ESP_PIN["USB_DM"]),"right","USB_DM",dist=18)
    add_stub(wires,labels,pin(parts,"J6","3"),"left","USB_DP_CONN",dist=10)
    add_stub(wires,labels,pin(parts,"U12","3"),"left","USB_DP_CONN",dist=8)
    usb_dp_esd = pin(parts,"U12","4")
    usb_dp_r = pin(parts,"RUSBP","1")
    wires.append([usb_dp_esd, usb_dp_r])
    add_label(labels,(usb_dp_esd[0]+2, usb_dp_esd[1]),"USB_DP_ESD",justify="left")
    add_stub(wires,labels,pin(parts,"RUSBP","2"),"right","USB_DP",dist=6)
    add_stub(wires,labels,pin(parts,"U9",ESP_PIN["USB_DP"]),"right","USB_DP",dist=18)
    # ── VBUS ──
    mjunc=[]
    jv=pin(parts,"J6","1"); ev=pin(parts,"U12","5")
    vy=ev[1]-8; vtap=(round((jv[0]+ev[0])/2,4),vy)
    wires.append([(jv[0]-8,vy),(jv[0],vy)])
    wires.append([jv,(jv[0],vy),(ev[0],vy),ev])
    labels.append(("H:VBUS_5V",jv[0]-8,vy,"right","output"))
    power.append(("PWR_FLAG",vtap[0],vy-5)); wires.append([vtap,(vtap[0],vy-5)]); mjunc.append(vtap)
    # USB grounds
    add_rail(power,wires,"GND",pin(parts,"J6","5")); add_rail(power,wires,"GND",pin(parts,"J6","6"))
    add_rail(power,wires,"GND",pin(parts,"U12","2"))
    ncs.append(pin(parts,"J6","4"))
    # ── UART J3 ↔ ESP32 (left-side pins, use long left stubs) ──
    j3=[("1","ESP_TX","U0TXD"),("2","ESP_RX","U0RXD"),("3","ESP_EN","EN"),("4","ESP_BOOT","BOOT"),("5","GND",None)]
    for jp,net,epin in j3:
        if net=="GND":
            add_rail(power,wires,"GND",pin(parts,"J3",jp))
        else:
            add_stub(wires,labels,pin(parts,"J3",jp),"left",net,dist=10)
            esp_pin = pin(parts,"U9",ESP_PIN[epin])
            if epin == "EN":
                add_bent_label(
                    wires,
                    labels,
                    esp_pin,
                    [(174, esp_pin[1]), (174, 132), (166, 132)],
                    net,
                    justify="right",
                )
            else:
                add_stub(wires,labels,esp_pin,"right",net,dist=18)
    # ── ESP32 right-side hierarchical pins (long stubs to clear symbol) ──
    bench_signal_names = [f"PWM{i+1}" for i in range(4)]+[f"ISENSE{i+1}" for i in range(4)]+[f"MPD{i+1}" for i in range(4)]+["CONVST"]
    bench_signal_shapes = {
        **{f"PWM{i+1}": "output" for i in range(4)},
        **{f"ISENSE{i+1}": "input" for i in range(4)},
        **{f"MPD{i+1}": "input" for i in range(4)},
        "CONVST": "output",
    }
    for nm in bench_signal_names:
        pin_num = ESP_PIN[nm]
        esp_pin = pin(parts,"U9",pin_num)
        if nm == "PWM1":
            add_bent_label(
                wires,
                labels,
                esp_pin,
                [(174, esp_pin[1]), (174, 136), (150, 136)],
                f"H:{nm}",
                justify="right",
                shape=bench_signal_shapes[nm],
            )
            continue
        side = "left" if SYM["Espressif:ESP32-S3-WROOM-1"]["pins"][pin_num][0] < 0 else "right"
        add_stub(wires,labels,esp_pin,side,f"H:{nm}",dist=30,shape=bench_signal_shapes[nm])
    used_esp_pins = {
        ESP_PIN["GND"], ESP_PIN["VDD3P3"], ESP_PIN["EN"], ESP_PIN["BOOT"],
        ESP_PIN["U0TXD"], ESP_PIN["U0RXD"], ESP_PIN["USB_DM"], ESP_PIN["USB_DP"],
        "40", "41",
    } | {ESP_PIN[nm] for nm in bench_signal_names}
    for pin_num in sorted(set(SYM["Espressif:ESP32-S3-WROOM-1"]["pins"]) - used_esp_pins, key=lambda s: int(s)):
        ncs.append(pin(parts,"U9",pin_num))
    texts=[
        ("Microcontroller — ESP32-S3-WROOM-1 (2.4GHz Wi-Fi b/g/n + Bluetooth LE + native USB) + USB Mini-B + AP2112K-3.3 LDO",30,50,2.2),
        ("USB Mini-B entries use copied-sheet discrete LESD clamps and 1N5819HW VBUS isolation; native USB D+=GPIO20, D−=GPIO19.",30,56,1.3),
        ("PWM1-4 -> GPIO10/11/12/16. ISENSE1-4 -> GPIO4/5/6/7.",30,62,1.3),
        ("MPD1-4 -> GPIO2/3/8/9. CONVST -> GPIO15. UART/EN/BOOT follow the copied MCU sheet.",30,68,1.3),
        ("EN pulled up (REN=10k→+3V3) + POR cap (CEN=100nF). GPIO0/BOOT pulled up and exposed on J2. LDO: AP2112K-3.3, 5V→3V3.",30,74,1.3),
    ]
    return build_sch_content(
        "Microcontroller",
        "2026-06-24",
        "v9",
        actualize_parts("MCU_ESP32-S3", parts),
        power,
        wires,
        mjunc,
        labels,
        texts,
        mult=1,
        ncs=ncs,
    )

# ═══ SUB-SHEET: power_io.kicad_sch ═══
def build_power_io():
    def px(x): return 30 + x * 1.25
    def py(y): return 20 + y * 1.25
    def ppt(x, y): return snap_point((px(x), py(y)))
    def pparts(raw_parts):
        return {
            ref: (sym, val, fp, mpn, lcsc, px(x), py(y))
            for ref, (sym, val, fp, mpn, lcsc, x, y) in raw_parts.items()
        }

    parts={
        "JDC":("BARREL_JACK_SWITCH","24V DC IN",FP_BARREL,"DC-470-2.1GP",LCSC_BARREL,42,56),
        "JRJ45":("open_automation:CONN_RJ45","CONN_RJ45",FP_RJ45,"R-RJ45R08P-C000",LCSC_RJ45,42,84),
        "RJR45PWR":("R_H_RJ45","10K",FP_R,"CRCW060310K0FKEA",LCSC_10K,24.13,76.2),
        "RJR45LED":("R_H_RJ45","10K",FP_R,"CRCW060310K0FKEA",LCSC_10K,24.13,91.44),
        "CIN24A":("C_V","10uF 50V",FP_1206,"CL31B106KBHNNNE",LCSC_10UF_50V,68,52),
        "CIN24B":("C_V","10uF 50V",FP_1206,"CL31B106KBHNNNE",LCSC_10UF_50V,80,52),
        "CIN24BULK":("C_POL_V","22uF 100V",FP_CELEC_8X10,"100CE22FS+P",LCSC_22UF_100V,92,52),
        "U5V":("AP6320X_TSOT6","AP63205WU-7 5V BUCK",FP_TSOT236,"AP63205WU-7",LCSC_AP63205,105,60),
        "L5V":("L_H","4.7uH",FP_IND_4R7,"MWSA0503S-4R7MT",LCSC_L4R7,136,54),
        "CBST5V":("C_V","100nF BST",FP_402,"0402B104K160CT",LCSC_100NF,124,57),
        "C5VOUT1":("C_V","22uF 5V buck",FP_805,"CL21A226MAQNNNE",LCSC_22UF_25V,156,42),
        "C5VOUT2":("C_V","22uF 5V buck",FP_805,"CL21A226MAQNNNE",LCSC_22UF_25V,168,42),
        "D10":("SCHOTTKY","SS14",FP_SMA,"SS14",LCSC_SCH,205,72),
        "D11":("SCHOTTKY","SS14",FP_SMA,"SS14",LCSC_SCH,205,54),
        "C50":("C_V","10uF +5V bulk",FP_805,"CL21A106KAYNNNG",LCSC_10UF,225,64),
        "U3V3":("LDO5","AP2112K-3.3",FP_SOT235,"AP2112K-3.3TRG1",LCSC_LDO,250,64),
        "C3V3IN":("C_V","1uF",FP_402,"HGC0402R5105K250NTEJ",LCSC_1UF,238,64),
        "C3V3OUT":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,268,60),
        "C3V3BULK":("C_V","10uF",FP_805,"CL21A106KAYNNNG",LCSC_10UF,282,60),
        "ULASER":("AP6320X_TSOT6","AP63200WU-7 9.3V BUCK",FP_TSOT236,"AP63200WU-7",LCSC_AP63200,105,90),
        "LLASER":("L_H","10uH",FP_IND_10,"WPN4020H100MT",LCSC_L10UH,136,84),
        "CBSTLASER":("C_V","100nF BST",FP_402,"0402B104K160CT",LCSC_100NF,124,87),
        "CLASEROUT1":("C_V","22uF laser buck",FP_805,"CL21A226MAQNNNE",LCSC_22UF_25V,148,84),
        "CLASEROUT2":("C_V","22uF laser buck",FP_805,"CL21A226MAQNNNE",LCSC_22UF_25V,160,84),
        "RFBTOP":("R_V","237k FB",FP_R,"FRC0603F2373TS",LCSC_237K,190,90),
        "RFBBOT":("R_V","22.1K FB",FP_R0402,"FRC0402F2212TS",LCSC_221K,190,106),
        "CFFLASER":("C_V","100pF FF",FP_402,"0402CG101J500NT",LCSC_100PF,202,90),
        "UADC":("AD7606_4","AD7606BSTZ-4",FP_AD7606,"AD7606BSTZ-4RL",LCSC_AD7606,250,205),
        "CADCAV1":("C_V","100nF ADC AVCC",FP_402,"0402B104K160CT",LCSC_100NF,220,158),
        "CADCAV2":("C_V","100nF ADC AVCC",FP_402,"0402B104K160CT",LCSC_100NF,235,158),
        "CADCAV3":("C_V","100nF ADC AVCC",FP_402,"0402B104K160CT",LCSC_100NF,250,158),
        "CADCAV4":("C_V","100nF ADC AVCC",FP_402,"0402B104K160CT",LCSC_100NF,265,158),
        # Keep this off UADC pin 7's x-coordinate so the decoupler GND stub
        # cannot merge with the STBY high strap in the generated schematic.
        "CADCDRV":("C_V","100nF ADC VDRIVE",FP_402,"0402B104K160CT",LCSC_100NF,285,158),
        "CADCBULK":("C_V","10uF ADC AVCC",FP_805,"CL21A106KAYNNNG",LCSC_10UF,205,158),
        "CREG1":("C_V","1uF ADC REGCAP",FP_402,"HGC0402R5105K250NTEJ",LCSC_1UF,205,215),
        "CREG2":("C_V","1uF ADC REGCAP",FP_402,"HGC0402R5105K250NTEJ",LCSC_1UF,195,220),
        "CREFIN":("C_V","10uF ADC REF",FP_805,"CL21A106KAYNNNG",LCSC_10UF,185,225),
        "CREFCAP":("C_V","10uF ADC REFCAP",FP_805,"CL21A106KAYNNNG",LCSC_10UF,175,230),
        "UMPD":("INA4180_TSSOP14","INA4180A1",FP_TSSOP14,"INA4180A1IPWR",LCSC_INA4180,178,132),
        "UREF":("LM4040_DBZ","LM4040C50 5V",FP_SOT23,"LM4040C50IDBZR",LCSC_LM4040,114,122),
        "CINA":("C_V","100nF",FP_402,"0402B104K160CT",LCSC_100NF,172,88),
        "CREF":("C_V","100nF MPD bias",FP_402,"0402B104K160CT",LCSC_100NF,128,122),
        "RBIAS":("R_V","2.49k MPD bias",FP_R,"0603WAF2491T5E",LCSC_249K,132,146),
    }
    for i in range(4):
        sense_y = 110 + i*12
        adc_y = 114 + i*12
        parts[f"RMPD{i+1}"] = ("R_H","240R MPD sense",FP_R,"RTT032400FTP",LCSC_240R,236,sense_y)
        parts[f"RADC{i+1}"] = ("R_H","1k ADC",FP_R,"FRC0603F1001TS",LCSC_1K,288,adc_y)
        parts[f"CMPD{i+1}"] = ("C_V","100nF MPD ADC",FP_402,"0402B104K160CT",LCSC_100NF,306,adc_y+2.54)
    parts = grid_parts(pparts(parts))
    power=[]; wires=[]; labels=[]; ncs=[]; junctions=[]
    # 24V barrel/RJ45 input and onboard 5V buck. USB VBUS remains an optional OR-ed 5V source.
    add_rail(power,wires,"VIN_24V",pin(parts,"JDC","1"))
    add_bus_rail(
        power,
        wires,
        "GND",
        [pin(parts,"JDC","2"), pin(parts,"JDC","3")],
        bus_y=py(64),
        symbol_at=ppt(50,69),
    )
    add_bus_rail(
        power,
        wires,
        "VIN_24V",
        [pin(parts,"JRJ45","4"), pin(parts,"JRJ45","5")],
        bus_x=px(60),
        symbol_at=ppt(65,84),
    )
    rj45_gnd_right = [pin(parts,"JRJ45",rj45_pin) for rj45_pin in ["7","8"]]
    rj45_gnd_left = [pin(parts,"JRJ45",rj45_pin) for rj45_pin in ["9","11"]]
    rj45_gnd_left_x, rj45_gnd_right_x = snap(px(14)), snap(px(60))
    rj45_gnd_y = snap(py(99))
    for point in rj45_gnd_left:
        wires.append([point, (rj45_gnd_left_x, point[1])])
    for point in rj45_gnd_right:
        wires.append([point, (rj45_gnd_right_x, point[1])])
    wires.append([(rj45_gnd_left_x, y) for y in sorted({p[1] for p in rj45_gnd_left} | {rj45_gnd_y})])
    wires.append([(rj45_gnd_right_x, y) for y in sorted({p[1] for p in rj45_gnd_right} | {rj45_gnd_y})])
    rj45_gnd_symbol = ppt(42, 104)
    wires.append([(rj45_gnd_left_x, rj45_gnd_y), (rj45_gnd_symbol[0], rj45_gnd_y)])
    wires.append([(rj45_gnd_symbol[0], rj45_gnd_y), (rj45_gnd_right_x, rj45_gnd_y)])
    wires.append([(rj45_gnd_symbol[0], rj45_gnd_y), rj45_gnd_symbol])
    power.append(("GND", rj45_gnd_symbol[0], rj45_gnd_symbol[1]))
    junctions.extend([
        (rj45_gnd_left_x, rj45_gnd_y),
        (rj45_gnd_right_x, rj45_gnd_y),
        (rj45_gnd_symbol[0], rj45_gnd_y),
    ])
    rj45_pwr_label_anchor = snap_point(((pin(parts,"RJR45PWR","2")[0] + pin(parts,"JRJ45","10")[0]) / 2, pin(parts,"RJR45PWR","2")[1]))
    wires.append([pin(parts,"RJR45PWR","2"), rj45_pwr_label_anchor, pin(parts,"JRJ45","10")])
    rj45_pwr_label = snap_point((rj45_pwr_label_anchor[0], rj45_pwr_label_anchor[1] - 5.08))
    wires.append([rj45_pwr_label_anchor, rj45_pwr_label])
    junctions.append(rj45_pwr_label_anchor)
    labels.append(("RJ45_PWR_DETECT", rj45_pwr_label[0], rj45_pwr_label[1], "right"))
    rj45_led_label_anchor = snap_point(((pin(parts,"RJR45LED","2")[0] + pin(parts,"JRJ45","12")[0]) / 2, pin(parts,"RJR45LED","2")[1]))
    wires.append([pin(parts,"RJR45LED","2"), rj45_led_label_anchor, pin(parts,"JRJ45","12")])
    rj45_led_label = snap_point((rj45_led_label_anchor[0], rj45_led_label_anchor[1] + 10.16))
    wires.append([rj45_led_label_anchor, rj45_led_label])
    junctions.append(rj45_led_label_anchor)
    labels.append(("RJ45_LED_CONTACT", rj45_led_label[0], rj45_led_label[1], "right"))
    rj45_pwr_tap = ppt(20.32, 69.85)
    rj45_led_tap = ppt(20.32, 86.36)
    wires.append([pin(parts,"RJR45PWR","1"), rj45_pwr_tap])
    wires.append([pin(parts,"RJR45LED","1"), rj45_led_tap])
    power.append(("VIN_24V", rj45_pwr_tap[0], rj45_pwr_tap[1]))
    power.append(("+3V3", rj45_led_tap[0], rj45_led_tap[1]))
    for rj45_pin in ["1","2","3","6"]:
        ncs.append(pin(parts,"JRJ45",rj45_pin))
    for cap in ["CIN24A","CIN24B","CIN24BULK"]:
        add_rail(power,wires,"VIN_24V",pin(parts,cap,"1"))
        add_rail(power,wires,"GND",pin(parts,cap,"2"))

    add_rail(power,wires,"VIN_24V",pin(parts,"U5V","3"))
    add_rail(power,wires,"VIN_24V",pin(parts,"U5V","2"))
    add_rail(power,wires,"GND",pin(parts,"U5V","4"))
    wires.append([pin(parts,"U5V","5"), pin(parts,"L5V","1")])
    wires.append([pin(parts,"U5V","5"), pin(parts,"CBST5V","1")])
    wires.append([pin(parts,"U5V","6"), pin(parts,"CBST5V","2")])
    add_label(labels, pin(parts,"U5V","5"), "BUCK5_SW", justify="left")
    add_label(labels, pin(parts,"U5V","6"), "BUCK5_BST", justify="left")
    l5v_out = pin(parts,"L5V","2")
    add_bent_label(wires,labels,l5v_out,[(l5v_out[0],py(47)),ppt(145,47)],"BUCK_5V",justify="right")
    add_stub(wires,labels,pin(parts,"U5V","1"),"right","BUCK_5V",dist=12)
    add_stub(wires,labels,pin(parts,"D11","1"),"left","BUCK_5V",dist=12)
    buck5_bus_y = snap(py(32))
    buck5_bus_left = ppt(148, 32)
    buck5_bus_points = [buck5_bus_left]
    for cap in ["C5VOUT1","C5VOUT2"]:
        cap_top = pin(parts,cap,"1")
        cap_bus = snap_point((cap_top[0], buck5_bus_y))
        wires.append([cap_top, cap_bus])
        buck5_bus_points.append(cap_bus)
        add_rail(power,wires,"GND",pin(parts,cap,"2"))
    wires.append(buck5_bus_points)
    add_label(labels, buck5_bus_left, "BUCK_5V", justify="right")

    add_stub(wires,labels,pin(parts,"D10","1"),"left","H:VBUS_5V",shape="input")
    add_rail(power,wires,"+5V",pin(parts,"D10","2"))
    add_rail(power,wires,"+5V",pin(parts,"D11","2"))
    add_rail(power,wires,"+5V",pin(parts,"C50","1")); add_rail(power,wires,"GND",pin(parts,"C50","2"))
    # Board 3V3 source for the imported access-controller MCU sheet.
    add_rail(power,wires,"+5V",pin(parts,"U3V3","1"))
    add_rail(power,wires,"+5V",pin(parts,"U3V3","3"))
    add_rail(power,wires,"GND",pin(parts,"U3V3","2"))
    add_rail(power,wires,"+3V3",pin(parts,"U3V3","5"))
    ncs.append(pin(parts,"U3V3","4"))
    add_rail(power,wires,"+5V",pin(parts,"C3V3IN","1"))
    add_rail(power,wires,"GND",pin(parts,"C3V3IN","2"))
    add_rail(power,wires,"+3V3",pin(parts,"C3V3OUT","1"))
    add_rail(power,wires,"GND",pin(parts,"C3V3OUT","2"))
    add_rail(power,wires,"+3V3",pin(parts,"C3V3BULK","1"))
    add_rail(power,wires,"GND",pin(parts,"C3V3BULK","2"))
    # Shared bench laser rail: AP63200 adjustable buck, set near 9.3V by 237k/22.1k.
    add_rail(power,wires,"VIN_24V",pin(parts,"ULASER","3"))
    add_rail(power,wires,"VIN_24V",pin(parts,"ULASER","2"))
    add_rail(power,wires,"GND",pin(parts,"ULASER","4"))
    wires.append([pin(parts,"ULASER","5"), pin(parts,"LLASER","1")])
    wires.append([pin(parts,"ULASER","5"), pin(parts,"CBSTLASER","1")])
    wires.append([pin(parts,"ULASER","6"), pin(parts,"CBSTLASER","2")])
    add_label(labels, pin(parts,"ULASER","5"), "LASER_BUCK_SW", justify="left")
    add_label(labels, pin(parts,"ULASER","6"), "LASER_BUCK_BST", justify="left")
    add_rail(power,wires,"LASER_VP",pin(parts,"LLASER","2"))
    for cap in ["CLASEROUT1","CLASEROUT2"]:
        add_rail(power,wires,"LASER_VP",pin(parts,cap,"1"))
        add_rail(power,wires,"GND",pin(parts,cap,"2"))
    fb_node = pin(parts,"RFBBOT","1")
    wires.append([pin(parts,"ULASER","1"), fb_node])
    wires.append([pin(parts,"RFBTOP","2"), fb_node])
    wires.append([pin(parts,"CFFLASER","2"), fb_node])
    add_label(labels, fb_node, "LASER_BUCK_FB", justify="left")
    add_rail(power,wires,"LASER_VP",pin(parts,"RFBTOP","1"))
    add_rail(power,wires,"LASER_VP",pin(parts,"CFFLASER","1"))
    add_rail(power,wires,"GND",pin(parts,"RFBBOT","2"))
    # On-board AD7606-4: four OPA380 TIA outputs into V1/V2/V3/V4, serial data back to ESP32.
    adc_input_pins = {"VOUT1":"49", "VOUT2":"51", "VOUT3":"57", "VOUT4":"59"}
    for net, adc_pin in adc_input_pins.items():
        add_stub(wires,labels,pin(parts,"UADC",adc_pin),"left",f"H:{net}",dist=10,shape="input")
    conv_a = pin(parts,"UADC","9")
    conv_b = pin(parts,"UADC","10")
    conv_bus = (conv_a[0]+8.89, conv_a[1])
    wires.append([conv_a, conv_bus, (conv_bus[0], conv_b[1]), conv_b])
    add_label(labels,conv_bus,"H:CONVST",justify="left",shape="input")
    for adc_pin, net, shape in [
        ("11","ADC_RESET","input"),
        ("12","ADC_SCLK","input"),
        ("13","ADC_CS","input"),
        ("14","ADC_BUSY","output"),
        ("24","ADC_MISO_A","output"),
        ("25","ADC_MISO_B","output"),
    ]:
        add_stub(wires,labels,pin(parts,"UADC",adc_pin),"right",f"H:{net}",dist=10,shape=shape)
    ncs.append(pin(parts,"UADC","15"))
    add_bus_rail(
        power,
        wires,
        "+5V",
        [pin(parts,"UADC",adc_pin) for adc_pin in ["1","37","38","48"]]
        + [pin(parts,cap,"1") for cap in ["CADCBULK","CADCAV1","CADCAV2","CADCAV3","CADCAV4"]],
        bus_y=py(155),
        symbol_at=ppt(235,150),
    )
    add_bus_rail(
        power,
        wires,
        "+3V3",
        [pin(parts,"UADC",adc_pin) for adc_pin in ["6","7","23"]],
        bus_y=py(174),
        symbol_at=ppt(268,169),
    )
    add_rail(power,wires,"+3V3",pin(parts,"UADC","34"))
    add_bus_rail(
        power,
        wires,
        "GND",
        [pin(parts,"UADC",adc_pin) for adc_pin in [
            "3","4","5","8","16","17","18","19","20","21","22","27","28","29","30","31","32","33",
            "2","26","35","40","41","43","46","47","50","52","53","54","55","56","58","60","61","62","63","64",
        ]],
        bus_y=py(247),
        symbol_at=ppt(250,254),
    )
    cadcdrv_top = pin(parts,"CADCDRV","1")
    cadcdrv_3v3 = snap_point((cadcdrv_top[0] + 7.62, cadcdrv_top[1]))
    wires.append([cadcdrv_top, cadcdrv_3v3])
    power.append(("+3V3", cadcdrv_3v3[0], cadcdrv_3v3[1]))
    add_bus_rail(
        power,
        wires,
        "GND",
        [pin(parts,cap,"2") for cap in ["CADCBULK","CADCAV1","CADCAV2","CADCAV3","CADCAV4","CADCDRV"]],
        bus_y=py(166),
        symbol_at=ppt(245,171),
    )
    for cap, adc_pin in [("CREG1","36"),("CREG2","39"),("CREFIN","42")]:
        cap_top = pin(parts,cap,"1")
        adc_ref_pin = pin(parts,"UADC",adc_pin)
        jog = (adc_ref_pin[0] - 8.89, adc_ref_pin[1])
        wires.append([adc_ref_pin, jog, (jog[0], cap_top[1]), cap_top])
        add_stub(wires, labels, cap_top, "left", f"ADC_{cap}", dist=10.16)
        add_rail(power,wires,"GND",pin(parts,cap,"2"))
    refcap_top = pin(parts,"CREFCAP","1")
    refcap_a = pin(parts,"UADC","44")
    refcap_b = pin(parts,"UADC","45")
    refcap_jog = (refcap_a[0] - 8.89, refcap_a[1])
    wires.append([refcap_a, refcap_jog, (refcap_jog[0], refcap_b[1]), refcap_b])
    wires.append([refcap_jog, (refcap_jog[0], refcap_top[1]), refcap_top])
    add_stub(wires, labels, refcap_top, "left", "ADC_REFCAP", dist=10.16)
    add_rail(power,wires,"GND",pin(parts,"CREFCAP","2"))
    # monitor PD telemetry: hold PD cathode-to-anode bias near 5V, sense monitor current high-side,
    # then feed a low-impedance filtered voltage into the ESP32 ADC.
    add_rail(power,wires,"+3V3",pin(parts,"UMPD","4"))
    add_rail(power,wires,"GND",pin(parts,"UMPD","11"))
    add_rail(power,wires,"+3V3",pin(parts,"CINA","1"))
    add_rail(power,wires,"GND",pin(parts,"CINA","2"))
    add_rail(power,wires,"LASER_VP",pin(parts,"UREF","1"))
    uref_anode = pin(parts,"UREF","2")
    uref_star = pin(parts,"UREF","3")
    wires.append([uref_anode, uref_star])
    add_stub(wires,labels,uref_anode,"left","MPD_BIAS",dist=10)
    add_rail(power,wires,"LASER_VP",pin(parts,"CREF","1"))
    cref_bias = pin(parts,"CREF","2")
    cref_label = (cref_bias[0], round(cref_bias[1]+8,4))
    wires.append([cref_bias, cref_label])
    labels.append(("MPD_BIAS", cref_label[0], cref_label[1], "left"))
    add_stub(wires,labels,pin(parts,"RBIAS","1"),"left","MPD_BIAS",dist=10)
    add_rail(power,wires,"GND",pin(parts,"RBIAS","2"))

    ina_in_plus = {1:"3", 2:"5", 3:"10", 4:"12"}
    ina_in_minus = {1:"2", 2:"6", 3:"9", 4:"13"}
    ina_out = {1:"1", 2:"7", 3:"8", 4:"14"}
    for i in range(1,5):
        raw = f"MPD_RAW{i}"
        amp = f"MPD_AMP{i}"
        add_stub(wires,labels,pin(parts,f"RMPD{i}","1"),"left",f"H:{raw}",dist=14,shape="input")
        add_stub(wires,labels,pin(parts,f"RMPD{i}","2"),"right","MPD_BIAS",dist=11)
        add_stub(wires,labels,pin(parts,"UMPD",ina_in_plus[i]),"left",f"H:{raw}",dist=8.89,shape="input")
        add_stub(wires,labels,pin(parts,"UMPD",ina_in_minus[i]),"left","MPD_BIAS",dist=8.89)
        add_stub(wires,labels,pin(parts,"UMPD",ina_out[i]),"right",amp,dist=12)
        add_stub(wires,labels,pin(parts,f"RADC{i}","1"),"left",amp,dist=12)
        radc_out = pin(parts,f"RADC{i}","2")
        cmpd_top = pin(parts,f"CMPD{i}","1")
        mpd_label = (cmpd_top[0] + 10, cmpd_top[1])
        wires.append([radc_out, cmpd_top, mpd_label])
        add_label(labels,mpd_label,f"H:MPD{i}",justify="left",shape="output")
    add_bus_rail(
        power,
        wires,
        "GND",
        [pin(parts,f"CMPD{i}","2") for i in range(1,5)],
        bus_x=px(322),
        symbol_at=ppt(327,142),
    )
    # PWR_FLAGs — declare real external/generated rails as sources (silences ERC)
    declare_source(power,wires,"VIN_24V",px(42),py(150))
    declare_source(power,wires,"+5V",px(60),py(150))
    declare_source(power,wires,"GND",px(78),py(150))
    declare_source(power,wires,"LASER_VP",px(96),py(150))
    da=pin(parts,"D10","1")                         # D10 anode = VBUS_5V net
    power.append(("PWR_FLAG",da[0],da[1]+9)); wires.append([da,(da[0],da[1]+9)]); junctions.append(da)
    db=pin(parts,"D11","1")                         # D11 anode = onboard AP63205 5V buck output
    power.append(("PWR_FLAG",db[0],db[1]-9)); wires.append([db,(db[0],db[1]-9)]); junctions.append(db)
    texts=[
        ("Power & I/O  -  24V barrel/RJ45 input, onboard AP63205 +5V buck, AP63200 laser buck, AD7606-4 ADC, monitor-PD front end",px(36),py(8),2.0),
        ("Inputs: J5 barrel center and J6 pins 4/5 -> VIN_24V; J5 sleeve/switch and J6 pins 7/8/9/11 -> GND.",px(36),py(14),1.2),
        ("RJ45: copied access-controller CONN_RJ45 symbol; J6 pins 10/12 use 10k LED/contact resistors to VIN_24V/+3V3.",px(36),py(20),1.2),
        ("Supplies: U15 AP63205 -> BUCK_5V/+5V, U16 AP63200 -> LASER_V+ ~=9.3V; raw 24V stays off laser anodes.",px(36),py(26),1.2),
    ]
    return build_sch_content(
        "Power & IO",
        "2026-06-24",
        "v9",
        actualize_parts("POWER_IO", parts),
        power,
        wires,
        junctions,
        labels,
        texts,
        mult=1,
        ncs=ncs,
        paper="A2",
    )

# ═══ ROOT SHEET: laser_controller.kicad_sch ═══
def gl(name,x,y,j):
    ang = 180 if j=="right" else 0
    x, y = snap(x), snap(y)
    return f'  (global_label "{name}" (shape bidirectional) (at {fmt(x)} {fmt(y)} {ang}) (effects (font (size 1.27 1.27)) (justify {j})) (uuid {uid()}))'

def build_root():
    P=["(kicad_sch","  (version 20230121)","  (generator eeschema)",f"  (uuid {ROOT_UUID})",
       '  (paper "A2")',"  (title_block",
       '    (title "Laser Controller")',
       '    (date "2026-06-24")','    (rev "v9")','    (company "Vivonics")',"  )"]
    P.append("  (lib_symbols")
    for name in ("GND", "MOUNTING_HOLE_PAD"):
        P.append(sym_def(name))
    P.append("  )")
    extra=[]
    def sheet(name,file,sx,sy,w,h,pins,fontsz=1.4,pps=7):
        sx, sy, w, h = snap(sx), snap(sy), snap(w), snap(h)
        pps = snap(pps)
        P.append(f"  (sheet (at {fmt(sx)} {fmt(sy)}) (size {fmt(w)} {fmt(h)}) (stroke (width 0.254) (type solid)) (fill (color 0 0 0 0.0))")
        P.append(f"    (uuid {uid()})")
        P.append(f'    (property "Sheetname" "{name}" (at {fmt(sx)} {fmt(sy-3)} 0) (effects (font (size {fontsz} {fontsz})) (justify left bottom)))')
        P.append(f'    (property "Sheetfile" "{file}" (at {fmt(sx)} {fmt(sy+h+4)} 0) (effects (font (size 1.0 1.0)) (justify left top)))')
        lefts=[p for p in pins if p[2]=="left"]; rights=[p for p in pins if p[2]=="right"]
        for grp,side in ((lefts,"left"),(rights,"right")):
            for i,(pn,pin_type,_,net) in enumerate(grp):
                px = sx if side=="left" else sx+w
                py = snap(sy+7.62+i*pps)
                ang = 180 if side=="left" else 0
                just = "right" if side=="left" else "left"
                P.append(f'    (pin "{pn}" {pin_type} (at {fmt(px)} {fmt(py)} {ang}) (effects (font (size 1.0 1.0)) (justify {just})) (uuid {uid()}))')
                ex = snap(px-7.62 if side=="left" else px+7.62)
                extra.append(f"  (wire (pts (xy {fmt(px)} {fmt(py)}) (xy {fmt(ex)} {fmt(py)})) (stroke (width 0) (type default)) (uuid {uid()}))")
                extra.append(gl(net,ex,py,"right" if side=="left" else "left"))
        P.append("  )")

    rows=[70+i*54 for i in range(4)]                 # 4 channel rows
    # TIA channels (column 1) — on-board PD, only V_OUT exported
    for i,wl in enumerate(WL):
        sheet(f"TIA_{wl}",f"tia_{wl.lower()}.kicad_sch",60,rows[i],62,34,
              [("V_OUT","output","right",f"VOUT{i+1}")])
    # Laser drivers (column 2)
    for i,wl in enumerate(WL):
        laser_pins = [
            ("PWM_IN","input","left",f"PWM{i+1}"),
            ("LASER_N","output","right",f"LASER_N{i+1}"),
            ("ISENSE","output","right",f"ISENSE{i+1}"),
        ]
        if wl != "BLUE":
            laser_pins.append(("MPD_RAW","output","right",f"MPD_RAW{i+1}"))
        sheet(f"LASER_{wl}",f"laser_{wl.lower()}.kicad_sch",240,rows[i],62,34,laser_pins)
    # MCU (column 3, top).  The imported access-controller MCU sheet exposes
    # generic ESP32 GPIO names; map the bench control/telemetry nets at the
    # root so the MCU page can stay visually aligned with the source design.
    mcu_pins=[
        ("IO10","output","left","PWM1"),
        ("IO11","output","left","PWM2"),
        ("IO12","output","left","PWM3"),
        ("IO16","output","left","PWM4"),
        ("IO4","input","left","ISENSE1"),
        ("IO5","input","left","ISENSE2"),
        ("IO6","input","left","ISENSE3"),
        ("IO7","input","left","ISENSE4"),
        ("IO2","input","left","MPD1"),
        ("IO3","input","left","MPD2"),
        ("IO8","input","left","MPD3"),
        ("IO9","input","left","MPD4"),
        ("IO15","output","left","CONVST"),
        ("5V","output","left","VBUS_5V"),
        ("3V3","input","left","+3V3"),
        ("IO17","output","right","ADC_SCLK"),
        ("IO18","output","right","ADC_CS"),
        ("IO21","input","right","ADC_MISO_A"),
        ("IO38","input","right","ADC_MISO_B"),
        ("IO47","input","right","ADC_BUSY"),
        ("IO48","output","right","ADC_RESET"),
    ]
    sheet("MCU_ESP32-S3","mcu.kicad_sch",430,rows[0],95,118,mcu_pins)
    # POWER_IO (column 3, bottom)
    pio_pins=[(f"VOUT{i+1}","input","left",f"VOUT{i+1}") for i in range(4)]+[
        ("CONVST","input","left","CONVST"),("VBUS_5V","input","left","VBUS_5V")]+[
        (f"MPD_RAW{i+1}","input","left",f"MPD_RAW{i+1}") for i in range(4)]+[
        (f"MPD{i+1}","output","left",f"MPD{i+1}") for i in range(4)]+[
        ("ADC_SCLK","input","right","ADC_SCLK"),
        ("ADC_CS","input","right","ADC_CS"),
        ("ADC_MISO_A","output","right","ADC_MISO_A"),
        ("ADC_MISO_B","output","right","ADC_MISO_B"),
        ("ADC_BUSY","output","right","ADC_BUSY"),
        ("ADC_RESET","input","right","ADC_RESET"),
    ]
    sheet("POWER_IO","power_io.kicad_sch",430,220,95,140,pio_pins,pps=6.5)

    mounting_holes = [("H1", 552, 382), ("H2", 572, 382)]
    for ref, x, y in mounting_holes:
        P.append(emit_part(ref, "MOUNTING_HOLE_PAD", "M3", "MountingHole:MountingHole_3.2mm_M3", "", "", x, y))
        pin = snap_point((x, y))
        gnd = snap_point((x, y + 6))
        P.append(f"  (wire (pts (xy {fmt(pin[0])} {fmt(pin[1])}) (xy {fmt(gnd[0])} {fmt(gnd[1])})) (stroke (width 0) (type default)) (uuid {uid()}))")
        P.append(emit_power("GND", gnd[0], gnd[1], 0))

    P+=extra
    P.append(f'  (text "LASER CONTROLLER  ·  Vivonics  ·  rev v9   —   1 channel x 4 wavelengths (IR / RED / GREEN / BLUE)  ·  TIA x4  ·  laser_driver x4  ·  AD7606-4 signal ADC  ·  monitor PD ADC x3+spare  ·  mcu  ·  power_io" (at 40 30 0) (effects (font (size 2.4 2.4)) (justify left)) (uuid {uid()}))')
    P.append(f'  (text "Global-label nets join sheet pins (VOUT1..4, ADC_SCLK/CS/MISO_A/MISO_B/BUSY/RESET, PWM1..4, ISENSE1..4, MPD_RAW1..3 plus spare MPD_RAW4, MPD1..4, LASER_N1..4, CONVST, VBUS_5V, +3V3)." (at 40 36 0) (effects (font (size 1.6 1.6)) (justify left)) (uuid {uid()}))')
    P+=['  (sheet_instances','    (path "/" (page "1"))',"  )",")"]
    txt="\n".join(P)+"\n"
    assert sum((c=="(")-(c==")") for c in txt)==0,"paren imbalance in root"
    return txt

# ═══ BOM ═══
def imported_sheet_parts(path: Path) -> dict[str, tuple]:
    if not path.exists():
        return {}
    text = path.read_text()
    start = text.find("\n  (symbol (lib_id")
    body = text[start + 1:] if start >= 0 else text
    blocks = []
    current = []
    depth = 0
    in_block = False
    for line in body.splitlines():
        if not in_block and line.startswith('  (symbol (lib_id "'):
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

    parts = {}
    for block in blocks:
        def field(pattern: str) -> str:
            match = re.search(pattern, block)
            return match.group(1).strip() if match else ""
        ref = field(r'\(property "Reference" "([^#][^"]*)"')
        if not ref:
            continue
        parts[ref] = (
            field(r'\(symbol \(lib_id "([^"]+)"'),
            field(r'\(property "Value" "([^"]*)"'),
            field(r'\(property "Footprint" "([^"]*)"'),
            field(r'\(property "Part Number" "([^"]*)"'),
            field(r'\(property "LCSC" "([^"]*)"'),
            0,
            0,
        )
    return parts

def build_bom():
    groups={}; hand={}; ctr={}
    bom_sources = dict(BOM_REG)
    bom_sources["MCU_ESP32-S3_IMPORTED"] = (1, imported_sheet_parts(OUT_DIR / "mcu.kicad_sch"))
    for sheet,(mult,parts) in bom_sources.items():
        for ref,(sym,val,fp,mpn,lcsc,x,y) in parts.items():
            if sym in HAND or sym in NON_SMT_ASSEMBLY or lcsc=="":
                hand[(val,mpn)] = hand.get((val,mpn),0)+mult; continue
            for _ in range(mult):
                groups.setdefault((val,fp,lcsc),[]).append(ref)
    rows=["Comment,Designator,Footprint,LCSC"]; n=0
    for (val,fp,lcsc),refs in sorted(groups.items(), key=lambda kv:(kv[0][2],kv[0][0])):
        n+=len(refs); rows.append(f'"{val}","{",".join(refs)}","{fp}","{lcsc}"')
    return "\n".join(rows) + "\n"

def build_procurement_manifest():
    groups = {}
    bom_sources = dict(BOM_REG)
    bom_sources["MCU_ESP32-S3_IMPORTED"] = (1, imported_sheet_parts(OUT_DIR / "mcu.kicad_sch"))
    for sheet, (mult, parts) in bom_sources.items():
        for ref, (sym, val, fp, mpn, lcsc, x, y) in parts.items():
            if sym in NON_SMT_ASSEMBLY:
                assembly = "Hand install optical"
                note = "Direct laser can; install after PCB/PCBA and inspect pin orientation."
            elif sym in JLCPCB_THT_ASSEMBLY:
                assembly = "JLCPCB THT"
                note = "Included in JLCPCB BOM/CPL for through-hole/wave/manual connector assembly."
            elif sym in HAND:
                assembly = "Hand install mechanical"
                note = "Mechanical connector/header not included in the JLCPCB assembly BOM/CPL."
            elif lcsc == "":
                assembly = "Manual review"
                note = "No JLCPCB/LCSC code in schematic fields."
            else:
                assembly = "JLCPCB SMT"
                note = "Included in laser_controller_bom_jlcpcb.csv and CPL."
            key = (assembly, val, fp, mpn, lcsc, note)
            groups.setdefault(key, []).extend([ref] * mult)

    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["Assembly", "Comment", "Designator", "Qty", "Footprint", "MPN", "LCSC", "Notes"])
    for (assembly, val, fp, mpn, lcsc, note), refs in sorted(
        groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][4], ",".join(kv[1]))
    ):
        writer.writerow([assembly, val, ",".join(refs), len(refs), fp, mpn, lcsc, note])
    return output.getvalue()

KICAD_PRO='{\n  "board": {"design_settings": {"rules": {}}},\n  "meta": {"filename": "laser_controller.kicad_pro", "version": 1},\n  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},\n  "sheets": [],\n  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}\n}\n'

def atomic_write(path, text):
    path = Path(path)
    if not path.is_absolute():
        path = OUT_DIR / path
    tmp=f"{path}.tmp.{os.getpid()}"
    with open(tmp,"w") as f: f.write(text)
    os.replace(tmp,path)

def main():
    _pwr_ctr[0] = 200
    BOM_REG.clear()
    sheets = {
        **{f"tia_{wl.lower()}.kicad_sch": build_tia_channel(f"TIA_{wl}") for wl in WL},
        **{f"laser_{wl.lower()}.kicad_sch": build_laser_driver(f"LASER_{wl}") for wl in WL},
        "power_io.kicad_sch": build_power_io(),
        "laser_controller.kicad_sch": build_root(),
    }
    for fname, content in sheets.items():
        atomic_write(fname, content)
        print(f"  wrote {fname} ({len(content)} bytes, {content.count(chr(10))} lines)")
    atomic_write("lib/viv.kicad_sym", build_viv_symbol_library())
    print("  wrote lib/viv.kicad_sym")
    atomic_write("laser_controller_bom_jlcpcb.csv", build_bom())
    print("  wrote laser_controller_bom_jlcpcb.csv")
    atomic_write("fab/laser_controller_full_procurement.csv", build_procurement_manifest())
    print("  wrote fab/laser_controller_full_procurement.csv")
    if not (OUT_DIR / "laser_controller.kicad_pro").exists():
        atomic_write("laser_controller.kicad_pro", KICAD_PRO)
        print("  wrote laser_controller.kicad_pro")


if __name__ == "__main__":
    main()
