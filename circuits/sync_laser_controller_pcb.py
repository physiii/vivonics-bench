#!/usr/bin/env python3
"""Merge the current schematic footprint set into the hand-placed PCB.

This intentionally does not regenerate the board.  Existing schematic-matching
footprints keep their placement; missing or footprint-changed refs are staged
outside the 90 x 50 mm outline for manual placement.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import gen_pcb
from check_laser_controller_netlist import parse_components
from check_pcb_staging import bboxes_overlap, footprint_bbox, footprint_ref


DEFAULT_BOARD = Path(__file__).resolve().parent / "laser_controller.kicad_pcb"
DEFAULT_NETLIST = Path("/tmp/lc.net")
BOARD_W_MM = 90.0
BOARD_H_MM = 50.0
OUTSIDE_MARGIN_MM = 5.0

STAGE_ORDER = [
    "J5", "J6",
    "C61", "C62", "U15", "C63", "L1", "C64", "C65", "R61", "R62",
    "U16", "C66", "L2", "C67", "C68", "R63", "R64", "C69", "C70",
]

STAGE_PLACEMENTS = {
    "J5": (305.0, 76.0, 0.0),
    "J6": (334.0, 76.0, 0.0),
    "C61": (294.0, 98.0, 0.0),
    "C62": (300.0, 98.0, 0.0),
    "U15": (306.0, 103.0, 0.0),
    "C63": (306.0, 98.0, 0.0),
    "L1": (314.0, 103.0, 0.0),
    "C64": (322.0, 100.0, 0.0),
    "C65": (322.0, 105.0, 0.0),
    "R61": (306.0, 110.0, 0.0),
    "R62": (313.0, 110.0, 0.0),
    "U16": (338.0, 103.0, 0.0),
    "C66": (338.0, 98.0, 0.0),
    "L2": (346.0, 103.0, 0.0),
    "C67": (354.0, 100.0, 0.0),
    "C68": (354.0, 105.0, 0.0),
    "R63": (338.0, 110.0, 0.0),
    "R64": (345.0, 110.0, 0.0),
    "C69": (352.0, 110.0, 0.0),
    "C70": (369.0, 103.0, 0.0),
}


def paren_delta(line: str) -> int:
    return line.count("(") - line.count(")")


def top_level_blocks(text: str) -> list[tuple[int, int, str, str]]:
    lines = text.splitlines(keepends=True)
    blocks: list[tuple[int, int, str, str]] = []
    depth = 0
    index = 0
    while index < len(lines):
        if depth == 1 and lines[index].lstrip().startswith("("):
            start = index
            local_depth = 0
            while index < len(lines):
                local_depth += paren_delta(lines[index])
                index += 1
                if local_depth == 0:
                    break
            block = "".join(lines[start:index])
            name_match = re.match(r'\s*\(([^\s\)]+)', block)
            name = name_match.group(1) if name_match else ""
            blocks.append((start, index, name, block))
            continue
        depth += paren_delta(lines[index])
        index += 1
    return blocks


def footprint_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for _, _, name, block in top_level_blocks(text):
        if name != "footprint":
            continue
        ref = footprint_ref(block)
        if ref:
            blocks[ref] = block
    return blocks


def footprint_name(block: str) -> str:
    match = re.match(r'\s*\(footprint\s+(?:"([^"]+)"|([^\s\)]+))', block)
    return match.group(1) if match and match.group(1) is not None else (match.group(2) if match else "")


def footprint_basename(lib_id: str) -> str:
    return lib_id.split(":", 1)[-1]


def component_tstamps(netlist_path: Path) -> dict[str, str]:
    """Return the KiCad schematic symbol UUID used to link each PCB footprint."""
    stamps: dict[str, str] = {}
    in_comp = False
    depth = 0
    block: list[str] = []
    for line in netlist_path.read_text().splitlines():
        text = line.strip()
        if not in_comp and text.startswith("(comp (ref "):
            in_comp = True
            block = [line]
            depth = line.count("(") - line.count(")")
        elif in_comp:
            block.append(line)
            depth += line.count("(") - line.count(")")
        if in_comp and depth == 0:
            joined = "\n".join(block)
            ref = re.search(r'\(comp \(ref "([^"]+)"\)', joined)
            stamp = re.search(r'\(tstamps "([^"]+)"\)', joined)
            if ref and stamp:
                stamps[ref.group(1)] = stamp.group(1)
            in_comp = False
    return stamps


def escape_net_name(name: str) -> str:
    return name.replace("\\", "\\\\").replace('"', '\\"')


def set_footprint_tstamp(block: str, tstamp: str) -> str:
    updated, count = re.subn(
        r'(?m)^(\s*)\(tstamp\s+[^\)]+\)',
        rf'\1(tstamp {tstamp})',
        block,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"could not update footprint tstamp for {footprint_ref(block) or '<unknown>'}")
    return updated


def set_footprint_at(block: str, x: float, y: float, rot: float) -> str:
    replacement = rf'\1(at {x:.3f} {y:.3f} {rot:g})'
    updated, count = re.subn(
        r'(?m)^(\s*)\(at\s+-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?(?:\s+-?\d+(?:\.\d+)?)?\)',
        replacement,
        block,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"could not update footprint placement for {footprint_ref(block) or '<unknown>'}")
    return updated


def pad_name(pad_block: str) -> str:
    match = re.search(r'\(pad\s+(?:"([^"]*)"|([^\s\)]+))', pad_block)
    if not match:
        return ""
    return match.group(1) if match.group(1) is not None else match.group(2)


def update_pad_block(pad_block: str, expected: tuple[int, str] | None) -> str:
    if expected is None:
        return re.sub(r'\s+\(net\s+\d+\s+"[^"]*"\)', "", pad_block)

    code, name = expected
    token = f'(net {code} "{escape_net_name(name)}")'
    if re.search(r'\(net\s+\d+\s+"[^"]*"\)', pad_block):
        return re.sub(r'\(net\s+\d+\s+"[^"]*"\)', token, pad_block)

    if "(tstamp " in pad_block:
        return pad_block.replace("(tstamp ", f"{token} (tstamp ", 1)
    close = pad_block.rfind(")")
    if close < 0:
        raise RuntimeError(f"could not insert pad net token in pad block: {pad_block[:80]}")
    return pad_block[:close].rstrip() + " " + token + pad_block[close:]


def update_footprint_pad_nets(block: str, pad_map: dict[str, tuple[int, str]]) -> str:
    lines = block.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].lstrip().startswith("(pad "):
            start = index
            local_depth = 0
            while index < len(lines):
                local_depth += paren_delta(lines[index])
                index += 1
                if local_depth == 0:
                    break
            pad_block = "".join(lines[start:index])
            output.append(update_pad_block(pad_block, pad_map.get(pad_name(pad_block))))
            continue
        output.append(lines[index])
        index += 1
    return "".join(output)


def outside_outline(bbox: tuple[float, float, float, float]) -> bool:
    return (
        bbox[0] >= BOARD_W_MM + OUTSIDE_MARGIN_MM
        or bbox[2] <= -OUTSIDE_MARGIN_MM
        or bbox[1] >= BOARD_H_MM + OUTSIDE_MARGIN_MM
        or bbox[3] <= -OUTSIDE_MARGIN_MM
    )


def validate_staged_placements(board_text: str, staged_refs: set[str]) -> None:
    bboxes: dict[str, tuple[float, float, float, float]] = {}
    for block in footprint_blocks(board_text).values():
        ref = footprint_ref(block)
        bbox = footprint_bbox(block)
        if ref and bbox:
            bboxes[ref] = bbox

    for ref in sorted(staged_refs):
        bbox = bboxes.get(ref)
        if bbox is None:
            raise RuntimeError(f"staged ref missing bbox: {ref}")
        if not outside_outline(bbox):
            raise RuntimeError(f"staged ref is inside board outline: {ref} bbox={bbox}")
        for other_ref, other_bbox in sorted(bboxes.items()):
            if other_ref == ref:
                continue
            if bboxes_overlap(bbox, other_bbox):
                raise RuntimeError(f"staged ref overlaps existing footprint: {ref} overlaps {other_ref}")


def merge(
    board_path: Path,
    netlist_path: Path,
    force_restage_refs: set[str] | None = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    if not netlist_path.exists():
        raise SystemExit(f"netlist not found: {netlist_path}")
    gen_pcb.NET = str(netlist_path)
    reference_text, _, _, expected_pad_data, _ = gen_pcb.build_board(emit_routes=False)
    reference_blocks = footprint_blocks(reference_text)
    reference_net_blocks = [
        block
        for _, _, name, block in top_level_blocks(reference_text)
        if name in {"net", "net_class"}
    ]

    components = parse_components(netlist_path)
    expected_footprints = {
        comp["ref"]: comp["footprint"]
        for comp in components
        if comp["footprint"]
    }
    expected_tstamps = component_tstamps(netlist_path)
    missing_tstamps = sorted(set(expected_footprints) - set(expected_tstamps))
    if missing_tstamps:
        raise RuntimeError(f"netlist missing component tstamp(s): {missing_tstamps}")

    board_text = board_path.read_text()
    board_blocks = footprint_blocks(board_text)
    expected_refs = set(expected_footprints)
    board_refs = set(board_blocks)
    missing_refs = sorted(expected_refs - board_refs)
    extra_refs = sorted(board_refs - expected_refs)
    changed_refs = sorted(
        ref
        for ref in expected_refs & board_refs
        if footprint_name(board_blocks[ref]) != footprint_basename(expected_footprints[ref])
    )
    staged_refs = set(missing_refs) | set(changed_refs) | (force_restage_refs or set())
    staged_refs &= expected_refs
    unknown_refs = sorted(staged_refs - set(reference_blocks))
    if unknown_refs:
        raise RuntimeError(f"reference board missing footprint block(s): {unknown_refs}")

    staged_blocks: list[str] = []
    ordered_stage_refs = [ref for ref in STAGE_ORDER if ref in staged_refs]
    ordered_stage_refs.extend(sorted(staged_refs - set(ordered_stage_refs)))
    for index, ref in enumerate(ordered_stage_refs):
        placement = STAGE_PLACEMENTS.get(ref)
        if placement is None:
            placement = (300.0 + (index % 8) * 9.0, 125.0 + (index // 8) * 10.0, 0.0)
        staged_block = set_footprint_at(reference_blocks[ref], *placement)
        staged_block = set_footprint_tstamp(staged_block, expected_tstamps[ref])
        staged_blocks.append(staged_block.rstrip() + "\n")

    lines = board_text.splitlines(keepends=True)
    blocks = top_level_blocks(board_text)
    output: list[str] = []
    cursor = 0
    inserted_nets = False

    for start, end, name, block in blocks:
        output.extend(lines[cursor:start])
        cursor = end

        if name in {"net", "net_class"}:
            if not inserted_nets:
                output.extend(net_block.rstrip() + "\n" for net_block in reference_net_blocks)
                inserted_nets = True
            continue

        if name == "footprint":
            ref = footprint_ref(block)
            if ref in extra_refs or ref in staged_refs:
                continue
            updated_block = update_footprint_pad_nets(block, expected_pad_data.get(ref, {}))
            if ref in expected_tstamps:
                updated_block = set_footprint_tstamp(updated_block, expected_tstamps[ref])
            output.append(updated_block)
            continue

        output.append(block)

    tail = lines[cursor:]
    if staged_blocks:
        close_index = next((i for i in range(len(tail) - 1, -1, -1) if tail[i].strip() == ")"), None)
        if close_index is None:
            raise RuntimeError("could not find PCB root close")
        output.extend(tail[:close_index])
        if output and output[-1].strip():
            output.append("\n")
        output.extend(staged_blocks)
        output.extend(tail[close_index:])
    else:
        output.extend(tail)

    merged_text = "".join(output)
    validate_staged_placements(merged_text, staged_refs)
    board_path.write_text(merged_text)
    return missing_refs, extra_refs, changed_refs, ordered_stage_refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument(
        "--restage-ref",
        action="append",
        default=[],
        help="Force a schematic ref to be replaced from the generated footprint and staged outside the board.",
    )
    args = parser.parse_args()
    missing_refs, extra_refs, changed_refs, staged_refs = merge(
        args.board,
        args.netlist,
        set(args.restage_ref),
    )
    print(f"missing refs added/staged: {missing_refs}")
    print(f"extra refs removed: {extra_refs}")
    print(f"changed refs restaged: {changed_refs}")
    print(f"staged outside board: {staged_refs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
