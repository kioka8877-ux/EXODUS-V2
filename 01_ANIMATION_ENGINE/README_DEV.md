# 🛠️ README DEV — TRANSMUTATION ENGINE

## Guide Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FRÉGATE 01_TRANSMUTATION — DEVELOPER GUIDE                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🚀 Quick Start

### 1. Setup Google Colab

```python
# Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Configuration
DRIVE_ROOT = "/content/drive/MyDrive/DRIVE_EXODUS_V2"
CODEBASE = f"{DRIVE_ROOT}/01_ANIMATION_ENGINE/CODEBASE"

import sys
sys.path.insert(0, CODEBASE)
```

### 2. Install Dependencies

```bash
pip install torch torchvision opencv-python-headless scipy omegaconf Pillow tqdm
```

### 3. Run Pipeline

```bash
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx dance_motion.fbx \
    --video face_capture.mp4 \
    --actor-blend avatar.blend \
    --output-name ACTOR_01 \
    -v
```

---

## 📦 Installation Blender 4.0

### Automatique (recommandé)
Le notebook `EXO_01_PRODUCTION.ipynb` installe automatiquement Blender si absent.

### Manuelle
```bash
# Télécharger Blender 4.0 portable
wget https://download.blender.org/release/Blender4.0/blender-4.0.0-linux-x64.tar.xz

# Extraire sur le Drive
tar -xf blender-4.0.0-linux-x64.tar.xz -C /content/drive/MyDrive/DRIVE_EXODUS_V2/EXODUS_AI_MODELS/
```

### Vérification
```bash
/content/drive/MyDrive/DRIVE_EXODUS_V2/EXODUS_AI_MODELS/blender-4.0.0-linux-x64/blender --version
```

---

## 🧠 Installation EMOCA

### Option A: Modèles pré-entraînés
1. Télécharger depuis: https://github.com/radekd91/emoca
2. Placer dans `EXODUS_AI_MODELS/emoca/`:
   - `cfg.yaml`
   - `model.ckpt`

### Option B: Mode Fallback
Si EMOCA n'est pas disponible, le système utilise un mode fallback basé sur l'analyse d'image. Moins précis mais fonctionnel pour les tests.

---

## 🎮 CLI Reference

```bash
python EXO_01_TRANSMUTATION.py [OPTIONS]

# Required
--drive-root PATH       Racine du Drive EXODUS
--body-fbx FILE         FBX body motion (dans IN_INPUTS/body_motions/)
--video FILE            MP4 source video (dans IN_INPUTS/source_videos/)
--actor-blend FILE      Blend avatar (dans IN_INPUTS/actor_models/)

# Optional
--output-name NAME      Nom output (défaut: TRANSMUTED_ACTOR)
--sync-offset INT       Offset sync en frames (défaut: 0)
--sync-marker V F       Calcul offset: V=video_frame, F=fbx_frame
--smooth-window INT     Fenêtre Savitzky-Golay, impair (défaut: 5)
-v, --verbose           Logs détaillés
--dry-run               Validation sans exécution
```

### Exemples

```bash
# Basic
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx walk.fbx \
    --video capture.mp4 \
    --actor-blend avatar.blend

# Avec sync par marqueur (clap à frame 150 vidéo, 100 FBX)
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx dance.fbx \
    --video face.mp4 \
    --actor-blend model.blend \
    --sync-marker 150 100 \
    --smooth-window 7 \
    -v

# Dry run (validation seulement)
python EXO_01_TRANSMUTATION.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --body-fbx test.fbx \
    --video test.mp4 \
    --actor-blend test.blend \
    --dry-run
```

---

## 🧩 Module API

### facial_extractor.py

```python
from facial_extractor import EMOCAExtractor, ARKIT_52_BLENDSHAPES

# Initialiser
extractor = EMOCAExtractor("/path/to/emoca")

# Extraire
face_data = extractor.extract_arkit_from_video(
    video_path="video.mp4",
    start_frame=0,
    end_frame=-1  # -1 = toutes les frames
)

# Structure retournée
{
    "fps": 30,
    "total_frames": 1000,
    "frames": [
        {
            "frame": 0,
            "blendshapes": {
                "eyeBlinkLeft": 0.0,
                "mouthSmileLeft": 0.5,
                ...
            },
            "confidence": 0.95
        },
        ...
    ]
}
```

### sync_engine.py

```python
from sync_engine import SyncEngine

sync = SyncEngine(verbose=True)

# Calcul offset par marqueur
offset = sync.calculate_offset(
    method="marker",
    marker_video=150,  # Frame du clap dans la vidéo
    marker_fbx=100     # Frame du mouvement dans le FBX
)

# Validation
is_valid, message = sync.validate_sync(
    body_length=1000,
    face_length=900,
    offset=offset
)

# Rapport complet
report = sync.create_sync_report(
    body_path="motion.fbx",
    video_path="capture.mp4",
    offset=offset,
    body_length=1000,
    face_length=900
)
```

### smoothing.py

```python
from smoothing import savgol_smooth, adaptive_smooth, smooth_blendshapes

import numpy as np

# Lissage simple
data = np.random.rand(100)
smoothed = savgol_smooth(data, window=5)

# Lissage adaptatif (préserve micro-expressions)
data_2d = np.random.rand(100, 52)
smoothed = adaptive_smooth(
    data_2d,
    base_window=7,
    velocity_threshold=0.1
)

# Lissage sur données faciales JSON
smoothed_data = smooth_blendshapes(
    face_data,
    window=5,
    adaptive=True
)
```

---

## 🎭 Préparer un Avatar Roblox

### Requirements
1. Avatar doit être au format `.blend`
2. Doit avoir un armature Roblox standard
3. Le mesh tête doit avoir les 52 shape keys ARKit

### Naming Convention
Les shape keys doivent être nommées exactement selon ARKit:
- `eyeBlinkLeft` ✓
- `EyeBlinkLeft` ✗
- `eye_blink_left` ✗

### Script de vérification
```python
import bpy

mesh = bpy.data.objects["Head"]  # Adapter le nom
keys = mesh.data.shape_keys.key_blocks

from facial_extractor import ARKIT_52_BLENDSHAPES

missing = []
for name in ARKIT_52_BLENDSHAPES:
    if name not in keys:
        missing.append(name)

if missing:
    print(f"Shape keys manquantes: {missing}")
else:
    print("✓ Toutes les shape keys présentes")
```

---

## 🔧 Debug

### Logs détaillés
```bash
python EXO_01_TRANSMUTATION.py [...] -v
```

### Test EMOCA seul
```bash
python facial_extractor.py video.mp4 /path/to/emoca
```

### Test Blender seul
```bash
blender --background --python blender_fusion.py -- \
    --body-fbx motion.fbx \
    --actor-blend avatar.blend \
    --face-json face.json \
    --output output.abc
```

### Inspecter face.json
```python
import json
with open("face.json") as f:
    data = json.load(f)
    
print(f"Frames: {len(data['frames'])}")
print(f"FPS: {data['fps']}")

# Voir valeurs max par blendshape
from collections import defaultdict
max_vals = defaultdict(float)
for frame in data['frames']:
    for key, val in frame['blendshapes'].items():
        max_vals[key] = max(max_vals[key], val)

for key, val in sorted(max_vals.items(), key=lambda x: -x[1])[:10]:
    print(f"  {key}: {val:.3f}")
```

---

## 📊 Performance Tips

### GPU Acceleration
```python
# Vérifier GPU dans Colab
import torch
print(f"GPU: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
```

### Batch Processing
Utiliser `EXO_01_PRODUCTION.ipynb` pour traiter plusieurs acteurs en séquence.

### Réduire le temps
1. Limiter les frames (`end_frame=500`)
2. Réduire `smooth_window` (3 au lieu de 7)
3. Utiliser GPU pour EMOCA

---

## 🐛 Known Issues

### Issue: "EMOCA model not found"
**Solution**: Mode fallback automatique. Pour full quality, installer EMOCA.

### Issue: "Shape key not found in mesh"
**Solution**: Le script crée automatiquement les shape keys manquantes.

### Issue: "Blender crash on export"
**Solution**: Vérifier RAM disponible. Réduire le nombre de frames si nécessaire.

### Issue: "Audio sync doesn't work"
**Solution**: Audio sync est expérimental. Utiliser `--sync-marker` à la place.

---

## 📁 Output Format

### Alembic (.abc)
- Contient mesh + animation
- Compatible: Blender, Unity, Maya
- Inclut shape keys animées

### Face JSON
```json
{
    "fps": 30,
    "total_frames": 1000,
    "source_video": "capture.mp4",
    "frames": [...]
}
```

---

## 🔗 Resources

- [EMOCA GitHub](https://github.com/radekd91/emoca)
- [Blender Python API](https://docs.blender.org/api/current/)
- [ARKit Face Tracking](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation)
- [Savitzky-Golay Filter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html)

---

## 📝 Changelog

### v1.0.0
- Initial release
- EMOCA facial extraction
- Blender headless fusion
- Savitzky-Golay smoothing
- Sync engine (manual, marker)

---

*EXODUS SYSTEM — Frégate 01_TRANSMUTATION v1.0.0*
