#!/usr/bin/env python3
"""Generate reactor_tia.kicad_sch + reactor_tia_bom_jlcpcb.csv (OPA380 reactor TIA).

Conventions copied from the working office board
(~/devices/access-controller/circuits/controller on host `office`):
  * KiCad file format (version 20230121) (generator eeschema)  -- opens in KiCad 7/8.
  * Custom symbol fields are named exactly `Part Number` (MPN) and `LCSC` (C-number).
  * JLCPCB BOM = 4 columns  Comment,Designator,Footprint,LCSC  (every cell quoted,
    like-parts grouped into one comma-joined Designator cell). This matches what
    the JLCPCB Fabrication Toolkit plugin emits, so the board's plugin export and
    this file agree.
  * HandSolder footprint variants (prototype/bench rework friendly).

Design (JLCPCB-buildable):
  * 2x OPA380AID single (LCSC C201677, in stock). The OPA2380 DUAL is NOT stocked
    at JLCPCB, so we use two singles: U1 = TIA, U2 = Sallen-Key anti-alias.
  * VBIAS from a divider off +5V (R4/R5 = 100k/10k -> 0.45 V) + RC (R6/C4). The
    M-read is ratiometric + re-baselined, so no precision reference is needed.
  * R_f = 10M 1% (0.1% pointless: gain cancels in dV/V and is bench-calibrated).
  * Filter: R2=R3=68k, C2=2.2nF, C3=1nF C0G -> fc ~1.57 kHz, Q ~0.74.
  * D1 (BPW34, THT) and J1/J2 (headers) are HAND-ADD (not in the SMT BOM); D1 also
    needs to be positionable for optical alignment.

VERIFIED LCSC (web, 2026-05-31): C201677 OPA380AID, C85128 BPW34, C15850 10uF0805,
C1525 100nF0402, C52923 1uF0402, C25803 100k0603, C140329 REF3330 (unused).
BEST-EFFORT (verify on JLCPCB upload -- it auto-validates): R 0603 UNI-ROYAL
0603WAFxxxxT5E family + C0G caps. The `Part Number` (MPN) column lets JLCPCB match
by MPN if a C-number is stale.

Connectivity is by local net labels on wire stubs (robust to placement).
Atomic write. Re-run:  python3 gen_reactor_tia_sch.py
Schematic Y is DOWN; lib symbols are Y-UP: a lib pin (lx,ly) on a part at (px,py)
lands at schematic (px+lx, py-ly).
"""
from __future__ import annotations
import os

ROOT_UUID = "a1b2c3d4-0000-4000-8000-000000000001"
_ctr = [0]


def uid() -> str:
    _ctr[0] += 1
    return f"a1b2c3d4-0000-4000-8000-{_ctr[0]:012d}"


def sgn(x: float) -> int:
    return (x > 0) - (x < 0)


# library symbol pin geometry: name -> {pin: (lx, ly, angle, pin_name, etype)}
SYM = {
    "R": {"1": (0, 5.08, 270, "~", "passive"), "2": (0, -5.08, 90, "~", "passive")},
    "C": {"1": (0, 5.08, 270, "~", "passive"), "2": (0, -5.08, 90, "~", "passive")},
    "PD": {"1": (0, 5.08, 270, "K", "passive"), "2": (0, -5.08, 90, "A", "passive")},
    "OPA380": {
        "2": (-7.62, 2.54, 0, "-IN", "input"),
        "3": (-7.62, -2.54, 0, "+IN", "input"),
        "6": (7.62, 0, 180, "OUT", "output"),
        "7": (0, 7.62, 270, "V+", "power_in"),
        "4": (0, -7.62, 90, "V-", "power_in"),
    },
    "CONN4": {"1": (-5.08, 3.81, 0, "1", "passive"), "2": (-5.08, 1.27, 0, "2", "passive"),
              "3": (-5.08, -1.27, 0, "3", "passive"), "4": (-5.08, -3.81, 0, "4", "passive")},
    "CONN2": {"1": (-5.08, 1.27, 0, "1", "passive"), "2": (-5.08, -1.27, 0, "2", "passive")},
}
BODY = {"R": (1.016, 2.54), "C": (1.27, 2.0), "PD": (1.27, 2.54),
        "OPA380": (5.08, 5.08), "CONN4": (2.54, 5.08), "CONN2": (2.54, 3.81)}
REFLET = {"R": "R", "C": "C", "PD": "D", "OPA380": "U", "CONN4": "J", "CONN2": "J"}
HAND = {"PD", "CONN4", "CONN2"}  # not SMT-assembled by JLCPCB

FP_R = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_603 = "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_402 = "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"
FP_805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SO8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_PD = "OptoDevice:Vishay_BPW34"
FP_H4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
FP_H2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

# ref -> (sym, value, footprint, mpn, lcsc, px, py, {pin: net})
COMPONENTS = {
    "D1": ("PD", "BPW34", FP_PD, "BPW34", "C85128", 55, 95, {"1": "SUMMING", "2": "GND"}),
    "U1": ("OPA380", "OPA380AID", FP_SO8, "OPA380AID", "C201677", 120, 95,
           {"2": "SUMMING", "3": "VBIAS", "6": "V_TIA", "7": "+5V", "4": "GND"}),
    "U2": ("OPA380", "OPA380AID", FP_SO8, "OPA380AID", "C201677", 255, 95,
           {"3": "FILT_P", "2": "V_FILT", "6": "V_FILT", "7": "+5V", "4": "GND"}),
    "R1": ("R", "10M 1%", FP_R, "0603WAF1005T5E", "C57129", 120, 52, {"1": "V_TIA", "2": "SUMMING"}),
    "C1": ("C", "10pF C0G 50V", FP_603, "CC0603JRNPO9BN100", "C168544", 145, 52, {"1": "V_TIA", "2": "SUMMING"}),
    "R2": ("R", "68k 1%", FP_R, "0603WAF6802T5E", "C36871", 190, 52, {"1": "V_TIA", "2": "NODE_A"}),
    "R3": ("R", "68k 1%", FP_R, "0603WAF6802T5E", "C36871", 215, 52, {"1": "NODE_A", "2": "FILT_P"}),
    "C2": ("C", "2.2nF C0G 50V", FP_603, "CC0603JRNPO9BN222", "C108194", 230, 52, {"1": "NODE_A", "2": "V_FILT"}),
    "C3": ("C", "1nF C0G 50V", FP_603, "CC0603JRNPO9BN102", "C57112", 280, 125, {"1": "FILT_P", "2": "GND"}),
    "R4": ("R", "100k 1%", FP_R, "0603WAF1003T5E", "C25803", 60, 160, {"1": "+5V", "2": "VBIAS_RAW"}),
    "R5": ("R", "10k 1%", FP_R, "0603WAF1002T5E", "C25804", 60, 190, {"1": "VBIAS_RAW", "2": "GND"}),
    "R6": ("R", "10k 1%", FP_R, "0603WAF1002T5E", "C25804", 90, 160, {"1": "VBIAS_RAW", "2": "VBIAS"}),
    "C4": ("C", "10uF 25V X5R", FP_805, "CL21A106KAYNNNE", "C15850", 115, 160, {"1": "VBIAS", "2": "GND"}),
    "C5": ("C", "100nF 50V X7R", FP_402, "CL05B104KO5NNNC", "C1525", 100, 35, {"1": "+5V", "2": "GND"}),
    "C6": ("C", "1uF 25V X7R", FP_402, "CL05A105KA5NQNC", "C52923", 145, 35, {"1": "+5V", "2": "GND"}),
    "C7": ("C", "100nF 50V X7R", FP_402, "CL05B104KO5NNNC", "C1525", 280, 35, {"1": "+5V", "2": "GND"}),
    "J1": ("CONN4", "Conn_01x04 OUT->AD7606", FP_H4, "", "", 330, 95,
           {"1": "V_TIA", "2": "V_FILT", "3": "GND", "4": "+5V"}),
    "J2": ("CONN2", "Conn_01x02 +5V/GND", FP_H2, "", "", 330, 160, {"1": "+5V", "2": "GND"}),
}

NOTES = [
    (40, 18, 3.0, "Reactor TIA - 2x OPA380AID (C201677) - red M-state read (JLCPCB)"),
    (40, 118, 2.0, "U1=TIA  U2=Sallen-Key anti-alias.  OPA2380 dual is NOT stocked at JLCPCB -> 2 singles."),
    (40, 123, 2.0, "BIAS: zero-bias (D1 anode->GND). V_out RISES with light. 5V is plenty; 12V NOT needed."),
    (40, 128, 2.0, "For 10 kHz BW only: lift D1 anode to a -5V ICL7660 charge pump (C_d ~20 pF)."),
    (40, 78, 2.0, "D1 BPW34 (C85128) + J1/J2 = HAND-ADD (THT). JLCPCB SMT-places U1,U2,R*,C* only."),
    (40, 200, 2.0, "VBIAS = +5V * 10k/(100k+10k) = 0.45 V, RC-filtered (R6,C4). R_f sized so red pedestal ~3 V."),
    (175, 45, 2.0, "Sallen-Key 2-pole LP fc ~1.57 kHz (R2=R3=68k, C2=2.2n, C3=1n)."),
    (300, 88, 2.0, "J1 -> AD7606: V_TIA=CHn (pedestal+signal), V_FILT=CHn+1 (anti-aliased)."),
]


def sym_def(name: str) -> str:
    hx, hy = BODY[name]
    out = [f'  (symbol "viv:{name}"']
    if name in ("R", "C", "PD"):
        out.append("    (pin_numbers hide)")
    out += ["    (pin_names (offset 1.016))", "    (in_bom yes) (on_board yes)",
            f'    (property "Reference" "{REFLET[name]}" (at 0 {hy+2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
            f'    (property "Value" "{name}" (at 0 {-hy-2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (symbol "{name}_0_1"',
            f"      (rectangle (start {-hx:.3f} {hy:.3f}) (end {hx:.3f} {-hy:.3f})",
            "        (stroke (width 0.254) (type default)) (fill (type none)))"]
    if name == "OPA380":
        out.append("      (polyline (pts (xy -3.0 3.0) (xy 3.0 0) (xy -3.0 -3.0) (xy -3.0 3.0)) (stroke (width 0) (type default)) (fill (type none)))")
    out.append("    )")
    out.append(f'    (symbol "{name}_1_1"')
    for num, (lx, ly, ang, pname, et) in SYM[name].items():
        out.append(f'      (pin {et} line (at {lx:.3f} {ly:.3f} {ang}) (length 2.54)'
                   f' (name "{pname}" (effects (font (size 1.0 1.0))))'
                   f' (number "{num}" (effects (font (size 1.0 1.0)))))')
    out += ["    )", "  )"]
    return "\n".join(out)


def build_sch() -> str:
    P = ["(kicad_sch", "  (version 20230121)", "  (generator eeschema)",
         f"  (uuid {ROOT_UUID})", '  (paper "A3")', "  (title_block",
         '    (title "Reactor TIA - 2x OPA380AID (JLCPCB)")', '    (date "2026-05-31")',
         '    (rev "v3")', '    (company "Vivonics")', "  )", "  (lib_symbols"]
    for name in SYM:
        P.append(sym_def(name))
    P.append("  )")

    for ref, (sym, val, fp, mpn, lcsc, px, py, nets) in COMPONENTS.items():
        P.append(f'  (symbol (lib_id "viv:{sym}") (at {px} {py} 0) (unit 1)')
        P.append("    (in_bom yes) (on_board yes) (dnp no)")
        P.append(f"    (uuid {uid()})")
        ox = BODY[sym][0] + 3
        P.append(f'    (property "Reference" "{ref}" (at {px+ox:.2f} {py-3:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
        P.append(f'    (property "Value" "{val}" (at {px+ox:.2f} {py:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
        P.append(f'    (property "Footprint" "{fp}" (at {px+ox:.2f} {py+3:.2f} 0) (effects (font (size 1.0 1.0)) (justify left) hide))')
        P.append(f'    (property "Datasheet" "" (at {px} {py} 0) (effects (font (size 1.0 1.0)) hide))')
        P.append(f'    (property "Part Number" "{mpn}" (at {px} {py} 0) (effects (font (size 1.0 1.0)) hide))')
        P.append(f'    (property "LCSC" "{lcsc}" (at {px} {py} 0) (effects (font (size 1.0 1.0)) hide))')
        for num in SYM[sym]:
            P.append(f"    (pin \"{num}\" (uuid {uid()}))")
        P.append("    (instances")
        P.append('      (project "reactor_tia"')
        P.append(f'        (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))')
        P.append("      )")
        P.append("    )")
        P.append("  )")
        for num, net in nets.items():
            lx, ly, ang, pname, et = SYM[sym][num]
            tx, ty = px + lx, py - ly
            dxt, dyt = lx, -ly
            sd = (sgn(dxt) or 1, 0) if abs(dxt) >= abs(dyt) else (0, sgn(dyt) or 1)
            ex, ey = tx + sd[0] * 2.54, ty + sd[1] * 2.54
            P.append(f"  (wire (pts (xy {tx:.2f} {ty:.2f}) (xy {ex:.2f} {ey:.2f})) (stroke (width 0) (type default)) (uuid {uid()}))")
            just = "left" if sd[0] >= 0 else "right"
            P.append(f'  (label "{net}" (at {ex:.2f} {ey:.2f} 0) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {uid()}))')

    for x, y, sz, txt in NOTES:
        P.append(f'  (text "{txt}" (at {x} {y} 0) (effects (font (size {sz} {sz})) (justify left)) (uuid {uid()}))')
    P += ['  (sheet_instances', '    (path "/" (page "1"))', "  )", ")"]
    text = "\n".join(P) + "\n"
    assert sum((c == "(") - (c == ")") for c in text) == 0, "paren imbalance"
    return text


def build_bom() -> str:
    """JLCPCB BOM, office format: Comment,Designator,Footprint,LCSC (quoted, grouped).
    SMT parts only (HAND parts excluded; they are placed by hand)."""
    groups: dict[tuple, list[str]] = {}
    for ref, (sym, val, fp, mpn, lcsc, *_rest) in COMPONENTS.items():
        if sym in HAND:
            continue
        groups.setdefault((val, fp, lcsc), []).append(ref)

    def desig_key(r: str):
        return (r.rstrip("0123456789"), int(r[len(r.rstrip("0123456789")):] or 0))

    rows = ["Comment,Designator,Footprint,LCSC"]
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: desig_key(sorted(kv[1], key=desig_key)[0])):
        ds = ",".join(sorted(refs, key=desig_key))
        rows.append(f'"{val}","{ds}","{fp}","{lcsc}"')
    return "\n".join(rows) + "\n"


def atomic_write(path: str, text: str) -> None:
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def main() -> None:
    sch = build_sch()
    atomic_write("reactor_tia.kicad_sch", sch)
    bom = build_bom()
    atomic_write("reactor_tia_bom_jlcpcb.csv", bom)
    n_smt = sum(1 for v in COMPONENTS.values() if v[0] not in HAND)
    print(f"wrote reactor_tia.kicad_sch ({len(sch)} B, {len(COMPONENTS)} comps) + "
          f"reactor_tia_bom_jlcpcb.csv ({n_smt} SMT parts)")


if __name__ == "__main__":
    main()
