#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 MATCH COLOR — EXODUS ALCHEMIST LAB                          ║
║          Histogram Specification (LAB) — Fusion Couleur Source/Render       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Aligne la distribution couleur d'un rendu 3D sur une vidéo source
via histogram matching en espace LAB. Stabilité temporelle par
histogramme de référence par scène.

Moteur : OpenCV + numpy
"""

import sys
from typing import Dict, List, Optional

import cv2
import numpy as np

from alchemist_schema import (
    MATCH_COLOR_DEFAULTS,
    MATCH_COLOR_RANGES,
    VALID_COLOR_SPACES,
    DEFAULT_COLOR_SPACE,
    VALID_REFERENCE_STRATEGIES,
    UINT8_MAX,
    UINT16_MAX,
    PROCESSING_DTYPE,
)


# =============================================================================
# CONVERSIONS COLOR SPACE
# =============================================================================

_BGR_TO_CS = {
    "LAB": cv2.COLOR_BGR2LAB,
    "RGB": cv2.COLOR_BGR2RGB,
    "YCrCb": cv2.COLOR_BGR2YCrCb,
}

_CS_TO_BGR = {
    "LAB": cv2.COLOR_LAB2BGR,
    "RGB": cv2.COLOR_RGB2BGR,
    "YCrCb": cv2.COLOR_YCrCb2BGR,
}

_CHANNEL_NAMES = {
    "LAB": ("L", "A", "B"),
    "RGB": ("R", "G", "B"),
    "YCrCb": ("Y", "Cr", "Cb"),
}


class MatchColor:
    """Histogram-specification color matcher — aligne la palette couleur
    d'un render 3D sur la vidéo source, canal par canal dans l'espace
    couleur choisi (LAB par défaut)."""

    def __init__(self, color_space: str = None, verbose: bool = False):
        """Initialise avec le color space depuis la Bible.

        Args:
            color_space: Espace couleur cible. Doit figurer dans
                         VALID_COLOR_SPACES. Par défaut DEFAULT_COLOR_SPACE.
            verbose:     Active les logs de debug.
        """
        self.color_space: str = color_space or DEFAULT_COLOR_SPACE
        if self.color_space not in VALID_COLOR_SPACES:
            self.log(f"Color space '{self.color_space}' invalide, "
                     f"fallback → {DEFAULT_COLOR_SPACE}")
            self.color_space = DEFAULT_COLOR_SPACE
        self.verbose: bool = verbose
        self.operations: List[dict] = []
        self.log(f"MatchColor initialisé — espace: {self.color_space}")

    # -----------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------

    def log(self, msg: str) -> None:
        """Log toujours affiché."""
        print(f"[MATCH_COLOR] {msg}")
        self.operations.append({"action": "log", "message": msg})

    def debug(self, msg: str) -> None:
        """Log conditionnel (verbose)."""
        if self.verbose:
            print(f"[MATCH_COLOR:DEBUG] {msg}")

    # -----------------------------------------------------------------
    # Utilitaires internes
    # -----------------------------------------------------------------

    def _to_cs(self, frame_bgr: np.ndarray) -> np.ndarray:
        """BGR → color-space choisi."""
        return cv2.cvtColor(frame_bgr, _BGR_TO_CS[self.color_space])

    def _to_bgr(self, frame_cs: np.ndarray) -> np.ndarray:
        """Color-space choisi → BGR."""
        return cv2.cvtColor(frame_cs, _CS_TO_BGR[self.color_space])

    @staticmethod
    def _calc_cdf(hist: np.ndarray) -> np.ndarray:
        """Calcule la CDF normalisée d'un histogramme."""
        cdf = np.cumsum(hist).astype(PROCESSING_DTYPE)
        total = cdf[-1]
        if total > 0:
            cdf /= total
        return cdf

    def _select_frames(
        self,
        source_frames: List[np.ndarray],
        strategy: str,
        sample_count: int,
    ) -> List[np.ndarray]:
        """Sélectionne les frames selon la stratégie demandée.

        Args:
            source_frames: Liste complète de frames BGR.
            strategy:      "uniform" | "first_n" | "random".
            sample_count:  Nombre max de frames à utiliser.

        Returns:
            Sous-liste de frames sélectionnées.
        """
        n = len(source_frames)
        count = min(sample_count, n)

        if strategy == "first_n":
            selected = source_frames[:count]
        elif strategy == "random":
            indices = np.random.choice(n, size=count, replace=False)
            selected = [source_frames[i] for i in sorted(indices)]
        else:
            selected = list(source_frames)

        self.debug(f"Stratégie '{strategy}' → {len(selected)}/{n} frames")
        return selected

    # -----------------------------------------------------------------
    # API publique
    # -----------------------------------------------------------------

    def compute_reference_histogram(
        self,
        source_frames: List[np.ndarray],
        strategy: str = None,
    ) -> Dict[str, np.ndarray]:
        """Calcule l'histogramme de référence (CDFs) à partir de frames source.

        Algorithme :
        1. Convertir chaque frame en color-space cible.
        2. Pour chaque canal, accumuler les histogrammes (256 bins).
        3. Normaliser les histogrammes accumulés.
        4. Calculer la CDF normalisée par canal.

        Args:
            source_frames: Liste de frames BGR (numpy uint8).
            strategy:      Stratégie de sélection des frames
                           (default: MATCH_COLOR_DEFAULTS["reference_strategy"]).

        Returns:
            Dict avec une CDF (array 256) par nom de canal.
        """
        if not source_frames:
            raise ValueError("source_frames est vide")

        strategy = strategy or MATCH_COLOR_DEFAULTS["reference_strategy"]
        if strategy not in VALID_REFERENCE_STRATEGIES:
            self.log(f"Stratégie '{strategy}' invalide → "
                     f"fallback '{MATCH_COLOR_DEFAULTS['reference_strategy']}'")
            strategy = MATCH_COLOR_DEFAULTS["reference_strategy"]

        sample_count = int(MATCH_COLOR_DEFAULTS["reference_sample_count"])
        selected = self._select_frames(source_frames, strategy, sample_count)

        ch_names = _CHANNEL_NAMES[self.color_space]
        accum_hists = {name: np.zeros(256, dtype=PROCESSING_DTYPE) for name in ch_names}

        for frame in selected:
            cs_frame = self._to_cs(frame)
            for c, name in enumerate(ch_names):
                hist = cv2.calcHist([cs_frame], [c], None, [256], [0, 256])
                accum_hists[name] += hist.ravel()

        reference_cdfs: Dict[str, np.ndarray] = {}
        for name in ch_names:
            reference_cdfs[name] = self._calc_cdf(accum_hists[name])

        self.log(f"Référence calculée — {len(selected)} frames, "
                 f"canaux: {list(ch_names)}")
        return reference_cdfs

    def match_frame(
        self,
        render_frame: np.ndarray,
        reference_cdfs: Dict[str, np.ndarray],
        intensity: float = None,
    ) -> np.ndarray:
        """Applique le histogram matching à une frame render.

        Algorithme :
        1. Convertir render en color-space cible.
        2. Pour chaque canal :
           a. Calculer la CDF du canal render.
           b. Construire une LUT 256 via np.interp(render_cdf, ref_cdf, arange).
           c. Appliquer la LUT.
        3. Reconvertir en BGR.
        4. Blend : output = render*(1-intensity) + matched*intensity.

        Args:
            render_frame:   Frame render BGR (uint8).
            reference_cdfs: CDFs de référence (sortie de compute_reference_histogram).
            intensity:      Force du matching [0.0, 1.0].
                            Default: MATCH_COLOR_DEFAULTS["intensity"].

        Returns:
            Frame BGR matched (même dtype que l'entrée).
        """
        if intensity is None:
            intensity = float(MATCH_COLOR_DEFAULTS["intensity"])
        lo, hi = MATCH_COLOR_RANGES["intensity"]
        intensity = float(np.clip(intensity, lo, hi))

        ch_names = _CHANNEL_NAMES[self.color_space]
        cs_frame = self._to_cs(render_frame)
        matched_channels = []

        for c, name in enumerate(ch_names):
            channel = cs_frame[:, :, c]
            hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
            render_cdf = self._calc_cdf(hist.ravel())

            ref_cdf = reference_cdfs[name]
            lut = np.interp(render_cdf, ref_cdf, np.arange(256)).astype(np.uint8)
            matched_channels.append(lut[channel])

        matched_cs = np.stack(matched_channels, axis=-1).astype(np.uint8)
        matched_bgr = self._to_bgr(matched_cs)

        output = cv2.addWeighted(
            render_frame, 1.0 - intensity,
            matched_bgr, intensity,
            0.0,
        )
        self.debug(f"Frame matched — intensity={intensity:.2f}")
        return output


# =============================================================================
# STANDALONE TEST
# =============================================================================

def _channel_stats(frame_bgr: np.ndarray, label: str) -> None:
    """Affiche mean / std par canal BGR."""
    for c, name in enumerate(("B", "G", "R")):
        ch = frame_bgr[:, :, c].astype(PROCESSING_DTYPE)
        print(f"  {label} {name}: mean={ch.mean():.2f}  std={ch.std():.2f}")


def main() -> None:
    print("=" * 72)
    print("  MATCH COLOR — Test standalone avec images synthétiques")
    print("=" * 72)

    h, w = 256, 256

    source_r = np.zeros((h, w, 3), dtype=np.uint8)
    source_r[:, :, 2] = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    source_r[:, :, 1] = 30

    render_b = np.zeros((h, w, 3), dtype=np.uint8)
    render_b[:, :, 0] = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    render_b[:, :, 1] = 30

    print("\n--- Stats AVANT matching ---")
    _channel_stats(source_r, "Source (rouge)")
    _channel_stats(render_b, "Render (bleu) ")

    mc = MatchColor(verbose=True)
    ref_cdfs = mc.compute_reference_histogram([source_r])
    matched = mc.match_frame(render_b, ref_cdfs)

    print("\n--- Stats APRÈS matching ---")
    _channel_stats(matched, "Matched       ")

    src_mean_r = source_r[:, :, 2].astype(float).mean()
    out_mean_r = matched[:, :, 2].astype(float).mean()
    delta = abs(src_mean_r - out_mean_r)
    threshold = 30.0

    print(f"\n  Delta mean(R) source vs matched : {delta:.2f}")
    if delta < threshold:
        print("  [OK] Histogram matching a rapproché les distributions.")
    else:
        print("  [WARN] Delta élevé — vérifier le pipeline.")

    print("\n  Test terminé.\n")


if __name__ == "__main__":
    main()
