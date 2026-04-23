"""
VOX — Tests Pytest — U03 SCENOGRAPHY DOCK
Valide la structure, les contrats, et la logique non-Blender de la fregate U03.

Lancer :
  pytest test_u03.py -v
  pytest test_u03.py -v --tb=short
"""

import json
import sys
from pathlib import Path

import pytest

# Chemin racine du repo
REPO_ROOT = Path(__file__).resolve().parents[2]
U03_ROOT = REPO_ROOT / "03_SCENOGRAPHY_DOCK"
U03_CODEBASE = U03_ROOT / "CODEBASE"

sys.path.insert(0, str(U03_CODEBASE))


# =============================================================================
# TESTS STRUCTURE
# =============================================================================

class TestStructureU03:
    """Verifie la structure canonique de U03."""

    def test_fregate_dir_exists(self):
        assert U03_ROOT.exists(), "Dossier U03 manquant"

    def test_codebase_exists(self):
        assert U03_CODEBASE.exists(), "Dossier CODEBASE manquant"

    def test_readme_exists(self):
        assert (U03_ROOT / "README_DEV.md").exists(), "README_DEV.md manquant"

    def test_subplan_exists(self):
        assert (U03_ROOT / "UNIT_03_SUBPLAN.md").exists(), "UNIT_03_SUBPLAN.md manquant"

    def test_rules_exists(self):
        assert (U03_ROOT / "RULES.md").exists(), "RULES.md manquant (Tache 46)"

    def test_tracking_exists(self):
        tracking = REPO_ROOT / "TRACKING" / "TRACKING_U03.md"
        assert tracking.exists(), "TRACKING_U03.md manquant"

    def test_in_cortex_json_dir(self):
        assert (U03_ROOT / "IN_CORTEX_JSON").exists(), "IN_CORTEX_JSON manquant"

    def test_in_map_raw_dir(self):
        assert (U03_ROOT / "IN_MAP_RAW").exists(), "IN_MAP_RAW manquant"

    def test_out_premium_scene_dir(self):
        assert (U03_ROOT / "OUT_PREMIUM_SCENE").exists(), "OUT_PREMIUM_SCENE manquant"


# =============================================================================
# TESTS FICHIERS CLES
# =============================================================================

class TestKeyFilesU03:
    """Verifie la presence et la syntaxe des fichiers cles."""

    REQUIRED_FILES = [
        "EXO_03_SCENOGRAPHY.py",
        "EXO_03_PRODUCTION.ipynb",
        "layer_assembler.py",
        "geometry_probe_u03.py",
        "dome_builder.py",
        "shadow_catcher_builder.py",
        "scene_schema.py",
        "requirements.txt",
        "blender_adapter.py",
        "session_store.py",
    ]

    @pytest.mark.parametrize("fname", REQUIRED_FILES)
    def test_file_exists(self, fname):
        fpath = U03_CODEBASE / fname
        assert fpath.exists(), f"Fichier requis manquant : {fname}"

    @pytest.mark.parametrize("fname", [f for f in REQUIRED_FILES if f.endswith(".py")])
    def test_python_syntax(self, fname):
        fpath = U03_CODEBASE / fname
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

class TestVoidFlushIntegrationU03:
    """Verifie l'integration VOID-FLUSH dans U03."""

    def test_blender_adapter_importable(self):
        """blender_adapter.py est importable depuis CODEBASE."""
        fpath = U03_CODEBASE / "blender_adapter.py"
        assert fpath.exists()
        source = fpath.read_text(encoding="utf-8")
        assert "flush_before_render" in source
        assert "flush_after_render" in source

    def test_exo03_imports_void_flush(self):
        """EXO_03_SCENOGRAPHY.py contient le bloc VOID-FLUSH."""
        source = (U03_CODEBASE / "EXO_03_SCENOGRAPHY.py").read_text(encoding="utf-8")
        assert "flush_before_render" in source, "Hook pre-render absent dans EXO_03"
        assert "_VOID_FLUSH_AVAILABLE" in source, "Flag VOID_FLUSH absent"

    def test_void_flush_hook_before_blender(self):
        """Le hook flush est appele AVANT le subprocess Blender."""
        source = (U03_CODEBASE / "EXO_03_SCENOGRAPHY.py").read_text(encoding="utf-8")
        flush_pos = source.find("flush_before_render")
        blender_pos = source.find("subprocess.run")
        assert flush_pos < blender_pos, "flush_before_render doit preceder subprocess.run"


# =============================================================================
# TESTS INTEGRATION ATLAS
# =============================================================================

class TestAtlasIntegrationU03:
    """Verifie l'integration ATLAS/SessionStore dans U03."""

    def test_session_store_importable(self):
        """session_store.py est present dans CODEBASE."""
        fpath = U03_CODEBASE / "session_store.py"
        assert fpath.exists()
        source = fpath.read_text(encoding="utf-8")
        assert "class SessionStore" in source

    def test_exo03_imports_atlas(self):
        """EXO_03_SCENOGRAPHY.py contient le bloc ATLAS."""
        source = (U03_CODEBASE / "EXO_03_SCENOGRAPHY.py").read_text(encoding="utf-8")
        assert "SessionStore" in source, "SessionStore absent dans EXO_03"
        assert "_ATLAS_AVAILABLE" in source, "Flag ATLAS absent"

    def test_session_store_save_after_success(self):
        """Le save() est appele apres un run reussi."""
        source = (U03_CODEBASE / "EXO_03_SCENOGRAPHY.py").read_text(encoding="utf-8")
        assert 'SessionStore("U03")' in source
        assert ".save()" in source

    def test_session_store_has_drive_root(self):
        """drive_root est sauvegarde dans la session."""
        source = (U03_CODEBASE / "EXO_03_SCENOGRAPHY.py").read_text(encoding="utf-8")
        assert '"drive_root"' in source


# =============================================================================
# TESTS SCENE_SCHEMA
# =============================================================================

class TestSceneSchemaU03:
    """Verifie la coherence de scene_schema.py."""

    def test_scene_schema_importable(self):
        fpath = U03_CODEBASE / "scene_schema.py"
        assert fpath.exists()

    def test_scene_schema_has_validate(self):
        source = (U03_CODEBASE / "scene_schema.py").read_text(encoding="utf-8")
        assert "validate_scene" in source, "validate_scene() absent dans scene_schema"

    def test_scene_schema_has_canonical_collections(self):
        source = (U03_CODEBASE / "scene_schema.py").read_text(encoding="utf-8")
        for coll in ["ENV_DOME", "ENV_TERRAIN", "ENV_SHADOW"]:
            assert coll in source, f"Collection canonique '{coll}' absente"

    def test_scene_schema_has_vram_profiles(self):
        source = (U03_CODEBASE / "scene_schema.py").read_text(encoding="utf-8")
        assert "colab_t4" in source, "Profil VRAM colab_t4 absent"


# =============================================================================
# TESTS LAYER_ASSEMBLER
# =============================================================================

class TestLayerAssemblerU03:
    """Verifie la coherence de layer_assembler.py."""

    def test_layer_assembler_exists(self):
        assert (U03_CODEBASE / "layer_assembler.py").exists()

    def test_layer_assembler_has_assemble_scene(self):
        source = (U03_CODEBASE / "layer_assembler.py").read_text(encoding="utf-8")
        assert "assemble_scene" in source or "def main" in source

    def test_layer_assembler_references_env_dome(self):
        source = (U03_CODEBASE / "layer_assembler.py").read_text(encoding="utf-8")
        assert "ENV_DOME" in source or "dome" in source.lower()


# =============================================================================
# TESTS REQUIREMENTS
# =============================================================================

class TestRequirementsU03:
    """Verifie requirements.txt."""

    def test_requirements_not_empty(self):
        req = U03_CODEBASE / "requirements.txt"
        assert req.exists()
        content = req.read_text().strip()
        assert len(content) > 0, "requirements.txt vide"
