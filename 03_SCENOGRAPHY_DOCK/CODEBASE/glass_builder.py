#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     GLASS BUILDER — Reflectivity Hack — Glass BSDF Planes                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Crée des plans Glass BSDF sur les zones vitrées détectées par SAM.       ║
║  Z-offset contractuel : 0.01 m (anti z-fighting).                         ║
║                                                                              ║
║  Collection cible : ENV_GLASS                                               ║
║  Validation : scene_schema.validate_glass_planes()                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scene_schema import OBJECT_SPECS, PBR_MATERIAL_PRESETS

_GLASS_SPEC = OBJECT_SPECS["glass_plane_*"]
_GLASS_PRESET = PBR_MATERIAL_PRESETS["glass_clear"]
_Z_OFFSET = _GLASS_SPEC["constraints"]["z_offset"]


def pixel_to_world(
    px: float,
    py: float,
    image_width: int,
    image_height: int,
    world_size: float = 200.0,
) -> Tuple[float, float]:
    x = (px / image_width - 0.5) * world_size
    y = (0.5 - py / image_height) * world_size
    return x, y


def _create_glass_material(index: int) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=f"Glass_BSDF_{index}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)

    bsdf.inputs["Base Color"].default_value = _GLASS_PRESET["base_color"]
    bsdf.inputs["Roughness"].default_value = _GLASS_PRESET["roughness"]
    bsdf.inputs["Metallic"].default_value = _GLASS_PRESET["metallic"]
    bsdf.inputs["Specular IOR Level"].default_value = _GLASS_PRESET["specular"]
    bsdf.inputs["Transmission Weight"].default_value = _GLASS_PRESET["transmission"]

    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    mat.blend_method = "BLEND"
    mat.shadow_method = "HASHED"

    print(f"[GLASS] Matériau créé : Glass_BSDF_{index}")
    return mat


def _ensure_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def build_glass_planes(
    collection_name: str = "ENV_GLASS",
    semantic_masks_path: str = "",
    world_size: float = 200.0,
) -> List[bpy.types.Object]:
    """
    Crée des plans Glass BSDF pour les zones vitrées SAM.

    Returns:
        Liste des objets glass_plane_* créés.
    """
    masks_path = Path(semantic_masks_path)
    if not masks_path.exists():
        print(f"[GLASS] semantic_masks.json introuvable : {masks_path} — aucun glass plane")
        return []

    with open(masks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    masks = data.get("masks", [])
    image_size = data.get("image_size", [1920, 1080])
    img_w, img_h = image_size[0], image_size[1]

    glass_masks = [m for m in masks if m.get("label") == "glass"]
    if not glass_masks:
        print("[GLASS] Aucun masque 'glass' — aucun glass plane")
        return []

    coll = _ensure_collection(collection_name)
    created: List[bpy.types.Object] = []

    for idx, mask in enumerate(glass_masks):
        bbox = mask.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox

        cx_px = (x1 + x2) / 2.0
        cy_px = (y1 + y2) / 2.0
        cx, cy = pixel_to_world(cx_px, cy_px, img_w, img_h, world_size)

        w_px = abs(x2 - x1)
        h_px = abs(y2 - y1)
        w_world = (w_px / img_w) * world_size
        h_world = (h_px / img_h) * world_size

        obj_name = f"glass_plane_{idx}"

        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(cx, cy, _Z_OFFSET))
        obj = bpy.context.active_object
        obj.name = obj_name
        obj.scale = (w_world, h_world, 1.0)

        mat = _create_glass_material(idx)
        obj.data.materials.clear()
        obj.data.materials.append(mat)

        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

        created.append(obj)
        print(f"[GLASS] {obj_name} → z={_Z_OFFSET}, pos=({cx:.2f}, {cy:.2f}), size=({w_world:.2f}×{h_world:.2f})")

    print(f"[GLASS] {len(created)} glass plane(s) créé(s) dans {collection_name}")
    return created
