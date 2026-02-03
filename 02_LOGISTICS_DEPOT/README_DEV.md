# 🛠️ README DEV — LOGISTICS DEPOT

## Guide Développeur

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              FRÉGATE 02_LOGISTICS — DEVELOPER GUIDE                          ║
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
CODEBASE = f"{DRIVE_ROOT}/02_LOGISTICS_DEPOT/CODEBASE"

import sys
sys.path.insert(0, CODEBASE)
```

### 2. Install Dependencies

```bash
pip install numpy
```

### 3. Run Pipeline

```bash
python EXO_02_LOGISTICS.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --actor-blend actor_animated.blend \
    --production-plan PRODUCTION_PLAN.JSON \
    -v
```

---

## 📦 Installation Blender 4.0

### Automatique (recommandé)
Le notebook `EXO_02_PRODUCTION.ipynb` installe automatiquement Blender si absent.

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

## 🎮 CLI Reference

```bash
python EXO_02_LOGISTICS.py [OPTIONS]

# Required
--drive-root PATH         Racine du Drive EXODUS
--actor-blend FILE        Actor .blend animé (de U01)
--production-plan FILE    PRODUCTION_PLAN.JSON du Cortex

# Optional
--props-library PATH      Dossier props_library/ (défaut: IN_LOGISTICS/props_library)
--output-dir PATH         Dossier output (défaut: OUT_EQUIPPED/)
--output-name NAME        Nom output (défaut: actor_equipped)
--blender-path PATH       Chemin custom vers Blender
-v, --verbose             Logs détaillés
--dry-run                 Validation sans exécution
```

### Exemples

```bash
# Basic
python EXO_02_LOGISTICS.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --actor-blend actor_animated.blend \
    --production-plan PRODUCTION_PLAN.JSON

# Avec options
python EXO_02_LOGISTICS.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --actor-blend /path/to/actor.blend \
    --production-plan /path/to/plan.json \
    --props-library /path/to/props/ \
    --output-name hero_equipped \
    -v

# Dry run (validation seulement)
python EXO_02_LOGISTICS.py \
    --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \
    --actor-blend test.blend \
    --production-plan test.json \
    --dry-run
```

---

## 📋 Format PRODUCTION_PLAN.JSON

### Structure Complète

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "props_actions": [
        {
          "frame": 100,
          "action": "GRAB",
          "prop_id": "gun_pistol",
          "actor": "Actor_1",
          "socket": "hand_right"
        },
        {
          "frame": 250,
          "action": "DROP",
          "prop_id": "gun_pistol",
          "actor": "Actor_1"
        },
        {
          "frame": 300,
          "action": "GRAB",
          "prop_id": "phone_smartphone",
          "actor": "Actor_1",
          "socket": "hand_left"
        }
      ]
    }
  ]
}
```

### Actions Supportées

| Action | Description |
|--------|-------------|
| `GRAB` | Attache le prop au socket et le rend visible |
| `DROP` | Désactive la contrainte (le prop "tombe") |
| `HIDE` | Cache le prop |
| `SHOW` | Montre le prop (sans l'attacher) |
| `SWITCH_SOCKET` | Change de socket (`new_socket` requis) |

### Sockets Disponibles

| Socket | Bones reconnus |
|--------|----------------|
| `hand_right` | hand.R, RightHand, mixamorig:RightHand, ... |
| `hand_left` | hand.L, LeftHand, mixamorig:LeftHand, ... |
| `back` | spine.003, Spine3, UpperBack, ... |
| `head` | head, Head, mixamorig:Head, ... |
| `hip_holster` | pelvis, Hips, mixamorig:Hips, ... |
| `chest` | spine.002, Spine2, Chest, ... |
| `shoulder_right` | shoulder.R, RightShoulder, ... |
| `shoulder_left` | shoulder.L, LeftShoulder, ... |
| `foot_right` | foot.R, RightFoot, ... |
| `foot_left` | foot.L, LeftFoot, ... |

---

## 🧩 Module API

### socketing_engine.py

```python
from socketing_engine import SocketingEngine

# Initialiser
engine = SocketingEngine(verbose=True)

# Trouver l'armature
armature = engine.find_armature()

# Lister les sockets disponibles
sockets = engine.list_available_sockets()
# {'hand_right': 'mixamorig:RightHand', ...}

# Attacher un prop
engine.attach_to_socket(
    prop_obj,
    socket_name="hand_right",
    custom_offset=(0.05, 0, 0),
    custom_rotation=(0, 0, 45)
)
```

### timeline_manager.py

```python
from timeline_manager import TimelineManager

timeline = TimelineManager(verbose=True)

# Montrer un prop à la frame 100
timeline.show_prop(prop_obj, frame=100)

# Activer la contrainte d'attachement
timeline.activate_constraint(prop_obj, frame=100)

# Désactiver (drop) à la frame 250
timeline.deactivate_constraint(prop_obj, frame=250)

# Ou appliquer une séquence complète
events = [
    {"frame": 100, "action": "GRAB"},
    {"frame": 250, "action": "DROP"},
    {"frame": 300, "action": "HIDE"}
]
timeline.apply_prop_timeline(prop_obj, events)
```

### props_loader.py

```python
from props_loader import PropsLoader

# Scanner la bibliothèque
loader = PropsLoader("/path/to/props_library", verbose=True)
props = loader.scan_library()

# Charger un prop
prop_obj = loader.load_prop("gun_pistol")

# Dupliquer pour un second acteur
prop_copy = loader.load_prop("gun_pistol")  # Auto-duplicate
```

### final_baker.py

```python
from final_baker import bake_and_export, save_blend_backup, get_export_stats

# Vérifier les stats
stats = get_export_stats()
print(f"Objects: {stats['total_objects']}")
print(f"Frame range: {stats['frame_range']}")

# Exporter en Alembic
bake_and_export("/output/actor_equipped.abc")

# Sauvegarder le blend
save_blend_backup("/output/actor_equipped.blend")
```

---

## 🔧 Props Library

### Formats Supportés

| Extension | Format |
|-----------|--------|
| `.glb` | GLTF Binary (recommandé) |
| `.gltf` | GLTF |
| `.fbx` | Autodesk FBX |
| `.blend` | Blender |
| `.obj` | Wavefront OBJ |

### Structure Recommandée

```
props_library/
├── gun_pistol.glb
├── gun_rifle.glb
├── phone_smartphone.glb
├── bag_backpack.glb
├── hat_cap.glb
├── generic_prop.glb      # Placeholder pour props manquants
└── custom/
    ├── custom_weapon.fbx
    └── custom_item.blend
```

### Conventions de Nommage

- Utilisez des noms sans espaces: `gun_pistol` ✓, `gun pistol` ✗
- Préfixez par catégorie: `weapon_`, `phone_`, `bag_`, etc.
- Le fichier `generic_prop.glb` est utilisé comme placeholder

---

## 🐛 Debug

### Logs détaillés
```bash
python EXO_02_LOGISTICS.py [...] -v
```

### Test Socketing seul
```python
# Dans Blender
import bpy
import sys
sys.path.insert(0, "/path/to/CODEBASE")

from socketing_engine import SocketingEngine

engine = SocketingEngine(verbose=True)
armature = engine.find_armature()
print(engine.list_available_sockets())
```

### Inspecter le rapport
```python
import json
with open("logistics_report.json") as f:
    report = json.load(f)
    
print(f"Status: {report['status']}")
print(f"Attachments: {len(report['attachments'])}")

for att in report['attachments']:
    print(f"  {att['prop_id']} -> {att['socket']} @ frame {att['frame']}")
```

---

## 📊 Performance Tips

### Optimiser les Props

1. Utilisez GLB plutôt que FBX (import plus rapide)
2. Réduisez le polycount des props (< 5000 triangles)
3. Évitez les textures 4K sur les props

### Batch Processing

Utiliser `EXO_02_PRODUCTION.ipynb` pour traiter plusieurs acteurs en séquence.

### Réduire le temps

1. Limiter le nombre de props simultanés
2. Utiliser `--dry-run` pour valider avant exécution
3. Pré-charger les props fréquemment utilisés

---

## 🐛 Known Issues

### Issue: "Bone not found for socket"
**Solution**: Vérifiez le nom des bones dans votre armature. Utilisez `engine.list_armature_bones()` pour voir les noms disponibles.

### Issue: "Prop flips on attachment"
**Solution**: Ajustez le `custom_rotation` dans l'action GRAB ou modifiez l'orientation du prop source.

### Issue: "Constraint influence not keyframing"
**Solution**: Assurez-vous que l'objet est sélectionné et que l'animation est bakée.

### Issue: "Alembic export crashes"
**Solution**: Vérifiez la RAM disponible. Réduisez le nombre d'objets ou la plage de frames.

---

## 📁 Output Format

### Dual Export
Le pipeline génère deux outputs:

```
OUT_EQUIPPED/
├── actor_equipped.abc       # Alembic avec props
├── actor_equipped.blend     # Backup éditable
└── logistics_report.json    # Rapport détaillé
```

### Alembic (.abc)
- Contient mesh + animation + props attachés
- Transformations évaluées (contraintes résolues)
- Compatible: Blender, Unity, Maya, Houdini

### Blend (.blend)
- Fichier éditable avec contraintes actives
- Textures packées
- Peut être modifié manuellement

### Rapport JSON
```json
{
  "version": "1.0.0",
  "timestamp": "2026-02-03T12:00:00",
  "status": "SUCCESS",
  "attachments": [
    {
      "prop_id": "gun_pistol",
      "socket": "hand_right",
      "frame": 100,
      "action": "GRAB",
      "resolved": true
    }
  ]
}
```

---

## 🔗 Resources

- [Blender Python API](https://docs.blender.org/api/current/)
- [Alembic Format](https://www.alembic.io/)
- [GLTF Specification](https://www.khronos.org/gltf/)

---

## 📝 Changelog

### v1.0.0
- Initial release
- Socket-based attachment system
- Timeline management (visibility, constraints)
- Alembic + Blend export
- Props library with placeholder support
- Batch processing notebook

---

*EXODUS SYSTEM — Frégate 02_LOGISTICS v1.0.0*
