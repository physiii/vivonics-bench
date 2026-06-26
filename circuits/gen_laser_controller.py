#!/usr/bin/env python3
"""Hierarchical schematic generator for the Laser Controller board.

Source of truth — DO NOT hand-edit the .kicad_sch files; edit this and re-run.
Produces (1 channel, 4 wavelengths):
  laser_controller.kicad_sch       — root (sheet symbols + global-label interconnect)
  tia_ir/red/green/blue.kicad_sch  — four on-board signal PD + OPA380 TIA sheets
  laser_ir/red/green/blue.kicad_sch — four constant-current laser sink sheets
  mcu.kicad_sch                    — ESP32-S3 MCU sheet using the access-controller Espressif symbol
  power_io.kicad_sch               — 5V OR-ing, laser supply, AD7606 outputs, laser outputs, MPD high-side feedback
  laser_controller_bom_jlcpcb.csv  — consolidated JLCPCB BOM
  laser_controller.kicad_pro       — minimal project file (written once if absent)

Architecture: ONE optical channel, FOUR wavelengths (IR / RED / GREEN / BLUE). Each
wavelength has a constant-current laser driver with current-sense feedback, and one
on-board single clear Si PIN photodiode (Osram SFH2201, 300–1100 nm — covers blue→IR)
reverse-biased into an OPA380 TIA → 4 TIA outputs to the external AD7606. (Single-PD
intensity read = the bench proxy for the
production Gpixel per-pixel intensity reader; see DUAL_PINHOLE / INDEX_READ_PRODUCTION
docs.) Control: ESP32-S3-WROOM-1 (matches access-controller), native USB Mini-B + USBLC6
ESD; 4× PWM → 4 laser drivers; 4 laser I-sense + 4 monitor-PD current-sense outputs → ESP32 ADC pins.
Power: USB VBUS (5V) ‖ external J6 5V OR-ed via SS14 Schottkys → +5V; AP2112K-3.3 → +3V3;
laser anode supply LASER_V+ (J5) is a separate rail.  Every SMT part carries visible-on-
click LCSC + Part Number fields (same convention as the access-controller project).

Run:  python3 gen_laser_controller.py
"""
from __future__ import annotations
import os
from pathlib import Path
from circuit_designators import WL, actualize_parts

PROJECT = "laser_controller"
ROOT_UUID = "c1d2e3f4-6000-4000-a000-000000000001"
ACCESS_CONTROLLER_MCU = Path("/home/andy/projects/access-controller/circuits/controller/microcontroller.kicad_sch")
OUT_DIR = Path(__file__).resolve().parent
_ctr = [0]
def uid(): _ctr[0]+=1; return f"c1d2e3f4-6000-4000-a000-{_ctr[0]:012d}"
def fmt(v): return f"{v:.4f}".rstrip("0").rstrip(".")

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
CONNS = ("CONN2","CONN3","CONN4","CONN5","CONN6","CONN8","CONN10","USB_MINIB","ESD_USB")
def S(name, pins, glyph, texts=None, power=False, hide_nums=None, roff=(5.6,-1.4), voff=(5.6,1.4)):
    SYM[name] = {"pins":pins, "glyph":glyph, "texts":texts or [], "power":power, "roff":roff, "voff":voff,
                 "hide_nums": hide_nums if hide_nums is not None else (name not in CONNS)}

S("R_H", {"1":(-3.81,0,0,"~","passive",1.27),"2":(3.81,0,180,"~","passive",1.27)},
  [[(-2.54,1.016),(2.54,1.016),(2.54,-1.016),(-2.54,-1.016),(-2.54,1.016)]])
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
# Photodiode (Osram SFH2201 clear Si PIN, KiCad D_Photo convention): cathode (pin1, left) → +5V bias ; anode (pin2, right) → TIA −IN
S("PHOTODIODE", {"1":(-3.81,0,0,"K","passive",1.27),"2":(3.81,0,180,"A","passive",1.27)},
  [[(1.27,1.524),(1.27,-1.524),(-1.27,0),(1.27,1.524)],       # diode triangle (anode base right → apex left)
   [(-1.27,1.524),(-1.27,-1.524)],                            # cathode bar (left)
   [(0.6,3.0),(-0.4,1.8)],[(-0.4,1.8),(0.32,1.82)],[(-0.4,1.8),(-0.28,2.5)],   # incoming-light arrow 1
   [(2.1,3.0),(1.1,1.8)],[(1.1,1.8),(1.82,1.82)],[(1.1,1.8),(1.22,2.5)]],      # incoming-light arrow 2
  hide_nums=True, roff=(6,2.2), voff=(6,4.2))
# OPA380AID SOIC-8: 1/5/8 are NC, 2=IN-, 3=IN+, 4=V-, 6=OUT, 7=V+.
S("OPA_N", {"1":(-10.16,5.08,0,"NC","passive",2.54),
            "2":(-7.62,2.54,0,"-","input",2.54),"3":(-7.62,-2.54,0,"+","input",2.54),
            "4":(0,-7.62,90,"V-","power_in",2.54),
            "5":(10.16,-5.08,180,"NC","passive",2.54),
            "6":(7.62,0,180,"","output",2.54),"7":(0,7.62,270,"V+","power_in",2.54),
            "8":(10.16,5.08,180,"NC","passive",2.54)},
  [[(-5.08,-5.08),(5.08,0),(-5.08,5.08),(-5.08,-5.08)]],[("+",-3.81,-2.54,1.0),("-",-3.81,2.54,1.0)])
# TLV9001IDBVR, DBV SOT-23-5 package: 1=OUT, 2=V-, 3=IN+, 4=IN-, 5=V+.
S("TLV9001_SOT23_5", {"4":(-7.62,2.54,0,"-","input",2.54),"3":(-7.62,-2.54,0,"+","input",2.54),
            "1":(7.62,0,180,"","output",2.54),"5":(0,7.62,270,"V+","power_in",2.54),"2":(0,-7.62,90,"V-","power_in",2.54)},
  [[(-5.08,-5.08),(5.08,0),(-5.08,5.08),(-5.08,-5.08)]],[("+",-3.81,-2.54,1.0),("-",-3.81,2.54,1.0)])
# AO3400A SOT-23 N-MOSFET: 1=gate, 2=source, 3=drain.
S("NMOS", {"3":(0,5.08,270,"D","passive",1.27),"1":(-5.08,0,0,"G","input",1.27),"2":(0,-5.08,90,"S","passive",1.27)},
  [[(-0.635,2.032),(0,0),(-0.635,-2.032)],[(0,2.54),(0,1.524)],[(0,-1.524),(0,-2.54)],[(-0.762,-0.762),(0,-1.524),(0.762,-0.762)]])
# Schottky diode (SS14): anode left, cathode right
S("SCHOTTKY", {"1":(-3.81,0,0,"A","passive",1.27),"2":(3.81,0,180,"K","passive",1.27)},
  [[(-3.81,0),(-1.27,0)],[(1.27,0),(3.81,0)],[(-1.27,1.27),(1.27,0),(-1.27,-1.27),(-1.27,1.27)],
   [(1.27,1.27),(1.27,-1.27)],[(1.27,1.27),(0.508,1.27)],[(1.27,-1.27),(2.032,-1.27)]])
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
    # Keep all analog telemetry on ADC1 (GPIO1..GPIO10). PWM uses documented,
    # non-strapping GPIOs so Wi-Fi/ADC2 behavior cannot disturb current/monitor
    # readings. PWM2 uses GPIO38 because GPIO18 is physically trapped by the
    # dense USB/ADC escape corridor on this 90 x 50 mm bench layout.
    "PWM1":"9", "PWM2":"31", "PWM3":"21", "PWM4":"22",
    "ISENSE1":"4", "ISENSE2":"5", "ISENSE3":"6", "ISENSE4":"7",
    "MPD1":"38", "MPD2":"39", "MPD3":"12", "MPD4":"17",
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
# PWR_FLAG — declares an external supply node as a power source (silences ERC "no power source")
S("PWR_FLAG",{"1":(0,0,90,"~","power_out",0)},
  [[(0,0),(0,1.27)],[(0,1.27),(-1.016,1.905),(0,2.54),(1.016,1.905),(0,1.27)]],power=True)
# USB Mini-B receptacle (LCSC C5120592): 1=VBUS 2=D− 3=D+ 4=ID 5=GND 6=shell
S("USB_MINIB",{"1":(-7.62,5.08,0,"VBUS","passive",2.54),"2":(-7.62,2.54,0,"D-","passive",2.54),
               "3":(-7.62,0,0,"D+","passive",2.54),"4":(-7.62,-2.54,0,"ID","passive",2.54),
               "5":(-7.62,-5.08,0,"GND","passive",2.54),"6":(-7.62,-8.89,0,"SHLD","passive",2.54)},
  [[(-5.08,7.62),(2.54,7.62),(2.54,-11.43),(-5.08,-11.43),(-5.08,7.62)]],[("USB",-1.27,0,1.4)])
# USBLC6-2SC6 ESD (SOT-23-6): 1,6 = IO line A ; 3,4 = IO line B ; 2=GND ; 5=VBUS
S("ESD_USB",{"1":(-7.62,2.54,0,"IO1","passive",2.54),"6":(7.62,2.54,180,"IO1","passive",2.54),
             "3":(-7.62,-2.54,0,"IO2","passive",2.54),"4":(7.62,-2.54,180,"IO2","passive",2.54),
             "5":(0,7.62,270,"VBUS","passive",2.54),"2":(0,-7.62,90,"GND","passive",2.54)},
  [[(-5.08,5.08),(5.08,5.08),(5.08,-5.08),(-5.08,-5.08),(-5.08,5.08)]],[("ESD",0,0,1.2)], roff=(-4,-9), voff=(-4,10))
# INA4180A1IPWR, PW TSSOP-14: quad high/low-side current-sense amplifier.
# Pinout from TI INAx180 datasheet: 1 OUT1, 2 IN-1, 3 IN+1, 4 VS, 5 IN+2,
# 6 IN-2, 7 OUT2, 8 OUT3, 9 IN-3, 10 IN+3, 11 GND, 12 IN+4, 13 IN-4, 14 OUT4.
S("INA4180_TSSOP14",
  {"1":(12.7,16.0,180,"OUT1","output",2.54),
   "2":(-12.7,13.5,0,"IN-1","input",2.54),"3":(-12.7,18.5,0,"IN+1","input",2.54),
   "4":(0,23.0,270,"VS","power_in",2.54),
   "5":(-12.7,8.5,0,"IN+2","input",2.54),"6":(-12.7,3.5,0,"IN-2","input",2.54),
   "7":(12.7,6.0,180,"OUT2","output",2.54),
   "8":(12.7,-6.0,180,"OUT3","output",2.54),
   "9":(-12.7,-8.5,0,"IN-3","input",2.54),"10":(-12.7,-3.5,0,"IN+3","input",2.54),
   "11":(0,-23.0,90,"GND","power_in",2.54),
   "12":(-12.7,-13.5,0,"IN+4","input",2.54),"13":(-12.7,-18.5,0,"IN-4","input",2.54),
   "14":(12.7,-16.0,180,"OUT4","output",2.54)},
  [[(-10.16,21.0),(10.16,21.0),(10.16,-21.0),(-10.16,-21.0),(-10.16,21.0)]],
  [("INA4180",0,0,1.3)], hide_nums=False, roff=(-10.0,-25.5), voff=(-10.0,24.5))
# LM4040C50IDBZR, DBZ SOT-23-3: pin 1 cathode, pin 2 anode, pin 3 "*" must float or tie to anode.
S("LM4040_DBZ",
  {"1":(0,5.08,270,"K","passive",1.27),"2":(0,-5.08,90,"A","passive",1.27),"3":(5.08,-5.08,180,"*","passive",1.27)},
  [[(-1.27,1.27),(1.27,1.27),(0,-1.27),(-1.27,1.27)], [(-1.27,-1.27),(1.27,-1.27)], [(-1.8,2.2),(1.8,2.2)]],
  [("5.0V",0,0,1.0)], hide_nums=False, roff=(6,-6), voff=(6,6))
S("LASER_CAN_MON_PD",
  {"1":(-12.7,0,0,"LD_K","passive",2.54),
   "2":(0,-12.7,270,"LD_A/PD_K/CASE","passive",2.54),
   "3":(12.7,5.08,180,"PD_A","passive",2.54)},
  [[(-8.0,-8.0),(8.0,-8.0),(8.0,10.0),(-8.0,10.0),(-8.0,-8.0)],
   [(-5.0,-2.5),(1.0,0.0),(-5.0,2.5),(-5.0,-2.5)],
   [(1.0,-3.2),(1.0,3.2)],
   [(-2.5,6.8),(2.5,6.8),(0.0,9.2),(-2.5,6.8)],
   [(2.5,6.0),(2.5,9.6)]],
  [("LD",-2.5,-5.5,1.0),("MPD",-1.0,4.2,1.0)],
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
S("GND",{"1":(0,0,270,"GND","power_in",0)},[[(0,0),(0,-2.032)],[(-2.032,-2.032),(2.032,-2.032)],
  [(-1.27,-2.794),(1.27,-2.794)],[(-0.508,-3.556),(0.508,-3.556)]],power=True)

REFLET={"R_H":"R","R_V":"R","POT_H":"RV","POT_V":"RV","C_H":"C","C_V":"C","PHOTODIODE":"D","OPA_N":"U",
        "TLV9001_SOT23_5":"U",
        "INA4180_TSSOP14":"U","LM4040_DBZ":"U",
        "LASER_CAN_MON_PD":"LD",
        "CONN2":"J","CONN3":"J","CONN4":"J","CONN5":"J","CONN6":"J","CONN8":"J","CONN10":"J","NMOS":"Q",
        "Espressif:ESP32-S3-WROOM-1":"U",
        "LDO5":"U","SCHOTTKY":"D","USB_MINIB":"J","ESD_USB":"U"}
# Hand-add (excluded from SMT BOM): only the THT 2.54mm I/O headers. Everything else, including
# the SFH2201 signal PDs, ESP32-S3, 3224W SMD pots, and USB Mini-B connector, is JLCPCB machine-placed.
HAND={"CONN2","CONN3","CONN4","CONN5","CONN6","CONN8","CONN10"}
OFFBOARD={"LASER_CAN_MON_PD"}
PASSIVE_GLYPH_NUMS=("R_H","R_V","POT_H","POT_V","C_H","C_V","PHOTODIODE","OPA_N","TLV9001_SOT23_5","NMOS","SCHOTTKY")

FP_R="Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_R2512="Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder"
FP_603="Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_402="Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"
FP_805="Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SO8="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_TSSOP14="Package_SO:TSSOP-14_4.4x5mm_P0.65mm"
FP_POT_SMD="Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical"   # SMD trimmer (JLCPCB-mountable)
FP_SOT235="Package_TO_SOT_SMD:SOT-23-5"
FP_SOT236="Package_TO_SOT_SMD:SOT-23-6"
FP_SOT23="Package_TO_SOT_SMD:SOT-23"
FP_SMA="Diode_SMD:D_SMA"
FP_ESP32S3="RF_Module:ESP32-S3-WROOM-1"   # stock KiCad footprint available here; access-controller uses Espressif lib name for same module
FP_USB="Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal"  # Würth 65100516121 horizontal SMD Mini-B (same as access-controller)
FP_PD="OptoDevice:Osram_SFH2201"          # clear broadband Si PIN PD; in-tree KiCad footprint (pad1=K, pad2=A)
FP_H2="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_H5="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
FP_H6="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
FP_H10="Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical"

# ── Verified LCSC numbers (parts agent, 2026-06-22) ───────────────────
LCSC_10K="C269701"    # 10k 0603 1% TyoHM RMC060310KFN (Basic, in stock)
LCSC_22R="C23345"     # 22Ω 0603 1% UNI-ROYAL 0603WAF220JT5E (Basic) — USB D+/D− series damping
LCSC_10R="C5123624"  # 10Ω 2512 2W 1% Milliohm HoCR2512-2W-10R-1% — laser source sense
LCSC_1K="C21190"; LCSC_10PF="C106245"; LCSC_10UF="C15850"; LCSC_1UF="C52923"; LCSC_100NF="C1525"
LCSC_30K="C22984"    # 30k 0603 1% UNI-ROYAL 0603WAF3002T5E — PWM command divider
LCSC_10M="C57129"    # 10M 0603 1% (UNI-ROYAL 0603WAF1005T5E) — verify stock at order
LCSC_750R="C114635"  # 750Ω 0603 1% Yageo RC0603FR-07750RL — monitor-PD sense shunt
LCSC_249K="C22908"   # 2.49k 0603 1% UNI-ROYAL 0603WAF2491T5E — LM4040 shunt-reference sink
LCSC_POT10K="C81348" # Bourns 3224W-1-103 10k SMD trimmer (Extended) — replaces THT 3296W VBIAS pot
LCSC_OPA="C201677"   # OPA380AID (Extended, low stock — buy buffer)
LCSC_TLV="C398363"; LCSC_NMOS="C20917" # AO3400A N-MOSFET, SOT-23, Basic
LCSC_INA4180="C2057528" # INA4180A1IPWR quad current-sense amplifier, TSSOP-14
LCSC_LM4040="C69316"    # LM4040C50IDBZR 5.0V shunt reference, SOT-23-3
LCSC_ESP="C2913199"  # ESP32-S3-WROOM-1 (exact C-number used on the access-controller); native USB D-=GPIO19 D+=GPIO20
LCSC_LDO="C51118"    # AP2112K-3.3 SOT-23-5, 250mV dropout (was AMS1117 C6186 — too much dropout off USB VBUS)
LCSC_ESD="C7519"     # USBLC6-2SC6
LCSC_SCH="C2480"     # SS14 SMA Schottky 40V/1A (Basic)
LCSC_USB="C5120592"     # Würth 65100516121 USB Mini-B horizontal SMD (same as access-controller)
LCSC_PD="C2900216"   # Osram SFH2201 clear broadband Si PIN PD (Extended); 300–1100nm covers 450/520/650/780nm

def pin(parts,ref,num):
    sym,*_,x,y=parts[ref]; lx,ly=SYM[sym]["pins"][num][:2]; return (x+lx,y-ly)

def add_stub(wires,labels,p,side,name,dist=5.08,shape="passive"):
    """Short stub + label off a pin.  side: 'left'|'right'.  name may start 'H:' (hierarchical)."""
    d = -dist if side=="left" else dist
    end=(round(p[0]+d,4), round(p[1],4))
    wires.append([p,end]); labels.append((name,end[0],end[1],"right" if d<0 else "left",shape))

def add_rail(power,wires,kind,p):
    """Drop a power symbol on a pin via a short vertical stub (rail above, GND below)."""
    sp=(round(p[0],4), round(p[1]+ (6 if kind=="GND" else -6),4))
    power.append((kind,sp[0],sp[1])); wires.append([p,sp])

def add_rail_dn(power,wires,kind,p):
    """Place a rail symbol BELOW a pin (for bottom-of-connector supply pins)."""
    sp=(round(p[0],4), round(p[1]+7,4)); power.append((kind,sp[0],sp[1])); wires.append([p,sp])

def declare_source(power,wires,kind,x,y):
    """Isolated rail-symbol + PWR_FLAG pair → tells ERC this externally-supplied net has a source."""
    power.append((kind,x,y)); power.append(("PWR_FLAG",x,y-5)); wires.append([(x,y),(x,y-5)])

def ortho(poly):
    """Manhattanize a polyline: insert an L-bend corner so no segment is ever diagonal."""
    out=[poly[0]]
    for a,b in zip(poly,poly[1:]):
        if abs(a[0]-b[0])>1e-6 and abs(a[1]-b[1])>1e-6:
            out.append((b[0],a[1]))
        out.append(b)
    return out

def sym_def(name):
    if name == "Espressif:ESP32-S3-WROOM-1":
        return extract_symbol_block(ACCESS_CONTROLLER_MCU, name)
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
        f"    (in_bom {'no' if s['power'] or name in OFFBOARD else 'yes'}) (on_board yes)",
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

def emit_part(ref,sym,val,fp,mpn,lcsc,x,y):
    rx,ry=SYM[sym]["roff"]; vx,vy=SYM[sym]["voff"]
    lib_id = sym if ":" in sym else f"viv:{sym}"
    in_bom = "no" if sym in OFFBOARD else "yes"
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
    ry=y+3.0 if kind=="GND" else y-3.0; vy=y+4.2 if kind=="GND" else y-3.2
    return "\n".join([
        f'  (symbol (lib_id "viv:{kind}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
        "    (in_bom no) (on_board yes) (dnp no)",f"    (uuid {uid()})",
        f'    (property "Reference" "#PWR{n:02d}" (at {fmt(x)} {fmt(ry)} 0) (effects (font (size 1.0 1.0)) hide))',
        f'    (property "Value" "{kind}" (at {fmt(x)} {fmt(vy)} 0) (effects (font (size 1.27 1.27))))',
        '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.0 1.0)) hide))',
        '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.0 1.0)) hide))',
        f'    (pin "1" (uuid {uid()}))',"    (instances",f'      (project "{PROJECT}"',
        f'        (path "/{ROOT_UUID}" (reference "#PWR{n:02d}") (unit 1))',"      )","    )","  )"])

BOM_REG = {}
def build_sch_content(title,date,rev,parts,power,wires,junctions,labels,texts,mult=1,ncs=None):
    BOM_REG[title]=(mult,parts)
    P=["(kicad_sch","  (version 20230121)","  (generator eeschema)",f"  (uuid {ROOT_UUID})",
       '  (paper "A3")',"  (title_block",f'    (title "{title}")',f'    (date "{date}")',f'    (rev "{rev}")',
       '    (company "Vivonics")',"  )","  (lib_symbols"]
    used=sorted({t[0] for t in parts.values()} | {k for k,_,_ in power})
    for name in used: P.append(sym_def(name))
    P.append("  )")
    for ref,t in parts.items(): P.append(emit_part(ref,*t))
    for i,(kind,x,y) in enumerate(power,1): P.append(emit_power(kind,x,y,i))
    for poly in wires:
        poly=ortho(poly)
        for a,b in zip(poly,poly[1:]):
            if a==b: continue
            P.append(f"  (wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})) (stroke (width 0) (type default)) (uuid {uid()}))")
    for x,y in junctions: P.append(f"  (junction (at {fmt(x)} {fmt(y)}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))")
    for x,y in (ncs or []): P.append(f"  (no_connect (at {fmt(x)} {fmt(y)}) (uuid {uid()}))")
    for label in labels:
        if len(label) == 4:
            t,x,y,j = label
            shape = "passive"
        else:
            t,x,y,j,shape = label
        if t.startswith("H:"):
            P.append(f'  (hierarchical_label "{t[2:]}" (shape {shape}) (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (justify {j})) (uuid {uid()}))')
        else:
            P.append(f'  (label "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (justify {j} bottom)) (uuid {uid()}))')
    for t,x,y,sz in texts: P.append(f'  (text "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size {sz} {sz})) (justify left)) (uuid {uid()}))')
    P+=['  (sheet_instances','    (path "/" (page "1"))',"  )",")"]
    txt="\n".join(P)+"\n"
    assert sum((c=="(")-(c==")") for c in txt)==0,f"paren imbalance in {title}"
    return txt

# ═══ SUB-SHEET: tia_<wavelength>.kicad_sch  (on-board PD + OPA380 TIA) ═══
def build_tia_channel(sheet_name: str):
    oy=150; ux=215
    nIN=(ux-7.62,oy-2.54); pIN=(ux-7.62,oy+2.54); OUT=(ux+7.62,oy)
    LRX,RRX = nIN[0], OUT[0]                          # feedback rails rise from −IN / out
    RfY,CfY = 138, 143
    pdcx,pdcy=188,131                                # PD cluster sits ABOVE the VBIAS chain (own clear column)
    parts={
        "D1":("PHOTODIODE","SFH2201",FP_PD,"SFH2201",LCSC_PD,pdcx,pdcy),       # on-board signal PD (one wavelength)
        "RB":("R_H","1k",FP_R,"0603WAF1001T5E",LCSC_1K,pdcx-16,pdcy),          # PD cathode → +5V bias
        "CB":("C_V","1uF",FP_402,"CL05A105KA5NQNC",LCSC_1UF,pdcx-5.81,pdcy+6), # PD cathode bypass → GND
        "U1":("OPA_N","OPA380AID",FP_SO8,"OPA380AID",LCSC_OPA,ux,oy),
        "R2":("R_H","10M",FP_R,"0603WAF1005T5E",LCSC_10M,215,RfY),            # fixed Rf (no 10M SMD trimmer)
        "C1":("C_H","10pF C0G",FP_603,"CC0603JRNPO9BN100",LCSC_10PF,215,CfY),
        "RT":("R_V","10k",FP_R,"0603WAF1002T5E",LCSC_10K,165,140),            # bounds VBIAS ≤2.5V (OPA380 CM)
        "RV11":("POT_V","VBIAS 10k",FP_POT_SMD,"3224W-1-103E",LCSC_POT10K,165,oy+2.54),  # SMD trimmer
        "R1":("R_H","10k",FP_R,"0603WAF1002T5E",LCSC_10K,181,oy+2.54),
        "C11":("C_V","10uF",FP_805,"CL21A106KAYNNNE",LCSC_10UF,191,oy+12),
        "C2":("C_V","100nF",FP_402,"CL05B104KO5NNNC",LCSC_100NF,246,oy+10),   # V+ decoupling (clear space)
    }
    power=[]; wires=[]; labels=[]
    add_rail(power,wires,"+5V",pin(parts,"U1","7")); add_rail(power,wires,"GND",pin(parts,"U1","4"))
    add_rail(power,wires,"+5V",pin(parts,"C2","1")); add_rail(power,wires,"GND",pin(parts,"C2","2"))
    # PD: anode (pin2) → −IN summing node ; cathode (pin1) → +5V via RB ; CB bypasses cathode to GND
    anode=pin(parts,"D1","2"); cathode=pin(parts,"D1","1")
    wires += [[anode,(anode[0],nIN[1]),nIN], [pin(parts,"RB","2"),cathode], [cathode,pin(parts,"CB","1")]]
    add_rail(power,wires,"+5V",pin(parts,"RB","1"))
    add_rail(power,wires,"GND",pin(parts,"CB","2"))
    # feedback: −IN → left rail up ; out → right rail up ; R2 (Rf) ∥ C1 (Cf) bridge across the top
    wires += [
        [nIN,(LRX,CfY),(LRX,RfY)],                             # left rail (−IN → Cf row → Rf row ; vertices = endpoints)
        [OUT,(RRX,oy),(RRX,CfY),(RRX,RfY)],                    # right rail (out → Cf row → Rf row)
        [pin(parts,"R2","1"),(LRX,RfY)], [pin(parts,"R2","2"),(RRX,RfY)],   # fixed Rf across feedback rails
        [pin(parts,"C1","1"),(LRX,CfY)], [pin(parts,"C1","2"),(RRX,CfY)],
        [OUT,(233,oy)],                                        # → V_OUT
    ]
    junctions=[nIN,cathode,(LRX,RfY),(LRX,CfY),(RRX,RfY),(RRX,CfY),OUT]
    # VBIAS chain (at +IN level): +5V → RT → RV11 → wiper → R1 → node → C11→GND ; node → +IN
    node=(202,oy+2.54)
    add_rail(power,wires,"+5V",pin(parts,"RT","1")); add_rail(power,wires,"GND",pin(parts,"RV11","3"))
    add_rail(power,wires,"GND",pin(parts,"C11","2"))
    wires += [[pin(parts,"RT","2"),pin(parts,"RV11","1")],
              [pin(parts,"RV11","2"),pin(parts,"R1","1")],
              [pin(parts,"R1","2"),node], [node,pin(parts,"C11","1")], [node,pIN]]
    junctions.append(node)
    labels.append(("H:V_OUT",233,oy,"left","output"))
    texts=[
        ("TIA Channel  —  on-board SFH2201 signal PD → OPA380AID transimpedance amp  ·  reused 4× (IR / RED / GREEN / BLUE)",150,104,2.0),
        ("PD reverse-biased: cathode → +5V via RB (1k) + CB bypass ; anode → OPA380 −IN summing node.  Rf = R2 (10M) ∥ Cf = C1 (10pF).",150,110,1.3),
        ("VBIAS: +5V → RT(10k) → RV11 trim → RC(R1,C11) → +IN (held ≤2.5V).  V_OUT = VBIAS ± I_pd·Rf → external AD7606.",150,116,1.3),
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
    nIN=(ux-7.62,oy-2.54); pIN=(ux-7.62,oy+2.54); OUT=(ux+7.62,oy)
    parts={
        "U11":("TLV9001_SOT23_5","TLV9001",FP_SOT235,"TLV9001IDBVR",LCSC_TLV,ux,oy),
        "LD":("LASER_CAN_MON_PD","OFFBOARD LASER+MPD","","","",315,150),
        "R21":("R_H","10k",FP_R,"0603WAF1002T5E",LCSC_10K,172,oy+2.54),
        "R22":("R_V","30k LIMIT",FP_R,"0603WAF3002T5E",LCSC_30K,198,oy+6.35),
        "C21":("C_V","1uF",FP_402,"CL05A105KA5NQNC",LCSC_1UF,188,oy+13),
        "C22":("C_V","100nF",FP_402,"CL05B104KO5NNNC",LCSC_100NF,235,oy+16),       # V+ decoupling (open lower-middle)
        "R31":("R_H","1k",FP_R,"0603WAF1001T5E",LCSC_1K,232,oy),
        "Q1":("NMOS","AO3400A",FP_SOT23,"AO3400A",LCSC_NMOS,254,oy),
        "R11":("R_V","10R 2W",FP_R2512,"HoCR2512-2W-10R-1%",LCSC_10R,254,oy+16),   # source sense
        "R12":("R_H","1k",FP_R,"0603WAF1001T5E",LCSC_1K,274,oy+13.46),             # isolates ISENSE tap
        "CC":("C_V","10pF C0G",FP_603,"CC0603JRNPO9BN100",LCSC_10PF,165,oy+15),    # loop comp (FB↔LOUT)
    }
    power=[]; wires=[]; labels=[]
    add_rail(power,wires,"+5V",pin(parts,"U11","5")); add_rail(power,wires,"GND",pin(parts,"U11","2"))
    add_rail(power,wires,"+5V",pin(parts,"C22","1")); add_rail(power,wires,"GND",pin(parts,"C22","2"))
    pnode=(188,oy+2.54)
    wires += [[pin(parts,"R21","2"),pnode,pIN], [pnode,pin(parts,"C21","1")], [pnode,pin(parts,"R22","1")]]
    add_rail(power,wires,"GND",pin(parts,"C21","2"))
    add_rail(power,wires,"GND",pin(parts,"R22","2"))
    wires += [[OUT,pin(parts,"R31","1")], [pin(parts,"R31","2"),pin(parts,"Q1","1")],
              [pin(parts,"Q1","2"),pin(parts,"R11","1")]]
    add_rail(power,wires,"GND",pin(parts,"R11","2"))
    sense=pin(parts,"R11","1")
    wires += [[sense,pin(parts,"R12","1")]]
    junctions=[pnode,sense,OUT]
    add_stub(wires,labels,pin(parts,"R21","1"),"left","H:PWM_IN",shape="input")
    add_stub(wires,labels,pin(parts,"R12","2"),"right","H:ISENSE",shape="output")
    cN=pin(parts,"Q1","3"); top=(cN[0],cN[1]-7)                          # drain → LASER_N and off-board LD cathode
    ld_k=pin(parts,"LD","1")
    wires.append([cN,top,(ld_k[0],top[1]),ld_k]); labels.append(("H:LASER_N",top[0],top[1],"left","output"))
    add_rail(power,wires,"LASER_VP",pin(parts,"LD","2"))
    add_stub(wires,labels,pin(parts,"LD","3"),"right","H:MPD_RAW",dist=10,shape="output")
    for p in (nIN,sense):                                                # FB: −IN and sense top
        e=(p[0]-9,p[1]); wires.append([p,e]); labels.append(("FB",e[0],e[1],"right"))
    e=(OUT[0]+4,oy-7); wires.append([OUT,(OUT[0]+4,oy),e]); labels.append(("LOUT",e[0],e[1],"left"))
    wires.append([pin(parts,"CC","1"),(165,oy+9)]);  labels.append(("FB",165,oy+9,"right"))
    wires.append([pin(parts,"CC","2"),(165,oy+21)]); labels.append(("LOUT",165,oy+21,"right"))
    texts=[
        ("Laser Driver  —  TLV9001 + AO3400A constant-current sink  ·  I = V_ctrl / 10Ω  ·  reused 4× (IR / RED / GREEN / BLUE)",150,114,2.0),
        ("PWM_IN → R21/C21 with R22 30k limiter → +IN (full-scale ≈2.48V, ≈248mA) ;  −IN = FB (sense top).",150,120,1.3),
        ("TLV9001 out → R31 → Q1 gate ; source → 10Ω 2W sense → GND.  CC = loop comp (FB↔LOUT, tune in bring-up).",150,125,1.3),
        ("Off-board PLT/A-code laser can shown for connectivity: LD_K→LASER_N, LD_A/PD_K/case→LASER_V+, PD_A→MPD_RAW→POWER_IO U12/U13.",150,130,1.3),
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
    )

# ═══ SUB-SHEET: mcu.kicad_sch  (ESP32-S3 + LDO + USB Mini-B + ESD) ═══
def build_mcu():
    # ESP32 centered on page (A3=420x297), large 91x81mm symbol needs room
    ex,ey = 230, 180
    # Left-side components (power + USB + UART) well clear of ESP32 left edge (ex-46 = 184)
    lx = 60   # left column x
    parts={
        "U9":("Espressif:ESP32-S3-WROOM-1","ESP32-S3-WROOM-1",FP_ESP32S3,"ESP32-S3-WROOM-1-N16R8",LCSC_ESP,ex,ey),
        # Power zone (top-left corner)
        "U10":("LDO5","AP2112K-3.3",FP_SOT235,"AP2112K-3.3TRG1",LCSC_LDO,lx+20,90),
        "C44":("C_V","1uF",FP_402,"CL05A105KA5NQNC",LCSC_1UF,lx,90),
        "C41":("C_V","100nF",FP_402,"CL05B104KO5NNNC",LCSC_100NF,lx+40,90),
        "C42":("C_V","10uF",FP_805,"CL21A106KAYNNNE",LCSC_10UF,lx+55,90),
        # USB zone (mid-left)
        "J6":("USB_MINIB","USB Mini-B",FP_USB,"65100516121",LCSC_USB,lx,160),
        "U12":("ESD_USB","USBLC6",FP_SOT236,"USBLC6-2SC6",LCSC_ESD,lx+60,160),
        "RUSBM":("R_H","22R USB",FP_R,"0603WAF220JT5E",LCSC_22R,lx+96,157.46),
        "RUSBP":("R_H","22R USB",FP_R,"0603WAF220JT5E",LCSC_22R,lx+96,162.54),
        # UART (bottom-left)
        "J3":("CONN5","UART->Pi",FP_H5,"","",lx,230),
        # EN network (between LDO and ESP32, clear of symbol)
        "REN":("R_V","10k",FP_R,"RMC060310KFN",LCSC_10K,lx+80,100),
        "CEN":("C_V","100nF",FP_402,"CL05B104KO5NNNC",LCSC_100NF,lx+100,100),
        "RBOOT":("R_V","10k BOOT",FP_R,"RMC060310KFN",LCSC_10K,lx+120,100),
        # ESP VDD decoupling (near ESP32 top)
        "C43":("C_V","100nF",FP_402,"CL05B104KO5NNNC",LCSC_100NF,ex-20,ey-55),
    }
    power=[]; wires=[]; labels=[]; ncs=[]
    # ── LDO: 5V→3V3 ──
    add_rail(power,wires,"+5V",pin(parts,"U10","1")); add_rail(power,wires,"+5V",pin(parts,"U10","3"))
    add_rail(power,wires,"GND",pin(parts,"U10","2")); add_rail(power,wires,"+3V3",pin(parts,"U10","5"))
    ncs.append(pin(parts,"U10","4"))
    add_rail(power,wires,"+5V",pin(parts,"C44","1")); add_rail(power,wires,"GND",pin(parts,"C44","2"))
    for c in ("C41","C42","C43"):
        add_rail(power,wires,"+3V3",pin(parts,c,"1")); add_rail(power,wires,"GND",pin(parts,c,"2"))
    # ── EN pull-up + POR cap ──
    add_rail(power,wires,"+3V3",pin(parts,"REN","1")); add_stub(wires,labels,pin(parts,"REN","2"),"right","ESP_EN",dist=8)
    add_stub(wires,labels,pin(parts,"CEN","1"),"right","ESP_EN",dist=8); add_rail(power,wires,"GND",pin(parts,"CEN","2"))
    add_rail(power,wires,"+3V3",pin(parts,"RBOOT","1")); add_stub(wires,labels,pin(parts,"RBOOT","2"),"right","ESP_BOOT",dist=8)
    # ── ESP32 power ──
    add_rail(power,wires,"+3V3",pin(parts,"U9",ESP_PIN["VDD3P3"]))
    add_rail(power,wires,"GND",pin(parts,"U9",ESP_PIN["GND"]))
    # ── USB: J6 → USBLC6 ESD → 22R series resistors → ESP32 native USB ──
    add_stub(wires,labels,pin(parts,"J6","2"),"right","USB_DM_CONN",dist=8)
    add_stub(wires,labels,pin(parts,"U12","1"),"left","USB_DM_CONN",dist=8)
    add_stub(wires,labels,pin(parts,"U12","6"),"right","USB_DM_ESD",dist=8)
    add_stub(wires,labels,pin(parts,"RUSBM","1"),"left","USB_DM_ESD",dist=6)
    add_stub(wires,labels,pin(parts,"RUSBM","2"),"right","USB_DM",dist=6)
    add_stub(wires,labels,pin(parts,"U9",ESP_PIN["USB_DM"]),"right","USB_DM",dist=18)
    add_stub(wires,labels,pin(parts,"J6","3"),"right","USB_DP_CONN",dist=8)
    add_stub(wires,labels,pin(parts,"U12","3"),"left","USB_DP_CONN",dist=8)
    add_stub(wires,labels,pin(parts,"U12","4"),"right","USB_DP_ESD",dist=8)
    add_stub(wires,labels,pin(parts,"RUSBP","1"),"left","USB_DP_ESD",dist=6)
    add_stub(wires,labels,pin(parts,"RUSBP","2"),"right","USB_DP",dist=6)
    add_stub(wires,labels,pin(parts,"U9",ESP_PIN["USB_DP"]),"right","USB_DP",dist=18)
    # ── VBUS ──
    mjunc=[]
    jv=pin(parts,"J6","1"); ev=pin(parts,"U12","5")
    vy=ev[1]-8; vtap=(round((jv[0]+ev[0])/2,4),vy)
    wires.append([jv,(jv[0],vy),(ev[0],vy),ev])
    labels.append(("H:VBUS_5V",jv[0]+2,vy,"left","output"))
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
            add_stub(wires,labels,pin(parts,"J3",jp),"right",net,dist=8)
            esp_side = "left" if epin == "EN" else "right"
            add_stub(wires,labels,pin(parts,"U9",ESP_PIN[epin]),esp_side,net,dist=18)
    # ── ESP32 right-side hierarchical pins (long stubs to clear symbol) ──
    bench_signal_names = [f"PWM{i+1}" for i in range(4)]+[f"ISENSE{i+1}" for i in range(4)]+[f"MPD{i+1}" for i in range(4)]+["CONVST"]
    bench_signal_shapes = {
        **{f"PWM{i+1}": "output" for i in range(4)},
        **{f"ISENSE{i+1}": "input" for i in range(4)},
        **{f"MPD{i+1}": "input" for i in range(4)},
        "CONVST": "output",
    }
    for nm in bench_signal_names:
        add_stub(wires,labels,pin(parts,"U9",ESP_PIN[nm]),"right",f"H:{nm}",dist=30,shape=bench_signal_shapes[nm])
    used_esp_pins = {
        ESP_PIN["GND"], ESP_PIN["VDD3P3"], ESP_PIN["EN"], ESP_PIN["BOOT"],
        ESP_PIN["U0TXD"], ESP_PIN["U0RXD"], ESP_PIN["USB_DM"], ESP_PIN["USB_DP"],
        "40", "41",
    } | {ESP_PIN[nm] for nm in bench_signal_names}
    for pin_num in sorted(set(SYM["Espressif:ESP32-S3-WROOM-1"]["pins"]) - used_esp_pins, key=lambda s: int(s)):
        ncs.append(pin(parts,"U9",pin_num))
    texts=[
        ("Microcontroller — ESP32-S3-WROOM-1 (2.4GHz Wi-Fi b/g/n + Bluetooth LE + native USB) + USB Mini-B + AP2112K-3.3 LDO",30,50,2.2),
        ("USB Mini-B (J1) → USBLC6 ESD (U10) → 22R series resistors → ESP32: D+=GPIO20, D−=GPIO19.  VBUS → power_io.",30,56,1.3),
        ("PWM1-4 -> GPIO16/38/13/14 (LEDC). ISENSE1-4 -> GPIO4/5/6/7 (ADC1_CH3/4/5/6), keeping current telemetry off ADC2.",30,62,1.3),
        ("MPD1-4 -> GPIO2/1/8/9 (ADC1_CH1/0/7/8). CONVST -> GPIO17. UART/EN/BOOT -> J2.",30,68,1.3),
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
    parts={
        "D10":("SCHOTTKY","SS14",FP_SMA,"SS14",LCSC_SCH,80,60),
        "D11":("SCHOTTKY","SS14",FP_SMA,"SS14",LCSC_SCH,80,74),
        "J2":("CONN2","EXT 5V",FP_H2,"","",45,74),
        "J5":("CONN2","LASER PSU",FP_H2,"","",45,110),
        "C50":("C_V","10uF",FP_805,"CL21A106KAYNNNE",LCSC_10UF,105,64),
        "J1":("CONN6","AD7606 out",FP_H6,"","",250,70),
        "J4":("CONN10","LASER+MPD out",FP_H10,"","",340,135),
        "UMPD":("INA4180_TSSOP14","INA4180A1",FP_TSSOP14,"INA4180A1IPWR",LCSC_INA4180,192,132),
        "UREF":("LM4040_DBZ","LM4040C50 5V",FP_SOT23,"LM4040C50IDBZR",LCSC_LM4040,114,122),
        "CINA":("C_V","100nF",FP_402,"CL05B104KO5NNNC",LCSC_100NF,172,88),
        "CREF":("C_V","100nF MPD bias",FP_402,"CL05B104KO5NNNC",LCSC_100NF,128,122),
        "RBIAS":("R_V","2.49k MPD bias",FP_R,"0603WAF2491T5E",LCSC_249K,132,146),
    }
    for i in range(4):
        sense_y = 110 + i*12
        adc_y = 114 + i*12
        parts[f"RMPD{i+1}"] = ("R_H","750R MPD sense",FP_R,"RC0603FR-07750RL",LCSC_750R,218,sense_y)
        parts[f"RADC{i+1}"] = ("R_H","1k ADC",FP_R,"0603WAF1001T5E",LCSC_1K,260,adc_y)
        parts[f"CMPD{i+1}"] = ("C_V","100nF MPD ADC",FP_402,"CL05B104KO5NNNC",LCSC_100NF,280,adc_y+2.54)
    power=[]; wires=[]; labels=[]
    # 5V OR-ing
    add_stub(wires,labels,pin(parts,"D10","1"),"left","H:VBUS_5V",shape="input")
    add_rail(power,wires,"+5V",pin(parts,"D10","2"))
    add_stub(wires,labels,pin(parts,"D11","1"),"left","EXT5V")
    add_stub(wires,labels,pin(parts,"J2","1"),"left","EXT5V")
    add_rail(power,wires,"+5V",pin(parts,"D11","2"))
    add_rail(power,wires,"GND",pin(parts,"J2","2"))
    add_rail(power,wires,"+5V",pin(parts,"C50","1")); add_rail(power,wires,"GND",pin(parts,"C50","2"))
    # laser supply rail
    add_rail(power,wires,"LASER_VP",pin(parts,"J5","1")); add_rail(power,wires,"GND",pin(parts,"J5","2"))
    # AD7606 outputs: 4 TIA outputs + CONVST + GND  (dist=9 so labels clear the header pin numbers)
    for jp,net in [("1","VOUT1"),("2","VOUT2"),("3","VOUT3"),("4","VOUT4"),("5","CONVST")]:
        add_stub(wires,labels,pin(parts,"J1",jp),"left",f"H:{net}",dist=9,shape="input")
    add_rail_dn(power,wires,"GND",pin(parts,"J1","6"))
    # laser outputs: cathode/monitor pairs + common laser anode supply + shield/return ground
    for jp,net in [("1","LASER_N1"),("3","LASER_N2"),("5","LASER_N3"),("7","LASER_N4")]:
        add_stub(wires,labels,pin(parts,"J4",jp),"left",f"H:{net}",dist=9,shape="input")
    for jp,net in [("2","MPD_RAW1"),("4","MPD_RAW2"),("6","MPD_RAW3"),("8","MPD_RAW4")]:
        add_stub(wires,labels,pin(parts,"J4",jp),"left",f"H:{net}",dist=9,shape="input")
    add_rail_dn(power,wires,"LASER_VP",pin(parts,"J4","9"))
    add_rail_dn(power,wires,"GND",pin(parts,"J4","10"))
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
    add_stub(wires,labels,pin(parts,"RBIAS","1"),"right","MPD_BIAS",dist=7)
    add_rail(power,wires,"GND",pin(parts,"RBIAS","2"))

    ina_in_plus = {1:"3", 2:"5", 3:"10", 4:"12"}
    ina_in_minus = {1:"2", 2:"6", 3:"9", 4:"13"}
    ina_out = {1:"1", 2:"7", 3:"8", 4:"14"}
    for i in range(1,5):
        raw = f"MPD_RAW{i}"
        amp = f"MPD_AMP{i}"
        add_stub(wires,labels,pin(parts,f"RMPD{i}","1"),"left",raw,dist=7)
        add_stub(wires,labels,pin(parts,f"RMPD{i}","2"),"right","MPD_BIAS",dist=7)
        add_stub(wires,labels,pin(parts,"UMPD",ina_in_plus[i]),"left",raw,dist=7)
        add_stub(wires,labels,pin(parts,"UMPD",ina_in_minus[i]),"left","MPD_BIAS",dist=7)
        add_stub(wires,labels,pin(parts,"UMPD",ina_out[i]),"right",amp,dist=7)
        add_stub(wires,labels,pin(parts,f"RADC{i}","1"),"left",amp,dist=7)
        add_stub(wires,labels,pin(parts,f"RADC{i}","2"),"right",f"H:MPD{i}",dist=7,shape="output")
        add_stub(wires,labels,pin(parts,f"CMPD{i}","1"),"right",f"H:MPD{i}",dist=5,shape="output")
        add_rail(power,wires,"GND",pin(parts,f"CMPD{i}","2"))
    # PWR_FLAGs — declare the externally-supplied rails as sources (silences ERC)
    junctions=[]
    declare_source(power,wires,"+5V",60,138)
    declare_source(power,wires,"GND",78,138)
    declare_source(power,wires,"LASER_VP",96,138)
    da=pin(parts,"D10","1")                         # D10 anode = VBUS_5V net
    power.append(("PWR_FLAG",da[0],da[1]+9)); wires.append([da,(da[0],da[1]+9)]); junctions.append(da)
    texts=[
        ("Power & I/O  —  USB‖external 5V OR-ing, separate laser supply, AD7606 outputs, laser + monitor-PD outputs",36,16,2.2),
        ("J6 = ext +5V in;  USB VBUS (from J1) ‖ J6 OR-ed via SS14 Schottkys (D5/D6) → +5V.  J5 = laser anode supply (LASER_V+).",36,22,1.3),
        ("J3 → external AD7606 (VOUT1..4 = the 4 TIA outputs + CONVST + GND).  J4 → LASER_N/MPD_RAW pairs + LASER_V+ + GND shield/return.",36,28,1.3),
        ("MPD_RAWx -> 750R sense to MPD_BIAS; INA4180A1 gain=20 -> 1k/100nF -> MPDx ESP32 ADC.",36,34,1.3),
        ("LM4040C50 holds LASER_V+ - MPD_BIAS near 5V; PLT5 typ 150uA -> about 2.25V ADC and about 4.89V monitor-PD reverse bias.",36,40,1.3),
        ("ISENSE headroom: keep I_laser <= 250 mA so V_sense (=I*10ohm) stays inside the ESP32 ADC range with margin.",36,46,1.3),
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
    )

# ═══ ROOT SHEET: laser_controller.kicad_sch ═══
def gl(name,x,y,j):
    ang = 180 if j=="right" else 0
    return f'  (global_label "{name}" (shape bidirectional) (at {fmt(x)} {fmt(y)} {ang}) (effects (font (size 1.27 1.27)) (justify {j})) (uuid {uid()}))'

def build_root():
    P=["(kicad_sch","  (version 20230121)","  (generator eeschema)",f"  (uuid {ROOT_UUID})",
       '  (paper "A2")',"  (title_block",
       '    (title "Laser Controller")',
       '    (date "2026-06-24")','    (rev "v9")','    (company "Vivonics")',"  )"]
    extra=[]
    def sheet(name,file,sx,sy,w,h,pins,fontsz=1.4,pps=7):
        P.append(f"  (sheet (at {fmt(sx)} {fmt(sy)}) (size {fmt(w)} {fmt(h)}) (stroke (width 0.254) (type solid)) (fill (color 0 0 0 0.0))")
        P.append(f"    (uuid {uid()})")
        P.append(f'    (property "Sheetname" "{name}" (at {fmt(sx)} {fmt(sy-3)} 0) (effects (font (size {fontsz} {fontsz})) (justify left bottom)))')
        P.append(f'    (property "Sheetfile" "{file}" (at {fmt(sx)} {fmt(sy+h+4)} 0) (effects (font (size 1.0 1.0)) (justify left top)))')
        lefts=[p for p in pins if p[2]=="left"]; rights=[p for p in pins if p[2]=="right"]
        for grp,side in ((lefts,"left"),(rights,"right")):
            for i,(pn,pin_type,_,net) in enumerate(grp):
                px = sx if side=="left" else sx+w
                py = sy+8+i*pps
                ang = 180 if side=="left" else 0
                just = "right" if side=="left" else "left"
                P.append(f'    (pin "{pn}" {pin_type} (at {fmt(px)} {fmt(py)} {ang}) (effects (font (size 1.0 1.0)) (justify {just})) (uuid {uid()}))')
                ex = px-8 if side=="left" else px+8
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
        sheet(f"LASER_{wl}",f"laser_{wl.lower()}.kicad_sch",240,rows[i],62,34,
              [("PWM_IN","input","left",f"PWM{i+1}"),
               ("LASER_N","output","right",f"LASER_N{i+1}"),
               ("ISENSE","output","right",f"ISENSE{i+1}"),
               ("MPD_RAW","output","right",f"MPD_RAW{i+1}")])
    # MCU (column 3, top) — control pins on the left (facing the lasers)
    mcu_pins=[(f"PWM{i+1}","output","left",f"PWM{i+1}") for i in range(4)]+[
        (f"ISENSE{i+1}","input","left",f"ISENSE{i+1}") for i in range(4)]+[
        (f"MPD{i+1}","input","left",f"MPD{i+1}") for i in range(4)]+[
        ("CONVST","output","left","CONVST"),("VBUS_5V","output","left","VBUS_5V")]
    sheet("MCU_ESP32-S3","mcu.kicad_sch",430,rows[0],95,118,mcu_pins)
    # POWER_IO (column 3, bottom)
    pio_pins=[(f"VOUT{i+1}","input","left",f"VOUT{i+1}") for i in range(4)]+[
        ("CONVST","input","left","CONVST"),("VBUS_5V","input","left","VBUS_5V")]+[
        (f"LASER_N{i+1}","input","left",f"LASER_N{i+1}") for i in range(4)]+[
        (f"MPD_RAW{i+1}","input","left",f"MPD_RAW{i+1}") for i in range(4)]+[
        (f"MPD{i+1}","output","left",f"MPD{i+1}") for i in range(4)]
    sheet("POWER_IO","power_io.kicad_sch",430,rows[3]+24,95,140,pio_pins)

    P+=extra
    P.append(f'  (text "LASER CONTROLLER  ·  Vivonics  ·  rev v9   —   1 channel x 4 wavelengths (IR / RED / GREEN / BLUE)  ·  TIA x4  ·  laser_driver x4  ·  monitor PD ADC x4  ·  mcu  ·  power_io" (at 40 30 0) (effects (font (size 2.4 2.4)) (justify left)) (uuid {uid()}))')
    P.append(f'  (text "Global-label nets join the sheet pins (VOUT1..4, PWM1..4, ISENSE1..4, MPD_RAW1..4, MPD1..4, LASER_N1..4, CONVST, VBUS_5V).   +5V / +3V3 / LASER_V+ / GND are global power.   Each channel = 1 laser + current-sense + internal monitor PD + external/sample PD TIA." (at 40 36 0) (effects (font (size 1.6 1.6)) (justify left)) (uuid {uid()}))')
    P+=['  (sheet_instances','    (path "/" (page "1"))',"  )",")"]
    txt="\n".join(P)+"\n"
    assert sum((c=="(")-(c==")") for c in txt)==0,"paren imbalance in root"
    return txt

# ═══ BOM ═══
def build_bom():
    groups={}; hand={}; ctr={}
    for sheet,(mult,parts) in BOM_REG.items():
        for ref,(sym,val,fp,mpn,lcsc,x,y) in parts.items():
            if sym in HAND or sym in OFFBOARD or lcsc=="":
                hand[(val,mpn)] = hand.get((val,mpn),0)+mult; continue
            for _ in range(mult):
                groups.setdefault((val,fp,lcsc),[]).append(ref)
    rows=["Comment,Designator,Footprint,LCSC"]; n=0
    for (val,fp,lcsc),refs in sorted(groups.items(), key=lambda kv:(kv[0][2],kv[0][0])):
        n+=len(refs); rows.append(f'"{val}","{",".join(refs)}","{fp}","{lcsc}"')
    out="\n".join(rows)+"\n#\n# Hand-add / off-board (not in SMT assembly):\n"
    for (val,mpn),qty in sorted(hand.items()): out+=f"#   {qty}x {val}  ({mpn})\n"
    out+=f"# SMT placements: {n}.  Designators are generated uniquely by the schematic generator.\n"
    out+="# NOTE: 10k uses C269701 (TyoHM/RMC060310KFN class 0603 1%); verify stock at order.\n"
    out+="# NOTE: SFH2201 (C2900216) clear broadband Si PIN PD — covers blue/green/red/IR; JLCPCB Extended (one-time feeder fee).\n"
    return out

KICAD_PRO='{\n  "board": {"design_settings": {"rules": {}}},\n  "meta": {"filename": "laser_controller.kicad_pro", "version": 1},\n  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},\n  "sheets": [],\n  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}\n}\n'

def atomic_write(path, text):
    path = Path(path)
    if not path.is_absolute():
        path = OUT_DIR / path
    tmp=f"{path}.tmp.{os.getpid()}"
    with open(tmp,"w") as f: f.write(text)
    os.replace(tmp,path)

def main():
    BOM_REG.clear()
    sheets = {
        **{f"tia_{wl.lower()}.kicad_sch": build_tia_channel(f"TIA_{wl}") for wl in WL},
        **{f"laser_{wl.lower()}.kicad_sch": build_laser_driver(f"LASER_{wl}") for wl in WL},
        "mcu.kicad_sch": build_mcu(),
        "power_io.kicad_sch": build_power_io(),
        "laser_controller.kicad_sch": build_root(),
    }
    for fname, content in sheets.items():
        atomic_write(fname, content)
        print(f"  wrote {fname} ({len(content)} bytes, {content.count(chr(10))} lines)")
    atomic_write("laser_controller_bom_jlcpcb.csv", build_bom())
    print("  wrote laser_controller_bom_jlcpcb.csv")
    if not (OUT_DIR / "laser_controller.kicad_pro").exists():
        atomic_write("laser_controller.kicad_pro", KICAD_PRO)
        print("  wrote laser_controller.kicad_pro")


if __name__ == "__main__":
    main()
