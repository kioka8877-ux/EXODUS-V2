#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     FINAL ENCODER — EXODUS CARRIER                           ║
║              Encodage final H.265/ProRes + Thumbnail                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Encodage haute qualité pour distribution (H.265) et archivage (ProRes)     ║
║  Génération de thumbnails et embedding de métadonnées                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


class FinalEncoder:
    """Encodeur final pour export vidéo haute qualité."""
    
    CODEC_PRESETS = {
        "h265": {
            "codec": "libx265",
            "default_crf": 18,
            "preset": "slow",
            "params": ["-tag:v", "hvc1"]
        },
        "h264": {
            "codec": "libx264",
            "default_crf": 18,
            "preset": "slow",
            "params": []
        },
        "prores": {
            "codec": "prores_ks",
            "profile": 3,
            "params": ["-pix_fmt", "yuv422p10le"]
        },
        "prores_hq": {
            "codec": "prores_ks",
            "profile": 3,
            "params": ["-pix_fmt", "yuv422p10le"]
        },
        "prores_4444": {
            "codec": "prores_ks",
            "profile": 4,
            "params": ["-pix_fmt", "yuva444p10le"]
        }
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[ENCODER] {msg}")
    
    def get_video_info(self, video_path: Path) -> Optional[dict]:
        """Récupère les informations d'une vidéo."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration,codec_name",
            "-show_entries", "format=duration,size,bit_rate",
            "-of", "json",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data.get("streams", [{}])[0]
                format_info = data.get("format", {})
                
                fps_str = stream.get("r_frame_rate", "30/1")
                fps_parts = fps_str.split('/')
                fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])
                
                return {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                    "fps": fps,
                    "duration": float(stream.get("duration") or format_info.get("duration", 0)),
                    "codec": stream.get("codec_name", "unknown"),
                    "size_bytes": int(format_info.get("size", 0)),
                    "bitrate": int(format_info.get("bit_rate", 0))
                }
        except Exception as e:
            self._log(f"Erreur FFprobe: {e}")
        
        return None
    
    def encode(
        self,
        video_input: Path,
        audio_input: Optional[Path],
        output_path: Path,
        codec: str = "h265",
        crf: int = 18,
        bitrate: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Encode la vidéo finale avec audio et métadonnées.
        
        Args:
            video_input: Vidéo source
            audio_input: Audio source (None pour vidéo muette)
            output_path: Chemin de sortie
            codec: 'h265', 'h264', 'prores', 'prores_hq', 'prores_4444'
            crf: Qualité pour H.265/H.264 (0-51, plus bas = meilleur)
            bitrate: Bitrate cible (ex: "50M") - override CRF si spécifié
            metadata: Métadonnées à intégrer
        
        Returns:
            True si succès
        """
        codec_config = self.CODEC_PRESETS.get(codec.lower())
        if not codec_config:
            self._log(f"Codec inconnu: {codec}, fallback H.265")
            codec_config = self.CODEC_PRESETS["h265"]
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = ["ffmpeg", "-y"]
        
        cmd.extend(["-i", str(video_input)])
        
        if audio_input and audio_input.exists():
            cmd.extend(["-i", str(audio_input)])
            audio_index = 1
        else:
            audio_index = None
        
        cmd.extend(["-c:v", codec_config["codec"]])
        
        if "profile" in codec_config:
            cmd.extend(["-profile:v", str(codec_config["profile"])])
        
        if "preset" in codec_config:
            cmd.extend(["-preset", codec_config["preset"]])
        
        if bitrate:
            cmd.extend(["-b:v", bitrate])
        elif "default_crf" in codec_config:
            cmd.extend(["-crf", str(crf)])
        
        cmd.extend(codec_config.get("params", []))
        
        if codec.lower() not in ["prores", "prores_hq", "prores_4444"]:
            cmd.extend(["-pix_fmt", "yuv420p"])
        
        if audio_index is not None:
            cmd.extend(["-map", "0:v:0", "-map", f"{audio_index}:a:0"])
            if output_path.suffix.lower() == ".mp4":
                cmd.extend(["-c:a", "aac", "-b:a", "320k"])
            else:
                cmd.extend(["-c:a", "pcm_s24le"])
        else:
            cmd.extend(["-map", "0:v:0"])
            cmd.extend(["-an"])
        
        if metadata:
            for key, value in metadata.items():
                cmd.extend(["-metadata", f"{key}={value}"])
        
        cmd.extend([
            "-metadata", f"creation_time={datetime.now().isoformat()}",
            "-metadata", "encoder=EXODUS_CARRIER_v1.0"
        ])
        
        cmd.append(str(output_path))
        
        self._log(f"Encodage {codec.upper()} → {output_path.name}")
        self._log(f"Commande: {' '.join(cmd[:15])}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode != 0:
                self._log(f"Encodage échoué: {result.stderr[-500:]}")
                return False
            
            if output_path.exists():
                info = self.get_video_info(output_path)
                if info:
                    size_mb = info.get("size_bytes", 0) / (1024 * 1024)
                    bitrate_mbps = info.get("bitrate", 0) / 1_000_000
                    self._log(f"Output: {size_mb:.1f} MB, {bitrate_mbps:.1f} Mbps")
                return True
            
            return False
            
        except subprocess.TimeoutExpired:
            self._log("Timeout encodage (1h)")
            return False
        except Exception as e:
            self._log(f"Erreur encodage: {e}")
            return False
    
    def extract_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: str = "50%",
        width: int = 1920,
        height: int = 1080
    ) -> bool:
        """
        Extrait une thumbnail de la vidéo.
        
        Args:
            video_path: Vidéo source
            output_path: Image de sortie
            timestamp: Position (ex: "50%", "00:01:30", "90")
            width: Largeur de sortie
            height: Hauteur de sortie
        
        Returns:
            True si succès
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if timestamp.endswith('%'):
            info = self.get_video_info(video_path)
            if info and info.get("duration"):
                percentage = float(timestamp.rstrip('%')) / 100
                timestamp = str(info["duration"] * percentage)
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", timestamp,
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-q:v", "2",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                self._log(f"Thumbnail échoué: {result.stderr[-300:]}")
                return False
            
            return output_path.exists()
            
        except Exception as e:
            self._log(f"Erreur thumbnail: {e}")
            return False
    
    def extract_thumbnails_grid(
        self,
        video_path: Path,
        output_path: Path,
        columns: int = 4,
        rows: int = 4,
        thumb_width: int = 480
    ) -> bool:
        """
        Génère une grille de thumbnails (preview sheet).
        
        Args:
            video_path: Vidéo source
            output_path: Image de sortie
            columns: Nombre de colonnes
            rows: Nombre de lignes
            thumb_width: Largeur de chaque vignette
        
        Returns:
            True si succès
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        info = self.get_video_info(video_path)
        if not info or not info.get("duration"):
            return False
        
        duration = info["duration"]
        total_frames = columns * rows
        interval = duration / (total_frames + 1)
        
        filter_complex = f"fps=1/{interval},scale={thumb_width}:-1,tile={columns}x{rows}"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", filter_complex,
            "-frames:v", "1",
            "-q:v", "2",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode == 0 and output_path.exists()
        except Exception as e:
            self._log(f"Erreur thumbnail grid: {e}")
            return False
    
    def add_watermark(
        self,
        video_input: Path,
        output_path: Path,
        watermark_path: Path,
        position: str = "bottom_right",
        opacity: float = 0.5,
        scale: float = 0.15
    ) -> bool:
        """
        Ajoute un watermark à la vidéo.
        
        Args:
            video_input: Vidéo source
            output_path: Vidéo avec watermark
            watermark_path: Image du watermark (PNG avec transparence)
            position: 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'
            opacity: Opacité du watermark (0-1)
            scale: Taille relative au frame
        
        Returns:
            True si succès
        """
        position_map = {
            "top_left": "10:10",
            "top_right": "main_w-overlay_w-10:10",
            "bottom_left": "10:main_h-overlay_h-10",
            "bottom_right": "main_w-overlay_w-10:main_h-overlay_h-10",
            "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
        }
        
        pos = position_map.get(position, position_map["bottom_right"])
        
        filter_complex = f"[1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm];[0:v][wm]overlay={pos}"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_input),
            "-i", str(watermark_path),
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-crf", "18",
            "-c:a", "copy",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return result.returncode == 0 and output_path.exists()
        except Exception as e:
            self._log(f"Erreur watermark: {e}")
            return False
    
    def concat_videos(
        self,
        video_list: list,
        output_path: Path,
        codec: str = "h265"
    ) -> bool:
        """
        Concatène plusieurs vidéos.
        
        Args:
            video_list: Liste des chemins vidéo
            output_path: Vidéo de sortie
            codec: Codec de sortie
        
        Returns:
            True si succès
        """
        if not video_list:
            return False
        
        temp_list = output_path.parent / "_temp_concat_list.txt"
        
        try:
            with open(temp_list, 'w') as f:
                for video in video_list:
                    f.write(f"file '{video}'\n")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(temp_list),
                "-c", "copy",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return result.returncode == 0 and output_path.exists()
            
        finally:
            if temp_list.exists():
                temp_list.unlink()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python final_encoder.py <video_input> <output> <codec> [audio_input]")
        print("  video_input: Vidéo source")
        print("  output: Fichier de sortie (.mp4 ou .mov)")
        print("  codec: h265, h264, prores, prores_hq, prores_4444")
        print("  audio_input: Audio source (optionnel)")
        sys.exit(1)
    
    video_input = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    codec = sys.argv[3]
    audio_input = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    
    encoder = FinalEncoder(verbose=True)
    success = encoder.encode(video_input, audio_input, output_path, codec=codec)
    
    sys.exit(0 if success else 1)
