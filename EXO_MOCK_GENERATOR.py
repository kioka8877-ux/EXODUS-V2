#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              EXODUS V2 — MOCK GENERATOR (Le Simulacre)                       ║
║       Génère des données mock alignées sur le MANIFEST                       ║
║       pour tester le pipeline U00→U06 sans Gemini API.                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Usage:                                                                      ║
║    python EXO_MOCK_GENERATOR.py --drive-root /content/drive/MyDrive/EXODUS_V2║
║    python EXO_MOCK_GENERATOR.py --drive-root ... --scenario brookhaven       ║
║    python EXO_MOCK_GENERATOR.py --drive-root ... --duration 15 --fps 30      ║
║    python EXO_MOCK_GENERATOR.py --drive-root ... --deploy-only               ║
║    python EXO_MOCK_GENERATOR.py --drive-root ... --u00-only                  ║
║    python EXO_MOCK_GENERATOR.py --drive-root ... --no-depth                  ║
║                                                                              ║
║  Zéro dépendance externe — Python standard library uniquement.               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import struct
import zlib
import os
import sys
import argparse
import hashlib
import shutil
import random
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Import locaux EXODUS V2
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from EXO_MARSHAL import MANIFEST, TRANSFER_ROUTES
from phantom_link import create_link


# ═══════════════════════════════════════════════════════════════════════════════
# SCÉNARIOS PRÉCONFIGURÉS
# ═══════════════════════════════════════════════════════════════════════════════

SCENARIOS = {
    "brookhaven": {
        "description": "Scène urbaine Brookhaven — 2 personnages, combat",
        "duration": 10,
        "fps": 30,
        "resolution": "1080p",
        "ratio": "9:16",
        "characters": ["bacon_hair", "noob"],
        "environment": "brookhaven_street",
        "complexity": 5,
    },
    "baseplate": {
        "description": "Scène simple baseplate — 1 personnage, idle",
        "duration": 5,
        "fps": 30,
        "resolution": "1080p",
        "ratio": "16:9",
        "characters": ["bacon_hair"],
        "environment": "classic_baseplate",
        "complexity": 2,
    },
    "cinematic": {
        "description": "Cinématique longue — 3 personnages, multi-scènes",
        "duration": 30,
        "fps": 30,
        "resolution": "1080p",
        "ratio": "9:16",
        "characters": ["bacon_hair", "noob", "builderman"],
        "environment": "grass_terrain",
        "complexity": 8,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEURS BINAIRES (zéro dépendance)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_wav(path, duration_s=10, sample_rate=44100, bits=16):
    """Génère un WAV silence valide de la bonne durée."""
    num_samples = int(sample_rate * duration_s)
    data_size = num_samples * (bits // 8)

    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate,
                            sample_rate * bits // 8, bits // 8, bits))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(b"\x00" * data_size)


def generate_depth_png(path, width=128, height=128, frame_index=0, total_frames=300):
    """Génère un PNG grayscale gradient + bruit (simule depth map, >1KB)."""
    rng = random.Random(frame_index)
    shift = int((frame_index / max(total_frames, 1)) * 60)
    rows = []
    for y in range(height):
        row = b"\x00"
        for x in range(width):
            base = int((y / height) * 200) + shift
            noise = rng.randint(-15, 15)
            val = min(255, max(0, base + noise))
            row += bytes([val])
        rows.append(row)

    raw = b"".join(rows)

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))


def generate_graded_png(path, width=128, height=128, frame_index=0, total_frames=10):
    """Génère un PNG RGB gradient + bruit (simule frame gradée, >1KB)."""
    rng = random.Random(frame_index + 10000)
    shift = int((frame_index / max(total_frames, 1)) * 40)
    rows = []
    for y in range(height):
        row = b"\x00"
        for x in range(width):
            nr, ng, nb = rng.randint(-10, 10), rng.randint(-10, 10), rng.randint(-10, 10)
            r = min(255, max(0, int((y / height) * 200) + shift + 40 + nr))
            g = min(255, max(0, int((x / width) * 160) + shift + ng))
            b_val = min(255, max(0, 80 + shift + nb))
            row += bytes([r, g, b_val])
        rows.append(row)

    raw = b"".join(rows)

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))


def generate_stub(path, size, magic=None):
    """Génère un fichier stub binaire de la taille donnée avec magic header optionnel."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        if magic:
            f.write(magic)
            remaining = size - len(magic)
            if remaining > 0:
                f.write(os.urandom(remaining))
        else:
            f.write(os.urandom(size))


def format_size(size_bytes):
    """Formatage taille lisible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 1 — MOCK U00 (Cortex HQ outputs)
# ═══════════════════════════════════════════════════════════════════════════════

def build_production_plan(scenario, duration, fps, now_iso):
    """Construit le PRODUCTION_PLAN.JSON conforme au dispatch_master_json()."""
    sc = SCENARIOS[scenario]
    characters = sc["characters"]
    env_id = sc["environment"]
    ratio = sc["ratio"]
    complexity = sc["complexity"]

    scene_duration = duration / max(len(characters), 1)
    scenes = []

    if scenario == "brookhaven":
        scenes = [
            {
                "scene_id": 1,
                "timecode_start": 0.0,
                "timecode_end": duration / 2,
                "description": "Personnage marche dans la rue",
                "characters": [
                    {"character_id": "bacon_hair", "role": "protagonist", "actions": ["walk", "idle"]}
                ],
                "props": [
                    {"prop_id": "linked_sword", "quantity": 1, "interaction": "held"}
                ],
                "environment": {"environment_id": env_id, "modifications": []},
                "camera": {"style_id": "tracking", "movements": ["tracking_forward", "slight_pan_left"]},
                "lighting": {"preset_id": "daylight", "adjustments": []},
                "audio": {"music_id": "none", "sfx": [], "ambient_id": "city_ambient"},
            },
            {
                "scene_id": 2,
                "timecode_start": duration / 2,
                "timecode_end": duration,
                "description": "Confrontation avec antagoniste",
                "characters": [
                    {"character_id": "bacon_hair", "role": "protagonist", "actions": ["run", "sword_slash"]},
                    {"character_id": "noob", "role": "antagonist", "actions": ["idle", "death"]},
                ],
                "props": [
                    {"prop_id": "linked_sword", "quantity": 1, "interaction": "held"}
                ],
                "environment": {"environment_id": env_id, "modifications": []},
                "camera": {"style_id": "follow", "movements": ["tracking du protagoniste"]},
                "lighting": {"preset_id": "dramatic", "adjustments": []},
                "audio": {"music_id": "action_electronic", "sfx": ["sword_hit", "oof"], "ambient_id": "none"},
            },
        ]
    elif scenario == "baseplate":
        scenes = [
            {
                "scene_id": 1,
                "timecode_start": 0.0,
                "timecode_end": duration,
                "description": "Personnage idle sur baseplate classique",
                "characters": [
                    {"character_id": "bacon_hair", "role": "protagonist", "actions": ["idle", "look_around"]}
                ],
                "props": [],
                "environment": {"environment_id": env_id, "modifications": []},
                "camera": {"style_id": "orbit", "movements": ["slow_orbit_360"]},
                "lighting": {"preset_id": "studio", "adjustments": []},
                "audio": {"music_id": "calm_ambient", "sfx": [], "ambient_id": "wind_light"},
            }
        ]
    elif scenario == "cinematic":
        t_step = duration / 3
        scenes = [
            {
                "scene_id": 1,
                "timecode_start": 0.0,
                "timecode_end": t_step,
                "description": "Introduction — trois personnages se retrouvent",
                "characters": [
                    {"character_id": c, "role": r, "actions": ["walk", "idle"]}
                    for c, r in zip(characters, ["protagonist", "ally", "mentor"])
                ],
                "props": [],
                "environment": {"environment_id": env_id, "modifications": []},
                "camera": {"style_id": "crane", "movements": ["crane_down", "push_in"]},
                "lighting": {"preset_id": "golden_hour", "adjustments": []},
                "audio": {"music_id": "epic_orchestral", "sfx": [], "ambient_id": "nature_ambient"},
            },
            {
                "scene_id": 2,
                "timecode_start": t_step,
                "timecode_end": t_step * 2,
                "description": "Confrontation — combat à trois",
                "characters": [
                    {"character_id": "bacon_hair", "role": "protagonist", "actions": ["run", "sword_slash"]},
                    {"character_id": "noob", "role": "antagonist", "actions": ["attack", "dodge"]},
                    {"character_id": "builderman", "role": "ally", "actions": ["shield", "support"]},
                ],
                "props": [
                    {"prop_id": "linked_sword", "quantity": 1, "interaction": "held"},
                    {"prop_id": "shield", "quantity": 1, "interaction": "held"},
                ],
                "environment": {"environment_id": env_id, "modifications": ["destroyed_terrain"]},
                "camera": {"style_id": "handheld", "movements": ["shake_light", "tracking_fast"]},
                "lighting": {"preset_id": "dramatic", "adjustments": ["rim_light_strong"]},
                "audio": {"music_id": "action_electronic", "sfx": ["sword_hit", "explosion", "oof"], "ambient_id": "none"},
            },
            {
                "scene_id": 3,
                "timecode_start": t_step * 2,
                "timecode_end": duration,
                "description": "Résolution — victoire et départ",
                "characters": [
                    {"character_id": "bacon_hair", "role": "protagonist", "actions": ["victory_pose", "walk_away"]},
                    {"character_id": "builderman", "role": "ally", "actions": ["wave", "idle"]},
                ],
                "props": [],
                "environment": {"environment_id": env_id, "modifications": []},
                "camera": {"style_id": "dolly", "movements": ["dolly_out", "tilt_up"]},
                "lighting": {"preset_id": "sunset", "adjustments": []},
                "audio": {"music_id": "emotional_piano", "sfx": [], "ambient_id": "wind_light"},
            },
        ]

    res_hw = [1080, 1920] if ratio == "9:16" else [1920, 1080]

    plan = {
        "schema_version": "2.0",
        "generated_at": now_iso,
        "metadata": {
            "source_video": f"mock_{scenario}.mp4",
            "duration_seconds": duration,
            "fps": fps,
            "resolution": sc["resolution"],
            "analysis_date": now_iso,
            "cortex_version": "2.0.0-mock",
        },
        "scenes": scenes,
        "production_notes": {
            "complexity_score": complexity,
            "estimated_render_hours": max(1, int(duration / 5)),
            "special_requirements": ["[MOCK] Données simulées — aucune analyse Gemini"],
            "warnings": ["Mode simulation — données générées sans Gemini API"],
            "requires_u02": True,
        },
        "format": {
            "resolution": res_hw,
            "ratio": ratio,
            "fps_source": fps,
            "duration_seconds": duration,
        },
        "output": {
            "resolution": sc["resolution"],
            "ratio": ratio,
            "fps_source": fps,
        },
        "flags": {
            "all_motors_ok": False,
            "partial_failure": ["depth_anything", "sam_segmentation"],
            "manual_review_required": False,
            "warnings": ["[MOCK] Moteurs GPU simulés"],
        },
    }
    return plan


def build_facial_animation(scenario, duration):
    """Construit facial_animation.json avec segments par personnage."""
    sc = SCENARIOS[scenario]
    protagonist = sc["characters"][0]
    seq_id = f"MOCK_{scenario.upper()}_001"

    t_third = duration / 3.0
    segments = [
        {
            "time_start": 0.0,
            "time_end": round(t_third, 1),
            "character_id": protagonist,
            "expression": "neutral",
            "intensity": 0.3,
            "eyes": "focused_forward",
            "mouth": "closed_tight",
            "apex_time": round(t_third / 2, 2),
            "low_visibility": False,
        },
        {
            "time_start": round(t_third, 1),
            "time_end": round(t_third * 2, 1),
            "character_id": protagonist,
            "expression": "joy",
            "intensity": 0.7,
            "eyes": "wide_open",
            "mouth": "smiling",
            "apex_time": round(t_third * 1.5, 2),
            "low_visibility": False,
        },
        {
            "time_start": round(t_third * 2, 1),
            "time_end": duration,
            "character_id": protagonist,
            "expression": "determined",
            "intensity": 0.6,
            "eyes": "narrowed",
            "mouth": "closed_tight",
            "apex_time": round(t_third * 2.5, 2),
            "low_visibility": False,
        },
    ]

    return {"sequence_id": seq_id, "segments": segments}


def build_semantic_masks(fps, duration):
    """Construit semantic_masks.json pour U03."""
    total_frames = int(fps * duration)
    return {
        "masks": [
            {
                "keyframe_index": 0,
                "timestamp": 0.0,
                "segments": {
                    "road": {"bbox": [0, 800, 1080, 1200], "area": 0.3, "confidence": 0.95},
                    "sidewalk": {"bbox": [0, 700, 200, 900], "area": 0.1, "confidence": 0.88},
                    "building": {"bbox": [200, 0, 1080, 700], "area": 0.5, "confidence": 0.92},
                    "sky": {"bbox": [0, 0, 1080, 400], "area": 0.2, "confidence": 0.97},
                },
            }
        ],
        "categories": ["road", "sidewalk", "building", "sky", "vegetation"],
        "model": "sam_vit_h_mock",
        "frame_count": total_frames,
    }


def build_camera_fov(scenario, fps):
    """Construit camera_fov_ratio.json pour U04."""
    sc = SCENARIOS[scenario]
    ratio = sc["ratio"]
    res = [1080, 1920] if ratio == "9:16" else [1920, 1080]
    return {
        "resolution": res,
        "ratio": ratio,
        "fps_source": fps,
        "fov_estimate": 75.0,
        "source_video": f"mock_{scenario}.mp4",
    }


def build_motion_prompt(scenario, duration):
    """Construit motion_synthesis_prompt.txt."""
    sc = SCENARIOS[scenario]
    prompts = {
        "brookhaven": "Un personnage marche dans la rue puis court vers un adversaire et effectue une attaque à l'épée.",
        "baseplate": "Un personnage est debout sur une baseplate et regarde autour de lui calmement.",
        "cinematic": "Trois personnages se retrouvent, combattent ensemble puis le héros part victorieux au coucher du soleil.",
    }
    text = prompts.get(scenario, "Scène Roblox générée automatiquement.")
    text += f"\nDuration: {duration} seconds. Style: dramatic. Ratio: {sc['ratio']}."
    return text


def write_json(path, data):
    """Écrit un fichier JSON indenté."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_u00(drive_root, scenario, duration, fps, skip_depth=False, verbose=False):
    """PHASE 1 — Génération des 7 outputs de U00 (Cortex HQ)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    out_dir = drive_root / MANIFEST["U00"]["folder"] / "OUT_PRODUCTION_PLAN"
    out_dir.mkdir(parents=True, exist_ok=True)
    total_frames = int(fps * duration)

    results = []

    # 1. PRODUCTION_PLAN.JSON
    pp = build_production_plan(scenario, duration, fps, now_iso)
    pp_path = out_dir / "PRODUCTION_PLAN.JSON"
    write_json(pp_path, pp)
    sz = pp_path.stat().st_size
    n_scenes = len(pp["scenes"])
    results.append(("PRODUCTION_PLAN.JSON", sz, f"JSON valide | {n_scenes} scènes"))

    # 2. facial_animation.json
    fa = build_facial_animation(scenario, duration)
    fa_path = out_dir / "facial_animation.json"
    write_json(fa_path, fa)
    sz = fa_path.stat().st_size
    n_seg = len(fa["segments"])
    results.append(("facial_animation.json", sz, f"{n_seg} segments"))

    # 3. semantic_masks.json
    sm = build_semantic_masks(fps, duration)
    sm_path = out_dir / "semantic_masks.json"
    write_json(sm_path, sm)
    sz = sm_path.stat().st_size
    n_cat = len(sm["categories"])
    results.append(("semantic_masks.json", sz, f"{n_cat} catégories"))

    # 4. camera_fov_ratio.json
    cf = build_camera_fov(scenario, fps)
    cf_path = out_dir / "camera_fov_ratio.json"
    write_json(cf_path, cf)
    sz = cf_path.stat().st_size
    results.append(("camera_fov_ratio.json", sz, None))

    # 5. motion_synthesis_prompt.txt
    mp = build_motion_prompt(scenario, duration)
    mp_path = out_dir / "motion_synthesis_prompt.txt"
    mp_path.write_text(mp, encoding="utf-8")
    sz = mp_path.stat().st_size
    results.append(("motion_synthesis_prompt.txt", sz, None))

    # 6. audio_source.wav
    wav_path = out_dir / "audio_source.wav"
    generate_wav(wav_path, duration_s=duration)
    sz = wav_path.stat().st_size
    results.append(("audio_source.wav", sz, f"{duration}s silence"))

    # 7. DEPTH_MAP/*.png
    depth_dir = out_dir / "DEPTH_MAP"
    depth_dir.mkdir(parents=True, exist_ok=True)
    if skip_depth:
        for i in range(min(10, total_frames)):
            generate_depth_png(depth_dir / f"depth_{i:06d}.png",
                               frame_index=i, total_frames=total_frames)
        results.append(("DEPTH_MAP/", None, f"{min(10, total_frames)} frames (--no-depth)"))
    else:
        for i in range(total_frames):
            generate_depth_png(depth_dir / f"depth_{i:06d}.png",
                               frame_index=i, total_frames=total_frames)
        results.append(("DEPTH_MAP/", None, f"{total_frames} frames × 128×128 PNG"))

    # Affichage
    print("\n\U0001f9e0 PHASE 1 — Génération outputs U00 (Cortex HQ)")
    for name, sz, detail in results:
        size_str = f"{format_size(sz):>8s}" if sz else "        "
        detail_str = f" | {detail}" if detail else ""
        print(f"  ✅ {name:<30s} ({size_str}{detail_str})")


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 2 — MOCK U01→U06 (fichiers intermédiaires)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_downstream(drive_root, fps, duration, verbose=False):
    """PHASE 2 — Génération des stubs U01→U06."""
    print("\n⚙️  PHASE 2 — Génération stubs U01→U06")

    # U01/OUT_MOTION_DATA
    u01_out = drive_root / MANIFEST["U01"]["folder"] / "OUT_MOTION_DATA"
    u01_out.mkdir(parents=True, exist_ok=True)
    generate_stub(u01_out / "actor_animated.blend", 55_000, magic=b"BLENDER")
    generate_stub(u01_out / "actor_animated.abc", 12_000)
    print(f"  ✅ U01/OUT_MOTION_DATA           (2 fichiers)")

    # U02/OUT_BAKED_ACTORS
    u02_out = drive_root / MANIFEST["U02"]["folder"] / "OUT_BAKED_ACTORS"
    u02_out.mkdir(parents=True, exist_ok=True)
    generate_stub(u02_out / "actor_equipped.blend", 55_000, magic=b"BLENDER")
    generate_stub(u02_out / "actor_equipped.abc", 12_000)
    print(f"  ✅ U02/OUT_BAKED_ACTORS          (2 fichiers)")

    # U03/OUT_PREMIUM_SCENE
    u03_out = drive_root / MANIFEST["U03"]["folder"] / "OUT_PREMIUM_SCENE"
    u03_out.mkdir(parents=True, exist_ok=True)
    generate_stub(u03_out / "environment.blend", 55_000, magic=b"BLENDER")
    print(f"  ✅ U03/OUT_PREMIUM_SCENE         (1 fichier)")

    # U04/OUT_CAMERA_LOGIC
    u04_out = drive_root / MANIFEST["U04"]["folder"] / "OUT_CAMERA_LOGIC"
    u04_out.mkdir(parents=True, exist_ok=True)
    generate_stub(u04_out / "scene_final.blend", 55_000, magic=b"BLENDER")
    for i in range(10):
        generate_graded_png(u04_out / f"render_{i:04d}.png",
                            frame_index=i, total_frames=10)
    print(f"  ✅ U04/OUT_CAMERA_LOGIC          (1 blend + 10 frames)")

    # U05/OUT_FINAL_FRAMES
    u05_out = drive_root / MANIFEST["U05"]["folder"] / "OUT_FINAL_FRAMES"
    u05_out.mkdir(parents=True, exist_ok=True)
    for i in range(10):
        generate_graded_png(u05_out / f"graded_{i:04d}.png",
                            frame_index=i, total_frames=10)
    print(f"  ✅ U05/OUT_FINAL_FRAMES          (10 frames)")

    # U06/OUT_FINAL_MOVIE
    u06_out = drive_root / MANIFEST["U06"]["folder"] / "OUT_FINAL_MOVIE"
    u06_out.mkdir(parents=True, exist_ok=True)
    generate_stub(u06_out / "final_output.mp4", 12_000)
    print(f"  ✅ U06/OUT_FINAL_MOVIE           (1 MP4 stub)")

    # Fichiers IN spéciaux (pas issus de U00)
    u01_mixamo = drive_root / MANIFEST["U01"]["folder"] / "IN_MIXAMO_BASE"
    u01_mixamo.mkdir(parents=True, exist_ok=True)
    generate_stub(u01_mixamo / "mock_motion.fbx", 12_000)

    u04_video = drive_root / MANIFEST["U04"]["folder"] / "IN_VIDEO_SOURCE"
    u04_video.mkdir(parents=True, exist_ok=True)
    generate_stub(u04_video / f"mock_brookhaven.mp4", 12_000)


# ═══════════════════════════════════════════════════════════════════════════════
# COUCHE 3 — DÉPLOIEMENT PHANTOM LINKS
# ═══════════════════════════════════════════════════════════════════════════════

# Routes de fichiers individuels (U00 dispatche des fichiers spécifiques vers des IN/ différents)
# Les Phantom Links opèrent au niveau dossier : on lie un OUT/ vers un IN/.
# Pour U00, les fichiers sont tous dans OUT_PRODUCTION_PLAN/ mais vont vers plusieurs IN/.
# On utilise des copies directes pour les fichiers individuels de U00, et des Phantom Links
# pour les liaisons dossier-à-dossier des unités U01→U05.

PHANTOM_ROUTES = {
    "U01": {
        "OUT_MOTION_DATA": ["U02/IN_MOTION_DATA"],
    },
    "U02": {
        "OUT_BAKED_ACTORS": ["U04/IN_SCENE_REF"],
    },
    "U03": {
        "OUT_PREMIUM_SCENE": ["U04/IN_SCENE_REF"],
    },
    "U04": {
        "OUT_CAMERA_LOGIC": ["U05/IN_RAW_FRAMES"],
    },
    "U05": {
        "OUT_FINAL_FRAMES": ["U06/IN_ASSEMBLY_KIT"],
    },
}

# Fichiers U00 à copier directement dans les IN/ des frégates cibles
U00_FILE_ROUTES = {
    "U01/IN_CORTEX_JSON": ["PRODUCTION_PLAN.JSON", "facial_animation.json"],
    "U03/IN_CORTEX_JSON": ["PRODUCTION_PLAN.JSON"],
    "U03/IN_MAP_RAW": ["semantic_masks.json"],
    "U04/IN_VIDEO_SOURCE": ["camera_fov_ratio.json"],
    "U06/IN_ASSEMBLY_KIT": ["audio_source.wav"],
}

# Dossiers U00 à linker (depth maps)
U00_DIR_ROUTES = {
    "U03/IN_MAP_RAW": "DEPTH_MAP",
}


def deploy_u00_files(drive_root, verbose=False):
    """Copie les fichiers U00 individuels vers les bons IN/."""
    u00_out = drive_root / MANIFEST["U00"]["folder"] / "OUT_PRODUCTION_PLAN"
    results = []

    for dest_spec, files in U00_FILE_ROUTES.items():
        dest_unit, dest_in = dest_spec.split("/")
        dest_folder = MANIFEST[dest_unit]["folder"]
        dest_dir = drive_root / dest_folder / dest_in
        dest_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        for fname in files:
            src = u00_out / fname
            if src.is_file():
                shutil.copy2(src, dest_dir / fname)
                copied += 1
        results.append((f"U00/OUT → {dest_unit}/{dest_in}", f"{copied} fichier(s) copié(s)"))

    # Depth maps : copier les PNGs dans IN_MAP_RAW
    for dest_spec, subdir in U00_DIR_ROUTES.items():
        dest_unit, dest_in = dest_spec.split("/")
        dest_folder = MANIFEST[dest_unit]["folder"]
        dest_dir = drive_root / dest_folder / dest_in
        dest_dir.mkdir(parents=True, exist_ok=True)

        src_dir = u00_out / subdir
        if src_dir.is_dir():
            pngs = sorted(src_dir.glob("*.png"))
            for p in pngs:
                shutil.copy2(p, dest_dir / p.name)
            results.append((f"U00/OUT → {dest_unit}/{dest_in}", f"depth + masks ({len(pngs)} PNGs)"))

    return results


def deploy_phantom_links(drive_root, verbose=False):
    """Crée les Phantom Links entre OUT/ et IN/ (U01→U05)."""
    results = []

    for src_unit, routes in PHANTOM_ROUTES.items():
        src_folder = MANIFEST[src_unit]["folder"]
        for out_subfolder, destinations in routes.items():
            source_dir = drive_root / src_folder / out_subfolder

            if not source_dir.is_dir():
                continue

            for dest in destinations:
                dest_unit, dest_in = dest.split("/")
                dest_folder = MANIFEST[dest_unit]["folder"]
                target_dir = drive_root / dest_folder / dest_in
                target_dir.mkdir(parents=True, exist_ok=True)

                create_link(str(source_dir), str(target_dir))

                n_files = len([f for f in source_dir.iterdir() if f.is_file()])
                results.append((f"{src_unit}/OUT → {dest_unit}/{dest_in}", f"{n_files} fichier(s) linké(s)"))

    return results


def deploy_all(drive_root, verbose=False):
    """PHASE 3 — Déploiement complet (copies U00 + Phantom Links U01→U05)."""
    print("\n\U0001f517 PHASE 3 — Déploiement Phantom Links")

    u00_results = deploy_u00_files(drive_root, verbose)
    for label, detail in u00_results:
        print(f"  ✅ {label:<35s} ({detail})")

    link_results = deploy_phantom_links(drive_root, verbose)
    for label, detail in link_results:
        print(f"  ✅ {label:<35s} ({detail})")


# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE — CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="EXODUS V2 Mock Generator")
    parser.add_argument("--drive-root", required=True, help="Racine SACRED_ARCHITECTURE")
    parser.add_argument("--scenario", default="brookhaven", choices=SCENARIOS.keys())
    parser.add_argument("--duration", type=float, help="Override durée (secondes)")
    parser.add_argument("--fps", type=int, default=30, help="Override FPS")
    parser.add_argument("--full-chain", action="store_true", default=True,
                        help="Générer mocks U01→U06 aussi")
    parser.add_argument("--u00-only", action="store_true",
                        help="Générer seulement les outputs U00")
    parser.add_argument("--deploy-only", action="store_true",
                        help="Déployer Phantom Links sans regénérer")
    parser.add_argument("--no-depth", action="store_true",
                        help="Skip les 300+ depth map PNGs (rapide)")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    drive_root = Path(args.drive_root)
    scenario = args.scenario
    sc = SCENARIOS[scenario]
    duration = args.duration if args.duration else sc["duration"]
    fps = args.fps

    # Bannière
    print("═" * 67)
    print(f"⚗️  EXODUS V2 — MOCK GENERATOR (Le Simulacre)")
    print(f"    Scénario : {scenario} ({duration}s @ {fps}fps)")
    print("═" * 67)

    if args.deploy_only:
        deploy_all(drive_root, args.verbose)
    elif args.u00_only:
        generate_u00(drive_root, scenario, duration, fps,
                     skip_depth=args.no_depth, verbose=args.verbose)
        deploy_all(drive_root, args.verbose)
    else:
        generate_u00(drive_root, scenario, duration, fps,
                     skip_depth=args.no_depth, verbose=args.verbose)
        generate_downstream(drive_root, fps, duration, verbose=args.verbose)
        deploy_all(drive_root, args.verbose)

    # Bannière finale
    print()
    print("═" * 67)
    print(f"🎉 MOCK DÉPLOYÉ — Prêt pour Fleet Validator")
    print(f"   Lancez: python EXO_FLEET_VALIDATOR.py --drive-root {drive_root}")
    print("═" * 67)


if __name__ == "__main__":
    main()
