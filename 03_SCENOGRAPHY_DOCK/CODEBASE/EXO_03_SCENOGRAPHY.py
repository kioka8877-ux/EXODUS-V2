#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           EXO_03_SCENOGRAPHY — CHANTIER DÉCORS FLOTTE EXODUS                 ║
║          Construction Environnements 3D + PBR + HDRi Lighting                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Construire les décors 3D selon le PRODUCTION_PLAN.JSON             ║
║  Stack: Blender 4.0 Headless + Cycles/EEVEE                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS (fournis par l'Empereur):
    - PRODUCTION_PLAN.JSON : Spécifications environnement du Cortex
    - hdri_library/ : Fichiers HDRi (.hdr, .exr) par mood
    - environment_assets/ : Assets décors (.blend, .glb, .fbx)
    
OUTPUTS:
    - environment_{scene_id}.blend : Scène Blender avec environnement
    - scenography_report.json : Rapport de construction
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

SCENOGRAPHY_VERSION = "1.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"


class ScenographyLogger:
    """Logger structuré pour SCENOGRAPHY DOCK."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []
    
    def info(self, msg: str):
        entry = f"[SCENOGRAPHY] {msg}"
        print(entry)
        self.logs.append({"level": "INFO", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def debug(self, msg: str):
        if self.verbose:
            entry = f"[SCENOGRAPHY:DEBUG] {msg}"
            print(entry)
            self.logs.append({"level": "DEBUG", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def error(self, msg: str):
        entry = f"[SCENOGRAPHY:ERROR] {msg}"
        print(entry, file=sys.stderr)
        self.logs.append({"level": "ERROR", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def success(self, msg: str):
        entry = f"[SCENOGRAPHY:OK] ✓ {msg}"
        print(entry)
        self.logs.append({"level": "SUCCESS", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def warn(self, msg: str):
        entry = f"[SCENOGRAPHY:WARN] ⚠ {msg}"
        print(entry)
        self.logs.append({"level": "WARN", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def get_logs(self) -> list:
        return self.logs


def check_blender(drive_root: Path, logger: ScenographyLogger, custom_path: str = None) -> str:
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


def validate_production_plan(plan_path: Path, logger: ScenographyLogger) -> dict:
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
    
    env_count = 0
    props_count = 0
    for scene in plan.get("scenes", []):
        if "environment" in scene:
            env_count += 1
            props_count += len(scene.get("environment", {}).get("props", []))
    
    logger.success(f"Plan validé: {len(plan['scenes'])} scènes, {env_count} environnements, {props_count} props")
    return plan


def validate_hdri_library(library_path: Path, plan: dict, logger: ScenographyLogger) -> dict:
    """
    Vérifie les HDRi disponibles et crée un mapping mood → fichier.
    Retourne un mapping lighting_mood -> chemin HDRi.
    """
    hdri_mapping = {}
    
    if not library_path.exists():
        logger.warn(f"HDRI library introuvable: {library_path}")
        logger.info("Création du dossier hdri_library...")
        library_path.mkdir(parents=True, exist_ok=True)
        return hdri_mapping
    
    required_moods = set()
    for scene in plan.get("scenes", []):
        env = scene.get("environment", {})
        if "lighting_mood" in env:
            required_moods.add(env["lighting_mood"])
    
    logger.info(f"Moods requis: {required_moods or 'aucun'}")
    
    supported_extensions = [".hdr", ".exr", ".hdri"]
    available_files = {}
    
    for ext in supported_extensions:
        for f in library_path.glob(f"*{ext}"):
            mood_name = f.stem.lower()
            available_files[mood_name] = str(f)
    
    mood_keywords = {
        "neon": ["neon", "cyber", "night", "city_night", "urban_night"],
        "dramatic": ["dramatic", "storm", "sunset", "golden", "contrast"],
        "natural": ["natural", "daylight", "outdoor", "sky", "sunny", "overcast"],
        "studio": ["studio", "neutral", "grey", "white", "softbox"]
    }
    
    for mood in required_moods:
        mood_lower = mood.lower()
        if mood_lower in available_files:
            hdri_mapping[mood] = available_files[mood_lower]
            logger.debug(f"  ✓ {mood}: {available_files[mood_lower]}")
        else:
            found = False
            for keyword in mood_keywords.get(mood_lower, []):
                for file_mood, file_path in available_files.items():
                    if keyword in file_mood:
                        hdri_mapping[mood] = file_path
                        logger.debug(f"  ✓ {mood} (via {file_mood}): {file_path}")
                        found = True
                        break
                if found:
                    break
            
            if not found:
                logger.warn(f"  ✗ {mood}: HDRi INTROUVABLE — fallback gris neutre")
    
    logger.success(f"HDRi library: {len(hdri_mapping)}/{len(required_moods)} moods résolus")
    return hdri_mapping


def validate_environment_assets(assets_path: Path, plan: dict, logger: ScenographyLogger) -> dict:
    """
    Vérifie les assets environnement disponibles.
    Retourne un mapping type/prop_id -> chemin fichier.
    """
    assets_mapping = {}
    
    if not assets_path.exists():
        logger.warn(f"Environment assets introuvable: {assets_path}")
        logger.info("Création du dossier environment_assets...")
        assets_path.mkdir(parents=True, exist_ok=True)
        return assets_mapping
    
    required_types = set()
    required_props = set()
    
    for scene in plan.get("scenes", []):
        env = scene.get("environment", {})
        if "type" in env:
            required_types.add(env["type"])
        for prop in env.get("props", []):
            required_props.add(prop)
    
    logger.info(f"Types requis: {required_types or 'aucun'}")
    logger.info(f"Props requis: {required_props or 'aucun'}")
    
    supported_extensions = [".blend", ".glb", ".gltf", ".fbx", ".obj"]
    available_files = {}
    
    for ext in supported_extensions:
        for f in assets_path.glob(f"*{ext}"):
            asset_id = f.stem.lower()
            available_files[asset_id] = str(f)
        for f in assets_path.glob(f"**/*{ext}"):
            asset_id = f.stem.lower()
            if asset_id not in available_files:
                available_files[asset_id] = str(f)
    
    for asset_type in required_types:
        type_lower = asset_type.lower().replace("_", "")
        matched = False
        for file_id, file_path in available_files.items():
            if type_lower in file_id.replace("_", "") or file_id.replace("_", "") in type_lower:
                assets_mapping[f"env:{asset_type}"] = file_path
                logger.debug(f"  ✓ env:{asset_type}: {file_path}")
                matched = True
                break
        if not matched:
            logger.warn(f"  ✗ env:{asset_type}: Asset INTROUVABLE — sera généré basique")
    
    for prop in required_props:
        prop_lower = prop.lower().replace("_", "")
        matched = False
        for file_id, file_path in available_files.items():
            if prop_lower in file_id.replace("_", "") or file_id.replace("_", "") in prop_lower:
                assets_mapping[f"prop:{prop}"] = file_path
                logger.debug(f"  ✓ prop:{prop}: {file_path}")
                matched = True
                break
        if not matched:
            logger.warn(f"  ✗ prop:{prop}: Asset INTROUVABLE — placeholder utilisé")
    
    logger.success(f"Assets: {len(assets_mapping)} résolus")
    return assets_mapping


def run_blender_scenography(
    blender_path: str,
    production_plan: str,
    hdri_mapping: dict,
    assets_mapping: dict,
    output_dir: str,
    scene_filter: list,
    logger: ScenographyLogger
) -> bool:
    """
    Exécute Blender en mode headless pour la construction des environnements.
    """
    logger.info("Lancement Blender Scenography Engine...")
    
    script_dir = Path(__file__).parent
    builder_script = script_dir / "environment_builder.py"
    
    if not builder_script.exists():
        logger.error(f"Script builder introuvable: {builder_script}")
        return False
    
    hdri_mapping_json = json.dumps(hdri_mapping)
    assets_mapping_json = json.dumps(assets_mapping)
    scene_filter_json = json.dumps(scene_filter) if scene_filter else "[]"
    
    cmd = [
        blender_path,
        "--background",
        "--python", str(builder_script),
        "--",
        "--production-plan", production_plan,
        "--hdri-mapping", hdri_mapping_json,
        "--assets-mapping", assets_mapping_json,
        "--output-dir", output_dir,
        "--scene-filter", scene_filter_json
    ]
    
    logger.debug(f"Commande Blender: {' '.join(cmd[:6])}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Blender échoué (code {result.returncode})")
        logger.error(f"STDERR: {result.stderr[-2000:] if result.stderr else 'N/A'}")
        return False
    
    logger.debug(f"STDOUT: {result.stdout[-1000:] if result.stdout else 'N/A'}")
    logger.success("Blender Scenography terminé")
    return True


def generate_report(
    output_dir: Path,
    plan: dict,
    hdri_mapping: dict,
    assets_mapping: dict,
    scene_filter: list,
    success: bool,
    logger: ScenographyLogger
) -> dict:
    """
    Génère le rapport de production scenography_report.json.
    """
    scenes_built = []
    for scene in plan.get("scenes", []):
        scene_id = scene.get("scene_id")
        if scene_filter and scene_id not in scene_filter:
            continue
        
        env = scene.get("environment", {})
        scene_info = {
            "scene_id": scene_id,
            "environment_type": env.get("type", "unknown"),
            "lighting_mood": env.get("lighting_mood", "natural"),
            "props_count": len(env.get("props", [])),
            "hdri_resolved": env.get("lighting_mood") in hdri_mapping,
            "output_file": f"environment_{scene_id}.blend" if success else None
        }
        scenes_built.append(scene_info)
    
    report = {
        "version": SCENOGRAPHY_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "summary": {
            "total_scenes": len(plan.get("scenes", [])),
            "scenes_built": len(scenes_built),
            "hdri_resolved": len(hdri_mapping),
            "assets_resolved": len(assets_mapping)
        },
        "scenes": scenes_built,
        "hdri_library": {
            "resolved": list(hdri_mapping.keys()),
            "missing": [
                s.get("environment", {}).get("lighting_mood")
                for s in plan.get("scenes", [])
                if s.get("environment", {}).get("lighting_mood") not in hdri_mapping
            ]
        },
        "assets": {
            "resolved": list(assets_mapping.keys()),
            "types_resolved": [k for k in assets_mapping.keys() if k.startswith("env:")],
            "props_resolved": [k for k in assets_mapping.keys() if k.startswith("prop:")]
        },
        "logs": logger.get_logs()
    }
    
    report_path = output_dir / "scenography_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.success(f"Rapport généré: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description=f'SCENOGRAPHY DOCK - EXODUS v{SCENOGRAPHY_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_03_SCENOGRAPHY.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --production-plan PRODUCTION_PLAN.JSON

  python EXO_03_SCENOGRAPHY.py --drive-root /path/to/drive \\
    --production-plan /path/to/plan.json \\
    --hdri-library /path/to/hdri/ \\
    --environment-assets /path/to/assets/ \\
    --output-dir /path/to/output \\
    --scene-ids 1,2,3 \\
    -v
        """
    )
    
    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--production-plan', required=True,
                        help='PRODUCTION_PLAN.JSON du Cortex')
    parser.add_argument('--hdri-library',
                        help='Dossier HDRi library (défaut: IN_MAP_RAW/hdri_library)')
    parser.add_argument('--environment-assets',
                        help='Dossier environment assets (défaut: IN_MAP_RAW/environment_assets)')
    parser.add_argument('--output-dir',
                        help='Dossier output (défaut: OUT_PREMIUM_SCENE/)')
    parser.add_argument('--scene-ids',
                        help='IDs des scènes à traiter (ex: 1,2,3) — défaut: toutes')
    parser.add_argument('--blender-path',
                        help='Chemin custom vers Blender')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')
    
    args = parser.parse_args()
    logger = ScenographyLogger(verbose=args.verbose)
    
    print("=" * 70)
    print("   FRÉGATE 03_SCENOGRAPHY — EXODUS CHANTIER DÉCORS")
    print(f"   Version {SCENOGRAPHY_VERSION}")
    print("=" * 70)
    
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "03_SCENOGRAPHY_DOCK"
    
    cortex_json_dir = unit_root / "IN_CORTEX_JSON"
    map_raw_dir = unit_root / "IN_MAP_RAW"
    
    plan_path = Path(args.production_plan)
    if not plan_path.is_absolute():
        plan_path = cortex_json_dir / args.production_plan
    
    if args.hdri_library:
        hdri_library = Path(args.hdri_library)
    else:
        hdri_library = map_raw_dir / "hdri_library"
    
    if args.environment_assets:
        env_assets = Path(args.environment_assets)
    else:
        env_assets = map_raw_dir / "environment_assets"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_PREMIUM_SCENE"
    
    scene_filter = []
    if args.scene_ids:
        scene_filter = [int(x.strip()) for x in args.scene_ids.split(',')]
    
    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Production Plan: {plan_path}")
    logger.info(f"HDRI Library: {hdri_library}")
    logger.info(f"Environment Assets: {env_assets}")
    logger.info(f"Output Dir: {output_dir}")
    if scene_filter:
        logger.info(f"Scene Filter: {scene_filter}")
    
    blender_path = check_blender(drive_root, logger, args.blender_path)
    plan = validate_production_plan(plan_path, logger)
    hdri_mapping = validate_hdri_library(hdri_library, plan, logger)
    assets_mapping = validate_environment_assets(env_assets, plan, logger)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.success("Configuration validée")
    
    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\n✓ Tous les chemins sont valides. Prêt pour la construction.")
        
        print("\n=== Résumé ===")
        print(f"  Scènes: {len(plan.get('scenes', []))}")
        print(f"  Environnements: {sum(1 for s in plan.get('scenes', []) if 'environment' in s)}")
        print(f"  HDRi résolus: {len(hdri_mapping)}")
        print(f"  Assets résolus: {len(assets_mapping)}")
        if scene_filter:
            print(f"  Scènes filtrées: {scene_filter}")
        sys.exit(0)
    
    success = run_blender_scenography(
        blender_path,
        str(plan_path),
        hdri_mapping,
        assets_mapping,
        str(output_dir),
        scene_filter,
        logger
    )
    
    report = generate_report(
        output_dir,
        plan,
        hdri_mapping,
        assets_mapping,
        scene_filter,
        success,
        logger
    )
    
    if not success:
        logger.error("Construction décors échouée")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    logger.success("CONSTRUCTION DÉCORS TERMINÉE")
    print(f"  → Environnements: {output_dir}/environment_*.blend")
    print(f"  → Rapport: {output_dir}/scenography_report.json")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
