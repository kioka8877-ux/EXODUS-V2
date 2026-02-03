#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PBR APPLICATOR — EXODUS SCENOGRAPHY                        ║
║              Application Automatique Matériaux PBR                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour créer et appliquer des matériaux PBR dans Blender.
Supporte les textures (albedo, normal, roughness, metallic) avec fallback.
"""

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from pathlib import Path


MATERIAL_PRESETS = {
    "asphalt": {
        "base_color": (0.15, 0.15, 0.15, 1.0),
        "roughness": 0.8,
        "metallic": 0.0,
        "specular": 0.3
    },
    "concrete": {
        "base_color": (0.5, 0.5, 0.5, 1.0),
        "roughness": 0.9,
        "metallic": 0.0,
        "specular": 0.3
    },
    "grass": {
        "base_color": (0.15, 0.35, 0.1, 1.0),
        "roughness": 0.95,
        "metallic": 0.0,
        "specular": 0.2
    },
    "wood_floor": {
        "base_color": (0.4, 0.25, 0.12, 1.0),
        "roughness": 0.6,
        "metallic": 0.0,
        "specular": 0.4
    },
    "plaster": {
        "base_color": (0.9, 0.88, 0.85, 1.0),
        "roughness": 0.85,
        "metallic": 0.0,
        "specular": 0.2
    },
    "studio_floor": {
        "base_color": (0.18, 0.18, 0.18, 1.0),
        "roughness": 0.4,
        "metallic": 0.0,
        "specular": 0.5
    },
    "studio_white": {
        "base_color": (0.95, 0.95, 0.95, 1.0),
        "roughness": 0.8,
        "metallic": 0.0,
        "specular": 0.3
    },
    "metal_steel": {
        "base_color": (0.6, 0.6, 0.65, 1.0),
        "roughness": 0.3,
        "metallic": 0.9,
        "specular": 0.8
    },
    "metal_rust": {
        "base_color": (0.45, 0.25, 0.15, 1.0),
        "roughness": 0.7,
        "metallic": 0.6,
        "specular": 0.4
    },
    "brick": {
        "base_color": (0.55, 0.25, 0.15, 1.0),
        "roughness": 0.85,
        "metallic": 0.0,
        "specular": 0.2
    },
    "glass": {
        "base_color": (0.9, 0.95, 1.0, 0.3),
        "roughness": 0.05,
        "metallic": 0.0,
        "specular": 1.0,
        "transmission": 0.9
    },
    "plastic_glossy": {
        "base_color": (0.1, 0.1, 0.12, 1.0),
        "roughness": 0.2,
        "metallic": 0.0,
        "specular": 0.6
    },
    "fabric": {
        "base_color": (0.3, 0.28, 0.25, 1.0),
        "roughness": 0.95,
        "metallic": 0.0,
        "specular": 0.1
    },
    "default": {
        "base_color": (0.5, 0.5, 0.5, 1.0),
        "roughness": 0.7,
        "metallic": 0.0,
        "specular": 0.4
    }
}


def create_basic_material(name: str, preset_type: str = "default") -> 'bpy.types.Material':
    """
    Crée un matériau basique avec les paramètres PBR.
    
    Args:
        name: Nom du matériau
        preset_type: Type de preset (asphalt, concrete, grass, etc.)
    
    Returns:
        Le matériau créé
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("PBR Applicator requires Blender")
    
    preset = MATERIAL_PRESETS.get(preset_type, MATERIAL_PRESETS["default"])
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    bsdf.inputs['Base Color'].default_value = preset["base_color"]
    bsdf.inputs['Roughness'].default_value = preset["roughness"]
    bsdf.inputs['Metallic'].default_value = preset["metallic"]
    bsdf.inputs['Specular IOR Level'].default_value = preset["specular"]
    
    if "transmission" in preset:
        bsdf.inputs['Transmission Weight'].default_value = preset["transmission"]
        mat.blend_method = 'BLEND'
        mat.shadow_method = 'HASHED'
    
    links = mat.node_tree.links
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    print(f"[PBR] Matériau créé: {name} (preset: {preset_type})")
    return mat


def create_textured_material(
    name: str,
    albedo_path: str = None,
    normal_path: str = None,
    roughness_path: str = None,
    metallic_path: str = None,
    fallback_preset: str = "default"
) -> 'bpy.types.Material':
    """
    Crée un matériau PBR avec textures.
    
    Args:
        name: Nom du matériau
        albedo_path: Chemin vers la texture albedo/diffuse
        normal_path: Chemin vers la normal map
        roughness_path: Chemin vers la roughness map
        metallic_path: Chemin vers la metallic map
        fallback_preset: Preset à utiliser si textures manquantes
    
    Returns:
        Le matériau créé
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("PBR Applicator requires Blender")
    
    mat = create_basic_material(name, fallback_preset)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break
    
    if not bsdf:
        print(f"[PBR:WARN] BSDF node not found for {name}")
        return mat
    
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    mapping = nodes.new(type='ShaderNodeMapping')
    mapping.location = (-600, 0)
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    
    current_y = 200
    
    if albedo_path and Path(albedo_path).exists():
        albedo_tex = nodes.new(type='ShaderNodeTexImage')
        albedo_tex.location = (-400, current_y)
        albedo_tex.image = bpy.data.images.load(albedo_path)
        albedo_tex.image.colorspace_settings.name = 'sRGB'
        links.new(mapping.outputs['Vector'], albedo_tex.inputs['Vector'])
        links.new(albedo_tex.outputs['Color'], bsdf.inputs['Base Color'])
        print(f"[PBR] Albedo texture: {albedo_path}")
        current_y -= 300
    
    if normal_path and Path(normal_path).exists():
        normal_tex = nodes.new(type='ShaderNodeTexImage')
        normal_tex.location = (-400, current_y)
        normal_tex.image = bpy.data.images.load(normal_path)
        normal_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping.outputs['Vector'], normal_tex.inputs['Vector'])
        
        normal_map = nodes.new(type='ShaderNodeNormalMap')
        normal_map.location = (-100, current_y)
        links.new(normal_tex.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
        print(f"[PBR] Normal texture: {normal_path}")
        current_y -= 300
    
    if roughness_path and Path(roughness_path).exists():
        rough_tex = nodes.new(type='ShaderNodeTexImage')
        rough_tex.location = (-400, current_y)
        rough_tex.image = bpy.data.images.load(roughness_path)
        rough_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping.outputs['Vector'], rough_tex.inputs['Vector'])
        links.new(rough_tex.outputs['Color'], bsdf.inputs['Roughness'])
        print(f"[PBR] Roughness texture: {roughness_path}")
        current_y -= 300
    
    if metallic_path and Path(metallic_path).exists():
        metal_tex = nodes.new(type='ShaderNodeTexImage')
        metal_tex.location = (-400, current_y)
        metal_tex.image = bpy.data.images.load(metallic_path)
        metal_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping.outputs['Vector'], metal_tex.inputs['Vector'])
        links.new(metal_tex.outputs['Color'], bsdf.inputs['Metallic'])
        print(f"[PBR] Metallic texture: {metallic_path}")
    
    print(f"[PBR] Matériau texturé créé: {name}")
    return mat


def apply_material_to_object(obj: 'bpy.types.Object', material: 'bpy.types.Material'):
    """Applique un matériau à un objet."""
    if not BLENDER_AVAILABLE:
        raise RuntimeError("PBR Applicator requires Blender")
    
    if obj.type != 'MESH':
        print(f"[PBR:WARN] Object {obj.name} n'est pas un mesh, skip")
        return
    
    obj.data.materials.clear()
    obj.data.materials.append(material)
    
    print(f"[PBR] Matériau {material.name} appliqué à {obj.name}")


def auto_apply_materials(collection: 'bpy.types.Collection', material_hints: dict = None):
    """
    Applique automatiquement des matériaux aux objets d'une collection.
    
    Args:
        collection: Collection Blender
        material_hints: Dict {object_name_pattern: preset_type}
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("PBR Applicator requires Blender")
    
    hints = material_hints or {}
    
    name_to_preset = {
        "ground": "concrete",
        "floor": "wood_floor",
        "wall": "plaster",
        "ceiling": "plaster",
        "street": "asphalt",
        "grass": "grass",
        "metal": "metal_steel",
        "steel": "metal_steel",
        "rust": "metal_rust",
        "brick": "brick",
        "glass": "glass",
        "window": "glass",
        "plastic": "plastic_glossy",
        "fabric": "fabric",
        "cyclorama": "studio_white"
    }
    name_to_preset.update(hints)
    
    for obj in collection.objects:
        if obj.type != 'MESH':
            continue
        
        obj_name_lower = obj.name.lower()
        
        preset = "default"
        for pattern, preset_type in name_to_preset.items():
            if pattern.lower() in obj_name_lower:
                preset = preset_type
                break
        
        if not obj.data.materials:
            mat = create_basic_material(f"Auto_{obj.name}", preset)
            obj.data.materials.append(mat)
            print(f"[PBR:AUTO] {obj.name} → {preset}")


def find_pbr_textures(base_path: str, material_name: str) -> dict:
    """
    Recherche automatiquement les textures PBR dans un dossier.
    
    Args:
        base_path: Dossier de base
        material_name: Nom du matériau (utilisé pour matching)
    
    Returns:
        Dict avec les chemins vers les textures trouvées
    """
    base = Path(base_path)
    textures = {}
    
    suffixes = {
        "albedo": ["_albedo", "_diffuse", "_color", "_basecolor", "_base_color", "_diff", "_col"],
        "normal": ["_normal", "_norm", "_nrm", "_normalgl", "_nor"],
        "roughness": ["_roughness", "_rough", "_rgh"],
        "metallic": ["_metallic", "_metal", "_met", "_metalness"]
    }
    
    extensions = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr"]
    
    material_lower = material_name.lower()
    
    for tex_type, patterns in suffixes.items():
        for pattern in patterns:
            for ext in extensions:
                candidates = [
                    base / f"{material_name}{pattern}{ext}",
                    base / f"{material_lower}{pattern}{ext}",
                    base / material_name / f"{material_name}{pattern}{ext}",
                    base / material_lower / f"{material_lower}{pattern}{ext}",
                ]
                
                for candidate in candidates:
                    if candidate.exists():
                        textures[tex_type] = str(candidate)
                        break
                
                if tex_type in textures:
                    break
            
            if tex_type in textures:
                break
    
    if textures:
        print(f"[PBR] Textures trouvées pour {material_name}: {list(textures.keys())}")
    
    return textures


if __name__ == "__main__":
    print("[PBR] Module PBR Applicator chargé")
    print(f"[PBR] Presets disponibles: {list(MATERIAL_PRESETS.keys())}")
