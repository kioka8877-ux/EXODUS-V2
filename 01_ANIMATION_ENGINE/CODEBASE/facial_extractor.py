"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        FACIAL EXTRACTOR — Emotional Intent → 52 ARKit Shape Keys            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de traduction émotionnelle via expression_schema.py (Bible          ║
║  Anatomique).  Convertit facial_animation.json → 52 shape keys ARKit       ║
║  pré-calculées pour Blender.                                                ║
║  ZÉRO EMOCA — Pure Python stdlib + Bible Anatomique.                        ║
║  Couche 1 (Observation) + Couche 2 (Translation) du pipeline V2.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from expression_schema import (
    ARKIT_52_BLENDSHAPES,
    ExpressionSchema,
    VALID_EXPRESSIONS,
    VALID_EYE_STATES,
    VALID_MOUTH_STATES,
)

REQUIRED_SEGMENT_FIELDS = [
    "time_start", "time_end", "expression", "eyes", "mouth",
    "intensity", "apex_time",
]


class EmotionalIntentTranslator:
    """Traduit les segments émotionnels de U00 en shape key data pour Blender.
    Couche 1 (Observation) + Couche 2 (Translation) du pipeline V2."""

    def __init__(self, schema: ExpressionSchema = None):
        self.schema = schema or ExpressionSchema()

    def load_facial_animation(self, json_path: str) -> dict:
        """
        Charge et valide un facial_animation.json de U00.
        Supporte deux formats :
        - Format principal : {"facial_animation": [...], ...}
        - Format legacy    : {"segments": [...], ...}  ← auto-conversion
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"facial_animation.json introuvable: {json_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "facial_animation" in data:
            segments = data["facial_animation"]
        elif "segments" in data:
            print("[TRANSMUTATION:WARN] Format legacy 'segments' détecté — auto-conversion vers 'facial_animation'")
            segments = data["segments"]
            data["facial_animation"] = segments
        else:
            raise ValueError("Clé 'facial_animation' ou 'segments' absente du JSON")

        if not isinstance(segments, list) or len(segments) == 0:
            raise ValueError("Les segments doivent être une liste non vide")

        for i, seg in enumerate(segments):
            for field in REQUIRED_SEGMENT_FIELDS:
                if field not in seg:
                    raise ValueError(f"Segment {i}: champ '{field}' manquant")

            ok, errs = self.schema.validate_expression_request(
                seg["expression"], seg["eyes"], seg["mouth"], seg["intensity"]
            )
            if not ok:
                raise ValueError(f"Segment {i}: {errs}")

            if seg["apex_time"] < seg["time_start"] or seg["apex_time"] > seg["time_end"]:
                raise ValueError(
                    f"Segment {i}: apex_time ({seg['apex_time']}) "
                    f"hors bornes [{seg['time_start']}, {seg['time_end']}]"
                )

        return data

    def translate_segment(self, segment: dict) -> dict:
        """Traduit un segment émotionnel en 52 shape key values.
        Utilise schema.fuse_expression() pour combiner expression + eyes + mouth.
        Gère low_visibility: si True, force expression='neutral', intensity=0.2"""
        expression = segment["expression"]
        eyes = segment["eyes"]
        mouth = segment["mouth"]
        intensity = segment["intensity"]

        if segment.get("low_visibility", False):
            expression = "neutral"
            intensity = min(0.2, intensity)

        values = self.schema.fuse_expression(
            expression_id=expression,
            eye_id=eyes,
            mouth_id=mouth,
            intensity=intensity,
        )

        return {
            "values": values,
            "time_start": segment["time_start"],
            "time_end": segment["time_end"],
            "apex_time": segment["apex_time"],
        }

    def translate_all(self, facial_data: dict, fps: int = 30) -> list:
        """Traduit tous les segments en une liste de keyframe data.
        Gère les transitions entre segments:
        - Si deux segments consécutifs ont des émotions opposées
          (via schema.requires_neutral_transition), insérer un segment neutre
          intermédiaire.
        - Retourne une liste de dicts prêts pour blender_fusion.py"""
        segments = facial_data.get("facial_animation") or facial_data.get("segments", [])
        translated: List[dict] = []

        for i, seg in enumerate(segments):
            if i > 0:
                prev_expr = segments[i - 1].get("expression", "neutral")
                if segments[i - 1].get("low_visibility", False):
                    prev_expr = "neutral"
                curr_expr = seg["expression"]
                if seg.get("low_visibility", False):
                    curr_expr = "neutral"

                if self.schema.requires_neutral_transition(prev_expr, curr_expr):
                    prev_end = segments[i - 1]["time_end"]
                    curr_start = seg["time_start"]
                    mid_time = (prev_end + curr_start) / 2.0
                    neutral_seg = {
                        "expression": "neutral",
                        "eyes": "focused_forward",
                        "mouth": "neutral",
                        "intensity": 0.3,
                        "time_start": prev_end,
                        "time_end": curr_start,
                        "apex_time": mid_time,
                        "low_visibility": False,
                    }
                    neutral_data = self.translate_segment(neutral_seg)
                    neutral_data["is_transition"] = True
                    translated.append(neutral_data)

            seg_data = self.translate_segment(seg)
            seg_data["is_transition"] = False
            translated.append(seg_data)

        return translated

    def generate_blender_data(self, facial_data: dict, fps: int = 30) -> dict:
        """Point d'entrée principal. Retourne un dict structuré pour blender_fusion.py:
        {
            "fps": 30,
            "segments": [
                {
                    "frame_start": 0,
                    "frame_end": 75,
                    "frame_apex": 36,
                    "values": {52 ARKit keys},
                    "is_transition": false
                },
                ...
            ],
            "micro_expressions": schema.get_micro_expression_presets()
        }
        """
        translated = self.translate_all(facial_data, fps=fps)
        segments: List[dict] = []

        for seg in translated:
            frame_start = int(round(seg["time_start"] * fps))
            frame_end = int(round(seg["time_end"] * fps))
            frame_apex = int(round(seg["apex_time"] * fps))
            segments.append({
                "frame_start": frame_start,
                "frame_end": frame_end,
                "frame_apex": frame_apex,
                "values": seg["values"],
                "is_transition": seg.get("is_transition", False),
            })

        return {
            "fps": fps,
            "segments": segments,
            "micro_expressions": self.schema.get_micro_expression_presets(),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  EMOTIONAL INTENT TRANSLATOR — Test Standalone")
    print("=" * 60)

    sample_data = {
        "sequence_id": "ACTOR_01",
        "facial_animation": [
            {
                "time_start": 0.0,
                "time_end": 2.5,
                "expression": "determined",
                "eyes": "focused_forward",
                "mouth": "closed_tight",
                "intensity": 0.8,
                "apex_time": 1.2,
                "low_visibility": False,
            },
            {
                "time_start": 2.5,
                "time_end": 5.0,
                "expression": "joy",
                "eyes": "narrowed",
                "mouth": "smiling",
                "intensity": 0.9,
                "apex_time": 3.8,
                "low_visibility": False,
            },
            {
                "time_start": 5.0,
                "time_end": 7.0,
                "expression": "sadness",
                "eyes": "looking_down",
                "mouth": "frowning",
                "intensity": 0.6,
                "apex_time": 6.0,
                "low_visibility": False,
            },
        ],
    }

    translator = EmotionalIntentTranslator()
    blender_data = translator.generate_blender_data(sample_data, fps=30)

    print(f"\nFPS: {blender_data['fps']}")
    print(f"Segments: {len(blender_data['segments'])}")
    print(f"Micro-expressions: {list(blender_data['micro_expressions'].keys())}")

    for i, seg in enumerate(blender_data["segments"]):
        tag = " [TRANSITION]" if seg["is_transition"] else ""
        print(f"\n--- Segment {i}{tag} ---")
        print(f"  Frames: {seg['frame_start']} -> {seg['frame_end']} (apex: {seg['frame_apex']})")
        active_keys = {k: v for k, v in seg["values"].items() if v > 0.0}
        print(f"  Active keys ({len(active_keys)}):")
        for k, v in sorted(active_keys.items(), key=lambda x: -x[1]):
            print(f"    {k:30s} = {v:.4f}")

    print(f"\n{'=' * 60}")
    print("  TEST COMPLET")
    print(f"{'=' * 60}")
