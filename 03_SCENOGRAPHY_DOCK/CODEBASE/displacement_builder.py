#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DISPLACEMENT BUILDER — Couche B (Displacement Mesh) — Script Blender       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Construit un plan subdivisé avec Displace modifier piloté par depth map.   ║
║  Anti-ghosting via depth_map_cleaner (aplatissement zones personnages).      ║
║                                                                              ║
║  Formule subdivision : levels = round(log2(max_subdivisions))               ║
║    colab_t4  (128) → levels=7   |  2^7  = 128                              ║
║    colab_a100(256) → levels=8   |  2^8  = 256                              ║
║    local_low  (64) → levels=6   |  2^6  =  64                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ===================================================================
# SARCOPHAGE — DECRET II — CODEX BRAINSTORM v1 (01.05.2026)
# Ce module est EN STASE quand le mode GLB est actif (--glb-path).
# Non supprime : conserve pour le mode Tri-Layer legacy (sans GLB).
# ===================================================================

import bpy
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scene_schema import VRAM_PROFILES, OBJECT_SPECS

try:
    from depth_map_cleaner import clean_depth_map_batch
    _CLEANER_OK = True
except Exception as _cleaner_err:
    _CLEANER_OK = False
    print(f"[DISPLACEMENT] depth_map_cleaner non chargé (PIL absent dans Blender Python) : {_cleaner_err}")


def _ensure_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    print(f"[DISPLACEMENT] Collection '{name}' créée")
    return coll


def _resolve_depth_map(depth_map_dir: str, semantic_masks_path: str) -> str:
    if not depth_map_dir or not Path(depth_map_dir).is_dir():
        return ""

    pngs = sorted(Path(depth_map_dir).glob("*.png"))
    if not pngs:
        return ""

    if semantic_masks_path and Path(semantic_masks_path).exists() and _CLEANER_OK:
        cleaned_dir = str(Path(depth_map_dir) / "_cleaned")
        results = clean_depth_map_batch(
            depth_map_dir=depth_map_dir,
            semantic_masks_path=semantic_masks_path,
            output_dir=cleaned_dir,
        )
        if results:
            print(f"[DISPLACEMENT] {len(results)} depth maps nettoyées → {cleaned_dir}")
            cleaned_pngs = sorted(Path(cleaned_dir).glob("*.png"))
            if cleaned_pngs:
                return str(cleaned_pngs[0])

    return str(pngs[0])


def build_displacement_mesh(
    collection_name: str = "ENV_TERRAIN",
    depth_map_dir: str = "",
    semantic_masks_path: str = "",
    vram_profile: str = "colab_t4",
    plane_size: float = 200.0,
    displacement_strength: float = 10.0,
) -> bpy.types.Object:
    """
    Construit le displacement mesh avec depth map et anti-ghosting.

    Étapes :
    1. Lire max_subdivisions depuis VRAM_PROFILES
    2. Nettoyer les depth maps si semantic_masks fourni
    3. Créer un plan subdivisé (Simple mode)
    4. Appliquer Displace modifier avec la depth map comme texture
    5. Nommer "displacement_mesh", linker dans collection_name

    Args:
        collection_name: Collection Blender cible (défaut ENV_TERRAIN).
        depth_map_dir: Répertoire contenant les depth maps PNG.
        semantic_masks_path: Chemin vers semantic_masks.json pour anti-ghosting.
        vram_profile: Profil VRAM (colab_t4, colab_a100, local_low).
        plane_size: Taille du plan en unités Blender.
        displacement_strength: Force du Displace modifier.

    Returns:
        L'objet Blender displacement_mesh.
    """
    profile = VRAM_PROFILES.get(vram_profile, VRAM_PROFILES["colab_t4"])
    max_subdivisions = profile["max_subdivisions"]
    levels = max(1, int(round(math.log2(max_subdivisions))))

    coll = _ensure_collection(collection_name)

    depth_map_path = _resolve_depth_map(depth_map_dir, semantic_masks_path)

    bpy.ops.mesh.primitive_plane_add(size=plane_size, location=(0, 0, 0))
    mesh_obj = bpy.context.active_object
    mesh_obj.name = "displacement_mesh"

    subsurf = mesh_obj.modifiers.new(name="Subdivision", type="SUBSURF")
    subsurf.subdivision_type = "SIMPLE"
    subsurf.levels = levels
    subsurf.render_levels = levels

    disp_mod = mesh_obj.modifiers.new(name="Displace", type="DISPLACE")
    disp_mod.mid_level = 0.5
    disp_mod.strength = displacement_strength
    disp_mod.direction = "NORMAL"

    if depth_map_path and Path(depth_map_path).exists():
        tex = bpy.data.textures.new("depth_map_texture", type="IMAGE")
        img = bpy.data.images.load(depth_map_path)
        tex.image = img
        disp_mod.texture = tex
        print(f"[DISPLACEMENT] Texture depth map chargée : {depth_map_path}")
    else:
        tex = bpy.data.textures.new("depth_map_texture", type="IMAGE")
        disp_mod.texture = tex
        print("[DISPLACEMENT] Pas de depth map trouvée — texture vide")

    mesh_obj["exodus_texture_type"] = "DEPTH_MAP_PNG"

    for existing_coll in mesh_obj.users_collection:
        existing_coll.objects.unlink(mesh_obj)
    coll.objects.link(mesh_obj)

    effective_subdivisions = 2 ** levels
    print(
        f"[DISPLACEMENT] displacement_mesh construit — "
        f"size={plane_size}, subdivisions={effective_subdivisions} (levels={levels}), "
        f"strength={displacement_strength}, vram_profile={vram_profile}"
    )
    return mesh_obj
