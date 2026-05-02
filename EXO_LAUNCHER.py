#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 EXODUS V2 — LAUNCHER — AIGUILLAGE IMPERIAL                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Point d'entrée unique. Routing vers Mode 1 ou Mode 2.             ║
║  Loi: ZERO logique métier. ZERO transformation de données. ROUTING PUR.     ║
╚══════════════════════════════════════════════════════════════════════════════╝

DECRET IMPERIAL R-06 — LOI DU LAUNCHER :
    Le Launcher ne contient aucune logique métier.
    Il ne transforme aucune donnée.
    Il ne connaît pas le contenu des pipelines.
    Il route. C'est tout. C'est suffisant.

MODES :
    [1] MODE VIDEO-TO-VIDEO  — Pipeline Mode 1 (Sacré — Inchangé)
        Input : vidéo virale existante → FINAL_OUTPUT.mp4 4K/120FPS

    [2] MODE FROM SCRATCH    — Pipeline Mode 2 (Forgé)
        Input : avatar GLB animé + audio optionnel → FINAL_OUTPUT.mp4

Usage:
    python EXO_LAUNCHER.py                  # Menu interactif
    python EXO_LAUNCHER.py --mode 1         # Forcer Mode 1
    python EXO_LAUNCHER.py --mode 2         # Forcer Mode 2
    python EXO_LAUNCHER.py --mode 1 --args "--unit U00 --verbose"
    python EXO_LAUNCHER.py --mode 2 --args "--fregate F01 --verbose"
    python EXO_LAUNCHER.py --dry-run        # Affiche le routing sans lancer
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

LAUNCHER_VERSION = "1.0.0"

BANNER = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║  ███████ ██   ██  ██████  ██████  ██   ██ ███████    ║
║  ██       ██ ██  ██    ██ ██   ██ ██   ██ ██         ║
║  █████     ███   ██    ██ ██   ██ ██   ██ ███████    ║
║  ██       ██ ██  ██    ██ ██   ██ ██   ██      ██    ║
║  ███████ ██   ██  ██████  ██████   █████  ███████    ║
║                                                       ║
║           << FORGE-MONDE EXODUS V2 >>                ║
║           << DUAL PIPELINE DOCTRINE >>               ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""

MENU = """
╔═══════════════════════════════════════════════════════╗
║                   AIGUILLAGE IMPERIAL                 ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║   [ 1 ]  MODE VIDEO-TO-VIDEO                         ║
║          Pipeline Sacré — Inchangé                   ║
║          Input : vidéo virale existante              ║
║          → analyse + reconstruction 4K/120FPS        ║
║                                                       ║
║   [ 2 ]  MODE FROM SCRATCH                           ║
║          Pipeline Forgé                              ║
║          Input : avatar GLB animé + audio optionnel  ║
║          → composition directe 4K/120FPS             ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""

# Chemins relatifs des orchestrateurs par mode
PIPELINE_ENTRYPOINTS = {
    1: {
        "label": "VIDEO-TO-VIDEO",
        "description": "Pipeline Sacré Mode 1",
        "units": {
            "U00": "00_CORTEX_HQ/CODEBASE/EXO_00_CORTEX.py",
            "U01": "01_ANIMATION_ENGINE/CODEBASE/EXO_01_TRANSMUTATION.py",
            "U02": "02_LOGISTICS_DEPOT/CODEBASE/EXO_02_LOGISTICS.py",
            "U03": "03_SCENOGRAPHY_DOCK/CODEBASE/EXO_03_SCENOGRAPHY.py",
            "U04": "04_PHOTOGRAPHY_WING/CODEBASE/EXO_04_PHOTOGRAPHY.py",
            "U05": "05_ALCHEMIST_LAB/CODEBASE/EXO_05_ALCHEMIST.py",
            "U06": "06_AIRCRAFT_CARRIER/CODEBASE/EXO_06_CARRIER.py",
        },
        "readme": "00_CORTEX_HQ/README_DEV.md",
    },
    2: {
        "label": "FROM SCRATCH",
        "description": "Pipeline Forgé Mode 2",
        "units": {
            "F01": "M2_01_ANIMATION_ENGINE/CODEBASE/EXO_M2_F01_ANIMATION.py",
            "F02": "M2_02_LOGISTICS_DEPOT/CODEBASE/EXO_M2_F02_LOGISTICS.py",
            "F03": "M2_03_SCENOGRAPHY_DOCK/CODEBASE/EXO_M2_F03_SCENOGRAPHY.py",
            "F04": "M2_04_PHOTOGRAPHY_WING/CODEBASE/EXO_M2_F04_PHOTOGRAPHY.py",
            "F05": "M2_05_ALCHEMIST_LAB/CODEBASE/EXO_M2_F05_ALCHEMIST.py",
            "F06": "M2_06_AIRCRAFT_CARRIER/CODEBASE/EXO_M2_F06_CARRIER.py",
        },
        "readme": "M2_01_ANIMATION_ENGINE/README_DEV.md",
    },
}


def print_banner() -> None:
    print(BANNER)
    print(f"  Launcher v{LAUNCHER_VERSION} — Doctrine Dual Pipeline")
    print()


def choose_mode_interactive() -> int:
    """Demande à l'Opérateur de choisir son mode. Retourne 1 ou 2."""
    print(MENU)
    while True:
        try:
            choice = input("Votre choix [1/2] : ").strip()
            if choice in ("1", "2"):
                return int(choice)
            print("  → Entrée invalide. Tapez 1 ou 2.")
        except (KeyboardInterrupt, EOFError):
            print("\n  → Annulé.")
            sys.exit(0)


def display_routing(mode: int, drive_root: str, extra_args: str, dry_run: bool) -> None:
    """Affiche le routing qui va être effectué."""
    pipeline = PIPELINE_ENTRYPOINTS[mode]
    print(f"\n  ROUTING → MODE {mode} : {pipeline['label']}")
    print(f"  Drive Root : {drive_root}")
    print(f"  Unités disponibles :")
    for unit_id, rel_path in pipeline["units"].items():
        abs_path = Path(drive_root) / rel_path
        exists = "✓" if abs_path.exists() else "✗ (absent)"
        print(f"    [{unit_id}] {rel_path} {exists}")
    if extra_args:
        print(f"  Args supplémentaires : {extra_args}")
    if dry_run:
        print("\n  [DRY-RUN] Aucune exécution. Routing affiché uniquement.")


def route_to_pipeline(
    mode: int,
    drive_root: str,
    unit: str | None = None,
    extra_args: str = "",
    dry_run: bool = False,
    verbose: bool = False,
) -> int:
    """
    Route vers le pipeline choisi.
    Retourne le code de sortie du processus lancé.
    LOI R-06 : cette fonction ne fait que router. Elle ne transforme rien.
    """
    pipeline = PIPELINE_ENTRYPOINTS[mode]
    units = pipeline["units"]

    if unit:
        unit_upper = unit.upper()
        if unit_upper not in units:
            print(f"  ERREUR : Unité '{unit}' inconnue pour Mode {mode}.")
            print(f"  Unités valides : {list(units.keys())}")
            return 1
        targets = {unit_upper: units[unit_upper]}
    else:
        targets = units

    if verbose or dry_run:
        display_routing(mode, drive_root, extra_args, dry_run)

    if dry_run:
        return 0

    print(f"\n  ► ROUTING MODE {mode} : {pipeline['label']}")
    print(f"  {pipeline['description']}")
    print(f"  L'Opérateur doit lancer les unités dans l'ordre ci-dessous :\n")

    for unit_id, rel_path in targets.items():
        abs_path = Path(drive_root) / rel_path
        if abs_path.exists():
            cmd = f"python {abs_path}"
            if extra_args:
                cmd += f" {extra_args}"
            print(f"    [{unit_id}] {cmd}")
        else:
            print(f"    [{unit_id}] ABSENT → {abs_path}")

    print()
    print("  → Exécution manuelle requise (transit manuel entre frégates).")
    print("  → LOI II : L'Empereur transfère les fichiers entre Frégates.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EXODUS V2 — Launcher Dual Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode", type=int, choices=[1, 2], default=None,
        help="Mode pipeline : 1=Video-to-Video, 2=From Scratch",
    )
    parser.add_argument(
        "--drive-root", type=str,
        default=os.environ.get("EXODUS_DRIVE_ROOT", "."),
        help="Racine Drive EXODUS_V2 (défaut: $EXODUS_DRIVE_ROOT ou '.')",
    )
    parser.add_argument(
        "--unit", type=str, default=None,
        help="Unité spécifique à afficher (ex: U00, F01). Omis = toutes.",
    )
    parser.add_argument(
        "--args", type=str, default="",
        dest="extra_args",
        help="Arguments à passer aux orchestrateurs (ex: '--verbose')",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Affiche le routing sans lancer",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Logs détaillés",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print_banner()

    mode = args.mode
    if mode is None:
        mode = choose_mode_interactive()

    return route_to_pipeline(
        mode=mode,
        drive_root=args.drive_root,
        unit=args.unit,
        extra_args=args.extra_args,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
