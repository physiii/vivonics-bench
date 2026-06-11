#!/usr/bin/env python3
"""Generate reactor_tia.kicad_sch + reactor_tia_bom_jlcpcb.csv.

Reactor TIA front-end: **two independent channels, one op-amp each** (BPW34 ->
OPA380AID transimpedance amp, TIA only -- no 2nd-stage filter).  Use CH2 as a
matched ratiometric reference PD (laser drift cancel) or a 2nd optical plane.
Anti-aliasing is handed to the AD7606 oversampling instead of an analog
Sallen-Key stage (see REACTOR_TIA_DESIGN.md sec.7 / sec.10 v1).

Laser control: four active-high 2N7000 low-side switches for green, red,
infrared, and blue laser modules.  The laser modules stay current-limited
externally; this board only switches their low side and shares ground with the
Pi/ADC.  Each GPIO has a 330R series gate resistor and each MOSFET gate has a
100k pulldown.

Shared across both channels: one VBIAS divider (matched bias), the +5 V/GND
rails, decoupling, and the output/power headers.  Each channel connects to the
shared nets purely by net-label name (VBIAS / +5V / GND), so the blocks are
self-contained.

Layout: CH1 top, CH2 bottom (48 mm apart); divider + decoupling along the bottom;
J1/J2 carry TIA output/power, and J3/J4/J5 carry laser control/output/power on
the right.  Same symbol lib, footprints, and office BOM conventions as the rest
of the bench (KiCad (version 20230121) (generator eeschema); custom fields
`Part Number` (MPN) and `LCSC`).
Schematic Y is DOWN; lib symbols are Y-UP: lib pin (lx,ly) on a part at (px,py)
lands at schematic (px+lx, py-ly).  Re-run:  python3 gen_reactor_tia_sch.py
"""
from __future__ import annotations
import os

ROOT = "a1b2c3d4-2c00-4000-8000-000000000001"
_ctr = [0]
USE_POWER_SYMBOLS = True


def uid():
    _ctr[0] += 1
    return f"a1b2c3d4-2c00-4000-8000-{_ctr[0]:012d}"


# pins: num -> (lx, ly, angle, name, etype, length)   [angle = tip->body, lib Y-up]
SYM = {
 "R_H": {"pins": {"1": (-3.81, 0, 0, "~", "passive", 1.27), "2": (3.81, 0, 180, "~", "passive", 1.27)},
         "glyph": [[(-2.54, 1.016), (2.54, 1.016), (2.54, -1.016), (-2.54, -1.016), (-2.54, 1.016)]], "texts": []},
 "R_V": {"pins": {"1": (0, 3.81, 270, "~", "passive", 1.27), "2": (0, -3.81, 90, "~", "passive", 1.27)},
         "glyph": [[(-1.016, 2.54), (1.016, 2.54), (1.016, -2.54), (-1.016, -2.54), (-1.016, 2.54)]], "texts": []},
 "C_H": {"pins": {"1": (-2.54, 0, 0, "~", "passive", 1.905), "2": (2.54, 0, 180, "~", "passive", 1.905)},
         "glyph": [[(-0.635, -1.778), (-0.635, 1.778)], [(0.635, -1.778), (0.635, 1.778)]], "texts": []},
 "C_V": {"pins": {"1": (0, 2.54, 270, "~", "passive", 1.905), "2": (0, -2.54, 90, "~", "passive", 1.905)},
         "glyph": [[(-1.778, 0.635), (1.778, 0.635)], [(-1.778, -0.635), (1.778, -0.635)]], "texts": []},
 "PD": {"pins": {"1": (0, 3.81, 270, "K", "passive", 1.27), "2": (0, -3.81, 90, "A", "passive", 1.27)},
        "glyph": [[(-1.524, -1.27), (1.524, -1.27), (0, 1.27), (-1.524, -1.27)],
                  [(-1.524, 1.27), (1.524, 1.27)],
                  [(-4.2, 2.6), (-2.7, 1.6)], [(-3.1, 1.4), (-2.7, 1.6), (-2.9, 2.0)],
                  [(-3.6, 3.3), (-2.1, 2.3)], [(-2.5, 2.1), (-2.1, 2.3), (-2.3, 2.7)]], "texts": []},
 "OPA_N": {"pins": {"2": (-7.62, 2.54, 0, "-", "input", 2.54), "3": (-7.62, -2.54, 0, "+", "input", 2.54),
                    "6": (7.62, 0, 180, "", "output", 2.54), "7": (0, 7.62, 270, "V+", "power_in", 2.54),
                    "4": (0, -7.62, 90, "V-", "power_in", 2.54)},
           "glyph": [[(-5.08, 5.08), (5.08, 0), (-5.08, -5.08), (-5.08, 5.08)]],
           "texts": [("-", -3.4, 2.54, 1.27), ("+", -3.6, -2.54, 1.27)]},
 "CONN4": {"pins": {"1": (-5.08, 3.81, 0, "1", "passive", 2.54), "2": (-5.08, 1.27, 0, "2", "passive", 2.54),
                    "3": (-5.08, -1.27, 0, "3", "passive", 2.54), "4": (-5.08, -3.81, 0, "4", "passive", 2.54)},
           "glyph": [[(-2.54, 5.08), (2.54, 5.08), (2.54, -5.08), (-2.54, -5.08), (-2.54, 5.08)]], "texts": []},
 "CONN2": {"pins": {"1": (-5.08, 1.27, 0, "1", "passive", 2.54), "2": (-5.08, -1.27, 0, "2", "passive", 2.54)},
           "glyph": [[(-2.54, 2.54), (2.54, 2.54), (2.54, -2.54), (-2.54, -2.54), (-2.54, 2.54)]], "texts": []},
 "CONN5": {"pins": {"1": (-5.08, 5.08, 0, "1", "passive", 2.54), "2": (-5.08, 2.54, 0, "2", "passive", 2.54),
                    "3": (-5.08, 0, 0, "3", "passive", 2.54), "4": (-5.08, -2.54, 0, "4", "passive", 2.54),
                    "5": (-5.08, -5.08, 0, "5", "passive", 2.54)},
           "glyph": [[(-2.54, 6.35), (2.54, 6.35), (2.54, -6.35), (-2.54, -6.35), (-2.54, 6.35)]], "texts": []},
 "CONN8": {"pins": {"1": (-5.08, 8.89, 0, "1", "passive", 2.54), "2": (-5.08, 6.35, 0, "2", "passive", 2.54),
                    "3": (-5.08, 3.81, 0, "3", "passive", 2.54), "4": (-5.08, 1.27, 0, "4", "passive", 2.54),
                    "5": (-5.08, -1.27, 0, "5", "passive", 2.54), "6": (-5.08, -3.81, 0, "6", "passive", 2.54),
                    "7": (-5.08, -6.35, 0, "7", "passive", 2.54), "8": (-5.08, -8.89, 0, "8", "passive", 2.54)},
           "glyph": [[(-2.54, 10.16), (2.54, 10.16), (2.54, -10.16), (-2.54, -10.16), (-2.54, 10.16)]], "texts": []},
 "MOS_N": {"pins": {"3": (0, 5.08, 270, "D", "passive", 1.27), "2": (-5.08, 0, 0, "G", "input", 1.27),
                    "1": (0, -5.08, 90, "S", "passive", 1.27)},
           "glyph": [[(-2.54, 2.54), (-2.54, -2.54)], [(0, 2.54), (0, -2.54)],
                     [(-2.54, 0), (-0.635, 0)], [(0, 3.81), (0, 2.54)], [(0, -2.54), (0, -3.81)],
                     [(-0.762, -1.27), (0, -2.032), (0.762, -1.27)]], "texts": []},
 "+5V": {"power": True, "pins": {"1": (0, 0, 90, "+5V", "power_in", 0)},
         "glyph": [[(0, 0), (0, 2.54)], [(-1.27, 1.524), (0, 2.54), (1.27, 1.524)]], "texts": []},
 "GND": {"power": True, "pins": {"1": (0, 0, 270, "GND", "power_in", 0)},
         "glyph": [[(0, 0), (0, -2.032)], [(-2.032, -2.032), (2.032, -2.032)],
                   [(-1.27, -2.794), (1.27, -2.794)], [(-0.508, -3.556), (0.508, -3.556)]], "texts": []},
}
REFLET = {"R_H": "R", "R_V": "R", "C_H": "C", "C_V": "C", "PD": "D", "OPA_N": "U", "CONN4": "J", "CONN5": "J", "CONN8": "J", "CONN2": "J", "MOS_N": "Q"}

FP_R = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_603 = "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_402 = "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"
FP_805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SO8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_PD = "OptoDevice:Vishay_BPW34"
FP_Q_TO92 = "Package_TO_SOT_THT:TO-92_Inline"
FP_H4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
FP_H5 = "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
FP_H8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
FP_H2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

OX, DX = 88, 60                 # op-amp x, photodiode x (both channels)
CHANNELS = [(1, 84), (2, 132)]  # (index, op-amp centre y);  48 mm apart
DRIVER_CHANNELS = [
    # color, gpio net, laser low-side net, q ref, series R, pulldown R, schematic y
    ("GREEN", "GPIO24_GREEN", "GREEN_LASER_N", "Q1", "R6", "R10", 72),
    ("RED", "GPIO15_RED", "RED_LASER_N", "Q2", "R7", "R11", 96),
    ("INFRARED", "GPIO23_INFRARED", "INFRARED_LASER_N", "Q3", "R8", "R12", 120),
    ("BLUE", "GPIO14_BLUE", "BLUE_LASER_N", "Q4", "R9", "R13", 144),
]

# ref -> (sym, value, footprint, mpn, lcsc, x, y)
PARTS: dict = {}
for _n, _OY in CHANNELS:        # per-channel TIA block
    PARTS[f"D{_n}"] = ("PD", "BPW34", FP_PD, "BPW34", "C85128", DX, _OY + 3)
    PARTS[f"U{_n}"] = ("OPA_N", "OPA380AID", FP_SO8, "OPA380AID", "C201677", OX, _OY)
    PARTS[f"R{_n}"] = ("R_H", "10M", FP_R, "0603WAF1005T5E", "C57129", OX + 2, _OY - 24)
    PARTS[f"C{_n}"] = ("C_H", "10pF C0G", FP_603, "CC0603JRNPO9BN100", "C168544", OX + 2, _OY - 16)
PARTS.update({           # shared: VBIAS divider, decoupling, headers
 "R3": ("R_V", "100k", FP_R, "0603WAF1003T5E", "C25803", 50, 159),
 "R4": ("R_V", "10k", FP_R, "0603WAF1002T5E", "C25804", 50, 173),
 "R5": ("R_H", "10k", FP_R, "0603WAF1002T5E", "C25804", 62, 162.81),
 "C3": ("C_V", "10uF", FP_805, "CL21A106KAYNNNE", "C15850", 80, 168),
 "C4": ("C_V", "100nF", FP_402, "CL05B104KO5NNNC", "C1525", 110, 168),
 "C5": ("C_V", "100nF", FP_402, "CL05B104KO5NNNC", "C1525", 126, 168),
 "C6": ("C_V", "10uF", FP_805, "CL21A106KAYNNNE", "C15850", 142, 168),
 "C7": ("C_V", "1uF", FP_402, "CL05A105KA5NQNC", "C52923", 158, 168),
 "J1": ("CONN4", "Conn_01x04", FP_H4, "", "", 190, 100),
 "J2": ("CONN2", "Conn_01x02", FP_H2, "", "", 190, 150),
 "J3": ("CONN5", "Pi GPIO control", FP_H5, "", "", 356, 70),
 "J4": ("CONN8", "Laser outputs", FP_H8, "", "", 356, 118),
 "J5": ("CONN2", "Laser power", FP_H2, "", "", 356, 156),
})
for _color, _gpio, _laser, _q, _series, _pulldown, _y in DRIVER_CHANNELS:
    PARTS[_q] = ("MOS_N", "2N7000", FP_Q_TO92, "2N7000", "", 272, _y)
    PARTS[_series] = ("R_H", "330R", FP_R, "0603WAF3300T5E", "C23138", 242, _y)
    PARTS[_pulldown] = ("R_V", "100k", FP_R, "0603WAF1003T5E", "C25803", 252, _y + 3.81)
HAND = {"PD", "CONN4", "CONN5", "CONN8", "CONN2", "MOS_N"}


def pin(ref, num):
    sym, *_rest, x, y = PARTS[ref]
    lx, ly = SYM[sym]["pins"][num][:2]
    return (x + lx, y - ly)


POWER, WIRES, JUNCTIONS, LABELS = [], [], [], []

for _n, _OY in CHANNELS:                       # ----- per-channel wiring -----
    LR, RR = OX - 7.62, OX + 10                 # left rail (-IN x = 80.38), right rail (98)
    CfY, RfY = _OY - 16, _OY - 24               # feedback tap heights
    POWER += [("+5V", OX, _OY - 11), ("GND", OX, _OY + 11), ("GND", DX, _OY + 10.5)]
    WIRES += [
        [(DX, _OY - 0.81), (DX, _OY - 2.54), (LR, _OY - 2.54)],   # D cathode -> -IN
        [(DX, _OY + 6.81), (DX, _OY + 10.5)],                     # D anode -> GND (zero bias)
        [(LR, _OY - 2.54), (LR, CfY), (LR, RfY)],                 # left feedback rail
        [pin(f"R{_n}", "1"), (LR, RfY)], [pin(f"R{_n}", "2"), (RR, RfY)],
        [pin(f"C{_n}", "1"), (LR, CfY)], [pin(f"C{_n}", "2"), (RR, CfY)],
        [(RR, _OY), (RR, CfY), (RR, RfY)],                        # right feedback rail
        [pin(f"U{_n}", "6"), (RR, _OY)], [(RR, _OY), (RR + 10, _OY)],  # out + tap
        [pin(f"U{_n}", "3"), (OX - 14, _OY + 2.54)],              # +IN stub (VBIAS by name)
        [pin(f"U{_n}", "7"), (OX, _OY - 11)], [pin(f"U{_n}", "4"), (OX, _OY + 11)],
    ]
    JUNCTIONS += [(LR, _OY - 2.54), (LR, CfY), (RR, CfY), (RR, _OY)]
    LABELS += [(f"V_CH{_n}", RR + 6, _OY, "left"), ("VBIAS", OX - 9, _OY + 2.54, "right")]

POWER += [("+5V", 50, 152), ("GND", 50, 180.5), ("GND", 80, 174)]     # divider rails
WIRES += [                                                            # ----- VBIAS divider -----
 [pin("R3", "1"), (50, 152)], [pin("R3", "2"), pin("R4", "1")],
 [pin("R5", "1"), (50, 162.81)], [pin("R4", "2"), (50, 180.5)],
 [pin("R5", "2"), (80, 162.81), pin("C3", "1")], [pin("C3", "2"), (80, 174)],
]
JUNCTIONS += [(50, 162.81)]
LABELS += [("VBIAS", 74, 162.81, "left")]

for _x in (110, 126, 142, 158):                                       # ----- decoupling -----
    POWER += [("+5V", _x, 162), ("GND", _x, 174)]
WIRES += [[pin(c, "1"), (PARTS[c][5], 162)] for c in ("C4", "C5", "C6", "C7")]
WIRES += [[pin(c, "2"), (PARTS[c][5], 174)] for c in ("C4", "C5", "C6", "C7")]

WIRES += [                                                            # ----- headers -----
 [pin("J1", "1"), (179, 96.19)], [pin("J1", "2"), (179, 98.73)],
 [pin("J1", "3"), (179, 101.27)], [pin("J1", "4"), (179, 103.81)],
 [pin("J2", "1"), (179, 148.73)], [pin("J2", "2"), (179, 151.27)],
]
LABELS += [
 ("V_CH1", 179, 96.19, "left"), ("V_CH2", 179, 98.73, "left"),
 ("GND", 179, 101.27, "left"), ("+5V", 179, 103.81, "left"),
 ("+5V", 179, 148.73, "left"), ("GND", 179, 151.27, "left"),
]

for _color, _gpio, _laser, _q, _series, _pulldown, _y in DRIVER_CHANNELS:       # ----- 2N7000 laser drivers -----
    gate_x = PARTS[_pulldown][5]
    q_x = PARTS[_q][5]
    gpio_x = pin(_series, "1")[0] - 4
    POWER += [("GND", gate_x, _y + 12), ("GND", q_x, _y + 10)]
    WIRES += [
        [(gpio_x, _y), pin(_series, "1")],                                      # GPIO label -> series gate resistor
        [pin(_series, "2"), (gate_x, _y), pin(_pulldown, "1"), pin(_q, "2")],    # series R -> MOSFET gate
        [pin(_pulldown, "2"), (gate_x, _y + 12)],                                # gate pulldown -> GND
        [pin(_q, "1"), (q_x, _y + 10)],                                          # source -> GND
        [pin(_q, "3"), (q_x, _y - 8), (q_x + 18, _y - 8)],                       # drain -> laser low side
    ]
    JUNCTIONS += [(gate_x, _y)]
    LABELS += [(_gpio, gpio_x, _y, "right"), (_laser, q_x + 18, _y - 8, "left")]

_j3_labels = ["GPIO24_GREEN", "GPIO15_RED", "GPIO23_INFRARED", "GPIO14_BLUE", "GND"]
for _idx, _label in enumerate(_j3_labels, start=1):
    _p = pin("J3", str(_idx))
    WIRES.append([_p, (_p[0] - 6, _p[1])])
    LABELS.append((_label, _p[0] - 6, _p[1], "right"))

_j4_labels = [
    "LASER+", "GREEN_LASER_N",
    "LASER+", "RED_LASER_N",
    "LASER+", "INFRARED_LASER_N",
    "LASER+", "BLUE_LASER_N",
]
for _idx, _label in enumerate(_j4_labels, start=1):
    _p = pin("J4", str(_idx))
    WIRES.append([_p, (_p[0] - 6, _p[1])])
    LABELS.append((_label, _p[0] - 6, _p[1], "right"))

WIRES += [[pin("J5", "1"), (345, 154.73)], [pin("J5", "2"), (345, 157.27)]]
LABELS += [("LASER+", 345, 154.73, "right"), ("GND", 345, 157.27, "right")]
if not USE_POWER_SYMBOLS:
    for kind, x, y in POWER:
        LABELS.append((kind, x, y, "left"))
    POWER = []

TEXTS = [  # ASCII only (KiCad stroke-font export mangles em-dash / micro / approx)
 ("Reactor TIA  -  2 channels, one op-amp each  (BPW34 -> OPA380 TIA)", 40, 34, 2.6),
 ("One op-amp per channel = TIA only, no 2nd-stage filter.  R_f -> ~3 V pedestal;  C_f -> ~1.6 kHz pole.", 42, 44, 1.6),
 ("Anti-alias handled by AD7606 oversampling.  CH2 = matched: ratiometric reference PD (drift cancel) or a 2nd plane.", 42, 49, 1.6),
 ("Channel 1", 26, 86, 2.2),
 ("Channel 2", 26, 134, 2.2),
 ("VBIAS divider  (0.45 V)  -  shared by both channels", 40, 190, 1.8),
 ("decoupling  (100 nF / amp + 10 uF + 1 uF bulk)", 104, 156, 1.6),
 ("4x 2N7000 low-side laser drivers  -  green/red/infrared/blue", 226, 28, 1.8),
 ("Each GPIO path: input -> 330R series gate resistor -> 2N7000 gate, with 100k pulldown at the gate.", 226, 34, 1.25),
 ("J3 = Pi GPIO control.  J4 = laser module outputs.  J5 = current-limited laser supply + common ground.", 226, 39, 1.25),
 ("Do not route laser switching return through the TIA summing-node area; star back to common ground.", 226, 44, 1.25),
 ("D1, D2 / Q1-Q4 / J1-J5 = hand-add (THT)", 168, 132, 1.6),
]


def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def sym_def(name):
    s = SYM[name]
    out = [f'  (symbol "viv:{name}"']
    if s.get("power"):
        out.append("    (power)")
    if name not in ("CONN4", "CONN5", "CONN8", "CONN2"):
        out.append("    (pin_numbers hide)")
    out += ["    (pin_names (offset 1.016) hide)",
            f"    (in_bom {'no' if s.get('power') else 'yes'}) (on_board yes)",
            f'    (property "Reference" "{"#PWR" if s.get("power") else REFLET[name]}" (at 0 {3.6 if s.get("power") else 6.6} 0) (effects (font (size 1.27 1.27))' + (" hide" if s.get("power") else "") + "))",
            f'    (property "Value" "{name}" (at 0 {3.0 if s.get("power") else -6.6} 0) (effects (font (size 1.27 1.27))))',
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (symbol "{name}_0_1"']
    for poly in s["glyph"]:
        pts = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in poly)
        out.append(f"      (polyline (pts {pts}) (stroke (width 0.1524) (type default)) (fill (type none)))")
    for t, x, y, sz in s["texts"]:
        out.append(f'      (text "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size {sz} {sz}))))')
    out.append("    )")
    out.append(f'    (symbol "{name}_1_1"')
    hide_num = s.get("power") or name in ("R_H", "R_V", "C_H", "C_V", "PD")
    for num, (lx, ly, ang, pname, et, ln) in s["pins"].items():
        out.append(f'      (pin {et} line (at {fmt(lx)} {fmt(ly)} {ang}) (length {fmt(ln)}) '
                   f'(name "{pname}" (effects (font (size 1.0 1.0)))) '
                   f'(number "{num}" (effects (font (size 1.0 1.0))' + (" hide" if hide_num else "") + ")))")
    out += ["    )", "  )"]
    return "\n".join(out)


def emit_part(ref, sym, val, fp, mpn, lcsc, x, y):
    L = [f'  (symbol (lib_id "viv:{sym}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
         "    (in_bom yes) (on_board yes) (dnp no)", f"    (uuid {uid()})",
         f'    (property "Reference" "{ref}" (at {fmt(x+5.6)} {fmt(y-1.4)} 0) (effects (font (size 1.0 1.0)) (justify left)))',
         f'    (property "Value" "{val}" (at {fmt(x+5.6)} {fmt(y+1.4)} 0) (effects (font (size 1.0 1.0)) (justify left)))',
         f'    (property "Footprint" "{fp}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))',
         f'    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))',
         f'    (property "Part Number" "{mpn}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))',
         f'    (property "LCSC" "{lcsc}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.0 1.0)) hide))']
    for num in SYM[sym]["pins"]:
        L.append(f'    (pin "{num}" (uuid {uid()}))')
    L += ["    (instances", '      (project "reactor_tia"',
          f'        (path "/{ROOT}" (reference "{ref}") (unit 1))', "      )", "    )", "  )"]
    return "\n".join(L)


def emit_power(kind, x, y, n):
    ry = y + 3.0 if kind == "GND" else y - 3.0
    vy = y + 4.2 if kind == "GND" else y - 3.2
    return "\n".join([
        f'  (symbol (lib_id "viv:{kind}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
        "    (in_bom no) (on_board yes) (dnp no)", f"    (uuid {uid()})",
        f'    (property "Reference" "#PWR{n:02d}" (at {fmt(x)} {fmt(ry)} 0) (effects (font (size 1.0 1.0)) hide))',
        f'    (property "Value" "{kind}" (at {fmt(x)} {fmt(vy)} 0) (effects (font (size 1.27 1.27))))',
        '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.0 1.0)) hide))',
        '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.0 1.0)) hide))',
        f'    (pin "1" (uuid {uid()}))', "    (instances", '      (project "reactor_tia"',
        f'        (path "/{ROOT}" (reference "#PWR{n:02d}") (unit 1))', "      )", "    )", "  )"])


def build_sch():
    P = ["(kicad_sch", "  (version 20230121)", "  (generator eeschema)", f"  (uuid {ROOT})",
         '  (paper "A3")', "  (title_block", '    (title "Reactor TIA + 4-channel 2N7000 laser driver")',
         '    (date "2026-06-06")', '    (rev "v3")', '    (company "Vivonics")', "  )", "  (lib_symbols"]
    for name in SYM:
        P.append(sym_def(name))
    P.append("  )")
    for ref, t in PARTS.items():
        P.append(emit_part(ref, *t))
    for i, (kind, x, y) in enumerate(POWER, 1):
        P.append(emit_power(kind, x, y, i))
    for poly in WIRES:
        for a, b in zip(poly, poly[1:]):
            P.append(f"  (wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})) "
                     f"(stroke (width 0) (type default)) (uuid {uid()}))")
    for x, y in JUNCTIONS:
        P.append(f"  (junction (at {fmt(x)} {fmt(y)}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))")
    for t, x, y, j in LABELS:
        P.append(f'  (label "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (justify {j} bottom)) (uuid {uid()}))')
    for t, x, y, sz in TEXTS:
        P.append(f'  (text "{t}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size {sz} {sz})) (justify left)) (uuid {uid()}))')
    P += ['  (sheet_instances', '    (path "/" (page "1"))', "  )", ")"]
    txt = "\n".join(P) + "\n"
    assert sum((c == "(") - (c == ")") for c in txt) == 0, "paren imbalance"
    return txt


def build_bom():
    groups = {}
    for ref, (sym, val, fp, mpn, lcsc, x, y) in PARTS.items():
        if sym in HAND:
            continue
        groups.setdefault((val, fp, lcsc), []).append(ref)

    def k(r):
        return (r.rstrip("0123456789"), int(r[len(r.rstrip("0123456789")):] or 0))
    rows = ["Comment,Designator,Footprint,LCSC"]
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: k(sorted(kv[1], key=k)[0])):
        rows.append(f'"{val}","{",".join(sorted(refs, key=k))}","{fp}","{lcsc}"')
    return "\n".join(rows) + "\n"


def atomic_write(path, text):
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def main():
    atomic_write("reactor_tia.kicad_sch", build_sch())
    atomic_write("reactor_tia_bom_jlcpcb.csv", build_bom())
    n = sum(1 for v in PARTS.values() if v[0] not in HAND)
    print(f"wrote reactor_tia.kicad_sch + reactor_tia_bom_jlcpcb.csv ({n} SMT, {len(PARTS)} total)")


if __name__ == "__main__":
    main()
