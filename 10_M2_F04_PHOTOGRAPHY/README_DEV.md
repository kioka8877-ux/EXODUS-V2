# MODE 2 — FRÉGATE M2_F04 PHOTOGRAPHY WING

> Phase 8 — Dual Pipeline Doctrine | Version 1.0.0 | 03.05.2026
> Loi R-01 : Copie étanche Mode 2 — zéro contamination Mode 1

---

## Rôle

Configurer la caméra et l'éclairage sur la scène Mode 2.
Reçoit `scene_ready.blend` de M2_F03 (décor GLB + shadow catcher + HDRi).
Produit `scene_with_camera.blend` prêt pour M2_F05 ALCHEMIST.

---

## Structure

```
10_M2_F04_PHOTOGRAPHY/
├── CODEBASE/
│   ├── EXO_M2_F04_PHOTOGRAPHY.py     — Orchestrateur Mode 2
│   ├── EXO_M2_F04_CONTROL.ipynb      — Notebook de contrôle
│   ├── EXO_M2_F04_PRODUCTION.ipynb   — Notebook de production
│   ├── camera_director.py            — Caméra + keyframes (copie M1_F04)
│   ├── camera_schema.py              — Bible optique
│   ├── lighting_rig.py               — Éclairage 3-Point + HDRi
│   ├── render_forge.py               — Config Cycles
│   ├── auto_dof.py                   — Profondeur de champ automatique
│   ├── keyframe_animator.py          — Keyframes caméra
│   └── requirements.txt
├── IN_SCENE_BLEND/                   — Input : scene_ready.blend (de M2_F03)
├── IN_PRODUCTION_PLAN/               — Input optionnel : PRODUCTION_PLAN.JSON
├── OUT_CAMERA_READY/                 — Output : scene_with_camera.blend
└── OUT_REPORT/                       — m2_f04_report.json
```

---

## Lancement

```bash
# Lancement simple (auto-détection du .blend dans IN_SCENE_BLEND/)
python CODEBASE/EXO_M2_F04_PHOTOGRAPHY.py

# Avec fichier .blend explicite
python CODEBASE/EXO_M2_F04_PHOTOGRAPHY.py --scene /path/to/scene_ready.blend

# Preset preview (rendu rapide)
python CODEBASE/EXO_M2_F04_PHOTOGRAPHY.py --preset preview --no-dof

# Dry-run (validation chemins sans Blender)
python CODEBASE/EXO_M2_F04_PHOTOGRAPHY.py --dry-run --verbose
```

---

## Pipeline Mode 2

```
LAUNCHER → M2_F01 → M2_F02 → M2_F03 → [M2_F04] → M2_F05 → M2_F06 → FINAL.mp4
```

**Input de** : M2_F03 SCENOGRAPHY (`scene_ready.blend`)
**Output vers** : M2_F05 ALCHEMIST (`scene_with_camera.blend`)

---

## Lois Inviolables

| Loi | Règle |
|-----|-------|
| R-01 | Copie étanche — ne jamais importer depuis Mode 1 |
| R-06 | Ce module ne contient aucune logique de routing |

---

<!-- v1.0.0 — M2_F04 FORGÉ — 03.05.2026 -->
