# SOUS-PLAN TECHNIQUE — UNITÉ 05: ALCHEMIST LAB

## Mission
Fusion visuelle automatisée des rendus 3D avec la vidéo source pour atteindre le look cinéma 4K. Pipeline OpenCV CPU pur en 4 étapes.

## Statut: 🟢 SCELLÉE — VALIDÉE EN SESSION (2026-04-23)

## Stack Technique V2
- **OpenCV** (headless) — Traitement d'image, I/O, blur, unsharp mask
- **numpy** — Calcul matriciel float32, opérations pixel
- **Pillow** — Support formats image complémentaire
- **tqdm** — Barre de progression CLI
- **CPU pur** — Zéro dépendance Blender, GPU ou scipy

## Inputs
- `IN_RAW_FRAMES/render_*.{exr,png,tiff}` — Frames rendues (de U04)
- `PRODUCTION_PLAN.JSON` — Scènes, timecodes, paramètres
- Vidéo source `.mp4/.avi/.mov` — Référence visuelle pour fusion

## Outputs
- `OUT_FINAL_FRAMES/final_{scene}_{frame}.png` — Frames fusionnées PNG 16-bit
- `OUT_FINAL_FRAMES/alchemist_report.json` — Rapport de production détaillé

## Pipeline V2 : 4 Étapes

```
Render → [1] Match Color → [2] Grain → [3] Bloom → [4] Sharpness → Output PNG 16-bit
```

## Modules V2 Implémentés

### 1. alchemist_schema.py ✅
- Bible Alchimique — 7 piliers de données pures
- Constantes canoniques (OUTPUT_FORMAT, PIPELINE_ORDER, etc.)
- Paramètres et ranges pour chaque étape
- 5 pipeline presets + 4 bloom presets
- Classe AlchemistSchema avec validation complète
- Self-test intégré (8 tests)

### 2. match_color.py ✅
- Classe ColorMatcher — transfert d'histogrammes
- Espace colorimétrique LAB
- compute_reference_histogram() depuis N frames source
- match_frame() avec intensité réglable

### 3. grain_matcher.py ✅
- Classe GrainMatcher — transfert de grain filmique
- Extraction profil grain via filtrage bilatéral
- extract_grain_stats() depuis N frames source
- apply_grain() procédural avec intensité réglable

### 4. bloom_engine.py ✅
- Classe BloomEngine — bloom additif OpenCV
- Extraction hautes lumières (luminance Rec.709)
- Flou gaussien massif → glow
- Blend additif avec intensité
- 4 presets (cinema, subtle, neon, none)
- Support uint8, uint16, float32
- Self-test intégré (5 tests)

### 5. sharpness_transfer.py ✅
- Classe SharpnessTransfer — alignement de netteté
- Mesure variance du Laplacien
- Blur gaussien si render trop net (ratio < 1)
- Unsharp mask si render trop mou (ratio > 1)
- Support uint8, uint16, float32
- Self-test intégré (6 tests)

### 6. EXO_05_ALCHEMIST.py ✅ (v2.0.0)
- Orchestrateur CLI complet (argparse)
- Résolution preset + overrides individuels
- Chargement vidéo source via cv2.VideoCapture
- Extraction frames reference (histogrammes, grain, sharpness)
- Pipeline séquentiel 4 étapes par frame
- Sauvegarde PNG 16-bit
- Rapport JSON + résumé console
- Support --dry-run, --scene, --skip-*, -v
- Gestion gracieuse modules absents (match_color, grain_matcher)

## Pipeline Presets

| Preset | match_color | grain | bloom | sharpness |
|--------|-------------|-------|-------|-----------|
| cinema_fusion | 0.85 | 0.5 | cinema | 0.7 |
| subtle_blend | 0.6 | 0.3 | subtle | 0.5 |
| neon_blast | 0.7 | 0.2 | neon | 0.4 |
| raw_match | 1.0 | 0.0 | none | 0.0 |
| full_nuke | 0.95 | 0.6 | cinema | 0.8 |

## Performance Estimée (CPU)

| Opération | Temps/frame 4K | RAM |
|-----------|---------------|-----|
| Match Color | ~0.3s | ~200 MB |
| Grain | ~0.2s | ~150 MB |
| Bloom | ~0.4s | ~300 MB |
| Sharpness | ~0.1s | ~100 MB |
| **Total** | **~1.0s/frame** | **~500 MB peak** |

**Stockage** : ~25 MB/frame PNG 16-bit 4K → ~60 GB pour 2400 frames.

## Commandes

```bash
# Tests standalone
python bloom_engine.py
python sharpness_transfer.py
python alchemist_schema.py

# Dry-run
python EXO_05_ALCHEMIST.py --drive-root /path --production-plan plan.json --dry-run -v

# Production complète
python EXO_05_ALCHEMIST.py \
    --drive-root /path \
    --production-plan plan.json \
    --source-video source.mp4 \
    --preset cinema_fusion -v

# Scène unique
python EXO_05_ALCHEMIST.py \
    --drive-root /path \
    --production-plan plan.json \
    --source-video source.mp4 \
    --scene 1 -v
```

## Fichiers Legacy V1 (inactifs)

| Fichier | Rôle V1 | Statut |
|---------|---------|--------|
| compositor_pipeline.py | Blender Compositor nodes | Inactif |
| color_grader.py | LUTs .cube | Inactif |
| effects_forge.py | Effets Blender (bloom, grain) | Inactif |
| denoiser.py | OptiX/OIDN | Inactif |

## Décrets Impériaux Validés (Session 2026-04-23)

### Mode A — Bypass (DECRET II)
Flag `--bypass` : F05 skippée, frames copiées directement vers `OUT_FINAL_FRAMES/`.
Génère `alchemist_report.json` avec `status: "SKIPPED"`.
Activé si rendu Blender Cycles déjà satisfaisant — aucun traitement, transit direct vers F06.

### Mode B — DaVinci Resolve (Manuel)
Outil externe gratuit. L'opérateur importe la séquence EXR, applique le LUT, exporte.
Non scriptable (Resolve Free). Hors du scope code EXODUS — documenté ici pour référence.

### Mode C — Python LUT Engine (DECRET III)
Module `lut_engine.py` : lecture .cube + interpolation trilinéaire 3D, 100% numpy, zéro dépendance externe.
Activation : `--lut LUTS/cinematic_cold.cube [--lut-intensity 0.8]`
Step ajouté après le pipeline OpenCV existant : match_color → grain → bloom → sharpness → **LUT**.

### DECRET I — Inventaire LUTs
`LUTS/MANIFEST.json` créé. 4 LUTs en stock, versionnées dans le repo :
- `cinematic_cold.cube` — Look froid, ambiances nocturnes
- `cinematic_warm.cube` — Look chaud, éclairages dorés
- `natural.cube` — Grade neutre, correction légère
- `neon_nights.cube` — Cyberpunk, saturé, contrastes hauts

## Checklist Déploiement V2 (SCELLÉE)

- [x] alchemist_schema.py — Bible Alchimique
- [x] match_color.py — Transfert couleur
- [x] grain_matcher.py — Transfert grain
- [x] bloom_engine.py — Bloom additif
- [x] sharpness_transfer.py — Alignement netteté
- [x] EXO_05_ALCHEMIST.py v2.0.0 — Orchestrateur CLI
- [x] lut_engine.py — LUT .cube 3D (numpy trilinéaire) — DECRET III
- [x] LUTS/MANIFEST.json — Inventaire LUTs — DECRET I
- [x] --bypass flag — Transit direct F04 → F06 — DECRET II
- [x] requirements.txt — 4 dépendances CPU pur
- [x] README_DEV.md — Documentation V2
- [x] UNIT_05_SUBPLAN.md — Sous-plan V2

## Dépendances

```
numpy>=1.21.0
opencv-python-headless>=4.5.0
Pillow>=9.0.0
tqdm>=4.62.0
```
