#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             EXO_04_PHOTOGRAPHY — CINÉMATIQUE DE LA FLOTTE EXODUS             ║
║              Tracking Caméra + Éclairage Cinématique Automatisés             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Configurer caméras et lumières selon PRODUCTION_PLAN.JSON          ║
║  Stack: Blender 4.0 Headless + Keyframe Animation + Light Rigs              ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS (fournis par l'Empereur):
    - environment_*.blend : Scènes environnement de U03
    - PRODUCTION_PLAN.JSON : Instructions caméra/éclairage du Cortex
    - actor_equipped.blend : Avatar équipé de U02 (optionnel, merge manuel)
    
OUTPUTS:
    - scene_ready_{scene_id}.blend : Scène prête au rendu
    - camera_data_{scene_id}.json : Export données caméra
    - photography_report.json : Log complet des opérations
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PHOTOGRAPHY_VERSION = "1.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"


class PhotographyLogger:
    """Logger structuré pour PHOTOGRAPHY WING."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []
    
    def info(self, msg: str):
        entry = f"[PHOTOGRAPHY] {msg}"
        print(entry)
        self.logs.append({"level": "INFO", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def debug(self, msg: str):
        if self.verbose:
            entry = f"[PHOTOGRAPHY:DEBUG] {msg}"
            print(entry)
            self.logs.append({"level": "DEBUG", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def error(self, msg: str):
        entry = f"[PHOTOGRAPHY:ERROR] {msg}"
        print(entry, file=sys.stderr)
        self.logs.append({"level": "ERROR", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def success(self, msg: str):
        entry = f"[PHOTOGRAPHY:OK] ✓ {msg}"
        print(entry)
        self.logs.append({"level": "SUCCESS", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def warn(self, msg: str):
        entry = f"[PHOTOGRAPHY:WARN] ⚠ {msg}"
        print(entry)
        self.logs.append({"level": "WARN", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def get_logs(self) -> list:
        return self.logs


def check_blender(drive_root: Path, logger: PhotographyLogger, custom_path: str = None) -> str:
    """
    Vérifie que Blender 4.0 est disponible.
    Retourne le chemin vers l'exécutable Blender.
    """
    if custom_path:
        blender_path = Path(custom_path)
        if blender_path.exists():
            logger.success(f"Blender custom trouvé: {blender_path}")
            return str(blender_path)
        else:
            logger.error(f"Blender custom introuvable: {blender_path}")
            sys.exit(1)
    
    ai_models_path = drive_root / AI_MODELS_SUBDIR
    blender_path = ai_models_path / BLENDER_SUBDIR / "blender"
    
    if not blender_path.exists():
        logger.error(f"Blender 4.0 introuvable: {blender_path}")
        logger.info("Téléchargez Blender 4.0 Linux x64 portable et placez-le dans:")
        logger.info(f"  {ai_models_path / BLENDER_SUBDIR}/")
        sys.exit(1)
    
    logger.success("Blender 4.0 vérifié")
    return str(blender_path)


def validate_production_plan(plan_path: Path, logger: PhotographyLogger) -> dict:
    """
    Valide et charge le PRODUCTION_PLAN.JSON.
    Vérifie la présence des sections camera et lighting.
    """
    if not plan_path.exists():
        logger.error(f"PRODUCTION_PLAN.JSON introuvable: {plan_path}")
        sys.exit(1)
    
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide dans {plan_path}: {e}")
        sys.exit(1)
    
    if "scenes" not in plan:
        logger.warn("Aucune scène trouvée dans le plan, création structure vide")
        plan["scenes"] = []
    
    total_cameras = 0
    total_cuts = 0
    total_lights = 0
    
    for scene in plan.get("scenes", []):
        if "camera" in scene:
            total_cameras += 1
            total_cuts += len(scene.get("camera", {}).get("cuts", []))
        if "lighting" in scene:
            total_lights += 1
    
    logger.success(f"Plan validé: {len(plan['scenes'])} scènes, {total_cameras} configs caméra, {total_cuts} cuts, {total_lights} configs lighting")
    return plan


def validate_environment_files(input_dir: Path, plan: dict, logger: PhotographyLogger) -> dict:
    """
    Vérifie que les fichiers environment.blend existent pour chaque scène.
    Retourne un mapping scene_id -> chemin fichier.
    """
    env_mapping = {}
    missing = []
    
    supported_extensions = [".blend"]
    available_files = {}
    
    for ext in supported_extensions:
        for f in input_dir.glob(f"*{ext}"):
            available_files[f.stem] = str(f)
    
    logger.debug(f"Fichiers .blend trouvés: {list(available_files.keys())}")
    
    for scene in plan.get("scenes", []):
        scene_id = scene.get("scene_id", "unknown")
        env_name = scene.get("environment_file", f"environment_{scene_id}")
        
        if env_name.endswith(".blend"):
            env_name = env_name[:-6]
        
        if env_name in available_files:
            env_mapping[scene_id] = available_files[env_name]
            logger.debug(f"  ✓ Scene {scene_id}: {env_name}.blend")
        else:
            for name, path in available_files.items():
                if "environment" in name.lower():
                    env_mapping[scene_id] = path
                    logger.debug(f"  → Scene {scene_id}: fallback to {name}.blend")
                    break
            else:
                missing.append(scene_id)
                logger.warn(f"  ✗ Scene {scene_id}: aucun environment.blend trouvé")
    
    if missing and available_files:
        default_blend = list(available_files.values())[0]
        for scene_id in missing:
            env_mapping[scene_id] = default_blend
            logger.warn(f"  → Scene {scene_id}: utilise {Path(default_blend).name} par défaut")
    
    logger.success(f"Environments résolus: {len(env_mapping)}/{len(plan.get('scenes', []))} scènes")
    return env_mapping


def run_blender_photography(
    blender_path: str,
    env_blend: str,
    scene_config: dict,
    output_dir: str,
    scene_id: str,
    logger: PhotographyLogger
) -> bool:
    """
    Exécute Blender en mode headless pour configurer caméra et éclairage.
    """
    logger.info(f"Traitement Scene {scene_id}...")
    
    script_dir = Path(__file__).parent
    director_script = script_dir / "camera_director.py"
    
    if not director_script.exists():
        logger.error(f"Script camera_director introuvable: {director_script}")
        return False
    
    scene_config_json = json.dumps(scene_config)
    
    cmd = [
        blender_path,
        "--background",
        env_blend,
        "--python", str(director_script),
        "--",
        "--scene-config", scene_config_json,
        "--output-dir", output_dir,
        "--scene-id", str(scene_id)
    ]
    
    logger.debug(f"Commande Blender: {' '.join(cmd[:6])}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Blender échoué (code {result.returncode})")
        logger.error(f"STDERR: {result.stderr[-2000:] if result.stderr else 'N/A'}")
        return False
    
    logger.debug(f"STDOUT: {result.stdout[-1000:] if result.stdout else 'N/A'}")
    logger.success(f"Scene {scene_id} configurée")
    return True


def generate_report(
    output_dir: Path,
    plan: dict,
    env_mapping: dict,
    results: dict,
    logger: PhotographyLogger
) -> dict:
    """
    Génère le rapport de production photography_report.json.
    """
    total_success = sum(1 for v in results.values() if v)
    total_failed = len(results) - total_success
    
    report = {
        "version": PHOTOGRAPHY_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if total_failed == 0 else "PARTIAL" if total_success > 0 else "FAILED",
        "summary": {
            "scenes_total": len(plan.get("scenes", [])),
            "scenes_processed": total_success,
            "scenes_failed": total_failed
        },
        "scenes": [],
        "logs": logger.get_logs()
    }
    
    for scene in plan.get("scenes", []):
        scene_id = scene.get("scene_id", "unknown")
        scene_report = {
            "scene_id": scene_id,
            "environment_file": env_mapping.get(scene_id, "N/A"),
            "success": results.get(scene_id, False),
            "camera": {
                "style": scene.get("camera", {}).get("style", "static"),
                "movement": scene.get("camera", {}).get("movement", "medium"),
                "cuts_count": len(scene.get("camera", {}).get("cuts", []))
            },
            "lighting": {
                "style": scene.get("lighting", {}).get("style", "3point"),
                "intensity": scene.get("lighting", {}).get("intensity", 1.0),
                "color_temp": scene.get("lighting", {}).get("color_temp", 5500)
            },
            "output": {
                "blend": f"scene_ready_{scene_id}.blend" if results.get(scene_id) else None,
                "camera_data": f"camera_data_{scene_id}.json" if results.get(scene_id) else None
            }
        }
        report["scenes"].append(scene_report)
    
    report_path = output_dir / "photography_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.success(f"Rapport généré: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description=f'PHOTOGRAPHY WING - EXODUS v{PHOTOGRAPHY_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_04_PHOTOGRAPHY.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --production-plan PRODUCTION_PLAN.JSON

  python EXO_04_PHOTOGRAPHY.py --drive-root /path/to/drive \\
    --production-plan /path/to/plan.json \\
    --input-dir /path/to/environments \\
    --output-dir /path/to/output \\
    -v
        """
    )
    
    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--production-plan', required=True,
                        help='PRODUCTION_PLAN.JSON du Cortex')
    parser.add_argument('--video-source-dir',
                        help='Dossier IN_VIDEO_SOURCE/ (vidéo de référence)')
    parser.add_argument('--scene-ref-dir',
                        help='Dossier IN_SCENE_REF/ (référence scène 3D)')
    parser.add_argument('--output-dir',
                        help='Dossier output (défaut: OUT_CAMERA_LOGIC/)')
    parser.add_argument('--scene-id',
                        help='Traiter uniquement cette scène (défaut: toutes)')
    parser.add_argument('--blender-path',
                        help='Chemin custom vers Blender')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')
    
    args = parser.parse_args()
    logger = PhotographyLogger(verbose=args.verbose)
    
    print("=" * 70)
    print("   FRÉGATE 04_PHOTOGRAPHY — EXODUS CINÉMATIQUE")
    print(f"   Version {PHOTOGRAPHY_VERSION}")
    print("=" * 70)
    
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "04_PHOTOGRAPHY_WING"
    
    video_source_dir = unit_root / "IN_VIDEO_SOURCE"
    scene_ref_dir = unit_root / "IN_SCENE_REF"
    
    plan_path = Path(args.production_plan)
    if not plan_path.is_absolute():
        plan_path = scene_ref_dir / args.production_plan
    
    if args.video_source_dir:
        video_source_dir = Path(args.video_source_dir)
    
    if args.scene_ref_dir:
        scene_ref_dir = Path(args.scene_ref_dir)
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_CAMERA_LOGIC"
    
    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Production Plan: {plan_path}")
    logger.info(f"Video Source Dir: {video_source_dir}")
    logger.info(f"Scene Ref Dir: {scene_ref_dir}")
    logger.info(f"Output Dir: {output_dir}")
    
    blender_path = check_blender(drive_root, logger, args.blender_path)
    plan = validate_production_plan(plan_path, logger)
    env_mapping = validate_environment_files(scene_ref_dir, plan, logger)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.success("Configuration validée")
    
    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\n✓ Tous les chemins sont valides. Prêt pour la photographie.")
        
        print("\n=== Résumé ===")
        print(f"  Scènes: {len(plan.get('scenes', []))}")
        for scene in plan.get("scenes", []):
            sid = scene.get("scene_id", "?")
            cam_style = scene.get("camera", {}).get("style", "static")
            light_style = scene.get("lighting", {}).get("style", "3point")
            cuts = len(scene.get("camera", {}).get("cuts", []))
            print(f"    Scene {sid}: camera={cam_style}, lighting={light_style}, cuts={cuts}")
        sys.exit(0)
    
    scenes_to_process = plan.get("scenes", [])
    if args.scene_id:
        scenes_to_process = [s for s in scenes_to_process if str(s.get("scene_id")) == str(args.scene_id)]
        if not scenes_to_process:
            logger.error(f"Scene ID {args.scene_id} non trouvée dans le plan")
            sys.exit(1)
    
    results = {}
    for scene in scenes_to_process:
        scene_id = scene.get("scene_id", "unknown")
        env_blend = env_mapping.get(scene_id)
        
        if not env_blend:
            logger.error(f"Scene {scene_id}: aucun environment.blend")
            results[scene_id] = False
            continue
        
        success = run_blender_photography(
            blender_path,
            env_blend,
            scene,
            str(output_dir),
            str(scene_id),
            logger
        )
        results[scene_id] = success
    
    report = generate_report(
        output_dir,
        plan,
        env_mapping,
        results,
        logger
    )
    
    total_failed = sum(1 for v in results.values() if not v)
    if total_failed == len(results) and len(results) > 0:
        logger.error("Toutes les scènes ont échoué")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    logger.success(f"PHOTOGRAPHIE COMPLÈTE")
    print(f"  → Scènes traitées: {sum(1 for v in results.values() if v)}/{len(results)}")
    print(f"  → Output: {output_dir}")
    print(f"  → Rapport: {output_dir}/photography_report.json")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
