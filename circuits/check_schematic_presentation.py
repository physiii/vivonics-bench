#!/usr/bin/env python3
"""Presentation guardrails for generated KiCad schematic sheets.

The hierarchy/netlist checks prove connectivity.  This check catches visual
regressions that still make the schematic hard to review: wire segments that
run through a symbol body, and generated net labels placed over symbols,
component reference/value text, visible pin numbers/internal symbol text, or
other labels.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import gen_laser_controller as gen


PROJECT_DIR = Path(__file__).resolve().parent
ROOT = PROJECT_DIR / "laser_controller.kicad_sch"

LABEL_KINDS = ("label", "hierarchical_label", "global_label")
BODY_MARGIN = 0.18
LABEL_BODY_CLEARANCE = 0.35
TEXT_TEXT_CLEARANCE = 0.15
PIN_TOUCH_TOLERANCE = 1e-4
SCHEMATIC_GRID_MM = 1.27
GRID_TOLERANCE = 1e-5
IMPORTED_SOURCE_SHEETS = {"mcu.kicad_sch"}


@dataclass(frozen=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    def expanded(self, amount: float) -> "Box":
        return Box(
            self.left - amount,
            self.top - amount,
            self.right + amount,
            self.bottom + amount,
        )

    def shrunk(self, amount: float) -> "Box":
        return Box(
            self.left + amount,
            self.top + amount,
            self.right - amount,
            self.bottom - amount,
        )

    def overlaps(self, other: "Box") -> bool:
        return (
            self.left < other.right
            and self.right > other.left
            and self.top < other.bottom
            and self.bottom > other.top
        )

    def valid(self) -> bool:
        return self.left < self.right and self.top < self.bottom


@dataclass(frozen=True)
class TextItem:
    kind: str
    text: str
    box: Box


@dataclass(frozen=True)
class SymbolItem:
    ref: str
    lib_id: str
    box: Box


def block_iter(text: str, prefix: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    in_block = False
    for line in text.splitlines():
        if not in_block and line.lstrip().startswith(prefix):
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


def text_width(text: str, size: float) -> float:
    # KiCad's stroke font is narrow; this errs slightly wide for clearance.
    return max(size * 0.8, len(text) * size * 0.72)


def text_box(text: str, x: float, y: float, size: float, justify: str) -> Box:
    width = text_width(text, size)
    height = size * 1.15
    if "right" in justify:
        left, right = x - width, x
    elif "center" in justify:
        left, right = x - width / 2, x + width / 2
    else:
        left, right = x, x + width

    if "bottom" in justify:
        top, bottom = y - height, y + size * 0.18
    elif "top" in justify:
        top, bottom = y - size * 0.18, y + height
    else:
        top, bottom = y - height / 2, y + height / 2
    return Box(left, top, right, bottom)


def first_font_size(block: str, default: float = 1.27) -> float:
    match = re.search(r"\(font \(size ([\d.]+) ([\d.]+)\)\)", block)
    if not match:
        return default
    return max(float(match.group(1)), float(match.group(2)))


def first_justify(block: str, default: str = "left") -> str:
    match = re.search(r"\(justify ([^)]+)\)", block)
    if not match:
        return default
    return match.group(1)


def on_schematic_grid(value: float) -> bool:
    return abs(value / SCHEMATIC_GRID_MM - round(value / SCHEMATIC_GRID_MM)) <= GRID_TOLERANCE


def point_on_schematic_grid(point: tuple[float, float]) -> bool:
    return on_schematic_grid(point[0]) and on_schematic_grid(point[1])


def grid_failure(label: str, point: tuple[float, float]) -> str | None:
    if point_on_schematic_grid(point):
        return None
    return f"{label} at ({point[0]:.4f}, {point[1]:.4f}) is not on the 50 mil schematic grid"


def parse_labels(text: str) -> list[TextItem]:
    labels: list[TextItem] = []
    pattern = re.compile(
        rf'\(({"|".join(LABEL_KINDS)}) "([^"]+)"[^()]*'
        r"(?:\(shape \w+\)\s*)?"
        r"\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\).*?\(effects (?P<effects>.*?)\)\s*\(uuid",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        kind = match.group(1)
        label_text = match.group(2)
        x = float(match.group(3))
        y = float(match.group(4))
        effects = match.group("effects")
        size = first_font_size(effects)
        justify = first_justify(effects, "left")
        labels.append(TextItem(kind, label_text, text_box(label_text, x, y, size, justify)))
    return labels


def parse_visible_properties(symbol_block: str) -> list[TextItem]:
    props: list[TextItem] = []
    for prop in block_iter(symbol_block, "(property "):
        name_match = re.match(r'\s*\(property "([^"]+)" "([^"]*)"', prop)
        at_match = re.search(r"\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)", prop)
        if not name_match or not at_match or " hide" in prop:
            continue
        prop_name, value = name_match.group(1), name_match.group(2)
        if prop_name not in {"Reference", "Value"} or not value:
            continue
        size = first_font_size(prop, 1.0)
        justify = first_justify(prop, "left")
        props.append(
            TextItem(
                f"property:{prop_name}",
                value,
                text_box(value, float(at_match.group(1)), float(at_match.group(2)), size, justify),
            )
        )
    return props


def symbol_body_box(lib_id: str, x: float, y: float) -> Box | None:
    if lib_id == "Espressif:ESP32-S3-WROOM-1":
        return Box(x - 45.72, y - 40.64, x + 45.72, y + 40.64)
    if not lib_id.startswith("viv:"):
        return None
    sym_name = lib_id.removeprefix("viv:")
    sym = gen.SYM.get(sym_name)
    if not sym or sym.get("power"):
        return None
    points = [pt for poly in sym["glyph"] for pt in poly]
    if not points:
        return None
    xs = [x + px for px, _ in points]
    ys = [y - py for _, py in points]
    return Box(min(xs), min(ys), max(xs), max(ys))


def symbol_model(lib_id: str) -> tuple[str, dict] | None:
    if lib_id == "Espressif:ESP32-S3-WROOM-1":
        return lib_id, gen.SYM[lib_id]
    if not lib_id.startswith("viv:"):
        return None
    sym_name = lib_id.removeprefix("viv:")
    sym = gen.SYM.get(sym_name)
    if not sym:
        return None
    return sym_name, sym


def pin_line_segment(
    lx: float, ly: float, angle: int, length: float
) -> tuple[tuple[float, float], tuple[float, float]]:
    if angle == 0:
        return (lx, ly), (lx + length, ly)
    if angle == 180:
        return (lx, ly), (lx - length, ly)
    if angle == 90:
        return (lx, ly), (lx, ly + length)
    if angle == 270:
        return (lx, ly), (lx, ly - length)
    return (lx, ly), (lx, ly)


def value_between(value: float, a: float, b: float, tol: float = PIN_TOUCH_TOLERANCE) -> bool:
    return min(a, b) - tol <= value <= max(a, b) + tol


def point_on_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    tol: float = PIN_TOUCH_TOLERANCE,
) -> bool:
    px, py = point
    ax, ay = start
    bx, by = end
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    return (
        abs(cross) <= tol
        and value_between(px, ax, bx, tol)
        and value_between(py, ay, by, tol)
    )


def segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
    tol: float = PIN_TOUCH_TOLERANCE,
) -> bool:
    for point in (a, b):
        if point_on_segment(point, c, d, tol):
            return True
    for point in (c, d):
        if point_on_segment(point, a, b, tol):
            return True

    def orientation(
        p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]
    ) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return orientation(a, b, c) * orientation(a, b, d) < -tol and orientation(
        c, d, a
    ) * orientation(c, d, b) < -tol


def symbol_pin_contact_failures() -> list[str]:
    failures: list[str] = []
    for sym_name, sym in gen.SYM.items():
        if sym.get("power") or "glyph" not in sym:
            continue
        glyph_segments = [
            segment
            for polyline in sym["glyph"]
            for segment in zip(polyline, polyline[1:])
        ]
        for number, (lx, ly, angle, pin_name, _etype, length) in sym["pins"].items():
            if pin_name == "NC":
                continue
            if length <= 0:
                if any(point_on_segment((lx, ly), *glyph) for glyph in glyph_segments):
                    continue
                failures.append(
                    f"symbol {sym_name}.{number} ({pin_name}) zero-length pin anchor does not touch symbol glyph"
                )
                continue
            pin_segment = pin_line_segment(lx, ly, angle, length)
            if any(segments_intersect(*pin_segment, *glyph) for glyph in glyph_segments):
                continue
            failures.append(
                f"symbol {sym_name}.{number} ({pin_name}) pin stroke does not touch symbol glyph"
            )
    return failures


def symbol_pin_grid_failures() -> list[str]:
    failures: list[str] = []
    for sym_name, sym in gen.SYM.items():
        for number, (lx, ly, _angle, pin_name, _etype, _length) in sym.get("pins", {}).items():
            failure = grid_failure(f"symbol {sym_name}.{number} ({pin_name}) pin anchor", (lx, ly))
            if failure:
                failures.append(failure)
    return failures


def visible_pin_number_box(
    number: str, x: float, y: float, lx: float, ly: float, angle: int, length: float
) -> Box:
    px = x + lx
    py = y - ly
    # KiCad places pin numbers just inside the symbol side.  Use a small
    # corridor instead of one exact text box so generator-side checks catch
    # labels that crowd the pin-number lane after rendering.
    half_height = 0.72
    side_depth = max(3.2, len(number) * 0.8 + 1.4)
    if angle == 0:
        return Box(px + length - 0.25, py - half_height, px + length + side_depth, py + half_height)
    if angle == 180:
        return Box(px - length - side_depth, py - half_height, px - length + 0.25, py + half_height)
    if angle == 90:
        return Box(px - half_height, py - length - side_depth, px + half_height, py - length + 0.25)
    if angle == 270:
        return Box(px - half_height, py + length - 0.25, px + half_height, py + length + side_depth)
    return text_box(number, px, py, 1.0, "center")


def parse_symbol_texts(lib_id: str, ref: str, x: float, y: float) -> list[TextItem]:
    model = symbol_model(lib_id)
    if not model:
        return []
    sym_name, sym = model
    texts: list[TextItem] = []
    for text, lx, ly, size in sym.get("texts", []):
        texts.append(
            TextItem(
                "symbol-text",
                f"{ref}:{text}",
                text_box(text, x + lx, y - ly, size, "center"),
            )
        )

    pin_numbers_hidden = (
        sym.get("power")
        or sym.get("hide_nums")
        or sym_name in getattr(gen, "PASSIVE_GLYPH_NUMS", ())
    )
    if pin_numbers_hidden:
        return texts

    for number, (lx, ly, angle, _pin_name, _etype, length) in sym["pins"].items():
        texts.append(
            TextItem(
                "pin-number",
                f"{ref}.{number}",
                visible_pin_number_box(number, x, y, lx, ly, angle, length),
            )
        )
    return texts


def parse_symbols(text: str) -> tuple[list[SymbolItem], list[TextItem]]:
    symbols: list[SymbolItem] = []
    visible_texts: list[TextItem] = []
    for block in block_iter(text, "(symbol (lib_id "):
        lib_match = re.search(r'\(lib_id "([^"]+)"\)', block)
        at_match = re.search(r"\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)", block)
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
        if not lib_match or not at_match:
            continue
        lib_id = lib_match.group(1)
        x = float(at_match.group(1))
        y = float(at_match.group(2))
        ref = ref_match.group(1) if ref_match else lib_id
        body = symbol_body_box(lib_id, x, y)
        if body and body.valid():
            symbols.append(SymbolItem(ref, lib_id, body))
        visible_texts.extend(parse_visible_properties(block))
        visible_texts.extend(parse_symbol_texts(lib_id, ref, x, y))
    return symbols, visible_texts


def parse_wires(text: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    wires: list[tuple[tuple[float, float], tuple[float, float]]] = []
    pattern = re.compile(
        r"\(wire \(pts \(xy ([\d.-]+) ([\d.-]+)\) \(xy ([\d.-]+) ([\d.-]+)\)\)"
    )
    for match in pattern.finditer(text):
        wires.append(
            (
                (float(match.group(1)), float(match.group(2))),
                (float(match.group(3)), float(match.group(4))),
            )
        )
    return wires


def rounded_point(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], 4), round(point[1], 4))


def parse_label_anchors(text: str) -> list[tuple[float, float]]:
    anchors: list[tuple[float, float]] = []
    pattern = re.compile(
        rf'\(({"|".join(LABEL_KINDS)}) "([^"]+)"[^()]*'
        r"(?:\(shape \w+\)\s*)?"
        r"\(at ([\d.-]+) ([\d.-]+) [\d.-]+\)",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        anchors.append((float(match.group(3)), float(match.group(4))))
    return anchors


def parse_symbol_pin_points(text: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for block in block_iter(text, "(symbol (lib_id "):
        lib_match = re.search(r'\(lib_id "([^"]+)"\)', block)
        at_match = re.search(r"\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)", block)
        if not lib_match or not at_match:
            continue
        model = symbol_model(lib_match.group(1))
        if not model:
            continue
        _sym_name, sym = model
        x = float(at_match.group(1))
        y = float(at_match.group(2))
        for lx, ly, *_rest in sym["pins"].values():
            points.append((x + lx, y - ly))
    return points


def parse_sheet_pin_points(text: str) -> list[tuple[str, tuple[float, float]]]:
    points: list[tuple[str, tuple[float, float]]] = []
    pattern = re.compile(r'\(pin "([^"]+)" \w+ \(at ([\d.-]+) ([\d.-]+) [\d.-]+\)')
    for match in pattern.finditer(text):
        points.append((match.group(1), (float(match.group(2)), float(match.group(3)))))
    return points


def parse_point_objects(text: str, kind: str) -> list[tuple[float, float]]:
    pattern = re.compile(rf"\({kind} \(at ([\d.-]+) ([\d.-]+)\)")
    return [(float(match.group(1)), float(match.group(2))) for match in pattern.finditer(text)]


def loose_wire_endpoint_failures(
    path: Path,
    text: str,
    wires: list[tuple[tuple[float, float], tuple[float, float]]],
) -> list[str]:
    endpoint_counts: Counter[tuple[float, float]] = Counter()
    for start, end in wires:
        endpoint_counts[rounded_point(start)] += 1
        endpoint_counts[rounded_point(end)] += 1

    connected_points = {
        rounded_point(point)
        for point in (
            parse_symbol_pin_points(text)
            + parse_label_anchors(text)
            + [point for _pin_name, point in parse_sheet_pin_points(text)]
            + parse_point_objects(text, "junction")
            + parse_point_objects(text, "no_connect")
        )
    }

    failures: list[str] = []
    for point, count in endpoint_counts.items():
        if count > 1 or point in connected_points:
            continue
        failures.append(
            f"{path.name}: wire endpoint at ({point[0]:.4f}, {point[1]:.4f}) is loose"
        )
    return failures


def segment_enters_box(
    segment: tuple[tuple[float, float], tuple[float, float]], box: Box
) -> bool:
    (x1, y1), (x2, y2) = segment
    body = box.shrunk(BODY_MARGIN)
    if not body.valid():
        return False
    if abs(x1 - x2) < 1e-6:
        if not (body.left < x1 < body.right):
            return False
        return max(y1, y2) > body.top and min(y1, y2) < body.bottom
    if abs(y1 - y2) < 1e-6:
        if not (body.top < y1 < body.bottom):
            return False
        return max(x1, x2) > body.left and min(x1, x2) < body.right
    seg_box = Box(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    return seg_box.overlaps(body)


def sheet_paths(root: Path) -> list[Path]:
    text = root.read_text()
    sheet_files = re.findall(r'\(property "Sheetfile" "([^"]+)"', text)
    return [root, *[root.parent / file_name for file_name in sheet_files]]


def check_sheet(path: Path) -> list[str]:
    text = path.read_text()
    symbols, visible_texts = parse_symbols(text)
    labels = parse_labels(text)
    wires = parse_wires(text)
    failures: list[str] = []
    for start, end in wires:
        if abs(start[0] - end[0]) > 1e-6 and abs(start[1] - end[1]) > 1e-6:
            failures.append(f"{path.name}: diagonal wire {start}->{end}")
    if path.name in IMPORTED_SOURCE_SHEETS:
        return failures

    failures.extend(loose_wire_endpoint_failures(path, text, wires))

    for block in block_iter(text, "(symbol (lib_id "):
        lib_match = re.search(r'\(lib_id "([^"]+)"\)', block)
        at_match = re.search(r"\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)", block)
        if not lib_match or not at_match:
            continue
        point = (float(at_match.group(1)), float(at_match.group(2)))
        failure = grid_failure(f"{path.name}: symbol {lib_match.group(1)} origin", point)
        if failure:
            failures.append(failure)

    for start, end in wires:
        for point in (start, end):
            failure = grid_failure(f"{path.name}: wire endpoint", point)
            if failure:
                failures.append(failure)

    label_pattern = re.compile(
        rf'\(({"|".join(LABEL_KINDS)}) "([^"]+)"[^()]*'
        r"(?:\(shape \w+\)\s*)?"
        r"\(at ([\d.-]+) ([\d.-]+) [\d.-]+\)",
        re.DOTALL,
    )
    for match in label_pattern.finditer(text):
        point = (float(match.group(3)), float(match.group(4)))
        failure = grid_failure(f"{path.name}: {match.group(1)} `{match.group(2)}` anchor", point)
        if failure:
            failures.append(failure)

    for kind in ("junction", "no_connect"):
        for point in parse_point_objects(text, kind):
            failure = grid_failure(f"{path.name}: {kind}", point)
            if failure:
                failures.append(failure)

    for pin_name, point in parse_sheet_pin_points(text):
        failure = grid_failure(f"{path.name}: sheet pin `{pin_name}`", point)
        if failure:
            failures.append(failure)

    for wire in wires:
        for symbol in symbols:
            if segment_enters_box(wire, symbol.box):
                failures.append(
                    f"{path.name}: wire {wire[0]}->{wire[1]} enters {symbol.ref} ({symbol.lib_id}) body"
                )

    for label in labels:
        label_box = label.box.expanded(LABEL_BODY_CLEARANCE)
        for symbol in symbols:
            if label_box.overlaps(symbol.box):
                failures.append(
                    f"{path.name}: {label.kind} `{label.text}` overlaps {symbol.ref} ({symbol.lib_id}) body"
                )
        for visible_text in visible_texts:
            if label_box.overlaps(visible_text.box.expanded(TEXT_TEXT_CLEARANCE)):
                failures.append(
                    f"{path.name}: {label.kind} `{label.text}` overlaps visible {visible_text.kind} `{visible_text.text}`"
                )

    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            if left.box.expanded(TEXT_TEXT_CLEARANCE).overlaps(
                right.box.expanded(TEXT_TEXT_CLEARANCE)
            ):
                failures.append(
                    f"{path.name}: {left.kind} `{left.text}` overlaps {right.kind} `{right.text}`"
                )

    return failures


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    failures = symbol_pin_contact_failures()
    failures.extend(symbol_pin_grid_failures())
    for path in sheet_paths(root):
        if not path.exists():
            failures.append(f"missing sheet {path}")
            continue
        failures.extend(check_sheet(path))

    if failures:
        print(f"FAIL {len(failures)} schematic presentation checks")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS schematic presentation guardrails: no generated wire segments enter "
        "symbol bodies, no loose wire endpoints, labels clear symbols/text, symbol "
        "pin anchors/strokes touch their glyphs, and generated connection objects "
        "stay on the 50 mil grid; imported source sheets are checked for non-diagonal wires"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
