#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               COMPOSITOR PIPELINE — EXODUS ALCHEMIST LAB                     ║
║                   Blender Compositor Node Tree Automatique                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Script Blender headless pour créer et exécuter un node tree de compositing.
Pipeline: Image Input → Denoise → Color Grade → Effects → Output

Usage (appelé par EXO_05_ALCHEMIST.py):
    blender --background --python compositor_pipeline.py -- \\
        --config '{"scene_id": 1, "input_exr": "...", "post_config": {...}}'
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[COMPOSITOR] Running outside Blender - validation mode only")


def clear_compositor():
    """Supprime le node tree existant."""
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    return tree


def create_image_input_node(tree, exr_path: str, frame_start: int, frame_end: int) -> 'bpy.types.Node':
    """Crée le node d'entrée image pour la séquence EXR."""
    image_node = tree.nodes.new('CompositorNodeImage')
    image_node.location = (-800, 0)
    image_node.name = "EXR_Input"
    
    exr_dir = Path(exr_path).parent
    exr_pattern = Path(exr_path).stem
    
    if Path(exr_path).exists():
        try:
            img = bpy.data.images.load(exr_path)
            img.source = 'SEQUENCE'
            image_node.image = img
            image_node.frame_duration = frame_end - frame_start + 1
            image_node.frame_start = frame_start
            image_node.use_auto_refresh = True
        except Exception as e:
            print(f"[COMPOSITOR:WARN] Impossible de charger EXR: {e}")
    
    return image_node


def create_denoise_node(tree, use_optix: bool = True) -> 'bpy.types.Node':
    """Crée un node de denoising."""
    denoise = tree.nodes.new('CompositorNodeDenoise')
    denoise.location = (-500, 0)
    denoise.name = "Denoiser"
    
    if hasattr(denoise, 'use_hdr'):
        denoise.use_hdr = True
    
    return denoise


def create_color_grade_group(tree, config: dict, lut_path: str = "") -> 'bpy.types.Node':
    """
    Crée un groupe de nodes pour le color grading.
    Inclut: Exposure, Contrast, Saturation, LUT.
    """
    exposure_val = config.get("exposure", 0.0)
    contrast_val = config.get("contrast", 1.0)
    saturation_val = config.get("saturation", 1.0)
    
    exposure_node = tree.nodes.new('CompositorNodeExposure')
    exposure_node.location = (-200, 100)
    exposure_node.name = "Exposure"
    exposure_node.inputs['Exposure'].default_value = exposure_val
    
    contrast_node = tree.nodes.new('CompositorNodeBrightContrast')
    contrast_node.location = (0, 100)
    contrast_node.name = "Contrast"
    contrast_value = (contrast_val - 1.0) * 50
    contrast_node.inputs['Contrast'].default_value = contrast_value
    
    hue_sat = tree.nodes.new('CompositorNodeHueSat')
    hue_sat.location = (200, 100)
    hue_sat.name = "Saturation"
    hue_sat.inputs['Saturation'].default_value = saturation_val
    
    tree.links.new(exposure_node.outputs['Image'], contrast_node.inputs['Image'])
    tree.links.new(contrast_node.outputs['Image'], hue_sat.inputs['Image'])
    
    return exposure_node, hue_sat


def create_lut_node(tree, lut_path: str) -> 'bpy.types.Node':
    """Crée un node Color Balance ou applique une LUT via curves."""
    color_balance = tree.nodes.new('CompositorNodeColorBalance')
    color_balance.location = (400, 100)
    color_balance.name = "LUT_ColorBalance"
    color_balance.correction_method = 'LIFT_GAMMA_GAIN'
    
    if lut_path and Path(lut_path).exists():
        lut_data = parse_cube_lut(lut_path)
        if lut_data:
            apply_lut_to_color_balance(color_balance, lut_data)
    
    return color_balance


def parse_cube_lut(lut_path: str) -> dict:
    """Parse un fichier .cube LUT et extrait les paramètres."""
    lut_data = {
        "title": "",
        "size": 0,
        "domain_min": [0.0, 0.0, 0.0],
        "domain_max": [1.0, 1.0, 1.0],
        "data": [],
        "lift": [1.0, 1.0, 1.0],
        "gamma": [1.0, 1.0, 1.0],
        "gain": [1.0, 1.0, 1.0]
    }
    
    try:
        with open(lut_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('TITLE'):
                lut_data["title"] = line.split('"')[1] if '"' in line else line.split()[1]
            elif line.startswith('LUT_3D_SIZE'):
                lut_data["size"] = int(line.split()[1])
            elif line.startswith('DOMAIN_MIN'):
                lut_data["domain_min"] = [float(x) for x in line.split()[1:4]]
            elif line.startswith('DOMAIN_MAX'):
                lut_data["domain_max"] = [float(x) for x in line.split()[1:4]]
            elif line[0].isdigit() or line[0] == '-':
                values = [float(x) for x in line.split()[:3]]
                if len(values) == 3:
                    lut_data["data"].append(values)
        
        if lut_data["data"]:
            analyze_lut_characteristics(lut_data)
        
    except Exception as e:
        print(f"[COMPOSITOR:WARN] Erreur parsing LUT: {e}")
        return None
    
    return lut_data


def analyze_lut_characteristics(lut_data: dict):
    """Analyse la LUT pour extraire lift/gamma/gain approximatifs."""
    data = lut_data["data"]
    if not data:
        return
    
    size = lut_data["size"] or int(round(len(data) ** (1/3)))
    if size < 2:
        return
    
    shadows = data[0] if data else [0, 0, 0]
    lut_data["lift"] = [1.0 + (s - 0.0) * 0.5 for s in shadows]
    
    mid_idx = len(data) // 2
    midtones = data[mid_idx] if mid_idx < len(data) else [0.5, 0.5, 0.5]
    lut_data["gamma"] = [1.0 + (m - 0.5) * 0.5 for m in midtones]
    
    highlights = data[-1] if data else [1, 1, 1]
    lut_data["gain"] = [h for h in highlights]


def apply_lut_to_color_balance(node, lut_data: dict):
    """Applique les paramètres LUT au node Color Balance."""
    lift = lut_data.get("lift", [1, 1, 1])
    gamma = lut_data.get("gamma", [1, 1, 1])
    gain = lut_data.get("gain", [1, 1, 1])
    
    node.lift = (lift[0], lift[1], lift[2], 1.0)
    node.gamma = (gamma[0], gamma[1], gamma[2], 1.0)
    node.gain = (gain[0], gain[1], gain[2], 1.0)


def create_effects_nodes(tree, effects: dict, last_output) -> 'bpy.types.Node':
    """Crée les nodes d'effets visuels."""
    current_output = last_output
    x_pos = 600
    
    if effects.get("bloom", False):
        glare = tree.nodes.new('CompositorNodeGlare')
        glare.location = (x_pos, 0)
        glare.name = "Bloom"
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'HIGH'
        glare.threshold = 0.8
        glare.mix = 0.3
        glare.size = 7
        
        tree.links.new(current_output, glare.inputs['Image'])
        current_output = glare.outputs['Image']
        x_pos += 200
    
    if effects.get("lens_flare", False):
        flare = tree.nodes.new('CompositorNodeGlare')
        flare.location = (x_pos, 0)
        flare.name = "LensFlare"
        flare.glare_type = 'STREAKS'
        flare.quality = 'HIGH'
        flare.threshold = 0.9
        flare.mix = 0.2
        flare.streaks = 4
        flare.angle_offset = 0.0
        
        tree.links.new(current_output, flare.inputs['Image'])
        current_output = flare.outputs['Image']
        x_pos += 200
    
    vignette_strength = effects.get("vignette", 0.0)
    if vignette_strength > 0:
        vignette_ellipse = tree.nodes.new('CompositorNodeEllipseMask')
        vignette_ellipse.location = (x_pos, -200)
        vignette_ellipse.name = "Vignette_Mask"
        vignette_ellipse.width = 0.8
        vignette_ellipse.height = 0.8
        
        vignette_blur = tree.nodes.new('CompositorNodeBlur')
        vignette_blur.location = (x_pos + 150, -200)
        vignette_blur.name = "Vignette_Blur"
        vignette_blur.size_x = 200
        vignette_blur.size_y = 200
        
        vignette_mix = tree.nodes.new('CompositorNodeMixRGB')
        vignette_mix.location = (x_pos + 300, 0)
        vignette_mix.name = "Vignette_Mix"
        vignette_mix.blend_type = 'MULTIPLY'
        vignette_mix.inputs['Fac'].default_value = vignette_strength
        
        tree.links.new(vignette_ellipse.outputs['Mask'], vignette_blur.inputs['Image'])
        tree.links.new(current_output, vignette_mix.inputs[1])
        tree.links.new(vignette_blur.outputs['Image'], vignette_mix.inputs[2])
        
        current_output = vignette_mix.outputs['Image']
        x_pos += 500
    
    grain_strength = effects.get("film_grain", 0.0)
    if grain_strength > 0:
        grain_texture = tree.nodes.new('CompositorNodeTexture')
        grain_texture.location = (x_pos, -200)
        grain_texture.name = "Grain_Texture"
        
        if 'FilmGrain' not in bpy.data.textures:
            grain_tex = bpy.data.textures.new('FilmGrain', type='NOISE')
            grain_tex.noise_scale = 0.5
        grain_texture.texture = bpy.data.textures.get('FilmGrain')
        
        grain_mix = tree.nodes.new('CompositorNodeMixRGB')
        grain_mix.location = (x_pos + 200, 0)
        grain_mix.name = "Grain_Mix"
        grain_mix.blend_type = 'OVERLAY'
        grain_mix.inputs['Fac'].default_value = grain_strength
        
        tree.links.new(current_output, grain_mix.inputs[1])
        tree.links.new(grain_texture.outputs['Color'], grain_mix.inputs[2])
        
        current_output = grain_mix.outputs['Image']
        x_pos += 400
    
    ca_strength = effects.get("chromatic_aberration", 0.0)
    if ca_strength > 0:
        lens_distort = tree.nodes.new('CompositorNodeLensdist')
        lens_distort.location = (x_pos, 0)
        lens_distort.name = "ChromaticAberration"
        lens_distort.use_fit = True
        lens_distort.inputs['Dispersion'].default_value = ca_strength
        
        tree.links.new(current_output, lens_distort.inputs['Image'])
        current_output = lens_distort.outputs['Image']
        x_pos += 200
    
    return current_output, x_pos


def create_output_nodes(tree, output_dir: str, scene_id: int, x_pos: int):
    """Crée les nodes de sortie EXR et optionnellement viewer."""
    output = tree.nodes.new('CompositorNodeOutputFile')
    output.location = (x_pos + 200, 0)
    output.name = "EXR_Output"
    output.base_path = output_dir
    output.format.file_format = 'OPEN_EXR'
    output.format.color_depth = '16'
    output.format.exr_codec = 'ZIP'
    
    if output.file_slots:
        output.file_slots[0].path = f"graded_{scene_id:03d}_"
    
    viewer = tree.nodes.new('CompositorNodeViewer')
    viewer.location = (x_pos + 200, -200)
    viewer.name = "Viewer"
    
    return output, viewer


def build_compositor_pipeline(config: dict):
    """Construit le pipeline de compositing complet."""
    scene_id = config.get("scene_id", 1)
    input_exr = config.get("input_exr", "")
    frame_start = config.get("frame_start", 1)
    frame_end = config.get("frame_end", 1)
    output_dir = config.get("output_dir", "/tmp")
    lut_path = config.get("lut_path", "")
    post_config = config.get("post_config", {})
    
    effects = post_config.get("effects", {})
    use_denoise = post_config.get("denoise", True)
    
    print(f"[COMPOSITOR] Building pipeline for Scene {scene_id}")
    print(f"[COMPOSITOR] Input: {input_exr}")
    print(f"[COMPOSITOR] Frames: {frame_start} - {frame_end}")
    print(f"[COMPOSITOR] LUT: {lut_path or 'None'}")
    print(f"[COMPOSITOR] Effects: {effects}")
    
    tree = clear_compositor()
    
    image_node = create_image_input_node(tree, input_exr, frame_start, frame_end)
    current_output = image_node.outputs['Image']
    
    if use_denoise:
        denoise_node = create_denoise_node(tree)
        tree.links.new(current_output, denoise_node.inputs['Image'])
        current_output = denoise_node.outputs['Image']
    
    exposure_node, hue_sat_node = create_color_grade_group(tree, post_config, lut_path)
    tree.links.new(current_output, exposure_node.inputs['Image'])
    current_output = hue_sat_node.outputs['Image']
    
    if lut_path:
        lut_node = create_lut_node(tree, lut_path)
        tree.links.new(current_output, lut_node.inputs['Image'])
        current_output = lut_node.outputs['Image']
        x_pos = 600
    else:
        x_pos = 400
    
    if any(effects.values()):
        current_output, x_pos = create_effects_nodes(tree, effects, current_output)
    
    output_node, viewer_node = create_output_nodes(tree, output_dir, scene_id, x_pos)
    tree.links.new(current_output, output_node.inputs[0])
    tree.links.new(current_output, viewer_node.inputs['Image'])
    
    print("[COMPOSITOR] Pipeline built successfully")
    return tree


def render_sequence(frame_start: int, frame_end: int):
    """Lance le rendu de la séquence."""
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    
    print(f"[COMPOSITOR] Rendering frames {frame_start} to {frame_end}...")
    
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.ops.render.render(write_still=False)
        
        if frame % 10 == 0:
            progress = (frame - frame_start + 1) / (frame_end - frame_start + 1) * 100
            print(f"[COMPOSITOR] Progress: {progress:.1f}% (frame {frame})")
    
    print("[COMPOSITOR] Render complete")


def main():
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = []
    
    parser = argparse.ArgumentParser(description='Compositor Pipeline')
    parser.add_argument('--config', required=True, help='JSON configuration')
    
    args = parser.parse_args(argv)
    
    try:
        config = json.loads(args.config)
    except json.JSONDecodeError as e:
        print(f"[COMPOSITOR:ERROR] Invalid JSON config: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("   COMPOSITOR PIPELINE — EXODUS ALCHEMIST")
    print("=" * 60)
    
    if not BLENDER_AVAILABLE:
        print("[COMPOSITOR] Validation mode - Blender not available")
        print(f"[COMPOSITOR] Config validated: {json.dumps(config, indent=2)}")
        sys.exit(0)
    
    tree = build_compositor_pipeline(config)
    
    frame_start = config.get("frame_start", 1)
    frame_end = config.get("frame_end", 1)
    
    if frame_start > 0 and frame_end >= frame_start:
        render_sequence(frame_start, frame_end)
    else:
        print("[COMPOSITOR] Skipping render - invalid frame range")
    
    print("\n" + "=" * 60)
    print("   COMPOSITOR PIPELINE — COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
