# SOUS-PLAN TECHNIQUE — UNITÉ 05: ALCHEMIST LAB

## Mission
Post-production automatisée et color grading cinématique des rendus EXR pour atteindre la qualité finale 4K/120FPS.

## Statut: 🟢 OPÉRATIONNEL

## Stack Technique
- **Blender 4.0 Compositor** - Node tree automatique (headless)
- **OpenColorIO** - Color management professionnel
- **OptiX Denoiser** - GPU NVIDIA RTX (optimal)
- **OIDN** - Intel Open Image Denoise (CPU fallback)
- **FFmpeg** - Génération previews H.264
- **.cube LUTs** - Format Adobe/Resolve compatible

## Inputs
- `IN_RENDER/render_*.exr` — Séquences EXR multi-layer (de U04)
- `IN_RENDER/PRODUCTION_PLAN.JSON` — Instructions post-production du Cortex
- `LUTS/*.cube` — LUTs cinématiques personnalisées

## Outputs
- `OUT_GRADED/graded_{scene_id}_####.exr` — Rendus color-gradés 16-bit
- `OUT_GRADED/graded_preview_{scene_id}.mp4` — Preview H.264 1080p
- `OUT_GRADED/alchemist_report.json` — Rapport de production détaillé

## Modules Implémentés

### 1. EXO_05_ALCHEMIST.py ✅
- CLI wrapper principal avec argparse
- Orchestration du pipeline compositing
- Validation des séquences EXR
- Génération du rapport final
- Support dry-run et traitement par scène

### 2. compositor_pipeline.py ✅
- Script Blender headless
- Construction automatique du node tree
- Pipeline: Input → Denoise → Color → Effects → Output
- Support multi-pass et render layers

### 3. color_grader.py ✅
- Parser fichiers .cube LUT complet
- 7 presets cinématiques intégrés
- Lift/Gamma/Gain control
- Exposition, contraste, saturation
- Température et teinte

### 4. effects_forge.py ✅
- Bloom (Glare Fog Glow)
- Lens Flare (Streaks, Ghosts)
- Film Grain (Noise overlay)
- Vignette (Ellipse mask + blur)
- Chromatic Aberration (Lens Distortion)
- 6 presets d'effets

### 5. denoiser.py ✅
- Détection automatique backend optimal
- Support OptiX (GPU RTX)
- Fallback OIDN (CPU)
- Fallback Blender Compositor
- Validation EXR pour denoise

## LUTs Fournies

| Nom | Description |
|-----|-------------|
| `cinematic_warm.cube` | Tons chauds, ombres orangées |
| `cinematic_cold.cube` | Tons froids, bleus profonds |
| `neon_nights.cube` | Style cyberpunk saturé |
| `natural.cube` | Correction neutre |

## Presets Color Grade

| Preset | Exposure | Contrast | Saturation | Temperature |
|--------|----------|----------|------------|-------------|
| cinematic_warm | +0.1 | 1.15 | 0.95 | +0.15 |
| cinematic_cold | +0.05 | 1.2 | 0.9 | -0.1 |
| neon_nights | 0 | 1.3 | 1.3 | -0.05 |
| natural | 0 | 1.0 | 1.0 | 0 |
| bleach_bypass | +0.1 | 1.4 | 0.6 | 0 |
| vintage_film | +0.05 | 0.9 | 0.85 | +0.1 |
| teal_orange | 0 | 1.1 | 1.1 | 0 |

## Format PRODUCTION_PLAN.JSON

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "post_production": {
        "color_grade": "cinematic_warm",
        "effects": {
          "bloom": true,
          "lens_flare": false,
          "film_grain": 0.05,
          "vignette": 0.2
        },
        "denoise": true
      }
    }
  ]
}
```

## Gestion d'Erreurs

| Erreur | Comportement |
|--------|--------------|
| LUT manquante | Warning + utilise preset |
| Pas de GPU | Fallback OIDN CPU |
| EXR corrompu | Skip frame + log |
| FFmpeg absent | Skip preview |

## Performance Estimée

| Config | Temps/frame 4K |
|--------|---------------|
| GPU RTX 3090 | ~1s |
| GPU RTX 2080 | ~2s |
| CPU 8-core | ~4s |

## Notebooks

- `EXO_05_CONTROL.ipynb` — Debug et tests unitaires
- `EXO_05_PRODUCTION.ipynb` — Batch processing production

## Commandes

```bash
# Dry-run validation
python EXO_05_ALCHEMIST.py --drive-root /path --production-plan plan.json --dry-run -v

# Production complète
python EXO_05_ALCHEMIST.py --drive-root /path --production-plan plan.json -v

# Scène unique
python EXO_05_ALCHEMIST.py --drive-root /path --production-plan plan.json --scene 1 -v
```

## Checklist Déploiement

- [x] Structure dossiers créée
- [x] CLI wrapper EXO_05_ALCHEMIST.py
- [x] Compositor pipeline Blender
- [x] Color grader avec LUTs
- [x] Effects forge (5 effets)
- [x] Denoiser multi-backend
- [x] 4 fichiers LUT .cube
- [x] Notebook CONTROL
- [x] Notebook PRODUCTION
- [x] Documentation README_DEV.md
- [x] UNIT_05_SUBPLAN.md mis à jour

## Prochaines Améliorations (V2)

- [ ] Support ACES color space natif
- [ ] Timeline-based effects (keyframes)
- [ ] AI upscaling integration
- [ ] DaVinci Resolve XML export
- [ ] Multi-GPU rendering
