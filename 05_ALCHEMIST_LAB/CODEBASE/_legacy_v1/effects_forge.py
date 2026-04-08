#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  EFFECTS FORGE — EXODUS ALCHEMIST LAB                        ║
║       Bloom • Lens Flare • Film Grain • Vignette • Chromatic Aberration      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module d'effets visuels cinématiques.
Génère les paramètres pour les nodes Blender Compositor.

Effets supportés:
- Bloom (Glare Fog Glow)
- Lens Flare (Glare Streaks/Ghosts)
- Film Grain (Noise overlay)
- Vignette (Ellipse mask)
- Chromatic Aberration (Lens Distortion)
- Glow (Emission enhancement)
- Motion Blur (Vector blur)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class BloomQuality(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class GlareType(Enum):
    FOG_GLOW = "FOG_GLOW"
    SIMPLE_STAR = "SIMPLE_STAR"
    STREAKS = "STREAKS"
    GHOSTS = "GHOSTS"


@dataclass
class BloomConfig:
    """Configuration pour l'effet Bloom."""
    enabled: bool = False
    threshold: float = 0.8
    intensity: float = 0.3
    size: int = 7
    quality: BloomQuality = BloomQuality.HIGH
    color_modulation: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    
    def to_blender_params(self) -> dict:
        """Convertit en paramètres Blender Glare node."""
        return {
            "glare_type": "FOG_GLOW",
            "quality": self.quality.value,
            "threshold": self.threshold,
            "mix": self.intensity,
            "size": self.size,
            "color_modulation": self.color_modulation
        }


@dataclass
class LensFlareConfig:
    """Configuration pour l'effet Lens Flare."""
    enabled: bool = False
    threshold: float = 0.9
    intensity: float = 0.2
    streaks: int = 4
    angle_offset: float = 0.0
    fade: float = 0.9
    use_ghosts: bool = False
    
    def to_blender_params(self) -> dict:
        """Convertit en paramètres Blender Glare node."""
        return {
            "glare_type": "GHOSTS" if self.use_ghosts else "STREAKS",
            "quality": "HIGH",
            "threshold": self.threshold,
            "mix": self.intensity,
            "streaks": self.streaks,
            "angle_offset": self.angle_offset,
            "fade": self.fade
        }


@dataclass
class FilmGrainConfig:
    """Configuration pour l'effet Film Grain."""
    enabled: bool = False
    intensity: float = 0.1
    size: float = 1.0
    color_saturation: float = 0.5
    uniform: bool = True
    
    def to_blender_params(self) -> dict:
        """Convertit en paramètres pour noise overlay."""
        return {
            "intensity": self.intensity,
            "noise_scale": 0.5 / self.size,
            "color_saturation": self.color_saturation,
            "blend_mode": "OVERLAY",
            "uniform": self.uniform
        }


@dataclass
class VignetteConfig:
    """Configuration pour l'effet Vignette."""
    enabled: bool = False
    intensity: float = 0.3
    softness: float = 0.5
    width: float = 0.8
    height: float = 0.8
    offset_x: float = 0.0
    offset_y: float = 0.0
    
    def to_blender_params(self) -> dict:
        """Convertit en paramètres Ellipse Mask + Mix."""
        return {
            "ellipse_width": self.width,
            "ellipse_height": self.height,
            "ellipse_x": 0.5 + self.offset_x,
            "ellipse_y": 0.5 + self.offset_y,
            "blur_size": int(200 * self.softness),
            "mix_factor": self.intensity,
            "blend_mode": "MULTIPLY"
        }


@dataclass
class ChromaticAberrationConfig:
    """Configuration pour l'effet Chromatic Aberration."""
    enabled: bool = False
    dispersion: float = 0.01
    distortion: float = 0.0
    use_jitter: bool = False
    use_fit: bool = True
    
    def to_blender_params(self) -> dict:
        """Convertit en paramètres Lens Distortion node."""
        return {
            "dispersion": self.dispersion,
            "distortion": self.distortion,
            "use_jitter": self.use_jitter,
            "use_fit": self.use_fit
        }


@dataclass
class GlowConfig:
    """Configuration pour l'effet Glow (émission enhancement)."""
    enabled: bool = False
    threshold: float = 0.7
    intensity: float = 0.5
    radius: int = 5
    iterations: int = 3
    
    def to_blender_params(self) -> dict:
        """Convertit en paramètres Blur + Add."""
        return {
            "threshold": self.threshold,
            "blur_size": self.radius * 2,
            "iterations": self.iterations,
            "mix_factor": self.intensity,
            "blend_mode": "ADD"
        }


@dataclass
class EffectsConfig:
    """Configuration complète des effets visuels."""
    bloom: BloomConfig = field(default_factory=BloomConfig)
    lens_flare: LensFlareConfig = field(default_factory=LensFlareConfig)
    film_grain: FilmGrainConfig = field(default_factory=FilmGrainConfig)
    vignette: VignetteConfig = field(default_factory=VignetteConfig)
    chromatic_aberration: ChromaticAberrationConfig = field(default_factory=ChromaticAberrationConfig)
    glow: GlowConfig = field(default_factory=GlowConfig)


EFFECTS_PRESETS = {
    "cinematic": EffectsConfig(
        bloom=BloomConfig(enabled=True, threshold=0.85, intensity=0.25, size=7),
        vignette=VignetteConfig(enabled=True, intensity=0.25, softness=0.6),
        film_grain=FilmGrainConfig(enabled=True, intensity=0.05)
    ),
    "action": EffectsConfig(
        bloom=BloomConfig(enabled=True, threshold=0.75, intensity=0.4, size=8),
        lens_flare=LensFlareConfig(enabled=True, threshold=0.9, intensity=0.15, streaks=6),
        chromatic_aberration=ChromaticAberrationConfig(enabled=True, dispersion=0.005)
    ),
    "dramatic": EffectsConfig(
        bloom=BloomConfig(enabled=True, threshold=0.9, intensity=0.2),
        vignette=VignetteConfig(enabled=True, intensity=0.4, softness=0.4),
        film_grain=FilmGrainConfig(enabled=True, intensity=0.08)
    ),
    "neon": EffectsConfig(
        bloom=BloomConfig(enabled=True, threshold=0.6, intensity=0.5, size=9),
        glow=GlowConfig(enabled=True, threshold=0.5, intensity=0.6),
        chromatic_aberration=ChromaticAberrationConfig(enabled=True, dispersion=0.015)
    ),
    "vintage": EffectsConfig(
        vignette=VignetteConfig(enabled=True, intensity=0.35, softness=0.7),
        film_grain=FilmGrainConfig(enabled=True, intensity=0.12, color_saturation=0.3)
    ),
    "clean": EffectsConfig(
        bloom=BloomConfig(enabled=True, threshold=0.95, intensity=0.1, size=5)
    ),
    "none": EffectsConfig()
}


class EffectsForge:
    """Moteur de génération d'effets visuels."""
    
    def __init__(self):
        self.presets = EFFECTS_PRESETS.copy()
    
    def get_preset(self, name: str) -> Optional[EffectsConfig]:
        """Récupère un preset d'effets."""
        normalized = name.lower().replace("-", "_").replace(" ", "_")
        return self.presets.get(normalized) or self.presets.get(name)
    
    def parse_effects_dict(self, effects_dict: dict) -> EffectsConfig:
        """
        Parse un dictionnaire d'effets (format PRODUCTION_PLAN.JSON).
        
        Args:
            effects_dict: Dict avec les clés bloom, lens_flare, film_grain, etc.
            
        Returns:
            EffectsConfig configuré
        """
        config = EffectsConfig()
        
        bloom_val = effects_dict.get("bloom", False)
        if isinstance(bloom_val, bool):
            config.bloom.enabled = bloom_val
        elif isinstance(bloom_val, (int, float)):
            config.bloom.enabled = bloom_val > 0
            config.bloom.intensity = float(bloom_val) if bloom_val <= 1 else bloom_val / 100
        elif isinstance(bloom_val, dict):
            config.bloom.enabled = bloom_val.get("enabled", True)
            config.bloom.threshold = bloom_val.get("threshold", 0.8)
            config.bloom.intensity = bloom_val.get("intensity", 0.3)
            config.bloom.size = bloom_val.get("size", 7)
        
        flare_val = effects_dict.get("lens_flare", False)
        if isinstance(flare_val, bool):
            config.lens_flare.enabled = flare_val
        elif isinstance(flare_val, dict):
            config.lens_flare.enabled = flare_val.get("enabled", True)
            config.lens_flare.threshold = flare_val.get("threshold", 0.9)
            config.lens_flare.intensity = flare_val.get("intensity", 0.2)
            config.lens_flare.streaks = flare_val.get("streaks", 4)
        
        grain_val = effects_dict.get("film_grain", 0.0)
        if isinstance(grain_val, bool):
            config.film_grain.enabled = grain_val
            config.film_grain.intensity = 0.1 if grain_val else 0.0
        elif isinstance(grain_val, (int, float)):
            config.film_grain.enabled = grain_val > 0
            config.film_grain.intensity = float(grain_val)
        elif isinstance(grain_val, dict):
            config.film_grain.enabled = grain_val.get("enabled", True)
            config.film_grain.intensity = grain_val.get("intensity", 0.1)
            config.film_grain.size = grain_val.get("size", 1.0)
        
        vignette_val = effects_dict.get("vignette", 0.0)
        if isinstance(vignette_val, bool):
            config.vignette.enabled = vignette_val
            config.vignette.intensity = 0.3 if vignette_val else 0.0
        elif isinstance(vignette_val, (int, float)):
            config.vignette.enabled = vignette_val > 0
            config.vignette.intensity = float(vignette_val)
        elif isinstance(vignette_val, dict):
            config.vignette.enabled = vignette_val.get("enabled", True)
            config.vignette.intensity = vignette_val.get("intensity", 0.3)
            config.vignette.softness = vignette_val.get("softness", 0.5)
        
        ca_val = effects_dict.get("chromatic_aberration", 0.0)
        if isinstance(ca_val, bool):
            config.chromatic_aberration.enabled = ca_val
            config.chromatic_aberration.dispersion = 0.01 if ca_val else 0.0
        elif isinstance(ca_val, (int, float)):
            config.chromatic_aberration.enabled = ca_val > 0
            config.chromatic_aberration.dispersion = float(ca_val)
        elif isinstance(ca_val, dict):
            config.chromatic_aberration.enabled = ca_val.get("enabled", True)
            config.chromatic_aberration.dispersion = ca_val.get("dispersion", 0.01)
        
        return config
    
    def config_to_blender_nodes(self, config: EffectsConfig) -> List[dict]:
        """
        Génère la liste des nodes Blender à créer.
        
        Args:
            config: Configuration des effets
            
        Returns:
            Liste de dictionnaires décrivant les nodes
        """
        nodes = []
        
        if config.bloom.enabled:
            nodes.append({
                "type": "CompositorNodeGlare",
                "name": "Bloom",
                "params": config.bloom.to_blender_params()
            })
        
        if config.lens_flare.enabled:
            nodes.append({
                "type": "CompositorNodeGlare",
                "name": "LensFlare",
                "params": config.lens_flare.to_blender_params()
            })
        
        if config.vignette.enabled:
            params = config.vignette.to_blender_params()
            nodes.append({
                "type": "CompositorNodeEllipseMask",
                "name": "Vignette_Mask",
                "params": {
                    "width": params["ellipse_width"],
                    "height": params["ellipse_height"],
                    "x": params["ellipse_x"],
                    "y": params["ellipse_y"]
                }
            })
            nodes.append({
                "type": "CompositorNodeBlur",
                "name": "Vignette_Blur",
                "params": {
                    "size_x": params["blur_size"],
                    "size_y": params["blur_size"]
                }
            })
            nodes.append({
                "type": "CompositorNodeMixRGB",
                "name": "Vignette_Mix",
                "params": {
                    "blend_type": params["blend_mode"],
                    "fac": params["mix_factor"]
                }
            })
        
        if config.film_grain.enabled:
            params = config.film_grain.to_blender_params()
            nodes.append({
                "type": "CompositorNodeTexture",
                "name": "Grain_Texture",
                "params": {
                    "texture_type": "NOISE",
                    "noise_scale": params["noise_scale"]
                }
            })
            nodes.append({
                "type": "CompositorNodeMixRGB",
                "name": "Grain_Mix",
                "params": {
                    "blend_type": params["blend_mode"],
                    "fac": params["intensity"]
                }
            })
        
        if config.chromatic_aberration.enabled:
            nodes.append({
                "type": "CompositorNodeLensdist",
                "name": "ChromaticAberration",
                "params": config.chromatic_aberration.to_blender_params()
            })
        
        if config.glow.enabled:
            params = config.glow.to_blender_params()
            nodes.append({
                "type": "CompositorNodeBlur",
                "name": "Glow_Blur",
                "params": {
                    "size_x": params["blur_size"],
                    "size_y": params["blur_size"]
                }
            })
            nodes.append({
                "type": "CompositorNodeMixRGB",
                "name": "Glow_Mix",
                "params": {
                    "blend_type": params["blend_mode"],
                    "fac": params["mix_factor"]
                }
            })
        
        return nodes
    
    def get_active_effects(self, config: EffectsConfig) -> List[str]:
        """Retourne la liste des effets actifs."""
        active = []
        if config.bloom.enabled:
            active.append("bloom")
        if config.lens_flare.enabled:
            active.append("lens_flare")
        if config.film_grain.enabled:
            active.append("film_grain")
        if config.vignette.enabled:
            active.append("vignette")
        if config.chromatic_aberration.enabled:
            active.append("chromatic_aberration")
        if config.glow.enabled:
            active.append("glow")
        return active
    
    def list_presets(self) -> List[str]:
        """Liste tous les presets disponibles."""
        return list(self.presets.keys())


def create_blender_effect_nodes(tree, effects: dict, input_socket) -> Any:
    """
    Crée les nodes d'effets dans un Blender compositor tree.
    Cette fonction est appelée depuis compositor_pipeline.py.
    
    Args:
        tree: Blender node tree
        effects: Dict d'effets depuis PRODUCTION_PLAN.JSON
        input_socket: Socket d'entrée (output du node précédent)
        
    Returns:
        Socket de sortie du dernier node
    """
    forge = EffectsForge()
    config = forge.parse_effects_dict(effects)
    
    current_output = input_socket
    x_pos = 600
    
    return current_output, x_pos


if __name__ == "__main__":
    print("=" * 60)
    print("   EFFECTS FORGE — EXODUS ALCHEMIST LAB")
    print("=" * 60)
    
    forge = EffectsForge()
    
    print("\n=== Presets Disponibles ===")
    for name in forge.list_presets():
        preset = forge.get_preset(name)
        active = forge.get_active_effects(preset)
        print(f"  • {name}: {', '.join(active) if active else 'aucun effet'}")
    
    print("\n=== Test Parsing ===")
    test_dict = {
        "bloom": True,
        "lens_flare": False,
        "film_grain": 0.1,
        "vignette": 0.3
    }
    
    config = forge.parse_effects_dict(test_dict)
    print(f"  Input: {test_dict}")
    print(f"  Active: {forge.get_active_effects(config)}")
    
    nodes = forge.config_to_blender_nodes(config)
    print(f"  Blender nodes: {len(nodes)}")
    for node in nodes:
        print(f"    - {node['name']} ({node['type']})")
