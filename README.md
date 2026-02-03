# EXODUS V2 — Production Pipeline Roblox

> Transmuter n'importe quelle vidéo virale en animation Roblox cinématique 4K/120FPS

## 🎯 Mission

Pipeline de production industrielle pour créer des animations Roblox de "Surqualité" à partir de vidéos sources.

## 🏗️ Architecture

Le système EXODUS est composé de 7 unités autonomes (Frégates) et d'un centre d'assemblage (Porte-Avions):

| Unité | Nom | Rôle |
|-------|-----|------|
| 00 | CORTEX HQ | Analyse vidéo → Plan de production JSON |
| 01 | ANIMATION ENGINE | Extraction MoCap (corps + visage) |
| 02 | LOGISTICS DEPOT | Assemblage Acteur/Props → Alembic |
| 03 | SCENOGRAPHY DOCK | Construction décors PBR/HDRi |
| 04 | PHOTOGRAPHY WING | Tracking caméra + Éclairage |
| 05 | ALCHEMIST LAB | Post-production + Color Grading |
| 06 | AIRCRAFT CARRIER | Assemblage final + RIFE 120FPS |

## 📦 Architecture EXODUS-V2 (Drive)

```
DRIVE_EXODUS_V2/
├── 00_CORTEX_HQ/
│   ├── CODEBASE/
│   ├── IN_VIDEO_SOURCE/       ← Vidéo source à analyser
│   └── OUT_PRODUCTION_PLAN/   ← PRODUCTION_PLAN.JSON généré
│
├── 01_ANIMATION_ENGINE/
│   ├── CODEBASE/
│   ├── IN_CORTEX_JSON/        ← PRODUCTION_PLAN.JSON (copie de U00)
│   ├── IN_MIXAMO_BASE/        ← body_motion.fbx (MoCap)
│   └── OUT_MOTION_DATA/       ← Animation fusionnée .abc/.blend
│
├── 02_LOGISTICS_DEPOT/
│   ├── CODEBASE/
│   ├── IN_MOTION_DATA/        ← .blend de U01
│   ├── IN_ROBLOX_AVATAR/      ← Avatar Roblox .blend
│   ├── IN_PROPS_LIBRARY/      ← Bibliothèque props
│   └── OUT_BAKED_ACTORS/      ← Acteurs équipés .abc
│
├── 03_SCENOGRAPHY_DOCK/
│   ├── CODEBASE/
│   ├── IN_MAP_RAW/            ← Carte Minecraft brute
│   │   ├── hdri_library/      ← Fichiers HDRi (.hdr, .exr)
│   │   └── environment_assets/← Assets environnement
│   ├── IN_CORTEX_JSON/        ← PRODUCTION_PLAN.JSON
│   └── OUT_PREMIUM_SCENE/     ← Scènes environnement .blend
│
├── 04_PHOTOGRAPHY_WING/
│   ├── CODEBASE/
│   ├── IN_VIDEO_SOURCE/       ← Vidéo de référence
│   ├── IN_SCENE_REF/          ← Référence scène 3D (.blend de U03)
│   └── OUT_CAMERA_LOGIC/      ← Scènes avec caméra configurée
│
├── 05_ALCHEMIST_LAB/
│   ├── CODEBASE/
│   ├── IN_RAW_FRAMES/         ← Séquences EXR rendues
│   ├── LUTS/                  ← Fichiers LUT pour color grading
│   └── OUT_FINAL_FRAMES/      ← Frames gradées et composées
│
├── 06_AIRCRAFT_CARRIER/
│   ├── CODEBASE/
│   ├── IN_ASSEMBLY_KIT/       ← Frames finales + audio
│   └── OUT_FINAL_MOVIE/       ← Vidéo finale 4K/120FPS
│
└── EXODUS_AI_MODELS/
    ├── BLENDER/               ← Blender 4.0 portable
    ├── EMOCA/                 ← Modèle extraction faciale
    ├── RIFE/                  ← Modèle interpolation frames
    ├── REALESRGAN/            ← Modèle upscale
    ├── McPrep/                ← Addon Minecraft pour Blender
    └── HDRi/                  ← Collection HDRi partagée
```

## 🔄 Flux de Production

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUX EXODUS-V2                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  [VIDEO SOURCE]
       │
       ▼
  ┌──────────┐
  │ U00      │──────► PRODUCTION_PLAN.JSON
  │ CORTEX   │        (copié manuellement vers U01, U02, U03, U04)
  └──────────┘
       │
       ▼
  ┌──────────┐
  │ U01      │──────► Animation fusionnée (.blend/.abc)
  │ ANIMATION│        (copié vers U02/IN_MOTION_DATA)
  └──────────┘
       │
       ▼
  ┌──────────┐
  │ U02      │──────► Acteur équipé (.abc)
  │ LOGISTICS│        (copié vers U04/IN_SCENE_REF)
  └──────────┘
       │
       │      ┌──────────┐
       │      │ U03      │──────► Environnement (.blend)
       │      │ SCENOGRAPH│       (copié vers U04/IN_SCENE_REF)
       │      └──────────┘
       │           │
       ▼           ▼
  ┌──────────────────────┐
  │ U04                  │──────► Scène prête au rendu (.blend)
  │ PHOTOGRAPHY          │        [RENDU MANUEL DANS BLENDER]
  └──────────────────────┘
              │
              ▼
  ┌──────────┐
  │ U05      │──────► Frames gradées (.exr/.png)
  │ ALCHEMIST│        (copié vers U06/IN_ASSEMBLY_KIT)
  └──────────┘
              │
              ▼
  ┌──────────┐
  │ U06      │──────► VIDÉO FINALE 4K/120FPS
  │ CARRIER  │        (.mp4 + .mov)
  └──────────┘
```

## 🛡️ Doctrine d'Étanchéité

**CHAQUE UNITÉ EST UNE ÎLE**

- Les scripts fonctionnent en **autonomie totale** (exécutables seuls dans Colab)
- Les scripts cherchent **UNIQUEMENT** dans leurs propres dossiers `IN_*`
- **JAMAIS** de référence aux dossiers d'autres unités
- L'Empereur (vous) assure le **transit manuel** entre frégates

## 🚀 Quick Start

```bash
# 1. Générer la structure sur le Drive
python EXO_GENESIS_DRIVE.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2

# 2. Configurer la clé Gemini
export GEMINI_API_KEY='votre_clé'

# 3. Lancer l'analyse CORTEX
python 00_CORTEX_HQ/CODEBASE/EXO_00_CORTEX.py \
  --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
  --input-video source.mp4
```

## 📖 Documentation

- [Carnet de Bord](./EXODUS_CAMPAIGN_LOG.md) — État de la flotte
- [Frégate 00 — CORTEX](./00_CORTEX_HQ/README_DEV.md) — Analyse vidéo

## 📜 Licence

Propriétaire — EXODUS Empire
