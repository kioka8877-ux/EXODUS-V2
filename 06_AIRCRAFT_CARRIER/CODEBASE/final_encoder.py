#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     FINAL ENCODER — EXODUS CARRIER V2                        ║
║         Encodage final AV1/H.265/ProRes + Encode depuis frames PNG          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  C'est le SEUL module du pipeline qui fait de la compression lossy.         ║
║  Toutes les autres étapes travaillent en PNG lossless.                      ║
║  Support AV1 (libsvtav1), H.265, H.264, ProRes.                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


class FinalEncoder:
    """Encodeur final — SEUL point de compression lossy du pipeline."""

    CODEC_PRESETS = {
        "av1": {
            "codec": "libsvtav1",
            "default_crf": 30,
            "preset": 6,
            "params": ["-pix_fmt", "yuv420p10le"],
        },
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

    def check_av1_available(self) -> bool:
        """Vérifie si libsvtav1 est disponible dans FFmpeg."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            return "libsvtav1" in result.stdout
        except Exception:
            return False

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

    def encode_from_frames(
        self,
        frames_dir: Path,
        frame_pattern: str,
        audio_input: Optional[Path],
        output_path: Path,
        fps: int = 120,
        codec: str = "av1",
        crf: int = None,
        preset_name: str = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Encode une séquence de frames PNG en vidéo finale.

        C'est la SEULE méthode qui fait de la compression lossy.
        Toutes les autres étapes du pipeline passent par celle-ci.

        Args:
            frames_dir: Dossier de frames PNG
            frame_pattern: ex: "frame_%08d.png"
            audio_input: Fichier audio (None pour vidéo muette)
            output_path: Chemin de sortie vidéo
            fps: Framerate
            codec: 'av1', 'h265', 'h264', 'prores'
            crf: CRF custom (override preset)
            preset_name: Si fourni, utilise ENCODING_PRESETS du carrier_schema
            metadata: Métadonnées à intégrer

        Returns:
            True si succès
        """
        codec_config = None

        if preset_name:
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent))
                from carrier_schema import ENCODING_PRESETS
                if preset_name in ENCODING_PRESETS:
                    ep = ENCODING_PRESETS[preset_name]
                    codec_key = self._schema_codec_to_key(ep.get("codec", ""))
                    codec_config = self.CODEC_PRESETS.get(codec_key)
                    if codec_config:
                        codec_config = dict(codec_config)
                        if "crf" in ep and crf is None:
                            crf = ep["crf"]
                        if "preset" in ep:
                            codec_config["preset"] = ep["preset"]
                        if "pix_fmt" in ep:
                            # Remove existing -pix_fmt and its value (pair-aware filter)
                            old_params = codec_config.get("params", [])
                            filtered = []
                            skip_next = False
                            for p in old_params:
                                if skip_next:
                                    skip_next = False
                                    continue
                                if p == "-pix_fmt":
                                    skip_next = True
                                    continue
                                filtered.append(p)
                            codec_config["params"] = ["-pix_fmt", ep["pix_fmt"]] + filtered
                        if "tune" in ep:
                            codec_config["_tune"] = ep["tune"]
                        if "extra_params" in ep:
                            codec_config["params"] = codec_config.get("params", []) + ep["extra_params"]
                        self._log(f"Preset schema '{preset_name}': codec={ep.get('codec')}, crf={crf}")
            except ImportError:
                self._log(f"carrier_schema non disponible, fallback codec '{codec}'")

        if not codec_config:
            codec_config = self.CODEC_PRESETS.get(codec.lower())
        if not codec_config:
            self._log(f"Codec inconnu: {codec}, fallback H.265")
            codec_config = self.CODEC_PRESETS["h265"]

        if crf is None:
            crf = codec_config.get("default_crf", 18)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = ["ffmpeg", "-y"]

        cmd.extend([
            "-framerate", str(fps),
            "-i", str(frames_dir / frame_pattern),
        ])

        if audio_input and Path(audio_input).exists():
            cmd.extend(["-i", str(audio_input)])
            audio_index = 1
        else:
            audio_index = None

        cmd.extend(["-c:v", codec_config["codec"]])

        if "profile" in codec_config:
            cmd.extend(["-profile:v", str(codec_config["profile"])])

        if "preset" in codec_config:
            cmd.extend(["-preset", str(codec_config["preset"])])

        if "_tune" in codec_config:
            cmd.extend(["-tune", codec_config["_tune"]])

        if "default_crf" in codec_config or crf is not None:
            cmd.extend(["-crf", str(crf)])

        cmd.extend(codec_config.get("params", []))

        has_pix_fmt = any("-pix_fmt" in str(p) for p in codec_config.get("params", []))
        if not has_pix_fmt and codec.lower() not in ["prores", "prores_hq", "prores_4444"]:
            cmd.extend(["-pix_fmt", "yuv420p"])

        if audio_index is not None:
            cmd.extend(["-map", "0:v:0", "-map", f"{audio_index}:a:0"])
            if output_path.suffix.lower() == ".mp4":
                cmd.extend(["-c:a", "aac", "-b:a", "320k"])
            else:
                cmd.extend(["-c:a", "pcm_s24le"])
        else:
            cmd.extend(["-an"])

        if metadata:
            for key, value in metadata.items():
                cmd.extend(["-metadata", f"{key}={value}"])

        cmd.extend([
            "-metadata", f"creation_time={datetime.now().isoformat()}",
            "-metadata", "encoder=EXODUS_CARRIER_v2.0"
        ])

        cmd.append(str(output_path))

        self._log(f"Encodage {codec.upper()} depuis frames → {output_path.name}")
        self._log(f"CRF={crf}, FPS={fps}, codec={codec_config['codec']}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200
            )

            if result.returncode != 0:
                self._log(f"Encodage échoué: {result.stderr[-500:]}")
                return False

            if output_path.exists():
                info = self.get_video_info(output_path)
                if info:
                    size_mb = info.get("size_bytes", 0) / (1024 * 1024)
                    bitrate_mbps = info.get("bitrate", 0) / 1_000_000
                    self._log(f"Output: {size_mb:.1f} MB, {bitrate_mbps:.1f} Mbps, {info.get('duration', 0):.1f}s")
                return True

            return False

        except subprocess.TimeoutExpired:
            self._log("Timeout encodage (2h)")
            return False
        except Exception as e:
            self._log(f"Erreur encodage: {e}")
            return False

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
        """Encode depuis une vidéo source (gardé pour rétrocompatibilité)."""
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
            cmd.extend(["-preset", str(codec_config["preset"])])

        if bitrate:
            cmd.extend(["-b:v", bitrate])
        elif "default_crf" in codec_config:
            cmd.extend(["-crf", str(crf)])

        cmd.extend(codec_config.get("params", []))

        has_pix_fmt = any("-pix_fmt" in str(p) for p in codec_config.get("params", []))
        if not has_pix_fmt and codec.lower() not in ["prores", "prores_hq", "prores_4444"]:
            cmd.extend(["-pix_fmt", "yuv420p"])

        if audio_index is not None:
            cmd.extend(["-map", "0:v:0", "-map", f"{audio_index}:a:0"])
            if output_path.suffix.lower() == ".mp4":
                cmd.extend(["-c:a", "aac", "-b:a", "320k"])
            else:
                cmd.extend(["-c:a", "pcm_s24le"])
        else:
            cmd.extend(["-map", "0:v:0", "-an"])

        if metadata:
            for key, value in metadata.items():
                cmd.extend(["-metadata", f"{key}={value}"])

        cmd.extend([
            "-metadata", f"creation_time={datetime.now().isoformat()}",
            "-metadata", "encoder=EXODUS_CARRIER_v2.0"
        ])

        cmd.append(str(output_path))

        self._log(f"Encodage {codec.upper()} → {output_path.name}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

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
        """Extrait une thumbnail de la vidéo."""
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
        """Génère une grille de thumbnails (preview sheet)."""
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

    def _schema_codec_to_key(self, schema_codec: str) -> str:
        """Convertit un nom de codec schema en clé CODEC_PRESETS."""
        mapping = {
            "libsvtav1": "av1",
            "libx265": "h265",
            "libx264": "h264",
            "prores_ks": "prores",
        }
        return mapping.get(schema_codec, schema_codec)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python final_encoder.py <frames_dir> <output> [codec] [audio_input]")
        print("  frames_dir: Dossier de frames PNG")
        print("  output: Fichier de sortie (.mp4 ou .mov)")
        print("  codec: av1, h265, h264, prores (défaut: av1)")
        print("  audio_input: Audio source (optionnel)")
        sys.exit(1)

    frames_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    codec = sys.argv[3] if len(sys.argv) > 3 else "av1"
    audio_input = Path(sys.argv[4]) if len(sys.argv) > 4 else None

    encoder = FinalEncoder(verbose=True)

    print(f"AV1 disponible: {encoder.check_av1_available()}")

    success = encoder.encode_from_frames(
        frames_dir=frames_dir,
        frame_pattern="frame_%08d.png",
        audio_input=audio_input,
        output_path=output_path,
        codec=codec,
    )

    sys.exit(0 if success else 1)
