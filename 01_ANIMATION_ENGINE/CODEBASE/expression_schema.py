"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 01_TRANSMUTATION — EXPRESSION SCHEMA (Bible Anatomique)          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de données pures : définit TOUTES les données nécessaires à la     ║
║  traduction émotion → 52 ARKit Shape Keys pour avatars Roblox DynamicHead. ║
║  Zéro dépendance Blender. Zéro traitement. Données + Validation.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Dict, List, Tuple, Optional


# =============================================================================
# CONSTANTE CANONIQUE — 52 ARKit Blendshapes
# =============================================================================

ARKIT_52_BLENDSHAPES: List[str] = [
    "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight", "eyeSquintLeft", "eyeSquintRight",
    "eyeWideLeft", "eyeWideRight",
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    "noseSneerLeft", "noseSneerRight",
    "tongueOut"
]

_ZERO_52: Dict[str, float] = {k: 0.0 for k in ARKIT_52_BLENDSHAPES}

EYE_KEYS: List[str] = [
    "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight", "eyeSquintLeft", "eyeSquintRight",
    "eyeWideLeft", "eyeWideRight",
]

MOUTH_KEYS: List[str] = [
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "tongueOut",
]


# =============================================================================
# PILIER 1 — EXPRESSION_PRESETS (15 émotions × 52 keys)
# =============================================================================

def _preset(overrides: Dict[str, float]) -> Dict[str, float]:
    """Crée un preset 52-keys à partir d'un dict partiel sur base neutre."""
    p = dict(_ZERO_52)
    p.update(overrides)
    return p


EXPRESSION_PRESETS: Dict[str, Dict[str, float]] = {
    "neutral": _preset({}),

    "joy": _preset({
        "mouthSmileLeft": 0.8, "mouthSmileRight": 0.8,
        "cheekSquintLeft": 0.6, "cheekSquintRight": 0.6,
        "eyeSquintLeft": 0.3, "eyeSquintRight": 0.3,
        "mouthDimpleLeft": 0.3, "mouthDimpleRight": 0.3,
        "mouthUpperUpLeft": 0.15, "mouthUpperUpRight": 0.15,
        "browInnerUp": 0.1,
    }),

    "sadness": _preset({
        "mouthFrownLeft": 0.7, "mouthFrownRight": 0.7,
        "browInnerUp": 0.65, "browDownLeft": 0.15, "browDownRight": 0.15,
        "eyeLookDownLeft": 0.3, "eyeLookDownRight": 0.3,
        "eyeSquintLeft": 0.2, "eyeSquintRight": 0.2,
        "mouthPressLeft": 0.2, "mouthPressRight": 0.2,
        "mouthStretchLeft": 0.15, "mouthStretchRight": 0.15,
        "mouthRollLower": 0.2,
    }),

    "anger": _preset({
        "browDownLeft": 0.8, "browDownRight": 0.8,
        "eyeSquintLeft": 0.5, "eyeSquintRight": 0.5,
        "noseSneerLeft": 0.55, "noseSneerRight": 0.55,
        "jawOpen": 0.25,
        "mouthFrownLeft": 0.3, "mouthFrownRight": 0.3,
        "mouthPressLeft": 0.4, "mouthPressRight": 0.4,
        "mouthUpperUpLeft": 0.2, "mouthUpperUpRight": 0.2,
        "mouthShrugLower": 0.15,
    }),

    "fear": _preset({
        "eyeWideLeft": 0.85, "eyeWideRight": 0.85,
        "browInnerUp": 0.8, "browOuterUpLeft": 0.4, "browOuterUpRight": 0.4,
        "jawOpen": 0.35,
        "mouthStretchLeft": 0.4, "mouthStretchRight": 0.4,
        "mouthFrownLeft": 0.2, "mouthFrownRight": 0.2,
        "mouthLowerDownLeft": 0.25, "mouthLowerDownRight": 0.25,
    }),

    "surprise": _preset({
        "eyeWideLeft": 1.0, "eyeWideRight": 1.0,
        "browInnerUp": 0.9, "browOuterUpLeft": 0.8, "browOuterUpRight": 0.8,
        "jawOpen": 0.6,
        "mouthFunnel": 0.45,
        "mouthShrugUpper": 0.2,
        "mouthLowerDownLeft": 0.15, "mouthLowerDownRight": 0.15,
    }),

    "disgust": _preset({
        "noseSneerLeft": 0.85, "noseSneerRight": 0.85,
        "mouthFrownLeft": 0.5, "mouthFrownRight": 0.5,
        "browDownLeft": 0.55, "browDownRight": 0.55,
        "mouthUpperUpLeft": 0.6, "mouthUpperUpRight": 0.6,
        "eyeSquintLeft": 0.35, "eyeSquintRight": 0.35,
        "mouthShrugLower": 0.25, "mouthShrugUpper": 0.15,
        "mouthRollLower": 0.15,
    }),

    "suspicious": _preset({
        "eyeSquintLeft": 0.7, "eyeSquintRight": 0.45,
        "browDownLeft": 0.6, "browDownRight": 0.3,
        "mouthPucker": 0.2,
        "mouthLeft": 0.15,
        "mouthPressLeft": 0.25, "mouthPressRight": 0.15,
        "noseSneerLeft": 0.15,
        "jawForward": 0.1,
    }),

    "determined": _preset({
        "browDownLeft": 0.4, "browDownRight": 0.4,
        "eyeSquintLeft": 0.25, "eyeSquintRight": 0.25,
        "mouthPressLeft": 0.5, "mouthPressRight": 0.5,
        "jawForward": 0.15,
        "mouthClose": 0.3,
        "noseSneerLeft": 0.1, "noseSneerRight": 0.1,
        "mouthShrugLower": 0.1,
    }),

    "confused": _preset({
        "browInnerUp": 0.6,
        "browOuterUpLeft": 0.35, "browOuterUpRight": 0.1,
        "eyeWideLeft": 0.2, "eyeWideRight": 0.35,
        "mouthLeft": 0.3,
        "mouthFrownLeft": 0.15, "mouthFrownRight": 0.25,
        "mouthPucker": 0.1,
        "eyeSquintLeft": 0.15,
    }),

    "pain": _preset({
        "eyeSquintLeft": 0.8, "eyeSquintRight": 0.8,
        "browInnerUp": 0.7, "browDownLeft": 0.5, "browDownRight": 0.5,
        "mouthStretchLeft": 0.6, "mouthStretchRight": 0.6,
        "jawOpen": 0.4,
        "noseSneerLeft": 0.35, "noseSneerRight": 0.35,
        "mouthFrownLeft": 0.3, "mouthFrownRight": 0.3,
        "mouthUpperUpLeft": 0.25, "mouthUpperUpRight": 0.25,
        "cheekSquintLeft": 0.3, "cheekSquintRight": 0.3,
    }),

    "love": _preset({
        "mouthSmileLeft": 0.55, "mouthSmileRight": 0.55,
        "eyeSquintLeft": 0.35, "eyeSquintRight": 0.35,
        "cheekSquintLeft": 0.3, "cheekSquintRight": 0.3,
        "cheekPuff": 0.1,
        "browInnerUp": 0.25,
        "mouthDimpleLeft": 0.2, "mouthDimpleRight": 0.2,
        "mouthPressLeft": 0.1, "mouthPressRight": 0.1,
    }),

    "bored": _preset({
        "eyeLookDownLeft": 0.4, "eyeLookDownRight": 0.4,
        "eyeBlinkLeft": 0.15, "eyeBlinkRight": 0.15,
        "mouthFrownLeft": 0.2, "mouthFrownRight": 0.2,
        "browDownLeft": 0.2, "browDownRight": 0.2,
        "mouthRollLower": 0.15,
        "jawOpen": 0.05,
        "mouthShrugLower": 0.1,
    }),

    "excited": _preset({
        "mouthSmileLeft": 1.0, "mouthSmileRight": 1.0,
        "eyeWideLeft": 0.6, "eyeWideRight": 0.6,
        "browOuterUpLeft": 0.5, "browOuterUpRight": 0.5,
        "browInnerUp": 0.4,
        "cheekSquintLeft": 0.7, "cheekSquintRight": 0.7,
        "mouthDimpleLeft": 0.4, "mouthDimpleRight": 0.4,
        "jawOpen": 0.3,
        "mouthUpperUpLeft": 0.2, "mouthUpperUpRight": 0.2,
    }),

    "shocked": _preset({
        "eyeWideLeft": 1.0, "eyeWideRight": 1.0,
        "browInnerUp": 0.95, "browOuterUpLeft": 0.85, "browOuterUpRight": 0.85,
        "jawOpen": 0.75,
        "mouthFunnel": 0.3,
        "mouthStretchLeft": 0.25, "mouthStretchRight": 0.25,
        "mouthLowerDownLeft": 0.3, "mouthLowerDownRight": 0.3,
        "mouthShrugUpper": 0.15,
    }),
}


# =============================================================================
# PILIER 2 — MATRICE DES CONFLITS
# =============================================================================

CONFLICTS: Dict[str, List[str]] = {
    "mouthSmileLeft": ["mouthFrownLeft", "mouthPucker", "mouthFunnel"],
    "mouthSmileRight": ["mouthFrownRight", "mouthPucker", "mouthFunnel"],
    "mouthFrownLeft": ["mouthSmileLeft"],
    "mouthFrownRight": ["mouthSmileRight"],
    "eyeBlinkLeft": ["eyeWideLeft"],
    "eyeBlinkRight": ["eyeWideRight"],
    "eyeWideLeft": ["eyeBlinkLeft"],
    "eyeWideRight": ["eyeBlinkRight"],
    "jawOpen": ["mouthClose"],
    "mouthClose": ["jawOpen"],
    "mouthPucker": ["mouthSmileLeft", "mouthSmileRight", "mouthFunnel"],
    "mouthFunnel": ["mouthSmileLeft", "mouthSmileRight", "mouthPucker"],
    "eyeLookUpLeft": ["eyeLookDownLeft"],
    "eyeLookUpRight": ["eyeLookDownRight"],
    "eyeLookDownLeft": ["eyeLookUpLeft"],
    "eyeLookDownRight": ["eyeLookUpRight"],
    "eyeLookInLeft": ["eyeLookOutLeft"],
    "eyeLookOutLeft": ["eyeLookInLeft"],
    "eyeLookInRight": ["eyeLookOutRight"],
    "eyeLookOutRight": ["eyeLookInRight"],
    "jawLeft": ["jawRight"],
    "jawRight": ["jawLeft"],
}


# =============================================================================
# PILIER 3 — TABLE DES OPPOSITIONS
# =============================================================================

OPPOSING_EMOTIONS: List[Tuple[str, str]] = [
    ("joy", "sadness"),
    ("joy", "anger"),
    ("anger", "fear"),
    ("surprise", "bored"),
    ("love", "disgust"),
    ("excited", "bored"),
]


# =============================================================================
# PILIER 4 — RANGES ANATOMIQUES
# =============================================================================

ANATOMICAL_RANGES: Dict[str, Tuple[float, float]] = {k: (0.0, 1.0) for k in ARKIT_52_BLENDSHAPES}
ANATOMICAL_RANGES["jawOpen"] = (0.0, 0.8)
ANATOMICAL_RANGES["jawForward"] = (0.0, 0.5)
ANATOMICAL_RANGES["jawLeft"] = (0.0, 0.6)
ANATOMICAL_RANGES["jawRight"] = (0.0, 0.6)
ANATOMICAL_RANGES["tongueOut"] = (0.0, 0.5)
ANATOMICAL_RANGES["mouthStretchLeft"] = (0.0, 0.7)
ANATOMICAL_RANGES["mouthStretchRight"] = (0.0, 0.7)
ANATOMICAL_RANGES["cheekPuff"] = (0.0, 0.8)


# =============================================================================
# PILIER 5 — COURBES D'INTENSITÉ (constantes de mode)
# =============================================================================

INTENSITY_MODES: List[str] = ["linear", "quadratic", "ease_in_out"]


# =============================================================================
# PILIER 6 — MICRO-EXPRESSIONS INVOLONTAIRES
# =============================================================================

MICRO_EXPRESSION_PRESETS: Dict[str, dict] = {
    "eye_blink": {
        "target_keys": ["eyeBlinkLeft", "eyeBlinkRight"],
        "amplitude": 0.02,
        "frequency_hz": 0.3,
        "description": "Clignotement naturel",
    },
    "eye_dart": {
        "target_keys": ["eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight"],
        "amplitude": 0.015,
        "frequency_hz": 2.0,
        "description": "Micro-mouvements oculaires",
    },
    "mouth_twitch": {
        "target_keys": ["mouthLeft", "mouthRight", "mouthDimpleLeft", "mouthDimpleRight"],
        "amplitude": 0.01,
        "frequency_hz": 0.5,
        "description": "Micro-tics buccaux",
    },
    "brow_micro": {
        "target_keys": ["browInnerUp", "browOuterUpLeft", "browOuterUpRight"],
        "amplitude": 0.015,
        "frequency_hz": 0.2,
        "description": "Micro-mouvements sourciliers",
    },
}


# =============================================================================
# PILIER 7 — EYE_PRESETS (9 états) + MOUTH_PRESETS (8 états)
# =============================================================================

_ZERO_EYES: Dict[str, float] = {k: 0.0 for k in EYE_KEYS}
_ZERO_MOUTH: Dict[str, float] = {k: 0.0 for k in MOUTH_KEYS}


def _eye(overrides: Dict[str, float]) -> Dict[str, float]:
    p = dict(_ZERO_EYES)
    p.update(overrides)
    return p


def _mouth(overrides: Dict[str, float]) -> Dict[str, float]:
    p = dict(_ZERO_MOUTH)
    p.update(overrides)
    return p


EYE_PRESETS: Dict[str, Dict[str, float]] = {
    "focused_forward": _eye({}),

    "looking_left": _eye({
        "eyeLookOutLeft": 0.8, "eyeLookInRight": 0.8,
    }),

    "looking_right": _eye({
        "eyeLookInLeft": 0.8, "eyeLookOutRight": 0.8,
    }),

    "looking_up": _eye({
        "eyeLookUpLeft": 0.75, "eyeLookUpRight": 0.75,
    }),

    "looking_down": _eye({
        "eyeLookDownLeft": 0.75, "eyeLookDownRight": 0.75,
    }),

    "narrowed": _eye({
        "eyeSquintLeft": 0.7, "eyeSquintRight": 0.7,
    }),

    "wide_open": _eye({
        "eyeWideLeft": 0.85, "eyeWideRight": 0.85,
    }),

    "closed": _eye({
        "eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0,
    }),

    "winking": _eye({
        "eyeBlinkLeft": 0.9, "eyeBlinkRight": 0.0,
        "eyeSquintRight": 0.15,
    }),
}

MOUTH_PRESETS: Dict[str, Dict[str, float]] = {
    "closed_tight": _mouth({
        "mouthClose": 0.6,
        "mouthPressLeft": 0.5, "mouthPressRight": 0.5,
        "mouthRollLower": 0.2, "mouthRollUpper": 0.2,
    }),

    "slightly_open": _mouth({
        "jawOpen": 0.15,
        "mouthLowerDownLeft": 0.1, "mouthLowerDownRight": 0.1,
    }),

    "wide_open": _mouth({
        "jawOpen": 0.75,
        "mouthLowerDownLeft": 0.4, "mouthLowerDownRight": 0.4,
        "mouthStretchLeft": 0.3, "mouthStretchRight": 0.3,
    }),

    "smiling": _mouth({
        "mouthSmileLeft": 0.85, "mouthSmileRight": 0.85,
        "mouthDimpleLeft": 0.3, "mouthDimpleRight": 0.3,
        "mouthUpperUpLeft": 0.1, "mouthUpperUpRight": 0.1,
    }),

    "frowning": _mouth({
        "mouthFrownLeft": 0.7, "mouthFrownRight": 0.7,
        "mouthPressLeft": 0.2, "mouthPressRight": 0.2,
        "mouthStretchLeft": 0.15, "mouthStretchRight": 0.15,
    }),

    "pursed_lips": _mouth({
        "mouthPucker": 0.75,
        "mouthFunnel": 0.2,
        "mouthRollLower": 0.15, "mouthRollUpper": 0.15,
    }),

    "shouting": _mouth({
        "jawOpen": 0.8,
        "mouthStretchLeft": 0.5, "mouthStretchRight": 0.5,
        "mouthLowerDownLeft": 0.5, "mouthLowerDownRight": 0.5,
        "mouthUpperUpLeft": 0.35, "mouthUpperUpRight": 0.35,
        "mouthShrugLower": 0.2, "mouthShrugUpper": 0.15,
    }),

    "neutral": _mouth({}),
}


# =============================================================================
# ENUMS DE VALIDATION
# =============================================================================

VALID_EXPRESSIONS: List[str] = [
    "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral",
    "suspicious", "determined", "confused", "pain", "love", "bored",
    "excited", "shocked",
]

VALID_EYE_STATES: List[str] = [
    "focused_forward", "looking_left", "looking_right", "looking_up",
    "looking_down", "narrowed", "wide_open", "closed", "winking",
]

VALID_MOUTH_STATES: List[str] = [
    "closed_tight", "slightly_open", "wide_open", "smiling", "frowning",
    "pursed_lips", "shouting", "neutral",
]


# =============================================================================
# CLASSE PRINCIPALE — ExpressionSchema
# =============================================================================

class ExpressionSchema:
    """Bible Anatomique de U01 — encapsule les 7 piliers de données faciales
    et toutes les fonctions de validation / fusion / intensité."""

    def __init__(self) -> None:
        self.expression_presets: Dict[str, Dict[str, float]] = dict(EXPRESSION_PRESETS)
        self.eye_presets: Dict[str, Dict[str, float]] = dict(EYE_PRESETS)
        self.mouth_presets: Dict[str, Dict[str, float]] = dict(MOUTH_PRESETS)
        self.conflicts: Dict[str, List[str]] = dict(CONFLICTS)
        self.opposing_emotions: List[Tuple[str, str]] = list(OPPOSING_EMOTIONS)
        self.anatomical_ranges: Dict[str, Tuple[float, float]] = dict(ANATOMICAL_RANGES)
        self.micro_expression_presets: Dict[str, dict] = dict(MICRO_EXPRESSION_PRESETS)

    # -----------------------------------------------------------------
    # Extensibilité — injection de presets
    # -----------------------------------------------------------------

    def add_expression_preset(self, name: str, values: Dict[str, float]) -> None:
        """Ajoute ou remplace un preset d'expression (doit contenir 52 keys)."""
        missing = set(ARKIT_52_BLENDSHAPES) - set(values.keys())
        if missing:
            raise ValueError(f"Preset '{name}' incomplet — keys manquantes : {sorted(missing)}")
        self.expression_presets[name] = {k: float(values[k]) for k in ARKIT_52_BLENDSHAPES}

    def add_eye_preset(self, name: str, values: Dict[str, float]) -> None:
        """Ajoute ou remplace un preset oculaire (14 keys oculaires)."""
        invalid = set(values.keys()) - set(EYE_KEYS)
        if invalid:
            raise ValueError(f"Eye preset '{name}' contient des keys invalides : {sorted(invalid)}")
        full = dict(_ZERO_EYES)
        full.update(values)
        self.eye_presets[name] = full

    def add_mouth_preset(self, name: str, values: Dict[str, float]) -> None:
        """Ajoute ou remplace un preset buccal (28 keys buccales + jaw)."""
        invalid = set(values.keys()) - set(MOUTH_KEYS)
        if invalid:
            raise ValueError(f"Mouth preset '{name}' contient des keys invalides : {sorted(invalid)}")
        full = dict(_ZERO_MOUTH)
        full.update(values)
        self.mouth_presets[name] = full

    # -----------------------------------------------------------------
    # PILIER 5 — Courbes d'intensité
    # -----------------------------------------------------------------

    def apply_intensity(
        self,
        preset_values: Dict[str, float],
        intensity: float,
        mode: str = "ease_in_out",
    ) -> Dict[str, float]:
        """Applique une courbe d'intensité sur un dict de shape key values.

        Modes :
            linear      — value * intensity
            quadratic   — value * intensity²
            ease_in_out — value * smoothstep(intensity)  [3t² − 2t³]

        Retourne un nouveau dict avec valeurs clampées à [0.0, 1.0].
        """
        t = max(0.0, min(1.0, intensity))
        if mode == "linear":
            factor = t
        elif mode == "quadratic":
            factor = t * t
        elif mode == "ease_in_out":
            factor = 3.0 * t * t - 2.0 * t * t * t
        else:
            raise ValueError(f"Mode d'intensité inconnu : '{mode}'. Valides : {INTENSITY_MODES}")
        return {k: max(0.0, min(1.0, v * factor)) for k, v in preset_values.items()}

    # -----------------------------------------------------------------
    # PILIER 4 — Clamp anatomique
    # -----------------------------------------------------------------

    def clamp_to_ranges(self, shape_key_values: Dict[str, float]) -> Dict[str, float]:
        """Clampe chaque valeur dans son range anatomique Roblox."""
        result = {}
        for k, v in shape_key_values.items():
            lo, hi = self.anatomical_ranges.get(k, (0.0, 1.0))
            result[k] = max(lo, min(hi, v))
        return result

    # -----------------------------------------------------------------
    # PILIER 2 — Validation des conflits
    # -----------------------------------------------------------------

    def validate_no_conflicts(
        self, shape_key_values: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """Détecte les conflits anatomiques (deux keys incompatibles > 0.3).

        Retourne (True, []) si OK, (False, [messages]) sinon.
        """
        errors: List[str] = []
        seen: set = set()
        for key, incompatibles in self.conflicts.items():
            val_a = shape_key_values.get(key, 0.0)
            if val_a <= 0.3:
                continue
            for other in incompatibles:
                pair = tuple(sorted((key, other)))
                if pair in seen:
                    continue
                val_b = shape_key_values.get(other, 0.0)
                if val_b > 0.3:
                    errors.append(f"{key} conflicts with {other}")
                    seen.add(pair)
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # PILIER 3 — Transition neutre obligatoire
    # -----------------------------------------------------------------

    def requires_neutral_transition(
        self, emotion_from: str, emotion_to: str
    ) -> bool:
        """Retourne True si la transition directe entre ces deux émotions
        est interdite et doit passer par neutre."""
        for a, b in self.opposing_emotions:
            if (emotion_from == a and emotion_to == b) or (
                emotion_from == b and emotion_to == a
            ):
                return True
        return False

    # -----------------------------------------------------------------
    # Validation de requête
    # -----------------------------------------------------------------

    def validate_expression_request(
        self,
        expression: str,
        eyes: str,
        mouth: str,
        intensity: float,
    ) -> Tuple[bool, List[str]]:
        """Valide une requête d'expression complète.

        Retourne (True, []) ou (False, [erreurs]).
        """
        errors: List[str] = []
        if expression not in self.expression_presets:
            errors.append(f"Unknown expression: {expression}")
        if eyes not in self.eye_presets:
            errors.append(f"Unknown eye state: {eyes}")
        if mouth not in self.mouth_presets:
            errors.append(f"Unknown mouth state: {mouth}")
        if not (0.0 <= intensity <= 1.0):
            errors.append(f"Intensity out of range [0.0, 1.0]: {intensity}")
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # PILIER 6 — Accès micro-expressions
    # -----------------------------------------------------------------

    def get_micro_expression_presets(self) -> Dict[str, dict]:
        """Retourne une copie des presets de micro-expressions."""
        return dict(self.micro_expression_presets)

    # -----------------------------------------------------------------
    # PILIER 7 — Fusion expression + eyes + mouth
    # -----------------------------------------------------------------

    def fuse_expression(
        self,
        expression_id: str,
        eye_id: str,
        mouth_id: str,
        intensity: float = 1.0,
        intensity_mode: str = "ease_in_out",
    ) -> Dict[str, float]:
        """Fusionne un preset d'expression avec des overrides oculaires et buccaux.

        Pipeline :
            1. Charger EXPRESSION_PRESETS[expression_id] (52 keys)
            2. Appliquer l'intensité via apply_intensity()
            3. Override zone oculaire avec EYE_PRESETS[eye_id]
            4. Override zone buccale avec MOUTH_PRESETS[mouth_id]
            5. Clamp via clamp_to_ranges()
            6. Résoudre conflits (eyes/mouth gagnent sur expression)
            7. Retourner 52 valeurs propres
        """
        ok, errs = self.validate_expression_request(expression_id, eye_id, mouth_id, intensity)
        if not ok:
            raise ValueError(f"Requête invalide : {errs}")

        base = dict(self.expression_presets[expression_id])
        scaled = self.apply_intensity(base, intensity, intensity_mode)

        eye_override = self.eye_presets[eye_id]
        for k in EYE_KEYS:
            scaled[k] = eye_override[k]

        mouth_override = self.mouth_presets[mouth_id]
        for k in MOUTH_KEYS:
            scaled[k] = mouth_override[k]

        clamped = self.clamp_to_ranges(scaled)

        valid, conflicts = self.validate_no_conflicts(clamped)
        if not valid:
            override_keys = set(EYE_KEYS) | set(MOUTH_KEYS)
            for msg in conflicts:
                parts = msg.split(" conflicts with ")
                key_a, key_b = parts[0], parts[1]
                a_is_override = key_a in override_keys
                b_is_override = key_b in override_keys
                if a_is_override and not b_is_override:
                    clamped[key_b] = 0.0
                elif b_is_override and not a_is_override:
                    clamped[key_a] = 0.0
                elif a_is_override and b_is_override:
                    pass
                else:
                    clamped[key_b] = 0.0

        return clamped


# =============================================================================
# RAPPORT DE VALIDATION — exécution standalone
# =============================================================================

if __name__ == "__main__":
    schema = ExpressionSchema()
    passed = 0
    total = 7

    print("=== EXPRESSION SCHEMA — RAPPORT DE VALIDATION ===")

    # --- TEST 1 : Complétude presets ---
    t1_ok = True
    for name, preset in schema.expression_presets.items():
        if set(preset.keys()) != set(ARKIT_52_BLENDSHAPES):
            t1_ok = False
            missing = set(ARKIT_52_BLENDSHAPES) - set(preset.keys())
            extra = set(preset.keys()) - set(ARKIT_52_BLENDSHAPES)
            print(f"  ERREUR preset '{name}': manquantes={missing}, extras={extra}")
    n_expr = len(schema.expression_presets)
    n_keys = len(ARKIT_52_BLENDSHAPES)
    if t1_ok:
        passed += 1
        print(f"[TEST 1] Complétude presets........... ✓ ({n_expr} expressions × {n_keys} keys)")
    else:
        print(f"[TEST 1] Complétude presets........... ✗")

    # --- TEST 2 : Ranges anatomiques ---
    violations = 0
    for name, preset in schema.expression_presets.items():
        for k, v in preset.items():
            lo, hi = schema.anatomical_ranges.get(k, (0.0, 1.0))
            if v < lo - 1e-9 or v > hi + 1e-9:
                violations += 1
                print(f"  ERREUR range '{name}'.{k} = {v} hors [{lo}, {hi}]")
    if violations == 0:
        passed += 1
        print(f"[TEST 2] Ranges anatomiques........... ✓ ({violations} violations)")
    else:
        print(f"[TEST 2] Ranges anatomiques........... ✗ ({violations} violations)")

    # --- TEST 3 : Conflits presets natifs ---
    total_conflicts = 0
    for name, preset in schema.expression_presets.items():
        ok, errs = schema.validate_no_conflicts(preset)
        if not ok:
            total_conflicts += len(errs)
            for e in errs:
                print(f"  ERREUR conflit '{name}': {e}")
    if total_conflicts == 0:
        passed += 1
        print(f"[TEST 3] Conflits presets natifs...... ✓ ({total_conflicts} conflits)")
    else:
        print(f"[TEST 3] Conflits presets natifs...... ✗ ({total_conflicts} conflits)")

    # --- TEST 4 : Oppositions ---
    t4_ok = schema.requires_neutral_transition("joy", "anger")
    t4_ok = t4_ok and schema.requires_neutral_transition("anger", "joy")
    t4_ok = t4_ok and not schema.requires_neutral_transition("joy", "surprise")
    if t4_ok:
        passed += 1
        print("[TEST 4] Oppositions émotionnelles.... ✓ (transitions vérifiées)")
    else:
        print("[TEST 4] Oppositions émotionnelles.... ✗")

    # --- TEST 5 : Expressions hérétiques ---
    t5_ok = True
    _, errs5a = schema.validate_expression_request("inexistant", "focused_forward", "neutral", 0.5)
    if not errs5a:
        t5_ok = False
    _, errs5b = schema.validate_expression_request("joy", "focused_forward", "neutral", 1.5)
    if not errs5b:
        t5_ok = False
    conflict_dict = dict(_ZERO_52)
    conflict_dict["mouthSmileLeft"] = 0.9
    conflict_dict["mouthFrownLeft"] = 0.9
    ok5c, errs5c = schema.validate_no_conflicts(conflict_dict)
    if ok5c:
        t5_ok = False
    if t5_ok:
        passed += 1
        print("[TEST 5] Expressions hérétiques....... ✓ (rejets corrects)")
    else:
        print("[TEST 5] Expressions hérétiques....... ✗")

    # --- TEST 6 : Fusion ---
    t6_ok = True
    try:
        fused = schema.fuse_expression(
            expression_id="determined",
            eye_id="narrowed",
            mouth_id="closed_tight",
            intensity=0.8,
            intensity_mode="ease_in_out",
        )
        if len(fused) != 52:
            t6_ok = False
        for k, v in fused.items():
            lo, hi = schema.anatomical_ranges.get(k, (0.0, 1.0))
            if v < lo - 1e-9 or v > hi + 1e-9:
                t6_ok = False
    except Exception as exc:
        t6_ok = False
        print(f"  ERREUR fusion : {exc}")
    if t6_ok:
        passed += 1
        print("[TEST 6] Fusion expression............ ✓ (52 keys, ranges OK)")
        print("         Résultat fusion determined+narrowed+closed_tight @0.8 :")
        for k in ARKIT_52_BLENDSHAPES:
            v = fused[k]
            if v > 0.0:
                print(f"           {k:30s} = {v:.4f}")
    else:
        print("[TEST 6] Fusion expression............ ✗")

    # --- TEST 7 : Comparaison intensité ---
    t7_ok = True
    test_preset = {"test_key": 0.8}
    r_lin = schema.apply_intensity(test_preset, 0.5, "linear")["test_key"]
    r_quad = schema.apply_intensity(test_preset, 0.5, "quadratic")["test_key"]
    r_ease = schema.apply_intensity(test_preset, 0.5, "ease_in_out")["test_key"]
    if not (r_quad < r_lin):
        t7_ok = False
    if not (abs(r_ease - r_lin) < 0.5):
        t7_ok = False
    if t7_ok:
        passed += 1
        print(f"[TEST 7] Courbes d'intensité.......... ✓")
        print(f"         intensity=0.5, base=0.8 → linear={r_lin:.4f}  quadratic={r_quad:.4f}  ease_in_out={r_ease:.4f}")
    else:
        print(f"[TEST 7] Courbes d'intensité.......... ✗")

    print(f"=== VALIDATION COMPLÈTE : {passed}/{total} TESTS PASSÉS ===")
