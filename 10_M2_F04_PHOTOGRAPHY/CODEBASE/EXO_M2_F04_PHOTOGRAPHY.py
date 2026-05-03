#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         MODE 2 — FRÉGATE M2_F04 — PHOTOGRAPHY (Cinématique Mode 2)          ║
║              Caméra + Éclairage pour Pipeline From Scratch                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0 — Phase 8 — Dual Pipeline Doctrine (03.05.2026)            ║
║  Loi R-01 : Copie indépendante Mode 2 — ZERO contamination Mode 1          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  INPUTS (IN_SCENE_BLEND/):                                                  ║
║    scene_ready.blend  (de M2_F03 — décor GLB + shadow catcher + HDRi)      ║
║  INPUTS (IN_PRODUCTION_PLAN/) [OPTIONNEL]:                                  ║
║    PRODUCTION_PLAN.JSON  (instructions caméra/éclairage — optionnel)       ║
║  OUTPUTS (OUT_CAMERA_READY/):                                               ║
║    scene_with_camera.blend  (scène prête pour M2_F05 / rendu)              ║
║  OUTPUTS (OUT_REPORT/):                                                     ║
║    m2_f04_report.json                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python EXO_M2_F04_PHOTOGRAPHY.py                          # Auto-détection
    python EXO_M2_F04_PHOTOGRAPHY.py --scene scene_ready.blend
    python EXO_M2_F04_PHOTOGRAPHY.py --preset preview --no-dof
    python EXO_M2_F04_PHOTOGRAPHY.py --dry-run --verbose
    python EXO_M2_F04_PHOTOGRAPHY.py --blender-path /path/to/blender
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

M2_F04_VERSION = "1.0.0"

FREGATE_DIR    = Path(__file__).resolve().parent.parent
CODEBASE_DIR   = Path(__file__).resolve().parent
IN_SCENE_DIR   = FREGATE_DIR / "IN_SCENE_BLEND"
IN_PLAN_DIR    = FREGATE_DIR / "IN_PRODUCTION_PLAN"
OUT_CAMERA_DIR = FREGATE_DIR / "OUT_CAMERA_READY"
OUT_REPORT_DIR = FREGATE_DIR / "OUT_REPORT"

BLENDER_SUBDIR   = "blender-4.0.0-linux-x64"
AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║    MODE 2 — FRÉGATE M2_F04 — PHOTOGRAPHY CINÉMATIQUE        ║
║    Caméra + Éclairage (Mode 2 From Scratch)                  ║
╠══════════════════════════════════════════════════════════════╣
║  R-01 : Copie étanche Mode 2                                 ║
╚══════════════════════════════════════════════════════════════╝"""


class M2F04Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []

    def info(self, msg):
        line = f"[M2_F04] {msg}"
        print(line)
        self.logs.append({"level": "INFO", "message": msg, "ts": datetime.now().isoformat()})

    def debug(self, msg):
        if self.verbose:
            line = f"[M2_F04:DBG] {msg}"
            print(line)
            self.logs.append({"level": "DEBUG", "message": msg, "ts": datetime.now().isoformat()})

    def error(self, msg):
        line = f"[M2_F04:ERR] {msg}"
        print(line, file=sys.stderr)
        self.logs.append({"level": "ERROR", "message": msg, "ts": datetime.now().isoformat()})

    def success(self, msg):
        line = f"[M2_F04:OK] ✓ {msg}"
        print(line)
        self.logs.append({"level": "SUCCESS", "message": msg, "ts": datetime.now().isoformat()})

    def warn(self, msg):
        line = f"[M2_F04:WARN] ⚠ {msg}"
        print(line)
        self.logs.append({"level": "WARN", "message": msg, "ts": datetime.now().isoformat()})

    def get_logs(self):
        return self.logs


# ─── Blender ─────────────────────────────────────────────────────────────────

def find_blender(drive_root: Path, logger: M2F04Logger, custom_path: str = None) -> str:
    if custom_path:
        bp = Path(custom_path)
        if bp.exists():
            logger.success(f"Blender custom: {bp}")
            return str(bp)
        logger.error(f"Blender custom introuvable: {bp}")
        sys.exit(1)

    bp = drive_root / AI_MODELS_SUBDIR / BLENDER_SUBDIR / "blender"
    if not bp.exists():
        logger.error(f"Blender introuvable: {bp}")
        logger.info(f"Placez Blender 4.0 Linux x64 dans: {drive_root / AI_MODELS_SUBDIR / BLENDER_SUBDIR}/")
        sys.exit(1)
    logger.success("Blender 4.0 vérifié")
    return str(bp)


# ─── Inputs ──────────────────────────────────────────────────────────────────

def find_scene_blend(logger: M2F04Logger, explicit: str = None) -> Path:
    """Résout le fichier scene_ready.blend en entrée."""
    if explicit:
        p = Path(explicit)
        if not p.exists():
            logger.error(f"Fichier .blend explicite introuvable: {p}")
            sys.exit(1)
        logger.success(f"Scene .blend: {p}")
        return p

    # Auto-détection dans IN_SCENE_BLEND/
    candidates = list(IN_SCENE_DIR.glob("*.blend"))
    if not candidates:
        logger.error(f"Aucun .blend dans {IN_SCENE_DIR}")
        logger.info("Placez le scene_ready.blend de M2_F03 dans IN_SCENE_BLEND/")
        sys.exit(1)

    if len(candidates) > 1:
        logger.warn(f"{len(candidates)} fichiers .blend trouvés — utilise le premier: {candidates[0].name}")
    logger.success(f"Scene .blend: {candidates[0].name}")
    return candidates[0]


def load_production_plan(logger: M2F04Logger) -> dict:
    """Charge PRODUCTION_PLAN.JSON si présent, sinon retourne plan vide."""
    candidates = list(IN_PLAN_DIR.glob("*.json")) + list(IN_PLAN_DIR.glob("*.JSON"))
    if not candidates:
        logger.info("Aucun PRODUCTION_PLAN.JSON — configuration caméra par défaut")
        return {}
    plan_path = candidates[0]
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        logger.success(f"Plan chargé: {plan_path.name}")
        return plan
    except Exception as e:
        logger.warn(f"Lecture plan échouée ({e}) — configuration par défaut")
        return {}


# ─── Blender Script ──────────────────────────────────────────────────────────

def run_blender_photography(
    blender_path: str,
    scene_blend: Path,
    plan: dict,
    output_dir: Path,
    logger: M2F04Logger,
    preset: str = "production",
    no_dof: bool = False,
    no_atmosphere: bool = False,
    shake_preset: str = "handheld",
) -> bool:
    """Lance Blender headless pour configurer caméra + éclairage."""
    director_script = CODEBASE_DIR / "camera_director.py"
    if not director_script.exists():
        logger.error(f"camera_director.py introuvable: {director_script}")
        return False

    # Config scène Mode 2 : si plan présent, prend la première scène
    scenes = plan.get("scenes", [])
    scene_config = scenes[0] if scenes else {
        "scene_id": "m2_scene_01",
        "camera": {"style": "static", "movement": "medium", "cuts": []},
        "lighting": {"style": "3point", "intensity": 1.0, "color_temp": 5500},
    }
    scene_config["_v2_options"] = {
        "camera_fov_json": None,
        "preset": preset,
        "no_atmosphere": no_atmosphere,
        "no_dof": no_dof,
        "shake_preset": shake_preset,
    }
    scene_id = scene_config.get("scene_id", "m2_scene_01")
    scene_config_json = json.dumps(scene_config)

    cmd = [
        blender_path,
        "--background",
        str(scene_blend),
        "--python", str(director_script),
        "--",
        "--scene-config", scene_config_json,
        "--output-dir", str(output_dir),
        "--scene-id", str(scene_id),
    ]

    logger.info(f"Lancement Blender — scène {scene_id}...")
    logger.debug(f"Cmd: {' '.join(cmd[:6])}...")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Blender échoué (code {result.returncode})")
        logger.error(f"STDERR: {result.stderr[-2000:] if result.stderr else 'N/A'}")
        return False

    logger.success(f"Scène {scene_id} configurée")
    return True


# ─── Rapport ─────────────────────────────────────────────────────────────────

def write_report(output_dir: Path, scene_blend: Path, success: bool, logger: M2F04Logger, preset: str) -> dict:
    report = {
        "fregate": "M2_F04",
        "version": M2_F04_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "inputs": {"scene_blend": str(scene_blend)},
        "outputs": {
            "scene_with_camera": str(output_dir / "scene_with_camera.blend") if success else None,
        },
        "config": {"preset": preset},
        "logs": logger.get_logs(),
    }
    OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUT_REPORT_DIR / "m2_f04_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.success(f"Rapport: {report_path}")
    return report


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"MODE 2 — FRÉGATE M2_F04 PHOTOGRAPHY v{M2_F04_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_M2_F04_PHOTOGRAPHY.py
  python EXO_M2_F04_PHOTOGRAPHY.py --scene scene_ready.blend --preset preview
  python EXO_M2_F04_PHOTOGRAPHY.py --no-dof --shake-preset subtle --verbose
        """
    )
    parser.add_argument("--drive-root", default=str(FREGATE_DIR.parent),
                        help="Racine du Drive EXODUS (pour localiser Blender)")
    parser.add_argument("--scene",
                        help="Chemin explicite vers le .blend de M2_F03")
    parser.add_argument("--blender-path",
                        help="Chemin custom vers l'exécutable Blender")
    parser.add_argument("--preset", default="production",
                        choices=["production", "preview"],
                        help="Preset Cycles (défaut: production)")
    parser.add_argument("--no-dof", action="store_true",
                        help="Désactiver Auto-DOF")
    parser.add_argument("--no-atmosphere", action="store_true",
                        help="Désactiver Volume Scatter + lampes invisibles")
    parser.add_argument("--shake-preset", default="handheld",
                        choices=["handheld", "subtle", "aggressive"],
                        help="Preset shake caméra (défaut: handheld)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Valider les chemins sans exécuter Blender")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Logs détaillés")

    args = parser.parse_args()
    logger = M2F04Logger(verbose=args.verbose)

    print(BANNER)
    print(f"\n  Version {M2_F04_VERSION} | Phase 8 — Dual Pipeline Mode 2\n")

    drive_root  = Path(args.drive_root)
    scene_blend = find_scene_blend(logger, args.scene)
    plan        = load_production_plan(logger)
    blender     = find_blender(drive_root, logger, args.blender_path)

    OUT_CAMERA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Scene blend  : {scene_blend}")
    logger.info(f"Output dir   : {OUT_CAMERA_DIR}")
    logger.info(f"Preset       : {args.preset}")
    logger.info(f"DOF          : {'OFF' if args.no_dof else 'ON'}")
    logger.info(f"Atmosphere   : {'OFF' if args.no_atmosphere else 'ON'}")
    logger.info(f"Shake        : {args.shake_preset}")

    if args.dry_run:
        logger.info("Mode dry-run : tout est valide, arrêt avant Blender")
        print("\n✓ M2_F04 prête. Tous les chemins sont valides.")
        sys.exit(0)

    success = run_blender_photography(
        blender_path=blender,
        scene_blend=scene_blend,
        plan=plan,
        output_dir=OUT_CAMERA_DIR,
        logger=logger,
        preset=args.preset,
        no_dof=args.no_dof,
        no_atmosphere=args.no_atmosphere,
        shake_preset=args.shake_preset,
    )

    write_report(OUT_CAMERA_DIR, scene_blend, success, logger, args.preset)

    print("\n" + "=" * 66)
    if success:
        logger.success("M2_F04 PHOTOGRAPHY COMPLÈTE")
        print(f"  → Output : {OUT_CAMERA_DIR}/scene_with_camera.blend")
        print(f"  → Rapport: {OUT_REPORT_DIR}/m2_f04_report.json")
    else:
        logger.error("M2_F04 PHOTOGRAPHY ÉCHOUÉE — consultez le rapport")
        sys.exit(1)
    print("=" * 66)


if __name__ == "__main__":
    main()
