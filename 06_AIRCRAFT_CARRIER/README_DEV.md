# AIRCRAFT CARRIER V2 — Guide Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FREGATE 06_AIRCRAFT_CARRIER — EXODUS SYSTEM V2               ║
║          Pipeline Frame-Based : ZERO compression lossy intermédiaire        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

L'unité **AIRCRAFT CARRIER** est le point final du pipeline EXODUS. Elle assemble tous les composants (frames PNG, audio) et produit le livrable final en 4K/120FPS.

**V2** : Pipeline frame-based — les frames PNG traversent tout le pipeline sans jamais être encodées en vidéo intermédiaire. Seul l'encodage final produit la compression lossy.

## Structure

```
06_AIRCRAFT_CARRIER/
├── CODEBASE/
│   ├── EXO_06_CARRIER.py          # CLI principal V2 — orchestrateur frame-based
│   ├── carrier_schema.py          # Bible du Vaisseau-Mère — constantes + validation
│   ├── sequence_assembler.py      # Frame Indexer — scan + manifeste JSON
│   ├── audio_sync.py              # Mix et normalisation audio + auto_sync_duration
│   ├── rife_interpolator.py       # Interpolation chunk-based frame-to-frame
│   ├── upscaler.py                # Upscale chunk-based frame-to-frame
│   ├── final_encoder.py           # Encodage AV1/H.265/ProRes (SEUL lossy)
│   ├── requirements.txt           # Dépendances Python
│   ├── EXO_06_CONTROL.ipynb       # Notebook debug/test V2
│   └── EXO_06_PRODUCTION.ipynb    # Notebook production V2
├── IN_ASSEMBLY_KIT/
│   ├── graded_*.png               # Séquences rendues (de U05)
│   ├── audio_*.wav                # Pistes audio
│   └── PRODUCTION_PLAN.JSON       # Config production
├── OUT_FINAL_MOVIE/
│   ├── FINAL_OUTPUT_*.mp4         # Livrable AV1/H.265
│   ├── FINAL_OUTPUT_*.mov         # Archive ProRes
│   ├── thumbnail_*.png            # Vignette
│   └── carrier_report.json        # Rapport de production
├── README_DEV.md                  # Ce fichier
└── UNIT_06_SUBPLAN.md
```

## Pipeline V2 — Frame-Based

```
IN_ASSEMBLY_KIT/                                     OUT_FINAL_MOVIE/
  graded_*.png (U05)                                   FINAL_OUTPUT_*.mp4
  audio_source.wav (U00)                               FINAL_OUTPUT_*.mov
  PRODUCTION_PLAN.JSON (U00)                           thumbnail_*.png
       │                                                carrier_report.json
       ▼
  [1] Frame Indexer (sequence_assembler.py)
       → manifeste JSON {pattern, count, resolution, fps}
       │
       ▼
  [2] Audio Prep (audio_sync.py)
       → audio_mixed.wav (LUFS -14)
       │
       ▼
  [3] Chunk Pipeline (EXO_06_CARRIER.py orchestre)
       Pour chaque chunk de 10 secondes :
       │
       ├── [3a] RIFE (rife_interpolator.py)
       │    frames PNG source → frames PNG interpolées 120fps
       │    (PAS de vidéo intermédiaire)
       │
       ├── [3b] Upscale (upscaler.py)
       │    frames PNG 1080p → frames PNG 4K
       │    (PAS de vidéo intermédiaire)
       │
       ├── [3c] Accumulate dans dossier final_frames/
       │    Numérotation globale continue frame_XXXXXXXX.png
       │
       └── [3d] Checkpoint + cleanup
            Écrire checkpoint.json, supprimer frames temp du chunk
       │
       ▼
  [4] Final Encode (final_encoder.py)
       Frames PNG → FINAL_OUTPUT avec preset choisi
       SEULE compression lossy du pipeline
       Thumbnail extraction + Report JSON
```

## Utilisation

### CLI Principal

```bash
# Preset distribution (AV1)
python EXO_06_CARRIER.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --project-name "MyProject" \
    --preset distribution -v

# Preset H.265 (fallback si AV1 non dispo)
python EXO_06_CARRIER.py \
    --drive-root /path/to/drive \
    --project-name "MyVideo" \
    --preset distribution_h265 -v

# Custom codec + CRF
python EXO_06_CARRIER.py \
    --drive-root /path/to/drive \
    --project-name "MyVideo" \
    --preset custom --codec h265 --crf 20

# Reprendre après interruption
python EXO_06_CARRIER.py \
    --drive-root /path/to/drive \
    --project-name "MyVideo" \
    --resume
```

### Arguments CLI

| Argument | Description | Défaut |
|----------|-------------|--------|
| `--drive-root` | Racine du Drive EXODUS | **Requis** |
| `--project-name` | Nom du projet | `EXODUS_OUTPUT` |
| `--assembly-kit-dir` | Dossier composants | `IN_ASSEMBLY_KIT/` |
| `--output-dir` | Dossier sortie | `OUT_FINAL_MOVIE/` |
| `--production-plan` | Chemin PRODUCTION_PLAN.JSON | Auto-détecté |
| `--preset` | Preset d'encodage | `distribution` |
| `--crf` | CRF custom (override preset) | Depuis preset |
| `--codec` | Codec custom (override preset) | Depuis preset |
| `--resume` | Reprendre depuis checkpoint | False |
| `--no-rife` | Désactive RIFE | False |
| `--no-upscale` | Désactive upscale | False |
| `--cpu-only` | Force CPU | False |
| `--dry-run` | Validation sans exécution | False |
| `-v, --verbose` | Logs détaillés | False |

### Encoding Presets

| Preset | Codec | CRF | Description |
|--------|-------|-----|-------------|
| `distribution` | AV1 (libsvtav1) | 30 | YouTube/TikTok — meilleur ratio qualité/taille |
| `distribution_h265` | H.265 (libx265) | 20 | Fallback — tune animation |
| `master` | ProRes 422 HQ | N/A | Archive lossless pour réédition |
| `custom` | Via `--codec` | Via `--crf` | Override complet |

### Via Notebook (Colab)

1. Ouvrir `EXO_06_PRODUCTION.ipynb`
2. Configurer `PRODUCTION_CONFIG` avec preset
3. Exécuter les cellules

## Modules

### carrier_schema.py

Bible du Vaisseau-Mère — toutes les constantes, presets et validations.

```python
from carrier_schema import (
    CarrierSchema, ENCODING_PRESETS, DEFAULT_PRESET,
    RIFE_CHUNK_SECONDS, CHECKPOINT_FILENAME,
    parse_format_metadata, calculate_rife_params,
)

schema = CarrierSchema()
schema.self_test()  # 12 tests de validation
```

### sequence_assembler.py (Frame Indexer)

Scanne et indexe les séquences d'images. Ne fait AUCUN encodage.

```python
from sequence_assembler import SequenceAssembler

indexer = SequenceAssembler(verbose=True)
manifest = indexer.index_frames(Path("IN_ASSEMBLY_KIT/"))
# manifest = {"sequences": [...], "total_frames": 1800, "fps": 30, ...}
```

### audio_sync.py

Mix et normalise les pistes audio. Auto-sync avec durée vidéo calculée.

```python
from audio_sync import AudioSync

sync = AudioSync(verbose=True)
sync.mix_and_normalize(audio_files, Path("mixed.wav"), target_lufs=-14.0)
sync.auto_sync_duration(audio, total_frames=7200, fps=120, output)
```

### rife_interpolator.py (Chunk-Based)

Interpolation frame-to-frame. ZERO vidéo intermédiaire lossy.

```python
from rife_interpolator import RIFEInterpolator

rife = RIFEInterpolator(model_path="/path/to/rife", use_gpu=True)
output_frames = rife.interpolate_chunk(
    input_frames=png_list,
    output_dir=Path("interpolated/"),
    target_fps=120,
    source_fps=30,
)
```

**Fallback chain**: RIFE model → FFmpeg minterpolate (lossless ffv1) → frame duplication

### upscaler.py (Chunk-Based)

Upscale frame-to-frame. ZERO vidéo intermédiaire lossy.

```python
from upscaler import Upscaler

upscaler = Upscaler(model_path="/path/to/realesrgan.pth")
output_frames = upscaler.upscale_chunk(
    input_frames=png_list,
    output_dir=Path("upscaled/"),
    target_width=3840,
    target_height=2160,
)
```

**Fallback chain**: Real-ESRGAN → FFmpeg Lanczos (image par image)

### final_encoder.py

SEUL module qui fait de la compression lossy. Support AV1.

```python
from final_encoder import FinalEncoder

encoder = FinalEncoder(verbose=True)
encoder.check_av1_available()  # True/False

# Encode depuis frames PNG
encoder.encode_from_frames(
    frames_dir=Path("final_frames/"),
    frame_pattern="frame_%08d.png",
    audio_input=Path("audio.wav"),
    output_path=Path("FINAL.mp4"),
    fps=120,
    codec="av1",
    crf=30,
    preset_name="distribution",
)
```

**Codecs**: `av1`, `h265`, `h264`, `prores`, `prores_hq`, `prores_4444`

## Checkpoint System

Le pipeline écrit un checkpoint après chaque chunk de 10 secondes. En cas d'interruption :

```bash
python EXO_06_CARRIER.py --drive-root /path --project-name "MyVideo" --resume
```

Le pipeline reprend au dernier chunk complété.

## Dépendances

### Python

```bash
pip install torch torchvision opencv-python-headless scipy Pillow tqdm
```

### Système

```bash
# FFmpeg (requis)
sudo apt install ffmpeg

# SVT-AV1 (optionnel — via FFmpeg compilé avec --enable-libsvtav1)
# Vérifié automatiquement, fallback H.265 si absent

# Real-ESRGAN (optionnel)
pip install basicsr realesrgan
```

### Modèles IA

```
EXODUS_AI_MODELS/
├── rife/
│   └── flownet.pkl          # RIFE model
└── realesrgan/
    └── realesr-general-x4v3.pth
```

## Gestion d'Erreurs

| Erreur | Action |
|--------|--------|
| AV1 non disponible | Fallback preset distribution_h265 |
| RIFE model manquant | FFmpeg minterpolate (lossless) → frame duplication |
| Audio manquant | Warning, vidéo muette |
| GPU indisponible | Fallback CPU |
| Real-ESRGAN manquant | FFmpeg Lanczos image par image |
| Interruption pipeline | `--resume` reprend depuis checkpoint |

## Performances Estimées (Pipeline V2)

| Étape | GPU (RTX 3080) | CPU |
|-------|----------------|-----|
| Frame Indexer 1000 frames | ~2s | ~2s |
| RIFE chunk 10s (30→120fps) | ~2 min | ~15 min |
| Upscale chunk 10s 4K | ~4 min | ~20 min |
| Final Encode AV1 (1 min) | ~5 min | ~15 min |
| **Total 1 min video** | **~15 min** | **~1h** |

*Note: V2 est ~10% plus lent que V1 pour le processing (frames PNG vs video), mais la qualité finale est significativement meilleure car il n'y a aucune perte intermédiaire.*

## Migration V1 → V2

| V1 | V2 |
|----|-----|
| `IN_COMPONENTS/` | `IN_ASSEMBLY_KIT/` |
| `OUT_FINAL/` | `OUT_FINAL_MOVIE/` |
| 4 encodages libx264 intermédiaires | ZERO encodage intermédiaire |
| `crf=18` hardcodé | Presets via carrier_schema |
| Pas de checkpoint | Checkpoint par chunk |
| H.265 seulement | AV1 + H.265 + ProRes |

---

**Version:** 2.0.0
**Maintenu par:** EXODUS Production Pipeline
