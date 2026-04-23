#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     EMOCA EXTRACTOR — Real Human Face → Expression Parameters               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Codex Imperial v6 — D-II EMOCA sur Visage Humain Réel                      ║
║  EMOCA opère sur le VRAI visage humain (plage d'entraînement naturelle).    ║
║  InsightFace isole la crop correcte par avatar avant chaque passage.        ║
║  Output: segments compatible facial_animation.json → expression_schema.py  ║
║  VOID-FLUSH: modèle EMOCA libéré après traitement de chaque avatar.        ║
╚══════════════════════════════════════════════════════════════════════════════╝

VRAM peak: ~4GB (EMOCA ViT-L backbone)
Setup:
    git clone https://github.com/radekd91/emoca /opt/emoca
    cd /opt/emoca && pip install -r requirements.txt
    # Télécharger les modèles EMOCA depuis https://emoca.is.tue.mpg.de/
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    NP_AVAILABLE = True
except ImportError:
    NP_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# EMOCA — optionnel (nécessite installation séparée)
EMOCA_AVAILABLE = False
try:
    sys.path.insert(0, "/opt/emoca")
    from gdl.models.DECA import EMOCA
    from gdl_apps.EMOCA.utils.load import load_model as emoca_load_model
    EMOCA_AVAILABLE = True
except ImportError:
    pass


# ── Constantes ────────────────────────────────────────────────────────────────

VRAM_PEAK_GB = 4.0
VRAM_THRESHOLD_FREE_GB = 0.5    # VRAM libre minimum post-flush

# Mapping EMOCA expression dimension → preset expression_schema
# Les 5 premières dimensions de expcode correspondent aux expressions principales
# (ordre empirique: smile, brow_raise, brow_furrow, mouth_open, eye_squint)
EXPCODE_TO_PRESET = {
    # dim_idx: (seuil activation, preset si positif, preset si négatif)
    0: (0.3, "joy", "sadness"),           # dim 0 ≈ valence
    1: (0.3, "surprise", "suspicious"),   # dim 1 ≈ raised brows
    2: (0.25, "anger", "determined"),     # dim 2 ≈ brow furrow
    3: (0.2, "excited", "bored"),         # dim 3 ≈ activation
    4: (0.2, "pain", "neutral"),          # dim 4 ≈ negative valence
}

# Expression par défaut si aucune dimension dépasse le seuil
DEFAULT_EXPRESSION = "neutral"
DEFAULT_EYES = "focused_forward"
DEFAULT_MOUTH = "neutral"

# Mapping mouth open (jawOpen) → mouth preset
JAW_OPEN_THRESHOLD = 0.25

# Intervalle de segmentation temporelle (secondes)
SEGMENT_INTERVAL_S = 0.5


# ── Structures de données ─────────────────────────────────────────────────────

class ExpressionSegment:
    """Segment d'expression pour facial_animation.json."""
    def __init__(
        self,
        time_start: float,
        time_end: float,
        expression: str,
        eyes: str,
        mouth: str,
        intensity: float,
        apex_time: Optional[float] = None,
    ):
        self.time_start = time_start
        self.time_end = time_end
        self.expression = expression
        self.eyes = eyes
        self.mouth = mouth
        self.intensity = intensity
        self.apex_time = apex_time if apex_time else (time_start + time_end) / 2.0
        self.low_visibility = False

    def to_dict(self) -> dict:
        return {
            "time_start": round(self.time_start, 3),
            "time_end": round(self.time_end, 3),
            "expression": self.expression,
            "eyes": self.eyes,
            "mouth": self.mouth,
            "intensity": round(self.intensity, 3),
            "apex_time": round(self.apex_time, 3),
            "low_visibility": self.low_visibility,
        }


# ── Extracteur EMOCA ─────────────────────────────────────────────────────────

class EMOCAExtractor:
    """
    Extrait les paramètres d'expression du visage humain réel via EMOCA.
    Mappe vers les presets de expression_schema.py.

    Si EMOCA n'est pas disponible, bascule sur OpenCV Haar + règles simples.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cuda",
        verbose: bool = False,
    ):
        self.device = device
        self.verbose = verbose
        self._model_path = model_path or os.environ.get(
            "EMOCA_MODEL_PATH", "/opt/emoca/assets/EMOCA/models/EMOCA_v2_lr_mse_20"
        )
        self._model = None
        self._use_fallback = not EMOCA_AVAILABLE

        if self._use_fallback:
            self._log(
                "EMOCA non disponible — mode fallback OpenCV activé.\n"
                "  Pour EMOCA complet: git clone https://github.com/radekd91/emoca /opt/emoca"
            )

    # ── Init / Teardown ───────────────────────────────────────────────────────

    def setup(self):
        """Charge le modèle EMOCA (ou active le fallback)."""
        if self._use_fallback:
            return

        self._log(f"Chargement EMOCA depuis {self._model_path}...")
        model_path = Path(self._model_path)
        if not model_path.exists():
            self._log(
                f"Modèle EMOCA introuvable: {model_path}\n"
                "  Téléchargez depuis https://emoca.is.tue.mpg.de/\n"
                "  Activation du mode fallback."
            )
            self._use_fallback = True
            return

        self._check_vram(min_required_gb=3.5)
        try:
            self._model, _ = emoca_load_model(str(model_path), mode="coarse")
            self._model.eval()
            if self.device == "cuda":
                self._model = self._model.cuda()
            self._log("EMOCA prêt.")
        except Exception as e:
            self._log(f"Erreur chargement EMOCA: {e} — fallback activé")
            self._use_fallback = True

    def teardown(self):
        """VOID-FLUSH: libère EMOCA + GPU."""
        if self._model is not None:
            del self._model
            self._model = None
        if TORCH_AVAILABLE:
            try:
                import gc
                gc.collect()
                torch.cuda.empty_cache()
                free_gb = self._get_free_vram_gb()
                if free_gb < VRAM_THRESHOLD_FREE_GB:
                    self._log(f"WARN: VRAM libre après flush: {free_gb:.1f}GB")
                else:
                    self._log(f"VOID-FLUSH EMOCA: OK ({free_gb:.1f}GB libres)")
            except Exception:
                pass

    # ── Extraction principale ─────────────────────────────────────────────────

    def extract_from_crops(
        self,
        crop_paths: List[str],
        video_fps: float = 30.0,
        frame_indices: Optional[List[int]] = None,
    ) -> List[ExpressionSegment]:
        """
        Analyse les crops de visage et retourne des segments d'expression.

        Args:
            crop_paths: liste de chemins PNG (224x224, sortie InsightFace)
            video_fps: FPS de la vidéo source
            frame_indices: indices de frames correspondants (auto si None)

        Returns:
            liste de ExpressionSegment (format facial_animation.json)
        """
        if not crop_paths:
            return [self._default_segment(0.0, 1.0)]

        if self._model is None and not self._use_fallback:
            self.setup()

        if frame_indices is None:
            frame_indices = list(range(len(crop_paths)))

        # Extraire les paramètres par frame
        frame_data: List[dict] = []
        for i, (crop_path, frame_idx) in enumerate(zip(crop_paths, frame_indices)):
            time_s = frame_idx / video_fps
            params = self._extract_single(crop_path)
            params["time"] = time_s
            params["frame"] = frame_idx
            frame_data.append(params)

        # ── SMOOTHING (SENTINEL FIX: intégration smoothing.py) ───────────────
        # Applique Savitzky-Golay sur les intensités brutes avant segmentation.
        # Réduit le jitter d'expression frame-à-frame → segments plus stables.
        frame_data = self._smooth_frame_intensities(frame_data)

        # Segmenter en intervals temporels
        segments = self._temporalize_params(frame_data, video_fps)
        self._log(f"Extraction: {len(crop_paths)} crops → {len(segments)} segments")
        return segments

    # ── Extraction par frame ──────────────────────────────────────────────────

    def _extract_single(self, crop_path: str) -> dict:
        """
        Extrait les paramètres d'expression d'une crop.
        Retourne un dict avec 'expression', 'eyes', 'mouth', 'intensity'.
        """
        if not Path(crop_path).exists():
            return self._default_params()

        if not self._use_fallback and self._model is not None:
            return self._extract_emoca(crop_path)
        else:
            return self._extract_fallback(crop_path)

    def _extract_emoca(self, crop_path: str) -> dict:
        """Extraction via EMOCA (chemin nominal)."""
        try:
            import torch
            from PIL import Image
            import torchvision.transforms as T

            img = Image.open(crop_path).convert("RGB")
            transform = T.Compose([T.Resize((224, 224)), T.ToTensor()])
            img_t = transform(img).unsqueeze(0)
            if self.device == "cuda":
                img_t = img_t.cuda()

            with torch.no_grad():
                out = self._model.encode({"image": img_t})
                expcode = out.get("expcode", out.get("exp_code", None))
                if expcode is None:
                    return self._default_params()
                expcode = expcode.cpu().numpy().flatten()

            return self._map_expcode_to_preset(expcode)

        except Exception as e:
            self._log(f"Erreur EMOCA sur {crop_path}: {e}")
            return self._default_params()

    def _extract_fallback(self, crop_path: str) -> dict:
        """
        Fallback OpenCV: détecte émotions simplifiées via analyse d'image.
        Utilisé si EMOCA n'est pas installé.
        """
        if not CV2_AVAILABLE or not NP_AVAILABLE:
            return self._default_params()

        try:
            img = cv2.imread(str(crop_path))
            if img is None:
                return self._default_params()

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Détecter bouche ouverte via région inférieure du visage
            h, w = gray.shape
            mouth_region = gray[int(h * 0.65):int(h * 0.9), int(w * 0.2):int(w * 0.8)]
            jaw_open_score = float(mouth_region.std()) / 128.0  # Variance ≈ ouverture

            # Détecter les sourcils via région supérieure
            brow_region = gray[int(h * 0.15):int(h * 0.4), int(w * 0.1):int(w * 0.9)]
            brow_score = float(brow_region.mean()) / 255.0

            # Mapping simplifié
            if jaw_open_score > 0.4:
                expression = "excited"
                mouth = "wide_open"
                intensity = min(1.0, jaw_open_score)
            elif brow_score < 0.35:
                expression = "suspicious"
                mouth = "closed_tight"
                intensity = 0.5
            else:
                expression = "neutral"
                mouth = "neutral"
                intensity = 0.4

            return {
                "expression": expression,
                "eyes": DEFAULT_EYES,
                "mouth": mouth,
                "intensity": intensity,
            }

        except Exception:
            return self._default_params()

    # ── Mapping expcode → presets ─────────────────────────────────────────────

    def _map_expcode_to_preset(self, expcode: "np.ndarray") -> dict:
        """
        Mappe le code d'expression EMOCA (50-dim FLAME) vers les presets
        de expression_schema.py.
        """
        # Normaliser le code
        norm = float(np.linalg.norm(expcode))
        if norm < 1e-6:
            return self._default_params()
        expcode_norm = expcode / norm

        # Intensité globale = norme du vecteur
        intensity = min(1.0, norm / 5.0)
        intensity = max(0.2, intensity)

        # Trouver la dimension dominante
        best_preset = DEFAULT_EXPRESSION
        best_score = 0.0

        for dim_idx, (threshold, pos_preset, neg_preset) in EXPCODE_TO_PRESET.items():
            if dim_idx < len(expcode_norm):
                val = float(expcode_norm[dim_idx])
                score = abs(val)
                if score > threshold and score > best_score:
                    best_score = score
                    best_preset = pos_preset if val > 0 else neg_preset

        # Détecter bouche ouverte (dim 3 de posecode ou expcode[25] ≈ jawOpen en FLAME)
        jaw_open = False
        if len(expcode) > 25:
            jaw_open = float(abs(expcode[25])) > JAW_OPEN_THRESHOLD
        mouth_preset = "wide_open" if jaw_open else DEFAULT_MOUTH

        # Eyes: utiliser dim 4-5 (yeux)
        eyes_preset = DEFAULT_EYES
        if len(expcode) > 5:
            eye_val = float(expcode_norm[4])
            if eye_val > 0.3:
                eyes_preset = "narrowed"
            elif eye_val < -0.3:
                eyes_preset = "wide_open"

        return {
            "expression": best_preset,
            "eyes": eyes_preset,
            "mouth": mouth_preset,
            "intensity": round(intensity, 3),
        }

    # ── Smoothing des intensités brutes ──────────────────────────────────────

    def _smooth_frame_intensities(self, frame_data: List[dict]) -> List[dict]:
        """
        Applique un filtre Savitzky-Golay sur les intensités par frame.
        Réduit le jitter sans effacer les peaks (window=5, order=2).
        Si numpy/scipy indisponibles, retourne frame_data inchangé.
        """
        if not NP_AVAILABLE or len(frame_data) < 5:
            return frame_data
        try:
            from smoothing import savgol_smooth
            intensities = np.array([fd["intensity"] for fd in frame_data])
            smoothed = savgol_smooth(intensities, window=5, order=2)
            result = []
            for fd, sv in zip(frame_data, smoothed):
                new_fd = dict(fd)
                new_fd["intensity"] = float(np.clip(sv, 0.1, 1.0))
                result.append(new_fd)
            self._log(f"Smoothing OK: {len(result)} frames lissées (SavGol w=5)")
            return result
        except Exception as e:
            self._log(f"Smoothing skip: {e}")
            return frame_data

    # ── Segmentation temporelle ───────────────────────────────────────────────

    def _temporalize_params(
        self,
        frame_data: List[dict],
        video_fps: float,
    ) -> List[ExpressionSegment]:
        """
        Fusionne les paramètres par frame en segments temporels.
        Groupe les frames consécutives avec la même expression.
        """
        if not frame_data:
            return [self._default_segment(0.0, 1.0)]

        segments = []
        current_expr = frame_data[0]["expression"]
        current_eyes = frame_data[0]["eyes"]
        current_mouth = frame_data[0]["mouth"]
        current_intensities = [frame_data[0]["intensity"]]
        seg_start = frame_data[0]["time"]
        last_time = frame_data[0]["time"]

        for i in range(1, len(frame_data)):
            fd = frame_data[i]
            same_group = (
                fd["expression"] == current_expr
                and (fd["time"] - seg_start) < 3.0  # max 3s par segment
            )

            if same_group:
                current_intensities.append(fd["intensity"])
                last_time = fd["time"]
            else:
                # Fermer le segment courant
                seg_end = last_time + SEGMENT_INTERVAL_S
                avg_intensity = float(np.mean(current_intensities)) if NP_AVAILABLE else sum(current_intensities) / len(current_intensities)
                apex = seg_start + (seg_end - seg_start) * 0.4
                segments.append(ExpressionSegment(
                    time_start=seg_start,
                    time_end=seg_end,
                    expression=current_expr,
                    eyes=current_eyes,
                    mouth=current_mouth,
                    intensity=round(avg_intensity, 3),
                    apex_time=apex,
                ))
                # Démarrer nouveau segment
                current_expr = fd["expression"]
                current_eyes = fd["eyes"]
                current_mouth = fd["mouth"]
                current_intensities = [fd["intensity"]]
                seg_start = fd["time"]
                last_time = fd["time"]

        # Dernier segment
        seg_end = last_time + SEGMENT_INTERVAL_S
        avg_intensity = float(np.mean(current_intensities)) if NP_AVAILABLE else sum(current_intensities) / len(current_intensities)
        apex = seg_start + (seg_end - seg_start) * 0.4
        segments.append(ExpressionSegment(
            time_start=seg_start,
            time_end=seg_end,
            expression=current_expr,
            eyes=current_eyes,
            mouth=current_mouth,
            intensity=round(avg_intensity, 3),
            apex_time=apex,
        ))

        return segments

    # ── Sortie facial_animation.json ─────────────────────────────────────────

    def to_facial_animation_json(
        self,
        segments: List[ExpressionSegment],
        avatar_name: str = "avatar-ferrus-0",
    ) -> dict:
        """
        Génère un dict au format facial_animation.json
        compatible avec EmotionalIntentTranslator de facial_extractor.py.
        """
        return {
            "source": "emoca_extractor",
            "avatar": avatar_name,
            "facial_animation": [s.to_dict() for s in segments],
        }

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _default_params(self) -> dict:
        return {
            "expression": DEFAULT_EXPRESSION,
            "eyes": DEFAULT_EYES,
            "mouth": DEFAULT_MOUTH,
            "intensity": 0.5,
        }

    def _default_segment(self, start: float, end: float) -> ExpressionSegment:
        return ExpressionSegment(
            time_start=start,
            time_end=end,
            expression=DEFAULT_EXPRESSION,
            eyes=DEFAULT_EYES,
            mouth=DEFAULT_MOUTH,
            intensity=0.5,
        )

    def _get_free_vram_gb(self) -> float:
        if not TORCH_AVAILABLE:
            return 0.0
        try:
            free, total = torch.cuda.mem_get_info(0)
            return free / 1e9
        except Exception:
            return 0.0

    def _check_vram(self, min_required_gb: float = 3.5):
        if not TORCH_AVAILABLE:
            return
        free_gb = self._get_free_vram_gb()
        if free_gb < min_required_gb:
            self._log(
                f"WARN: VRAM disponible ({free_gb:.1f}GB) < minimum requis ({min_required_gb:.1f}GB). "
                "EMOCA risque d'échouer. Libérez la VRAM ou utilisez --skip-emoca."
            )

    def _log(self, msg: str):
        if self.verbose:
            print(f"[EMOCA] {msg}")


# ── CLI standalone ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EMOCA Extractor CLI")
    parser.add_argument("--crops-dir", required=True, help="Dossier des crops PNG")
    parser.add_argument("--output", required=True, help="facial_animation.json output")
    parser.add_argument("--avatar-name", default="avatar-ferrus-0")
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    extractor = EMOCAExtractor(
        model_path=args.model_path,
        device=args.device,
        verbose=True,
    )
    try:
        crops_dir = Path(args.crops_dir)
        crops = sorted([str(p) for p in crops_dir.glob("*.png")])
        print(f"[EMOCA] {len(crops)} crops trouvés")

        segments = extractor.extract_from_crops(crops, video_fps=args.fps)
        result = extractor.to_facial_animation_json(segments, avatar_name=args.avatar_name)

        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)

        print(f"[OK] {len(segments)} segments → {args.output}")
    finally:
        extractor.teardown()
