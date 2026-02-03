#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             EXO_02_LOGISTICS — ARMURERIE DE LA FLOTTE EXODUS                 ║
║                   Attachement Props → Avatar Équipé                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Fusionner Avatar animé + Props selon le PRODUCTION_PLAN.JSON       ║
║  Stack: Blender 4.0 Headless + Alembic Export                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS (fournis par l'Empereur):
    - actor_animated.blend : Avatar animé de U01 (avec armature active)
    - PRODUCTION_PLAN.JSON : Instructions props du Cortex
    - props_library/ : Arsenal d'objets (.glb, .fbx, .blend)
    
OUTPUTS:
    - actor_equipped.abc : Animation bakée avec props en Alembic
    - actor_equipped.blend : Backup éditable
    - logistics_report.json : Log des attachements
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

LOGISTICS_VERSION = "1.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"


class LogisticsLogger:
    """Logger structuré pour LOGISTICS DEPOT."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []
    
    def info(self, msg: str):
        entry = f"[LOGISTICS] {msg}"
        print(entry)
        self.logs.append({"level": "INFO", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def debug(self, msg: str):
        if self.verbose:
            entry = f"[LOGISTICS:DEBUG] {msg}"
            print(entry)
            self.logs.append({"level": "DEBUG", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def error(self, msg: str):
        entry = f"[LOGISTICS:ERROR] {msg}"
        print(entry, file=sys.stderr)
        self.logs.append({"level": "ERROR", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def success(self, msg: str):
        entry = f"[LOGISTICS:OK] ✓ {msg}"
        print(entry)
        self.logs.append({"level": "SUCCESS", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def warn(self, msg: str):
        entry = f"[LOGISTICS:WARN] ⚠ {msg}"
        print(entry)
        self.logs.append({"level": "WARN", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def get_logs(self) -> list:
        return self.logs


def check_blender(drive_root: Path, logger: LogisticsLogger, custom_path: str = None) -> str:
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


def validate_production_plan(plan_path: Path, logger: LogisticsLogger) -> dict:
    """
    Valide et charge le PRODUCTION_PLAN.JSON.
    Retourne les données du plan.
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
    
    total_props = 0
    for scene in plan.get("scenes", []):
        props_actions = scene.get("props_actions", [])
        total_props += len(props_actions)
    
    logger.success(f"Plan validé: {len(plan['scenes'])} scènes, {total_props} actions props")
    return plan


def validate_props_library(library_path: Path, plan: dict, logger: LogisticsLogger) -> dict:
    """
    Vérifie que les props requis existent dans la bibliothèque.
    Retourne un mapping prop_id -> chemin fichier.
    """
    if not library_path.exists():
        logger.warn(f"Props library introuvable: {library_path}")
        logger.info("Création du dossier props_library...")
        library_path.mkdir(parents=True, exist_ok=True)
        return {}
    
    required_props = set()
    for scene in plan.get("scenes", []):
        for action in scene.get("props_actions", []):
            if "prop_id" in action:
                required_props.add(action["prop_id"])
    
    logger.info(f"Props requis: {len(required_props)}")
    
    supported_extensions = [".glb", ".gltf", ".fbx", ".blend", ".obj"]
    available_files = {}
    
    for ext in supported_extensions:
        for f in library_path.glob(f"*{ext}"):
            prop_id = f.stem
            available_files[prop_id] = str(f)
    
    props_mapping = {}
    missing_props = []
    
    for prop_id in required_props:
        if prop_id in available_files:
            props_mapping[prop_id] = available_files[prop_id]
            logger.debug(f"  ✓ {prop_id}: {available_files[prop_id]}")
        else:
            missing_props.append(prop_id)
            logger.warn(f"  ✗ {prop_id}: INTROUVABLE")
    
    if missing_props:
        logger.warn(f"{len(missing_props)} props manquants - placeholders seront utilisés")
        generic_placeholder = library_path / "generic_prop.glb"
        if generic_placeholder.exists():
            for prop_id in missing_props:
                props_mapping[prop_id] = str(generic_placeholder)
                logger.debug(f"  → {prop_id}: utilise generic_prop.glb")
    
    logger.success(f"Props library: {len(props_mapping)}/{len(required_props)} props résolus")
    return props_mapping


def run_blender_logistics(
    blender_path: str,
    actor_blend: str,
    production_plan: str,
    props_mapping: dict,
    output_dir: str,
    output_name: str,
    logger: LogisticsLogger
) -> bool:
    """
    Exécute Blender en mode headless pour l'attachement des props.
    """
    logger.info("Lancement Blender Logistics Engine...")
    
    script_dir = Path(__file__).parent
    socketing_script = script_dir / "socketing_engine.py"
    
    if not socketing_script.exists():
        logger.error(f"Script socketing introuvable: {socketing_script}")
        return False
    
    props_mapping_json = json.dumps(props_mapping)
    
    cmd = [
        blender_path,
        "--background",
        actor_blend,
        "--python", str(socketing_script),
        "--",
        "--production-plan", production_plan,
        "--props-mapping", props_mapping_json,
        "--output-dir", output_dir,
        "--output-name", output_name
    ]
    
    logger.debug(f"Commande Blender: {' '.join(cmd[:6])}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Blender échoué (code {result.returncode})")
        logger.error(f"STDERR: {result.stderr[-2000:] if result.stderr else 'N/A'}")
        return False
    
    logger.debug(f"STDOUT: {result.stdout[-1000:] if result.stdout else 'N/A'}")
    logger.success("Blender Logistics terminé")
    return True


def generate_report(
    output_dir: Path,
    output_name: str,
    plan: dict,
    props_mapping: dict,
    success: bool,
    logger: LogisticsLogger
) -> dict:
    """
    Génère le rapport de production logistics_report.json.
    """
    report = {
        "version": LOGISTICS_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "input": {
            "scenes_count": len(plan.get("scenes", [])),
            "props_resolved": len(props_mapping),
            "props_missing": [pid for pid in get_all_prop_ids(plan) if pid not in props_mapping]
        },
        "output": {
            "alembic": f"{output_name}.abc" if success else None,
            "blend": f"{output_name}.blend" if success else None
        },
        "attachments": [],
        "logs": logger.get_logs()
    }
    
    for scene in plan.get("scenes", []):
        for action in scene.get("props_actions", []):
            attachment = {
                "scene_id": scene.get("scene_id"),
                "frame": action.get("frame"),
                "action": action.get("action"),
                "prop_id": action.get("prop_id"),
                "actor": action.get("actor"),
                "socket": action.get("socket"),
                "resolved": action.get("prop_id") in props_mapping
            }
            report["attachments"].append(attachment)
    
    report_path = output_dir / "logistics_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.success(f"Rapport généré: {report_path}")
    return report


def get_all_prop_ids(plan: dict) -> set:
    """Extrait tous les prop_ids du plan."""
    prop_ids = set()
    for scene in plan.get("scenes", []):
        for action in scene.get("props_actions", []):
            if "prop_id" in action:
                prop_ids.add(action["prop_id"])
    return prop_ids


def main():
    parser = argparse.ArgumentParser(
        description=f'LOGISTICS DEPOT - EXODUS v{LOGISTICS_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_02_LOGISTICS.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --actor-blend actor_animated.blend --production-plan PRODUCTION_PLAN.JSON

  python EXO_02_LOGISTICS.py --drive-root /path/to/drive \\
    --actor-blend /path/to/actor.blend \\
    --production-plan /path/to/plan.json \\
    --props-library /path/to/props/ \\
    --output-dir /path/to/output \\
    -v
        """
    )
    
    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--actor-blend', required=True,
                        help='Fichier .blend de l\'avatar animé (de U01)')
    parser.add_argument('--production-plan', required=True,
                        help='PRODUCTION_PLAN.JSON du Cortex')
    parser.add_argument('--props-library',
                        help='Dossier props_library/ (défaut: IN_LOGISTICS/props_library)')
    parser.add_argument('--output-dir',
                        help='Dossier output (défaut: OUT_EQUIPPED/)')
    parser.add_argument('--output-name', default='actor_equipped',
                        help='Nom des fichiers output (défaut: actor_equipped)')
    parser.add_argument('--blender-path',
                        help='Chemin custom vers Blender')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')
    
    args = parser.parse_args()
    logger = LogisticsLogger(verbose=args.verbose)
    
    print("=" * 70)
    print("   FRÉGATE 02_LOGISTICS — EXODUS ARMURERIE")
    print(f"   Version {LOGISTICS_VERSION}")
    print("=" * 70)
    
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "02_LOGISTICS_DEPOT"
    
    actor_path = Path(args.actor_blend)
    if not actor_path.is_absolute():
        actor_path = unit_root / "IN_LOGISTICS" / args.actor_blend
    
    plan_path = Path(args.production_plan)
    if not plan_path.is_absolute():
        plan_path = unit_root / "IN_LOGISTICS" / args.production_plan
    
    if args.props_library:
        props_library = Path(args.props_library)
    else:
        props_library = unit_root / "IN_LOGISTICS" / "props_library"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_EQUIPPED"
    
    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Actor Blend: {actor_path}")
    logger.info(f"Production Plan: {plan_path}")
    logger.info(f"Props Library: {props_library}")
    logger.info(f"Output Dir: {output_dir}")
    
    if not actor_path.exists():
        logger.error(f"Actor .blend introuvable: {actor_path}")
        sys.exit(1)
    
    blender_path = check_blender(drive_root, logger, args.blender_path)
    plan = validate_production_plan(plan_path, logger)
    props_mapping = validate_props_library(props_library, plan, logger)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.success("Configuration validée")
    
    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\n✓ Tous les chemins sont valides. Prêt pour l'équipement.")
        
        print("\n=== Résumé ===")
        print(f"  Scènes: {len(plan.get('scenes', []))}")
        print(f"  Props actions: {sum(len(s.get('props_actions', [])) for s in plan.get('scenes', []))}")
        print(f"  Props résolus: {len(props_mapping)}")
        sys.exit(0)
    
    success = run_blender_logistics(
        blender_path,
        str(actor_path),
        str(plan_path),
        props_mapping,
        str(output_dir),
        args.output_name,
        logger
    )
    
    report = generate_report(
        output_dir,
        args.output_name,
        plan,
        props_mapping,
        success,
        logger
    )
    
    if not success:
        logger.error("Équipement échoué")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    logger.success(f"ÉQUIPEMENT COMPLET")
    print(f"  → Alembic: {output_dir}/{args.output_name}.abc")
    print(f"  → Blend: {output_dir}/{args.output_name}.blend")
    print(f"  → Rapport: {output_dir}/logistics_report.json")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
