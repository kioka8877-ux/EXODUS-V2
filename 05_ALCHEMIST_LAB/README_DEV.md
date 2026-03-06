# FRÉGATE 05_ALCHEMIST_LAB — Documentation Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║         FRÉGATE 05_ALCHEMIST — VISUAL FUSION PIPELINE V2                     ║
║      Match Color • Grain • Bloom • Sharpness (OpenCV CPU pur)               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Vue d'ensemble

L'unité ALCHEMIST LAB fusionne visuellement les rendus 3D (de U04) avec la vidéo source originale. Le pipeline V2 utilise exclusivement OpenCV + numpy en CPU pur (zéro Blender, zéro GPU) pour appliquer 4 étapes de traitement séquentielles qui donnent aux frames rendues le "look" cinéma de la source.

### Stack Technique
- **OpenCV** (headless) — Traitement d'image, I/O, flou gaussien
- **numpy** — Calcul matriciel float32
- **Pillow** — Support formats image complémentaire
- **tqdm** — Barre de progression

## Architecture V2

```
05_ALCHEMIST_LAB/
├── CODEBASE/
│   ├── alchemist_schema.py        # Bible Alchimique — constantes, presets, validation
│   ├── EXO_05_ALCHEMIST.py        # Orchestrateur CLI v2.0.0
│   ├── match_color.py             # Étape 1 — Transfert de couleur source → render
│   ├── grain_matcher.py           # Étape 2 — Transfert de grain filmique
│   ├── bloom_engine.py            # Étape 3 — Bloom additif (hautes lumières)
│   ├── sharpness_transfer.py      # Étape 4 — Alignement de netteté
│   ├── requirements.txt
│   ├── compositor_pipeline.py     # [V1 — legacy Blender, inactif]
│   ├── color_grader.py            # [V1 — legacy LUT, inactif]
│   ├── effects_forge.py           # [V1 — legacy effects, inactif]
│   └── denoiser.py                # [V1 — legacy denoise, inactif]
├── IN_RAW_FRAMES/                 # Frames rendues (EXR/PNG/TIFF de U04)
├── IN_SOURCE_REF/                 # Références source extraites
├── OUT_FINAL_FRAMES/              # Output — frames fusionnées PNG 16-bit
├── README_DEV.md
└── UNIT_05_SUBPLAN.md
```

## Pipeline V2

```
Render Frame ─┬─► [1] Match Color ──► [2] Grain ──► [3] Bloom ──► [4] Sharpness ──► Output PNG 16-bit
              │         ▲                  ▲                             ▲
Source Video ─┼─► histogrammes ref   grain stats                  source frame
              └──────────────────────────────────────────────────────────┘
```

**Ordre** : `match_color → grain → bloom → sharpness` (défini dans `PIPELINE_ORDER`)

Chaque étape peut être désactivée individuellement via `--skip-*`.

## Modules

### alchemist_schema.py — Bible Alchimique

Zéro dépendance externe. Définit les 7 piliers de données :
1. **Constantes canoniques** — OUTPUT_FORMAT, PIPELINE_ORDER, etc.
2. **Match Color params** — intensity, color_space, reference_sample_count
3. **Grain params** — intensity, bilateral_d, calibration_samples
4. **Bloom presets** — cinema, subtle, neon, none (threshold/intensity/radius)
5. **Sharpness params** — intensity, max_blur_sigma, unsharp_amount/radius
6. **Pipeline presets** — cinema_fusion, subtle_blend, neon_blast, raw_match, full_nuke
7. **AlchemistSchema class** — Façade validation + résolution de config

### EXO_05_ALCHEMIST.py — Orchestrateur CLI v2.0.0

```bash
python EXO_05_ALCHEMIST.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --source-video source_video.mp4 \
    --preset cinema_fusion \
    [--render-dir /path/to/frames] \
    [--output-dir /path/to/output] \
    [--source-ref-dir /path/to/source] \
    [--scene 1] \
    [--match-intensity 0.85] \
    [--grain-intensity 0.5] \
    [--bloom-preset cinema] \
    [--sharpness-intensity 0.7] \
    [--skip-match] [--skip-grain] [--skip-bloom] [--skip-sharpness] \
    [-v] [--dry-run]
```

**Options obligatoires :**

| Flag | Description |
|------|-------------|
| `--drive-root` | Racine du Drive EXODUS V2 |
| `--production-plan` | Chemin vers PRODUCTION_PLAN.JSON |

**Options pipeline :**

| Flag | Description | Défaut |
|------|-------------|--------|
| `--source-video` | Vidéo source de référence | (aucune) |
| `--preset` | Preset pipeline global | `cinema_fusion` |
| `--render-dir` | Dossier frames render | `IN_RAW_FRAMES` |
| `--output-dir` | Dossier output | `OUT_FINAL_FRAMES` |
| `--source-ref-dir` | Dossier références source | `IN_SOURCE_REF` |
| `--scene` | Traiter une seule scène | (toutes) |

**Overrides par étape :**

| Flag | Étape | Range |
|------|-------|-------|
| `--match-intensity` | match_color | 0.0–1.0 |
| `--grain-intensity` | grain | 0.0–1.0 |
| `--bloom-preset` | bloom | cinema/subtle/neon/none |
| `--sharpness-intensity` | sharpness | 0.0–1.0 |

**Skip flags :** `--skip-match`, `--skip-grain`, `--skip-bloom`, `--skip-sharpness`

### bloom_engine.py — Moteur de Bloom

Algorithme bloom additif :
1. Convertir en float32 [0.0, 1.0]
2. Extraire luminance Rec.709 (L = 0.2126R + 0.7152G + 0.0722B)
3. Masque hautes lumières : `bright_mask = max(0, luminance - threshold)`
4. Isoler pixels brillants : `bright_areas = frame * mask`
5. Gros flou gaussien : `glow = GaussianBlur(bright_areas, radius)`
6. Blend additif : `output = frame + glow * intensity`
7. Clip [0, 1], reconvertir au dtype d'entrée

```python
from bloom_engine import BloomEngine
engine = BloomEngine(verbose=True)
result = engine.apply_bloom(frame, threshold=0.8, intensity=0.3, radius=51)
```

### sharpness_transfer.py — Transfert de Netteté

Aligne la netteté du rendu sur celle de la source :
1. Mesurer la variance du Laplacien des deux frames
2. Calculer le ratio source/render
3. Si ratio < 1 (render trop net) → flou gaussien pondéré
4. Si ratio > 1 (render trop mou) → unsharp mask
5. Si ratio ≈ 1 → pas de changement

```python
from sharpness_transfer import SharpnessTransfer
st = SharpnessTransfer(verbose=True)
sharpness = st.measure_sharpness(frame)
result = st.transfer(render_frame, source_frame, intensity=0.7)
```

### match_color.py — Transfert de Couleur

Transfert des histogrammes de couleur de la vidéo source vers le rendu. Espace colorimétrique LAB.

### grain_matcher.py — Transfert de Grain Filmique

Extrait le profil de grain de la vidéo source et l'applique sur le rendu via filtrage bilatéral + bruit procédural.

## Pipeline Presets

| Preset | match_color | grain | bloom | sharpness | Description |
|--------|-------------|-------|-------|-----------|-------------|
| `cinema_fusion` | 0.85 | 0.5 | cinema | 0.7 | Look standard — fusion invisible |
| `subtle_blend` | 0.6 | 0.3 | subtle | 0.5 | Fusion légère — garde l'identité CG |
| `neon_blast` | 0.7 | 0.2 | neon | 0.4 | Style cyberpunk — bloom agressif |
| `raw_match` | 1.0 | 0.0 | none | 0.0 | Match Color pur |
| `full_nuke` | 0.95 | 0.6 | cinema | 0.8 | Tout à fond |

## Bloom Presets

| Preset | threshold | intensity | radius |
|--------|-----------|-----------|--------|
| `cinema` | 0.8 | 0.3 | 51 |
| `subtle` | 0.9 | 0.15 | 31 |
| `neon` | 0.6 | 0.5 | 71 |
| `none` | 1.0 | 0.0 | 1 |

## Format PRODUCTION_PLAN.JSON

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "name": "Scene_001_Intro",
      "timecode_start": 0,
      "timecode_end": 2400,
      "frame_start": 0,
      "frame_end": 2400
    }
  ]
}
```

## I/O

### Input : Frames Render
- Formats : `.exr`, `.png`, `.tiff`, `.tif`
- Nommage : `*_scene_{id}_*` ou tout fichier supporté
- Chargement : `cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH`

### Input : Vidéo Source
- Formats : `.mp4`, `.avi`, `.mov`, `.mkv`
- Ouverture via `cv2.VideoCapture`
- Si résolution différente du render → resize automatique

### Output : Frames Fusionnées
- Format : PNG 16-bit (`uint16`)
- Nommage : `final_{scene_id:03d}_{frame_idx:06d}.png`
- Compression : niveau 3
- Rapport : `alchemist_report.json`

## Gestion de Cas Limites

| Cas | Comportement |
|-----|-------------|
| Pas de vidéo source | Skip match_color, grain, sharpness → bloom seul |
| Résolutions différentes | Resize source à la taille du render |
| Frame source hors range | Clamp au dernier frame + warning |
| Render en .exr | Chargé via `IMREAD_ANYCOLOR \| IMREAD_ANYDEPTH` |
| Module manquant (match_color/grain) | Skip l'étape + warning |

## Outputs

### alchemist_report.json
```json
{
  "version": "2.0.0",
  "timestamp": "2025-01-15T14:30:00",
  "preset": "cinema_fusion",
  "pipeline": ["match_color", "grain", "bloom", "sharpness"],
  "scenes": [{
    "scene_id": 1,
    "frames_total": 2400,
    "frames_processed": 2400,
    "frames_failed": 0,
    "time_seconds": 480.5
  }],
  "summary": {
    "scenes_total": 1,
    "scenes_processed": 1,
    "total_frames_processed": 2400,
    "total_frames_failed": 0,
    "total_time_seconds": 480.5,
    "status": "SUCCESS"
  }
}
```

## Performance Estimée (CPU)

| Opération | Temps/frame 4K | RAM |
|-----------|---------------|-----|
| Match Color | ~0.3s | ~200 MB |
| Grain | ~0.2s | ~150 MB |
| Bloom | ~0.4s | ~300 MB |
| Sharpness | ~0.1s | ~100 MB |
| **Total pipeline** | **~1.0s** | **~500 MB peak** |

Stockage output : ~25 MB/frame PNG 16-bit 4K → ~60 GB pour 2400 frames.

## Tests

```bash
# Tests standalone des modules
python bloom_engine.py
python sharpness_transfer.py
python alchemist_schema.py

# Dry-run validation complète
python EXO_05_ALCHEMIST.py --drive-root /path --production-plan plan.json --dry-run -v

# Production avec preset
python EXO_05_ALCHEMIST.py \
    --drive-root /path \
    --production-plan plan.json \
    --source-video source.mp4 \
    --preset cinema_fusion -v

# Bloom seul (sans source vidéo)
python EXO_05_ALCHEMIST.py \
    --drive-root /path \
    --production-plan plan.json \
    --skip-match --skip-grain --skip-sharpness -v
```

## Dépendances

```
numpy>=1.21.0
opencv-python-headless>=4.5.0
Pillow>=9.0.0
tqdm>=4.62.0
```

Aucune dépendance Blender, GPU, scipy ou autre librairie lourde.
