# ATLAS — Tech-Pretre des Chemins

> "Celui qui connait tous les chemins ne se perd jamais."
> Constitution : Les Mini Programs servent. L'Empereur valide.

---

## Pourquoi

Chaque fregate hardcodait ses propres chemins — fragile, non maintenable.
ATLAS est la carte de l'Empire : un seul endroit pour tous les chemins.

---

## Installation

Aucune dependance externe. Python standard.

```bash
# Voir l'etat du pipeline
python atlas.py --state

# Chemins d'une fregate
python atlas.py --paths U03

# Health check d'une fregate
python atlas.py --health U04

# Resoudre un chemin specifique
python atlas.py --resolve U03 OUT_PREMIUM_SCENE
```

---

## Integration dans une Fregate

```python
import sys
sys.path.append('/path/to/EXODUS-V2')
from ADEPTUS_EXODUS.magos_logis.ATLAS.atlas import resolve_path, get_fregate_paths
from ADEPTUS_EXODUS.magos_logis.ATLAS.session_store import SessionStore

# Obtenir le chemin de sortie
out_path = resolve_path("U03", "OUT_PREMIUM_SCENE")

# Persister l'etat de la session
store = SessionStore("U03")
store.update({
    "vertex_count": 16641,
    "scene_type": "cinematic",
    "camera": "camera_main",
})
store.save()

# Session suivante — relire l'etat
store = SessionStore("U03")
vertex_count = store.get("vertex_count")  # 16641
```

---

## Carte des Fregates

| ID | Nom | Inputs | Outputs |
|----|-----|--------|---------|
| U00 | CORTEX_HQ | IN_VIDEO_SOURCE | — |
| U01 | ANIMATION_ENGINE | IN_CORTEX_JSON, IN_MIXAMO_BASE | OUT_MOTION_DATA |
| U02 | LOGISTICS_DEPOT | IN_MOTION_DATA, IN_PROPS_LIBRARY, IN_ROBLOX_AVATAR | OUT_BAKED_ACTORS |
| U03 | SCENOGRAPHY_DOCK | IN_CORTEX_JSON, IN_MAP_RAW | OUT_PREMIUM_SCENE |
| U04 | PHOTOGRAPHY_WING | IN_SCENE_REF, IN_VIDEO_SOURCE | — |
| U05 | ALCHEMIST_LAB | IN_RAW_FRAMES, IN_SOURCE_REF | OUT_FINAL_FRAMES |
| U06 | AIRCRAFT_CARRIER | IN_ASSEMBLY_KIT | OUT_FINAL_MOVIE |

---

## pipeline_state.json

Fichier de reference pour KRONOS et VOX.
Mis a jour manuellement ou via les hooks de hook_dispatcher.

```json
{
  "fregates": { "U03": { "status": "VALIDE", ... } },
  "tech_pretres": { "ATLAS": { "status": "OPERATIONNEL", ... } },
  "pipeline_health": { "fregates_validees": 2, ... }
}
```
