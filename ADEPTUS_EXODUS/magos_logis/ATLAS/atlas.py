"""
ATLAS — Tech-Pretre P2
Role : Centralisation des chemins et etat du pipeline
       Source de verite pour tous les chemins de l'Empire

Usage :
  python atlas.py --paths U03
  python atlas.py --state
  python atlas.py --resolve U04 OUT_FINAL_FRAMES

Constitution : Les fregates produisent. Les Mini Programs servent.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent.parent  # racine EXODUS-V2
SESSION_STORE = Path(__file__).parent / "session_store.py"
STATE_FILE = Path(__file__).parent / "pipeline_state.json"


# Carte canonique de toutes les fregates
FREGATE_MAP = {
    "U00": {
        "name": "CORTEX_HQ",
        "dir": "00_CORTEX_HQ",
        "inputs": ["IN_VIDEO_SOURCE"],
        "outputs": [],
        "codebase": "CODEBASE",
        "key_files": ["EXO_00_CORTEX.py", "EXO_00_CORTEX_PRODUCTION.ipynb"],
    },
    "U01": {
        "name": "ANIMATION_ENGINE",
        "dir": "01_ANIMATION_ENGINE",
        "inputs": ["IN_CORTEX_JSON/actor_models", "IN_CORTEX_JSON/body_motions",
                   "IN_CORTEX_JSON/source_videos", "IN_MIXAMO_BASE"],
        "outputs": ["OUT_MOTION_DATA"],
        "codebase": "CODEBASE",
        "key_files": ["EXO_01_TRANSMUTATION.py", "EXO_01_PRODUCTION.ipynb"],
    },
    "U02": {
        "name": "LOGISTICS_DEPOT",
        "dir": "02_LOGISTICS_DEPOT",
        "inputs": ["IN_MOTION_DATA", "IN_PROPS_LIBRARY", "IN_ROBLOX_AVATAR"],
        "outputs": ["OUT_BAKED_ACTORS"],
        "codebase": "CODEBASE",
        "key_files": ["EXO_02_LOGISTICS.py", "EXO_02_PRODUCTION.ipynb"],
    },
    "U03": {
        "name": "SCENOGRAPHY_DOCK",
        "dir": "03_SCENOGRAPHY_DOCK",
        "inputs": ["IN_CORTEX_JSON", "IN_MAP_RAW"],
        "outputs": ["OUT_PREMIUM_SCENE"],
        "codebase": "CODEBASE",
        "key_files": ["EXO_03_SCENOGRAPHY.py", "EXO_03_PRODUCTION.ipynb",
                      "layer_assembler.py", "geometry_probe_u03.py"],
    },
    "U04": {
        "name": "PHOTOGRAPHY_WING",
        "dir": "04_PHOTOGRAPHY_WING",
        "inputs": ["IN_SCENE_REF", "IN_VIDEO_SOURCE"],
        "outputs": [],
        "codebase": "CODEBASE",
        "key_files": ["EXO_04_PHOTOGRAPHY.py", "EXO_04_PRODUCTION.ipynb",
                      "render_forge.py", "camera_director.py"],
    },
    "U05": {
        "name": "ALCHEMIST_LAB",
        "dir": "05_ALCHEMIST_LAB",
        "inputs": ["IN_RAW_FRAMES", "IN_SOURCE_REF"],
        "outputs": ["OUT_FINAL_FRAMES"],
        "codebase": "CODEBASE",
        "key_files": ["EXO_05_ALCHEMIST.py", "EXO_05_PRODUCTION.ipynb"],
    },
    "U06": {
        "name": "AIRCRAFT_CARRIER",
        "dir": "06_AIRCRAFT_CARRIER",
        "inputs": ["IN_ASSEMBLY_KIT"],
        "outputs": ["OUT_FINAL_MOVIE"],
        "codebase": "CODEBASE",
        "key_files": ["EXO_06_CARRIER.py", "EXO_06_PRODUCTION.ipynb"],
    },
}


def resolve_path(fregate_id, folder, base=None):
    """
    Resout le chemin absolu d'un dossier dans une fregate.
    Retourne Path ou None si fregate inconnue.
    """
    if base is None:
        base = BASE_DIR
    fregate = FREGATE_MAP.get(fregate_id.upper())
    if not fregate:
        return None
    return base / fregate["dir"] / folder


def get_fregate_paths(fregate_id, base=None):
    """
    Retourne tous les chemins d'une fregate (inputs + outputs + codebase).
    """
    if base is None:
        base = BASE_DIR
    fregate = FREGATE_MAP.get(fregate_id.upper())
    if not fregate:
        return {"error": f"Fregate inconnue : {fregate_id}"}

    fregate_base = base / fregate["dir"]
    paths = {
        "fregate": fregate_id,
        "name": fregate["name"],
        "base": str(fregate_base),
        "codebase": str(fregate_base / fregate["codebase"]),
        "inputs": {d: str(fregate_base / d) for d in fregate["inputs"]},
        "outputs": {d: str(fregate_base / d) for d in fregate["outputs"]},
        "key_files": {f: str(fregate_base / fregate["codebase"] / f)
                      for f in fregate["key_files"]},
    }
    return paths


def get_pipeline_state():
    """Charge l'etat du pipeline depuis pipeline_state.json."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"error": "pipeline_state.json introuvable"}


def check_fregate_health(fregate_id, base=None):
    """
    Verifie que les dossiers et fichiers cles d'une fregate existent.
    """
    if base is None:
        base = BASE_DIR
    paths = get_fregate_paths(fregate_id, base)
    if "error" in paths:
        return paths

    checks = {}
    checks["base"] = Path(paths["base"]).exists()
    checks["codebase"] = Path(paths["codebase"]).exists()
    for name, p in paths["inputs"].items():
        checks[f"input:{name}"] = Path(p).exists()
    for name, p in paths["outputs"].items():
        checks[f"output:{name}"] = Path(p).exists()

    ok = sum(1 for v in checks.values() if v)
    total = len(checks)
    return {
        "fregate": fregate_id,
        "health": f"{ok}/{total}",
        "status": "OK" if ok == total else "PARTIAL",
        "checks": checks
    }


def main():
    args = sys.argv[1:]

    if not args or "--state" in args:
        state = get_pipeline_state()
        print(json.dumps(state, indent=2, ensure_ascii=False))

    elif "--paths" in args:
        idx = args.index("--paths")
        fregate_id = args[idx + 1] if idx + 1 < len(args) else None
        if not fregate_id:
            print("[ATLAS] Usage: --paths <fregate_id>")
            sys.exit(1)
        paths = get_fregate_paths(fregate_id)
        print(json.dumps(paths, indent=2, ensure_ascii=False))

    elif "--resolve" in args:
        idx = args.index("--resolve")
        if idx + 2 >= len(args):
            print("[ATLAS] Usage: --resolve <fregate_id> <folder>")
            sys.exit(1)
        fregate_id = args[idx + 1]
        folder = args[idx + 2]
        path = resolve_path(fregate_id, folder)
        print(str(path) if path else f"[ATLAS] Fregate inconnue : {fregate_id}")

    elif "--health" in args:
        idx = args.index("--health")
        fregate_id = args[idx + 1] if idx + 1 < len(args) else None
        if fregate_id:
            result = check_fregate_health(fregate_id)
        else:
            result = {fid: check_fregate_health(fid) for fid in FREGATE_MAP}
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
