#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   RENDER FORGE — EXODUS PHOTOGRAPHY                         ║
║              Configuration Cycles + Passes (NO Rendering)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Configure le moteur Cycles (samples, denoising, résolution, passes GPU)
sans jamais lancer de rendu — c'est le rôle de U04-B.

Usage (appelé par le pipeline U04):
    blender --background env.blend --python render_forge.py -- \
        --preset production
"""

from typing import Dict, List, Optional

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[RENDER_FORGE] Blender non disponible - mode test")

from camera_schema import (
    RENDER_PRESETS,
    TARGET_RESOLUTION_4K,
    TARGET_FPS,
    DEFAULT_CYCLES_SAMPLES,
    PREVIEW_CYCLES_SAMPLES,
)


class RenderForge:
    """Configure Cycles (engine, samples, denoising, passes, GPU) — ne rend jamais."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.presets: Dict[str, dict] = dict(RENDER_PRESETS)
        self.operations: list = []

    def log(self, msg: str) -> None:
        print(f"[RENDER_FORGE] {msg}")
        self.operations.append({"action": "log", "message": msg})

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[RENDER_FORGE:DEBUG] {msg}")

    def get_operations(self) -> list:
        return self.operations

    def apply_preset(self, preset_name: str = "production") -> None:
        """Applique un preset de rendu Cycles à la scène active."""
        if preset_name not in self.presets:
            raise ValueError(
                f"Preset inconnu : '{preset_name}'. Valides : {list(self.presets.keys())}"
            )

        preset = self.presets[preset_name]
        self.log(f"Application preset : {preset_name}")

        if not BLENDER_AVAILABLE:
            self.log("Blender indisponible — preset simulé")
            self.operations.append({
                "action": "apply_preset",
                "preset": preset_name,
                "settings": preset,
                "simulated": True,
            })
            return

        scene = bpy.context.scene

        scene.render.engine = 'CYCLES'

        scene.cycles.samples = preset["samples"]
        scene.cycles.use_adaptive_sampling = preset["use_adaptive_sampling"]
        scene.cycles.adaptive_threshold = preset["adaptive_threshold"]

        scene.cycles.use_denoising = preset["use_denoising"]
        scene.cycles.denoiser = preset["denoiser"]

        scene.render.resolution_x = preset["resolution"][0]
        scene.render.resolution_y = preset["resolution"][1]
        scene.render.resolution_percentage = 100

        scene.render.fps = TARGET_FPS

        scene.render.film_transparent = preset["film_transparent"]

        self.log(
            f"Preset '{preset_name}' appliqué : "
            f"{preset['resolution'][0]}x{preset['resolution'][1]} @ "
            f"{preset['samples']} samples, denoiser={preset['denoiser']}, "
            f"fps={TARGET_FPS}"
        )
        self.operations.append({
            "action": "apply_preset",
            "preset": preset_name,
            "engine": "CYCLES",
            "samples": preset["samples"],
            "resolution": list(preset["resolution"]),
            "denoiser": preset["denoiser"],
            "fps": TARGET_FPS,
        })

    def activate_passes(self, passes: List[str]) -> None:
        """Active les render passes sur le view layer actif."""
        self.log(f"Activation passes : {passes}")

        if not BLENDER_AVAILABLE:
            self.log("Blender indisponible — passes simulées")
            self.operations.append({
                "action": "activate_passes",
                "passes": passes,
                "simulated": True,
            })
            return

        vl = bpy.context.scene.view_layers[0]

        vl.use_pass_combined = "Combined" in passes
        vl.use_pass_z = "Depth" in passes
        vl.use_pass_normal = "Normal" in passes
        vl.use_pass_diffuse_color = "DiffCol" in passes
        vl.use_pass_glossy_color = "GlossCol" in passes
        vl.use_pass_emit = "Emit" in passes

        self.log(f"Passes activées ({len(passes)}) sur view layer '{vl.name}'")
        self.operations.append({
            "action": "activate_passes",
            "passes": passes,
            "view_layer": vl.name,
        })

    def set_gpu_if_available(self) -> None:
        """Tente d'activer le GPU pour Cycles (CUDA → OPTIX → CPU fallback)."""
        if not BLENDER_AVAILABLE:
            self.log("Blender indisponible — GPU config simulée")
            self.operations.append({
                "action": "set_gpu",
                "device": "CPU",
                "simulated": True,
            })
            return

        scene = bpy.context.scene
        device_type_used = "NONE"

        for compute_type in ('CUDA', 'OPTIX'):
            try:
                prefs = bpy.context.preferences.addons['cycles'].preferences
                prefs.compute_device_type = compute_type
                prefs.get_devices()
                for device in prefs.devices:
                    device.use = True
                scene.cycles.device = 'GPU'
                device_type_used = compute_type
                self.log(f"GPU activé : {compute_type}")
                break
            except Exception:
                self.debug(f"{compute_type} indisponible, tentative suivante...")
                continue
        else:
            scene.cycles.device = 'CPU'
            device_type_used = "CPU"
            self.log("Aucun GPU détecté — fallback CPU")

        self.operations.append({
            "action": "set_gpu",
            "device": device_type_used,
        })

    def process(self, preset_name: str = "production") -> dict:
        """Pipeline complet : preset → passes → GPU → résumé."""
        self.log(f"=== Pipeline Render Forge (preset={preset_name}) ===")

        self.apply_preset(preset_name)

        preset = self.presets[preset_name]
        self.activate_passes(preset["passes"])

        self.set_gpu_if_available()

        summary = {
            "preset": preset_name,
            "engine": "CYCLES",
            "samples": preset["samples"],
            "resolution": list(preset["resolution"]),
            "fps": TARGET_FPS,
            "denoiser": preset["denoiser"],
            "passes": preset["passes"],
            "film_transparent": preset["film_transparent"],
            "operations_count": len(self.operations),
        }
        self.log(f"Pipeline terminé : {preset_name} ({preset['samples']} samples, {len(preset['passes'])} passes)")
        return summary


# =============================================================================
# STANDALONE TEST — exécution hors Blender
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   RENDER FORGE — TEST STANDALONE")
    print("=" * 60)

    passed = 0
    total = 4

    # --- TEST 1 : RENDER_PRESETS a les clés attendues ---
    expected_presets = {"production", "darkroom", "preview"}
    actual_presets = set(RENDER_PRESETS.keys())
    t1_ok = actual_presets == expected_presets
    if t1_ok:
        passed += 1
    print(f"\n[TEST 1] RENDER_PRESETS keys = {sorted(actual_presets)} ... {'✓' if t1_ok else '✗'}")

    # --- TEST 2 : Production a 6 passes ---
    prod_passes = RENDER_PRESETS["production"]["passes"]
    t2_ok = len(prod_passes) == 6
    if t2_ok:
        passed += 1
    print(f"[TEST 2] production passes ({len(prod_passes)}) = {prod_passes} ... {'✓' if t2_ok else '✗'}")

    # --- TEST 3 : Constantes cohérentes ---
    t3_ok = (
        DEFAULT_CYCLES_SAMPLES == 256
        and PREVIEW_CYCLES_SAMPLES == 64
        and TARGET_RESOLUTION_4K == (3840, 2160)
        and TARGET_FPS == 30
    )
    if t3_ok:
        passed += 1
    print(
        f"[TEST 3] Constantes : samples={DEFAULT_CYCLES_SAMPLES}/{PREVIEW_CYCLES_SAMPLES}, "
        f"res={TARGET_RESOLUTION_4K}, fps={TARGET_FPS} ... {'✓' if t3_ok else '✗'}"
    )

    # --- TEST 4 : Simulation process() ---
    forge = RenderForge(verbose=True)
    print(f"\n--- Simulation process('production') ---")
    result = forge.process("production")
    t4_ok = (
        result["preset"] == "production"
        and result["samples"] == 256
        and result["engine"] == "CYCLES"
        and len(result["passes"]) == 6
    )
    if t4_ok:
        passed += 1
    print(f"[TEST 4] process() summary valid ... {'✓' if t4_ok else '✗'}")

    print(f"\n{'=' * 60}")
    print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
    print(f"{'=' * 60}")
