#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   FSPY TRACKER — EXODUS PHOTOGRAPHY                         ║
║              Pilier A : Perspective Lock (fSpy ±5%)                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Lit camera_fov_ratio.json (U00), calcule la focale mm, configure le lens
Blender et valide que la déviation reste dans la tolérance ±5%.

Usage (appelé par le pipeline U04):
    blender --background env.blend --python fspy_tracker.py -- \
        --json /path/to/camera_fov_ratio.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[FSPY_TRACKER] Blender non disponible - mode test")

from camera_schema import (
    CameraSchema,
    DEFAULT_SENSOR_WIDTH_MM,
    PERSPECTIVE_LOCK_TOLERANCE,
    fov_to_focal_mm,
    focal_mm_to_fov,
)


class FspyTracker:
    """Gère le verrouillage de perspective fSpy et la validation ±5%."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.schema = CameraSchema()
        self.operations: list = []

    def log(self, msg: str) -> None:
        print(f"[FSPY_TRACKER] {msg}")
        self.operations.append({"action": "log", "message": msg})

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[FSPY_TRACKER:DEBUG] {msg}")

    def get_operations(self) -> list:
        return self.operations

    def load_fov_json(self, json_path: str) -> dict:
        """Lit et valide camera_fov_ratio.json depuis U00."""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {json_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "estimated_fov_degrees" not in data:
            raise KeyError("Clé 'estimated_fov_degrees' absente du JSON")

        self.log(f"JSON chargé : {json_path} (FOV={data['estimated_fov_degrees']}°)")
        self.debug(f"Contenu JSON : {data}")
        return data

    def compute_focal_mm(self, fov_degrees: float) -> float:
        """Convertit un FOV en focale mm via camera_schema."""
        focal = fov_to_focal_mm(fov_degrees, DEFAULT_SENSOR_WIDTH_MM)
        self.log(f"FOV {fov_degrees:.1f}° → focal {focal:.2f}mm (sensor={DEFAULT_SENSOR_WIDTH_MM}mm)")
        self.operations.append({
            "action": "compute_focal",
            "fov_degrees": fov_degrees,
            "focal_mm": focal,
            "sensor_width_mm": DEFAULT_SENSOR_WIDTH_MM,
        })
        return focal

    def apply_perspective_lock(self, camera_obj: object, fov_degrees: float) -> None:
        """Configure le lens Blender avec la focale calculée."""
        if not BLENDER_AVAILABLE:
            self.log("Blender indisponible — perspective lock simulé")
            return

        focal = self.compute_focal_mm(fov_degrees)
        camera_obj.data.lens = focal
        camera_obj.data.sensor_width = DEFAULT_SENSOR_WIDTH_MM
        self.log(f"Perspective lock appliqué : lens={focal:.2f}mm, sensor={DEFAULT_SENSOR_WIDTH_MM}mm")
        self.operations.append({
            "action": "apply_perspective_lock",
            "focal_mm": focal,
            "sensor_width_mm": DEFAULT_SENSOR_WIDTH_MM,
        })

    def validate_lock(self, original_fov: float, current_fov: float) -> Tuple[bool, float]:
        """Valide la déviation de perspective via le schema (tolérance ±5%)."""
        ok, deviation = self.schema.validate_perspective_deviation(original_fov, current_fov)
        status = "OK" if ok else "FAIL"
        self.log(
            f"Validation perspective : {original_fov:.1f}° → {current_fov:.1f}° "
            f"(déviation={deviation:.2%}, seuil={PERSPECTIVE_LOCK_TOLERANCE:.0%}) → {status}"
        )
        self.operations.append({
            "action": "validate_lock",
            "original_fov": original_fov,
            "current_fov": current_fov,
            "deviation": deviation,
            "within_tolerance": ok,
        })
        return (ok, deviation)

    def process(self, camera_obj: object, json_path: str) -> dict:
        """Pipeline complet : load JSON → compute focal → apply lock → validate."""
        self.log("=== Pipeline fSpy Perspective Lock ===")

        data = self.load_fov_json(json_path)
        fov = data["estimated_fov_degrees"]

        focal = self.compute_focal_mm(fov)

        if BLENDER_AVAILABLE:
            self.apply_perspective_lock(camera_obj, fov)
            current_focal = camera_obj.data.lens
            current_fov = focal_mm_to_fov(current_focal, DEFAULT_SENSOR_WIDTH_MM)
        else:
            current_fov = focal_mm_to_fov(focal, DEFAULT_SENSOR_WIDTH_MM)
            self.log("Blender indisponible — validation sur valeur calculée")

        ok, deviation = self.validate_lock(fov, current_fov)

        summary = {
            "source_json": json_path,
            "original_fov": fov,
            "focal_mm": focal,
            "current_fov": current_fov,
            "deviation": deviation,
            "lock_valid": ok,
            "operations_count": len(self.operations),
        }
        self.log(f"Pipeline terminé : lock_valid={ok}, deviation={deviation:.4%}")
        return summary


# =============================================================================
# STANDALONE TEST — exécution hors Blender
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   FSPY TRACKER — TEST STANDALONE")
    print("=" * 60)

    tracker = FspyTracker(verbose=True)

    mock_json = {
        "resolution": [1080, 1920],
        "ratio": "9:16",
        "ratio_raw": "1080:1920",
        "fps_source": 30,
        "frame_count": 900,
        "duration_seconds": 30.0,
        "estimated_fov_degrees": 60.0,
    }

    passed = 0
    total = 3

    # --- TEST 1 : Conversion FOV → focal_mm ---
    focal = tracker.compute_focal_mm(60.0)
    t1_ok = 30.0 <= focal <= 32.5
    if t1_ok:
        passed += 1
    print(f"\n[TEST 1] FOV 60° → focal {focal:.2f}mm ............. {'✓' if t1_ok else '✗'}")

    # --- TEST 2 : Validation ±5% — 60→62 (doit passer) ---
    ok_pass, dev_pass = tracker.validate_lock(60.0, 62.0)
    t2_ok = ok_pass and dev_pass <= PERSPECTIVE_LOCK_TOLERANCE
    if t2_ok:
        passed += 1
    print(f"[TEST 2] 60→62° déviation {dev_pass:.2%} ............ {'✓' if t2_ok else '✗'}")

    # --- TEST 3 : Validation ±5% — 60→70 (doit échouer) ---
    ok_fail, dev_fail = tracker.validate_lock(60.0, 70.0)
    t3_ok = not ok_fail and dev_fail > PERSPECTIVE_LOCK_TOLERANCE
    if t3_ok:
        passed += 1
    print(f"[TEST 3] 60→70° déviation {dev_fail:.2%} ........... {'✓' if t3_ok else '✗'}")

    print(f"\n{'=' * 60}")
    print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
    print(f"{'=' * 60}")
