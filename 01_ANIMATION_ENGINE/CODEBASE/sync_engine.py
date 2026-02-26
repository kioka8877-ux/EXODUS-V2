"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SYNC ENGINE V2 — Timecode / FBX Synchronization                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de synchronisation timecodes JSON → frames FBX.                     ║
║  ZÉRO vidéo — uniquement maths de timecodes et alignment FBX.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import List, Tuple, Dict
import json


class SyncEngine:
    """Moteur de synchronisation timecodes/FBX V2."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def log(self, msg: str):
        if self.verbose:
            print(f"[SYNC] {msg}")

    def timecodes_to_frames(self, segments: list, fps: int) -> list:
        """Convertit les time_start/time_end/apex_time en numéros de frames."""
        result = []
        for seg in segments:
            result.append({
                **seg,
                "frame_start": int(round(seg["time_start"] * fps)),
                "frame_end": int(round(seg["time_end"] * fps)),
                "frame_apex": int(round(seg["apex_time"] * fps)),
            })
        return result

    def align_to_fbx(self, segments: list, fbx_frame_count: int, offset: int = 0) -> list:
        """Clampe les segments aux bornes du FBX."""
        result = []
        for seg in segments:
            fs = seg["frame_start"] + offset
            fe = seg["frame_end"] + offset
            fa = seg["frame_apex"] + offset

            fs = max(0, min(fs, fbx_frame_count - 1))
            fe = max(0, min(fe, fbx_frame_count - 1))
            fa = max(fs, min(fa, fe))

            if fs >= fe:
                self.log(f"Segment ignoré (clamped hors bornes): frames {fs}-{fe}")
                continue

            result.append({
                **seg,
                "frame_start": fs,
                "frame_end": fe,
                "frame_apex": fa,
            })
        return result

    def validate_timeline(self, segments: list) -> Tuple[bool, List[str]]:
        """Vérifie que les timecodes sont croissants, pas de chevauchement,
        apex dans les bornes."""
        errors: List[str] = []

        for i, seg in enumerate(segments):
            ts = seg.get("time_start", 0)
            te = seg.get("time_end", 0)
            apex = seg.get("apex_time", 0)

            if te <= ts:
                errors.append(f"Segment {i}: time_end ({te}) <= time_start ({ts})")

            if apex < ts or apex > te:
                errors.append(
                    f"Segment {i}: apex_time ({apex}) hors bornes [{ts}, {te}]"
                )

            if i > 0:
                prev_end = segments[i - 1].get("time_end", 0)
                if ts < prev_end:
                    errors.append(
                        f"Segment {i}: time_start ({ts}) chevauche segment {i-1} "
                        f"(time_end={prev_end})"
                    )

        return (len(errors) == 0, errors)

    def create_sync_report(
        self,
        body_path: str,
        facial_json_path: str,
        offset: int,
        fbx_frame_count: int,
        segment_count: int,
    ) -> Dict:
        """Génère un rapport de synchronisation V2."""
        return {
            "inputs": {
                "body_fbx": body_path,
                "facial_json": facial_json_path,
            },
            "sync": {
                "offset_frames": offset,
                "fbx_frame_count": fbx_frame_count,
                "segment_count": segment_count,
            },
            "validation": {
                "status": "OK",
            },
        }


def timecodes_to_frames(segments: list, fps: int) -> list:
    """Fonction utilitaire. Wrapper autour de SyncEngine."""
    return SyncEngine().timecodes_to_frames(segments, fps)


def validate_timeline(segments: list) -> Tuple[bool, List[str]]:
    """Fonction utilitaire de validation."""
    return SyncEngine().validate_timeline(segments)


if __name__ == "__main__":
    engine = SyncEngine(verbose=True)

    print("\n=== Test Sync Engine V2 ===")

    test_segments = [
        {"time_start": 0.0, "time_end": 2.5, "apex_time": 1.2, "expression": "determined"},
        {"time_start": 2.5, "time_end": 5.0, "apex_time": 3.8, "expression": "joy"},
        {"time_start": 5.0, "time_end": 7.0, "apex_time": 6.0, "expression": "sadness"},
    ]

    ok, errs = engine.validate_timeline(test_segments)
    print(f"Validation timeline: {'OK' if ok else 'ERREURS'}")
    for e in errs:
        print(f"  {e}")

    framed = engine.timecodes_to_frames(test_segments, fps=30)
    for seg in framed:
        print(f"  {seg['expression']}: frame {seg['frame_start']} -> {seg['frame_end']} (apex {seg['frame_apex']})")

    aligned = engine.align_to_fbx(framed, fbx_frame_count=180, offset=0)
    print(f"\nAligned to FBX (180 frames):")
    for seg in aligned:
        print(f"  {seg['expression']}: frame {seg['frame_start']} -> {seg['frame_end']} (apex {seg['frame_apex']})")

    report = engine.create_sync_report(
        body_path="test.fbx",
        facial_json_path="facial_animation.json",
        offset=0,
        fbx_frame_count=180,
        segment_count=len(test_segments),
    )
    print(f"\nRapport: {json.dumps(report, indent=2)}")
