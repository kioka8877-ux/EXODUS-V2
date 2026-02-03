#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 06_AIRCRAFT_CARRIER — EXODUS SYSTEM                  ║
║              Assemblage Final + Upscale 4K/120FPS via RIFE                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Assembler séquences vidéo, sync audio, RIFE 120FPS, encode final  ║
║  Stack: FFmpeg + RIFE + Real-ESRGAN (optionnel)                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS (fournis par l'Empereur):
    - graded_*.exr/png : Séquences rendues de U05
    - audio_*.wav : Pistes audio (music, sfx, voice)
    - PRODUCTION_PLAN.JSON : Instructions d'assemblage
    
OUTPUTS:
    - FINAL_OUTPUT_*.mp4 : Livrable 4K/120FPS H.265
    - FINAL_OUTPUT_*.mov : ProRes archivage
    - thumbnail_*.png : Vignette publication
    - carrier_report.json : Log de production
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

CARRIER_VERSION = "1.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
RIFE_SUBDIR = "rife"
REALESRGAN_SUBDIR = "realesrgan"


class CarrierLogger:
    """Logger structuré pour AIRCRAFT CARRIER."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []
        self.warnings = []
        self.errors = []
    
    def info(self, msg: str):
        entry = f"[CARRIER] {msg}"
        print(entry)
        self.logs.append({"level": "INFO", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def debug(self, msg: str):
        if self.verbose:
            entry = f"[CARRIER:DEBUG] {msg}"
            print(entry)
            self.logs.append({"level": "DEBUG", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def error(self, msg: str):
        entry = f"[CARRIER:ERROR] {msg}"
        print(entry, file=sys.stderr)
        self.logs.append({"level": "ERROR", "message": msg, "timestamp": datetime.now().isoformat()})
        self.errors.append(msg)
    
    def success(self, msg: str):
        entry = f"[CARRIER:OK] ✓ {msg}"
        print(entry)
        self.logs.append({"level": "SUCCESS", "message": msg, "timestamp": datetime.now().isoformat()})
    
    def warn(self, msg: str):
        entry = f"[CARRIER:WARN] ⚠ {msg}"
        print(entry)
        self.logs.append({"level": "WARN", "message": msg, "timestamp": datetime.now().isoformat()})
        self.warnings.append(msg)
    
    def get_logs(self) -> list:
        return self.logs


def check_ffmpeg(logger: CarrierLogger) -> bool:
    """Vérifie que FFmpeg est disponible."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            logger.success(f"FFmpeg disponible: {version_line[:50]}...")
            return True
    except FileNotFoundError:
        pass
    logger.error("FFmpeg introuvable. Installez FFmpeg et ajoutez-le au PATH.")
    return False


def check_gpu(logger: CarrierLogger) -> bool:
    """Vérifie la disponibilité GPU (CUDA)."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.success(f"GPU CUDA disponible: {gpu_name}")
            return True
        else:
            logger.warn("CUDA non disponible, fallback CPU (plus lent)")
            return False
    except ImportError:
        logger.warn("PyTorch non installé, RIFE/upscale utiliseront CPU via FFmpeg")
        return False


def check_rife_model(drive_root: Path, logger: CarrierLogger) -> Optional[str]:
    """Vérifie que le modèle RIFE est disponible."""
    ai_models_path = drive_root / AI_MODELS_SUBDIR
    rife_path = ai_models_path / RIFE_SUBDIR
    
    flownet_candidates = [
        rife_path / "flownet.pkl",
        rife_path / "flownet-v46.pkl",
        rife_path / "train_log" / "flownet.pkl"
    ]
    
    for candidate in flownet_candidates:
        if candidate.exists():
            logger.success(f"Modèle RIFE trouvé: {candidate}")
            return str(candidate.parent)
    
    logger.error(f"Modèle RIFE introuvable dans: {rife_path}")
    logger.info("Téléchargez RIFE et placez les modèles dans:")
    logger.info(f"  {rife_path}/")
    return None


def check_realesrgan_model(drive_root: Path, logger: CarrierLogger) -> Optional[str]:
    """Vérifie que Real-ESRGAN est disponible (optionnel)."""
    ai_models_path = drive_root / AI_MODELS_SUBDIR
    esrgan_path = ai_models_path / REALESRGAN_SUBDIR
    
    model_candidates = [
        esrgan_path / "realesr-general-x4v3.pth",
        esrgan_path / "RealESRGAN_x4plus.pth",
        esrgan_path / "model.pth"
    ]
    
    for candidate in model_candidates:
        if candidate.exists():
            logger.success(f"Real-ESRGAN trouvé: {candidate}")
            return str(candidate)
    
    logger.debug(f"Real-ESRGAN non trouvé (optionnel): {esrgan_path}")
    return None


def validate_production_plan(plan_path: Path, logger: CarrierLogger) -> dict:
    """Valide et charge le PRODUCTION_PLAN.JSON."""
    if not plan_path.exists():
        logger.error(f"PRODUCTION_PLAN.JSON introuvable: {plan_path}")
        sys.exit(1)
    
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide dans {plan_path}: {e}")
        sys.exit(1)
    
    if "output" not in plan:
        logger.warn("Aucune config 'output' dans le plan, utilisation des défauts")
        plan["output"] = {
            "resolution": "4K",
            "framerate": 120,
            "codec": "h265",
            "audio_tracks": []
        }
    
    logger.success(f"Plan validé: {plan['output'].get('resolution', '4K')} @ {plan['output'].get('framerate', 120)}FPS")
    return plan


def validate_components(
    components_dir: Path,
    plan: dict,
    logger: CarrierLogger
) -> Dict[str, List[Path]]:
    """Valide que tous les composants nécessaires sont présents."""
    components = {
        "sequences": [],
        "audio": []
    }
    
    exr_files = sorted(components_dir.glob("graded_*.exr"))
    png_files = sorted(components_dir.glob("graded_*.png"))
    components["sequences"] = exr_files if exr_files else png_files
    
    if not components["sequences"]:
        all_exr = sorted(components_dir.glob("*.exr"))
        all_png = sorted(components_dir.glob("*.png"))
        components["sequences"] = all_exr if all_exr else all_png
    
    if not components["sequences"]:
        logger.error(f"Aucune séquence image trouvée dans: {components_dir}")
        logger.info("Attendu: graded_*.exr ou graded_*.png")
        sys.exit(1)
    
    logger.success(f"Séquences trouvées: {len(components['sequences'])} images")
    
    audio_tracks = plan.get("output", {}).get("audio_tracks", [])
    for track_name in audio_tracks:
        track_path = components_dir / track_name
        if track_path.exists():
            components["audio"].append(track_path)
            logger.debug(f"  ✓ Audio: {track_name}")
        else:
            logger.warn(f"  ✗ Audio manquant: {track_name}")
    
    audio_wavs = sorted(components_dir.glob("audio_*.wav"))
    for wav in audio_wavs:
        if wav not in components["audio"]:
            components["audio"].append(wav)
            logger.debug(f"  ✓ Audio (auto): {wav.name}")
    
    if not components["audio"]:
        logger.warn("Aucune piste audio trouvée - vidéo sera muette")
    else:
        logger.success(f"Pistes audio: {len(components['audio'])}")
    
    return components


def run_pipeline(
    components: Dict[str, List[Path]],
    plan: dict,
    output_dir: Path,
    project_name: str,
    drive_root: Path,
    rife_model_path: Optional[str],
    esrgan_model_path: Optional[str],
    use_gpu: bool,
    logger: CarrierLogger
) -> Tuple[bool, dict]:
    """Exécute le pipeline complet d'assemblage."""
    from sequence_assembler import SequenceAssembler
    from audio_sync import AudioSync
    from rife_interpolator import RIFEInterpolator
    from upscaler import Upscaler
    from final_encoder import FinalEncoder
    
    output_config = plan.get("output", {})
    target_resolution = output_config.get("resolution", "4K")
    target_fps = output_config.get("framerate", 120)
    codec = output_config.get("codec", "h265")
    
    temp_dir = output_dir / "_temp_carrier"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline_result = {
        "stages": {},
        "files": {}
    }
    
    try:
        logger.info("=" * 50)
        logger.info("STAGE 1: Assemblage Séquence")
        logger.info("=" * 50)
        
        assembler = SequenceAssembler(verbose=logger.verbose)
        assembled_video = temp_dir / "assembled_30fps.mp4"
        
        success = assembler.assemble(
            sequence_files=components["sequences"],
            output_path=assembled_video,
            fps=30
        )
        
        if not success:
            logger.error("Assemblage séquence échoué")
            return False, pipeline_result
        
        pipeline_result["stages"]["assemble"] = {"status": "OK", "output": str(assembled_video)}
        logger.success(f"Séquence assemblée: {assembled_video}")
        
        logger.info("=" * 50)
        logger.info("STAGE 2: Synchronisation Audio")
        logger.info("=" * 50)
        
        audio_sync = AudioSync(verbose=logger.verbose)
        audio_output = temp_dir / "audio_mixed.wav"
        
        if components["audio"]:
            success = audio_sync.mix_and_normalize(
                audio_tracks=components["audio"],
                output_path=audio_output,
                target_lufs=-14.0
            )
            if success:
                pipeline_result["stages"]["audio"] = {"status": "OK", "output": str(audio_output)}
                logger.success(f"Audio mixé: {audio_output}")
            else:
                logger.warn("Mix audio échoué, vidéo sera muette")
                audio_output = None
        else:
            logger.info("Pas d'audio à traiter")
            audio_output = None
        
        logger.info("=" * 50)
        logger.info("STAGE 3: Interpolation RIFE 30→120 FPS")
        logger.info("=" * 50)
        
        rife = RIFEInterpolator(
            model_path=rife_model_path,
            use_gpu=use_gpu,
            verbose=logger.verbose
        )
        
        interpolated_video = temp_dir / "interpolated_120fps.mp4"
        
        if rife_model_path:
            success = rife.interpolate(
                input_video=assembled_video,
                output_video=interpolated_video,
                target_fps=target_fps
            )
            if success:
                pipeline_result["stages"]["rife"] = {"status": "OK", "output": str(interpolated_video)}
                logger.success(f"Interpolation RIFE: {target_fps}FPS")
            else:
                logger.error("Interpolation RIFE échouée")
                return False, pipeline_result
        else:
            success = rife.interpolate_ffmpeg_fallback(
                input_video=assembled_video,
                output_video=interpolated_video,
                target_fps=target_fps
            )
            if success:
                pipeline_result["stages"]["rife"] = {"status": "OK (ffmpeg fallback)", "output": str(interpolated_video)}
                logger.warn(f"Interpolation via FFmpeg (qualité réduite): {target_fps}FPS")
            else:
                logger.error("Interpolation fallback échouée")
                return False, pipeline_result
        
        upscale_input = interpolated_video
        
        if target_resolution == "4K":
            logger.info("=" * 50)
            logger.info("STAGE 4: Upscale → 4K")
            logger.info("=" * 50)
            
            upscaler = Upscaler(
                model_path=esrgan_model_path,
                use_gpu=use_gpu,
                verbose=logger.verbose
            )
            
            current_res = upscaler.get_resolution(interpolated_video)
            if current_res and current_res[0] < 3840:
                upscaled_video = temp_dir / "upscaled_4k.mp4"
                success = upscaler.upscale(
                    input_video=interpolated_video,
                    output_video=upscaled_video,
                    target_width=3840,
                    target_height=2160
                )
                if success:
                    pipeline_result["stages"]["upscale"] = {"status": "OK", "output": str(upscaled_video)}
                    upscale_input = upscaled_video
                    logger.success("Upscale 4K complété")
                else:
                    logger.warn("Upscale échoué, utilisation résolution originale")
            else:
                logger.info("Résolution déjà ≥4K, upscale ignoré")
                pipeline_result["stages"]["upscale"] = {"status": "SKIPPED", "reason": "already_4k"}
        else:
            pipeline_result["stages"]["upscale"] = {"status": "SKIPPED", "reason": "not_requested"}
        
        logger.info("=" * 50)
        logger.info("STAGE 5: Encodage Final")
        logger.info("=" * 50)
        
        encoder = FinalEncoder(verbose=logger.verbose)
        
        final_mp4 = output_dir / f"FINAL_OUTPUT_{project_name}.mp4"
        success = encoder.encode(
            video_input=upscale_input,
            audio_input=audio_output,
            output_path=final_mp4,
            codec="h265",
            crf=18
        )
        
        if not success:
            logger.error("Encodage H.265 échoué")
            return False, pipeline_result
        
        pipeline_result["stages"]["encode_h265"] = {"status": "OK", "output": str(final_mp4)}
        pipeline_result["files"]["mp4"] = str(final_mp4)
        logger.success(f"H.265 MP4: {final_mp4}")
        
        if codec == "prores" or True:
            final_mov = output_dir / f"FINAL_OUTPUT_{project_name}.mov"
            success = encoder.encode(
                video_input=upscale_input,
                audio_input=audio_output,
                output_path=final_mov,
                codec="prores"
            )
            if success:
                pipeline_result["stages"]["encode_prores"] = {"status": "OK", "output": str(final_mov)}
                pipeline_result["files"]["mov"] = str(final_mov)
                logger.success(f"ProRes MOV: {final_mov}")
            else:
                logger.warn("Encodage ProRes échoué (non bloquant)")
        
        logger.info("=" * 50)
        logger.info("STAGE 6: Génération Thumbnail")
        logger.info("=" * 50)
        
        thumbnail_path = output_dir / f"thumbnail_{project_name}.png"
        success = encoder.extract_thumbnail(
            video_path=final_mp4,
            output_path=thumbnail_path,
            timestamp="50%"
        )
        
        if success:
            pipeline_result["stages"]["thumbnail"] = {"status": "OK", "output": str(thumbnail_path)}
            pipeline_result["files"]["thumbnail"] = str(thumbnail_path)
            logger.success(f"Thumbnail: {thumbnail_path}")
        else:
            logger.warn("Génération thumbnail échouée (non bloquant)")
        
        return True, pipeline_result
        
    finally:
        logger.debug(f"Nettoyage temp: {temp_dir}")
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def generate_report(
    output_dir: Path,
    project_name: str,
    plan: dict,
    pipeline_result: dict,
    success: bool,
    logger: CarrierLogger
) -> dict:
    """Génère le rapport final carrier_report.json."""
    report = {
        "version": CARRIER_VERSION,
        "project": project_name,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "config": plan.get("output", {}),
        "pipeline": pipeline_result.get("stages", {}),
        "outputs": pipeline_result.get("files", {}),
        "warnings": logger.warnings,
        "errors": logger.errors,
        "logs": logger.get_logs()
    }
    
    report_path = output_dir / "carrier_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.success(f"Rapport généré: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description=f'AIRCRAFT CARRIER - EXODUS v{CARRIER_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_06_CARRIER.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --project-name "MyProject"

  python EXO_06_CARRIER.py --drive-root /path/to/drive \\
    --components-dir /path/to/components \\
    --output-dir /path/to/output \\
    --project-name "MyVideo" \\
    -v
        """
    )
    
    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--components-dir',
                        help='Dossier des composants (défaut: IN_COMPONENTS/)')
    parser.add_argument('--output-dir',
                        help='Dossier output (défaut: OUT_FINAL/)')
    parser.add_argument('--production-plan',
                        help='PRODUCTION_PLAN.JSON (défaut: IN_COMPONENTS/PRODUCTION_PLAN.JSON)')
    parser.add_argument('--project-name', default='EXODUS_OUTPUT',
                        help='Nom du projet pour les fichiers output')
    parser.add_argument('--no-rife', action='store_true',
                        help='Désactive RIFE (utilise FFmpeg pour interpolation)')
    parser.add_argument('--no-upscale', action='store_true',
                        help='Désactive upscale même si résolution < 4K')
    parser.add_argument('--cpu-only', action='store_true',
                        help='Force utilisation CPU uniquement')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')
    
    args = parser.parse_args()
    logger = CarrierLogger(verbose=args.verbose)
    
    print("=" * 70)
    print("   FRÉGATE 06_AIRCRAFT_CARRIER — EXODUS FINAL ASSEMBLY")
    print(f"   Version {CARRIER_VERSION}")
    print("=" * 70)
    
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "06_AIRCRAFT_CARRIER"
    
    if args.components_dir:
        components_dir = Path(args.components_dir)
    else:
        components_dir = unit_root / "IN_COMPONENTS"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_FINAL"
    
    if args.production_plan:
        plan_path = Path(args.production_plan)
    else:
        plan_path = components_dir / "PRODUCTION_PLAN.JSON"
    
    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Components: {components_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Project: {args.project_name}")
    
    if not check_ffmpeg(logger):
        sys.exit(1)
    
    use_gpu = not args.cpu_only and check_gpu(logger)
    
    rife_model_path = None
    if not args.no_rife:
        rife_model_path = check_rife_model(drive_root, logger)
        if not rife_model_path:
            logger.warn("RIFE non disponible, interpolation FFmpeg sera utilisée")
    
    esrgan_model_path = None
    if not args.no_upscale:
        esrgan_model_path = check_realesrgan_model(drive_root, logger)
    
    plan = validate_production_plan(plan_path, logger)
    components = validate_components(components_dir, plan, logger)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.success("Configuration validée")
    
    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\n✓ Tous les chemins sont valides. Prêt pour l'assemblage final.")
        
        print("\n=== Résumé ===")
        print(f"  Séquences: {len(components['sequences'])} images")
        print(f"  Audio: {len(components['audio'])} pistes")
        print(f"  Target: {plan['output'].get('resolution', '4K')} @ {plan['output'].get('framerate', 120)}FPS")
        print(f"  GPU: {'Oui' if use_gpu else 'Non'}")
        print(f"  RIFE: {'Oui' if rife_model_path else 'Non (FFmpeg fallback)'}")
        sys.exit(0)
    
    success, pipeline_result = run_pipeline(
        components=components,
        plan=plan,
        output_dir=output_dir,
        project_name=args.project_name,
        drive_root=drive_root,
        rife_model_path=rife_model_path,
        esrgan_model_path=esrgan_model_path,
        use_gpu=use_gpu,
        logger=logger
    )
    
    report = generate_report(
        output_dir,
        args.project_name,
        plan,
        pipeline_result,
        success,
        logger
    )
    
    if not success:
        logger.error("ASSEMBLAGE ÉCHOUÉ")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    logger.success("ASSEMBLAGE FINAL COMPLET")
    for file_type, file_path in pipeline_result.get("files", {}).items():
        print(f"  → {file_type.upper()}: {file_path}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
