#!/usr/bin/env python3
"""
SENTINEL B7 — PERSONNAGES (CHARACTER VALIDATOR)
Valide les outputs des frégates U01 (animation) et U02 (logistics).

Objectif : confirmer que l'acteur Roblox/DynamicHead est correctement monte
           avant de lancer U03 (scenographie) ou le pipeline aval.

Ce que B7 verifie :
    Sur .blend (via bpy — Colab uniquement) :
        - Armature presente et active
        - ARKit ShapeKeys : >= 52 (DynamicHead Roblox standard)
        - Bones : >= 20 dans la chaine principale
        - Keyframes d'animation : > 0
        - Scale armature : (1.0, 1.0, 1.0) — requis U02
        - Mesh enfants attaches a l'armature
        - ABC export present (fichier .abc adjacent)

    Sans bpy (mode degrade — local / validation rapide) :
        - Existence et taille des fichiers attendus
        - ACTOR_01.blend (U01) : >= 500KB
        - actor_equipped.blend (U02) : >= 500KB
        - *.abc : >= 100KB
        - character_report.json (si present) : champs critiques valides

Frégates cibles :
    U01 — ANIMATION ENGINE  : ACTOR_01.blend + preview.abc
    U02 — LOGISTICS DEPOT   : actor_equipped.blend + actor_equipped.abc

Usage (standalone) :
    python brique7_characters.py --fregate U01 --blend /path/to/ACTOR_01.blend
    python brique7_characters.py --fregate U02 --blend /path/to/actor_equipped.blend
    python brique7_characters.py --fregate U01 --output-dir /path/to/U01/output/

Usage (depuis sentinel_core) :
    from brique7_characters import CharacterValidator
    cv = CharacterValidator()
    result = cv.validate(fregate="U01", blend_path="/path/to/ACTOR_01.blend")
    print(result["verdict"])  # PASS | WARN | FAIL | ERROR
"""
from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# bpy disponible uniquement sur Colab avec Blender installe
try:
    import bpy
    _BPY_AVAILABLE = True
except ImportError:
    _BPY_AVAILABLE = False

VERSION = "1.0.0"

# ─── Seuils par fregate ───────────────────────────────────────────────────────

THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "U01": {
        "shapekeys_min": 52,
        "bones_min": 20,
        "keyframes_min": 1,
        "scale_required": False,        # U01 ne require pas encore le scale
        "mesh_children_min": 1,
        "file_size_min_kb": 500,        # .blend >= 500KB
        "abc_required": False,          # optionnel en U01
        "expected_filename": "ACTOR_01.blend",
    },
    "U02": {
        "shapekeys_min": 52,
        "bones_min": 20,
        "keyframes_min": 1,
        "scale_required": True,         # (1,1,1) obligatoire en U02
        "scale_tolerance": 0.01,        # ±1% acceptable
        "mesh_children_min": 1,
        "file_size_min_kb": 500,
        "abc_required": True,           # ABC export obligatoire en U02
        "expected_filename": "actor_equipped.blend",
    },
}

# Fallback si fregate inconnue
DEFAULT_THRESHOLDS = THRESHOLDS["U01"]


# ─── Classe principale ────────────────────────────────────────────────────────

class CharacterValidator:
    """
    SENTINEL B7 — Validateur de personnage/acteur.
    Supporte deux modes : bpy (Colab) et degrade (local).
    """

    def validate(
        self,
        fregate: str,
        blend_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Point d'entree principal.

        fregate    : "U01" ou "U02"
        blend_path : chemin du fichier .blend (optionnel — si pas fourni, mode degrade)
        output_dir : dossier output de la fregate (fallback si blend_path absent)

        Retourne :
        {
            "fregate", "mode", "verdict",
            "checks": { nom_check: { "status": "PASS"|"FAIL"|"WARN", "value", "expected" } },
            "shapekeys_count", "bones_count", "keyframes_count",
            "scale_ok", "abc_present",
            "detail", "timestamp"
        }
        """
        result: Dict[str, Any] = {
            "fregate": fregate,
            "mode": "UNKNOWN",
            "verdict": "UNKNOWN",
            "checks": {},
            "shapekeys_count": 0,
            "bones_count": 0,
            "keyframes_count": 0,
            "scale_ok": None,
            "abc_present": False,
            "detail": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        thresholds = THRESHOLDS.get(fregate, DEFAULT_THRESHOLDS)

        # Mode bpy complet
        if blend_path and _BPY_AVAILABLE:
            result["mode"] = "BPY"
            return self._validate_blend_bpy(result, fregate, blend_path, thresholds)

        # Mode degrade — validation par fichiers
        result["mode"] = "DEGRADE"
        return self._validate_degrade(result, fregate, blend_path, output_dir, thresholds)

    # ── Mode bpy (Colab) ──────────────────────────────────────────────────────

    def _validate_blend_bpy(
        self,
        result: Dict[str, Any],
        fregate: str,
        blend_path: str,
        thresholds: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validation complete via bpy."""
        import bpy

        blend_file = Path(blend_path)
        if not blend_file.exists():
            result["verdict"] = "ERROR"
            result["detail"] = f"Fichier .blend introuvable : {blend_path}"
            return result

        # Charger le fichier
        try:
            bpy.ops.wm.open_mainfile(filepath=str(blend_file))
        except Exception as e:
            result["verdict"] = "ERROR"
            result["detail"] = f"Impossible d'ouvrir le .blend : {e}"
            return result

        checks = {}

        # Check 1 : Armature presente
        armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
        checks["armature_present"] = {
            "status": "PASS" if armatures else "FAIL",
            "value": len(armatures),
            "expected": ">= 1",
        }

        if not armatures:
            result["checks"] = checks
            result["verdict"] = "FAIL"
            result["detail"] = "Aucune armature dans le .blend"
            return result

        arm_obj = armatures[0]

        # Check 2 : Bones
        n_bones = len(arm_obj.data.bones)
        bones_min = thresholds.get("bones_min", 20)
        checks["bones_count"] = {
            "status": "PASS" if n_bones >= bones_min else "FAIL",
            "value": n_bones,
            "expected": f">= {bones_min}",
        }
        result["bones_count"] = n_bones

        # Check 3 : Keyframes
        n_keys = 0
        if arm_obj.animation_data and arm_obj.animation_data.action:
            n_keys = len(arm_obj.animation_data.action.fcurves)
        keys_min = thresholds.get("keyframes_min", 1)
        checks["keyframes_present"] = {
            "status": "PASS" if n_keys >= keys_min else "FAIL",
            "value": n_keys,
            "expected": f">= {keys_min}",
        }
        result["keyframes_count"] = n_keys

        # Check 4 : ShapeKeys (sur mesh enfants)
        shapekey_count = 0
        for obj in bpy.data.objects:
            if obj.type == "MESH" and obj.data.shape_keys:
                shapekey_count = max(shapekey_count, len(obj.data.shape_keys.key_blocks))

        sk_min = thresholds.get("shapekeys_min", 52)
        checks["shapekeys_count"] = {
            "status": "PASS" if shapekey_count >= sk_min else ("WARN" if shapekey_count >= sk_min // 2 else "FAIL"),
            "value": shapekey_count,
            "expected": f">= {sk_min}",
        }
        result["shapekeys_count"] = shapekey_count

        # Check 5 : Scale armature (U02)
        if thresholds.get("scale_required", False):
            tol = thresholds.get("scale_tolerance", 0.01)
            s = arm_obj.scale
            scale_ok = all(abs(v - 1.0) <= tol for v in (s.x, s.y, s.z))
            checks["scale_unit"] = {
                "status": "PASS" if scale_ok else "FAIL",
                "value": f"({round(s.x,3)}, {round(s.y,3)}, {round(s.z,3)})",
                "expected": "(1.0, 1.0, 1.0)",
            }
            result["scale_ok"] = scale_ok
        else:
            result["scale_ok"] = True

        # Check 6 : Mesh enfants
        mesh_children = [
            o for o in bpy.data.objects
            if o.type == "MESH" and o.parent == arm_obj
        ]
        mch_min = thresholds.get("mesh_children_min", 1)
        checks["mesh_children"] = {
            "status": "PASS" if len(mesh_children) >= mch_min else "WARN",
            "value": len(mesh_children),
            "expected": f">= {mch_min}",
        }

        # Check 7 : ABC export adjacent
        abc_path = blend_file.with_suffix(".abc")
        if not abc_path.exists():
            # Chercher .abc dans le meme dossier
            abc_candidates = list(blend_file.parent.glob("*.abc"))
            abc_path = abc_candidates[0] if abc_candidates else None

        abc_present = abc_path is not None and Path(abc_path).exists()
        abc_required = thresholds.get("abc_required", False)
        checks["abc_export"] = {
            "status": "PASS" if abc_present else ("FAIL" if abc_required else "WARN"),
            "value": str(abc_path) if abc_present else "absent",
            "expected": "fichier .abc adjacent",
        }
        result["abc_present"] = abc_present

        result["checks"] = checks

        # Verdict global
        n_fail = sum(1 for c in checks.values() if c["status"] == "FAIL")
        n_warn = sum(1 for c in checks.values() if c["status"] == "WARN")

        if n_fail > 0:
            result["verdict"] = "FAIL"
            failed = [k for k, v in checks.items() if v["status"] == "FAIL"]
            result["detail"] = f"{n_fail} check(s) FAIL : {', '.join(failed)}"
        elif n_warn > 0:
            result["verdict"] = "WARN"
            result["detail"] = f"{n_warn} warning(s) — personnage acceptable"
        else:
            result["verdict"] = "PASS"
            result["detail"] = f"Personnage {fregate} valide — {shapekey_count} ShapeKeys, {n_bones} bones"

        return result

    # ── Mode degrade (sans bpy) ───────────────────────────────────────────────

    def _validate_degrade(
        self,
        result: Dict[str, Any],
        fregate: str,
        blend_path: Optional[str],
        output_dir: Optional[str],
        thresholds: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validation par taille de fichier et structure (mode sans bpy)."""
        checks = {}
        size_min_kb = thresholds.get("file_size_min_kb", 500)
        abc_required = thresholds.get("abc_required", False)
        expected_fname = thresholds.get("expected_filename", "*.blend")

        # Construire le chemin .blend a partir de output_dir si pas fourni
        blend_file = None
        if blend_path:
            blend_file = Path(blend_path)
        elif output_dir:
            output_path = Path(output_dir)
            candidates = list(output_path.glob("*.blend"))
            if candidates:
                blend_file = candidates[0]

        # Check 1 : Fichier .blend present
        if blend_file and blend_file.exists():
            size_kb = blend_file.stat().st_size / 1024
            checks["blend_exists"] = {
                "status": "PASS" if size_kb >= size_min_kb else "WARN",
                "value": f"{round(size_kb, 1)} KB",
                "expected": f">= {size_min_kb} KB",
            }
        else:
            checks["blend_exists"] = {
                "status": "FAIL",
                "value": "absent",
                "expected": expected_fname,
            }

        # Check 2 : ABC export
        abc_present = False
        if blend_file and blend_file.exists():
            abc_path = blend_file.with_suffix(".abc")
            if not abc_path.exists():
                abc_candidates = list(blend_file.parent.glob("*.abc"))
                abc_path = abc_candidates[0] if abc_candidates else None
            abc_present = abc_path is not None and Path(abc_path).exists()
            if abc_present:
                abc_size_kb = Path(abc_path).stat().st_size / 1024
                checks["abc_export"] = {
                    "status": "PASS" if abc_size_kb >= 100 else "WARN",
                    "value": f"{round(abc_size_kb, 1)} KB",
                    "expected": ">= 100 KB",
                }
            else:
                checks["abc_export"] = {
                    "status": "FAIL" if abc_required else "WARN",
                    "value": "absent",
                    "expected": "fichier .abc adjacent",
                }
        result["abc_present"] = abc_present

        # Check 3 : character_report.json si present
        report_file = None
        if blend_file and blend_file.parent.exists():
            for candidate in blend_file.parent.glob("*character*report*.json"):
                report_file = candidate
                break
        if report_file and report_file.exists():
            try:
                with open(report_file, encoding="utf-8") as f:
                    char_report = json.load(f)
                sk = char_report.get("shapekeys_count", char_report.get("shapekeys", 0))
                bones = char_report.get("bones_count", char_report.get("bones", 0))
                sk_min = thresholds.get("shapekeys_min", 52)
                bones_min = thresholds.get("bones_min", 20)

                if sk > 0:
                    result["shapekeys_count"] = sk
                    checks["shapekeys_from_report"] = {
                        "status": "PASS" if sk >= sk_min else ("WARN" if sk >= sk_min // 2 else "FAIL"),
                        "value": sk,
                        "expected": f">= {sk_min}",
                    }
                if bones > 0:
                    result["bones_count"] = bones
                    checks["bones_from_report"] = {
                        "status": "PASS" if bones >= bones_min else "FAIL",
                        "value": bones,
                        "expected": f">= {bones_min}",
                    }
            except Exception:
                pass  # character_report corrompu → ignorer

        result["checks"] = checks

        # Verdict global
        n_fail = sum(1 for c in checks.values() if c["status"] == "FAIL")
        n_warn = sum(1 for c in checks.values() if c["status"] == "WARN")

        if n_fail > 0:
            result["verdict"] = "FAIL"
            failed = [k for k, v in checks.items() if v["status"] == "FAIL"]
            result["detail"] = f"Mode degrade — {n_fail} check(s) FAIL : {', '.join(failed)}"
        elif n_warn > 0:
            result["verdict"] = "WARN"
            result["detail"] = "Mode degrade (sans bpy) — verifier manuellement shapekeys et bones"
        else:
            result["verdict"] = "PASS"
            result["detail"] = "Mode degrade — fichiers presents et taille correcte"

        return result

    def save(self, result: Dict[str, Any], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    def print_report(self, result: Dict[str, Any]) -> None:
        verdict = result.get("verdict", "?")
        icon = "[PASS]" if verdict == "PASS" else ("[WARN]" if verdict == "WARN" else "[FAIL]")
        mode = result.get("mode", "?")
        print(f"\n  [B7 PERSONNAGES] {result.get('fregate', '?')} — mode {mode} — {icon}")
        print(f"  ShapeKeys      : {result.get('shapekeys_count', '?')} (requis >= 52)")
        print(f"  Bones          : {result.get('bones_count', '?')} (requis >= 20)")
        print(f"  ABC export     : {'OUI' if result.get('abc_present') else 'NON'}")
        print(f"  Scale OK       : {result.get('scale_ok', 'N/A')}")
        print(f"  Detail         : {result.get('detail', 'N/A')}")

        for check_name, check_data in result.get("checks", {}).items():
            status = check_data.get("status", "?")
            if status != "PASS":
                print(f"    {status} — {check_name}: {check_data.get('value')} (attendu: {check_data.get('expected')})")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B7 — Validateur de personnage U01/U02")
    p.add_argument("--fregate", required=True, choices=["U01", "U02"], help="Fregate cible")
    p.add_argument("--blend", default=None, help="Chemin fichier .blend")
    p.add_argument("--output-dir", default=None, help="Dossier output de la fregate")
    p.add_argument("--output", default=None, help="Chemin JSON de sortie")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    cv = CharacterValidator()
    result = cv.validate(
        fregate=args.fregate,
        blend_path=args.blend,
        output_dir=args.output_dir,
    )
    cv.print_report(result)
    if args.output:
        cv.save(result, args.output)
        print(f"  [B7] Rapport sauvegarde : {args.output}")

    return 0 if result["verdict"] in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
