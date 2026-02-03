# README DEV — Unit 03: Scenography Dock

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   GUIDE DÉVELOPPEUR — SCENOGRAPHY DOCK                        ║
║                      Construction Environnements 3D                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Quick Start

### 1. Prérequis

- Python 3.10+
- Blender 4.0 (portable Linux x64)
- PRODUCTION_PLAN.JSON (généré par U00 Cortex)

### 2. Installation Blender

```bash
# Télécharger Blender 4.0 portable
wget https://download.blender.org/release/Blender4.0/blender-4.0.0-linux-x64.tar.xz

# Extraire dans le dossier AI Models
tar -xf blender-4.0.0-linux-x64.tar.xz -C /path/to/drive/EXODUS_AI_MODELS/
```

### 3. Test Dry-Run

```bash
cd 03_SCENOGRAPHY_DOCK/CODEBASE

python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v
```

### 4. Production

```bash
python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    -v
```

---

## Structure des Modules

### EXO_03_SCENOGRAPHY.py

Point d'entrée CLI principal.

```python
# Arguments
--drive-root        # Obligatoire: Racine du Drive EXODUS
--production-plan   # Obligatoire: Chemin vers le plan JSON
--hdri-library      # Optionnel: Dossier HDRi custom
--environment-assets # Optionnel: Dossier assets custom
--output-dir        # Optionnel: Dossier output custom
--scene-ids         # Optionnel: Filtrer scènes (ex: 1,2,3)
--blender-path      # Optionnel: Chemin Blender custom
--verbose, -v       # Optionnel: Logs détaillés
--dry-run           # Optionnel: Validation sans exécution
```

### environment_builder.py

Script Blender headless pour la construction.

```python
# Fonctions principales
clear_scene()                    # Nettoie la scène
create_environment_collection()  # Crée collection
create_ground()                  # Crée le sol
create_walls()                   # Crée les murs (indoor)
create_ceiling()                 # Crée le plafond (indoor)
create_cyclorama()               # Crée cyclorama (studio)
build_environment()              # Construction complète
process_scene()                  # Traitement d'une scène
```

### pbr_applicator.py

Gestion des matériaux PBR.

```python
# Fonctions principales
create_basic_material(name, preset)       # Matériau simple
create_textured_material(name, textures)  # Matériau avec textures
apply_material_to_object(obj, mat)        # Application
auto_apply_materials(collection)          # Auto-application
find_pbr_textures(path, name)             # Recherche textures

# Presets disponibles
MATERIAL_PRESETS = {
    "asphalt", "concrete", "grass", "wood_floor",
    "plaster", "studio_white", "metal_steel", "glass", ...
}
```

### hdri_manager.py

Gestion de l'éclairage HDRi.

```python
# Fonctions principales
setup_hdri_lighting(path, mood)      # Configure HDRi World
setup_fallback_lighting(mood, style) # Éclairage de fallback
create_scene_lights(style)           # Lumières procédurales
setup_render_settings(engine)        # Config rendu
add_volumetric_lighting(density)     # Effet volumétrique

# Styles d'éclairage
LIGHTING_CONFIGS = {
    "three_point", "interior", "overhead_multi", "sun"
}
```

### props_placer.py

Placement des props environnement.

```python
# Fonctions principales
place_props(list, mapping, template, collection)  # Placement auto
import_prop_asset(path, name, index, collection)  # Import asset
create_placeholder(name, index, collection)        # Placeholder
generate_random_positions(name, size, used)        # Positions aléatoires
scatter_props(name, count, bounds, ...)            # Multi-instances
```

---

## Format PRODUCTION_PLAN.JSON

```json
{
  "metadata": {
    "source_video": "video.mp4",
    "cortex_version": "2.0"
  },
  "scenes": [
    {
      "scene_id": 1,
      "description": "Description scène",
      "environment": {
        "type": "urban_street",
        "description": "Rue de ville nocturne",
        "lighting_mood": "neon",
        "props": ["streetlight", "bench", "car"]
      }
    }
  ]
}
```

### Types d'environnement

| Type | Ground | Walls | Ceiling | Cyclorama |
|------|--------|-------|---------|-----------|
| `urban_street` | 100x100 asphalte | Non | Non | Non |
| `indoor` | 20x20 bois | Oui | Oui | Non |
| `outdoor` | 200x200 herbe | Non | Non | Non |
| `studio` | 50x50 studio | Non | Non | Oui |

### Moods d'éclairage

| Mood | Description | Fallback Color |
|------|-------------|----------------|
| `neon` | Cyberpunk, néons | Violet (0.05, 0.02, 0.1) |
| `dramatic` | Coucher de soleil | Orange (0.15, 0.08, 0.05) |
| `natural` | Lumière du jour | Bleu ciel (0.4, 0.5, 0.6) |
| `studio` | Neutre contrôlé | Gris (0.3, 0.3, 0.3) |

---

## Ajouter des HDRi

1. Téléchargez des HDRi depuis:
   - [Poly Haven](https://polyhaven.com/hdris)
   - [HDRI Haven](https://hdrihaven.com)

2. Placez les fichiers dans `IN_MAPS/hdri_library/`

3. Nommez selon le mood: `neon.hdr`, `dramatic.exr`, etc.

---

## Ajouter des Assets

### Structure recommandée

```
IN_MAPS/environment_assets/
├── urban_street.blend     # Environnement complet
├── indoor.blend
├── props/
│   ├── streetlight.glb
│   ├── bench.glb
│   ├── chair.glb
│   └── table.glb
└── textures/
    ├── asphalt_albedo.png
    ├── asphalt_normal.png
    └── asphalt_roughness.png
```

### Formats supportés

- `.blend` — Recommandé, natif Blender
- `.glb/.gltf` — Format web, bon support
- `.fbx` — Format échange standard
- `.obj` — Format legacy simple

---

## Étendre le Système

### Ajouter un nouveau type d'environnement

1. Modifier `environment_builder.py`:

```python
ENVIRONMENT_TEMPLATES["my_type"] = {
    "ground_size": (50, 50),
    "ground_material": "my_material",
    "default_props": ["prop1", "prop2"],
    "lighting_style": "three_point"
}
```

2. Modifier `props_placer.py`:

```python
PROPS_POSITIONS["my_type"] = {
    "prop1": [
        {"pos": (0, 0, 0), "rot": (0, 0, 0), "scale": 1.0}
    ]
}
```

### Ajouter un nouveau preset matériau

```python
# Dans pbr_applicator.py
MATERIAL_PRESETS["my_material"] = {
    "base_color": (0.5, 0.5, 0.5, 1.0),
    "roughness": 0.7,
    "metallic": 0.0,
    "specular": 0.4
}
```

### Ajouter un nouveau mood

```python
# Dans hdri_manager.py
MOOD_SETTINGS["my_mood"] = {
    "strength": 1.0,
    "rotation_z": 0.0,
    "tint": (1.0, 1.0, 1.0),
    "fallback_color": (0.3, 0.3, 0.3)
}
```

---

## Debug

### Logs verbeux

```bash
python EXO_03_SCENOGRAPHY.py ... -v
```

### Test une seule scène

```bash
python EXO_03_SCENOGRAPHY.py ... --scene-ids 1
```

### Inspection Blender manuelle

```bash
blender --python environment_builder.py -- \
    --production-plan plan.json \
    --hdri-mapping '{}' \
    --assets-mapping '{}' \
    --output-dir ./test \
    --scene-filter '[1]'
```

---

## Troubleshooting

### "Blender introuvable"

Vérifiez que Blender est installé:
```bash
ls -la $DRIVE_ROOT/EXODUS_AI_MODELS/blender-4.0.0-linux-x64/blender
```

### "HDRi manquant"

Les HDRi sont optionnels. Le système utilise un éclairage de fallback.
Pour de meilleurs résultats, ajoutez des HDRi dans `IN_MAPS/hdri_library/`.

### "Asset introuvable"

Un placeholder magenta sera créé. Remplacez-le en ajoutant l'asset manquant.

### Erreur import GLTF

Vérifiez que le fichier est un GLTF 2.0 valide:
```bash
# Valider avec glTF Validator
npx gltf-validator model.glb
```

---

## API Reference

Voir les docstrings dans chaque module pour la documentation complète des fonctions.

---

*EXODUS SYSTEM — Frégate 03_SCENOGRAPHY v1.0.0*
