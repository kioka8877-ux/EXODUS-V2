#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    FINAL BAKER — EXODUS LOGISTICS                            ║
║                   Export Alembic et Backup Blend                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour baker les animations et exporter en format Alembic (.abc).
Crée également un backup .blend éditable.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


ALEMBIC_EXPORT_DEFAULTS = {
    "face_sets": True,
    "uvs": True,
    "packuv": True,
    "export_hair": False,
    "export_particles": False,
    "flatten": False,
    "visible_objects_only": False,
    "evaluation_mode": "RENDER"
}


def get_scene_frame_range() -> Tuple[int, int]:
    """Retourne la plage de frames de la scène active."""
    if not BLENDER_AVAILABLE:
        return (1, 250)
    
    scene = bpy.context.scene
    return (scene.frame_start, scene.frame_end)


def bake_constraints(objects: Optional[List[Any]] = None, frame_start: int = None, frame_end: int = None):
    """
    Bake les contraintes des objets en keyframes.
    Optionnel car Alembic exporte déjà les transformations évaluées.
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
    
    if frame_start is None or frame_end is None:
        frame_start, frame_end = get_scene_frame_range()
    
    if objects is None:
        objects = [obj for obj in bpy.context.scene.objects if obj.constraints]
    
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in objects:
        obj.select_set(True)
    
    if not objects:
        print("[BAKER] No objects with constraints to bake")
        return
    
    bpy.context.view_layer.objects.active = objects[0]
    
    bpy.ops.nla.bake(
        frame_start=frame_start,
        frame_end=frame_end,
        only_selected=True,
        visual_keying=True,
        clear_constraints=False,
        use_current_action=True,
        clean_curves=True,
        bake_types={'OBJECT'}
    )
    
    print(f"[BAKER] Baked {len(objects)} objects from frame {frame_start} to {frame_end}")


def bake_and_export(
    output_path: str,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
    selected_only: bool = False,
    **kwargs
) -> bool:
    """
    Bake toutes les animations et exporte en Alembic.
    
    Args:
        output_path: Chemin du fichier .abc de sortie
        frame_start: Frame de début (défaut: frame_start de la scène)
        frame_end: Frame de fin (défaut: frame_end de la scène)
        selected_only: Exporter seulement les objets sélectionnés
        **kwargs: Options supplémentaires pour l'export Alembic
    
    Returns:
        True si l'export réussit, False sinon
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
    
    if frame_start is None or frame_end is None:
        scene_start, scene_end = get_scene_frame_range()
        frame_start = frame_start or scene_start
        frame_end = frame_end or scene_end
    
    output_path = str(Path(output_path).resolve())
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    export_options = ALEMBIC_EXPORT_DEFAULTS.copy()
    export_options.update(kwargs)
    
    try:
        bpy.ops.wm.alembic_export(
            filepath=output_path,
            selected=selected_only,
            start=frame_start,
            end=frame_end,
            face_sets=export_options["face_sets"],
            uvs=export_options["uvs"],
            packuv=export_options["packuv"],
            export_hair=export_options["export_hair"],
            export_particles=export_options["export_particles"],
            flatten=export_options["flatten"],
            visible_objects_only=export_options["visible_objects_only"],
            evaluation_mode=export_options["evaluation_mode"]
        )
        
        print(f"[BAKER] Alembic exported: {output_path}")
        print(f"[BAKER] Frame range: {frame_start} - {frame_end}")
        return True
        
    except Exception as e:
        print(f"[BAKER] ERROR: Alembic export failed: {e}")
        return False


def save_blend_backup(output_path: str, pack_resources: bool = True) -> bool:
    """
    Sauvegarde le fichier .blend actuel comme backup.
    
    Args:
        output_path: Chemin du fichier .blend de sortie
        pack_resources: Inclure les textures dans le fichier
    
    Returns:
        True si la sauvegarde réussit, False sinon
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
    
    output_path = str(Path(output_path).resolve())
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if pack_resources:
            bpy.ops.file.pack_all()
            print("[BAKER] Resources packed into blend file")
        
        bpy.ops.wm.save_as_mainfile(filepath=output_path, copy=True)
        
        print(f"[BAKER] Blend backup saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"[BAKER] ERROR: Blend save failed: {e}")
        return False


def export_fbx(
    output_path: str,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
    selected_only: bool = False
) -> bool:
    """
    Export alternatif en FBX.
    
    Args:
        output_path: Chemin du fichier .fbx de sortie
        frame_start: Frame de début
        frame_end: Frame de fin
        selected_only: Exporter seulement les objets sélectionnés
    
    Returns:
        True si l'export réussit, False sinon
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
    
    if frame_start is None or frame_end is None:
        scene_start, scene_end = get_scene_frame_range()
        frame_start = frame_start or scene_start
        frame_end = frame_end or scene_end
    
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        bpy.ops.export_scene.fbx(
            filepath=output_path,
            use_selection=selected_only,
            bake_anim=True,
            bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=0.0,
            embed_textures=True
        )
        
        print(f"[BAKER] FBX exported: {output_path}")
        return True
        
    except Exception as e:
        print(f"[BAKER] ERROR: FBX export failed: {e}")
        return False


def generate_preview_image(output_path: str, frame: Optional[int] = None) -> bool:
    """
    Génère une image de preview de la scène.
    
    Args:
        output_path: Chemin de l'image de sortie (.png)
        frame: Frame à rendre (défaut: frame actuelle)
    
    Returns:
        True si le rendu réussit, False sinon
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
    
    scene = bpy.context.scene
    
    if frame is not None:
        scene.frame_set(frame)
    
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    original_path = scene.render.filepath
    original_format = scene.render.image_settings.file_format
    
    try:
        scene.render.filepath = output_path
        scene.render.image_settings.file_format = 'PNG'
        
        bpy.ops.render.opengl(write_still=True)
        
        print(f"[BAKER] Preview image saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"[BAKER] ERROR: Preview render failed: {e}")
        return False
        
    finally:
        scene.render.filepath = original_path
        scene.render.image_settings.file_format = original_format


def get_export_stats() -> Dict[str, Any]:
    """
    Retourne des statistiques sur la scène à exporter.
    """
    if not BLENDER_AVAILABLE:
        return {}
    
    scene = bpy.context.scene
    
    mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
    armature_objects = [obj for obj in scene.objects if obj.type == 'ARMATURE']
    
    total_vertices = sum(len(obj.data.vertices) for obj in mesh_objects if obj.data)
    total_faces = sum(len(obj.data.polygons) for obj in mesh_objects if obj.data)
    
    objects_with_constraints = [obj for obj in scene.objects if obj.constraints]
    animated_objects = [obj for obj in scene.objects if obj.animation_data and obj.animation_data.action]
    
    return {
        "frame_range": get_scene_frame_range(),
        "total_objects": len(scene.objects),
        "mesh_objects": len(mesh_objects),
        "armature_objects": len(armature_objects),
        "total_vertices": total_vertices,
        "total_faces": total_faces,
        "objects_with_constraints": len(objects_with_constraints),
        "animated_objects": len(animated_objects)
    }


def validate_export_ready() -> Tuple[bool, List[str]]:
    """
    Valide que la scène est prête pour l'export.
    
    Returns:
        Tuple (is_valid, list of warnings/errors)
    """
    if not BLENDER_AVAILABLE:
        return (False, ["Blender (bpy) not available"])
    
    issues = []
    scene = bpy.context.scene
    
    if scene.frame_end <= scene.frame_start:
        issues.append(f"Invalid frame range: {scene.frame_start} - {scene.frame_end}")
    
    mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
    if not mesh_objects:
        issues.append("No mesh objects in scene")
    
    for obj in mesh_objects:
        if obj.data and len(obj.data.vertices) == 0:
            issues.append(f"Empty mesh: {obj.name}")
    
    for obj in scene.objects:
        for constraint in obj.constraints:
            if constraint.type == 'CHILD_OF':
                if constraint.target is None:
                    issues.append(f"Broken constraint on {obj.name}: {constraint.name}")
    
    is_valid = len(issues) == 0
    return (is_valid, issues)


if __name__ == "__main__":
    print("Final Baker - EXODUS LOGISTICS")
    print("Ce module doit être importé dans Blender.")
    
    print("\nExemple d'utilisation:")
    print("""
    from final_baker import bake_and_export, save_blend_backup, get_export_stats
    
    # Vérifier les stats
    stats = get_export_stats()
    print(f"Objects: {stats['total_objects']}")
    print(f"Frame range: {stats['frame_range']}")
    
    # Exporter en Alembic
    bake_and_export("/output/actor_equipped.abc")
    
    # Sauvegarder le blend
    save_blend_backup("/output/actor_equipped.blend")
    """)
