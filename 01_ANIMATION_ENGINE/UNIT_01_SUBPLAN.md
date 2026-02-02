# 🔧 UNIT 01 — TRANSMUTATION ENGINE

## Sub-Plan Technique

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 01_TRANSMUTATION — TECHNICAL SUBPLAN                 ║
║                    Body Motion + Facial Capture → Alembic                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🎯 Mission

Fusionner des animations corporelles (FBX MoCap) avec des expressions faciales extraites par IA (EMOCA) pour produire des animations complètes exportées en Alembic (.abc).

### Inputs
| Type | Format | Source |
|------|--------|--------|
| Body Motion | `.fbx` | MoCap Pro / Rokoko / Mixamo |
| Face Video | `.mp4` | iPhone / Webcam |
| Actor Model | `.blend` | Avatar Roblox avec DynamicHead |

### Output
| Type | Format | Destination |
|------|--------|-------------|
| Baked Animation | `.abc` | Blender / Unity / Roblox |
| Face Data | `.json` | Debug / Archive |

---

## 🏗️ Architecture Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRANSMUTATION PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Video.mp4  │───▶│    EMOCA     │───▶│  face.json   │                  │
│  │  (Facial)    │    │  Extraction  │    │ (52 ARKit)   │                  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘                  │
│                                                  │                          │
│  ┌──────────────┐                               ▼                          │
│  │  Motion.fbx  │───────────────────────▶┌──────────────┐                  │
│  │   (Body)     │                        │   BLENDER    │                  │
│  └──────────────┘                        │   FUSION     │                  │
│                                          │  (Headless)  │                  │
│  ┌──────────────┐                        └──────┬───────┘                  │
│  │ Avatar.blend │───────────────────────────────┘                          │
│  │  (Rigged)    │                               │                          │
│  └──────────────┘                               ▼                          │
│                                          ┌──────────────┐                  │
│                                          │  OUTPUT.abc  │                  │
│                                          │  (Alembic)   │                  │
│                                          └──────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Stack Technique

### Core
- **Python 3.10+** — Orchestration
- **Blender 4.0** — Fusion et export (headless)
- **EMOCA** — Extraction faciale 3D

### Libraries
- `torch` — Deep Learning (EMOCA)
- `opencv-python` — Video processing
- `scipy` — Savitzky-Golay filtering
- `omegaconf` — Configuration EMOCA

---

## 🗂️ Structure Dossiers

```
01_ANIMATION_ENGINE/
├── CODEBASE/
│   ├── EXO_01_TRANSMUTATION.py    # Script principal (wrapper)
│   ├── facial_extractor.py         # EMOCA → 52 ARKit
│   ├── blender_fusion.py           # Blender headless fusion
│   ├── sync_engine.py              # Synchronisation body/face
│   ├── smoothing.py                # Savitzky-Golay filter
│   ├── requirements.txt
│   ├── EXO_01_CONTROL.ipynb        # Debug notebook
│   └── EXO_01_PRODUCTION.ipynb     # Batch notebook
├── IN_INPUTS/
│   ├── body_motions/               # .fbx files
│   ├── source_videos/              # .mp4 files
│   └── actor_models/               # .blend files
├── OUT_BAKED/
│   └── *.abc                       # Outputs
├── UNIT_01_SUBPLAN.md              # Ce fichier
└── README_DEV.md                   # Guide développeur
```

---

## 🔄 Workflow Détaillé

### Phase 1: Extraction Faciale (EMOCA)
```python
# facial_extractor.py
# Input: video.mp4
# Output: face.json (52 ARKit blendshapes par frame)

{
    "fps": 30,
    "frames": [
        {
            "frame": 0,
            "blendshapes": {
                "eyeBlinkLeft": 0.0,
                "mouthSmileLeft": 0.45,
                ...
            },
            "confidence": 0.95
        }
    ]
}
```

### Phase 2: Synchronisation
```python
# sync_engine.py
# Méthodes:
# - manual: offset direct en frames
# - marker: calcul depuis frames de référence (clap, etc.)
# - audio: corrélation croisée audio (expérimental)

offset = video_frame - fbx_frame
# offset > 0: vidéo en avance
# offset < 0: FBX en avance
```

### Phase 3: Fusion Blender
```python
# blender_fusion.py
# Exécuté via: blender --background --python blender_fusion.py -- [args]

# 1. Import FBX body motion
# 2. Import Actor .blend
# 3. Transfer body animation
# 4. Apply facial shape keys
# 5. Apply smoothing
# 6. Export Alembic
```

### Phase 4: Smoothing
```python
# smoothing.py
# Savitzky-Golay: préserve les peaks, supprime le jitter

# Mode adaptatif:
# - Mouvements lents → window=7
# - Mouvements rapides → window=3 (préserve micro-expressions)
```

---

## 🎚️ Paramètres Clés

| Paramètre | Default | Description |
|-----------|---------|-------------|
| `--sync-offset` | 0 | Offset sync en frames |
| `--smooth-window` | 5 | Fenêtre Savitzky-Golay |
| `--sync-marker` | — | Paire (video_frame, fbx_frame) |
| `--dry-run` | false | Validation sans exécution |

---

## 📊 52 ARKit Blendshapes

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

## 🚨 Troubleshooting

### EMOCA ne trouve pas de visage
- Vérifier l'éclairage de la vidéo
- Le visage doit être visible (pas de profil extrême)
- Résolution minimum: 480p

### Sync décalé
- Utiliser `--sync-marker` avec un point de référence clair (clap)
- Vérifier les FPS de la vidéo et du FBX

### Blender crash
- Vérifier que Blender 4.0 portable est bien installé
- Vérifier les chemins absolus

### Shape keys manquantes
- L'avatar doit avoir les 52 ARKit shape keys
- Utiliser le mode fallback qui crée les keys manquantes

---

## 📈 Performance

| Étape | Temps estimé (1000 frames) |
|-------|---------------------------|
| EMOCA extraction | ~5 min (GPU) / ~20 min (CPU) |
| Blender fusion | ~2 min |
| Export Alembic | ~1 min |

**Total estimé**: 8-25 min par acteur selon hardware.

---

## 🔗 Dépendances Externes

### Sur Google Drive (EXODUS_AI_MODELS/)
```
EXODUS_AI_MODELS/
├── blender-4.0.0-linux-x64/
│   └── blender
└── emoca/
    ├── cfg.yaml
    └── model.ckpt
```

---

## ✅ Checklist Production

- [ ] Inputs validés (FBX, MP4, BLEND)
- [ ] EMOCA modèle présent
- [ ] Blender 4.0 installé
- [ ] Sync offset calculé
- [ ] Dry-run passé
- [ ] Output .abc généré
- [ ] Validé dans Blender

---

*EXODUS SYSTEM — Frégate 01_TRANSMUTATION v1.0.0*
