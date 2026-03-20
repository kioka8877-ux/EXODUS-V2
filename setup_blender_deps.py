#!/usr/bin/env python3
"""
setup_blender_deps.py — Patch Session #003

Mission:
1) Vérifier Blender (portable) dans le Drive, sinon le télécharger et l'extraire.
2) Installer les dépendances Python *dans le Python embarqué Blender*:
   - Pillow
   - numpy
   - opencv-python
3) Vérifier que PIL fonctionne.
"""

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


BLENDER_VERSION = "4.0.0"
BLENDER_DIRNAME = f"blender-{BLENDER_VERSION}-linux-x64"
BLENDER_URL = f"https://download.blender.org/release/Blender4.0/{BLENDER_DIRNAME}.tar.xz"


def _download(url: str, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(dest_path, "wb") as f:
        shutil.copyfileobj(r, f)


def find_blender_bin(drive_root: Path) -> Path | None:
    candidates = [
        drive_root / "EXODUS_AI_MODELS" / BLENDER_DIRNAME / "blender",
        Path("/opt") / BLENDER_DIRNAME / "blender",
        Path("/opt/blender-4.0.2-linux-x64/blender"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def ensure_blender_executable(blender_bin: Path) -> Path:
    # Sur Drive, les bits executables peuvent être perdus.
    # Si blender_bin n'est pas exécutable, on duplique le dossier localement.
    if os.access(str(blender_bin), os.X_OK):
        return blender_bin

    blender_dir = blender_bin.parent
    local_dst_dir = Path("/opt") / blender_dir.name
    local_dst_dir.mkdir(parents=True, exist_ok=True)

    if not (local_dst_dir / "blender").exists():
        print(f"[SETUP] Blender non exécutable — copie locale: {local_dst_dir}")
        shutil.copytree(str(blender_dir), str(local_dst_dir), dirs_exist_ok=True)

    local_bin = local_dst_dir / "blender"
    try:
        os.chmod(str(local_bin), 0o755)
    except Exception:
        pass
    return local_bin


def blender_python_from_bin(blender_bin: Path) -> Path:
    blender_dir = blender_bin.parent  # blender-4.0.0-linux-x64/
    python_root = blender_dir / "python" / "bin"
    if not python_root.exists():
        raise FileNotFoundError(f"Python Blender introuvable: {python_root}")

    # Blender 4.0 embarque généralement python3.10
    for candidate in ["python3.10", "python3.11", "python3.9", "python"]:
        p = python_root / candidate
        if p.exists():
            return p

    # fallback: premier python3.*
    ps = sorted(python_root.glob("python3.*"))
    if ps:
        return ps[0]

    raise FileNotFoundError(f"Aucun binaire python trouvé dans: {python_root}")


def install_deps_into_blender_python(blender_python: Path) -> None:
    # Installer/mettre à jour pip + libs nécessaires
    cmd = [
        str(blender_python),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "pip",
        "setuptools",
        "wheel",
        "pillow",
        "numpy",
        "opencv-python",
    ]
    subprocess.run(cmd, check=True)

    # Vérifier l'import côté Blender Python
    verify = [
        str(blender_python),
        "-c",
        "import PIL, numpy; import cv2; print('deps_ok')",
    ]
    subprocess.run(verify, check=True)


def ensure_blender_on_drive(drive_root: Path) -> Path:
    blender_bin = find_blender_bin(drive_root)
    if blender_bin:
        return ensure_blender_executable(blender_bin)

    archive_tmp = Path("/tmp") / f"{BLENDER_DIRNAME}.tar.xz"
    blender_models_dir = drive_root / "EXODUS_AI_MODELS"
    extract_parent = blender_models_dir

    print(f"[SETUP] Blender absent — téléchargement: {BLENDER_URL}")
    _download(BLENDER_URL, archive_tmp)

    print(f"[SETUP] Extraction vers: {extract_parent}")
    subprocess.run(["tar", "-xf", str(archive_tmp), "-C", str(extract_parent)], check=True)
    try:
        archive_tmp.unlink()
    except OSError:
        pass

    blender_bin = find_blender_bin(drive_root)
    if not blender_bin:
        raise RuntimeError("Blender téléchargé mais binaire introuvable après extraction.")
    return ensure_blender_executable(blender_bin)


def main() -> int:
    parser = argparse.ArgumentParser(description="setup_blender_deps — Blender + deps Blender Python")
    parser.add_argument("--drive-root", required=True, help="Racine du Drive EXODUS")
    args = parser.parse_args()

    drive_root = Path(args.drive_root)
    if not drive_root.exists():
        print(f"[SETUP:ERROR] drive-root introuvable: {drive_root}", file=sys.stderr)
        return 1

    blender_bin = ensure_blender_on_drive(drive_root)
    print(f"[SETUP] Blender OK: {blender_bin}")

    blender_python = blender_python_from_bin(blender_bin)
    print(f"[SETUP] Blender Python OK: {blender_python}")

    install_deps_into_blender_python(blender_python)
    print("[SETUP:OK] Dépendances installées et test import OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

