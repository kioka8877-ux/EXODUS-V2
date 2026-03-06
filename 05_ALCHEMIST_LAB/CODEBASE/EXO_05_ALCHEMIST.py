#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             FRÉGATE 05_ALCHEMIST — EXODUS VISUAL FUSION PIPELINE             ║
║         Match Color • Grain • Bloom • Sharpness (OpenCV CPU pur)            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 2.0.0                                                              ║
║  Mission: Fusion visuelle rendu/source pour atteindre le look cinéma 4K    ║
║  Stack: OpenCV + Pillow + numpy (CPU pur — zéro Blender, zéro GPU)         ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.

INPUTS REQUIS:
    - IN_RAW_FRAMES/ : Séquences rendues (EXR/PNG/TIFF de U04)
    - PRODUCTION_PLAN.JSON : Scènes, timecodes, paramètres
    - Source vidéo (.mp4/.avi/.mov) : Référence visuelle

OUTPUTS:
    - OUT_FINAL_FRAMES/ : Frames fusionnées PNG 16-bit
    - alchemist_report.json : Rapport de production
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

ALCHEMIST_VERSION = "2.0.0"

_CODEBASE_DIR = Path(__file__).parent
sys.path.insert(0, str(_CODEBASE_DIR))

from alchemist_schema import (
    AlchemistSchema,
    OUTPUT_COMPRESSION,
    OUTPUT_DEPTH,
    OUTPUT_FORMAT,
    PIPELINE_ORDER,
    SUPPORTED_INPUT_FORMATS,
    SUPPORTED_VIDEO_FORMATS,
)
from bloom_engine import BloomEngine
from sharpness_transfer import SharpnessTransfer

try:
    from match_color import ColorMatcher
    HAS_MATCH_COLOR = True
except ImportError:
    HAS_MATCH_COLOR = False

try:
    from grain_matcher import GrainMatcher
    HAS_GRAIN_MATCHER = True
except ImportError:
    HAS_GRAIN_MATCHER = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class AlchemistLogger:
    """Logger structuré pour ALCHEMIST LAB."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs: list = []

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


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION & HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_production_plan(plan_path: Path, logger: AlchemistLogger) -> dict:
    """Charge et valide le PRODUCTION_PLAN.JSON."""
    if not plan_path.exists():
        logger.error(f"PRODUCTION_PLAN.JSON introuvable: {plan_path}")
        sys.exit(1)

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide dans {plan_path}: {e}")
        sys.exit(1)

    if "scenes" not in plan:
        logger.warn("Aucune scène trouvée dans le plan, création structure vide")
        plan["scenes"] = []

    logger.success(f"Plan validé: {len(plan['scenes'])} scènes")
    return plan


def scan_render_frames(render_dir: Path, logger: AlchemistLogger, scene_id: int = None) -> Dict[int, List[Path]]:
    """Scanne render_dir pour trouver les frames par scène."""
    sequences: Dict[int, List[Path]] = {}

    if not render_dir.exists():
        logger.warn(f"Dossier render introuvable: {render_dir}")
        return sequences

    all_files = sorted(render_dir.iterdir())
    for f in all_files:
        if f.suffix.lower() not in SUPPORTED_INPUT_FORMATS:
            continue

        name = f.stem.lower()
        sid = 1
        if "_scene_" in name:
            try:
                parts = name.split("_scene_")
                sid = int(parts[1].split("_")[0])
            except (ValueError, IndexError):
                pass
        elif "scene" in name:
            try:
                idx = name.index("scene")
                num_str = ""
                for c in name[idx + 5:]:
                    if c.isdigit():
                        num_str += c
                    elif num_str:
                        break
                if num_str:
                    sid = int(num_str)
            except (ValueError, IndexError):
                pass

        if scene_id is not None and sid != scene_id:
            continue

        sequences.setdefault(sid, []).append(f)

    for sid in sequences:
        sequences[sid] = sorted(sequences[sid])

    logger.info(f"Frames render trouvées: {sum(len(v) for v in sequences.values())} dans {len(sequences)} scène(s)")
    for sid, files in sorted(sequences.items()):
        logger.debug(f"  Scene {sid}: {len(files)} frames")

    return sequences


def open_source_video(video_path: Path, logger: AlchemistLogger) -> Optional[cv2.VideoCapture]:
    """Ouvre la vidéo source avec cv2.VideoCapture."""
    if video_path is None or not video_path.exists():
        return None

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.warn(f"Impossible d'ouvrir la vidéo source: {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logger.success(f"Vidéo source ouverte: {w}x{h} @ {fps:.1f}fps, {total} frames")
    return cap


def extract_source_frame(cap: cv2.VideoCapture, frame_idx: int, total_frames: int) -> Optional[np.ndarray]:
    """Extrait une frame de la vidéo source, avec clamp aux bornes."""
    clamped = max(0, min(frame_idx, total_frames - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, clamped)
    ret, frame = cap.read()
    if not ret:
        return None
    return frame


def extract_sample_frames(
    cap: cv2.VideoCapture,
    start_frame: int,
    end_frame: int,
    total_video_frames: int,
    count: int,
) -> List[np.ndarray]:
    """Extrait `count` frames uniformément réparties entre start et end."""
    if end_frame <= start_frame:
        end_frame = start_frame + 1
    count = min(count, end_frame - start_frame)
    if count <= 0:
        return []

    step = max(1, (end_frame - start_frame) // count)
    frames = []
    for i in range(count):
        idx = start_frame + i * step
        f = extract_source_frame(cap, idx, total_video_frames)
        if f is not None:
            frames.append(f)
    return frames


def resize_to_match(source: np.ndarray, target_shape: tuple) -> np.ndarray:
    """Redimensionne source pour matcher target_shape (h, w)."""
    th, tw = target_shape[:2]
    sh, sw = source.shape[:2]
    if sh == th and sw == tw:
        return source
    return cv2.resize(source, (tw, th), interpolation=cv2.INTER_LINEAR)


def get_scene_timecodes(scene: dict, fps_source: float) -> Tuple[int, int]:
    """Extrait start_frame et end_frame d'une scène du plan."""
    tc_start = scene.get("timecode_start", scene.get("frame_start", 0))
    tc_end = scene.get("timecode_end", scene.get("frame_end", 0))

    if isinstance(tc_start, str) and ":" in tc_start:
        parts = tc_start.split(":")
        seconds = sum(float(p) * (60 ** (len(parts) - 1 - i)) for i, p in enumerate(parts))
        tc_start = int(seconds * fps_source)
    if isinstance(tc_end, str) and ":" in tc_end:
        parts = tc_end.split(":")
        seconds = sum(float(p) * (60 ** (len(parts) - 1 - i)) for i, p in enumerate(parts))
        tc_end = int(seconds * fps_source)

    return int(tc_start), int(tc_end)


def save_frame(frame: np.ndarray, output_path: Path):
    """Sauvegarde une frame en PNG 16-bit."""
    if frame.dtype == np.float32 or frame.dtype == np.float64:
        frame = np.clip(frame, 0.0, 1.0)
        frame = (frame * 65535.0).astype(np.uint16)
    elif frame.dtype == np.uint8:
        frame = (frame.astype(np.uint16) * 257)

    cv2.imwrite(
        str(output_path),
        frame,
        [cv2.IMWRITE_PNG_COMPRESSION, OUTPUT_COMPRESSION],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_config(args, schema: AlchemistSchema) -> dict:
    """Résout la config pipeline depuis le preset + overrides CLI."""
    preset_name = args.preset
    valid, msg = schema.validate_pipeline_preset(preset_name)
    if not valid:
        print(f"[ALCHEMIST:ERROR] {msg}", file=sys.stderr)
        sys.exit(1)

    config = schema.get_pipeline_config(preset_name)

    if args.match_intensity is not None:
        config["match_color"]["intensity"] = schema.validate_intensity(
            "match_color", args.match_intensity
        )
    if args.grain_intensity is not None:
        config["grain"]["intensity"] = schema.validate_intensity(
            "grain", args.grain_intensity
        )
    if args.bloom_preset is not None:
        config["bloom"] = schema.get_bloom_config(args.bloom_preset)
    if args.sharpness_intensity is not None:
        config["sharpness"]["intensity"] = schema.validate_intensity(
            "sharpness", args.sharpness_intensity
        )

    return config


def process_pipeline(args, logger: AlchemistLogger):
    """Pipeline principal de fusion visuelle."""

    schema = AlchemistSchema()
    config = resolve_config(args, schema)

    drive_root = Path(args.drive_root)
    unit_root = drive_root / "05_ALCHEMIST_LAB"

    render_dir = Path(args.render_dir) if args.render_dir else unit_root / "IN_RAW_FRAMES"
    output_dir = Path(args.output_dir) if args.output_dir else unit_root / "OUT_FINAL_FRAMES"
    source_ref_dir = Path(args.source_ref_dir) if args.source_ref_dir else unit_root / "IN_SOURCE_REF"
    plan_path = Path(args.production_plan)

    logger.info(f"ALCHEMIST v{ALCHEMIST_VERSION} — Pipeline OpenCV CPU pur")
    logger.info(f"Preset: {args.preset}")
    logger.debug(f"drive_root   = {drive_root}")
    logger.debug(f"render_dir   = {render_dir}")
    logger.debug(f"output_dir   = {output_dir}")
    logger.debug(f"source_ref   = {source_ref_dir}")
    logger.debug(f"plan         = {plan_path}")

    plan = validate_production_plan(plan_path, logger)

    if not render_dir.exists():
        logger.error(f"Dossier render introuvable: {render_dir}")
        sys.exit(1)

    source_video_path = None
    if args.source_video:
        svp = Path(args.source_video)
        if svp.exists():
            source_video_path = svp
        else:
            logger.warn(f"Vidéo source introuvable: {svp}")

    skip_match = args.skip_match or not HAS_MATCH_COLOR
    skip_grain = args.skip_grain or not HAS_GRAIN_MATCHER
    skip_bloom = args.skip_bloom
    skip_sharpness = args.skip_sharpness

    if not HAS_MATCH_COLOR:
        logger.warn("Module match_color non disponible → match_color désactivé")
    if not HAS_GRAIN_MATCHER:
        logger.warn("Module grain_matcher non disponible → grain désactivé")
    if source_video_path is None:
        skip_match = True
        skip_grain = True
        skip_sharpness = True
        logger.warn("Pas de vidéo source → match_color, grain, sharpness désactivés")

    active_stages = []
    for stage in PIPELINE_ORDER:
        if stage == "match_color" and skip_match:
            continue
        if stage == "grain" and skip_grain:
            continue
        if stage == "bloom" and skip_bloom:
            continue
        if stage == "sharpness" and skip_sharpness:
            continue
        active_stages.append(stage)

    logger.info(f"Pipeline actif: {' → '.join(active_stages) if active_stages else '(passthrough)'}")

    scene_filter = args.scene
    sequences = scan_render_frames(render_dir, logger, scene_id=scene_filter)

    if not sequences:
        logger.error("Aucune frame render trouvée")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        logger.success("DRY-RUN — Validation complète, aucun traitement exécuté")
        _print_dry_run_summary(config, active_stages, sequences, logger)
        return

    bloom_engine = BloomEngine(verbose=args.verbose) if not skip_bloom else None
    sharpness_engine = SharpnessTransfer(verbose=args.verbose) if not skip_sharpness else None

    color_matcher = None
    grain_matcher = None
    if HAS_MATCH_COLOR and not skip_match:
        color_matcher = ColorMatcher(verbose=args.verbose)
    if HAS_GRAIN_MATCHER and not skip_grain:
        grain_matcher = GrainMatcher(verbose=args.verbose)

    cap = None
    total_video_frames = 0
    fps_source = 24.0
    if source_video_path is not None:
        cap = open_source_video(source_video_path, logger)
        if cap is not None:
            total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps_source = cap.get(cv2.CAP_PROP_FPS) or 24.0

    report = {
        "version": ALCHEMIST_VERSION,
        "timestamp": datetime.now().isoformat(),
        "preset": args.preset,
        "pipeline": active_stages,
        "scenes": [],
    }

    total_processed = 0
    total_errors = 0
    t_global_start = time.time()

    scenes_data = plan.get("scenes", [])
    if not scenes_data:
        scenes_data = [{"scene_id": sid} for sid in sorted(sequences.keys())]

    for scene in scenes_data:
        sid = scene.get("scene_id", 1)
        if scene_filter is not None and sid != scene_filter:
            continue
        if sid not in sequences:
            logger.warn(f"Scene {sid}: aucune frame render, skip")
            continue

        frames_list = sequences[sid]
        logger.info(f"Scene {sid}: {len(frames_list)} frames à traiter")

        start_frame, end_frame = get_scene_timecodes(scene, fps_source)
        if end_frame <= start_frame:
            end_frame = start_frame + len(frames_list)

        reference_cdfs = None
        grain_stats = None
        if cap is not None and color_matcher is not None and not skip_match:
            ref_samples = extract_sample_frames(
                cap, start_frame, end_frame, total_video_frames,
                config["match_color"].get("reference_sample_count", 20),
            )
            if ref_samples:
                reference_cdfs = color_matcher.compute_reference_histogram(ref_samples)
                logger.debug(f"  Reference histograms calculés depuis {len(ref_samples)} frames source")

        if cap is not None and grain_matcher is not None and not skip_grain:
            grain_samples = extract_sample_frames(
                cap, start_frame, end_frame, total_video_frames,
                config["grain"].get("calibration_samples", 10),
            )
            if grain_samples:
                grain_stats = grain_matcher.extract_grain_stats(grain_samples)
                logger.debug(f"  Grain stats extraits depuis {len(grain_samples)} frames source")

        scene_report = {
            "scene_id": sid,
            "frames_total": len(frames_list),
            "frames_processed": 0,
            "frames_failed": 0,
            "time_seconds": 0.0,
        }

        frame_iter = frames_list
        if HAS_TQDM:
            frame_iter = tqdm(frames_list, desc=f"  Scene {sid}", unit="frame", leave=True)

        t_scene_start = time.time()

        for frame_idx, render_path in enumerate(frame_iter):
            try:
                render = cv2.imread(
                    str(render_path),
                    cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH,
                )
                if render is None:
                    logger.warn(f"  Frame illisible: {render_path.name}")
                    scene_report["frames_failed"] += 1
                    total_errors += 1
                    continue

                source_f = None
                if cap is not None:
                    src_idx = start_frame + frame_idx
                    source_f = extract_source_frame(cap, src_idx, total_video_frames)
                    if source_f is not None:
                        source_f = resize_to_match(source_f, render.shape)

                current = render

                if "match_color" in active_stages and color_matcher is not None and reference_cdfs is not None:
                    current = color_matcher.match_frame(
                        current, reference_cdfs,
                        intensity=config["match_color"]["intensity"],
                    )

                if "grain" in active_stages and grain_matcher is not None and grain_stats is not None:
                    current = grain_matcher.apply_grain(
                        current, grain_stats,
                        intensity=config["grain"]["intensity"],
                    )

                if "bloom" in active_stages and bloom_engine is not None:
                    bloom_cfg = config["bloom"]
                    current = bloom_engine.apply_bloom(
                        current,
                        threshold=bloom_cfg["threshold"],
                        intensity=bloom_cfg["intensity"],
                        radius=bloom_cfg["radius"],
                    )

                if "sharpness" in active_stages and sharpness_engine is not None and source_f is not None:
                    current = sharpness_engine.transfer(
                        current, source_f,
                        intensity=config["sharpness"]["intensity"],
                    )

                out_name = f"final_{sid:03d}_{frame_idx:06d}.{OUTPUT_FORMAT}"
                save_frame(current, output_dir / out_name)

                scene_report["frames_processed"] += 1
                total_processed += 1

            except Exception as e:
                logger.error(f"  Frame {render_path.name}: {e}")
                scene_report["frames_failed"] += 1
                total_errors += 1

        scene_report["time_seconds"] = round(time.time() - t_scene_start, 2)
        report["scenes"].append(scene_report)

        fps_scene = scene_report["frames_processed"] / max(scene_report["time_seconds"], 0.001)
        logger.success(
            f"Scene {sid}: {scene_report['frames_processed']} traitées, "
            f"{scene_report['frames_failed']} erreurs, "
            f"{fps_scene:.1f} frames/s"
        )

    if cap is not None:
        cap.release()

    total_time = round(time.time() - t_global_start, 2)

    report["summary"] = {
        "scenes_total": len(report["scenes"]),
        "scenes_processed": sum(1 for s in report["scenes"] if s["frames_processed"] > 0),
        "total_frames_processed": total_processed,
        "total_frames_failed": total_errors,
        "total_time_seconds": total_time,
        "status": "SUCCESS" if total_errors == 0 else "PARTIAL",
    }

    report_path = output_dir / "alchemist_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.success(f"Rapport: {report_path}")

    print()
    print("═══════════════════════════════════════════════════")
    print(f"   ALCHEMIST v{ALCHEMIST_VERSION} — RÉSUMÉ")
    print("═══════════════════════════════════════════════════")
    print(f"   Frames traitées : {total_processed}")
    print(f"   Erreurs         : {total_errors}")
    print(f"   Temps total     : {total_time:.1f}s")
    if total_processed > 0:
        print(f"   Moyenne         : {total_time / total_processed:.2f}s/frame")
    print(f"   Output          : {output_dir}")
    print("═══════════════════════════════════════════════════")


def _print_dry_run_summary(config: dict, active_stages: list, sequences: dict, logger: AlchemistLogger):
    """Affiche un résumé détaillé en mode dry-run."""
    print()
    print("═══════════════════════════════════════════════════")
    print(f"   ALCHEMIST v{ALCHEMIST_VERSION} — DRY RUN")
    print("═══════════════════════════════════════════════════")
    print(f"   Pipeline : {' → '.join(active_stages) if active_stages else '(vide)'}")
    print(f"   Scènes   : {len(sequences)}")
    total = sum(len(v) for v in sequences.values())
    print(f"   Frames   : {total}")
    print()
    for stage in PIPELINE_ORDER:
        enabled = stage in active_stages
        marker = "✓" if enabled else "✗"
        if stage in config:
            params = config[stage]
            if isinstance(params, dict):
                detail = ", ".join(f"{k}={v}" for k, v in params.items() if k != "description")
            else:
                detail = str(params)
            print(f"   [{marker}] {stage:15s} → {detail}")
        else:
            print(f"   [{marker}] {stage}")
    print("═══════════════════════════════════════════════════")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="EXO_05_ALCHEMIST",
        description=(
            "EXODUS ALCHEMIST v2 — Pipeline de fusion visuelle OpenCV\n"
            "Fusionne les rendus 3D avec la vidéo source via match_color, grain, bloom, sharpness."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--drive-root", required=True,
        help="Racine du Drive EXODUS V2",
    )
    parser.add_argument(
        "--production-plan", required=True,
        help="Chemin vers PRODUCTION_PLAN.JSON",
    )
    parser.add_argument(
        "--source-video", default=None,
        help="Vidéo source de référence (.mp4/.avi/.mov)",
    )
    parser.add_argument(
        "--preset", default="cinema_fusion",
        help="Preset pipeline (cinema_fusion, subtle_blend, neon_blast, raw_match, full_nuke)",
    )

    parser.add_argument("--render-dir", default=None, help="Dossier frames render (défaut: IN_RAW_FRAMES)")
    parser.add_argument("--output-dir", default=None, help="Dossier output (défaut: OUT_FINAL_FRAMES)")
    parser.add_argument("--source-ref-dir", default=None, help="Dossier références source (défaut: IN_SOURCE_REF)")

    parser.add_argument("--scene", type=int, default=None, help="Traiter une seule scène (par ID)")

    parser.add_argument("--match-intensity", type=float, default=None, help="Override intensité match_color [0.0-1.0]")
    parser.add_argument("--grain-intensity", type=float, default=None, help="Override intensité grain [0.0-1.0]")
    parser.add_argument("--bloom-preset", default=None, help="Override bloom preset (cinema, subtle, neon, none)")
    parser.add_argument("--sharpness-intensity", type=float, default=None, help="Override intensité sharpness [0.0-1.0]")

    parser.add_argument("--skip-match", action="store_true", help="Désactiver match_color")
    parser.add_argument("--skip-grain", action="store_true", help="Désactiver grain")
    parser.add_argument("--skip-bloom", action="store_true", help="Désactiver bloom")
    parser.add_argument("--skip-sharpness", action="store_true", help="Désactiver sharpness")

    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbose")
    parser.add_argument("--dry-run", action="store_true", help="Valider sans traitement")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    logger = AlchemistLogger(verbose=args.verbose)

    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║             FRÉGATE 05_ALCHEMIST — VISUAL FUSION PIPELINE                    ║")
    print(f"║             Version {ALCHEMIST_VERSION}  •  OpenCV CPU pur                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()

    process_pipeline(args, logger)


if __name__ == "__main__":
    main()
