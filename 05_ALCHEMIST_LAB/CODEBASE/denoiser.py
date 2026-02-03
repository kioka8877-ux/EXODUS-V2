#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DENOISER — EXODUS ALCHEMIST LAB                           ║
║                  OptiX Denoiser • OIDN • AI-Based Denoising                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module de denoising pour supprimer le bruit Monte Carlo des rendus.

Backends supportés:
- OptiX Denoiser (NVIDIA GPU, optimal)
- OpenImageDenoise (Intel OIDN, CPU fallback)
- Blender Compositor Denoise Node (universel)

Le module détecte automatiquement le meilleur backend disponible.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DenoiserBackend(Enum):
    """Backends de denoising disponibles."""
    OPTIX = "optix"
    OIDN = "oidn"
    BLENDER = "blender"
    NONE = "none"


@dataclass
class DenoiseConfig:
    """Configuration du denoiser."""
    enabled: bool = True
    backend: DenoiserBackend = DenoiserBackend.BLENDER
    strength: float = 1.0
    preserve_detail: float = 0.5
    use_hdr: bool = True
    use_albedo: bool = False
    use_normal: bool = False
    prefilter: str = "FAST"


@dataclass
class DenoiseResult:
    """Résultat du denoising."""
    success: bool
    backend_used: DenoiserBackend
    frames_processed: int
    average_time_per_frame: float
    error_message: str = ""


class DenoiserDetector:
    """Détecte les backends de denoising disponibles."""
    
    @staticmethod
    def detect_cuda() -> bool:
        """Vérifie si CUDA est disponible."""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def detect_optix() -> bool:
        """Vérifie si OptiX est disponible (NVIDIA RTX)."""
        if not DenoiserDetector.detect_cuda():
            return False
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10
            )
            gpu_name = result.stdout.lower()
            rtx_keywords = ["rtx", "quadro rtx", "titan rtx", "geforce rtx"]
            return any(kw in gpu_name for kw in rtx_keywords)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def detect_oidn() -> bool:
        """Vérifie si OpenImageDenoise est disponible."""
        try:
            result = subprocess.run(
                ["oidnDenoise", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 or "oidn" in result.stdout.lower()
        except FileNotFoundError:
            pass
        
        try:
            import oidn
            return True
        except ImportError:
            pass
        
        return False
    
    @staticmethod
    def detect_blender(blender_path: Optional[str] = None) -> bool:
        """Vérifie si Blender est disponible."""
        paths_to_try = [blender_path] if blender_path else []
        paths_to_try.extend([
            "blender",
            "/usr/bin/blender",
            "/opt/blender/blender"
        ])
        
        for path in paths_to_try:
            if path is None:
                continue
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return False
    
    @staticmethod
    def get_best_backend(blender_path: Optional[str] = None) -> DenoiserBackend:
        """Retourne le meilleur backend disponible."""
        if DenoiserDetector.detect_optix():
            print("[DENOISER] OptiX disponible (GPU NVIDIA RTX)")
            return DenoiserBackend.OPTIX
        
        if DenoiserDetector.detect_oidn():
            print("[DENOISER] OIDN disponible (CPU)")
            return DenoiserBackend.OIDN
        
        if DenoiserDetector.detect_blender(blender_path):
            print("[DENOISER] Blender Compositor disponible")
            return DenoiserBackend.BLENDER
        
        print("[DENOISER:WARN] Aucun backend de denoising disponible")
        return DenoiserBackend.NONE
    
    @staticmethod
    def get_available_backends(blender_path: Optional[str] = None) -> List[DenoiserBackend]:
        """Retourne la liste de tous les backends disponibles."""
        available = []
        
        if DenoiserDetector.detect_optix():
            available.append(DenoiserBackend.OPTIX)
        
        if DenoiserDetector.detect_oidn():
            available.append(DenoiserBackend.OIDN)
        
        if DenoiserDetector.detect_blender(blender_path):
            available.append(DenoiserBackend.BLENDER)
        
        return available


class Denoiser:
    """Moteur de denoising multi-backend."""
    
    def __init__(self, blender_path: Optional[str] = None):
        """
        Initialise le denoiser.
        
        Args:
            blender_path: Chemin vers l'exécutable Blender (optionnel)
        """
        self.blender_path = blender_path
        self.available_backends = DenoiserDetector.get_available_backends(blender_path)
        self.preferred_backend = DenoiserDetector.get_best_backend(blender_path)
    
    def get_blender_denoise_params(self, config: DenoiseConfig) -> dict:
        """
        Génère les paramètres pour le Blender Denoise node.
        
        Args:
            config: Configuration de denoising
            
        Returns:
            Dict de paramètres pour le node Blender
        """
        return {
            "use_hdr": config.use_hdr,
            "prefilter": config.prefilter
        }
    
    def denoise_with_blender(
        self,
        input_path: str,
        output_path: str,
        config: DenoiseConfig
    ) -> bool:
        """
        Denoise une image via Blender Compositor.
        
        Args:
            input_path: Chemin vers l'image source
            output_path: Chemin de sortie
            config: Configuration
            
        Returns:
            True si succès
        """
        if not self.blender_path:
            print("[DENOISER:ERROR] Chemin Blender non configuré")
            return False
        
        script = f'''
import bpy

bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree

for node in tree.nodes:
    tree.nodes.remove(node)

image_node = tree.nodes.new('CompositorNodeImage')
img = bpy.data.images.load("{input_path}")
image_node.image = img
image_node.location = (-400, 0)

denoise_node = tree.nodes.new('CompositorNodeDenoise')
denoise_node.location = (0, 0)
denoise_node.use_hdr = {str(config.use_hdr)}
denoise_node.prefilter = "{config.prefilter}"

output_node = tree.nodes.new('CompositorNodeOutputFile')
output_node.location = (400, 0)
output_node.base_path = "{Path(output_path).parent}"
output_node.file_slots[0].path = "{Path(output_path).stem}"
output_node.format.file_format = 'OPEN_EXR'

tree.links.new(image_node.outputs['Image'], denoise_node.inputs['Image'])
tree.links.new(denoise_node.outputs['Image'], output_node.inputs[0])

bpy.context.scene.frame_set(1)
bpy.ops.render.render(write_still=False)
print("[DENOISER] Frame denoised successfully")
'''
        
        try:
            result = subprocess.run(
                [self.blender_path, "--background", "--python-expr", script],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("[DENOISER:ERROR] Blender timeout")
            return False
    
    def denoise_with_oidn_cli(
        self,
        input_path: str,
        output_path: str,
        config: DenoiseConfig
    ) -> bool:
        """
        Denoise une image via OIDN CLI.
        
        Args:
            input_path: Chemin vers l'image source
            output_path: Chemin de sortie
            config: Configuration
            
        Returns:
            True si succès
        """
        cmd = [
            "oidnDenoise",
            "--hdr" if config.use_hdr else "",
            "-i", input_path,
            "-o", output_path
        ]
        
        cmd = [c for c in cmd if c]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def create_denoise_node_config(self, config: DenoiseConfig) -> dict:
        """
        Crée la configuration pour un Blender Denoise node.
        Utilisé par compositor_pipeline.py.
        
        Args:
            config: Configuration de denoising
            
        Returns:
            Dict avec les paramètres du node
        """
        node_config = {
            "type": "CompositorNodeDenoise",
            "name": "Denoiser",
            "params": {
                "use_hdr": config.use_hdr,
                "prefilter": config.prefilter
            }
        }
        
        if config.backend == DenoiserBackend.OPTIX and DenoiserBackend.OPTIX in self.available_backends:
            node_config["params"]["use_gpu"] = True
        
        return node_config
    
    def get_status(self) -> dict:
        """Retourne le statut du denoiser."""
        return {
            "available_backends": [b.value for b in self.available_backends],
            "preferred_backend": self.preferred_backend.value,
            "cuda_available": DenoiserDetector.detect_cuda(),
            "optix_available": DenoiserBackend.OPTIX in self.available_backends,
            "oidn_available": DenoiserBackend.OIDN in self.available_backends,
            "blender_available": DenoiserBackend.BLENDER in self.available_backends
        }


def get_optimal_denoise_config(
    has_albedo: bool = False,
    has_normal: bool = False,
    is_animation: bool = True
) -> DenoiseConfig:
    """
    Génère une configuration de denoising optimale selon le contexte.
    
    Args:
        has_albedo: True si les passes Albedo sont disponibles
        has_normal: True si les passes Normal sont disponibles
        is_animation: True si c'est une séquence animée
        
    Returns:
        DenoiseConfig optimisée
    """
    config = DenoiseConfig(
        enabled=True,
        use_hdr=True,
        use_albedo=has_albedo,
        use_normal=has_normal
    )
    
    if is_animation:
        config.prefilter = "ACCURATE"
        config.preserve_detail = 0.6
    else:
        config.prefilter = "FAST"
        config.preserve_detail = 0.5
    
    backend = DenoiserDetector.get_best_backend()
    config.backend = backend
    
    return config


def validate_exr_for_denoise(exr_path: str) -> dict:
    """
    Valide qu'un fichier EXR est adapté au denoising.
    
    Args:
        exr_path: Chemin vers le fichier EXR
        
    Returns:
        Dict avec les informations de validation
    """
    result = {
        "valid": False,
        "has_color": False,
        "has_albedo": False,
        "has_normal": False,
        "has_depth": False,
        "channels": [],
        "error": ""
    }
    
    if not Path(exr_path).exists():
        result["error"] = "Fichier introuvable"
        return result
    
    try:
        import OpenEXR
        import Imath
        
        exr_file = OpenEXR.InputFile(exr_path)
        header = exr_file.header()
        
        channels = list(header.get('channels', {}).keys())
        result["channels"] = channels
        
        color_channels = ['R', 'G', 'B', 'Image.R', 'Image.G', 'Image.B', 'Combined.R']
        result["has_color"] = any(c in channels for c in color_channels)
        
        albedo_channels = ['Albedo.R', 'Albedo.G', 'Albedo.B', 'DiffCol.R']
        result["has_albedo"] = any(c in channels for c in albedo_channels)
        
        normal_channels = ['Normal.X', 'Normal.Y', 'Normal.Z', 'N.X']
        result["has_normal"] = any(c in channels for c in normal_channels)
        
        depth_channels = ['Depth.Z', 'Z', 'Depth']
        result["has_depth"] = any(c in channels for c in depth_channels)
        
        result["valid"] = result["has_color"]
        
        exr_file.close()
        
    except ImportError:
        result["valid"] = Path(exr_path).suffix.lower() == '.exr'
        result["error"] = "OpenEXR non disponible - validation basique"
    except Exception as e:
        result["error"] = str(e)
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("   DENOISER — EXODUS ALCHEMIST LAB")
    print("=" * 60)
    
    print("\n=== Détection des Backends ===")
    
    detector = DenoiserDetector()
    
    cuda = detector.detect_cuda()
    print(f"  CUDA: {'✓ Disponible' if cuda else '✗ Non disponible'}")
    
    optix = detector.detect_optix()
    print(f"  OptiX: {'✓ Disponible' if optix else '✗ Non disponible'}")
    
    oidn = detector.detect_oidn()
    print(f"  OIDN: {'✓ Disponible' if oidn else '✗ Non disponible'}")
    
    blender = detector.detect_blender()
    print(f"  Blender: {'✓ Disponible' if blender else '✗ Non disponible'}")
    
    best = detector.get_best_backend()
    print(f"\n  → Backend recommandé: {best.value}")
    
    print("\n=== Configuration Optimale ===")
    config = get_optimal_denoise_config(has_albedo=False, has_normal=False, is_animation=True)
    print(f"  Backend: {config.backend.value}")
    print(f"  HDR: {config.use_hdr}")
    print(f"  Prefilter: {config.prefilter}")
    print(f"  Preserve Detail: {config.preserve_detail}")
    
    if len(sys.argv) > 1:
        exr_path = sys.argv[1]
        print(f"\n=== Validation EXR: {exr_path} ===")
        validation = validate_exr_for_denoise(exr_path)
        print(f"  Valid: {validation['valid']}")
        print(f"  Color: {validation['has_color']}")
        print(f"  Albedo: {validation['has_albedo']}")
        print(f"  Normal: {validation['has_normal']}")
        if validation['error']:
            print(f"  Error: {validation['error']}")
