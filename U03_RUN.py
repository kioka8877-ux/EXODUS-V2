#!/usr/bin/env python3
"""
U03_RUN.py — Patch Session #003

Objectif:
Automatiser U03 SCENOGRAPHY pour qu'elle fonctionne du premier coup.

Séquence d'exécution (résumé):
1) Monter Drive (force remount)
2) Attendre la synchro FUSE
3) setup_blender_deps.py (Blender + deps Blender Python)
4) Clone GitHub (shallow) si CODEBASE incomplet, puis copie phantom_link.py sur la racine Drive
5) setup_inputs.py (PRODUCTION_PLAN + 240 depth maps + semantic_masks.json)
6) Lancer EXO_03_SCENOGRAPHY.py (qui appelle Blender headless + layer_assembler.py)
7) Afficher rapport final (outputs visibles sur Drive)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


DEFAULT_REPO_URL = "https://github.com/kioka8877-ux/EXODUS-V2"
DEFAULT_VRAM_PROFILE = "colab_t4"


def _has_cmd(cmd: str) -> bool:
    from shutil import which

    return which(cmd) is not None


def mount_drive_if_colab() -> None:
    try:
        from google.colab import drive  # type: ignore

        # Force remount pour réduire le bug "fichiers invisibles".
        drive.mount("/content/drive", force_remount=True)
    except Exception:
        # Pas en Colab (execution locale): ignorer.
        pass


def _download_zip(repo_url: str, dest_zip_path: Path) -> None:
    # Télécharge main.zip (fallback si git absent)
    # Note: pour un clone fidèle d'une branche, utiliser git serait mieux.
    if repo_url.endswith("/"):
        repo_url = repo_url[:-1]
    zip_url = f"{repo_url}/archive/refs/heads/main.zip"
    with urllib.request.urlopen(zip_url) as r, open(dest_zip_path, "wb") as f:
        shutil.copyfileobj(r, f)


def clone_repo_shallow(repo_url: str, dest_dir: Path) -> bool:
    dest_dir = Path(dest_dir)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    if _has_cmd("git"):
        cmd = ["git", "clone", "--depth", "1", repo_url, str(dest_dir)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[U03_RUN:WARN] git clone a échoué, fallback zip. stderr:\n{res.stderr[-800:]}")
        else:
            return True

    # fallback: zip
    tmp_zip = Path(tempfile.gettempdir()) / "EXODUS_V2_main.zip"
    print(f"[U03_RUN] Téléchargement ZIP (fallback): {tmp_zip}")
    _download_zip(repo_url, tmp_zip)
    # Extraction
    import zipfile

    with zipfile.ZipFile(str(tmp_zip), "r") as z:
        z.extractall(str(dest_dir.parent))

    # Finder du dossier extrait
    candidates = [p for p in dest_dir.parent.iterdir() if p.is_dir() and p.name.startswith("EXODUS-V2-")]
    if not candidates:
        # parfois le nom ressemble à exodus-repo-main
        candidates = [p for p in dest_dir.parent.iterdir() if p.is_dir()]
    # Prendre le premier candidat et renommer
    extracted = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    # Renommer pour correspondre à dest_dir
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    extracted.rename(dest_dir)
    return True


def ensure_unit_codebase(drive_root: Path, repo_root: Path) -> None:
    dst_codebase = drive_root / "03_SCENOGRAPHY_DOCK" / "CODEBASE"
    src_codebase = repo_root / "03_SCENOGRAPHY_DOCK" / "CODEBASE"

    if dst_codebase.exists() and (dst_codebase / "layer_assembler.py").exists():
        return

    if not src_codebase.exists():
        print(f"[U03_RUN:WARN] src_codebase introuvable: {src_codebase}")
        return

    dst_codebase.mkdir(parents=True, exist_ok=True)
    for p in src_codebase.iterdir():
        if p.is_file():
            shutil.copy2(str(p), str(dst_codebase / p.name))


def ensure_phantom_link_at_drive_root(drive_root: Path, repo_root: Path) -> None:
    phantom_dst = drive_root / "phantom_link.py"
    if phantom_dst.exists():
        return

    phantom_src = repo_root / "phantom_link.py"
    if phantom_src.exists():
        shutil.copy2(str(phantom_src), str(phantom_dst))
        print("[U03_RUN] phantom_link.py copié sur la racine Drive.")
    else:
        print(f"[U03_RUN:WARN] phantom_link.py introuvable dans repo clone: {phantom_src}")


def ensure_root_scripts(drive_root: Path, repo_root: Path) -> None:
    """S'assure que les scripts wrapper existent dans la racine Drive."""
    for fname in ["setup_blender_deps.py", "setup_inputs.py"]:
        src = repo_root / fname
        dst = drive_root / fname
        if dst.exists():
            continue
        if src.exists():
            shutil.copy2(str(src), str(dst))
            print(f"[U03_RUN] {fname} copié sur la racine Drive.")
        else:
            print(f"[U03_RUN:WARN] Script introuvable dans repo clone: {src}")


def run_setup_script(script_path: Path, drive_root: Path, extra_args: list[str] | None = None) -> None:
    if not script_path.exists():
        raise FileNotFoundError(f"Script manquant: {script_path}")
    cmd = [sys.executable, str(script_path), "--drive-root", str(drive_root)]
    if extra_args:
        cmd.extend(extra_args)
    print(f"[U03_RUN] Lancement: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_exo_03_scenography(
    drive_root: Path,
    vram_profile: str,
    exposure: float,
    verbose: bool,
) -> None:
    u03 = drive_root / "03_SCENOGRAPHY_DOCK"
    codebase = u03 / "CODEBASE"
    script = codebase / "EXO_03_SCENOGRAPHY.py"

    production_plan = u03 / "IN_CORTEX_JSON" / "PRODUCTION_PLAN.JSON"

    output_dir = u03 / "OUT_PREMIUM_SCENE"
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(script),
        "--drive-root",
        str(drive_root),
        "--production-plan",
        str(production_plan),
        "--output-dir",
        str(output_dir),
        "--vram-profile",
        vram_profile,
        "--exposure",
        str(exposure),
    ]
    if verbose:
        cmd.append("--verbose")

    print(f"[U03_RUN] Lancement EXO_03_SCENOGRAPHY: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="U03_RUN — automatisation Patch Session #003")
    default_drive_root = str(Path(__file__).resolve().parent)
    parser.add_argument(
        "--drive-root",
        default=default_drive_root,
        help="Racine Drive EXODUS (par défaut: dossier où se trouve U03_RUN.py)",
    )
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="Repo GitHub EXODUS")
    parser.add_argument("--vram-profile", default=DEFAULT_VRAM_PROFILE, choices=["colab_t4", "colab_a100", "local_low"])
    parser.add_argument("--exposure", type=float, default=1.0, help="World Sync strength")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--depth-map-count", type=int, default=240)
    args = parser.parse_args()

    drive_root = Path(args.drive_root)

    # 1) Drive mount
    mount_drive_if_colab()
    time.sleep(10)  # laisse FUSE se stabiliser

    # 2) Blender deps
    # Chemins supposés: scripts déjà sur la racine Drive.
    run_setup_script(drive_root / "setup_blender_deps.py", drive_root)

    # 3) Clone repo pour reconstituer CODEBASE + phantom_link si nécessaire
    clone_dir = Path("/tmp") / "exodus-v2-clone"
    try:
        repo_ok = clone_repo_shallow(args.repo_url, clone_dir)
    except Exception as e:
        print(f"[U03_RUN:WARN] Clone repo impossible, on tente avec code Drive existant. Erreur: {e}")
        repo_ok = False

    if repo_ok:
        ensure_unit_codebase(drive_root=drive_root, repo_root=clone_dir)
        ensure_phantom_link_at_drive_root(drive_root=drive_root, repo_root=clone_dir)
        ensure_root_scripts(drive_root=drive_root, repo_root=clone_dir)

    # 4) Inputs U03
    run_setup_script(
        drive_root / "setup_inputs.py",
        drive_root,
        extra_args=["--depth-map-count", str(args.depth_map_count), "--allow-upload-fallback"],
    )

    # 5) Run orchestration (Blender headless + layer_assembler)
    run_exo_03_scenography(
        drive_root=drive_root,
        vram_profile=args.vram_profile,
        exposure=args.exposure,
        verbose=args.verbose,
    )

    # 6) Rapport final (vérifs simples)
    out_dir = drive_root / "03_SCENOGRAPHY_DOCK" / "OUT_PREMIUM_SCENE"
    blends = sorted(out_dir.glob("environment_*.blend"))
    report = out_dir / "scenography_report.json"
    assembler = out_dir / "assembler_results.json"

    print("\n" + "=" * 70)
    print("[U03_RUN] Résumé outputs")
    print("=" * 70)
    print(f"environment_*.blend: {len(blends)}")
    print(f"assembler_results.json: {'OK' if assembler.exists() else 'MISSING'}")
    print(f"scenography_report.json: {'OK' if report.exists() else 'MISSING'}")
    print("=" * 70)

    if not report.exists():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

