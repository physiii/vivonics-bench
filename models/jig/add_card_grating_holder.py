"""Add a low-profile card/grating holder to the open Blender scene.

Run with Blender 5.2 or newer:

    blender --background jig.blend --python add_card_grating_holder.py

The scene uses one Blender unit as one millimeter, matching the existing STL
exports even though the scene's display-unit metadata says meters.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


COLLECTION_NAME = "card-grating-holder"
OBJECT_NAME = "Card_Grating_Holder"
MATERIAL_NAME = "Card_Grating_Holder_Blue"

REFERENCE_BASE_NAME = "Base_Plate_B2"
REFERENCE_HOLDER_NAME = "Lens_Punch_B"
REFERENCE_RAZOR_ASSEMBLY_NAME = "Razor_Assembly"

HEIGHT_RATIO = 0.5
BLOCK_WIDTH_MM = 40.0
BLOCK_DEPTH_MM = 20.0
LENS_CLEARANCE_MM = 20.0

SLOT_DEPTH_MM = 14.0
SLOT_BEVEL_DEPTH_MM = 2.5
SLOT_MOUTH_MM = 3.6
SLOT_THROAT_MM = 1.1
SLOT_TIP_MM = 0.36


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Blend file to save; defaults to the currently open file.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Build the holder without writing the blend file.",
    )
    return parser.parse_args(argv)


def evaluated_world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    corners = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    lower = Vector(min(corner[axis] for corner in corners) for axis in range(3))
    upper = Vector(max(corner[axis] for corner in corners) for axis in range(3))
    return lower, upper


def require_object(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required reference object is missing: {name}")
    return obj


def ensure_collection() -> bpy.types.Collection:
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
    collection.color_tag = "COLOR_05"
    return collection


def remove_previous_holder() -> None:
    existing = bpy.data.objects.get(OBJECT_NAME)
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)


def build_slotted_block_mesh(height_mm: float) -> bpy.types.Mesh:
    half_height = height_mm / 2.0
    half_depth = BLOCK_DEPTH_MM / 2.0

    # This Y-Z outline is a rectangle with a tapered, chamfered notch cut down
    # from its top. Extruding the outline produces one clean watertight solid
    # without relying on an unapplied Boolean modifier.
    outline_yz = [
        (-half_depth, -half_height),
        (half_depth, -half_height),
        (half_depth, half_height),
        (SLOT_MOUTH_MM / 2.0, half_height),
        (SLOT_THROAT_MM / 2.0, half_height - SLOT_BEVEL_DEPTH_MM),
        (SLOT_TIP_MM / 2.0, half_height - SLOT_DEPTH_MM),
        (-SLOT_TIP_MM / 2.0, half_height - SLOT_DEPTH_MM),
        (-SLOT_THROAT_MM / 2.0, half_height - SLOT_BEVEL_DEPTH_MM),
        (-SLOT_MOUTH_MM / 2.0, half_height),
        (-half_depth, half_height),
    ]

    half_width = BLOCK_WIDTH_MM / 2.0
    vertices = [(-half_width, y, z) for y, z in outline_yz]
    vertices.extend((half_width, y, z) for y, z in outline_yz)

    count = len(outline_yz)
    faces: list[list[int]] = [
        list(reversed(range(count))),
        list(range(count, 2 * count)),
    ]
    for index in range(count):
        following = (index + 1) % count
        faces.append([index, following, count + following, count + index])

    mesh = bpy.data.meshes.new(f"{OBJECT_NAME}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=True)
    mesh.update(calc_edges=True)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    return mesh


def ensure_material() -> bpy.types.Material:
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(MATERIAL_NAME)
    material.diffuse_color = (0.055, 0.32, 0.8, 1.0)
    material.metallic = 0.0
    material.roughness = 0.42
    return material


def add_holder() -> bpy.types.Object:
    base = require_object(REFERENCE_BASE_NAME)
    lens_holder = require_object(REFERENCE_HOLDER_NAME)
    razor_assembly = require_object(REFERENCE_RAZOR_ASSEMBLY_NAME)
    base_lower, _ = evaluated_world_bounds(base)
    lens_lower, lens_upper = evaluated_world_bounds(lens_holder)

    reference_height = lens_upper.z - base_lower.z
    height = reference_height * HEIGHT_RATIO
    if height <= SLOT_DEPTH_MM:
        raise RuntimeError(
            f"Derived block height {height:.3f} mm is too small for the slot"
        )

    remove_previous_holder()
    collection = ensure_collection()
    mesh = build_slotted_block_mesh(height)
    holder = bpy.data.objects.new(OBJECT_NAME, mesh)
    collection.objects.link(holder)

    center_x = lens_upper.x + LENS_CLEARANCE_MM + BLOCK_WIDTH_MM / 2.0
    center_y = razor_assembly.matrix_world.translation.y
    center_z = base_lower.z + height / 2.0
    holder.location = (center_x, center_y, center_z)
    holder.data.materials.append(ensure_material())
    holder.color = (0.055, 0.32, 0.8, 1.0)

    holder["purpose"] = "Low-profile holder for plastic cards, film, and gratings"
    holder["print_orientation"] = "Flat base down; no supports"
    holder["reference_lens_height_mm"] = round(reference_height, 3)
    holder["height_ratio"] = HEIGHT_RATIO
    holder["holder_width_mm"] = BLOCK_WIDTH_MM
    holder["holder_depth_mm"] = BLOCK_DEPTH_MM
    holder["holder_height_mm"] = round(height, 3)
    holder["slot_depth_mm"] = SLOT_DEPTH_MM
    holder["slot_mouth_mm"] = SLOT_MOUTH_MM
    holder["slot_throat_mm"] = SLOT_THROAT_MM
    holder["slot_tip_mm"] = SLOT_TIP_MM
    holder["scene_scale_note"] = "1 Blender unit = 1 mm in this jig"

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    holder.hide_set(False)
    holder.hide_viewport = False
    holder.hide_render = False
    holder.select_set(True)
    bpy.context.view_layer.objects.active = holder
    return holder


def main() -> None:
    args = parse_args()
    holder = add_holder()
    print(
        "Created "
        f"{holder.name}: {holder.dimensions.x:.3f} x "
        f"{holder.dimensions.y:.3f} x {holder.dimensions.z:.3f} mm"
    )

    if args.no_save:
        return

    output = args.output.resolve() if args.output else Path(bpy.data.filepath).resolve()
    if not str(output):
        raise RuntimeError("No output path supplied and the current scene has no file path")

    # Keep the user's existing jig.blend1 backup untouched.
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
