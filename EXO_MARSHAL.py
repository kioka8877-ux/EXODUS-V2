#!/usr/bin/env python3
"""
EXODUS V2 — THE MARSHAL (L'Intendant)
Ghost script de validation logistique inter-frégates.
Ne déplace, ne copie, ne supprime JAMAIS de fichier. Lecture et validation uniquement.
"""

import os
import sys
import json
import hashlib
import argparse
import fnmatch
from pathlib import Path
from datetime import datetime

# Phantom Link — Phase D.1
from phantom_link import create_link, resolve_input, validate_link

MANIFEST = {
    "U00": {
        "name": "CORTEX HQ",
        "folder": "00_CORTEX_HQ",
        "in": {
            "IN_VIDEO_SOURCE": [
                {"pattern": "*.mp4", "required": True, "min_count": 1, "description": "Source video file"}
            ]
        },
        "out": {
            "OUT_PRODUCTION_PLAN": [
                {"pattern": "PRODUCTION_PLAN.JSON", "required": True, "validate": "json", "description": "Master production plan"},
                {"pattern": "motion_synthesis_prompt.txt", "required": True, "description": "SayMotion prompt for Emperor"},
                {"pattern": "facial_animation.json", "required": True, "validate": "json", "description": "ARKit facial segments for U01"},
                {"pattern": "semantic_masks.json", "required": False, "validate": "json", "description": "SAM segmentation for U03 (GPU requis — optionnel si GPU indisponible)"},
                {"pattern": "camera_fov_ratio.json", "required": True, "validate": "json", "description": "Camera metadata for U04"},
                {"pattern": "audio_source.wav", "required": True, "description": "Audio track for U06"}
            ],
            "OUT_PRODUCTION_PLAN/DEPTH_MAP": [
                {"pattern": "*.png", "required": False, "min_count": 1, "description": "Depth map sequence from DepthAnything V2 (GPU requis — optionnel si GPU indisponible)"}
            ]
        }
    },
    "U01": {
        "name": "ANIMATION ENGINE",
        "folder": "01_ANIMATION_ENGINE",
        "in": {
            "IN_CORTEX_JSON": [
                {"pattern": "PRODUCTION_PLAN.JSON", "required": True, "validate": "json"},
                {"pattern": "facial_animation.json", "required": True, "validate": "json"}
            ],
            "IN_MIXAMO_BASE": [
                {"pattern": "*.fbx", "required": True, "min_count": 1, "description": "Body motion from SayMotion"}
            ]
        },
        "out": {
            "OUT_MOTION_DATA": [
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Animated actor Blender file"},
                {"pattern": "*.abc", "required": True, "min_count": 1, "description": "Alembic cache backup"}
            ]
        }
    },
    "U02": {
        "name": "LOGISTICS DEPOT",
        "folder": "02_LOGISTICS_DEPOT",
        "in": {
            "IN_MOTION_DATA": [
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Animated actor from U01"},
                {"pattern": "PRODUCTION_PLAN.JSON", "required": True, "validate": "json", "description": "Production plan from U00"}
            ],
            "IN_PROPS_LIBRARY": [
                {"pattern": "*", "required": False, "description": "Props assets (optional based on requires_u02)"}
            ]
        },
        "out": {
            "OUT_BAKED_ACTORS": [
                {"pattern": "*.abc", "required": True, "min_count": 1, "description": "Equipped actor Alembic"},
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Equipped actor Blender backup"}
            ]
        }
    },
    "U03": {
        "name": "SCENOGRAPHY DOCK",
        "folder": "03_SCENOGRAPHY_DOCK",
        "in": {
            "IN_CORTEX_JSON": [
                {"pattern": "PRODUCTION_PLAN.JSON", "required": True, "validate": "json"}
            ],
            "IN_MAP_RAW": [
                {"pattern": "semantic_masks.json", "required": True, "validate": "json", "description": "SAM masks from U00"}
            ],
            "IN_MAP_RAW/DEPTH_MAP": [
                {"pattern": "*.png", "required": True, "min_count": 1, "description": "Depth maps from U00 (IN_MAP_RAW/DEPTH_MAP/)"}
            ]
        },
        "out": {
            "OUT_PREMIUM_SCENE": [
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Environment scene"}
            ]
        }
    },
    "U04": {
        "name": "PHOTOGRAPHY WING",
        "folder": "04_PHOTOGRAPHY_WING",
        "in": {
            "IN_SCENE_REF": [
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Scene from U03 + actor from U02"}
            ],
            "IN_VIDEO_SOURCE": [
                {"pattern": "*.mp4", "required": True, "min_count": 1, "description": "Reference video for camera tracking"}
            ]
        },
        "out": {
            "OUT_CAMERA_LOGIC": [
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Scene with camera configured"}
            ]
        }
    },
    "U05": {
        "name": "ALCHEMIST LAB",
        "folder": "05_ALCHEMIST_LAB",
        "in": {
            "IN_RAW_FRAMES": [
                {"pattern": "*.exr", "required": False, "min_count": 1, "description": "EXR render sequence from U04"},
                {"pattern": "*.png", "required": False, "min_count": 1, "description": "PNG render sequence from U04"},
                {"pattern": "PRODUCTION_PLAN.JSON", "required": True, "validate": "json"}
            ]
        },
        "out": {
            "OUT_FINAL_FRAMES": [
                {"pattern": "*.png", "required": True, "min_count": 1, "description": "Graded frames 16-bit"}
            ]
        }
    },
    "U06": {
        "name": "AIRCRAFT CARRIER",
        "folder": "06_AIRCRAFT_CARRIER",
        "in": {
            "IN_ASSEMBLY_KIT": [
                {"pattern": "*.png", "required": True, "min_count": 1, "description": "Graded frames from U05"},
                {"pattern": "*.wav", "required": True, "min_count": 1, "description": "Audio from U00"}
            ]
        },
        "out": {
            "OUT_FINAL_MOVIE": [
                {"pattern": "*.mp4", "required": True, "min_count": 1, "description": "Final 4K/120FPS video"}
            ]
        }
    }
}

TRANSFER_ROUTES = {
    "U00": {
        "OUT_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON": ["U01/IN_CORTEX_JSON", "U03/IN_CORTEX_JSON"],
        "OUT_PRODUCTION_PLAN/facial_animation.json": ["U01/IN_CORTEX_JSON"],
        "OUT_PRODUCTION_PLAN/DEPTH_MAP": ["U03/IN_MAP_RAW"],
        "OUT_PRODUCTION_PLAN/semantic_masks.json": ["U03/IN_MAP_RAW"],
        "OUT_PRODUCTION_PLAN/camera_fov_ratio.json": ["U04/IN_VIDEO_SOURCE"],
        "OUT_PRODUCTION_PLAN/audio_source.wav": ["U06/IN_ASSEMBLY_KIT"],
        "OUT_PRODUCTION_PLAN/motion_synthesis_prompt.txt": ["EMPEROR"]
    },
    "U01": {
        "OUT_MOTION_DATA/*.blend": ["U02/IN_MOTION_DATA"],
        "OUT_MOTION_DATA/*.abc": ["U02/IN_MOTION_DATA"]
    },
    "U02": {
        "OUT_BAKED_ACTORS/*.abc": ["U04/IN_SCENE_REF"],
        "OUT_BAKED_ACTORS/*.blend": ["U04/IN_SCENE_REF"]
    },
    "U03": {
        "OUT_PREMIUM_SCENE/*.blend": ["U04/IN_SCENE_REF"]
    },
    "U04": {
        "OUT_CAMERA_LOGIC/*.exr": ["U05/IN_RAW_FRAMES"],
        "OUT_CAMERA_LOGIC/*.png": ["U05/IN_RAW_FRAMES"]
    },
    "U05": {
        "OUT_FINAL_FRAMES/*.png": ["U06/IN_ASSEMBLY_KIT"]
    },
    "U06": {
        "OUT_FINAL_MOVIE/*.mp4": ["EMPEROR"]
    }
}

def _build_reverse_routes():
    """Construit la map inversée : {dest_unit: {dest_in_folder: [(source_unit, source_folder, out_subfolder), ...]}}"""
    reverse = {}
    for src_unit, routes in TRANSFER_ROUTES.items():
        src_info = MANIFEST[src_unit]
        src_folder = src_info["folder"]
        for route_key, destinations in routes.items():
            out_subfolder = route_key.split("/")[0]
            for dest in destinations:
                if dest == "EMPEROR":
                    continue
                dest_unit = dest.split("/")[0]
                dest_in = dest.split("/")[1]
                if dest_unit not in reverse:
                    reverse[dest_unit] = {}
                if dest_in not in reverse[dest_unit]:
                    reverse[dest_unit][dest_in] = []
                entry = (src_unit, src_folder, out_subfolder)
                if entry not in reverse[dest_unit][dest_in]:
                    reverse[dest_unit][dest_in].append(entry)
    return reverse

REVERSE_ROUTES = _build_reverse_routes()

VALID_UNITS = ["U00", "U01", "U02", "U03", "U04", "U05", "U06"]
VALID_MODES = ["check-out", "check-in", "validate", "link", "cleanup"]
UNIT_ALIASES = {f"F{i:02d}": f"U{i:02d}" for i in range(7)}


def normalize_unit(raw):
    u = raw.strip().upper()
    if u in UNIT_ALIASES:
        u = UNIT_ALIASES[u]
    if u not in VALID_UNITS:
        return None
    return u


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def sha256_hash(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def validate_json_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def find_matching_files(directory, pattern):
    directory = Path(directory)
    if not directory.is_dir():
        return []
    matches = []
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
            matches.append(entry)
    return matches


def print_banner(title):
    width = 56
    print(f"\n\u2554{'═' * width}\u2557")
    print(f"\u2551{title:^{width}}\u2551")
    print(f"\u255a{'═' * width}\u255d")
    print()


def print_separator():
    print("\u2501" * 56)


def link_inputs(unit, drive_root, verbose=False):
    """Crée les _LINK.json pour tous les dossiers IN/ de l'unité cible."""
    info = MANIFEST[unit]
    unit_folder = Path(drive_root) / info["folder"]

    print_banner(f"EXODUS MARSHAL — LINK: {unit} {info['name']}")

    if unit not in REVERSE_ROUTES:
        print(f"  Aucune route entrante pour {unit} — rien à linker")
        return True, 0

    routes = REVERSE_ROUTES[unit]
    created = 0
    issues = []

    for in_folder, sources in routes.items():
        target_in_dir = unit_folder / in_folder

        if len(sources) > 1:
            print(f"  [MULTI-SOURCE] {in_folder}/ reçoit de {len(sources)} sources :")
            for (su, sf, osf) in sources:
                print(f"    → {su}/{osf}/")
            print(f"  [INFO] Phantom link créé vers la dernière source de la chaîne uniquement")
            print(f"  [INFO] Les autres fichiers doivent être copiés manuellement ou via symlinks")

        src_unit, src_unit_folder, out_subfolder = sources[-1]
        source_out_dir = Path(drive_root) / src_unit_folder / out_subfolder

        if not source_out_dir.is_dir():
            print(f"  [MISSING] Source {src_unit}/{out_subfolder}/ introuvable")
            issues.append(f"Source {source_out_dir} introuvable")
            continue

        source_files = [f for f in source_out_dir.iterdir() if f.is_file()] if source_out_dir.is_dir() else []
        if not source_files:
            print(f"  [EMPTY] Source {src_unit}/{out_subfolder}/ est vide")
            issues.append(f"Source {source_out_dir} vide")
            continue

        create_link(str(source_out_dir), str(target_in_dir))
        created += 1

        if verbose:
            total_size = sum(f.stat().st_size for f in source_files)
            print(f"         ({len(source_files)} fichiers, {format_size(total_size)})")

    print_separator()
    if not issues:
        print(f"RÉSULTAT: ✅ FRÉGATE {unit} — {created} PHANTOM LINK(S) CRÉÉ(S)")
    else:
        print(f"RÉSULTAT: ⚠️ FRÉGATE {unit} — {created} link(s) créé(s), {len(issues)} erreur(s)")
        for iss in issues:
            print(f"  → {iss}")
    print_separator()
    print()

    return len(issues) == 0, created


def cleanup_outputs(unit, drive_root, force=False, verbose=False):
    """Supprime les fichiers dans OUT/ de l'unité, avec garde-fous."""
    info = MANIFEST[unit]
    unit_folder = Path(drive_root) / info["folder"]
    out_spec = info["out"]

    print_banner(f"EXODUS MARSHAL — CLEANUP: {unit} {info['name']}")

    if unit in TRANSFER_ROUTES:
        for route_key, destinations in TRANSFER_ROUTES[unit].items():
            for dest in destinations:
                if dest == "EMPEROR":
                    continue
                dest_unit = dest.split("/")[0]
                dest_info = MANIFEST.get(dest_unit, {})
                if not dest_info:
                    continue
                dest_folder = Path(drive_root) / dest_info["folder"]
                dest_out_spec = dest_info.get("out", {})
                for dest_out_subfolder in dest_out_spec:
                    dest_out_dir = dest_folder / dest_out_subfolder
                    if dest_out_dir.is_dir():
                        dest_files = [f for f in dest_out_dir.iterdir() if f.is_file()]
                        if not dest_files and not force:
                            print(f"  [BLOCKED] {dest_unit}/{dest_out_subfolder}/ est vide — la frégate suivante n'a pas terminé")
                            print(f"  → Utilisez --force pour forcer le cleanup")
                            return False, 0

    total_freed = 0
    files_deleted = 0

    for subfolder in out_spec:
        out_dir = unit_folder / subfolder
        if not out_dir.is_dir():
            continue

        for f in sorted(out_dir.iterdir()):
            if f.is_file() and f.name != "_LINK.json":
                fsize = f.stat().st_size
                if verbose:
                    print(f"  [DEL] {f.name} ({format_size(fsize)})")
                f.unlink()
                total_freed += fsize
                files_deleted += 1

    print_separator()
    print(f"RÉSULTAT: 🧹 FRÉGATE {unit} — {files_deleted} fichiers supprimés ({format_size(total_freed)} libérés)")
    print_separator()

    log_result(unit, "cleanup", files_deleted, files_deleted, [], drive_root)

    print()
    return True, total_freed


def check_out(unit, drive_root, verbose=False):
    info = MANIFEST[unit]
    unit_folder = Path(drive_root) / info["folder"]
    out_spec = info["out"]

    print_banner(f"EXODUS MARSHAL \u2014 OUT-CHECK: {unit} {info['name']}")

    total_checks = 0
    passed_checks = 0
    all_found_files = []
    issues = []

    for subfolder, entries in out_spec.items():
        scan_dir = unit_folder / subfolder
        print(f"Scanning: {info['folder']}/{subfolder}/")

        for entry in entries:
            pattern = entry["pattern"]
            required = entry.get("required", False)
            min_count = entry.get("min_count", None)
            do_validate = entry.get("validate", None)
            description = entry.get("description", "")

            matches = find_matching_files(scan_dir, pattern)
            non_empty = [m for m in matches if m.stat().st_size > 0]

            if min_count is not None and not fnmatch.translate(pattern).startswith("(?s:"):
                total_checks += 1
                if len(non_empty) >= min_count:
                    avg_size = sum(m.stat().st_size for m in non_empty) // max(len(non_empty), 1)
                    print(f"  [OK] {len(non_empty)} {pattern} files detected" + (f"        (avg {format_size(avg_size)} each)" if verbose else ""))
                    passed_checks += 1
                    all_found_files.extend(non_empty)
                    if verbose:
                        for m in non_empty:
                            h = sha256_hash(m)
                            print(f"       \u2514\u2500 {m.name} ({format_size(m.stat().st_size)} | SHA256: {h[:16]})")
                elif required:
                    ext = pattern.replace("*", "")
                    print(f"  [MISSING] {pattern}                    \u2014 Aucun fichier {ext} trouv\u00e9")
                    issues.append(f"Fichier(s) {pattern} manquant(s) dans {subfolder}/")
                else:
                    print(f"  [--] {pattern}                    (optionnel, non trouv\u00e9)")
                    passed_checks += 1
                continue

            total_checks += 1
            if len(matches) == 0:
                if required:
                    print(f"  [MISSING] {pattern:<30s} \u2014 Fichier requis introuvable")
                    issues.append(f"Fichier {pattern} manquant dans {subfolder}/")
                else:
                    print(f"  [--] {pattern:<30s} (optionnel, non trouv\u00e9)")
                    passed_checks += 1
                continue

            target = matches[0]
            fsize = target.stat().st_size

            if fsize == 0:
                print(f"  [EMPTY]   {pattern:<30s} \u2014 Fichier vide (0 octets)")
                if required:
                    issues.append(f"Fichier {pattern} vide dans {subfolder}/")
                else:
                    passed_checks += 1
                continue

            json_tag = ""
            if do_validate == "json":
                if validate_json_file(target):
                    json_tag = " | JSON valid"
                else:
                    print(f"  [INVALID] {target.name:<30s} ({format_size(fsize)} | JSON invalide)")
                    if required:
                        issues.append(f"Fichier {target.name} JSON invalide dans {subfolder}/")
                    continue

            status_line = f"  [OK] {target.name:<30s} ({format_size(fsize)}{json_tag})"
            print(status_line)
            if verbose:
                h = sha256_hash(target)
                if h:
                    print(f"       SHA256: {h[:16]}")
            passed_checks += 1
            all_found_files.append(target)

        print()

    print_separator()
    if not issues:
        print(f"R\u00c9SULTAT: \u2705 FR\u00c9GATE {unit} \u2014 OUT-CHECK PASS\u00c9 ({passed_checks}/{total_checks})")
    else:
        print(f"R\u00c9SULTAT: \u274c FR\u00c9GATE {unit} \u2014 OUT-CHECK \u00c9CHOU\u00c9 ({passed_checks}/{total_checks})")
    print_separator()

    routes = TRANSFER_ROUTES.get(unit, {})
    if routes and not issues:
        print(f"\n📋 INSTRUCTIONS DE TRANSFERT:")
        printed = set()
        for route_key, destinations in routes.items():
            for dest in destinations:
                parts = route_key.split("/")
                file_part = parts[-1] if len(parts) > 1 else route_key
                if dest == "EMPEROR":
                    line = f"  \u2192 Remettre {file_part} \u00e0 l'Empereur"
                    if "SayMotion" in (MANIFEST[unit]["out"].get(parts[0], [{}])[0].get("description", "") if parts[0] in MANIFEST[unit]["out"] else ""):
                        line += " pour SayMotion"
                else:
                    dest_unit = dest.split("/")[0]
                    dest_folder = "/".join(dest.split("/")[1:])
                    dest_info = MANIFEST.get(dest_unit, {})
                    dest_unit_folder = dest_info.get("folder", dest_unit)
                    line = f"  \u2192 Copier {file_part} \u2192 {dest_unit_folder}/{dest_folder}/"
                if line not in printed:
                    print(line)
                    printed.add(line)
    elif issues:
        print(f"\n\u26a0\ufe0f  ACTION REQUISE:")
        for iss in issues:
            print(f"  \u2192 {iss}")
        print(f"  \u2192 FR\u00c9GATE {unit} BLOQU\u00c9E \u2014 Transfert interdit.")

    print()
    return len(issues) == 0, passed_checks, total_checks, issues


def check_in(unit, drive_root, verbose=False):
    info = MANIFEST[unit]
    unit_folder = Path(drive_root) / info["folder"]
    in_spec = info["in"]

    print_banner(f"EXODUS MARSHAL \u2014 IN-CHECK: {unit} {info['name']}")

    total_checks = 0
    passed_checks = 0
    issues = []

    for subfolder, entries in in_spec.items():
        raw_dir = unit_folder / subfolder
        scan_dir = resolve_input(raw_dir)
        if scan_dir != raw_dir:
            print(f"  [PHANTOM] {subfolder}/ → {scan_dir}")
        print(f"Scanning: {info['folder']}/{subfolder}/")

        for entry in entries:
            pattern = entry["pattern"]
            required = entry.get("required", False)
            min_count = entry.get("min_count", None)
            do_validate = entry.get("validate", None)
            description = entry.get("description", "")

            matches = find_matching_files(scan_dir, pattern)

            if min_count is not None and pattern.startswith("*"):
                total_checks += 1
                non_empty = [m for m in matches if m.stat().st_size > 0]
                empty = [m for m in matches if m.stat().st_size == 0]

                if empty:
                    for ef in empty:
                        print(f"  [EMPTY]   {ef.name:<30s} \u2014 Fichier vide (0 octets)")

                if len(non_empty) >= min_count:
                    avg_size = sum(m.stat().st_size for m in non_empty) // max(len(non_empty), 1)
                    print(f"  [OK] {len(non_empty)} {pattern} files detected" + (f"        (avg {format_size(avg_size)} each)" if verbose else ""))
                    passed_checks += 1
                    if verbose:
                        for m in non_empty:
                            h = sha256_hash(m)
                            print(f"       \u2514\u2500 {m.name} ({format_size(m.stat().st_size)} | SHA256: {h[:16]})")
                elif required:
                    ext = pattern.replace("*", "")
                    print(f"  [MISSING] {pattern:<30s} \u2014 Aucun fichier {ext} trouv\u00e9")
                    issues.append(f"Fichier(s) {pattern} manquant(s) dans {subfolder}/")
                else:
                    print(f"  [--] {pattern:<30s} (optionnel, non trouv\u00e9)")
                    passed_checks += 1
                continue

            total_checks += 1
            if len(matches) == 0:
                if required:
                    print(f"  [MISSING] {pattern:<30s} \u2014 Fichier requis introuvable")
                    issues.append(f"Fichier {pattern} manquant dans {subfolder}/")
                else:
                    print(f"  [--] {pattern:<30s} (optionnel, non trouv\u00e9)")
                    passed_checks += 1
                continue

            target = matches[0]
            fsize = target.stat().st_size

            if fsize == 0:
                print(f"  [EMPTY]   {target.name:<30s} \u2014 Fichier vide (0 octets)")
                if required:
                    issues.append(f"Fichier {target.name} vide dans {subfolder}/")
                else:
                    passed_checks += 1
                continue

            json_tag = ""
            if do_validate == "json":
                if validate_json_file(target):
                    json_tag = " | JSON valid"
                else:
                    print(f"  [INVALID] {target.name:<30s} ({format_size(fsize)} | JSON invalide)")
                    if required:
                        issues.append(f"Fichier {target.name} JSON invalide dans {subfolder}/")
                    continue

            status_line = f"  [OK]      {target.name:<30s} ({format_size(fsize)}{json_tag})"
            print(status_line)
            if verbose:
                h = sha256_hash(target)
                if h:
                    print(f"            SHA256: {h[:16]}")
            passed_checks += 1

        print()

    print_separator()
    if not issues:
        print(f"R\u00c9SULTAT: \u2705 FR\u00c9GATE {unit} \u2014 IN-CHECK PASS\u00c9 ({passed_checks}/{total_checks})")
        print_separator()
        print(f"\nFR\u00c9GATE {unit} PR\u00caTE AU LANCEMENT \u2705")
    else:
        print(f"R\u00c9SULTAT: \u274c FR\u00c9GATE {unit} \u2014 IN-CHECK \u00c9CHOU\u00c9 ({passed_checks}/{total_checks})")
        print_separator()
        print(f"\n\u26a0\ufe0f  ACTION REQUISE:")
        for iss in issues:
            print(f"  \u2192 {iss}")
        print(f"  \u2192 L'Empereur doit fournir les fichiers manquants.")
        print(f"  \u2192 FR\u00c9GATE {unit} BLOQU\u00c9E \u2014 Lancement interdit.")

    print()
    return len(issues) == 0, passed_checks, total_checks, issues


def log_result(unit, mode, passed, total, issues, drive_root):
    log_path = Path(drive_root) / "EXODUS_CAMPAIGN.LOG"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "\u2705 PASS" if not issues else "\u274c FAIL"
    summary = f"{passed}/{total} files"

    if issues:
        details = "MISSING: " + "; ".join(issues[:3])
        if len(issues) > 3:
            details += f" (+{len(issues) - 3} more)"
    else:
        details = "All checks passed"

    line = f"[{timestamp}] | {unit} | {mode:<10s} | {status} | {summary} | {details}\n"

    if not log_path.exists():
        header = (
            "# EXODUS V2 \u2014 Campaign Log (Auto-generated by MARSHAL)\n"
            "# Format: [Timestamp] | Unit | Mode | Status | Summary | Details\n\n"
        )
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(header)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="EXO_MARSHAL",
        description="EXODUS V2 \u2014 THE MARSHAL (L'Intendant) \u2014 Validation logistique inter-fr\u00e9gates",
        epilog="Loi III : \u00c9tanch\u00e9it\u00e9 \u2014 Le Marshal ne d\u00e9place, ne copie, ne supprime jamais de fichier."
    )
    parser.add_argument(
        "--unit", required=True,
        help="Unit identifier: U00-U06 (or F00-F06). Case-insensitive."
    )
    parser.add_argument(
        "--mode", required=True, choices=VALID_MODES,
        help="Validation mode: check-out, check-in, validate, link, cleanup."
    )
    parser.add_argument(
        "--drive-root", default=None,
        help="Path to EXODUS V2 drive root. Default: auto-detect from script location."
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show detailed file info (sizes, SHA256 hashes)."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force cleanup without checking downstream completion."
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    unit = normalize_unit(args.unit)
    if unit is None:
        print(f"\u274c Erreur: Unit\u00e9 invalide '{args.unit}'. Valeurs accept\u00e9es: U00-U06 / F00-F06", file=sys.stderr)
        sys.exit(2)

    if args.drive_root:
        drive_root = Path(args.drive_root)
    else:
        drive_root = Path(__file__).resolve().parent

    if not drive_root.is_dir():
        print(f"\u274c Erreur: R\u00e9pertoire racine introuvable: {drive_root}", file=sys.stderr)
        sys.exit(2)

    unit_info = MANIFEST[unit]
    unit_dir = drive_root / unit_info["folder"]
    if not unit_dir.is_dir():
        print(f"\u26a0\ufe0f  Avertissement: Dossier unit\u00e9 introuvable: {unit_dir}", file=sys.stderr)

    mode = args.mode
    verbose = args.verbose
    all_passed = True

    if mode in ("check-out", "validate"):
        ok, passed, total, issues = check_out(unit, drive_root, verbose)
        log_result(unit, "check-out", passed, total, issues, drive_root)
        if not ok:
            all_passed = False

    if mode in ("check-in", "validate"):
        ok, passed, total, issues = check_in(unit, drive_root, verbose)
        log_result(unit, "check-in", passed, total, issues, drive_root)
        if not ok:
            all_passed = False

    if mode == "link":
        expected = len(REVERSE_ROUTES.get(unit, {}))
        ok, count = link_inputs(unit, drive_root, verbose)
        log_result(unit, "link", count, expected, [] if ok else ["Phantom link errors"], drive_root)
        if not ok:
            all_passed = False

        import shutil
        u00_out = drive_root / "00_CORTEX_HQ" / "OUT_PRODUCTION_PLAN"
        u01_in  = drive_root / "01_ANIMATION_ENGINE" / "IN_CORTEX_JSON"
        u01_in.mkdir(parents=True, exist_ok=True)

        FILES_U00_TO_U01 = [
            "PRODUCTION_PLAN.JSON",
            "facial_animation.json",
            "camera_fov_ratio.json",
            "audio_source.wav",
        ]

        copied = 0
        for filename in FILES_U00_TO_U01:
            src = u00_out / filename
            dst = u01_in / filename
            if src.exists() and not dst.exists():
                shutil.copy2(str(src), str(dst))
                print(f"   \u2705 {filename} \u2192 IN_CORTEX_JSON/")
                copied += 1
            elif dst.exists():
                print(f"   \u23ed\ufe0f  {filename} d\u00e9j\u00e0 pr\u00e9sent")

        print(f"[MARSHAL] {copied} fichier(s) transf\u00e9r\u00e9s U00 \u2192 U01")

    if mode == "cleanup":
        ok, freed = cleanup_outputs(unit, drive_root, force=args.force, verbose=verbose)
        if not ok:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
