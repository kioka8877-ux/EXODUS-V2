# AIRCRAFT CARRIER — Guide Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 06_AIRCRAFT_CARRIER — EXODUS SYSTEM                  ║
║              Assemblage Final + Upscale 4K/120FPS via RIFE                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 🎯 Mission

L'unité **AIRCRAFT CARRIER** est le point final du pipeline EXODUS. Elle assemble tous les composants (vidéo, audio) et produit le livrable final en 4K/120FPS.

## 📁 Structure

```
06_AIRCRAFT_CARRIER/
├── CODEBASE/
│   ├── EXO_06_CARRIER.py          # CLI principal - orchestrateur
│   ├── sequence_assembler.py      # Assemblage séquences EXR/PNG → vidéo
│   ├── audio_sync.py              # Mix et normalisation audio
│   ├── rife_interpolator.py       # Interpolation 30→120 FPS
│   ├── upscaler.py                # Upscale 1080p→4K
│   ├── final_encoder.py           # Encodage H.265/ProRes
│   ├── requirements.txt           # Dépendances Python
│   ├── EXO_06_CONTROL.ipynb       # Notebook debug/test
│   └── EXO_06_PRODUCTION.ipynb    # Notebook production
├── IN_COMPONENTS/
│   ├── graded_*.exr               # Séquences rendues (de U05)
│   ├── audio_*.wav                # Pistes audio
│   └── PRODUCTION_PLAN.JSON       # Config production
├── OUT_FINAL/
│   ├── FINAL_OUTPUT_*.mp4         # Livrable H.265
│   ├── FINAL_OUTPUT_*.mov         # Archive ProRes
│   ├── thumbnail_*.png            # Vignette
│   └── carrier_report.json        # Rapport de production
└── README_DEV.md                  # Ce fichier
```

## 🚀 Utilisation

### CLI Principal

```bash
python EXO_06_CARRIER.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --project-name "MyProject" \
    -v
```

#### Arguments

| Argument | Description | Défaut |
|----------|-------------|--------|
| `--drive-root` | Racine du Drive EXODUS | **Requis** |
| `--project-name` | Nom du projet | `EXODUS_OUTPUT` |
| `--components-dir` | Dossier composants | `IN_COMPONENTS/` |
| `--output-dir` | Dossier sortie | `OUT_FINAL/` |
| `--production-plan` | Chemin PRODUCTION_PLAN.JSON | Auto-détecté |
| `--no-rife` | Désactive RIFE | False |
| `--no-upscale` | Désactive upscale | False |
| `--cpu-only` | Force CPU | False |
| `--dry-run` | Validation sans exécution | False |
| `-v, --verbose` | Logs détaillés | False |

### Via Notebook (Colab)

1. Ouvrir `EXO_06_PRODUCTION.ipynb`
2. Configurer `PRODUCTION_CONFIG`
3. Exécuter les cellules

## 📥 PRODUCTION_PLAN.JSON

```json
{
  "output": {
    "resolution": "4K",
    "framerate": 120,
    "codec": "h265",
    "audio_tracks": ["music.wav", "sfx.wav", "voice.wav"]
  },
  "scenes": [
    {
      "scene_id": "scene_001",
      "sequence_pattern": "graded_scene_001_*.exr",
      "transition": "cut"
    }
  ]
}
```

### Options Output

| Clé | Valeurs | Description |
|-----|---------|-------------|
| `resolution` | `"4K"`, `"1080p"` | Résolution cible |
| `framerate` | `120`, `60`, `30` | FPS cible |
| `codec` | `"h265"`, `"prores"` | Codec principal |
| `audio_tracks` | Liste de fichiers | Pistes à mixer |

## 🔧 Modules

### sequence_assembler.py

Assemble les séquences d'images (EXR/PNG) en vidéo.

```python
from sequence_assembler import SequenceAssembler

assembler = SequenceAssembler(verbose=True)

# Assemblage simple
files = sorted(Path("frames/").glob("*.exr"))
assembler.assemble(files, Path("output.mp4"), fps=30)

# Avec transitions
scenes = [{"scene_id": "001", "sequence_pattern": "scene_001_*.exr"}]
assembler.assemble_with_transitions(scenes, components_dir, output)
```

### audio_sync.py

Mix et normalise les pistes audio.

```python
from audio_sync import AudioSync

sync = AudioSync(verbose=True)

# Mix + normalisation LUFS
audio_files = [Path("music.wav"), Path("sfx.wav")]
sync.mix_and_normalize(audio_files, Path("mixed.wav"), target_lufs=-14.0)

# Sync avec vidéo
sync.sync_to_video(audio, video_duration=120.5, output, fade_out=2.0)
```

**Types auto-détectés:**
- `music` → -6 dB
- `sfx` → -3 dB  
- `voice` → 0 dB

### rife_interpolator.py

Interpolation temporelle 30→120 FPS.

```python
from rife_interpolator import RIFEInterpolator

rife = RIFEInterpolator(model_path="/path/to/rife", use_gpu=True)

# Avec RIFE
rife.interpolate(input_video, output_video, target_fps=120)

# Fallback FFmpeg
rife.interpolate_ffmpeg_fallback(input_video, output_video, target_fps=120)
```

**Note:** Si RIFE n'est pas disponible, FFmpeg `minterpolate` est utilisé automatiquement.

### upscaler.py

Upscale vidéo vers 4K.

```python
from upscaler import Upscaler

upscaler = Upscaler(model_path="/path/to/realesrgan.pth")

# Vérifier si nécessaire
if upscaler.needs_upscale(video, target_width=3840):
    upscaler.upscale(video, output, 3840, 2160)
```

**Méthodes:**
- **Real-ESRGAN**: Meilleure qualité (si disponible)
- **FFmpeg Lanczos**: Plus rapide, qualité correcte

### final_encoder.py

Encodage final H.265/ProRes.

```python
from final_encoder import FinalEncoder

encoder = FinalEncoder(verbose=True)

# H.265 (distribution)
encoder.encode(video, audio, output_mp4, codec="h265", crf=18)

# ProRes (archivage)
encoder.encode(video, audio, output_mov, codec="prores")

# Thumbnail
encoder.extract_thumbnail(video, thumbnail_path, timestamp="50%")

# Grille de preview
encoder.extract_thumbnails_grid(video, grid_path, columns=4, rows=4)
```

**Codecs supportés:**
- `h265` (libx265, CRF 18)
- `h264` (libx264, CRF 18)
- `prores` (prores_ks, profile 3)
- `prores_hq` (profile 3)
- `prores_4444` (profile 4, alpha)

## ⚙️ Dépendances

### Python

```bash
pip install torch torchvision opencv-python-headless scipy Pillow tqdm
```

### Système

```bash
# FFmpeg (requis)
sudo apt install ffmpeg

# Optionnel: Real-ESRGAN
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

**Téléchargement:**
- RIFE: https://github.com/hzwer/Practical-RIFE
- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN

## 📊 Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AIRCRAFT CARRIER PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXR/PNG Séquences ──┬──► Assemblage 30FPS ──► RIFE 120FPS ──► Upscale 4K  │
│                      │                                               │      │
│  Audio WAV ──────────┴──► Mix LUFS ──────────────────────────────────┘      │
│                                                                      │      │
│                                                    ┌─────────────────┴────┐ │
│                                                    │  Final Encode        │ │
│                                                    │  ├── H.265 MP4       │ │
│                                                    │  ├── ProRes MOV      │ │
│                                                    │  └── Thumbnail       │ │
│                                                    └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔴 Gestion d'Erreurs

| Erreur | Action |
|--------|--------|
| RIFE model manquant | FFmpeg minterpolate (qualité réduite) |
| Audio manquant | Warning, vidéo muette |
| GPU indisponible | Fallback CPU (plus lent) |
| Real-ESRGAN manquant | FFmpeg Lanczos upscale |
| Séquence incomplète | Skip frames manquants + warning |

## 📈 Performances

| Étape | GPU (RTX 3080) | CPU |
|-------|----------------|-----|
| Assemblage 1000 frames | ~30s | ~30s |
| RIFE 4x (1080p) | ~5 min | ~30 min |
| Upscale 4K (Real-ESRGAN) | ~15 min | ~2h |
| Encode H.265 | ~3 min | ~10 min |

## 📋 Outputs

### FINAL_OUTPUT_*.mp4

- Codec: H.265 (HEVC)
- Résolution: 3840x2160
- FPS: 120
- Bitrate: ~50-100 Mbps
- Audio: AAC 320kbps

### FINAL_OUTPUT_*.mov

- Codec: ProRes 422 HQ
- Résolution: 3840x2160
- FPS: 120
- Audio: PCM 24-bit

### carrier_report.json

```json
{
  "version": "1.0.0",
  "project": "MyProject",
  "status": "SUCCESS",
  "pipeline": {
    "assemble": {"status": "OK"},
    "audio": {"status": "OK"},
    "rife": {"status": "OK"},
    "upscale": {"status": "SKIPPED"},
    "encode_h265": {"status": "OK"},
    "encode_prores": {"status": "OK"}
  },
  "outputs": {
    "mp4": "/path/to/FINAL_OUTPUT.mp4",
    "mov": "/path/to/FINAL_OUTPUT.mov"
  }
}
```

## 🔗 Intégration Pipeline EXODUS

```
U01 ──► U02 ──► U03 ──► U04 ──► U05 ──► U06 (CARRIER) ──► YouTube/Distribution
                                  │
                                  └── graded_*.exr + audio_*.wav
```

---

**Version:** 1.0.0  
**Maintenu par:** EXODUS Production Pipeline
