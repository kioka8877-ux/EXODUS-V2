#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   LIGHTING RIG — EXODUS PHOTOGRAPHY                           ║
║              Configuration Éclairage Cinématique Automatisée                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Gère la création des rigs d'éclairage selon les styles prédéfinis.
Styles supportés: 3point, dramatic, neon, natural, studio

Usage (appelé par camera_director.py):
    lighting = LightingRig(verbose=True)
    lighting.apply_style("dramatic", intensity=1.2, color_temp=4500)
"""

import math
from typing import Optional, Tuple
from camera_schema import (
    LIGHTING_STYLES,
    VALID_LIGHTING_STYLES,
    DEFAULT_LIGHTING_STYLE,
    COLOR_TEMPS,
    NEON_COLORS,
    DEFAULT_VOLUME_DENSITY,
    DEFAULT_VOLUME_ANISOTROPY,
)

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False




class LightingRig:
    """Gère la création et configuration des éclairages."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.lights = []
        self.operations = []
        self.scene_center = (0, 0, 1)
        self.scene_radius = 5.0
        
        if BLENDER_AVAILABLE:
            self._calculate_scene_metrics()
    
    def log(self, msg: str):
        print(f"[LIGHTING_RIG] {msg}")
        self.operations.append({"action": "log", "message": msg})
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[LIGHTING_RIG:DEBUG] {msg}")
    
    def _calculate_scene_metrics(self):
        """Calcule les métriques de la scène."""
        if not BLENDER_AVAILABLE:
            return
        
        meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        if not meshes:
            return
        
        total = mathutils.Vector((0, 0, 0))
        for obj in meshes:
            total += obj.location
        
        center = total / len(meshes)
        self.scene_center = (center.x, center.y, max(center.z, 1.0))
        
        max_dist = 1.0
        for obj in meshes:
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ mathutils.Vector(corner)
                dist = (world_corner - center).length
                max_dist = max(max_dist, dist)
        
        self.scene_radius = max_dist
        self.debug(f"Scene: center={self.scene_center}, radius={self.scene_radius}")
    
    def color_temp_to_rgb(self, kelvin: int) -> Tuple[float, float, float]:
        """Convertit une température couleur en RGB."""
        closest_temp = min(COLOR_TEMPS.keys(), key=lambda x: abs(x - kelvin))
        return COLOR_TEMPS[closest_temp]
    
    def clear_existing_lights(self, prefix: str = "EXODUS_"):
        """Supprime les lumières existantes avec le préfixe donné."""
        if not BLENDER_AVAILABLE:
            return
        
        to_remove = [obj for obj in bpy.data.objects 
                     if obj.type == 'LIGHT' and obj.name.startswith(prefix)]
        
        for obj in to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)
            self.debug(f"Lumière supprimée: {obj.name}")
        
        self.lights = []
    
    def create_light(self, name: str, light_type: str, location: tuple,
                     energy: float, color: tuple, size: float = 1.0) -> object:
        """Crée une lumière avec les paramètres spécifiés."""
        if not BLENDER_AVAILABLE:
            self.operations.append({
                "action": "create_light",
                "name": name,
                "type": light_type,
                "location": location,
                "energy": energy,
                "color": color
            })
            return None
        
        light_data = bpy.data.lights.new(name=name, type=light_type)
        light_data.energy = energy
        light_data.color = color
        
        if light_type == 'AREA':
            light_data.size = size
        elif light_type == 'SPOT':
            light_data.spot_size = math.radians(60)
            light_data.spot_blend = 0.5
        elif light_type == 'SUN':
            light_data.angle = math.radians(0.526)
        
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        bpy.context.scene.collection.objects.link(light_obj)
        
        light_obj.location = location
        
        self.lights.append(light_obj)
        self.debug(f"Lumière créée: {name} ({light_type}) @ {location}")
        
        return light_obj
    
    def point_light_at(self, light_obj, target: tuple):
        """Oriente une lumière vers une cible."""
        if not BLENDER_AVAILABLE or not light_obj:
            return
        
        direction = mathutils.Vector(target) - light_obj.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        light_obj.rotation_euler = rot_quat.to_euler()
    
    def apply_style_3point(self, intensity: float, color_temp: int):
        """Style 3-POINT: éclairage classique Key + Fill + Back."""
        self.log("Application style: 3-POINT")
        self.clear_existing_lights()
        
        rgb = self.color_temp_to_rgb(color_temp)
        r = self.scene_radius * 2
        
        key = self.create_light(
            "EXODUS_Key",
            'AREA',
            (self.scene_center[0] + r * 0.8,
             self.scene_center[1] - r * 0.6,
             self.scene_center[2] + r * 0.8),
            energy=1000 * intensity,
            color=rgb,
            size=2.0
        )
        if key:
            self.point_light_at(key, self.scene_center)
        
        fill_rgb = (rgb[0] * 0.9, rgb[1] * 0.95, min(rgb[2] * 1.1, 1.0))
        fill = self.create_light(
            "EXODUS_Fill",
            'AREA',
            (self.scene_center[0] - r * 0.6,
             self.scene_center[1] - r * 0.4,
             self.scene_center[2] + r * 0.3),
            energy=300 * intensity,
            color=fill_rgb,
            size=3.0
        )
        if fill:
            self.point_light_at(fill, self.scene_center)
        
        back = self.create_light(
            "EXODUS_Back",
            'SPOT',
            (self.scene_center[0],
             self.scene_center[1] + r * 0.8,
             self.scene_center[2] + r * 0.6),
            energy=500 * intensity,
            color=rgb
        )
        if back:
            self.point_light_at(back, self.scene_center)
        
        self.operations.append({
            "action": "style_applied",
            "style": "3point",
            "lights_count": 3
        })
    
    def apply_style_dramatic(self, intensity: float, color_temp: int):
        """Style DRAMATIC: fort contraste, ombres dures."""
        self.log("Application style: DRAMATIC")
        self.clear_existing_lights()
        
        rgb = self.color_temp_to_rgb(color_temp)
        r = self.scene_radius * 2
        
        key = self.create_light(
            "EXODUS_Key_Dramatic",
            'SPOT',
            (self.scene_center[0] + r * 0.5,
             self.scene_center[1] - r * 0.3,
             self.scene_center[2] + r * 1.2),
            energy=2000 * intensity,
            color=rgb
        )
        if key:
            self.point_light_at(key, self.scene_center)
            if BLENDER_AVAILABLE:
                key.data.spot_size = math.radians(30)
                key.data.spot_blend = 0.15
        
        rim = self.create_light(
            "EXODUS_Rim",
            'SPOT',
            (self.scene_center[0] - r * 0.3,
             self.scene_center[1] + r * 0.8,
             self.scene_center[2] + r * 0.5),
            energy=800 * intensity,
            color=(1.0, 1.0, 1.0)
        )
        if rim:
            self.point_light_at(rim, self.scene_center)
        
        self.operations.append({
            "action": "style_applied",
            "style": "dramatic",
            "lights_count": 2
        })
    
    def apply_style_neon(self, intensity: float, color_temp: int):
        """Style NEON: lumières émissives colorées."""
        self.log("Application style: NEON")
        self.clear_existing_lights()
        
        r = self.scene_radius * 1.5
        neon_colors = ["cyan", "magenta", "purple", "pink"]
        
        for i, color_name in enumerate(neon_colors):
            angle = (i / len(neon_colors)) * 2 * math.pi
            
            pos = (
                self.scene_center[0] + r * math.cos(angle),
                self.scene_center[1] + r * math.sin(angle),
                self.scene_center[2] + (i % 2) * 0.5
            )
            
            self.create_light(
                f"EXODUS_Neon_{color_name}",
                'AREA',
                pos,
                energy=500 * intensity,
                color=NEON_COLORS[color_name],
                size=0.5
            )
        
        self.create_light(
            "EXODUS_Ambient",
            'AREA',
            (self.scene_center[0],
             self.scene_center[1],
             self.scene_center[2] + r),
            energy=100 * intensity,
            color=(0.1, 0.1, 0.15),
            size=5.0
        )
        
        self.operations.append({
            "action": "style_applied",
            "style": "neon",
            "lights_count": len(neon_colors) + 1
        })
    
    def apply_style_natural(self, intensity: float, color_temp: int):
        """Style NATURAL: sun + sky (outdoor lighting)."""
        self.log("Application style: NATURAL")
        self.clear_existing_lights()
        
        sun_rgb = self.color_temp_to_rgb(5500)
        r = self.scene_radius * 3
        
        sun = self.create_light(
            "EXODUS_Sun",
            'SUN',
            (self.scene_center[0] + r,
             self.scene_center[1] - r * 0.5,
             self.scene_center[2] + r * 2),
            energy=5 * intensity,
            color=sun_rgb
        )
        if sun:
            self.point_light_at(sun, self.scene_center)
        
        sky_rgb = self.color_temp_to_rgb(9000)
        self.create_light(
            "EXODUS_Sky",
            'AREA',
            (self.scene_center[0],
             self.scene_center[1],
             self.scene_center[2] + r * 1.5),
            energy=200 * intensity,
            color=sky_rgb,
            size=10.0
        )
        
        bounce_rgb = self.color_temp_to_rgb(6500)
        self.create_light(
            "EXODUS_Bounce",
            'AREA',
            (self.scene_center[0] - r * 0.5,
             self.scene_center[1] + r * 0.3,
             self.scene_center[2] + 0.5),
            energy=100 * intensity,
            color=bounce_rgb,
            size=5.0
        )
        
        self.operations.append({
            "action": "style_applied",
            "style": "natural",
            "lights_count": 3
        })
    
    def apply_style_studio(self, intensity: float, color_temp: int):
        """Style STUDIO: softbox setup professionnel."""
        self.log("Application style: STUDIO")
        self.clear_existing_lights()
        
        rgb = self.color_temp_to_rgb(color_temp)
        r = self.scene_radius * 1.8
        
        main_soft = self.create_light(
            "EXODUS_Softbox_Main",
            'AREA',
            (self.scene_center[0] + r * 0.6,
             self.scene_center[1] - r * 0.4,
             self.scene_center[2] + r * 0.6),
            energy=800 * intensity,
            color=rgb,
            size=3.0
        )
        if main_soft:
            self.point_light_at(main_soft, self.scene_center)
        
        side_soft = self.create_light(
            "EXODUS_Softbox_Side",
            'AREA',
            (self.scene_center[0] - r * 0.5,
             self.scene_center[1] - r * 0.3,
             self.scene_center[2] + r * 0.4),
            energy=400 * intensity,
            color=rgb,
            size=2.5
        )
        if side_soft:
            self.point_light_at(side_soft, self.scene_center)
        
        top_soft = self.create_light(
            "EXODUS_Softbox_Top",
            'AREA',
            (self.scene_center[0],
             self.scene_center[1],
             self.scene_center[2] + r * 1.2),
            energy=300 * intensity,
            color=rgb,
            size=4.0
        )
        
        hair = self.create_light(
            "EXODUS_Hair_Light",
            'SPOT',
            (self.scene_center[0] + r * 0.2,
             self.scene_center[1] + r * 0.6,
             self.scene_center[2] + r * 0.8),
            energy=400 * intensity,
            color=(1.0, 1.0, 1.0)
        )
        if hair:
            self.point_light_at(hair, self.scene_center)
        
        self.operations.append({
            "action": "style_applied",
            "style": "studio",
            "lights_count": 4
        })
    
    def apply_style(self, style: str, intensity: float = 1.0, color_temp: int = 5500):
        """Applique le style d'éclairage demandé."""
        style = style.lower()
        
        if style not in VALID_LIGHTING_STYLES:
            self.log(f"Style '{style}' inconnu, fallback vers '3point'")
            style = "3point"
        
        intensity = max(0.1, min(intensity, 5.0))
        color_temp = max(2700, min(color_temp, 9000))
        
        if style == "3point":
            self.apply_style_3point(intensity, color_temp)
        elif style == "dramatic":
            self.apply_style_dramatic(intensity, color_temp)
        elif style == "neon":
            self.apply_style_neon(intensity, color_temp)
        elif style == "natural":
            self.apply_style_natural(intensity, color_temp)
        elif style == "studio":
            self.apply_style_studio(intensity, color_temp)
        
        self.log(f"Style '{style}' appliqué: intensity={intensity}, color_temp={color_temp}K")
        
        # Add atmosphere and invisible lamps
        self.apply_atmosphere()
        self.place_invisible_lamps()
    
    def animate_light(self, light_name: str, property_path: str, 
                      values: list, frames: list):
        """Anime une propriété d'une lumière."""
        if not BLENDER_AVAILABLE:
            return
        
        if light_name not in bpy.data.objects:
            self.log(f"Lumière '{light_name}' non trouvée")
            return
        
        light_obj = bpy.data.objects[light_name]
        
        for value, frame in zip(values, frames):
            if property_path == "energy":
                light_obj.data.energy = value
                light_obj.data.keyframe_insert(data_path="energy", frame=frame)
            elif property_path == "color":
                light_obj.data.color = value
                light_obj.data.keyframe_insert(data_path="color", frame=frame)
            elif property_path == "location":
                light_obj.location = value
                light_obj.keyframe_insert(data_path="location", frame=frame)
        
        self.debug(f"Animation ajoutée: {light_name}.{property_path}")
    
    def apply_atmosphere(self, density: float = DEFAULT_VOLUME_DENSITY,
                         anisotropy: float = DEFAULT_VOLUME_ANISOTROPY,
                         color: tuple = (1.0, 1.0, 1.0)) -> None:
        """Ajoute un Volume Scatter au World shader pour l'atmosphère cinématographique."""
        self.log(f"Application atmosphère : density={density}, anisotropy={anisotropy}")
        
        if not BLENDER_AVAILABLE:
            self.operations.append({
                "action": "apply_atmosphere",
                "density": density,
                "anisotropy": anisotropy,
                "simulated": True,
            })
            return
        
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("EXODUS_World")
            bpy.context.scene.world = world
        
        world.use_nodes = True
        tree = world.node_tree
        
        # Check if Volume Scatter already exists
        vol_scatter = None
        for node in tree.nodes:
            if node.type == 'VOLUME_SCATTER':
                vol_scatter = node
                break
        
        if vol_scatter is None:
            vol_scatter = tree.nodes.new(type='ShaderNodeVolumeScatter')
            vol_scatter.location = (0, -300)
        
        vol_scatter.inputs['Color'].default_value = (*color, 1.0)
        vol_scatter.inputs['Density'].default_value = density
        vol_scatter.inputs['Anisotropy'].default_value = anisotropy
        
        # Connect to World Output volume input
        output_node = None
        for node in tree.nodes:
            if node.type == 'OUTPUT_WORLD':
                output_node = node
                break
        
        if output_node is None:
            output_node = tree.nodes.new(type='ShaderNodeOutputWorld')
            output_node.location = (400, 0)
        
        # Connect Volume Scatter to Volume input of World Output
        tree.links.new(vol_scatter.outputs['Volume'], output_node.inputs['Volume'])
        
        self.log("Volume Scatter connecté au World shader")
        self.operations.append({
            "action": "apply_atmosphere",
            "density": density,
            "anisotropy": anisotropy,
            "color": color,
        })
    
    def place_invisible_lamps(self, count: int = 3, energy: float = 50.0,
                              color: tuple = (1.0, 1.0, 1.0)) -> None:
        """Place des lampes invisibles (camera_ray=False) pour rehausser l'atmosphère
        sans apparaître dans le rendu direct."""
        self.log(f"Placement lampes invisibles : count={count}, energy={energy}")
        
        if not BLENDER_AVAILABLE:
            self.operations.append({
                "action": "place_invisible_lamps",
                "count": count,
                "energy": energy,
                "simulated": True,
            })
            return
        
        r = self.scene_radius * 1.5
        
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            height_offset = (i % 2) * r * 0.3
            
            pos = (
                self.scene_center[0] + r * math.cos(angle),
                self.scene_center[1] + r * math.sin(angle),
                self.scene_center[2] + r * 0.5 + height_offset,
            )
            
            light_obj = self.create_light(
                f"EXODUS_Invisible_{i}",
                'POINT',
                pos,
                energy=energy,
                color=color,
            )
            
            if light_obj and light_obj.data:
                # Make invisible to camera ray (visible only for indirect/volume)
                light_obj.visible_camera = False
                light_obj.visible_diffuse = True
                light_obj.visible_glossy = True
                light_obj.visible_volume_scatter = True
                self.debug(f"Lampe invisible placée : {light_obj.name}")
        
        self.operations.append({
            "action": "place_invisible_lamps",
            "count": count,
            "energy": energy,
            "color": color,
        })
    
    def get_operations(self) -> list:
        return self.operations


def test_lighting_rig():
    """Fonction de test hors Blender."""
    print("=== Test LightingRig ===")
    
    rig = LightingRig(verbose=True)
    
    print(f"\nStyles disponibles: {LIGHTING_STYLES}")
    print(f"Températures couleur: {list(COLOR_TEMPS.keys())}K")
    print(f"Couleurs néon: {list(NEON_COLORS.keys())}")
    
    print("\n--- Test application styles ---")
    for style in VALID_LIGHTING_STYLES:
        print(f"\nStyle: {style}")
        rig.apply_style(style, intensity=1.0, color_temp=5500)
        print(f"  Opérations: {len(rig.operations)}")
        rig.operations = []


if __name__ == "__main__":
    test_lighting_rig()
