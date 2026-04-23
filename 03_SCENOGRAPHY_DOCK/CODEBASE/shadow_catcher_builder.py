#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║    SHADOW CATCHER BUILDER — Plan Invisible Capteur d'Ombres                 ║
║                       Script Blender Headless                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Construit un plan au sol avec les flags shadow catcher activés.            ║
║  Le plan est invisible au rendu mais capture les ombres portées.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import sys
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from blender_layer_base import BlenderLayerBuilder

_ensure_collection = BlenderLayerBuilder._ensure_collection


def build_shadow_catcher(
    collection_name: str = "ENV_SHADOW",
    size: float = 50.0,
) -> bpy.types.Object:
    """
    Construit un plan invisible capteur d'ombres.

    Étapes :
    1. Créer collection ENV_SHADOW si absente
    2. Créer un Plane (taille = size x size)
    3. Position : (0, 0, 0) — au sol sous l'avatar
    4. Nommer "shadow_catcher"
    5. Configurer les flags de visibilité (Blender 4.0+)
    6. Appliquer un matériau SHADOW_ONLY (Principled BSDF noir, Alpha=0)
    7. Linker dans la collection ENV_SHADOW

    IMPORTANT : le Shadow Catcher est un plan SÉPARÉ du displacement_mesh.
    C'est une erreur de l'activer sur le terrain.

    Contraintes scene_schema.py :
    - is_shadow_catcher: True
    - visible_camera: False
    - visible_diffuse: False

    Args:
        collection_name: Nom de la collection cible.
        size: Taille du plan (côté).

    Returns:
        L'objet shadow_catcher créé.
    """
    coll = _ensure_collection(collection_name)
    print(f"[SHADOW] Collection '{collection_name}' prête")

    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    sc_obj = bpy.context.active_object
    sc_obj.name = "shadow_catcher"

    sc_obj.is_shadow_catcher = True
    sc_obj.visible_camera = False
    sc_obj.visible_diffuse = False
    sc_obj.visible_glossy = False
    sc_obj.visible_transmission = False
    sc_obj.visible_volume_scatter = False

    _apply_shadow_material(sc_obj)

    for existing_coll in sc_obj.users_collection:
        existing_coll.objects.unlink(sc_obj)
    coll.objects.link(sc_obj)

    print(f"[SHADOW] shadow_catcher construit — size={size}, is_shadow_catcher=True")
    print("[SHADOW] Flags visibilité : camera=False, diffuse=False, glossy=False, "
          "transmission=False, volume_scatter=False")
    return sc_obj


def _apply_shadow_material(sc_obj: bpy.types.Object) -> None:
    """
    Applique un matériau SHADOW_ONLY sur l'objet shadow catcher.

    Principled BSDF tout noir avec Alpha = 0.
    Blend mode Clip pour transparence totale.

    Args:
        sc_obj: L'objet shadow catcher.
    """
    mat_name = "MAT_ShadowCatcher"
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)

    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    principled.inputs["Roughness"].default_value = 1.0
    principled.inputs["Metallic"].default_value = 0.0
    principled.inputs["Alpha"].default_value = 0.0

    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    mat.blend_method = "CLIP"
    mat.shadow_method = "CLIP"

    if sc_obj.data.materials:
        sc_obj.data.materials[0] = mat
    else:
        sc_obj.data.materials.append(mat)

    print(f"[SHADOW] Matériau '{mat_name}' appliqué — type=SHADOW_ONLY, Alpha=0")
