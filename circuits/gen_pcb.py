#!/usr/bin/env python3
"""Placement-staging generator for laser_controller.kicad_pcb.

Board: 90 x 50 mm outline only.

All schematic footprints are staged outside the board outline by sheet so they
can be dragged into the board manually in KiCad.  The generator intentionally
emits no board traces, vias, or board-level copper zones.  Footprint-internal
items such as the ESP32 antenna keepout are preserved as part of the loaded
component footprint.

Reference numbering: automatic sequential per prefix (U1-U11, D1-D6, etc.).
Pad net assignments are resolved from the exported KiCad netlist using the known
    generated sheet order.  This PCB generator is intentionally not a router.

Run:  kicad-cli sch export netlist laser_controller.kicad_sch -o /tmp/lc.net
      python3 gen_pcb.py
"""
import re, os
from collections import OrderedDict, defaultdict
from math import cos, radians, sin
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

FPROOT = Path("/usr/share/kicad/footprints")
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
    if not libid or ":" not in libid:
        _fp[libid] = None
        print(f"  WARN footprint not placeable, skipping: {libid or '<empty>'}")
        return None
    lib,name=libid.split(":",1)
    search_paths = [
        OUT_DIR / "lib" / f"{lib}.pretty" / f"{name}.kicad_mod",
        OUT_DIR / f"{lib}.pretty" / f"{name}.kicad_mod",
        FPROOT / f"{lib}.pretty" / f"{name}.kicad_mod",
    ]
    found_path = next((path for path in search_paths if path.exists()), None)
    _fp[libid]=found_path.read_text() if found_path else None
    if _fp[libid] is None: print(f"  WARN footprint not found, skipping: {libid}")
    return _fp[libid]

# ── place a footprint instance ────────────────────────────────────
def transform_zone_polygons_to_board_coords(fp, origin_x, origin_y, rotation_deg):
    """KiCad stores footprint keepout-zone polygon points in board coordinates."""
    theta = radians(rotation_deg)
    c = cos(theta)
    s = sin(theta)

    def transform_match(match):
        lx = float(match.group(1))
        ly = float(match.group(2))
        gx = origin_x + lx * c - ly * s
        gy = origin_y + lx * s + ly * c
        return f"(xy {gx:.3f} {gy:.3f})"

    def transform_zone(zone_match):
        return re.sub(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)', transform_match, zone_match.group(0))

    return re.sub(r'\(zone\b[\s\S]*?\n\s*\)', transform_zone, fp)

def place(libid, ref, val, x, y, rot=0):
    fp=get_fp(libid)
    if fp is None: return None
    fp=transform_zone_polygons_to_board_coords(fp, x, y, rot)
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
        "description": "ESP32 UART, reset/boot, and AD7606 serial/control logic nets.",
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
    if net_name in {"CONVST", "ADC_SCLK", "ADC_CS", "ADC_MISO_A", "ADC_MISO_B", "ADC_BUSY", "ADC_RESET",
                    "/MCU_ESP32-S3/ESP_BOOT", "/MCU_ESP32-S3/ESP_EN", "/MCU_ESP32-S3/ESP_RX", "/MCU_ESP32-S3/ESP_TX"}:
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
TIA_REFS = {"C1","C2","C11","CB","D1","R1","RB","RT","RV11","RVFB","U1"}
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

    ROLE_IC=('SOIC-8','SOT-23-5','SOT-23-6','SOT-23','TSSOP','LQFP','D_SMA')

def build_board(emit_routes=False):
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

    # ===== FLOORPLAN: 90 x 50 mm outline, footprints staged outside =====
    BW,BH=90,50
    body.append(outline(0,0,BW,BH))

    def emit_fp(comp, x, y, rot=0, prefix=None):
        ref = comp["ref"]
        sheet = comp["sheet"].strip("/")
        board_ref_by_comp[(sheet, ref)] = ref
        if not comp["footprint"]:
            return
        fp_str = place(comp["footprint"], ref, comp["value"], x, y, rot)
        if fp_str is None:
            raise RuntimeError(f"missing footprint for {ref}: {comp['footprint']}")
        body.append(fp_str)

    WL=["IR","RED","GREEN","BLUE"]
    stage_x = 115.0
    stage_y = 8.0

    def ordered_parts(sheet_name, local_order):
        parts_by_ref = {p["ref"]: p for p in bysheet[sheet_name]}
        ordered = []
        for local_ref in local_order:
            actual_ref = ref_for(sheet_name, local_ref)
            if actual_ref in parts_by_ref:
                ordered.append(parts_by_ref.pop(actual_ref))
        ordered.extend(sorted(parts_by_ref.values(), key=lambda p: p["ref"]))
        return ordered

    def stage_sheet(sheet_name, label, local_order, y, cols=10, dx=17.0, dy=14.0):
        body.append(text(label, stage_x, y - 5.5, 1.2, "Cmts.User"))
        ordered = ordered_parts(sheet_name, local_order)
        for comp in ordered:
            board_ref_by_comp[(comp["sheet"].strip("/"), comp["ref"])] = comp["ref"]
        physical_parts = [comp for comp in ordered if comp["footprint"]]
        for i, comp in enumerate(physical_parts):
            x = stage_x + (i % cols) * dx
            yy = y + (i // cols) * dy
            emit_fp(comp, x, yy, 0)
        rows = max(1, (len(physical_parts) + cols - 1) // cols)
        return y + rows * dy + 12.0

    tia_order = ["D1", "RB", "CB", "U1", "RVFB", "C1", "C2", "RT", "RV11", "R1", "C11"]
    laser_order = ["U11", "R31", "Q1", "R11", "R12", "C22", "R21", "R22", "C21", "CC", "LD"]
    mcu_order = [
        "U9", "C43", "C41", "C42", "C44", "R54", "R59", "R60",
        "SW1", "SW2", "SW3", "Q5", "Q6", "R50", "R51",
        "R52", "R53", "R58", "U10", "J1", "D7", "D8", "R55",
        "R56", "R57", "C45", "C46", "C47", "J2", "D9", "D10",
        "D11", "D12", "D13", "D14",
    ]
    power_io_order = [
        "D10", "D11", "J2", "J5", "C50",
        "U3V3", "C3V3IN", "C3V3OUT", "C3V3BULK",
        "J1", "UADC", "CADCBULK", "CADCAV1", "CADCAV2", "CADCAV3", "CADCAV4", "CADCDRV",
        "CREG1", "CREG2", "CREFIN", "CREFCAP",
        "J4", "UMPD", "UREF", "CINA", "CREF", "RBIAS",
        "RMPD1", "RADC1", "CMPD1", "RMPD2", "RADC2", "CMPD2", "RMPD3", "RADC3", "CMPD3",
        "RMPD4", "RADC4", "CMPD4",
    ]

    for wl in WL:
        stage_y = stage_sheet(f"TIA_{wl}", f"TIA_{wl}", tia_order, stage_y, cols=11)
    for wl in WL:
        stage_y = stage_sheet(f"LASER_{wl}", f"LASER_{wl}", laser_order, stage_y, cols=10)
    stage_y = stage_sheet("MCU_ESP32-S3", "MCU_ESP32-S3", mcu_order, stage_y, cols=8, dx=25.0, dy=33.0)
    stage_sheet("POWER_IO", "POWER_IO", power_io_order, stage_y, cols=8, dx=25.0, dy=33.0)

    net_names, pad_nets_by_ref = build_pad_net_map(nets, board_ref_by_comp, sheets_by_ref)
    for i, net_name in enumerate(net_names, 1):
        P.append(f'  (net {i} "{net_name}")')
    P += emit_net_classes(net_names)
    body = [
        add_pad_nets(block, pad_nets_by_ref.get(fp_ref(block), {}))
        for block in body
        if block
    ]
    if emit_routes:
        raise RuntimeError("Routing is intentionally disabled for the placement-staging PCB.")
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
