#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           FRÉGATE 01_TRANSMUTATION — EXODUS V1 PIVOT                        ║
║           Orchestrateur Multi-Avatar — Corps + Visage + Lip-Sync            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 3.0.0 — Codex Imperial v6 (23.04.2026)                           ║
║  D-I  : Corps animé = avatar-ferrus-N.blend (outil externe, 0 Mixamo)      ║
║  D-II : EMOCA sur visage humain réel (InsightFace → crops → EMOCA)         ║
║  D-III: Rhubarb TOUJOURS activé si audio_original.wav présent              ║
║         pyannote → piste propre par avatar → Rhubarb                       ║
║  D-IV : for N in avatars (scalable 1→N sans modification)                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  INPUTS (IN_BODY_ANIMATED/):                                                ║
║    avatar-ferrus-N.blend  (corps pré-animé, livré par outil externe)       ║
║  INPUTS (IN_VIDEO_SOURCE/):                                                 ║
║    video_source.mp4       (vidéo humaine originale)                         ║
║    audio_original.wav     (audio source, toutes voix)                       ║
║  INPUTS (IN_CORTEX_JSON/):                                                  ║
║    PRODUCTION_PLAN.JSON   (de U00 CORTEX)                                   ║
║  OUTPUTS (OUT_ANIMATED_ACTORS/):                                            ║
║    avatar-ferrus-N_animated.blend + .abc                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import importlib.util
_phantom_spec = importlib.util.spec_from_file_location(
    "phantom_link", Path(__file__).resolve().parents[2] / "phantom_link.py"
)
if _phantom_spec and _phantom_spec.loader:
    _phantom_mod = importlib.util.module_from_spec(_phantom_spec)
    _phantom_spec.loader.exec_module(_phantom_mod)
    resolve_input = _phantom_mod.resolve_input
else:
    resolve_input = lambda p: Path(p)

TRANSMUTATION_VERSION = "3.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"

BODY_ANIMATED_DIR = "IN_BODY_ANIMATED"
VIDEO_SOURCE_DIR = "IN_VIDEO_SOURCE"
CORTEX_JSON_DIR = "IN_CORTEX_JSON"
OUTPUT_DIR = "OUT_ANIMATED_ACTORS"

AVATAR_BLEND_PATTERN = "avatar-ferrus-*.blend"
VIDEO_FILENAME = "video_source.mp4"
AUDIO_FILENAME = "audio_original.wav"
PLAN_FILENAME = "PRODUCTION_PLAN.JSON"


class Logger:
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

    def section(self, title: str):
        print(f"\n{'─'*60}\n  {title}\n{'─'*60}")


def discover_avatars(body_animated_dir: Path, logger: Logger) -> List[Path]:
    """Scanne IN_BODY_ANIMATED/ — hard-fail si vide."""
    if not body_animated_dir.exists():
        logger.error(
            f"IN_BODY_ANIMATED/ manquant: {body_animated_dir}\n"
            "  Déposez les avatar-ferrus-N.blend (livrés par outil externe)"
        )
        sys.exit(1)
    avatars = sorted(body_animated_dir.glob(AVATAR_BLEND_PATTERN))
    if not avatars:
        logger.error(f"Aucun avatar-ferrus-*.blend dans {body_animated_dir}")
        sys.exit(1)
    logger.success(f"{len(avatars)} avatar(s) trouvé(s):")
    for av in avatars:
        logger.info(f"  - {av.name}")
    return avatars


def find_blender(drive_root: Path, blender_arg: Optional[str], logger: Logger) -> str:
    candidates = []
    if blender_arg:
        candidates.append(blender_arg)
    if os.environ.get("BLENDER_PATH"):
        candidates.append(os.environ["BLENDER_PATH"])
    candidates += [
        str(drive_root / AI_MODELS_SUBDIR / BLENDER_SUBDIR / "blender"),
        "/opt/blender-4.0.2-linux-x64/blender",
        "/opt/blender-4.0.0-linux-x64/blender",
        "/usr/local/bin/blender",
    ]
    for c in candidates:
        if Path(c).exists():
            logger.success(f"Blender: {c}")
            return c
    logger.error(f"Blender 4.0 introuvable. Candidats: {candidates}")
    sys.exit(1)


def find_rhubarb(drive_root: Path, logger: Logger) -> Optional[str]:
    env_path = os.environ.get("RHUBARB_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    candidates = [
        str(drive_root / AI_MODELS_SUBDIR / "rhubarb" / "rhubarb"),
        "/usr/local/bin/rhubarb",
        "/opt/rhubarb/rhubarb",
    ]
    for c in candidates:
        if Path(c).exists():
            logger.success(f"Rhubarb: {c}")
            return c
    return None


def run_insightface_tracking(
    video_path: Path,
    tracks_dir: Path,
    production_plan: dict,
    logger: Logger,
    verbose: bool = False,
) -> Tuple[dict, dict, dict]:
    """Phase A: InsightFace → tracks + mapping avatars + crops."""
    logger.section("PHASE A — InsightFace Tracking")
    from insightface_tracker import InsightFaceTracker

    tracker = InsightFaceTracker(verbose=verbose)
    try:
        tracks = tracker.track_video(str(video_path))
        crops = tracker.extract_crops(str(video_path), tracks, str(tracks_dir))
        avatar_mapping = tracker.map_to_avatars(tracks, production_plan)
        report = tracker.create_report(tracks, avatar_mapping)
        with open(tracks_dir / "insightface_report.json", "w") as f:
            json.dump(report, f, indent=2)
        logger.success(f"InsightFace: {len(tracks)} identités")
        return tracks, avatar_mapping, crops
    finally:
        tracker.teardown()


def run_diarization(
    audio_path: Path,
    audio_dir: Path,
    avatar_names: List[str],
    production_plan: dict,
    logger: Logger,
    hf_token: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, str]:
    """Phase B: pyannote → pistes audio propres par avatar (D-III)."""
    logger.section("PHASE B — Speaker Diarization (pyannote.audio)")
    from pyannote_diarizer import PyannoteDialrizer

    diarizer = PyannoteDialrizer(hf_token=hf_token, verbose=verbose)
    try:
        segments = diarizer.diarize(str(audio_path), num_speakers=len(avatar_names))
        mapping = diarizer.map_speakers_to_avatars(segments, avatar_names, production_plan)
        avatar_tracks = diarizer.generate_avatar_tracks(
            str(audio_path), mapping, segments, str(audio_dir)
        )
        report = diarizer.create_report(segments, mapping, avatar_tracks)
        with open(audio_dir / "diarization_report.json", "w") as f:
            json.dump(report, f, indent=2)
        logger.success(f"Diarization: {len(avatar_tracks)} pistes")
        return avatar_tracks
    finally:
        diarizer.teardown()


def run_emoca_for_avatar(
    crop_paths: List[str],
    frame_indices: List[int],
    avatar_name: str,
    output_dir: Path,
    video_fps: float,
    logger: Logger,
    model_path: Optional[str] = None,
    device: str = "cuda",
    verbose: bool = False,
) -> str:
    """Phase C: EMOCA sur crops visage humain réel → facial_animation.json (D-II)."""
    logger.info(f"EMOCA: {avatar_name}...")
    from emoca_extractor import EMOCAExtractor

    extractor = EMOCAExtractor(model_path=model_path, device=device, verbose=verbose)
    try:
        segments = extractor.extract_from_crops(
            crop_paths, video_fps=video_fps, frame_indices=frame_indices
        )
        result = extractor.to_facial_animation_json(segments, avatar_name=avatar_name)
        out_path = str(output_dir / f"{avatar_name}_facial_animation.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.success(f"EMOCA {avatar_name}: {len(segments)} segments")
        return out_path
    finally:
        extractor.teardown()


def translate_facial_data(
    facial_json_path: str,
    output_path: str,
    fps: int,
    logger: Logger,
) -> dict:
    from facial_extractor import EmotionalIntentTranslator
    translator = EmotionalIntentTranslator()
    blender_data = translator.generate_blender_data(
        translator.load_facial_animation(facial_json_path), fps=fps
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blender_data, f, indent=2)
    logger.success(f"Translation: {len(blender_data['segments'])} segments")
    return blender_data


def generate_lip_sync(
    audio_path: str,
    rhubarb_path: str,
    avatar_name: str,
    output_dir: Path,
    fps: int,
    logger: Logger,
    verbose: bool = False,
) -> Optional[str]:
    """D-III: Rhubarb TOUJOURS activé si audio présent."""
    from rhubarb_bridge import RhubarbBridge
    try:
        bridge = RhubarbBridge(rhubarb_path=rhubarb_path)
        lip_data = bridge.generate_lip_sync_data(audio_path, None, fps=fps)
        out_path = str(output_dir / f"{avatar_name}_lipsync.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(lip_data, f, indent=2)
        n = len(lip_data.get("lip_sync_segments", []))
        logger.success(f"Rhubarb {avatar_name}: {n} cues")
        return out_path
    except Exception as e:
        logger.error(f"Rhubarb {avatar_name}: {e}")
        return None


def run_blender_fusion(
    blender_path: str,
    body_blend: str,
    translated_json: str,
    output_blend: str,
    output_abc: str,
    logger: Logger,
    lip_sync_json: Optional[str] = None,
    intensity_mode: str = "ease_in_out",
    fps: int = 30,
    verbose: bool = False,
) -> bool:
    """Phase F: Blender headless — corps .blend + visage + lip-sync (D-I)."""
    script = Path(__file__).parent / "blender_fusion.py"
    cmd = [
        blender_path, "--background",
        "--python", str(script),
        "--",
        "--body-blend", body_blend,
        "--face-json", translated_json,
        "--output-blend", output_blend,
        "--output-abc", output_abc,
        "--intensity-mode", intensity_mode,
        "--fps", str(fps),
    ]
    if lip_sync_json:
        cmd += ["--lip-sync-json", lip_sync_json]
    if verbose:
        cmd.append("--verbose")

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        logger.error(f"Blender échoué:\n{r.stderr[-600:]}")
        return False
    logger.success(f"Blender OK → {output_blend}")
    return True


def process_avatar(
    idx: int,
    avatar_blend: Path,
    face_crops: List[str],
    face_frame_indices: List[int],
    avatar_audio: Optional[str],
    rhubarb_path: Optional[str],
    blender_path: str,
    output_dir: Path,
    tmp_dir: Path,
    video_fps: float,
    logger: Logger,
    args,
) -> dict:
    """Traite un avatar complet (D-IV: boucle for N in avatars)."""
    avatar_name = avatar_blend.stem
    logger.section(f"AVATAR {idx}: {avatar_name}")
    t0 = time.time()

    atmp = tmp_dir / avatar_name
    atmp.mkdir(parents=True, exist_ok=True)

    result = {
        "avatar": avatar_name,
        "success": False,
        "elapsed": 0.0,
        "outputs": {},
    }

    # ── EMOCA (D-II) ──────────────────────────────────────────────────────────
    facial_json = str(atmp / f"{avatar_name}_facial_animation.json")
    if face_crops and not args.skip_emoca:
        facial_json = run_emoca_for_avatar(
            crop_paths=face_crops,
            frame_indices=face_frame_indices,
            avatar_name=avatar_name,
            output_dir=atmp,
            video_fps=video_fps,
            logger=logger,
            model_path=args.emoca_model_path,
            device=args.device,
            verbose=args.verbose,
        )
    else:
        # Neutral fallback
        fallback = {"facial_animation": [{
            "time_start": 0.0, "time_end": 5.0,
            "expression": "neutral", "eyes": "focused_forward",
            "mouth": "neutral", "intensity": 0.5, "apex_time": 2.5,
            "low_visibility": True,
        }]}
        with open(facial_json, "w") as f:
            json.dump(fallback, f, indent=2)
        logger.warn(f"Fallback neutral pour {avatar_name}")

    # ── Translation (expression_schema) ──────────────────────────────────────
    translated_json = str(atmp / f"{avatar_name}_translated.json")
    try:
        translate_facial_data(facial_json, translated_json, fps=args.fps, logger=logger)
    except Exception as e:
        logger.error(f"Translation {avatar_name}: {e}")
        result["elapsed"] = round(time.time() - t0, 1)
        return result

    # ── Rhubarb (D-III: OBLIGATOIRE) ─────────────────────────────────────────
    lipsync_json = None
    if avatar_audio and Path(avatar_audio).exists():
        if rhubarb_path:
            lipsync_json = generate_lip_sync(
                audio_path=avatar_audio,
                rhubarb_path=rhubarb_path,
                avatar_name=avatar_name,
                output_dir=atmp,
                fps=args.fps,
                logger=logger,
                verbose=args.verbose,
            )
        else:
            logger.warn(
                f"[D-III] Rhubarb OBLIGATOIRE mais introuvable pour {avatar_name}.\n"
                "  Installez Rhubarb: https://github.com/DanielSWolf/rhubarb-lip-sync\n"
                "  export RHUBARB_PATH=/opt/rhubarb/rhubarb"
            )

    # ── Blender Fusion (D-I: .blend input) ───────────────────────────────────
    out_blend = str(output_dir / f"{avatar_name}_animated.blend")
    out_abc = str(output_dir / f"{avatar_name}_animated.abc")

    if not args.dry_run:
        ok = run_blender_fusion(
            blender_path=blender_path,
            body_blend=str(avatar_blend),
            translated_json=translated_json,
            output_blend=out_blend,
            output_abc=out_abc,
            logger=logger,
            lip_sync_json=lipsync_json,
            intensity_mode=args.intensity_mode,
            fps=args.fps,
            verbose=args.verbose,
        )
        result["success"] = ok
    else:
        logger.info(f"[DRY-RUN] Blender sauté pour {avatar_name}")
        result["success"] = True

    elapsed = round(time.time() - t0, 1)
    result["elapsed"] = elapsed
    result["outputs"] = {
        "blend": out_blend,
        "abc": out_abc,
        "facial_json": facial_json,
        "translated_json": translated_json,
        "lipsync_json": lipsync_json,
    }

    status = "OK" if result["success"] else "ECHEC"
    logger.info(f"{avatar_name}: {status} en {elapsed}s")
    return result


def main():
    parser = argparse.ArgumentParser(
        description=f"TRANSMUTATION V1 PIVOT — EXODUS v{TRANSMUTATION_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--drive-root", required=True)
    parser.add_argument("--blender-path", default=None)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument(
        "--intensity-mode",
        choices=["linear", "quadratic", "ease_in_out"],
        default="ease_in_out",
    )
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--hf-token", default=None,
                        help="Hugging Face token pour pyannote.audio")
    parser.add_argument("--emoca-model-path", default=None)
    parser.add_argument("--skip-emoca", action="store_true",
                        help="Expressions neutres (sans EMOCA, pour tests rapides)")
    parser.add_argument("--skip-diarization", action="store_true",
                        help="Piste audio globale (sans diarization par speaker)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logger = Logger(verbose=args.verbose)
    t_total = time.time()

    print("=" * 70)
    print(f"   FRÉGATE 01 — V1 PIVOT MULTI-AVATAR v{TRANSMUTATION_VERSION}")
    print(f"   Décrets D-I D-II D-III D-IV — Codex Imperial v6")
    print("=" * 70)

    drive_root = Path(args.drive_root)
    unit_root = drive_root / "01_ANIMATION_ENGINE"

    body_animated_dir = resolve_input(unit_root / BODY_ANIMATED_DIR)
    video_source_dir = resolve_input(unit_root / VIDEO_SOURCE_DIR)
    cortex_json_dir = resolve_input(unit_root / CORTEX_JSON_DIR)
    output_dir = unit_root / OUTPUT_DIR
    tmp_dir = unit_root / "TMP_TRANSMUTATION"

    video_path = video_source_dir / VIDEO_FILENAME
    audio_path = video_source_dir / AUDIO_FILENAME
    plan_path = cortex_json_dir / PLAN_FILENAME

    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # ── Pre-flight ────────────────────────────────────────────────────────────
    logger.section("PRE-FLIGHT")
    if not video_path.exists():
        logger.error(f"video_source.mp4 manquant: {video_path}")
        sys.exit(1)
    if not plan_path.exists():
        logger.error(f"PRODUCTION_PLAN.JSON manquant: {plan_path}")
        sys.exit(1)

    audio_present = audio_path.exists()
    if not audio_present:
        logger.warn(f"audio_original.wav absent: {audio_path}")

    with open(plan_path, "r", encoding="utf-8") as f:
        production_plan = json.load(f)
    logger.success("PRODUCTION_PLAN.JSON chargé")

    avatar_blends = discover_avatars(Path(str(body_animated_dir)), logger)
    avatar_names = [av.stem for av in avatar_blends]
    n_avatars = len(avatar_blends)

    blender_path = find_blender(drive_root, args.blender_path, logger)
    rhubarb_path = find_rhubarb(drive_root, logger)
    if audio_present and not rhubarb_path:
        logger.warn("[D-III] Rhubarb non trouvé. Lip-sync OBLIGATOIRE — voir README_DEV.md")

    if args.dry_run:
        logger.success(f"Dry-run OK: {n_avatars} avatar(s) configuré(s)")
        sys.exit(0)

    # ── Phase A: InsightFace ───────────────────────────────────────────────────
    avatar_to_face: Dict[str, dict] = {}
    if not args.skip_emoca:
        tracks_dir = tmp_dir / "insightface_tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)
        try:
            tracks, face_avatar_map, crops_per_face = run_insightface_tracking(
                video_path=video_path,
                tracks_dir=tracks_dir,
                production_plan=production_plan,
                logger=logger,
                verbose=args.verbose,
            )
            for face_id, av_name in face_avatar_map.items():
                if av_name in avatar_names and face_id in tracks:
                    avatar_to_face[av_name] = {
                        "crops": crops_per_face.get(face_id, []),
                        "frame_indices": tracks[face_id].frame_indices,
                    }
        except Exception as e:
            logger.warn(f"InsightFace échoué: {e} — fallback neutral")

    # ── Phase B: Diarization ──────────────────────────────────────────────────
    avatar_audio_tracks: Dict[str, Optional[str]] = {n: None for n in avatar_names}
    if audio_present and not args.skip_diarization:
        audio_dir = tmp_dir / "audio_tracks"
        audio_dir.mkdir(parents=True, exist_ok=True)
        try:
            avatar_audio_tracks = run_diarization(
                audio_path=audio_path,
                audio_dir=audio_dir,
                avatar_names=avatar_names,
                production_plan=production_plan,
                logger=logger,
                hf_token=args.hf_token or os.environ.get("HF_TOKEN"),
                verbose=args.verbose,
            )
        except Exception as e:
            logger.warn(f"Diarization échouée: {e} — piste globale pour tous les avatars")
            for n in avatar_names:
                avatar_audio_tracks[n] = str(audio_path)
    elif audio_present:
        for n in avatar_names:
            avatar_audio_tracks[n] = str(audio_path)

    # ── Boucle Multi-Avatar D-IV ───────────────────────────────────────────────
    logger.section(f"FORGE — {n_avatars} avatar(s)")
    results = []
    for idx, av_blend in enumerate(avatar_blends):
        av_name = av_blend.stem
        fd = avatar_to_face.get(av_name, {})
        res = process_avatar(
            idx=idx,
            avatar_blend=av_blend,
            face_crops=fd.get("crops", []),
            face_frame_indices=fd.get("frame_indices", []),
            avatar_audio=avatar_audio_tracks.get(av_name),
            rhubarb_path=rhubarb_path,
            blender_path=blender_path,
            output_dir=output_dir,
            tmp_dir=tmp_dir,
            video_fps=float(args.fps),
            logger=logger,
            args=args,
        )
        results.append(res)

    # ── Rapport ───────────────────────────────────────────────────────────────
    elapsed_total = time.time() - t_total
    n_ok = sum(1 for r in results if r["success"])

    print("\n" + "=" * 70)
    print(f"   TRANSMUTATION V1 PIVOT — {n_ok}/{n_avatars} OK — {elapsed_total:.1f}s")
    print("=" * 70)
    for r in results:
        s = "✓" if r["success"] else "✗"
        print(f"   {s} {r['avatar']} ({r['elapsed']}s)")

    report = {
        "version": TRANSMUTATION_VERSION,
        "timestamp": datetime.now().isoformat(),
        "n_avatars": n_avatars,
        "n_success": n_ok,
        "elapsed_total": round(elapsed_total, 1),
        "results": results,
    }
    rp = output_dir / "transmutation_report.json"
    with open(rp, "w") as f:
        json.dump(report, f, indent=2)
    logger.success(f"Rapport → {rp}")

    if n_ok < n_avatars:
        sys.exit(1)

    logger.success(f"TRANSMUTATION V1 PIVOT COMPLÈTE → {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
