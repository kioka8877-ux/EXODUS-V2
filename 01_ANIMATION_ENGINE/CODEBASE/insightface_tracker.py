#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     INSIGHTFACE TRACKER — Face Detection + Stable Face_ID Assignment        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Codex Imperial v6 — D-IV Orchestration Multi-Avatar                        ║
║  Détecte les visages humains dans video_source.mp4.                         ║
║  Assigne un Face_ID stable par personnage via clustering d'embeddings.      ║
║  Extrait les crops de visage pour EMOCA.                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

VOID-FLUSH Protocol: modèle InsightFace libéré après usage.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import insightface
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False


# ── Constantes ────────────────────────────────────────────────────────────────

EMBEDDING_SIM_THRESHOLD = 0.55   # cosine similarity pour fusionner deux identités
SAMPLE_RATE_FPS = 3               # frames analysées par seconde (performance)
MIN_DET_SCORE = 0.5               # score de détection minimum
CROP_MARGIN_RATIO = 0.25          # marge autour du bbox (25%)
MIN_FACE_SIZE = 40                # taille minimale d'un visage (pixels)


# ── Structures de données ─────────────────────────────────────────────────────

class FaceTrack:
    """Track d'un visage : embeddings + bboxes + frames."""
    def __init__(self, face_id: int):
        self.face_id = face_id
        self.embeddings: List[np.ndarray] = []
        self.bboxes: List[Tuple[int, int, int, int]] = []  # (x1, y1, x2, y2)
        self.frame_indices: List[int] = []
        self.crop_paths: List[str] = []

    @property
    def mean_embedding(self) -> Optional[np.ndarray]:
        if not self.embeddings:
            return None
        stack = np.stack(self.embeddings)
        mean = stack.mean(axis=0)
        norm = np.linalg.norm(mean)
        return mean / (norm + 1e-8)

    def add_detection(self, embedding: np.ndarray, bbox: Tuple, frame_idx: int):
        self.embeddings.append(embedding / (np.linalg.norm(embedding) + 1e-8))
        self.bboxes.append(bbox)
        self.frame_indices.append(frame_idx)

    def to_dict(self) -> dict:
        return {
            "face_id": self.face_id,
            "n_frames": len(self.frame_indices),
            "frame_indices": self.frame_indices,
            "bboxes": self.bboxes,
            "crop_paths": self.crop_paths,
        }


# ── Tracker ───────────────────────────────────────────────────────────────────

class InsightFaceTracker:
    """
    Détecte et suit les visages humains dans une vidéo.
    Assign un Face_ID stable par identité via clustering d'embeddings.
    """

    def __init__(
        self,
        app_name: str = "buffalo_l",
        device: str = "cuda",
        verbose: bool = False,
    ):
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError(
                "insightface non installé.\n"
                "  pip install insightface onnxruntime-gpu"
            )
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python non installé.  pip install opencv-python")

        self.verbose = verbose
        self.app = None
        self._app_name = app_name
        self._device = device
        self._ctx_id = 0 if device == "cuda" else -1

    # ── Init / Teardown ───────────────────────────────────────────────────────

    def setup(self):
        """Charge le modèle InsightFace."""
        self._log("Chargement InsightFace...")
        self.app = FaceAnalysis(
            name=self._app_name,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self.app.prepare(ctx_id=self._ctx_id, det_size=(640, 640))
        self._log("InsightFace prêt.")

    def teardown(self):
        """VOID-FLUSH: libère le modèle InsightFace."""
        if self.app is not None:
            del self.app
            self.app = None
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass
        try:
            import gc
            gc.collect()
        except Exception:
            pass
        self._log("VOID-FLUSH InsightFace: OK")

    # ── Tracking ──────────────────────────────────────────────────────────────

    def track_video(
        self,
        video_path: str,
        sample_fps: float = SAMPLE_RATE_FPS,
    ) -> Dict[int, FaceTrack]:
        """
        Parcourt video_path, détecte les visages, assigne Face_IDs stables.

        Returns:
            dict face_id → FaceTrack
        """
        if self.app is None:
            self.setup()

        video_path = str(video_path)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Impossible d'ouvrir la vidéo: {video_path}")

        vid_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_step = max(1, int(vid_fps / sample_fps))

        self._log(f"Vidéo: {total_frames} frames @ {vid_fps:.1f} FPS, step={frame_step}")

        tracks: Dict[int, FaceTrack] = {}
        next_id = 0
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                faces = self.app.get(frame)
                for face in faces:
                    if face.det_score < MIN_DET_SCORE:
                        continue
                    bbox = tuple(int(v) for v in face.bbox.astype(int))
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
                        continue

                    emb = face.embedding.astype(np.float32)
                    emb /= np.linalg.norm(emb) + 1e-8

                    # Trouver le track existant le plus proche
                    best_id = None
                    best_sim = -1.0
                    for fid, track in tracks.items():
                        ref = track.mean_embedding
                        if ref is not None:
                            sim = float(np.dot(emb, ref))
                            if sim > best_sim:
                                best_sim = sim
                                best_id = fid

                    if best_id is not None and best_sim >= EMBEDDING_SIM_THRESHOLD:
                        tracks[best_id].add_detection(emb, bbox, frame_idx)
                    else:
                        new_track = FaceTrack(next_id)
                        new_track.add_detection(emb, bbox, frame_idx)
                        tracks[next_id] = new_track
                        next_id += 1

            frame_idx += 1

        cap.release()
        self._log(f"Tracking terminé: {len(tracks)} identités détectées")

        # Filtrer les tracks fantômes (moins de 3 détections)
        tracks = {fid: t for fid, t in tracks.items() if len(t.frame_indices) >= 3}
        self._log(f"Tracks valides (≥3 détections): {len(tracks)}")
        return tracks

    # ── Extraction de crops ───────────────────────────────────────────────────

    def extract_crops(
        self,
        video_path: str,
        tracks: Dict[int, FaceTrack],
        output_dir: str,
        max_crops_per_face: int = 60,
    ) -> Dict[int, List[str]]:
        """
        Extrait et sauvegarde les crops de visage par Face_ID.

        Returns:
            dict face_id → liste de chemins PNG
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise IOError(f"Impossible d'ouvrir la vidéo: {video_path}")

        # Construire un index frame → [(face_id, bbox)]
        frame_face_map: Dict[int, List[Tuple[int, tuple]]] = {}
        for fid, track in tracks.items():
            for i, fidx in enumerate(track.frame_indices):
                if fidx not in frame_face_map:
                    frame_face_map[fidx] = []
                frame_face_map[fidx].append((fid, track.bboxes[i]))

        # Calculer quels frames extraire (échantillonnage uniforme)
        face_crop_counts: Dict[int, int] = {fid: 0 for fid in tracks}
        result_paths: Dict[int, List[str]] = {fid: [] for fid in tracks}

        needed_frames = sorted(frame_face_map.keys())

        frame_idx = 0
        needed_set = set(needed_frames)

        while needed_set:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx in needed_set:
                needed_set.discard(frame_idx)
                for fid, bbox in frame_face_map[frame_idx]:
                    if face_crop_counts[fid] >= max_crops_per_face:
                        continue
                    crop = self._extract_crop(frame, bbox)
                    if crop is None:
                        continue
                    crop_path = str(
                        output_dir / f"face_{fid:02d}_frame_{frame_idx:06d}.png"
                    )
                    cv2.imwrite(crop_path, crop)
                    result_paths[fid].append(crop_path)
                    face_crop_counts[fid] += 1

            frame_idx += 1

        cap.release()

        # Stocker les paths dans les tracks
        for fid, paths in result_paths.items():
            if fid in tracks:
                tracks[fid].crop_paths = paths

        for fid, paths in result_paths.items():
            self._log(f"Face {fid}: {len(paths)} crops extraits")

        return result_paths

    # ── Mapping avatars ───────────────────────────────────────────────────────

    def map_to_avatars(
        self,
        tracks: Dict[int, FaceTrack],
        production_plan: dict,
    ) -> Dict[int, str]:
        """
        Mappe Face_ID → avatar_name depuis PRODUCTION_PLAN.JSON.

        Le plan peut contenir un bloc 'face_avatar_mapping':
          {"0": "avatar-ferrus-0", "1": "avatar-ferrus-1"}
        Si absent, mapping par ordre d'apparition (Face_ID 0 → avatar 0).

        Returns:
            dict face_id → avatar_name (ex: "avatar-ferrus-0")
        """
        explicit = production_plan.get("face_avatar_mapping", {})
        if explicit:
            result = {}
            for sid, avatar_name in explicit.items():
                result[int(sid)] = avatar_name
            self._log(f"Mapping explicite: {result}")
            return result

        # Fallback : tri par premier frame d'apparition → avatar-ferrus-N
        ordered = sorted(tracks.keys(), key=lambda fid: tracks[fid].frame_indices[0])
        result = {fid: f"avatar-ferrus-{i}" for i, fid in enumerate(ordered)}
        self._log(f"Mapping auto (ordre d'apparition): {result}")
        return result

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _extract_crop(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        """Extrait un crop centré sur le visage avec marge."""
        x1, y1, x2, y2 = bbox
        h_img, w_img = frame.shape[:2]
        w = x2 - x1
        h = y2 - y1
        if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
            return None
        margin_x = int(w * CROP_MARGIN_RATIO)
        margin_y = int(h * CROP_MARGIN_RATIO)
        x1c = max(0, x1 - margin_x)
        y1c = max(0, y1 - margin_y)
        x2c = min(w_img, x2 + margin_x)
        y2c = min(h_img, y2 + margin_y)
        crop = frame[y1c:y2c, x1c:x2c]
        if crop.size == 0:
            return None
        crop_resized = cv2.resize(crop, (224, 224))
        return crop_resized

    def _log(self, msg: str):
        if self.verbose:
            print(f"[INSIGHTFACE] {msg}")

    # ── Rapport ───────────────────────────────────────────────────────────────

    def create_report(
        self,
        tracks: Dict[int, FaceTrack],
        avatar_mapping: Dict[int, str],
    ) -> dict:
        """Génère un rapport JSON du tracking."""
        return {
            "n_identities": len(tracks),
            "avatar_mapping": {str(k): v for k, v in avatar_mapping.items()},
            "faces": {
                str(fid): {
                    **t.to_dict(),
                    "avatar": avatar_mapping.get(fid, f"unknown_{fid}"),
                }
                for fid, t in tracks.items()
            },
        }


# ── CLI standalone ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="InsightFace Tracker CLI")
    parser.add_argument("--video", required=True, help="video_source.mp4")
    parser.add_argument("--output-dir", required=True, help="Dossier crops output")
    parser.add_argument("--report", default=None, help="Chemin rapport JSON")
    parser.add_argument("--sample-fps", type=float, default=SAMPLE_RATE_FPS)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    tracker = InsightFaceTracker(device=args.device, verbose=True)
    try:
        tracks = tracker.track_video(args.video, sample_fps=args.sample_fps)
        crops = tracker.extract_crops(args.video, tracks, args.output_dir)
        mapping = tracker.map_to_avatars(tracks, {})
        report = tracker.create_report(tracks, mapping)

        if args.report:
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Rapport: {args.report}")

        print(f"\n[OK] {len(tracks)} identités | {sum(len(p) for p in crops.values())} crops")
    finally:
        tracker.teardown()
