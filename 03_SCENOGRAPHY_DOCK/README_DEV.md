# README DEV — Unit 03: Scenography Dock V2 — Tri-Layer System

```
╔══════════════════════════════════════════════════════════════════════════════╗
║             GUIDE DEVELOPPEUR — SCENOGRAPHY DOCK V2                          ║
║                     Tri-Layer System (Dome + Displacement + PBR)             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Quick Start

### 1. Prerequis

- Python 3.10+
- Blender 4.0 (portable Linux x64)
- Pillow (`pip install Pillow`)
- numpy (`pip install numpy`)
- PRODUCTION_PLAN.JSON (genere par U00 Cortex)
- Depth maps DepthAnything V2 (IN_MAP_RAW/*.png)
- semantic_masks.json (segmentation SAM, optionnel)

### 2. Installation Blender

```bash
wget https://download.blender.org/release/Blender4.0/blender-4.0.0-linux-x64.tar.xz
tar -xf blender-4.0.0-linux-x64.tar.xz -C /path/to/drive/EXODUS_AI_MODELS/
```

### 3. Test Dry-Run V2

```bash
cd 03_SCENOGRAPHY_DOCK/CODEBASE

python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v
```

### 4. Production V2

```bash
python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --vram-profile colab_t4 \
    --exposure 1.0 \
    --depth-map-dir IN_MAP_RAW \
    --semantic-masks IN_MAP_RAW/semantic_masks.json \
    -v
```

---

## Architecture Tri-Layer

### Flux Pipeline

```
PRODUCTION_PLAN.JSON
        │
        ▼
EXO_03_SCENOGRAPHY.py  (CLI orchestrateur)
        │
        ▼
layer_assembler.py  (Blender headless)
        │
        ├──▶ dome_builder.py            ──▶ Couche A : Infinity Dome (ENV_DOME)
        ├──▶ shadow_catcher_builder.py   ──▶ Shadow Catcher (ENV_SHADOW)
        ├──▶ world_sync.py              ──▶ World HDRi + Exposition
        ├──▶ displacement_builder.py     ──▶ Couche B : Displacement Mesh (ENV_TERRAIN)
        │       └──▶ depth_map_cleaner.py  ──▶ Anti-ghosting SAM
        ├──▶ pbr_swap_builder.py         ──▶ Couche C : PBR Swap (ENV_PBR)
        └──▶ glass_builder.py            ──▶ Reflectivity Hack (ENV_GLASS)
        │
        ▼
environment_{scene_id}.blend  (5 collections)
```

### Modules V2

| Module | Role | Taille | Dependances |
|--------|------|--------|-------------|
| `EXO_03_SCENOGRAPHY.py` | Orchestrateur CLI V2 | ~17KB | argparse, json, subprocess |
| `layer_assembler.py` | Assembleur Blender headless | ~13KB | bpy, tous les builders |
| `scene_schema.py` | Contrat inter-fregates | ~32KB | re (zero dep Blender) |
| `dome_builder.py` | Couche A — Infinity Dome | ~6KB | bpy, bmesh |
| `shadow_catcher_builder.py` | Shadow Catcher separe | ~5KB | bpy |
| `world_sync.py` | World Sync HDRi | ~7KB | bpy, math |
| `displacement_builder.py` | Couche B — Displacement Mesh | ~6KB | bpy, scene_schema, depth_map_cleaner |
| `depth_map_cleaner.py` | Anti-ghosting | ~9KB | Pillow, numpy, json (zero dep Blender) |
| `pbr_swap_builder.py` | Couche C — PBR Swap | ~6KB | bpy, scene_schema |
| `glass_builder.py` | Reflectivity Hack | ~5KB | bpy, scene_schema |

---

## Structure des Modules

### EXO_03_SCENOGRAPHY.py

Orchestrateur CLI V2. Valide les inputs, resout le HDRi, lance Blender headless, genere le rapport.

```python
# Arguments CLI V2
--drive-root        # Obligatoire : racine du Drive EXODUS
--production-plan   # Obligatoire : chemin vers le plan JSON
--vram-profile      # Optionnel : colab_t4 (defaut) | colab_a100 | local_low
--exposure          # Optionnel : float, exposition World Sync (defaut: 1.0)
--depth-map-dir     # Optionnel : repertoire depth maps (IN_MAP_RAW)
--semantic-masks    # Optionnel : chemin semantic_masks.json
--scene-ids         # Optionnel : filtrer scenes (ex: 1,2,3)
--blender-path      # Optionnel : chemin Blender custom
--output-dir        # Optionnel : dossier output custom
--verbose, -v       # Optionnel : logs detailles
--dry-run           # Optionnel : validation sans execution Blender
```

### layer_assembler.py

Script Blender headless. Coordonne les 3 couches + 5 collections.

```python
assemble_scene(
    scene_data: dict,           # Donnees scene depuis PRODUCTION_PLAN
    depth_map_dir: str,         # Repertoire depth maps
    semantic_masks_path: str,   # Chemin semantic_masks.json
    hdri_path: str | None,      # Chemin HDRi
    output_dir: str,            # Repertoire sortie
    exposure_strength: float,   # Exposition World Sync (defaut: 1.0)
    vram_profile: str,          # Profil VRAM (defaut: "colab_t4")
) -> dict

# Flux interne :
# 1. _clear_scene()
# 2. _ensure_collection() x5
# 3. build_infinity_dome()        → ENV_DOME
# 4. build_shadow_catcher()       → ENV_SHADOW
# 5. setup_world_sync()           → World HDRi
# 6. setup_render_settings()      → Cycles config
# 7. build_displacement_mesh()    → ENV_TERRAIN
# 8. build_pbr_surfaces()         → ENV_PBR
# 9. build_glass_planes()         → ENV_GLASS
# 10. _stamp_custom_properties()  → exodus_*
# 11. bpy.ops.wm.save_as_mainfile()
```

### scene_schema.py

Contrat inter-fregates. Zero dependance Blender.

```python
SCENE_SCHEMA_VERSION = "2.0.0"

REQUIRED_COLLECTIONS  # 5 collections (ENV_DOME, ENV_TERRAIN, ENV_SHADOW, ENV_GLASS, ENV_PBR)
OBJECT_SPECS          # Specifications par objet (type, geometrie, materiau, contraintes)
WORLD_SETTINGS        # use_nodes=True, strength_range=(0.1, 3.0)
CUSTOM_PROPERTIES     # exodus_schema_version, exodus_frigate, exodus_validated, exodus_layers
SAM_LABEL_TO_PBR      # 10 labels SAM → presets PBR (ou None)
PBR_MATERIAL_PRESETS   # 10 presets Principled BSDF + default
VRAM_PROFILES          # 3 profils GPU (colab_t4, colab_a100, local_low)

class SceneSchema:
    validate_scene(scene_report) -> (bool, list[str])  # 7 sous-validations
    get_vram_limits() -> dict
    get_sam_pbr_mapping(label) -> str | None
    get_pbr_preset(name) -> dict
    get_marshal_manifest() -> dict
```

### dome_builder.py

Couche A — Infinity Dome.

```python
build_infinity_dome(
    collection_name: str = "ENV_DOME",
    radius: float = 100.0,          # Clampe [50.0, 200.0]
) -> bpy.types.Object
# UV Sphere segments=64, rings=32, moitie inferieure supprimee, normals inversees

apply_dome_material(
    dome_obj: bpy.types.Object,
    video_frame_path: str | None = None,
) -> None
# Emission shader + ImageTexture (ou placeholder gris fonce)
```

### displacement_builder.py

Couche B — Displacement Mesh.

```python
build_displacement_mesh(
    collection_name: str = "ENV_TERRAIN",
    depth_map_dir: str = "",
    semantic_masks_path: str = "",
    vram_profile: str = "colab_t4",
    plane_size: float = 200.0,
    displacement_strength: float = 10.0,
) -> bpy.types.Object
# Plan subdivise (Subsurf levels selon VRAM profile) + Displace modifier + depth map texture
# Anti-ghosting : appelle clean_depth_map_batch() si semantic_masks_path fourni
```

### depth_map_cleaner.py

Anti-ghosting. Python pur (zero dep Blender).

```python
clean_depth_map(
    depth_map_path: str,
    semantic_masks_path: str,
    output_path: str,
    labels_to_flatten: list[str] | None = None,   # defaut: ["person", "character", "human", "animal"]
    feather_radius: int = 4,
) -> dict   # {input, output, masks_applied, labels_found, pixels_modified}

clean_depth_map_batch(
    depth_map_dir: str,
    semantic_masks_path: str,
    output_dir: str,
    labels_to_flatten: list[str] | None = None,
    feather_radius: int = 4,
) -> list[dict]
```

### pbr_swap_builder.py

Couche C — PBR Swap.

```python
build_pbr_surfaces(
    collection_name: str = "ENV_PBR",
    semantic_masks_path: str = "",
    world_size: float = 200.0,
    z_offset: float = 0.02,
) -> list[bpy.types.Object]
# SAM labels → PBR Principled BSDF (exclut sky et glass)
# Mapping via SAM_LABEL_TO_PBR → PBR_MATERIAL_PRESETS
```

### glass_builder.py

Reflectivity Hack.

```python
build_glass_planes(
    collection_name: str = "ENV_GLASS",
    semantic_masks_path: str = "",
    world_size: float = 200.0,
) -> list[bpy.types.Object]
# Filtre label="glass" uniquement, z_offset=0.01m (anti z-fighting)
# Glass BSDF : transmission=0.9, roughness_max=0.1
```

### shadow_catcher_builder.py

Shadow Catcher separe.

```python
build_shadow_catcher(
    collection_name: str = "ENV_SHADOW",
    size: float = 50.0,
) -> bpy.types.Object
# Plan invisible : is_shadow_catcher=True, visible_camera=False, visible_diffuse=False
# Materiau Principled BSDF noir, Alpha=0
```

### world_sync.py

World Sync HDRi.

```python
setup_world_sync(
    hdri_path: str | None = None,
    mood: str = "natural",             # neon | dramatic | natural | studio
    exposure_strength: float = 1.0,    # Clampe [0.1, 3.0]
) -> None
# HDRi : TexCoord → Mapping → TexEnvironment → MixRGB (tint) → Background → Output
# Fallback : Background avec couleur mood → Output (TexEnvironment cree mais deconnecte)
# 3 node types toujours presents (scene_schema compliance)

setup_render_settings(
    engine: str = "CYCLES",    # CYCLES | EEVEE
    samples: int = 128,
) -> None
```

---

## Format PRODUCTION_PLAN.JSON V2

```json
{
  "metadata": {
    "source_video": "video.mp4",
    "cortex_version": "2.0",
    "analysis_date": "2026-02-27"
  },
  "scenes": [
    {
      "scene_id": 1,
      "description": "Description scene",
      "environment": {
        "lighting_mood": "neon",
        "description": "Rue de ville avec neons",
        "video_frame_path": "/path/to/frame_001.png",
        "hdri_path": "/path/to/scene_001.hdr"
      }
    }
  ]
}
```

---

## VRAM Profiles

| Profile | max_vram_gb | max_subdivisions | max_texture_size | Description |
|---------|-------------|------------------|------------------|-------------|
| `colab_t4` | 6.0 GB | 128 | 4096 | Google Colab T4 (defaut) |
| `colab_a100` | 20.0 GB | 256 | 8192 | Google Colab A100 |
| `local_low` | 4.0 GB | 64 | 2048 | GPU locale budget (<6GB) |

Formule subdivision : `levels = round(log2(max_subdivisions))`
- colab_t4 : 2^7 = 128
- colab_a100 : 2^8 = 256
- local_low : 2^6 = 64

---

## SAM Labels → PBR

| SAM Label | PBR Preset | Base Color | Roughness | Metallic |
|-----------|------------|------------|-----------|----------|
| `road` | asphalt | (0.15, 0.15, 0.15) | 0.8 | 0.0 |
| `grass` | grass | (0.15, 0.35, 0.1) | 0.95 | 0.0 |
| `wall` | concrete | (0.5, 0.5, 0.5) | 0.9 | 0.0 |
| `water` | water_surface | (0.01, 0.04, 0.08) | 0.05 | 0.0 |
| `glass` | glass_clear | (0.9, 0.95, 1.0) | 0.05 | 0.0 |
| `sky` | *(ignored)* | — | — | — |
| `dirt` | dirt_ground | (0.35, 0.22, 0.1) | 0.95 | 0.0 |
| `wood` | wood_planks | (0.4, 0.25, 0.12) | 0.6 | 0.0 |
| `metal` | metal_steel | (0.6, 0.6, 0.65) | 0.3 | 0.9 |
| `fabric` | fabric_generic | (0.3, 0.28, 0.25) | 0.95 | 0.0 |

---

## Inputs / Outputs V2

### Inputs

| Fichier | Source | Description |
|---------|--------|-------------|
| `PRODUCTION_PLAN.JSON` | Cortex U00 | Specifications scenes |
| `IN_MAP_RAW/*.png` | Cortex U00 | Depth maps DepthAnything V2 |
| `semantic_masks.json` | Cortex U00 | Segmentation SAM |
| `*.hdr` / `*.exr` | IN_MAP_RAW | HDRi auto-detecte |

### Outputs

| Fichier | Description |
|---------|-------------|
| `environment_{scene_id}.blend` | Scene Blender Tri-Layer avec 5 collections |
| `scenography_report.json` | Rapport V2 avec schema_validations |
| `assembler_results.json` | Resultats detailles par scene |

---

## Debug

### Logs verbeux

```bash
python EXO_03_SCENOGRAPHY.py ... -v
```

### Test une seule scene

```bash
python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/drive \
    --production-plan PRODUCTION_PLAN.JSON \
    --vram-profile colab_t4 \
    --scene-ids 1 \
    -v
```

### Test unitaire scene_schema.py

```bash
cd 03_SCENOGRAPHY_DOCK/CODEBASE
python scene_schema.py
```

### Test unitaire depth_map_cleaner.py

```python
from depth_map_cleaner import clean_depth_map
result = clean_depth_map(
    depth_map_path="test.png",
    semantic_masks_path="masks.json",
    output_path="cleaned.png",
)
print(result)
```

### Inspection Blender manuelle V2

```bash
blender --background --python layer_assembler.py -- \
    --production-plan plan.json \
    --output-dir ./test \
    --vram-profile colab_t4 \
    --exposure 1.0 \
    --depth-map-dir ./depth_maps \
    --semantic-masks ./semantic_masks.json \
    --scene-filter '[1]'
```

---

## Troubleshooting V2

### "Blender introuvable"

```bash
ls -la $DRIVE_ROOT/EXODUS_AI_MODELS/blender-4.0.0-linux-x64/blender
```

Verifiez que le binaire est bien present et executable. Sinon, telechargez Blender 4.0 portable Linux x64.

### "Depth maps manquantes"

Le systeme fonctionne sans depth maps — le displacement mesh sera cree en mode stub (plan plat avec custom property `exodus_stub=True`). Pour des resultats complets, ajoutez les depth maps dans `IN_MAP_RAW/*.png`.

### "semantic_masks.json absent"

Graceful fallback : PBR Swap et Glass BSDF seront desactives, l'anti-ghosting ne sera pas applique. Les couches A (Dome) et B (Displacement) fonctionnent normalement sans masques SAM.

### "VRAM profile inconnu"

Profils valides : `colab_t4`, `colab_a100`, `local_low`. Le profil par defaut est `colab_t4`.

### "World strength hors limites"

La strength d'exposition est clampee dans [0.1, 3.0] par world_sync.py (contrainte scene_schema.py WORLD_SETTINGS).

---

*EXODUS SYSTEM — Fregate 03_SCENOGRAPHY v2.0.0 — Tri-Layer System*
