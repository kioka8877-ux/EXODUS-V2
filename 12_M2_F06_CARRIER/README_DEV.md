# M2_F06 — AIRCRAFT CARRIER

> Mode 2 — Phase 8 — Dual Pipeline Doctrine — v1.0.0

## Rôle

Dernière frégate du pipeline Mode 2. Assemble les frames finales en vidéo et applique
le choix binaire overlay (LOI R-04).

## Lois Impériales appliquées

| Loi | Règle |
|-----|-------|
| R-01 | Isolation stricte — copie indépendante, zéro lien Mode 1 |
| R-04 | Overlay BINAIRE — OUI (audio + texte) ou NON (vidéo brute) |

## Structure

```
12_M2_F06_CARRIER/
├── CODEBASE/
│   ├── EXO_M2_F06_CARRIER.py         ← Script principal CLI
│   ├── EXO_M2_F06_CONTROL.ipynb      ← Diagnostics pré-vol
│   ├── EXO_M2_F06_PRODUCTION.ipynb   ← Notebook de production
│   └── requirements.txt
├── IN_FINAL_FRAMES/ ← Frames PNG de M2_F05 (ou M2_F04 si bypass F05)
├── IN_AUDIO/        ← audio_validated.* (optionnel)
├── OUT_FINAL_MOVIE/ ← FINAL_M2.mp4
└── OUT_REPORT/      ← m2_f06_report.json
```

## Pipeline

```
1. Assembly frames PNG → vidéo intermédiaire (ffmpeg, lossless)
2. RIFE interpolation 24→60 ou 24→120 FPS (optionnel)
3. Real-CUGAN upscale x2/x4 (optionnel)
4. LOI R-04 — Overlay BINAIRE :
   OUI → mixage audio + drawtext overlay ffmpeg
   NON → vidéo brute, aucun traitement
5. Encode final H.265 / AV1 / ProRes
```

## Utilisation

```bash
# Interactif (demande OUI/NON pour overlay)
python CODEBASE/EXO_M2_F06_CARRIER.py

# Overlay explicite
python CODEBASE/EXO_M2_F06_CARRIER.py --overlay yes
python CODEBASE/EXO_M2_F06_CARRIER.py --overlay no

# Avec texte gravé
python CODEBASE/EXO_M2_F06_CARRIER.py --overlay yes --text "Mon titre"

# RIFE 120 FPS
python CODEBASE/EXO_M2_F06_CARRIER.py --overlay no --target-fps 120

# Encode direct (sans RIFE ni upscale)
python CODEBASE/EXO_M2_F06_CARRIER.py --overlay no --no-rife --no-upscale

# ProRes archivage
python CODEBASE/EXO_M2_F06_CARRIER.py --overlay yes --format prores

# Dry-run
python CODEBASE/EXO_M2_F06_CARRIER.py --dry-run --verbose
```

## Dépendances

- **ffmpeg** : requis (`apt install ffmpeg` ou binaire standalone)
- **rife-ncnn-vulkan** : optionnel (RIFE interpolation)
- **realcugan-ncnn-vulkan** : optionnel (upscale)
- Aucune dépendance Python externe requise
