#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SEQUENCE ASSEMBLER — EXODUS CARRIER V2                    ║
║                  Frame Indexer : Scan + Manifeste JSON                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Scanne les séquences d'images, valide l'intégrité, retourne un manifeste  ║
║  JSON prêt pour le pipeline frame-based. N'appelle JAMAIS FFmpeg encode.   ║
║  Utilise FFprobe uniquement pour lire les dimensions des images.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import re
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class SequenceInfo:
    """Informations sur une séquence d'images."""
    pattern: str
    first_frame: int
    last_frame: int
    frame_count: int
    width: int
    height: int
    format: str


class SequenceAssembler:
    """Frame Indexer — scanne et indexe les séquences d'images."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"[FRAME_INDEXER] {msg}")

    def detect_sequence_pattern(self, files: List[Path]) -> Optional[SequenceInfo]:
        """
        Détecte le pattern de numérotation dans une liste de fichiers.
        Retourne un SequenceInfo avec le pattern FFmpeg.
        """
        if not files:
            return None

        files = sorted(files)
        first_file = files[0]
        ext = first_file.suffix.lower()

        stem = first_file.stem
        match = re.search(r'(\d+)$', stem)

        if match:
            number_str = match.group(1)
            padding = len(number_str)
            prefix = stem[:match.start()]
            first_frame = int(number_str)

            last_file_stem = files[-1].stem
            last_match = re.search(r'(\d+)$', last_file_stem)
            last_frame = int(last_match.group(1)) if last_match else first_frame + len(files) - 1

            pattern = f"{first_file.parent}/{prefix}%0{padding}d{ext}"
        else:
            pattern = str(first_file.parent / f"%04d{ext}")
            first_frame = 1
            last_frame = len(files)

        width, height = self._get_image_dimensions(first_file)

        return SequenceInfo(
            pattern=pattern,
            first_frame=first_frame,
            last_frame=last_frame,
            frame_count=len(files),
            width=width,
            height=height,
            format=ext.lstrip('.')
        )

    def _get_image_dimensions(self, image_path: Path) -> Tuple[int, int]:
        """Récupère les dimensions d'une image via FFprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(image_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1])
        except Exception as e:
            self._log(f"Erreur FFprobe dimensions: {e}")

        return 1920, 1080

    def index_frames(self, components_dir: Path, plan: dict = None) -> dict:
        """Scanne le dossier, détecte les séquences, valide, retourne un manifeste.

        Args:
            components_dir: Dossier contenant les séquences d'images
            plan: PRODUCTION_PLAN dict (optionnel, pour extraire fps)

        Returns:
            {
                "sequences": [
                    {
                        "scene_id": "scene_001",
                        "pattern": "/path/to/graded_%06d.png",
                        "first_frame": 1,
                        "last_frame": 300,
                        "frame_count": 300,
                        "width": 1920,
                        "height": 1080,
                        "format": "png",
                        "files": [Path, Path, ...]
                    }
                ],
                "total_frames": 1800,
                "fps": 30,
                "duration_seconds": 60.0,
                "resolution": (1920, 1080),
            }
        """
        components_dir = Path(components_dir)

        fps = 30
        if plan:
            pp = plan.get("production_plan", {})
            fmt = pp.get("format", {})
            fps = int(fmt.get("fps_source", plan.get("output", {}).get("framerate_source", 30)))

        exr_files = sorted(components_dir.glob("graded_*.exr"))
        png_files = sorted(components_dir.glob("graded_*.png"))
        all_files = exr_files if exr_files else png_files

        if not all_files:
            all_files = sorted(components_dir.glob("*.exr")) or sorted(components_dir.glob("*.png"))

        if not all_files:
            self._log("Aucune séquence image trouvée")
            return {
                "sequences": [],
                "total_frames": 0,
                "fps": fps,
                "duration_seconds": 0.0,
                "resolution": (0, 0),
            }

        scenes = plan.get("scenes", []) if plan else []
        sequences = []

        if scenes:
            for i, scene in enumerate(scenes):
                scene_id = scene.get("scene_id", f"scene_{i:03d}")
                pattern_glob = scene.get("sequence_pattern", f"graded_{scene_id}_*.exr")
                scene_files = sorted(components_dir.glob(pattern_glob))

                if not scene_files:
                    pattern_glob_png = pattern_glob.replace(".exr", ".png")
                    scene_files = sorted(components_dir.glob(pattern_glob_png))

                if not scene_files:
                    self._log(f"Aucun fichier pour scène {scene_id}, skip")
                    continue

                seq_info = self.detect_sequence_pattern(scene_files)
                if seq_info:
                    sequences.append({
                        "scene_id": scene_id,
                        "pattern": seq_info.pattern,
                        "first_frame": seq_info.first_frame,
                        "last_frame": seq_info.last_frame,
                        "frame_count": seq_info.frame_count,
                        "width": seq_info.width,
                        "height": seq_info.height,
                        "format": seq_info.format,
                        "files": scene_files,
                    })
        else:
            seq_info = self.detect_sequence_pattern(all_files)
            if seq_info:
                sequences.append({
                    "scene_id": "scene_001",
                    "pattern": seq_info.pattern,
                    "first_frame": seq_info.first_frame,
                    "last_frame": seq_info.last_frame,
                    "frame_count": seq_info.frame_count,
                    "width": seq_info.width,
                    "height": seq_info.height,
                    "format": seq_info.format,
                    "files": all_files,
                })

        total_frames = sum(s["frame_count"] for s in sequences)
        duration = total_frames / fps if fps > 0 else 0.0
        resolution = (sequences[0]["width"], sequences[0]["height"]) if sequences else (0, 0)

        self._log(f"Indexé {len(sequences)} séquence(s), {total_frames} frames total")
        self._log(f"Résolution: {resolution[0]}x{resolution[1]}, FPS source: {fps}")
        self._log(f"Durée estimée: {duration:.2f}s")

        return {
            "sequences": sequences,
            "total_frames": total_frames,
            "fps": fps,
            "duration_seconds": duration,
            "resolution": resolution,
        }

    def get_video_info(self, video_path: Path) -> Optional[dict]:
        """Récupère les informations d'une vidéo (gardé pour rétrocompatibilité)."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
            "-of", "json",
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data.get("streams", [{}])[0]

                fps_str = stream.get("r_frame_rate", "30/1")
                fps_parts = fps_str.split('/')
                fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])

                return {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                    "fps": fps,
                    "frames": int(stream.get("nb_frames", 0)),
                    "duration": float(stream.get("duration", 0))
                }
        except Exception as e:
            self._log(f"Erreur FFprobe: {e}")

        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sequence_assembler.py <input_dir> [fps]")
        print("  input_dir: Dossier contenant les images séquence")
        print("  fps: Framerate source (défaut: 30)")
        print()
        print("Retourne un manifeste JSON sur stdout.")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    fps = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    assembler = SequenceAssembler(verbose=True)
    manifest = assembler.index_frames(input_dir, {"output": {"framerate_source": fps}})

    output = {k: v for k, v in manifest.items() if k != "sequences"}
    output["sequences"] = []
    for seq in manifest["sequences"]:
        seq_clean = {k: v for k, v in seq.items() if k != "files"}
        seq_clean["file_count"] = len(seq.get("files", []))
        output["sequences"].append(seq_clean)

    print(json.dumps(output, indent=2, default=str))
