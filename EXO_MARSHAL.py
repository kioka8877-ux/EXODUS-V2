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
                {"pattern": "semantic_masks.json", "required": True, "validate": "json", "description": "SAM segmentation for U03"},
                {"pattern": "camera_fov_ratio.json", "required": True, "validate": "json", "description": "Camera metadata for U04"},
                {"pattern": "audio_source.wav", "required": True, "description": "Audio track for U06"}
            ],
            "OUT_PRODUCTION_PLAN/DEPTH_MAP": [
                {"pattern": "*.png", "required": True, "min_count": 1, "description": "Depth map sequence from DepthAnything V2"}
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
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Animated actor from U01"}
            ],
            "IN_ROBLOX_AVATAR": [
                {"pattern": "*.blend", "required": True, "min_count": 1, "description": "Roblox avatar model"}
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
                {"pattern": "*.png", "required": True, "min_count": 1, "description": "Depth maps from U00"},
                {"pattern": "semantic_masks.json", "required": True, "validate": "json", "description": "SAM masks from U00"}
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

VALID_UNITS = ["U00", "U01", "U02", "U03", "U04", "U05", "U06"]
VALID_MODES = ["check-out", "check-in", "validate"]
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
        scan_dir = unit_folder / subfolder
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
        help="Validation mode: check-out, check-in, or validate (both)."
    )
    parser.add_argument(
        "--drive-root", default=None,
        help="Path to EXODUS V2 drive root. Default: auto-detect from script location."
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show detailed file info (sizes, SHA256 hashes)."
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

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
