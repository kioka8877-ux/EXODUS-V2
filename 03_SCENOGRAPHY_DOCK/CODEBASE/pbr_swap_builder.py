#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     PBR SWAP BUILDER — Couche C — SAM Masks → PBR Surfaces                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Crée des surfaces PBR (Principled BSDF) sur les zones foreground          ║
║  détectées par le segmenteur SAM.                                          ║
║                                                                              ║
║  Mapping : semantic_masks.json → SAM_LABEL_TO_PBR → PBR_MATERIAL_PRESETS   ║
║  Collection cible : ENV_PBR                                                 ║
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

from scene_schema import SAM_LABEL_TO_PBR, PBR_MATERIAL_PRESETS

EXCLUDED_LABELS = {"sky", "glass"}


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


def _create_pbr_material(preset_name: str, preset: Dict) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=f"PBR_{preset_name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)

    bsdf.inputs["Base Color"].default_value = preset["base_color"]
    bsdf.inputs["Roughness"].default_value = preset["roughness"]
    bsdf.inputs["Metallic"].default_value = preset["metallic"]
    bsdf.inputs["Specular IOR Level"].default_value = preset["specular"]

    if "transmission" in preset:
        bsdf.inputs["Transmission Weight"].default_value = preset["transmission"]

    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    print(f"[PBR_SWAP] Matériau créé : PBR_{preset_name}")
    return mat


def _ensure_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def build_pbr_surfaces(
    collection_name: str = "ENV_PBR",
    semantic_masks_path: str = "",
    world_size: float = 200.0,
    z_offset: float = 0.02,
) -> List[bpy.types.Object]:
    """
    Crée des surfaces PBR pour les zones SAM proches.

    Returns:
        Liste des objets pbr_surface_* créés.
    """
    masks_path = Path(semantic_masks_path)
    if not masks_path.exists():
        print(f"[PBR_SWAP] semantic_masks.json introuvable : {masks_path} — aucune surface PBR")
        return []

    with open(masks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    masks = data.get("masks", [])
    image_size = data.get("image_size", [1920, 1080])
    img_w, img_h = image_size[0], image_size[1]

    if not masks:
        print("[PBR_SWAP] Aucun masque dans semantic_masks.json — aucune surface PBR")
        return []

    coll = _ensure_collection(collection_name)
    created: List[bpy.types.Object] = []
    label_counters: Dict[str, int] = {}

    for mask in masks:
        label = mask.get("label", "")

        if label not in SAM_LABEL_TO_PBR:
            continue

        preset_name = SAM_LABEL_TO_PBR[label]
        if preset_name is None:
            continue

        if label in EXCLUDED_LABELS:
            continue

        preset = PBR_MATERIAL_PRESETS.get(preset_name, PBR_MATERIAL_PRESETS["default"])

        bbox = mask.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox

        cx_px = (x1 + x2) / 2.0
        cy_px = (y1 + y2) / 2.0
        cx, cy = pixel_to_world(cx_px, cy_px, img_w, img_h, world_size)

        w_px = abs(x2 - x1)
        h_px = abs(y2 - y1)
        w_world = (w_px / img_w) * world_size
        h_world = (h_px / img_h) * world_size

        idx = label_counters.get(label, 0)
        label_counters[label] = idx + 1
        obj_name = f"pbr_surface_{label}_{idx}"

        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(cx, cy, z_offset))
        obj = bpy.context.active_object
        obj.name = obj_name
        obj.scale = (w_world, h_world, 1.0)

        mat = _create_pbr_material(preset_name, preset)
        obj.data.materials.clear()
        obj.data.materials.append(mat)

        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

        created.append(obj)
        print(f"[PBR_SWAP] {obj_name} → preset={preset_name}, pos=({cx:.2f}, {cy:.2f}, {z_offset}), size=({w_world:.2f}×{h_world:.2f})")

    print(f"[PBR_SWAP] {len(created)} surface(s) PBR créée(s) dans {collection_name}")
    return created
