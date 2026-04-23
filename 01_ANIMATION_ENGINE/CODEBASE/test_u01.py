"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     TEST SUITE — FRÉGATE 01 ANIMATION ENGINE                                ║
║     VOX Protocol — Pytest — Codex Imperial v6                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Modules testés:                                                             ║
║    expression_schema.py   — Bible Anatomique (7 Piliers)                    ║
║    facial_extractor.py    — EmotionalIntentTranslator                       ║
║    smoothing.py           — Savitzky-Golay + Adaptive                       ║
║    pyannote_diarizer.py   — Alias + SpeakerSegment                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Exécuter: pytest test_u01.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# EXPRESSION SCHEMA — Bible Anatomique
# =============================================================================

class TestExpressionSchema:
    """Tests de la Bible Anatomique (7 Piliers)."""

    def test_import(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        assert schema is not None

    def test_15_expressions_present(self):
        from expression_schema import VALID_EXPRESSIONS
        assert len(VALID_EXPRESSIONS) >= 15

    def test_9_eye_states_present(self):
        from expression_schema import VALID_EYE_STATES
        assert len(VALID_EYE_STATES) >= 9

    def test_8_mouth_states_present(self):
        from expression_schema import VALID_MOUTH_STATES
        assert len(VALID_MOUTH_STATES) >= 8

    def test_fuse_expression_joy(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        result = schema.fuse_expression("joy", "narrowed", "smiling", 0.8)
        assert isinstance(result, dict)
        assert len(result) > 0
        # Les valeurs doivent être dans [0, 1]
        for v in result.values():
            assert 0.0 <= v <= 1.0, f"Valeur hors range: {v}"

    def test_fuse_expression_neutral_returns_zeros_or_low(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        result = schema.fuse_expression("neutral", "focused_forward", "neutral", 0.5)
        assert isinstance(result, dict)
        # Neutral doit avoir peu de shape keys actives
        active = {k: v for k, v in result.items() if v > 0.3}
        assert len(active) <= 5, f"Trop de keys actives pour neutral: {active}"

    def test_validate_valid_request(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        ok, errs = schema.validate_expression_request("joy", "narrowed", "smiling", 0.7)
        assert ok, f"Validation échouée: {errs}"

    def test_validate_intensity_too_high(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        ok, errs = schema.validate_expression_request("joy", "narrowed", "smiling", 1.5)
        assert not ok, "Intensity > 1.0 doit échouer"

    def test_conflict_detection(self):
        """Brique 2: matrice des conflits."""
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        # joy + sadness sont des oppositions : doit passer par neutral
        needs_trans = schema.requires_neutral_transition("joy", "sadness")
        assert needs_trans, "joy→sadness doit nécessiter une transition neutre"

    def test_no_conflict_same_expression(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        needs_trans = schema.requires_neutral_transition("joy", "joy")
        assert not needs_trans

    def test_micro_expression_presets(self):
        from expression_schema import ExpressionSchema
        schema = ExpressionSchema()
        presets = schema.get_micro_expression_presets()
        assert isinstance(presets, dict)
        assert len(presets) > 0
        for name, preset in presets.items():
            assert "target_keys" in preset
            assert "amplitude" in preset
            assert "frequency_hz" in preset

    def test_range_clamp_jaw(self):
        """Pilier 4: jaw max 0.8 pour Roblox."""
        from expression_schema import ExpressionSchema, ARKIT_52_BLENDSHAPES
        schema = ExpressionSchema()
        result = schema.fuse_expression("excited", "wide_open", "wide_open", 1.0)
        if "jawOpen" in result:
            assert result["jawOpen"] <= 0.85, f"jawOpen trop élevé: {result['jawOpen']}"


# =============================================================================
# FACIAL EXTRACTOR — EmotionalIntentTranslator
# =============================================================================

SAMPLE_FACIAL_DATA = {
    "sequence_id": "TEST_01",
    "facial_animation": [
        {
            "time_start": 0.0, "time_end": 2.0,
            "expression": "neutral", "eyes": "focused_forward",
            "mouth": "neutral", "intensity": 0.5,
            "apex_time": 1.0, "low_visibility": False,
        },
        {
            "time_start": 2.0, "time_end": 4.5,
            "expression": "joy", "eyes": "narrowed",
            "mouth": "smiling", "intensity": 0.9,
            "apex_time": 3.2, "low_visibility": False,
        },
        {
            "time_start": 4.5, "time_end": 7.0,
            "expression": "sadness", "eyes": "looking_down",
            "mouth": "frowning", "intensity": 0.6,
            "apex_time": 5.8, "low_visibility": False,
        },
    ],
}


class TestEmotionalIntentTranslator:

    def test_import(self):
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        assert t is not None

    def test_generate_blender_data_structure(self):
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(SAMPLE_FACIAL_DATA, fps=30)
        assert "fps" in result
        assert "segments" in result
        assert "micro_expressions" in result
        assert result["fps"] == 30

    def test_segments_count_with_transition(self):
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(SAMPLE_FACIAL_DATA, fps=30)
        # joy→sadness nécessite une transition neutre → N+1 segments minimum
        assert len(result["segments"]) >= len(SAMPLE_FACIAL_DATA["facial_animation"])

    def test_segment_frame_range(self):
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(SAMPLE_FACIAL_DATA, fps=30)
        for seg in result["segments"]:
            assert seg["frame_start"] <= seg["frame_apex"], \
                f"frame_apex avant frame_start: {seg}"
            assert seg["frame_apex"] <= seg["frame_end"], \
                f"frame_apex après frame_end: {seg}"

    def test_values_in_range(self):
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(SAMPLE_FACIAL_DATA, fps=30)
        for seg in result["segments"]:
            for k, v in seg["values"].items():
                assert 0.0 <= v <= 1.0, f"Valeur hors [0,1] pour {k}: {v}"

    def test_low_visibility_forces_neutral(self):
        from facial_extractor import EmotionalIntentTranslator
        data = {
            "facial_animation": [{
                "time_start": 0.0, "time_end": 2.0,
                "expression": "joy", "eyes": "narrowed",
                "mouth": "smiling", "intensity": 0.9,
                "apex_time": 1.0, "low_visibility": True,
            }]
        }
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(data, fps=30)
        # low_visibility → expression forcée à neutral → peu de shape keys actives
        assert len(result["segments"]) >= 1
        seg = result["segments"][0]
        active = {k: v for k, v in seg["values"].items() if v > 0.5}
        assert len(active) <= 5, f"Trop de keys actives pour low_visibility: {active}"

    def test_legacy_segments_format(self):
        """Format legacy 'segments' → auto-conversion vers 'facial_animation'."""
        from facial_extractor import EmotionalIntentTranslator
        legacy_data = {
            "segments": SAMPLE_FACIAL_DATA["facial_animation"]
        }
        t = EmotionalIntentTranslator()
        # Ne doit pas lever d'exception
        result = t.generate_blender_data(legacy_data, fps=30)
        assert len(result["segments"]) >= 1


# =============================================================================
# SMOOTHING ENGINE
# =============================================================================

class TestSmoothing:

    def test_import(self):
        pytest.importorskip("numpy", reason="numpy requis")
        from smoothing import savgol_smooth, adaptive_smooth
        assert savgol_smooth is not None

    def test_savgol_basic(self):
        pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        import numpy as np
        from smoothing import savgol_smooth
        data = np.array([0.0, 0.1, 0.9, 0.1, 0.0, 0.1, 0.8, 0.1, 0.0])
        result = savgol_smooth(data, window=5, order=2)
        assert result.shape == data.shape
        # Les valeurs restent dans un range raisonnable
        assert result.max() <= 1.1

    def test_savgol_preserves_length(self):
        pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        import numpy as np
        from smoothing import savgol_smooth
        data = np.random.rand(100)
        result = savgol_smooth(data, window=7, order=2)
        assert len(result) == len(data)

    def test_adaptive_smooth_2d(self):
        pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        import numpy as np
        from smoothing import adaptive_smooth
        data = np.random.rand(50, 5)
        result = adaptive_smooth(data, base_window=5)
        assert result.shape == data.shape

    def test_smooth_blendshapes_dict(self):
        pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        from smoothing import smooth_blendshapes
        face_data = {
            "fps": 30,
            "frames": [
                {"frame": i, "blendshapes": {"mouthSmileLeft": float(i % 10) / 10.0}}
                for i in range(30)
            ]
        }
        result = smooth_blendshapes(face_data, window=5, adaptive=True)
        assert len(result["frames"]) == 30
        for frame in result["frames"]:
            assert 0.0 <= frame["blendshapes"]["mouthSmileLeft"] <= 1.0

    def test_short_data_no_crash(self):
        """Moins de frames que la fenêtre → pas d'exception."""
        pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        import numpy as np
        from smoothing import savgol_smooth
        data = np.array([0.5, 0.6])  # < window=5
        result = savgol_smooth(data, window=5, order=2)
        assert len(result) == len(data)


# =============================================================================
# PYANNOTE DIARIZER — Alias + SpeakerSegment
# =============================================================================

class TestPyannoteDiarizer:

    def test_class_rename(self):
        """SENTINEL FIX: PyannoteDiarizer est le nom correct."""
        from pyannote_diarizer import PyannoteDiarizer
        assert PyannoteDiarizer is not None

    def test_backward_compat_alias(self):
        """PyannoteDialrizer (typo) doit encore fonctionner via alias."""
        from pyannote_diarizer import PyannoteDialrizer, PyannoteDiarizer
        assert PyannoteDialrizer is PyannoteDiarizer

    def test_speaker_segment(self):
        from pyannote_diarizer import SpeakerSegment
        seg = SpeakerSegment("SPEAKER_0", 1.5, 4.2)
        assert seg.duration == pytest.approx(2.7, abs=0.01)
        d = seg.to_dict()
        assert d["speaker_id"] == "SPEAKER_0"
        assert d["start"] == 1.5
        assert d["end"] == 4.2

    def test_diarizer_instantiation_no_token(self):
        """Instanciation sans HF token doit réussir (erreur seulement au setup)."""
        from pyannote_diarizer import PyannoteDiarizer
        d = PyannoteDiarizer(hf_token=None, verbose=False)
        assert d is not None

    def test_map_speakers_to_avatars_explicit(self):
        """Mapping explicite depuis production_plan prioritaire sur tri automatique."""
        from pyannote_diarizer import PyannoteDiarizer, SpeakerSegment
        d = PyannoteDiarizer()
        segments = {
            "SPEAKER_0": [SpeakerSegment("SPEAKER_0", 0.0, 5.0)],
            "SPEAKER_1": [SpeakerSegment("SPEAKER_1", 5.0, 8.0)],
        }
        plan = {"speaker_avatar_mapping": {"SPEAKER_0": "avatar-ferrus-0", "SPEAKER_1": "avatar-ferrus-1"}}
        mapping = d.map_speakers_to_avatars(segments, ["avatar-ferrus-0", "avatar-ferrus-1"], plan)
        assert mapping["SPEAKER_0"] == "avatar-ferrus-0"
        assert mapping["SPEAKER_1"] == "avatar-ferrus-1"

    def test_map_speakers_auto_by_duration(self):
        """Sans mapping explicite : speaker avec plus de parole → avatar-ferrus-0."""
        from pyannote_diarizer import PyannoteDiarizer, SpeakerSegment
        d = PyannoteDiarizer()
        segments = {
            "SPEAKER_A": [SpeakerSegment("SPEAKER_A", 0.0, 1.0)],   # 1s
            "SPEAKER_B": [SpeakerSegment("SPEAKER_B", 1.0, 10.0)],  # 9s (dominant)
        }
        mapping = d.map_speakers_to_avatars(segments, ["avatar-ferrus-0", "avatar-ferrus-1"], {})
        assert mapping["SPEAKER_B"] == "avatar-ferrus-0"
        assert mapping["SPEAKER_A"] == "avatar-ferrus-1"


# =============================================================================
# INTEGRATION TESTS — Pipeline bout-en-bout (sans GPU)
# =============================================================================

class TestPipelineIntegration:

    def test_facial_pipeline_no_gpu(self, tmp_path):
        """Pipeline complet expression_schema → facial_extractor → JSON output."""
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(SAMPLE_FACIAL_DATA, fps=24)

        # Écrire en JSON et relire
        out = tmp_path / "blender_data.json"
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        assert out.exists()

        with open(out) as f:
            loaded = json.load(f)
        assert loaded["fps"] == 24
        assert len(loaded["segments"]) > 0

    def test_all_52_arkit_keys_valid(self):
        """Tous les shape keys produits sont dans la liste ARKit officielle."""
        from expression_schema import ARKIT_52_BLENDSHAPES
        from facial_extractor import EmotionalIntentTranslator
        t = EmotionalIntentTranslator()
        result = t.generate_blender_data(SAMPLE_FACIAL_DATA, fps=30)
        valid_keys = set(ARKIT_52_BLENDSHAPES)
        for seg in result["segments"]:
            for k in seg["values"].keys():
                assert k in valid_keys, f"Shape key invalide: {k}"


# =============================================================================
# VOX REPORT
# =============================================================================

if __name__ == "__main__":
    import subprocess
    ret = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        cwd=str(Path(__file__).parent),
    )
    sys.exit(ret.returncode)
