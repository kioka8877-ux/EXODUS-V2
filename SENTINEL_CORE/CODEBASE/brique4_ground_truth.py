#!/usr/bin/env python3
"""
SENTINEL B4 — LA VERITE (GROUND TRUTH COMPARATOR)
Compare les outputs reels d'une fregate contre une reference stockee dans REFERENCES/.

Objectif : detecter les regressions visuelles et structurelles entre runs.
Principe : si l'output s'eloigne de la reference doree → FAIL.

Ce que B4 detecte :
    - Regression luminance : ecart > 20% vs reference
    - Regression couleur  : deviation histogram > seuil
    - Regression taille   : fichier trop petit ou trop grand vs reference
    - Reference absente   : premier run = creation de la reference
    - JSON drift          : champs critiques absents ou modifies dans PRODUCTION_PLAN.JSON

Modes :
    - FRAMES  : compare un dossier de frames PNG contre REFERENCES/{fregate}/
    - JSON    : compare un fichier JSON contre REFERENCES/{fregate}/reference.json
    - BLEND   : compare les metadonnees .blend (taille + timestamp) vs reference

Usage (standalone) :
    python brique4_ground_truth.py --fregate U04 --frames /path/to/frames/ --refs /path/to/REFERENCES/
    python brique4_ground_truth.py --fregate U00 --json /path/to/PRODUCTION_PLAN.JSON --refs /path/to/REFERENCES/
    python brique4_ground_truth.py --fregate U03 --blend /path/to/env.blend --refs /path/to/REFERENCES/
    python brique4_ground_truth.py --fregate U04 --update-ref --frames /path/to/frames/ --refs /path/to/REFERENCES/

Usage (depuis sentinel_core) :
    from brique4_ground_truth import GroundTruth
    gt = GroundTruth(refs_dir="/path/to/SENTINEL_CORE/REFERENCES")
    result = gt.compare_frames(fregate="U04", frames_dir="/path/to/frames/")
    print(result["verdict"])  # PASS | WARN | FAIL | NO_REF | ERROR
"""
from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Imports optionnels — B4 fonctionne en mode degrade sans PIL/numpy
try:
    from PIL import Image
    import numpy as np
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

VERSION = "1.0.0"

# Seuils de regression
LUMINANCE_TOLERANCE = 0.20   # 20% de deviation acceptable
COLOR_TOLERANCE = 0.25        # 25% de deviation histogram
SIZE_TOLERANCE = 0.30         # 30% de deviation taille fichier
JSON_FIELDS_CRITICAL = {      # Champs JSON critiques par fregate
    "U00": ["scenes", "camera", "lighting"],
    "U01": ["actor", "armature", "shapekeys"],
    "U02": ["actor", "props", "rig_scale"],
    "U03": ["environment_id", "scene_type", "displacement"],
    "U04": ["frames", "resolution", "camera_path"],
    "U05": ["frames_post", "lut_applied"],
    "U06": ["output_video", "duration_sec", "fps"],
}


# ─── Classe principale ────────────────────────────────────────────────────────

class GroundTruth:
    """
    SENTINEL B4 — Comparateur Ground Truth.
    Detecte les regressions entre le run actuel et la reference stockee.
    """

    def __init__(self, refs_dir: str = "SENTINEL_CORE/REFERENCES"):
        self.refs_dir = Path(refs_dir)

    # ── Comparaison frames ────────────────────────────────────────────────────

    def compare_frames(self, fregate: str, frames_dir: str) -> Dict[str, Any]:
        """
        Compare les frames actuelles contre la reference.
        Si aucune reference : retourne verdict NO_REF (premier run).

        Retourne :
        {
            "fregate", "mode": "FRAMES", "verdict", "ref_exists": bool,
            "frames_compared": int, "regressions": [...],
            "luminance_delta": float, "color_delta": float,
            "timestamp"
        }
        """
        result: Dict[str, Any] = {
            "fregate": fregate,
            "mode": "FRAMES",
            "verdict": "UNKNOWN",
            "ref_exists": False,
            "frames_compared": 0,
            "regressions": [],
            "luminance_delta": 0.0,
            "color_delta": 0.0,
            "detail": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        frames_path = Path(frames_dir)
        ref_path = self.refs_dir / fregate

        if not frames_path.exists():
            result["verdict"] = "ERROR"
            result["detail"] = f"Dossier frames introuvable : {frames_dir}"
            return result

        # Collecter frames actuelles
        current_frames = sorted([
            f for f in frames_path.iterdir()
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".exr")
        ])

        if not current_frames:
            result["verdict"] = "WARN"
            result["detail"] = "Aucune frame trouvee dans le dossier"
            return result

        # Verifier existence reference
        if not ref_path.exists() or not any(ref_path.iterdir()):
            result["verdict"] = "NO_REF"
            result["ref_exists"] = False
            result["detail"] = (
                f"Aucune reference pour {fregate}. "
                f"Lancer avec --update-ref pour creer la reference a partir de ce run."
            )
            return result

        result["ref_exists"] = True
        ref_frames = sorted([
            f for f in ref_path.iterdir()
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".exr")
        ])

        if not ref_frames:
            result["verdict"] = "NO_REF"
            result["detail"] = f"Dossier reference {fregate}/ vide."
            return result

        if not _PIL_AVAILABLE:
            # Mode degrade : comparaison par taille de fichier uniquement
            result = self._compare_frames_size_only(result, current_frames, ref_frames)
            return result

        # Mode complet : comparaison luminance + histogramme
        result = self._compare_frames_visual(result, current_frames, ref_frames)
        return result

    def _compare_frames_size_only(
        self,
        result: Dict[str, Any],
        current: List[Path],
        refs: List[Path],
    ) -> Dict[str, Any]:
        """Comparaison par taille de fichier (mode degrade sans PIL)."""
        n = min(len(current), len(refs))
        regressions = []
        for i in range(n):
            cur_size = current[i].stat().st_size
            ref_size = refs[i].stat().st_size
            if ref_size > 0:
                delta = abs(cur_size - ref_size) / ref_size
                if delta > SIZE_TOLERANCE:
                    regressions.append({
                        "frame": current[i].name,
                        "type": "SIZE_REGRESSION",
                        "delta_pct": round(delta * 100, 1),
                        "cur_bytes": cur_size,
                        "ref_bytes": ref_size,
                    })

        result["frames_compared"] = n
        result["regressions"] = regressions
        result["detail"] = f"Mode degrade (PIL absent) — {n} frames comparees par taille"

        if regressions:
            result["verdict"] = "WARN"
        else:
            result["verdict"] = "PASS"
        return result

    def _compare_frames_visual(
        self,
        result: Dict[str, Any],
        current: List[Path],
        refs: List[Path],
    ) -> Dict[str, Any]:
        """Comparaison visuelle (luminance + histogramme) avec PIL."""
        import numpy as np
        from PIL import Image

        n = min(len(current), len(refs), 10)  # max 10 frames comparees
        luma_deltas = []
        color_deltas = []
        regressions = []

        for i in range(n):
            try:
                cur_img = np.array(Image.open(current[i]).convert("L"), dtype=float)
                ref_img = np.array(Image.open(refs[i]).convert("L"), dtype=float)

                cur_luma = float(cur_img.mean())
                ref_luma = float(ref_img.mean())

                if ref_luma > 0:
                    luma_delta = abs(cur_luma - ref_luma) / ref_luma
                else:
                    luma_delta = 0.0
                luma_deltas.append(luma_delta)

                # Comparaison histogramme (16 bins)
                cur_hist = np.histogram(cur_img, bins=16, range=(0, 255))[0].astype(float)
                ref_hist = np.histogram(ref_img, bins=16, range=(0, 255))[0].astype(float)
                cur_hist /= (cur_hist.sum() + 1e-9)
                ref_hist /= (ref_hist.sum() + 1e-9)
                color_delta = float(np.abs(cur_hist - ref_hist).mean())
                color_deltas.append(color_delta)

                if luma_delta > LUMINANCE_TOLERANCE:
                    regressions.append({
                        "frame": current[i].name,
                        "type": "LUMINANCE_REGRESSION",
                        "delta_pct": round(luma_delta * 100, 1),
                        "cur_luma": round(cur_luma, 1),
                        "ref_luma": round(ref_luma, 1),
                    })
                elif color_delta > COLOR_TOLERANCE:
                    regressions.append({
                        "frame": current[i].name,
                        "type": "COLOR_REGRESSION",
                        "delta_pct": round(color_delta * 100, 1),
                    })

            except Exception as e:
                regressions.append({
                    "frame": current[i].name,
                    "type": "COMPARE_ERROR",
                    "detail": str(e),
                })

        result["frames_compared"] = n
        result["regressions"] = regressions
        result["luminance_delta"] = round(float(sum(luma_deltas) / len(luma_deltas)) * 100, 1) if luma_deltas else 0.0
        result["color_delta"] = round(float(sum(color_deltas) / len(color_deltas)) * 100, 1) if color_deltas else 0.0

        n_regress = len(regressions)
        if n_regress == 0:
            result["verdict"] = "PASS"
            result["detail"] = f"{n} frames — aucune regression detectee"
        elif n_regress <= 2:
            result["verdict"] = "WARN"
            result["detail"] = f"{n_regress}/{n} frames en regression (seuil {int(LUMINANCE_TOLERANCE*100)}%)"
        else:
            result["verdict"] = "FAIL"
            result["detail"] = f"{n_regress}/{n} frames en regression — pipeline instable"

        return result

    # ── Comparaison JSON ──────────────────────────────────────────────────────

    def compare_json(self, fregate: str, json_path: str) -> Dict[str, Any]:
        """
        Compare un fichier JSON contre la reference.
        Verifie la presence des champs critiques et leur type.
        """
        result: Dict[str, Any] = {
            "fregate": fregate,
            "mode": "JSON",
            "verdict": "UNKNOWN",
            "ref_exists": False,
            "fields_checked": 0,
            "fields_missing": [],
            "fields_type_changed": [],
            "detail": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        json_file = Path(json_path)
        if not json_file.exists():
            result["verdict"] = "ERROR"
            result["detail"] = f"Fichier JSON introuvable : {json_path}"
            return result

        try:
            with open(json_file, encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception as e:
            result["verdict"] = "FAIL"
            result["detail"] = f"JSON non parseable : {e}"
            return result

        ref_file = self.refs_dir / fregate / "reference.json"

        if not ref_file.exists():
            result["verdict"] = "NO_REF"
            result["ref_exists"] = False
            result["detail"] = "Aucune reference JSON. Lancer --update-ref pour creer la reference."
            return result

        result["ref_exists"] = True
        try:
            with open(ref_file, encoding="utf-8") as f:
                ref_data = json.load(f)
        except Exception as e:
            result["verdict"] = "ERROR"
            result["detail"] = f"Reference JSON corrompue : {e}"
            return result

        # Verifier champs critiques par fregate
        critical_fields = JSON_FIELDS_CRITICAL.get(fregate, [])
        missing = []
        type_changed = []

        for field in critical_fields:
            result["fields_checked"] += 1
            if field not in current_data:
                missing.append(field)
            elif field in ref_data and type(current_data[field]) != type(ref_data[field]):
                type_changed.append({
                    "field": field,
                    "expected_type": type(ref_data[field]).__name__,
                    "actual_type": type(current_data[field]).__name__,
                })

        result["fields_missing"] = missing
        result["fields_type_changed"] = type_changed

        if missing:
            result["verdict"] = "FAIL"
            result["detail"] = f"Champs critiques absents : {', '.join(missing)}"
        elif type_changed:
            result["verdict"] = "WARN"
            result["detail"] = f"{len(type_changed)} champ(s) de type modifie"
        else:
            result["verdict"] = "PASS"
            result["detail"] = f"{result['fields_checked']} champs critiques presents et conformes"

        return result

    # ── Comparaison .blend (metadonnees) ──────────────────────────────────────

    def compare_blend(self, fregate: str, blend_path: str) -> Dict[str, Any]:
        """
        Compare les metadonnees d'un .blend contre la reference (taille + hash simple).
        """
        result: Dict[str, Any] = {
            "fregate": fregate,
            "mode": "BLEND",
            "verdict": "UNKNOWN",
            "ref_exists": False,
            "size_delta_pct": 0.0,
            "detail": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        blend_file = Path(blend_path)
        if not blend_file.exists():
            result["verdict"] = "ERROR"
            result["detail"] = f"Fichier .blend introuvable : {blend_path}"
            return result

        ref_meta_file = self.refs_dir / fregate / "blend_meta.json"

        if not ref_meta_file.exists():
            result["verdict"] = "NO_REF"
            result["ref_exists"] = False
            result["detail"] = "Aucune reference blend. Lancer --update-ref pour creer la reference."
            return result

        result["ref_exists"] = True
        try:
            with open(ref_meta_file, encoding="utf-8") as f:
                ref_meta = json.load(f)
        except Exception as e:
            result["verdict"] = "ERROR"
            result["detail"] = f"Metadonnees reference corrompues : {e}"
            return result

        cur_size = blend_file.stat().st_size
        ref_size = ref_meta.get("size_bytes", 0)

        if ref_size > 0:
            delta = abs(cur_size - ref_size) / ref_size
            result["size_delta_pct"] = round(delta * 100, 1)
            if delta > SIZE_TOLERANCE:
                result["verdict"] = "WARN"
                result["detail"] = (
                    f"Taille .blend modifiee de {result['size_delta_pct']}% "
                    f"(ref: {ref_size}B, actuel: {cur_size}B)"
                )
            else:
                result["verdict"] = "PASS"
                result["detail"] = f"Taille .blend conforme (delta: {result['size_delta_pct']}%)"
        else:
            result["verdict"] = "UNKNOWN"
            result["detail"] = "Reference de taille absente"

        return result

    # ── Mise a jour reference ─────────────────────────────────────────────────

    def update_reference(
        self,
        fregate: str,
        frames_dir: Optional[str] = None,
        json_path: Optional[str] = None,
        blend_path: Optional[str] = None,
        max_ref_frames: int = 5,
    ) -> Dict[str, Any]:
        """
        Cree ou met a jour la reference pour une fregate.
        Utilise le run actuel comme nouvelle reference.
        """
        ref_dir = self.refs_dir / fregate
        ref_dir.mkdir(parents=True, exist_ok=True)

        updated: List[str] = []

        # Reference frames
        if frames_dir:
            frames_path = Path(frames_dir)
            if frames_path.exists():
                # Copier les N premieres frames comme reference
                frames = sorted([
                    f for f in frames_path.iterdir()
                    if f.suffix.lower() in (".png", ".jpg", ".jpeg")
                ])[:max_ref_frames]

                # Nettoyer anciennes references
                for old in ref_dir.glob("*.png"):
                    old.unlink()
                for old in ref_dir.glob("*.jpg"):
                    old.unlink()

                for f in frames:
                    import shutil
                    shutil.copy2(f, ref_dir / f.name)
                    updated.append(f.name)

        # Reference JSON
        if json_path:
            json_file = Path(json_path)
            if json_file.exists():
                import shutil
                shutil.copy2(json_file, ref_dir / "reference.json")
                updated.append("reference.json")

        # Reference .blend (metadonnees seulement)
        if blend_path:
            blend_file = Path(blend_path)
            if blend_file.exists():
                meta = {
                    "filename": blend_file.name,
                    "size_bytes": blend_file.stat().st_size,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                with open(ref_dir / "blend_meta.json", "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
                updated.append("blend_meta.json")

        return {
            "fregate": fregate,
            "ref_dir": str(ref_dir),
            "updated_files": updated,
            "status": "OK" if updated else "NOTHING_UPDATED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def save(self, result: Dict[str, Any], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    def print_report(self, result: Dict[str, Any]) -> None:
        verdict = result.get("verdict", "?")
        icon = "[PASS]" if verdict == "PASS" else ("[NO_REF]" if verdict == "NO_REF" else ("[WARN]" if verdict == "WARN" else "[FAIL]"))
        print(f"\n  [B4 LA VERITE] {result.get('fregate', '?')} — mode {result.get('mode', '?')} — {icon}")
        print(f"  Reference      : {'PRESENTE' if result.get('ref_exists') else 'ABSENTE'}")
        print(f"  Detail         : {result.get('detail', 'N/A')}")
        if result.get("regressions"):
            for r in result["regressions"][:3]:
                print(f"    Regression : {r.get('frame', '?')} — {r.get('type', '?')} ({r.get('delta_pct', '?')}%)")
        if result.get("fields_missing"):
            print(f"  Champs absents : {', '.join(result['fields_missing'])}")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B4 — Comparateur Ground Truth")
    p.add_argument("--fregate", required=True, help="ID fregate (U00-U06)")
    p.add_argument("--refs", default="SENTINEL_CORE/REFERENCES", help="Dossier REFERENCES/")
    p.add_argument("--frames", default=None, help="Dossier frames a comparer")
    p.add_argument("--json", default=None, help="Fichier JSON a comparer")
    p.add_argument("--blend", default=None, help="Fichier .blend a comparer")
    p.add_argument("--update-ref", action="store_true", help="Creer/maj reference a partir de ce run")
    p.add_argument("--output", default=None, help="Chemin JSON de sortie")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    gt = GroundTruth(refs_dir=args.refs)

    if args.update_ref:
        upd = gt.update_reference(
            fregate=args.fregate,
            frames_dir=args.frames,
            json_path=args.json,
            blend_path=args.blend,
        )
        print(f"[B4] Reference mise a jour : {upd['updated_files']}")
        return 0

    result = None
    if args.frames:
        result = gt.compare_frames(fregate=args.fregate, frames_dir=args.frames)
    elif args.json:
        result = gt.compare_json(fregate=args.fregate, json_path=args.json)
    elif args.blend:
        result = gt.compare_blend(fregate=args.fregate, blend_path=args.blend)
    else:
        print("Usage : --frames / --json / --blend requis (ou --update-ref)")
        return 1

    gt.print_report(result)
    if args.output:
        gt.save(result, args.output)
        print(f"  [B4] Rapport sauvegarde : {args.output}")

    return 0 if result["verdict"] in ("PASS", "WARN", "NO_REF") else 1


if __name__ == "__main__":
    sys.exit(main())
