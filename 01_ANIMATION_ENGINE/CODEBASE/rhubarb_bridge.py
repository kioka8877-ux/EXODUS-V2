"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        RHUBARB BRIDGE — Audio → Lip-Sync NLA Data                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Pont entre Rhubarb CLI et le pipeline U01 Blender.                        ║
║  Exécute Rhubarb, parse le JSON, convertit en segments NLA avec les        ║
║  valeurs ARKit via LIP_SYNC_VISEMES de expression_schema.py.               ║
║  ZÉRO dépendance ML. Pure Python stdlib + Rhubarb binaire externe.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from expression_schema import ExpressionSchema, VALID_VISEMES


class RhubarbBridge:
    """Pont Rhubarb → NLA lip-sync data pour Blender."""

    def __init__(self, rhubarb_path: str = None, schema: ExpressionSchema = None):
        self.rhubarb_path = rhubarb_path
        self.schema = schema or ExpressionSchema()

    def run_rhubarb(self, audio_path: str, dialogue_path: str = None) -> dict:
        """Exécute Rhubarb CLI et retourne le JSON de mouth cues.

        Commande : rhubarb <audio> -f json [-d <dialogue.txt>] --machineReadable

        Si rhubarb_path est None, cherche 'rhubarb' dans PATH.
        Si Rhubarb n'est pas installé, raise RuntimeError avec message clair.
        """
        rhubarb_bin = self.rhubarb_path or "rhubarb"

        if self.rhubarb_path and not Path(self.rhubarb_path).exists():
            raise RuntimeError(
                "Rhubarb non trouvé. Installez rhubarb-lip-sync et placez le binaire "
                "dans EXODUS_AI_MODELS/rhubarb/ ou dans le PATH."
            )

        audio = Path(audio_path)
        if not audio.exists():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        cmd = [rhubarb_bin, str(audio), "-f", "json", "--machineReadable"]

        if dialogue_path:
            dp = Path(dialogue_path)
            if dp.exists():
                cmd.extend(["-d", str(dp)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Rhubarb non trouvé. Installez rhubarb-lip-sync et placez le binaire "
                "dans EXODUS_AI_MODELS/rhubarb/ ou dans le PATH."
            )

        if result.returncode != 0:
            raise RuntimeError(f"Rhubarb a échoué (code {result.returncode}): {result.stderr}")

        return json.loads(result.stdout)

    def parse_mouth_cues(self, rhubarb_output: dict) -> list:
        """Parse le JSON Rhubarb en liste de segments.

        Retourne :
        [
            {"time_start": 0.0, "time_end": 0.05, "viseme": "X"},
            {"time_start": 0.05, "time_end": 0.27, "viseme": "D"},
            ...
        ]
        """
        raw_cues = rhubarb_output.get("mouthCues", [])
        segments = []

        for cue in raw_cues:
            viseme = cue.get("value", "X")
            if viseme not in VALID_VISEMES:
                viseme = "X"

            segments.append({
                "time_start": float(cue["start"]),
                "time_end": float(cue["end"]),
                "viseme": viseme,
            })

        return segments

    def translate_to_arkit(self, mouth_cues: list) -> list:
        """Convertit les visèmes Rhubarb en MOUTH_KEYS ARKit via schema.get_viseme().

        Retourne :
        [
            {
                "time_start": 0.0,
                "time_end": 0.05,
                "values": {28 MOUTH_KEYS values from LIP_SYNC_VISEMES["X"]}
            },
            ...
        ]
        """
        arkit_segments = []

        for cue in mouth_cues:
            values = self.schema.get_viseme(cue["viseme"])
            arkit_segments.append({
                "time_start": cue["time_start"],
                "time_end": cue["time_end"],
                "values": values,
            })

        return arkit_segments

    def generate_lip_sync_data(self, audio_path: str, dialogue_path: str = None, fps: int = 30) -> dict:
        """Point d'entrée principal. Audio → lip-sync NLA data.

        Retourne :
        {
            "fps": 30,
            "lip_sync_segments": [
                {
                    "frame_start": 0,
                    "frame_end": 2,
                    "values": {28 MOUTH_KEYS}
                },
                ...
            ],
            "metadata": {
                "audio_file": "...",
                "duration": 5.32,
                "total_cues": 42
            }
        }
        """
        rhubarb_output = self.run_rhubarb(audio_path, dialogue_path)

        mouth_cues = self.parse_mouth_cues(rhubarb_output)
        arkit_segments = self.translate_to_arkit(mouth_cues)

        lip_sync_segments = []
        for seg in arkit_segments:
            frame_start = int(round(seg["time_start"] * fps))
            frame_end = int(round(seg["time_end"] * fps))
            lip_sync_segments.append({
                "frame_start": frame_start,
                "frame_end": frame_end,
                "values": seg["values"],
            })

        metadata = rhubarb_output.get("metadata", {})
        duration = metadata.get("duration", 0.0)
        audio_file = metadata.get("soundFile", str(audio_path))

        return {
            "fps": fps,
            "lip_sync_segments": lip_sync_segments,
            "metadata": {
                "audio_file": audio_file,
                "duration": duration,
                "total_cues": len(lip_sync_segments),
            },
        }

    @staticmethod
    def load_lip_sync_json(json_path: str) -> dict:
        """Charge un fichier lip_sync_data.json pré-généré."""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    print("=" * 60)
    print("  RHUBARB BRIDGE — Test conversion visème → ARKit")
    print("=" * 60)

    SAMPLE_RHUBARB_OUTPUT = {
        "metadata": {
            "soundFile": "test_dialogue.wav",
            "duration": 2.50
        },
        "mouthCues": [
            {"start": 0.00, "end": 0.05, "value": "X"},
            {"start": 0.05, "end": 0.27, "value": "D"},
            {"start": 0.27, "end": 0.31, "value": "C"},
            {"start": 0.31, "end": 0.50, "value": "B"},
            {"start": 0.50, "end": 0.72, "value": "E"},
            {"start": 0.72, "end": 0.85, "value": "F"},
            {"start": 0.85, "end": 1.10, "value": "A"},
            {"start": 1.10, "end": 1.35, "value": "G"},
            {"start": 1.35, "end": 1.60, "value": "H"},
            {"start": 1.60, "end": 2.00, "value": "C"},
            {"start": 2.00, "end": 2.50, "value": "X"},
        ]
    }

    bridge = RhubarbBridge()

    print("\n--- 1. Parse mouth cues ---")
    cues = bridge.parse_mouth_cues(SAMPLE_RHUBARB_OUTPUT)
    print(f"Cues parsés: {len(cues)}")
    for c in cues[:3]:
        print(f"  {c['time_start']:.2f}-{c['time_end']:.2f} → visème {c['viseme']}")
    print(f"  ... ({len(cues)} total)")

    print("\n--- 2. Translate to ARKit ---")
    arkit = bridge.translate_to_arkit(cues)
    print(f"Segments ARKit: {len(arkit)}")
    for seg in arkit[:3]:
        active = {k: v for k, v in seg["values"].items() if v > 0.0}
        print(f"  {seg['time_start']:.2f}-{seg['time_end']:.2f} → {len(active)} keys actives")
        for k, v in sorted(active.items()):
            print(f"    {k:30s} = {v:.2f}")

    print("\n--- 3. Full pipeline (simulated) ---")
    fps = 30
    lip_sync_segments = []
    for seg in arkit:
        fs = int(round(seg["time_start"] * fps))
        fe = int(round(seg["time_end"] * fps))
        lip_sync_segments.append({
            "frame_start": fs,
            "frame_end": fe,
            "values": seg["values"],
        })

    lip_sync_data = {
        "fps": fps,
        "lip_sync_segments": lip_sync_segments,
        "metadata": {
            "audio_file": SAMPLE_RHUBARB_OUTPUT["metadata"]["soundFile"],
            "duration": SAMPLE_RHUBARB_OUTPUT["metadata"]["duration"],
            "total_cues": len(lip_sync_segments),
        },
    }

    print(f"FPS: {lip_sync_data['fps']}")
    print(f"Total segments: {lip_sync_data['metadata']['total_cues']}")
    print(f"Duration: {lip_sync_data['metadata']['duration']}s")
    print(f"Audio: {lip_sync_data['metadata']['audio_file']}")

    print("\nSegments NLA (frames):")
    for seg in lip_sync_data["lip_sync_segments"]:
        active = {k: v for k, v in seg["values"].items() if v > 0.0}
        print(f"  frames {seg['frame_start']:4d}-{seg['frame_end']:4d} → {len(active)} MOUTH_KEYS actives")

    print("\n--- 4. Visème coverage ---")
    schema = bridge.schema
    for v_id in VALID_VISEMES:
        vals = schema.get_viseme(v_id)
        active = {k: v for k, v in vals.items() if v > 0.0}
        print(f"  Visème {v_id}: {len(active):2d} keys actives")

    print("\n" + "=" * 60)
    print("  TEST RHUBARB BRIDGE COMPLET")
    print("=" * 60)
