"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              BLENDER FUSION — Body + Face → Alembic Export                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Script Blender pour fusion Body + Face → Alembic.                           ║
║  Exécuté via: blender --background --python blender_fusion.py -- [args]      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import bpy
import json
import sys
import argparse
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

parser = argparse.ArgumentParser(description='Blender Fusion Script')
parser.add_argument('--body-fbx', required=True, help='Body motion FBX file')
parser.add_argument('--actor-blend', required=True, help='Actor .blend file')
parser.add_argument('--face-json', required=True, help='Facial data JSON')
parser.add_argument('--output', required=True, help='Output Alembic path')
parser.add_argument('--sync-offset', type=int, default=0, help='Sync offset in frames')
parser.add_argument('--smooth-window', type=int, default=5, help='Savitzky-Golay window')

args = parser.parse_args(argv)


def log(msg: str, level: str = "INFO"):
    """Logger formaté pour Blender."""
    print(f"[BLENDER:{level}] {msg}")


def clear_scene():
    """Nettoie complètement la scène Blender."""
    log("Nettoyage de la scène")
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.actions:
        if block.users == 0:
            bpy.data.actions.remove(block)


def import_body_fbx(fbx_path: str) -> bpy.types.Object:
    """Importe l'animation body depuis FBX."""
    log(f"Import FBX: {fbx_path}")
    
    if not Path(fbx_path).exists():
        log(f"FBX introuvable: {fbx_path}", "ERROR")
        return None
    
    bpy.ops.import_scene.fbx(
        filepath=fbx_path,
        use_anim=True,
        anim_offset=1.0,
        use_custom_normals=True,
        ignore_leaf_bones=True,
        automatic_bone_orientation=True
    )
    
    armature = None
    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
    
    if armature:
        log(f"Armature FBX importée: {armature.name}")
        
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            log(f"Action trouvée: {action.name} ({action.frame_range[0]}-{action.frame_range[1]})")
    else:
        log("Aucune armature trouvée dans le FBX", "WARN")
    
    return armature


def import_actor_blend(blend_path: str) -> bpy.types.Object:
    """Importe l'avatar depuis .blend."""
    log(f"Import Actor: {blend_path}")
    
    if not Path(blend_path).exists():
        log(f"Blend introuvable: {blend_path}", "ERROR")
        return None
    
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects
        data_to.armatures = data_from.armatures
        data_to.actions = data_from.actions
    
    actor_armature = None
    linked_objects = []
    
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            linked_objects.append(obj)
            
            if obj.type == 'ARMATURE':
                actor_armature = obj
                log(f"Armature Actor: {obj.name}")
    
    if actor_armature:
        for child in actor_armature.children:
            if child.type == 'MESH' and child.data.shape_keys:
                log(f"Mesh avec Shape Keys: {child.name} ({len(child.data.shape_keys.key_blocks)} keys)")
    
    return actor_armature


def load_face_data(json_path: str) -> dict:
    """Charge les données faciales depuis JSON."""
    log(f"Chargement données faciales: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    log(f"Données chargées: {len(data.get('frames', []))} frames @ {data.get('fps', 30)} FPS")
    return data


def find_shape_key_mesh(armature: bpy.types.Object) -> bpy.types.Object:
    """Trouve le mesh avec shape keys dans les enfants de l'armature."""
    if not armature:
        return None
    
    for child in armature.children:
        if child.type == 'MESH' and child.data.shape_keys:
            return child
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            if obj.parent == armature or obj.parent is None:
                return obj
    
    return None


def create_missing_shape_keys(mesh_obj: bpy.types.Object, required_keys: list):
    """Crée les shape keys manquantes si nécessaire."""
    if not mesh_obj.data.shape_keys:
        mesh_obj.shape_key_add(name='Basis')
    
    existing_keys = {key.name for key in mesh_obj.data.shape_keys.key_blocks}
    
    for key_name in required_keys:
        if key_name not in existing_keys and key_name != 'Basis':
            mesh_obj.shape_key_add(name=key_name)
            log(f"Shape key créée: {key_name}", "DEBUG")


def apply_facial_animation(actor: bpy.types.Object, face_data: dict, sync_offset: int):
    """Applique les shape keys faciales avec offset de sync."""
    log(f"Application animation faciale (offset: {sync_offset} frames)")
    
    mesh_obj = find_shape_key_mesh(actor)
    
    if not mesh_obj:
        log("Aucun mesh avec shape keys trouvé!", "ERROR")
        return
    
    if not face_data.get('frames'):
        log("Aucune frame dans les données faciales", "WARN")
        return
    
    required_keys = list(face_data['frames'][0]['blendshapes'].keys())
    create_missing_shape_keys(mesh_obj, required_keys)
    
    shape_keys = mesh_obj.data.shape_keys.key_blocks
    available_keys = {key.name: key for key in shape_keys}
    
    frames_applied = 0
    
    for frame_data in face_data["frames"]:
        source_frame = frame_data["frame"]
        target_frame = source_frame - sync_offset
        
        if target_frame < 0:
            continue
        
        for key_name, value in frame_data["blendshapes"].items():
            if key_name in available_keys:
                shape_key = available_keys[key_name]
                shape_key.value = float(value)
                shape_key.keyframe_insert(data_path="value", frame=target_frame)
        
        frames_applied += 1
    
    log(f"Animation faciale: {frames_applied} frames appliquées sur {len(available_keys)} shape keys")


def apply_smoothing(actor: bpy.types.Object, window: int):
    """Applique le lissage Savitzky-Golay sur les keyframes faciales."""
    log(f"Application lissage Savitzky-Golay (window={window})")
    
    if window < 3:
        log("Window trop petite, lissage ignoré", "WARN")
        return
    
    try:
        from scipy.signal import savgol_filter
        import numpy as np
    except ImportError:
        log("scipy non disponible - lissage ignoré", "WARN")
        return
    
    mesh_obj = find_shape_key_mesh(actor)
    if not mesh_obj or not mesh_obj.data.shape_keys:
        return
    
    if not mesh_obj.data.shape_keys.animation_data:
        return
    
    action = mesh_obj.data.shape_keys.animation_data.action
    if not action:
        return
    
    smoothed_count = 0
    
    for fcurve in action.fcurves:
        if 'key_blocks' not in fcurve.data_path:
            continue
        
        keyframe_points = fcurve.keyframe_points
        if len(keyframe_points) < window:
            continue
        
        frames = [kp.co[0] for kp in keyframe_points]
        values = [kp.co[1] for kp in keyframe_points]
        
        actual_window = min(window, len(values))
        if actual_window % 2 == 0:
            actual_window -= 1
        if actual_window < 3:
            continue
        
        order = min(2, actual_window - 1)
        
        try:
            smoothed = savgol_filter(values, actual_window, order)
            
            for i, kp in enumerate(keyframe_points):
                kp.co[1] = float(smoothed[i])
            
            smoothed_count += 1
        except Exception as e:
            log(f"Erreur lissage fcurve: {e}", "DEBUG")
    
    log(f"Lissage appliqué sur {smoothed_count} courbes")


def build_bone_mapping(source_armature: bpy.types.Object, target_armature: bpy.types.Object) -> dict:
    """Construit le mapping entre les os source et target."""
    mapping = {}
    
    source_bones = {bone.name.lower(): bone.name for bone in source_armature.data.bones}
    target_bones = {bone.name.lower(): bone.name for bone in target_armature.data.bones}
    
    for source_lower, source_name in source_bones.items():
        if source_lower in target_bones:
            mapping[source_name] = target_bones[source_lower]
    
    common_mappings = {
        'hips': ['pelvis', 'root', 'hip'],
        'spine': ['spine1', 'torso'],
        'spine1': ['spine2', 'chest'],
        'spine2': ['spine3', 'upperchest'],
        'neck': ['neck1'],
        'head': ['head1'],
        'leftshoulder': ['l_shoulder', 'shoulder_l', 'lshoulder'],
        'leftarm': ['l_upperarm', 'upperarm_l', 'lupperarm'],
        'leftforearm': ['l_forearm', 'forearm_l', 'lforearm'],
        'lefthand': ['l_hand', 'hand_l', 'lhand'],
        'rightshoulder': ['r_shoulder', 'shoulder_r', 'rshoulder'],
        'rightarm': ['r_upperarm', 'upperarm_r', 'rupperarm'],
        'rightforearm': ['r_forearm', 'forearm_r', 'rforearm'],
        'righthand': ['r_hand', 'hand_r', 'rhand'],
        'leftupleg': ['l_thigh', 'thigh_l', 'lthigh', 'leftthigh'],
        'leftleg': ['l_calf', 'calf_l', 'lcalf', 'leftshin'],
        'leftfoot': ['l_foot', 'foot_l', 'lfoot'],
        'rightupleg': ['r_thigh', 'thigh_r', 'rthigh', 'rightthigh'],
        'rightleg': ['r_calf', 'calf_r', 'rcalf', 'rightshin'],
        'rightfoot': ['r_foot', 'foot_r', 'rfoot'],
    }
    
    for standard, alternatives in common_mappings.items():
        if standard in source_bones:
            for alt in alternatives:
                if alt in target_bones and source_bones[standard] not in mapping:
                    mapping[source_bones[standard]] = target_bones[alt]
                    break
    
    log(f"Bone mapping: {len(mapping)} correspondances trouvées")
    return mapping


def transfer_body_animation(source_armature: bpy.types.Object, target_armature: bpy.types.Object):
    """Transfère l'animation body vers l'avatar."""
    log("Transfert animation body")
    
    if not source_armature or not target_armature:
        log("Armatures manquantes pour le transfert", "ERROR")
        return
    
    if not source_armature.animation_data or not source_armature.animation_data.action:
        log("Pas d'animation sur le FBX source", "WARN")
        return
    
    source_action = source_armature.animation_data.action
    
    new_action = source_action.copy()
    new_action.name = f"{target_armature.name}_Action"
    
    if not target_armature.animation_data:
        target_armature.animation_data_create()
    
    target_armature.animation_data.action = new_action
    
    bone_mapping = build_bone_mapping(source_armature, target_armature)
    
    for fcurve in new_action.fcurves:
        if 'pose.bones' in fcurve.data_path:
            for source_bone, target_bone in bone_mapping.items():
                if f'pose.bones["{source_bone}"]' in fcurve.data_path:
                    fcurve.data_path = fcurve.data_path.replace(
                        f'pose.bones["{source_bone}"]',
                        f'pose.bones["{target_bone}"]'
                    )
                    break
    
    frame_start = int(source_action.frame_range[0])
    frame_end = int(source_action.frame_range[1])
    
    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    
    log(f"Animation transférée: frames {frame_start}-{frame_end}")


def export_alembic(output_path: str):
    """Exporte la scène en Alembic."""
    log(f"Export Alembic: {output_path}")
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    bpy.ops.wm.alembic_export(
        filepath=output_path,
        selected=False,
        start=bpy.context.scene.frame_start,
        end=bpy.context.scene.frame_end,
        face_sets=True,
        uvs=True,
        packuv=True,
        export_hair=False,
        export_particles=False,
        flatten=False,
        visible_objects_only=False
    )
    
    if Path(output_path).exists():
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        log(f"Export réussi: {output_path} ({size_mb:.2f} MB)")
    else:
        log("Export Alembic échoué!", "ERROR")


def main():
    print("=" * 60)
    print("  BLENDER FUSION — TRANSMUTATION ENGINE")
    print("=" * 60)
    
    log(f"Body FBX: {args.body_fbx}")
    log(f"Actor Blend: {args.actor_blend}")
    log(f"Face JSON: {args.face_json}")
    log(f"Output: {args.output}")
    log(f"Sync Offset: {args.sync_offset}")
    log(f"Smooth Window: {args.smooth_window}")
    
    clear_scene()
    
    body_armature = import_body_fbx(args.body_fbx)
    
    actor_armature = import_actor_blend(args.actor_blend)
    
    face_data = load_face_data(args.face_json)
    
    if body_armature and actor_armature:
        transfer_body_animation(body_armature, actor_armature)
    
    if actor_armature:
        apply_facial_animation(actor_armature, face_data, args.sync_offset)
    
    if actor_armature and args.smooth_window > 2:
        apply_smoothing(actor_armature, args.smooth_window)
    
    if body_armature:
        bpy.data.objects.remove(body_armature, do_unlink=True)
        log("Armature FBX source supprimée")
    
    export_alembic(args.output)
    
    print("=" * 60)
    print("  FUSION COMPLÈTE")
    print("=" * 60)


if __name__ == "__main__":
    main()
