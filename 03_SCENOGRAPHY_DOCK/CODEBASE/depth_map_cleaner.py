#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEPTH MAP CLEANER — Anti-Ghosting pour Depth Maps                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Aplatit les zones de personnages/caractères détectées par SAM AVANT que    ║
║  le displacement mesh ne les consomme. Empêche les silhouettes humaines     ║
║  de créer des bosses 3D parasites sur le terrain.                           ║
║                                                                              ║
║  Python pur — AUCUNE dépendance Blender (importable côté CPU sans bpy).     ║
║  Dépendances : Pillow (PIL), numpy, json, pathlib, os                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


DEFAULT_LABELS_TO_FLATTEN: list[str] = [
    "person", "character", "human", "animal",
]


def _rasterize_polygon(
    polygon: list[list[int]], width: int, height: int,
) -> np.ndarray:
    mask_img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask_img)
    if len(polygon) >= 3:
        flat_poly = [(int(p[0]), int(p[1])) for p in polygon]
        draw.polygon(flat_poly, fill=255)
    return np.array(mask_img, dtype=np.uint8)


def _dilate_mask(mask: np.ndarray, iterations: int = 2) -> np.ndarray:
    result = mask.copy()
    for _ in range(iterations):
        expanded = result.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                shifted = np.roll(np.roll(result, dy, axis=0), dx, axis=1)
                expanded = np.maximum(expanded, shifted)
        result = expanded
    return result


def _compute_border_median(
    depth_array: np.ndarray, binary_mask: np.ndarray, dilation_px: int = 3,
) -> float:
    dilated = _dilate_mask(binary_mask, iterations=dilation_px)
    border = (dilated > 0) & (binary_mask == 0)
    border_values = depth_array[border]
    if len(border_values) == 0:
        return float(np.median(depth_array))
    return float(np.median(border_values))


def clean_depth_map(
    depth_map_path: str,
    semantic_masks_path: str,
    output_path: str,
    labels_to_flatten: list[str] | None = None,
    feather_radius: int = 4,
) -> dict:
    """
    Nettoie un depth map en aplatissant les zones de personnages.

    Returns:
        dict avec : {
            "input": str,
            "output": str,
            "masks_applied": int,
            "labels_found": list[str],
            "pixels_modified": int,
        }
    """
    if labels_to_flatten is None:
        labels_to_flatten = list(DEFAULT_LABELS_TO_FLATTEN)

    depth_img = Image.open(depth_map_path)
    is_16bit = depth_img.mode in ("I", "I;16")
    if is_16bit:
        depth_array = np.array(depth_img, dtype=np.float64)
    else:
        depth_img = depth_img.convert("L")
        depth_array = np.array(depth_img, dtype=np.float64)

    height, width = depth_array.shape

    with open(semantic_masks_path, "r", encoding="utf-8") as f:
        mask_data = json.load(f)

    masks = mask_data.get("masks", [])
    masks_applied = 0
    labels_found: list[str] = []
    total_pixels_modified = 0

    for mask_entry in masks:
        label = mask_entry.get("label", "")
        if label not in labels_to_flatten:
            continue

        polygon = mask_entry.get("polygon", [])
        if len(polygon) < 3:
            continue

        labels_found.append(label)

        binary_mask = _rasterize_polygon(polygon, width, height)

        fill_value = _compute_border_median(depth_array, binary_mask)

        mask_img = Image.fromarray(binary_mask)
        blurred = mask_img.filter(ImageFilter.BoxBlur(feather_radius))
        feathered = np.array(blurred, dtype=np.float64) / 255.0

        depth_array = depth_array * (1.0 - feathered) + fill_value * feathered

        pixel_count = int(np.sum(binary_mask > 0))
        total_pixels_modified += pixel_count
        masks_applied += 1

    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)

    if is_16bit:
        result_img = Image.fromarray(
            np.clip(depth_array, 0, 65535).astype(np.uint16), mode="I;16",
        )
    else:
        result_img = Image.fromarray(
            np.clip(depth_array, 0, 255).astype(np.uint8), mode="L",
        )
    result_img.save(output_path)

    return {
        "input": str(depth_map_path),
        "output": str(output_path),
        "masks_applied": masks_applied,
        "labels_found": labels_found,
        "pixels_modified": total_pixels_modified,
    }


def clean_depth_map_batch(
    depth_map_dir: str,
    semantic_masks_path: str,
    output_dir: str,
    labels_to_flatten: list[str] | None = None,
    feather_radius: int = 4,
) -> list[dict]:
    """
    Batch : nettoie tous les *.png d'un répertoire.
    Crée output_dir si nécessaire.
    Returns: list de résultats clean_depth_map.
    """
    input_dir = Path(depth_map_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for png_file in sorted(input_dir.glob("*.png")):
        output_path = out_dir / png_file.name
        result = clean_depth_map(
            depth_map_path=str(png_file),
            semantic_masks_path=semantic_masks_path,
            output_path=str(output_path),
            labels_to_flatten=labels_to_flatten,
            feather_radius=feather_radius,
        )
        results.append(result)

    return results


if __name__ == "__main__":
    import tempfile
    import os

    print("[CLEAN:TEST] Running self-tests...")
    passed = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        depth_array = np.tile(
            np.arange(64, dtype=np.uint8).reshape(64, 1), (1, 64),
        )
        depth_img = Image.fromarray(depth_array, mode="L")
        depth_path = os.path.join(tmpdir, "depth.png")
        depth_img.save(depth_path)

        masks_data = {
            "masks": [
                {
                    "label": "person",
                    "bbox": [20, 20, 44, 44],
                    "polygon": [[20, 20], [44, 20], [44, 44], [20, 44]],
                    "confidence": 0.95,
                },
            ],
            "image_size": [64, 64],
        }
        masks_path = os.path.join(tmpdir, "semantic_masks.json")
        with open(masks_path, "w") as f:
            json.dump(masks_data, f)

        output_path = os.path.join(tmpdir, "output", "depth_cleaned.png")

        result = clean_depth_map(
            depth_map_path=depth_path,
            semantic_masks_path=masks_path,
            output_path=output_path,
        )

        original_arr = np.array(Image.open(depth_path))
        cleaned_arr = np.array(Image.open(output_path))
        mask_zone_original = original_arr[20:44, 20:44]
        mask_zone_cleaned = cleaned_arr[20:44, 20:44]
        assert np.std(mask_zone_cleaned) < np.std(mask_zone_original), \
            "Masked zone not flattened"
        passed += 1
        print("[CLEAN:TEST] 1/5 — Masked zone flattened OK")

        assert os.path.exists(output_path), "Output file missing"
        passed += 1
        print("[CLEAN:TEST] 2/5 — Output file exists OK")

        verify_img = Image.open(output_path)
        assert verify_img.size == (64, 64), "Output size mismatch"
        passed += 1
        print("[CLEAN:TEST] 3/5 — Output PNG valid (64x64) OK")

        assert result["masks_applied"] == 1, \
            f"Expected masks_applied=1, got {result['masks_applied']}"
        passed += 1
        print("[CLEAN:TEST] 4/5 — masks_applied == 1 OK")

        assert result["pixels_modified"] > 0, \
            f"Expected pixels_modified>0, got {result['pixels_modified']}"
        passed += 1
        print("[CLEAN:TEST] 5/5 — pixels_modified > 0 OK")

    if passed == 5:
        print("[CLEAN:TEST] 5/5 tests passed")
    else:
        print(f"[CLEAN:TEST] FAILED — {passed}/5 tests passed")
