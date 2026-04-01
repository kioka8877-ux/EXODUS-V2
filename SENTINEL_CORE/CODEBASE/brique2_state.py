#!/usr/bin/env python3
"""
SENTINEL B2 — SIGNATURE D'ETAT (LE CORPS)
Mesure l'etat reel d'un fichier .blend ou d'un dossier output apres execution d'une fregate.

Logique adversariale : chercher les echecs, pas confirmer le succes.
Inspire du Verification Agent : "Le premier 80% est facile. Ta valeur est dans les 20% restants."

Usage (standalone) :
    python brique2_state.py --fregate U03 --blend /path/to/scene.blend --output /path/to/STATE_SIG.json

Usage (depuis sentinel_core) :
    from brique2_state import StateSignature
    sig = StateSignature("U03")
    result = sig.check_blend("/path/to/scene.blend")
    sig.save(result, "/path/STATE_SIG.json")
"""
from __future__ import annotations

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ─── Constantes ──────────────────────────────────────────────────────────────

VERSION = "1.0.0"
TIMEOUT_SEC = 30

# Seuils par fregate — ce qui est acceptable
THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "U03": {
        "vertices_min": 10000,
        "energy_min": 1.0,
        "luminance_range": None,         # pas applicable sur .blend
        "camera_required": True,
        "gpu_required": True,
        "scene_type_not_unknown": True,
    },
    "U04": {
        "vertices_min": None,
        "energy_min": None,
        "luminance_range": (50, 200),
        "camera_required": True,
        "gpu_required": True,
        "scene_type_not_unknown": False,
    },
    "U00": {
        "vertices_min": None,
        "energy_min": None,
        "luminance_range": None,
        "camera_required": False,
        "gpu_required": False,
        "scene_type_not_unknown": False,
    },
    "U01": {
        "vertices_min": None,
        "energy_min": None,
        "luminance_range": None,
        "camera_required": False,
        "gpu_required": False,
        "scene_type_not_unknown": False,
    },
    "U02": {
        "vertices_min": None,
        "energy_min": None,
        "luminance_range": None,
        "camera_required": False,
        "gpu_required": False,
        "scene_type_not_unknown": False,
    },
    "U05": {
        "vertices_min": None,
        "energy_min": None,
        "luminance_range": (30, 220),
        "camera_required": False,
        "gpu_required": False,
        "scene_type_not_unknown": False,
    },
    "U06": {
        "vertices_min": None,
        "energy_min": None,
        "luminance_range": None,
        "camera_required": False,
        "gpu_required": False,
        "scene_type_not_unknown": False,
    },
}


# ─── Fonctions utilitaires ────────────────────────────────────────────────────

def _check_result(value: Any, expected: Any, label: str) -> Dict[str, Any]:
    """Retourne un check standardise avec statut PASS/FAIL/WARN."""
    if expected is None:
        return {"value": value, "expected": "N/A", "status": "SKIP"}
    
    if isinstance(expected, tuple) and len(expected) == 2:
        # Range check
        lo, hi = expected
        passed = (value is not None) and (lo <= value <= hi)
        return {
            "value": value,
            "expected": f"[{lo}, {hi}]",
            "status": "PASS" if passed else "FAIL",
        }
    elif isinstance(expected, bool):
        passed = (value == expected)
        return {
            "value": value,
            "expected": expected,
            "status": "PASS" if passed else "FAIL",
        }
    elif isinstance(expected, (int, float)):
        passed = (value is not None) and (value >= expected)
        return {
            "value": value,
            "expected": f">= {expected}",
            "status": "PASS" if passed else "FAIL",
        }
    return {"value": value, "expected": str(expected), "status": "UNKNOWN"}


def _overall_verdict(checks: Dict[str, Dict]) -> str:
    """FAIL si un check critique echoue. WARN si optionnel."""
    statuses = [c.get("status") for c in checks.values()]
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _elapsed(start: float) -> float:
    return round(time.time() - start, 3)


# ─── Classe principale ────────────────────────────────────────────────────────

class StateSignature:
    """
    Signature d'etat SENTINEL B2.
    Mesure les parametres critiques d'une fregate et retourne STATE_SIG.json.
    """

    def __init__(self, fregate: str):
        if fregate not in THRESHOLDS:
            raise ValueError(f"Fregate inconnue : {fregate}. Options : {list(THRESHOLDS)}")
        self.fregate = fregate
        self.thresholds = THRESHOLDS[fregate]

    # ── Checks .blend (Blender API) ──────────────────────────────────────────

    def check_blend(self, blend_path: str) -> Dict[str, Any]:
        """
        Mesure l'etat d'un fichier .blend via Blender API.
        Doit etre appele DANS un contexte Blender (headless ou notebook).
        """
        start = time.time()
        blend_path = Path(blend_path)

        if not blend_path.exists():
            return self._error_result(f"Fichier introuvable : {blend_path}", _elapsed(start))

        try:
            import bpy  # type: ignore
        except ImportError:
            return self._error_result("bpy non disponible — executer dans Blender", _elapsed(start))

        try:
            bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        except Exception as e:
            return self._error_result(f"Impossible d'ouvrir le fichier : {e}", _elapsed(start))

        checks = {}
        thr = self.thresholds

        # Check 1 — Vertices
        if thr["vertices_min"] is not None:
            vertices = self._count_displacement_vertices()
            checks["vertices"] = _check_result(vertices, thr["vertices_min"], "vertices")

        # Check 2 — Camera
        if thr["camera_required"]:
            cam_present, cam_pos_ok = self._check_camera()
            checks["camera_present"] = _check_result(cam_present, True, "camera_present")
            checks["camera_position"] = _check_result(cam_pos_ok, True, "camera_position")

        # Check 3 — GPU
        if thr["gpu_required"]:
            gpu_active = self._check_gpu()
            checks["gpu_active"] = _check_result(gpu_active, True, "gpu_active")

        # Check 4 — Energie lumiere
        if thr["energy_min"] is not None:
            max_energy = self._check_light_energy()
            checks["energy_max"] = _check_result(max_energy, thr["energy_min"], "energy_max")

        # Check 5 — Scene type
        if thr["scene_type_not_unknown"]:
            scene_type = self._check_scene_type()
            not_unknown = (scene_type != "unknown" and scene_type is not None)
            checks["scene_type"] = _check_result(not_unknown, True, "scene_type_not_unknown")
            checks["scene_type"]["raw_value"] = scene_type

        verdict = _overall_verdict(checks)
        elapsed = _elapsed(start)

        return {
            "version": VERSION,
            "fregate": self.fregate,
            "blend_file": str(blend_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": elapsed,
            "verdict": verdict,
            "checks": checks,
            "timeout_exceeded": elapsed > TIMEOUT_SEC,
        }

    # ── Checks output frames (U04 / U05) ────────────────────────────────────

    def check_frames(self, frames_dir: str, pattern: str = "*.png") -> Dict[str, Any]:
        """
        Mesure l'etat d'un dossier de frames rendues.
        Pas besoin de Blender — pur Python + numpy optionnel.
        """
        start = time.time()
        frames_dir = Path(frames_dir)

        if not frames_dir.exists():
            return self._error_result(f"Dossier introuvable : {frames_dir}", _elapsed(start))

        frames = sorted(frames_dir.glob(pattern))
        checks = {}
        thr = self.thresholds

        # Check 1 — Nombre de frames
        checks["frames_count"] = {
            "value": len(frames),
            "expected": ">= 1",
            "status": "PASS" if len(frames) >= 1 else "FAIL",
        }

        # Check 2 — Taille minimale par frame
        if frames:
            sizes_kb = [f.stat().st_size / 1024 for f in frames]
            min_size = round(min(sizes_kb), 1)
            checks["frame_size_min_kb"] = _check_result(min_size, 50.0, "frame_size_min_kb")

        # Check 3 — Luminance moyenne (si numpy disponible)
        if thr.get("luminance_range") and frames:
            luminance = self._sample_luminance(frames[:3])  # Sample sur 3 frames max
            if luminance is not None:
                checks["luminance_mean"] = _check_result(
                    luminance, thr["luminance_range"], "luminance_mean"
                )

        # Check 4 — Continuite de sequence (pas de trous)
        if frames:
            gaps = self._detect_sequence_gaps(frames)
            checks["sequence_gaps"] = {
                "value": gaps,
                "expected": 0,
                "status": "PASS" if gaps == 0 else "WARN",
            }

        verdict = _overall_verdict(checks)
        elapsed = _elapsed(start)

        return {
            "version": VERSION,
            "fregate": self.fregate,
            "frames_dir": str(frames_dir),
            "frames_found": len(frames),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": elapsed,
            "verdict": verdict,
            "checks": checks,
            "timeout_exceeded": elapsed > TIMEOUT_SEC,
        }

    # ── Helpers internes ─────────────────────────────────────────────────────

    def _count_displacement_vertices(self) -> Optional[int]:
        """Compte les vertices evalues du displacement_mesh."""
        try:
            import bpy
            bpy.context.view_layer.update()
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.update()

            for obj in bpy.data.objects:
                if "displacement" in obj.name.lower() and obj.type == "MESH":
                    ev = obj.evaluated_get(depsgraph)
                    mesh = ev.to_mesh()
                    try:
                        return len(mesh.vertices)
                    finally:
                        ev.to_mesh_clear()
            return 0
        except Exception:
            return None

    def _check_camera(self) -> Tuple[bool, bool]:
        """Retourne (camera_presente, position_non_nulle)."""
        try:
            import bpy
            for obj in bpy.data.objects:
                if obj.type == "CAMERA" and "camera_main" in obj.name.lower():
                    loc = obj.location
                    pos_ok = not (loc.x == 0.0 and loc.y == 0.0 and loc.z == 0.0)
                    return True, pos_ok
            return False, False
        except Exception:
            return False, False

    def _check_gpu(self) -> bool:
        """Verifie que le rendu est configure sur GPU."""
        try:
            import bpy
            scene = bpy.context.scene
            if scene.render.engine != "CYCLES":
                return False
            prefs = bpy.context.preferences.addons.get("cycles")
            if prefs:
                cprefs = prefs.preferences
                return getattr(cprefs, "compute_device_type", "NONE") != "NONE"
            return False
        except Exception:
            return False

    def _check_light_energy(self) -> Optional[float]:
        """Retourne l'energie maximale des lumieres dans la scene."""
        try:
            import bpy
            energies = []
            for obj in bpy.data.objects:
                if obj.type == "LIGHT":
                    e = getattr(obj.data, "energy", None)
                    if e is not None:
                        energies.append(e)
            return max(energies) if energies else 0.0
        except Exception:
            return None

    def _check_scene_type(self) -> Optional[str]:
        """Lit le scene_type depuis assembler_results.json si disponible."""
        try:
            import bpy
            blend_dir = Path(bpy.data.filepath).parent
            assembler_path = blend_dir / "assembler_results.json"
            if assembler_path.exists():
                with open(assembler_path) as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    return data[0].get("scene_type", "unknown")
                if isinstance(data, dict):
                    return data.get("scene_type", "unknown")
            return "unknown"
        except Exception:
            return None

    def _sample_luminance(self, frames: List[Path]) -> Optional[float]:
        """Luminance moyenne sur un echantillon de frames."""
        try:
            import numpy as np
            from PIL import Image  # type: ignore
            lumas = []
            for f in frames:
                img = np.array(Image.open(f).convert("L"), dtype=float)
                lumas.append(img.mean())
            return round(sum(lumas) / len(lumas), 2) if lumas else None
        except ImportError:
            # Fallback sans numpy/PIL
            return None
        except Exception:
            return None

    def _detect_sequence_gaps(self, frames: List[Path]) -> int:
        """Detecte les trous dans une sequence numerotee de frames."""
        import re
        numbers = []
        for f in frames:
            m = re.search(r"(\d+)", f.stem)
            if m:
                numbers.append(int(m.group(1)))
        if len(numbers) < 2:
            return 0
        numbers.sort()
        gaps = sum(1 for i in range(1, len(numbers)) if numbers[i] - numbers[i-1] > 1)
        return gaps

    def _error_result(self, msg: str, elapsed: float) -> Dict[str, Any]:
        return {
            "version": VERSION,
            "fregate": self.fregate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": elapsed,
            "verdict": "ERROR",
            "error": msg,
            "checks": {},
        }

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save(self, result: Dict[str, Any], output_path: str) -> None:
        """Sauvegarde STATE_SIG.json."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def print_report(self, result: Dict[str, Any]) -> None:
        """Affichage console lisible."""
        verdict = result.get("verdict", "?")
        fregate = result.get("fregate", "?")
        elapsed = result.get("elapsed_sec", 0)
        print(f"\n{'='*60}")
        print(f"  SENTINEL B2 — {fregate} — {verdict} ({elapsed}s)")
        print(f"{'='*60}")
        for name, check in result.get("checks", {}).items():
            status = check.get("status", "?")
            value = check.get("value", "?")
            expected = check.get("expected", "?")
            icon = "OK" if status == "PASS" else ("--" if status == "SKIP" else "!!")
            print(f"  [{icon}] {name:<30} val={value}  seuil={expected}")
        print(f"{'='*60}\n")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B2 — Signature d'Etat")
    p.add_argument("--fregate", required=True, choices=list(THRESHOLDS), help="ID de la fregate")
    p.add_argument("--blend", help="Chemin vers le fichier .blend a auditer")
    p.add_argument("--frames", help="Chemin vers le dossier de frames a auditer")
    p.add_argument("--output", default="STATE_SIG.json", help="Chemin du rapport JSON de sortie")
    p.add_argument("--quiet", action="store_true", help="Pas d'affichage console")
    return p.parse_args(_argv_after_dd() if "--" in sys.argv else sys.argv[1:])


def _argv_after_dd() -> List[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def main() -> int:
    args = _parse_args()
    sig = StateSignature(args.fregate)

    if args.blend:
        result = sig.check_blend(args.blend)
    elif args.frames:
        result = sig.check_frames(args.frames)
    else:
        print("ERREUR : --blend ou --frames requis", file=sys.stderr)
        return 1

    sig.save(result, args.output)
    if not args.quiet:
        sig.print_report(result)

    return 0 if result.get("verdict") in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
