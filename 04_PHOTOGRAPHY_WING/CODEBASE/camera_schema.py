"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 04_PHOTOGRAPHY — CAMERA SCHEMA (Bible Optique)                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de données pures : définit TOUTES les constantes, presets et       ║
║  validations nécessaires au pipeline caméra / éclairage / rendu de U04.    ║
║  Zéro dépendance Blender. Zéro traitement. Données + Validation.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
from typing import Dict, List, Optional, Tuple


# =============================================================================
# PILIER 1 — CONSTANTES CANONIQUES
# =============================================================================

PERSPECTIVE_LOCK_TOLERANCE = 0.05

DEFAULT_SENSOR_WIDTH_MM = 36.0
DEFAULT_FSTOP = 2.8
DEFAULT_FOV_DEGREES = 50.0

TARGET_RESOLUTION_4K = (3840, 2160)
TARGET_FPS = 30

DEFAULT_CYCLES_SAMPLES = 256
PREVIEW_CYCLES_SAMPLES = 64

DEFAULT_VOLUME_DENSITY = 0.01
DEFAULT_VOLUME_ANISOTROPY = 0.3


def fov_to_focal_mm(fov_degrees: float, sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM) -> float:
    """Convertit un FOV en focale mm. Usage: lire estimated_fov_degrees de U00."""
    return (sensor_width_mm / 2) / math.tan(math.radians(fov_degrees / 2))


def focal_mm_to_fov(focal_mm: float, sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM) -> float:
    """Convertit une focale mm en FOV degrés."""
    return 2 * math.degrees(math.atan(sensor_width_mm / (2 * focal_mm)))


# =============================================================================
# PILIER 2 — CAMERA STYLE PRESETS (6 styles)
# =============================================================================

CAMERA_STYLES: Dict[str, dict] = {
    "static": {
        "description": "Caméra fixe pointant vers le centre",
        "default_fov": 50,
        "distance_mult": 2.5,
        "supports_cuts": True,
        "supports_shake": False,
    },
    "dolly": {
        "description": "Mouvement linéaire sur rail",
        "default_fov": 45,
        "distance_mult": 2.0,
        "supports_cuts": True,
        "supports_shake": True,
    },
    "orbit": {
        "description": "Rotation autour du sujet",
        "default_fov": 50,
        "distance_mult": 1.8,
        "supports_cuts": True,
        "supports_shake": True,
    },
    "handheld": {
        "description": "Shake procédural via Noise modifier",
        "default_fov": 40,
        "distance_mult": 2.0,
        "supports_cuts": True,
        "supports_shake": True,
    },
    "tracking": {
        "description": "Suit un objet cible",
        "default_fov": 45,
        "distance_mult": 2.0,
        "supports_cuts": True,
        "supports_shake": True,
    },
    "matchmove": {
        "description": "Reproduit la caméra source (fSpy perspective lock)",
        "default_fov": None,
        "distance_mult": None,
        "supports_cuts": False,
        "supports_shake": False,
    },
}

VALID_CAMERA_STYLES: List[str] = list(CAMERA_STYLES.keys())
DEFAULT_CAMERA_STYLE = "static"

MOVEMENT_SPEEDS: Dict[str, float] = {
    "slow": 0.3,
    "medium": 1.0,
    "fast": 2.5,
}


# =============================================================================
# PILIER 3 — CUT PRESETS (8 types — DÉDUPLIQUÉ)
# =============================================================================

CUT_PRESETS: Dict[str, dict] = {
    "wide": {"fov": 60, "distance_mult": 2.5, "height_offset": 0.2, "roll": 0},
    "medium": {"fov": 50, "distance_mult": 1.5, "height_offset": 0.1, "roll": 0},
    "closeup": {"fov": 35, "distance_mult": 0.8, "height_offset": 0.05, "roll": 0},
    "extreme_closeup": {"fov": 25, "distance_mult": 0.4, "height_offset": 0.02, "roll": 0},
    "dutch_angle": {"fov": 45, "distance_mult": 1.2, "height_offset": 0.15, "roll": 15},
    "low_angle": {"fov": 50, "distance_mult": 1.8, "height_offset": -0.5, "roll": 0},
    "high_angle": {"fov": 50, "distance_mult": 1.8, "height_offset": 0.8, "roll": 0},
    "over_shoulder": {"fov": 40, "distance_mult": 0.6, "height_offset": 0.1, "roll": 0, "offset_x": 0.3},
}

VALID_CUT_TYPES: List[str] = list(CUT_PRESETS.keys())

TRANSITION_TYPES: Dict[str, dict] = {
    "cut": {"blend_frames": 0},
    "smooth": {"blend_frames": 15},
    "fast": {"blend_frames": 5},
    "slow": {"blend_frames": 30},
}


# =============================================================================
# PILIER 4 — LIGHTING PRESETS (5 styles + couleurs)
# =============================================================================

LIGHTING_STYLES: Dict[str, dict] = {
    "3point": {"description": "Key + Fill + Back classique", "lights_count": 3},
    "dramatic": {"description": "Fort contraste, ombres dures", "lights_count": 2},
    "neon": {"description": "Émissifs colorés cyberpunk", "lights_count": 5},
    "natural": {"description": "Sun + Sky extérieur", "lights_count": 3},
    "studio": {"description": "Softbox professionnel", "lights_count": 4},
}

VALID_LIGHTING_STYLES: List[str] = list(LIGHTING_STYLES.keys())
DEFAULT_LIGHTING_STYLE = "3point"

COLOR_TEMPS: Dict[int, Tuple[float, float, float]] = {
    2700: (1.0, 0.76, 0.54),
    3200: (1.0, 0.82, 0.65),
    4000: (1.0, 0.88, 0.78),
    5000: (1.0, 0.95, 0.90),
    5500: (1.0, 0.98, 0.95),
    6500: (0.95, 0.98, 1.0),
    7500: (0.88, 0.94, 1.0),
    9000: (0.80, 0.90, 1.0),
}

NEON_COLORS: Dict[str, Tuple[float, float, float]] = {
    "cyan": (0.0, 1.0, 1.0),
    "magenta": (1.0, 0.0, 1.0),
    "pink": (1.0, 0.4, 0.7),
    "blue": (0.2, 0.4, 1.0),
    "purple": (0.6, 0.2, 1.0),
    "green": (0.2, 1.0, 0.4),
    "orange": (1.0, 0.5, 0.1),
    "red": (1.0, 0.1, 0.1),
}


# =============================================================================
# PILIER 5 — BUST BONE CHAIN (16 noms — fallback Mixamo→Generic→Rigify→3dsMax)
# =============================================================================

BUST_BONE_CHAIN: List[str] = [
    "mixamorig:Spine2",
    "mixamorig:Spine1",
    "mixamorig:Spine",
    "mixamorig:UpperChest",
    "Spine2",
    "Spine1",
    "UpperChest",
    "Chest",
    "Spine",
    "spine.003",
    "spine.002",
    "spine.001",
    "Bip01 Spine2",
    "Bip01 Spine1",
    "Bip001 Spine2",
    "Bip001 Spine1",
]


# =============================================================================
# PILIER 6 — RENDER PRESETS (production 4K/256, darkroom 1080p/128, preview 1080p/64)
# =============================================================================

RENDER_PRESETS: Dict[str, dict] = {
    "production": {
        "engine": "CYCLES",
        "samples": 256,
        "resolution": (3840, 2160),
        "use_denoising": True,
        "denoiser": "OPENIMAGEDENOISE",
        "use_adaptive_sampling": True,
        "adaptive_threshold": 0.01,
        "film_transparent": False,
        "passes": ["Combined", "Depth", "Normal", "DiffCol", "GlossCol", "Emit"],
    },
    "darkroom": {
        "engine": "CYCLES",
        "samples": 128,
        "resolution": (1920, 1080),
        "use_denoising": True,
        "denoiser": "OPENIMAGEDENOISE",
        "use_adaptive_sampling": True,
        "adaptive_threshold": 0.02,
        "film_transparent": False,
        "passes": ["Combined"],
        "output_format": "PNG",
        "color_depth": "16",
    },
    "preview": {
        "engine": "CYCLES",
        "samples": 64,
        "resolution": (1920, 1080),
        "use_denoising": True,
        "denoiser": "OPENIMAGEDENOISE",
        "use_adaptive_sampling": True,
        "adaptive_threshold": 0.05,
        "film_transparent": False,
        "passes": ["Combined"],
    },
}


# =============================================================================
# PILIER 7 — SHAKE PRESETS (Noise modifier params)
# =============================================================================

SHAKE_PRESETS: Dict[str, dict] = {
    "handheld": {
        "description": "Tremblement caméra portée réaliste",
        "strength": 0.015,
        "scale": 2.5,
        "phase": 0.0,
        "offset": 0.0,
        "depth": 0,
        "axes": ["rotation_euler"],
    },
    "subtle": {
        "description": "Micro-tremblement à peine perceptible",
        "strength": 0.005,
        "scale": 3.0,
        "phase": 0.0,
        "offset": 0.0,
        "depth": 0,
        "axes": ["rotation_euler"],
    },
    "aggressive": {
        "description": "Tremblement violent (action/explosion)",
        "strength": 0.04,
        "scale": 1.5,
        "phase": 0.0,
        "offset": 0.0,
        "depth": 0,
        "axes": ["rotation_euler", "location"],
    },
}

VALID_SHAKE_PRESETS: List[str] = list(SHAKE_PRESETS.keys())
DEFAULT_SHAKE_PRESET = "handheld"


# =============================================================================
# PILIER 8 — MATRICE STYLE ↔ FEATURES (validation)
# =============================================================================

STYLE_FEATURE_MATRIX: Dict[str, Tuple[bool, bool, bool, bool]] = {
    "static": (True, False, True, False),
    "dolly": (True, True, True, False),
    "orbit": (True, True, True, False),
    "handheld": (True, True, True, False),
    "tracking": (True, True, True, False),
    "matchmove": (False, False, True, True),
}


# =============================================================================
# CLASSE PRINCIPALE — CameraSchema
# =============================================================================

class CameraSchema:
    """Bible Optique de U04 — encapsule les 8 piliers de données caméra
    et toutes les fonctions de validation / conversion / lookup."""

    def __init__(self) -> None:
        self.camera_styles: Dict[str, dict] = dict(CAMERA_STYLES)
        self.cut_presets: Dict[str, dict] = dict(CUT_PRESETS)
        self.lighting_styles: Dict[str, dict] = dict(LIGHTING_STYLES)
        self.color_temps: Dict[int, Tuple[float, float, float]] = dict(COLOR_TEMPS)
        self.neon_colors: Dict[str, Tuple[float, float, float]] = dict(NEON_COLORS)
        self.bust_bone_chain: List[str] = list(BUST_BONE_CHAIN)
        self.render_presets: Dict[str, dict] = dict(RENDER_PRESETS)
        self.shake_presets: Dict[str, dict] = dict(SHAKE_PRESETS)
        self.transition_types: Dict[str, dict] = dict(TRANSITION_TYPES)
        self.movement_speeds: Dict[str, float] = dict(MOVEMENT_SPEEDS)
        self.style_feature_matrix: Dict[str, Tuple[bool, bool, bool, bool]] = dict(STYLE_FEATURE_MATRIX)

    # -----------------------------------------------------------------
    # Validation — Camera Style
    # -----------------------------------------------------------------

    def validate_camera_style(self, style: str) -> Tuple[bool, str]:
        """Valide un style caméra. Retourne (True, '') ou (False, message)."""
        if style in self.camera_styles:
            return (True, "")
        return (False, f"Style inconnu : '{style}'. Valides : {VALID_CAMERA_STYLES}")

    # -----------------------------------------------------------------
    # Validation — Cut Type
    # -----------------------------------------------------------------

    def validate_cut_type(self, cut_type: str) -> Tuple[bool, str]:
        """Valide un type de cut."""
        if cut_type in self.cut_presets:
            return (True, "")
        return (False, f"Cut inconnu : '{cut_type}'. Valides : {VALID_CUT_TYPES}")

    # -----------------------------------------------------------------
    # Validation — Lighting Style
    # -----------------------------------------------------------------

    def validate_lighting_style(self, style: str) -> Tuple[bool, str]:
        """Valide un style d'éclairage."""
        if style in self.lighting_styles:
            return (True, "")
        return (False, f"Lighting inconnu : '{style}'. Valides : {VALID_LIGHTING_STYLES}")

    # -----------------------------------------------------------------
    # Validation — Perspective Deviation
    # -----------------------------------------------------------------

    def validate_perspective_deviation(self, original_fov: float, current_fov: float) -> Tuple[bool, float]:
        """Vérifie que la déviation de perspective reste dans ±5%.
        Retourne (True, deviation_ratio) si OK, (False, deviation_ratio) sinon."""
        if original_fov == 0.0:
            return (False, float("inf"))
        deviation = abs(current_fov - original_fov) / original_fov
        return (deviation <= PERSPECTIVE_LOCK_TOLERANCE, deviation)

    # -----------------------------------------------------------------
    # Style Features
    # -----------------------------------------------------------------

    def get_style_features(self, style: str) -> dict:
        """Retourne les features supportées pour un style.
        Keys : supports_cuts, supports_shake, supports_dof, requires_fspy."""
        if style not in self.style_feature_matrix:
            raise ValueError(f"Style inconnu : '{style}'. Valides : {VALID_CAMERA_STYLES}")
        cuts, shake, dof, fspy = self.style_feature_matrix[style]
        return {
            "supports_cuts": cuts,
            "supports_shake": shake,
            "supports_dof": dof,
            "requires_fspy": fspy,
        }

    # -----------------------------------------------------------------
    # Bust Bone Lookup
    # -----------------------------------------------------------------

    def find_bust_bone(self, bone_names: list) -> Optional[str]:
        """Cherche le bone du buste dans une liste de bones d'armature.
        Retourne le premier match dans BUST_BONE_CHAIN, ou None."""
        bone_set = set(bone_names)
        for candidate in self.bust_bone_chain:
            if candidate in bone_set:
                return candidate
        return None

    # -----------------------------------------------------------------
    # Conversions FOV ↔ Focal
    # -----------------------------------------------------------------

    def fov_to_focal_mm(self, fov_degrees: float) -> float:
        """Conversion FOV → focale mm (utilise DEFAULT_SENSOR_WIDTH_MM)."""
        return fov_to_focal_mm(fov_degrees)

    def focal_mm_to_fov(self, focal_mm: float) -> float:
        """Conversion focale mm → FOV."""
        return focal_mm_to_fov(focal_mm)


# =============================================================================
# RAPPORT DE VALIDATION — exécution standalone
# =============================================================================

if __name__ == "__main__":
    schema = CameraSchema()
    passed = 0
    total = 8

    print("=== CAMERA SCHEMA — RAPPORT DE VALIDATION ===")

    # --- TEST 1 : Complétude presets ---
    t1_ok = True
    required_style_fields = {"description", "default_fov", "distance_mult", "supports_cuts", "supports_shake"}
    for name, style in schema.camera_styles.items():
        missing = required_style_fields - set(style.keys())
        if missing:
            t1_ok = False
            print(f"  ERREUR style '{name}': champs manquants = {sorted(missing)}")
    required_cut_fields = {"fov", "distance_mult", "height_offset", "roll"}
    for name, cut in schema.cut_presets.items():
        missing = required_cut_fields - set(cut.keys())
        if missing:
            t1_ok = False
            print(f"  ERREUR cut '{name}': champs manquants = {sorted(missing)}")
    required_shake_fields = {"description", "strength", "scale", "phase", "offset", "depth", "axes"}
    for name, shake in schema.shake_presets.items():
        missing = required_shake_fields - set(shake.keys())
        if missing:
            t1_ok = False
            print(f"  ERREUR shake '{name}': champs manquants = {sorted(missing)}")
    n_styles = len(schema.camera_styles)
    n_cuts = len(schema.cut_presets)
    n_shakes = len(schema.shake_presets)
    if t1_ok:
        passed += 1
        print(f"[TEST 1] Complétude presets........... ✓ ({n_styles} styles, {n_cuts} cuts, {n_shakes} shakes)")
    else:
        print(f"[TEST 1] Complétude presets........... ✗")

    # --- TEST 2 : Déduplication CUT_PRESETS ---
    t2_ok = True
    expected_cuts = {"wide", "medium", "closeup", "extreme_closeup", "dutch_angle", "low_angle", "high_angle", "over_shoulder"}
    actual_cuts = set(schema.cut_presets.keys())
    if actual_cuts != expected_cuts:
        t2_ok = False
        missing = expected_cuts - actual_cuts
        extra = actual_cuts - expected_cuts
        print(f"  ERREUR cuts: manquants={sorted(missing)}, extras={sorted(extra)}")
    if len(schema.cut_presets) != len(expected_cuts):
        t2_ok = False
        print(f"  ERREUR doublons: {len(schema.cut_presets)} entries vs {len(expected_cuts)} attendus")
    if t2_ok:
        passed += 1
        print(f"[TEST 2] Déduplication cuts........... ✓ ({len(schema.cut_presets)} types, 0 doublons)")
    else:
        print(f"[TEST 2] Déduplication cuts........... ✗")

    # --- TEST 3 : Conversion FOV ---
    t3_ok = True
    focal_60 = schema.fov_to_focal_mm(60.0)
    if not (30.0 <= focal_60 <= 32.5):
        t3_ok = False
        print(f"  ERREUR fov_to_focal_mm(60.0) = {focal_60:.2f} (attendu ~31.2)")
    roundtrip_fov = 47.0
    focal_rt = schema.fov_to_focal_mm(roundtrip_fov)
    fov_back = schema.focal_mm_to_fov(focal_rt)
    if abs(fov_back - roundtrip_fov) > 1e-6:
        t3_ok = False
        print(f"  ERREUR aller-retour: {roundtrip_fov} → {focal_rt:.2f}mm → {fov_back:.4f}° (delta={abs(fov_back - roundtrip_fov):.8f})")
    if t3_ok:
        passed += 1
        print(f"[TEST 3] Conversion FOV............... ✓ (fov60→{focal_60:.1f}mm, roundtrip delta<1e-6)")
    else:
        print(f"[TEST 3] Conversion FOV............... ✗")

    # --- TEST 4 : Perspective lock ---
    t4_ok = True
    ok_4a, dev_4a = schema.validate_perspective_deviation(50.0, 52.0)
    if not ok_4a:
        t4_ok = False
        print(f"  ERREUR 50→52 devrait être OK (dev={dev_4a:.2%})")
    ok_4b, dev_4b = schema.validate_perspective_deviation(50.0, 60.0)
    if ok_4b:
        t4_ok = False
        print(f"  ERREUR 50→60 devrait être FAIL (dev={dev_4b:.2%})")
    if t4_ok:
        passed += 1
        print(f"[TEST 4] Perspective lock............. ✓ (50→52: {dev_4a:.0%} OK, 50→60: {dev_4b:.0%} FAIL)")
    else:
        print(f"[TEST 4] Perspective lock............. ✗")

    # --- TEST 5 : Bust bone ---
    t5_ok = True
    found = schema.find_bust_bone(["Root", "Hips", "mixamorig:Spine2", "Head"])
    if found != "mixamorig:Spine2":
        t5_ok = False
        print(f"  ERREUR find_bust_bone = '{found}' (attendu 'mixamorig:Spine2')")
    not_found = schema.find_bust_bone(["Root", "Hips", "Head"])
    if not_found is not None:
        t5_ok = False
        print(f"  ERREUR find_bust_bone sans match = '{not_found}' (attendu None)")
    if t5_ok:
        passed += 1
        print(f"[TEST 5] Bust bone lookup............. ✓ (mixamorig:Spine2 trouvé, absent→None)")
    else:
        print(f"[TEST 5] Bust bone lookup............. ✗")

    # --- TEST 6 : Style features ---
    t6_ok = True
    feat_match = schema.get_style_features("matchmove")
    if feat_match["requires_fspy"] is not True:
        t6_ok = False
        print(f"  ERREUR matchmove.requires_fspy = {feat_match['requires_fspy']} (attendu True)")
    feat_static = schema.get_style_features("static")
    if feat_static["supports_shake"] is not False:
        t6_ok = False
        print(f"  ERREUR static.supports_shake = {feat_static['supports_shake']} (attendu False)")
    try:
        schema.get_style_features("inexistant")
        t6_ok = False
        print("  ERREUR style inexistant devrait lever ValueError")
    except ValueError:
        pass
    if t6_ok:
        passed += 1
        print(f"[TEST 6] Style features............... ✓ (matchmove.fspy=True, static.shake=False)")
    else:
        print(f"[TEST 6] Style features............... ✗")

    # --- TEST 7 : Darkroom preset ---
    t7_ok = True
    if "darkroom" not in RENDER_PRESETS:
        t7_ok = False
        print("  ERREUR 'darkroom' absent de RENDER_PRESETS")
    else:
        dr = RENDER_PRESETS["darkroom"]
        if dr["samples"] != 128:
            t7_ok = False
            print(f"  ERREUR darkroom.samples = {dr['samples']} (attendu 128)")
        if dr["resolution"] != (1920, 1080):
            t7_ok = False
            print(f"  ERREUR darkroom.resolution = {dr['resolution']} (attendu (1920, 1080))")
        if dr["denoiser"] != "OPENIMAGEDENOISE":
            t7_ok = False
            print(f"  ERREUR darkroom.denoiser = {dr['denoiser']} (attendu OPENIMAGEDENOISE)")
        if dr.get("output_format") != "PNG":
            t7_ok = False
            print(f"  ERREUR darkroom.output_format = {dr.get('output_format')} (attendu PNG)")
        if dr.get("color_depth") != "16":
            t7_ok = False
            print(f"  ERREUR darkroom.color_depth = {dr.get('color_depth')} (attendu 16)")
        if dr["passes"] != ["Combined"]:
            t7_ok = False
            print(f"  ERREUR darkroom.passes = {dr['passes']} (attendu ['Combined'])")
    if t7_ok:
        passed += 1
        print(f"[TEST 7] Darkroom preset.............. ✓ (128 samples, 1080p, OIDN, PNG 16-bit)")
    else:
        print(f"[TEST 7] Darkroom preset.............. ✗")

    # --- TEST 8 : Rejets hérétiques ---
    t8_ok = True
    ok_8a, _ = schema.validate_camera_style("inexistant")
    if ok_8a:
        t8_ok = False
        print("  ERREUR style 'inexistant' devrait être rejeté")
    ok_8b, _ = schema.validate_cut_type("inexistant")
    if ok_8b:
        t8_ok = False
        print("  ERREUR cut 'inexistant' devrait être rejeté")
    ok_8c, _ = schema.validate_lighting_style("inexistant")
    if ok_8c:
        t8_ok = False
        print("  ERREUR lighting 'inexistant' devrait être rejeté")
    ok_8d, _ = schema.validate_camera_style("static")
    if not ok_8d:
        t8_ok = False
        print("  ERREUR style 'static' devrait être accepté")
    if t8_ok:
        passed += 1
        print(f"[TEST 8] Rejets hérétiques............ ✓ (style/cut/lighting inconnus rejetés)")
    else:
        print(f"[TEST 8] Rejets hérétiques............ ✗")

    print(f"=== VALIDATION COMPLÈTE : {passed}/{total} TESTS PASSÉS ===")
