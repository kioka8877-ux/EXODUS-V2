#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                GRAIN MATCHER — EXODUS ALCHEMIST LAB                         ║
║           Extraction Grain Source + Application Procédurale Calibrée        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Extrait la signature du grain (bruit capteur) de la vidéo source
via bilateral filter decomposition, puis génère du grain procédural
calibré sur les statistiques extraites.

Moteur : OpenCV + numpy
"""

import sys
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from alchemist_schema import (
    GRAIN_DEFAULTS,
    GRAIN_RANGES,
    VALID_GRAIN_METHODS,
    DEFAULT_GRAIN_METHOD,
    UINT8_MAX,
    UINT16_MAX,
    PROCESSING_DTYPE,
)


class GrainMatcher:
    """Extraction + synthèse de grain calibré — décompose le bruit capteur
    d'une vidéo source via bilateral filtering puis génère du grain
    procédural aux mêmes caractéristiques statistiques."""

    def __init__(self, verbose: bool = False):
        """Initialise le GrainMatcher.

        Paramètres bilateral et calibration lus depuis GRAIN_DEFAULTS.

        Args:
            verbose: Active les logs de debug.
        """
        self.verbose: bool = verbose
        self.bilateral_d: int = int(GRAIN_DEFAULTS["bilateral_d"])
        self.bilateral_sigma_color: float = float(GRAIN_DEFAULTS["bilateral_sigma_color"])
        self.bilateral_sigma_space: float = float(GRAIN_DEFAULTS["bilateral_sigma_space"])
        self.calibration_samples: int = int(GRAIN_DEFAULTS["calibration_samples"])
        self.method: str = DEFAULT_GRAIN_METHOD
        self.operations: List[dict] = []
        self.log("GrainMatcher initialisé — "
                 f"bilateral(d={self.bilateral_d}, "
                 f"σc={self.bilateral_sigma_color}, "
                 f"σs={self.bilateral_sigma_space})")

    # -----------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------

    def log(self, msg: str) -> None:
        """Log toujours affiché."""
        print(f"[GRAIN_MATCHER] {msg}")
        self.operations.append({"action": "log", "message": msg})

    def debug(self, msg: str) -> None:
        """Log conditionnel (verbose)."""
        if self.verbose:
            print(f"[GRAIN_MATCHER:DEBUG] {msg}")

    # -----------------------------------------------------------------
    # Utilitaires internes
    # -----------------------------------------------------------------

    @staticmethod
    def _to_float32(frame: np.ndarray) -> np.ndarray:
        """Convertit une frame uint8/uint16 en float32 [0.0, 1.0]."""
        if frame.dtype == np.uint8:
            return frame.astype(PROCESSING_DTYPE) / UINT8_MAX
        if frame.dtype == np.uint16:
            return frame.astype(PROCESSING_DTYPE) / UINT16_MAX
        return frame.astype(PROCESSING_DTYPE)

    @staticmethod
    def _from_float32(frame_f: np.ndarray, target_dtype: np.dtype) -> np.ndarray:
        """Reconvertit float32 [0.0, 1.0] vers le dtype cible."""
        clipped = np.clip(frame_f, 0.0, 1.0)
        if target_dtype == np.uint8:
            return (clipped * UINT8_MAX).astype(np.uint8)
        if target_dtype == np.uint16:
            return (clipped * UINT16_MAX).astype(np.uint16)
        return clipped

    def _select_frames(self, source_frames: List[np.ndarray]) -> List[np.ndarray]:
        """Sous-échantillonne les frames pour la calibration."""
        n = len(source_frames)
        count = min(self.calibration_samples, n)
        if count >= n:
            return list(source_frames)
        indices = np.linspace(0, n - 1, count, dtype=int)
        selected = [source_frames[i] for i in indices]
        self.debug(f"Calibration : {count}/{n} frames sélectionnées")
        return selected

    # -----------------------------------------------------------------
    # API publique
    # -----------------------------------------------------------------

    def extract_grain_stats(self, source_frames: List[np.ndarray]) -> Dict:
        """Extrait les statistiques du grain à partir de frames source.

        Algorithme :
        1. Pour chaque frame :
           a. Convertir en float32 [0.0, 1.0].
           b. Bilateral filter sur la version uint8 (OpenCV exige uint8).
           c. grain_residual = frame_float − filtered_float.
           d. Calculer mean / std par canal (B, G, R).
        2. Moyenner les stats sur les frames échantillonnées.

        Args:
            source_frames: Liste de frames BGR (numpy uint8/uint16).

        Returns:
            Dict avec mean_per_channel, std_per_channel, global_std,
            samples_used.
        """
        if not source_frames:
            raise ValueError("source_frames est vide")

        selected = self._select_frames(source_frames)

        all_means: List[np.ndarray] = []
        all_stds: List[np.ndarray] = []

        for frame in selected:
            frame_f = self._to_float32(frame)

            frame_u8 = frame if frame.dtype == np.uint8 else \
                (frame_f * UINT8_MAX).astype(np.uint8)

            smoothed_u8 = cv2.bilateralFilter(
                frame_u8,
                d=self.bilateral_d,
                sigmaColor=self.bilateral_sigma_color,
                sigmaSpace=self.bilateral_sigma_space,
            )
            smoothed_f = smoothed_u8.astype(PROCESSING_DTYPE) / UINT8_MAX

            residual = frame_f - smoothed_f

            ch_means = np.array([residual[:, :, c].mean() for c in range(3)],
                                dtype=PROCESSING_DTYPE)
            ch_stds = np.array([residual[:, :, c].std() for c in range(3)],
                               dtype=PROCESSING_DTYPE)
            all_means.append(ch_means)
            all_stds.append(ch_stds)

        mean_per_channel = np.mean(all_means, axis=0).tolist()
        std_per_channel = np.mean(all_stds, axis=0).tolist()
        global_std = float(np.mean(std_per_channel))

        stats = {
            "mean_per_channel": mean_per_channel,
            "std_per_channel": std_per_channel,
            "global_std": global_std,
            "samples_used": len(selected),
        }

        self.log(f"Grain stats extraites — {len(selected)} frames, "
                 f"global_std={global_std:.6f}")
        for c, name in enumerate(("B", "G", "R")):
            self.debug(f"  {name}: mean={mean_per_channel[c]:.6f}  "
                       f"std={std_per_channel[c]:.6f}")

        return stats

    def generate_grain(
        self,
        shape: Tuple[int, ...],
        grain_stats: Dict,
        seed: int = None,
    ) -> np.ndarray:
        """Génère du grain procédural calibré sur les stats extraites.

        Algorithme :
        1. Pour chaque canal (B, G, R) :
           grain_channel = N(mean_c, std_c) de taille (H, W).
        2. Empiler → (H, W, 3) float32.

        Args:
            shape:       Forme cible (H, W) ou (H, W, 3).
            grain_stats: Stats issues de extract_grain_stats.
            seed:        Graine RNG (None = aléatoire).

        Returns:
            Grain float32 (H, W, 3).
        """
        rng = np.random.default_rng(seed)
        h, w = shape[0], shape[1]

        channels = []
        for c in range(3):
            ch = rng.normal(
                loc=grain_stats["mean_per_channel"][c],
                scale=grain_stats["std_per_channel"][c],
                size=(h, w),
            ).astype(PROCESSING_DTYPE)
            channels.append(ch)

        grain = np.stack(channels, axis=-1)
        self.debug(f"Grain généré — shape={grain.shape}, seed={seed}")
        return grain

    def apply_grain(
        self,
        render_frame: np.ndarray,
        grain_stats: Dict,
        intensity: float = None,
        seed: int = None,
    ) -> np.ndarray:
        """Applique du grain calibré à une frame render.

        Algorithme :
        1. Convertir render en float32 [0.0, 1.0].
        2. Générer le grain via generate_grain.
        3. output = render_float + grain * intensity.
        4. Clip [0.0, 1.0], reconvertir au dtype d'entrée.

        Args:
            render_frame: Frame BGR (uint8 ou uint16).
            grain_stats:  Stats issues de extract_grain_stats.
            intensity:    Force du grain [0.0, 1.0].
                          Default: GRAIN_DEFAULTS["intensity"].
            seed:         Graine RNG (None = aléatoire).

        Returns:
            Frame BGR avec grain (même dtype que l'entrée).
        """
        if intensity is None:
            intensity = float(GRAIN_DEFAULTS["intensity"])
        lo, hi = GRAIN_RANGES["intensity"]
        intensity = float(np.clip(intensity, lo, hi))

        original_dtype = render_frame.dtype
        render_f = self._to_float32(render_frame)

        grain = self.generate_grain(render_f.shape, grain_stats, seed=seed)
        output_f = render_f + grain * intensity
        output = self._from_float32(output_f, original_dtype)

        self.debug(f"Grain appliqué — intensity={intensity:.2f}")
        return output


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main() -> None:
    print("=" * 72)
    print("  GRAIN MATCHER — Test standalone avec image synthétique")
    print("=" * 72)

    h, w = 256, 256

    gradient = np.zeros((h, w, 3), dtype=np.uint8)
    ramp = np.tile(np.linspace(40, 200, w, dtype=np.uint8), (h, 1))
    gradient[:, :, 0] = ramp
    gradient[:, :, 1] = ramp
    gradient[:, :, 2] = ramp

    noisy = gradient.copy().astype(np.float64)
    rng = np.random.default_rng(42)
    noisy += rng.normal(0, 8.0, noisy.shape)
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)

    gm = GrainMatcher(verbose=True)

    print("\n--- Extraction du grain depuis l'image bruitée ---")
    stats = gm.extract_grain_stats([noisy])
    print(f"  global_std   : {stats['global_std']:.6f}")
    for c, name in enumerate(("B", "G", "R")):
        print(f"  {name}: mean={stats['mean_per_channel'][c]:.6f}  "
              f"std={stats['std_per_channel'][c]:.6f}")

    print("\n--- Application du grain calibré au gradient propre ---")
    result = gm.apply_grain(gradient, stats, intensity=1.0, seed=123)

    result_f = result.astype(np.float64) / UINT8_MAX
    gradient_f = gradient.astype(np.float64) / UINT8_MAX
    residual = result_f - gradient_f

    print("\n--- Stats du résidu appliqué ---")
    for c, name in enumerate(("B", "G", "R")):
        res_std = residual[:, :, c].std()
        expected = stats["std_per_channel"][c]
        ratio = res_std / expected if expected > 0 else float("inf")
        print(f"  {name}: std_résidu={res_std:.6f}  "
              f"std_calibré={expected:.6f}  "
              f"ratio={ratio:.2f}")

    expected_global = stats["global_std"]
    actual_global = np.mean([residual[:, :, c].std() for c in range(3)])
    tolerance = 0.5

    print(f"\n  Global std attendu : {expected_global:.6f}")
    print(f"  Global std obtenu  : {actual_global:.6f}")
    if abs(actual_global - expected_global) / max(expected_global, 1e-9) < tolerance:
        print("  [OK] Grain calibré correctement (ratio < 50% d'erreur).")
    else:
        print("  [WARN] Écart significatif — vérifier bilateral params.")

    print("\n  Test terminé.\n")


if __name__ == "__main__":
    main()
