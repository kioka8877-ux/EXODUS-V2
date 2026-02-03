#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 01_TRANSMUTATION — EXODUS SYSTEM                     ║
║                    Fusion Corps + Visage → Alembic                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Fusionner body FBX + facial EMOCA → Baked Alembic                 ║
║  Stack: EMOCA + Blender 4.0 Headless + Savitzky-Golay                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS (fournis par l'Empereur):
    - body_motion.fbx : Mouvement corps (MoCap Pro)
    - source_video.mp4 : Vidéo pour extraction faciale
    - actor_model.blend : Avatar Roblox riggé (DynamicHead)
    
OUTPUT:
    - ACTOR_XX.abc : Animation bakée en Alembic
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

TRANSMUTATION_VERSION = "1.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"
EMOCA_SUBDIR = "emoca"


class TransmutationLogger:
    """Logger structuré pour TRANSMUTATION."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def info(self, msg: str):
        print(f"[TRANSMUTATION] {msg}")
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[TRANSMUTATION:DEBUG] {msg}")
    
    def error(self, msg: str):
        print(f"[TRANSMUTATION:ERROR] {msg}", file=sys.stderr)
    
    def success(self, msg: str):
        print(f"[TRANSMUTATION:OK] ✓ {msg}")
    
    def warn(self, msg: str):
        print(f"[TRANSMUTATION:WARN] ⚠ {msg}")


def check_ai_models(drive_root: Path, logger: TransmutationLogger) -> dict:
    """
    Vérifie que les modèles IA sont présents sur le Drive.
    Retourne les chemins vers Blender et EMOCA.
    """
    ai_models_path = drive_root / AI_MODELS_SUBDIR
    
    blender_path = ai_models_path / BLENDER_SUBDIR / "blender"
    emoca_path = ai_models_path / EMOCA_SUBDIR
    
    if not blender_path.exists():
        logger.error(f"Blender 4.0 introuvable: {blender_path}")
        logger.info("Téléchargez Blender 4.0 Linux x64 portable et placez-le dans:")
        logger.info(f"  {ai_models_path / BLENDER_SUBDIR}/")
        sys.exit(1)
    
    if not emoca_path.exists():
        logger.error(f"EMOCA introuvable: {emoca_path}")
        logger.info("Clonez EMOCA et placez les modèles dans:")
        logger.info(f"  {emoca_path}/")
        sys.exit(1)
    
    logger.success("Modèles IA vérifiés")
    return {
        "blender": str(blender_path),
        "emoca": str(emoca_path)
    }


def extract_facial_data(
    video_path: str,
    emoca_path: str,
    output_path: str,
    logger: TransmutationLogger
) -> dict:
    """
    Extrait les 52 blendshapes ARKit depuis la vidéo via EMOCA.
    """
    logger.info("Extraction faciale EMOCA en cours...")
    
    from facial_extractor import EMOCAExtractor
    
    extractor = EMOCAExtractor(emoca_path)
    face_data = extractor.extract_arkit_from_video(video_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(face_data, f, indent=2)
    
    logger.success(f"Données faciales extraites: {len(face_data['frames'])} frames")
    return face_data


def run_blender_fusion(
    blender_path: str,
    body_fbx: str,
    actor_blend: str,
    face_json: str,
    output_abc: str,
    sync_offset: int,
    smooth_window: int,
    logger: TransmutationLogger
) -> bool:
    """
    Exécute Blender en mode headless pour la fusion.
    """
    logger.info("Fusion Blender en cours...")
    
    script_dir = Path(__file__).parent
    fusion_script = script_dir / "blender_fusion.py"
    
    cmd = [
        blender_path,
        "--background",
        "--python", str(fusion_script),
        "--",
        "--body-fbx", body_fbx,
        "--actor-blend", actor_blend,
        "--face-json", face_json,
        "--output", output_abc,
        "--sync-offset", str(sync_offset),
        "--smooth-window", str(smooth_window)
    ]
    
    logger.debug(f"Commande: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Blender échoué: {result.stderr}")
        return False
    
    logger.success(f"Fusion complète: {output_abc}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description=f'TRANSMUTATION ENGINE - EXODUS v{TRANSMUTATION_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_01_TRANSMUTATION.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --body-fbx motion.fbx --video source.mp4 --actor-blend avatar.blend
        """
    )
    
    parser.add_argument('--drive-root', required=True, 
                        help='Racine du Drive EXODUS')
    parser.add_argument('--body-fbx', required=True,
                        help='Fichier FBX du mouvement corps (cherché dans IN_MIXAMO_BASE/)')
    parser.add_argument('--video', required=True,
                        help='Vidéo source pour extraction faciale (cherchée dans IN_CORTEX_JSON/ ou chemin absolu)')
    parser.add_argument('--actor-blend', required=True,
                        help='Fichier .blend de l\'avatar Roblox riggé (chemin absolu requis)')
    parser.add_argument('--production-plan',
                        help='PRODUCTION_PLAN.JSON (cherché dans IN_CORTEX_JSON/)')
    
    parser.add_argument('--output-name', default='TRANSMUTED_ACTOR',
                        help='Nom du fichier output (sans extension)')
    parser.add_argument('--sync-offset', type=int, default=0,
                        help='Offset de synchronisation en frames')
    parser.add_argument('--sync-marker', nargs=2, type=int, metavar=('VIDEO_FRAME', 'FBX_FRAME'),
                        help='Frames de référence pour calculer l\'offset')
    parser.add_argument('--smooth-window', type=int, default=5,
                        help='Fenêtre Savitzky-Golay (impair, défaut: 5)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')
    
    args = parser.parse_args()
    logger = TransmutationLogger(verbose=args.verbose)
    
    print("=" * 70)
    print("   FRÉGATE 01_TRANSMUTATION — EXODUS PRODUCTION PIPELINE")
    print(f"   Version {TRANSMUTATION_VERSION}")
    print("=" * 70)
    
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "01_ANIMATION_ENGINE"
    
    cortex_json_dir = unit_root / "IN_CORTEX_JSON"
    mixamo_base_dir = unit_root / "IN_MIXAMO_BASE"
    output_dir = unit_root / "OUT_MOTION_DATA"
    
    body_path = Path(args.body_fbx)
    if not body_path.is_absolute():
        body_path = mixamo_base_dir / args.body_fbx
    
    video_path = Path(args.video)
    if not video_path.is_absolute():
        video_path = cortex_json_dir / args.video
    
    actor_path = Path(args.actor_blend)
    
    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Body FBX: {body_path}")
    logger.info(f"Video: {video_path}")
    logger.info(f"Actor: {actor_path}")
    
    for path, name in [(body_path, "Body FBX"), (video_path, "Video"), (actor_path, "Actor")]:
        if not path.exists():
            logger.error(f"{name} introuvable: {path}")
            sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ai_paths = check_ai_models(drive_root, logger)
    
    logger.success("Configuration validée")
    
    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\n✓ Tous les chemins sont valides. Prêt pour la transmutation.")
        sys.exit(0)
    
    sync_offset = args.sync_offset
    if args.sync_marker:
        sync_offset = args.sync_marker[0] - args.sync_marker[1]
        logger.info(f"Offset calculé depuis marqueurs: {sync_offset} frames")
    
    face_json_path = output_dir / f"{args.output_name}_face.json"
    output_abc_path = output_dir / f"{args.output_name}.abc"
    
    face_data = extract_facial_data(
        str(video_path),
        ai_paths["emoca"],
        str(face_json_path),
        logger
    )
    
    success = run_blender_fusion(
        ai_paths["blender"],
        str(body_path),
        str(actor_path),
        str(face_json_path),
        str(output_abc_path),
        sync_offset,
        args.smooth_window,
        logger
    )
    
    if not success:
        logger.error("Transmutation échouée")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    logger.success(f"TRANSMUTATION COMPLÈTE: {output_abc_path}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
