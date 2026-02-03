#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RIFE INTERPOLATOR — EXODUS CARRIER                        ║
║              Interpolation temporelle 30→120 FPS via RIFE                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Utilise RIFE (Real-Time Intermediate Flow Estimation) pour interpoler      ║
║  les frames et obtenir un mouvement fluide à 120 FPS                        ║
║  Fallback FFmpeg (minterpolate) si RIFE non disponible                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
import json


class RIFEInterpolator:
    """Interpolateur de frames via RIFE ou FFmpeg fallback."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_gpu: bool = True,
        verbose: bool = False
    ):
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.verbose = verbose
        self._rife_available = self._check_rife_available()
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[RIFE] {msg}")
    
    def _check_rife_available(self) -> bool:
        """Vérifie si RIFE est disponible."""
        if not self.model_path:
            return False
        
        model_path = Path(self.model_path)
        if not model_path.exists():
            return False
        
        flownet_files = list(model_path.glob("*.pkl")) + list(model_path.glob("*.pth"))
        if not flownet_files:
            self._log("Aucun modèle RIFE trouvé (*.pkl, *.pth)")
            return False
        
        try:
            import torch
            self._log(f"PyTorch disponible, GPU: {torch.cuda.is_available()}")
            return True
        except ImportError:
            self._log("PyTorch non disponible")
            return False
    
    def get_video_info(self, video_path: Path) -> Optional[dict]:
        """Récupère les informations d'une vidéo."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
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
                    "frames": int(stream.get("nb_frames", 0) or 0)
                }
        except Exception as e:
            self._log(f"Erreur FFprobe: {e}")
        
        return None
    
    def interpolate(
        self,
        input_video: Path,
        output_video: Path,
        target_fps: int = 120,
        scale: float = 1.0
    ) -> bool:
        """
        Interpole une vidéo vers un FPS cible via RIFE.
        
        Args:
            input_video: Vidéo source
            output_video: Vidéo interpolée
            target_fps: FPS cible (défaut: 120)
            scale: Facteur d'échelle pour traitement (0.5 = demi-résolution)
        
        Returns:
            True si succès
        """
        if not self._rife_available:
            self._log("RIFE non disponible, utilisation du fallback FFmpeg")
            return self.interpolate_ffmpeg_fallback(input_video, output_video, target_fps)
        
        video_info = self.get_video_info(input_video)
        if not video_info:
            self._log("Impossible de lire les infos vidéo")
            return False
        
        source_fps = video_info.get("fps", 30)
        multiplier = target_fps / source_fps
        
        exp = 0
        while (2 ** exp) < multiplier:
            exp += 1
        
        self._log(f"Source: {source_fps} FPS → Target: {target_fps} FPS (exp={exp})")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import torch
            import numpy as np
            from PIL import Image
            import cv2
            
            device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")
            self._log(f"Device: {device}")
            
            model = self._load_rife_model(device)
            if model is None:
                self._log("Échec chargement modèle RIFE, fallback FFmpeg")
                return self.interpolate_ffmpeg_fallback(input_video, output_video, target_fps)
            
            temp_dir = output_video.parent / "_temp_rife"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                frames_dir = temp_dir / "frames"
                interp_dir = temp_dir / "interpolated"
                frames_dir.mkdir(exist_ok=True)
                interp_dir.mkdir(exist_ok=True)
                
                self._log("Extraction frames...")
                self._extract_frames(input_video, frames_dir)
                
                self._log(f"Interpolation RIFE (exp={exp})...")
                self._rife_interpolate_frames(model, frames_dir, interp_dir, exp, device, scale)
                
                self._log("Assemblage vidéo finale...")
                self._frames_to_video(interp_dir, output_video, target_fps)
                
                return output_video.exists()
                
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except ImportError as e:
            self._log(f"Dépendance manquante: {e}")
            return self.interpolate_ffmpeg_fallback(input_video, output_video, target_fps)
        except Exception as e:
            self._log(f"Erreur RIFE: {e}")
            return self.interpolate_ffmpeg_fallback(input_video, output_video, target_fps)
    
    def _load_rife_model(self, device):
        """Charge le modèle RIFE."""
        try:
            import torch
            import sys
            
            model_path = Path(self.model_path)
            
            if str(model_path) not in sys.path:
                sys.path.insert(0, str(model_path))
            
            try:
                from model.RIFE import Model
                model = Model()
                model.load_model(str(model_path), -1)
                model.eval()
                model.device()
                return model
            except ImportError:
                pass
            
            try:
                from RIFE_HDv3 import Model
                model = Model()
                model.load_model(str(model_path), -1)
                model.eval()
                model.device()
                return model
            except ImportError:
                pass
            
            self._log("Aucun modèle RIFE compatible trouvé")
            return None
            
        except Exception as e:
            self._log(f"Erreur chargement modèle: {e}")
            return None
    
    def _extract_frames(self, video_path: Path, output_dir: Path):
        """Extrait les frames d'une vidéo."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-qscale:v", "2",
            str(output_dir / "frame_%08d.png")
        ]
        subprocess.run(cmd, capture_output=True, timeout=600)
    
    def _rife_interpolate_frames(self, model, input_dir, output_dir, exp, device, scale):
        """Interpole les frames via RIFE."""
        import torch
        import numpy as np
        from PIL import Image
        
        frame_files = sorted(input_dir.glob("*.png"))
        
        with torch.no_grad():
            for i in range(len(frame_files) - 1):
                frame0 = self._load_frame(frame_files[i], device, scale)
                frame1 = self._load_frame(frame_files[i + 1], device, scale)
                
                output_idx = i * (2 ** exp)
                self._save_frame(frame0, output_dir / f"frame_{output_idx:08d}.png", scale)
                
                self._interpolate_pair(model, frame0, frame1, output_dir, output_idx, exp, scale)
            
            final_idx = (len(frame_files) - 1) * (2 ** exp)
            self._save_frame(frame1, output_dir / f"frame_{final_idx:08d}.png", scale)
    
    def _load_frame(self, path, device, scale):
        """Charge une frame et la prépare pour RIFE."""
        import torch
        import numpy as np
        from PIL import Image
        
        img = Image.open(path).convert('RGB')
        
        if scale != 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)
        
        img_np = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).to(device)
        
        return img_tensor
    
    def _save_frame(self, tensor, path, scale):
        """Sauvegarde une frame."""
        import torch
        import numpy as np
        from PIL import Image
        
        img_np = (tensor.squeeze().permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_np)
        
        if scale != 1.0:
            new_size = (int(img.width / scale), int(img.height / scale))
            img = img.resize(new_size, Image.LANCZOS)
        
        img.save(path)
    
    def _interpolate_pair(self, model, frame0, frame1, output_dir, base_idx, exp, scale):
        """Interpole récursivement entre deux frames."""
        import torch
        
        if exp == 0:
            return
        
        mid = model.inference(frame0, frame1, scale=scale)
        mid_idx = base_idx + (2 ** (exp - 1))
        
        self._save_frame(mid, output_dir / f"frame_{mid_idx:08d}.png", scale)
        
        self._interpolate_pair(model, frame0, mid, output_dir, base_idx, exp - 1, scale)
        self._interpolate_pair(model, mid, frame1, output_dir, mid_idx, exp - 1, scale)
    
    def _frames_to_video(self, frames_dir, output_path, fps):
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
        subprocess.run(cmd, capture_output=True, timeout=600)
    
    def interpolate_ffmpeg_fallback(
        self,
        input_video: Path,
        output_video: Path,
        target_fps: int = 120
    ) -> bool:
        """
        Interpolation via FFmpeg minterpolate (qualité inférieure à RIFE).
        
        Args:
            input_video: Vidéo source
            output_video: Vidéo interpolée
            target_fps: FPS cible
        
        Returns:
            True si succès
        """
        self._log(f"FFmpeg minterpolate: {target_fps} FPS")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vf", f"minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps={target_fps}'",
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
                timeout=1800
            )
            
            if result.returncode != 0:
                self._log(f"FFmpeg minterpolate échoué: {result.stderr[-500:]}")
                return self._simple_fps_convert(input_video, output_video, target_fps)
            
            return output_video.exists()
            
        except subprocess.TimeoutExpired:
            self._log("Timeout FFmpeg minterpolate")
            return False
        except Exception as e:
            self._log(f"Erreur FFmpeg: {e}")
            return False
    
    def _simple_fps_convert(
        self,
        input_video: Path,
        output_video: Path,
        target_fps: int
    ) -> bool:
        """Conversion simple de FPS (frame duplication)."""
        self._log(f"Simple FPS convert: {target_fps} FPS (frame duplication)")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-r", str(target_fps),
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(output_video)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return result.returncode == 0 and output_video.exists()
        except Exception as e:
            self._log(f"Erreur: {e}")
            return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python rife_interpolator.py <input.mp4> <output.mp4> [target_fps] [model_path]")
        print("  input.mp4: Vidéo source")
        print("  output.mp4: Vidéo interpolée")
        print("  target_fps: FPS cible (défaut: 120)")
        print("  model_path: Chemin vers le modèle RIFE (optionnel)")
        sys.exit(1)
    
    input_video = Path(sys.argv[1])
    output_video = Path(sys.argv[2])
    target_fps = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    model_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    rife = RIFEInterpolator(model_path=model_path, verbose=True)
    
    if model_path:
        success = rife.interpolate(input_video, output_video, target_fps)
    else:
        success = rife.interpolate_ffmpeg_fallback(input_video, output_video, target_fps)
    
    sys.exit(0 if success else 1)
