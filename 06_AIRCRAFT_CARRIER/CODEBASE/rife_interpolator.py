#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RIFE INTERPOLATOR — EXODUS CARRIER V2                     ║
║              Interpolation temporelle chunk-based frame-to-frame            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Travaille directement sur des frames PNG — aucune vidéo intermédiaire     ║
║  lossy. Les fallbacks (minterpolate) utilisent des codecs LOSSLESS.        ║
║  ZÉRO libx264 dans ce module.                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import json


class RIFEInterpolator:
    """Interpolateur de frames via RIFE ou FFmpeg fallback (chunk-based)."""

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
        """Récupère les informations d'une vidéo (gardé pour rétrocompatibilité)."""
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
            self._log(f"Erreur FFprobe frame info: {e}")

        return {"width": 0, "height": 0}

    def interpolate_chunk(
        self,
        input_frames: List[Path],
        output_dir: Path,
        target_fps: int = 120,
        source_fps: int = 30,
    ) -> List[Path]:
        """Interpole un chunk de frames via RIFE.

        Lit directement les PNG sources.
        Écrit les PNG interpolées dans output_dir.
        Retourne la liste des frames interpolées triées.
        Ne crée AUCUNE vidéo intermédiaire.
        """
        if not input_frames:
            return []

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        multiplier = target_fps // source_fps if source_fps > 0 else 4
        if multiplier < 1:
            multiplier = 1

        exp = 0
        while (2 ** exp) < multiplier:
            exp += 1

        self._log(f"Chunk: {len(input_frames)} frames, {source_fps}→{target_fps} FPS (exp={exp}, mult={multiplier})")

        if self._rife_available:
            result = self._interpolate_chunk_rife(input_frames, output_dir, exp)
            if result:
                return result
            self._log("RIFE échoué, fallback minterpolate")

        result = self._interpolate_chunk_minterpolate(input_frames, output_dir, target_fps, source_fps)
        if result:
            return result

        self._log("minterpolate échoué, fallback frame duplication")
        return self._interpolate_chunk_duplication(input_frames, output_dir, multiplier)

    def _interpolate_chunk_rife(
        self,
        input_frames: List[Path],
        output_dir: Path,
        exp: int,
        scale: float = 1.0
    ) -> Optional[List[Path]]:
        """Interpole un chunk via RIFE directement frame-to-frame."""
        try:
            import torch
            import numpy as np
            from PIL import Image

            device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")
            self._log(f"RIFE device: {device}")

            model = self._load_rife_model(device)
            if model is None:
                return None

            with torch.no_grad():
                output_files = []

                for i in range(len(input_frames) - 1):
                    frame0 = self._load_frame(input_frames[i], device, scale)
                    frame1 = self._load_frame(input_frames[i + 1], device, scale)

                    base_idx = i * (2 ** exp)
                    out_path = output_dir / f"frame_{base_idx:08d}.png"
                    self._save_frame(frame0, out_path, scale)
                    output_files.append(out_path)

                    interp_frames = self._interpolate_pair_collect(model, frame0, frame1, output_dir, base_idx, exp, scale)
                    output_files.extend(interp_frames)

                final_idx = (len(input_frames) - 1) * (2 ** exp)
                out_path = output_dir / f"frame_{final_idx:08d}.png"
                self._save_frame(
                    self._load_frame(input_frames[-1], device, scale),
                    out_path, scale
                )
                output_files.append(out_path)

            return sorted(output_files)

        except ImportError as e:
            self._log(f"Dépendance manquante: {e}")
            return None
        except Exception as e:
            self._log(f"Erreur RIFE chunk: {e}")
            return None

    def _interpolate_chunk_minterpolate(
        self,
        input_frames: List[Path],
        output_dir: Path,
        target_fps: int,
        source_fps: int
    ) -> Optional[List[Path]]:
        """Fallback minterpolate — passe par vidéo LOSSLESS temporaire."""
        self._log(f"FFmpeg minterpolate fallback: {source_fps}→{target_fps} FPS")

        temp_dir = output_dir.parent / f"_temp_minterp_{output_dir.name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            staging_dir = temp_dir / "staged"
            staging_dir.mkdir(exist_ok=True)
            for i, frame in enumerate(input_frames):
                dst = staging_dir / f"frame_{i:08d}.png"
                shutil.copy2(str(frame), str(dst))

            lossless_input = temp_dir / "lossless_input.mkv"
            cmd_encode = [
                "ffmpeg", "-y",
                "-framerate", str(source_fps),
                "-i", str(staging_dir / "frame_%08d.png"),
                "-c:v", "ffv1",
                "-level", "3",
                "-pix_fmt", "rgb24",
                str(lossless_input)
            ]
            result = subprocess.run(cmd_encode, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                self._log(f"Encodage lossless échoué: {result.stderr[-300:]}")
                return None

            lossless_output = temp_dir / "lossless_output.mkv"
            cmd_interp = [
                "ffmpeg", "-y",
                "-i", str(lossless_input),
                "-vf", f"minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps={target_fps}'",
                "-c:v", "ffv1",
                "-level", "3",
                "-pix_fmt", "rgb24",
                str(lossless_output)
            ]
            result = subprocess.run(cmd_interp, capture_output=True, text=True, timeout=1800)
            if result.returncode != 0:
                self._log(f"minterpolate échoué: {result.stderr[-300:]}")
                return None

            cmd_extract = [
                "ffmpeg", "-y",
                "-i", str(lossless_output),
                str(output_dir / "frame_%08d.png")
            ]
            result = subprocess.run(cmd_extract, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                self._log(f"Extraction frames échouée: {result.stderr[-300:]}")
                return None

            output_files = sorted(output_dir.glob("frame_*.png"))
            self._log(f"minterpolate: {len(output_files)} frames produites")
            return output_files if output_files else None

        except subprocess.TimeoutExpired:
            self._log("Timeout minterpolate")
            return None
        except Exception as e:
            self._log(f"Erreur minterpolate: {e}")
            return None
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _interpolate_chunk_duplication(
        self,
        input_frames: List[Path],
        output_dir: Path,
        multiplier: int
    ) -> List[Path]:
        """Fallback simple : duplication de frames (aucune vidéo intermédiaire)."""
        self._log(f"Frame duplication fallback: x{multiplier}")

        output_files = []
        global_idx = 0

        for frame_path in input_frames:
            for _ in range(multiplier):
                out_path = output_dir / f"frame_{global_idx:08d}.png"
                shutil.copy2(str(frame_path), str(out_path))
                output_files.append(out_path)
                global_idx += 1

        self._log(f"Duplication: {len(output_files)} frames produites")
        return output_files

    def _load_rife_model(self, device):
        """Charge le modèle RIFE."""
        try:
            import torch
            import sys as _sys

            model_path = Path(self.model_path)

            if str(model_path) not in _sys.path:
                _sys.path.insert(0, str(model_path))

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
        import numpy as np
        from PIL import Image

        img_np = (tensor.squeeze().permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_np)

        if scale != 1.0:
            new_size = (int(img.width / scale), int(img.height / scale))
            img = img.resize(new_size, Image.LANCZOS)

        img.save(path)

    def _interpolate_pair_collect(self, model, frame0, frame1, output_dir, base_idx, exp, scale):
        """Interpole récursivement entre deux frames et collecte les résultats."""
        results = []
        self._interpolate_pair_recursive(model, frame0, frame1, output_dir, base_idx, exp, scale, results)
        return results

    def _interpolate_pair_recursive(self, model, frame0, frame1, output_dir, base_idx, exp, scale, results):
        """Interpole récursivement entre deux frames."""
        if exp == 0:
            return

        mid = model.inference(frame0, frame1, scale=scale)
        mid_idx = base_idx + (2 ** (exp - 1))

        out_path = output_dir / f"frame_{mid_idx:08d}.png"
        self._save_frame(mid, out_path, scale)
        results.append(out_path)

        self._interpolate_pair_recursive(model, frame0, mid, output_dir, base_idx, exp - 1, scale, results)
        self._interpolate_pair_recursive(model, mid, frame1, output_dir, mid_idx, exp - 1, scale, results)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python rife_interpolator.py <input_dir> <output_dir> [target_fps] [source_fps] [model_path]")
        print("  input_dir: Dossier de frames PNG source")
        print("  output_dir: Dossier de frames PNG interpolées")
        print("  target_fps: FPS cible (défaut: 120)")
        print("  source_fps: FPS source (défaut: 30)")
        print("  model_path: Chemin vers le modèle RIFE (optionnel)")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    target_fps = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    source_fps = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    model_path = sys.argv[5] if len(sys.argv) > 5 else None

    input_frames = sorted(input_dir.glob("*.png"))
    if not input_frames:
        print(f"Aucune frame PNG dans {input_dir}")
        sys.exit(1)

    rife = RIFEInterpolator(model_path=model_path, verbose=True)
    result = rife.interpolate_chunk(input_frames, output_dir, target_fps, source_fps)

    print(f"Frames interpolées: {len(result)}")
    sys.exit(0 if result else 1)
