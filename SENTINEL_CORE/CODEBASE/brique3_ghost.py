#!/usr/bin/env python3
"""
SENTINEL B3 — L'OEIL (GHOST RENDERER)
Rendu rapide 128x128 en Workbench pour detection visuelle de frames noires.

Objectif : detecter en <3 secondes si une scene va produire un rendu noir,
avant de lancer le vrai rendu Cycles (qui peut prendre 30 min).

Principe :
    Workbench = moteur de visualisation rapide (pas de calcul lumiere)
    128x128   = resolution minimale suffisante pour detecter le noir
    <3 sec    = si ca depasse, quelque chose bloque

Usage (headless Blender) :
    blender --background scene.blend --python brique3_ghost.py -- --output /path/ghost.png

Usage (depuis sentinel_core) :
    from brique3_ghost import GhostRenderer
    ghost = GhostRenderer()
    result = ghost.render(blend_path="scene.blend", output_path="ghost.png")
    print(result["verdict"])  # VISIBLE | BLACK | DARK | ERROR
"""
from __future__ import annotations

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

VERSION = "1.0.0"
GHOST_RESOLUTION = 128
TIMEOUT_SEC = 10
BLACK_THRESHOLD = 15.0    # Luminance moyenne < 15 = frame noire
DARK_THRESHOLD = 40.0     # Luminance moyenne < 40 = frame tres sombre (warning)


# ─── Classe principale ────────────────────────────────────────────────────────

class GhostRenderer:
    """
    SENTINEL B3 — Ghost Renderer.
    Rendu Workbench 128x128 pour detection rapide de frames noires.
    """

    def render(self, blend_path: str, output_path: str = "ghost_frame.png") -> Dict[str, Any]:
        """
        Rend une frame ghost 128x128 en Workbench.
        Doit etre appele dans un contexte Blender headless.

        Retourne :
        {
            "verdict": "VISIBLE" | "BLACK" | "DARK" | "ERROR",
            "luminance_mean": float,
            "elapsed_sec": float,
            "output_path": str,
        }
        """
        start = time.time()
        output_path = Path(output_path)

        try:
            import bpy
        except ImportError:
            return self._error("bpy non disponible", start)

        # Charger le blend si pas deja charge
        if blend_path and Path(blend_path).exists():
            try:
                if bpy.data.filepath != str(Path(blend_path).resolve()):
                    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
            except Exception as e:
                return self._error(f"Impossible ouvrir blend : {e}", start)

        scene = bpy.context.scene

        # Sauvegarder parametres originaux
        orig_engine = scene.render.engine
        orig_x = scene.render.resolution_x
        orig_y = scene.render.resolution_y
        orig_pct = scene.render.resolution_percentage
        orig_filepath = scene.render.filepath
        orig_format = scene.render.image_settings.file_format

        try:
            # Configurer Workbench rapide
            scene.render.engine = "BLENDER_WORKBENCH"
            scene.render.resolution_x = GHOST_RESOLUTION
            scene.render.resolution_y = GHOST_RESOLUTION
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(output_path.with_suffix(""))
            scene.render.image_settings.file_format = "PNG"

            # Parametres Workbench pour visibilite maximale
            if hasattr(scene, "display"):
                scene.display.shading.light = "STUDIO"
                scene.display.shading.color_type = "MATERIAL"

            # Rendu
            bpy.ops.render.render(write_still=True)
            elapsed = round(time.time() - start, 3)

            # Analyser le resultat
            if not output_path.exists():
                # Blender ajoute parfois l'extension
                candidates = list(output_path.parent.glob(output_path.stem + "*"))
                if candidates:
                    output_path = candidates[0]
                else:
                    return self._error("Fichier ghost introuvable apres rendu", start)

            luminance = self._compute_luminance(output_path)
            verdict = self._classify(luminance)

            return {
                "version": VERSION,
                "verdict": verdict,
                "luminance_mean": luminance,
                "elapsed_sec": elapsed,
                "output_path": str(output_path),
                "timeout_exceeded": elapsed > TIMEOUT_SEC,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            return self._error(f"Rendu ghost echoue : {e}", start)

        finally:
            # Restaurer parametres originaux
            try:
                scene.render.engine = orig_engine
                scene.render.resolution_x = orig_x
                scene.render.resolution_y = orig_y
                scene.render.resolution_percentage = orig_pct
                scene.render.filepath = orig_filepath
                scene.render.image_settings.file_format = orig_format
            except Exception:
                pass

    def analyze_existing(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse une image existante sans lancer de rendu.
        Utile pour analyser les frames U04 deja rendues.
        """
        start = time.time()
        p = Path(image_path)

        if not p.exists():
            return self._error(f"Image introuvable : {image_path}", start)

        luminance = self._compute_luminance(p)
        verdict = self._classify(luminance)

        return {
            "version": VERSION,
            "verdict": verdict,
            "luminance_mean": luminance,
            "elapsed_sec": round(time.time() - start, 3),
            "output_path": str(p),
            "timeout_exceeded": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def analyze_folder(self, frames_dir: str, pattern: str = "*.png", sample_size: int = 3) -> Dict[str, Any]:
        """
        Analyse un echantillon de frames d'un dossier.
        Retourne le verdict global + stats par frame.
        """
        start = time.time()
        frames_dir = Path(frames_dir)

        if not frames_dir.exists():
            return self._error(f"Dossier introuvable : {frames_dir}", start)

        frames = sorted(frames_dir.glob(pattern))
        if not frames:
            return self._error(f"Aucune frame {pattern} dans {frames_dir}", start)

        # Echantillonner : premiere, milieu, derniere
        sample = self._sample_frames(frames, sample_size)
        results = []
        for f in sample:
            luma = self._compute_luminance(f)
            results.append({"frame": f.name, "luminance": luma, "verdict": self._classify(luma)})

        lumas = [r["luminance"] for r in results if r["luminance"] is not None]
        mean_luma = round(sum(lumas) / len(lumas), 2) if lumas else 0.0
        global_verdict = self._classify(mean_luma)

        # Si une frame est noire, verdict global = BLACK
        if any(r["verdict"] == "BLACK" for r in results):
            global_verdict = "BLACK"

        return {
            "version": VERSION,
            "verdict": global_verdict,
            "luminance_mean": mean_luma,
            "frames_total": len(frames),
            "frames_sampled": len(sample),
            "sample_results": results,
            "elapsed_sec": round(time.time() - start, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _compute_luminance(self, image_path: Path) -> Optional[float]:
        """Luminance moyenne d'une image (0-255)."""
        try:
            import numpy as np
            from PIL import Image
            img = np.array(Image.open(image_path).convert("L"), dtype=float)
            return round(float(img.mean()), 2)
        except ImportError:
            # Fallback sans numpy/PIL : lecture brute des bytes PNG
            return self._luminance_fallback(image_path)
        except Exception:
            return None

    def _luminance_fallback(self, image_path: Path) -> Optional[float]:
        """Luminance approximative sans numpy : moyenne des bytes."""
        try:
            data = image_path.read_bytes()
            # Lire quelques bytes au milieu du fichier comme proxy
            mid = len(data) // 2
            sample = data[mid:mid + 1000]
            if not sample:
                return None
            return round(sum(sample) / len(sample), 2)
        except Exception:
            return None

    def _classify(self, luminance: Optional[float]) -> str:
        if luminance is None:
            return "ERROR"
        if luminance < BLACK_THRESHOLD:
            return "BLACK"
        if luminance < DARK_THRESHOLD:
            return "DARK"
        return "VISIBLE"

    def _sample_frames(self, frames: List[Path], n: int) -> List[Path]:
        if len(frames) <= n:
            return frames
        indices = [0, len(frames) // 2, len(frames) - 1]
        extra = [len(frames) // 4, 3 * len(frames) // 4]
        all_idx = sorted(set(indices + extra))[:n]
        return [frames[i] for i in all_idx if i < len(frames)]

    def _error(self, msg: str, start: float) -> Dict[str, Any]:
        return {
            "version": VERSION,
            "verdict": "ERROR",
            "luminance_mean": None,
            "elapsed_sec": round(time.time() - start, 3),
            "error": msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def print_report(self, result: Dict[str, Any]) -> None:
        verdict = result.get("verdict", "?")
        luma = result.get("luminance_mean", "?")
        elapsed = result.get("elapsed_sec", 0)
        icon = "OK" if verdict == "VISIBLE" else ("!!" if verdict == "BLACK" else "--")
        print(f"\n[SENTINEL B3] [{icon}] GHOST — {verdict} | luma={luma} | {elapsed}s")
        if result.get("sample_results"):
            for r in result["sample_results"]:
                si = "OK" if r["verdict"] == "VISIBLE" else "!!"
                print(f"  [{si}] {r['frame']:<40} luma={r['luminance']}")


# ─── CLI (appel depuis Blender headless) ─────────────────────────────────────

def _argv_after_dd() -> List[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B3 — Ghost Renderer")
    p.add_argument("--blend", default=None, help="Fichier .blend a rendre")
    p.add_argument("--frames", default=None, help="Dossier frames a analyser")
    p.add_argument("--image", default=None, help="Image unique a analyser")
    p.add_argument("--output", default="ghost_frame.png", help="Fichier ghost de sortie")
    p.add_argument("--json-out", default=None, help="Sauvegarder resultat JSON")
    return p.parse_args(_argv_after_dd() if "--" in sys.argv else sys.argv[1:])


def main() -> int:
    args = _parse_args()
    ghost = GhostRenderer()

    if args.blend:
        result = ghost.render(args.blend, args.output)
    elif args.frames:
        result = ghost.analyze_folder(args.frames)
    elif args.image:
        result = ghost.analyze_existing(args.image)
    else:
        print("ERREUR : --blend, --frames ou --image requis", file=sys.stderr)
        return 1

    ghost.print_report(result)

    if args.json_out:
        Path(args.json_out).write_text(
            __import__("json").dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    return 0 if result.get("verdict") in ("VISIBLE", "DARK") else 1


if __name__ == "__main__":
    sys.exit(main())
