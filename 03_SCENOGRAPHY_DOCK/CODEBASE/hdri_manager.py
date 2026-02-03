#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    HDRI MANAGER — EXODUS SCENOGRAPHY                         ║
║                  Gestion Éclairage HDRi World Shader                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour configurer l'éclairage HDRi dans Blender.
Supporte le mapping mood → fichier HDRi avec fallback.
"""

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from pathlib import Path


MOOD_SETTINGS = {
    "neon": {
        "strength": 1.2,
        "rotation_z": 0.0,
        "tint": (0.9, 0.8, 1.0),
        "fallback_color": (0.05, 0.02, 0.1)
    },
    "dramatic": {
        "strength": 1.5,
        "rotation_z": 45.0,
        "tint": (1.0, 0.85, 0.7),
        "fallback_color": (0.15, 0.08, 0.05)
    },
    "natural": {
        "strength": 1.0,
        "rotation_z": 0.0,
        "tint": (1.0, 1.0, 1.0),
        "fallback_color": (0.4, 0.5, 0.6)
    },
    "studio": {
        "strength": 0.8,
        "rotation_z": 0.0,
        "tint": (1.0, 1.0, 1.0),
        "fallback_color": (0.3, 0.3, 0.3)
    }
}


LIGHTING_CONFIGS = {
    "three_point": {
        "lights": [
            {"type": "AREA", "name": "Key", "location": (4, -3, 5), "rotation": (0.8, 0, 0.5), "energy": 800, "size": 2},
            {"type": "AREA", "name": "Fill", "location": (-3, -2, 4), "rotation": (0.7, 0, -0.3), "energy": 300, "size": 3},
            {"type": "AREA", "name": "Back", "location": (0, 4, 5), "rotation": (0.5, 3.14, 0), "energy": 500, "size": 1.5}
        ]
    },
    "interior": {
        "lights": [
            {"type": "AREA", "name": "Ceiling_1", "location": (0, 0, 2.8), "rotation": (3.14, 0, 0), "energy": 400, "size": 2},
            {"type": "POINT", "name": "Accent_1", "location": (3, 3, 2.5), "rotation": (0, 0, 0), "energy": 200, "size": 0.5}
        ]
    },
    "overhead_multi": {
        "lights": [
            {"type": "SUN", "name": "Sun", "location": (0, 0, 10), "rotation": (0.8, 0, 0.3), "energy": 5, "size": 0.02},
            {"type": "POINT", "name": "Street_1", "location": (-10, 0, 4), "rotation": (0, 0, 0), "energy": 800, "size": 0.5},
            {"type": "POINT", "name": "Street_2", "location": (10, 0, 4), "rotation": (0, 0, 0), "energy": 800, "size": 0.5}
        ]
    },
    "sun": {
        "lights": [
            {"type": "SUN", "name": "Sun_Main", "location": (0, 0, 100), "rotation": (0.9, 0, 0.5), "energy": 8, "size": 0.02}
        ]
    }
}


def setup_hdri_lighting(hdri_path: str, mood: str = "natural"):
    """
    Configure l'éclairage HDRi pour le World shader.
    
    Args:
        hdri_path: Chemin vers le fichier HDRi (.hdr, .exr)
        mood: Type de mood pour ajuster les paramètres
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("HDRI Manager requires Blender")
    
    path = Path(hdri_path)
    if not path.exists():
        print(f"[HDRI:WARN] Fichier introuvable: {hdri_path}")
        setup_fallback_lighting(mood)
        return
    
    settings = MOOD_SETTINGS.get(mood, MOOD_SETTINGS["natural"])
    
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World_HDRI")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputWorld')
    output.location = (600, 0)
    
    background = nodes.new(type='ShaderNodeBackground')
    background.location = (300, 0)
    background.inputs['Strength'].default_value = settings["strength"]
    
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.location = (100, 0)
    mix_rgb.blend_type = 'MULTIPLY'
    mix_rgb.inputs['Fac'].default_value = 0.3
    mix_rgb.inputs['Color2'].default_value = (*settings["tint"], 1.0)
    
    env_tex = nodes.new(type='ShaderNodeTexEnvironment')
    env_tex.location = (-200, 0)
    env_tex.image = bpy.data.images.load(hdri_path)
    
    mapping = nodes.new(type='ShaderNodeMapping')
    mapping.location = (-400, 0)
    mapping.inputs['Rotation'].default_value[2] = settings["rotation_z"] * (3.14159 / 180)
    
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
    links.new(env_tex.outputs['Color'], mix_rgb.inputs['Color1'])
    links.new(mix_rgb.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])
    
    print(f"[HDRI] World HDRi configuré: {path.name}")
    print(f"[HDRI] Mood: {mood}, Strength: {settings['strength']}")


def setup_fallback_lighting(mood: str = "natural", lighting_style: str = "three_point"):
    """
    Configure un éclairage de fallback quand HDRi non disponible.
    
    Args:
        mood: Type de mood pour la couleur de fond
        lighting_style: Style d'éclairage (three_point, interior, etc.)
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("HDRI Manager requires Blender")
    
    settings = MOOD_SETTINGS.get(mood, MOOD_SETTINGS["natural"])
    
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World_Fallback")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputWorld')
    output.location = (300, 0)
    
    background = nodes.new(type='ShaderNodeBackground')
    background.location = (0, 0)
    background.inputs['Color'].default_value = (*settings["fallback_color"], 1.0)
    background.inputs['Strength'].default_value = 0.5
    
    links.new(background.outputs['Background'], output.inputs['Surface'])
    
    print(f"[HDRI] Fallback World: couleur {settings['fallback_color']}")
    
    create_scene_lights(lighting_style)


def create_scene_lights(style: str = "three_point"):
    """
    Crée les lumières de scène selon un style prédéfini.
    
    Args:
        style: Style d'éclairage (three_point, interior, overhead_multi, sun)
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("HDRI Manager requires Blender")
    
    config = LIGHTING_CONFIGS.get(style, LIGHTING_CONFIGS["three_point"])
    
    for existing in bpy.data.objects:
        if existing.type == 'LIGHT':
            bpy.data.objects.remove(existing, do_unlink=True)
    
    for light_spec in config["lights"]:
        light_type = light_spec["type"]
        name = light_spec["name"]
        
        light_data = bpy.data.lights.new(name=name, type=light_type)
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        bpy.context.scene.collection.objects.link(light_obj)
        
        light_obj.location = light_spec["location"]
        light_obj.rotation_euler = light_spec["rotation"]
        
        light_data.energy = light_spec["energy"]
        
        if light_type == 'AREA':
            light_data.size = light_spec.get("size", 1.0)
        elif light_type == 'SUN':
            light_data.angle = light_spec.get("size", 0.02)
        elif light_type == 'POINT':
            light_data.shadow_soft_size = light_spec.get("size", 0.5)
        
        print(f"[HDRI] Lumière créée: {name} ({light_type})")
    
    print(f"[HDRI] Style d'éclairage: {style} ({len(config['lights'])} lumières)")


def setup_render_settings(render_engine: str = "CYCLES", samples: int = 128):
    """
    Configure les paramètres de rendu optimaux pour l'éclairage.
    
    Args:
        render_engine: CYCLES ou EEVEE
        samples: Nombre de samples pour Cycles
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("HDRI Manager requires Blender")
    
    scene = bpy.context.scene
    
    if render_engine == "CYCLES":
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        
        try:
            bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
            scene.cycles.device = 'GPU'
            print("[HDRI] Rendu GPU CUDA activé")
        except:
            scene.cycles.device = 'CPU'
            print("[HDRI] Rendu CPU (GPU non disponible)")
    
    elif render_engine == "EEVEE":
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.eevee.taa_render_samples = samples
        scene.eevee.use_gtao = True
        scene.eevee.use_bloom = True
        scene.eevee.use_ssr = True
        print("[HDRI] Rendu EEVEE configuré")
    
    print(f"[HDRI] Moteur de rendu: {render_engine}, samples: {samples}")


def add_volumetric_lighting(density: float = 0.01, anisotropy: float = 0.3):
    """
    Ajoute un effet volumétrique pour des rayons de lumière.
    
    Args:
        density: Densité du volume
        anisotropy: Direction de diffusion (0 = uniforme, 1 = vers l'avant)
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("HDRI Manager requires Blender")
    
    world = bpy.context.scene.world
    if not world or not world.use_nodes:
        print("[HDRI:WARN] World non configuré, volumétrie ignorée")
        return
    
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    output = None
    for node in nodes:
        if node.type == 'OUTPUT_WORLD':
            output = node
            break
    
    if not output:
        return
    
    volume_scatter = nodes.new(type='ShaderNodeVolumeScatter')
    volume_scatter.location = (300, -200)
    volume_scatter.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    volume_scatter.inputs['Density'].default_value = density
    volume_scatter.inputs['Anisotropy'].default_value = anisotropy
    
    links.new(volume_scatter.outputs['Volume'], output.inputs['Volume'])
    
    print(f"[HDRI] Volumétrie ajoutée: densité={density}, anisotropy={anisotropy}")


def create_gradient_background(color_top: tuple, color_bottom: tuple, strength: float = 1.0):
    """
    Crée un fond dégradé simple.
    
    Args:
        color_top: Couleur du haut (R, G, B)
        color_bottom: Couleur du bas (R, G, B)
        strength: Intensité
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("HDRI Manager requires Blender")
    
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World_Gradient")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputWorld')
    output.location = (600, 0)
    
    background = nodes.new(type='ShaderNodeBackground')
    background.location = (400, 0)
    background.inputs['Strength'].default_value = strength
    
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (200, 0)
    color_ramp.color_ramp.elements[0].color = (*color_bottom, 1.0)
    color_ramp.color_ramp.elements[1].color = (*color_top, 1.0)
    
    separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
    separate_xyz.location = (0, 0)
    
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-200, 0)
    
    links.new(tex_coord.outputs['Generated'], separate_xyz.inputs['Vector'])
    links.new(separate_xyz.outputs['Z'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])
    
    print(f"[HDRI] Fond dégradé créé: {color_bottom} → {color_top}")


if __name__ == "__main__":
    print("[HDRI] Module HDRI Manager chargé")
    print(f"[HDRI] Moods disponibles: {list(MOOD_SETTINGS.keys())}")
    print(f"[HDRI] Styles d'éclairage: {list(LIGHTING_CONFIGS.keys())}")
