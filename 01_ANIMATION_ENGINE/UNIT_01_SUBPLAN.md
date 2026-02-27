# UNIT 01 — TRANSMUTATION ENGINE V2

## Sub-Plan Technique

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 01_TRANSMUTATION — TECHNICAL SUBPLAN V2               ║
║     Body Motion + Emotional Intent Transfer → .blend (Master) + .abc         ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Mission

Fusionner des animations corporelles (FBX MoCap) avec des expressions faciales traduites par Emotional Intent Transfer (Bible Anatomique → 52 ARKit Shape Keys) pour produire des animations complètes exportées en dual .blend + .abc.

### Inputs
| Type | Format | Source |
|------|--------|--------|
| Body Motion | `.fbx` | SayMotion / Mixamo |
| Facial Animation | `.json` | U00 CORTEX (Gemini → segments émotionnels) |
| Actor Model | `.blend` | Avatar Roblox avec DynamicHead |

### Output
| Type | Format | Destination |
|------|--------|-------------|
| Animation Master | `.blend` | U02 LOGISTICS (props attachment) |
| Animation Preview | `.abc` | Preview / Backup |
| Translated Data | `.json` | Debug / Archive |

---

## Architecture Pipeline V2

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRANSMUTATION PIPELINE V2                                  │
│                   Emotional Intent Transfer                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  facial_animation │───▶│  Expression      │───▶│  52 ARKit        │      │
│  │  .json (U00)      │    │  Schema (Bible)  │    │  Shape Keys      │      │
│  └──────────────────┘    └──────────────────┘    └────────┬─────────┘      │
│                                    │                       │                │
│                                    ▼                       │                │
│                          ┌──────────────────┐              │                │
│                          │  Emotional Intent │              │                │
│                          │  Translator       │──────────────┘                │
│                          └──────────────────┘                               │
│                                    │                                        │
│  ┌──────────────────┐              ▼                                        │
│  │  Motion.fbx      │───────▶┌──────────────────┐                          │
│  │  (Body)          │        │   BLENDER FUSION  │                          │
│  └──────────────────┘        │   NLA + Bézier +  │                          │
│                              │   Noise Modifier  │                          │
│  ┌──────────────────┐        └────────┬──────────┘                          │
│  │  Avatar.blend    │────────────────┘│                                     │
│  │  (Rigged)        │                 │                                     │
│  └──────────────────┘                 ▼                                     │
│                              ┌──────────────────┐                           │
│                              │  OUTPUT.blend     │ ← MASTER                 │
│                              │  (NLA + Armature) │                          │
│                              └────────┬──────────┘                          │
│                                       │                                     │
│                                       ▼                                     │
│                              ┌──────────────────┐                           │
│                              │  OUTPUT.abc       │ ← PREVIEW                │
│                              │  (Alembic Cache)  │                          │
│                              └──────────────────┘                           │
│                                                                             │
│  ┌──────────────────┐  (optionnel)                                         │
│  │  Audio.wav +     │───▶ Rhubarb Bridge ───▶ NLA Lip-Sync Strip           │
│  │  Dialogue.txt    │                                                       │
│  └──────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Stack Technique

### Core
- **Python 3.10+** — Orchestration
- **Blender 4.0** — Fusion et export (headless)
- **expression_schema.py** — Bible Anatomique (7 Piliers, 52 ARKit)

### Libraries
- `scipy` — Optionnel, legacy smoothing uniquement

### Blender Natif (3 Leviers Pareto 80/20)
- **F-Curve Bézier** — Interpolation (`AUTO_CLAMPED`)
- **F-Curve Noise Modifier** — Micro-jitter yeux+bouche (strength=0.01-0.03, scale≈8-12Hz)
- **NLA Editor** — Layering multicouche (expression + eyes override + mouth override)

---

## Structure Dossiers V2

```
01_ANIMATION_ENGINE/
├── CODEBASE/
│   ├── EXO_01_TRANSMUTATION.py    # Script principal (orchestrateur)
│   ├── expression_schema.py        # Bible Anatomique (7 Piliers, 52 ARKit)
│   ├── facial_extractor.py         # EmotionalIntentTranslator
│   ├── blender_fusion.py           # Blender headless NLA + Bézier + Noise
│   ├── sync_engine.py              # Synchronisation timecodes/FBX
│   ├── rhubarb_bridge.py           # Lip-sync Rhubarb (optionnel)
│   ├── smoothing.py                # LEGACY — non utilisé en V2
│   ├── requirements.txt
│   ├── EXO_01_CONTROL.ipynb        # Debug notebook V2
│   └── EXO_01_PRODUCTION.ipynb     # Batch notebook V2
├── IN_CORTEX_JSON/                  # facial_animation.json (de U00 CORTEX)
├── IN_MIXAMO_BASE/                  # .fbx body motions (SayMotion/Mixamo)
├── OUT_MOTION_DATA/                 # .blend (Master) + .abc (Preview)
├── UNIT_01_SUBPLAN.md               # Ce fichier
└── README_DEV.md                    # Guide développeur V2
```

---

## Workflow Détaillé

### Phase 1: Emotional Intent Translation
```python
# facial_extractor.py — EmotionalIntentTranslator
# Input: facial_animation.json (produit par U00 CORTEX)
# Output: segments traduits en 52 ARKit Shape Keys

# Format d'entrée (U00 CORTEX)
{
    "facial_animation": [
        {
            "time_start": 0.0,
            "time_end": 2.5,
            "expression": "determined",
            "eyes": "focused_forward",
            "mouth": "closed_tight",
            "intensity": 0.8,
            "apex_time": 1.2,
            "low_visibility": false
        }
    ]
}

# Traduction via expression_schema.py (Bible Anatomique)
# expression + eyes override (zone oculaire) + mouth override (zone buccale)
# → 52 ARKit shape key values fusionnées
```

### Phase 2: Synchronisation
```python
# sync_engine.py — SyncEngine
# Convertit timecodes JSON en numéros de frames
# Aligne sur bornes FBX avec offset optionnel
# Valide timeline (croissant, pas de chevauchement)

framed = sync.timecodes_to_frames(segments, fps=30)
aligned = sync.align_to_fbx(framed, fbx_frame_count=180, offset=0)
```

### Phase 3: Fusion Blender (NLA)
```python
# blender_fusion.py
# Exécuté via: blender --background --python blender_fusion.py -- [args]

# 1. Import FBX body motion
# 2. Import Actor .blend
# 3. Transfer body animation
# 4. Appliquer shape keys faciales via NLA strips multicouche :
#    - Strip expression (base)
#    - Strip eyes override (zone oculaire)
#    - Strip mouth override (zone buccale)
# 5. F-Curve Bézier (handle_right_type = 'AUTO_CLAMPED')
# 6. F-Curve Noise Modifier (micro-jitter)
# 7. (Optionnel) NLA Strip lip-sync Rhubarb
# 8. Export .blend MASTER (avec armature pour U02)
# 9. Export .abc PREVIEW (Alembic cache)
```

### Phase 4: Lip-Sync (Optionnel)
```python
# rhubarb_bridge.py — RhubarbBridge
# Exécute Rhubarb CLI → mouth cues JSON
# Convertit en segments NLA avec valeurs ARKit (LIP_SYNC_VISEMES)
# NLA strip dédié, priorité sur zone bouche pendant parole
```

---

## Paramètres Clés

| Paramètre | Default | Description |
|-----------|---------|-------------|
| `--drive-root` | — | Racine du Drive EXODUS (requis) |
| `--body-fbx` | — | FBX body motion dans IN_MIXAMO_BASE/ (requis) |
| `--facial-json` | — | JSON facial animation dans IN_CORTEX_JSON/ (requis) |
| `--actor-blend` | — | Avatar .blend chemin absolu (requis) |
| `--output-name` | TRANSMUTED_ACTOR | Nom des fichiers output |
| `--sync-offset` | 0 | Offset sync en frames |
| `--intensity-mode` | ease_in_out | Courbe d'intensité (linear, quadratic, ease_in_out) |
| `--audio` | — | Audio pour lip-sync Rhubarb (optionnel) |
| `--dialogue` | — | Texte dialogue pour Rhubarb (optionnel) |
| `--dry-run` | false | Validation sans exécution |

---

## 52 ARKit Blendshapes

### Eyes (14)
`eyeBlinkLeft`, `eyeBlinkRight`, `eyeLookDownLeft`, `eyeLookDownRight`, `eyeLookInLeft`, `eyeLookInRight`, `eyeLookOutLeft`, `eyeLookOutRight`, `eyeLookUpLeft`, `eyeLookUpRight`, `eyeSquintLeft`, `eyeSquintRight`, `eyeWideLeft`, `eyeWideRight`

### Jaw (4)
`jawForward`, `jawLeft`, `jawRight`, `jawOpen`

### Mouth (24)
`mouthClose`, `mouthFunnel`, `mouthPucker`, `mouthLeft`, `mouthRight`, `mouthSmileLeft`, `mouthSmileRight`, `mouthFrownLeft`, `mouthFrownRight`, `mouthDimpleLeft`, `mouthDimpleRight`, `mouthStretchLeft`, `mouthStretchRight`, `mouthRollLower`, `mouthRollUpper`, `mouthShrugLower`, `mouthShrugUpper`, `mouthPressLeft`, `mouthPressRight`, `mouthLowerDownLeft`, `mouthLowerDownRight`, `mouthUpperUpLeft`, `mouthUpperUpRight`

### Brow (5)
`browDownLeft`, `browDownRight`, `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight`

### Cheek (3)
`cheekPuff`, `cheekSquintLeft`, `cheekSquintRight`

### Nose (2)
`noseSneerLeft`, `noseSneerRight`

### Tongue (1)
`tongueOut`

---

## Troubleshooting

### Expression inconnue rejetée
- Vérifier que l'expression est dans `VALID_EXPRESSIONS` (15 presets)
- Vérifier que les yeux sont dans `VALID_EYE_STATES` (9 états)
- Vérifier que la bouche est dans `VALID_MOUTH_STATES` (8 états)

### Transition abrupte entre émotions
- Le translator insère automatiquement un segment neutre intermédiaire pour les émotions antagonistes
- Vérifier via `schema.requires_neutral_transition(expr_a, expr_b)`

### Shape keys manquantes sur l'avatar
- L'avatar doit avoir les 52 ARKit shape keys exactes
- `blender_fusion.py` crée automatiquement les keys manquantes (fallback)

### Blender crash
- Vérifier que Blender 4.0 portable est installé dans `EXODUS_AI_MODELS/`
- Vérifier les chemins absolus

### Lip-sync non fonctionnel
- Rhubarb est optionnel et doit être installé séparément
- Le pipeline fonctionne sans lip-sync si `--audio` n'est pas spécifié

---

## Performance

| Étape | Temps estimé (1000 frames) |
|-------|---------------------------|
| Emotional Intent Translation | < 1 sec (pure Python) |
| Blender fusion + NLA | ~2 min |
| Export Alembic | ~1 min |

**Total estimé** : ~3 min par acteur. RÉDUIT vs V1 (zéro GPU pour extraction faciale).

---

## Dépendances Externes

### Sur Google Drive (EXODUS_AI_MODELS/)
```
EXODUS_AI_MODELS/
├── blender-4.0.0-linux-x64/
│   └── blender
└── rhubarb/                    # Optionnel — lip-sync
    └── rhubarb
```

---

## Checklist Production V2

- [ ] Inputs validés (FBX dans IN_MIXAMO_BASE/, JSON dans IN_CORTEX_JSON/, .blend avatar)
- [ ] Blender 4.0 installé
- [ ] Marshal check-in passé
- [ ] Expression Schema testé (15 expressions + 9 yeux + 8 bouche)
- [ ] Dry-run passé
- [ ] Output .blend généré (MASTER) dans OUT_MOTION_DATA/
- [ ] Output .abc généré (PREVIEW) dans OUT_MOTION_DATA/
- [ ] Marshal check-out passé
- [ ] Prêt pour U02 (LOGISTICS)

---

*EXODUS SYSTEM — Frégate 01_TRANSMUTATION v2.0.0*
