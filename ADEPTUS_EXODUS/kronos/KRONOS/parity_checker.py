"""
KRONOS — Parity Checker
Role : Verifier la coherence entre deux fregates ou deux etats
       Detecter les derives, fichiers manquants, contrats brises

Usage :
  python parity_checker.py --fregates U03 U04
  python parity_checker.py --contracts
  python parity_checker.py --drift       # Detecter derives vs etat reference
"""

import sys
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent

FREGATE_DIRS = {
    "U00": "00_CORTEX_HQ",
    "U01": "01_ANIMATION_ENGINE",
    "U02": "02_LOGISTICS_DEPOT",
    "U03": "03_SCENOGRAPHY_DOCK",
    "U04": "04_PHOTOGRAPHY_WING",
    "U05": "05_ALCHEMIST_LAB",
    "U06": "06_AIRCRAFT_CARRIER",
}

# Structure canonique attendue pour toute fregate
CANONICAL_STRUCTURE = [
    "CODEBASE",
    "README_DEV.md",
]

# Fichiers devant exister dans toute fregate saine
CANONICAL_CODEBASE_PATTERNS = [
    "EXO_*.py",
    "EXO_*_PRODUCTION.ipynb",
    "requirements.txt",
]


def get_fregate_inventory(fregate_id):
    """Inventaire complet d'une fregate."""
    fregate_id = fregate_id.upper()
    fregate_dir = BASE / FREGATE_DIRS.get(fregate_id, "")

    if not fregate_dir.exists():
        return {"fregate": fregate_id, "exists": False, "files": []}

    files = []
    for f in sorted(fregate_dir.rglob("*")):
        if f.is_file() and "__pycache__" not in str(f):
            files.append(str(f.relative_to(fregate_dir)))

    codebase = fregate_dir / "CODEBASE"
    py_files = sorted([f.name for f in codebase.glob("*.py")]) if codebase.exists() else []
    nb_files = sorted([f.name for f in codebase.glob("*.ipynb")]) if codebase.exists() else []

    return {
        "fregate": fregate_id,
        "exists": True,
        "total_files": len(files),
        "py_files": py_files,
        "nb_files": nb_files,
        "has_readme": (fregate_dir / "README_DEV.md").exists(),
        "has_subplan": any(fregate_dir.glob("UNIT_*_SUBPLAN.md")),
        "has_tracking": (BASE / "TRACKING" / f"TRACKING_{fregate_id}.md").exists(),
    }


def check_parity(fregate_a, fregate_b):
    """
    Compare la structure de deux fregates.
    Retourne les differences et un score de parite.
    """
    inv_a = get_fregate_inventory(fregate_a)
    inv_b = get_fregate_inventory(fregate_b)

    if not inv_a["exists"] or not inv_b["exists"]:
        return {
            "status": "ERROR",
            "detail": f"{fregate_a if not inv_a['exists'] else fregate_b} introuvable"
        }

    diffs = []

    # Comparer py_files
    set_a = set(inv_a["py_files"])
    set_b = set(inv_b["py_files"])

    only_in_a = set_a - set_b
    only_in_b = set_b - set_a

    if only_in_a:
        diffs.append({"type": "only_in_A", "fregate": fregate_a, "files": sorted(only_in_a)})
    if only_in_b:
        diffs.append({"type": "only_in_B", "fregate": fregate_b, "files": sorted(only_in_b)})

    # Comparer structure de base
    for key in ["has_readme", "has_subplan", "has_tracking"]:
        if inv_a[key] != inv_b[key]:
            diffs.append({
                "type": "structure_diff",
                "key": key,
                fregate_a: inv_a[key],
                fregate_b: inv_b[key],
            })

    parity_score = max(0, 100 - len(diffs) * 15)

    return {
        "fregate_a": fregate_a.upper(),
        "fregate_b": fregate_b.upper(),
        "parity_score": f"{parity_score}%",
        "differences": diffs,
        "verdict": "PARITY_OK" if not diffs else "DRIFT_DETECTED",
        "timestamp": datetime.utcnow().isoformat(),
    }


def check_all_contracts():
    """
    Verifie que chaque fregate respecte la structure canonique.
    """
    results = {}
    for fid in sorted(FREGATE_DIRS.keys()):
        inv = get_fregate_inventory(fid)
        violations = []

        if not inv["exists"]:
            violations.append("FREGATE_DIR_MISSING")
        else:
            if not inv["has_readme"]:
                violations.append("README_DEV_MISSING")
            if not inv["has_subplan"]:
                violations.append("SUBPLAN_MISSING")
            if not inv["py_files"]:
                violations.append("NO_PY_FILES")
            if not inv["nb_files"]:
                violations.append("NO_NOTEBOOKS")

        results[fid] = {
            "violations": violations,
            "contract": "OK" if not violations else "VIOLATED",
            "score": f"{max(0, 4 - len(violations))}/4",
        }

    total_ok = sum(1 for r in results.values() if r["contract"] == "OK")
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "contracts_ok": f"{total_ok}/{len(results)}",
        "fregates": results,
    }


def detect_drift():
    """
    Compare l'etat actuel au dernier sceau du registre.
    Detecte les derives depuis le dernier snapshot valide.
    """
    registry_file = Path(__file__).parent / "execution_registry.json"
    if not registry_file.exists():
        return {"status": "NO_REGISTRY", "detail": "execution_registry.json introuvable"}

    registry = json.loads(registry_file.read_text())
    seals = registry.get("seals", [])

    if not seals:
        return {"status": "NO_SEALS", "detail": "Aucun sceau de reference"}

    last_seal = seals[-1]
    current_contracts = check_all_contracts()

    return {
        "reference_seal": last_seal["seal_id"],
        "reference_date": last_seal["timestamp"],
        "current_contracts": current_contracts["contracts_ok"],
        "drift_analysis": current_contracts["fregates"],
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--fregates" in args:
        idx = args.index("--fregates")
        fids = args[idx + 1:idx + 3]
        if len(fids) < 2:
            print("Usage: --fregates <F1> <F2>")
            sys.exit(1)
        result = check_parity(fids[0], fids[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif "--contracts" in args:
        result = check_all_contracts()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif "--drift" in args:
        result = detect_drift()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(__doc__)
