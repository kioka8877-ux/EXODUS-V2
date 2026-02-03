#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 KEYFRAME ANIMATOR — EXODUS PHOTOGRAPHY                        ║
║              Animation Caméra Fluide par Keyframes avec Easing               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Génère des keyframes caméra fluides avec interpolation Bezier et easing.
Supporte: ease_in, ease_out, ease_in_out, linear

Usage:
    animator = KeyframeAnimator(camera_obj, verbose=True)
    animator.animate_path(path_points, frame_start, frame_end, easing="ease_in_out")
"""

import math
from typing import List, Tuple, Optional

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


EASING_FUNCTIONS = {
    "linear": lambda t: t,
    "ease_in": lambda t: t * t,
    "ease_out": lambda t: 1 - (1 - t) * (1 - t),
    "ease_in_out": lambda t: 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2,
    "ease_in_cubic": lambda t: t * t * t,
    "ease_out_cubic": lambda t: 1 - pow(1 - t, 3),
    "ease_in_out_cubic": lambda t: 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2,
    "ease_in_expo": lambda t: 0 if t == 0 else pow(2, 10 * t - 10),
    "ease_out_expo": lambda t: 1 if t == 1 else 1 - pow(2, -10 * t),
    "bounce": lambda t: _bounce_ease_out(t)
}

def _bounce_ease_out(t: float) -> float:
    """Fonction bounce pour easing."""
    n1 = 7.5625
    d1 = 2.75
    
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


class KeyframeAnimator:
    """Anime la caméra avec des keyframes fluides."""
    
    def __init__(self, camera_obj=None, verbose: bool = False):
        self.camera_obj = camera_obj
        self.verbose = verbose
        self.operations = []
    
    def log(self, msg: str):
        print(f"[KEYFRAME_ANIMATOR] {msg}")
        self.operations.append({"action": "log", "message": msg})
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[KEYFRAME_ANIMATOR:DEBUG] {msg}")
    
    def lerp(self, a: float, b: float, t: float) -> float:
        """Interpolation linéaire."""
        return a + (b - a) * t
    
    def lerp_vector(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolation linéaire pour vecteurs."""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))
    
    def get_easing_function(self, name: str):
        """Retourne la fonction d'easing par nom."""
        return EASING_FUNCTIONS.get(name, EASING_FUNCTIONS["ease_in_out"])
    
    def catmull_rom_spline(self, p0: tuple, p1: tuple, p2: tuple, p3: tuple, t: float) -> tuple:
        """Interpolation Catmull-Rom pour courbes lisses."""
        t2 = t * t
        t3 = t2 * t
        
        result = []
        for i in range(len(p0)):
            v = 0.5 * (
                (2 * p1[i]) +
                (-p0[i] + p2[i]) * t +
                (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 +
                (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3
            )
            result.append(v)
        
        return tuple(result)
    
    def bezier_curve(self, p0: tuple, p1: tuple, p2: tuple, p3: tuple, t: float) -> tuple:
        """Courbe de Bézier cubique."""
        u = 1 - t
        u2 = u * u
        u3 = u2 * u
        t2 = t * t
        t3 = t2 * t
        
        result = []
        for i in range(len(p0)):
            v = (u3 * p0[i] + 
                 3 * u2 * t * p1[i] + 
                 3 * u * t2 * p2[i] + 
                 t3 * p3[i])
            result.append(v)
        
        return tuple(result)
    
    def insert_keyframe(self, frame: int, location: tuple = None, 
                        rotation: tuple = None, fov: float = None):
        """Insère un keyframe sur la caméra."""
        if not BLENDER_AVAILABLE or not self.camera_obj:
            self.operations.append({
                "action": "keyframe",
                "frame": frame,
                "location": location,
                "rotation": rotation,
                "fov": fov
            })
            return
        
        if location:
            self.camera_obj.location = location
            self.camera_obj.keyframe_insert(data_path="location", frame=frame)
        
        if rotation:
            self.camera_obj.rotation_euler = rotation
            self.camera_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        if fov and self.camera_obj.data:
            self.camera_obj.data.angle = math.radians(fov)
            self.camera_obj.data.keyframe_insert(data_path="angle", frame=frame)
        
        self.debug(f"Keyframe @ {frame}: loc={location}, rot={rotation}, fov={fov}")
    
    def set_keyframe_interpolation(self, interpolation: str = 'BEZIER'):
        """Configure l'interpolation sur tous les keyframes."""
        if not BLENDER_AVAILABLE or not self.camera_obj:
            return
        
        if not self.camera_obj.animation_data or not self.camera_obj.animation_data.action:
            return
        
        action = self.camera_obj.animation_data.action
        
        for fcurve in action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = interpolation
                kf.handle_left_type = 'AUTO_CLAMPED'
                kf.handle_right_type = 'AUTO_CLAMPED'
        
        self.debug(f"Interpolation définie: {interpolation}")
    
    def animate_linear(self, start_pos: tuple, end_pos: tuple,
                       frame_start: int, frame_end: int,
                       easing: str = "ease_in_out"):
        """Animation linéaire entre deux points avec easing."""
        self.log(f"Animation linéaire: {frame_start} → {frame_end}, easing={easing}")
        
        ease_func = self.get_easing_function(easing)
        total_frames = frame_end - frame_start
        
        num_keyframes = max(2, min(total_frames // 10, 20))
        
        for i in range(num_keyframes + 1):
            t = i / num_keyframes
            eased_t = ease_func(t)
            
            frame = frame_start + int(t * total_frames)
            position = self.lerp_vector(start_pos, end_pos, eased_t)
            
            self.insert_keyframe(frame, location=position)
        
        self.set_keyframe_interpolation('BEZIER')
        
        self.operations.append({
            "action": "animate_linear",
            "start": start_pos,
            "end": end_pos,
            "frames": [frame_start, frame_end],
            "easing": easing,
            "keyframes_count": num_keyframes + 1
        })
    
    def animate_path(self, path_points: List[tuple], 
                     frame_start: int, frame_end: int,
                     easing: str = "ease_in_out",
                     use_catmull_rom: bool = True):
        """Animation le long d'un chemin avec plusieurs points."""
        if len(path_points) < 2:
            self.log("Chemin insuffisant (< 2 points)")
            return
        
        self.log(f"Animation path: {len(path_points)} points, easing={easing}")
        
        ease_func = self.get_easing_function(easing)
        total_frames = frame_end - frame_start
        
        num_keyframes = max(len(path_points), min(total_frames // 5, 50))
        
        if use_catmull_rom and len(path_points) >= 4:
            extended_points = [path_points[0]] + path_points + [path_points[-1]]
            num_segments = len(path_points) - 1
            
            for i in range(num_keyframes + 1):
                t = i / num_keyframes
                eased_t = ease_func(t)
                
                segment_float = eased_t * num_segments
                segment_idx = min(int(segment_float), num_segments - 1)
                local_t = segment_float - segment_idx
                
                p0 = extended_points[segment_idx]
                p1 = extended_points[segment_idx + 1]
                p2 = extended_points[segment_idx + 2]
                p3 = extended_points[segment_idx + 3]
                
                position = self.catmull_rom_spline(p0, p1, p2, p3, local_t)
                frame = frame_start + int(t * total_frames)
                
                self.insert_keyframe(frame, location=position)
        else:
            segment_length = 1.0 / (len(path_points) - 1)
            
            for i in range(num_keyframes + 1):
                t = i / num_keyframes
                eased_t = ease_func(t)
                
                segment_idx = min(int(eased_t / segment_length), len(path_points) - 2)
                local_t = (eased_t - segment_idx * segment_length) / segment_length
                
                position = self.lerp_vector(
                    path_points[segment_idx],
                    path_points[segment_idx + 1],
                    local_t
                )
                
                frame = frame_start + int(t * total_frames)
                self.insert_keyframe(frame, location=position)
        
        self.set_keyframe_interpolation('BEZIER')
        
        self.operations.append({
            "action": "animate_path",
            "points_count": len(path_points),
            "frames": [frame_start, frame_end],
            "easing": easing,
            "keyframes_count": num_keyframes + 1
        })
    
    def animate_orbit(self, center: tuple, radius: float, height: float,
                      frame_start: int, frame_end: int,
                      start_angle: float = 0, rotation_amount: float = math.pi,
                      easing: str = "ease_in_out"):
        """Animation orbitale autour d'un centre."""
        self.log(f"Animation orbit: angle={math.degrees(rotation_amount)}°, easing={easing}")
        
        ease_func = self.get_easing_function(easing)
        total_frames = frame_end - frame_start
        
        num_keyframes = max(8, min(total_frames // 10, 30))
        
        for i in range(num_keyframes + 1):
            t = i / num_keyframes
            eased_t = ease_func(t)
            
            angle = start_angle + rotation_amount * eased_t
            
            position = (
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle),
                height
            )
            
            frame = frame_start + int(t * total_frames)
            self.insert_keyframe(frame, location=position)
        
        self.set_keyframe_interpolation('BEZIER')
        
        self.operations.append({
            "action": "animate_orbit",
            "center": center,
            "radius": radius,
            "rotation_degrees": math.degrees(rotation_amount),
            "frames": [frame_start, frame_end],
            "easing": easing
        })
    
    def animate_zoom(self, start_fov: float, end_fov: float,
                     frame_start: int, frame_end: int,
                     easing: str = "ease_in_out"):
        """Animation du FOV (zoom)."""
        self.log(f"Animation zoom: {start_fov}° → {end_fov}°")
        
        ease_func = self.get_easing_function(easing)
        total_frames = frame_end - frame_start
        
        num_keyframes = max(2, min(total_frames // 15, 10))
        
        for i in range(num_keyframes + 1):
            t = i / num_keyframes
            eased_t = ease_func(t)
            
            fov = self.lerp(start_fov, end_fov, eased_t)
            frame = frame_start + int(t * total_frames)
            
            self.insert_keyframe(frame, fov=fov)
        
        self.operations.append({
            "action": "animate_zoom",
            "start_fov": start_fov,
            "end_fov": end_fov,
            "frames": [frame_start, frame_end],
            "easing": easing
        })
    
    def animate_crane_shot(self, start_pos: tuple, end_pos: tuple,
                           frame_start: int, frame_end: int,
                           arc_height: float = 2.0,
                           easing: str = "ease_in_out"):
        """Animation crane shot (mouvement vertical en arc)."""
        self.log(f"Crane shot: arc_height={arc_height}")
        
        mid_pos = (
            (start_pos[0] + end_pos[0]) / 2,
            (start_pos[1] + end_pos[1]) / 2,
            max(start_pos[2], end_pos[2]) + arc_height
        )
        
        control1 = (
            start_pos[0] + (mid_pos[0] - start_pos[0]) * 0.5,
            start_pos[1] + (mid_pos[1] - start_pos[1]) * 0.5,
            start_pos[2] + arc_height * 0.7
        )
        
        control2 = (
            end_pos[0] + (mid_pos[0] - end_pos[0]) * 0.5,
            end_pos[1] + (mid_pos[1] - end_pos[1]) * 0.5,
            end_pos[2] + arc_height * 0.7
        )
        
        ease_func = self.get_easing_function(easing)
        total_frames = frame_end - frame_start
        num_keyframes = max(8, min(total_frames // 8, 25))
        
        for i in range(num_keyframes + 1):
            t = i / num_keyframes
            eased_t = ease_func(t)
            
            position = self.bezier_curve(start_pos, control1, control2, end_pos, eased_t)
            frame = frame_start + int(t * total_frames)
            
            self.insert_keyframe(frame, location=position)
        
        self.set_keyframe_interpolation('BEZIER')
        
        self.operations.append({
            "action": "animate_crane",
            "start": start_pos,
            "end": end_pos,
            "arc_height": arc_height,
            "frames": [frame_start, frame_end],
            "easing": easing
        })
    
    def get_operations(self) -> list:
        return self.operations


def test_keyframe_animator():
    """Fonction de test hors Blender."""
    print("=== Test KeyframeAnimator ===")
    
    animator = KeyframeAnimator(verbose=True)
    
    print(f"\nFonctions d'easing disponibles: {list(EASING_FUNCTIONS.keys())}")
    
    print("\n--- Test interpolations ---")
    for easing in ["linear", "ease_in", "ease_out", "ease_in_out"]:
        func = animator.get_easing_function(easing)
        values = [func(t/10) for t in range(11)]
        print(f"{easing}: {[round(v, 2) for v in values]}")
    
    print("\n--- Test animation linéaire ---")
    animator.animate_linear(
        start_pos=(0, 0, 0),
        end_pos=(10, 5, 2),
        frame_start=0,
        frame_end=100,
        easing="ease_in_out"
    )
    
    print("\n--- Test animation path ---")
    path = [(0, 0, 1), (5, 2, 1.5), (10, 0, 2), (15, -2, 1.5), (20, 0, 1)]
    animator.animate_path(path, frame_start=0, frame_end=200)
    
    print(f"\nTotal opérations: {len(animator.get_operations())}")


if __name__ == "__main__":
    test_keyframe_animator()
