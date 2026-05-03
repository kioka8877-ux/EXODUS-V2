#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         SOCKETING ENGINE — M2_F02 LOGISTICS (Mode 2 — From Scratch)         ║
║     Importe GLB avatar + attache props + exporte ABC/Blend                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Loi R-01 : Copie étanche Mode 2 — ZERO Phantom Link, ZERO Mode 1          ║
║  Adapté   : import GLB au lieu d'ouvrir un .blend existant                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Appelé par EXO_M2_F02_LOGISTICS.py via Blender headless:
    blender --background --python socketing_engine.py -- \\
        --glb-avatar   avatar_validated.glb \\
        --production-plan '{"scenes": [...]}' \\
        --props-mapping '{"gun": "/path/gun.glb"}' \\
        --output-dir   /path/OUT_BAKED_ACTORS \\
        --output-name  actor_equipped
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import bpy
    import mathutils
except ImportError:
    print("[SOCKETING_M2] ERREUR: ce script doit être exécuté dans Blender")
    sys.exit(1)

# Import logique depuis actor_assembly (même dossier)
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

try:
    from actor_assembly import (
        SocketingEngine,
        import_prop,
        process_production_plan,
    )
    from final_baker import export_alembic, save_blend_backup
except ImportError as e:
    print(f"[SOCKETING_M2] Import error: {e}")
    sys.exit(1)

SOCKETING_VERSION = "1.0.0"


def _log(msg: str):
    print(f"[SOCKETING_M2] {msg}")


# ──────────────────────────────────────────────────────────────
# IMPORT GLB AVATAR (Mode 2 — pas de .blend source)
# ──────────────────────────────────────────────────────────────

def import_glb_avatar(glb_path: str) -> bool:
    """Importe le GLB avatar Roblox dans une scène Blender vierge."""
    _log(f"Import GLB avatar: {glb_path}")

    # Vider la scène par défaut
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    path = Path(glb_path)
    if not path.exists():
        _log(f"ERREUR: GLB introuvable: {glb_path}")
        return False

    if path.suffix.lower() not in [".glb", ".gltf"]:
        _log(f"ERREUR: Format non supporté: {path.suffix}")
        return False

    try:
        bpy.ops.import_scene.gltf(filepath=str(path))
        _log(f"Import réussi — {len(bpy.context.scene.objects)} objets dans la scène")
    except Exception as e:
        _log(f"ERREUR import GLB: {e}")
        return False

    # Vérifier la présence d'une armature (requis pour socketing)
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        _log("WARN: Aucune armature dans le GLB — socketing sans contraintes")
    else:
        _log(f"Armature(s): {[a.name for a in armatures]}")

    return True


# ──────────────────────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────────────────────

def export_results(output_dir: str, output_name: str) -> bool:
    """Exporte en Alembic (.abc) + backup .blend."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    abc_path  = out_dir / f"{output_name}.abc"
    blend_path = out_dir / f"{output_name}.blend"

    # Alembic
    try:
        export_alembic(str(abc_path))
        _log(f"ABC exporté: {abc_path}")
    except Exception as e:
        _log(f"WARN ABC export: {e}")
        # Fallback: export Alembic natif
        try:
            bpy.ops.wm.alembic_export(
                filepath=str(abc_path),
                visible_objects_only=False,
            )
            _log(f"ABC exporté (fallback): {abc_path}")
        except Exception as e2:
            _log(f"ERREUR ABC: {e2}")
            return False

    # Blend backup
    try:
        save_blend_backup(str(blend_path))
        _log(f"Blend sauvegardé: {blend_path}")
    except Exception as e:
        _log(f"WARN backup .blend: {e}")
        try:
            bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
            _log(f"Blend sauvegardé (fallback): {blend_path}")
        except Exception as e2:
            _log(f"ERREUR Blend: {e2}")

    return abc_path.exists()


# ──────────────────────────────────────────────────────────────
# MAIN (exécuté dans Blender)
# ──────────────────────────────────────────────────────────────

def main():
    # Récupérer les args après "--"
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Socketing Engine M2_F02")
    parser.add_argument("--glb-avatar",      required=True)
    parser.add_argument("--production-plan", required=True,
                        help="JSON string ou chemin fichier")
    parser.add_argument("--props-mapping",   required=True,
                        help="JSON string {prop_id: filepath}")
    parser.add_argument("--output-dir",      required=True)
    parser.add_argument("--output-name",     default="actor_equipped")
    parser.add_argument("--verbose", "-v",   action="store_true")
    args = parser.parse_args(argv)

    _log(f"SOCKETING ENGINE v{SOCKETING_VERSION} — Mode 2 from Scratch")
    _log(f"GLB Avatar: {args.glb_avatar}")

    # ── 1. Parse plan & mapping ────────────────────────────────────────
    try:
        plan = json.loads(args.production_plan)
    except json.JSONDecodeError:
        plan_path = Path(args.production_plan)
        if plan_path.exists():
            with open(plan_path) as f:
                plan = json.load(f)
        else:
            _log("WARN: plan JSON invalide — utilise plan vide")
            plan = {"scenes": []}

    try:
        props_mapping = json.loads(args.props_mapping)
    except json.JSONDecodeError:
        _log("WARN: props_mapping JSON invalide — pas de props")
        props_mapping = {}

    # ── 2. Import GLB avatar ───────────────────────────────────────────
    if not import_glb_avatar(args.glb_avatar):
        _log("ÉCHEC: import GLB avatar")
        sys.exit(1)

    # ── 3. Pipeline socketing (si props) ──────────────────────────────
    total_props = sum(len(s.get("props_actions", [])) for s in plan.get("scenes", []))

    if total_props > 0 and props_mapping:
        _log(f"Pipeline socketing: {total_props} actions, {len(props_mapping)} props")
        engine = SocketingEngine(verbose=args.verbose)
        try:
            result = process_production_plan(plan, props_mapping, engine, verbose=args.verbose)
            _log(f"Socketing terminé: {len(result.get('operations', []))} opérations")
        except ValueError as e:
            _log(f"ERREUR socketing: {e}")
            sys.exit(1)
    else:
        _log("Pas de props à attacher — export direct")

    # ── 4. Export ──────────────────────────────────────────────────────
    if not export_results(args.output_dir, args.output_name):
        _log("ÉCHEC: export ABC")
        sys.exit(1)

    _log("SOCKETING ENGINE — TERMINÉ")


if __name__ == "__main__":
    main()
