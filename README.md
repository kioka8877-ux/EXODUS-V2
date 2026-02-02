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

## 📖 Documentation

- [Carnet de Bord](./EXODUS_CAMPAIGN_LOG.md) — État de la flotte
- [Frégate 00 — CORTEX](./00_CORTEX_HQ/README_DEV.md) — Analyse vidéo

## 🚀 Quick Start

```bash
# 1. Configurer la clé Gemini
export GEMINI_API_KEY='votre_clé'

# 2. Lancer l'analyse CORTEX
python 00_CORTEX_HQ/CODEBASE/EXO_00_CORTEX.py \
  --drive-root /chemin/vers/EXODUS \
  --input-video source.mp4
```

## 📜 Licence
Propriétaire — EXODUS Empire
