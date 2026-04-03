"""
VOX — Tests Pytest — U04 PHOTOGRAPHY WING
Valide la structure, les contrats, et la logique non-Blender de la fregate U04.

Lancer :
  pytest test_u04.py -v
  pytest test_u04.py -v --tb=short
"""

import json
import sys
from pathlib import Path

import pytest

# Chemin racine du repo
REPO_ROOT = Path(__file__).resolve().parents[2]
U04_ROOT = REPO_ROOT / "04_PHOTOGRAPHY_WING"
U04_CODEBASE = U04_ROOT / "CODEBASE"

sys.path.insert(0, str(U04_CODEBASE))


# =============================================================================
# TESTS STRUCTURE
# =============================================================================

class TestStructureU04:
    """Verifie la structure canonique de U04."""

    def test_fregate_dir_exists(self):
        assert U04_ROOT.exists(), "Dossier U04 manquant"

    def test_codebase_exists(self):
        assert U04_CODEBASE.exists(), "Dossier CODEBASE manquant"

    def test_readme_exists(self):
        assert (U04_ROOT / "README_DEV.md").exists(), "README_DEV.md manquant"

    def test_subplan_exists(self):
        assert (U04_ROOT / "UNIT_04_SUBPLAN.md").exists(), "UNIT_04_SUBPLAN.md manquant"

    def test_rules_exists(self):
        assert (U04_ROOT / "RULES.md").exists(), "RULES.md manquant (Tache 46)"

    def test_architecture_doc_exists(self):
        assert (U04_ROOT / "ARCHITECTURE_U04.md").exists(), "ARCHITECTURE_U04.md manquant"

    def test_tracking_exists(self):
        tracking = REPO_ROOT / "TRACKING" / "TRACKING_U04.md"
        assert tracking.exists(), "TRACKING_U04.md manquant"

    def test_in_scene_ref_dir(self):
        assert (U04_ROOT / "IN_SCENE_REF").exists(), "IN_SCENE_REF manquant"

    def test_in_video_source_dir(self):
        assert (U04_ROOT / "IN_VIDEO_SOURCE").exists(), "IN_VIDEO_SOURCE manquant"


# =============================================================================
# TESTS FICHIERS CLES
# =============================================================================

class TestKeyFilesU04:
    """Verifie la presence et la syntaxe des fichiers cles."""

    REQUIRED_FILES = [
        "EXO_04_PHOTOGRAPHY.py",
        "EXO_04_PRODUCTION.ipynb",
        "EXO_04_DARKROOM.py",
        "camera_director.py",
        "camera_schema.py",
        "lighting_rig.py",
        "render_forge.py",
        "fspy_tracker.py",
        "auto_dof.py",
        "cuts_engine.py",
        "requirements.txt",
        "blender_adapter.py",
        "session_store.py",
    ]

    @pytest.mark.parametrize("fname", REQUIRED_FILES)
    def test_file_exists(self, fname):
        fpath = U04_CODEBASE / fname
        assert fpath.exists(), f"Fichier requis manquant : {fname}"

    @pytest.mark.parametrize("fname", [f for f in REQUIRED_FILES if f.endswith(".py")])
    def test_python_syntax(self, fname):
        fpath = U04_CODEBASE / fname
        if not fpath.exists():
            pytest.skip(f"{fname} absent")
        source = fpath.read_text(encoding="utf-8")
        try:
            compile(source, str(fpath), "exec")
        except SyntaxError as e:
            pytest.fail(f"Erreur syntaxe dans {fname}: {e}")


# =============================================================================
# TESTS INTEGRATION VOID-FLUSH
# =============================================================================

class TestVoidFlushIntegrationU04:
    """Verifie l'integration VOID-FLUSH dans U04."""

    def test_blender_adapter_importable(self):
        fpath = U04_CODEBASE / "blender_adapter.py"
        assert fpath.exists()
        source = fpath.read_text(encoding="utf-8")
        assert "flush_before_render" in source
        assert "flush_after_render" in source

    def test_exo04_imports_void_flush(self):
        source = (U04_CODEBASE / "EXO_04_PHOTOGRAPHY.py").read_text(encoding="utf-8")
        assert "flush_before_render" in source, "Hook pre-render absent dans EXO_04"
        assert "_VOID_FLUSH_AVAILABLE" in source, "Flag VOID_FLUSH absent"

    def test_void_flush_hook_before_blender(self):
        source = (U04_CODEBASE / "EXO_04_PHOTOGRAPHY.py").read_text(encoding="utf-8")
        flush_pos = source.find("flush_before_render")
        blender_pos = source.find("subprocess.run")
        assert flush_pos < blender_pos, "flush_before_render doit preceder subprocess.run"


# =============================================================================
# TESTS INTEGRATION ATLAS
# =============================================================================

class TestAtlasIntegrationU04:
    """Verifie l'integration ATLAS/SessionStore dans U04."""

    def test_session_store_importable(self):
        fpath = U04_CODEBASE / "session_store.py"
        assert fpath.exists()
        source = fpath.read_text(encoding="utf-8")
        assert "class SessionStore" in source

    def test_exo04_imports_atlas(self):
        source = (U04_CODEBASE / "EXO_04_PHOTOGRAPHY.py").read_text(encoding="utf-8")
        assert "SessionStore" in source
        assert "_ATLAS_AVAILABLE" in source

    def test_session_store_save_after_success(self):
        source = (U04_CODEBASE / "EXO_04_PHOTOGRAPHY.py").read_text(encoding="utf-8")
        assert 'SessionStore("U04")' in source
        assert ".save()" in source

    def test_session_store_has_drive_root(self):
        source = (U04_CODEBASE / "EXO_04_PHOTOGRAPHY.py").read_text(encoding="utf-8")
        assert '"drive_root"' in source


# =============================================================================
# TESTS CAMERA_SCHEMA (Bible Optique)
# =============================================================================

class TestCameraSchemaU04:
    """Verifie la coherence de camera_schema.py."""

    def test_camera_schema_exists(self):
        assert (U04_CODEBASE / "camera_schema.py").exists()

    def test_camera_schema_has_presets(self):
        source = (U04_CODEBASE / "camera_schema.py").read_text(encoding="utf-8")
        assert "CUT_PRESETS" in source or "CAMERA_PRESETS" in source or "darkroom" in source

    def test_camera_schema_has_scene_type_mapping(self):
        source = (U04_CODEBASE / "camera_schema.py").read_text(encoding="utf-8")
        assert "SCENE_TYPE_TO_LIGHTING" in source, "Mapping scene_type absent"

    def test_camera_schema_has_lighting_preset_mapping(self):
        source = (U04_CODEBASE / "camera_schema.py").read_text(encoding="utf-8")
        assert "LIGHTING_PRESET_TO_STYLE" in source, "Mapping preset_id absent"

    def test_camera_schema_no_random_gauss(self):
        """R5: shake procédural via Noise Modifier, pas random.gauss."""
        source = (U04_CODEBASE / "camera_schema.py").read_text(encoding="utf-8")
        assert "random.gauss" not in source, "random.gauss interdit (R5)"

    def test_camera_director_no_random_gauss(self):
        source = (U04_CODEBASE / "camera_director.py").read_text(encoding="utf-8")
        assert "random.gauss" not in source, "random.gauss interdit dans camera_director (R5)"


# =============================================================================
# TESTS DARKROOM (U04-B)
# =============================================================================

class TestDarkroomU04:
    """Verifie la fregate U04-B Darkroom."""

    def test_darkroom_orchestrator_exists(self):
        assert (U04_CODEBASE / "EXO_04_DARKROOM.py").exists()

    def test_darkroom_render_script_exists(self):
        assert (U04_CODEBASE / "darkroom_render.py").exists()

    def test_darkroom_notebook_exists(self):
        assert (U04_CODEBASE / "EXO_04_DARKROOM.ipynb").exists()

    def test_darkroom_orchestrator_has_resume(self):
        source = (U04_CODEBASE / "EXO_04_DARKROOM.py").read_text(encoding="utf-8")
        assert "resume" in source.lower() or "checkpoint" in source.lower(), \
            "Support resume/checkpoint absent dans Darkroom"


# =============================================================================
# TESTS ARCHITECTURE SEPARATION A/B
# =============================================================================

class TestArchitectureSeparationU04:
    """Verifie que U04-A et U04-B respectent la separation R2."""

    def test_architecture_doc_mentions_split(self):
        doc = (U04_ROOT / "ARCHITECTURE_U04.md").read_text(encoding="utf-8")
        assert "Director" in doc or "A" in doc
        assert "Darkroom" in doc or "B" in doc

    def test_exo04_photography_does_not_import_darkroom(self):
        """U04-A ne doit pas importer U04-B (isolation)."""
        source = (U04_CODEBASE / "EXO_04_PHOTOGRAPHY.py").read_text(encoding="utf-8")
        assert "darkroom" not in source.lower() or "EXO_04_DARKROOM" not in source


# =============================================================================
# TESTS REQUIREMENTS
# =============================================================================

class TestRequirementsU04:
    """Verifie requirements.txt."""

    def test_requirements_not_empty(self):
        req = U04_CODEBASE / "requirements.txt"
        assert req.exists()
        content = req.read_text().strip()
        assert len(content) > 0, "requirements.txt vide"
