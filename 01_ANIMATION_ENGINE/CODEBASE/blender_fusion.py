"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     BLENDER FUSION V2 — Body + Face → .blend (Master) + .abc (Preview)      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ZÉRO EMOCA — Emotional Intent Transfer via expression_schema.py            ║
║  NLA Strips + Bézier F-Curves + Noise Modifier pour micro-jitter           ║
║  Output Principal: .blend avec armature active (pour attachement props)      ║
║  Output Secondaire: .abc (preview/backup)                                    ║
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

parser = argparse.ArgumentParser(description='Blender Fusion Script V2')
parser.add_argument('--body-fbx', required=True, help='Body motion FBX file')
parser.add_argument('--actor-blend', required=True, help='Actor .blend file')
parser.add_argument('--face-json', required=True, help='Translated facial data JSON (from EmotionalIntentTranslator)')
parser.add_argument('--output', required=True, help='Output Alembic path')
parser.add_argument('--sync-offset', type=int, default=0, help='Sync offset in frames')
parser.add_argument('--intensity-mode', choices=['linear', 'quadratic', 'ease_in_out'],
                    default='ease_in_out', help='Intensity interpolation mode')
parser.add_argument('--output-blend', help='Output .blend path (auto-generated if not provided)')
parser.add_argument('--lip-sync-json', help='Lip-sync data JSON (from RhubarbBridge)', default=None)

args = parser.parse_args(argv)


def log(msg: str, level: str = "INFO"):
    """Logger formaté pour Blender."""
    print(f"[BLENDER:{level}] {msg}")


# =========================================================================
# FONCTIONS CONSERVÉES — identiques à V1
# =========================================================================

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


def export_blend(output_path: str):
    """Exporte le fichier .blend avec textures packées."""
    log(f"Export Blend: {output_path}")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.file.pack_all()

    bpy.ops.wm.save_as_mainfile(filepath=output_path, compress=True)

    if Path(output_path).exists():
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        log(f"Export Blend réussi: {output_path} ({size_mb:.2f} MB)")
    else:
        log("Export Blend échoué!", "ERROR")


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


# =========================================================================
# NOUVELLES FONCTIONS V2 — NLA Strips + Bézier + Noise
# =========================================================================

def load_blender_data(json_path: str) -> dict:
    """Charge les données traduites depuis EmotionalIntentTranslator."""
    log(f"Chargement données faciales V2: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    n_segments = len(data.get('segments', []))
    fps = data.get('fps', 30)
    log(f"Données chargées: {n_segments} segments @ {fps} FPS")
    return data


def apply_nla_facial_animation(actor: bpy.types.Object, blender_data: dict, sync_offset: int):
    """Applique les shape keys via NLA strips avec keyframes Bézier.

    Pour chaque segment, 3 keyframes:
      - frame_start : valeurs à intensity 0
      - frame_apex  : valeurs à pleine intensité
      - frame_end   : valeurs fade vers 0
    """
    log(f"Application animation faciale NLA (offset: {sync_offset} frames)")

    mesh_obj = find_shape_key_mesh(actor)
    if not mesh_obj:
        log("Aucun mesh avec shape keys trouvé!", "ERROR")
        return

    segments = blender_data.get("segments", [])
    if not segments:
        log("Aucun segment dans les données faciales", "WARN")
        return

    all_keys = set()
    for seg in segments:
        all_keys.update(seg["values"].keys())
    create_missing_shape_keys(mesh_obj, list(all_keys))

    shape_keys = mesh_obj.data.shape_keys
    if not shape_keys.animation_data:
        shape_keys.animation_data_create()

    for i, seg in enumerate(segments):
        frame_start = seg["frame_start"] - sync_offset
        frame_end = seg["frame_end"] - sync_offset
        frame_apex = seg["frame_apex"] - sync_offset

        if frame_end < 0:
            continue
        frame_start = max(0, frame_start)

        action = bpy.data.actions.new(name=f"expr_segment_{i}")

        for key_name, peak_value in seg["values"].items():
            kb = shape_keys.key_blocks.get(key_name)
            if not kb:
                continue

            data_path = f'key_blocks["{key_name}"].value'
            fcurve = action.fcurves.new(data_path=data_path)

            fcurve.keyframe_points.add(3)
            fcurve.keyframe_points[0].co = (float(frame_start), 0.0)
            fcurve.keyframe_points[1].co = (float(frame_apex), float(peak_value))
            fcurve.keyframe_points[2].co = (float(frame_end), 0.0)

            for kp in fcurve.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'

        track = shape_keys.animation_data.nla_tracks.new()
        track.name = f"segment_{i}"
        strip = track.strips.new(
            name=f"segment_{i}",
            start=frame_start,
            action=action,
        )
        strip.blend_type = 'COMBINE' if seg.get("is_transition", False) else 'REPLACE'

        tag = " [TRANSITION]" if seg.get("is_transition", False) else ""
        log(f"NLA strip {i}{tag}: frames {frame_start}-{frame_end} (apex {frame_apex})")

    log(f"Animation faciale NLA: {len(segments)} segments appliqués")


def apply_micro_jitter(actor: bpy.types.Object, blender_data: dict):
    """Ajoute du bruit procédural via F-Curve Noise Modifier pour micro-expressions."""
    micro_presets = blender_data.get("micro_expressions", {})
    if not micro_presets:
        log("Aucun preset micro-expression", "WARN")
        return

    mesh_obj = find_shape_key_mesh(actor)
    if not mesh_obj or not mesh_obj.data.shape_keys:
        return

    shape_keys = mesh_obj.data.shape_keys
    if not shape_keys.animation_data:
        return

    modified_count = 0
    for track in shape_keys.animation_data.nla_tracks:
        for strip in track.strips:
            action = strip.action
            if not action:
                continue

            for preset_name, preset in micro_presets.items():
                for key_name in preset["target_keys"]:
                    data_path = f'key_blocks["{key_name}"].value'
                    fcurve = action.fcurves.find(data_path)
                    if fcurve:
                        noise_mod = fcurve.modifiers.new(type='NOISE')
                        noise_mod.strength = preset["amplitude"]
                        noise_mod.scale = preset["frequency_hz"]
                        noise_mod.phase = hash(key_name) % 1000 / 1000.0
                        noise_mod.blend_type = 'ADD'
                        modified_count += 1

    log(f"Micro-jitter: {modified_count} noise modifiers appliqués")


def apply_lip_sync_nla(actor: bpy.types.Object, lip_sync_data: dict, sync_offset: int):
    """Applique le lip-sync comme NLA track prioritaire sur MOUTH_KEYS.

    Ce track est layered AU-DESSUS des expression segments.
    blend_type = 'REPLACE' pour que le lip-sync écrase les MOUTH_KEYS des émotions.

    Architecture NLA après application :
        Track N+1 (TOP) : Lip-Sync (Rhubarb) — REPLACE sur MOUTH_KEYS uniquement
        Track N         : Expressions (émotions) — REPLACE
        Track N-1       : Micro-Jitter (Noise) — ADD
    """
    log("Application lip-sync NLA")

    mesh_obj = find_shape_key_mesh(actor)
    if not mesh_obj:
        log("Aucun mesh avec shape keys trouvé!", "ERROR")
        return

    segments = lip_sync_data.get("lip_sync_segments", [])
    if not segments:
        log("Aucun segment lip-sync", "WARN")
        return

    all_keys = set()
    for seg in segments:
        all_keys.update(seg["values"].keys())
    create_missing_shape_keys(mesh_obj, list(all_keys))

    shape_keys = mesh_obj.data.shape_keys
    if not shape_keys.animation_data:
        shape_keys.animation_data_create()

    action = bpy.data.actions.new(name="lip_sync_rhubarb")

    for key_name in all_keys:
        kb = shape_keys.key_blocks.get(key_name)
        if not kb:
            continue

        data_path = f'key_blocks["{key_name}"].value'
        fcurve = action.fcurves.new(data_path=data_path)

        for seg in segments:
            fs = seg["frame_start"] - sync_offset
            fe = seg["frame_end"] - sync_offset

            if fe < 0:
                continue
            fs = max(0, fs)

            mid_frame = (fs + fe) / 2.0
            value = float(seg["values"].get(key_name, 0.0))

            fcurve.keyframe_points.add(1)
            kp = fcurve.keyframe_points[-1]
            kp.co = (mid_frame, value)
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'

    track = shape_keys.animation_data.nla_tracks.new()
    track.name = "lip_sync"

    first_frame = max(0, segments[0]["frame_start"] - sync_offset)
    strip = track.strips.new(
        name="lip_sync_rhubarb",
        start=first_frame,
        action=action,
    )
    strip.blend_type = 'REPLACE'

    log(f"Lip-sync NLA: {len(segments)} cues appliqués sur {len(all_keys)} MOUTH_KEYS")


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("=" * 60)
    print("  BLENDER FUSION V2 — TRANSMUTATION ENGINE")
    print("=" * 60)

    log(f"Body FBX: {args.body_fbx}")
    log(f"Actor Blend: {args.actor_blend}")
    log(f"Face JSON: {args.face_json}")
    log(f"Output: {args.output}")
    log(f"Sync Offset: {args.sync_offset}")
    log(f"Intensity Mode: {args.intensity_mode}")

    clear_scene()

    body_armature = import_body_fbx(args.body_fbx)

    actor_armature = import_actor_blend(args.actor_blend)

    blender_data = load_blender_data(args.face_json)

    if body_armature and actor_armature:
        transfer_body_animation(body_armature, actor_armature)

    if actor_armature:
        apply_nla_facial_animation(actor_armature, blender_data, args.sync_offset)
        apply_micro_jitter(actor_armature, blender_data)

        # Lip-sync (optionnel — NLA track prioritaire sur MOUTH_KEYS)
        if args.lip_sync_json:
            lip_sync_data = load_blender_data(args.lip_sync_json)
            apply_lip_sync_nla(actor_armature, lip_sync_data, args.sync_offset)

    blend_output = args.output_blend
    if not blend_output:
        blend_output = str(Path(args.output).with_suffix('.blend'))

    export_blend(blend_output)

    export_alembic(args.output)

    if body_armature:
        bpy.data.objects.remove(body_armature, do_unlink=True)
        log("Armature FBX source supprimée")

    print("=" * 60)
    print("  FUSION V2 COMPLÈTE")
    print("=" * 60)


if __name__ == "__main__":
    main()
