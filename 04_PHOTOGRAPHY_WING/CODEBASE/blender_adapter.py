"""
VOID-FLUSH — Blender Adapter (U04 bridge)
Source : ADEPTUS_EXODUS/magos_physic/VOID-FLUSH/blender_adapter.py

Usage dans U04 :
  from blender_adapter import flush_before_render, flush_after_render
  flush_before_render(fregate_id="U04")
"""

import importlib.util
from pathlib import Path

_adapter_path = (
    Path(__file__).resolve().parents[3]
    / "ADEPTUS_EXODUS" / "magos_physic" / "VOID-FLUSH" / "blender_adapter.py"
)

_spec = importlib.util.spec_from_file_location("_void_flush_adapter", _adapter_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

flush_before_render = _mod.flush_before_render
flush_after_render = _mod.flush_after_render

__all__ = ["flush_before_render", "flush_after_render"]
