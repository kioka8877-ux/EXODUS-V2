#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PROPS PLACER — EXODUS SCENOGRAPHY                         ║
║               Placement Automatique Props Environnement                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour placer les props d'environnement (non-acteur) dans Blender.
Gère le positionnement automatique et les collisions basiques.
"""

try:
    import bpy
    import mathutils
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Vector = None

from pathlib import Path
import random


PROPS_POSITIONS = {
    "urban_street": {
        "streetlight": [
            {"pos": (-8, -5, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (8, -5, 0), "rot": (0, 0, 3.14), "scale": 1.0},
            {"pos": (-8, 15, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (8, 15, 0), "rot": (0, 0, 3.14), "scale": 1.0},
        ],
        "bench": [
            {"pos": (-6, 0, 0), "rot": (0, 0, 1.57), "scale": 1.0},
            {"pos": (6, 10, 0), "rot": (0, 0, -1.57), "scale": 1.0},
        ],
        "trash_can": [
            {"pos": (-7, -3, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (7, 12, 0), "rot": (0, 0, 0.5), "scale": 1.0},
        ],
        "car": [
            {"pos": (3, 5, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (-3, -10, 0), "rot": (0, 0, 3.14), "scale": 1.0},
        ]
    },
    "indoor": {
        "table": [
            {"pos": (0, 0, 0), "rot": (0, 0, 0), "scale": 1.0},
        ],
        "chair": [
            {"pos": (0, -1.5, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (1.5, 0, 0), "rot": (0, 0, 1.57), "scale": 1.0},
            {"pos": (-1.5, 0, 0), "rot": (0, 0, -1.57), "scale": 1.0},
            {"pos": (0, 1.5, 0), "rot": (0, 0, 3.14), "scale": 1.0},
        ],
        "lamp": [
            {"pos": (3, 3, 0), "rot": (0, 0, 0), "scale": 1.0},
        ],
        "plant": [
            {"pos": (-4, 4, 0), "rot": (0, 0, 0), "scale": 1.0},
        ]
    },
    "outdoor": {
        "tree": [
            {"pos": (-15, 10, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (20, -15, 0), "rot": (0, 0, 0.3), "scale": 1.2},
            {"pos": (-25, -20, 0), "rot": (0, 0, 0.7), "scale": 0.9},
            {"pos": (10, 25, 0), "rot": (0, 0, 1.2), "scale": 1.1},
        ],
        "rock": [
            {"pos": (5, 5, 0), "rot": (0, 0, 0.5), "scale": 1.0},
            {"pos": (-8, -8, 0), "rot": (0.1, 0.1, 1.2), "scale": 0.8},
            {"pos": (12, -3, 0), "rot": (0, 0.05, 2.1), "scale": 1.3},
        ],
        "bush": [
            {"pos": (-10, 5, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (8, 12, 0), "rot": (0, 0, 0), "scale": 1.1},
        ]
    },
    "studio": {
        "camera_stand": [
            {"pos": (0, -6, 0), "rot": (0, 0, 0), "scale": 1.0},
        ],
        "light_stand": [
            {"pos": (4, -3, 0), "rot": (0, 0, 0), "scale": 1.0},
            {"pos": (-4, -3, 0), "rot": (0, 0, 0), "scale": 1.0},
        ],
        "reflector": [
            {"pos": (-5, 0, 0), "rot": (0, 0, 0.5), "scale": 1.0},
        ]
    }
}


DEFAULT_PLACEHOLDER_SIZE = {
    "streetlight": (0.3, 0.3, 4.0),
    "bench": (1.5, 0.5, 0.5),
    "trash_can": (0.4, 0.4, 0.8),
    "car": (2.0, 4.5, 1.5),
    "table": (1.2, 1.2, 0.75),
    "chair": (0.5, 0.5, 1.0),
    "lamp": (0.3, 0.3, 1.5),
    "plant": (0.4, 0.4, 1.0),
    "tree": (2.0, 2.0, 5.0),
    "rock": (1.0, 1.0, 0.6),
    "bush": (1.0, 1.0, 0.8),
    "camera_stand": (0.5, 0.5, 1.5),
    "light_stand": (0.3, 0.3, 2.0),
    "reflector": (1.0, 0.1, 1.5),
    "default": (1.0, 1.0, 1.0)
}


def place_props(
    props_list: list,
    assets_mapping: dict,
    template: dict,
    collection: 'bpy.types.Collection'
) -> int:
    """
    Place les props dans l'environnement.
    
    Args:
        props_list: Liste des props à placer (ex: ["car", "streetlight", "bench"])
        assets_mapping: Mapping prop_id → chemin fichier
        template: Template de l'environnement
        collection: Collection Blender cible
    
    Returns:
        Nombre de props placés
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Props Placer requires Blender")
    
    if not props_list:
        print("[PROPS] Aucun prop à placer")
        return 0
    
    env_type = "studio"
    ground_size = template.get("ground_size", (50, 50))
    
    for env_name, env_positions in PROPS_POSITIONS.items():
        if template.get("ground_size") == PROPS_POSITIONS.get(env_name, {}).get("ground_size", (0, 0)):
            env_type = env_name
            break
    
    for env_name, env_template in [
        ("urban_street", {"ground_size": (100, 100)}),
        ("indoor", {"ground_size": (20, 20)}),
        ("outdoor", {"ground_size": (200, 200)}),
        ("studio", {"ground_size": (50, 50)})
    ]:
        if ground_size == env_template["ground_size"]:
            env_type = env_name
            break
    
    print(f"[PROPS] Placement pour environnement type: {env_type}")
    print(f"[PROPS] Props demandés: {props_list}")
    
    placed_count = 0
    used_positions = []
    
    for prop_name in props_list:
        prop_name_lower = prop_name.lower().replace("_", "")
        
        asset_key = f"prop:{prop_name}"
        asset_path = assets_mapping.get(asset_key)
        
        positions = PROPS_POSITIONS.get(env_type, {}).get(prop_name.lower(), [])
        
        if not positions:
            positions = generate_random_positions(prop_name, ground_size, used_positions)
        
        for i, pos_data in enumerate(positions):
            obj = None
            
            if asset_path and Path(asset_path).exists():
                obj = import_prop_asset(asset_path, prop_name, i, collection)
            
            if not obj:
                obj = create_placeholder(prop_name, i, collection)
            
            if obj:
                position = Vector(pos_data["pos"])
                obj.location = position
                obj.rotation_euler = pos_data["rot"]
                obj.scale = (pos_data["scale"],) * 3
                
                used_positions.append(position)
                placed_count += 1
                
                print(f"[PROPS] Placé: {prop_name} @ {pos_data['pos']}")
            
            if i == 0:
                break
    
    print(f"[PROPS] Total props placés: {placed_count}/{len(props_list)}")
    return placed_count


def import_prop_asset(
    asset_path: str,
    prop_name: str,
    index: int,
    collection: 'bpy.types.Collection'
) -> 'bpy.types.Object':
    """
    Importe un asset prop depuis un fichier.
    
    Returns:
        L'objet racine importé ou None
    """
    if not BLENDER_AVAILABLE:
        return None
    
    path = Path(asset_path)
    suffix = path.suffix.lower()
    
    try:
        if suffix == ".blend":
            with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
            
            root_obj = None
            for obj in data_to.objects:
                if obj is not None:
                    collection.objects.link(obj)
                    if root_obj is None:
                        root_obj = obj
            
            if root_obj:
                root_obj.name = f"{prop_name}_{index}"
            return root_obj
        
        elif suffix in [".glb", ".gltf"]:
            bpy.ops.import_scene.gltf(filepath=str(path))
            imported = bpy.context.selected_objects
            
            root_obj = None
            for obj in imported:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                collection.objects.link(obj)
                if root_obj is None:
                    root_obj = obj
            
            if root_obj:
                root_obj.name = f"{prop_name}_{index}"
            return root_obj
        
        elif suffix == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
            imported = bpy.context.selected_objects
            
            root_obj = None
            for obj in imported:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                collection.objects.link(obj)
                if root_obj is None:
                    root_obj = obj
            
            if root_obj:
                root_obj.name = f"{prop_name}_{index}"
            return root_obj
        
        elif suffix == ".obj":
            bpy.ops.wm.obj_import(filepath=str(path))
            imported = bpy.context.selected_objects
            
            root_obj = None
            for obj in imported:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                collection.objects.link(obj)
                if root_obj is None:
                    root_obj = obj
            
            if root_obj:
                root_obj.name = f"{prop_name}_{index}"
            return root_obj
    
    except Exception as e:
        print(f"[PROPS:ERROR] Erreur import {asset_path}: {e}")
    
    return None


def create_placeholder(
    prop_name: str,
    index: int,
    collection: 'bpy.types.Collection'
) -> 'bpy.types.Object':
    """
    Crée un placeholder cube pour un prop manquant.
    
    Returns:
        L'objet placeholder créé
    """
    if not BLENDER_AVAILABLE:
        return None
    
    size = DEFAULT_PLACEHOLDER_SIZE.get(prop_name.lower(), DEFAULT_PLACEHOLDER_SIZE["default"])
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, size[2]/2))
    obj = bpy.context.active_object
    obj.name = f"Placeholder_{prop_name}_{index}"
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    collection.objects.link(obj)
    
    mat = bpy.data.materials.new(name=f"Placeholder_{prop_name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.8, 1.0)
        bsdf.inputs['Alpha'].default_value = 0.5
    mat.blend_method = 'BLEND'
    obj.data.materials.append(mat)
    
    print(f"[PROPS:WARN] Placeholder créé pour: {prop_name}")
    return obj


def generate_random_positions(
    prop_name: str,
    ground_size: tuple,
    used_positions: list,
    count: int = 1
) -> list:
    """
    Génère des positions aléatoires pour un prop.
    
    Args:
        prop_name: Nom du prop
        ground_size: Taille du sol (x, y)
        used_positions: Positions déjà utilisées
        count: Nombre de positions à générer
    
    Returns:
        Liste de positions {pos, rot, scale}
    """
    positions = []
    max_x = ground_size[0] / 2 - 2
    max_y = ground_size[1] / 2 - 2
    min_distance = 3.0
    
    for _ in range(count):
        for attempt in range(20):
            x = random.uniform(-max_x, max_x)
            y = random.uniform(-max_y, max_y)
            pos = Vector((x, y, 0)) if Vector else (x, y, 0)
            
            too_close = False
            for used in used_positions:
                if Vector:
                    dist = (pos - used).length
                else:
                    dist = ((pos[0]-used[0])**2 + (pos[1]-used[1])**2)**0.5
                if dist < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                positions.append({
                    "pos": (x, y, 0),
                    "rot": (0, 0, random.uniform(0, 6.28)),
                    "scale": random.uniform(0.8, 1.2)
                })
                break
    
    if not positions:
        positions.append({
            "pos": (random.uniform(-5, 5), random.uniform(-5, 5), 0),
            "rot": (0, 0, 0),
            "scale": 1.0
        })
    
    return positions


def check_collision(
    position: 'Vector',
    used_positions: list,
    min_distance: float = 2.0
) -> bool:
    """
    Vérifie si une position entre en collision avec des positions existantes.
    
    Returns:
        True si collision détectée
    """
    if not Vector:
        return False
    
    for used in used_positions:
        if (position - used).length < min_distance:
            return True
    return False


def scatter_props(
    prop_name: str,
    count: int,
    area_bounds: tuple,
    assets_mapping: dict,
    collection: 'bpy.types.Collection',
    min_spacing: float = 3.0
) -> int:
    """
    Scatter multiple instances d'un prop dans une zone.
    
    Args:
        prop_name: Nom du prop
        count: Nombre d'instances
        area_bounds: (min_x, max_x, min_y, max_y)
        assets_mapping: Mapping assets
        collection: Collection cible
        min_spacing: Espacement minimum entre instances
    
    Returns:
        Nombre d'instances placées
    """
    if not BLENDER_AVAILABLE:
        return 0
    
    min_x, max_x, min_y, max_y = area_bounds
    placed = 0
    positions = []
    
    for i in range(count):
        for attempt in range(30):
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            pos = Vector((x, y, 0))
            
            if not check_collision(pos, positions, min_spacing):
                positions.append(pos)
                
                asset_key = f"prop:{prop_name}"
                asset_path = assets_mapping.get(asset_key)
                
                if asset_path and Path(asset_path).exists():
                    obj = import_prop_asset(asset_path, prop_name, i, collection)
                else:
                    obj = create_placeholder(prop_name, i, collection)
                
                if obj:
                    obj.location = pos
                    obj.rotation_euler = (0, 0, random.uniform(0, 6.28))
                    scale = random.uniform(0.8, 1.2)
                    obj.scale = (scale, scale, scale)
                    placed += 1
                break
    
    print(f"[PROPS:SCATTER] {prop_name}: {placed}/{count} instances placées")
    return placed


if __name__ == "__main__":
    print("[PROPS] Module Props Placer chargé")
    print(f"[PROPS] Environnements configurés: {list(PROPS_POSITIONS.keys())}")
