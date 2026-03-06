#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  EXO_04_DARKROOM — EXODUS PHOTOGRAPHY                        ║
║               Orchestrateur CLI — Rendu Batch ATOM-IC                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Lance darkroom_render.py dans Blender headless pour chaque scene_ready.    ║
║  Chunks de 300 frames + checkpoint JSON + auto-resume.                      ║
║  ATOM-IC : 1080p → U06 Real-ESRGAN → 4K                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python EXO_04_DARKROOM.py \
        --drive-root /path/to/DRIVE_EXODUS_V2 \
        --project-name MY_PROJECT \
        --chunk-size 300 \
        --preset darkroom \
        --resume -v

    python EXO_04_DARKROOM.py \
        --drive-root /path/to/DRIVE_EXODUS_V2 \
        --project-name MY_PROJECT \
        --dry-run -v
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from camera_schema import RENDER_PRESETS, TARGET_FPS

VERSION = "1.0.0"
DARKROOM_SCRIPT = Path(__file__).parent / "darkroom_render.py"


def log(msg: str) -> None:
    print(f"[EXO_04_DARKROOM] {msg}")


def debug(msg: str, verbose: bool = False) -> None:
    if verbose:
        print(f"[EXO_04_DARKROOM:DEBUG] {msg}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EXO_04_DARKROOM — Orchestrateur CLI rendu batch ATOM-IC"
    )
    parser.add_argument(
        "--drive-root", required=True, type=str,
        help="Racine du Drive EXODUS",
    )
    parser.add_argument(
        "--project-name", required=True, type=str,
        help="Nom du projet (pour trouver les .blend)",
    )
    parser.add_argument(
        "--blend-file", type=str, default=None,
        help="Chemin direct vers le .blend (override auto-detection)",
    )
    parser.add_argument(
        "--blender-path", type=str, default="blender",
        help="Chemin vers l'exécutable Blender (default: blender)",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=300,
        help="Frames par chunk (default: 300)",
    )
    parser.add_argument(
        "--preset", type=str, default="darkroom",
        help="Preset de rendu (default: darkroom)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Reprendre depuis checkpoint",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Afficher le plan sans rendre",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Logs détaillés",
    )
    return parser.parse_args()


def find_blend_files(drive_root: Path) -> list[Path]:
    out_dir = drive_root / "04_PHOTOGRAPHY_WING" / "OUT_CAMERA_LOGIC"
    if not out_dir.exists():
        return []
    blends = sorted(out_dir.glob("scene_ready_*.blend"))
    return blends


def validate_blender(blender_path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [blender_path, "--version"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            version_line = result.stdout.strip().split("\n")[0]
            return True, version_line
        return False, f"exit code {result.returncode}"
    except FileNotFoundError:
        return False, "not found"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def validate_preset(preset_name: str) -> bool:
    return preset_name in RENDER_PRESETS


def estimate_render(total_frames: int, preset_name: str) -> dict:
    preset = RENDER_PRESETS.get(preset_name, RENDER_PRESETS["darkroom"])
    samples = preset["samples"]
    res = preset["resolution"]

    if res == (1920, 1080):
        spf_range = (3.0, 8.0)
    elif res == (3840, 2160):
        spf_range = (15.0, 45.0)
    else:
        spf_range = (5.0, 15.0)

    spf_factor = samples / 128.0
    spf_low = spf_range[0] * spf_factor
    spf_high = spf_range[1] * spf_factor

    size_per_frame_mb = (res[0] * res[1] * 3 * 2) / (1024 * 1024) * 0.7

    return {
        "total_frames": total_frames,
        "seconds_per_frame": f"{spf_low:.1f}–{spf_high:.1f}",
        "estimated_time_hours": f"{(total_frames * spf_low) / 3600:.1f}–{(total_frames * spf_high) / 3600:.1f}",
        "estimated_size_gb": round(total_frames * size_per_frame_mb / 1024, 1),
        "resolution": f"{res[0]}x{res[1]}",
        "samples": samples,
    }


def run_darkroom(
    blender_path: str,
    blend_file: Path,
    output_dir: Path,
    chunk_size: int,
    preset: str,
    resume: bool,
    verbose: bool,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        blender_path, "--background", str(blend_file),
        "--python", str(DARKROOM_SCRIPT),
        "--",
        "--output-dir", str(output_dir),
        "--chunk-size", str(chunk_size),
        "--preset", preset,
    ]
    if resume:
        cmd.append("--resume")
    if verbose:
        cmd.append("--verbose")

    log(f"Commande : {' '.join(cmd)}")

    t_start = time.time()
    result = subprocess.run(cmd, text=True)
    t_elapsed = time.time() - t_start

    frames = sorted(output_dir.glob("render_*.png"))
    total_size = sum(f.stat().st_size for f in frames)

    return {
        "blend_file": blend_file.name,
        "return_code": result.returncode,
        "elapsed_seconds": round(t_elapsed, 2),
        "frames_on_disk": len(frames),
        "total_size_mb": round(total_size / (1024 * 1024), 1),
        "output_dir": str(output_dir),
    }


def generate_report(
    output_dir: Path,
    results: list[dict],
    preset: str,
    chunk_size: int,
    total_elapsed: float,
) -> Path:
    report_path = output_dir / "darkroom_report.json"

    total_frames = sum(r["frames_on_disk"] for r in results)
    total_size_mb = sum(r["total_size_mb"] for r in results)
    avg_spf = total_elapsed / total_frames if total_frames > 0 else 0

    report = {
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "preset": preset,
        "chunk_size": chunk_size,
        "resolution": list(RENDER_PRESETS.get(preset, {}).get("resolution", (0, 0))),
        "samples": RENDER_PRESETS.get(preset, {}).get("samples", 0),
        "scenes": results,
        "summary": {
            "total_scenes": len(results),
            "total_frames": total_frames,
            "total_size_mb": round(total_size_mb, 1),
            "total_elapsed_seconds": round(total_elapsed, 2),
            "avg_seconds_per_frame": round(avg_spf, 2),
            "fps": TARGET_FPS,
        },
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log(f"Rapport : {report_path}")
    return report_path


def main() -> None:
    args = parse_args()
    drive_root = Path(args.drive_root)
    unit_root = drive_root / "04_PHOTOGRAPHY_WING"
    output_dir = unit_root / "OUT_CAMERA_LOGIC"

    log("=" * 60)
    log("EXO_04_DARKROOM — Orchestrateur rendu batch ATOM-IC")
    log("=" * 60)
    log(f"  Drive root    : {drive_root}")
    log(f"  Project       : {args.project_name}")
    log(f"  Preset        : {args.preset}")
    log(f"  Chunk size    : {args.chunk_size}")
    log(f"  Resume        : {args.resume}")
    log(f"  Dry-run       : {args.dry_run}")

    if not validate_preset(args.preset):
        log(f"ERREUR : Preset '{args.preset}' inconnu. "
            f"Valides : {list(RENDER_PRESETS.keys())}")
        sys.exit(1)

    if not args.dry_run:
        blender_ok, blender_info = validate_blender(args.blender_path)
        if not blender_ok:
            log(f"ERREUR : Blender non accessible ({blender_info})")
            log(f"  Chemin testé : {args.blender_path}")
            log("  Utilisez --blender-path ou --dry-run")
            sys.exit(1)
        log(f"  Blender       : {blender_info}")
    else:
        log("  Blender       : N/A (dry-run)")

    if args.blend_file:
        blend_files = [Path(args.blend_file)]
        if not blend_files[0].exists():
            log(f"ERREUR : Fichier .blend introuvable : {args.blend_file}")
            sys.exit(1)
    else:
        blend_files = find_blend_files(drive_root)
        if not blend_files:
            log("ERREUR : Aucun scene_ready_*.blend trouvé dans OUT_CAMERA_LOGIC/")
            log(f"  Dossier scanné : {output_dir}")
            sys.exit(1)

    log(f"\n  Fichiers .blend trouvés : {len(blend_files)}")
    for bf in blend_files:
        size_mb = bf.stat().st_size / (1024 * 1024)
        log(f"    {bf.name} ({size_mb:.1f} MB)")

    if args.dry_run:
        log("\n=== DRY-RUN — Plan de rendu ===")
        preset_cfg = RENDER_PRESETS[args.preset]
        for bf in blend_files:
            log(f"\n  Scene : {bf.name}")
            est = estimate_render(1800, args.preset)
            log(f"    Resolution   : {est['resolution']}")
            log(f"    Samples      : {est['samples']}")
            log(f"    Frames       : {est['total_frames']} (estimé)")
            log(f"    Chunks       : {(est['total_frames'] + args.chunk_size - 1) // args.chunk_size}")
            log(f"    Temps estimé : {est['estimated_time_hours']}h")
            log(f"    Taille       : ~{est['estimated_size_gb']} GB")
            log(f"    s/frame      : {est['seconds_per_frame']}s (GPU T4)")
        log("\n  Pour lancer le rendu, retirez --dry-run")
        return

    results = []
    t_total_start = time.time()

    for idx, bf in enumerate(blend_files, 1):
        log(f"\n{'=' * 60}")
        log(f"SCÈNE {idx}/{len(blend_files)} : {bf.name}")
        log(f"{'=' * 60}")

        scene_result = run_darkroom(
            blender_path=args.blender_path,
            blend_file=bf,
            output_dir=output_dir,
            chunk_size=args.chunk_size,
            preset=args.preset,
            resume=args.resume,
            verbose=args.verbose,
        )
        results.append(scene_result)

        if scene_result["return_code"] != 0:
            log(f"ERREUR : Blender exit code {scene_result['return_code']}")
            log("  Le checkpoint est conservé pour --resume")
        else:
            log(f"Scène terminée : {scene_result['frames_on_disk']} frames, "
                f"{scene_result['total_size_mb']:.1f} MB, "
                f"{scene_result['elapsed_seconds']:.0f}s")

    t_total = time.time() - t_total_start

    report_path = generate_report(output_dir, results, args.preset, args.chunk_size, t_total)

    log("\n" + "=" * 60)
    log("EXO_04_DARKROOM — TERMINÉ")
    total_frames = sum(r["frames_on_disk"] for r in results)
    total_size = sum(r["total_size_mb"] for r in results)
    log(f"  Scènes     : {len(results)}")
    log(f"  Frames     : {total_frames}")
    log(f"  Taille     : {total_size:.1f} MB")
    log(f"  Temps      : {t_total / 60:.1f} min ({t_total / 3600:.2f}h)")
    log(f"  Rapport    : {report_path}")
    log("=" * 60)


if __name__ == "__main__":
    main()
