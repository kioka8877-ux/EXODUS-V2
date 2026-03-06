#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 05_ALCHEMIST — BLOOM ENGINE                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Moteur de bloom OpenCV pur (CPU). Extrait les zones lumineuses d'une      ║
║  frame, applique un flou gaussien massif, puis blend additivement pour     ║
║  créer un halo lumineux cinématique.                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from alchemist_schema import (
    BLOOM_DEFAULTS,
    BLOOM_RANGES,
    AlchemistSchema,
)

BLOOM_ENGINE_VERSION = "2.0.0"

_schema = AlchemistSchema()


class BloomEngine:
    """Moteur de bloom additif basé sur l'isolation des hautes lumières."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.defaults = dict(BLOOM_DEFAULTS)
        self.ranges = dict(BLOOM_RANGES)

    def _log(self, msg: str):
        if self.verbose:
            print(f"[BLOOM] {msg}")

    def apply_bloom(
        self,
        frame: np.ndarray,
        threshold: float = None,
        intensity: float = None,
        radius: int = None,
    ) -> np.ndarray:
        """Applique un bloom additif à une frame BGR.

        1. Convertir en float32 [0.0, 1.0]
        2. Extraire la luminance (Rec.709)
        3. Masque des hautes lumières au-dessus du seuil
        4. Isoler les pixels brillants
        5. Gros flou gaussien → glow
        6. Blend additif avec intensité
        7. Clip et reconvertir au format d'entrée
        """
        if threshold is None:
            threshold = self.defaults["threshold"]
        if intensity is None:
            intensity = self.defaults["intensity"]
        if radius is None:
            radius = self.defaults["radius"]

        threshold = float(np.clip(threshold, *self.ranges["threshold"]))
        intensity = float(np.clip(intensity, *self.ranges["intensity"]))
        radius = _schema.validate_radius(int(radius))

        self._log(f"threshold={threshold:.2f} intensity={intensity:.2f} radius={radius}")

        if intensity <= 0.0:
            return frame.copy()

        src_dtype = frame.dtype
        if src_dtype == np.uint8:
            frame_f = frame.astype(np.float32) / 255.0
        elif src_dtype == np.uint16:
            frame_f = frame.astype(np.float32) / 65535.0
        else:
            frame_f = frame.astype(np.float32)

        r = frame_f[:, :, 2]
        g = frame_f[:, :, 1]
        b = frame_f[:, :, 0]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        bright_mask = np.maximum(0.0, luminance - threshold)

        bright_areas = frame_f * bright_mask[:, :, np.newaxis]

        glow = cv2.GaussianBlur(bright_areas, (radius, radius), 0)

        output = frame_f + glow * intensity

        output = np.clip(output, 0.0, 1.0)

        if src_dtype == np.uint8:
            return (output * 255.0).astype(np.uint8)
        elif src_dtype == np.uint16:
            return (output * 65535.0).astype(np.uint16)
        return output


def _standalone_test():
    """Test autonome : carré blanc sur fond noir → le glow doit baver."""
    print()
    print("═══════════════════════════════════════════════════")
    print("   BLOOM ENGINE — TEST STANDALONE v" + BLOOM_ENGINE_VERSION)
    print("═══════════════════════════════════════════════════")
    print()

    total = 0
    passed = 0

    engine = BloomEngine(verbose=True)

    # --- TEST 1 : glow bave autour du carré blanc ---
    total += 1
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[80:120, 80:120] = 255

    result = engine.apply_bloom(img, threshold=0.5, intensity=0.6, radius=51)

    glow_zone = result[60:80, 60:80]
    max_outside = glow_zone.max()
    t1_ok = max_outside > 0
    if t1_ok:
        passed += 1
        print(f"[TEST 1] Glow diffusion .................. ✓ (max pixel autour={max_outside})")
    else:
        print(f"[TEST 1] Glow diffusion .................. ✗ (max pixel autour={max_outside}, attendu >0)")

    # --- TEST 2 : intensity=0 → pas de changement ---
    total += 1
    img2 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2[40:60, 40:60] = 200
    result2 = engine.apply_bloom(img2, intensity=0.0)
    t2_ok = np.array_equal(img2, result2)
    if t2_ok:
        passed += 1
        print("[TEST 2] Intensité zéro = no-op .......... ✓")
    else:
        print("[TEST 2] Intensité zéro = no-op .......... ✗")

    # --- TEST 3 : uint16 support ---
    total += 1
    img16 = np.zeros((100, 100, 3), dtype=np.uint16)
    img16[40:60, 40:60] = 65535
    result16 = engine.apply_bloom(img16, threshold=0.5, intensity=0.5, radius=31)
    t3_ok = result16.dtype == np.uint16 and result16[30, 30].max() > 0
    if t3_ok:
        passed += 1
        print(f"[TEST 3] uint16 round-trip ............... ✓ (dtype={result16.dtype})")
    else:
        print(f"[TEST 3] uint16 round-trip ............... ✗ (dtype={result16.dtype})")

    # --- TEST 4 : radius pair → forcé impair ---
    total += 1
    validated = _schema.validate_radius(50)
    t4_ok = validated % 2 == 1
    if t4_ok:
        passed += 1
        print(f"[TEST 4] Radius pair → impair ............ ✓ (50 → {validated})")
    else:
        print(f"[TEST 4] Radius pair → impair ............ ✗ ({validated})")

    # --- TEST 5 : float32 passthrough ---
    total += 1
    img_f = np.zeros((100, 100, 3), dtype=np.float32)
    img_f[40:60, 40:60] = 1.0
    result_f = engine.apply_bloom(img_f, threshold=0.5, intensity=0.5, radius=31)
    t5_ok = result_f.dtype == np.float32 and result_f[30, 30].max() > 0.0
    if t5_ok:
        passed += 1
        print(f"[TEST 5] float32 passthrough ............. ✓")
    else:
        print(f"[TEST 5] float32 passthrough ............. ✗")

    print()
    print("═══════════════════════════════════════════════════")
    print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
    print("═══════════════════════════════════════════════════")

    return passed == total


if __name__ == "__main__":
    success = _standalone_test()
    sys.exit(0 if success else 1)
