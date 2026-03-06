#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       UPSCALER — EXODUS CARRIER V2                           ║
║                Upscale chunk-based frame-to-frame PNG→PNG                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Travaille directement sur des frames PNG — aucune vidéo intermédiaire     ║
║  lossy. Le fallback FFmpeg Lanczos traite image par image.                  ║
║  ZÉRO libx264 dans ce module.                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict


class Upscaler:
    """Upscaler de frames PNG via Real-ESRGAN ou FFmpeg Lanczos."""

    RESOLUTION_PRESETS = {
        "4K": (3840, 2160),
        "UHD": (3840, 2160),
        "2K": (2560, 1440),
        "1080p": (1920, 1080),
        "720p": (1280, 720)
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        use_gpu: bool = True,
        verbose: bool = False
    ):
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.verbose = verbose
        self._esrgan_available = self._check_esrgan_available()

    def _log(self, msg: str):
        if self.verbose:
            print(f"[UPSCALER] {msg}")

    def _check_esrgan_available(self) -> bool:
        """Vérifie si Real-ESRGAN est disponible."""
        if not self.model_path:
            return False

        model_path = Path(self.model_path)
        if not model_path.exists():
            return False

        try:
            import torch
            self._log(f"PyTorch disponible pour Real-ESRGAN, GPU: {torch.cuda.is_available()}")
            return True
        except ImportError:
            self._log("PyTorch non disponible, Real-ESRGAN désactivé")
            return False

    def get_frame_info(self, frame_path: Path) -> dict:
        """Lit les dimensions d'une frame PNG via FFprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(frame_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    return {"width": int(parts[0]), "height": int(parts[1])}
        except Exception as e:
            self._log(f"Erreur FFprobe: {e}")

        return {"width": 0, "height": 0}

    def get_resolution(self, video_path: Path) -> Optional[Tuple[int, int]]:
        """Récupère la résolution d'une vidéo (gardé pour rétrocompatibilité)."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1])
        except Exception as e:
            self._log(f"Erreur FFprobe: {e}")

        return None

    def needs_upscale_frames(
        self,
        sample_frame: Path,
        target_width: int = 3840,
        target_height: int = 2160
    ) -> bool:
        """Vérifie si les frames nécessitent un upscale."""
        info = self.get_frame_info(sample_frame)
        if not info or info["width"] == 0:
            return False
        return info["width"] < target_width or info["height"] < target_height

    def upscale_chunk(
        self,
        input_frames: List[Path],
        output_dir: Path,
        target_width: int = 3840,
        target_height: int = 2160,
    ) -> List[Path]:
        """Upscale un chunk de frames.

        Lit les PNG sources.
        Écrit les PNG upscalées dans output_dir.
        Ne crée AUCUNE vidéo intermédiaire.
        """
        if not input_frames:
            return []

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        sample_info = self.get_frame_info(input_frames[0])
        current_w = sample_info.get("width", 0)
        current_h = sample_info.get("height", 0)

        self._log(f"Chunk: {len(input_frames)} frames, {current_w}x{current_h} → {target_width}x{target_height}")

        if current_w >= target_width and current_h >= target_height:
            self._log("Résolution déjà suffisante, copie simple")
            output_files = []
            for i, frame in enumerate(input_frames):
                out_path = output_dir / f"frame_{i:08d}.png"
                shutil.copy2(str(frame), str(out_path))
                output_files.append(out_path)
            return output_files

        if self._esrgan_available:
            result = self._upscale_chunk_esrgan(input_frames, output_dir, target_width, target_height)
            if result:
                return result
            self._log("Real-ESRGAN échoué, fallback FFmpeg Lanczos")

        return self._upscale_chunk_lanczos(input_frames, output_dir, target_width, target_height)

    def _upscale_chunk_esrgan(
        self,
        input_frames: List[Path],
        output_dir: Path,
        target_width: int,
        target_height: int
    ) -> Optional[List[Path]]:
        """Upscale via Real-ESRGAN frame par frame (PNG→PNG)."""
        try:
            import torch
            import numpy as np
            from PIL import Image

            device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")
            self._log(f"Real-ESRGAN sur {device}")

            model = self._load_esrgan_model(device)
            if model is None:
                return None

            output_files = []

            with torch.no_grad():
                for i, frame_path in enumerate(input_frames):
                    if i % 100 == 0:
                        self._log(f"  Upscale frame {i}/{len(input_frames)}")

                    img = Image.open(frame_path).convert('RGB')
                    img_np = np.array(img)

                    upscaled = self._process_frame_esrgan(model, img_np, device)

                    if upscaled.shape[1] != target_width or upscaled.shape[0] != target_height:
                        upscaled_img = Image.fromarray(upscaled)
                        upscaled_img = upscaled_img.resize((target_width, target_height), Image.LANCZOS)
                        upscaled = np.array(upscaled_img)

                    out_path = output_dir / f"frame_{i:08d}.png"
                    Image.fromarray(upscaled).save(out_path)
                    output_files.append(out_path)

            self._log(f"Real-ESRGAN: {len(output_files)} frames upscalées")
            return output_files

        except ImportError as e:
            self._log(f"Dépendance manquante pour Real-ESRGAN: {e}")
            return None
        except Exception as e:
            self._log(f"Erreur Real-ESRGAN: {e}")
            return None

    def _upscale_chunk_lanczos(
        self,
        input_frames: List[Path],
        output_dir: Path,
        target_width: int,
        target_height: int
    ) -> List[Path]:
        """Upscale via FFmpeg Lanczos frame par frame (image→image, pas de vidéo)."""
        self._log(f"FFmpeg Lanczos upscale → {target_width}x{target_height}")

        output_files = []

        for i, frame_path in enumerate(input_frames):
            if i % 100 == 0 and i > 0:
                self._log(f"  Lanczos frame {i}/{len(input_frames)}")

            out_path = output_dir / f"frame_{i:08d}.png"

            cmd = [
                "ffmpeg", "-y",
                "-i", str(frame_path),
                "-vf", f"scale={target_width}:{target_height}:flags=lanczos",
                str(out_path)
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0 and out_path.exists():
                    output_files.append(out_path)
                else:
                    self._log(f"Lanczos échoué pour {frame_path.name}: {result.stderr[-200:]}")
                    shutil.copy2(str(frame_path), str(out_path))
                    output_files.append(out_path)
            except Exception as e:
                self._log(f"Erreur Lanczos {frame_path.name}: {e}")
                shutil.copy2(str(frame_path), str(out_path))
                output_files.append(out_path)

        self._log(f"Lanczos: {len(output_files)} frames upscalées")
        return output_files

    def _load_esrgan_model(self, device):
        """Charge le modèle Real-ESRGAN."""
        try:
            import torch

            model_path = Path(self.model_path)

            try:
                from basicsr.archs.rrdbnet_arch import RRDBNet
                from realesrgan import RealESRGANer

                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
                upsampler = RealESRGANer(
                    scale=4,
                    model_path=str(model_path),
                    model=model,
                    tile=0,
                    tile_pad=10,
                    pre_pad=0,
                    half=True if device.type == 'cuda' else False,
                    device=device
                )
                return upsampler
            except ImportError:
                pass

            state_dict = torch.load(str(model_path), map_location=device)
            self._log("Modèle chargé directement (pas de wrapper RealESRGAN)")
            return state_dict

        except Exception as e:
            self._log(f"Erreur chargement modèle: {e}")
            return None

    def _process_frame_esrgan(self, model, img_np, device):
        """Traite une frame avec Real-ESRGAN."""
        try:
            if hasattr(model, 'enhance'):
                output, _ = model.enhance(img_np, outscale=4)
                return output
        except Exception:
            pass

        return img_np


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python upscaler.py <input_dir> <output_dir> [width] [height] [model_path]")
        print("  input_dir: Dossier de frames PNG source")
        print("  output_dir: Dossier de frames PNG upscalées")
        print("  width: Largeur cible (défaut: 3840)")
        print("  height: Hauteur cible (défaut: 2160)")
        print("  model_path: Chemin vers le modèle Real-ESRGAN (optionnel)")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    target_width = int(sys.argv[3]) if len(sys.argv) > 3 else 3840
    target_height = int(sys.argv[4]) if len(sys.argv) > 4 else 2160
    model_path = sys.argv[5] if len(sys.argv) > 5 else None

    input_frames = sorted(input_dir.glob("*.png"))
    if not input_frames:
        print(f"Aucune frame PNG dans {input_dir}")
        sys.exit(1)

    upscaler = Upscaler(model_path=model_path, verbose=True)
    result = upscaler.upscale_chunk(input_frames, output_dir, target_width, target_height)

    print(f"Frames upscalées: {len(result)}")
    sys.exit(0 if result else 1)
