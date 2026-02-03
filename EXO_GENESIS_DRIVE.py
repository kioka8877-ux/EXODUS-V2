#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    EXODUS GENESIS — Drive Structure Creator                  ║
║              Crée l'Architecture Sacrée sur Google Drive                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 2.0.0                                                              ║
║  Mission: Générer la structure complète EXODUS-V2 sur le Drive              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage (Colab):
    python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2

Options:
    --drive-root    Racine du Drive où créer la structure
    --dry-run       Affiche la structure sans la créer
    --force         Écrase les fichiers existants
    --verbose       Logs détaillés

Exemple:
    # Mode dry-run pour voir la structure
    python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/EXODUS --dry-run

    # Création complète
    python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/EXODUS
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

GENESIS_VERSION = "2.0.0"

SACRED_ARCHITECTURE = {
    "00_CORTEX_HQ": {
        "description": "Analyse vidéo → Plan de production JSON",
        "inputs": {
            "IN_VIDEO_SOURCE": "Vidéo source à analyser"
        },
        "outputs": {
            "OUT_PRODUCTION_PLAN": "PRODUCTION_PLAN.JSON généré"
        },
        "subfolders": {
            "CODEBASE": []
        }
    },
    "01_ANIMATION_ENGINE": {
        "description": "Extraction MoCap (corps + visage) → Animation fusionnée",
        "inputs": {
            "IN_CORTEX_JSON": "PRODUCTION_PLAN.JSON (copie de U00)",
            "IN_MIXAMO_BASE": "body_motion.fbx (MoCap)"
        },
        "outputs": {
            "OUT_MOTION_DATA": "Animation fusionnée .abc/.blend"
        },
        "subfolders": {
            "CODEBASE": []
        }
    },
    "02_LOGISTICS_DEPOT": {
        "description": "Assemblage Acteur/Props → Alembic équipé",
        "inputs": {
            "IN_MOTION_DATA": ".blend de U01",
            "IN_ROBLOX_AVATAR": "Avatar Roblox .blend",
            "IN_PROPS_LIBRARY": "Bibliothèque props"
        },
        "outputs": {
            "OUT_BAKED_ACTORS": "Acteurs équipés .abc"
        },
        "subfolders": {
            "CODEBASE": []
        }
    },
    "03_SCENOGRAPHY_DOCK": {
        "description": "Construction décors PBR/HDRi",
        "inputs": {
            "IN_MAP_RAW": {
                "description": "Carte Minecraft brute + assets",
                "subfolders": ["hdri_library", "environment_assets"]
            },
            "IN_CORTEX_JSON": "PRODUCTION_PLAN.JSON"
        },
        "outputs": {
            "OUT_PREMIUM_SCENE": "Scènes environnement .blend"
        },
        "subfolders": {
            "CODEBASE": []
        }
    },
    "04_PHOTOGRAPHY_WING": {
        "description": "Tracking caméra + Éclairage cinématique",
        "inputs": {
            "IN_VIDEO_SOURCE": "Vidéo de référence",
            "IN_SCENE_REF": "Référence scène 3D (.blend de U03)"
        },
        "outputs": {
            "OUT_CAMERA_LOGIC": "Scènes avec caméra/lumières configurées"
        },
        "subfolders": {
            "CODEBASE": []
        }
    },
    "05_ALCHEMIST_LAB": {
        "description": "Post-production + Color Grading",
        "inputs": {
            "IN_RAW_FRAMES": "Séquences EXR rendues"
        },
        "outputs": {
            "OUT_FINAL_FRAMES": "Frames gradées et composées"
        },
        "subfolders": {
            "CODEBASE": [],
            "LUTS": []
        }
    },
    "06_AIRCRAFT_CARRIER": {
        "description": "Assemblage final + RIFE 120FPS + Export",
        "inputs": {
            "IN_ASSEMBLY_KIT": "Frames finales + audio"
        },
        "outputs": {
            "OUT_FINAL_MOVIE": "Vidéo finale 4K/120FPS"
        },
        "subfolders": {
            "CODEBASE": []
        }
    },
    "EXODUS_AI_MODELS": {
        "description": "Modèles IA partagés entre unités",
        "inputs": {},
        "outputs": {},
        "subfolders": {
            "BLENDER": [],
            "EMOCA": [],
            "RIFE": [],
            "REALESRGAN": [],
            "McPrep": [],
            "HDRi": []
        }
    }
}


def print_banner():
    """Affiche le banner EXODUS."""
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    EXODUS GENESIS — Drive Structure Creator                  ║")
    print(f"║              Version {GENESIS_VERSION}                                                 ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()


def create_readme_for_unit(unit_name: str, unit_config: dict) -> str:
    """Génère le contenu README.md pour une unité."""
    lines = [
        f"# {unit_name}",
        "",
        f"> {unit_config.get('description', 'Unité EXODUS')}",
        "",
        "## 📥 Inputs",
        ""
    ]
    
    inputs = unit_config.get("inputs", {})
    if inputs:
        for folder, desc in inputs.items():
            if isinstance(desc, dict):
                lines.append(f"### `{folder}/`")
                lines.append(f"{desc.get('description', '')}")
                if desc.get('subfolders'):
                    lines.append("")
                    lines.append("Sous-dossiers:")
                    for sub in desc['subfolders']:
                        lines.append(f"- `{sub}/`")
                lines.append("")
            else:
                lines.append(f"- **`{folder}/`** — {desc}")
    else:
        lines.append("_Aucun input requis_")
    
    lines.extend([
        "",
        "## 📤 Outputs",
        ""
    ])
    
    outputs = unit_config.get("outputs", {})
    if outputs:
        for folder, desc in outputs.items():
            lines.append(f"- **`{folder}/`** — {desc}")
    else:
        lines.append("_Aucun output_")
    
    lines.extend([
        "",
        "---",
        f"_Généré par EXODUS GENESIS v{GENESIS_VERSION}_"
    ])
    
    return "\n".join(lines)


def create_structure(
    drive_root: Path,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """Crée la structure complète sur le Drive."""
    
    report = {
        "created_dirs": [],
        "created_files": [],
        "skipped": [],
        "errors": []
    }
    
    def log(msg: str, level: str = "INFO"):
        if verbose or level in ["ERROR", "WARN"]:
            prefix = {"INFO": "→", "OK": "✓", "WARN": "⚠", "ERROR": "✗"}
            print(f"[GENESIS:{level}] {prefix.get(level, '')} {msg}")
    
    if dry_run:
        print("\n🔍 MODE DRY-RUN — Aucun fichier ne sera créé\n")
    
    if not drive_root.exists():
        if dry_run:
            log(f"Créerait: {drive_root}")
        else:
            drive_root.mkdir(parents=True, exist_ok=True)
            log(f"Créé: {drive_root}", "OK")
        report["created_dirs"].append(str(drive_root))
    
    for unit_name, unit_config in SACRED_ARCHITECTURE.items():
        unit_path = drive_root / unit_name
        
        if not unit_path.exists():
            if dry_run:
                log(f"Créerait: {unit_path}")
            else:
                unit_path.mkdir(parents=True, exist_ok=True)
                log(f"Créé: {unit_path}", "OK")
            report["created_dirs"].append(str(unit_path))
        else:
            log(f"Existe: {unit_path}")
            report["skipped"].append(str(unit_path))
        
        inputs = unit_config.get("inputs", {})
        for folder_name, folder_config in inputs.items():
            folder_path = unit_path / folder_name
            
            if not folder_path.exists():
                if dry_run:
                    log(f"  Créerait: {folder_path}")
                else:
                    folder_path.mkdir(parents=True, exist_ok=True)
                report["created_dirs"].append(str(folder_path))
            
            gitkeep = folder_path / ".gitkeep"
            if not dry_run and not gitkeep.exists():
                gitkeep.touch()
                report["created_files"].append(str(gitkeep))
            
            if isinstance(folder_config, dict) and folder_config.get("subfolders"):
                for subfolder in folder_config["subfolders"]:
                    sub_path = folder_path / subfolder
                    if not sub_path.exists():
                        if dry_run:
                            log(f"    Créerait: {sub_path}")
                        else:
                            sub_path.mkdir(parents=True, exist_ok=True)
                        report["created_dirs"].append(str(sub_path))
                    
                    sub_gitkeep = sub_path / ".gitkeep"
                    if not dry_run and not sub_gitkeep.exists():
                        sub_gitkeep.touch()
                        report["created_files"].append(str(sub_gitkeep))
        
        outputs = unit_config.get("outputs", {})
        for folder_name in outputs.keys():
            folder_path = unit_path / folder_name
            
            if not folder_path.exists():
                if dry_run:
                    log(f"  Créerait: {folder_path}")
                else:
                    folder_path.mkdir(parents=True, exist_ok=True)
                report["created_dirs"].append(str(folder_path))
            
            gitkeep = folder_path / ".gitkeep"
            if not dry_run and not gitkeep.exists():
                gitkeep.touch()
                report["created_files"].append(str(gitkeep))
        
        subfolders = unit_config.get("subfolders", {})
        for folder_name, sub_items in subfolders.items():
            folder_path = unit_path / folder_name
            
            if not folder_path.exists():
                if dry_run:
                    log(f"  Créerait: {folder_path}")
                else:
                    folder_path.mkdir(parents=True, exist_ok=True)
                report["created_dirs"].append(str(folder_path))
            
            gitkeep = folder_path / ".gitkeep"
            if not dry_run and not gitkeep.exists():
                gitkeep.touch()
                report["created_files"].append(str(gitkeep))
            
            for sub_item in sub_items:
                sub_path = folder_path / sub_item
                if not sub_path.exists():
                    if dry_run:
                        log(f"    Créerait: {sub_path}")
                    else:
                        sub_path.mkdir(parents=True, exist_ok=True)
                    report["created_dirs"].append(str(sub_path))
        
        readme_path = unit_path / "README.md"
        if not readme_path.exists() or force:
            if dry_run:
                log(f"  Créerait: {readme_path}")
            else:
                readme_content = create_readme_for_unit(unit_name, unit_config)
                readme_path.write_text(readme_content, encoding="utf-8")
                log(f"  README créé: {readme_path}", "OK")
            report["created_files"].append(str(readme_path))
    
    return report


def print_structure_preview():
    """Affiche un aperçu de la structure à créer."""
    print("\n📂 STRUCTURE EXODUS-V2 (Architecture Sacrée)")
    print("=" * 60)
    print()
    
    for unit_name, unit_config in SACRED_ARCHITECTURE.items():
        print(f"├── {unit_name}/")
        
        inputs = unit_config.get("inputs", {})
        outputs = unit_config.get("outputs", {})
        subfolders = unit_config.get("subfolders", {})
        
        all_folders = list(inputs.keys()) + list(outputs.keys()) + list(subfolders.keys())
        
        for i, folder_name in enumerate(all_folders):
            is_last = (i == len(all_folders) - 1)
            prefix = "└──" if is_last else "├──"
            
            if folder_name in inputs:
                folder_config = inputs[folder_name]
                desc = folder_config.get("description", folder_config) if isinstance(folder_config, dict) else folder_config
                print(f"│   {prefix} {folder_name}/  ← {desc[:40]}...")
                
                if isinstance(folder_config, dict) and folder_config.get("subfolders"):
                    for sub in folder_config["subfolders"]:
                        print(f"│   │   ├── {sub}/")
            
            elif folder_name in outputs:
                desc = outputs[folder_name]
                print(f"│   {prefix} {folder_name}/  → {desc[:40]}...")
            
            elif folder_name in subfolders:
                print(f"│   {prefix} {folder_name}/")
                for sub in subfolders[folder_name]:
                    print(f"│   │   ├── {sub}/")
        
        print("│")
    
    print()


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description=f'EXODUS GENESIS - Drive Structure Creator v{GENESIS_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Prévisualisation (dry-run)
  python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/EXODUS --dry-run

  # Création complète
  python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/EXODUS

  # Création avec écrasement des README
  python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/EXODUS --force
        """
    )
    
    parser.add_argument('--drive-root', required=True,
                        help='Racine du Drive où créer la structure')
    parser.add_argument('--dry-run', action='store_true',
                        help='Affiche la structure sans la créer')
    parser.add_argument('--force', action='store_true',
                        help='Écrase les fichiers existants')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Logs détaillés')
    parser.add_argument('--show-structure', action='store_true',
                        help='Affiche uniquement la structure')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.show_structure:
        print_structure_preview()
        return 0
    
    drive_root = Path(args.drive_root)
    
    print(f"📍 Drive Root: {drive_root}")
    print(f"🔧 Options: dry-run={args.dry_run}, force={args.force}, verbose={args.verbose}")
    print()
    
    print_structure_preview()
    
    if args.dry_run:
        print("\n🔍 Analyse des changements nécessaires:\n")
    else:
        print("\n🚀 Création de la structure:\n")
    
    report = create_structure(
        drive_root=drive_root,
        dry_run=args.dry_run,
        force=args.force,
        verbose=args.verbose
    )
    
    print("\n" + "=" * 60)
    print("📊 RAPPORT DE GÉNÉRATION")
    print("=" * 60)
    print(f"  Dossiers créés:  {len(report['created_dirs'])}")
    print(f"  Fichiers créés:  {len(report['created_files'])}")
    print(f"  Éléments skippés: {len(report['skipped'])}")
    print(f"  Erreurs:         {len(report['errors'])}")
    
    if report['errors']:
        print("\n⚠️ Erreurs rencontrées:")
        for error in report['errors']:
            print(f"  - {error}")
    
    if args.dry_run:
        print("\n✨ Mode dry-run terminé. Aucun fichier n'a été créé.")
        print("   Relancez sans --dry-run pour créer la structure.")
    else:
        print("\n✅ GÉNÈSE COMPLÈTE — Architecture Sacrée créée!")
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
