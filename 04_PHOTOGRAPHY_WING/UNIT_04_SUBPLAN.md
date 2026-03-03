# SOUS-PLAN TECHNIQUE — UNITÉ 04: PHOTOGRAPHY WING

## Mission
Implémenter le tracking caméra et l'éclairage cinématique basés sur le PRODUCTION_PLAN.JSON généré par CORTEX.

## Statut: 🟢 U04-A SCELLÉ (V2)

## Stack Technique
- **Python 3.10+**
- **Blender 4.0** (headless via CLI)
- **Scipy** (interpolation Catmull-Rom, courbes Bezier)
- **NumPy** (calculs vectoriels)

## Architecture Implémentée

```
04_PHOTOGRAPHY_WING/
├── CODEBASE/
│   ├── EXO_04_PHOTOGRAPHY.py      # ✅ Wrapper CLI principal (v2.0.0)
│   ├── camera_schema.py           # ✅ Bible Optique (8 piliers, source unique de vérité)
│   ├── camera_director.py         # ✅ Styles caméra + matchmove + Noise shake + frustum
│   ├── fspy_tracker.py            # ✅ Pilier A : Perspective Lock fSpy ±5%
│   ├── auto_dof.py                # ✅ Pilier B : Auto-DOF Empty→buste avatar
│   ├── render_forge.py            # ✅ Config Cycles + passes + résolution (PAS de rendu)
│   ├── cuts_engine.py             # ✅ Système de cuts (imports depuis camera_schema)
│   ├── lighting_rig.py            # ✅ Rigs éclairage + Volume Scatter + lampes invisibles
│   ├── keyframe_animator.py       # ✅ Animation par keyframes
│   ├── requirements.txt           # ✅ Dépendances
│   ├── EXO_04_CONTROL.ipynb       # ✅ Notebook debug
│   └── EXO_04_PRODUCTION.ipynb    # ✅ Notebook production
├── IN_VIDEO_SOURCE/
│   └── camera_fov_ratio.json      # De U00 (métadonnées caméra)
├── IN_SCENE_REF/
│   ├── environment_*.blend        # De U03
│   ├── actor_equipped.blend       # De U02 (optionnel)
│   └── PRODUCTION_PLAN.JSON       # De U00/CORTEX
├── OUT_CAMERA_LOGIC/
│   ├── scene_ready_*.blend        # Scènes prêtes au rendu (U04-A)
│   ├── camera_data_*.json         # Export données caméra
│   └── photography_report.json    # Rapport production
├── ARCHITECTURE_U04.md            # ✅ Note technique split A/B
├── README_DEV.md                  # ✅ Documentation dev
└── UNIT_04_SUBPLAN.md             # ✅ Ce fichier
```

## Inputs

| Fichier | Source | Description |
|---------|--------|-------------|
| `environment_*.blend` | U03 | Scènes avec environnements 3D |
| `actor_equipped.blend` | U02 | Avatar avec props (optionnel) |
| `PRODUCTION_PLAN.JSON` | U00 | Instructions caméra/lighting |
| `camera_fov_ratio.json` | U00 | Métadonnées caméra source (FOV, ratio) |

## Outputs

| Fichier | Destination | Description |
|---------|-------------|-------------|
| `scene_ready_*.blend` | U04-B / U05 | Scène complète prête au rendu |
| `camera_data_*.json` | Archive | Données caméra exportées |
| `photography_report.json` | Logs | Rapport de production |

## Fonctionnalités Implémentées

### Styles Caméra
- [x] `static` — Caméra fixe
- [x] `dolly` — Mouvement linéaire sur rail
- [x] `orbit` — Rotation autour du sujet
- [x] `handheld` — Shake procédural (Noise modifier)
- [x] `tracking` — Suit un objet cible
- [x] `matchmove` — Reproduit la caméra source (fSpy perspective lock)

### Types de Cuts
- [x] `wide` — Plan large (FOV 60°)
- [x] `medium` — Plan moyen (FOV 50°)
- [x] `closeup` — Gros plan (FOV 35°)
- [x] `extreme_closeup` — Très gros plan (FOV 25°)
- [x] `dutch_angle` — Plan incliné 15°
- [x] `low_angle` — Contre-plongée
- [x] `high_angle` — Plongée
- [x] `over_shoulder` — Par-dessus l'épaule

### Styles Éclairage
- [x] `3point` — Key + Fill + Back classique
- [x] `dramatic` — Fort contraste, ombres dures
- [x] `neon` — Émissifs colorés (cyberpunk)
- [x] `natural` — Sun + Sky (extérieur)
- [x] `studio` — Softbox professionnel

### V2 Features (4 Piliers)
- [x] **Pilier A — fSpy Perspective Lock** : `fspy_tracker.py` verrouille le FOV à ±5% de la caméra source
- [x] **Pilier B — Auto-DOF** : `auto_dof.py` crée un Empty parenté au buste avatar → Bokeh automatique
- [x] **Pilier C — Noise Shake** : `camera_director.py` utilise un Noise modifier sur F-Curves (pas de random.gauss)
- [x] **Pilier D — Volume Scatter** : `lighting_rig.py` ajoute Volume Scatter + lampes invisibles
- [x] **check_frustum()** : Alerte si avatar hors champ caméra

### Fonctions Easing
- [x] `linear`, `ease_in`, `ease_out`, `ease_in_out`
- [x] `ease_in_cubic`, `ease_out_cubic`, `ease_in_out_cubic`
- [x] `ease_in_expo`, `ease_out_expo`
- [x] `bounce`

### Animation
- [x] Interpolation Bezier sur keyframes
- [x] Courbes Catmull-Rom pour paths
- [x] Animation orbit/dolly/crane
- [x] Animation FOV (zoom)

## Format PRODUCTION_PLAN.JSON

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "camera": {
        "style": "dolly|orbit|static|handheld|tracking|matchmove",
        "movement": "slow|medium|fast",
        "cuts": [
          {"frame": 0, "type": "wide", "transition": "cut"},
          {"frame": 120, "type": "closeup", "transition": "smooth"}
        ]
      },
      "lighting": {
        "style": "3point|dramatic|neon|natural|studio",
        "intensity": 1.0,
        "color_temp": 5500
      }
    }
  ]
}
```

## Gestion d'Erreurs

| Situation | Comportement |
|-----------|--------------|
| Style caméra inconnu | Fallback → `static` |
| Style lighting inconnu | Fallback → `3point` |
| Pas de cuts définis | Caméra statique toute durée |
| Environment manquant | Utilise premier .blend disponible |
| Objet tracking absent | Centre de la scène |
| FOV déviation > ±5% | Warning perspective lock |

## CLI Usage

```bash
# Validation dry-run
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v

# Production complète (V2)
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --blender-path /path/to/blender \
    --camera-fov-json /path/to/camera_fov_ratio.json \
    --preset production \
    --shake-preset handheld \
    -v

# Scène unique, preview rapide, sans atmosphère
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --scene-id 1 \
    --preset preview \
    --no-atmosphere \
    -v
```

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION_PLAN.JSON                     │
│                    (from U00/CORTEX)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXO_04_PHOTOGRAPHY.py                      │
│                  (CLI Wrapper v2.0.0)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Camera   │   │ Cuts     │   │ Lighting │
    │ Director │   │ Engine   │   │ Rig      │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         ▼              │              │
    ┌──────────┐        │              │
    │ fSpy     │        │              │
    │ Tracker  │        │              │
    └────┬─────┘        │              │
         │              │              │
         ▼              │              │
    ┌──────────┐        │              │
    │ Auto-DOF │        │              │
    └────┬─────┘        │              │
         │              │              │
         ▼              │              │
    ┌──────────┐        │              │
    │ Render   │        │              │
    │ Forge    │        │              │
    └────┬─────┘        │              │
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Keyframe        │
              │ Animator        │
              └────────┬────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   scene_ready_{id}.blend    │
         │   camera_data_{id}.json     │
         │   photography_report.json   │
         └─────────────────────────────┘
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

## Notes Techniques

1. **Performance**: Les keyframes sont générés par interpolation, pas frame-by-frame
2. **Compatibilité**: Testé avec Blender 4.0+ headless
3. **Isolation**: Aucune dépendance vers autres unités (Loi des Silos)
4. **Extensibilité**: Nouveaux styles ajoutables via `camera_schema.py` (Bible Optique)
5. **Séparation A/B**: U04-A configure le .blend (~30s), U04-B rendra les frames (planifié)

## Changelog

### v2.0.0 (U04-A Scellé)
- `camera_schema.py` : Bible Optique centralisée (8 piliers, 533 lignes)
- `fspy_tracker.py` : Perspective Lock fSpy ±5%
- `auto_dof.py` : Empty parenté au buste avatar → DOF automatique
- `render_forge.py` : Config Cycles + passes + résolution (PAS de rendu)
- `camera_director.py` : Noise modifier shake + matchmove style + check_frustum()
- `lighting_rig.py` : Volume Scatter + lampes invisibles
- `cuts_engine.py` : Imports centralisés depuis camera_schema.py
- `EXO_04_PHOTOGRAPHY.py` v2.0.0 : Nouveaux arguments CLI (--camera-fov-json, --preset, --no-atmosphere, --no-dof, --shake-preset)
- Architecture split A/B (Director / Darkroom)

### v1.0.0 (Initial)
- Implémentation complète des 5 styles caméra
- Système de cuts avec 8 types
- 5 styles d'éclairage
- 10 fonctions d'easing
- Notebooks de contrôle et production
- Documentation complète
