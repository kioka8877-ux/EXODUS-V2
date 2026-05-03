#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                ACTOR ASSEMBLY — EXODUS LOGISTICS                             ║
║        Fusion : SocketingEngine + TimelineManager (Codex v6 D-II)           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module unifié issu de la fusion de socketing_engine.py et timeline_manager.py.
Décret D-II (Codex v6) : réduction de la complexité de maintenance.

Interface externe identique — aucun notebook cassé.
socketing_engine.py et timeline_manager.py restent comme thin wrappers.

Classes:
    SocketingEngine   — Attachement props → bones via contrainte Child Of
    TimelineManager   — Visibilité et animation des props sur la timeline

Fonctions:
    import_prop()               — Import multi-format (.glb/.fbx/.blend/.obj)
    process_production_plan()   — Pipeline complet socketing + timeline
    apply_events_from_plan()    — Application événements timeline depuis le plan
"""

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

ACTOR_ASSEMBLY_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# SOCKET MAPPING — correspondance socket logique → noms de bones candidats
# ---------------------------------------------------------------------------

SOCKET_MAPPING: Dict[str, List[str]] = {
    "hand_right": [
        "hand.R", "RightHand", "Hand_R", "mixamorig:RightHand",
        "hand_r", "r_hand", "Bip01_R_Hand", "DEF-hand.R", "ORG-hand.R",
    ],
    "hand_left": [
        "hand.L", "LeftHand", "Hand_L", "mixamorig:LeftHand",
        "hand_l", "l_hand", "Bip01_L_Hand", "DEF-hand.L", "ORG-hand.L",
    ],
    "back": [
        "spine.003", "Spine3", "UpperBack", "spine3",
        "mixamorig:Spine2", "Bip01_Spine2", "DEF-spine.003",
    ],
    "head": [
        "head", "Head", "mixamorig:Head", "Bip01_Head",
        "DEF-head", "ORG-head",
    ],
    "hip_holster": [
        "pelvis", "Hips", "mixamorig:Hips", "Bip01_Pelvis",
        "DEF-pelvis", "hips", "hip",
    ],
    "chest": [
        "spine.002", "Spine2", "Chest", "chest",
        "mixamorig:Spine1", "Bip01_Spine1", "DEF-spine.002",
    ],
    "shoulder_right": [
        "shoulder.R", "RightShoulder", "mixamorig:RightShoulder",
        "Bip01_R_Clavicle", "DEF-shoulder.R",
    ],
    "shoulder_left": [
        "shoulder.L", "LeftShoulder", "mixamorig:LeftShoulder",
        "Bip01_L_Clavicle", "DEF-shoulder.L",
    ],
    "foot_right": [
        "foot.R", "RightFoot", "mixamorig:RightFoot",
        "Bip01_R_Foot", "DEF-foot.R",
    ],
    "foot_left": [
        "foot.L", "LeftFoot", "mixamorig:LeftFoot",
        "Bip01_L_Foot", "DEF-foot.L",
    ],
}

SOCKET_OFFSETS: Dict[str, Tuple[float, float, float]] = {
    "hand_right":    (0.0,  0.0,   0.0),
    "hand_left":     (0.0,  0.0,   0.0),
    "back":          (0.0,  0.1,   0.0),
    "head":          (0.0,  0.1,   0.0),
    "hip_holster":   (0.15, 0.0,  -0.05),
    "chest":         (0.0,  0.0,   0.0),
    "shoulder_right":(0.0,  0.0,   0.0),
    "shoulder_left": (0.0,  0.0,   0.0),
    "foot_right":    (0.0,  0.0,   0.0),
    "foot_left":     (0.0,  0.0,   0.0),
}


# ===========================================================================
# SOCKETING ENGINE
# ===========================================================================

class SocketingEngine:
    """
    Engine d'attachement des props aux bones de l'armature.
    Inclut D-I : validation pré-socketing (Codex v6).
    """

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
        armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]

        if not armatures:
            self._log("ERROR: Aucune armature trouvée dans la scène")
            return None

        self.armature = (
            armatures[0]
            if len(armatures) == 1
            else max(armatures, key=lambda a: len(a.data.bones))
        )
        if len(armatures) > 1:
            self._log(f"Multiple armatures — utilisation de : {self.armature.name}")

        self._log(f"Armature : {self.armature.name} ({len(self.armature.data.bones)} bones)")
        return self.armature

    def resolve_bone_name(self, socket_name: str) -> Optional[str]:
        """Résout un socket logique en nom de bone réel (avec cache)."""
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
                    self._debug(f"Socket '{socket_name}' → bone '{candidate}'")
                    return candidate

        if socket_name in bone_names:
            self.bone_cache[socket_name] = socket_name
            return socket_name

        for bone_name in bone_names:
            if socket_name.lower() in bone_name.lower():
                self.bone_cache[socket_name] = bone_name
                self._log(f"Fuzzy match : '{socket_name}' → '{bone_name}'")
                return bone_name

        self._log(f"WARN : bone non trouvé pour socket '{socket_name}'")
        return None

    # ------------------------------------------------------------------
    # D-I — Validation pré-socketing (Codex v6)
    # ------------------------------------------------------------------

    def validate_sockets_for_plan(self, plan: Dict) -> Tuple[List[str], List[str]]:
        """
        D-I (Codex v6) — Validation pré-socketing.
        Vérifie que chaque socket requis dans le plan peut être résolu vers
        un bone réel AVANT de commencer tout attachement.

        Lève ValueError avec rapport détaillé si des sockets sont introuvables.
        Retourne (valid_sockets, missing_sockets).
        """
        if self.armature is None:
            self.find_armature()
        if self.armature is None:
            raise ValueError("[SOCKETING] VALIDATION ÉCHOUÉE : aucune armature dans la scène.")

        required_sockets: List[str] = []
        for scene in plan.get("scenes", []):
            for action in scene.get("props_actions", []):
                socket = action.get("socket", "hand_right")
                if socket not in required_sockets:
                    required_sockets.append(socket)

        valid_sockets: List[str] = []
        missing_sockets: List[str] = []

        for socket in required_sockets:
            bone = self.resolve_bone_name(socket)
            if bone:
                valid_sockets.append(socket)
                self._debug(f"  ✓ socket '{socket}' → bone '{bone}'")
            else:
                missing_sockets.append(socket)
                self._log(f"  ✗ socket '{socket}' → BONE INTROUVABLE")

        if missing_sockets:
            available_bones = self.list_armature_bones()
            known_sockets = list(SOCKET_MAPPING.keys())
            raise ValueError(
                f"[SOCKETING] VALIDATION PRÉ-SOCKETING ÉCHOUÉE — "
                f"{len(missing_sockets)} socket(s) non résolu(s) :\n"
                + "\n".join(f"  - '{s}'" for s in missing_sockets)
                + f"\n\nBones disponibles dans '{self.armature.name}' "
                f"({len(available_bones)}) :\n"
                + "  " + ", ".join(available_bones[:20])
                + (" ..." if len(available_bones) > 20 else "")
                + f"\n\nSockets connus : {', '.join(known_sockets)}"
                + "\n\nAction requise : ajouter les sockets manquants dans SOCKET_MAPPING "
                "ou corriger les noms de socket dans PRODUCTION_PLAN.JSON."
            )

        self._log(
            f"Validation pré-socketing : {len(valid_sockets)}/{len(required_sockets)} "
            "sockets résolus — OK"
        )
        return valid_sockets, missing_sockets

    # ------------------------------------------------------------------
    # Attachement
    # ------------------------------------------------------------------

    def attach_prop_to_bone(
        self,
        prop_obj: Any,
        bone_name: str,
        offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> bool:
        """Attache un prop à un bone via contrainte Child Of."""
        if self.armature is None:
            self._log("ERROR : pas d'armature définie")
            return False
        if bone_name not in self.armature.data.bones:
            self._log(f"ERROR : bone '{bone_name}' introuvable dans l'armature")
            return False

        for c in prop_obj.constraints:
            if c.type == "CHILD_OF" and c.target == self.armature:
                prop_obj.constraints.remove(c)

        constraint = prop_obj.constraints.new("CHILD_OF")
        constraint.name = f"Socket_{bone_name}"
        constraint.target = self.armature
        constraint.subtarget = bone_name
        constraint.use_scale_x = False
        constraint.use_scale_y = False
        constraint.use_scale_z = False

        prop_obj.matrix_world = mathutils.Matrix.Identity(4)
        with bpy.context.temp_override(object=prop_obj):
            bpy.ops.constraint.childof_set_inverse(
                constraint=constraint.name, owner="OBJECT"
            )

        prop_obj.location = offset
        prop_obj.rotation_euler = (
            math.radians(rotation[0]),
            math.radians(rotation[1]),
            math.radians(rotation[2]),
        )
        prop_obj.scale = scale

        self.attached_props.append(
            {"prop": prop_obj.name, "bone": bone_name, "constraint": constraint.name}
        )
        self._log(f"Attached : {prop_obj.name} → {bone_name}")
        return True

    def attach_to_socket(
        self,
        prop_obj: Any,
        socket_name: str,
        custom_offset: Optional[Tuple[float, float, float]] = None,
        custom_rotation: Optional[Tuple[float, float, float]] = None,
        custom_scale: Optional[Tuple[float, float, float]] = None,
    ) -> bool:
        """Attache un prop à un socket nommé (hand_right, back, etc.)."""
        bone_name = self.resolve_bone_name(socket_name)
        if bone_name is None:
            self._log(f"WARN : impossible d'attacher à '{socket_name}' — bone non trouvé")
            return False

        offset = custom_offset or SOCKET_OFFSETS.get(socket_name, (0.0, 0.0, 0.0))
        rotation = custom_rotation or (0.0, 0.0, 0.0)
        scale = custom_scale or (1.0, 1.0, 1.0)
        return self.attach_prop_to_bone(prop_obj, bone_name, offset, rotation, scale)

    def detach_prop(self, prop_obj: Any):
        """Détache un prop de son bone (supprime la contrainte Child Of)."""
        for c in [c for c in prop_obj.constraints if c.type == "CHILD_OF"]:
            prop_obj.constraints.remove(c)
        self.attached_props = [a for a in self.attached_props if a["prop"] != prop_obj.name]
        self._log(f"Detached : {prop_obj.name}")

    def list_available_sockets(self) -> Dict[str, str]:
        """Liste les sockets disponibles avec leur bone résolu."""
        return {
            s: b
            for s in SOCKET_MAPPING
            if (b := self.resolve_bone_name(s)) is not None
        }

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


# ===========================================================================
# TIMELINE MANAGER
# ===========================================================================

class TimelineManager:
    """Gestionnaire de timeline pour la visibilité et l'animation des props."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.keyframe_log: List[Dict] = []

    def _log(self, msg: str):
        if self.verbose:
            print(f"[TIMELINE] {msg}")

    def _add_keyframe_log(self, obj_name: str, property_name: str, frame: int, value: Any):
        self.keyframe_log.append(
            {"object": obj_name, "property": property_name, "frame": frame, "value": value}
        )

    def hide_prop(self, prop_obj: Any, frame: int):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        prop_obj.hide_viewport = True
        prop_obj.hide_render = True
        prop_obj.keyframe_insert("hide_viewport", frame=frame)
        prop_obj.keyframe_insert("hide_render", frame=frame)
        self._add_keyframe_log(prop_obj.name, "hide_viewport", frame, True)
        self._add_keyframe_log(prop_obj.name, "hide_render", frame, True)
        self._log(f"Hide : {prop_obj.name} @ frame {frame}")

    def show_prop(self, prop_obj: Any, frame: int):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        if frame > 1:
            prop_obj.hide_viewport = True
            prop_obj.hide_render = True
            prop_obj.keyframe_insert("hide_viewport", frame=frame - 1)
            prop_obj.keyframe_insert("hide_render", frame=frame - 1)
        prop_obj.hide_viewport = False
        prop_obj.hide_render = False
        prop_obj.keyframe_insert("hide_viewport", frame=frame)
        prop_obj.keyframe_insert("hide_render", frame=frame)
        self._set_keyframe_interpolation(prop_obj, "hide_viewport", "CONSTANT")
        self._set_keyframe_interpolation(prop_obj, "hide_render", "CONSTANT")
        self._add_keyframe_log(prop_obj.name, "hide_viewport", frame, False)
        self._add_keyframe_log(prop_obj.name, "hide_render", frame, False)
        self._log(f"Show : {prop_obj.name} @ frame {frame}")

    def activate_constraint(
        self, prop_obj: Any, frame: int, constraint_name: Optional[str] = None
    ):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        for constraint in self._get_child_of_constraints(prop_obj, constraint_name):
            if frame > 1:
                constraint.influence = 0.0
                constraint.keyframe_insert("influence", frame=frame - 1)
            constraint.influence = 1.0
            constraint.keyframe_insert("influence", frame=frame)
            self._set_constraint_interpolation(prop_obj, constraint.name, "CONSTANT")
            self._add_keyframe_log(
                prop_obj.name, f"constraint:{constraint.name}:influence", frame, 1.0
            )
            self._log(f"Activate constraint : {prop_obj.name}.{constraint.name} @ {frame}")

    def deactivate_constraint(
        self, prop_obj: Any, frame: int, constraint_name: Optional[str] = None
    ):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        for constraint in self._get_child_of_constraints(prop_obj, constraint_name):
            constraint.influence = 0.0
            constraint.keyframe_insert("influence", frame=frame)
            self._add_keyframe_log(
                prop_obj.name, f"constraint:{constraint.name}:influence", frame, 0.0
            )
            self._log(f"Deactivate constraint : {prop_obj.name}.{constraint.name} @ {frame}")

    def _get_child_of_constraints(
        self, prop_obj: Any, constraint_name: Optional[str] = None
    ) -> List[Any]:
        return [
            c
            for c in prop_obj.constraints
            if c.type == "CHILD_OF" and (constraint_name is None or c.name == constraint_name)
        ]

    def _set_keyframe_interpolation(self, obj: Any, data_path: str, interpolation: str):
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == data_path:
                    for kp in fcurve.keyframe_points:
                        kp.interpolation = interpolation

    def _set_constraint_interpolation(
        self, obj: Any, constraint_name: str, interpolation: str
    ):
        self._set_keyframe_interpolation(
            obj, f'constraints["{constraint_name}"].influence', interpolation
        )

    def apply_prop_timeline(self, prop_obj: Any, events: List[Dict]):
        """Applique une séquence d'événements timeline à un prop."""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        prop_obj.hide_viewport = True
        prop_obj.hide_render = True
        prop_obj.keyframe_insert("hide_viewport", frame=0)
        prop_obj.keyframe_insert("hide_render", frame=0)
        for c in self._get_child_of_constraints(prop_obj):
            c.influence = 0.0
            c.keyframe_insert("influence", frame=0)

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
                self._log(f"Unknown action : {action}")

    def create_visibility_animation(
        self, prop_obj: Any, visible_ranges: List[Tuple[int, int]]
    ):
        """Crée une animation de visibilité à partir de plages de frames."""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        prop_obj.hide_viewport = True
        prop_obj.hide_render = True
        prop_obj.keyframe_insert("hide_viewport", frame=0)
        prop_obj.keyframe_insert("hide_render", frame=0)
        for start, end in sorted(visible_ranges, key=lambda r: r[0]):
            self.show_prop(prop_obj, start)
            self.hide_prop(prop_obj, end + 1)
        self._log(
            f"Created visibility animation for {prop_obj.name} : "
            f"{len(visible_ranges)} ranges"
        )

    def get_keyframe_log(self) -> List[Dict]:
        return self.keyframe_log.copy()

    def clear_prop_animation(self, prop_obj: Any):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        if prop_obj.animation_data:
            prop_obj.animation_data_clear()
        for c in prop_obj.constraints:
            if c.animation_data:
                c.animation_data_clear()
        self._log(f"Cleared animation : {prop_obj.name}")

    def get_frame_range(self) -> Tuple[int, int]:
        if not BLENDER_AVAILABLE:
            return (1, 250)
        scene = bpy.context.scene
        return (scene.frame_start, scene.frame_end)

    def set_frame_range(self, start: int, end: int):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        bpy.context.scene.frame_start = start
        bpy.context.scene.frame_end = end
        self._log(f"Frame range : {start} - {end}")


# ===========================================================================
# HELPERS PARTAGÉS
# ===========================================================================

def import_prop(filepath: str, prop_id: str) -> Optional[Any]:
    """Importe un prop depuis filepath et retourne l'objet principal."""
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
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
        print(f"[ACTOR_ASSEMBLY] Format non supporté : {ext}")
        return None

    new_objects = [obj for obj in bpy.data.objects if obj.name not in existing_objects]
    if not new_objects:
        return None

    meshes = [obj for obj in new_objects if obj.type == "MESH"]
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
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Pipeline complet : D-I validation → socketing → timeline.
    Retourne un rapport des opérations.
    """
    # D-I — Validation pré-socketing obligatoire
    engine.validate_sockets_for_plan(plan)

    timeline = TimelineManager(verbose=verbose)
    loaded_props: Dict[str, Any] = {}
    operations: List[Dict] = []

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
                        prop_obj.keyframe_insert("hide_viewport", frame=0)
                        prop_obj.keyframe_insert("hide_render", frame=0)
                        print(f"[ACTOR_ASSEMBLY] Loaded prop : {prop_id}")

            prop_obj = loaded_props.get(prop_id)

            if prop_obj is None:
                print(f"[ACTOR_ASSEMBLY] WARN : prop non trouvé : {prop_id}")
                operations.append(
                    {"scene_id": scene_id, "frame": frame, "action": action_type,
                     "prop_id": prop_id, "status": "SKIPPED", "reason": "Prop not loaded"}
                )
                continue

            if action_type == "GRAB":
                success = engine.attach_to_socket(prop_obj, socket)
                if success:
                    timeline.show_prop(prop_obj, frame)
                    timeline.activate_constraint(prop_obj, frame)
                operations.append(
                    {"scene_id": scene_id, "frame": frame, "action": action_type,
                     "prop_id": prop_id, "socket": socket,
                     "status": "SUCCESS" if success else "FAILED"}
                )

            elif action_type == "DROP":
                timeline.deactivate_constraint(prop_obj, frame)
                operations.append(
                    {"scene_id": scene_id, "frame": frame, "action": action_type,
                     "prop_id": prop_id, "status": "SUCCESS"}
                )

            elif action_type == "HIDE":
                timeline.hide_prop(prop_obj, frame)
                operations.append(
                    {"scene_id": scene_id, "frame": frame, "action": action_type,
                     "prop_id": prop_id, "status": "SUCCESS"}
                )

            elif action_type == "SWITCH_SOCKET":
                new_socket = action.get("new_socket", socket)
                timeline.deactivate_constraint(prop_obj, frame - 1)
                success = engine.attach_to_socket(prop_obj, new_socket)
                if success:
                    timeline.activate_constraint(prop_obj, frame)
                operations.append(
                    {"scene_id": scene_id, "frame": frame, "action": action_type,
                     "prop_id": prop_id, "old_socket": socket, "new_socket": new_socket,
                     "status": "SUCCESS" if success else "FAILED"}
                )

    return {
        "loaded_props": list(loaded_props.keys()),
        "operations": operations,
        "attachments": engine.get_attachment_report(),
    }


def apply_events_from_plan(
    plan: Dict, loaded_props: Dict[str, Any], verbose: bool = False
) -> List[Dict]:
    """Applique les événements timeline du PRODUCTION_PLAN aux props chargés."""
    timeline = TimelineManager(verbose=verbose)
    prop_events: Dict[str, List[Dict]] = {}

    for scene in plan.get("scenes", []):
        for action in scene.get("props_actions", []):
            prop_id = action.get("prop_id")
            if prop_id:
                prop_events.setdefault(prop_id, []).append(action)

    for prop_id, events in prop_events.items():
        if prop_id in loaded_props:
            timeline.apply_prop_timeline(loaded_props[prop_id], events)

    return timeline.get_keyframe_log()


# ---------------------------------------------------------------------------
# Exposition publique (backward-compat imports)
# ---------------------------------------------------------------------------

__all__ = [
    "SOCKET_MAPPING",
    "SOCKET_OFFSETS",
    "SocketingEngine",
    "TimelineManager",
    "import_prop",
    "process_production_plan",
    "apply_events_from_plan",
    "ACTOR_ASSEMBLY_VERSION",
]
