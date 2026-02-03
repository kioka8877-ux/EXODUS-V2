#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 ENVIRONMENT BUILDER — EXODUS SCENOGRAPHY                     ║
║          Construction Scènes Blender avec PBR et HDRi                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Script Blender headless pour construire les environnements 3D.

Usage (appelé par EXO_03_SCENOGRAPHY.py):
    blender --background --python environment_builder.py -- \\
        --production-plan plan.json \\
        --hdri-mapping '{"neon": "/path/to/neon.hdr"}' \\
        --assets-mapping '{"env:urban_street": "/path/to/street.blend"}' \\
        --output-dir /path/to/output \\
        --scene-filter '[1, 2, 3]'
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[BUILDER] ERREUR: Ce script doit être exécuté dans Blender")


ENVIRONMENT_TEMPLATES = {
    "urban_street": {
        "ground_size": (100, 100),
        "ground_material": "asphalt",
        "default_props": ["streetlight", "bench", "trash_can"],
        "lighting_style": "overhead_multi"
    },
    "indoor": {
        "ground_size": (20, 20),
        "ground_material": "wood_floor",
        "walls": True,
        "ceiling": True,
        "default_props": ["table", "chair"],
        "lighting_style": "interior"
    },
    "outdoor": {
        "ground_size": (200, 200),
        "ground_material": "grass",
        "default_props": ["tree", "rock"],
        "lighting_style": "sun"
    },
    "studio": {
        "ground_size": (50, 50),
        "ground_material": "studio_floor",
        "cyclorama": True,
        "default_props": [],
        "lighting_style": "three_point"
    }
}


def print_header():
    """Affiche le header du builder."""
    print("\n" + "=" * 60)
    print("   ENVIRONMENT BUILDER — EXODUS SCENOGRAPHY")
    print("=" * 60 + "\n")


def clear_scene():
    """Nettoie la scène Blender pour repartir à zéro."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)
    
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    for image in bpy.data.images:
        bpy.data.images.remove(image)
    
    print("[BUILDER] Scène nettoyée")


def create_environment_collection(scene_id: int) -> 'bpy.types.Collection':
    """Crée une collection pour l'environnement."""
    name = f"Environment_{scene_id}"
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    print(f"[BUILDER] Collection créée: {name}")
    return collection


def create_ground(env_type: str, template: dict, collection: 'bpy.types.Collection') -> 'bpy.types.Object':
    """Crée le sol de l'environnement."""
    size_x, size_y = template.get("ground_size", (50, 50))
    
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.scale = (size_x, size_y, 1)
    bpy.ops.object.transform_apply(scale=True)
    
    for coll in ground.users_collection:
        coll.objects.unlink(ground)
    collection.objects.link(ground)
    
    from pbr_applicator import create_basic_material
    mat_type = template.get("ground_material", "concrete")
    material = create_basic_material(f"Ground_{mat_type}", mat_type)
    ground.data.materials.append(material)
    
    print(f"[BUILDER] Sol créé: {size_x}x{size_y}m, matériau: {mat_type}")
    return ground


def create_walls(template: dict, collection: 'bpy.types.Collection'):
    """Crée les murs pour un environnement intérieur."""
    if not template.get("walls", False):
        return
    
    size_x, size_y = template.get("ground_size", (20, 20))
    wall_height = 3.0
    wall_thickness = 0.2
    
    walls_data = [
        {"pos": (0, size_y/2, wall_height/2), "scale": (size_x, wall_thickness, wall_height)},
        {"pos": (0, -size_y/2, wall_height/2), "scale": (size_x, wall_thickness, wall_height)},
        {"pos": (size_x/2, 0, wall_height/2), "scale": (wall_thickness, size_y, wall_height)},
        {"pos": (-size_x/2, 0, wall_height/2), "scale": (wall_thickness, size_y, wall_height)},
    ]
    
    from pbr_applicator import create_basic_material
    wall_material = create_basic_material("Wall_Plaster", "plaster")
    
    for i, wall in enumerate(walls_data):
        bpy.ops.mesh.primitive_cube_add(size=1, location=wall["pos"])
        obj = bpy.context.active_object
        obj.name = f"Wall_{i+1}"
        obj.scale = wall["scale"]
        bpy.ops.object.transform_apply(scale=True)
        
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        collection.objects.link(obj)
        
        obj.data.materials.append(wall_material)
    
    print(f"[BUILDER] 4 murs créés, hauteur: {wall_height}m")


def create_ceiling(template: dict, collection: 'bpy.types.Collection'):
    """Crée le plafond pour un environnement intérieur."""
    if not template.get("ceiling", False):
        return
    
    size_x, size_y = template.get("ground_size", (20, 20))
    ceiling_height = 3.0
    
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, ceiling_height))
    ceiling = bpy.context.active_object
    ceiling.name = "Ceiling"
    ceiling.scale = (size_x, size_y, 1)
    ceiling.rotation_euler = (3.14159, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    
    for coll in ceiling.users_collection:
        coll.objects.unlink(ceiling)
    collection.objects.link(ceiling)
    
    from pbr_applicator import create_basic_material
    ceiling_material = create_basic_material("Ceiling_White", "plaster")
    ceiling.data.materials.append(ceiling_material)
    
    print(f"[BUILDER] Plafond créé à {ceiling_height}m")


def create_cyclorama(template: dict, collection: 'bpy.types.Collection'):
    """Crée un cyclorama pour un environnement studio."""
    if not template.get("cyclorama", False):
        return
    
    size_x, size_y = template.get("ground_size", (50, 50))
    height = 10.0
    curve_radius = 3.0
    
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -size_y/2, height/2))
    back = bpy.context.active_object
    back.name = "Cyclorama_Back"
    back.scale = (size_x, 1, height)
    back.rotation_euler = (1.5708, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    
    for coll in back.users_collection:
        coll.objects.unlink(back)
    collection.objects.link(back)
    
    from pbr_applicator import create_basic_material
    cyclo_material = create_basic_material("Cyclorama_White", "studio_white")
    back.data.materials.append(cyclo_material)
    
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Cyclorama_Floor"
    floor.scale = (size_x, size_y, 1)
    bpy.ops.object.transform_apply(scale=True)
    
    for coll in floor.users_collection:
        coll.objects.unlink(floor)
    collection.objects.link(floor)
    floor.data.materials.append(cyclo_material)
    
    print(f"[BUILDER] Cyclorama créé: {size_x}x{size_y}m, hauteur: {height}m")


def build_environment(
    scene_data: dict,
    assets_mapping: dict,
    collection: 'bpy.types.Collection'
) -> dict:
    """
    Construit l'environnement complet pour une scène.
    Retourne un dict avec les infos de construction.
    """
    env = scene_data.get("environment", {})
    env_type = env.get("type", "studio")
    
    template = ENVIRONMENT_TEMPLATES.get(env_type, ENVIRONMENT_TEMPLATES["studio"])
    
    print(f"[BUILDER] Construction environnement: {env_type}")
    print(f"[BUILDER] Template: ground={template.get('ground_size')}, style={template.get('lighting_style')}")
    
    create_ground(env_type, template, collection)
    create_walls(template, collection)
    create_ceiling(template, collection)
    create_cyclorama(template, collection)
    
    asset_key = f"env:{env_type}"
    if asset_key in assets_mapping:
        asset_path = assets_mapping[asset_key]
        print(f"[BUILDER] Import asset environnement: {asset_path}")
        import_environment_asset(asset_path, collection)
    
    from props_placer import place_props
    props_list = env.get("props", [])
    props_placed = place_props(props_list, assets_mapping, template, collection)
    
    build_info = {
        "environment_type": env_type,
        "ground_size": template.get("ground_size"),
        "has_walls": template.get("walls", False),
        "has_ceiling": template.get("ceiling", False),
        "has_cyclorama": template.get("cyclorama", False),
        "props_requested": len(props_list),
        "props_placed": props_placed
    }
    
    return build_info


def import_environment_asset(asset_path: str, collection: 'bpy.types.Collection'):
    """Importe un asset environnement depuis un fichier."""
    path = Path(asset_path)
    
    if not path.exists():
        print(f"[BUILDER:WARN] Asset introuvable: {asset_path}")
        return
    
    suffix = path.suffix.lower()
    
    try:
        if suffix == ".blend":
            with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
            
            for obj in data_to.objects:
                if obj is not None:
                    collection.objects.link(obj)
            print(f"[BUILDER] Asset .blend importé: {len(data_to.objects)} objets")
        
        elif suffix in [".glb", ".gltf"]:
            bpy.ops.import_scene.gltf(filepath=str(path))
            imported = bpy.context.selected_objects
            for obj in imported:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                collection.objects.link(obj)
            print(f"[BUILDER] Asset GLTF importé: {len(imported)} objets")
        
        elif suffix == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
            imported = bpy.context.selected_objects
            for obj in imported:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                collection.objects.link(obj)
            print(f"[BUILDER] Asset FBX importé: {len(imported)} objets")
        
        elif suffix == ".obj":
            bpy.ops.wm.obj_import(filepath=str(path))
            imported = bpy.context.selected_objects
            for obj in imported:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                collection.objects.link(obj)
            print(f"[BUILDER] Asset OBJ importé: {len(imported)} objets")
        
        else:
            print(f"[BUILDER:WARN] Format non supporté: {suffix}")
    
    except Exception as e:
        print(f"[BUILDER:ERROR] Erreur import {asset_path}: {e}")


def setup_lighting(lighting_mood: str, hdri_mapping: dict, template: dict):
    """Configure l'éclairage de la scène."""
    from hdri_manager import setup_hdri_lighting, setup_fallback_lighting
    
    if lighting_mood in hdri_mapping:
        hdri_path = hdri_mapping[lighting_mood]
        setup_hdri_lighting(hdri_path, lighting_mood)
    else:
        print(f"[BUILDER:WARN] HDRi manquant pour mood '{lighting_mood}', fallback utilisé")
        setup_fallback_lighting(lighting_mood, template.get("lighting_style", "three_point"))


def save_environment(output_dir: Path, scene_id: int) -> str:
    """Sauvegarde la scène Blender."""
    output_path = output_dir / f"environment_{scene_id}.blend"
    
    bpy.ops.file.pack_all()
    
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    
    print(f"[BUILDER] Scène sauvegardée: {output_path}")
    return str(output_path)


def process_scene(
    scene_data: dict,
    hdri_mapping: dict,
    assets_mapping: dict,
    output_dir: Path
) -> dict:
    """
    Traite une scène complète: construction + éclairage + sauvegarde.
    Retourne un dict avec le résultat.
    """
    scene_id = scene_data.get("scene_id", 0)
    env = scene_data.get("environment", {})
    lighting_mood = env.get("lighting_mood", "natural")
    env_type = env.get("type", "studio")
    
    print(f"\n{'='*60}")
    print(f"[BUILDER] === SCÈNE {scene_id} ===")
    print(f"[BUILDER] Type: {env_type}, Mood: {lighting_mood}")
    print(f"{'='*60}\n")
    
    clear_scene()
    
    collection = create_environment_collection(scene_id)
    
    template = ENVIRONMENT_TEMPLATES.get(env_type, ENVIRONMENT_TEMPLATES["studio"])
    build_info = build_environment(scene_data, assets_mapping, collection)
    
    setup_lighting(lighting_mood, hdri_mapping, template)
    
    output_path = save_environment(output_dir, scene_id)
    
    result = {
        "scene_id": scene_id,
        "status": "SUCCESS",
        "output_file": output_path,
        "build_info": build_info
    }
    
    print(f"\n[BUILDER] Scène {scene_id} terminée avec succès")
    return result


def main():
    """Point d'entrée principal du builder."""
    if not BLENDER_AVAILABLE:
        print("[BUILDER] ERREUR: Blender non disponible")
        sys.exit(1)
    
    print_header()
    
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    parser = argparse.ArgumentParser(description='Environment Builder - Blender Script')
    parser.add_argument('--production-plan', required=True,
                        help='Chemin vers PRODUCTION_PLAN.JSON')
    parser.add_argument('--hdri-mapping', required=True,
                        help='JSON mapping mood → HDRi path')
    parser.add_argument('--assets-mapping', required=True,
                        help='JSON mapping asset_id → path')
    parser.add_argument('--output-dir', required=True,
                        help='Dossier output')
    parser.add_argument('--scene-filter', default='[]',
                        help='JSON liste des scene_ids à traiter')
    
    args = parser.parse_args(argv)
    
    plan_path = Path(args.production_plan)
    if not plan_path.exists():
        print(f"[BUILDER:ERROR] Plan introuvable: {plan_path}")
        sys.exit(1)
    
    with open(plan_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)
    
    hdri_mapping = json.loads(args.hdri_mapping)
    assets_mapping = json.loads(args.assets_mapping)
    scene_filter = json.loads(args.scene_filter)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[BUILDER] Plan chargé: {len(plan.get('scenes', []))} scènes")
    print(f"[BUILDER] HDRi mapping: {len(hdri_mapping)} moods")
    print(f"[BUILDER] Assets mapping: {len(assets_mapping)} assets")
    print(f"[BUILDER] Scene filter: {scene_filter or 'toutes'}")
    print(f"[BUILDER] Output dir: {output_dir}")
    
    results = []
    
    for scene in plan.get("scenes", []):
        scene_id = scene.get("scene_id")
        
        if scene_filter and scene_id not in scene_filter:
            print(f"[BUILDER] Scène {scene_id} ignorée (filtre)")
            continue
        
        if "environment" not in scene:
            print(f"[BUILDER:WARN] Scène {scene_id} sans environnement, skip")
            continue
        
        try:
            result = process_scene(scene, hdri_mapping, assets_mapping, output_dir)
            results.append(result)
        except Exception as e:
            print(f"[BUILDER:ERROR] Échec scène {scene_id}: {e}")
            results.append({
                "scene_id": scene_id,
                "status": "FAILED",
                "error": str(e)
            })
    
    print("\n" + "=" * 60)
    print("   ENVIRONMENT BUILDER — COMPLETE")
    print(f"   {len(results)} scènes traitées")
    print("=" * 60 + "\n")
    
    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    if success_count < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
