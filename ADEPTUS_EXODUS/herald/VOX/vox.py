"""
VOX — Tech-Pretre P3 — Scribe de l'Empire
Role : Rapports flotte, tests Pytest, self-learning loop

Usage :
  python vox.py --report          # Rapport global de la flotte
  python vox.py --report U03      # Rapport d'une fregate
  python vox.py --test U03        # Tests Pytest sur une fregate
  python vox.py --learn           # Apprendre depuis les logs recents
  python vox.py --rules           # Afficher les regles apprises

Constitution : Les fregates produisent. Les Mini Programs servent.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent  # racine EXODUS-V2
ATLAS_PATH = Path(__file__).parent.parent.parent / "magos_logis" / "ATLAS"
VULKAN_MEMORY = Path(__file__).parent.parent.parent.parent / "VULKAN_FORGE" / "MEMORY"
RULES_FILE = Path(__file__).parent / "RULES.md"


def load_pipeline_state():
    state_file = ATLAS_PATH / "pipeline_state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def report_fregate(fregate_id, state=None):
    """Genere un rapport structure pour une fregate."""
    if state is None:
        state = load_pipeline_state()

    fregates = state.get("fregates", {})
    fregate = fregates.get(fregate_id.upper())
    if not fregate:
        return {"error": f"Fregate inconnue : {fregate_id}"}

    fregate_dirs = {
        "U00": "00_CORTEX_HQ",
        "U01": "01_ANIMATION_ENGINE",
        "U02": "02_LOGISTICS_DEPOT",
        "U03": "03_SCENOGRAPHY_DOCK",
        "U04": "04_PHOTOGRAPHY_WING",
        "U05": "05_ALCHEMIST_LAB",
        "U06": "06_AIRCRAFT_CARRIER",
    }

    fregate_dir = BASE / fregate_dirs.get(fregate_id.upper(), "")
    tracking_file = BASE / "TRACKING" / f"TRACKING_{fregate_id.upper()}.md"

    report = {
        "fregate": fregate_id.upper(),
        "name": fregate.get("name"),
        "status": fregate.get("status"),
        "last_output": fregate.get("last_output"),
        "blocking": fregate.get("blocking"),
        "dir_exists": fregate_dir.exists(),
        "tracking_exists": tracking_file.exists(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Compter fichiers codebase
    codebase = fregate_dir / "CODEBASE"
    if codebase.exists():
        py_files = list(codebase.glob("*.py"))
        report["codebase_py_files"] = len(py_files)
        report["codebase_files"] = [f.name for f in py_files]

    return report


def report_fleet():
    """Rapport global de toute la flotte."""
    state = load_pipeline_state()
    fregates = state.get("fregates", {})

    fleet_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline_health": state.get("pipeline_health", {}),
        "tech_pretres": state.get("tech_pretres", {}),
        "fregates": {}
    }

    for fid in sorted(fregates.keys()):
        fleet_report["fregates"][fid] = report_fregate(fid, state)

    # Compteurs
    validees = sum(1 for f in fregates.values() if f.get("status") == "VALIDE")
    en_attente = sum(1 for f in fregates.values() if f.get("status") == "EN_ATTENTE")

    fleet_report["summary"] = {
        "total": len(fregates),
        "validees": validees,
        "en_attente": en_attente,
        "taux_completion": f"{validees}/{len(fregates)}"
    }

    return fleet_report


def render_fleet_report(report):
    """Affiche un rapport de flotte lisible."""
    print("\n" + "=" * 60)
    print("  VOX — RAPPORT DE FLOTTE EXODUS")
    print(f"  {report['timestamp']}")
    print("=" * 60)

    summary = report.get("summary", {})
    print(f"\n  Fregates : {summary.get('taux_completion')} validees")

    health = report.get("pipeline_health", {})
    print(f"  Tech-Pretres : {health.get('tech_pretres_operationnels')}/{health.get('tech_pretres_total')} operationnels")
    print(f"  Checklist : {health.get('progression_checklist')}")

    print("\n  FREGATES :")
    for fid, frep in sorted(report.get("fregates", {}).items()):
        status = frep.get("status", "?")
        name = frep.get("name", "?")
        blocking = frep.get("blocking")
        icon = "V" if status == "VALIDE" else "~"
        line = f"    [{icon}] {fid} {name} — {status}"
        if blocking:
            line += f" [bloquant: {blocking}]"
        print(line)

    print("\n  TECH-PRETRES :")
    for name, tp in sorted(report.get("tech_pretres", {}).items()):
        s = tp.get("status", "?")
        p = tp.get("priorite", "?")
        icon = "V" if "OPERATIONNEL" in s else "~"
        print(f"    [{icon}] P{p} {name} — {s}")

    print("\n" + "=" * 60)


def main():
    args = sys.argv[1:]

    if not args or "--report" in args:
        idx = args.index("--report") if "--report" in args else -1
        if idx >= 0 and idx + 1 < len(args) and not args[idx + 1].startswith("--"):
            fregate_id = args[idx + 1]
            report = report_fregate(fregate_id)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            report = report_fleet()
            render_fleet_report(report)

    elif "--test" in args:
        idx = args.index("--test")
        fregate_id = args[idx + 1] if idx + 1 < len(args) else None
        from test_runner_vox import run_fregate_tests
        result = run_fregate_tests(fregate_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif "--learn" in args:
        from self_learner import run_learning_cycle
        result = run_learning_cycle()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif "--rules" in args:
        if RULES_FILE.exists():
            print(RULES_FILE.read_text())
        else:
            print("[VOX] Aucune regle apprise pour l'instant.")

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
