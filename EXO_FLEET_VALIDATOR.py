#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              EXODUS FLEET VALIDATOR — Validation End-to-End                  ║
║                    Phase D.2 — Le 2ème Sceau de l'Empire                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Valide la chaîne complète U00→U06 en 3 couches :                           ║
║    Layer 1 — QUICK  : fichiers existent ? taille OK ?              (~2s)    ║
║    Layer 2 — DEEP   : JSON valides ? schemas corrects ? code OK ?  (~10s)   ║
║    Layer 3 — CROSS  : Phantom Links ? dépendances inter-frégates ? (~30s)   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import argparse
import hashlib
import fnmatch
import py_compile
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from EXO_MARSHAL import (
    MANIFEST,
    TRANSFER_ROUTES,
    VALID_UNITS,
    normalize_unit,
    validate_json_file,
    find_matching_files,
    format_size,
    sha256_hash,
    print_banner,
    print_separator,
)
from phantom_link import resolve_input, validate_link

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FLEET_VERSION = "1.0.0"
VALIDATION_ORDER = ["U00", "U01", "U02", "U03", "U04", "U05", "U06"]

MIN_SIZES = {
    ".json": 100,
    ".blend": 50_000,
    ".abc": 10_000,
    ".png": 1_000,
    ".exr": 10_000,
    ".wav": 44,
    ".mp4": 10_000,
    ".fbx": 10_000,
    ".txt": 10,
}

EXPECTED_SCRIPTS = {
    "U00": ["EXO_00_CORTEX.py"],
    "U01": ["EXO_01_TRANSMUTATION.py", "expression_schema.py"],
    "U02": ["EXO_02_LOGISTICS.py"],
    "U03": ["EXO_03_SCENOGRAPHY.py", "scene_schema.py"],
    "U04": ["EXO_04_PHOTOGRAPHY.py", "camera_schema.py", "EXO_04_DARKROOM.py"],
    "U05": ["EXO_05_ALCHEMIST.py", "alchemist_schema.py"],
    "U06": ["EXO_06_CARRIER.py", "carrier_schema.py"],
}


# ---------------------------------------------------------------------------
# FleetValidator
# ---------------------------------------------------------------------------

class FleetValidator:
    """Orchestrateur de validation End-to-End de la flotte EXODUS V2."""

    def __init__(self, drive_root: str, verbose: bool = False):
        self.drive_root = Path(drive_root)
        self.verbose = verbose
        self.report = {
            "version": FLEET_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drive_root": str(drive_root),
            "units": {},
            "cross_validation": {},
            "fleet_seal": {
                "status": "PENDING",
                "reason": None,
            },
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            },
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_full(self) -> dict:
        """Lance la validation complète en 3 couches."""
        print_banner("EXODUS FLEET VALIDATOR — VALIDATION COMPLÈTE")

        all_pass = True
        for unit in VALIDATION_ORDER:
            unit_result = self._validate_unit(unit)
            self.report["units"][unit] = unit_result
            if unit_result["status"] == "FAIL":
                all_pass = False

        cross_result = self._validate_cross_dependencies()
        self.report["cross_validation"] = cross_result
        if cross_result["status"] == "FAIL":
            all_pass = False

        if all_pass:
            self.report["fleet_seal"] = {
                "status": "SEALED",
                "reason": "All units and cross-dependencies validated",
                "sealed_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            failed_units = [
                u for u, r in self.report["units"].items() if r["status"] == "FAIL"
            ]
            self.report["fleet_seal"] = {
                "status": "REJECTED",
                "reason": (
                    f"Failed units: {', '.join(failed_units)}"
                    if failed_units
                    else "Cross-dependency validation failed"
                ),
            }

        self._print_summary()
        return self.report

    def validate_unit(self, unit: str) -> dict:
        """Valide une seule unité (wrapper public)."""
        unit = normalize_unit(unit)
        if unit is None or unit not in MANIFEST:
            print(f"❌ Unité invalide: {unit}")
            return {"status": "FAIL", "reason": "Invalid unit"}

        print_banner(f"EXODUS FLEET VALIDATOR — UNIT {unit}")
        result = self._validate_unit(unit)
        self.report["units"][unit] = result

        icon = "✅" if result["status"] == "PASS" else "❌"
        print_separator()
        print(f"RÉSULTAT: {icon} {unit} — {result['name']} — {result['status']}")
        print_separator()
        return result

    def fix(self) -> dict:
        """Tente de réparer automatiquement les problèmes courants."""
        print_banner("EXODUS FLEET VALIDATOR — MODE RÉPARATION")
        fixes = []

        for unit in VALIDATION_ORDER:
            info = MANIFEST[unit]
            unit_path = self.drive_root / info["folder"]

            for folder_type in ("in", "out"):
                for subfolder in info.get(folder_type, {}):
                    full_path = unit_path / subfolder
                    if not full_path.is_dir():
                        full_path.mkdir(parents=True, exist_ok=True)
                        fixes.append(
                            f"Created missing folder: {info['folder']}/{subfolder}/"
                        )

        for unit in VALIDATION_ORDER:
            info = MANIFEST[unit]
            unit_path = self.drive_root / info["folder"]
            for in_folder in info.get("in", {}):
                in_path = unit_path / in_folder
                link_info = validate_link(str(in_path))
                if link_info["has_link"] and not link_info["valid"]:
                    fixes.append(
                        f"Broken link detected: {unit}/{in_folder}. "
                        f"Run: python EXO_MARSHAL.py --unit {unit} --mode link "
                        f"--drive-root {self.drive_root}"
                    )

        for unit in VALIDATION_ORDER:
            info = MANIFEST[unit]
            unit_path = self.drive_root / info["folder"]
            for out_folder, entries in info.get("out", {}).items():
                out_path = unit_path / out_folder
                for entry in entries:
                    if entry.get("required"):
                        matches = (
                            find_matching_files(out_path, entry["pattern"])
                            if out_path.is_dir()
                            else []
                        )
                        if not matches:
                            fixes.append(
                                f"Missing output: {unit}/{out_folder}/{entry['pattern']}. "
                                f"Must re-run {unit} pipeline"
                            )

        return {
            "fixes_applied": fixes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate_seal_certificate(self, output_path: str) -> bool:
        """Génère le certificat de scellement si la validation est passée."""
        if self.report["fleet_seal"]["status"] != "SEALED":
            print("❌ Cannot generate certificate — fleet validation failed")
            return False

        lines = [
            "# 🛡️ FLEET SEAL CERTIFICATE — EXODUS V2",
            "",
            "> Certificat de Scellement End-to-End de la Flotte",
            "",
            "---",
            "",
            "## STATUT : 🟢 FLOTTE SCELLÉE",
            "",
            f"**Date de scellement** : {self.report['fleet_seal']['sealed_at']}",
            f"**Version validateur** : {FLEET_VERSION}",
            f"**Drive root** : `{self.drive_root}`",
            "",
            "## RÉSULTATS PAR FRÉGATE",
            "",
            "| Unité | Nom | Quick | Deep | Cross | Statut |",
            "|-------|-----|-------|------|-------|--------|",
        ]

        for unit in VALIDATION_ORDER:
            r = self.report["units"][unit]
            q = r["layers"]["quick"]["status"]
            d = r["layers"]["deep"]["status"]
            c = r["layers"]["cross"]["status"]
            s = "✅" if r["status"] == "PASS" else "❌"
            lines.append(f"| {unit} | {r['name']} | {q} | {d} | {c} | {s} |")

        lines.extend(
            [
                "",
                "## STATISTIQUES",
                "",
                f"- Total checks : {self.report['summary']['total_checks']}",
                f"- Passed : {self.report['summary']['passed']}",
                f"- Failed : {self.report['summary']['failed']}",
                "",
                "## CROSS-VALIDATION",
                "",
                "- Phantom Links : {}".format(
                    "✅ Tous valides"
                    if self.report["cross_validation"]["status"] == "PASS"
                    else "❌ Erreurs détectées"
                ),
                "- Transfer Routes : Vérifiées",
                "",
                "---",
                "",
                "*Généré automatiquement par EXO_FLEET_VALIDATOR.py*",
                f"*{datetime.now(timezone.utc).isoformat()}*",
            ]
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text("\n".join(lines), encoding="utf-8")
        print(f"🛡️ Fleet Seal Certificate generated: {output_path}")
        return True

    # ------------------------------------------------------------------
    # Internal — Unit validation (3 layers)
    # ------------------------------------------------------------------

    def _validate_unit(self, unit: str) -> dict:
        """Validation 3 couches pour une unité."""
        info = MANIFEST[unit]
        result = {
            "name": info["name"],
            "status": "PENDING",
            "layers": {
                "quick": {"status": "PENDING", "checks": []},
                "deep": {"status": "PENDING", "checks": []},
                "cross": {"status": "PENDING", "checks": []},
            },
            "fixes_suggested": [],
        }

        print(f"\n{'━' * 56}")
        print(f"  {unit} — {info['name']}")
        print(f"{'━' * 56}")

        print(f"\n  ── Layer 1 · QUICK ──")
        result["layers"]["quick"] = self._layer_quick(unit)
        if result["layers"]["quick"]["status"] == "FAIL":
            result["status"] = "FAIL"
            result["layers"]["deep"]["status"] = "SKIPPED"
            result["layers"]["cross"]["status"] = "SKIPPED"
            return result

        print(f"\n  ── Layer 2 · DEEP ──")
        result["layers"]["deep"] = self._layer_deep(unit)

        print(f"\n  ── Layer 3 · CROSS ──")
        result["layers"]["cross"] = self._layer_cross(unit)

        has_fail = any(
            result["layers"][layer]["status"] == "FAIL"
            for layer in ("quick", "deep", "cross")
        )
        result["status"] = "FAIL" if has_fail else "PASS"

        for layer_name in ("quick", "deep", "cross"):
            for chk in result["layers"][layer_name].get("checks", []):
                if not chk["passed"] and chk.get("fix"):
                    result["fixes_suggested"].append(chk["fix"])

        return result

    # ------------------------------------------------------------------
    # Layer 1 — QUICK (~2s)
    # ------------------------------------------------------------------

    def _layer_quick(self, unit: str) -> dict:
        """Layer 1 — Vérification rapide d'existence et taille."""
        checks = []
        info = MANIFEST[unit]
        unit_path = self.drive_root / info["folder"]

        checks.append(
            self._check(
                f"{unit} folder exists",
                unit_path.is_dir(),
                fix=f"Run EXO_GENESIS_DRIVE.py --drive-root {self.drive_root}",
            )
        )

        if not unit_path.is_dir():
            return {"status": "FAIL", "checks": checks}

        codebase = unit_path / "CODEBASE"
        has_code = codebase.is_dir() and any(codebase.iterdir()) if codebase.is_dir() else False
        checks.append(
            self._check(
                f"{unit} CODEBASE/ populated",
                has_code,
                fix="Run Genesis notebook Cell 3 (deploy code)",
            )
        )

        for out_folder, entries in info.get("out", {}).items():
            out_path = unit_path / out_folder
            for entry in entries:
                pattern = entry["pattern"]
                required = entry.get("required", False)
                matches = (
                    find_matching_files(out_path, pattern)
                    if out_path.is_dir()
                    else []
                )

                if required:
                    ok = len(matches) > 0
                    checks.append(
                        self._check(
                            f"{unit}/{out_folder}/{pattern} exists",
                            ok,
                            fix=f"Re-run {unit} pipeline",
                        )
                    )

                    for m in matches:
                        ext = m.suffix.lower()
                        min_size = MIN_SIZES.get(ext, 100)
                        file_size = m.stat().st_size
                        size_ok = file_size >= min_size
                        if not size_ok:
                            checks.append(
                                self._check(
                                    f"{m.name} size >= {min_size}B (actual: {file_size}B)",
                                    False,
                                    fix=f"File may be corrupted. Re-run {unit} pipeline",
                                )
                            )

                        if file_size == 0:
                            checks.append(
                                self._check(
                                    f"{m.name} not empty",
                                    False,
                                    fix=f"Empty file detected. Re-run {unit} pipeline",
                                )
                            )

        has_fail = any(not c["passed"] for c in checks)
        return {"status": "FAIL" if has_fail else "PASS", "checks": checks}

    # ------------------------------------------------------------------
    # Layer 2 — DEEP (~10s)
    # ------------------------------------------------------------------

    def _layer_deep(self, unit: str) -> dict:
        """Layer 2 — Vérification de contenu et format."""
        checks = []
        info = MANIFEST[unit]
        unit_path = self.drive_root / info["folder"]

        for out_folder, entries in info.get("out", {}).items():
            out_path = unit_path / out_folder
            for entry in entries:
                if entry.get("validate") == "json":
                    matches = (
                        find_matching_files(out_path, entry["pattern"])
                        if out_path.is_dir()
                        else []
                    )
                    for m in matches:
                        valid = validate_json_file(m)
                        checks.append(
                            self._check(
                                f"{m.name} JSON valid",
                                valid,
                                fix=f"JSON corrupted in {out_folder}/. Re-run {unit}",
                            )
                        )

                        if m.name == "PRODUCTION_PLAN.JSON" and valid:
                            try:
                                with open(m, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                has_scenes = "scenes" in data and len(data["scenes"]) > 0
                                checks.append(
                                    self._check(
                                        "PRODUCTION_PLAN has scenes[]",
                                        has_scenes,
                                        fix="Plan has no scenes. Re-run U00 CORTEX",
                                    )
                                )
                                has_metadata = "metadata" in data
                                checks.append(
                                    self._check(
                                        "PRODUCTION_PLAN has metadata",
                                        has_metadata,
                                        fix="Plan has no metadata. Re-run U00 CORTEX",
                                    )
                                )
                            except (json.JSONDecodeError, OSError):
                                pass

        codebase = unit_path / "CODEBASE"
        if unit in EXPECTED_SCRIPTS and codebase.is_dir():
            for script_name in EXPECTED_SCRIPTS[unit]:
                script_path = codebase / script_name
                exists = script_path.is_file()
                checks.append(
                    self._check(
                        f"{script_name} exists in CODEBASE/",
                        exists,
                        fix="Missing script. Re-deploy with Genesis Cell 3",
                    )
                )
                if exists:
                    try:
                        py_compile.compile(str(script_path), doraise=True)
                        syntax_ok = True
                    except py_compile.PyCompileError:
                        syntax_ok = False
                    checks.append(
                        self._check(
                            f"{script_name} syntax valid",
                            syntax_ok,
                            fix=f"Syntax error in {script_name}. Check the code",
                        )
                    )

        for out_folder, entries in info.get("out", {}).items():
            out_path = unit_path / out_folder
            for entry in entries:
                matches = (
                    find_matching_files(out_path, entry["pattern"])
                    if out_path.is_dir()
                    else []
                )
                for m in matches:
                    if m.suffix == ".blend":
                        try:
                            with open(m, "rb") as f:
                                magic = f.read(7)
                            checks.append(
                                self._check(
                                    f"{m.name} Blender magic",
                                    magic == b"BLENDER",
                                    fix=f"Corrupted .blend file. Re-run {unit}",
                                )
                            )
                        except OSError:
                            checks.append(
                                self._check(
                                    f"{m.name} readable",
                                    False,
                                    fix=f"Cannot read {m.name}",
                                )
                            )
                    elif m.suffix == ".wav":
                        try:
                            with open(m, "rb") as f:
                                magic = f.read(4)
                            checks.append(
                                self._check(
                                    f"{m.name} WAV header",
                                    magic == b"RIFF",
                                    fix=f"Corrupted .wav file. Re-extract audio",
                                )
                            )
                        except OSError:
                            checks.append(
                                self._check(
                                    f"{m.name} readable",
                                    False,
                                    fix=f"Cannot read {m.name}",
                                )
                            )

        has_fail = any(not c["passed"] for c in checks)
        return {"status": "FAIL" if has_fail else "PASS", "checks": checks}

    # ------------------------------------------------------------------
    # Layer 3 — CROSS (per-unit portion)
    # ------------------------------------------------------------------

    def _layer_cross(self, unit: str) -> dict:
        """Layer 3 — Vérification des liens entrants de cette unité."""
        checks = []
        info = MANIFEST[unit]
        unit_path = self.drive_root / info["folder"]

        for in_folder in info.get("in", {}):
            in_path = unit_path / in_folder
            link_info = validate_link(str(in_path))

            if link_info["has_link"]:
                checks.append(
                    self._check(
                        f"{unit}/{in_folder} Phantom Link valid",
                        link_info["valid"],
                        fix=(
                            f"python EXO_MARSHAL.py --unit {unit} --mode link "
                            f"--drive-root {self.drive_root}"
                        ),
                    )
                )
                if link_info["valid"]:
                    checks.append(
                        self._check(
                            f"{unit}/{in_folder} source has files ({link_info['file_count']})",
                            link_info["file_count"] > 0,
                            fix="Source folder empty. Run the upstream unit first",
                        )
                    )
            else:
                if in_path.is_dir():
                    has_files = any(in_path.iterdir())
                    checks.append(
                        self._check(
                            f"{unit}/{in_folder} has local files (no Phantom Link)",
                            has_files,
                            fix=(
                                f"No Phantom Link and no local files in {in_folder}/. "
                                f"Run: python EXO_MARSHAL.py --unit {unit} --mode link "
                                f"--drive-root {self.drive_root}"
                            ),
                        )
                    )
                else:
                    checks.append(
                        self._check(
                            f"{unit}/{in_folder} folder exists",
                            False,
                            fix=(
                                f"IN folder missing. Run: python EXO_MARSHAL.py "
                                f"--unit {unit} --mode link --drive-root {self.drive_root}"
                            ),
                        )
                    )

        if not checks:
            return {"status": "PASS", "checks": []}

        has_fail = any(not c["passed"] for c in checks)
        return {"status": "FAIL" if has_fail else "PASS", "checks": checks}

    # ------------------------------------------------------------------
    # Layer 3 — CROSS (global: transfer routes)
    # ------------------------------------------------------------------

    def _validate_cross_dependencies(self) -> dict:
        """Layer 3 — Vérification des dépendances inter-frégates."""
        print(f"\n{'━' * 56}")
        print(f"  CROSS-VALIDATION — Transfer Routes")
        print(f"{'━' * 56}\n")

        checks = []

        for src_unit, routes in TRANSFER_ROUTES.items():
            src_info = MANIFEST[src_unit]

            for route_key, destinations in routes.items():
                for dest in destinations:
                    if dest == "EMPEROR":
                        continue

                    parts = dest.split("/")
                    if len(parts) < 2:
                        continue

                    dest_unit = parts[0]
                    dest_in = parts[1]

                    if dest_unit not in MANIFEST:
                        continue

                    dest_info = MANIFEST[dest_unit]
                    dest_path = self.drive_root / dest_info["folder"] / dest_in

                    resolved = resolve_input(dest_path)
                    has_access = False
                    if resolved.is_dir():
                        try:
                            has_access = any(resolved.iterdir())
                        except OSError:
                            has_access = False

                    checks.append(
                        self._check(
                            f"Route {src_unit}→{dest_unit}/{dest_in} accessible",
                            has_access,
                            fix=(
                                f"python EXO_MARSHAL.py --unit {dest_unit} --mode link "
                                f"--drive-root {self.drive_root}"
                            ),
                        )
                    )

        has_fail = any(not c["passed"] for c in checks)
        return {"status": "FAIL" if has_fail else "PASS", "checks": checks}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check(self, name: str, passed: bool, fix: str = "") -> dict:
        """Crée un résultat de check avec log console."""
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
        self.report["summary"]["total_checks"] += 1
        if passed:
            self.report["summary"]["passed"] += 1
        else:
            self.report["summary"]["failed"] += 1
        return {"name": name, "passed": passed, "fix": fix}

    def _print_summary(self):
        """Affiche le résumé final."""
        print(f"\n{'═' * 56}")
        print(f"  📊 RÉSUMÉ FLEET VALIDATOR v{FLEET_VERSION}")
        print(f"{'═' * 56}\n")

        for unit in VALIDATION_ORDER:
            if unit in self.report["units"]:
                r = self.report["units"][unit]
                icon = "✅" if r["status"] == "PASS" else "❌"
                q = r["layers"]["quick"]["status"]
                d = r["layers"]["deep"]["status"]
                c = r["layers"]["cross"]["status"]
                print(f"  {icon} {unit} — {r['name']:<22s} Q:{q:<6s} D:{d:<6s} C:{c}")

        print()
        s = self.report["summary"]
        print(f"  Total checks : {s['total_checks']}")
        print(f"  Passed       : {s['passed']}")
        print(f"  Failed       : {s['failed']}")

        seal = self.report["fleet_seal"]
        print()
        if seal["status"] == "SEALED":
            print(f"  🛡️  Fleet Seal : SEALED ✅")
        elif seal["status"] == "REJECTED":
            print(f"  🛡️  Fleet Seal : REJECTED ❌")
            print(f"     Raison : {seal['reason']}")
        else:
            print(f"  🛡️  Fleet Seal : {seal['status']}")

        print(f"\n{'═' * 56}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="EXO_FLEET_VALIDATOR",
        description="EXODUS Fleet Validator — E2E Validation",
        epilog="Phase D.2 — Le 2ème Sceau de l'Empire",
    )
    parser.add_argument(
        "--drive-root",
        required=True,
        help="Racine du Drive EXODUS",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "unit", "fix"],
        default="full",
        help="Mode de validation (default: full)",
    )
    parser.add_argument(
        "--unit",
        help="Unité à valider (mode unit uniquement, ex: U03)",
    )
    parser.add_argument(
        "--output",
        help="Chemin du rapport JSON (défaut: DRIVE_ROOT/FLEET_VALIDATION_REPORT.json)",
    )
    parser.add_argument(
        "--seal",
        action="store_true",
        help="Générer le certificat de scellement si validation OK",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Logs détaillés",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les checks sans les exécuter",
    )

    args = parser.parse_args()

    drive_root = Path(args.drive_root)
    if not drive_root.is_dir():
        print(f"❌ Drive root introuvable: {drive_root}", file=sys.stderr)
        sys.exit(2)

    validator = FleetValidator(str(drive_root), verbose=args.verbose)

    if args.dry_run:
        print_banner("EXODUS FLEET VALIDATOR — DRY RUN")
        print("Mode dry-run activé — les checks suivants seront exécutés :\n")
        for unit in VALIDATION_ORDER:
            info = MANIFEST[unit]
            out_count = sum(len(e) for e in info.get("out", {}).values())
            in_count = len(info.get("in", {}))
            scripts = len(EXPECTED_SCRIPTS.get(unit, []))
            print(
                f"  {unit} — {info['name']:<22s} "
                f"OUT:{out_count} checks | IN:{in_count} links | "
                f"SCRIPTS:{scripts}"
            )
        print(f"\n  Total transfer routes: {sum(len(v) for v in TRANSFER_ROUTES.values())}")
        print(f"\n  Layers: Quick → Deep → Cross")
        sys.exit(0)

    if args.mode == "full":
        report = validator.validate_full()
    elif args.mode == "unit":
        if not args.unit:
            print("❌ --unit requis pour le mode unit", file=sys.stderr)
            sys.exit(2)
        report = validator.validate_unit(args.unit)
    elif args.mode == "fix":
        fixes = validator.fix()
        for fix_msg in fixes["fixes_applied"]:
            print(f"  🔧 {fix_msg}")
        if not fixes["fixes_applied"]:
            print("  ✅ Rien à réparer")
        else:
            print(f"\n🔧 {len(fixes['fixes_applied'])} réparation(s)")
            print("   Relancez avec --mode full pour re-valider")
        report = fixes
    else:
        report = {}

    output_path = args.output or str(drive_root / "FLEET_VALIDATION_REPORT.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Rapport sauvegardé : {output_path}")

    if args.seal and args.mode == "full":
        cert_path = str(drive_root / "FLEET_SEAL_CERTIFICATE.md")
        validator.generate_seal_certificate(cert_path)

    if args.mode in ("full", "unit"):
        seal_status = report.get("fleet_seal", {}).get("status", "UNKNOWN")
        if args.mode == "full" and seal_status == "REJECTED":
            sys.exit(1)
        elif args.mode == "unit":
            unit_status = report.get("status", "FAIL")
            if unit_status == "FAIL":
                sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
