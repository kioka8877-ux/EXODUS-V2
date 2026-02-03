#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  COLOR GRADER — EXODUS ALCHEMIST LAB                         ║
║             LUTs • Color Correction • Lift/Gamma/Gain Control                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module de color grading avec support des fichiers .cube LUT.
Inclut des presets cinématiques et des corrections manuelles.

Peut être utilisé:
- Comme module Python importé par compositor_pipeline.py
- En standalone pour tester les LUTs
"""

import json
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field


@dataclass
class LUTData:
    """Structure de données pour une LUT 3D."""
    title: str = ""
    size: int = 0
    domain_min: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    domain_max: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    data: List[List[float]] = field(default_factory=list)
    
    lift: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    gamma: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    gain: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    
    temperature_shift: float = 0.0
    tint_shift: float = 0.0


@dataclass
class ColorGradeConfig:
    """Configuration complète de color grading."""
    exposure: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    temperature: float = 0.0
    tint: float = 0.0
    
    lift_r: float = 1.0
    lift_g: float = 1.0
    lift_b: float = 1.0
    
    gamma_r: float = 1.0
    gamma_g: float = 1.0
    gamma_b: float = 1.0
    
    gain_r: float = 1.0
    gain_g: float = 1.0
    gain_b: float = 1.0
    
    lut_name: str = ""
    lut_intensity: float = 1.0


CINEMATIC_PRESETS = {
    "cinematic_warm": ColorGradeConfig(
        exposure=0.1,
        contrast=1.15,
        saturation=0.95,
        temperature=0.15,
        lift_r=1.02, lift_g=0.98, lift_b=0.95,
        gamma_r=1.02, gamma_g=1.0, gamma_b=0.98,
        gain_r=1.05, gain_g=1.02, gain_b=0.95
    ),
    "cinematic_cold": ColorGradeConfig(
        exposure=0.05,
        contrast=1.2,
        saturation=0.9,
        temperature=-0.1,
        lift_r=0.95, lift_g=0.98, lift_b=1.02,
        gamma_r=0.98, gamma_g=1.0, gamma_b=1.02,
        gain_r=0.95, gain_g=1.0, gain_b=1.08
    ),
    "neon_nights": ColorGradeConfig(
        exposure=0.0,
        contrast=1.3,
        saturation=1.3,
        temperature=-0.05,
        lift_r=0.98, lift_g=0.95, lift_b=1.1,
        gamma_r=1.05, gamma_g=0.95, gamma_b=1.1,
        gain_r=1.1, gain_g=0.95, gain_b=1.15
    ),
    "natural": ColorGradeConfig(
        exposure=0.0,
        contrast=1.0,
        saturation=1.0,
        temperature=0.0,
    ),
    "bleach_bypass": ColorGradeConfig(
        exposure=0.1,
        contrast=1.4,
        saturation=0.6,
        temperature=0.0,
        gamma_r=0.95, gamma_g=0.95, gamma_b=0.95
    ),
    "vintage_film": ColorGradeConfig(
        exposure=0.05,
        contrast=0.9,
        saturation=0.85,
        temperature=0.1,
        tint=0.05,
        lift_r=1.05, lift_g=1.02, lift_b=0.95,
        gain_r=1.0, gain_g=0.98, gain_b=0.9
    ),
    "teal_orange": ColorGradeConfig(
        exposure=0.0,
        contrast=1.1,
        saturation=1.1,
        lift_r=0.95, lift_g=1.0, lift_b=1.1,
        gamma_r=1.0, gamma_g=1.0, gamma_b=0.95,
        gain_r=1.1, gain_g=1.0, gain_b=0.9
    )
}


class CubeLUTParser:
    """Parser pour fichiers .cube (Adobe/Resolve compatible)."""
    
    @staticmethod
    def parse(file_path: Union[str, Path]) -> Optional[LUTData]:
        """
        Parse un fichier .cube et retourne les données LUT.
        
        Args:
            file_path: Chemin vers le fichier .cube
            
        Returns:
            LUTData ou None si échec
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"[COLOR_GRADER:ERROR] Fichier LUT introuvable: {file_path}")
            return None
        
        if file_path.suffix.lower() != '.cube':
            print(f"[COLOR_GRADER:WARN] Extension non .cube: {file_path}")
        
        lut = LUTData()
        lut.title = file_path.stem
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if line.upper().startswith('TITLE'):
                if '"' in line:
                    lut.title = line.split('"')[1]
                else:
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        lut.title = parts[1]
            
            elif line.upper().startswith('LUT_3D_SIZE'):
                try:
                    lut.size = int(line.split()[1])
                except (ValueError, IndexError):
                    print(f"[COLOR_GRADER:WARN] LUT_3D_SIZE invalide")
            
            elif line.upper().startswith('DOMAIN_MIN'):
                try:
                    values = [float(x) for x in line.split()[1:4]]
                    if len(values) == 3:
                        lut.domain_min = values
                except ValueError:
                    pass
            
            elif line.upper().startswith('DOMAIN_MAX'):
                try:
                    values = [float(x) for x in line.split()[1:4]]
                    if len(values) == 3:
                        lut.domain_max = values
                except ValueError:
                    pass
            
            elif line[0].isdigit() or line[0] == '-' or line[0] == '.':
                try:
                    values = [float(x) for x in line.split()[:3]]
                    if len(values) == 3:
                        lut.data.append(values)
                except ValueError:
                    continue
        
        if not lut.data:
            print(f"[COLOR_GRADER:ERROR] Aucune donnée LUT trouvée dans {file_path}")
            return None
        
        if lut.size == 0:
            lut.size = int(round(len(lut.data) ** (1/3)))
        
        expected_size = lut.size ** 3
        if len(lut.data) != expected_size:
            print(f"[COLOR_GRADER:WARN] Taille LUT incohérente: {len(lut.data)} != {expected_size}")
        
        CubeLUTParser._analyze_lut(lut)
        
        print(f"[COLOR_GRADER] LUT chargée: {lut.title} ({lut.size}³)")
        return lut
    
    @staticmethod
    def _analyze_lut(lut: LUTData):
        """Analyse la LUT pour extraire des paramètres approximatifs."""
        if not lut.data or lut.size < 2:
            return
        
        shadows = lut.data[0]
        lut.lift = [1.0 + (s - 0.0) * 0.5 for s in shadows]
        
        mid_idx = lut.size // 2
        if lut.size > 2:
            mid_linear = mid_idx * (lut.size ** 2) + mid_idx * lut.size + mid_idx
            if mid_linear < len(lut.data):
                midtones = lut.data[mid_linear]
                lut.gamma = [1.0 + (m - 0.5) * 0.5 for m in midtones]
        
        highlights = lut.data[-1]
        lut.gain = [h for h in highlights]
        
        r_avg = sum(d[0] for d in lut.data) / len(lut.data)
        b_avg = sum(d[2] for d in lut.data) / len(lut.data)
        lut.temperature_shift = (r_avg - b_avg) * 0.5


class ColorGrader:
    """Moteur de color grading avec support LUT et corrections manuelles."""
    
    def __init__(self, luts_directory: Optional[Union[str, Path]] = None):
        """
        Initialise le ColorGrader.
        
        Args:
            luts_directory: Dossier contenant les fichiers .cube
        """
        self.luts_dir = Path(luts_directory) if luts_directory else None
        self.loaded_luts: Dict[str, LUTData] = {}
        self.presets = CINEMATIC_PRESETS.copy()
        
        if self.luts_dir and self.luts_dir.exists():
            self._scan_luts()
    
    def _scan_luts(self):
        """Scanne le dossier LUTs et charge les métadonnées."""
        if not self.luts_dir:
            return
        
        for lut_file in self.luts_dir.glob("*.cube"):
            lut_name = lut_file.stem.lower().replace("-", "_").replace(" ", "_")
            self.loaded_luts[lut_name] = None
            self.loaded_luts[lut_file.stem] = None
        
        print(f"[COLOR_GRADER] {len(self.loaded_luts)//2} LUTs disponibles")
    
    def load_lut(self, name: str) -> Optional[LUTData]:
        """
        Charge une LUT par nom.
        
        Args:
            name: Nom de la LUT (avec ou sans extension)
            
        Returns:
            LUTData ou None
        """
        normalized = name.lower().replace("-", "_").replace(" ", "_")
        
        if normalized in self.loaded_luts and self.loaded_luts[normalized] is not None:
            return self.loaded_luts[normalized]
        
        if name in self.loaded_luts and self.loaded_luts[name] is not None:
            return self.loaded_luts[name]
        
        if self.luts_dir:
            possible_paths = [
                self.luts_dir / f"{name}.cube",
                self.luts_dir / f"{normalized}.cube"
            ]
            
            for path in possible_paths:
                if path.exists():
                    lut = CubeLUTParser.parse(path)
                    if lut:
                        self.loaded_luts[name] = lut
                        self.loaded_luts[normalized] = lut
                        return lut
        
        if Path(name).exists():
            return CubeLUTParser.parse(name)
        
        print(f"[COLOR_GRADER:WARN] LUT introuvable: {name}")
        return None
    
    def get_preset(self, name: str) -> Optional[ColorGradeConfig]:
        """
        Récupère un preset cinématique.
        
        Args:
            name: Nom du preset
            
        Returns:
            ColorGradeConfig ou None
        """
        normalized = name.lower().replace("-", "_").replace(" ", "_")
        return self.presets.get(normalized) or self.presets.get(name)
    
    def get_config_from_name(self, grade_name: str) -> ColorGradeConfig:
        """
        Génère une config à partir d'un nom de grade.
        Essaie d'abord les presets, puis les LUTs.
        
        Args:
            grade_name: Nom du grade (preset ou LUT)
            
        Returns:
            ColorGradeConfig
        """
        preset = self.get_preset(grade_name)
        if preset:
            config = ColorGradeConfig(
                exposure=preset.exposure,
                contrast=preset.contrast,
                saturation=preset.saturation,
                temperature=preset.temperature,
                tint=preset.tint,
                lift_r=preset.lift_r, lift_g=preset.lift_g, lift_b=preset.lift_b,
                gamma_r=preset.gamma_r, gamma_g=preset.gamma_g, gamma_b=preset.gamma_b,
                gain_r=preset.gain_r, gain_g=preset.gain_g, gain_b=preset.gain_b,
                lut_name=grade_name if grade_name in ['cinematic_warm', 'cinematic_cold', 'neon_nights'] else "",
                lut_intensity=1.0
            )
            return config
        
        lut = self.load_lut(grade_name)
        if lut:
            config = ColorGradeConfig(
                lift_r=lut.lift[0], lift_g=lut.lift[1], lift_b=lut.lift[2],
                gamma_r=lut.gamma[0], gamma_g=lut.gamma[1], gamma_b=lut.gamma[2],
                gain_r=lut.gain[0], gain_g=lut.gain[1], gain_b=lut.gain[2],
                temperature=lut.temperature_shift,
                lut_name=grade_name,
                lut_intensity=1.0
            )
            return config
        
        return ColorGradeConfig()
    
    def config_to_blender_params(self, config: ColorGradeConfig) -> dict:
        """
        Convertit une ColorGradeConfig en paramètres Blender.
        
        Args:
            config: Configuration de color grading
            
        Returns:
            Dict avec les paramètres Blender nodes
        """
        return {
            "exposure": {
                "exposure": config.exposure
            },
            "color_balance": {
                "lift": (config.lift_r, config.lift_g, config.lift_b, 1.0),
                "gamma": (config.gamma_r, config.gamma_g, config.gamma_b, 1.0),
                "gain": (config.gain_r, config.gain_g, config.gain_b, 1.0)
            },
            "hue_saturation": {
                "saturation": config.saturation
            },
            "brightness_contrast": {
                "contrast": (config.contrast - 1.0) * 50
            },
            "lut_path": self._get_lut_path(config.lut_name) if config.lut_name else None,
            "lut_intensity": config.lut_intensity
        }
    
    def _get_lut_path(self, lut_name: str) -> Optional[str]:
        """Retourne le chemin complet vers une LUT."""
        if not self.luts_dir:
            return None
        
        for ext in ['.cube', '.CUBE']:
            path = self.luts_dir / f"{lut_name}{ext}"
            if path.exists():
                return str(path)
        
        normalized = lut_name.lower().replace("-", "_").replace(" ", "_")
        for ext in ['.cube', '.CUBE']:
            path = self.luts_dir / f"{normalized}{ext}"
            if path.exists():
                return str(path)
        
        return None
    
    def list_available(self) -> dict:
        """
        Liste tous les grades disponibles (presets + LUTs).
        
        Returns:
            Dict avec 'presets' et 'luts'
        """
        return {
            "presets": list(self.presets.keys()),
            "luts": [k for k in self.loaded_luts.keys() if not k.startswith("_")]
        }


def apply_color_grade_values(r: float, g: float, b: float, config: ColorGradeConfig) -> Tuple[float, float, float]:
    """
    Applique les corrections de couleur à un pixel RGB.
    Utilisé pour le traitement CPU standalone.
    
    Args:
        r, g, b: Valeurs RGB (0-1)
        config: Configuration de color grading
        
    Returns:
        Tuple (r, g, b) corrigé
    """
    exp_mult = 2 ** config.exposure
    r *= exp_mult
    g *= exp_mult
    b *= exp_mult
    
    r = config.lift_r + (r - 0.0) * (config.gain_r - config.lift_r)
    g = config.lift_g + (g - 0.0) * (config.gain_g - config.lift_g)
    b = config.lift_b + (b - 0.0) * (config.gain_b - config.lift_b)
    
    r = r ** (1.0 / config.gamma_r) if config.gamma_r > 0 else r
    g = g ** (1.0 / config.gamma_g) if config.gamma_g > 0 else g
    b = b ** (1.0 / config.gamma_b) if config.gamma_b > 0 else b
    
    mid = 0.5
    r = mid + (r - mid) * config.contrast
    g = mid + (g - mid) * config.contrast
    b = mid + (b - mid) * config.contrast
    
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    r = luminance + (r - luminance) * config.saturation
    g = luminance + (g - luminance) * config.saturation
    b = luminance + (b - luminance) * config.saturation
    
    if config.temperature != 0:
        r += config.temperature * 0.1
        b -= config.temperature * 0.1
    
    if config.tint != 0:
        g += config.tint * 0.1
    
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    
    return r, g, b


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("   COLOR GRADER — EXODUS ALCHEMIST LAB")
    print("=" * 60)
    
    grader = ColorGrader()
    
    print("\n=== Presets Disponibles ===")
    for name, preset in CINEMATIC_PRESETS.items():
        print(f"  • {name}")
        print(f"      Exposure: {preset.exposure:+.2f}, Contrast: {preset.contrast:.2f}, Saturation: {preset.saturation:.2f}")
    
    if len(sys.argv) > 1:
        lut_path = sys.argv[1]
        print(f"\n=== Test LUT: {lut_path} ===")
        
        lut = CubeLUTParser.parse(lut_path)
        if lut:
            print(f"  Title: {lut.title}")
            print(f"  Size: {lut.size}³")
            print(f"  Lift: {lut.lift}")
            print(f"  Gamma: {lut.gamma}")
            print(f"  Gain: {lut.gain}")
            print(f"  Temperature Shift: {lut.temperature_shift:+.3f}")
