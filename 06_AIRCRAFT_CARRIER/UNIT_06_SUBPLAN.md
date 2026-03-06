# SOUS-PLAN TECHNIQUE — UNITÉ 06: AIRCRAFT CARRIER

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FREGATE 06_AIRCRAFT_CARRIER — EXODUS SYSTEM V2               ║
║          Pipeline Frame-Based : ZERO compression lossy intermédiaire        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 2.0.0                                                              ║
║  Statut: IMPLÉMENTÉ                                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

L'unité **AIRCRAFT CARRIER** est le porte-avions de la flotte EXODUS. Elle assemble tous les composants produits par les unités précédentes et génère le livrable final 4K/120FPS prêt pour distribution.

**Pipeline V2** : Élimine les 4 compressions lossy intermédiaires de V1. Les frames PNG traversent tout le pipeline (RIFE interpolation + upscale 4K) sans jamais être encodées en vidéo. Seul l'encodage final produit la compression lossy (AV1/H.265/ProRes).

## Stack Technique

- **Python 3.10+** — Orchestration pipeline
- **FFmpeg** — Encodage final, manipulation média
- **carrier_schema.py** — Bible du Vaisseau-Mère (constantes, presets, validation)
- **RIFE** — Real-Time Intermediate Flow Estimation (interpolation IA)
- **Real-ESRGAN** — Super-resolution IA (optionnel)
- **SVT-AV1** — Encodage AV1 via FFmpeg (optionnel, fallback H.265)
- **PyTorch** — Backend ML pour RIFE/ESRGAN

## Inputs

| Fichier | Source | Description |
|---------|--------|-------------|
| `graded_*.exr` | U05 Alchemist Lab | Séquences images gradées |
| `graded_*.png` | U05 Alchemist Lab | Alternative PNG |
| `audio_*.wav` | Production | Pistes audio (music, sfx, voice) |
| `PRODUCTION_PLAN.JSON` | U00 Cortex | Configuration de production |

## Outputs

| Fichier | Format | Description |
|---------|--------|-------------|
| `FINAL_OUTPUT_*.mp4` | AV1/H.265 | Livrable 4K/120FPS pour distribution |
| `FINAL_OUTPUT_*.mov` | ProRes 422 HQ | Archive haute qualité |
| `thumbnail_*.png` | PNG 1920x1080 | Vignette pour publication |
| `carrier_report.json` | JSON | Rapport détaillé de production |

## Modules Implémentés

### EXO_06_CARRIER.py (Orchestrateur V2)
- Pipeline frame-based par chunks de 10 secondes
- Import carrier_schema pour constantes et validation
- CLI simplifié avec `--preset` (distribution, distribution_h265, master, custom)
- Checkpoint system pour reprise après interruption (`--resume`)
- Validation output via carrier_schema (poids, résolution)

### carrier_schema.py (Bible du Vaisseau-Mère)
- 6 piliers : constantes, format parser, encoding presets, RIFE config, upscale config, validation
- Classe `CarrierSchema` avec méthodes de validation
- `self_test()` avec 12 tests automatiques
- Exécutable standalone : `python carrier_schema.py`

### sequence_assembler.py (Frame Indexer V2)
- `index_frames()` → manifeste JSON (pattern, count, resolution, fps)
- N'appelle JAMAIS FFmpeg pour encoder
- Utilise FFprobe uniquement pour lire les dimensions
- Garde `detect_sequence_pattern()` et `SequenceInfo`

### audio_sync.py (V2)
- `auto_sync_duration()` → ajuste audio à total_frames/fps
- Mix multi-pistes avec détection de type
- Normalisation LUFS (-14 pour YouTube)

### rife_interpolator.py (Chunk-Based V2)
- `interpolate_chunk()` → frames PNG source → frames PNG interpolées
- ZERO vidéo intermédiaire lossy
- Fallback minterpolate via vidéo **lossless** (ffv1), pas libx264
- Fallback frame duplication (fichiers PNG dupliqués)

### upscaler.py (Chunk-Based V2)
- `upscale_chunk()` → frames PNG 1080p → frames PNG 4K
- ZERO vidéo intermédiaire lossy
- Fallback FFmpeg Lanczos **image par image** (pas de vidéo)

### final_encoder.py (V2 + AV1)
- `encode_from_frames()` → SEULE méthode de compression lossy
- Support AV1 (libsvtav1) + détection disponibilité
- `check_av1_available()` pour vérifier FFmpeg
- Intégration avec ENCODING_PRESETS de carrier_schema

## Pipeline V2 — Frame-Based

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AIRCRAFT CARRIER PIPELINE V2                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [1] Frame Indexer ──► Manifeste JSON (pas de vidéo!)                      │
│  [2] Audio Prep ──────► audio_mixed.wav (LUFS -14)                         │
│  [3] Chunk Pipeline (par 10 secondes) :                                    │
│      ├── RIFE ──────► frames PNG interpolées 120fps                        │
│      ├── Upscale ───► frames PNG 4K                                        │
│      ├── Accumulate → final_frames/frame_XXXXXXXX.png                      │
│      └── Checkpoint → carrier_checkpoint.json                              │
│  [4] Final Encode ──► SEULE compression lossy (AV1/H.265/ProRes)         │
│      ├── FINAL_OUTPUT_*.mp4                                                │
│      ├── FINAL_OUTPUT_*.mov (ProRes)                                       │
│      ├── thumbnail_*.png                                                   │
│      └── carrier_report.json                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Encoding Presets

| Preset | Codec | CRF | Cible 60s | Description |
|--------|-------|-----|-----------|-------------|
| `distribution` | AV1 (libsvtav1) | 30 | 200-400 MB | YouTube/TikTok streaming |
| `distribution_h265` | H.265 (libx265) | 20 | 350-600 MB | Fallback H.265 tune animation |
| `master` | ProRes 422 HQ | N/A | 4-8 GB | Archive lossless pour réédition |

## Checkpoint System

```json
{
  "version": "2.0.0",
  "next_chunk": 5,
  "timestamp": "2026-03-06T12:00:00",
  "global_frame_idx": 6000,
  "total_chunks": 12
}
```

Reprise : `python EXO_06_CARRIER.py --drive-root /path --project-name "MyVideo" --resume`

## CLI Simplifié

```bash
# Standard
python EXO_06_CARRIER.py --drive-root /path --project-name "MyVideo" --preset distribution

# Custom
python EXO_06_CARRIER.py --drive-root /path --project-name "MyVideo" --preset custom --codec h265 --crf 20

# Resume
python EXO_06_CARRIER.py --drive-root /path --project-name "MyVideo" --resume

# Dry-run
python EXO_06_CARRIER.py --drive-root /path --project-name "MyVideo" --dry-run -v
```

## Gestion d'Erreurs

| Situation | Comportement |
|-----------|--------------|
| AV1 non disponible | Fallback preset distribution_h265 |
| RIFE model manquant | FFmpeg minterpolate (lossless ffv1) |
| minterpolate échoué | Frame duplication |
| Audio manquant | Warning + vidéo muette |
| GPU indisponible | Warning + Fallback CPU |
| Real-ESRGAN manquant | FFmpeg Lanczos (image par image) |
| Séquence vide | Error fatal |
| FFmpeg manquant | Error fatal |
| Interruption pipeline | `--resume` reprend depuis checkpoint |

## Dépendances Externes

```
EXODUS_AI_MODELS/
├── rife/
│   └── flownet.pkl          # Modèle RIFE (requis pour interpolation IA)
└── realesrgan/
    └── realesr-general-x4v3.pth  # Real-ESRGAN (optionnel)
```

## Performances Estimées (Pipeline V2)

| Séquence | GPU (RTX 3080) | CPU |
|----------|----------------|-----|
| 1 minute 30fps → 4K/120fps | ~15 min | ~1h |
| 5 minutes 30fps → 4K/120fps | ~1h | ~5h |
| 10 minutes 30fps → 4K/120fps | ~2h | ~10h |

*Pic disque temporaire : < 5 GB pour 60s de vidéo (frames PNG nettoyées par chunk)*

## Contraintes de Conformité

- **ZERO `libx264` sauf dans `final_encoder.py`** — test de conformité principal
- Les fallbacks FFmpeg utilisent des codecs **lossless** (ffv1, png) pour les intermédiaires
- Le pic disque temporaire reste < 5 GB pour 60s de vidéo
- Tous les imports de `carrier_schema` utilisent `sys.path.insert(0, str(Path(__file__).parent))`

## Tâches

- [x] carrier_schema.py — Bible du Vaisseau-Mère
- [x] Frame Indexer (sequence_assembler.py V2)
- [x] RIFE chunk-based frame-to-frame
- [x] Upscaler chunk-based frame-to-frame
- [x] Final Encoder avec AV1 + encode_from_frames
- [x] Audio sync + auto_sync_duration
- [x] Orchestrateur V2 avec chunks + checkpoint
- [x] CLI simplifié avec --preset
- [x] Notebooks Colab V2 (CONTROL + PRODUCTION)
- [x] Documentation complète V2

## Statut: OPÉRATIONNEL V2

L'unité AIRCRAFT CARRIER V2 est complètement implémentée avec le pipeline frame-based.

---

**Dernière mise à jour:** Mars 2026
**Version:** 2.0.0
