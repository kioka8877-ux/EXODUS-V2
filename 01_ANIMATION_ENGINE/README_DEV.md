# README DEV — TRANSMUTATION ENGINE V2

## Guide Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║           FRÉGATE 01_TRANSMUTATION — DEVELOPER GUIDE V2                      ║
║                  Emotional Intent Transfer Pipeline                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Quick Start

### 1. Setup Google Colab

```python
from google.colab import drive
drive.mount('/content/drive')

DRIVE_ROOT = "/content/drive/MyDrive/DRIVE_EXODUS_V2"
CODEBASE = f"{DRIVE_ROOT}/01_ANIMATION_ENGINE/CODEBASE"

import sys
sys.path.insert(0, CODEBASE)
```

### 2. Install Dependencies

```bash
# V2: ZÉRO dépendance ML. scipy optionnel pour smoothing legacy.
pip install -q scipy
```

### 3. Run Pipeline

```bash
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx dance_motion.fbx \
    --facial-json facial_animation.json \
    --actor-blend avatar.blend \
    --output-name ACTOR_01 \
    --intensity-mode ease_in_out \
    -v
```

---

## Installation Blender 4.0

### Automatique (recommandé)
Le notebook `EXO_01_PRODUCTION.ipynb` installe automatiquement Blender si absent.

### Manuelle
```bash
wget https://download.blender.org/release/Blender4.0/blender-4.0.0-linux-x64.tar.xz
tar -xf blender-4.0.0-linux-x64.tar.xz -C /content/drive/MyDrive/DRIVE_EXODUS_V2/EXODUS_AI_MODELS/
```

### Vérification
```bash
/content/drive/MyDrive/DRIVE_EXODUS_V2/EXODUS_AI_MODELS/blender-4.0.0-linux-x64/blender --version
```

---

## Expression Schema (Bible Anatomique)

Le module `expression_schema.py` est le cœur du pipeline V2. Il définit **toutes** les données nécessaires à la traduction émotion → 52 ARKit Shape Keys, via 7 Piliers :

| Pilier | Contenu |
|--------|---------|
| 1 | 15 EXPRESSION_PRESETS × 52 ARKit (joy, sadness, anger, fear, surprise, disgust, neutral, suspicious, determined, confused, pain, love, bored, excited, shocked) |
| 2 | Matrice des Conflits (combinaisons anatomiques interdites : mouthSmile+mouthFrown, eyeBlink+eyeWide, jawOpen+mouthClose) |
| 3 | Table des Oppositions (émotions antagonistes obligeant passage par neutre : joy↔sadness, joy↔anger, anger↔fear, surprise↔bored, love↔disgust) |
| 4 | Ranges Anatomiques (clampage esthétique Roblox : jaw max 0.8, tongueOut max 0.5) |
| 5 | Courbes d'Intensité (scaling : linear, quadratic, ease-in-out) |
| 6 | Micro-Expressions Involontaires (presets blink/tics pour briser la rigidité) |
| 7 | EYE_PRESETS (9 états) + MOUTH_PRESETS (8 états) + Règle de fusion multicouche |

### Test rapide

```python
from expression_schema import ExpressionSchema, ARKIT_52_BLENDSHAPES, VALID_EXPRESSIONS

schema = ExpressionSchema()

# Fusion expression + eyes + mouth
values = schema.fuse_expression("joy", "narrowed", "smiling", intensity=0.8)
active = {k: v for k, v in values.items() if v > 0}
print(f"Active keys: {len(active)}")

# Validation hérétique (doit rejeter intensity > 1.0)
ok, errs = schema.validate_expression_request("joy", "focused_forward", "neutral", intensity=1.5)
print(f"Heresy blocked: {not ok}")

# Transition obligatoire
needs_neutral = schema.requires_neutral_transition("joy", "sadness")
print(f"joy→sadness needs neutral: {needs_neutral}")
```

---

## CLI Reference

```bash
python EXO_01_TRANSMUTATION.py [OPTIONS]

# Required
--drive-root PATH            Racine du Drive EXODUS
--body-fbx FILE              FBX body motion (dans IN_MIXAMO_BASE/)
--facial-json FILE           JSON facial animation (dans IN_CORTEX_JSON/)
--actor-blend FILE           Blend avatar (chemin absolu)

# Optional
--production-plan FILE       Plan de production JSON (batch)
--output-name NAME           Nom output (défaut: TRANSMUTED_ACTOR)
--sync-offset INT            Offset sync en frames (défaut: 0)
--intensity-mode MODE        Courbe d'intensité: linear|quadratic|ease_in_out (défaut: ease_in_out)
--audio FILE                 Audio source pour lip-sync Rhubarb (dans IN_CORTEX_JSON/)
--dialogue FILE              Texte dialogue pour lip-sync Rhubarb (dans IN_CORTEX_JSON/)
-v, --verbose                Logs détaillés
--dry-run                    Validation sans exécution
```

### Exemples

```bash
# Basic
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx walk.fbx \
    --facial-json facial_animation.json \
    --actor-blend /path/to/avatar.blend

# Avec lip-sync Rhubarb
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx dance.fbx \
    --facial-json facial_animation.json \
    --actor-blend /path/to/avatar.blend \
    --audio audio_source.wav \
    --dialogue dialogue.txt \
    --intensity-mode ease_in_out \
    -v

# Dry run (validation seulement)
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx test.fbx \
    --facial-json facial_animation.json \
    --actor-blend /path/to/avatar.blend \
    --dry-run
```

---

## Module API

### expression_schema.py

```python
from expression_schema import (
    ExpressionSchema,
    ARKIT_52_BLENDSHAPES,
    VALID_EXPRESSIONS,
    VALID_EYE_STATES,
    VALID_MOUTH_STATES,
)

schema = ExpressionSchema()

# Fusion expression + eyes override + mouth override
values = schema.fuse_expression("joy", "narrowed", "smiling", intensity=0.8)

# Validation (rejette combinaisons hérétiques)
ok, errors = schema.validate_expression_request("joy", "focused_forward", "neutral", intensity=0.8)

# Transition obligatoire entre émotions antagonistes
needs_neutral = schema.requires_neutral_transition("joy", "sadness")

# Micro-expressions involontaires (blink, tics)
micros = schema.get_micro_expression_presets()
```

### facial_extractor.py

```python
from facial_extractor import EmotionalIntentTranslator

translator = EmotionalIntentTranslator()

# Charger facial_animation.json (produit par U00 CORTEX)
data = translator.load_facial_animation("facial_animation.json")

# Traduire en données Blender (segments + frames + 52 ARKit values)
blender_data = translator.generate_blender_data(data, fps=30)

# Structure retournée
# {
#     "fps": 30,
#     "segments": [
#         {
#             "frame_start": 0,
#             "frame_end": 75,
#             "frame_apex": 36,
#             "values": { "eyeBlinkLeft": 0.0, "mouthSmileLeft": 0.64, ... },
#             "is_transition": false
#         },
#         ...
#     ],
#     "micro_expressions": { "blink": {...}, "tic_mouth": {...} }
# }
```

### sync_engine.py

```python
from sync_engine import SyncEngine

sync = SyncEngine(verbose=True)

# Convertir timecodes en frames
segments = [
    {"time_start": 0.0, "time_end": 2.5, "apex_time": 1.2},
    {"time_start": 2.5, "time_end": 5.0, "apex_time": 3.8},
]
framed = sync.timecodes_to_frames(segments, fps=30)

# Aligner sur bornes FBX
aligned = sync.align_to_fbx(framed, fbx_frame_count=180, offset=0)

# Valider timeline (croissant, pas de chevauchement, apex dans bornes)
ok, errors = sync.validate_timeline(segments)

# Rapport de synchronisation
report = sync.create_sync_report(
    body_path="motion.fbx",
    facial_json_path="facial_animation.json",
    offset=0,
    fbx_frame_count=180,
    segment_count=3,
)
```

### rhubarb_bridge.py

```python
from rhubarb_bridge import RhubarbBridge

bridge = RhubarbBridge(rhubarb_path="/path/to/rhubarb")

# Exécuter Rhubarb CLI → mouth cues JSON
raw = bridge.run_rhubarb("audio.wav", dialogue_path="dialogue.txt")

# Générer lip-sync NLA data (ARKit viseme values)
lip_data = bridge.generate_lip_sync_data("audio.wav", dialogue_path="dialogue.txt", fps=30)
```

### smoothing.py — LEGACY

> **Note** : Module legacy, non utilisé par le pipeline V2. Conservé pour rétrocompatibilité.
> Le pipeline V2 utilise les F-Curve Bézier et Noise Modifier natifs de Blender pour le lissage et le micro-jitter.

```python
from smoothing import savgol_smooth, adaptive_smooth, smooth_blendshapes
# Legacy — voir documentation V1 si nécessaire.
```

---

## Préparer un Avatar Roblox

### Requirements
1. Avatar au format `.blend`
2. Armature Roblox standard
3. Mesh tête avec les 52 shape keys ARKit

### Naming Convention
Les shape keys doivent être nommées exactement selon ARKit :
- `eyeBlinkLeft` ✓
- `EyeBlinkLeft` ✗
- `eye_blink_left` ✗

### Script de vérification
```python
import bpy
from expression_schema import ARKIT_52_BLENDSHAPES

mesh = bpy.data.objects["Head"]
keys = mesh.data.shape_keys.key_blocks

missing = [name for name in ARKIT_52_BLENDSHAPES if name not in keys]
if missing:
    print(f"Shape keys manquantes: {missing}")
else:
    print("✓ Toutes les shape keys présentes")
```

---

## Folder Structure V2

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
├── IN_CORTEX_JSON/                  # facial_animation.json (de U00)
├── IN_MIXAMO_BASE/                  # .fbx body motions
├── OUT_MOTION_DATA/                 # .blend (Master) + .abc (Preview)
├── UNIT_01_SUBPLAN.md
└── README_DEV.md                    # Ce fichier
```

---

## Output Format V2

### Master — `.blend`
- Armature complète avec animation corporelle
- Shape keys faciales sur NLA strips (expression + eyes override + mouth override)
- F-Curve Bézier (`AUTO_CLAMPED`) pour interpolation
- F-Curve Noise Modifier pour micro-jitter (strength=0.01-0.03, scale≈8-12Hz)
- **Destination** : U02 LOGISTICS (props attachment)

### Preview — `.abc`
- Alembic cache du mesh animé
- Preview / backup
- **Destination** : Preview / Archive

Les deux fichiers sont générés dans `OUT_MOTION_DATA/`.

---

## Debug

### Logs détaillés
```bash
python EXO_01_TRANSMUTATION.py [...] -v
```

### Test Expression Schema
```python
from expression_schema import ExpressionSchema, VALID_EXPRESSIONS, VALID_EYE_STATES, VALID_MOUTH_STATES

schema = ExpressionSchema()
print(f"Expressions: {len(VALID_EXPRESSIONS)}")
print(f"Eye States: {len(VALID_EYE_STATES)}")
print(f"Mouth States: {len(VALID_MOUTH_STATES)}")

# Test hérétique
ok, errs = schema.validate_expression_request("joy", "focused_forward", "neutral", intensity=1.5)
assert not ok, "Heresy should be blocked"
```

### Test EmotionalIntentTranslator
```python
from facial_extractor import EmotionalIntentTranslator

translator = EmotionalIntentTranslator()
sample = {
    "facial_animation": [{
        "time_start": 0.0, "time_end": 2.5,
        "expression": "joy", "eyes": "narrowed", "mouth": "smiling",
        "intensity": 0.8, "apex_time": 1.2, "low_visibility": False,
    }]
}
blender_data = translator.generate_blender_data(sample, fps=30)
print(f"Segments: {len(blender_data['segments'])}")
```

### Dry-run Pipeline
```bash
python EXO_01_TRANSMUTATION.py \
    --drive-root /path/to/DRIVE_EXODUS_V2 \
    --body-fbx test.fbx \
    --facial-json facial_animation.json \
    --actor-blend /path/to/avatar.blend \
    --dry-run -v
```

---

## Known Issues V2

| Issue | Description | Workaround |
|-------|-------------|------------|
| Expression inconnue | `validate_expression_request()` rejette les expressions hors des 15 presets | Utiliser uniquement les expressions de `VALID_EXPRESSIONS` |
| Transition abrupte | Certaines transitions entre émotions antagonistes peuvent être visibles | Le translator insère automatiquement un segment neutre intermédiaire |
| Shape keys manquantes | L'avatar doit avoir les 52 ARKit shape keys exactes | `blender_fusion.py` crée les keys manquantes automatiquement |
| Rhubarb non installé | Le lip-sync Rhubarb est optionnel | Le pipeline fonctionne sans lip-sync. Installer Rhubarb pour l'activer |
| Intensity scaling | `intensity=1.0` dans le JSON U00 ≠ multiplication brute | Les courbes d'intensité (Pilier 5) appliquent un scaling non-linéaire |

---

## Changelog

### v2.0.0 — Emotional Intent Transfer
- **Supprimé** : EMOCA, torch, torchvision, opencv, omegaconf — ZÉRO dépendance ML
- **Nouveau** : `expression_schema.py` (Bible Anatomique, 7 Piliers, 52 ARKit)
- **Nouveau** : `EmotionalIntentTranslator` dans `facial_extractor.py` (remplace `EMOCAExtractor`)
- **Nouveau** : NLA strips Blender pour layering multicouche (expression + eyes + mouth)
- **Nouveau** : F-Curve Bézier natif (`AUTO_CLAMPED`) + F-Curve Noise Modifier (micro-jitter)
- **Nouveau** : `rhubarb_bridge.py` pour lip-sync optionnel
- **Nouveau** : Dossiers V2 (`IN_CORTEX_JSON/`, `IN_MIXAMO_BASE/`, `OUT_MOTION_DATA/`)
- **Nouveau** : CLI args `--facial-json`, `--intensity-mode`, `--audio`, `--dialogue`
- **Supprimé** : CLI args `--video`, `--sync-marker`, `--smooth-window`
- **Modifié** : `sync_engine.py` simplifié (timecodes JSON → frames, plus de sync audio/marqueur)
- **Modifié** : `smoothing.py` marqué LEGACY (F-Curve natif Blender remplace Savitzky-Golay)
- **Flow** : U00 CORTEX produit `facial_animation.json` → U01 traduit en shape keys via la Bible

---

*EXODUS SYSTEM — Frégate 01_TRANSMUTATION v2.0.0*
