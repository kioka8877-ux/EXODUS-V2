#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  TIMELINE MANAGER — EXODUS LOGISTICS                         ║
║             Gestion Visibilité et Animation des Props                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour gérer la visibilité des props sur la timeline Blender.
Gère les keyframes de hide_viewport, hide_render et influence des contraintes.
"""

from typing import List, Dict, Optional, Any, Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


class TimelineManager:
    """Gestionnaire de timeline pour les props."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.keyframe_log: List[Dict] = []
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[TIMELINE] {msg}")
    
    def _add_keyframe_log(self, obj_name: str, property_name: str, frame: int, value: Any):
        """Enregistre un keyframe dans le log."""
        self.keyframe_log.append({
            "object": obj_name,
            "property": property_name,
            "frame": frame,
            "value": value
        })
    
    def hide_prop(self, prop_obj: Any, frame: int):
        """
        Cache un prop à partir d'une frame donnée.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        prop_obj.hide_viewport = True
        prop_obj.hide_render = True
        
        prop_obj.keyframe_insert('hide_viewport', frame=frame)
        prop_obj.keyframe_insert('hide_render', frame=frame)
        
        self._add_keyframe_log(prop_obj.name, 'hide_viewport', frame, True)
        self._add_keyframe_log(prop_obj.name, 'hide_render', frame, True)
        
        self._log(f"Hide: {prop_obj.name} @ frame {frame}")
    
    def show_prop(self, prop_obj: Any, frame: int):
        """
        Montre un prop à partir d'une frame donnée.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        if frame > 1:
            prop_obj.hide_viewport = True
            prop_obj.hide_render = True
            prop_obj.keyframe_insert('hide_viewport', frame=frame - 1)
            prop_obj.keyframe_insert('hide_render', frame=frame - 1)
        
        prop_obj.hide_viewport = False
        prop_obj.hide_render = False
        
        prop_obj.keyframe_insert('hide_viewport', frame=frame)
        prop_obj.keyframe_insert('hide_render', frame=frame)
        
        self._set_keyframe_interpolation(prop_obj, 'hide_viewport', 'CONSTANT')
        self._set_keyframe_interpolation(prop_obj, 'hide_render', 'CONSTANT')
        
        self._add_keyframe_log(prop_obj.name, 'hide_viewport', frame, False)
        self._add_keyframe_log(prop_obj.name, 'hide_render', frame, False)
        
        self._log(f"Show: {prop_obj.name} @ frame {frame}")
    
    def activate_constraint(self, prop_obj: Any, frame: int, constraint_name: Optional[str] = None):
        """
        Active la contrainte Child Of à une frame donnée.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        constraints = self._get_child_of_constraints(prop_obj, constraint_name)
        
        for constraint in constraints:
            if frame > 1:
                constraint.influence = 0.0
                constraint.keyframe_insert('influence', frame=frame - 1)
            
            constraint.influence = 1.0
            constraint.keyframe_insert('influence', frame=frame)
            
            self._set_constraint_interpolation(prop_obj, constraint.name, 'CONSTANT')
            
            self._add_keyframe_log(prop_obj.name, f'constraint:{constraint.name}:influence', frame, 1.0)
            self._log(f"Activate constraint: {prop_obj.name}.{constraint.name} @ frame {frame}")
    
    def deactivate_constraint(self, prop_obj: Any, frame: int, constraint_name: Optional[str] = None):
        """
        Désactive la contrainte Child Of à une frame donnée.
        Le prop "tombe" et conserve sa position world.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        constraints = self._get_child_of_constraints(prop_obj, constraint_name)
        
        for constraint in constraints:
            constraint.influence = 0.0
            constraint.keyframe_insert('influence', frame=frame)
            
            self._add_keyframe_log(prop_obj.name, f'constraint:{constraint.name}:influence', frame, 0.0)
            self._log(f"Deactivate constraint: {prop_obj.name}.{constraint.name} @ frame {frame}")
    
    def _get_child_of_constraints(self, prop_obj: Any, constraint_name: Optional[str] = None) -> List[Any]:
        """Récupère les contraintes Child Of d'un objet."""
        constraints = []
        
        for constraint in prop_obj.constraints:
            if constraint.type == 'CHILD_OF':
                if constraint_name is None or constraint.name == constraint_name:
                    constraints.append(constraint)
        
        return constraints
    
    def _set_keyframe_interpolation(self, obj: Any, data_path: str, interpolation: str):
        """Définit l'interpolation des keyframes pour une propriété."""
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == data_path:
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = interpolation
    
    def _set_constraint_interpolation(self, obj: Any, constraint_name: str, interpolation: str):
        """Définit l'interpolation pour une contrainte."""
        data_path = f'constraints["{constraint_name}"].influence'
        self._set_keyframe_interpolation(obj, data_path, interpolation)
    
    def apply_prop_timeline(self, prop_obj: Any, events: List[Dict]):
        """
        Applique une séquence d'événements timeline à un prop.
        
        events = [
            {"frame": 100, "action": "GRAB"},
            {"frame": 250, "action": "DROP"},
            {"frame": 300, "action": "HIDE"}
        ]
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        prop_obj.hide_viewport = True
        prop_obj.hide_render = True
        prop_obj.keyframe_insert('hide_viewport', frame=0)
        prop_obj.keyframe_insert('hide_render', frame=0)
        
        for constraint in self._get_child_of_constraints(prop_obj):
            constraint.influence = 0.0
            constraint.keyframe_insert('influence', frame=0)
        
        for event in sorted(events, key=lambda e: e.get("frame", 0)):
            frame = event.get("frame", 1)
            action = event.get("action", "").upper()
            
            if action == "GRAB":
                self.show_prop(prop_obj, frame)
                self.activate_constraint(prop_obj, frame)
                
            elif action == "DROP":
                self.deactivate_constraint(prop_obj, frame)
                
            elif action == "HIDE":
                self.hide_prop(prop_obj, frame)
                
            elif action == "SHOW":
                self.show_prop(prop_obj, frame)
                
            else:
                self._log(f"Unknown action: {action}")
    
    def create_visibility_animation(
        self,
        prop_obj: Any,
        visible_ranges: List[Tuple[int, int]]
    ):
        """
        Crée une animation de visibilité basée sur des plages de frames.
        
        visible_ranges = [(100, 200), (300, 400)]
        Le prop sera visible uniquement pendant ces plages.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        prop_obj.hide_viewport = True
        prop_obj.hide_render = True
        prop_obj.keyframe_insert('hide_viewport', frame=0)
        prop_obj.keyframe_insert('hide_render', frame=0)
        
        sorted_ranges = sorted(visible_ranges, key=lambda r: r[0])
        
        for start, end in sorted_ranges:
            self.show_prop(prop_obj, start)
            self.hide_prop(prop_obj, end + 1)
        
        self._log(f"Created visibility animation for {prop_obj.name}: {len(visible_ranges)} ranges")
    
    def get_keyframe_log(self) -> List[Dict]:
        """Retourne le log de tous les keyframes créés."""
        return self.keyframe_log.copy()
    
    def clear_prop_animation(self, prop_obj: Any):
        """Supprime toutes les animations d'un prop."""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        if prop_obj.animation_data:
            prop_obj.animation_data_clear()
        
        for constraint in prop_obj.constraints:
            if constraint.animation_data:
                constraint.animation_data_clear()
        
        self._log(f"Cleared animation: {prop_obj.name}")
    
    def get_frame_range(self) -> Tuple[int, int]:
        """Retourne la plage de frames de la scène."""
        if not BLENDER_AVAILABLE:
            return (1, 250)
        
        scene = bpy.context.scene
        return (scene.frame_start, scene.frame_end)
    
    def set_frame_range(self, start: int, end: int):
        """Définit la plage de frames de la scène."""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        scene = bpy.context.scene
        scene.frame_start = start
        scene.frame_end = end
        
        self._log(f"Frame range set: {start} - {end}")


def apply_events_from_plan(plan: Dict, loaded_props: Dict[str, Any], verbose: bool = False):
    """
    Applique les événements du PRODUCTION_PLAN aux props chargés.
    """
    timeline = TimelineManager(verbose=verbose)
    
    prop_events: Dict[str, List[Dict]] = {}
    
    for scene in plan.get("scenes", []):
        for action in scene.get("props_actions", []):
            prop_id = action.get("prop_id")
            if prop_id:
                if prop_id not in prop_events:
                    prop_events[prop_id] = []
                prop_events[prop_id].append(action)
    
    for prop_id, events in prop_events.items():
        if prop_id in loaded_props:
            timeline.apply_prop_timeline(loaded_props[prop_id], events)
    
    return timeline.get_keyframe_log()


if __name__ == "__main__":
    print("Timeline Manager - EXODUS LOGISTICS")
    print("Ce module doit être importé dans Blender.")
    
    print("\nExemple d'utilisation:")
    print("""
    from timeline_manager import TimelineManager
    
    timeline = TimelineManager(verbose=True)
    
    # Montrer un prop à la frame 100
    timeline.show_prop(prop_obj, frame=100)
    
    # Activer la contrainte d'attachement
    timeline.activate_constraint(prop_obj, frame=100)
    
    # Désactiver (drop) à la frame 250
    timeline.deactivate_constraint(prop_obj, frame=250)
    
    # Cacher le prop
    timeline.hide_prop(prop_obj, frame=300)
    """)
