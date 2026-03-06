#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 05_ALCHEMIST — SHARPNESS TRANSFER                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Transfère le niveau de netteté de la vidéo source vers le rendu.          ║
║  Mesure la variance du Laplacien (netteté) des deux images, puis           ║
║  applique un flou ou un unsharp-mask pour aligner le rendu sur la source.  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from alchemist_schema import (
    SHARPNESS_DEFAULTS,
    SHARPNESS_RANGES,
)

SHARPNESS_TRANSFER_VERSION = "2.0.0"


class SharpnessTransfer:
    """Aligne la netteté du rendu sur celle de la source vidéo."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.defaults = dict(SHARPNESS_DEFAULTS)
        self.ranges = dict(SHARPNESS_RANGES)

    def _log(self, msg: str):
        if self.verbose:
            print(f"[SHARPNESS] {msg}")

    def measure_sharpness(self, frame: np.ndarray) -> float:
        """Variance du Laplacien — mesure de netteté.

        Valeur élevée = image nette. Valeur basse = image floue.
        """
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        if gray.dtype != np.uint8:
            if gray.dtype == np.uint16:
                gray = (gray / 256).astype(np.uint8)
            elif gray.dtype == np.float32 or gray.dtype == np.float64:
                gray = (np.clip(gray, 0.0, 1.0) * 255).astype(np.uint8)

        lap = cv2.Laplacian(gray, cv2.CV_64F)
        return float(lap.var())

    def transfer(
        self,
        render_frame: np.ndarray,
        source_frame: np.ndarray,
        intensity: float = None,
    ) -> np.ndarray:
        """Transfère la netteté de la source vers le rendu.

        - ratio < 1 : rendu trop net → flou gaussien pondéré
        - ratio > 1 : rendu trop mou → unsharp mask
        - ratio ≈ 1 : pas de changement
        """
        if intensity is None:
            intensity = self.defaults["intensity"]

        lo, hi = self.ranges["intensity"]
        intensity = float(np.clip(intensity, lo, hi))

        max_blur_sigma = self.defaults["max_blur_sigma"]
        unsharp_amount = self.defaults["unsharp_amount"]
        unsharp_radius = self.defaults["unsharp_radius"]

        if intensity <= 0.0:
            return render_frame.copy()

        sharpness_render = self.measure_sharpness(render_frame)
        sharpness_source = self.measure_sharpness(source_frame)

        self._log(
            f"sharpness render={sharpness_render:.1f} source={sharpness_source:.1f}"
        )

        if sharpness_render < 1e-6:
            self._log("render sharpness ≈ 0, skip transfer")
            return render_frame.copy()

        ratio = sharpness_source / sharpness_render
        self._log(f"ratio={ratio:.4f}")

        tolerance = 0.05
        if abs(ratio - 1.0) < tolerance:
            self._log("ratio ≈ 1, no adjustment needed")
            return render_frame.copy()

        src_dtype = render_frame.dtype
        if src_dtype == np.uint8:
            work = render_frame.astype(np.float32) / 255.0
        elif src_dtype == np.uint16:
            work = render_frame.astype(np.float32) / 65535.0
        else:
            work = render_frame.astype(np.float32)

        if ratio < 1.0:
            raw_sigma = math.sqrt(1.0 / ratio - 1.0)
            sigma = min(raw_sigma, max_blur_sigma)
            self._log(f"render trop net → blur sigma={sigma:.3f}")
            blurred = cv2.GaussianBlur(work, (0, 0), sigma)
            output = work * (1.0 - intensity) + blurred * intensity
        else:
            self._log(f"render trop mou → unsharp amount={unsharp_amount} radius={unsharp_radius}")
            blurred = cv2.GaussianBlur(work, (0, 0), float(unsharp_radius))
            output = cv2.addWeighted(
                work,
                1.0 + unsharp_amount * intensity,
                blurred,
                -unsharp_amount * intensity,
                0,
            )

        output = np.clip(output, 0.0, 1.0)

        if src_dtype == np.uint8:
            return (output * 255.0).astype(np.uint8)
        elif src_dtype == np.uint16:
            return (output * 65535.0).astype(np.uint16)
        return output


def _standalone_test():
    """Test autonome : image nette vs floue → transfer réduit la netteté."""
    print()
    print("═══════════════════════════════════════════════════")
    print("   SHARPNESS TRANSFER — TEST STANDALONE v" + SHARPNESS_TRANSFER_VERSION)
    print("═══════════════════════════════════════════════════")
    print()

    total = 0
    passed = 0

    st = SharpnessTransfer(verbose=True)

    # --- TEST 1 : mesure de netteté ---
    total += 1
    sharp_img = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(0, 200, 4):
        sharp_img[i : i + 2, :] = 255

    blurry_img = cv2.GaussianBlur(sharp_img, (0, 0), 5.0)

    s_sharp = st.measure_sharpness(sharp_img)
    s_blurry = st.measure_sharpness(blurry_img)
    t1_ok = s_sharp > s_blurry and s_blurry > 0
    if t1_ok:
        passed += 1
        print(f"[TEST 1] Mesure sharpness ................ ✓ (nette={s_sharp:.1f} > floue={s_blurry:.1f})")
    else:
        print(f"[TEST 1] Mesure sharpness ................ ✗ (nette={s_sharp:.1f}, floue={s_blurry:.1f})")

    # --- TEST 2 : transfer réduit la netteté quand source est floue ---
    total += 1
    result = st.transfer(sharp_img, blurry_img, intensity=0.8)
    s_result = st.measure_sharpness(result)
    t2_ok = s_result < s_sharp
    if t2_ok:
        passed += 1
        print(f"[TEST 2] Transfer blur ................... ✓ (avant={s_sharp:.1f} → après={s_result:.1f})")
    else:
        print(f"[TEST 2] Transfer blur ................... ✗ (avant={s_sharp:.1f}, après={s_result:.1f})")

    # --- TEST 3 : transfer augmente la netteté quand source est plus nette ---
    total += 1
    result_sharp = st.transfer(blurry_img, sharp_img, intensity=0.8)
    s_result_sharp = st.measure_sharpness(result_sharp)
    t3_ok = s_result_sharp > s_blurry
    if t3_ok:
        passed += 1
        print(f"[TEST 3] Transfer sharpen ................ ✓ (avant={s_blurry:.1f} → après={s_result_sharp:.1f})")
    else:
        print(f"[TEST 3] Transfer sharpen ................ ✗ (avant={s_blurry:.1f}, après={s_result_sharp:.1f})")

    # --- TEST 4 : intensity=0 → pas de changement ---
    total += 1
    result_zero = st.transfer(sharp_img, blurry_img, intensity=0.0)
    t4_ok = np.array_equal(sharp_img, result_zero)
    if t4_ok:
        passed += 1
        print("[TEST 4] Intensité zéro = no-op .......... ✓")
    else:
        print("[TEST 4] Intensité zéro = no-op .......... ✗")

    # --- TEST 5 : uint16 round-trip ---
    total += 1
    sharp16 = np.zeros((200, 200, 3), dtype=np.uint16)
    for i in range(0, 200, 4):
        sharp16[i : i + 2, :] = 65535
    blurry16 = cv2.GaussianBlur(sharp16, (11, 11), 5.0)
    result16 = st.transfer(sharp16, blurry16, intensity=0.7)
    t5_ok = result16.dtype == np.uint16
    if t5_ok:
        passed += 1
        print(f"[TEST 5] uint16 round-trip ............... ✓ (dtype={result16.dtype})")
    else:
        print(f"[TEST 5] uint16 round-trip ............... ✗ (dtype={result16.dtype})")

    # --- TEST 6 : images identiques → pas de changement ---
    total += 1
    same = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    result_same = st.transfer(same, same.copy(), intensity=0.7)
    s_before = st.measure_sharpness(same)
    s_after = st.measure_sharpness(result_same)
    diff = abs(s_before - s_after) / max(s_before, 1.0)
    t6_ok = diff < 0.1
    if t6_ok:
        passed += 1
        print(f"[TEST 6] Identiques → stable ............. ✓ (delta={diff:.4f})")
    else:
        print(f"[TEST 6] Identiques → stable ............. ✗ (delta={diff:.4f})")

    print()
    print("═══════════════════════════════════════════════════")
    print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
    print("═══════════════════════════════════════════════════")

    return passed == total


if __name__ == "__main__":
    success = _standalone_test()
    sys.exit(0 if success else 1)
