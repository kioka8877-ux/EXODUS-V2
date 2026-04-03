"""
VOX — Test Runner
Role : Suite de tests de validation par fregate
       Verifie structure, fichiers cles, contrats entree/sortie

Usage :
  python test_runner_vox.py --all
  python test_runner_vox.py --fregate U03
  python test_runner_vox.py --fregate U04 --verbose
"""

import sys
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent


# Contrats attendus par fregate
FREGATE_CONTRACTS = {
    "U00": {
        "required_files": ["EXO_00_CORTEX.py", "EXO_00_CORTEX_PRODUCTION.ipynb"],
        "required_dirs": ["IN_VIDEO_SOURCE"],
        "optional_dirs": [],
    },
    "U01": {
        "required_files": ["EXO_01_TRANSMUTATION.py", "EXO_01_PRODUCTION.ipynb"],
        "required_dirs": ["IN_CORTEX_JSON/actor_models", "OUT_MOTION_DATA"],
        "optional_dirs": ["IN_MIXAMO_BASE"],
    },
    "U02": {
        "required_files": ["EXO_02_LOGISTICS.py", "EXO_02_PRODUCTION.ipynb"],
        "required_dirs": ["IN_MOTION_DATA", "OUT_BAKED_ACTORS"],
        "optional_dirs": ["IN_PROPS_LIBRARY"],
    },
    "U03": {
        "required_files": [
            "EXO_03_SCENOGRAPHY.py",
            "EXO_03_PRODUCTION.ipynb",
            "layer_assembler.py",
            "geometry_probe_u03.py",
            "depth_map_cleaner.py",
        ],
        "required_dirs": ["IN_CORTEX_JSON", "IN_MAP_RAW", "OUT_PREMIUM_SCENE"],
        "optional_dirs": [],
    },
    "U04": {
        "required_files": [
            "EXO_04_PHOTOGRAPHY.py",
            "EXO_04_PRODUCTION.ipynb",
            "render_forge.py",
            "camera_director.py",
            "lighting_rig.py",
        ],
        "required_dirs": ["IN_SCENE_REF", "IN_VIDEO_SOURCE"],
        "optional_dirs": [],
    },
    "U05": {
        "required_files": [
            "EXO_05_ALCHEMIST.py",
            "EXO_05_PRODUCTION.ipynb",
            "color_grader.py",
            "denoiser.py",
        ],
        "required_dirs": ["IN_RAW_FRAMES", "OUT_FINAL_FRAMES"],
        "optional_dirs": ["IN_SOURCE_REF", "LUTS"],
    },
    "U06": {
        "required_files": [
            "EXO_06_CARRIER.py",
            "EXO_06_PRODUCTION.ipynb",
            "final_encoder.py",
            "sequence_assembler.py",
        ],
        "required_dirs": ["IN_ASSEMBLY_KIT", "OUT_FINAL_MOVIE"],
        "optional_dirs": [],
    },
}

FREGATE_DIRS = {
    "U00": "00_CORTEX_HQ",
    "U01": "01_ANIMATION_ENGINE",
    "U02": "02_LOGISTICS_DEPOT",
    "U03": "03_SCENOGRAPHY_DOCK",
    "U04": "04_PHOTOGRAPHY_WING",
    "U05": "05_ALCHEMIST_LAB",
    "U06": "06_AIRCRAFT_CARRIER",
}


def run_fregate_tests(fregate_id, verbose=False):
    """
    Execute les tests de validation pour une fregate.
    Retourne un rapport structure.
    """
    fregate_id = fregate_id.upper()
    contract = FREGATE_CONTRACTS.get(fregate_id)
    fregate_dir_name = FREGATE_DIRS.get(fregate_id)

    if not contract or not fregate_dir_name:
        return {"fregate": fregate_id, "status": "UNKNOWN", "error": "Fregate non repertoriee"}

    fregate_base = BASE / fregate_dir_name
    codebase = fregate_base / "CODEBASE"

    tests = []

    # Test 1 : dossier fregate existe
    tests.append({
        "test": "fregate_dir_exists",
        "passed": fregate_base.exists(),
        "path": str(fregate_base),
    })

    # Test 2 : dossier CODEBASE existe
    tests.append({
        "test": "codebase_exists",
        "passed": codebase.exists(),
        "path": str(codebase),
    })

    # Test 3 : fichiers cles presents
    for fname in contract["required_files"]:
        fpath = codebase / fname
        tests.append({
            "test": f"file:{fname}",
            "passed": fpath.exists(),
            "path": str(fpath),
            "required": True,
        })

    # Test 4 : dossiers requis presents
    for dname in contract["required_dirs"]:
        dpath = fregate_base / dname
        tests.append({
            "test": f"dir:{dname}",
            "passed": dpath.exists(),
            "path": str(dpath),
            "required": True,
        })

    # Test 5 : syntaxe Python des fichiers .py
    if codebase.exists():
        for pyfile in codebase.glob("*.py"):
            try:
                with open(pyfile) as f:
                    compile(f.read(), str(pyfile), "exec")
                syntax_ok = True
                syntax_error = None
            except SyntaxError as e:
                syntax_ok = False
                syntax_error = str(e)
            tests.append({
                "test": f"syntax:{pyfile.name}",
                "passed": syntax_ok,
                "error": syntax_error,
                "required": False,
            })

    passed = sum(1 for t in tests if t["passed"])
    failed = [t for t in tests if not t["passed"] and t.get("required", True)]
    total = len(tests)

    report = {
        "fregate": fregate_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "OK" if not failed else "FAIL",
        "score": f"{passed}/{total}",
        "required_failures": len(failed),
        "tests": tests if verbose else None,
        "failures": failed if failed else None,
    }

    return report


def run_all_tests(verbose=False):
    """Lance les tests sur toutes les fregates."""
    results = {}
    for fid in sorted(FREGATE_CONTRACTS.keys()):
        results[fid] = run_fregate_tests(fid, verbose=verbose)
    return results


def print_summary(results):
    print("\n" + "=" * 50)
    print("  VOX — RAPPORT TESTS FREGATES")
    print("=" * 50)
    for fid, r in sorted(results.items()):
        status = r.get("status", "?")
        score = r.get("score", "?")
        icon = "V" if status == "OK" else "X"
        failures = r.get("required_failures", 0)
        line = f"  [{icon}] {fid} — {score} — {status}"
        if failures:
            line += f" ({failures} echecs requis)"
        print(line)
    print("=" * 50)


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv

    if "--all" in sys.argv:
        results = run_all_tests(verbose=verbose)
        print_summary(results)
        if verbose:
            print(json.dumps(results, indent=2, ensure_ascii=False))

    elif "--fregate" in sys.argv:
        idx = sys.argv.index("--fregate")
        fid = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if fid:
            result = run_fregate_tests(fid, verbose=verbose)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --fregate <fregate_id>")
    else:
        print(__doc__)
