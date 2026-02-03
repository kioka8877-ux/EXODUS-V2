# SOUS-PLAN TECHNIQUE — UNITÉ 06: AIRCRAFT CARRIER

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 06_AIRCRAFT_CARRIER — EXODUS SYSTEM                  ║
║              Assemblage Final + Upscale 4K/120FPS via RIFE                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Statut: ✅ IMPLÉMENTÉ                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

L'unité **AIRCRAFT CARRIER** est le porte-avions de la flotte EXODUS. Elle assemble tous les composants produits par les unités précédentes et génère le livrable final 4K/120FPS prêt pour distribution.

## Stack Technique

- **Python 3.10+** — Orchestration pipeline
- **FFmpeg** — Assemblage, encodage, manipulation média
- **RIFE** — Real-Time Intermediate Flow Estimation (interpolation IA)
- **Real-ESRGAN** — Super-resolution IA (optionnel)
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
| `FINAL_OUTPUT_*.mp4` | H.265/HEVC | Livrable 4K/120FPS pour distribution |
| `FINAL_OUTPUT_*.mov` | ProRes 422 HQ | Archive haute qualité |
| `thumbnail_*.png` | PNG 1920x1080 | Vignette pour publication |
| `carrier_report.json` | JSON | Rapport détaillé de production |

## Modules Implémentés

### ✅ EXO_06_CARRIER.py
- Parse arguments CLI
- Valide tous les composants
- Orchestre le pipeline complet
- Génère le rapport final

### ✅ sequence_assembler.py
- Détection automatique des patterns de séquence
- Assemblage EXR/PNG → vidéo MP4
- Support des transitions entre scènes
- Gestion des framerates

### ✅ audio_sync.py
- Détection automatique du type de piste
- Mix multi-pistes avec volumes ajustés
- Normalisation LUFS (-14 pour YouTube)
- Synchronisation avec timeline vidéo

### ✅ rife_interpolator.py
- Chargement modèle RIFE
- Interpolation 30→120 FPS (4x)
- Support GPU CUDA et CPU fallback
- Fallback FFmpeg minterpolate

### ✅ upscaler.py
- Détection résolution source
- Upscale via Real-ESRGAN (si disponible)
- Fallback FFmpeg Lanczos
- Skip automatique si déjà 4K

### ✅ final_encoder.py
- Encodage H.265 (CRF 18, preset slow)
- Encodage ProRes 422 HQ
- Extraction thumbnail
- Embedding métadonnées

## Pipeline Final

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  IN_COMPONENTS/                                                             │
│  ├── graded_*.exr ───┬──► [1] Assemblage ──► [3] RIFE 120FPS ──► [4] 4K ──┐│
│  └── audio_*.wav ────┴──► [2] Mix Audio ─────────────────────────────────┐││
│                                                                          │││
│  OUT_FINAL/                                                              │││
│  ├── FINAL_OUTPUT_*.mp4 ◄────── [5] H.265 Encode ◄───────────────────────┘││
│  ├── FINAL_OUTPUT_*.mov ◄────── [6] ProRes Encode ◄────────────────────────┘│
│  ├── thumbnail_*.png ◄───────── [7] Thumbnail                               │
│  └── carrier_report.json ◄───── [8] Report                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Gestion d'Erreurs

| Situation | Comportement |
|-----------|--------------|
| RIFE model manquant | ⚠️ Warning + FFmpeg minterpolate |
| Audio manquant | ⚠️ Warning + vidéo muette |
| GPU indisponible | ⚠️ Warning + Fallback CPU |
| Real-ESRGAN manquant | ⚠️ Warning + FFmpeg Lanczos |
| Séquence vide | ❌ Error fatal |
| FFmpeg manquant | ❌ Error fatal |

## Dépendances Externes

```
EXODUS_AI_MODELS/
├── rife/
│   └── flownet.pkl          # Modèle RIFE (requis pour interpolation IA)
└── realesrgan/
    └── realesr-general-x4v3.pth  # Real-ESRGAN (optionnel)
```

## Utilisation

### CLI
```bash
python EXO_06_CARRIER.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --project-name "MonProjet" \
    -v
```

### Colab Notebook
1. Ouvrir `EXO_06_PRODUCTION.ipynb`
2. Configurer les paramètres
3. Exécuter toutes les cellules

## Performances Estimées

| Séquence | GPU (RTX 3080) | CPU |
|----------|----------------|-----|
| 1 minute 30fps → 4K/120fps | ~15 min | ~2h |
| 5 minutes 30fps → 4K/120fps | ~45 min | ~8h |
| 10 minutes 30fps → 4K/120fps | ~1.5h | ~16h |

## Tâches

- [x] Assemblage séquences vidéo
- [x] Synchronisation audio multi-pistes
- [x] Interpolation 30→120 FPS via RIFE
- [x] Upscale 1080p→4K (Real-ESRGAN/Lanczos)
- [x] Encodage H.265/ProRes
- [x] Génération thumbnail
- [x] Rapport de production JSON
- [x] Notebooks Colab (CONTROL + PRODUCTION)
- [x] Documentation complète

## Statut: ✅ OPÉRATIONNEL

L'unité AIRCRAFT CARRIER est complètement implémentée et prête pour la production.

---

**Dernière mise à jour:** Février 2026  
**Version:** 1.0.0
