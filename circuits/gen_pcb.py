#!/usr/bin/env python3
"""Placement generator for laser_controller.kicad_pcb  (1 channel × 4 wavelengths).

Board: 90 × 50 mm, 1.6 mm, 4× M3 mounting holes.
Optimized columnar layout:
  Col 1 (x=0-13):  4× SFH2201 PDs at left edge (light enters from left)
  Col 2 (x=13-36): 4× TIA channels (OPA380 + VBIAS + passives)
  Col 3 (x=38-58): 4× Laser drivers (TLV9001 + AO3400A + passives)
  Col 4 (x=60-90): ESP32-S3 + LDO + ESD + decoupling + connectors

Reference numbering: automatic sequential per prefix (U1-U11, D1-D6, etc.).
Pad net assignments are resolved from the exported KiCad netlist using the known
generated sheet order.  The PCB generator emits a bounded set of auditable
critical and low-speed routes; it is not a production autorouter.

Run:  kicad-cli sch export netlist laser_controller.kicad_sch -o /tmp/lc.net
      LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 gen_pcb.py

Do not use a plain `python3 gen_pcb.py` for review or release work. The strict
route mode is the checked path; it fails closed on route candidates that cannot
meet the declared generated-board clearance policy.
"""
import re, os
from collections import OrderedDict, defaultdict
from pathlib import Path

# Default to the reviewed generated-copper policy. The routing module reads
# these at import time, so set them before importing pcb_critical_routes.
os.environ.setdefault("LC_STRICT_ROUTE_CLEARANCE", "1")
os.environ.setdefault("LC_MAX_ROUTE_SEARCH_CELLS", "2500")

from circuit_designators import ref_for
from check_laser_controller_netlist import parse_components, parse_netlist
from pcb_critical_routes import (
    BOTTOM_ROUTE_SKIP_DESCRIPTIONS,
    DEFERRED_POWER_ROUTE_DESCRIPTIONS,
    PREROUTE_POWER_ROUTE_DESCRIPTIONS,
    PREROUTE_ROUTE_DESCRIPTIONS,
    PREROUTE_INNER_ROUTE_DESCRIPTIONS,
    emit_bottom_signal_route_segments,
    emit_critical_route_segments,
    emit_extra_signal_route_segments,
    emit_ground_plane_fanout_segments,
    emit_inner_signal_route_segments,
    emit_power_route_segments,
    parse_pad_geometry_from_text,
)

FPROOT="/usr/share/kicad/footprints"
NET="/tmp/lc.net"
OUT_DIR=Path(__file__).resolve().parent
_uu=[0]
def uuid(): _uu[0]+=1; return f"b0b0b0b0-0000-4000-a000-{_uu[0]:012d}"

def env_float(name, default):
    raw = os.environ.get(name)
    return default if raw in (None, "") else float(raw)

# ── footprint cache ───────────────────────────────────────────────
_fp={}
def get_fp(libid):
    if libid in _fp: return _fp[libid]
    lib,name=libid.split(":",1)
    path=f"{FPROOT}/{lib}.pretty/{name}.kicad_mod"
    _fp[libid]=open(path).read() if os.path.exists(path) else None
    if _fp[libid] is None: print(f"  WARN footprint not found, skipping: {libid}")
    return _fp[libid]

# ── place a footprint instance ────────────────────────────────────
def place(libid, ref, val, x, y, rot=0):
    fp=get_fp(libid)
    if fp is None: return None
    fp=re.sub(r'\(tstamp [0-9a-fA-F-]+\)', lambda m:f'(tstamp {uuid()})', fp)
    # The KiCad ESP32-S3-WROOM footprint antenna keepout names only F/In1/B
    # in the stock footprint; this board is a four-layer Sig/GND/PWR/Sig
    # stackup, so extend the keepout to the second inner copper plane too.
    fp=fp.replace('(layers "F.Cu" "In1.Cu" "B.Cu")',
                  '(layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu")')
    # Insert at+layer — handle both quoted and bare (layer ...) names
    fp=re.sub(r'(\(footprint ("[^"]*"|[^\s"]+)[^\n]*\n\s*\(layer "[^"]*"\)\n)',
              lambda m: m.group(1)+f'  (tstamp {uuid()})\n  (at {x:.3f} {y:.3f} {rot})\n', fp, count=1)
    fp=re.sub(r'(\(footprint ("[^"]*"|[^\s"]+)[^\n]*\n\s*\(layer [^\s"]+\)\n)',
              lambda m: m.group(1)+f'  (tstamp {uuid()})\n  (at {x:.3f} {y:.3f} {rot})\n', fp, count=1)
    header = fp.split("(pad", 1)[0]
    if not re.search(r'\n\s*\(at\s+[-\d.]', header):
        first_newline = fp.find("\n")
        fp = (
            fp[: first_newline + 1]
            + f'  (tstamp {uuid()})\n  (at {x:.3f} {y:.3f} {rot})\n'
            + fp[first_newline + 1 :]
        )
    # Handle REF**
    fp=re.sub(r'(\(fp_text reference )"REF\*\*"', lambda m:m.group(1)+f'"{ref}"', fp, count=1)
    fp=re.sub(r'(\(fp_text reference )REF\*\*', lambda m:m.group(1)+f'"{ref}"', fp, count=1)
    fp=re.sub(r'(\(fp_text value )"[^"]*"', lambda m:m.group(1)+f'"{val}"', fp, count=1)
    return fp

def fp_ref(block):
    match = re.search(r'\(fp_text reference "?([^"\s\)]+)"?', block)
    return match.group(1) if match else ""

def add_pad_nets(block, pad_nets):
    """Attach `(net n "name")` entries to every matching pad line in a footprint."""
    if not pad_nets:
        return block
    out = []
    for line in block.splitlines():
        match = re.match(r'(\s*\(pad\s+(?:"([^"]*)"|([^\s\)]+))\s+.*)$', line)
        pad_name = (match.group(2) if match and match.group(2) is not None else match.group(3)) if match else ""
        if match and pad_name in pad_nets and "(net " not in line:
            code, name = pad_nets[pad_name]
            token = f' (net {code} "{name}")'
            if line.count("(") == line.count(")"):
                idx = line.rfind(")")
                line = line[:idx] + token + line[idx:]
            else:
                line += token
        out.append(line)
    return "\n".join(out)

def sexpr_quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'

NET_CLASS_SPECS = OrderedDict([
    ("Laser_Current", {
        "description": "Laser anode/cathode and MOSFET source-sense current paths; route short and wide.",
        "clearance": 0.30,
        "trace_width": 1.00,
        "via_dia": 1.20,
        "via_drill": 0.60,
    }),
    ("Power_Rails", {
        "description": "Board power and common return rails; prefer pours or wide trunks.",
        "clearance": 0.25,
        "trace_width": 0.60,
        "via_dia": 1.00,
        "via_drill": 0.50,
    }),
    ("USB", {
        "description": "USB D+/D- connector, ESD, and ESP32 native USB nets; route as a short 90 ohm pair.",
        "clearance": 0.18,
        "trace_width": 0.25,
        "via_dia": 0.60,
        "via_drill": 0.30,
    }),
    ("TIA_Sensitive", {
        "description": "Photodiode summing, TIA bias, and TIA output nets; keep tiny and away from switching/current paths.",
        "clearance": 0.25,
        "trace_width": 0.20,
        "via_dia": 0.60,
        "via_drill": 0.30,
    }),
    ("Monitor_ADC", {
        "description": "Laser monitor-PD and current-sense telemetry into ESP32 ADC pins.",
        "clearance": 0.25,
        "trace_width": 0.20,
        "via_dia": 0.60,
        "via_drill": 0.30,
    }),
    ("Laser_Control", {
        "description": "PWM command filters, TLV9001 outputs, and MOSFET gate-drive nets.",
        "clearance": 0.20,
        "trace_width": 0.25,
        "via_dia": 0.60,
        "via_drill": 0.30,
    }),
    ("Digital_Control", {
        "description": "ESP32 UART, reset/boot, and AD7606 conversion-start logic nets.",
        "clearance": 0.20,
        "trace_width": 0.25,
        "via_dia": 0.60,
        "via_drill": 0.30,
    }),
    ("Default", {
        "description": "Fallback class; all named nets should be explicitly classified by the generator.",
        "clearance": 0.20,
        "trace_width": 0.25,
        "via_dia": 0.80,
        "via_drill": 0.40,
    }),
])

TIA_CHANNEL_SHEETS = ("TIA_IR", "TIA_RED", "TIA_GREEN", "TIA_BLUE")
LASER_CHANNEL_SHEETS = ("LASER_IR", "LASER_RED", "LASER_GREEN", "LASER_BLUE")

TIA_SENSITIVE_AUTO_NETS = set()
for sheet in TIA_CHANNEL_SHEETS:
    TIA_SENSITIVE_AUTO_NETS.update({
        f"Net-({ref_for(sheet, 'D1')}-A)",
        f"Net-({ref_for(sheet, 'D1')}-K)",
        f"Net-({ref_for(sheet, 'U1')}-+)",
        f"Net-({ref_for(sheet, 'RT')}-Pad2)",
        f"Net-({ref_for(sheet, 'RV11')}-W)",
    })

LASER_CONTROL_AUTO_NETS = set()
for sheet in LASER_CHANNEL_SHEETS:
    LASER_CONTROL_AUTO_NETS.update({
        f"Net-({ref_for(sheet, 'Q1')}-G)",
        f"Net-({ref_for(sheet, 'U11')}-+)",
    })

def classify_net(net_name):
    if re.match(r"LASER_N[1-4]$", net_name) or net_name == "LASER_V+" or net_name.endswith("/FB"):
        return "Laser_Current"
    if net_name in {"+5V", "+3V3", "GND", "VBUS_5V", "/POWER_IO/EXT5V"}:
        return "Power_Rails"
    if "/USB_D" in net_name:
        return "USB"
    if (
        net_name.startswith("VOUT")
        or net_name in TIA_SENSITIVE_AUTO_NETS
    ):
        return "TIA_Sensitive"
    if re.match(r"(MPD|ISENSE)[1-4]$", net_name) or "MPD_RAW" in net_name:
        return "Monitor_ADC"
    if (
        re.match(r"PWM[1-4]$", net_name)
        or net_name in LASER_CONTROL_AUTO_NETS
        or net_name.endswith("/LOUT")
    ):
        return "Laser_Control"
    if net_name in {"CONVST", "/MCU_ESP32-S3/ESP_BOOT", "/MCU_ESP32-S3/ESP_EN", "/MCU_ESP32-S3/ESP_RX", "/MCU_ESP32-S3/ESP_TX"}:
        return "Digital_Control"
    return "Default"

def build_net_classes(net_names):
    classes = {name: [] for name in NET_CLASS_SPECS}
    for net_name in net_names:
        classes[classify_net(net_name)].append(net_name)
    return classes

def emit_net_classes(net_names):
    classes = build_net_classes(net_names)
    lines = []
    for name, spec in NET_CLASS_SPECS.items():
        lines.append(f'  (net_class {sexpr_quote(name)} {sexpr_quote(spec["description"])}')
        lines.append(f'    (clearance {spec["clearance"]:.2f})')
        lines.append(f'    (trace_width {spec["trace_width"]:.2f})')
        lines.append(f'    (via_dia {spec["via_dia"]:.2f})')
        lines.append(f'    (via_drill {spec["via_drill"]:.2f})')
        lines.append('    (uvia_dia 0.30)')
        lines.append('    (uvia_drill 0.10)')
        for net_name in sorted(classes[name]):
            lines.append(f'    (add_net {sexpr_quote(net_name)})')
        lines.append('  )')
    return lines

# ── board frame ───────────────────────────────────────────────────
LAYERS='''  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power)
    (2 "In2.Cu" power)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user)
  )'''
def outline(x0,y0,x1,y1):
    pts=[(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]
    return "\n".join(f'  (gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts"))'
                     for a,b in zip(pts,pts[1:]))
def mhole(x,y):
    return (f'  (footprint "MountingHole:MountingHole_3.2mm_M3" (layer "F.Cu") (tstamp {uuid()}) (at {x} {y})\n'
            f'    (attr exclude_from_pos_files exclude_from_bom)\n'
            f'    (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask")))')
def text(s,x,y,size=2.0,layer="F.SilkS"):
    return f'  (gr_text "{s}" (at {x} {y}) (layer "{layer}") (effects (font (size {size} {size}) (thickness {size*0.15:.2f}))))'

def copper_zone(net_code, net_name, layer, x0, y0, x1, y1, clearance=0.30):
    return f'''  (zone (net {net_code}) (net_name {sexpr_quote(net_name)}) (layer {sexpr_quote(layer)}) (tstamp {uuid()}) (hatch edge 0.508)
    (connect_pads (clearance {clearance:.2f}))
    (min_thickness 0.254) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.508) (thermal_bridge_width 0.508))
    (polygon
      (pts
        (xy {x0:.3f} {y0:.3f})
        (xy {x1:.3f} {y0:.3f})
        (xy {x1:.3f} {y1:.3f})
        (xy {x0:.3f} {y1:.3f})
      )
    )
  )'''

# ── parse components ──────────────────────────────────────────────
def load_components():
    bysheet=defaultdict(list)
    for comp in parse_components(Path(NET)):
        bysheet[comp["sheet"].strip("/")].append(comp)
    return bysheet

TIA_ORDER = ["TIA_IR", "TIA_RED", "TIA_GREEN", "TIA_BLUE"]
LASER_ORDER = ["LASER_IR", "LASER_RED", "LASER_GREEN", "LASER_BLUE"]
TIA_REFS = {"C1","C2","C11","CB","D1","R1","R2","RB","RT","RV11","U1"}
LASER_REFS = {"C21","C22","CC","Q1","R11","R12","R21","R22","R31","U11"}

def channel_sheet(prefix, index_text):
    idx = int(index_text) - 1
    return f"{prefix}_{['IR','RED','GREEN','BLUE'][idx]}"

def auto_index(name, base):
    if name == base:
        return 0
    if name.startswith(base + "_"):
        return int(name.rsplit("_", 1)[1])
    return None

def resolve_node_sheets(net_name, ref, sheets_by_ref):
    """Resolve a netlist node's local ref into concrete sheet instances.

    KiCad's unannotated hierarchical netlist exports nodes as local references
    (`Q1`, `U1`, `D1`, ...).  For global rails we intentionally expand to every
    matching sheet instance.  For channel nets we use the generator's fixed
    channel order, which is also locked by check_laser_controller_netlist.py.
    """
    if net_name.startswith("unconnected-"):
        return []
    if net_name in {"+5V", "+3V3", "GND"}:
        return sheets_by_ref.get(ref, [])
    match = re.match(r"/([^/]+)/", net_name)
    if match:
        sheet = match.group(1)
        if (sheet, ref) in COMPONENT_KEYS:
            return [sheet]
    if ref in sheets_by_ref and len(sheets_by_ref[ref]) == 1:
        return sheets_by_ref[ref]
    for base in ["Net-(D1-A)", "Net-(D1-K)", "Net-(U1-+)", "Net-(RT-Pad2)", "Net-(RV11-W)"]:
        idx = auto_index(net_name, base)
        if idx is not None:
            return [TIA_ORDER[idx]]
    for base in ["Net-(Q1-G)", "Net-(U11-+)"]:
        idx = auto_index(net_name, base)
        if idx is not None:
            return [LASER_ORDER[idx]]
    match = re.match(r"VOUT([1-4])$", net_name)
    if match and ref in TIA_REFS:
        return [channel_sheet("TIA", match.group(1))]
    match = re.match(r"(PWM|ISENSE|LASER_N)([1-4])$", net_name)
    if match and ref in LASER_REFS:
        return [channel_sheet("LASER", match.group(2))]
    return []

COMPONENT_KEYS = set()

def build_pad_net_map(nets, board_ref_by_comp, sheets_by_ref):
    net_names = [name for name in nets if not name.startswith("unconnected-")]
    net_code = {name: i + 1 for i, name in enumerate(net_names)}
    pad_nets = defaultdict(dict)
    conflicts = []
    unresolved = []
    for net_name, nodes in nets.items():
        if net_name.startswith("unconnected-"):
            continue
        for ref, pin, _, _ in nodes:
            sheets = resolve_node_sheets(net_name, ref, sheets_by_ref)
            if not sheets:
                unresolved.append((net_name, ref, pin))
                continue
            for sheet in sheets:
                board_ref = board_ref_by_comp.get((sheet, ref))
                if not board_ref:
                    unresolved.append((net_name, ref, pin))
                    continue
                existing = pad_nets[board_ref].get(pin)
                new_value = (net_code[net_name], net_name)
                if existing and existing != new_value:
                    conflicts.append((board_ref, pin, existing, new_value))
                pad_nets[board_ref][pin] = new_value
    if unresolved or conflicts:
        raise RuntimeError(f"PCB net assignment failed: unresolved={unresolved} conflicts={conflicts}")
    return net_names, pad_nets

# ── reference counters ────────────────────────────────────────────
def make_ref_counters():
    ctr={}
    def assign(prefix):
        ctr[prefix]=ctr.get(prefix,0)+1
        return f"{prefix}{ctr[prefix]}"
    return ctr, assign

ROLE_IC=('SOIC-8','SOT-23-5','SOT-23-6','SOT-23','TSSOP','D_SMA')

def build_board(emit_routes=True):
    global COMPONENT_KEYS
    _uu[0] = 0
    bysheet=load_components()
    comps = [comp for parts in bysheet.values() for comp in parts]
    COMPONENT_KEYS = {(comp["sheet"].strip("/"), comp["ref"]) for comp in comps}
    sheets_by_ref=defaultdict(list)
    for comp in comps:
        sheets_by_ref[comp["ref"]].append(comp["sheet"].strip("/"))
    nets = parse_netlist(Path(NET))
    board_ref_by_comp = {}

    P=['(kicad_pcb (version 20221018) (generator pcbnew)','  (general (thickness 1.6))','  (paper "A4")',
       LAYERS,'  (setup (pad_to_mask_clearance 0.05))','  (net 0 "")']
    body=[]

    # ===== FLOORPLAN: 90 × 50 mm =====
    BW,BH=90,50; M=3.0
    # Keep the external ADC header near the TIA column.  Putting it in the
    # right-edge connector stack makes VOUT3 the boxed-in analog output.
    ad7606_x = env_float("LC_AD7606_X", 28.0)
    ad7606_y = env_float("LC_AD7606_Y", 42.0)
    ad7606_rot = env_float("LC_AD7606_ROT", 90.0)
    j4_x = env_float("LC_J4_X", BW - 2.5)
    j4_y = env_float("LC_J4_Y", 26.0)
    j4_rot = env_float("LC_J4_ROT", 90.0)
    j5_x = env_float("LC_J5_X", BW - 2.5)
    j5_y = env_float("LC_J5_Y", 14.0)
    j5_rot = env_float("LC_J5_ROT", 90.0)
    j6_x = env_float("LC_J6_X", BW - 2.5)
    j6_y = env_float("LC_J6_Y", 6.0)
    j6_rot = env_float("LC_J6_ROT", 90.0)
    esp32_x = env_float("LC_ESP32_X", 64.0)
    esp32_y = env_float("LC_ESP32_Y", 6.75)
    esp32_rot = env_float("LC_ESP32_ROT", 0.0)
    laser_x_shift = env_float("LC_LASER_X_SHIFT", 0.0)
    laser_c22_dx = env_float("LC_LASER_C22_DX", 0.0)
    laser_c22_dy = env_float("LC_LASER_C22_DY", 0.0)
    laser_c22_rot = env_float("LC_LASER_C22_ROT", 0.0)
    body.append(outline(0,0,BW,BH))
    for mx,my in [(M,M),(BW-M,M),(M,BH-M),(BW-M,BH-M)]: body.append(mhole(mx,my))
    body.append(text("LASER CONTROLLER — Vivonics — 90x50mm — 4ch PD+TIA+Laser Driver+MPD — ESP32-S3",4,BH-1.8,1.0,"Cmts.User"))

    def emit_fp(comp, x, y, rot=0, prefix=None):
        ref = comp["ref"]
        sheet = comp["sheet"].strip("/")
        board_ref_by_comp[(sheet, ref)] = ref
        fp_str = place(comp["footprint"], ref, comp["value"], x, y, rot)
        if fp_str: body.append(fp_str)

    def pop_ref(parts_by_actual_ref, sheet, local_ref):
        return parts_by_actual_ref.pop(ref_for(sheet, local_ref))

    def cell(parts, x0, y0, refmap, wcols=4, dx=4.5, dy=3.5):
        """Compact cell: pots→ICs→passives in tight rows."""
        pots=[p for p in parts if p["ref"][:2]=='RV']
        ics =[p for p in parts if any(k in p["footprint"] for k in ROLE_IC)]
        smd =[p for p in parts if p not in pots and p not in ics]
        POT_H = 5 if pots else 0; IC_H = 5 if ics else 0
        for i,p in enumerate(pots):
            emit_fp(p, x0+i*8, y0, 0, prefix=refmap.get(p["ref"], p["ref"]))
        yo = y0 + POT_H
        for i,p in enumerate(ics):
            emit_fp(p, x0+i*7, yo, 0, prefix=refmap.get(p["ref"], p["ref"]))
        yo += IC_H
        for i,p in enumerate(smd):
            emit_fp(p, x0+(i%wcols)*dx, yo+(i//wcols)*dy, 0, prefix=refmap.get(p["ref"], p["ref"]))

    WL=["IR","RED","GREEN","BLUE"]
    rows=[5.0, 15.0, 27.0, 35.0]
    laser_rows=[16.0, 24.0, 32.0, 40.0]
    PD_X=3.0

    # ── Col 1: Photodiodes at LEFT EDGE (x=3) ──
    body.append(text("PD (SFH2201)",PD_X,47.5,0.7,"Cmts.User"))
    for i,wl in enumerate(WL):
        parts=bysheet[f"TIA_{wl}"]
        for p in [p for p in parts if p["footprint"].startswith("OptoDevice")]:
            emit_fp(p, PD_X, rows[i], 270, prefix="D")

    # ── Col 2: TIA channels (x=13..36) ──
    body.append(text("TIA (OPA380) x4",16,47.5,0.7,"Cmts.User"))
    tia_refs = {"D1":"D","U1":"U","RV11":"RV","C1":"C","C2":"C","C11":"C","CB":"C","R1":"R","R2":"R","RB":"R","RT":"R"}
    for i,wl in enumerate(WL):
        sheet_name = f"TIA_{wl}"
        row = rows[i]
        by_ref = {
            p["ref"]: p
            for p in bysheet[sheet_name]
            if not p["footprint"].startswith("OptoDevice")
        }
        tia_xy = {
            # Keep the SFH2201 anode / OPA380 inverting input / feedback loop compact.
            "U1": (10.0, row, 0),
            "R2": (10.0, row - 2.5, 0),
            "C1": (10.0, row, 0),
            "C2": (14.0, row - 1.2, 0),
            "RB": (4.8, row + 2.0, 180),
            "CB": (4.3, row + 4.2, 0),
            # VBIAS is lower bandwidth, but keep the RC output near OPA380 +IN.
            "R1": (10.0, row + 3.2, 0),
            "C11": (7.0, row + 3.9, 90),
            "RV11": (17.0, row, 0),
            "RT": (22.5, row + 1.0, 0),
        }
        for ref, (x, y, rot) in tia_xy.items():
            emit_fp(pop_ref(by_ref, sheet_name, ref), x, y, rot, prefix=tia_refs[ref])
        for j, p in enumerate(by_ref.values()):
            emit_fp(p, 13 + (j % 4) * 4.5, row - 2 + (j // 4) * 3.5, 0, prefix=tia_refs.get(p["ref"], p["ref"]))

    # ── Col 3: Laser drivers (x=38..56) ──
    body.append(text("LASER DRIVERS x4",40,47.5,0.7,"Cmts.User"))
    laser_refs = {"Q1":"Q","U11":"U","C21":"C","C22":"C","CC":"C","R11":"R","R12":"R","R21":"R","R22":"R","R31":"R"}
    for i,wl in enumerate(WL):
        sheet_name = f"LASER_{wl}"
        row = laser_rows[i]
        by_ref = {p["ref"]: p for p in bysheet[sheet_name]}
        laser_xy = {
            # Current loop: TLV9001 -> gate resistor -> AO3400A -> source sense -> FB.
            "U11": (39.5 + laser_x_shift, row, 0),
            "R31": (41.6 + laser_x_shift, row - 2.3, 0),
            "Q1": (44.0 + laser_x_shift, row, 0),
            # The 2512 sense resistor pad must stay close to Q1 source while
            # leaving Q1 drain a clear wide escape toward the laser harness.
            "R11": (47.0 + laser_x_shift, row + 2.5, 0),
            "R12": (45.5 + laser_x_shift, row + 4.0, 0),
            "C22": (41.2 + laser_x_shift + laser_c22_dx, row - 0.2 + laser_c22_dy, laser_c22_rot),
            # Command filter and limiter stay at TLV9001 IN+; rotate shunt parts vertical.
            "R21": (36.0 + laser_x_shift, row + 2.0, 0),
            "R22": (38.0 + laser_x_shift, row + 4.0, 90),
            "C21": (40.0 + laser_x_shift, row + 3.0, 90),
            # Compensation cap directly bridges TLV9001 OUT and FB pins.
            "CC": (39.5 + laser_x_shift, row, 270),
        }
        if wl == "RED":
            # Rotate the RED command resistor so its TLV9001-side pad stays
            # beside U6.3 while the ESP32 PWM2 pad escapes above the input
            # cluster instead of being trapped below it.
            laser_xy["R21"] = (36.8 + laser_x_shift, row, 90)
            # Keep the RED command-filter GND pad off the generated PWM3/PWM4
            # inner-route corridor so it can dogbone into the GND plane.
            laser_xy["C21"] = (36.5 + laser_x_shift, row + 3.0, 90)
        for ref, (x, y, rot) in laser_xy.items():
            emit_fp(pop_ref(by_ref, sheet_name, ref), x, y, rot, prefix=laser_refs[ref])
        for j, p in enumerate(by_ref.values()):
            emit_fp(p, 38 + (j % 4) * 4.5, row - 2 + (j // 4) * 3.5, 0, prefix=laser_refs.get(p["ref"], p["ref"]))

    # ── Col 4: MCU + ESP32 + Connectors (x=60..90) ──
    body.append(text("MCU + ESP32-S3",62,47.5,0.7,"Cmts.User"))
    mrest={}
    for comp in bysheet["MCU_ESP32-S3"]:
        fp = comp["footprint"]
        if "USB" in fp and "ESP32" not in fp:
            emit_fp(
                comp,
                env_float("LC_USB_CONN_X", 46.0),
                env_float("LC_USB_CONN_Y", 4.1),
                env_float("LC_USB_CONN_ROT", 0.0),
                prefix="J",
            )  # USB Mini-B at the top edge, left of the ESP32 module body
        elif "ESP32" in fp:
            emit_fp(comp, esp32_x, esp32_y, esp32_rot, prefix="U")  # ESP32-S3, antenna toward top edge
        elif "PinHeader" in fp:
            emit_fp(
                comp,
                env_float("LC_UART_HDR_X", 75.0),
                env_float("LC_UART_HDR_Y", 34.0),
                0,
                prefix="J",
            )  # UART/EN/BOOT header by ESP32 right-side pads
        else:
            mrest[comp["ref"]] = comp
    # MCU support placement: protection at connector, series parts at ESP32 pins,
    # regulator and decoupling at the ESP32 3V3/GND side, strap parts at pins.
    mcu_xy = {
        "U12": (env_float("LC_USBLC6_X", 47.7), env_float("LC_USBLC6_Y", 9.8), 0, "U"),  # USBLC6 beside Mini-B, with VBUS escape
        "RUSBM": (52.7, 14.0, 0, "R"),    # D- series resistor at ESP32 GPIO19 side pad
        "RUSBP": (52.7, 17.7, 0, "R"),    # D+ series resistor at ESP32 GPIO20 side pad
        "U10": (
            env_float("LC_AP2112_X", 80.0),
            env_float("LC_AP2112_Y", 12.0),
            env_float("LC_AP2112_ROT", 0.0),
            "U",
        ),  # AP2112 to the right of the module body
        "C44": (
            env_float("LC_AP2112_INCAP_X", 77.0),
            env_float("LC_AP2112_INCAP_Y", 12.0),
            env_float("LC_AP2112_INCAP_ROT", 90.0),
            "C",
        ),  # AP2112 input cap at VIN/GND pins
        "C41": (
            env_float("LC_AP2112_OUT100N_X", 83.2),
            env_float("LC_AP2112_OUT100N_Y", 10.8),
            env_float("LC_AP2112_OUT100N_ROT", 0.0),
            "C",
        ),  # AP2112 output 100n
        "C42": (
            env_float("LC_AP2112_OUTBULK_X", 83.2),
            env_float("LC_AP2112_OUTBULK_Y", 13.6),
            env_float("LC_AP2112_OUTBULK_ROT", 0.0),
            "C",
        ),  # AP2112 output bulk
        "C43": (53.0, 2.8, 0, "C"),       # ESP32 3V3 local decap at module side pad
        "CEN": (52.5, 4.2, 0, "C"),       # EN RC at ESP32 EN side pad
        "REN": (50.5, 4.2, 0, "R"),       # EN pull-up at ESP32 EN side pad
        "RBOOT": (75.5, 18.0, 180, "R"),  # BOOT pull-up at ESP32 GPIO0 side pad
    }
    for ref, (x, y, rot, pref) in mcu_xy.items():
        actual_ref = ref_for("MCU_ESP32-S3", ref)
        if actual_ref in mrest:
            emit_fp(mrest.pop(actual_ref), x, y, rot, prefix=pref)
    for i,p in enumerate(mrest.values()):
        pref = "R" if p["ref"].startswith("R") else "C" if p["ref"].startswith("C") else "U"
        emit_fp(p, 60+(i%3)*5, 6+(i//3)*4, 0, prefix=pref)

    # ── Power / IO connectors (RIGHT edge) ──
    body.append(text("I/O",82,47.5,0.7,"Cmts.User"))
    prest=[]
    for comp in bysheet["POWER_IO"]:
        ref = comp["ref"]
        if ref == ref_for("POWER_IO", "J1"):
            emit_fp(comp, ad7606_x, ad7606_y, ad7606_rot, prefix="J")  # AD7606 out
        elif ref == ref_for("POWER_IO", "J4"):
            emit_fp(comp, j4_x, j4_y, j4_rot, prefix="J")  # LASER + monitor-PD out
        elif ref == ref_for("POWER_IO", "J5"):
            emit_fp(comp, j5_x, j5_y, j5_rot, prefix="J")  # LASER PSU
        elif ref == ref_for("POWER_IO", "J2"):
            emit_fp(comp, j6_x, j6_y, j6_rot, prefix="J")  # EXT 5V
        else:
            prest.append(comp)
    # SS14 diodes + bulk cap + MPD sense/reference/filter/isolation passives.
    # MPD front-end parts are placed by J4 pin so the raw monitor-PD node is short and quiet.
    prest_by_ref = {p["ref"]: p for p in prest}
    power_io_xy = {
        "D10": (env_float("LC_D5_X", 80.0), env_float("LC_D5_Y", 8.5), 0, "D"),
        "D11": (env_float("LC_D6_X", 80.0), env_float("LC_D6_Y", 4.5), 180, "D"),
        # Rotate the +5 V bulk capacitor so pad 1 faces the OR-ing diode
        # cathodes; otherwise the GND pad sits between D5/D6 and +5 V.
        "C50": (env_float("LC_C34_X", 75.0), env_float("LC_C34_Y", 8.5), 180, "C"),
    }
    mpd_x_by_index = {1: 84.0, 2: 79.0, 3: 74.0, 4: 69.0}
    radc_x_by_index = {3: 72.0, 4: 67.0}
    for index, x in mpd_x_by_index.items():
        power_io_xy[f"RMPD{index}"] = (x, 23.3, 180, "R")
        power_io_xy[f"CMPD{index}"] = (x + 0.3, 27.4, 180, "C")
        power_io_xy[f"RADC{index}"] = (radc_x_by_index.get(index, x), 29.0, 0, "R")
    for ref, (x, y, rot, pref) in power_io_xy.items():
        actual_ref = ref_for("POWER_IO", ref)
        if actual_ref in prest_by_ref:
            emit_fp(prest_by_ref.pop(actual_ref), x, y, rot, prefix=pref)
    for i,p in enumerate(prest_by_ref.values()):
        pref = "D" if p["ref"].startswith("D") else "R" if p["ref"].startswith("R") else "C"
        emit_fp(p, 80+(i%2)*5, 44-(i//2)*4, 0, prefix=pref)

    net_names, pad_nets_by_ref = build_pad_net_map(nets, board_ref_by_comp, sheets_by_ref)
    for i, net_name in enumerate(net_names, 1):
        P.append(f'  (net {i} "{net_name}")')
    P += emit_net_classes(net_names)
    net_code_by_name = {name: i + 1 for i, name in enumerate(net_names)}
    body.append(copper_zone(net_code_by_name["GND"], "GND", "In1.Cu", 0.5, 0.5, BW - 0.5, BH - 0.5))

    body = [
        add_pad_nets(block, pad_nets_by_ref.get(fp_ref(block), {}))
        for block in body
        if block
    ]
    if emit_routes:
        routed_segment_state: list[dict[str, object]] = []
        pads_for_reservations = parse_pad_geometry_from_text("\n".join(body))
        c34_ref = board_ref_by_comp.get(("POWER_IO", ref_for("POWER_IO", "C50")))
        if c34_ref and c34_ref in pads_for_reservations and "2" in pads_for_reservations[c34_ref]:
            c34_gnd = pads_for_reservations[c34_ref]["2"][0]
            c34_gnd_point = (round(float(c34_gnd["x"]), 4), round(float(c34_gnd["y"]), 4))
            # Reserve the +5 V bulk-cap GND via before signal routing so
            # ESP_TX/EN cannot later occupy the drill path through inner layers.
            routed_segment_state.append(
                {"net": "GND", "a": c34_gnd_point, "b": c34_gnd_point, "w": 0.45, "layer": "*.Cu"}
            )
        usb_route_segments: list[str] = []
        usb_routed_descriptions: list[str] = []
        pre_power_route_segments, pre_power_routed_descriptions = emit_power_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            only_descriptions=PREROUTE_POWER_ROUTE_DESCRIPTIONS,
        )
        preroute_segments, pre_routed_descriptions, routed_segment_state = emit_critical_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            uuid,
            routed_segment_state,
            only_descriptions=PREROUTE_ROUTE_DESCRIPTIONS,
        )
        cathode_route_segments, cathode_routed_descriptions = emit_extra_signal_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            cathode_only=True,
        )
        pre_inner_route_segments, pre_inner_routed_descriptions = emit_inner_signal_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            only_descriptions=PREROUTE_INNER_ROUTE_DESCRIPTIONS,
        )
        route_segments, routed_descriptions, routed_segment_state = emit_critical_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            uuid,
            routed_segment_state,
            pre_routed_descriptions=pre_routed_descriptions,
            skip_descriptions=PREROUTE_ROUTE_DESCRIPTIONS,
        )
        extra_route_segments, extra_routed_descriptions = emit_extra_signal_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            skip_cathodes=True,
        )
        inner_route_segments, inner_routed_descriptions = emit_inner_signal_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            skip_descriptions=PREROUTE_INNER_ROUTE_DESCRIPTIONS,
        )
        bottom_route_segments, bottom_routed_descriptions = emit_bottom_signal_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            skip_descriptions=BOTTOM_ROUTE_SKIP_DESCRIPTIONS,
        )
        power_route_segments, power_routed_descriptions = emit_power_route_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
            skip_descriptions=DEFERRED_POWER_ROUTE_DESCRIPTIONS | PREROUTE_POWER_ROUTE_DESCRIPTIONS,
        )
        gnd_fanout_segments, gnd_fanout_descriptions = emit_ground_plane_fanout_segments(
            body,
            board_ref_by_comp,
            pad_nets_by_ref,
            routed_segment_state,
            uuid,
        )
        body += usb_route_segments + pre_power_route_segments + preroute_segments + cathode_route_segments + pre_inner_route_segments + route_segments + extra_route_segments + bottom_route_segments + inner_route_segments + power_route_segments + gnd_fanout_segments
        body.append(text(f"Generated critical local routes: {len(routed_descriptions)}/109 links",4,BH-3.0,0.8,"Cmts.User"))
        body.append(text(f"Generated cathode/extra routes: {len(cathode_routed_descriptions)}/{len(extra_routed_descriptions)} links",4,BH-1.8,0.8,"Cmts.User"))
        body.append(text(f"Generated bottom/inner/power routes: {len(bottom_routed_descriptions)}/{len(pre_inner_routed_descriptions) + len(inner_routed_descriptions)}/{len(pre_power_routed_descriptions) + len(power_routed_descriptions)} links",4,BH-0.6,0.8,"Cmts.User"))
        body.append(text(f"Generated GND fanouts: {len(gnd_fanout_descriptions)} pads to In1.Cu",4,BH-4.2,0.8,"Cmts.User"))
    P+=body
    P.append(")")
    pcb_text = "\n".join(P)+"\n"
    return pcb_text, body, board_ref_by_comp, pad_nets_by_ref, net_names


def main():
    pcb_text, body, _, _, _ = build_board()
    (OUT_DIR / "laser_controller.kicad_pcb").write_text(pcb_text)
    import collections
    all_refs=collections.Counter()
    for b in body:
        m=re.search(r'\(fp_text reference "?([^")]+)"?', b)
        if m: all_refs[m.group(1)]+=1
    print(f"  wrote laser_controller.kicad_pcb  ({len(body)} blocks, {sum(all_refs.values())} ref instances)")
    print(f"  refs: {len(all_refs)} unique")

if __name__=="__main__": main()
