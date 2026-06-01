#!/usr/bin/env python3
"""Generate reactor_tia.kicad_sch + reactor_tia_bom_jlcpcb.csv (OPA380 reactor TIA).

Hand-laid-out, readable schematic: left-to-right signal flow
  D1 photodiode -> U1 TIA (R_f||C_f feedback over the top) -> R-R-C-C
  Sallen-Key anti-alias (U2) -> J1 output.  Bias divider bottom-left.
Real wires + power symbols (+5V / GND) + a few net labels (VBIAS, V_TIA, V_FILT).

Conventions copied from the office board (access-controller): KiCad
(version 20230121)(generator eeschema); custom fields `Part Number` (MPN) and
`LCSC`; JLCPCB BOM = Comment,Designator,Footprint,LCSC (quoted, grouped).

Design: 2x OPA380AID single (LCSC C201677 - the OPA2380 dual is not stocked at
JLCPCB). VBIAS from a +5V divider (no precision ref needed: ratiometric read).
R_f=10M. Filter R2=R3=68k, C2=2.2n, C3=1n -> fc ~1.57 kHz. D1 (BPW34, THT) and
J1/J2 (headers) are hand-add, excluded from the SMT BOM.

Value strings are concise (= BOM Comment); full spec lives in Part Number+LCSC.
ASCII text only (KiCad stroke-font export mangles em-dash / micro / approx).
Tap points are polyline vertices (endpoint-to-endpoint connects; mid-wire T's do
not net-connect, so 3-way taps also get an explicit junction). Re-run:
  python3 gen_reactor_tia_sch.py    (atomic write; verify with kicad-cli netlist)
Schematic Y is DOWN; lib symbols are Y-UP: lib pin (lx,ly) on a part at (px,py)
lands at schematic (px+lx, py-ly).
"""
from __future__ import annotations
import os

ROOT = "a1b2c3d4-0000-4000-8000-000000000001"
_ctr = [0]
USE_POWER_SYMBOLS = True


def uid():
    _ctr[0] += 1
    return f"a1b2c3d4-0000-4000-8000-{_ctr[0]:012d}"


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
 "+5V": {"power": True, "pins": {"1": (0, 0, 90, "+5V", "power_in", 0)},
         "glyph": [[(0, 0), (0, 2.54)], [(-1.27, 1.524), (0, 2.54), (1.27, 1.524)]], "texts": []},
 "GND": {"power": True, "pins": {"1": (0, 0, 270, "GND", "power_in", 0)},
         "glyph": [[(0, 0), (0, -2.032)], [(-2.032, -2.032), (2.032, -2.032)],
                   [(-1.27, -2.794), (1.27, -2.794)], [(-0.508, -3.556), (0.508, -3.556)]], "texts": []},
}
REFLET = {"R_H": "R", "R_V": "R", "C_H": "C", "C_V": "C", "PD": "D", "OPA_N": "U", "CONN4": "J", "CONN2": "J"}

FP_R = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_603 = "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_402 = "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"
FP_805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SO8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_PD = "OptoDevice:Vishay_BPW34"
FP_H4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
FP_H2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

# ref -> (sym, value, footprint, mpn, lcsc, x, y)
PARTS = {
 "D1": ("PD", "BPW34", FP_PD, "BPW34", "C85128", 60, 103),
 "U1": ("OPA_N", "OPA380AID", FP_SO8, "OPA380AID", "C201677", 88, 100),
 "R1": ("R_H", "10M", FP_R, "0603WAF1005T5E", "C57129", 90, 80),
 "C1": ("C_H", "10pF C0G", FP_603, "CC0603JRNPO9BN100", "C168544", 90, 84),
 "R2": ("R_H", "68k", FP_R, "0603WAF6802T5E", "C36871", 118, 102.54),
 "R3": ("R_H", "68k", FP_R, "0603WAF6802T5E", "C36871", 140, 102.54),
 "C2": ("C_V", "2.2nF C0G", FP_603, "CC0603JRNPO9BN222", "C108194", 130, 96),
 "C3": ("C_V", "1nF C0G", FP_603, "CC0603JRNPO9BN102", "C57112", 150, 109),
 "U2": ("OPA_N", "OPA380AID", FP_SO8, "OPA380AID", "C201677", 165, 100),
 "R4": ("R_V", "100k", FP_R, "0603WAF1003T5E", "C25803", 50, 124),
 "R5": ("R_V", "10k", FP_R, "0603WAF1002T5E", "C25804", 50, 138),
 "R6": ("R_H", "10k", FP_R, "0603WAF1002T5E", "C25804", 62, 127.81),
 "C4": ("C_V", "10uF", FP_805, "CL21A106KAYNNNE", "C15850", 72, 133),
 "C5": ("C_V", "100nF", FP_402, "CL05B104KO5NNNC", "C1525", 106, 120),
 "C6": ("C_V", "1uF", FP_402, "CL05A105KA5NQNC", "C52923", 122, 120),
 "C7": ("C_V", "100nF", FP_402, "CL05B104KO5NNNC", "C1525", 138, 120),
 "J1": ("CONN4", "Conn_01x04", FP_H4, "", "", 200, 103),
 "J2": ("CONN2", "Conn_01x02", FP_H2, "", "", 200, 140),
}
HAND = {"PD", "CONN4", "CONN2"}


def pin(ref, num):
    sym, *_rest, x, y = PARTS[ref]
    lx, ly = SYM[sym]["pins"][num][:2]
    return (x + lx, y - ly)


POWER = [
 ("+5V", 88, 89), ("+5V", 165, 89), ("+5V", 106, 114), ("+5V", 122, 114), ("+5V", 138, 114), ("+5V", 50, 117),
 ("GND", 60, 110.5), ("GND", 88, 111), ("GND", 165, 111), ("GND", 50, 145.5), ("GND", 72, 139),
 ("GND", 150, 115), ("GND", 106, 126), ("GND", 122, 126), ("GND", 138, 126),
]

WIRES = [
 # --- TIA ---
 [pin("D1", "2"), (60, 110.5)],
 [pin("D1", "1"), (60, 97.46), pin("U1", "2")],
 [(80.38, 97.46), (80.38, 84), (80.38, 80)],
 [pin("R1", "1"), (80.38, 80)],
 [pin("C1", "1"), (80.38, 84)],
 [pin("R1", "2"), (98, 80)],
 [pin("C1", "2"), (98, 84)],
 [(98, 100), (98, 84), (98, 80)],
 [pin("U1", "6"), (98, 100)],
 [pin("U1", "3"), (74, 102.54)],
 [pin("U1", "7"), (88, 89)],
 [pin("U1", "4"), (88, 111)],
 # --- TIA out -> filter ---
 [(98, 100), (108, 100), (108, 102.54), pin("R2", "1")],
 [pin("R2", "2"), (130, 102.54), pin("R3", "1")],
 [(130, 102.54), pin("C2", "2")],
 [pin("C2", "1"), (130, 90)],
 [pin("R3", "2"), (150, 102.54), pin("U2", "3")],
 [(150, 102.54), pin("C3", "1")],
 [pin("C3", "2"), (150, 115)],
 [pin("U2", "2"), (157.38, 90)],
 [(130, 90), (157.38, 90), (176, 90), (176, 100), pin("U2", "6")],
 [pin("U2", "7"), (165, 89)],
 [pin("U2", "4"), (165, 111)],
 [(176, 100), (185, 100)],
 # --- output connector ---
 [pin("J1", "1"), (189, 99.19)],
 [pin("J1", "2"), (189, 101.73)],
 [pin("J1", "3"), (189, 104.27)],
 [pin("J1", "4"), (189, 106.81)],
 # --- bias divider ---
 [pin("R4", "1"), (50, 117)],
 [pin("R4", "2"), pin("R5", "1")],
 [pin("R6", "1"), (50, 127.81)],
 [pin("R5", "2"), (50, 145.5)],
 [pin("R6", "2"), (72, 127.81), pin("C4", "1")],
 [pin("C4", "2"), (72, 139)],
 # --- decoupling ---
 [pin("C5", "1"), (106, 114)], [pin("C5", "2"), (106, 126)],
 [pin("C6", "1"), (122, 114)], [pin("C6", "2"), (122, 126)],
 [pin("C7", "1"), (138, 114)], [pin("C7", "2"), (138, 126)],
 # --- power input ---
 [pin("J2", "1"), (189, 138.73)],
 [pin("J2", "2"), (189, 141.27)],
]

JUNCTIONS = [(80.38, 97.46), (80.38, 84), (98, 100), (98, 84),
             (130, 102.54), (150, 102.54), (157.38, 90), (176, 100), (50, 127.81)]

LABELS = [
 ("VBIAS", 74, 102.54, "right"), ("VBIAS", 66, 127.81, "left"),
 ("V_TIA", 104, 100, "left"), ("V_TIA", 189, 99.19, "left"),
 ("V_FILT", 185, 100, "left"), ("V_FILT", 189, 101.73, "left"),
 ("GND", 189, 104.27, "left"), ("+5V", 189, 106.81, "left"),
 ("+5V", 189, 138.73, "left"), ("GND", 189, 141.27, "left"),
]
if not USE_POWER_SYMBOLS:
    for kind, x, y in POWER:
        LABELS.append((kind, x, y, "left"))
    POWER = []

TEXTS = [  # ASCII only
 ("Reactor TIA  -  bacteriorhodopsin M-state red read", 48, 60, 3.0),
 ("TIA  (size R_f for ~3 V red pedestal)", 70, 70, 1.8),
 ("anti-alias  fc ~1.57 kHz", 150, 78, 1.8),
 ("VBIAS divider  (0.45 V)", 40, 114, 1.8),
 ("decoupling", 116, 110, 1.8),
 ("D1 / J1 / J2 = hand-add (THT)", 186, 124, 1.6),
]


def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def sym_def(name):
    s = SYM[name]
    out = [f'  (symbol "viv:{name}"']
    if s.get("power"):
        out.append("    (power)")
    if name not in ("CONN4", "CONN2"):
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
         '  (paper "A3")', "  (title_block", '    (title "Reactor TIA - 2x OPA380AID")',
         '    (date "2026-05-31")', '    (rev "v2")', '    (company "Vivonics")', "  )", "  (lib_symbols"]
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
