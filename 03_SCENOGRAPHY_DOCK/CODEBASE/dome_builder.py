#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       DOME BUILDER — INFINITY DOME (Couche A) — Script Blender Headless     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Construit une demi-sphère UV à normales inversées pour le background       ║
║  vidéo source. Matériau Emission (IMAGE_TEXTURE) pour auto-illumination.    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import bmesh
import math
import sys
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from blender_layer_base import BlenderLayerBuilder

_ensure_collection = BlenderLayerBuilder._ensure_collection


def build_infinity_dome(
    collection_name: str = "ENV_DOME",
    radius: float = 100.0,
) -> bpy.types.Object:
    """
    Construit une demi-sphère UV avec normales inversées.

    Étapes :
    1. Créer collection ENV_DOME si absente
    2. Créer UV Sphere (segments=64, rings=32)
    3. Supprimer la moitié inférieure (z < 0) en Edit Mode
    4. Inverser les normales pour vue intérieure
    5. Nommer l'objet "infinity_dome"
    6. Appliquer un matériau placeholder
    7. Linker dans la collection ENV_DOME

    Contraintes scene_schema.py :
    - radius dans [50.0, 200.0]
    - normals: INWARD
    - material_type: IMAGE_TEXTURE

    Args:
        collection_name: Nom de la collection cible.
        radius: Rayon de la demi-sphère (clampé dans [50.0, 200.0]).

    Returns:
        L'objet dome créé.
    """
    radius = max(50.0, min(200.0, radius))

    coll = _ensure_collection(collection_name)
    print(f"[DOME] Collection '{collection_name}' prête")

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64,
        ring_count=32,
        radius=radius,
        location=(0, 0, 0),
    )
    dome_obj = bpy.context.active_object
    dome_obj.name = "infinity_dome"

    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(dome_obj.data)
    bm.verts.ensure_lookup_table()

    verts_to_delete = [v for v in bm.verts if v.co.z < -0.001]
    bmesh.ops.delete(bm, geom=verts_to_delete, context="VERTS")

    bmesh.update_edit_mesh(dome_obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    dome_obj.data.flip_normals()

    apply_dome_material(dome_obj)

    for existing_coll in dome_obj.users_collection:
        existing_coll.objects.unlink(dome_obj)
    coll.objects.link(dome_obj)

    print(f"[DOME] infinity_dome construit — radius={radius}, segments=64, rings=32, normals=INWARD")
    return dome_obj


def apply_dome_material(
    dome_obj: bpy.types.Object,
    video_frame_path: Optional[str] = None,
    fallback_color: tuple = (0.05, 0.05, 0.1),
) -> None:
    """
    Applique la texture vidéo source sur le dome.

    Si video_frame_path est fourni : charge l'image comme texture.
    Sinon : crée un matériau placeholder avec fallback_color.
    La couleur par défaut (0.05, 0.05, 0.1) est sombre mais sera remplacée
    automatiquement par layer_assembler via ENVIRONMENT_TO_SCENE_PROFILE.

    Node setup :
    - ShaderNodeTexCoord (Generated) → ShaderNodeMapping → ShaderNodeTexImage
      → ShaderNodeEmission → Output
    - Emission au lieu de Principled BSDF (le dome émet sa propre lumière)
    - Strength de l'Emission = 1.0

    Args:
        dome_obj: L'objet dome Blender.
        video_frame_path: Chemin optionnel vers une frame vidéo.
        fallback_color: Tuple RGB (0-1) utilisé si aucune frame vidéo fournie.
    """
    mat_name = "MAT_InfinityDome"
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (600, 0)

    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (300, 0)
    emission.inputs["Strength"].default_value = 1.0

    tex_image = nodes.new(type="ShaderNodeTexImage")
    tex_image.location = (-100, 0)

    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-350, 0)

    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-600, 0)

    if video_frame_path and Path(video_frame_path).exists():
        img = bpy.data.images.load(video_frame_path)
        tex_image.image = img
        print(f"[DOME] Texture chargée : {video_frame_path}")
    else:
        r, g, b = fallback_color
        img = bpy.data.images.new("dome_placeholder", width=4, height=4)
        pixels = [r, g, b, 1.0] * (4 * 4)
        img.pixels = pixels
        tex_image.image = img
        print(f"[DOME] Texture placeholder appliquée ({r:.2f}, {g:.2f}, {b:.2f})")

    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex_image.inputs["Vector"])
    links.new(tex_image.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    if dome_obj.data.materials:
        dome_obj.data.materials[0] = mat
    else:
        dome_obj.data.materials.append(mat)

    print(f"[DOME] Matériau '{mat_name}' appliqué — type=IMAGE_TEXTURE, shader=Emission")
