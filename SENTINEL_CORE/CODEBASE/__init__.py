"""
SENTINEL_CORE — Systeme Immunitaire EXODUS V2
Phase D7 — B2 + B6 + B8 operationnels

Usage Colab :
    import sys
    sys.path.insert(0, "/content/drive/MyDrive/EXODUS_V2/SENTINEL_CORE/CODEBASE")
    from sentinel_core import Sentinel
"""
from .sentinel_core import Sentinel
from .brique2_state import StateSignature
from .brique6_ledger import Ledger
from .brique8_mirror import Mirror

__version__ = "1.0.0"
__all__ = ["Sentinel", "StateSignature", "Ledger", "Mirror"]
