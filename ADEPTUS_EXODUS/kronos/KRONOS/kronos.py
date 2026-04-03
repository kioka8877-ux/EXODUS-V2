"""
KRONOS — Tech-Pretre P4 — Gardien de la Coherence
Role : Audit de coherence toutes fregates, parity check,
       registre global d'execution

Usage :
  python kronos.py --audit              # Audit complet de la flotte
  python kronos.py --parity U03 U04     # Parity check entre deux fregates
  python kronos.py --registry           # Voir le registre global
  python kronos.py --seal               # Sceller l'etat actuel (snapshot)

Constitution : Les fregates produisent. Les Mini Programs servent.
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent
ATLAS_PATH = BASE / "ADEPTUS_EXODUS" / "magos_logis" / "ATLAS"
VOX_PATH = BASE / "ADEPTUS_EXODUS" / "herald" / "VOX"
REGISTRY_FILE = Path(__file__).parent / "execution_registry.json"
PARITY_CHECKER = Path(__file__).parent / "parity_checker.py"


def load_pipeline_state():
    state_file = ATLAS_PATH / "pipeline_state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def audit_fregate(fregate_id, state=None):
    """
    Audit complet d'une fregate :
    - Dossier present ?
    - Fichiers cles presents ?
    - TRACKING_.md present ?
    - Derniere entree du registre ?
    """
    if state is None:
        state = load_pipeline_state()

    fregate_id = fregate_id.upper()
    fregate_dirs = {
        "U00": "00_CORTEX_HQ",
        "U01": "01_ANIMATION_ENGINE",
        "U02": "02_LOGISTICS_DEPOT",
        "U03": "03_SCENOGRAPHY_DOCK",
        "U04": "04_PHOTOGRAPHY_WING",
        "U05": "05_ALCHEMIST_LAB",
        "U06": "06_AIRCRAFT_CARRIER",
    }

    fregate_dir = BASE / fregate_dirs.get(fregate_id, "")
    tracking_file = BASE / "TRACKING" / f"TRACKING_{fregate_id}.md"
    pipeline_info = state.get("fregates", {}).get(fregate_id, {})

    checks = {
        "dir_exists": fregate_dir.exists(),
        "codebase_exists": (fregate_dir / "CODEBASE").exists(),
        "tracking_md_exists": tracking_file.exists(),
        "readme_dev_exists": (fregate_dir / "README_DEV.md").exists(),
        "subplan_exists": (fregate_dir / f"UNIT_{fregate_id[1:]}_SUBPLAN.md").exists(),
        "pipeline_state_known": bool(pipeline_info),
    }

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    coherence = round(passed / total * 100)

    return {
        "fregate": fregate_id,
        "name": pipeline_info.get("name", "?"),
        "status": pipeline_info.get("status", "UNKNOWN"),
        "coherence": f"{coherence}%",
        "score": f"{passed}/{total}",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


def audit_full_fleet():
    """Audit coherence de toute la flotte."""
    state = load_pipeline_state()
    fregates = list(state.get("fregates", {}).keys())

    if not fregates:
        fregates = ["U00", "U01", "U02", "U03", "U04", "U05", "U06"]

    results = {}
    for fid in sorted(fregates):
        results[fid] = audit_fregate(fid, state)

    # Score global
    scores = [r["score"] for r in results.values()]
    total_passed = sum(int(s.split("/")[0]) for s in scores)
    total_checks = sum(int(s.split("/")[1]) for s in scores)
    global_coherence = round(total_passed / total_checks * 100) if total_checks else 0

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "global_coherence": f"{global_coherence}%",
        "total_score": f"{total_passed}/{total_checks}",
        "fregates": results,
    }


def audit_tech_pretres():
    """Audit coherence des Tech-Pretres."""
    state = load_pipeline_state()
    tech_pretres_dirs = {
        "SENTINEL": BASE / "SENTINEL_CORE",
        "VULKAN_FORGE": BASE / "VULKAN_FORGE",
        "VOID_FLUSH": BASE / "ADEPTUS_EXODUS" / "magos_physic" / "VOID-FLUSH",
        "ATLAS": BASE / "ADEPTUS_EXODUS" / "magos_logis" / "ATLAS",
        "VOX": BASE / "ADEPTUS_EXODUS" / "herald" / "VOX",
        "KRONOS": BASE / "ADEPTUS_EXODUS" / "kronos" / "KRONOS",
    }

    results = {}
    for name, path in tech_pretres_dirs.items():
        results[name] = {
            "exists": path.exists(),
            "py_files": len(list(path.glob("*.py"))) if path.exists() else 0,
            "md_files": len(list(path.glob("*.md"))) if path.exists() else 0,
            "status": state.get("tech_pretres", {}).get(name, {}).get("status", "UNKNOWN"),
        }

    return results


def seal_state():
    """
    Scelle l'etat actuel de l'Empire dans le registre.
    Snapshot immutable avec timestamp.
    """
    fleet_audit = audit_full_fleet()
    tp_audit = audit_tech_pretres()

    seal = {
        "seal_id": f"SEAL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.utcnow().isoformat(),
        "sealed_by": "KRONOS",
        "validated_by": "Empereur",
        "fleet_coherence": fleet_audit["global_coherence"],
        "fleet_score": fleet_audit["total_score"],
        "tech_pretres_present": sum(1 for v in tp_audit.values() if v["exists"]),
        "snapshot": {
            "fleet": fleet_audit["fregates"],
            "tech_pretres": tp_audit,
        }
    }

    # Charger registre existant
    registry = load_registry()
    registry.setdefault("seals", []).append(seal)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

    return {"status": "SEALED", "seal_id": seal["seal_id"], "coherence": seal["fleet_coherence"]}


def load_registry():
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {"seals": [], "executions": []}


def log_execution(fregate_id, action, result, duration_s=None):
    """Loggue une execution dans le registre."""
    registry = load_registry()
    entry = {
        "id": len(registry.get("executions", [])) + 1,
        "fregate": fregate_id,
        "action": action,
        "result": result,
        "duration_s": duration_s,
        "timestamp": datetime.utcnow().isoformat(),
    }
    registry.setdefault("executions", []).append(entry)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    return entry


def print_audit_report(audit):
    """Affiche un rapport d'audit lisible."""
    print("\n" + "=" * 60)
    print("  KRONOS — AUDIT DE COHERENCE EMPIRE")
    print(f"  {audit['timestamp']}")
    print(f"  Coherence globale : {audit['global_coherence']} ({audit['total_score']})")
    print("=" * 60)

    for fid, r in sorted(audit["fregates"].items()):
        icon = "V" if int(r["coherence"].rstrip("%")) >= 80 else "!"
        print(f"  [{icon}] {fid} {r['name']} — {r['coherence']} ({r['score']}) — {r['status']}")
        failures = [k for k, v in r["checks"].items() if not v]
        for f in failures:
            print(f"       MANQUE: {f}")

    print("=" * 60)


def main():
    args = sys.argv[1:]

    if not args or "--audit" in args:
        audit = audit_full_fleet()
        print_audit_report(audit)

    elif "--parity" in args:
        idx = args.index("--parity")
        fids = args[idx + 1:idx + 3]
        if len(fids) < 2:
            print("[KRONOS] Usage: --parity <F1> <F2>")
            sys.exit(1)
        import importlib.util
        spec = importlib.util.spec_from_file_location("parity", str(PARITY_CHECKER))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.check_parity(fids[0], fids[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif "--registry" in args:
        registry = load_registry()
        seals = registry.get("seals", [])
        executions = registry.get("executions", [])
        print(f"\n[KRONOS] Registre : {len(seals)} sceaux, {len(executions)} executions")
        if seals:
            last = seals[-1]
            print(f"  Dernier sceau : {last['seal_id']} — {last['fleet_coherence']}")

    elif "--seal" in args:
        result = seal_state()
        print(json.dumps(result, indent=2))

    elif "--tech-pretres" in args:
        result = audit_tech_pretres()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
