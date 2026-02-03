#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CUTS ENGINE — EXODUS PHOTOGRAPHY                           ║
║              Système de Cuts Automatiques et Transitions Caméra              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Gère les transitions de caméra (cuts) définies dans le PRODUCTION_PLAN.
Types supportés: wide, medium, closeup, extreme_closeup, dutch_angle

Usage (appelé par camera_director.py):
    cuts_engine = CutsEngine(camera_obj, target, verbose=True)
    cuts_engine.process_cuts(cuts_list, frame_start, frame_end)
"""

import math
import random
from typing import Optional

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


CUT_PRESETS = {
    "wide": {
        "fov": 60,
        "distance_mult": 2.5,
        "height_offset": 0.2,
        "roll": 0
    },
    "medium": {
        "fov": 50,
        "distance_mult": 1.5,
        "height_offset": 0.1,
        "roll": 0
    },
    "closeup": {
        "fov": 35,
        "distance_mult": 0.8,
        "height_offset": 0.05,
        "roll": 0
    },
    "extreme_closeup": {
        "fov": 25,
        "distance_mult": 0.4,
        "height_offset": 0.02,
        "roll": 0
    },
    "dutch_angle": {
        "fov": 45,
        "distance_mult": 1.2,
        "height_offset": 0.15,
        "roll": 15
    },
    "low_angle": {
        "fov": 50,
        "distance_mult": 1.8,
        "height_offset": -0.5,
        "roll": 0
    },
    "high_angle": {
        "fov": 50,
        "distance_mult": 1.8,
        "height_offset": 0.8,
        "roll": 0
    },
    "over_shoulder": {
        "fov": 40,
        "distance_mult": 0.6,
        "height_offset": 0.1,
        "roll": 0,
        "offset_x": 0.3
    }
}

TRANSITION_TYPES = {
    "cut": {"blend_frames": 0},
    "smooth": {"blend_frames": 15},
    "fast": {"blend_frames": 5},
    "slow": {"blend_frames": 30}
}


class CutsEngine:
    """Moteur de cuts et transitions caméra."""
    
    def __init__(self, camera_obj, target_obj, verbose: bool = False):
        self.camera_obj = camera_obj
        self.target_obj = target_obj
        self.verbose = verbose
        self.operations = []
        self.base_distance = 5.0
        self.scene_center = (0, 0, 1)
        
        if BLENDER_AVAILABLE:
            self._calculate_scene_metrics()
    
    def log(self, msg: str):
        print(f"[CUTS_ENGINE] {msg}")
        self.operations.append({"action": "log", "message": msg})
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[CUTS_ENGINE:DEBUG] {msg}")
    
    def _calculate_scene_metrics(self):
        """Calcule les métriques de la scène pour positionner la caméra."""
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
            dist = (obj.location - center).length
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ mathutils.Vector(corner)
                corner_dist = (world_corner - center).length
                max_dist = max(max_dist, corner_dist)
        
        self.base_distance = max_dist * 1.5
        self.debug(f"Scene metrics: center={self.scene_center}, base_dist={self.base_distance}")
    
    def get_cut_preset(self, cut_type: str) -> dict:
        """Retourne le preset pour un type de cut."""
        cut_type = cut_type.lower()
        if cut_type in CUT_PRESETS:
            return CUT_PRESETS[cut_type].copy()
        else:
            self.log(f"Cut type '{cut_type}' inconnu, fallback vers 'medium'")
            return CUT_PRESETS["medium"].copy()
    
    def calculate_camera_position(self, preset: dict, angle_variation: float = 0) -> tuple:
        """Calcule la position caméra pour un preset donné."""
        distance = self.base_distance * preset["distance_mult"]
        height = self.scene_center[2] + self.base_distance * preset["height_offset"]
        
        base_angle = -math.pi / 4 + angle_variation
        
        offset_x = preset.get("offset_x", 0) * self.base_distance
        
        pos = (
            self.scene_center[0] + distance * math.cos(base_angle) + offset_x,
            self.scene_center[1] + distance * math.sin(base_angle),
            max(height, 0.5)
        )
        
        return pos
    
    def apply_cut(self, frame: int, cut_type: str, transition: str = "cut"):
        """Applique un cut à la frame spécifiée."""
        if not BLENDER_AVAILABLE or not self.camera_obj:
            return
        
        preset = self.get_cut_preset(cut_type)
        
        angle_var = random.uniform(-0.3, 0.3)
        position = self.calculate_camera_position(preset, angle_var)
        
        trans_config = TRANSITION_TYPES.get(transition, TRANSITION_TYPES["cut"])
        blend_frames = trans_config["blend_frames"]
        
        if blend_frames > 0:
            self.camera_obj.keyframe_insert(data_path="location", frame=frame - blend_frames)
        
        self.camera_obj.location = position
        self.camera_obj.keyframe_insert(data_path="location", frame=frame)
        
        if self.camera_obj.data:
            self.camera_obj.data.angle = math.radians(preset["fov"])
            self.camera_obj.data.keyframe_insert(data_path="angle", frame=frame)
        
        if preset["roll"] != 0:
            roll_rad = math.radians(preset["roll"])
            self.camera_obj.rotation_euler[2] = roll_rad
            self.camera_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        if blend_frames > 0:
            self._set_interpolation(frame - blend_frames, frame)
        
        self.debug(f"Cut appliqué: frame={frame}, type={cut_type}, pos={position}")
        self.operations.append({
            "action": "cut",
            "frame": frame,
            "type": cut_type,
            "transition": transition,
            "position": position,
            "fov": preset["fov"]
        })
    
    def _set_interpolation(self, frame_start: int, frame_end: int, interp_type: str = 'BEZIER'):
        """Configure l'interpolation entre deux keyframes."""
        if not BLENDER_AVAILABLE or not self.camera_obj.animation_data:
            return
        
        action = self.camera_obj.animation_data.action
        if not action:
            return
        
        for fcurve in action.fcurves:
            for kf in fcurve.keyframe_points:
                if frame_start <= kf.co.x <= frame_end:
                    kf.interpolation = interp_type
                    kf.handle_left_type = 'AUTO_CLAMPED'
                    kf.handle_right_type = 'AUTO_CLAMPED'
    
    def create_markers(self, cuts: list):
        """Crée des markers Blender pour chaque cut."""
        if not BLENDER_AVAILABLE:
            return
        
        for marker in list(bpy.context.scene.timeline_markers):
            if marker.name.startswith("CUT_"):
                bpy.context.scene.timeline_markers.remove(marker)
        
        for i, cut in enumerate(cuts):
            frame = cut.get("frame", 0)
            cut_type = cut.get("type", "medium")
            marker_name = f"CUT_{i+1}_{cut_type}"
            
            marker = bpy.context.scene.timeline_markers.new(marker_name, frame=frame)
            self.debug(f"Marker créé: {marker_name} @ frame {frame}")
        
        self.operations.append({
            "action": "markers_created",
            "count": len(cuts)
        })
    
    def process_cuts(self, cuts: list, frame_start: int, frame_end: int):
        """Traite la liste complète des cuts."""
        if not cuts:
            self.log("Aucun cut défini, caméra statique sur toute la durée")
            return
        
        self.log(f"Traitement de {len(cuts)} cuts")
        
        self.create_markers(cuts)
        
        sorted_cuts = sorted(cuts, key=lambda x: x.get("frame", 0))
        
        for i, cut in enumerate(sorted_cuts):
            frame = cut.get("frame", 0)
            cut_type = cut.get("type", "medium")
            transition = cut.get("transition", "smooth" if i > 0 else "cut")
            
            if frame < frame_start:
                frame = frame_start
            elif frame > frame_end:
                self.debug(f"Cut frame {frame} hors range, ignoré")
                continue
            
            self.apply_cut(frame, cut_type, transition)
        
        self.log(f"Cuts traités: {len(sorted_cuts)}")
    
    def generate_auto_cuts(self, frame_start: int, frame_end: int, 
                           interval: int = 120, variety: bool = True) -> list:
        """Génère automatiquement des cuts à intervalle régulier."""
        cuts = []
        
        cut_types = list(CUT_PRESETS.keys())
        
        frame = frame_start
        i = 0
        
        while frame <= frame_end:
            if variety:
                cut_type = cut_types[i % len(cut_types)]
            else:
                cut_type = "medium" if i % 2 == 0 else "wide"
            
            cuts.append({
                "frame": frame,
                "type": cut_type,
                "transition": "cut" if i == 0 else "smooth"
            })
            
            frame += interval + random.randint(-20, 20) if variety else interval
            i += 1
        
        self.log(f"Auto-cuts générés: {len(cuts)} cuts à ~{interval} frames d'intervalle")
        return cuts
    
    def get_operations(self) -> list:
        return self.operations


def test_cuts_engine():
    """Fonction de test hors Blender."""
    print("=== Test CutsEngine ===")
    
    engine = CutsEngine(None, None, verbose=True)
    
    cuts = [
        {"frame": 0, "type": "wide"},
        {"frame": 120, "type": "medium"},
        {"frame": 240, "type": "closeup"},
        {"frame": 360, "type": "dutch_angle"}
    ]
    
    print(f"\nPresets disponibles: {list(CUT_PRESETS.keys())}")
    
    for cut in cuts:
        preset = engine.get_cut_preset(cut["type"])
        print(f"\nCut '{cut['type']}' @ frame {cut['frame']}:")
        print(f"  FOV: {preset['fov']}°")
        print(f"  Distance mult: {preset['distance_mult']}")
        print(f"  Roll: {preset['roll']}°")


if __name__ == "__main__":
    test_cuts_engine()
