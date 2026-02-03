#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   SOCKETING ENGINE — EXODUS LOGISTICS                        ║
║               Attachement Props aux Bones via Contraintes                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Script Blender headless pour attacher les props aux bones de l'armature.
Utilise des contraintes Child Of pour un attachement dynamique.

Usage (appelé par EXO_02_LOGISTICS.py):
    blender --background actor.blend --python socketing_engine.py -- \\
        --production-plan plan.json \\
        --props-mapping '{"gun": "/path/to/gun.glb"}' \\
        --output-dir /path/to/output \\
        --output-name actor_equipped
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import bpy
    import mathutils
except ImportError:
    print("ERROR: Ce script doit être exécuté dans Blender")
    sys.exit(1)


SOCKET_MAPPING = {
    "hand_right": [
        "hand.R", "RightHand", "Hand_R", "mixamorig:RightHand",
        "RightHand", "hand_r", "r_hand", "Bip01_R_Hand",
        "DEF-hand.R", "ORG-hand.R"
    ],
    "hand_left": [
        "hand.L", "LeftHand", "Hand_L", "mixamorig:LeftHand",
        "LeftHand", "hand_l", "l_hand", "Bip01_L_Hand",
        "DEF-hand.L", "ORG-hand.L"
    ],
    "back": [
        "spine.003", "Spine3", "UpperBack", "spine3",
        "mixamorig:Spine2", "Bip01_Spine2", "DEF-spine.003"
    ],
    "head": [
        "head", "Head", "mixamorig:Head", "Bip01_Head",
        "DEF-head", "ORG-head"
    ],
    "hip_holster": [
        "pelvis", "Hips", "mixamorig:Hips", "Bip01_Pelvis",
        "DEF-pelvis", "hips", "hip"
    ],
    "chest": [
        "spine.002", "Spine2", "Chest", "chest",
        "mixamorig:Spine1", "Bip01_Spine1", "DEF-spine.002"
    ],
    "shoulder_right": [
        "shoulder.R", "RightShoulder", "mixamorig:RightShoulder",
        "Bip01_R_Clavicle", "DEF-shoulder.R"
    ],
    "shoulder_left": [
        "shoulder.L", "LeftShoulder", "mixamorig:LeftShoulder",
        "Bip01_L_Clavicle", "DEF-shoulder.L"
    ],
    "foot_right": [
        "foot.R", "RightFoot", "mixamorig:RightFoot",
        "Bip01_R_Foot", "DEF-foot.R"
    ],
    "foot_left": [
        "foot.L", "LeftFoot", "mixamorig:LeftFoot",
        "Bip01_L_Foot", "DEF-foot.L"
    ]
}

SOCKET_OFFSETS = {
    "hand_right": (0.0, 0.0, 0.0),
    "hand_left": (0.0, 0.0, 0.0),
    "back": (0.0, 0.1, 0.0),
    "head": (0.0, 0.1, 0.0),
    "hip_holster": (0.15, 0.0, -0.05),
    "chest": (0.0, 0.0, 0.0),
    "shoulder_right": (0.0, 0.0, 0.0),
    "shoulder_left": (0.0, 0.0, 0.0),
    "foot_right": (0.0, 0.0, 0.0),
    "foot_left": (0.0, 0.0, 0.0)
}


class SocketingEngine:
    """Engine d'attachement des props aux bones."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.armature = None
        self.bone_cache: Dict[str, str] = {}
        self.attached_props: List[Dict] = []
    
    def _log(self, msg: str):
        print(f"[SOCKETING] {msg}")
    
    def _debug(self, msg: str):
        if self.verbose:
            print(f"[SOCKETING:DEBUG] {msg}")
    
    def find_armature(self) -> Optional[Any]:
        """Trouve l'armature principale dans la scène."""
        armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
        
        if not armatures:
            self._log("ERROR: Aucune armature trouvée dans la scène")
            return None
        
        if len(armatures) == 1:
            self.armature = armatures[0]
        else:
            self.armature = max(armatures, key=lambda a: len(a.data.bones))
            self._log(f"Multiple armatures trouvées, utilisation de: {self.armature.name}")
        
        self._log(f"Armature: {self.armature.name} ({len(self.armature.data.bones)} bones)")
        return self.armature
    
    def resolve_bone_name(self, socket_name: str) -> Optional[str]:
        """
        Résout un nom de socket en nom de bone réel.
        Utilise le cache pour éviter les recherches répétées.
        """
        if socket_name in self.bone_cache:
            return self.bone_cache[socket_name]
        
        if self.armature is None:
            self.find_armature()
        
        if self.armature is None:
            return None
        
        bone_names = [bone.name for bone in self.armature.data.bones]
        
        if socket_name in SOCKET_MAPPING:
            for candidate in SOCKET_MAPPING[socket_name]:
                if candidate in bone_names:
                    self.bone_cache[socket_name] = candidate
                    self._debug(f"Socket '{socket_name}' -> Bone '{candidate}'")
                    return candidate
        
        if socket_name in bone_names:
            self.bone_cache[socket_name] = socket_name
            return socket_name
        
        for bone_name in bone_names:
            if socket_name.lower() in bone_name.lower():
                self.bone_cache[socket_name] = bone_name
                self._log(f"Fuzzy match: '{socket_name}' -> '{bone_name}'")
                return bone_name
        
        self._log(f"WARN: Bone non trouvé pour socket '{socket_name}'")
        return None
    
    def attach_prop_to_bone(
        self,
        prop_obj: Any,
        bone_name: str,
        offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> bool:
        """
        Attache un prop à un bone via contrainte Child Of.
        """
        if self.armature is None:
            self._log("ERROR: Pas d'armature définie")
            return False
        
        if bone_name not in self.armature.data.bones:
            self._log(f"ERROR: Bone '{bone_name}' introuvable dans l'armature")
            return False
        
        for c in prop_obj.constraints:
            if c.type == 'CHILD_OF' and c.target == self.armature:
                prop_obj.constraints.remove(c)
        
        constraint = prop_obj.constraints.new('CHILD_OF')
        constraint.name = f"Socket_{bone_name}"
        constraint.target = self.armature
        constraint.subtarget = bone_name
        
        constraint.use_scale_x = False
        constraint.use_scale_y = False
        constraint.use_scale_z = False
        
        prop_obj.matrix_world = mathutils.Matrix.Identity(4)
        
        with bpy.context.temp_override(object=prop_obj):
            bpy.ops.constraint.childof_set_inverse(
                constraint=constraint.name,
                owner='OBJECT'
            )
        
        prop_obj.location = offset
        
        import math
        prop_obj.rotation_euler = (
            math.radians(rotation[0]),
            math.radians(rotation[1]),
            math.radians(rotation[2])
        )
        
        prop_obj.scale = scale
        
        self.attached_props.append({
            "prop": prop_obj.name,
            "bone": bone_name,
            "constraint": constraint.name
        })
        
        self._log(f"Attached: {prop_obj.name} -> {bone_name}")
        return True
    
    def attach_to_socket(
        self,
        prop_obj: Any,
        socket_name: str,
        custom_offset: Optional[Tuple[float, float, float]] = None,
        custom_rotation: Optional[Tuple[float, float, float]] = None,
        custom_scale: Optional[Tuple[float, float, float]] = None
    ) -> bool:
        """
        Attache un prop à un socket nommé (hand_right, back, etc.).
        """
        bone_name = self.resolve_bone_name(socket_name)
        
        if bone_name is None:
            self._log(f"WARN: Cannot attach to socket '{socket_name}' - bone not found")
            return False
        
        offset = custom_offset or SOCKET_OFFSETS.get(socket_name, (0.0, 0.0, 0.0))
        rotation = custom_rotation or (0.0, 0.0, 0.0)
        scale = custom_scale or (1.0, 1.0, 1.0)
        
        return self.attach_prop_to_bone(prop_obj, bone_name, offset, rotation, scale)
    
    def detach_prop(self, prop_obj: Any):
        """Détache un prop de son bone (supprime la contrainte)."""
        constraints_to_remove = [c for c in prop_obj.constraints if c.type == 'CHILD_OF']
        
        for constraint in constraints_to_remove:
            prop_obj.constraints.remove(constraint)
        
        self.attached_props = [a for a in self.attached_props if a["prop"] != prop_obj.name]
        self._log(f"Detached: {prop_obj.name}")
    
    def list_available_sockets(self) -> Dict[str, str]:
        """Liste tous les sockets disponibles avec leur bone résolu."""
        available = {}
        
        for socket_name in SOCKET_MAPPING.keys():
            bone = self.resolve_bone_name(socket_name)
            if bone:
                available[socket_name] = bone
        
        return available
    
    def list_armature_bones(self) -> List[str]:
        """Liste tous les bones de l'armature."""
        if self.armature is None:
            self.find_armature()
        
        if self.armature is None:
            return []
        
        return [bone.name for bone in self.armature.data.bones]
    
    def get_attachment_report(self) -> List[Dict]:
        """Retourne le rapport des attachements effectués."""
        return self.attached_props.copy()


def import_prop(filepath: str, prop_id: str) -> Optional[Any]:
    """Importe un prop et retourne l'objet principal."""
    path = Path(filepath)
    ext = path.suffix.lower()
    
    existing_objects = set(bpy.data.objects.keys())
    
    if ext in [".glb", ".gltf"]:
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext == ".blend":
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            data_to.objects = list(data_from.objects)
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=filepath)
    else:
        print(f"[SOCKETING] Unsupported format: {ext}")
        return None
    
    new_objects = [obj for obj in bpy.data.objects if obj.name not in existing_objects]
    
    if not new_objects:
        return None
    
    meshes = [obj for obj in new_objects if obj.type == 'MESH']
    main_obj = meshes[0] if meshes else new_objects[0]
    
    main_obj.name = f"PROP_{prop_id}"
    for i, obj in enumerate(new_objects):
        if obj != main_obj:
            obj.name = f"PROP_{prop_id}_{i:02d}"
    
    return main_obj


def process_production_plan(
    plan: Dict,
    props_mapping: Dict[str, str],
    engine: SocketingEngine,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Traite le PRODUCTION_PLAN.JSON et attache tous les props.
    Retourne un rapport des opérations.
    """
    from timeline_manager import TimelineManager
    
    timeline = TimelineManager(verbose=verbose)
    loaded_props: Dict[str, Any] = {}
    operations = []
    
    for scene in plan.get("scenes", []):
        scene_id = scene.get("scene_id", "unknown")
        
        for action in scene.get("props_actions", []):
            prop_id = action.get("prop_id")
            socket = action.get("socket", "hand_right")
            frame = action.get("frame", 1)
            action_type = action.get("action", "GRAB")
            
            if prop_id not in loaded_props:
                if prop_id in props_mapping:
                    prop_obj = import_prop(props_mapping[prop_id], prop_id)
                    if prop_obj:
                        loaded_props[prop_id] = prop_obj
                        prop_obj.hide_viewport = True
                        prop_obj.hide_render = True
                        prop_obj.keyframe_insert('hide_viewport', frame=0)
                        prop_obj.keyframe_insert('hide_render', frame=0)
                        print(f"[SOCKETING] Loaded prop: {prop_id}")
            
            prop_obj = loaded_props.get(prop_id)
            
            if prop_obj is None:
                print(f"[SOCKETING] WARN: Prop not found: {prop_id}")
                operations.append({
                    "scene_id": scene_id,
                    "frame": frame,
                    "action": action_type,
                    "prop_id": prop_id,
                    "status": "SKIPPED",
                    "reason": "Prop not loaded"
                })
                continue
            
            if action_type == "GRAB":
                success = engine.attach_to_socket(prop_obj, socket)
                
                if success:
                    timeline.show_prop(prop_obj, frame)
                    timeline.activate_constraint(prop_obj, frame)
                
                operations.append({
                    "scene_id": scene_id,
                    "frame": frame,
                    "action": action_type,
                    "prop_id": prop_id,
                    "socket": socket,
                    "status": "SUCCESS" if success else "FAILED"
                })
                
            elif action_type == "DROP":
                timeline.deactivate_constraint(prop_obj, frame)
                
                operations.append({
                    "scene_id": scene_id,
                    "frame": frame,
                    "action": action_type,
                    "prop_id": prop_id,
                    "status": "SUCCESS"
                })
                
            elif action_type == "HIDE":
                timeline.hide_prop(prop_obj, frame)
                
                operations.append({
                    "scene_id": scene_id,
                    "frame": frame,
                    "action": action_type,
                    "prop_id": prop_id,
                    "status": "SUCCESS"
                })
            
            elif action_type == "SWITCH_SOCKET":
                new_socket = action.get("new_socket", socket)
                timeline.deactivate_constraint(prop_obj, frame - 1)
                
                success = engine.attach_to_socket(prop_obj, new_socket)
                if success:
                    timeline.activate_constraint(prop_obj, frame)
                
                operations.append({
                    "scene_id": scene_id,
                    "frame": frame,
                    "action": action_type,
                    "prop_id": prop_id,
                    "old_socket": socket,
                    "new_socket": new_socket,
                    "status": "SUCCESS" if success else "FAILED"
                })
    
    return {
        "loaded_props": list(loaded_props.keys()),
        "operations": operations,
        "attachments": engine.get_attachment_report()
    }


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    parser = argparse.ArgumentParser(description='Blender Socketing Engine')
    parser.add_argument('--production-plan', required=True, help='Path to PRODUCTION_PLAN.JSON')
    parser.add_argument('--props-mapping', required=True, help='JSON string of prop_id -> filepath mapping')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--output-name', default='actor_equipped', help='Output filename (without extension)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args(argv)
    
    print("=" * 60)
    print("   SOCKETING ENGINE — EXODUS LOGISTICS")
    print("=" * 60)
    
    with open(args.production_plan, 'r', encoding='utf-8') as f:
        plan = json.load(f)
    
    props_mapping = json.loads(args.props_mapping)
    
    print(f"[SOCKETING] Plan loaded: {len(plan.get('scenes', []))} scenes")
    print(f"[SOCKETING] Props mapping: {len(props_mapping)} props")
    
    engine = SocketingEngine(verbose=args.verbose)
    armature = engine.find_armature()
    
    if armature is None:
        print("[SOCKETING] ERROR: No armature found, aborting")
        sys.exit(1)
    
    available_sockets = engine.list_available_sockets()
    print(f"[SOCKETING] Available sockets: {list(available_sockets.keys())}")
    
    report = process_production_plan(plan, props_mapping, engine, args.verbose)
    
    print(f"[SOCKETING] Operations completed: {len(report['operations'])}")
    
    from final_baker import bake_and_export, save_blend_backup
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    
    abc_path = output_dir / f"{args.output_name}.abc"
    blend_path = output_dir / f"{args.output_name}.blend"
    
    print(f"[SOCKETING] Exporting Alembic: {abc_path}")
    bake_and_export(str(abc_path), frame_start, frame_end)
    
    print(f"[SOCKETING] Saving Blend backup: {blend_path}")
    save_blend_backup(str(blend_path))
    
    print("\n" + "=" * 60)
    print("   SOCKETING ENGINE — COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
