#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      LAYER ASSEMBLER — Assemblage Tri-Layer — Script Blender Headless       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Appelé par EXO_03_SCENOGRAPHY.py via :                                     ║
║    blender --background --python layer_assembler.py -- [args]               ║
║                                                                              ║
║  Phase D1 : Dome + Shadow Catcher + World Sync                              ║
║  Phase D2 : Displacement Mesh (ACTIVE)                                       ║
║  Phase D3 (stub) : PBR Swap + Glass — placeholders                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dome_builder import build_infinity_dome, apply_dome_material
from shadow_catcher_builder import build_shadow_catcher
from world_sync import setup_world_sync, setup_render_settings
from displacement_builder import build_displacement_mesh

ASSEMBLER_VERSION = "2.0.0"

REQUIRED_COLLECTIONS = ["ENV_DOME", "ENV_TERRAIN", "ENV_SHADOW", "ENV_GLASS", "ENV_PBR"]


def _ensure_collection(name: str) -> bpy.types.Collection:
    """Crée ou récupère une collection par nom et la linke à la scène."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def _clear_scene() -> None:
    """Supprime tous les objets, meshes, matériaux et collections orphelines."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=True)

    for block_type in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for block in block_type:
            if block.users == 0:
                block_type.remove(block)

    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)

    print("[ASSEMBLER] Scène vidée")


def _stamp_custom_properties(active_layers: str) -> None:
    """
    Appose les custom properties exodus_* sur la scène active.

    Args:
        active_layers: CSV des couches actives (ex: "dome,shadow,world_sync").
    """
    scene = bpy.context.scene
    scene["exodus_schema_version"] = "2.0.0"
    scene["exodus_frigate"] = "U03"
    scene["exodus_validated"] = False
    scene["exodus_layers"] = active_layers
    print(f"[ASSEMBLER] Custom properties stampées — layers={active_layers}")


def _build_scene_report() -> Dict:
    """
    Construit le rapport de scène pour validation par scene_schema.validate_scene().

    Returns:
        Dict conforme au format scene_report attendu par SceneSchema.
    """
    collections = [c.name for c in bpy.data.collections]
    objects = {}
    for obj in bpy.data.objects:
        objects[obj.name] = obj.type

    world_info = {"use_nodes": False, "node_types": [], "strength": 1.0}
    world = bpy.context.scene.world
    if world and world.use_nodes:
        world_info["use_nodes"] = True
        world_info["node_types"] = [n.bl_idname for n in world.node_tree.nodes]
        for node in world.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBackground":
                world_info["strength"] = node.inputs["Strength"].default_value
                break

    props = {}
    scene = bpy.context.scene
    for key in ("exodus_schema_version", "exodus_frigate", "exodus_validated", "exodus_layers"):
        if key in scene:
            props[key] = scene[key]

    dm_info = {"subdivisions": 0, "has_displace_modifier": False, "texture_type": ""}
    dm_obj = bpy.data.objects.get("displacement_mesh")
    if dm_obj:
        for mod in dm_obj.modifiers:
            if mod.type == "DISPLACE":
                dm_info["has_displace_modifier"] = True
            if mod.type == "SUBSURF":
                dm_info["subdivisions"] = 2 ** mod.levels
        dm_info["texture_type"] = dm_obj.get("exodus_texture_type", "")
        dm_info["exodus_stub"] = dm_obj.get("exodus_stub", False)

    sc_info = {"is_shadow_catcher": False, "visible_camera": True, "visible_diffuse": True}
    sc_obj = bpy.data.objects.get("shadow_catcher")
    if sc_obj:
        sc_info["is_shadow_catcher"] = sc_obj.is_shadow_catcher
        sc_info["visible_camera"] = sc_obj.visible_camera
        sc_info["visible_diffuse"] = sc_obj.visible_diffuse

    return {
        "collections": collections,
        "objects": objects,
        "world": world_info,
        "custom_properties": props,
        "displacement_mesh": dm_info,
        "shadow_catcher": sc_info,
        "glass_planes": [],
    }


def assemble_scene(
    scene_data: Dict,
    depth_map_dir: str = "",
    semantic_masks_path: str = "",
    hdri_path: Optional[str] = None,
    output_dir: str = ".",
    exposure_strength: float = 1.0,
    vram_profile: str = "colab_t4",
) -> Dict:
    """
    Assemble une scène complète Tri-Layer.

    Phase D1 active :
    - Couche A : Infinity Dome (dome_builder)
    - Shadow Catcher (shadow_catcher_builder)
    - World Sync (world_sync)
    - Custom Properties exodus_*

    Phase D2 active :
    - Couche B : Displacement Mesh — depth map displacement (ENV_TERRAIN)

    Phase D3 (stub) :
    - Couche C : PBR Swap — placeholder collection ENV_PBR
    - Glass planes — placeholder collection ENV_GLASS

    Args:
        scene_data: Données de la scène depuis PRODUCTION_PLAN.
        depth_map_dir: Répertoire des depth maps (D2 futur).
        semantic_masks_path: Chemin semantic_masks.json (D3 futur).
        hdri_path: Chemin vers le HDRi.
        output_dir: Répertoire de sortie pour le .blend.
        exposure_strength: Strength d'exposition World Sync.
        vram_profile: Profil VRAM (colab_t4, colab_a100, local_low).

    Returns:
        Dict avec les métadonnées de la scène assemblée.
    """
    scene_id = scene_data.get("scene_id", "unknown")
    env = scene_data.get("environment", {})
    mood = env.get("lighting_mood", "natural")

    print(f"\n[ASSEMBLER] === Assemblage scène {scene_id} ===")
    print(f"[ASSEMBLER] Mood={mood}, exposure={exposure_strength}, vram={vram_profile}")

    _clear_scene()

    for coll_name in REQUIRED_COLLECTIONS:
        _ensure_collection(coll_name)
    print(f"[ASSEMBLER] {len(REQUIRED_COLLECTIONS)} collections créées")

    dome_obj = build_infinity_dome(collection_name="ENV_DOME", radius=100.0)

    video_frame = env.get("video_frame_path")
    if video_frame:
        apply_dome_material(dome_obj, video_frame_path=video_frame)

    sc_obj = build_shadow_catcher(collection_name="ENV_SHADOW", size=50.0)

    resolved_hdri = hdri_path
    if not resolved_hdri:
        hdri_from_env = env.get("hdri_path")
        if hdri_from_env and Path(hdri_from_env).exists():
            resolved_hdri = hdri_from_env

    setup_world_sync(
        hdri_path=resolved_hdri,
        mood=mood,
        exposure_strength=exposure_strength,
    )

    setup_render_settings(engine="CYCLES", samples=128)

    displacement_obj = build_displacement_mesh(
        collection_name="ENV_TERRAIN",
        depth_map_dir=depth_map_dir,
        semantic_masks_path=semantic_masks_path,
        vram_profile=vram_profile,
    )

    _ensure_collection("ENV_GLASS")
    _ensure_collection("ENV_PBR")

    active_layers = "dome,shadow,world_sync,displacement"
    _stamp_custom_properties(active_layers)

    try:
        bpy.ops.file.pack_all()
        print("[ASSEMBLER] Textures packées")
    except Exception as e:
        print(f"[ASSEMBLER] Pack textures ignoré : {e}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    blend_file = output_path / f"environment_{scene_id}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_file))
    print(f"[ASSEMBLER] Sauvegardé : {blend_file}")

    scene_report = _build_scene_report()

    result = {
        "scene_id": scene_id,
        "blend_file": str(blend_file),
        "layers_active": active_layers,
        "mood": mood,
        "exposure_strength": exposure_strength,
        "vram_profile": vram_profile,
        "hdri_used": resolved_hdri is not None,
        "scene_report": scene_report,
    }

    print(f"[ASSEMBLER] === Scène {scene_id} terminée ===\n")
    return result


def main() -> None:
    """Point d'entrée CLI (appelé par Blender --background --python)."""
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(
        description="EXODUS Layer Assembler — Tri-Layer Scene Builder"
    )
    parser.add_argument("--production-plan", required=True,
                        help="Chemin vers PRODUCTION_PLAN.JSON")
    parser.add_argument("--depth-map-dir", default="",
                        help="Répertoire des depth maps (D2 futur)")
    parser.add_argument("--semantic-masks", default="",
                        help="Chemin semantic_masks.json (D3 futur)")
    parser.add_argument("--hdri-path", default="",
                        help="Chemin vers le fichier HDRi")
    parser.add_argument("--output-dir", required=True,
                        help="Répertoire de sortie pour les .blend")
    parser.add_argument("--scene-filter", default="[]",
                        help="JSON array des scene_id à traiter")
    parser.add_argument("--exposure", type=float, default=1.0,
                        help="Strength d'exposition World Sync")
    parser.add_argument("--vram-profile", default="colab_t4",
                        choices=["colab_t4", "colab_a100", "local_low"],
                        help="Profil VRAM")
    args = parser.parse_args(argv)

    plan_path = Path(args.production_plan)
    if not plan_path.exists():
        print(f"[ASSEMBLER:ERROR] Plan introuvable : {plan_path}")
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    scene_filter = json.loads(args.scene_filter) if args.scene_filter else []
    scenes = plan.get("scenes", [])
    results: List[Dict] = []

    hdri = args.hdri_path if args.hdri_path else None

    for scene_data in scenes:
        sid = scene_data.get("scene_id")
        if scene_filter and sid not in scene_filter:
            continue

        result = assemble_scene(
            scene_data=scene_data,
            depth_map_dir=args.depth_map_dir,
            semantic_masks_path=args.semantic_masks,
            hdri_path=hdri,
            output_dir=args.output_dir,
            exposure_strength=args.exposure,
            vram_profile=args.vram_profile,
        )
        results.append(result)

    summary_path = Path(args.output_dir) / "assembler_results.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[ASSEMBLER] Résumé écrit : {summary_path}")
    print(f"[ASSEMBLER] {len(results)} scène(s) assemblée(s)")


if __name__ == "__main__":
    main()
