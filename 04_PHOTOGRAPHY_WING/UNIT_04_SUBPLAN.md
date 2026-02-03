# SOUS-PLAN TECHNIQUE — UNITÉ 04: PHOTOGRAPHY WING

## Mission
Implémenter le tracking caméra et l'éclairage cinématique basés sur le PRODUCTION_PLAN.JSON généré par CORTEX.

## Statut: 🟢 OPÉRATIONNEL

## Stack Technique
- **Python 3.10+**
- **Blender 4.0** (headless via CLI)
- **Scipy** (interpolation Catmull-Rom, courbes Bezier)
- **NumPy** (calculs vectoriels)

## Architecture Implémentée

```
04_PHOTOGRAPHY_WING/
├── CODEBASE/
│   ├── EXO_04_PHOTOGRAPHY.py      # ✅ Wrapper CLI principal
│   ├── camera_director.py         # ✅ Styles caméra
│   ├── cuts_engine.py             # ✅ Système de cuts
│   ├── lighting_rig.py            # ✅ Rigs éclairage
│   ├── keyframe_animator.py       # ✅ Animation par keyframes
│   ├── requirements.txt           # ✅ Dépendances
│   ├── EXO_04_CONTROL.ipynb       # ✅ Notebook debug
│   └── EXO_04_PRODUCTION.ipynb    # ✅ Notebook production
├── IN_SCENE/
│   ├── environment_*.blend        # De U03
│   ├── actor_equipped.blend       # De U02 (optionnel)
│   └── PRODUCTION_PLAN.JSON       # De U00/CORTEX
├── OUT_CAMERA/
│   ├── scene_ready_*.blend        # Scènes prêtes au rendu
│   ├── camera_data_*.json         # Export données caméra
│   └── photography_report.json    # Rapport production
├── README_DEV.md                  # ✅ Documentation dev
└── UNIT_04_SUBPLAN.md             # ✅ Ce fichier
```

## Inputs

| Fichier | Source | Description |
|---------|--------|-------------|
| `environment_*.blend` | U03 | Scènes avec environnements 3D |
| `actor_equipped.blend` | U02 | Avatar avec props (optionnel) |
| `PRODUCTION_PLAN.JSON` | U00 | Instructions caméra/lighting |

## Outputs

| Fichier | Destination | Description |
|---------|-------------|-------------|
| `scene_ready_*.blend` | U05 | Scène complète prête au rendu |
| `camera_data_*.json` | Archive | Données caméra exportées |
| `photography_report.json` | Logs | Rapport de production |

## Fonctionnalités Implémentées

### Styles Caméra
- [x] `static` — Caméra fixe
- [x] `dolly` — Mouvement linéaire sur rail
- [x] `orbit` — Rotation autour du sujet
- [x] `handheld` — Micro-mouvements aléatoires
- [x] `tracking` — Suit un objet cible

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
        "style": "dolly|orbit|static|handheld|tracking",
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

## CLI Usage

```bash
# Validation dry-run
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v

# Production complète
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --blender-path /path/to/blender \
    -v

# Scène unique
python EXO_04_PHOTOGRAPHY.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --production-plan PRODUCTION_PLAN.JSON \
    --scene-id 1 \
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
│                  (CLI Wrapper)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Camera   │   │ Cuts     │   │ Lighting │
    │ Director │   │ Engine   │   │ Rig      │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
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
# Test modules hors Blender
python cuts_engine.py
python lighting_rig.py
python keyframe_animator.py

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
4. **Extensibilité**: Nouveaux styles ajoutables via dictionnaires de presets

## Changelog

### v1.0.0 (Initial)
- Implémentation complète des 5 styles caméra
- Système de cuts avec 8 types
- 5 styles d'éclairage
- 10 fonctions d'easing
- Notebooks de contrôle et production
- Documentation complète
