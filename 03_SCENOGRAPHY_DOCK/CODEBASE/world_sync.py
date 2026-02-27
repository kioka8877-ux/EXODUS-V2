#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       WORLD SYNC — HDRi + Exposition Vidéo Source — Script Blender          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Remplace hdri_manager.py V1. Nouveau paradigme : exposure_strength         ║
║  alignée sur la vidéo source au lieu d'un strength fixe par mood.           ║
║  Les 3 node types requis par scene_schema sont TOUJOURS présents.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import math
from pathlib import Path
from typing import Optional, Tuple


MOOD_SETTINGS = {
    "neon": {
        "strength": 1.2,
        "rotation_z": 0.0,
        "tint": (0.9, 0.8, 1.0),
        "fallback_color": (0.05, 0.02, 0.1),
    },
    "dramatic": {
        "strength": 1.5,
        "rotation_z": 45.0,
        "tint": (1.0, 0.85, 0.7),
        "fallback_color": (0.15, 0.08, 0.05),
    },
    "natural": {
        "strength": 1.0,
        "rotation_z": 0.0,
        "tint": (1.0, 1.0, 1.0),
        "fallback_color": (0.4, 0.5, 0.6),
    },
    "studio": {
        "strength": 0.8,
        "rotation_z": 0.0,
        "tint": (1.0, 1.0, 1.0),
        "fallback_color": (0.3, 0.3, 0.3),
    },
}


def _clamp_strength(value: float) -> float:
    """Clampe la strength dans [0.1, 3.0] (scene_schema WORLD_SETTINGS)."""
    return max(0.1, min(3.0, value))


def setup_world_sync(
    hdri_path: Optional[str] = None,
    mood: str = "natural",
    exposure_strength: float = 1.0,
) -> None:
    """
    Configure le World shader avec HDRi + exposition alignée.

    Pipeline :
    1. Créer/récupérer le World
    2. use_nodes = True
    3. Si hdri_path existe :
       - TexCoord → Mapping (rotation Z mood) → TexEnvironment
         → MixRGB (tint) → Background → Output
       - Strength = exposure_strength clampé dans [0.1, 3.0]
    4. Si pas de HDRi :
       - Background avec fallback_color du mood → Output
       - Node TexEnvironment créé mais déconnecté (scene_schema compliance)
    5. Les 3 node types requis par scene_schema DOIVENT être présents :
       - ShaderNodeTexEnvironment
       - ShaderNodeBackground
       - ShaderNodeOutputWorld

    Contraintes scene_schema.py WORLD_SETTINGS :
    - use_nodes: True
    - required_node_types: [ShaderNodeTexEnvironment, ShaderNodeBackground,
      ShaderNodeOutputWorld]
    - strength dans [0.1, 3.0]

    Args:
        hdri_path: Chemin vers le fichier HDRi (.hdr, .exr). None = fallback.
        mood: Type de mood pour ajuster tint/rotation/fallback_color.
        exposure_strength: Strength d'exposition alignée sur la vidéo source.
    """
    settings = MOOD_SETTINGS.get(mood, MOOD_SETTINGS["natural"])
    strength = _clamp_strength(exposure_strength)

    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World_EXODUS")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputWorld")
    output.location = (600, 0)

    background = nodes.new(type="ShaderNodeBackground")
    background.location = (300, 0)
    background.inputs["Strength"].default_value = strength

    env_tex = nodes.new(type="ShaderNodeTexEnvironment")
    env_tex.location = (-200, 0)

    hdri_loaded = False
    if hdri_path:
        hdri_file = Path(hdri_path)
        if hdri_file.exists():
            env_tex.image = bpy.data.images.load(str(hdri_file))
            hdri_loaded = True
            print(f"[WORLD] HDRi chargé : {hdri_file.name}")
        else:
            print(f"[WORLD] HDRi introuvable : {hdri_path} — fallback activé")

    if hdri_loaded:
        mix_rgb = nodes.new(type="ShaderNodeMixRGB")
        mix_rgb.location = (100, 0)
        mix_rgb.blend_type = "MULTIPLY"
        mix_rgb.inputs["Fac"].default_value = 0.3
        mix_rgb.inputs["Color2"].default_value = (*settings["tint"], 1.0)

        mapping = nodes.new(type="ShaderNodeMapping")
        mapping.location = (-400, 0)
        mapping.inputs["Rotation"].default_value[2] = math.radians(settings["rotation_z"])

        tex_coord = nodes.new(type="ShaderNodeTexCoord")
        tex_coord.location = (-600, 0)

        links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
        links.new(env_tex.outputs["Color"], mix_rgb.inputs["Color1"])
        links.new(mix_rgb.outputs["Color"], background.inputs["Color"])
        links.new(background.outputs["Background"], output.inputs["Surface"])

        print(f"[WORLD] Pipeline HDRi complet — mood={mood}, strength={strength}, "
              f"rotation_z={settings['rotation_z']}")
    else:
        background.inputs["Color"].default_value = (*settings["fallback_color"], 1.0)
        links.new(background.outputs["Background"], output.inputs["Surface"])

        print(f"[WORLD] Fallback activé — couleur={settings['fallback_color']}, "
              f"strength={strength}")

    print(f"[WORLD] World Sync configuré — use_nodes=True, 3 node types présents")


def setup_render_settings(engine: str = "CYCLES", samples: int = 128) -> None:
    """
    Configure les paramètres de rendu (repris de hdri_manager.py V1).

    Args:
        engine: CYCLES ou EEVEE.
        samples: Nombre de samples pour le rendu.
    """
    scene = bpy.context.scene

    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"

        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "CUDA"
            scene.cycles.device = "GPU"
            print("[WORLD] Rendu GPU CUDA activé")
        except Exception:
            scene.cycles.device = "CPU"
            print("[WORLD] Rendu CPU (GPU non disponible)")

    elif engine == "EEVEE":
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = samples
        scene.eevee.use_gtao = True
        scene.eevee.use_bloom = True
        scene.eevee.use_ssr = True
        print("[WORLD] Rendu EEVEE configuré")

    print(f"[WORLD] Moteur de rendu : {engine}, samples={samples}")
