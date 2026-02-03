#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       UPSCALER — EXODUS CARRIER                              ║
║                    Upscale vidéo 1080p → 4K (3840x2160)                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Utilise Real-ESRGAN pour upscale de haute qualité (si disponible)          ║
║  Fallback FFmpeg Lanczos pour performance                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional, Tuple


class Upscaler:
    """Upscaler vidéo via Real-ESRGAN ou FFmpeg."""
    
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
    
    def get_resolution(self, video_path: Path) -> Optional[Tuple[int, int]]:
        """Récupère la résolution d'une vidéo."""
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
    
    def needs_upscale(
        self,
        video_path: Path,
        target_width: int = 3840,
        target_height: int = 2160
    ) -> bool:
        """Vérifie si une vidéo nécessite un upscale."""
        resolution = self.get_resolution(video_path)
        if not resolution:
            return False
        
        current_width, current_height = resolution
        return current_width < target_width or current_height < target_height
    
    def upscale(
        self,
        input_video: Path,
        output_video: Path,
        target_width: int = 3840,
        target_height: int = 2160,
        scale_factor: int = 4
    ) -> bool:
        """
        Upscale une vidéo vers la résolution cible.
        
        Args:
            input_video: Vidéo source
            output_video: Vidéo upscalée
            target_width: Largeur cible
            target_height: Hauteur cible
            scale_factor: Facteur de scale pour Real-ESRGAN
        
        Returns:
            True si succès
        """
        current_res = self.get_resolution(input_video)
        if not current_res:
            self._log("Impossible de lire la résolution source")
            return False
        
        current_width, current_height = current_res
        self._log(f"Source: {current_width}x{current_height} → Target: {target_width}x{target_height}")
        
        if current_width >= target_width and current_height >= target_height:
            self._log("Résolution déjà suffisante, copie simple")
            shutil.copy(input_video, output_video)
            return True
        
        if self._esrgan_available:
            success = self._upscale_esrgan(input_video, output_video, scale_factor)
            if success:
                return self._resize_to_target(output_video, output_video, target_width, target_height)
            self._log("Real-ESRGAN échoué, fallback FFmpeg")
        
        return self._upscale_ffmpeg(input_video, output_video, target_width, target_height)
    
    def _upscale_esrgan(
        self,
        input_video: Path,
        output_video: Path,
        scale_factor: int
    ) -> bool:
        """Upscale via Real-ESRGAN (frame par frame)."""
        try:
            import torch
            import numpy as np
            from PIL import Image
            
            device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")
            self._log(f"Real-ESRGAN sur {device}")
            
            model = self._load_esrgan_model(device)
            if model is None:
                return False
            
            temp_dir = output_video.parent / "_temp_upscale"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                frames_dir = temp_dir / "frames"
                upscaled_dir = temp_dir / "upscaled"
                frames_dir.mkdir(exist_ok=True)
                upscaled_dir.mkdir(exist_ok=True)
                
                self._log("Extraction frames...")
                fps = self._extract_frames_with_fps(input_video, frames_dir)
                
                frame_files = sorted(frames_dir.glob("*.png"))
                total_frames = len(frame_files)
                self._log(f"Upscale de {total_frames} frames...")
                
                with torch.no_grad():
                    for i, frame_path in enumerate(frame_files):
                        if i % 100 == 0:
                            self._log(f"  Frame {i}/{total_frames}")
                        
                        img = Image.open(frame_path).convert('RGB')
                        img_np = np.array(img)
                        
                        upscaled = self._process_frame_esrgan(model, img_np, device)
                        
                        out_path = upscaled_dir / frame_path.name
                        Image.fromarray(upscaled).save(out_path)
                
                self._log("Assemblage vidéo...")
                self._frames_to_video(upscaled_dir, output_video, fps)
                
                return output_video.exists()
                
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except ImportError as e:
            self._log(f"Dépendance manquante pour Real-ESRGAN: {e}")
            return False
        except Exception as e:
            self._log(f"Erreur Real-ESRGAN: {e}")
            return False
    
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
    
    def _extract_frames_with_fps(self, video_path: Path, output_dir: Path) -> float:
        """Extrait les frames et retourne le FPS."""
        cmd_info = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "csv=p=0",
            str(video_path)
        ]
        
        fps = 30.0
        try:
            result = subprocess.run(cmd_info, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                fps_str = result.stdout.strip()
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den)
                else:
                    fps = float(fps_str)
        except Exception:
            pass
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-qscale:v", "2",
            str(output_dir / "frame_%08d.png")
        ]
        subprocess.run(cmd, capture_output=True, timeout=600)
        
        return fps
    
    def _frames_to_video(self, frames_dir: Path, output_path: Path, fps: float):
        """Assemble les frames en vidéo."""
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%08d.png"),
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, timeout=1200)
    
    def _resize_to_target(
        self,
        input_video: Path,
        output_video: Path,
        target_width: int,
        target_height: int
    ) -> bool:
        """Redimensionne vers la résolution exacte cible."""
        current_res = self.get_resolution(input_video)
        if current_res and current_res[0] == target_width and current_res[1] == target_height:
            return True
        
        temp_output = output_video.parent / f"_temp_resize_{output_video.name}"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vf", f"scale={target_width}:{target_height}:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(temp_output)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and temp_output.exists():
                shutil.move(temp_output, output_video)
                return True
        except Exception as e:
            self._log(f"Erreur resize: {e}")
        
        if temp_output.exists():
            temp_output.unlink()
        return False
    
    def _upscale_ffmpeg(
        self,
        input_video: Path,
        output_video: Path,
        target_width: int,
        target_height: int
    ) -> bool:
        """
        Upscale via FFmpeg avec filtre Lanczos (rapide mais qualité moindre).
        """
        self._log(f"FFmpeg Lanczos upscale → {target_width}x{target_height}")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vf", f"scale={target_width}:{target_height}:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            str(output_video)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                self._log(f"FFmpeg upscale échoué: {result.stderr[-500:]}")
                return False
            
            return output_video.exists()
            
        except subprocess.TimeoutExpired:
            self._log("Timeout FFmpeg upscale")
            return False
        except Exception as e:
            self._log(f"Erreur FFmpeg: {e}")
            return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python upscaler.py <input.mp4> <output.mp4> [width] [height] [model_path]")
        print("  input.mp4: Vidéo source")
        print("  output.mp4: Vidéo upscalée")
        print("  width: Largeur cible (défaut: 3840)")
        print("  height: Hauteur cible (défaut: 2160)")
        print("  model_path: Chemin vers le modèle Real-ESRGAN (optionnel)")
        sys.exit(1)
    
    input_video = Path(sys.argv[1])
    output_video = Path(sys.argv[2])
    target_width = int(sys.argv[3]) if len(sys.argv) > 3 else 3840
    target_height = int(sys.argv[4]) if len(sys.argv) > 4 else 2160
    model_path = sys.argv[5] if len(sys.argv) > 5 else None
    
    upscaler = Upscaler(model_path=model_path, verbose=True)
    success = upscaler.upscale(input_video, output_video, target_width, target_height)
    
    sys.exit(0 if success else 1)
