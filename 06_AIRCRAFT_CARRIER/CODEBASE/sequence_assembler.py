#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SEQUENCE ASSEMBLER — EXODUS CARRIER                       ║
║                  Assemblage séquences EXR/PNG → Vidéo                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Charge les séquences d'images et les assemble en vidéo via FFmpeg          ║
║  Support EXR (OpenEXR) et PNG avec gestion des transitions                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import re
import os
from pathlib import Path
from typing import List, Optional, Tuple
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
    """Assembleur de séquences d'images vers vidéo."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[ASSEMBLER] {msg}")
    
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
    
    def assemble(
        self,
        sequence_files: List[Path],
        output_path: Path,
        fps: int = 30,
        pixel_format: str = "yuv420p",
        crf: int = 18
    ) -> bool:
        """
        Assemble une séquence d'images en vidéo.
        
        Args:
            sequence_files: Liste des fichiers image triés
            output_path: Chemin de sortie vidéo
            fps: Framerate de sortie
            pixel_format: Format pixel (yuv420p pour compatibilité)
            crf: Qualité (0-51, plus bas = meilleur)
        
        Returns:
            True si succès
        """
        seq_info = self.detect_sequence_pattern(sequence_files)
        if not seq_info:
            print("[ASSEMBLER:ERROR] Impossible de détecter le pattern de séquence")
            return False
        
        self._log(f"Pattern détecté: {seq_info.pattern}")
        self._log(f"Frames: {seq_info.first_frame} → {seq_info.last_frame} ({seq_info.frame_count} total)")
        self._log(f"Résolution: {seq_info.width}x{seq_info.height}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-start_number", str(seq_info.first_frame),
            "-i", seq_info.pattern,
            "-frames:v", str(seq_info.frame_count),
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "medium",
            "-pix_fmt", pixel_format,
            str(output_path)
        ]
        
        if seq_info.format == "exr":
            cmd.insert(1, "-apply_trc")
            cmd.insert(2, "bt709")
        
        self._log(f"Commande: {' '.join(cmd[:10])}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                print(f"[ASSEMBLER:ERROR] FFmpeg échoué: {result.stderr[-500:]}")
                return False
            
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                self._log(f"Output créé: {output_path} ({size_mb:.2f} MB)")
                return True
            
            print("[ASSEMBLER:ERROR] Fichier output non créé")
            return False
            
        except subprocess.TimeoutExpired:
            print("[ASSEMBLER:ERROR] Timeout dépassé (600s)")
            return False
        except Exception as e:
            print(f"[ASSEMBLER:ERROR] Exception: {e}")
            return False
    
    def assemble_with_transitions(
        self,
        scenes: List[dict],
        components_dir: Path,
        output_path: Path,
        fps: int = 30
    ) -> bool:
        """
        Assemble plusieurs scènes avec transitions.
        
        Args:
            scenes: Liste de scènes depuis PRODUCTION_PLAN
            components_dir: Dossier contenant les séquences
            output_path: Chemin de sortie
            fps: Framerate
        
        Returns:
            True si succès
        """
        if not scenes:
            self._log("Aucune scène à assembler")
            return False
        
        temp_dir = output_path.parent / "_temp_assembly"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        scene_videos = []
        concat_list = temp_dir / "concat_list.txt"
        
        try:
            for i, scene in enumerate(scenes):
                scene_id = scene.get("scene_id", f"scene_{i:03d}")
                pattern = scene.get("sequence_pattern", f"graded_{scene_id}_*.exr")
                transition = scene.get("transition", "cut")
                
                scene_files = sorted(components_dir.glob(pattern))
                
                if not scene_files:
                    self._log(f"Pas de fichiers pour scène {scene_id}, skip")
                    continue
                
                scene_output = temp_dir / f"scene_{i:03d}.mp4"
                
                if self.assemble(scene_files, scene_output, fps=fps):
                    scene_videos.append({
                        "path": scene_output,
                        "transition": transition,
                        "duration": scene.get("transition_duration", 0.5)
                    })
            
            if not scene_videos:
                print("[ASSEMBLER:ERROR] Aucune scène assemblée")
                return False
            
            if len(scene_videos) == 1:
                import shutil
                shutil.copy(scene_videos[0]["path"], output_path)
                return True
            
            with open(concat_list, 'w') as f:
                for sv in scene_videos:
                    f.write(f"file '{sv['path']}'\n")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0 and output_path.exists()
            
        finally:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def get_video_info(self, video_path: Path) -> Optional[dict]:
        """Récupère les informations d'une vidéo."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
            "-of", "json",
            str(video_path)
        ]
        
        try:
            import json
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
    
    if len(sys.argv) < 3:
        print("Usage: python sequence_assembler.py <input_dir> <output.mp4> [fps]")
        print("  input_dir: Dossier contenant les images séquence")
        print("  output.mp4: Fichier vidéo de sortie")
        print("  fps: Framerate (défaut: 30)")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    files = sorted(input_dir.glob("*.exr")) or sorted(input_dir.glob("*.png"))
    
    assembler = SequenceAssembler(verbose=True)
    success = assembler.assemble(files, output_file, fps=fps)
    
    sys.exit(0 if success else 1)
