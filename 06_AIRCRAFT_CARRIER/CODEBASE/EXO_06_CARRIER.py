#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 06_AIRCRAFT_CARRIER — EXODUS SYSTEM V2               ║
║          Pipeline Frame-Based : ZÉRO compression lossy intermédiaire        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 2.0.0                                                              ║
║  Mission: Assembler frames PNG, RIFE 120FPS, upscale 4K, encode UNE FOIS   ║
║  Stack: FFmpeg + RIFE + Real-ESRGAN + carrier_schema                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.

INPUTS REQUIS (fournis par l'Empereur):
    - graded_*.exr/png : Séquences rendues de U05
    - audio_*.wav : Pistes audio (music, sfx, voice)
    - PRODUCTION_PLAN.JSON : Instructions d'assemblage

OUTPUTS:
    - FINAL_OUTPUT_*.mp4 : Livrable 4K/120FPS
    - FINAL_OUTPUT_*.mov : ProRes archivage
    - thumbnail_*.png : Vignette publication
    - carrier_report.json : Log de production

PIPELINE V2 — Frame-Based:
    1. Frame Indexer    → manifeste JSON (pas de vidéo)
    2. Audio Prep       → audio_mixed.wav (LUFS -14)
    3. Chunk Pipeline   → pour chaque chunk de 10s :
       3a. RIFE         → frames PNG interpolées 120fps
       3b. Upscale      → frames PNG 4K
       3c. Accumulate   → frames finales numérotées
       3d. Checkpoint   → checkpoint.json + cleanup
    4. Final Encode     → SEULE compression lossy (AV1/H.265/ProRes)
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Phantom Link — Phase D.1
import importlib.util
_phantom_spec = importlib.util.spec_from_file_location("phantom_link", Path(__file__).resolve().parents[2] / "phantom_link.py")
if _phantom_spec and _phantom_spec.loader:
    _phantom_mod = importlib.util.module_from_spec(_phantom_spec)
    _phantom_spec.loader.exec_module(_phantom_mod)
    resolve_input = _phantom_mod.resolve_input
else:
    resolve_input = lambda p: Path(p)  # fallback si phantom_link.py absent

sys.path.insert(0, str(Path(__file__).parent))
from carrier_schema import (
    CarrierSchema, ENCODING_PRESETS, DEFAULT_PRESET,
    RIFE_CHUNK_SECONDS, CHECKPOINT_FILENAME,
    parse_format_metadata, calculate_rife_params,
    FALLBACK_CHAIN, DEFAULT_TARGET_FPS, DEFAULT_SOURCE_FPS,
)

CARRIER_VERSION = "2.0.0"

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
        entry = f"[CARRIER:OK] {msg}"
        print(entry)
        self.logs.append({"level": "SUCCESS", "message": msg, "timestamp": datetime.now().isoformat()})

    def warn(self, msg: str):
        entry = f"[CARRIER:WARN] {msg}"
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


def check_av1_available(logger: CarrierLogger) -> bool:
    """Vérifie si libsvtav1 est disponible dans FFmpeg."""
    try:
        result = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=10)
        available = "libsvtav1" in result.stdout
        if available:
            logger.success("AV1 (libsvtav1) disponible")
        else:
            logger.debug("AV1 (libsvtav1) non disponible")
        return available
    except Exception:
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

    logger.debug(f"Modèle RIFE introuvable dans: {rife_path}")
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

    if "output" not in plan and "production_plan" not in plan:
        logger.warn("Aucune config 'output'/'production_plan' dans le plan, utilisation des défauts")
        plan["output"] = {
            "resolution": "4K",
            "framerate": 120,
            "codec": "h265",
            "audio_tracks": []
        }

    logger.success("Plan de production validé")
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
            logger.debug(f"  Audio: {track_name}")
        else:
            logger.warn(f"  Audio manquant: {track_name}")

    audio_wavs = sorted(components_dir.glob("audio_*.wav"))
    for wav in audio_wavs:
        if wav not in components["audio"]:
            components["audio"].append(wav)
            logger.debug(f"  Audio (auto): {wav.name}")

    if not components["audio"]:
        logger.warn("Aucune piste audio trouvée - vidéo sera muette")
    else:
        logger.success(f"Pistes audio: {len(components['audio'])}")

    return components


def save_checkpoint(path: Path, next_chunk: int, metadata: dict = None):
    """Écrit un fichier checkpoint JSON."""
    data = {
        "version": CARRIER_VERSION,
        "next_chunk": next_chunk,
        "timestamp": datetime.now().isoformat(),
        **(metadata or {}),
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_checkpoint(path: Path) -> int:
    """Lit le checkpoint et retourne le numéro du prochain chunk à traiter."""
    if not path.exists():
        return 0
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("next_chunk", 0)
    except Exception:
        return 0


def resolve_preset(preset_name: str, crf_override: int = None, codec_override: str = None,
                   av1_available: bool = True, logger: CarrierLogger = None) -> dict:
    """Résout un preset d'encodage avec fallbacks.

    Returns:
        {"preset_name": str, "codec": str, "crf": int}
    """
    if preset_name == "custom":
        codec = codec_override or ("av1" if av1_available else "h265")
        crf = crf_override or ENCODING_PRESETS.get("distribution", {}).get("crf", 30)
        return {"preset_name": "custom", "codec": codec, "crf": crf}

    if preset_name not in ENCODING_PRESETS:
        if logger:
            logger.warn(f"Preset '{preset_name}' inconnu, fallback '{DEFAULT_PRESET}'")
        preset_name = DEFAULT_PRESET

    ep = ENCODING_PRESETS[preset_name]

    if ep.get("codec") == "libsvtav1" and not av1_available:
        for fallback_name in FALLBACK_CHAIN:
            if fallback_name == preset_name:
                continue
            fb = ENCODING_PRESETS.get(fallback_name, {})
            if fb.get("codec") != "libsvtav1":
                if logger:
                    logger.warn(f"AV1 non disponible, fallback preset '{fallback_name}'")
                preset_name = fallback_name
                ep = fb
                break

    codec_map = {
        "libsvtav1": "av1",
        "libx265": "h265",
        "libx264": "h264",
        "prores_ks": "prores",
    }
    codec = codec_override or codec_map.get(ep.get("codec", ""), "h265")
    crf = crf_override if crf_override is not None else ep.get("crf", 20)

    return {"preset_name": preset_name, "codec": codec, "crf": crf}


def run_pipeline(
    components: Dict[str, List[Path]],
    plan: dict,
    output_dir: Path,
    project_name: str,
    drive_root: Path,
    rife_model_path: Optional[str],
    esrgan_model_path: Optional[str],
    use_gpu: bool,
    logger: CarrierLogger,
    args: argparse.Namespace,
) -> Tuple[bool, dict]:
    """Exécute le pipeline V2 frame-based."""
    from sequence_assembler import SequenceAssembler
    from audio_sync import AudioSync
    from rife_interpolator import RIFEInterpolator
    from upscaler import Upscaler
    from final_encoder import FinalEncoder

    schema = CarrierSchema()

    pipeline_result = {
        "stages": {},
        "files": {},
        "pipeline_version": "2.0.0",
        "frame_based": True,
    }

    temp_dir = output_dir / "_temp_carrier"
    temp_dir.mkdir(parents=True, exist_ok=True)
    final_frames_dir = temp_dir / "final_frames"
    final_frames_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / CHECKPOINT_FILENAME

    try:
        format_meta = parse_format_metadata(plan)
        source_fps = format_meta.get("fps_source", DEFAULT_SOURCE_FPS)
        target_width = format_meta.get("width", 3840)
        target_height = format_meta.get("height", 2160)
        expected_ratio = format_meta.get("ratio", "16:9")

        ok, msg = schema.validate_ratio(target_width, target_height, expected_ratio)
        if not ok:
            logger.warn(f"Ratio: {msg}")

        output_config = plan.get("output", {})
        target_fps = output_config.get("framerate", DEFAULT_TARGET_FPS)
        if args.no_rife:
            target_fps = source_fps

        logger.info("=" * 50)
        logger.info("STAGE 1: Frame Indexer")
        logger.info("=" * 50)

        indexer = SequenceAssembler(verbose=logger.verbose)
        assembly_kit_dir = components["sequences"][0].parent if components["sequences"] else Path(".")
        manifest = indexer.index_frames(assembly_kit_dir, plan)

        if manifest["total_frames"] == 0:
            logger.error("Aucune frame indexée")
            return False, pipeline_result

        pipeline_result["stages"]["index"] = {
            "status": "OK",
            "total_frames": manifest["total_frames"],
            "fps": manifest["fps"],
            "duration": manifest["duration_seconds"],
            "resolution": f"{manifest['resolution'][0]}x{manifest['resolution'][1]}",
        }
        logger.success(f"Indexé: {manifest['total_frames']} frames, {manifest['duration_seconds']:.1f}s @ {manifest['fps']}fps")

        source_fps = manifest["fps"] if manifest["fps"] > 0 else source_fps

        logger.info("=" * 50)
        logger.info("STAGE 2: Audio Prep")
        logger.info("=" * 50)

        audio_sync = AudioSync(verbose=logger.verbose)
        audio_output = temp_dir / "audio_mixed.wav"
        audio_ready = False

        if components["audio"]:
            success = audio_sync.mix_and_normalize(
                audio_tracks=components["audio"],
                output_path=audio_output,
                target_lufs=-14.0
            )
            if success:
                rife_params = calculate_rife_params(source_fps, target_fps)
                total_output_frames = manifest["total_frames"] * rife_params["multiplier"]
                synced_audio = temp_dir / "audio_synced.wav"
                if audio_sync.auto_sync_duration(audio_output, total_output_frames, target_fps, synced_audio):
                    audio_output = synced_audio
                audio_ready = True
                pipeline_result["stages"]["audio"] = {"status": "OK", "output": str(audio_output)}
                logger.success(f"Audio prêt: {audio_output}")
            else:
                logger.warn("Mix audio échoué, vidéo sera muette")
        else:
            logger.info("Pas d'audio à traiter")

        logger.info("=" * 50)
        logger.info("STAGE 3: Chunk Pipeline (Frame-Based)")
        logger.info("=" * 50)

        rife_params = calculate_rife_params(source_fps, target_fps)
        multiplier = rife_params["multiplier"]
        logger.info(f"RIFE: {source_fps}fps -> {target_fps}fps (x{multiplier})")

        all_source_frames = []
        for seq in manifest["sequences"]:
            all_source_frames.extend(seq["files"])

        chunk_size = RIFE_CHUNK_SECONDS * source_fps
        total_chunks = math.ceil(len(all_source_frames) / chunk_size) if chunk_size > 0 else 1

        rife = RIFEInterpolator(
            model_path=rife_model_path,
            use_gpu=use_gpu,
            verbose=logger.verbose
        )

        upscaler = Upscaler(
            model_path=esrgan_model_path,
            use_gpu=use_gpu,
            verbose=logger.verbose
        )

        source_w = manifest["resolution"][0]
        source_h = manifest["resolution"][1]
        needs_upscale = (not args.no_upscale and
                         (source_w < target_width or source_h < target_height))

        start_chunk = load_checkpoint(checkpoint_path) if args.resume else 0
        if start_chunk > 0:
            logger.info(f"Reprise depuis checkpoint: chunk {start_chunk}/{total_chunks}")

        global_frame_idx = 0
        if start_chunk > 0:
            for c in range(start_chunk):
                chunk_start = c * chunk_size
                chunk_end = min((c + 1) * chunk_size, len(all_source_frames))
                chunk_len = chunk_end - chunk_start
                global_frame_idx += chunk_len * multiplier

        for chunk_idx in range(start_chunk, total_chunks):
            chunk_start = chunk_idx * chunk_size
            chunk_end = min((chunk_idx + 1) * chunk_size, len(all_source_frames))
            chunk_frames = all_source_frames[chunk_start:chunk_end]

            if not chunk_frames:
                continue

            logger.info(f"--- Chunk {chunk_idx + 1}/{total_chunks} ({len(chunk_frames)} frames source) ---")

            if not args.no_rife and multiplier > 1:
                rife_output_dir = temp_dir / f"rife_chunk_{chunk_idx:04d}"
                interpolated = rife.interpolate_chunk(
                    chunk_frames, rife_output_dir, target_fps, source_fps
                )
                if not interpolated:
                    logger.error(f"RIFE chunk {chunk_idx} échoué")
                    return False, pipeline_result
            else:
                interpolated = chunk_frames

            if needs_upscale:
                upscale_output_dir = temp_dir / f"upscale_chunk_{chunk_idx:04d}"
                final_chunk_frames = upscaler.upscale_chunk(
                    interpolated, upscale_output_dir, target_width, target_height
                )
                if not final_chunk_frames:
                    logger.error(f"Upscale chunk {chunk_idx} échoué")
                    return False, pipeline_result
            else:
                final_chunk_frames = interpolated

            # Déterminer si les frames sont des intermédiaires ou des originaux
            frames_are_intermediate = (not args.no_rife and multiplier > 1) or needs_upscale

            for i, frame in enumerate(final_chunk_frames):
                dest = final_frames_dir / f"frame_{global_frame_idx:08d}.png"
                if frames_are_intermediate:
                    shutil.move(str(frame), str(dest))
                else:
                    shutil.copy2(str(frame), str(dest))
                global_frame_idx += 1

            rife_output_dir_path = temp_dir / f"rife_chunk_{chunk_idx:04d}"
            if rife_output_dir_path.exists():
                shutil.rmtree(rife_output_dir_path, ignore_errors=True)
            if needs_upscale:
                upscale_dir_path = temp_dir / f"upscale_chunk_{chunk_idx:04d}"
                if upscale_dir_path.exists():
                    shutil.rmtree(upscale_dir_path, ignore_errors=True)

            save_checkpoint(checkpoint_path, chunk_idx + 1, {
                "global_frame_idx": global_frame_idx,
                "total_chunks": total_chunks,
            })

            progress = (chunk_idx + 1) / total_chunks * 100
            logger.info(f"Chunk {chunk_idx + 1}/{total_chunks} ({progress:.0f}%) — {global_frame_idx} frames accumulées")

        pipeline_result["stages"]["chunks"] = {
            "status": "OK",
            "total_chunks": total_chunks,
            "total_output_frames": global_frame_idx,
            "rife": "enabled" if not args.no_rife else "disabled",
            "upscale": "enabled" if needs_upscale else "disabled",
        }
        logger.success(f"Chunks complétés: {global_frame_idx} frames finales")

        logger.info("=" * 50)
        logger.info("STAGE 4: Final Encode (SEULE compression lossy)")
        logger.info("=" * 50)

        av1_ok = check_av1_available(logger)
        preset_info = resolve_preset(
            args.preset, args.crf, args.codec,
            av1_available=av1_ok, logger=logger
        )
        logger.info(f"Encodage: preset={preset_info['preset_name']}, codec={preset_info['codec']}, crf={preset_info['crf']}")

        encoder = FinalEncoder(verbose=logger.verbose)

        final_mp4 = output_dir / f"FINAL_OUTPUT_{project_name}.mp4"
        container = ENCODING_PRESETS.get(preset_info["preset_name"], {}).get("container", ".mp4")
        if container == ".mov":
            final_mp4 = output_dir / f"FINAL_OUTPUT_{project_name}.mov"

        success = encoder.encode_from_frames(
            frames_dir=final_frames_dir,
            frame_pattern="frame_%08d.png",
            audio_input=audio_output if audio_ready else None,
            output_path=final_mp4,
            fps=target_fps,
            codec=preset_info["codec"],
            crf=preset_info["crf"],
            preset_name=preset_info["preset_name"] if preset_info["preset_name"] != "custom" else None,
        )

        if not success:
            logger.error("Encodage final échoué")
            return False, pipeline_result

        pipeline_result["stages"]["encode"] = {
            "status": "OK",
            "output": str(final_mp4),
            "preset": preset_info["preset_name"],
            "codec": preset_info["codec"],
            "crf": preset_info["crf"],
        }
        pipeline_result["files"]["primary"] = str(final_mp4)
        logger.success(f"Encodé: {final_mp4}")

        video_info = encoder.get_video_info(final_mp4)
        if video_info:
            actual_duration = video_info.get("duration", 0)
            ok, msg = schema.validate_output_weight(
                final_mp4.stat().st_size, actual_duration, preset_info["preset_name"]
            )
            if not ok:
                logger.warn(f"Poids fichier: {msg}")
            else:
                logger.debug(f"Poids fichier OK")

            ok2, msg2 = schema.checksum_resolution(
                video_info.get("width", 0), video_info.get("height", 0),
                target_width, target_height
            )
            if not ok2:
                logger.warn(f"Résolution: {msg2}")

        if preset_info["codec"] != "prores":
            final_mov = output_dir / f"FINAL_OUTPUT_{project_name}.mov"
            mov_success = encoder.encode_from_frames(
                frames_dir=final_frames_dir,
                frame_pattern="frame_%08d.png",
                audio_input=audio_output if audio_ready else None,
                output_path=final_mov,
                fps=target_fps,
                codec="prores",
                preset_name="master",
            )
            if mov_success:
                pipeline_result["stages"]["encode_prores"] = {"status": "OK", "output": str(final_mov)}
                pipeline_result["files"]["mov"] = str(final_mov)
                logger.success(f"ProRes MOV: {final_mov}")
            else:
                logger.warn("Encodage ProRes échoué (non bloquant)")

        logger.info("=" * 50)
        logger.info("STAGE 5: Thumbnail + Report")
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

        # Cleanup checkpoint on success
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.debug("Checkpoint supprimé (pipeline terminé avec succès)")

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
        "pipeline_version": pipeline_result.get("pipeline_version", "2.0.0"),
        "frame_based": pipeline_result.get("frame_based", True),
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
        description=f'AIRCRAFT CARRIER - EXODUS v{CARRIER_VERSION} (Frame-Based Pipeline)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_06_CARRIER.py --drive-root /path/to/drive --project-name "MyProject"

  python EXO_06_CARRIER.py --drive-root /path/to/drive \\
    --project-name "MyVideo" --preset distribution -v

  python EXO_06_CARRIER.py --drive-root /path/to/drive \\
    --project-name "MyVideo" --preset custom --codec h265 --crf 20

  python EXO_06_CARRIER.py --drive-root /path/to/drive \\
    --project-name "MyVideo" --resume
        """
    )

    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive EXODUS')
    parser.add_argument('--assembly-kit-dir',
                        help='Dossier des composants (défaut: IN_ASSEMBLY_KIT/)')
    parser.add_argument('--output-dir',
                        help='Dossier output (défaut: OUT_FINAL_MOVIE/)')
    parser.add_argument('--production-plan',
                        help='PRODUCTION_PLAN.JSON (défaut: IN_ASSEMBLY_KIT/PRODUCTION_PLAN.JSON)')
    parser.add_argument('--project-name', default='EXODUS_OUTPUT',
                        help='Nom du projet pour les fichiers output')
    parser.add_argument('--preset', choices=['distribution', 'distribution_h265', 'master', 'custom'],
                        default='distribution', help="Preset d'encodage")
    parser.add_argument('--crf', type=int, default=None,
                        help='CRF custom (override preset)')
    parser.add_argument('--codec', choices=['av1', 'h265', 'h264', 'prores'],
                        default=None, help='Codec custom (override preset)')
    parser.add_argument('--resume', action='store_true',
                        help='Reprendre depuis le dernier checkpoint')
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
    print("   FREGATE 06_AIRCRAFT_CARRIER — EXODUS FINAL ASSEMBLY V2")
    print(f"   Version {CARRIER_VERSION} — Pipeline Frame-Based")
    print("=" * 70)

    drive_root = Path(args.drive_root)
    unit_root = drive_root / "06_AIRCRAFT_CARRIER"

    if args.assembly_kit_dir:
        assembly_kit_dir = Path(args.assembly_kit_dir)
    else:
        assembly_kit_dir = resolve_input(unit_root / "IN_ASSEMBLY_KIT")

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_FINAL_MOVIE"

    if args.production_plan:
        plan_path = Path(args.production_plan)
    else:
        plan_path = assembly_kit_dir / "PRODUCTION_PLAN.JSON"

    logger.info(f"Drive Root: {drive_root}")
    logger.info(f"Assembly Kit: {assembly_kit_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Project: {args.project_name}")
    logger.info(f"Preset: {args.preset}")

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
    components = validate_components(assembly_kit_dir, plan, logger)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.success("Configuration validée")

    if args.dry_run:
        logger.info("Mode dry-run: arrêt avant traitement")
        print("\nTous les chemins sont valides. Prêt pour l'assemblage final.")

        print("\n=== Résumé ===")
        print(f"  Séquences: {len(components['sequences'])} images")
        print(f"  Audio: {len(components['audio'])} pistes")
        print(f"  Preset: {args.preset}")
        print(f"  GPU: {'Oui' if use_gpu else 'Non'}")
        print(f"  RIFE: {'Oui' if rife_model_path else 'Non (FFmpeg fallback)'}")
        print(f"  Resume: {'Oui' if args.resume else 'Non'}")
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
        logger=logger,
        args=args,
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
        logger.error("ASSEMBLAGE ECHOUE")
        sys.exit(1)

    print("\n" + "=" * 70)
    logger.success("ASSEMBLAGE FINAL COMPLET (Pipeline V2 Frame-Based)")
    for file_type, file_path in pipeline_result.get("files", {}).items():
        print(f"  {file_type.upper()}: {file_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
