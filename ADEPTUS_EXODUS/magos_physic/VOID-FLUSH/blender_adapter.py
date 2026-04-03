"""
VOID-FLUSH — Blender Adapter
Role : Interface entre void_flush.py et l'API Blender
       Injecteur dans les frégates concernées

Usage dans une fregate (depuis un script Blender) :
  from ADEPTUS_EXODUS.magos_physic.VOID_FLUSH.blender_adapter import flush_before_render
  flush_before_render(scene)

Usage standalone (pre-render hook) :
  python blender_adapter.py --scene <scene.blend> --fregate U03
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def flush_before_render(scene=None, fregate_id=None, verbose=True):
    """
    Hook a appeler AVANT chaque render lourd.
    Purge memoire Blender + force depsgraph update.

    Retourne dict avec statut et actions effectuees.
    """
    actions = []

    try:
        import bpy

        # 1. Forcer mise a jour depsgraph (FIX D6_depsgraph)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        actions.append("depsgraph.update()")

        # 2. Purger orphelins
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        actions.append("orphans_purge(recursive)")

        # 3. Purger images GPU non utilisees
        removed_imgs = 0
        for img in list(bpy.data.images):
            if img.users == 0:
                bpy.data.images.remove(img)
                removed_imgs += 1
        if removed_imgs:
            actions.append(f"images_purge({removed_imgs})")

        # 4. Purger meshes orphelins
        removed_meshes = 0
        for mesh in list(bpy.data.meshes):
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
                removed_meshes += 1
        if removed_meshes:
            actions.append(f"meshes_purge({removed_meshes})")

        # 5. Verifier camera presente (FIX D6_camera)
        if scene and not scene.camera:
            from VULKAN_FORGE.ARSENAL.scripts.fix_camera_missing import fix_camera_missing
            fix_camera_missing(scene)
            actions.append("camera_main_injected")

        result = {
            "status": "OK",
            "fregate": fregate_id or "UNKNOWN",
            "timestamp": datetime.utcnow().isoformat(),
            "actions": actions,
            "engine": "blender"
        }

    except ImportError:
        result = {
            "status": "STANDALONE",
            "fregate": fregate_id or "UNKNOWN",
            "timestamp": datetime.utcnow().isoformat(),
            "actions": ["python_gc"],
            "note": "Blender non disponible — GC Python uniquement"
        }
        import gc
        gc.collect()

    if verbose:
        print(f"[VOID-FLUSH:ADAPTER] {result['status']} — {len(result['actions'])} actions — fregate={result['fregate']}")

    return result


def flush_after_render(fregate_id=None, verbose=True):
    """
    Hook a appeler APRES chaque render lourd.
    Libere les ressources temporaires du render.
    """
    actions = []

    try:
        import bpy
        import gc

        # Forcer GC Python
        gc.collect()
        actions.append("gc.collect()")

        # Nettoyer render results si possible
        for img in list(bpy.data.images):
            if img.users == 0:
                bpy.data.images.remove(img)
                actions.append(f"purge_img:{img.name}")

        result = {"status": "OK", "fregate": fregate_id, "actions": actions}

    except ImportError:
        import gc
        gc.collect()
        result = {"status": "STANDALONE", "fregate": fregate_id, "actions": ["gc.collect()"]}

    if verbose:
        print(f"[VOID-FLUSH:ADAPTER] POST-RENDER — {len(result['actions'])} actions")

    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    fregate_id = None

    if "--fregate" in args:
        idx = args.index("--fregate")
        fregate_id = args[idx + 1] if idx + 1 < len(args) else None

    result = flush_before_render(fregate_id=fregate_id, verbose=True)
    print(json.dumps(result, indent=2))
