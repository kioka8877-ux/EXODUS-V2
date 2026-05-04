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
from pathlib import Path
from camera_schema import (
    CAMERA_STYLES,
    VALID_CAMERA_STYLES,
    DEFAULT_CAMERA_STYLE,
    MOVEMENT_SPEEDS,
    CUT_PRESETS,
    SHAKE_PRESETS,
    DEFAULT_SHAKE_PRESET,
    LIGHTING_PRESET_TO_STYLE,
    SCENE_TYPE_TO_LIGHTING,
)

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[CAMERA_DIRECTOR] Blender non disponible - mode test")




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
        """Style HANDHELD: shake procédural via Noise modifier sur F-Curves rotation."""
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
        
        self.camera_obj.location = base_pos
        self.camera_obj.keyframe_insert(data_path="location", frame=frame_start)
        
        self.setup_camera_constraints(track_target=True)
        
        # --- Shake preset from camera_schema ---
        shake_name = config.get("shake_preset", DEFAULT_SHAKE_PRESET)
        if shake_name not in SHAKE_PRESETS:
            self.log(f"Shake preset '{shake_name}' inconnu, fallback '{DEFAULT_SHAKE_PRESET}'")
            shake_name = DEFAULT_SHAKE_PRESET
        shake = SHAKE_PRESETS[shake_name]
        
        # Apply Noise modifier on rotation_euler F-Curves
        self._apply_noise_shake(shake, frame_start, frame_end)
        
        self.set_fov(40)
        self.operations.append({
            "action": "style", "type": "handheld",
            "base_pos": base_pos, "shake_preset": shake_name,
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
    
    def _apply_noise_shake(self, shake_preset: dict, frame_start: int, frame_end: int):
        """Applique un Noise modifier sur les F-Curves de rotation/location."""
        if not BLENDER_AVAILABLE or not self.camera_obj:
            return
        
        # Ensure animation data exists
        if not self.camera_obj.animation_data:
            self.camera_obj.animation_data_create()
        if not self.camera_obj.animation_data.action:
            self.camera_obj.animation_data.action = bpy.data.actions.new(
                name=f"{self.camera_obj.name}_Action"
            )
        
        action = self.camera_obj.animation_data.action
        
        for axis_path in shake_preset["axes"]:
            # rotation_euler has 3 channels (X, Y, Z)
            num_channels = 3
            for channel_idx in range(num_channels):
                # Find or create the F-Curve
                fcurve = action.fcurves.find(axis_path, index=channel_idx)
                if fcurve is None:
                    fcurve = action.fcurves.new(data_path=axis_path, index=channel_idx)
                    # Insert a base keyframe so the fcurve exists
                    fcurve.keyframe_points.insert(frame_start, 0.0)
                
                # Add Noise modifier
                noise_mod = fcurve.modifiers.new(type='NOISE')
                noise_mod.strength = shake_preset["strength"]
                noise_mod.scale = shake_preset["scale"]
                noise_mod.phase = shake_preset["phase"] + channel_idx * 33.0
                noise_mod.offset = shake_preset["offset"]
                noise_mod.depth = shake_preset["depth"]
                noise_mod.use_restricted_range = True
                noise_mod.frame_start = float(frame_start)
                noise_mod.frame_end = float(frame_end)
                noise_mod.blend_in = 10.0
                noise_mod.blend_out = 10.0
        
        self.debug(f"Noise shake appliqué: axes={shake_preset['axes']}, strength={shake_preset['strength']}")
    
    def apply_style(self, style: str, config: dict, frame_start: int, frame_end: int):
        """Applique le style caméra demandé."""
        style = style.lower()
        
        if style not in VALID_CAMERA_STYLES:
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
        elif style == "matchmove":
            self.apply_style_matchmove(config, frame_start, frame_end)
    
    def apply_style_matchmove(self, config: dict, frame_start: int, frame_end: int):
        """Style MATCHMOVE: reproduit la caméra source via fSpy perspective lock."""
        self.log("Application style: MATCHMOVE")
        
        if not BLENDER_AVAILABLE:
            return
        
        from fspy_tracker import FspyTracker
        
        json_path = config.get("fov_json_path", None)
        if not json_path:
            self.log("ERREUR: fov_json_path requis pour le style matchmove")
            return
        
        tracker = FspyTracker(verbose=self.verbose)
        result = tracker.process(self.camera_obj, json_path)
        
        # Position camera at scene center, looking at target
        center = self.get_scene_center()
        bounds = self.get_scene_bounds()
        distance = max(bounds) * 2.0
        
        self.camera_obj.location = (
            center[0] + distance * 0.7,
            center[1] - distance * 0.7,
            center[2] + distance * 0.3
        )
        
        self.setup_camera_constraints(track_target=True)
        
        self.operations.append({
            "action": "style", "type": "matchmove",
            "fspy_result": result,
            "frames": [frame_start, frame_end]
        })
    
    def check_frustum(self) -> dict:
        """Vérifie si l'avatar (armature/mesh principal) est dans le champ de la caméra.
        Retourne un dict avec 'in_frustum' bool et 'details'."""
        if not BLENDER_AVAILABLE or not self.camera_obj:
            return {"in_frustum": True, "details": "Blender indisponible — check simulé"}
        
        scene = bpy.context.scene
        cam = self.camera_obj
        
        # Find the main subject (armature or actor mesh)
        subject = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                subject = obj
                break
        if subject is None:
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and 'actor' in obj.name.lower():
                    subject = obj
                    break
        
        if subject is None:
            self.log("WARN: Aucun sujet trouvé pour le frustum check")
            return {"in_frustum": True, "details": "no_subject_found"}
        
        # Get subject center in camera normalized coords
        subject_world = subject.matrix_world.translation
        cam_matrix = cam.matrix_world.normalized().inverted()
        subject_cam = cam_matrix @ subject_world
        
        # Check if behind camera (negative Z in camera space = in front)
        if subject_cam.z > 0:
            self.log(f"ALERTE FRUSTUM: '{subject.name}' est DERRIÈRE la caméra!")
            return {"in_frustum": False, "details": "behind_camera", "subject": subject.name}
        
        # Project to normalized device coordinates
        cam_data = cam.data
        frame = cam_data.view_frame(scene=scene)
        frame = [cam_matrix @ (cam.matrix_world @ v) for v in frame]
        
        # Simple bounds check using angle
        half_fov = cam_data.angle / 2
        angle_to_subject = math.atan2(
            math.sqrt(subject_cam.x**2 + subject_cam.y**2),
            abs(subject_cam.z)
        )
        
        margin = 1.2  # 20% margin
        in_frustum = angle_to_subject < (half_fov * margin)
        
        if not in_frustum:
            self.log(f"ALERTE FRUSTUM: '{subject.name}' est HORS CHAMP!")
        else:
            self.debug(f"Frustum OK: '{subject.name}' dans le champ")
        
        result = {
            "in_frustum": in_frustum,
            "subject": subject.name,
            "angle_to_subject_deg": math.degrees(angle_to_subject),
            "half_fov_deg": math.degrees(half_fov),
        }
        self.operations.append({"action": "check_frustum", **result})
        return result
    
    def get_operations(self) -> list:
        return self.operations


def setup_scene_from_config(config: dict, output_dir: str, scene_id: str, verbose: bool = False, res_x: int = 1920, res_y: int = 1080):
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

    # -- Resolution + sensor_fit selon format de sortie
    if BLENDER_AVAILABLE:
        scene = bpy.context.scene
        scene.render.resolution_x = res_x
        scene.render.resolution_y = res_y
        scene.render.resolution_percentage = 100
        director.log(f"Resolution : {res_x}x{res_y}")
    
    camera_config = config.get("camera", {})
    style = camera_config.get("style", DEFAULT_CAMERA_STYLE)
    
    director.apply_style(style, camera_config, frame_start, frame_end)

    # -- sensor_fit : adapte le cadrage camera vertical/horizontal
    if BLENDER_AVAILABLE and director.camera:
        director.camera.sensor_fit = 'VERTICAL' if res_y > res_x else 'HORIZONTAL'
        director.log(f"sensor_fit : {director.camera.sensor_fit} ({res_x}x{res_y})")
    
    cuts = camera_config.get("cuts", [])
    if cuts:
        from cuts_engine import CutsEngine
        cuts_engine = CutsEngine(director.camera_obj, director.target, verbose=verbose)
        cuts_engine.process_cuts(cuts, frame_start, frame_end)
        director.operations.extend(cuts_engine.get_operations())
    
    from lighting_rig import LightingRig
    lighting = LightingRig(verbose=verbose)
    lighting_config = config.get("lighting", {})
    scene_type = config.get("scene_type", "")

    # Priorité 1 : style explicite dans le config (override manuel)
    if lighting_config.get("style"):
        light_style = lighting_config["style"]
        color_temp  = lighting_config.get("color_temp", 5500)
        intensity   = lighting_config.get("intensity", 1.0)
        director.log(f"Éclairage explicite : style={light_style}")

    # Priorité 2 : scene_type produit par layer_assembler v2.1.0 (U03)
    elif scene_type and scene_type in SCENE_TYPE_TO_LIGHTING:
        profile     = SCENE_TYPE_TO_LIGHTING[scene_type]
        light_style = profile["style"]
        color_temp  = profile["color_temp"]
        intensity   = profile["intensity"]
        director.log(f"Éclairage auto (scene_type={scene_type}) : style={light_style}")

    # Priorité 3 : preset_id de Gemini M1 (PRODUCTION_PLAN.JSON)
    elif lighting_config.get("preset_id"):
        light_style = LIGHTING_PRESET_TO_STYLE.get(lighting_config["preset_id"], "3point")
        color_temp  = lighting_config.get("color_temp", 5500)
        intensity   = lighting_config.get("intensity", 1.0)
        director.log(f"Éclairage preset ({lighting_config['preset_id']}) → style={light_style}")

    # Fallback universel
    else:
        light_style = "3point"
        color_temp  = 5500
        intensity   = 1.0
        director.log("Éclairage fallback : 3point")

    lighting.apply_style(light_style, intensity, color_temp)
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
    parser.add_argument('--scene-id', required=True, help='ID de la scene')
    parser.add_argument('--res-x', type=int, default=1920, help='Resolution largeur (defaut: 1920)')
    parser.add_argument('--res-y', type=int, default=1080, help='Resolution hauteur (defaut: 1080)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logs detailles')
    
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
        verbose=args.verbose,
        res_x=args.res_x,
        res_y=args.res_y,
    )
    
    print(f"\n[CAMERA_DIRECTOR] Opérations effectuées: {len(operations)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
