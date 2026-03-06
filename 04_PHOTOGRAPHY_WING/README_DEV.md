# PHOTOGRAPHY WING — Documentation Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║             FRÉGATE 04_PHOTOGRAPHY — EXODUS PRODUCTION PIPELINE              ║
║              Tracking Caméra + Éclairage Cinématique Automatisés             ║
║              V2: fSpy Perspective Lock, Auto-DOF, Noise Shake               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

Configurer automatiquement caméras et lumières dans Blender selon les instructions du PRODUCTION_PLAN.JSON généré par CORTEX (U00).

## Architecture

```
04_PHOTOGRAPHY_WING/
├── CODEBASE/
│   ├── EXO_04_PHOTOGRAPHY.py      # Wrapper CLI principal (v2.0.0)
│   ├── camera_schema.py           # Bible Optique — source unique de vérité (8 piliers)
│   ├── camera_director.py         # Styles caméra + matchmove + Noise shake + frustum
│   ├── fspy_tracker.py            # Pilier A : Perspective Lock fSpy ±5%
│   ├── auto_dof.py                # Pilier B : Auto-DOF Empty→buste avatar
│   ├── render_forge.py            # Config Cycles + passes + résolution (PAS de rendu)
│   ├── cuts_engine.py             # Système de cuts (imports depuis camera_schema)
│   ├── lighting_rig.py            # Rigs éclairage + Volume Scatter + lampes invisibles
│   ├── keyframe_animator.py       # Animation caméra par keyframes + easing
│   ├── darkroom_render.py            # U04-B : Script Blender headless chunk rendering
│   ├── EXO_04_DARKROOM.py           # U04-B : Orchestrateur CLI Python pur
│   ├── requirements.txt
│   ├── EXO_04_CONTROL.ipynb       # Notebook debug/test
│   ├── EXO_04_PRODUCTION.ipynb    # Notebook production
│   └── EXO_04_DARKROOM.ipynb        # U04-B : Notebook Colab rendu batch
├── IN_VIDEO_SOURCE/
│   └── camera_fov_ratio.json      # Métadonnées caméra source (U00)
├── IN_SCENE_REF/
│   ├── environment_*.blend        # Scènes environnement de U03
│   ├── actor_equipped.blend       # Avatar équipé de U02 (optionnel)
│   └── PRODUCTION_PLAN.JSON       # Plan de production de U00
├── OUT_CAMERA_LOGIC/
│   ├── scene_ready_*.blend        # Scènes prêtes au rendu (U04-A)
│   ├── render_*.png               # Frames rendues (U04-B, PNG 16-bit 1080p)
│   ├── camera_data_*.json         # Export données caméra
│   ├── photography_report.json    # Rapport de production (U04-A)
│   └── darkroom_report.json       # Rapport de rendu (U04-B)
├── ARCHITECTURE_U04.md            # Note technique split A/B
├── README_DEV.md                  # Cette documentation
└── UNIT_04_SUBPLAN.md             # Sous-plan technique
```

## Module Dependency Diagram

```
                    ┌──────────────────┐
                    │  camera_schema   │  ← Bible Optique (source unique)
                    │  .py             │
                    └──┬───┬───┬───┬──┘
                       │   │   │   │
          ┌────────────┘   │   │   └────────────┐
          ▼                ▼   ▼                ▼
    ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐
    │ fspy_     │  │ camera_  │  │ cuts_    │  │ lighting_ │
    │ tracker   │  │ director │  │ engine   │  │ rig       │
    └───────────┘  └──────────┘  └──────────┘  └───────────┘
          │                │                          │
          │         ┌──────┘                          │
          ▼         ▼                                 │
    ┌───────────┐  ┌───────────┐                     │
    │ auto_dof  │  │ render_   │                     │
    │           │  │ forge     │                     │
    └───────────┘  └───────────┘                     │
          │         │                                │
          └────┬────┘────────────────────────────────┘
               ▼
    ┌────────────────────┐
    │ EXO_04_PHOTOGRAPHY │  ← CLI Wrapper U04-A (orchestre config)
    │ .py                │
    └────────────────────┘
               │
               ▼
    ┌────────────────────┐
    │ darkroom_render    │  ← Blender headless chunk rendering
    │ .py                │
    └────────────────────┘
               │
               ▼
    ┌────────────────────┐
    │ EXO_04_DARKROOM    │  ← CLI Wrapper U04-B (orchestre rendu)
    │ .py                │
    └────────────────────┘
```

## Stack Technique

- **Python 3.10+**
- **Blender 4.0** (headless)
- **Scipy** (interpolation Catmull-Rom, Bezier)
- **NumPy** (calculs vectoriels)

## Modules

### 1. EXO_04_PHOTOGRAPHY.py (Wrapper CLI v2.0.0)

Point d'entrée principal du pipeline.

```bash
# Dry-run (validation)
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v

# Exécution complète V2
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --blender-path /path/to/blender \
    --camera-fov-json /path/to/camera_fov_ratio.json \
    --preset production \
    --shake-preset handheld \
    -v

# Preview rapide, sans atmosphère ni DOF
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --blender-path /path/to/blender \
    --preset preview \
    --no-atmosphere --no-dof \
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
- `--video-source-dir`: Dossier IN_VIDEO_SOURCE/ (vidéo de référence)
- `--scene-ref-dir`: Dossier IN_SCENE_REF/ (référence scène 3D)
- `--output-dir`: Dossier OUT_CAMERA_LOGIC/ (défaut: auto)
- `--scene-id`: Traiter une seule scène
- `--blender-path`: Chemin custom vers Blender
- `--verbose, -v`: Logs détaillés
- `--dry-run`: Validation sans exécution
- `--camera-fov-json`: Chemin vers camera_fov_ratio.json (U00) pour fSpy perspective lock
- `--preset`: Preset de rendu Cycles (`production` | `preview`, défaut: production)
- `--no-atmosphere`: Désactiver Volume Scatter + lampes invisibles
- `--no-dof`: Désactiver Auto-DOF
- `--shake-preset`: Preset de shake caméra (`handheld` | `subtle` | `aggressive`, défaut: handheld)

### 2. camera_schema.py (Bible Optique)

Source unique de vérité pour TOUS les presets et constantes du pipeline caméra.

**8 Piliers:**
1. Constantes canoniques (PERSPECTIVE_LOCK_TOLERANCE ±5%, DEFAULT_FSTOP, etc.)
2. Camera Style Presets (6 styles : static, dolly, orbit, handheld, tracking, matchmove)
3. Cut Presets (8 types : wide → over_shoulder) — DÉDUPLIQUÉ
4. Lighting Presets (5 styles + couleurs)
5. Bust Bone Chain (16 noms — fallback Mixamo→Generic→Rigify→3dsMax)
6. Render Presets (production 256 samples / preview 64 samples)
7. Shake Presets (handheld / subtle / aggressive — Noise modifier params)
8. Matrice Style ↔ Features (validation)

### 3. camera_director.py (Styles Caméra)

Crée et anime la caméra selon le style demandé.

**Styles supportés:**

| Style | Description |
|-------|-------------|
| `static` | Caméra fixe pointant vers le centre |
| `dolly` | Mouvement linéaire sur rail |
| `orbit` | Rotation autour du sujet |
| `handheld` | Shake procédural (Noise modifier sur F-Curves) |
| `tracking` | Suit un objet cible |
| `matchmove` | Reproduit la caméra source (fSpy perspective lock) |

**Vitesses de mouvement:**
- `slow`: 0.3x
- `medium`: 1.0x
- `fast`: 2.5x

### 4. fspy_tracker.py (Pilier A — Perspective Lock)

Verrouille le FOV de la caméra Blender à ±5% du FOV source (camera_fov_ratio.json de U00).

### 5. auto_dof.py (Pilier B — Auto-DOF)

Crée un Empty parenté au bone du buste de l'avatar. La caméra Blender utilise cet Empty comme focus_object pour un Bokeh automatique.

### 6. render_forge.py (Config Cycles)

Configure le moteur de rendu Cycles (samples, passes, résolution, denoising) SANS lancer de rendu. Trois presets : `production` (4K, 256 samples), `darkroom` (1080p, 128 samples), et `preview` (1080p, 64 samples).

### 6b. darkroom_render.py (U04-B — Rendu Blender headless)

Script exécuté DANS Blender headless pour le rendu batch chunk-based. Approche ATOM-IC : rend en 1080p @ 128 samples + OIDN, U06 Real-ESRGAN upscale ensuite → 4K.

**Usage :**
```bash
blender --background scene_ready_1.blend --python darkroom_render.py -- \
    --output-dir /path/to/OUT_CAMERA_LOGIC \
    --chunk-size 300 \
    --preset darkroom \
    --resume -v
```

**Format de sortie :** `render_XXXXXXXX.png` — PNG 16-bit 1080p RGB. Compatible U05 `scan_render_frames()`.

**Checkpoint system :**
- Fichier `darkroom_checkpoint.json` dans `output_dir` (PAS dans un temp_dir)
- Sauvegardé à chaque fin de chunk (300 frames)
- Supprimé on success — survit on crash → `--resume` reprend au bon frame
- Format : version, blend_file, preset, next_frame, total_frames, chunk_size, timestamp

**Performances estimées (GPU T4) :**
- 3-8s/frame en 1080p @ 128 samples
- ~2-4h pour 60s de vidéo (1800 frames @ 30fps)
- ~1.5 GB d'output (PNG 16-bit)

### 6c. EXO_04_DARKROOM.py (U04-B — Orchestrateur CLI)

Script Python pur (PAS Blender) qui orchestre le rendu en lançant `darkroom_render.py` dans Blender headless.

```bash
# Dry-run (plan de rendu)
python EXO_04_DARKROOM.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --project-name MY_PROJECT \
    --dry-run -v

# Rendu avec auto-resume
python EXO_04_DARKROOM.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --project-name MY_PROJECT \
    --chunk-size 300 \
    --preset darkroom \
    --resume -v
```

**Arguments :**
- `--drive-root` (requis) : Racine du Drive EXODUS
- `--project-name` (requis) : Nom du projet
- `--blend-file` : Chemin direct vers .blend (override auto-detection)
- `--blender-path` : Chemin vers Blender (default: `blender`)
- `--chunk-size` : Frames par chunk (default: 300)
- `--preset` : Preset de rendu (default: `darkroom`)
- `--resume` : Reprendre depuis checkpoint
- `--dry-run` : Afficher le plan sans rendre
- `--verbose, -v` : Logs détaillés

### 7. cuts_engine.py (Cuts Automatiques)

Gère les transitions de caméra. Importe presets depuis `camera_schema.py`.

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

### 8. lighting_rig.py (Éclairage + Atmosphère)

Configure les lumières selon le style demandé. V2 ajoute Volume Scatter + lampes invisibles.

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

### 9. keyframe_animator.py (Animation)

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
- DOF actif (Empty→buste) si --no-dof non spécifié
- Noise modifier (shake) sur F-Curves rotation
- Volume Scatter + lampes invisibles si --no-atmosphere non spécifié
- Cycles configuré (production ou preview)

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
  "version": "2.0.0",
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
| FOV déviation > ±5% | Warning perspective lock |
| Bust bone introuvable | DOF désactivé |

## Workflow Complet

```
U03 (Scenography)     U00 (CORTEX)
      │                    │
      ▼                    ▼
environment.blend    PRODUCTION_PLAN.JSON + camera_fov_ratio.json
      │                    │
      └────────┬───────────┘
               ▼
        [U04-A DIRECTOR]
               │
               ▼
      scene_ready_*.blend  (~200 MB, ~30s)
               │
               ▼
        [U04-B DARKROOM]   (ATOM-IC : 1080p + OIDN)
               │
               ▼
        frames_1080p.png   (~1.5 GB, ~2-4h)
               │
               ▼
        U05 (Alchemist Lab)
```

## Tests

```bash
# Test modules individuels (hors Blender)
python camera_schema.py       # 7/7 tests
python cuts_engine.py         # Test presets + auto-cuts
python lighting_rig.py        # Test rigs
python fspy_tracker.py        # 3/3 tests
python auto_dof.py            # 3/3 tests
python render_forge.py        # 4/4 tests
python keyframe_animator.py   # Test easing

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

EXODUS Production Pipeline — Frégate 04_PHOTOGRAPHY_WING v2.0.0
