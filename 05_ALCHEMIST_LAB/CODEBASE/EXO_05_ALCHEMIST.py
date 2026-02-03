#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             FRÉGATE 05_ALCHEMIST — EXODUS POST-PRODUCTION LAB                ║
║              Compositing • Color Grading • Effets Cinématiques               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Post-production automatisée des rendus EXR 4K/120FPS              ║
║  Stack: Blender Compositor + OpenColorIO + OptiX/OIDN                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS:
    - render_*.exr : Séquences EXR multi-layer (de U04)
    - PRODUCTION_PLAN.JSON : Instructions color grade et effets
    - LUTS/*.cube : LUTs cinématiques
    
OUTPUTS:
    - graded_{scene_id}_####.exr : Séquences EXR finales
    - graded_preview_{scene_id}.mp4 : Preview H.264 pour validation
    - alchemist_report.json : Rapport de production
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

ALCHEMIST_VERSION = "1.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"


class AlchemistLogger:
    """Logger structuré pour ALCHEMIST LAB."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []
    
    def info(self, msg: str):
        entry = f"[ALCHEMIST] {msg}"
        print(entry)
        self.logs.append({"level": "INFO", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def debug(self, msg: str):
        if self.verbose:
            entry = f"[ALCHEMIST:DEBUG] {msg}"
            print(entry)
            self.logs.append({"level": "DEBUG", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def error(self, msg: str):
        entry = f"[ALCHEMIST:ERROR] {msg}"
        print(entry, file=sys.stderr)
        self.logs.append({"level": "ERROR", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def success(self, msg: str):
        entry = f"[ALCHEMIST:OK] ✓ {msg}"
        print(entry)
        self.logs.append({"level": "SUCCESS", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def warn(self, msg: str):
        entry = f"[ALCHEMIST:WARN] ⚠ {msg}"
        print(entry)
        self.logs.append({"level": "WARN", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def get_logs(self) -> list:
        return self.logs


def check_blender(drive_root: Path, logger: AlchemistLogger, custom_path: str = None) -> str:
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


def validate_production_plan(plan_path: Path, logger: AlchemistLogger) -> dict:
    """
    Valide et charge le PRODUCTION_PLAN.JSON.
    Extrait les paramètres post_production.
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
    
    total_post_config = 0
    for scene in plan.get("scenes", []):
        if "post_production" in scene:
            total_post_config += 1
    
    logger.success(f"Plan validé: {len(plan['scenes'])} scènes, {total_post_config} avec config post-prod")
    return plan


def scan_exr_sequences(render_dir: Path, logger: AlchemistLogger) -> Dict[int, List[Path]]:
    """
    Scanne le dossier IN_RENDER pour trouver les séquences EXR.
    Retourne un dict {scene_id: [liste de fichiers EXR]}.
    """
    sequences = {}
    
    if not render_dir.exists():
        logger.warn(f"Dossier render introuvable: {render_dir}")
        return sequences
    
    exr_files = sorted(render_dir.glob("*.exr"))
    
    if not exr_files:
        exr_files = sorted(render_dir.glob("**/*.exr"))
    
    for exr_file in exr_files:
        name = exr_file.stem
        
        scene_id = 1
        if "_scene_" in name.lower():
            try:
                parts = name.lower().split("_scene_")
                scene_id = int(parts[1].split("_")[0])
            except (ValueError, IndexError):
                pass
        elif name.startswith("render_"):
            try:
                scene_id = int(name.split("_")[1])
            except (ValueError, IndexError):
                pass
        
        if scene_id not in sequences:
            sequences[scene_id] = []
        sequences[scene_id].append(exr_file)
    
    for scene_id in sequences:
        sequences[scene_id] = sorted(sequences[scene_id])
    
    logger.info(f"Séquences EXR trouvées: {len(sequences)} scènes")
    for scene_id, files in sequences.items():
        logger.debug(f"  Scene {scene_id}: {len(files)} frames")
    
    return sequences


def validate_luts(luts_dir: Path, plan: dict, logger: AlchemistLogger) -> Dict[str, Path]:
    """
    Vérifie que les LUTs requis sont disponibles.
    Retourne un mapping {nom_lut: chemin}.
    """
    required_luts = set()
    
    for scene in plan.get("scenes", []):
        post_prod = scene.get("post_production", {})
        color_grade = post_prod.get("color_grade", "")
        if color_grade:
            required_luts.add(color_grade)
    
    lut_mapping = {}
    available_luts = list(luts_dir.glob("*.cube")) if luts_dir.exists() else []
    
    for lut_file in available_luts:
        lut_name = lut_file.stem
        lut_mapping[lut_name] = lut_file
        normalized_name = lut_name.lower().replace("-", "_").replace(" ", "_")
        if normalized_name != lut_name:
            lut_mapping[normalized_name] = lut_file
    
    missing_luts = []
    for lut_name in required_luts:
        normalized = lut_name.lower().replace("-", "_").replace(" ", "_")
        if lut_name not in lut_mapping and normalized not in lut_mapping:
            missing_luts.append(lut_name)
    
    if missing_luts:
        logger.warn(f"LUTs manquants: {missing_luts}")
        logger.info("Color grade sera appliqué sans LUT pour ces scènes")
    else:
        logger.success(f"Tous les LUTs requis disponibles: {len(required_luts)}")
    
    logger.debug(f"LUTs disponibles: {list(lut_mapping.keys())}")
    return lut_mapping


def get_post_config(scene: dict) -> dict:
    """Extrait la config post-production d'une scène avec valeurs par défaut."""
    default_config = {
        "color_grade": "natural",
        "effects": {
            "bloom": False,
            "lens_flare": False,
            "film_grain": 0.0,
            "vignette": 0.0,
            "chromatic_aberration": 0.0
        },
        "denoise": True,
        "exposure": 0.0,
        "contrast": 1.0,
        "saturation": 1.0
    }
    
    post_prod = scene.get("post_production", {})
    
    config = default_config.copy()
    config["color_grade"] = post_prod.get("color_grade", config["color_grade"])
    config["denoise"] = post_prod.get("denoise", config["denoise"])
    config["exposure"] = post_prod.get("exposure", config["exposure"])
    config["contrast"] = post_prod.get("contrast", config["contrast"])
    config["saturation"] = post_prod.get("saturation", config["saturation"])
    
    effects = post_prod.get("effects", {})
    for key in config["effects"]:
        if key in effects:
            config["effects"][key] = effects[key]
    
    return config


def run_blender_compositor(
    blender_path: str,
    scene_id: int,
    exr_files: List[Path],
    output_dir: Path,
    post_config: dict,
    luts_dir: Path,
    lut_mapping: Dict[str, Path],
    logger: AlchemistLogger
) -> Tuple[bool, dict]:
    """
    Exécute Blender en mode headless pour le compositing.
    """
    logger.info(f"Compositing Scene {scene_id}...")
    
    script_dir = Path(__file__).parent
    compositor_script = script_dir / "compositor_pipeline.py"
    
    if not compositor_script.exists():
        logger.error(f"Script compositor introuvable: {compositor_script}")
        return False, {"error": "Script missing"}
    
    lut_path = ""
    color_grade = post_config.get("color_grade", "")
    normalized_grade = color_grade.lower().replace("-", "_").replace(" ", "_")
    
    if color_grade in lut_mapping:
        lut_path = str(lut_mapping[color_grade])
    elif normalized_grade in lut_mapping:
        lut_path = str(lut_mapping[normalized_grade])
    
    first_exr = str(exr_files[0]) if exr_files else ""
    frame_start = 1
    frame_end = len(exr_files)
    
    config_json = json.dumps({
        "scene_id": scene_id,
        "input_exr": first_exr,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "output_dir": str(output_dir),
        "lut_path": lut_path,
        "post_config": post_config
    })
    
    cmd = [
        blender_path,
        "--background",
        "--python", str(compositor_script),
        "--",
        "--config", config_json
    ]
    
    logger.debug(f"Commande Blender: {' '.join(cmd[:5])}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    
    if result.returncode != 0:
        logger.error(f"Blender échoué (code {result.returncode})")
        logger.error(f"STDERR: {result.stderr[-2000:] if result.stderr else 'N/A'}")
        return False, {"error": result.stderr}
    
    logger.debug(f"STDOUT: {result.stdout[-1000:] if result.stdout else 'N/A'}")
    logger.success(f"Compositing Scene {scene_id} terminé")
    
    return True, {
        "scene_id": scene_id,
        "frames_processed": frame_end,
        "lut_applied": bool(lut_path),
        "effects_applied": post_config.get("effects", {})
    }


def generate_preview(
    scene_id: int,
    output_dir: Path,
    frame_count: int,
    logger: AlchemistLogger
) -> Optional[Path]:
    """
    Génère une preview MP4 basse qualité pour validation rapide.
    Utilise FFmpeg si disponible.
    """
    exr_pattern = output_dir / f"graded_{scene_id:03d}_%04d.exr"
    preview_path = output_dir / f"graded_preview_{scene_id:03d}.mp4"
    
    if not list(output_dir.glob(f"graded_{scene_id:03d}_*.exr")):
        logger.warn(f"Pas de frames EXR pour preview Scene {scene_id}")
        return None
    
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", "30",
        "-start_number", "1",
        "-i", str(exr_pattern),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080",
        str(preview_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.success(f"Preview générée: {preview_path.name}")
            return preview_path
        else:
            logger.warn(f"FFmpeg échoué pour preview: {result.stderr[:500]}")
            return None
    except FileNotFoundError:
        logger.warn("FFmpeg non disponible - preview non générée")
        return None
    except subprocess.TimeoutExpired:
        logger.warn("FFmpeg timeout - preview non générée")
        return None


def generate_report(
    output_dir: Path,
    plan: dict,
    sequences: Dict[int, List[Path]],
    results: List[dict],
    logger: AlchemistLogger
) -> dict:
    """
    Génère le rapport de production alchemist_report.json.
    """
    success_count = sum(1 for r in results if r.get("success", False))
    
    report = {
        "version": ALCHEMIST_VERSION,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success_count == len(results) else "PARTIAL" if success_count > 0 else "FAILED",
        "summary": {
            "scenes_total": len(sequences),
            "scenes_processed": success_count,
            "scenes_failed": len(results) - success_count,
            "total_frames": sum(len(files) for files in sequences.values())
        },
        "scenes": results,
        "logs": logger.get_logs()
    }
    
    report_path = output_dir / "alchemist_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.success(f"Rapport généré: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description=f'ALCHEMIST LAB - EXODUS v{ALCHEMIST_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_05_ALCHEMIST.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --production-plan PRODUCTION_PLAN.JSON

  python EXO_05_ALCHEMIST.py --drive-root /path/to/drive \\
    --render-dir /path/to/exr \\
    --output-dir /path/to/output \\
    --luts-dir /path/to/luts \\
    -v
        """
    )
    
    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--production-plan', required=True,
                        help='PRODUCTION_PLAN.JSON du Cortex')
    parser.add_argument('--render-dir',
                        help='Dossier rendus EXR (défaut: IN_RAW_FRAMES/)')
    parser.add_argument('--output-dir',
                        help='Dossier output (défaut: OUT_FINAL_FRAMES/)')
    parser.add_argument('--luts-dir',
                        help='Dossier LUTs (défaut: LUTS/)')
    parser.add_argument('--blender-path',
                        help='Chemin custom vers Blender')
    parser.add_argument('--scene', type=int,
                        help='Traiter uniquement une scène spécifique')
    parser.add_argument('--skip-preview', action='store_true',
                        help='Ne pas générer les previews MP4')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')
    
    args = parser.parse_args()
    logger = AlchemistLogger(verbose=args.verbose)
    
    print("=" * 70)
    print("   FRÉGATE 05_ALCHEMIST — EXODUS POST-PRODUCTION LAB")
    print(f"   Version {ALCHEMIST_VERSION}")
    print("=" * 70)
    
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "05_ALCHEMIST_LAB"
    
    raw_frames_dir = unit_root / "IN_RAW_FRAMES"
    
    plan_path = Path(args.production_plan)
    if not plan_path.is_absolute():
        plan_path = raw_frames_dir / args.production_plan
    
    if args.render_dir:
        render_dir = Path(args.render_dir)
    else:
        render_dir = raw_frames_dir
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_FINAL_FRAMES"
    
    if args.luts_dir:
        luts_dir = Path(args.luts_dir)
    else:
        luts_dir = unit_root / "LUTS"
    
    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Production Plan: {plan_path}")
    logger.info(f"Render Dir: {render_dir}")
    logger.info(f"Output Dir: {output_dir}")
    logger.info(f"LUTs Dir: {luts_dir}")
    
    blender_path = check_blender(drive_root, logger, args.blender_path)
    plan = validate_production_plan(plan_path, logger)
    sequences = scan_exr_sequences(render_dir, logger)
    lut_mapping = validate_luts(luts_dir, plan, logger)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.success("Configuration validée")
    
    if not sequences:
        logger.warn("Aucune séquence EXR trouvée - vérifiez IN_RENDER/")
        if args.dry_run:
            print("\n✓ Configuration valide (pas de rendus à traiter)")
            sys.exit(0)
    
    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\n✓ Tous les chemins sont valides. Prêt pour post-production.")
        
        print("\n=== Résumé ===")
        print(f"  Scènes à traiter: {len(sequences)}")
        print(f"  Frames totales: {sum(len(f) for f in sequences.values())}")
        print(f"  LUTs disponibles: {len(lut_mapping)}")
        sys.exit(0)
    
    results = []
    scenes_to_process = sequences.keys()
    
    if args.scene is not None:
        if args.scene in sequences:
            scenes_to_process = [args.scene]
        else:
            logger.error(f"Scene {args.scene} introuvable dans les rendus")
            sys.exit(1)
    
    for scene_id in scenes_to_process:
        exr_files = sequences[scene_id]
        
        scene_config = None
        for scene in plan.get("scenes", []):
            if scene.get("scene_id") == scene_id:
                scene_config = scene
                break
        
        if scene_config is None:
            scene_config = {"scene_id": scene_id}
            logger.warn(f"Scene {scene_id} sans config post-prod - utilisation défauts")
        
        post_config = get_post_config(scene_config)
        
        success, result_data = run_blender_compositor(
            blender_path,
            scene_id,
            exr_files,
            output_dir,
            post_config,
            luts_dir,
            lut_mapping,
            logger
        )
        
        result_entry = {
            "scene_id": scene_id,
            "success": success,
            "frames_input": len(exr_files),
            "config": post_config,
            **result_data
        }
        
        if success and not args.skip_preview:
            preview_path = generate_preview(scene_id, output_dir, len(exr_files), logger)
            if preview_path:
                result_entry["preview"] = str(preview_path.name)
        
        results.append(result_entry)
    
    report = generate_report(output_dir, plan, sequences, results, logger)
    
    success_count = sum(1 for r in results if r.get("success", False))
    
    if success_count == 0 and results:
        logger.error("Post-production échouée pour toutes les scènes")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    logger.success(f"POST-PRODUCTION COMPLÈTE: {success_count}/{len(results)} scènes")
    print(f"  → Output: {output_dir}")
    print(f"  → Rapport: {output_dir}/alchemist_report.json")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
