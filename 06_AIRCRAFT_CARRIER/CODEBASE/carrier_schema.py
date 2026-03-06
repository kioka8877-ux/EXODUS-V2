"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 06_AIRCRAFT_CARRIER — CARRIER SCHEMA (Bible du Vaisseau-Mère)    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de données pures : définit TOUTES les constantes, presets et       ║
║  validations nécessaires au pipeline d'assemblage final V2 de U06.         ║
║  Zéro dépendance externe. Zéro traitement. Données + Validation.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import math
from typing import Dict, List, Optional, Tuple


# =============================================================================
# PILIER 1 — CONSTANTES CANONIQUES
# =============================================================================

CARRIER_SCHEMA_VERSION = "2.0.0"

VALID_RATIOS: List[str] = ["9:16", "16:9", "4:3", "1:1"]

RESOLUTION_PRESETS: Dict[str, Tuple[int, int]] = {
    "4K": (3840, 2160),
    "UHD": (3840, 2160),
    "2K": (2560, 1440),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
}

VALID_TARGET_FPS: List[int] = [120, 60, 30]
DEFAULT_TARGET_FPS: int = 120
DEFAULT_SOURCE_FPS: int = 30

CRF_RANGES: Dict[str, Tuple[int, int]] = {
    "libx265": (16, 22),
    "libsvtav1": (20, 38),
    "default": (16, 28),
}
DEFAULT_CRF_DISTRIBUTION: int = 20
DEFAULT_CRF_AV1: int = 30

SUPPORTED_FRAME_FORMATS: List[str] = [".png", ".exr", ".tiff"]
SUPPORTED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".aac"]

PIPELINE_STAGES: List[str] = ["index", "rife", "upscale", "encode"]


# =============================================================================
# PILIER 2 — FORMAT METADATA PARSER
# =============================================================================

def parse_format_metadata(plan: dict) -> dict:
    """Parse le PRODUCTION_PLAN.JSON V2 et retourne les métadonnées de format.
    Supporte le format V2 (format.resolution array) ET le legacy (output.resolution string).

    V2 : plan["production_plan"]["format"]["resolution"] = [height, width]
    Legacy : plan["output"]["resolution"] = "4K" (string résolu via RESOLUTION_PRESETS)

    Returns:
        {"width": int, "height": int, "ratio": str, "fps_source": int}
    """
    pp = plan.get("production_plan", {})
    fmt = pp.get("format", {})

    res_array = fmt.get("resolution")
    if res_array and isinstance(res_array, (list, tuple)) and len(res_array) == 2:
        height, width = int(res_array[0]), int(res_array[1])
        ratio = fmt.get("ratio", "16:9")
        fps_source = int(fmt.get("fps_source", DEFAULT_SOURCE_FPS))
        return {"width": width, "height": height, "ratio": ratio, "fps_source": fps_source}

    output = plan.get("output", {})
    res_string = output.get("resolution", "1080p")
    if isinstance(res_string, str) and res_string in RESOLUTION_PRESETS:
        width, height = RESOLUTION_PRESETS[res_string]
    else:
        width, height = RESOLUTION_PRESETS["1080p"]
    ratio = output.get("ratio", "16:9")
    fps_source = int(output.get("fps_source", DEFAULT_SOURCE_FPS))
    return {"width": width, "height": height, "ratio": ratio, "fps_source": fps_source}


# =============================================================================
# PILIER 3 — ENCODING PRESETS
# =============================================================================

ENCODING_PRESETS: Dict[str, dict] = {
    "distribution": {
        "description": "YouTube/TikTok — AV1 optimisé streaming",
        "codec": "libsvtav1",
        "crf": 30,
        "preset": 6,
        "pix_fmt": "yuv420p10le",
        "audio_codec": "aac",
        "audio_bitrate": "320k",
        "container": ".mp4",
        "extra_params": [],
        "weight_target_60s": (200, 400),
    },
    "distribution_h265": {
        "description": "Fallback H.265 — tune animation pour Roblox",
        "codec": "libx265",
        "crf": 20,
        "preset": "slow",
        "tune": "animation",
        "pix_fmt": "yuv420p",
        "audio_codec": "aac",
        "audio_bitrate": "320k",
        "container": ".mp4",
        "extra_params": ["-tag:v", "hvc1"],
        "weight_target_60s": (350, 600),
    },
    "master": {
        "description": "Archive ProRes 422 HQ — lossless pour réédition",
        "codec": "prores_ks",
        "profile": 3,
        "pix_fmt": "yuv422p10le",
        "audio_codec": "pcm_s24le",
        "audio_bitrate": None,
        "container": ".mov",
        "extra_params": [],
        "weight_target_60s": (4000, 8000),
    },
}

VALID_PRESETS: List[str] = list(ENCODING_PRESETS.keys())
DEFAULT_PRESET: str = "distribution"
FALLBACK_CHAIN: List[str] = ["distribution", "distribution_h265"]


# =============================================================================
# PILIER 4 — RIFE CONFIGURATION
# =============================================================================

RIFE_CHUNK_SECONDS: int = 10
RIFE_VRAM_BUDGET_GB: int = 10

RIFE_FALLBACK_CHAIN: List[str] = ["rife_model", "ffmpeg_minterpolate", "frame_duplication"]

CHECKPOINT_FILENAME: str = "carrier_checkpoint.json"


def calculate_rife_params(source_fps: int, target_fps: int) -> dict:
    """Calcule le multiplicateur et l'exposant RIFE.

    Ex: 30fps → 120fps = multiplier 4, exp 2 (2^2 = 4)
    Retourne {"multiplier": int, "exp": int, "source_fps": int, "target_fps": int}
    """
    if source_fps <= 0:
        raise ValueError(f"source_fps doit être > 0, reçu {source_fps}")
    if target_fps <= 0:
        raise ValueError(f"target_fps doit être > 0, reçu {target_fps}")
    if target_fps < source_fps:
        raise ValueError(f"target_fps ({target_fps}) < source_fps ({source_fps})")

    multiplier = target_fps // source_fps
    if multiplier < 1:
        multiplier = 1

    exp = 0
    while (2 ** exp) < multiplier:
        exp += 1

    return {
        "multiplier": multiplier,
        "exp": exp,
        "source_fps": source_fps,
        "target_fps": target_fps,
    }


# =============================================================================
# PILIER 5 — UPSCALE CONFIGURATION
# =============================================================================

UPSCALE_MODELS: Dict[str, dict] = {
    "realesrgan_x4": {
        "filename": "realesr-general-x4v3.pth",
        "scale": 4,
        "description": "Real-ESRGAN x4 general purpose",
    },
    "realesrgan_x4plus": {
        "filename": "RealESRGAN_x4plus.pth",
        "scale": 4,
        "description": "Real-ESRGAN x4+ (meilleure qualité)",
    },
}

UPSCALE_FALLBACK_CHAIN: List[str] = ["realesrgan", "ffmpeg_lanczos"]


# =============================================================================
# PILIER 6 — VALIDATION + SELF_TEST
# =============================================================================

class CarrierSchema:
    """Bible du Vaisseau-Mère — encapsule les 6 piliers."""

    def __init__(self) -> None:
        self.encoding_presets: Dict[str, dict] = {k: dict(v) for k, v in ENCODING_PRESETS.items()}
        self.valid_presets: List[str] = list(VALID_PRESETS)
        self.valid_ratios: List[str] = list(VALID_RATIOS)
        self.resolution_presets: Dict[str, Tuple[int, int]] = dict(RESOLUTION_PRESETS)
        self.pipeline_stages: List[str] = list(PIPELINE_STAGES)

    # -----------------------------------------------------------------
    # Validation — Ratio
    # -----------------------------------------------------------------

    def validate_ratio(self, width: int, height: int, expected_ratio: str) -> Tuple[bool, str]:
        """Vérifie que width/height correspond au ratio attendu.
        Tolérance: ±1 pixel pour les arrondis."""
        if ":" not in expected_ratio:
            return (False, f"Format de ratio invalide : '{expected_ratio}'")
        rw, rh = expected_ratio.split(":")
        rw, rh = int(rw), int(rh)

        actual = width * rh
        expected = height * rw
        if abs(actual - expected) <= max(rw, rh):
            return (True, "")

        if height != 0:
            g = math.gcd(width, height)
            got_w, got_h = width // g, height // g
            got_ratio = f"{got_w}:{got_h}"
        else:
            got_ratio = "N/A"
        return (False, f"Ratio mismatch: got {got_ratio}, expected {expected_ratio}")

    # -----------------------------------------------------------------
    # Validation — CRF
    # -----------------------------------------------------------------

    def validate_crf(self, value: int, preset: str = None, codec: str = None) -> Tuple[bool, str]:
        """Vérifie que le CRF est dans le range du codec.
        Si preset fourni, le codec est déduit du preset.
        Si ni preset ni codec, utilise 'default'."""
        if preset and preset in ENCODING_PRESETS:
            codec = ENCODING_PRESETS[preset].get("codec", codec)
        if not codec or codec not in CRF_RANGES:
            codec = "default"
        crf_min, crf_max = CRF_RANGES[codec]
        if value < crf_min or value > crf_max:
            return (False, f"CRF {value} hors range [{crf_min}, {crf_max}] pour codec {codec}")
        if preset and preset in ENCODING_PRESETS:
            expected_crf = ENCODING_PRESETS[preset].get("crf")
            if expected_crf is not None and value != expected_crf:
                return (True, f"CRF {value} accepté mais diffère du preset '{preset}' (défaut {expected_crf})")
        return (True, "")

    # -----------------------------------------------------------------
    # Validation — Output Weight
    # -----------------------------------------------------------------

    def validate_output_weight(self, file_bytes: int, duration_seconds: float, preset: str) -> Tuple[bool, str]:
        """Vérifie que le poids du fichier est dans la cible pour le preset donné.
        Normalise à 60s pour comparer."""
        if preset not in ENCODING_PRESETS:
            return (False, f"Preset inconnu : '{preset}'")
        if duration_seconds <= 0:
            return (False, "Durée invalide (≤ 0)")
        target = ENCODING_PRESETS[preset].get("weight_target_60s")
        if not target:
            return (True, "Pas de cible de poids pour ce preset")

        file_mb = file_bytes / (1024 * 1024)
        normalized_mb = file_mb * (60.0 / duration_seconds)
        lo, hi = target

        if normalized_mb < lo:
            return (False, f"Fichier trop léger : {normalized_mb:.1f} MB/60s (cible {lo}-{hi} MB)")
        if normalized_mb > hi:
            return (False, f"Fichier trop lourd : {normalized_mb:.1f} MB/60s (cible {lo}-{hi} MB)")
        return (True, "")

    # -----------------------------------------------------------------
    # Validation — Checksum Resolution
    # -----------------------------------------------------------------

    def checksum_resolution(self, output_width: int, output_height: int,
                            format_width: int, format_height: int) -> Tuple[bool, str]:
        """Vérifie que la résolution de sortie correspond à la résolution attendue."""
        if output_width == format_width and output_height == format_height:
            return (True, "")
        return (False, f"Resolution mismatch: output {output_width}x{output_height} != attendu {format_width}x{format_height}")

    # -----------------------------------------------------------------
    # Validation — Preset Name
    # -----------------------------------------------------------------

    def validate_preset(self, name: str) -> Tuple[bool, str]:
        """Valide un nom de preset d'encodage."""
        if name in self.encoding_presets:
            return (True, "")
        return (False, f"Preset inconnu : '{name}'. Valides : {self.valid_presets}")

    # -----------------------------------------------------------------
    # Encoding Config
    # -----------------------------------------------------------------

    def get_encoding_config(self, preset_name: str) -> dict:
        """Retourne la config complète pour un preset."""
        valid, msg = self.validate_preset(preset_name)
        if not valid:
            raise ValueError(msg)
        return dict(self.encoding_presets[preset_name])

    # -----------------------------------------------------------------
    # Fallback Preset
    # -----------------------------------------------------------------

    def get_fallback_preset(self, preset_name: str) -> Optional[str]:
        """Retourne le preset fallback si le codec n'est pas disponible."""
        if preset_name not in FALLBACK_CHAIN:
            return None
        idx = FALLBACK_CHAIN.index(preset_name)
        if idx + 1 < len(FALLBACK_CHAIN):
            return FALLBACK_CHAIN[idx + 1]
        return None

    # -----------------------------------------------------------------
    # Self Test
    # -----------------------------------------------------------------

    def self_test(self) -> Tuple[int, int]:
        """Exécute les tests de validation. Retourne (passed, total)."""
        passed = 0
        total = 12

        print("═══════════════════════════════════════════════════")
        print("   CARRIER SCHEMA — SELF TEST")
        print("═══════════════════════════════════════════════════")
        print()

        # --- TEST 1 : Encoding presets completeness ---
        t1_ok = True
        required_keys = {"codec", "pix_fmt", "audio_codec", "audio_bitrate", "container", "extra_params", "weight_target_60s"}
        for name, preset in self.encoding_presets.items():
            missing = required_keys - set(preset.keys())
            if missing:
                t1_ok = False
                print(f"  ERREUR preset '{name}': clés manquantes = {sorted(missing)}")
        if t1_ok:
            n_fields = min(len(p) for p in self.encoding_presets.values())
            passed += 1
            print(f"[TEST 1]  Encoding presets completeness ... ✓ ({len(self.encoding_presets)} presets, {n_fields} champs chacun)")
        else:
            print("[TEST 1]  Encoding presets completeness ... ✗")

        # --- TEST 2 : VALID_RATIOS contient les 4 ratios requis ---
        t2_ok = True
        expected_ratios = {"9:16", "16:9", "4:3", "1:1"}
        actual_ratios = set(self.valid_ratios)
        if expected_ratios != actual_ratios:
            t2_ok = False
            print(f"  ERREUR VALID_RATIOS = {self.valid_ratios}, attendu {sorted(expected_ratios)}")
        if t2_ok:
            passed += 1
            print(f"[TEST 2]  VALID_RATIOS ................... ✓ ({', '.join(self.valid_ratios)})")
        else:
            print("[TEST 2]  VALID_RATIOS ................... ✗")

        # --- TEST 3 : CRF_RANGES valides (par codec) ---
        t3_ok = True
        for codec_name, (crf_min, crf_max) in CRF_RANGES.items():
            if crf_min >= crf_max:
                t3_ok = False
                print(f"  ERREUR CRF_RANGES[{codec_name}] min ({crf_min}) >= max ({crf_max})")
            if crf_min < 0:
                t3_ok = False
                print(f"  ERREUR CRF_RANGES[{codec_name}] min ({crf_min}) < 0")
            if crf_max > 63:
                t3_ok = False
                print(f"  ERREUR CRF_RANGES[{codec_name}] max ({crf_max}) > 63")
        if t3_ok:
            ranges_str = ", ".join(f"{k}:{v[0]}-{v[1]}" for k, v in CRF_RANGES.items())
            passed += 1
            print(f"[TEST 3]  CRF_RANGES per-codec ........... ✓ ({ranges_str})")
        else:
            print("[TEST 3]  CRF_RANGES per-codec ........... ✗")

        # --- TEST 4 : parse_format_metadata V2 ---
        t4_ok = True
        v2_plan = {
            "production_plan": {
                "format": {
                    "resolution": [1080, 1920],
                    "ratio": "9:16",
                    "fps_source": 30,
                }
            }
        }
        meta = parse_format_metadata(v2_plan)
        if meta["width"] != 1920:
            t4_ok = False
            print(f"  ERREUR V2 width = {meta['width']} (attendu 1920)")
        if meta["height"] != 1080:
            t4_ok = False
            print(f"  ERREUR V2 height = {meta['height']} (attendu 1080)")
        if meta["ratio"] != "9:16":
            t4_ok = False
            print(f"  ERREUR V2 ratio = {meta['ratio']} (attendu 9:16)")
        if meta["fps_source"] != 30:
            t4_ok = False
            print(f"  ERREUR V2 fps_source = {meta['fps_source']} (attendu 30)")
        if t4_ok:
            passed += 1
            print(f"[TEST 4]  parse_format_metadata V2 ....... ✓ ([1080,1920] → {meta['width']}x{meta['height']}, {meta['ratio']})")
        else:
            print("[TEST 4]  parse_format_metadata V2 ....... ✗")

        # --- TEST 5 : parse_format_metadata legacy ---
        t5_ok = True
        legacy_plan = {"output": {"resolution": "4K"}}
        meta_leg = parse_format_metadata(legacy_plan)
        if meta_leg["width"] != 3840 or meta_leg["height"] != 2160:
            t5_ok = False
            print(f"  ERREUR legacy résolution = {meta_leg['width']}x{meta_leg['height']} (attendu 3840x2160)")
        if t5_ok:
            passed += 1
            print(f"[TEST 5]  parse_format_metadata legacy ... ✓ ('4K' → {meta_leg['width']}x{meta_leg['height']})")
        else:
            print("[TEST 5]  parse_format_metadata legacy ... ✗")

        # --- TEST 6 : validate_ratio ---
        t6_ok = True
        ok_916, _ = self.validate_ratio(1080, 1920, "9:16")
        if not ok_916:
            t6_ok = False
            print("  ERREUR validate_ratio(1080, 1920, '9:16') devrait être True")
        ok_169, _ = self.validate_ratio(1920, 1080, "16:9")
        if not ok_169:
            t6_ok = False
            print("  ERREUR validate_ratio(1920, 1080, '16:9') devrait être True")
        ok_bad, msg_bad = self.validate_ratio(1920, 1080, "9:16")
        if ok_bad:
            t6_ok = False
            print("  ERREUR validate_ratio(1920, 1080, '9:16') devrait être False (mismatch)")
        if t6_ok:
            passed += 1
            print("[TEST 6]  validate_ratio ................. ✓ (9:16 ✓, 16:9 ✓, mismatch ✗)")
        else:
            print("[TEST 6]  validate_ratio ................. ✗")

        # --- TEST 7 : validate_crf (per-codec ranges) ---
        t7_ok = True
        ok_av1, _ = self.validate_crf(30, preset="distribution")
        if not ok_av1:
            t7_ok = False
            print("  ERREUR CRF 30 preset=distribution (AV1) devrait être accepté")
        ok_h265, _ = self.validate_crf(20, preset="distribution_h265")
        if not ok_h265:
            t7_ok = False
            print("  ERREUR CRF 20 preset=distribution_h265 devrait être accepté")
        ok_5, _ = self.validate_crf(5)
        if ok_5:
            t7_ok = False
            print("  ERREUR CRF 5 (default) devrait être rejeté")
        ok_50, _ = self.validate_crf(50)
        if ok_50:
            t7_ok = False
            print("  ERREUR CRF 50 (default) devrait être rejeté")
        if t7_ok:
            passed += 1
            print("[TEST 7]  validate_crf ................... ✓ (AV1:30 ✓, H265:20 ✓, 5 ✗, 50 ✗)")
        else:
            print("[TEST 7]  validate_crf ................... ✗")

        # --- TEST 8 : validate_output_weight ---
        t8_ok = True
        ok_in, _ = self.validate_output_weight(300 * 1024 * 1024, 60.0, "distribution")
        if not ok_in:
            t8_ok = False
            print("  ERREUR 300MB/60s devrait être dans la cible distribution (200-400)")
        ok_low, _ = self.validate_output_weight(50 * 1024 * 1024, 60.0, "distribution")
        if ok_low:
            t8_ok = False
            print("  ERREUR 50MB/60s devrait être hors cible distribution")
        ok_hi, _ = self.validate_output_weight(800 * 1024 * 1024, 60.0, "distribution")
        if ok_hi:
            t8_ok = False
            print("  ERREUR 800MB/60s devrait être hors cible distribution")
        if t8_ok:
            passed += 1
            print("[TEST 8]  validate_output_weight ......... ✓ (300MB ✓, 50MB ✗, 800MB ✗)")
        else:
            print("[TEST 8]  validate_output_weight ......... ✗")

        # --- TEST 9 : checksum_resolution ---
        t9_ok = True
        ok_match, _ = self.checksum_resolution(3840, 2160, 3840, 2160)
        if not ok_match:
            t9_ok = False
            print("  ERREUR 3840x2160 == 3840x2160 devrait matcher")
        ok_mis, _ = self.checksum_resolution(1920, 1080, 3840, 2160)
        if ok_mis:
            t9_ok = False
            print("  ERREUR 1920x1080 != 3840x2160 devrait être un mismatch")
        if t9_ok:
            passed += 1
            print("[TEST 9]  checksum_resolution ............ ✓ (match ✓, mismatch ✗)")
        else:
            print("[TEST 9]  checksum_resolution ............ ✗")

        # --- TEST 10 : validate_preset rejette les inconnus ---
        t10_ok = True
        ok_good, _ = self.validate_preset("distribution")
        if not ok_good:
            t10_ok = False
            print("  ERREUR preset 'distribution' devrait être accepté")
        ok_bad, _ = self.validate_preset("inexistant")
        if ok_bad:
            t10_ok = False
            print("  ERREUR preset 'inexistant' devrait être rejeté")
        if t10_ok:
            passed += 1
            print("[TEST 10] validate_preset ................ ✓ (distribution ✓, inexistant ✗)")
        else:
            print("[TEST 10] validate_preset ................ ✗")

        # --- TEST 11 : calculate_rife_params ---
        t11_ok = True
        params = calculate_rife_params(30, 120)
        if params["multiplier"] != 4:
            t11_ok = False
            print(f"  ERREUR multiplier = {params['multiplier']} (attendu 4)")
        if params["exp"] != 2:
            t11_ok = False
            print(f"  ERREUR exp = {params['exp']} (attendu 2)")
        params_2x = calculate_rife_params(30, 60)
        if params_2x["multiplier"] != 2 or params_2x["exp"] != 1:
            t11_ok = False
            print(f"  ERREUR 30→60: mult={params_2x['multiplier']} exp={params_2x['exp']} (attendu 2, 1)")
        if t11_ok:
            passed += 1
            print(f"[TEST 11] calculate_rife_params .......... ✓ (30→120: x{params['multiplier']} exp={params['exp']})")
        else:
            print("[TEST 11] calculate_rife_params .......... ✗")

        # --- TEST 12 : Fallback chains non-vides ---
        t12_ok = True
        if not FALLBACK_CHAIN:
            t12_ok = False
            print("  ERREUR FALLBACK_CHAIN est vide")
        if not RIFE_FALLBACK_CHAIN:
            t12_ok = False
            print("  ERREUR RIFE_FALLBACK_CHAIN est vide")
        if not UPSCALE_FALLBACK_CHAIN:
            t12_ok = False
            print("  ERREUR UPSCALE_FALLBACK_CHAIN est vide")
        fb = self.get_fallback_preset("distribution")
        if fb != "distribution_h265":
            t12_ok = False
            print(f"  ERREUR fallback('distribution') = '{fb}' (attendu 'distribution_h265')")
        if t12_ok:
            passed += 1
            print(f"[TEST 12] Fallback chains ................ ✓ (encode: {len(FALLBACK_CHAIN)}, rife: {len(RIFE_FALLBACK_CHAIN)}, upscale: {len(UPSCALE_FALLBACK_CHAIN)})")
        else:
            print("[TEST 12] Fallback chains ................ ✗")

        print()
        print("═══════════════════════════════════════════════════")
        print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
        print("═══════════════════════════════════════════════════")

        return (passed, total)


# =============================================================================
# RAPPORT DE VALIDATION — exécution standalone
# =============================================================================

if __name__ == "__main__":
    schema = CarrierSchema()
    schema.self_test()
