#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   AUTO DOF — EXODUS PHOTOGRAPHY                             ║
║              Pilier B : Profondeur de Champ Automatique (Bust Bone)         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Crée un Empty parenté au bone du buste de l'avatar, puis configure le DOF
de la caméra pour focaliser sur cet Empty.

Usage (appelé par le pipeline U04):
    blender --background env.blend --python auto_dof.py
"""

from typing import Dict, List, Optional

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[AUTO_DOF] Blender non disponible - mode test")

from camera_schema import (
    CameraSchema,
    BUST_BONE_CHAIN,
    DEFAULT_FSTOP,
)


class AutoDOF:
    """Gère la création du DOF target parenté au bust bone de l'avatar."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.schema = CameraSchema()
        self.operations: list = []

    def log(self, msg: str) -> None:
        print(f"[AUTO_DOF] {msg}")
        self.operations.append({"action": "log", "message": msg})

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[AUTO_DOF:DEBUG] {msg}")

    def get_operations(self) -> list:
        return self.operations

    def find_armature(self) -> Optional[object]:
        """Cherche la première armature dans la scène Blender."""
        if not BLENDER_AVAILABLE:
            self.log("Blender indisponible — recherche armature simulée")
            return None

        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                self.log(f"Armature trouvée : {obj.name}")
                self.operations.append({
                    "action": "find_armature",
                    "armature": obj.name,
                })
                return obj

        self.log("Aucune armature trouvée dans la scène")
        return None

    def find_bust_bone(self, armature: object) -> Optional[str]:
        """Cherche le bone du buste via la chaîne BUST_BONE_CHAIN du schema."""
        if not BLENDER_AVAILABLE:
            self.log("Blender indisponible — recherche bust bone simulée")
            return None

        bone_names = [bone.name for bone in armature.data.bones]
        self.debug(f"Bones disponibles ({len(bone_names)}) : {bone_names[:10]}...")

        bone_name = self.schema.find_bust_bone(bone_names)
        if bone_name:
            self.log(f"Bust bone trouvé : {bone_name}")
            self.operations.append({
                "action": "find_bust_bone",
                "bone_name": bone_name,
                "searched_chain": len(BUST_BONE_CHAIN),
            })
        else:
            self.log(f"Aucun bust bone trouvé (chaîne de {len(BUST_BONE_CHAIN)} candidats)")
        return bone_name

    def create_dof_empty(
        self,
        armature: object,
        bone_name: str,
        name: str = "EXODUS_DOF_Target",
    ) -> Optional[object]:
        """Crée un Empty parenté au bone du buste pour servir de DOF target."""
        if not BLENDER_AVAILABLE:
            self.log(f"Blender indisponible — création Empty '{name}' simulée")
            self.operations.append({
                "action": "create_dof_empty",
                "name": name,
                "bone_name": bone_name,
                "simulated": True,
            })
            return None

        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'CROSS'
        empty.empty_display_size = 0.2
        bpy.context.scene.collection.objects.link(empty)

        empty.parent = armature
        empty.parent_type = 'BONE'
        empty.parent_bone = bone_name

        self.log(f"Empty DOF créé : '{name}' parenté à '{bone_name}'")
        self.operations.append({
            "action": "create_dof_empty",
            "name": name,
            "bone_name": bone_name,
            "parent_armature": armature.name,
        })
        return empty

    def apply_dof(
        self,
        camera_obj: object,
        dof_target: object,
        f_stop: float = DEFAULT_FSTOP,
    ) -> None:
        """Configure le DOF de la caméra pour focaliser sur le target Empty."""
        if not BLENDER_AVAILABLE:
            self.log(f"Blender indisponible — DOF simulé (f/{f_stop})")
            self.operations.append({
                "action": "apply_dof",
                "f_stop": f_stop,
                "simulated": True,
            })
            return

        camera_obj.data.dof.use_dof = True
        camera_obj.data.dof.focus_object = dof_target
        camera_obj.data.dof.aperture_fstop = f_stop

        self.log(f"DOF activé : focus_object='{dof_target.name}', f/{f_stop}")
        self.operations.append({
            "action": "apply_dof",
            "focus_object": dof_target.name,
            "f_stop": f_stop,
        })

    def process(self, camera_obj: object) -> dict:
        """Pipeline complet : armature → bust bone → empty → DOF."""
        self.log("=== Pipeline Auto-DOF ===")

        armature = self.find_armature()
        if armature is None:
            self.log("WARN : Aucune armature — DOF non appliqué")
            return {
                "success": False,
                "reason": "no_armature",
                "operations_count": len(self.operations),
            }

        bone_name = self.find_bust_bone(armature)
        if bone_name is None:
            self.log("WARN : Aucun bust bone — DOF non appliqué")
            return {
                "success": False,
                "reason": "no_bust_bone",
                "operations_count": len(self.operations),
            }

        empty = self.create_dof_empty(armature, bone_name)

        if BLENDER_AVAILABLE and empty is not None:
            self.apply_dof(camera_obj, empty, DEFAULT_FSTOP)

        summary = {
            "success": True,
            "armature": armature.name if BLENDER_AVAILABLE else "simulated",
            "bone_name": bone_name,
            "empty_name": empty.name if (BLENDER_AVAILABLE and empty) else "EXODUS_DOF_Target",
            "f_stop": DEFAULT_FSTOP,
            "operations_count": len(self.operations),
        }
        self.log(f"Pipeline terminé : bone='{bone_name}', f/{DEFAULT_FSTOP}")
        return summary


# =============================================================================
# STANDALONE TEST — exécution hors Blender
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   AUTO DOF — TEST STANDALONE")
    print("=" * 60)

    schema = CameraSchema()

    passed = 0
    total = 3

    # --- TEST 1 : Bust bone trouvé (mixamorig:Spine2) ---
    bones_with_match = ["Root", "Hips", "mixamorig:Spine2", "Head"]
    found = schema.find_bust_bone(bones_with_match)
    t1_ok = found == "mixamorig:Spine2"
    if t1_ok:
        passed += 1
    print(f"\n[TEST 1] find_bust_bone({bones_with_match})")
    print(f"         → '{found}' {'✓' if t1_ok else '✗'}")

    # --- TEST 2 : Bust bone absent ---
    bones_no_match = ["Root", "Hips", "Head", "LeftHand"]
    not_found = schema.find_bust_bone(bones_no_match)
    t2_ok = not_found is None
    if t2_ok:
        passed += 1
    print(f"[TEST 2] find_bust_bone({bones_no_match})")
    print(f"         → {not_found} {'✓' if t2_ok else '✗'}")

    # --- TEST 3 : Vérification DEFAULT_FSTOP et chaîne ---
    t3_ok = DEFAULT_FSTOP == 2.8 and len(BUST_BONE_CHAIN) == 16
    if t3_ok:
        passed += 1
    print(f"[TEST 3] DEFAULT_FSTOP={DEFAULT_FSTOP}, BUST_BONE_CHAIN={len(BUST_BONE_CHAIN)} entries")
    print(f"         {'✓' if t3_ok else '✗'}")

    dof = AutoDOF(verbose=True)
    print(f"\n--- Simulation process() sans Blender ---")
    result = dof.process(None)
    print(f"Résultat : {result}")

    print(f"\n{'=' * 60}")
    print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
    print(f"{'=' * 60}")
