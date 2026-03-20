#!/usr/bin/env python3
"""
setup_inputs.py — Patch Session #003

Mission:
- Copier PRODUCTION_PLAN.JSON vers U03/IN_CORTEX_JSON/
- Copier ~240 depth maps vers U03/IN_MAP_RAW/ (gère zip avec sous-dossiers)
- Copier semantic_masks.json vers U03/IN_MAP_RAW/
- Si FUSE Colab bug (fichiers invisibles), fallback sur upload manuel via Colab.
"""

import argparse
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path


def _safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))


def _sync_drive():
    try:
        os.sync()
    except Exception:
        pass
    time.sleep(2)


def _collect_pngs_recursively(base_dir: Path) -> list[Path]:
    return sorted([p for p in base_dir.rglob("*.png") if p.is_file()])


def _copy_depth_maps_from_dir(depth_src_dir: Path, depth_dst_dir: Path, count: int) -> int:
    pngs = _collect_pngs_recursively(depth_src_dir)
    if not pngs:
        return 0

    depth_dst_dir.mkdir(parents=True, exist_ok=True)
    # Nettoyage pour rendre la reprise déterministe
    for old in depth_dst_dir.glob("*.png"):
        try:
            old.unlink()
        except OSError:
            pass

    selected = pngs[:count]
    for i, png in enumerate(selected):
        # Renommage stable pour éviter les collisions venant de zip multi-dossiers
        dst = depth_dst_dir / f"frame_{i:04d}.png"
        shutil.copy2(str(png), str(dst))
    return len(selected)


def _copy_depth_maps_from_zip(depth_zip_path: Path, depth_dst_dir: Path, count: int) -> int:
    if not depth_zip_path.exists():
        return 0

    depth_dst_dir.mkdir(parents=True, exist_ok=True)
    for old in depth_dst_dir.glob("*.png"):
        try:
            old.unlink()
        except OSError:
            pass

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Extraction récursive
        with zipfile.ZipFile(str(depth_zip_path), "r") as z:
            z.extractall(str(tmp_path))

        pngs = _collect_pngs_recursively(tmp_path)
        if not pngs:
            return 0

        selected = pngs[:count]
        for i, png in enumerate(selected):
            dst = depth_dst_dir / f"frame_{i:04d}.png"
            shutil.copy2(str(png), str(dst))
        return len(selected)


def _colab_manual_upload_fallback(
    u03_in_map_raw: Path,
    u03_in_cortex_json: Path,
    production_plan_dst: Path,
    semantic_masks_dst: Path,
) -> None:
    try:
        from google.colab import files  # type: ignore
    except Exception:
        raise RuntimeError("FUSE bug détecté mais Colab n'est pas disponible pour fallback upload.")

    print("[SETUP] Fallback upload manuel — merci de fournir les fichiers manquants.")
    uploaded = files.upload()

    # uploaded: dict(filename -> bytes)
    depth_zip_bytes = None
    for name, data in uploaded.items():
        n = name.lower()
        if n.endswith(".zip"):
            depth_zip_bytes = (name, data)
            continue

        if n == "semantic_masks.json" or "semantic_masks" in n:
            u03_in_map_raw.mkdir(parents=True, exist_ok=True)
            with open(semantic_masks_dst, "wb") as f:
                f.write(data)
            continue

        if "production_plan" in n and n.endswith(".json"):
            u03_in_cortex_json.mkdir(parents=True, exist_ok=True)
            with open(production_plan_dst, "wb") as f:
                f.write(data)
            continue

        if n.endswith(".png"):
            u03_in_map_raw.mkdir(parents=True, exist_ok=True)
            # écraser avec noms stables
            dst = u03_in_map_raw / name
            with open(dst, "wb") as f:
                f.write(data)

    if depth_zip_bytes:
        # Dézipper le contenu et remplir IN_MAP_RAW
        name, data = depth_zip_bytes
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_zip = Path(tmpdir) / name
            with open(tmp_zip, "wb") as f:
                f.write(data)
            # Copier 240 maps par défaut
            _copy_depth_maps_from_zip(tmp_zip, u03_in_map_raw, count=240)


def main() -> int:
    parser = argparse.ArgumentParser(description="setup_inputs — copier inputs U03")
    parser.add_argument("--drive-root", required=True, help="Racine Drive EXODUS")
    parser.add_argument("--depth-map-count", type=int, default=240)
    parser.add_argument(
        "--depth-maps-zip",
        default="",
        help="Chemin optionnel vers un zip contenant des depth maps (ex: DEPTH_MAP.zip)",
    )
    parser.add_argument(
        "--allow-upload-fallback",
        action="store_true",
        help="Active le fallback upload manuel si FUSE bug",
    )
    args = parser.parse_args()

    drive_root = Path(args.drive_root)
    cortex_out = drive_root / "00_CORTEX_HQ" / "OUT_PRODUCTION_PLAN"

    u03_unit = drive_root / "03_SCENOGRAPHY_DOCK"
    u03_in_cortex_json = u03_unit / "IN_CORTEX_JSON"
    u03_in_map_raw = u03_unit / "IN_MAP_RAW"

    production_plan_src = cortex_out / "PRODUCTION_PLAN.JSON"
    semantic_masks_src = cortex_out / "semantic_masks.json"
    depth_maps_src_dir = cortex_out / "DEPTH_MAP"

    production_plan_dst = u03_in_cortex_json / "PRODUCTION_PLAN.JSON"
    semantic_masks_dst = u03_in_map_raw / "semantic_masks.json"

    if not cortex_out.exists():
        print(f"[SETUP:ERROR] cortex_out introuvable: {cortex_out}", file=sys.stderr)
        return 1

    u03_in_cortex_json.mkdir(parents=True, exist_ok=True)
    u03_in_map_raw.mkdir(parents=True, exist_ok=True)

    # PRODUCTION_PLAN
    if not production_plan_src.exists():
        print(f"[SETUP:ERROR] PRODUCTION_PLAN.JSON introuvable: {production_plan_src}", file=sys.stderr)
        return 1
    _safe_copy(production_plan_src, production_plan_dst)

    # semantic_masks (optionnel mais recommandé)
    if semantic_masks_src.exists():
        _safe_copy(semantic_masks_src, semantic_masks_dst)
    else:
        print(f"[SETUP:WARN] semantic_masks.json introuvable: {semantic_masks_src}")

    # depth maps
    depth_dst_dir = u03_in_map_raw
    depth_count = 0

    if args.depth_maps_zip:
        zip_path = Path(args.depth_maps_zip)
        if zip_path.exists():
            print(f"[SETUP] Depth maps depuis zip: {zip_path}")
            depth_count = _copy_depth_maps_from_zip(zip_path, depth_dst_dir, args.depth_map_count)
        else:
            print(f"[SETUP:WARN] --depth-maps-zip introuvable: {zip_path}")

    if depth_count == 0:
        if depth_maps_src_dir.exists():
            print(f"[SETUP] Depth maps depuis dossier: {depth_maps_src_dir}")
            depth_count = _copy_depth_maps_from_dir(depth_maps_src_dir, depth_dst_dir, args.depth_map_count)
        else:
            print(f"[SETUP:ERROR] DEPTH_MAP introuvable: {depth_maps_src_dir}", file=sys.stderr)
            return 1

    _sync_drive()

    # Vérif après sync
    pngs_after = list(depth_dst_dir.glob("*.png"))
    if not pngs_after:
        print("[SETUP:WARN] Aucun PNG visible après copie (FUSE bug probable).")
        if args.allow_upload_fallback:
            _colab_manual_upload_fallback(
                u03_in_map_raw=u03_in_map_raw,
                u03_in_cortex_json=u03_in_cortex_json,
                production_plan_dst=production_plan_dst,
                semantic_masks_dst=semantic_masks_dst,
            )
            _sync_drive()
        else:
            print("[SETUP:ERROR] fallback upload non activé. Relance avec --allow-upload-fallback.", file=sys.stderr)
            return 1

    final_pngs = list(depth_dst_dir.glob("*.png"))
    print(f"[SETUP:OK] Inputs U03 prêts: depth_maps={len(final_pngs)} (cible={args.depth_map_count})")
    print(f"[SETUP:OK] production_plan={production_plan_dst.exists()} ; semantic_masks={semantic_masks_dst.exists()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

