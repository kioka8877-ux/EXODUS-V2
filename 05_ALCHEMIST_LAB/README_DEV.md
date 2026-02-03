# FRÉGATE 05_ALCHEMIST_LAB — Documentation Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║             FRÉGATE 05_ALCHEMIST — POST-PRODUCTION PIPELINE                  ║
║              Compositing • Color Grading • Effets Cinématiques               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Vue d'ensemble

L'unité ALCHEMIST LAB est responsable de la post-production des rendus EXR provenant de U04_PHOTOGRAPHY_WING. Elle applique le compositing, le color grading et les effets visuels pour produire les images finales prêtes pour l'encodage.

### Stack Technique
- **Blender 4.0** - Compositor nodes (headless)
- **OpenColorIO** - Color management
- **OptiX/OIDN** - Denoising AI
- **FFmpeg** - Génération previews

## Architecture

```
05_ALCHEMIST_LAB/
├── CODEBASE/
│   ├── EXO_05_ALCHEMIST.py        # CLI wrapper principal
│   ├── compositor_pipeline.py     # Blender Compositor nodes
│   ├── color_grader.py            # LUTs et presets cinématiques
│   ├── effects_forge.py           # Effets visuels (bloom, grain...)
│   ├── denoiser.py                # OptiX/OIDN denoising
│   ├── requirements.txt
│   ├── EXO_05_CONTROL.ipynb       # Debug & testing
│   └── EXO_05_PRODUCTION.ipynb    # Batch processing
├── IN_RENDER/
│   ├── render_*.exr               # Séquences EXR multi-layer
│   └── PRODUCTION_PLAN.JSON       # Instructions post-prod
├── OUT_GRADED/
│   ├── graded_*.exr               # Rendus finaux
│   ├── graded_preview_*.mp4       # Preview basse qualité
│   └── alchemist_report.json      # Rapport de production
├── LUTS/
│   ├── cinematic_warm.cube
│   ├── cinematic_cold.cube
│   ├── neon_nights.cube
│   └── natural.cube
├── README_DEV.md
└── UNIT_05_SUBPLAN.md
```

## Modules

### EXO_05_ALCHEMIST.py

CLI wrapper principal qui orchestre le pipeline.

```bash
python EXO_05_ALCHEMIST.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    [--render-dir /path/to/exr] \
    [--output-dir /path/to/output] \
    [--luts-dir /path/to/luts] \
    [--blender-path /path/to/blender] \
    [--scene 1] \
    [--skip-preview] \
    [-v] [--dry-run]
```

**Options:**
- `--drive-root` - Racine du Drive EXODUS (requis)
- `--production-plan` - Fichier JSON avec les instructions (requis)
- `--scene` - Traiter une seule scène
- `--skip-preview` - Ne pas générer les MP4 preview
- `-v` - Mode verbose
- `--dry-run` - Valider sans exécuter

### compositor_pipeline.py

Script Blender headless qui construit le node tree.

**Pipeline des nodes:**
```
Image Input → Denoise → Exposure → Contrast → Saturation → [LUT] → [Effects] → Output
```

**Nodes créés:**
- `CompositorNodeImage` - Entrée séquence EXR
- `CompositorNodeDenoise` - Denoising OptiX/OIDN
- `CompositorNodeExposure` - Ajustement exposition
- `CompositorNodeBrightContrast` - Contraste
- `CompositorNodeHueSat` - Saturation
- `CompositorNodeColorBalance` - Lift/Gamma/Gain (LUT)
- `CompositorNodeGlare` - Bloom, Lens Flare
- `CompositorNodeMixRGB` - Vignette, Grain
- `CompositorNodeLensdist` - Chromatic Aberration
- `CompositorNodeOutputFile` - Sortie EXR

### color_grader.py

Module de color grading avec support LUTs .cube.

**Presets intégrés:**
- `cinematic_warm` - Tons chauds, ombres relevées
- `cinematic_cold` - Tons froids, contraste élevé
- `neon_nights` - Couleurs saturées, style cyberpunk
- `natural` - Correction neutre
- `bleach_bypass` - Désaturation contrastée
- `vintage_film` - Look film rétro
- `teal_orange` - Style blockbuster Hollywood

**Classes:**
```python
from color_grader import ColorGrader, CubeLUTParser

grader = ColorGrader("/path/to/luts")
config = grader.get_config_from_name("cinematic_warm")
blender_params = grader.config_to_blender_params(config)
```

### effects_forge.py

Générateur d'effets visuels cinématiques.

**Effets supportés:**
- **Bloom** - Glare fog glow avec threshold
- **Lens Flare** - Streaks et ghosts
- **Film Grain** - Noise overlay
- **Vignette** - Ellipse mask avec blur
- **Chromatic Aberration** - Dispersion lens

**Presets:**
```python
from effects_forge import EffectsForge

forge = EffectsForge()
config = forge.parse_effects_dict({
    "bloom": True,
    "film_grain": 0.08,
    "vignette": 0.25
})
nodes = forge.config_to_blender_nodes(config)
```

### denoiser.py

Module de denoising multi-backend.

**Backends (par priorité):**
1. **OptiX** - GPU NVIDIA RTX (optimal)
2. **OIDN** - Intel CPU (fallback)
3. **Blender** - Compositor node (universel)

**Détection automatique:**
```python
from denoiser import Denoiser, DenoiserDetector

backend = DenoiserDetector.get_best_backend()
denoiser = Denoiser(blender_path="/path/to/blender")
status = denoiser.get_status()
```

## Format PRODUCTION_PLAN.JSON

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "name": "Scene_001_Intro",
      "post_production": {
        "color_grade": "cinematic_warm",
        "effects": {
          "bloom": true,
          "lens_flare": false,
          "film_grain": 0.05,
          "vignette": 0.2,
          "chromatic_aberration": 0.0
        },
        "denoise": true,
        "exposure": 0.0,
        "contrast": 1.0,
        "saturation": 1.0
      }
    }
  ]
}
```

**Valeurs effects:**
- `bloom` - boolean ou float (intensité)
- `lens_flare` - boolean
- `film_grain` - float 0.0-0.3
- `vignette` - float 0.0-0.5
- `chromatic_aberration` - float 0.0-0.02

## Fichiers LUT (.cube)

Format Adobe/Resolve compatible.

```
TITLE "Cinematic Warm"
LUT_3D_SIZE 17
DOMAIN_MIN 0.0 0.0 0.0
DOMAIN_MAX 1.0 1.0 1.0

0.020 0.015 0.010
0.082 0.065 0.048
...
```

**Création LUT custom:**
1. Créer le grade dans DaVinci Resolve
2. Exporter en .cube (17³ recommandé)
3. Placer dans `LUTS/`

## Outputs

### graded_{scene_id}_####.exr
Séquence EXR 16-bit avec color grade et effets appliqués.

### graded_preview_{scene_id}.mp4
Preview H.264 1080p pour validation rapide (si FFmpeg disponible).

### alchemist_report.json
```json
{
  "version": "1.0.0",
  "timestamp": "2024-01-15T14:30:00",
  "status": "SUCCESS",
  "summary": {
    "scenes_total": 3,
    "scenes_processed": 3,
    "scenes_failed": 0,
    "total_frames": 7200
  },
  "scenes": [
    {
      "scene_id": 1,
      "success": true,
      "frames_input": 2400,
      "lut_applied": true,
      "preview": "graded_preview_001.mp4"
    }
  ]
}
```

## Gestion d'Erreurs

| Erreur | Comportement |
|--------|--------------|
| LUT manquante | Warning + utilise preset équivalent |
| Pas de GPU | Fallback OIDN CPU |
| EXR corrompu | Skip frame + log erreur |
| FFmpeg absent | Skip preview + continue |
| Blender absent | Erreur fatale |

## Performance

| Opération | GPU (RTX) | CPU |
|-----------|-----------|-----|
| Denoise 4K | ~0.5s/frame | ~3s/frame |
| Color Grade | ~0.1s/frame | ~0.2s/frame |
| Effects | ~0.3s/frame | ~0.8s/frame |
| **Total** | ~1s/frame | ~4s/frame |

## Tests

```bash
# Validation rapide
python EXO_05_ALCHEMIST.py --drive-root /path --production-plan plan.json --dry-run

# Test modules individuels
python color_grader.py /path/to/lut.cube
python effects_forge.py
python denoiser.py /path/to/test.exr
```

## Notebooks Colab

### EXO_05_CONTROL.ipynb
- Test des chemins
- Validation LUTs
- Test effects parsing
- Détection backends denoise
- Dry-run pipeline

### EXO_05_PRODUCTION.ipynb
- Setup complet
- Validation pre-flight
- Exécution batch
- Vérification outputs
- Affichage previews

## Dépendances

```
numpy>=1.21.0
scipy>=1.7.0
Pillow>=9.0.0
opencv-python-headless>=4.5.0
imageio>=2.9.0
tqdm>=4.62.0
omegaconf>=2.1.0
```

**Optionnelles:**
- `OpenEXR` - Validation EXR avancée
- `colour-science` - Color management avancé
- `oidn` - Python bindings OIDN

## Contact

Pour les questions techniques, consulter le README principal EXODUS ou contacter l'équipe via le canal Cortex.
