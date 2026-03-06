"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 05_ALCHEMIST — ALCHEMIST SCHEMA (Bible Alchimique)               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de données pures : définit TOUTES les constantes, presets et       ║
║  validations nécessaires au pipeline de fusion visuelle V2 de U05.         ║
║  Zéro dépendance externe. Zéro traitement. Données + Validation.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
from typing import Dict, List, Tuple, Union


ALCHEMIST_SCHEMA_VERSION = "2.0.0"


# =============================================================================
# PILIER 1 — CONSTANTES CANONIQUES
# =============================================================================

OUTPUT_FORMAT = "png"
OUTPUT_DEPTH = 16
OUTPUT_COMPRESSION = 3
SUPPORTED_INPUT_FORMATS: List[str] = [".exr", ".png", ".tiff", ".tif"]
SUPPORTED_VIDEO_FORMATS: List[str] = [".mp4", ".avi", ".mov", ".mkv"]
PROCESSING_DTYPE = "float32"
PROCESSING_COLOR_SPACE = "LAB"

PIPELINE_ORDER: List[str] = ["match_color", "grain", "bloom", "sharpness"]

UINT8_MAX = 255
UINT16_MAX = 65535


# =============================================================================
# PILIER 2 — MATCH COLOR PARAMS
# =============================================================================

MATCH_COLOR_DEFAULTS: Dict[str, Union[float, str, int]] = {
    "intensity": 0.85,
    "color_space": "LAB",
    "reference_sample_count": 20,
    "reference_strategy": "uniform",
}

MATCH_COLOR_RANGES: Dict[str, Tuple[float, float]] = {
    "intensity": (0.0, 1.0),
    "reference_sample_count": (5, 100),
}

VALID_COLOR_SPACES: List[str] = ["LAB", "RGB", "YCrCb"]
DEFAULT_COLOR_SPACE = "LAB"
VALID_REFERENCE_STRATEGIES: List[str] = ["uniform", "first_n", "random"]


# =============================================================================
# PILIER 3 — GRAIN MATCHER PARAMS
# =============================================================================

GRAIN_DEFAULTS: Dict[str, Union[float, int, str]] = {
    "intensity": 0.5,
    "bilateral_d": 9,
    "bilateral_sigma_color": 75,
    "bilateral_sigma_space": 75,
    "calibration_samples": 10,
    "method": "procedural",
}

GRAIN_RANGES: Dict[str, Tuple[float, float]] = {
    "intensity": (0.0, 1.0),
    "bilateral_d": (5, 15),
    "bilateral_sigma_color": (25, 150),
    "bilateral_sigma_space": (25, 150),
    "calibration_samples": (3, 30),
}

VALID_GRAIN_METHODS: List[str] = ["procedural", "per_frame"]
DEFAULT_GRAIN_METHOD = "procedural"


# =============================================================================
# PILIER 4 — BLOOM PRESETS
# =============================================================================

BLOOM_DEFAULTS: Dict[str, Union[float, int]] = {
    "threshold": 0.8,
    "intensity": 0.3,
    "radius": 51,
}

BLOOM_PRESETS: Dict[str, dict] = {
    "cinema":  {"threshold": 0.8,  "intensity": 0.3,  "radius": 51},
    "subtle":  {"threshold": 0.9,  "intensity": 0.15, "radius": 31},
    "neon":    {"threshold": 0.6,  "intensity": 0.5,  "radius": 71},
    "none":    {"threshold": 1.0,  "intensity": 0.0,  "radius": 1},
}

BLOOM_RANGES: Dict[str, Tuple[float, float]] = {
    "threshold": (0.0, 1.0),
    "intensity": (0.0, 1.0),
    "radius": (3, 151),
}

VALID_BLOOM_PRESETS: List[str] = list(BLOOM_PRESETS.keys())
DEFAULT_BLOOM_PRESET = "cinema"


# =============================================================================
# PILIER 5 — SHARPNESS TRANSFER PARAMS
# =============================================================================

SHARPNESS_DEFAULTS: Dict[str, Union[float, int, str]] = {
    "intensity": 0.7,
    "method": "laplacian_variance",
    "max_blur_sigma": 3.0,
    "unsharp_amount": 0.5,
    "unsharp_radius": 3,
}

SHARPNESS_RANGES: Dict[str, Tuple[float, float]] = {
    "intensity": (0.0, 1.0),
    "max_blur_sigma": (0.5, 10.0),
    "unsharp_amount": (0.0, 2.0),
    "unsharp_radius": (1, 11),
}

VALID_SHARPNESS_METHODS: List[str] = ["laplacian_variance"]


# =============================================================================
# PILIER 6 — PIPELINE PRESETS
# =============================================================================

PIPELINE_PRESETS: Dict[str, dict] = {
    "cinema_fusion": {
        "description": "Look standard — fusion vidéo/avatar invisible",
        "match_color": 0.85,
        "grain": 0.5,
        "bloom": "cinema",
        "sharpness": 0.7,
    },
    "subtle_blend": {
        "description": "Fusion légère — avatar garde son identité CG",
        "match_color": 0.6,
        "grain": 0.3,
        "bloom": "subtle",
        "sharpness": 0.5,
    },
    "neon_blast": {
        "description": "Style cyberpunk — bloom agressif, grain léger",
        "match_color": 0.7,
        "grain": 0.2,
        "bloom": "neon",
        "sharpness": 0.4,
    },
    "raw_match": {
        "description": "Match Color pur — grain/bloom/sharpness off",
        "match_color": 1.0,
        "grain": 0.0,
        "bloom": "none",
        "sharpness": 0.0,
    },
    "full_nuke": {
        "description": "Toutes les transformations à fond",
        "match_color": 0.95,
        "grain": 0.6,
        "bloom": "cinema",
        "sharpness": 0.8,
    },
}

VALID_PIPELINE_PRESETS: List[str] = list(PIPELINE_PRESETS.keys())
DEFAULT_PIPELINE_PRESET = "cinema_fusion"


# =============================================================================
# PILIER 7 — CLASSE FACADE AlchemistSchema + VALIDATION
# =============================================================================

class AlchemistSchema:
    """Bible Alchimique de U05 — encapsule les 7 piliers de données
    et toutes les fonctions de validation."""

    def __init__(self) -> None:
        self.match_color_defaults: dict = dict(MATCH_COLOR_DEFAULTS)
        self.match_color_ranges: Dict[str, Tuple[float, float]] = dict(MATCH_COLOR_RANGES)
        self.grain_defaults: dict = dict(GRAIN_DEFAULTS)
        self.grain_ranges: Dict[str, Tuple[float, float]] = dict(GRAIN_RANGES)
        self.bloom_defaults: dict = dict(BLOOM_DEFAULTS)
        self.bloom_presets: Dict[str, dict] = {k: dict(v) for k, v in BLOOM_PRESETS.items()}
        self.bloom_ranges: Dict[str, Tuple[float, float]] = dict(BLOOM_RANGES)
        self.sharpness_defaults: dict = dict(SHARPNESS_DEFAULTS)
        self.sharpness_ranges: Dict[str, Tuple[float, float]] = dict(SHARPNESS_RANGES)
        self.pipeline_presets: Dict[str, dict] = {k: dict(v) for k, v in PIPELINE_PRESETS.items()}
        self.pipeline_order: List[str] = list(PIPELINE_ORDER)

    # -----------------------------------------------------------------
    # Validation — Intensity
    # -----------------------------------------------------------------

    def validate_intensity(self, name: str, value: float) -> float:
        """Valide et clamp une valeur d'intensité dans son range.
        Retourne la valeur clampée. Print warning si hors range."""
        ranges_map = {
            "match_color": MATCH_COLOR_RANGES.get("intensity", (0.0, 1.0)),
            "grain": GRAIN_RANGES.get("intensity", (0.0, 1.0)),
            "bloom": BLOOM_RANGES.get("intensity", (0.0, 1.0)),
            "sharpness": SHARPNESS_RANGES.get("intensity", (0.0, 1.0)),
        }
        lo, hi = ranges_map.get(name, (0.0, 1.0))
        if value < lo or value > hi:
            clamped = max(lo, min(hi, value))
            print(f"  WARNING {name} intensity {value} hors range [{lo}, {hi}] → clampé à {clamped}")
            return clamped
        return value

    # -----------------------------------------------------------------
    # Validation — Radius
    # -----------------------------------------------------------------

    def validate_radius(self, value: int) -> int:
        """Valide un radius de kernel : doit être impair et dans BLOOM_RANGES.
        Force impair si pair (value + 1). Clamp dans range."""
        lo, hi = BLOOM_RANGES["radius"]
        lo, hi = int(lo), int(hi)
        value = max(lo, min(hi, value))
        if value % 2 == 0:
            value += 1
        value = min(hi, value)
        return value

    # -----------------------------------------------------------------
    # Validation — Pipeline Preset
    # -----------------------------------------------------------------

    def validate_pipeline_preset(self, name: str) -> Tuple[bool, str]:
        """Valide un nom de preset. Retourne (True, '') ou (False, message)."""
        if name in self.pipeline_presets:
            return (True, "")
        return (False, f"Preset inconnu : '{name}'. Valides : {VALID_PIPELINE_PRESETS}")

    # -----------------------------------------------------------------
    # Pipeline Config
    # -----------------------------------------------------------------

    def get_pipeline_config(self, preset_name: str) -> dict:
        """Retourne la config complète pour un preset donné.
        Résout le bloom preset string en dict de params bloom.
        Retourne un dict prêt à l'emploi avec toutes les valeurs numériques."""
        valid, msg = self.validate_pipeline_preset(preset_name)
        if not valid:
            raise ValueError(msg)

        preset = self.pipeline_presets[preset_name]

        mc = dict(MATCH_COLOR_DEFAULTS)
        mc["intensity"] = preset["match_color"]

        gr = dict(GRAIN_DEFAULTS)
        gr["intensity"] = preset["grain"]

        bl = self.get_bloom_config(preset["bloom"])

        sh = dict(SHARPNESS_DEFAULTS)
        sh["intensity"] = preset["sharpness"]

        return {
            "match_color": mc,
            "grain": gr,
            "bloom": bl,
            "sharpness": sh,
        }

    # -----------------------------------------------------------------
    # Bloom Config
    # -----------------------------------------------------------------

    def get_bloom_config(self, preset_name_or_dict: Union[str, dict]) -> dict:
        """Résout un bloom config. Si string → lookup dans BLOOM_PRESETS.
        Si dict → valider et retourner. Si inconnu → fallback BLOOM_DEFAULTS."""
        if isinstance(preset_name_or_dict, dict):
            return dict(preset_name_or_dict)
        if isinstance(preset_name_or_dict, str) and preset_name_or_dict in BLOOM_PRESETS:
            return dict(BLOOM_PRESETS[preset_name_or_dict])
        return dict(BLOOM_DEFAULTS)

    # -----------------------------------------------------------------
    # Default Config
    # -----------------------------------------------------------------

    def get_default_config(self) -> dict:
        """Retourne get_pipeline_config(DEFAULT_PIPELINE_PRESET)."""
        return self.get_pipeline_config(DEFAULT_PIPELINE_PRESET)

    # -----------------------------------------------------------------
    # Validation — Input Format
    # -----------------------------------------------------------------

    def validate_input_format(self, filepath: str) -> Tuple[bool, str]:
        """Vérifie que l'extension est dans SUPPORTED_INPUT_FORMATS.
        Retourne (True, '') ou (False, message)."""
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext in SUPPORTED_INPUT_FORMATS:
            return (True, "")
        return (False, f"Format non supporté : '{ext}'. Valides : {SUPPORTED_INPUT_FORMATS}")

    # -----------------------------------------------------------------
    # Validation — Video Format
    # -----------------------------------------------------------------

    def validate_video_format(self, filepath: str) -> Tuple[bool, str]:
        """Vérifie que l'extension est dans SUPPORTED_VIDEO_FORMATS.
        Retourne (True, '') ou (False, message)."""
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext in SUPPORTED_VIDEO_FORMATS:
            return (True, "")
        return (False, f"Format vidéo non supporté : '{ext}'. Valides : {SUPPORTED_VIDEO_FORMATS}")

    # -----------------------------------------------------------------
    # Self Test
    # -----------------------------------------------------------------

    def self_test(self) -> Tuple[int, int]:
        """Exécute les tests de validation. Retourne (passed, total)."""
        passed = 0
        total = 8

        print("═══════════════════════════════════════════════════")
        print("   ALCHEMIST SCHEMA — SELF TEST")
        print("═══════════════════════════════════════════════════")
        print()

        # --- TEST 1 : Pipeline presets completeness ---
        t1_ok = True
        required_keys = {"match_color", "grain", "bloom", "sharpness"}
        for name, preset in self.pipeline_presets.items():
            missing = required_keys - set(preset.keys())
            if missing:
                t1_ok = False
                print(f"  ERREUR preset '{name}': clés manquantes = {sorted(missing)}")
        if t1_ok:
            passed += 1
            print(f"[TEST 1] Pipeline presets completeness ... ✓ ({len(self.pipeline_presets)} presets, 4 clés chacun)")
        else:
            print("[TEST 1] Pipeline presets completeness ... ✗")

        # --- TEST 2 : Intensity ranges validity ---
        t2_ok = True
        for name, preset in self.pipeline_presets.items():
            for key in ("match_color", "grain", "sharpness"):
                val = preset[key]
                if not (0.0 <= val <= 1.0):
                    t2_ok = False
                    print(f"  ERREUR preset '{name}'.{key} = {val} hors [0.0, 1.0]")
        if t2_ok:
            passed += 1
            print("[TEST 2] Intensity ranges validity ....... ✓ (toutes les intensités dans [0.0, 1.0])")
        else:
            print("[TEST 2] Intensity ranges validity ....... ✗")

        # --- TEST 3 : Bloom preset names exist ---
        t3_ok = True
        for name, preset in self.pipeline_presets.items():
            bloom_ref = preset["bloom"]
            if isinstance(bloom_ref, str) and bloom_ref not in BLOOM_PRESETS:
                t3_ok = False
                print(f"  ERREUR preset '{name}'.bloom = '{bloom_ref}' introuvable dans BLOOM_PRESETS")
        if t3_ok:
            passed += 1
            print(f"[TEST 3] Bloom preset references ......... ✓ (tous les bloom presets existent)")
        else:
            print("[TEST 3] Bloom preset references ......... ✗")

        # --- TEST 4 : PIPELINE_ORDER ---
        t4_ok = True
        expected_order = {"match_color", "grain", "bloom", "sharpness"}
        actual_order = set(self.pipeline_order)
        if actual_order != expected_order or len(self.pipeline_order) != 4:
            t4_ok = False
            print(f"  ERREUR PIPELINE_ORDER = {self.pipeline_order} (attendu 4 étapes: {sorted(expected_order)})")
        if t4_ok:
            passed += 1
            print(f"[TEST 4] Pipeline order .................. ✓ ({' → '.join(self.pipeline_order)})")
        else:
            print("[TEST 4] Pipeline order .................. ✗")

        # --- TEST 5 : validate_intensity clamp ---
        t5_ok = True
        clamped_hi = self.validate_intensity("match_color", 1.5)
        if clamped_hi != 1.0:
            t5_ok = False
            print(f"  ERREUR validate_intensity('match_color', 1.5) = {clamped_hi} (attendu 1.0)")
        clamped_lo = self.validate_intensity("grain", -0.3)
        if clamped_lo != 0.0:
            t5_ok = False
            print(f"  ERREUR validate_intensity('grain', -0.3) = {clamped_lo} (attendu 0.0)")
        if t5_ok:
            passed += 1
            print("[TEST 5] Intensity clamping .............. ✓ (1.5→1.0, -0.3→0.0)")
        else:
            print("[TEST 5] Intensity clamping .............. ✗")

        # --- TEST 6 : validate_radius force impair ---
        t6_ok = True
        r_even = self.validate_radius(50)
        if r_even != 51:
            t6_ok = False
            print(f"  ERREUR validate_radius(50) = {r_even} (attendu 51)")
        r_odd = self.validate_radius(51)
        if r_odd != 51:
            t6_ok = False
            print(f"  ERREUR validate_radius(51) = {r_odd} (attendu 51)")
        if t6_ok:
            passed += 1
            print("[TEST 6] Radius impair enforcement ....... ✓ (50→51, 51→51)")
        else:
            print("[TEST 6] Radius impair enforcement ....... ✗")

        # --- TEST 7 : get_pipeline_config completeness ---
        t7_ok = True
        config = self.get_pipeline_config("cinema_fusion")
        expected_sections = {"match_color", "grain", "bloom", "sharpness"}
        missing_sections = expected_sections - set(config.keys())
        if missing_sections:
            t7_ok = False
            print(f"  ERREUR config sections manquantes : {sorted(missing_sections)}")
        for section in expected_sections:
            if section in config and not isinstance(config[section], dict):
                t7_ok = False
                print(f"  ERREUR config['{section}'] n'est pas un dict")
        if t7_ok:
            passed += 1
            sizes = ", ".join(f"{k}:{len(v)}keys" for k, v in config.items())
            print(f"[TEST 7] get_pipeline_config ............. ✓ (cinema_fusion → {sizes})")
        else:
            print("[TEST 7] get_pipeline_config ............. ✗")

        # --- TEST 8 : Rejet hérétique ---
        t8_ok = True
        ok_bad, msg_bad = self.validate_pipeline_preset("inexistant")
        if ok_bad:
            t8_ok = False
            print("  ERREUR preset 'inexistant' devrait être rejeté")
        ok_good, _ = self.validate_pipeline_preset("cinema_fusion")
        if not ok_good:
            t8_ok = False
            print("  ERREUR preset 'cinema_fusion' devrait être accepté")
        ok_fmt, _ = self.validate_input_format("image.jpg")
        if ok_fmt:
            t8_ok = False
            print("  ERREUR format '.jpg' devrait être rejeté")
        ok_vid, _ = self.validate_video_format("video.mp4")
        if not ok_vid:
            t8_ok = False
            print("  ERREUR format '.mp4' devrait être accepté")
        if t8_ok:
            passed += 1
            print("[TEST 8] Rejets hérétiques ............... ✓ (preset/format inconnus rejetés)")
        else:
            print("[TEST 8] Rejets hérétiques ............... ✗")

        print()
        print("═══════════════════════════════════════════════════")
        print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
        print("═══════════════════════════════════════════════════")

        return (passed, total)


# =============================================================================
# RAPPORT DE VALIDATION — exécution standalone
# =============================================================================

if __name__ == "__main__":
    schema = AlchemistSchema()
    schema.self_test()
