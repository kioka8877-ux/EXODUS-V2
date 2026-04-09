#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DARKROOM RENDER — EXODUS PHOTOGRAPHY                      ║
║          Chunk-based Blender Batch Rendering (Headless CLI)                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Rendu 1080p @ 128 samples + OIDN — U06 AI upscale → 4K                    ║
║  Chunks de 300 frames + checkpoint JSON pour reprise après timeout          ║
║  ATOM-IC : Transmutation 1080p → 4K via Real-ESRGAN (U06)                  ║
║                                                                              ║
║  FIX #3 — VULKAN_FORGE 2026-04-09                                           ║
║  - Lecture camera_fov_ratio.json (aspect_ratio + fov_deg + lens_mm)        ║
║  - Résolution 9:16 (1080x1920) appliquée si aspect_ratio ≈ 0.5625          ║
║  - Lens mm injectée dans la caméra active Blender                          ║
║  - Log [U04] explicite + fallback 16:9 WARNING si JSON absent              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage (appelé par EXO_04_DARKROOM.py ou directement) :
    blender --background scene_ready_1.blend --python darkroom_render.py -- \
        --output-dir /path/to/OUT_CAMERA_LOGIC \
        --chunk-size 300 \
        --preset darkroom \
        --resume
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[DARKROOM] Blender non disponible — mode standalone")

sys.path.insert(0, str(Path(__file__).parent))
from camera_schema import RENDER_PRESETS, TARGET_FPS

VERSION = "1.1.0"  # FIX #3 — camera_fov_ratio.json + 9:16
CHECKPOINT_FILENAME = "darkroom_checkpoint.json"

# Tolérance pour comparer aspect_ratio
_PORTRAIT_916_RATIO = 9.0 / 16.0   # 0.5625
_LANDSCAPE_169_RATIO = 16.0 / 9.0  # 1.7778
_RATIO_TOLERANCE = 0.02


def log(msg: str) -> None:
    print(f"[DARKROOM] {msg}")


def debug(msg: str, verbose: bool = False) -> None:
    if verbose:
        print(f"[DARKROOM:DEBUG] {msg}")


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]

    parser = argparse.ArgumentParser(
        description="DARKROOM RENDER — Chunk-based Blender batch rendering"
    )
    parser.add_argument(
        "--output-dir", required=True, type=str,
        help="Dossier de sortie pour les frames PNG",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=300,
        help="Nombre de frames par chunk (default: 300)",
    )
    parser.add_argument(
        "--preset", type=str, default="darkroom",
        help="Preset de rendu depuis camera_schema.RENDER_PRESETS (default: darkroom)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Reprendre depuis le dernier checkpoint",
    )
    parser.add_argument(
        "--start-frame", type=int, default=None,
        help="Override du frame de début",
    )
    parser.add_argument(
        "--end-frame", type=int, default=None,
        help="Override du frame de fin",
    )
    parser.add_argument(
        "--camera-fov-json", type=str, default=None,
        help="Chemin vers camera_fov_ratio.json (U00) pour override résolution 9:16",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Logs détaillés",
    )
    return parser.parse_args(argv)


def apply_render_settings(preset_name: str, verbose: bool = False) -> dict:
    if preset_name not in RENDER_PRESETS:
        raise ValueError(
            f"Preset inconnu : '{preset_name}'. Valides : {list(RENDER_PRESETS.keys())}"
        )
    preset = RENDER_PRESETS[preset_name]
    log(f"Application preset : {preset_name}")

    if not BLENDER_AVAILABLE:
        log("Blender indisponible — preset simulé")
        return preset

    scene = bpy.context.scene

    scene.render.engine = "CYCLES"
    scene.cycles.samples = preset["samples"]
    scene.cycles.use_adaptive_sampling = preset["use_adaptive_sampling"]
    scene.cycles.adaptive_threshold = preset["adaptive_threshold"]
    scene.cycles.use_denoising = preset["use_denoising"]
    scene.cycles.denoiser = preset["denoiser"]

    scene.render.resolution_x = preset["resolution"][0]
    scene.render.resolution_y = preset["resolution"][1]
    scene.render.resolution_percentage = 100
    scene.render.fps = TARGET_FPS

    scene.render.film_transparent = preset["film_transparent"]

    scene.render.image_settings.file_format = preset.get("output_format", "PNG")
    scene.render.image_settings.color_depth = preset.get("color_depth", "16")
    scene.render.image_settings.color_mode = "RGB"

    log(
        f"Preset '{preset_name}' appliqué : "
        f"{preset['resolution'][0]}x{preset['resolution'][1]} @ "
        f"{preset['samples']} samples, denoiser={preset['denoiser']}, "
        f"format={preset.get('output_format', 'PNG')} {preset.get('color_depth', '16')}-bit"
    )
    return preset


def override_resolution_from_fov_json(
    fov_json_path: str,
    verbose: bool = False,
) -> dict:
    """
    FIX #3 — Lit camera_fov_ratio.json (généré par U00) et applique :
      - Résolution Blender selon aspect_ratio (9:16 → 1080x1920)
      - Lens mm sur la caméra active
      - Log [U04] explicite

    Format JSON attendu (U00) :
      {
        "aspect_ratio": 0.5625,   // 9/16 pour portrait
        "fov_deg": 60.0,
        "lens_mm": 28.0
      }
    Format legacy supporté :
      { "resolution": [1080, 1920], ... }

    Returns:
        dict avec :
          - applied       : bool
          - res_x, res_y  : int
          - aspect_ratio_applied : str (ex: "9:16")
          - fov_deg       : float | None
          - lens_mm       : float | None
    """
    result = {
        "applied": False,
        "res_x": 1920,
        "res_y": 1080,
        "aspect_ratio_applied": "16:9",
        "fov_deg": None,
        "lens_mm": None,
    }

    fov_path = Path(fov_json_path)
    if not fov_path.exists():
        log(f"[U04] WARNING — camera_fov_ratio.json introuvable : {fov_path}")
        log("[U04] Fallback résolution : 16:9 (1920x1080)")
        return result

    try:
        with open(fov_path, "r", encoding="utf-8") as f:
            fov_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"[U04] WARNING — Erreur lecture camera_fov_ratio.json : {e}")
        log("[U04] Fallback résolution : 16:9 (1920x1080)")
        return result

    # ── Résolution : format U00 (aspect_ratio) ou format legacy (resolution list) ──
    res_x, res_y = 1920, 1080
    aspect_ratio_applied = "16:9"
    aspect_ratio_val = None

    if "aspect_ratio" in fov_data:
        aspect_ratio_val = float(fov_data["aspect_ratio"])
        ratio_diff_916 = abs(aspect_ratio_val - _PORTRAIT_916_RATIO)
        ratio_diff_169 = abs(aspect_ratio_val - _LANDSCAPE_169_RATIO)

        if ratio_diff_916 < _RATIO_TOLERANCE:
            res_x, res_y = 1080, 1920
            aspect_ratio_applied = "9:16"
        elif ratio_diff_169 < _RATIO_TOLERANCE:
            res_x, res_y = 1920, 1080
            aspect_ratio_applied = "16:9"
        else:
            # Ratio personnalisé — calcul dynamique base 1080p
            if aspect_ratio_val < 1.0:
                res_x = 1080
                res_y = round(1080 / aspect_ratio_val)
                aspect_ratio_applied = f"{res_x}:{res_y}"
            else:
                res_y = 1080
                res_x = round(1080 * aspect_ratio_val)
                aspect_ratio_applied = f"{res_x}:{res_y}"

    elif "resolution" in fov_data:
        # Format legacy : [width, height]
        res_list = fov_data["resolution"]
        if isinstance(res_list, list) and len(res_list) == 2:
            res_x, res_y = int(res_list[0]), int(res_list[1])
            if res_x < res_y:
                aspect_ratio_applied = "9:16"
            elif res_x > res_y:
                aspect_ratio_applied = "16:9"
            else:
                aspect_ratio_applied = "1:1"
    else:
        log("[U04] WARNING — camera_fov_ratio.json sans 'aspect_ratio' ni 'resolution'")
        log("[U04] Fallback résolution : 16:9 (1920x1080)")
        return result

    # ── FOV / Lens ────────────────────────────────────────────────────────────
    fov_deg = fov_data.get("fov_deg") or fov_data.get("estimated_fov_degrees")
    lens_mm = fov_data.get("lens_mm") or fov_data.get("focal_length_mm")

    if fov_deg is not None:
        fov_deg = float(fov_deg)
    if lens_mm is not None:
        lens_mm = float(lens_mm)

    # ── Application Blender ───────────────────────────────────────────────────
    if BLENDER_AVAILABLE:
        scene = bpy.context.scene
        scene.render.resolution_x = res_x
        scene.render.resolution_y = res_y
        scene.render.resolution_percentage = 100

        if lens_mm is not None and scene.camera is not None:
            scene.camera.data.lens = lens_mm
            debug(f"[U04] Lens injectée sur camera '{scene.camera.name}' : {lens_mm}mm", verbose)
        elif lens_mm is not None:
            log("[U04] WARNING — Aucune caméra active, lens_mm non appliquée")

    # ── Log [U04] ─────────────────────────────────────────────────────────────
    fov_str  = f"{fov_deg:.1f}°" if fov_deg is not None else "N/A"
    lens_str = f"{lens_mm:.1f}mm" if lens_mm is not None else "N/A"
    log(f"[U04] Ratio appliqué : {aspect_ratio_applied} ({res_x}x{res_y}) "
        f"| FOV: {fov_str} | Lens: {lens_str}")

    result.update({
        "applied": True,
        "res_x": res_x,
        "res_y": res_y,
        "aspect_ratio_applied": aspect_ratio_applied,
        "fov_deg": fov_deg,
        "lens_mm": lens_mm,
    })
    return result


def set_gpu_if_available(verbose: bool = False) -> str:
    if not BLENDER_AVAILABLE:
        log("Blender indisponible — GPU config simulée (CPU)")
        return "CPU"

    scene = bpy.context.scene

    for compute_type in ("CUDA", "OPTIX"):
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = compute_type
            prefs.get_devices()
            for device in prefs.devices:
                device.use = True
            scene.cycles.device = "GPU"
            log(f"GPU activé : {compute_type}")
            debug(f"Devices : {[d.name for d in prefs.devices]}", verbose)
            return compute_type
        except Exception:
            debug(f"{compute_type} indisponible, tentative suivante...", verbose)
            continue

    scene.cycles.device = "CPU"
    log("Aucun GPU détecté — fallback CPU")
    return "CPU"


def load_checkpoint(checkpoint_path: Path) -> dict | None:
    if not checkpoint_path.exists():
        return None
    try:
        with open(checkpoint_path, "r") as f:
            data = json.load(f)
        log(f"Checkpoint trouvé : frame {data['next_frame']}/{data['total_frames']} "
            f"({data['frames_rendered']} rendues)")
        return data
    except (json.JSONDecodeError, KeyError) as e:
        log(f"Checkpoint corrompu ({e}) — redémarrage complet")
        return None


def save_checkpoint(
    checkpoint_path: Path,
    blend_file: str,
    preset: str,
    next_frame: int,
    total_frames: int,
    chunk_size: int,
    frames_rendered: int,
    elapsed_seconds: float,
) -> None:
    data = {
        "version": VERSION,
        "blend_file": blend_file,
        "preset": preset,
        "next_frame": next_frame,
        "total_frames": total_frames,
        "chunk_size": chunk_size,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frames_rendered": frames_rendered,
        "elapsed_seconds": round(elapsed_seconds, 2),
    }
    with open(checkpoint_path, "w") as f:
        json.dump(data, f, indent=2)
    debug(f"Checkpoint sauvegardé : frame {next_frame}", True)


def get_vram_info() -> str:
    if not BLENDER_AVAILABLE:
        return "N/A (standalone)"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for device in prefs.devices:
            if device.use and device.type != "CPU":
                return f"{device.name}"
        return "CPU only"
    except Exception:
        return "N/A"


def render_chunks(args: argparse.Namespace) -> dict:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    preset = apply_render_settings(args.preset, args.verbose)

    # ── FIX #3 : Override résolution depuis camera_fov_ratio.json (U00) ──────
    fov_override = {
        "applied": False,
        "res_x": preset["resolution"][0],
        "res_y": preset["resolution"][1],
        "aspect_ratio_applied": "16:9",
        "fov_deg": None,
        "lens_mm": None,
    }
    if args.camera_fov_json:
        fov_override = override_resolution_from_fov_json(
            args.camera_fov_json, args.verbose
        )
    else:
        log("[U04] WARNING — --camera-fov-json non fourni, résolution preset conservée (16:9)")
    # ─────────────────────────────────────────────────────────────────────────

    device_type = set_gpu_if_available(args.verbose)

    if BLENDER_AVAILABLE:
        scene = bpy.context.scene
        blend_file = bpy.data.filepath or "unknown.blend"
        frame_start = args.start_frame if args.start_frame is not None else scene.frame_start
        frame_end = args.end_frame if args.end_frame is not None else scene.frame_end
    else:
        blend_file = "simulated.blend"
        frame_start = args.start_frame if args.start_frame is not None else 1
        frame_end = args.end_frame if args.end_frame is not None else 1800

    total_frames = frame_end - frame_start + 1
    chunk_size = args.chunk_size
    total_chunks = (total_frames + chunk_size - 1) // chunk_size

    # Résolution effective après override
    eff_res_x = fov_override["res_x"]
    eff_res_y = fov_override["res_y"]

    checkpoint_path = output_dir / CHECKPOINT_FILENAME
    start_frame = frame_start
    frames_already_rendered = 0
    elapsed_prior = 0.0

    if args.resume:
        ckpt = load_checkpoint(checkpoint_path)
        if ckpt:
            start_frame = ckpt["next_frame"]
            frames_already_rendered = ckpt["frames_rendered"]
            elapsed_prior = ckpt.get("elapsed_seconds", 0.0)
            if start_frame > frame_end:
                log("Toutes les frames déjà rendues selon checkpoint")
                return {
                    "status": "ALREADY_COMPLETE",
                    "total_frames": total_frames,
                    "frames_rendered": frames_already_rendered,
                    "aspect_ratio_applied": fov_override["aspect_ratio_applied"],
                }
        else:
            log("Pas de checkpoint trouvé — démarrage depuis le début")

    log("=" * 60)
    log("DARKROOM RENDER — PLAN")
    log(f"  Blend       : {Path(blend_file).name}")
    log(f"  Preset      : {args.preset}")
    log(f"  Resolution  : {eff_res_x}x{eff_res_y} ({fov_override['aspect_ratio_applied']})")
    log(f"  Samples     : {preset['samples']}")
    log(f"  Denoiser    : {preset['denoiser']}")
    log(f"  Device      : {device_type} ({get_vram_info()})")
    log(f"  Frame range : {frame_start}–{frame_end} ({total_frames} frames)")
    log(f"  Start frame : {start_frame} (resume={args.resume})")
    log(f"  Chunk size  : {chunk_size}")
    log(f"  Chunks      : {total_chunks}")
    log(f"  Output      : {output_dir}")
    log(f"  Naming      : render_XXXXXXXX.png (PNG 16-bit)")
    log("=" * 60)

    if not BLENDER_AVAILABLE:
        log("MODE STANDALONE — Simulation du plan de rendu")
        est_seconds_per_frame = 5.0
        est_total = est_seconds_per_frame * (frame_end - start_frame + 1)
        log(f"  Temps estimé : {est_total / 3600:.1f}h ({est_seconds_per_frame:.1f}s/frame)")
        est_size_mb = total_frames * 6.0
        log(f"  Taille estimée : {est_size_mb / 1024:.1f} GB ({est_size_mb / total_frames:.1f} MB/frame)")
        return {
            "status": "SIMULATED",
            "blend_file": blend_file,
            "preset": args.preset,
            "total_frames": total_frames,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "device": device_type,
            "estimated_hours": round(est_total / 3600, 1),
            "estimated_size_gb": round(est_size_mb / 1024, 1),
            "aspect_ratio_applied": fov_override["aspect_ratio_applied"],
        }

    scene = bpy.context.scene
    frames_rendered = frames_already_rendered
    t_global_start = time.time() - elapsed_prior
    chunk_idx = 0

    for chunk_start in range(start_frame, frame_end + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, frame_end)
        chunk_idx += 1
        chunk_frames = chunk_end - chunk_start + 1
        t_chunk_start = time.time()

        log(f"--- Chunk {chunk_idx}/{total_chunks} : frames {chunk_start}–{chunk_end} ({chunk_frames} frames) ---")

        for frame_num in range(chunk_start, chunk_end + 1):
            t_frame_start = time.time()
            scene.frame_set(frame_num)
            filepath = output_dir / f"render_{frame_num:08d}.png"
            scene.render.filepath = str(filepath)
            bpy.ops.render.render(write_still=True)
            frames_rendered += 1

            t_frame_elapsed = time.time() - t_frame_start
            t_total_elapsed = time.time() - t_global_start
            remaining_frames = total_frames - frames_rendered
            avg_spf = t_total_elapsed / frames_rendered if frames_rendered > 0 else 0
            eta_seconds = avg_spf * remaining_frames

            if args.verbose or frame_num % 10 == 0:
                log(
                    f"  Frame {frame_num:>8d} | "
                    f"{t_frame_elapsed:.1f}s | "
                    f"{frames_rendered}/{total_frames} | "
                    f"avg {avg_spf:.1f}s/f | "
                    f"ETA {eta_seconds / 60:.0f}min"
                )

        t_chunk_elapsed = time.time() - t_chunk_start
        t_total_elapsed = time.time() - t_global_start
        log(
            f"Chunk {chunk_idx}/{total_chunks} terminé — "
            f"{frames_rendered}/{total_frames} frames — "
            f"{t_chunk_elapsed:.0f}s chunk / {t_total_elapsed / 60:.1f}min total"
        )

        save_checkpoint(
            checkpoint_path=checkpoint_path,
            blend_file=Path(blend_file).name,
            preset=args.preset,
            next_frame=chunk_end + 1,
            total_frames=total_frames,
            chunk_size=chunk_size,
            frames_rendered=frames_rendered,
            elapsed_seconds=t_total_elapsed,
        )

    t_total = time.time() - t_global_start
    avg_spf = t_total / frames_rendered if frames_rendered > 0 else 0

    if checkpoint_path.exists():
        checkpoint_path.unlink()
        log("Checkpoint supprimé — rendu complet")

    log("=" * 60)
    log("DARKROOM RENDER — TERMINÉ")
    log(f"  Frames      : {frames_rendered}/{total_frames}")
    log(f"  Resolution  : {eff_res_x}x{eff_res_y} ({fov_override['aspect_ratio_applied']})")
    log(f"  Temps total : {t_total / 60:.1f} min ({t_total / 3600:.2f}h)")
    log(f"  Moyenne     : {avg_spf:.1f}s/frame")
    log(f"  Output      : {output_dir}")
    log("=" * 60)

    return {
        "status": "SUCCESS",
        "blend_file": Path(blend_file).name,
        "preset": args.preset,
        "total_frames": total_frames,
        "frames_rendered": frames_rendered,
        "elapsed_seconds": round(t_total, 2),
        "avg_seconds_per_frame": round(avg_spf, 2),
        "device": device_type,
        "output_dir": str(output_dir),
        # ── FIX #3 : champs aspect ratio ──────────────────────────────────────
        "aspect_ratio_applied": fov_override["aspect_ratio_applied"],
        "resolution_applied": f"{eff_res_x}x{eff_res_y}",
        "fov_deg_applied": fov_override["fov_deg"],
        "lens_mm_applied": fov_override["lens_mm"],
        # ─────────────────────────────────────────────────────────────────────
    }


if __name__ == "__main__":
    args = parse_args()
    result = render_chunks(args)
    log(f"Résultat : {json.dumps(result, indent=2)}")
