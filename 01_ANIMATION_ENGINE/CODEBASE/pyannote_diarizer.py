#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     PYANNOTE DIARIZER — Speaker Diarization + Per-Avatar Audio Track        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Codex Imperial v6 — D-III Lip-Sync Obligatoire + D-IV Multi-Avatar         ║
║  Identifie quel speaker parle à quel moment.                                ║
║  Génère un fichier WAV propre par avatar (silence hors parole).             ║
║  Rhubarb reçoit ces pistes propres → lip-sync précis par avatar.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import shutil
import struct
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    NP_AVAILABLE = True
except ImportError:
    NP_AVAILABLE = False

try:
    from pyannote.audio import Pipeline as PyannotePipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False

try:
    import soundfile as sf
    SF_AVAILABLE = True
except ImportError:
    SF_AVAILABLE = False


# ── Structures de données ─────────────────────────────────────────────────────

class SpeakerSegment:
    """Segment de parole d'un speaker."""
    def __init__(self, speaker_id: str, start: float, end: float):
        self.speaker_id = speaker_id
        self.start = start
        self.end = end

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {"speaker_id": self.speaker_id, "start": self.start, "end": self.end}


# ── Diarizer ──────────────────────────────────────────────────────────────────

class PyannoteDiarizer:
    """
    Speaker diarization via pyannote.audio.
    Génère des pistes audio propres par avatar pour Rhubarb lip-sync.

    Nécessite: pip install pyannote.audio
    Nécessite: Hugging Face token avec accès pyannote/speaker-diarization-3.1
    """

    MODEL_ID = "pyannote/speaker-diarization-3.1"

    def __init__(
        self,
        hf_token: Optional[str] = None,
        device: str = "cuda",
        verbose: bool = False,
    ):
        self.hf_token = hf_token or os.environ.get("HF_TOKEN", "")
        self.device = device
        self.verbose = verbose
        self._pipeline = None

    # ── Init / Teardown ───────────────────────────────────────────────────────

    def setup(self):
        """Charge le pipeline pyannote."""
        if not PYANNOTE_AVAILABLE:
            raise ImportError(
                "pyannote.audio non installé.\n"
                "  pip install pyannote.audio\n"
                "  Puis accepter les conditions sur huggingface.co/pyannote/speaker-diarization-3.1"
            )
        if not self.hf_token:
            raise ValueError(
                "HF_TOKEN requis pour pyannote/speaker-diarization-3.1.\n"
                "  Exportez: export HF_TOKEN=hf_xxxx\n"
                "  Ou passez --hf-token"
            )
        self._log("Chargement pipeline pyannote...")
        self._pipeline = PyannotePipeline.from_pretrained(
            self.MODEL_ID,
            use_auth_token=self.hf_token,
        )
        if self.device == "cuda":
            import torch
            self._pipeline = self._pipeline.to(torch.device("cuda"))
        self._log("Pipeline pyannote prêt.")

    def teardown(self):
        """Libère le pipeline pyannote."""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
        try:
            import gc
            gc.collect()
        except Exception:
            pass
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass
        self._log("VOID-FLUSH pyannote: OK")

    # ── Diarization ───────────────────────────────────────────────────────────

    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
    ) -> Dict[str, List[SpeakerSegment]]:
        """
        Lance la diarisation sur audio_path.

        Args:
            audio_path: chemin vers audio_original.wav
            num_speakers: nombre de speakers attendus (None = auto)

        Returns:
            dict speaker_id → liste de SpeakerSegment
        """
        if self._pipeline is None:
            self.setup()

        self._log(f"Diarisation: {audio_path}")
        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers

        diarization = self._pipeline(str(audio_path), **kwargs)

        segments: Dict[str, List[SpeakerSegment]] = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            seg = SpeakerSegment(speaker, turn.start, turn.end)
            if speaker not in segments:
                segments[speaker] = []
            segments[speaker].append(seg)

        for spk, segs in segments.items():
            total = sum(s.duration for s in segs)
            self._log(f"  Speaker {spk}: {len(segs)} segments, {total:.1f}s total")

        return segments

    # ── Mapping speaker → avatar ──────────────────────────────────────────────

    def map_speakers_to_avatars(
        self,
        speaker_segments: Dict[str, List[SpeakerSegment]],
        avatar_names: List[str],
        production_plan: Optional[dict] = None,
    ) -> Dict[str, str]:
        """
        Mappe speaker_id → avatar_name.

        Priorité:
        1. PRODUCTION_PLAN.JSON['speaker_avatar_mapping'] si présent
        2. Tri par durée totale de parole (speaker le plus présent → avatar 0)

        Args:
            speaker_segments: sortie de diarize()
            avatar_names: liste ordonnée des noms d'avatars
            production_plan: dict optionnel du PRODUCTION_PLAN.JSON

        Returns:
            dict speaker_id → avatar_name
        """
        # Mapping explicite depuis le plan de production
        if production_plan:
            explicit = production_plan.get("speaker_avatar_mapping", {})
            if explicit:
                self._log(f"Mapping speakers explicite: {explicit}")
                return explicit

        # Tri par durée totale de parole décroissante
        speaker_durations = {
            spk: sum(s.duration for s in segs)
            for spk, segs in speaker_segments.items()
        }
        ranked = sorted(speaker_durations.keys(), key=lambda s: -speaker_durations[s])

        mapping = {}
        for i, spk in enumerate(ranked):
            if i < len(avatar_names):
                mapping[spk] = avatar_names[i]
                self._log(
                    f"  Speaker {spk} ({speaker_durations[spk]:.1f}s) → {avatar_names[i]}"
                )

        return mapping

    # ── Génération pistes audio ───────────────────────────────────────────────

    def generate_avatar_tracks(
        self,
        audio_path: str,
        speaker_mapping: Dict[str, str],
        speaker_segments: Dict[str, List[SpeakerSegment]],
        output_dir: str,
    ) -> Dict[str, str]:
        """
        Génère un WAV par avatar (silence hors segments de parole).

        Args:
            audio_path: audio_original.wav (source)
            speaker_mapping: speaker_id → avatar_name
            speaker_segments: dict speaker_id → List[SpeakerSegment]
            output_dir: dossier de sortie

        Returns:
            dict avatar_name → chemin WAV propre
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_data, sample_rate = self._load_audio(audio_path)
        result: Dict[str, str] = {}

        for speaker_id, avatar_name in speaker_mapping.items():
            if speaker_id not in speaker_segments:
                self._log(f"  {speaker_id} → aucun segment, skip")
                continue

            segs = speaker_segments[speaker_id]

            # Créer un buffer silence de même durée que l'original
            silent = np.zeros_like(audio_data)

            # Remplir avec la parole de ce speaker
            for seg in segs:
                start_sample = int(seg.start * sample_rate)
                end_sample = int(seg.end * sample_rate)
                end_sample = min(end_sample, len(audio_data))
                start_sample = min(start_sample, len(audio_data))
                if start_sample < end_sample:
                    silent[start_sample:end_sample] = audio_data[start_sample:end_sample]

            # Sauvegarder
            safe_name = avatar_name.replace("/", "_").replace("\\", "_")
            out_path = str(output_dir / f"{safe_name}_voice.wav")
            self._save_audio(silent, sample_rate, out_path)

            result[avatar_name] = out_path
            total_speech = sum(s.duration for s in segs)
            self._log(f"  Piste {avatar_name}: {total_speech:.1f}s de parole → {out_path}")

        return result

    # ── I/O audio ────────────────────────────────────────────────────────────

    def _load_audio(self, path: str) -> Tuple[np.ndarray, int]:
        """Charge un fichier audio en numpy array (mono float32)."""
        if not NP_AVAILABLE:
            raise ImportError("numpy requis pour le traitement audio")

        if SF_AVAILABLE:
            data, sr = sf.read(str(path), dtype="float32", always_2d=False)
            if data.ndim == 2:
                data = data.mean(axis=1)
            return data, sr

        # Fallback: wave stdlib (WAV PCM uniquement)
        with wave.open(str(path), "rb") as wf:
            sr = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Format WAV non supporté: {sampwidth} bytes/sample")

        if n_channels == 2:
            data = data[::2] * 0.5 + data[1::2] * 0.5

        return data, sr

    def _save_audio(self, data: np.ndarray, sample_rate: int, path: str):
        """Sauvegarde numpy array en WAV PCM 16-bit."""
        if SF_AVAILABLE:
            sf.write(str(path), data, sample_rate, subtype="PCM_16")
            return

        pcm = (data * 32767).clip(-32768, 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

    # ── Rapport ───────────────────────────────────────────────────────────────

    def create_report(
        self,
        speaker_segments: Dict[str, List[SpeakerSegment]],
        speaker_mapping: Dict[str, str],
        avatar_tracks: Dict[str, str],
    ) -> dict:
        return {
            "n_speakers": len(speaker_segments),
            "speaker_mapping": speaker_mapping,
            "avatar_tracks": avatar_tracks,
            "segments": {
                spk: [s.to_dict() for s in segs]
                for spk, segs in speaker_segments.items()
            },
        }

    def _log(self, msg: str):
        if self.verbose:
            print(f"[PYANNOTE] {msg}")


# ── CLI standalone ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PyannoteDialrizer CLI")
    parser.add_argument("--audio", required=True, help="audio_original.wav")
    parser.add_argument("--output-dir", required=True, help="Dossier output pistes")
    parser.add_argument("--avatars", nargs="+", default=["avatar-ferrus-0", "avatar-ferrus-1"])
    parser.add_argument("--n-speakers", type=int, default=None)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--report", default=None, help="Chemin rapport JSON")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    diarizer = PyannoteDiarizer(
        hf_token=args.hf_token,
        device=args.device,
        verbose=True,
    )
    try:
        segments = diarizer.diarize(args.audio, num_speakers=args.n_speakers)
        mapping = diarizer.map_speakers_to_avatars(segments, args.avatars)
        tracks = diarizer.generate_avatar_tracks(
            args.audio, mapping, segments, args.output_dir
        )
        report = diarizer.create_report(segments, mapping, tracks)

        if args.report:
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Rapport: {args.report}")

        print(f"\n[OK] {len(segments)} speakers | {len(tracks)} pistes générées")
    finally:
        diarizer.teardown()


# Alias backward-compat (SENTINEL FIX: typo PyannoteDialrizer → PyannoteDiarizer)
PyannoteDialrizer = PyannoteDiarizer
