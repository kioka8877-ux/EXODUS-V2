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
║  Phase D3 : PBR Swap + Glass (ACTIVE)                                        ║
║                                                                              ║
║  FIX #2 — VULKAN_FORGE 2026-04-09                                           ║
║  - Détection précoce échec depth/SAM                                        ║
║  - Mode PROCEDURAL_FALLBACK : sol+murs+porte+PBR (dimensions réelles)       ║
║  - Log explicite [U03] + JSON depth_status/sam_status                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import json
import sys
import math
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
from pbr_swap_builder import build_pbr_surfaces
from glass_builder import build_glass_planes
from scene_schema import ENVIRONMENT_TO_SCENE_PROFILE, DEFAULT_SCENE_PROFILE

ASSEMBLER_VERSION = "2.2.0"  # FIX #2 — Fallback procédural

REQUIRED_COLLECTIONS = ["ENV_DOME", "ENV_TERRAIN", "ENV_SHADOW", "ENV_GLASS", "ENV_PBR"]

# ─── STATUTS DEPTH / SAM ──────────────────────────────────────────────────────
STATUS_OK        = "OK"
STATUS_FALLBACK  = "FALLBACK"


def _detect_depth_sam_status(depth_map_dir: str, semantic_masks_path: str) -> Dict[str, str]:
    """
    Détecte la disponibilité réelle des depth maps et masques SAM.

    Retourne un dict avec :
      - depth_status : "OK" | "FALLBACK"
      - sam_status   : "OK" | "FALLBACK"
    """
    depth_ok = False
    if depth_map_dir and Path(depth_map_dir).is_dir():
        pngs = list(Path(depth_map_dir).glob("*.png"))
        if pngs and any(p.stat().st_size > 0 for p in pngs):
            depth_ok = True

    sam_ok = False
    if semantic_masks_path and Path(semantic_masks_path).exists():
        try:
            content = Path(semantic_masks_path).read_text().strip()
            if content and content != "{}":
                sam_ok = True
        except Exception:
            pass

    depth_status = STATUS_OK if depth_ok else STATUS_FALLBACK
    sam_status   = STATUS_OK if sam_ok   else STATUS_FALLBACK

    if depth_status == STATUS_FALLBACK or sam_status == STATUS_FALLBACK:
        print(f"[U03] Fallback procédural activé (depth/SAM indisponibles) "
              f"— depth={depth_status}, sam={sam_status}")
    else:
        print(f"[U03] depth={depth_status}, sam={sam_status} — mode normal")

    return {"depth_status": depth_status, "sam_status": sam_status}


def _build_procedural_fallback(collection_name: str = "ENV_TERRAIN") -> List[bpy.types.Object]:
    """
    Génère un intérieur house_interior procédural en dimensions réelles.

    Géométrie :
      - Sol        : 4x4m, Z=0
      - Mur arrière: 4x2.5m, Y=-2, Z=1.25
      - Mur gauche : 2.5x2.5m, X=-2, Z=1.25
      - Mur droit  : 2.5x2.5m, X=+2, Z=1.25
      - Porte      : 0.9x2m (découpe symbolique sur mur arrière)
      - Plafond    : 4x4m, Z=2.5

    Matériaux PBR par défaut (Principled BSDF, roughness=0.8).

    Returns:
        Liste des objets créés.
    """
    coll = _ensure_collection(collection_name)
    created = []

    def _make_pbr_mat(name: str, base_color=(0.8, 0.8, 0.8, 1.0),
                      roughness: float = 0.8) -> bpy.types.Material:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = base_color
            bsdf.inputs["Roughness"].default_value = roughness
        return mat

    def _add_plane(name, size_x, size_y, loc, rot_euler=(0, 0, 0),
                   mat=None) -> bpy.types.Object:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = (size_x, size_y, 1.0)
        obj.rotation_euler = rot_euler
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        if mat:
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll.objects.link(obj)
        created.append(obj)
        return obj

    mat_floor   = _make_pbr_mat("fallback_floor",   (0.55, 0.45, 0.35, 1.0), 0.9)
    mat_wall    = _make_pbr_mat("fallback_wall",     (0.85, 0.83, 0.80, 1.0), 0.8)
    mat_ceiling = _make_pbr_mat("fallback_ceiling",  (0.95, 0.95, 0.95, 1.0), 0.7)

    # Sol 4x4m
    _add_plane("fallback_floor",    4.0, 4.0, (0, 0, 0),     mat=mat_floor)

    # Plafond 4x4m à Z=2.5
    _add_plane("fallback_ceiling",  4.0, 4.0, (0, 0, 2.5),   mat=mat_ceiling)

    # Mur arrière 4x2.5m
    _add_plane("fallback_wall_back",  4.0, 2.5,
               (0, -2.0, 1.25),
               rot_euler=(math.radians(90), 0, 0),
               mat=mat_wall)

    # Mur gauche 4x2.5m
    _add_plane("fallback_wall_left",  4.0, 2.5,
               (-2.0, 0, 1.25),
               rot_euler=(math.radians(90), 0, math.radians(90)),
               mat=mat_wall)

    # Mur droit 4x2.5m
    _add_plane("fallback_wall_right", 4.0, 2.5,
               (2.0, 0, 1.25),
               rot_euler=(math.radians(90), 0, math.radians(90)),
               mat=mat_wall)

    # Porte symbolique (plan 0.9x2m sur mur arrière, offset légèrement)
    mat_door = _make_pbr_mat("fallback_door", (0.35, 0.22, 0.10, 1.0), 0.6)
    _add_plane("fallback_door",  0.9, 2.0,
               (0.5, -1.99, 1.0),
               rot_euler=(math.radians(90), 0, 0),
               mat=mat_door)

    print(f"[U03] PROCEDURAL_FALLBACK construit — {len(created)} objets "
          f"(sol 4x4m, murs 2.5m, porte 0.9x2m)")
    return created


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


def _inject_actor(
    actor_blend_dir: str,
    scene_data: Dict,
    collection_name: str = "ACTOR",
) -> int:
    """
    Appends actor(s) from ACTOR_*.blend files into the current Blender scene.

    Returns:
        Number of actor objects appended (0 if none found or error).
    """
    if not actor_blend_dir:
        print("[ASSEMBLER] actor_blend_dir vide — injection acteur ignorée")
        return 0

    actor_dir = Path(actor_blend_dir)
    if not actor_dir.exists():
        print(f"[ASSEMBLER:WARN] actor_blend_dir introuvable : {actor_dir} — injection ignorée")
        return 0

    characters = scene_data.get("characters", [])
    if not characters:
        print("[ASSEMBLER] Aucun personnage défini dans la scène — injection ignorée")
        return 0

    actor_blends = sorted(actor_dir.glob("ACTOR_*.blend"))
    if not actor_blends:
        print(f"[ASSEMBLER:WARN] Aucun ACTOR_*.blend trouvé dans {actor_dir}")
        return 0

    actor_coll = _ensure_collection(collection_name)
    total_appended = 0

    for i, char in enumerate(characters):
        char_id = char.get("character_id", "unknown")
        blend_path = actor_blends[min(i, len(actor_blends) - 1)]
        print(f"[ASSEMBLER] Injection acteur : character_id={char_id!r} → {blend_path.name}")

        try:
            with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
                data_to.objects = list(data_from.objects)

            count = 0
            for obj in data_to.objects:
                if obj is None:
                    continue
                scene_obj_names = [o.name for o in bpy.context.scene.collection.objects]
                if obj.name not in scene_obj_names:
                    bpy.context.scene.collection.objects.link(obj)
                actor_coll_names = [o.name for o in actor_coll.objects]
                if obj.name not in actor_coll_names:
                    actor_coll.objects.link(obj)
                count += 1

            total_appended += count
            print(f"[ASSEMBLER] {count} objet(s) acteur injecté(s) depuis {blend_path.name}")

        except Exception as e:
            print(f"[ASSEMBLER:ERROR] Echec injection acteur {blend_path.name} : {e}")

    return total_appended


def _collect_glass_planes_info() -> List[Dict]:
    glass_planes_info = []
    for obj in bpy.data.objects:
        if obj.name.startswith("glass_plane_"):
            plane_info = {"z_offset": obj.location.z, "transmission": 0.0, "roughness": 1.0}
            if obj.data.materials:
                mat = obj.data.materials[0]
                if mat.use_nodes:
                    for node in mat.node_tree.nodes:
                        if node.type == "BSDF_PRINCIPLED":
                            plane_info["transmission"] = node.inputs["Transmission Weight"].default_value
                            plane_info["roughness"] = node.inputs["Roughness"].default_value
                            break
            glass_planes_info.append(plane_info)
    return glass_planes_info


def _build_scene_report() -> Dict:
    """
    Construit le rapport de scène pour validation par scene_schema.validate_scene().
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
        "glass_planes": _collect_glass_planes_info(),
    }


def assemble_scene(
    scene_data: Dict,
    depth_map_dir: str = "",
    semantic_masks_path: str = "",
    hdri_path: Optional[str] = None,
    output_dir: str = ".",
    exposure_strength: float = 1.0,
    vram_profile: str = "colab_t4",
    actor_blend_dir: str = "",
) -> Dict:
    """
    Assemble une scène complète Tri-Layer.

    FIX #2 : Détection précoce depth/SAM + PROCEDURAL_FALLBACK si indisponibles.
    Ne skip jamais l'assemblage — produit toujours environment_*.blend.
    """
    scene_id = scene_data.get("scene_id", "unknown")
    env = scene_data.get("environment", {})

    environment_id = env.get("environment_id", "")
    scene_profile = ENVIRONMENT_TO_SCENE_PROFILE.get(environment_id, DEFAULT_SCENE_PROFILE)
    scene_type = scene_profile["scene_type"]
    dome_fallback = scene_profile["dome_fallback"]
    mood = env.get("lighting_mood") or scene_profile["world_mood"]

    print(f"\n[ASSEMBLER] === Assemblage scène {scene_id} ===")
    print(f"[ASSEMBLER] environment_id={environment_id!r} → scene_type={scene_type}, mood={mood}")
    print(f"[ASSEMBLER] exposure={exposure_strength}, vram={vram_profile}")

    # ── FIX #2 : Détection précoce depth / SAM ───────────────────────────────
    depth_sam = _detect_depth_sam_status(depth_map_dir, semantic_masks_path)
    depth_status = depth_sam["depth_status"]
    sam_status   = depth_sam["sam_status"]
    use_fallback = (depth_status == STATUS_FALLBACK or sam_status == STATUS_FALLBACK)
    # ─────────────────────────────────────────────────────────────────────────

    _clear_scene()

    for coll_name in REQUIRED_COLLECTIONS:
        _ensure_collection(coll_name)
    print(f"[ASSEMBLER] {len(REQUIRED_COLLECTIONS)} collections créées")

    dome_obj = build_infinity_dome(collection_name="ENV_DOME", radius=100.0)

    video_frame = env.get("video_frame_path")
    if video_frame:
        apply_dome_material(dome_obj, video_frame_path=video_frame)
    else:
        apply_dome_material(dome_obj, fallback_color=dome_fallback)

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

    # ── FIX #2 : Branche FALLBACK vs NORMAL ──────────────────────────────────
    if use_fallback:
        print(f"[U03] Mode PROCEDURAL_FALLBACK — depth={depth_status}, sam={sam_status}")
        fallback_objects = _build_procedural_fallback(collection_name="ENV_TERRAIN")
        displacement_obj = None
        pbr_objects      = []
        glass_objects    = []
        print(f"[U03] PROCEDURAL_FALLBACK prêt — {len(fallback_objects)} objets générés")
    else:
        displacement_obj = build_displacement_mesh(
            collection_name="ENV_TERRAIN",
            depth_map_dir=depth_map_dir,
            semantic_masks_path=semantic_masks_path,
            vram_profile=vram_profile,
        )
        pbr_objects = build_pbr_surfaces(
            collection_name="ENV_PBR",
            semantic_masks_path=semantic_masks_path,
        )
        glass_objects = build_glass_planes(
            collection_name="ENV_GLASS",
            semantic_masks_path=semantic_masks_path,
        )
    # ─────────────────────────────────────────────────────────────────────────

    # CAMÉRA DEFAULT — placeholder overridable par U04
    cam_data = bpy.data.cameras.new("camera_main")
    cam_data.lens = 35.0
    cam_obj = bpy.data.objects.new("camera_main", cam_data)
    cam_obj.location = (0.0, -15.0, 8.0)
    cam_obj.rotation_euler = (math.radians(75), 0.0, 0.0)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    print(f"[ASSEMBLER] Caméra default posée — lens=35mm, pos=(0,-15,8), rot=75°")

    actor_count = _inject_actor(
        actor_blend_dir=actor_blend_dir,
        scene_data=scene_data,
    )
    actor_injected = actor_count > 0

    active_layers = "dome,shadow,world_sync,camera"
    active_layers += ",procedural_fallback" if use_fallback else ",displacement,pbr,glass"
    if actor_injected:
        active_layers += ",actor"
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
        "environment_id": environment_id,
        "scene_type": scene_type,
        "mood": mood,
        "exposure_strength": exposure_strength,
        "vram_profile": vram_profile,
        "hdri_used": resolved_hdri is not None,
        "actor_injected": actor_injected,
        "actor_objects_count": actor_count,
        # ── FIX #2 : statuts depth/SAM documentés ──────────────────────────
        "depth_status": depth_status,
        "sam_status": sam_status,
        "procedural_fallback_active": use_fallback,
        # ───────────────────────────────────────────────────────────────────
        "scene_report": scene_report,
    }

    print(f"[ASSEMBLER] === Scène {scene_id} terminée — "
          f"fallback={'OUI' if use_fallback else 'NON'} ===\n")
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
                        help="Répertoire des depth maps")
    parser.add_argument("--semantic-masks", default="",
                        help="Chemin semantic_masks.json")
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
    parser.add_argument("--actor-blend-dir", default="",
                        help="Répertoire contenant les ACTOR_*.blend")
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
            actor_blend_dir=args.actor_blend_dir,
        )
        results.append(result)

    summary_path = Path(args.output_dir) / "assembler_results.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[ASSEMBLER] Résumé écrit : {summary_path}")
    print(f"[ASSEMBLER] {len(results)} scène(s) assemblée(s)")


if __name__ == "__main__":
    main()
