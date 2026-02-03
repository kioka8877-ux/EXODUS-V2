# 🎬 PHOTOGRAPHY WING — Documentation Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║             FRÉGATE 04_PHOTOGRAPHY — EXODUS PRODUCTION PIPELINE              ║
║              Tracking Caméra + Éclairage Cinématique Automatisés             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

Configurer automatiquement caméras et lumières dans Blender selon les instructions du PRODUCTION_PLAN.JSON généré par CORTEX (U00).

## Architecture

```
04_PHOTOGRAPHY_WING/
├── CODEBASE/
│   ├── EXO_04_PHOTOGRAPHY.py      # Wrapper CLI principal
│   ├── camera_director.py         # Styles caméra (dolly, orbit, static, handheld, tracking)
│   ├── cuts_engine.py             # Système de cuts automatiques
│   ├── lighting_rig.py            # Rigs éclairage (3-point, dramatic, neon, natural, studio)
│   ├── keyframe_animator.py       # Animation caméra par keyframes + easing
│   ├── requirements.txt
│   ├── EXO_04_CONTROL.ipynb       # Notebook debug/test
│   └── EXO_04_PRODUCTION.ipynb    # Notebook production
├── IN_SCENE/
│   ├── environment_*.blend        # Scènes environnement de U03
│   ├── actor_equipped.blend       # Avatar équipé de U02 (optionnel)
│   └── PRODUCTION_PLAN.JSON       # Plan de production de U00
├── OUT_CAMERA/
│   ├── scene_ready_*.blend        # Scènes prêtes au rendu
│   ├── camera_data_*.json         # Export données caméra
│   └── photography_report.json    # Rapport de production
├── README_DEV.md                  # Cette documentation
└── UNIT_04_SUBPLAN.md             # Sous-plan technique
```

## Stack Technique

- **Python 3.10+**
- **Blender 4.0** (headless)
- **Scipy** (interpolation Catmull-Rom, Bezier)
- **NumPy** (calculs vectoriels)

## Modules

### 1. EXO_04_PHOTOGRAPHY.py (Wrapper CLI)

Point d'entrée principal du pipeline.

```bash
# Dry-run (validation)
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v

# Exécution complète
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --blender-path /path/to/blender \
    -v

# Une seule scène
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --scene-id 1 \
    -v
```

**Arguments:**
- `--drive-root` (requis): Racine du Drive EXODUS
- `--production-plan` (requis): Fichier JSON du plan de production
- `--input-dir`: Dossier IN_SCENE (défaut: auto)
- `--output-dir`: Dossier OUT_CAMERA (défaut: auto)
- `--scene-id`: Traiter une seule scène
- `--blender-path`: Chemin custom vers Blender
- `--verbose, -v`: Logs détaillés
- `--dry-run`: Validation sans exécution

### 2. camera_director.py (Styles Caméra)

Crée et anime la caméra selon le style demandé.

**Styles supportés:**

| Style | Description |
|-------|-------------|
| `static` | Caméra fixe pointant vers le centre |
| `dolly` | Mouvement linéaire sur rail |
| `orbit` | Rotation autour du sujet |
| `handheld` | Micro-mouvements aléatoires (shake) |
| `tracking` | Suit un objet cible |

**Vitesses de mouvement:**
- `slow`: 0.3x
- `medium`: 1.0x
- `fast`: 2.5x

### 3. cuts_engine.py (Cuts Automatiques)

Gère les transitions de caméra.

**Types de cuts:**

| Type | FOV | Distance | Notes |
|------|-----|----------|-------|
| `wide` | 60° | 2.5x | Vue d'ensemble |
| `medium` | 50° | 1.5x | Plan moyen |
| `closeup` | 35° | 0.8x | Gros plan |
| `extreme_closeup` | 25° | 0.4x | Très gros plan |
| `dutch_angle` | 45° | 1.2x | Incliné 15° |
| `low_angle` | 50° | 1.8x | Contre-plongée |
| `high_angle` | 50° | 1.8x | Plongée |
| `over_shoulder` | 40° | 0.6x | Par-dessus l'épaule |

**Transitions:**
- `cut`: Transition instantanée (0 frames)
- `smooth`: Transition fluide (15 frames)
- `fast`: Transition rapide (5 frames)
- `slow`: Transition lente (30 frames)

### 4. lighting_rig.py (Éclairage)

Configure les lumières selon le style demandé.

**Styles d'éclairage:**

| Style | Lumières | Description |
|-------|----------|-------------|
| `3point` | Key + Fill + Back | Classique 3-points |
| `dramatic` | Key spot + Rim | Fort contraste |
| `neon` | 4 areas colorées | Ambiance cyberpunk |
| `natural` | Sun + Sky + Bounce | Extérieur naturel |
| `studio` | 4 softboxes | Setup studio pro |

**Paramètres:**
- `intensity`: Multiplicateur d'intensité (0.1 - 5.0)
- `color_temp`: Température couleur en Kelvin (2700K - 9000K)

### 5. keyframe_animator.py (Animation)

Génère des keyframes fluides avec easing.

**Fonctions d'easing:**
- `linear`: Linéaire
- `ease_in`: Accélération
- `ease_out`: Décélération
- `ease_in_out`: Accélération puis décélération
- `ease_in_cubic`: Accélération cubique
- `ease_out_cubic`: Décélération cubique
- `ease_in_out_cubic`: Cubic ease in/out
- `ease_in_expo`: Exponentiel in
- `ease_out_expo`: Exponentiel out
- `bounce`: Rebond

**Méthodes d'animation:**
- `animate_linear()`: Mouvement linéaire A → B
- `animate_path()`: Chemin multi-points (Catmull-Rom)
- `animate_orbit()`: Rotation orbitale
- `animate_zoom()`: Animation FOV
- `animate_crane_shot()`: Arc vertical (Bezier)

## Format PRODUCTION_PLAN.JSON

```json
{
  "project": "EXODUS_PRODUCTION",
  "scenes": [
    {
      "scene_id": 1,
      "environment_file": "environment_1.blend",
      "camera": {
        "style": "orbit",
        "movement": "slow",
        "tracking_target": "Actor_Main",
        "cuts": [
          {"frame": 0, "type": "wide", "transition": "cut"},
          {"frame": 120, "type": "medium", "transition": "smooth"},
          {"frame": 240, "type": "closeup", "transition": "smooth"}
        ]
      },
      "lighting": {
        "style": "dramatic",
        "intensity": 1.2,
        "color_temp": 4500
      }
    }
  ]
}
```

## Outputs

### scene_ready_{scene_id}.blend

Fichier Blender contenant:
- Caméra `EXODUS_Camera` animée
- Target `Camera_Target` (pour tracking)
- Lumières `EXODUS_*` configurées
- Markers de timeline pour chaque cut
- Frame range configuré

### camera_data_{scene_id}.json

```json
{
  "scene_id": "1",
  "frame_range": [1, 250],
  "camera": {
    "name": "EXODUS_Camera",
    "style": "orbit",
    "fov": 50,
    "location": [5.2, -8.1, 3.5]
  },
  "target": {
    "name": "Camera_Target",
    "location": [0, 0, 1.2]
  },
  "operations": [...]
}
```

### photography_report.json

```json
{
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00",
  "status": "SUCCESS",
  "summary": {
    "scenes_total": 3,
    "scenes_processed": 3,
    "scenes_failed": 0
  },
  "scenes": [...],
  "logs": [...]
}
```

## Gestion d'Erreurs

| Erreur | Fallback |
|--------|----------|
| Style caméra inconnu | `static` |
| Style lighting inconnu | `3point` |
| Pas de cuts définis | Caméra statique |
| Environment.blend manquant | Utilise le premier disponible |
| Objet tracking introuvable | Centre de la scène |

## Workflow Complet

```
U03 (Scenography)     U00 (CORTEX)
      │                    │
      ▼                    ▼
environment.blend    PRODUCTION_PLAN.JSON
      │                    │
      └────────┬───────────┘
               ▼
        [04_PHOTOGRAPHY]
               │
               ▼
      scene_ready_*.blend
               │
               ▼
        U05 (Alchemist Lab)
```

## Tests

```bash
# Test modules individuels (hors Blender)
python cuts_engine.py
python lighting_rig.py
python keyframe_animator.py

# Test avec Blender
blender --background --python camera_director.py -- \
    --scene-config '{"camera":{"style":"orbit"}}' \
    --output-dir /tmp \
    --scene-id test
```

## Notebooks

- **EXO_04_CONTROL.ipynb**: Debug et tests individuels des modules
- **EXO_04_PRODUCTION.ipynb**: Pipeline complet de production

## Dépendances

```
scipy>=1.10.0
numpy>=1.24.0
matplotlib>=3.7.0
jsonschema>=4.17.0
```

## Auteur

EXODUS Production Pipeline — Frégate 04_PHOTOGRAPHY_WING
