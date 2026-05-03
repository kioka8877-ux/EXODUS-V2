#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           MODE 2 — FRÉGATE M2_F02 — LOGISTICS (Armurerie Mode 2)            ║
║                  Attachement Props → Avatar GLB Équipé                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0 — Phase 8 — Dual Pipeline Doctrine (03.05.2026)            ║
║  Loi R-01 : Copie indépendante Mode 2 — ZERO contamination Mode 1          ║
║  Loi R-03 : Durée audio <= durée animation (animation prime)                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  INPUTS (IN_GLB_AVATAR/):                                                   ║
║    avatar_validated.glb  (de M2_F01 — GLB Roblox animé validé)             ║
║  INPUTS (IN_PROPS_LIBRARY/) [OPTIONNEL]:                                    ║
║    *.glb / *.fbx / *.blend  (arsenal de props)                              ║
║  INPUTS (IN_PRODUCTION_PLAN/) [OPTIONNEL]:                                  ║
║    PRODUCTION_PLAN.JSON  (instructions props — bypass auto si absent)       ║
║  OUTPUTS (OUT_BAKED_ACTORS/):                                               ║
║    actor_equipped.abc + actor_equipped.blend                                ║
║  OUTPUTS (OUT_REPORT/):                                                     ║
║    m2_f02_report.json                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python EXO_M2_F02_LOGISTICS.py                         # Auto-détection
    python EXO_M2_F02_LOGISTICS.py --glb avatar.glb        # GLB explicite
    python EXO_M2_F02_LOGISTICS.py --bypass                # Bypass props
    python EXO_M2_F02_LOGISTICS.py --dry-run --verbose
    python EXO_M2_F02_LOGISTICS.py --blender-path /path/to/blender
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

M2_F02_VERSION = "1.0.0"

FREGATE_DIR    = Path(__file__).resolve().parent.parent
CODEBASE_DIR   = Path(__file__).resolve().parent
IN_GLB_DIR     = FREGATE_DIR / "IN_GLB_AVATAR"
IN_PROPS_DIR   = FREGATE_DIR / "IN_PROPS_LIBRARY"
IN_PLAN_DIR    = FREGATE_DIR / "IN_PRODUCTION_PLAN"
OUT_BAKED_DIR  = FREGATE_DIR / "OUT_BAKED_ACTORS"
OUT_REPORT_DIR = FREGATE_DIR / "OUT_REPORT"

BLENDER_SUBDIR = "blender-4.0.0-linux-x64"
AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"

BANNER = """
╔══════════════════════════════════════════════════════════╗
║    MODE 2 — FRÉGATE M2_F02 — LOGISTICS ARMURERIE        ║
║    Attachement Props → Avatar GLB (Mode 2 From Scratch)  ║
╠══════════════════════════════════════════════════════════╣
║  R-01 : Copie étanche Mode 2                             ║
║  R-03 : Audio prime sur animation GLB                    ║
╚══════════════════════════════════════════════════════════╝
"""


# ──────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────

class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.entries = []

    def info(self, msg: str):
        print(f"[M2_F02] {msg}")
        self.entries.append({"level": "INFO", "message": msg, "ts": datetime.now().isoformat()})

    def debug(self, msg: str):
        if self.verbose:
            print(f"[M2_F02:DBG] {msg}")
        self.entries.append({"level": "DEBUG", "message": msg, "ts": datetime.now().isoformat()})

    def ok(self, msg: str):
        print(f"[M2_F02:OK] {msg}")
        self.entries.append({"level": "SUCCESS", "message": msg, "ts": datetime.now().isoformat()})

    def warn(self, msg: str):
        print(f"[M2_F02:WARN] {msg}")
        self.entries.append({"level": "WARN", "message": msg, "ts": datetime.now().isoformat()})

    def error(self, msg: str):
        print(f"[M2_F02:ERR] {msg}", file=sys.stderr)
        self.entries.append({"level": "ERROR", "message": msg, "ts": datetime.now().isoformat()})

    def section(self, title: str):
        bar = "─" * (len(title) + 4)
        print(f"\n┌{bar}┐")
        print(f"│  {title}  │")
        print(f"└{bar}┘")

    def get_logs(self):
        return self.entries


# ──────────────────────────────────────────────────────────────
# BLENDER DISCOVERY
# ──────────────────────────────────────────────────────────────

def find_blender(log: Logger, custom_path: str = None) -> str:
    """Retourne le chemin vers Blender ou quitte."""
    # 1. Chemin custom
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            log.ok(f"Blender custom: {p}")
            return str(p)
        log.error(f"Blender custom introuvable: {p}")
        sys.exit(1)

    # 2. Drive EXODUS standard
    drive_candidates = [
        Path("/content/drive/MyDrive") / "DRIVE_EXODUS_V2",
        Path.home() / "DRIVE_EXODUS_V2",
        Path("/mnt/drive") / "DRIVE_EXODUS_V2",
    ]
    for drive in drive_candidates:
        p = drive / AI_MODELS_SUBDIR / BLENDER_SUBDIR / "blender"
        if p.exists():
            log.ok(f"Blender: {p}")
            return str(p)

    # 3. PATH système
    for candidate in ["blender", "blender4", "/usr/bin/blender"]:
        result = shutil.which(candidate)
        if result:
            log.ok(f"Blender système: {result}")
            return result

    log.error("Blender 4.0 introuvable — spécifiez --blender-path")
    sys.exit(1)


# ──────────────────────────────────────────────────────────────
# PRODUCTION PLAN
# ──────────────────────────────────────────────────────────────

def load_production_plan(log: Logger) -> dict | None:
    """Charge le PRODUCTION_PLAN.JSON depuis IN_PRODUCTION_PLAN/ si présent."""
    candidates = list(IN_PLAN_DIR.glob("PRODUCTION_PLAN*.json")) + list(IN_PLAN_DIR.glob("*.json"))
    if not candidates:
        log.warn("Aucun PRODUCTION_PLAN.JSON dans IN_PRODUCTION_PLAN/ → bypass automatique")
        return None
    plan_path = candidates[0]
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        total_props = sum(len(s.get("props_actions", [])) for s in plan.get("scenes", []))
        log.ok(f"Plan chargé: {plan_path.name} — {len(plan.get('scenes', []))} scènes, {total_props} props actions")
        return plan
    except json.JSONDecodeError as e:
        log.error(f"JSON invalide dans {plan_path}: {e}")
        return None


def requires_logistics(plan: dict | None, force_bypass: bool) -> bool:
    """Détermine si le pipeline props est requis."""
    if force_bypass:
        return False
    if plan is None:
        return False
    # Check flag explicite
    if not plan.get("production_notes", {}).get("requires_u02", True):
        return False
    # Auto-détection — 0 props_actions
    total_props = sum(len(s.get("props_actions", [])) for s in plan.get("scenes", []))
    if total_props == 0:
        return False
    return True


# ──────────────────────────────────────────────────────────────
# PROPS MAPPING
# ──────────────────────────────────────────────────────────────

def build_props_mapping(plan: dict, log: Logger) -> dict:
    """Construit le mapping prop_id → chemin fichier depuis IN_PROPS_LIBRARY/."""
    required = set()
    for scene in plan.get("scenes", []):
        for action in scene.get("props_actions", []):
            if "prop_id" in action:
                required.add(action["prop_id"])

    log.info(f"Props requis: {len(required)}")

    supported = [".glb", ".gltf", ".fbx", ".blend", ".obj"]
    available = {}
    for ext in supported:
        for f in IN_PROPS_DIR.glob(f"*{ext}"):
            available[f.stem] = str(f)

    mapping = {}
    for pid in required:
        if pid in available:
            mapping[pid] = available[pid]
            log.debug(f"  ✓ {pid}: {available[pid]}")
        else:
            log.warn(f"  ✗ {pid}: introuvable dans IN_PROPS_LIBRARY/")
            placeholder = IN_PROPS_DIR / "generic_prop.glb"
            if placeholder.exists():
                mapping[pid] = str(placeholder)
                log.debug(f"  → {pid}: utilise generic_prop.glb")

    log.ok(f"Props mapping: {len(mapping)}/{len(required)} résolus")
    return mapping


# ──────────────────────────────────────────────────────────────
# BLENDER EXECUTION
# ──────────────────────────────────────────────────────────────

def run_blender_logistics(
    blender_path: str,
    glb_avatar: str,
    plan: dict | None,
    props_mapping: dict,
    output_name: str,
    log: Logger,
) -> bool:
    """Lance Blender headless pour l'attachement des props sur le GLB avatar."""
    log.section("BLENDER LOGISTICS ENGINE")

    socketing_script = CODEBASE_DIR / "socketing_engine.py"
    if not socketing_script.exists():
        log.error(f"socketing_engine.py introuvable: {socketing_script}")
        return False

    OUT_BAKED_DIR.mkdir(parents=True, exist_ok=True)

    plan_json = json.dumps(plan or {"scenes": []})
    props_json = json.dumps(props_mapping)

    cmd = [
        blender_path,
        "--background",
        "--python", str(socketing_script),
        "--",
        "--glb-avatar",    glb_avatar,
        "--production-plan", plan_json,
        "--props-mapping", props_json,
        "--output-dir",    str(OUT_BAKED_DIR),
        "--output-name",   output_name,
    ]

    log.debug(f"CMD: {cmd[0]} --background --python socketing_engine.py -- ...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            log.debug(f"  BPY: {line}")

    if result.returncode != 0:
        log.error(f"Blender échoué (code {result.returncode})")
        if result.stderr:
            log.error(f"STDERR: {result.stderr[-2000:]}")
        return False

    log.ok("Blender Logistics terminé")
    return True


# ──────────────────────────────────────────────────────────────
# BYPASS
# ──────────────────────────────────────────────────────────────

def run_bypass(glb_path: Path, plan: dict | None, output_name: str, log: Logger, reason: str):
    """Mode bypass — copie directe GLB vers OUT_BAKED_ACTORS sans Blender."""
    log.section("MODE BYPASS — Pas de props requis")
    OUT_BAKED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    out_glb = OUT_BAKED_DIR / f"{output_name}.glb"
    shutil.copy2(str(glb_path), str(out_glb))
    log.ok(f"Copie: {glb_path.name} → {out_glb.name}")

    report = {
        "version": M2_F02_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SKIPPED",
        "mode": "BYPASS",
        "reason": reason,
        "pipeline": "MODE_2",
        "input": {"glb_avatar": str(glb_path)},
        "output": {"glb": str(out_glb)},
        "next_fregate": "M2_F03_SCENOGRAPHY",
    }
    report_path = OUT_REPORT_DIR / "m2_f02_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    log.ok("M2_F02 BYPASS COMPLÉTÉ")
    print(f"  → GLB : {out_glb}")
    print(f"  → Rapport : {report_path}")
    print(f"  → Prochaine frégate : M2_F03_SCENOGRAPHY/IN_GLB_AVATAR/")
    print("=" * 70)


# ──────────────────────────────────────────────────────────────
# REPORT
# ──────────────────────────────────────────────────────────────

def write_report(
    glb_path: str,
    plan: dict | None,
    props_mapping: dict,
    output_name: str,
    success: bool,
    log: Logger,
):
    OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    missing = []
    if plan:
        all_pids = {a["prop_id"] for s in plan.get("scenes", []) for a in s.get("props_actions", []) if "prop_id" in a}
        missing = [p for p in all_pids if p not in props_mapping]

    report = {
        "version": M2_F02_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "pipeline": "MODE_2",
        "input": {
            "glb_avatar": glb_path,
            "scenes_count": len(plan.get("scenes", [])) if plan else 0,
            "props_resolved": len(props_mapping),
            "props_missing": missing,
        },
        "output": {
            "abc": f"{output_name}.abc" if success else None,
            "blend": f"{output_name}.blend" if success else None,
        },
        "next_fregate": "M2_F03_SCENOGRAPHY",
        "logs": log.get_logs(),
    }
    report_path = OUT_REPORT_DIR / "m2_f02_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.ok(f"Rapport: {report_path}")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"M2_F02 LOGISTICS — EXODUS Mode 2 v{M2_F02_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_M2_F02_LOGISTICS.py
  python EXO_M2_F02_LOGISTICS.py --glb avatar_validated.glb
  python EXO_M2_F02_LOGISTICS.py --bypass
  python EXO_M2_F02_LOGISTICS.py --dry-run --verbose
        """,
    )
    parser.add_argument("--glb", "--glb-avatar", dest="glb",
                        help="Fichier GLB avatar (auto-détecté dans IN_GLB_AVATAR/ si omis)")
    parser.add_argument("--bypass", action="store_true",
                        help="Bypass props — copie directe vers OUT_BAKED_ACTORS/")
    parser.add_argument("--output-name", default="actor_equipped",
                        help="Nom des fichiers output (défaut: actor_equipped)")
    parser.add_argument("--blender-path",
                        help="Chemin custom vers Blender")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validation des inputs sans exécution")

    args = parser.parse_args()
    log = Logger(verbose=args.verbose)

    print(BANNER)
    print(f"  Version  : {M2_F02_VERSION}")
    print(f"  Frégate  : 08_M2_F02_LOGISTICS")
    print(f"  Pipeline : MODE 2 — FROM SCRATCH")
    print()

    # ── 1. Résoudre GLB avatar ──────────────────────────────────────────
    log.section("RÉSOLUTION INPUTS")

    if args.glb:
        glb_path = Path(args.glb)
        if not glb_path.is_absolute():
            glb_path = IN_GLB_DIR / args.glb
    else:
        glbs = sorted(IN_GLB_DIR.glob("*.glb"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not glbs:
            log.error("Aucun .glb dans IN_GLB_AVATAR/ et --glb non spécifié")
            log.info("Déposez avatar_validated.glb (de M2_F01) dans IN_GLB_AVATAR/")
            sys.exit(1)
        glb_path = glbs[0]
        log.info(f"GLB auto-détecté: {glb_path.name}")

    if not glb_path.exists():
        log.error(f"GLB introuvable: {glb_path}")
        sys.exit(1)
    log.ok(f"GLB avatar: {glb_path}")

    # ── 2. Production plan ─────────────────────────────────────────────
    plan = load_production_plan(log)

    # ── 3. Décision bypass ─────────────────────────────────────────────
    run_logistics = requires_logistics(plan, args.bypass)

    if not run_logistics:
        if args.bypass:
            reason = "bypass CLI (--bypass)"
        elif plan is None:
            reason = "Aucun PRODUCTION_PLAN.JSON fourni — bypass automatique"
        elif not plan.get("production_notes", {}).get("requires_u02", True):
            reason = "requires_u02 == false dans PRODUCTION_PLAN.JSON"
        else:
            reason = "0 props_actions détectées dans le plan"

        log.info(f"Bypass déclenché: {reason}")
        run_bypass(glb_path, plan, args.output_name, log, reason)
        return 0

    # ── 4. Props mapping ───────────────────────────────────────────────
    log.section("RÉSOLUTION PROPS")
    props_mapping = build_props_mapping(plan, log)

    log.info(f"GLB Avatar : {glb_path}")
    log.info(f"Output Dir : {OUT_BAKED_DIR}")
    log.info(f"Output Name: {args.output_name}")

    if args.dry_run:
        log.section("DRY-RUN — Arrêt avant traitement")
        print("\n✓ Tous les inputs sont valides.")
        print(f"  Scènes      : {len(plan.get('scenes', []))}")
        total_pa = sum(len(s.get("props_actions", [])) for s in plan.get("scenes", []))
        print(f"  Props actions: {total_pa}")
        print(f"  Props résolus: {len(props_mapping)}")
        return 0

    # ── 5. Blender ─────────────────────────────────────────────────────
    blender_path = find_blender(log, args.blender_path)

    success = run_blender_logistics(
        blender_path,
        str(glb_path),
        plan,
        props_mapping,
        args.output_name,
        log,
    )

    # ── 6. Rapport ─────────────────────────────────────────────────────
    write_report(str(glb_path), plan, props_mapping, args.output_name, success, log)

    if not success:
        log.error("Équipement props échoué")
        sys.exit(1)

    print("\n" + "=" * 70)
    log.ok("M2_F02 LOGISTICS COMPLET")
    print(f"  → ABC   : {OUT_BAKED_DIR}/{args.output_name}.abc")
    print(f"  → Blend : {OUT_BAKED_DIR}/{args.output_name}.blend")
    print(f"  → Rapport : {OUT_REPORT_DIR}/m2_f02_report.json")
    print(f"  → Prochaine frégate : M2_F03_SCENOGRAPHY/IN_GLB_AVATAR/")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
