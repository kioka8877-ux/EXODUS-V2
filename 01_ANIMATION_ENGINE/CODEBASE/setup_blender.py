#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     EXODUS V2 — SETUP BLENDER — Installation auto Blender 4.0              ║
║     Installe Blender localement sur Colab ET le sauvegarde sur Drive.      ║
║     Usage: python setup_blender.py --drive-root /content/drive/MyDrive/EXODUS_V2
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import subprocess
import shutil
import sys
import os
import argparse
from pathlib import Path

BLENDER_VERSION = "4.0.0"
BLENDER_DIR = f"blender-{BLENDER_VERSION}-linux-x64"
BLENDER_URL = f"https://download.blender.org/release/Blender4.0/{BLENDER_DIR}.tar.xz"
BLENDER_LOCAL = f"/opt/{BLENDER_DIR}/blender"
BLENDER_LOCAL_DIR = f"/opt/{BLENDER_DIR}"


def find_blender() -> str | None:
    """Cherche Blender dans les emplacements connus."""
    candidates = [
        BLENDER_LOCAL,
        f"/opt/blender-4.0.2-linux-x64/blender",
        "/usr/local/bin/blender",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def install_blender_local() -> str:
    """Installe Blender localement dans /opt/ si absent."""
    existing = find_blender()
    if existing:
        print(f"✅ Blender déjà installé: {existing}")
        return existing

    print(f"⬇️  Téléchargement Blender {BLENDER_VERSION}...")
    subprocess.run([
        "wget", "-q", "--show-progress",
        "-O", "/tmp/blender.tar.xz", BLENDER_URL
    ], check=True)

    print("📦 Extraction vers /opt/...")
    subprocess.run(["tar", "-xf", "/tmp/blender.tar.xz", "-C", "/opt/"], check=True)
    subprocess.run(["rm", "-f", "/tmp/blender.tar.xz"])

    print(f"✅ Blender installé: {BLENDER_LOCAL}")
    return BLENDER_LOCAL


def save_to_drive(drive_root: str) -> str:
    """Copie Blender sur Drive pour réutilisation entre sessions."""
    drive_blender_dir = Path(drive_root) / "EXODUS_AI_MODELS" / BLENDER_DIR
    drive_blender_bin = drive_blender_dir / "blender"

    if drive_blender_bin.exists():
        print(f"✅ Blender déjà sur Drive: {drive_blender_bin}")
        return str(drive_blender_bin)

    local_dir = Path(BLENDER_LOCAL_DIR)
    if not local_dir.exists():
        print("⚠️  Blender local absent — impossible de copier sur Drive")
        return ""

    print(f"📋 Copie Blender vers Drive ({drive_blender_dir})...")
    drive_blender_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(local_dir), str(drive_blender_dir))
    print(f"✅ Blender sauvegardé sur Drive")
    return str(drive_blender_bin)


def main():
    parser = argparse.ArgumentParser(description="EXODUS V2 — Setup Blender 4.0")
    parser.add_argument("--drive-root", required=True, help="Racine du Drive EXODUS")
    parser.add_argument("--local-only", action="store_true", help="Installer localement sans copier sur Drive")
    args = parser.parse_args()

    print("═" * 60)
    print(f"  EXODUS V2 — SETUP BLENDER {BLENDER_VERSION}")
    print("═" * 60)

    # 1. Installer local
    blender_bin = install_blender_local()

    # 2. Sauvegarder sur Drive (pour sessions futures)
    if not args.local_only:
        drive_bin = save_to_drive(args.drive_root)
        if drive_bin:
            blender_bin = drive_bin

    # 3. Définir variable d'environnement
    os.environ["BLENDER_PATH"] = blender_bin
    print(f"\n✅ BLENDER_PATH = {blender_bin}")

    # 4. Vérification
    r = subprocess.run([blender_bin, "--version"], capture_output=True, text=True)
    print(f"   {r.stdout.splitlines()[0] if r.stdout else 'version inconnue'}")
    print("═" * 60)


if __name__ == "__main__":
    main()
