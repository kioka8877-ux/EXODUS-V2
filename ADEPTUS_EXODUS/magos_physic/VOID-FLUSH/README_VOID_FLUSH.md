# VOID-FLUSH — Tech-Pretre de Purge GPU

> "Ce qui est vide peut être rempli. Ce qui est plein peut exploser."
> Constitution : Les Mini Programs servent. L'Empereur valide.

---

## Pourquoi

Les rendus Blender lourds (U03, U04) accumulent des residus en memoire :
- Meshes evalues mais non liberes
- Images GPU chargees et oubliees
- Depsgraph stale (cause du BUG D6 — 4 vertices)

VOID-FLUSH purge tout ca avant et apres chaque render.

---

## Installation

Aucune dependance externe. Python standard + Blender (optionnel).

```bash
# Mode standalone (test sans Blender)
python void_flush.py --status
python void_flush.py --full

# Mode fregate
python void_flush.py --fregate U03
```

---

## Integration dans une Fregate

```python
# Dans le script de rendu de la fregate (ex: render_forge.py)
import sys
sys.path.append('/path/to/EXODUS-V2')
from ADEPTUS_EXODUS.magos_physic.VOID_FLUSH.blender_adapter import (
    flush_before_render,
    flush_after_render
)

# Avant render
flush_before_render(scene=bpy.context.scene, fregate_id="U04")

# ... render ...

# Apres render
flush_after_render(fregate_id="U04")
```

---

## Rapport de Sortie

```json
{
  "status": "OK",
  "fregate": "U03",
  "timestamp": "2026-04-03T12:00:00",
  "actions": [
    "depsgraph.update()",
    "orphans_purge(recursive)",
    "images_purge(3)",
    "meshes_purge(1)"
  ],
  "engine": "blender"
}
```

---

## Feature Flags

Editer `feature_flags.json` pour activer/desactiver chaque etape :

| Flag | Defaut | Role |
|------|--------|------|
| `gpu_flush` | true | Purge GPU Blender |
| `mesh_purge` | true | Supprime meshes orphelins |
| `orphan_purge` | true | Purge orphelins Blender |
| `force_depsgraph_update` | true | Fix D6_depsgraph integre |
| `verbose` | true | Logs detailles |

---

## Fregates Cibles

- U03 — SCENOGRAPHY_DOCK (scenes lourdes, >16K vertices)
- U04 — PHOTOGRAPHY_WING (rendus cameras multiples)
