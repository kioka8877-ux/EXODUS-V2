#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 01_TRANSMUTATION — EXODUS SYSTEM                     ║
║                    Fusion Corps + Visage → Alembic                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 2.1.0                                                              ║
║  Mission: Fusionner body FBX + Emotional Intent Transfer → Baked Alembic    ║
║  Stack: expression_schema.py + Blender 4.0 Headless + Bézier natif         ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.
    
INPUTS REQUIS (fournis par l'Empereur):
    - body_motion.fbx : Mouvement corps (MoCap Pro)
    - facial_animation.json : Segments émotionnels (produit par U00 CORTEX)
    - actor_model.blend : Avatar Roblox riggé (DynamicHead)
    - audio_source.wav : (optionnel) Audio dialogue pour lip-sync Rhubarb
    - dialogue.txt : (optionnel) Texte du dialogue pour meilleure précision
    
OUTPUT:
    - ACTOR_XX.blend : Master file avec armature active
    - ACTOR_XX.abc : Animation bakée en Alembic
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Phantom Link — Phase D.1
import importlib.util
_phantom_spec = importlib.util.spec_from_file_location("phantom_link", Path(__file__).resolve().parents[2] / "phantom_link.py")
if _phantom_spec and _phantom_spec.loader:
    _phantom_mod = importlib.util.module_from_spec(_phantom_spec)
    _phantom_spec.loader.exec_module(_phantom_mod)
    resolve_input = _phantom_mod.resolve_input
else:
    resolve_input = lambda p: Path(p)  # fallback si phantom_link.py absent

TRANSMUTATION_VERSION = "2.1.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"


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
        print(f"[TRANSMUTATION:OK] {msg}")

    def warn(self, msg: str):
        print(f"[TRANSMUTATION:WARN] {msg}")


def check_ai_models(drive_root: Path, logger: TransmutationLogger, blender_path_arg: str = None) -> dict:
    """
    Vérifie que Blender est présent.
    Chaîne de priorité : arg CLI → env var → Drive → /opt/ local.
    """
    ai_models_path = drive_root / AI_MODELS_SUBDIR

    candidates = []
    if blender_path_arg:
        candidates.append(blender_path_arg)
    if os.environ.get("BLENDER_PATH"):
        candidates.append(os.environ["BLENDER_PATH"])
    candidates.append(str(ai_models_path / BLENDER_SUBDIR / "blender"))
    candidates.extend([
        "/opt/blender-4.0.2-linux-x64/blender",
        "/opt/blender-4.0.0-linux-x64/blender",
        "/usr/local/bin/blender",
    ])

    blender_path = None
    for candidate in candidates:
        if Path(candidate).exists():
            blender_path = candidate
            logger.success(f"Blender trouvé: {blender_path}")
            break

    if not blender_path:
        logger.error("Blender 4.0 introuvable dans aucun des chemins candidates")
        logger.info(f"Candidats testés: {candidates}")
        sys.exit(1)

    result = {"blender": blender_path}

    rhubarb_path = ai_models_path / "rhubarb" / "rhubarb"
    if rhubarb_path.exists():
        logger.success("Rhubarb lip-sync trouvé")
        result["rhubarb"] = str(rhubarb_path)
    else:
        logger.warn("Rhubarb non trouvé (lip-sync désactivé)")
        result["rhubarb"] = None

    return result


def auto_detect_actor_model(unit_root, logger) -> str:
    """
    FIX #1b — Scanne IN_CORTEX_JSON/actor_models/ pour le premier modèle 3D trouvé.
    Formats supportés : .blend .fbx .glb .gltf .obj
    Hard-fail si aucun modèle trouvé.
    """
    SUPPORTED = {".blend", ".fbx", ".glb", ".gltf", ".obj"}
    actor_dir = unit_root / "IN_CORTEX_JSON" / "actor_models"

    if not actor_dir.exists():
        logger.error(f"[U01] ❌ ACTOR_DIR_MISSING: {actor_dir}")
        logger.error("[U01]   Créez le dossier et déposez votre modèle 3D")
        sys.exit(1)

    models = [f for f in actor_dir.iterdir() if f.suffix.lower() in SUPPORTED]
    if not models:
        logger.error(f"[U01] ❌ ACTOR_MODEL_MISSING: aucun modèle 3D dans {actor_dir}")
        logger.error(f"[U01]   Formats supportés: {', '.join(sorted(SUPPORTED))}")
        sys.exit(1)

    chosen = models[0]
    logger.info(f"[U01] Modèle auto-détecté : {chosen.name}")
    return str(chosen)



def translate_facial_data(
    facial_json_path: str,
    output_path: str,
    fps: int,
    logger: TransmutationLogger
) -> dict:
    """
    Traduit les segments émotionnels en shape key data via EmotionalIntentTranslator.
    """
    logger.info("Traduction émotionnelle en cours...")

    from facial_extractor import EmotionalIntentTranslator

    translator = EmotionalIntentTranslator()
    facial_data = translator.load_facial_animation(facial_json_path)
    blender_data = translator.generate_blender_data(facial_data, fps=fps)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(blender_data, f, indent=2)

    n_seg = len(blender_data["segments"])
    n_micro = len(blender_data["micro_expressions"])
    logger.success(f"Données traduites: {n_seg} segments, {n_micro} micro-expressions")
    return blender_data


def generate_lip_sync_data(
    audio_path: str,
    dialogue_path: str,
    output_path: str,
    fps: int,
    rhubarb_path: str,
    logger: TransmutationLogger
) -> dict:
    """Génère les données lip-sync via RhubarbBridge."""
    logger.info("Génération lip-sync Rhubarb en cours...")

    from rhubarb_bridge import RhubarbBridge

    bridge = RhubarbBridge(rhubarb_path=rhubarb_path)
    lip_sync_data = bridge.generate_lip_sync_data(audio_path, dialogue_path, fps=fps)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(lip_sync_data, f, indent=2)

    n_cues = len(lip_sync_data["lip_sync_segments"])
    logger.success(f"Lip-sync généré: {n_cues} cues")
    return lip_sync_data


def run_blender_fusion(
    blender_path: str,
    body_fbx: str,
    actor_blend: str,
    face_json: str,
    output_abc: str,
    sync_offset: int,
    intensity_mode: str,
    logger: TransmutationLogger,
    lip_sync_json_path: str = None,
    actor_model_path: str = None,
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
        "--actor-model", actor_model_path or actor_blend,
        "--face-json", face_json,
        "--output", output_abc,
        "--sync-offset", str(sync_offset),
        "--intensity-mode", intensity_mode,
    ]

    if lip_sync_json_path:
        cmd.extend(["--lip-sync-json", lip_sync_json_path])

    logger.debug(f"Commande: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Blender échoué: {result.stderr}")
        return False

    logger.success(f"Fusion complète: {output_abc}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description=f'TRANSMUTATION ENGINE V2 - EXODUS v{TRANSMUTATION_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_01_TRANSMUTATION.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --body-fbx motion.fbx --facial-json facial_animation.json --actor-blend avatar.blend
        """
    )

    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--blender-path', default=None,
                        help='Chemin vers Blender (optionnel, priorité sur auto-détection)')
    parser.add_argument('--body-fbx', required=True,
                        help='Fichier FBX du mouvement corps (cherché dans IN_MIXAMO_BASE/)')
    parser.add_argument('--facial-json', required=True,
                        help='facial_animation.json (cherché dans IN_CORTEX_JSON/)')
    parser.add_argument('--actor-model', required=False, default=None,
                        help='Modèle 3D acteur (.blend/.fbx/.glb/.obj) — auto-détecté dans IN_CORTEX_JSON/actor_models/ si absent')
    # Alias legacy
    parser.add_argument('--actor-blend', required=False, default=None,
                        help='[LEGACY] Alias --actor-model pour compatibilité')
    parser.add_argument('--production-plan',
                        help='PRODUCTION_PLAN.JSON (cherché dans IN_CORTEX_JSON/)')

    parser.add_argument('--output-name', default='TRANSMUTED_ACTOR',
                        help='Nom du fichier output (sans extension)')
    parser.add_argument('--sync-offset', type=int, default=0,
                        help='Offset de synchronisation en frames')
    parser.add_argument('--intensity-mode', choices=['linear', 'quadratic', 'ease_in_out'],
                        default='ease_in_out',
                        help='Mode d\'interpolation d\'intensité (défaut: ease_in_out)')
    parser.add_argument('--audio', default=None,
                        help='Audio WAV pour lip-sync Rhubarb (optionnel, cherché dans IN_CORTEX_JSON/)')
    parser.add_argument('--dialogue', default=None,
                        help='Fichier texte du dialogue pour Rhubarb (optionnel)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valider les chemins sans exécuter')

    args = parser.parse_args()
    logger = TransmutationLogger(verbose=args.verbose)

    print("=" * 70)
    print("   FRÉGATE 01_TRANSMUTATION — EXODUS PRODUCTION PIPELINE V2")
    print(f"   Version {TRANSMUTATION_VERSION}")
    print("=" * 70)

    drive_root = Path(args.drive_root)
    unit_root = drive_root / "01_ANIMATION_ENGINE"

    cortex_json_dir = resolve_input(unit_root / "IN_CORTEX_JSON")
    mixamo_base_dir = resolve_input(unit_root / "IN_MIXAMO_BASE")
    output_dir = unit_root / "OUT_MOTION_DATA"

    body_path = Path(args.body_fbx)
    if not body_path.is_absolute():
        body_path = mixamo_base_dir / args.body_fbx

    facial_json_path = Path(args.facial_json)
    if not facial_json_path.is_absolute():
        facial_json_path = cortex_json_dir / args.facial_json

    # FIX #1b — Résoudre le modèle acteur (--actor-model > --actor-blend > auto-detect)
    _actor_arg = args.actor_model or args.actor_blend
    if _actor_arg:
        actor_path = Path(_actor_arg)
    else:
        actor_path = Path(auto_detect_actor_model(unit_root, logger))

    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Body FBX: {body_path}")
    logger.info(f"Facial JSON: {facial_json_path}")
    logger.info(f"Actor: {actor_path}")

    for path, name in [
        (body_path, "Body FBX"),
        (facial_json_path, "Facial JSON"),
        (actor_path, "Actor"),
    ]:
        if not path.exists():
            logger.error(f"{name} introuvable: {path}")
            sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    ai_paths = check_ai_models(drive_root, logger, blender_path_arg=args.blender_path)

    logger.success("Configuration validée")

    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\nTous les chemins sont valides. Prêt pour la transmutation.")
        sys.exit(0)

    translated_json_path = output_dir / f"{args.output_name}_translated.json"
    output_abc_path = output_dir / f"{args.output_name}.abc"

    blender_data = translate_facial_data(
        str(facial_json_path),
        str(translated_json_path),
        fps=30,
        logger=logger,
    )

    # Lip-sync (optionnel)
    lip_sync_json_path = None
    if args.audio:
        audio_path = Path(args.audio)
        if not audio_path.is_absolute():
            audio_path = cortex_json_dir / args.audio

        if not audio_path.exists():
            logger.warn(f"Audio non trouvé: {audio_path} — lip-sync ignoré")
        elif not ai_paths.get("rhubarb"):
            logger.warn("Rhubarb non installé — lip-sync ignoré")
        else:
            dialogue_path = None
            if args.dialogue:
                dp = Path(args.dialogue)
                if not dp.is_absolute():
                    dp = cortex_json_dir / args.dialogue
                if dp.exists():
                    dialogue_path = str(dp)

            lip_sync_json_path = str(output_dir / f"{args.output_name}_lipsync.json")
            generate_lip_sync_data(
                str(audio_path), dialogue_path, lip_sync_json_path, fps=30,
                rhubarb_path=ai_paths["rhubarb"], logger=logger
            )

    success = run_blender_fusion(
        ai_paths["blender"],
        str(body_path),
        str(actor_path),
        str(translated_json_path),
        str(output_abc_path),
        args.sync_offset,
        args.intensity_mode,
        logger,
        lip_sync_json_path=lip_sync_json_path,
        actor_model_path=str(actor_path),
    )

    if not success:
        logger.error("Transmutation échouée")
        sys.exit(1)

    blend_path = output_abc_path.with_suffix('.blend')
    if blend_path.exists():
        logger.success(f"Output .blend: {blend_path}")
    if output_abc_path.exists():
        logger.success(f"Output .abc: {output_abc_path}")

    print("\n" + "=" * 70)
    logger.success(f"TRANSMUTATION V2 COMPLÈTE: {output_abc_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
