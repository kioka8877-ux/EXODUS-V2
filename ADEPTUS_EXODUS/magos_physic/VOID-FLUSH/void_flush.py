"""
VOID-FLUSH — Tech-Pretre P1
Role : Nettoyage GPU/VRAM avant rendu lourd
       Purge les donnees Blender residuelles entre fregates

Usage :
  python void_flush.py --fregate U03
  python void_flush.py --full
  python void_flush.py --status

Constitution : Les fregates produisent. Les Mini Programs servent.
"""

import sys
import json
import gc
from pathlib import Path
from datetime import datetime

# Feature flags
FLAGS_PATH = Path(__file__).parent / "feature_flags.json"


def load_flags():
    if FLAGS_PATH.exists():
        return json.loads(FLAGS_PATH.read_text())
    return {"gpu_flush": True, "mesh_purge": True, "orphan_purge": True, "verbose": True}


def flush_status():
    """Retourne l'etat memoire actuel (sans Blender)."""
    import os
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_gc_counts": gc.get_count(),
        "pid": os.getpid(),
    }

    # Tenter lecture memoire process
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS"):
                    status["ram_rss_kb"] = int(line.split()[1])
                elif line.startswith("VmPeak"):
                    status["ram_peak_kb"] = int(line.split()[1])
    except Exception:
        status["ram_info"] = "unavailable"

    return status


def flush_python_gc():
    """Purge le garbage collector Python."""
    before = gc.get_count()
    collected = gc.collect()
    after = gc.get_count()
    return {"collected": collected, "before": before, "after": after}


def flush_blender_orphans():
    """
    Purge les data-blocks orphelins dans Blender.
    Appele depuis un contexte Blender uniquement.
    """
    try:
        import bpy
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        return {"status": "PURGED", "engine": "blender"}
    except ImportError:
        return {"status": "SKIPPED", "reason": "Blender non disponible (mode standalone)"}


def flush_blender_gpu():
    """
    Vide le cache GPU de Blender si disponible.
    """
    try:
        import bpy
        # Purger les images non-utilisees du GPU
        for img in bpy.data.images:
            if not img.users:
                bpy.data.images.remove(img)
        # Liberer les meshes orphelins
        for mesh in bpy.data.meshes:
            if not mesh.users:
                bpy.data.meshes.remove(mesh)
        return {"status": "FLUSHED", "engine": "blender_gpu"}
    except ImportError:
        return {"status": "SKIPPED", "reason": "Blender non disponible"}


def run_full_flush(fregate_id=None, flags=None):
    """
    Sequence de flush complete.
    Retourne un rapport structure.
    """
    if flags is None:
        flags = load_flags()

    verbose = flags.get("verbose", True)
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "fregate": fregate_id or "ALL",
        "steps": []
    }

    # Etape 1 : Python GC
    if flags.get("mesh_purge", True):
        gc_result = flush_python_gc()
        report["steps"].append({"step": "python_gc", "result": gc_result})
        if verbose:
            print(f"[VOID-FLUSH] Python GC : {gc_result['collected']} objets purges")

    # Etape 2 : Orphelins Blender
    if flags.get("orphan_purge", True):
        orphan_result = flush_blender_orphans()
        report["steps"].append({"step": "blender_orphans", "result": orphan_result})
        if verbose:
            print(f"[VOID-FLUSH] Orphelins Blender : {orphan_result['status']}")

    # Etape 3 : GPU Blender
    if flags.get("gpu_flush", True):
        gpu_result = flush_blender_gpu()
        report["steps"].append({"step": "blender_gpu", "result": gpu_result})
        if verbose:
            print(f"[VOID-FLUSH] GPU Blender : {gpu_result['status']}")

    report["status"] = "COMPLETE"
    report["steps_ok"] = len(report["steps"])

    if verbose:
        print(f"[VOID-FLUSH] === FLUSH TERMINE — {report['steps_ok']} etapes ===")

    return report


def main():
    flags = load_flags()
    args = sys.argv[1:]

    if not args or "--status" in args:
        status = flush_status()
        print(json.dumps(status, indent=2))

    elif "--full" in args:
        report = run_full_flush(flags=flags)
        print(json.dumps(report, indent=2))

    elif "--fregate" in args:
        idx = args.index("--fregate")
        fregate_id = args[idx + 1] if idx + 1 < len(args) else "UNKNOWN"
        report = run_full_flush(fregate_id=fregate_id, flags=flags)
        print(json.dumps(report, indent=2))

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
