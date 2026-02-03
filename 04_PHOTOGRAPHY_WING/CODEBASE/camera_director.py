#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   CAMERA DIRECTOR — EXODUS PHOTOGRAPHY                        ║
║              Création et Animation Caméra selon Styles Prédéfinis            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Script Blender headless pour créer et animer la caméra selon le style demandé.
Supporte: dolly, orbit, static, handheld, tracking

Usage (appelé par EXO_04_PHOTOGRAPHY.py):
    blender --background env.blend --python camera_director.py -- \\
        --scene-config '{"camera": {...}, "lighting": {...}}' \\
        --output-dir /path/to/output \\
        --scene-id 1
"""

import argparse
import json
import sys
import math
import random
from pathlib import Path

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[CAMERA_DIRECTOR] Blender non disponible - mode test")


CAMERA_STYLES = ["dolly", "orbit", "static", "handheld", "tracking"]
DEFAULT_CAMERA_STYLE = "static"

MOVEMENT_SPEEDS = {
    "slow": 0.3,
    "medium": 1.0,
    "fast": 2.5
}

CUT_TYPES = {
    "wide": {"fov": 60, "distance_mult": 2.5},
    "medium": {"fov": 50, "distance_mult": 1.5},
    "closeup": {"fov": 35, "distance_mult": 0.8},
    "extreme_closeup": {"fov": 25, "distance_mult": 0.4},
    "dutch_angle": {"fov": 45, "distance_mult": 1.2, "roll": 15}
}


class CameraDirector:
    """Gère la création et l'animation de la caméra."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.camera = None
        self.camera_obj = None
        self.target = None
        self.operations = []
    
    def log(self, msg: str):
        print(f"[CAMERA_DIRECTOR] {msg}")
        self.operations.append({"action": "log", "message": msg})
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[CAMERA_DIRECTOR:DEBUG] {msg}")
    
    def get_scene_center(self) -> tuple:
        """Calcule le centre de la scène basé sur les objets mesh."""
        if not BLENDER_AVAILABLE:
            return (0, 0, 1)
        
        meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        if not meshes:
            self.debug("Aucun mesh trouvé, utilisation origine")
            return (0, 0, 1)
        
        total = mathutils.Vector((0, 0, 0))
        for obj in meshes:
            total += obj.location
        
        center = total / len(meshes)
        self.debug(f"Centre scène calculé: {center}")
        return (center.x, center.y, max(center.z, 1.0))
    
    def get_scene_bounds(self) -> tuple:
        """Retourne les dimensions approximatives de la scène."""
        if not BLENDER_AVAILABLE:
            return (10, 10, 5)
        
        min_coord = mathutils.Vector((float('inf'), float('inf'), float('inf')))
        max_coord = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
        
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for corner in obj.bound_box:
                    world_corner = obj.matrix_world @ mathutils.Vector(corner)
                    min_coord.x = min(min_coord.x, world_corner.x)
                    min_coord.y = min(min_coord.y, world_corner.y)
                    min_coord.z = min(min_coord.z, world_corner.z)
                    max_coord.x = max(max_coord.x, world_corner.x)
                    max_coord.y = max(max_coord.y, world_corner.y)
                    max_coord.z = max(max_coord.z, world_corner.z)
        
        if min_coord.x == float('inf'):
            return (10, 10, 5)
        
        size = max_coord - min_coord
        return (max(size.x, 1), max(size.y, 1), max(size.z, 1))
    
    def create_camera(self, name: str = "EXODUS_Camera") -> object:
        """Crée une nouvelle caméra ou récupère l'existante."""
        if not BLENDER_AVAILABLE:
            return None
        
        if name in bpy.data.objects:
            self.camera_obj = bpy.data.objects[name]
            self.camera = self.camera_obj.data
            self.log(f"Caméra existante récupérée: {name}")
        else:
            self.camera = bpy.data.cameras.new(name=name)
            self.camera_obj = bpy.data.objects.new(name=name, object_data=self.camera)
            bpy.context.scene.collection.objects.link(self.camera_obj)
            self.log(f"Nouvelle caméra créée: {name}")
        
        bpy.context.scene.camera = self.camera_obj
        return self.camera_obj
    
    def create_target(self, name: str = "Camera_Target") -> object:
        """Crée un empty comme cible pour la caméra."""
        if not BLENDER_AVAILABLE:
            return None
        
        if name in bpy.data.objects:
            self.target = bpy.data.objects[name]
        else:
            self.target = bpy.data.objects.new(name, None)
            self.target.empty_display_type = 'SPHERE'
            self.target.empty_display_size = 0.5
            bpy.context.scene.collection.objects.link(self.target)
        
        center = self.get_scene_center()
        self.target.location = center
        self.debug(f"Target créé à {center}")
        return self.target
    
    def setup_camera_constraints(self, track_target: bool = True):
        """Configure les contraintes de la caméra."""
        if not BLENDER_AVAILABLE or not self.camera_obj:
            return
        
        for constraint in self.camera_obj.constraints:
            self.camera_obj.constraints.remove(constraint)
        
        if track_target and self.target:
            track = self.camera_obj.constraints.new('TRACK_TO')
            track.target = self.target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            self.debug("Contrainte Track To ajoutée")
    
    def set_fov(self, fov_degrees: float):
        """Définit le FOV de la caméra en degrés."""
        if not BLENDER_AVAILABLE or not self.camera:
            return
        
        self.camera.angle = math.radians(fov_degrees)
        self.debug(f"FOV défini: {fov_degrees}°")
    
    def set_dof(self, enabled: bool = True, focus_distance: float = 5.0, f_stop: float = 2.8):
        """Configure la profondeur de champ."""
        if not BLENDER_AVAILABLE or not self.camera:
            return
        
        self.camera.dof.use_dof = enabled
        if enabled:
            self.camera.dof.focus_distance = focus_distance
            self.camera.dof.aperture_fstop = f_stop
            self.debug(f"DOF activé: distance={focus_distance}, f/{f_stop}")
    
    def apply_style_static(self, config: dict):
        """Style STATIC: caméra fixe pointant vers le centre."""
        self.log("Application style: STATIC")
        
        center = self.get_scene_center()
        bounds = self.get_scene_bounds()
        
        distance = max(bounds) * 2.5
        
        if BLENDER_AVAILABLE and self.camera_obj:
            self.camera_obj.location = (
                center[0] + distance * 0.7,
                center[1] - distance * 0.7,
                center[2] + distance * 0.3
            )
            self.setup_camera_constraints(track_target=True)
        
        self.set_fov(50)
        self.operations.append({"action": "style", "type": "static", "distance": distance})
    
    def apply_style_dolly(self, config: dict, frame_start: int, frame_end: int):
        """Style DOLLY: mouvement linéaire sur rail."""
        self.log("Application style: DOLLY")
        
        if not BLENDER_AVAILABLE:
            return
        
        center = self.get_scene_center()
        bounds = self.get_scene_bounds()
        
        speed_mult = MOVEMENT_SPEEDS.get(config.get("movement", "medium"), 1.0)
        distance = max(bounds) * 2.0
        
        travel_distance = max(bounds[0], bounds[1]) * speed_mult
        
        start_pos = (
            center[0] - travel_distance / 2,
            center[1] - distance,
            center[2] + bounds[2] * 0.5
        )
        end_pos = (
            center[0] + travel_distance / 2,
            center[1] - distance,
            center[2] + bounds[2] * 0.5
        )
        
        self.camera_obj.location = start_pos
        self.camera_obj.keyframe_insert(data_path="location", frame=frame_start)
        
        self.camera_obj.location = end_pos
        self.camera_obj.keyframe_insert(data_path="location", frame=frame_end)
        
        self.setup_camera_constraints(track_target=True)
        self._set_bezier_interpolation(self.camera_obj, "location")
        
        self.set_fov(45)
        self.operations.append({
            "action": "style", "type": "dolly",
            "start_pos": start_pos, "end_pos": end_pos,
            "frames": [frame_start, frame_end]
        })
    
    def apply_style_orbit(self, config: dict, frame_start: int, frame_end: int):
        """Style ORBIT: rotation autour du sujet."""
        self.log("Application style: ORBIT")
        
        if not BLENDER_AVAILABLE:
            return
        
        center = self.get_scene_center()
        bounds = self.get_scene_bounds()
        
        speed_mult = MOVEMENT_SPEEDS.get(config.get("movement", "medium"), 1.0)
        radius = max(bounds) * 1.8
        height = center[2] + bounds[2] * 0.3
        
        rotation_amount = math.pi * speed_mult
        
        num_keyframes = max(8, int((frame_end - frame_start) / 30))
        
        for i in range(num_keyframes + 1):
            t = i / num_keyframes
            frame = frame_start + int(t * (frame_end - frame_start))
            angle = -math.pi/4 + rotation_amount * t
            
            pos = (
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle),
                height
            )
            
            self.camera_obj.location = pos
            self.camera_obj.keyframe_insert(data_path="location", frame=frame)
        
        self.setup_camera_constraints(track_target=True)
        self._set_bezier_interpolation(self.camera_obj, "location")
        
        self.set_fov(50)
        self.operations.append({
            "action": "style", "type": "orbit",
            "radius": radius, "rotation": math.degrees(rotation_amount),
            "frames": [frame_start, frame_end]
        })
    
    def apply_style_handheld(self, config: dict, frame_start: int, frame_end: int):
        """Style HANDHELD: micro-mouvements aléatoires (noise)."""
        self.log("Application style: HANDHELD")
        
        if not BLENDER_AVAILABLE:
            return
        
        center = self.get_scene_center()
        bounds = self.get_scene_bounds()
        
        distance = max(bounds) * 2.0
        base_pos = (
            center[0] + distance * 0.5,
            center[1] - distance * 0.5,
            center[2] + bounds[2] * 0.3
        )
        
        noise_amplitude = 0.05
        noise_freq = 5
        
        for frame in range(frame_start, frame_end + 1, noise_freq):
            offset = (
                random.gauss(0, noise_amplitude),
                random.gauss(0, noise_amplitude),
                random.gauss(0, noise_amplitude * 0.5)
            )
            
            pos = (
                base_pos[0] + offset[0],
                base_pos[1] + offset[1],
                base_pos[2] + offset[2]
            )
            
            self.camera_obj.location = pos
            self.camera_obj.keyframe_insert(data_path="location", frame=frame)
            
            rot_offset = (
                random.gauss(0, 0.005),
                random.gauss(0, 0.005),
                random.gauss(0, 0.002)
            )
            
            self.camera_obj.rotation_euler = rot_offset
            self.camera_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        self.setup_camera_constraints(track_target=True)
        
        self.set_fov(40)
        self.operations.append({
            "action": "style", "type": "handheld",
            "base_pos": base_pos, "noise": noise_amplitude,
            "frames": [frame_start, frame_end]
        })
    
    def apply_style_tracking(self, config: dict, frame_start: int, frame_end: int):
        """Style TRACKING: suit un objet cible."""
        self.log("Application style: TRACKING")
        
        if not BLENDER_AVAILABLE:
            return
        
        target_name = config.get("tracking_target", None)
        tracked_obj = None
        
        if target_name and target_name in bpy.data.objects:
            tracked_obj = bpy.data.objects[target_name]
            self.debug(f"Objet cible trouvé: {target_name}")
        else:
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' or 'actor' in obj.name.lower():
                    tracked_obj = obj
                    break
        
        if tracked_obj:
            self.target.location = tracked_obj.location
            
            follow = self.target.constraints.new('COPY_LOCATION')
            follow.target = tracked_obj
            follow.use_offset = True
        
        bounds = self.get_scene_bounds()
        distance = max(bounds) * 2.0
        
        center = self.get_scene_center()
        self.camera_obj.location = (
            center[0],
            center[1] - distance,
            center[2] + bounds[2] * 0.5
        )
        
        self.setup_camera_constraints(track_target=True)
        
        self.set_fov(45)
        self.set_dof(enabled=True, focus_distance=distance, f_stop=2.0)
        self.operations.append({
            "action": "style", "type": "tracking",
            "target": tracked_obj.name if tracked_obj else "auto"
        })
    
    def _set_bezier_interpolation(self, obj, data_path: str):
        """Configure l'interpolation Bezier pour des mouvements fluides."""
        if not BLENDER_AVAILABLE or not obj.animation_data:
            return
        
        action = obj.animation_data.action
        if not action:
            return
        
        for fcurve in action.fcurves:
            if data_path in fcurve.data_path:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'BEZIER'
                    keyframe.handle_left_type = 'AUTO_CLAMPED'
                    keyframe.handle_right_type = 'AUTO_CLAMPED'
    
    def apply_style(self, style: str, config: dict, frame_start: int, frame_end: int):
        """Applique le style caméra demandé."""
        style = style.lower()
        
        if style not in CAMERA_STYLES:
            self.log(f"Style '{style}' inconnu, fallback vers 'static'")
            style = "static"
        
        self.create_camera()
        self.create_target()
        
        if style == "static":
            self.apply_style_static(config)
        elif style == "dolly":
            self.apply_style_dolly(config, frame_start, frame_end)
        elif style == "orbit":
            self.apply_style_orbit(config, frame_start, frame_end)
        elif style == "handheld":
            self.apply_style_handheld(config, frame_start, frame_end)
        elif style == "tracking":
            self.apply_style_tracking(config, frame_start, frame_end)
    
    def get_operations(self) -> list:
        return self.operations


def setup_scene_from_config(config: dict, output_dir: str, scene_id: str, verbose: bool = False):
    """Configure la scène complète depuis la configuration."""
    
    director = CameraDirector(verbose=verbose)
    
    if not BLENDER_AVAILABLE:
        director.log("Mode simulation (Blender non disponible)")
        return director.get_operations()
    
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    
    if frame_end <= frame_start:
        frame_end = frame_start + 250
        bpy.context.scene.frame_end = frame_end
    
    director.log(f"Frame range: {frame_start} - {frame_end}")
    
    camera_config = config.get("camera", {})
    style = camera_config.get("style", DEFAULT_CAMERA_STYLE)
    
    director.apply_style(style, camera_config, frame_start, frame_end)
    
    cuts = camera_config.get("cuts", [])
    if cuts:
        from cuts_engine import CutsEngine
        cuts_engine = CutsEngine(director.camera_obj, director.target, verbose=verbose)
        cuts_engine.process_cuts(cuts, frame_start, frame_end)
        director.operations.extend(cuts_engine.get_operations())
    
    lighting_config = config.get("lighting", {})
    if lighting_config:
        from lighting_rig import LightingRig
        lighting = LightingRig(verbose=verbose)
        lighting.apply_style(
            lighting_config.get("style", "3point"),
            lighting_config.get("intensity", 1.0),
            lighting_config.get("color_temp", 5500)
        )
        director.operations.extend(lighting.get_operations())
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    blend_path = output_path / f"scene_ready_{scene_id}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    director.log(f"Scène sauvegardée: {blend_path}")
    
    camera_data = {
        "scene_id": scene_id,
        "frame_range": [frame_start, frame_end],
        "camera": {
            "name": director.camera_obj.name if director.camera_obj else "N/A",
            "style": style,
            "fov": math.degrees(director.camera.angle) if director.camera else 50,
            "location": list(director.camera_obj.location) if director.camera_obj else [0, 0, 0]
        },
        "target": {
            "name": director.target.name if director.target else "N/A",
            "location": list(director.target.location) if director.target else [0, 0, 0]
        },
        "operations": director.get_operations()
    }
    
    camera_json_path = output_path / f"camera_data_{scene_id}.json"
    with open(camera_json_path, 'w', encoding='utf-8') as f:
        json.dump(camera_data, f, indent=2, ensure_ascii=False)
    director.log(f"Données caméra exportées: {camera_json_path}")
    
    return director.get_operations()


def main():
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description='Camera Director - Blender Script')
    parser.add_argument('--scene-config', required=True, help='JSON config de la scène')
    parser.add_argument('--output-dir', required=True, help='Dossier output')
    parser.add_argument('--scene-id', required=True, help='ID de la scène')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logs détaillés')
    
    args = parser.parse_args(argv)
    
    try:
        config = json.loads(args.scene_config)
    except json.JSONDecodeError as e:
        print(f"[CAMERA_DIRECTOR:ERROR] JSON invalide: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("   CAMERA DIRECTOR — EXODUS PHOTOGRAPHY")
    print("=" * 60)
    
    operations = setup_scene_from_config(
        config,
        args.output_dir,
        args.scene_id,
        verbose=args.verbose
    )
    
    print(f"\n[CAMERA_DIRECTOR] Opérations effectuées: {len(operations)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
