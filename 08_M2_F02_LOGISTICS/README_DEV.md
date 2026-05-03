# M2_F02 — LOGISTICS ARMURERIE (Mode 2)

> Mode 2 — Phase 8 — Dual Pipeline Doctrine — v1.0.0

## Rôle

Deuxième frégate du pipeline Mode 2 (From Scratch).
Attache les props à l'avatar GLB Roblox reçu de M2_F01.
Bypass automatique si aucun prop requis.

## Lois Impériales appliquées

| Loi | Règle |
|-----|-------|
| R-01 | Isolation stricte — copie indépendante, zéro lien Mode 1, zéro Phantom Link |
| R-03 | Durée audio <= durée animation (héritée de M2_F01) |

## Structure

```
08_M2_F02_LOGISTICS/
├── CODEBASE/
│   ├── EXO_M2_F02_LOGISTICS.py     ← Script principal CLI
│   ├── socketing_engine.py          ← Blender headless — import GLB + socketing
│   ├── actor_assembly.py            ← SocketingEngine + TimelineManager (copie M1)
│   ├── props_loader.py              ← Chargement props multi-format (copie M1)
│   ├── timeline_manager.py          ← Thin wrapper (copie M1)
│   ├── final_baker.py               ← Export Alembic + backup blend (copie M1)
│   ├── EXO_M2_F02_CONTROL.ipynb    ← Diagnostics pré-vol
│   ├── EXO_M2_F02_PRODUCTION.ipynb ← Notebook de production
│   └── requirements.txt
├── IN_GLB_AVATAR/    ← Déposer avatar_validated.glb (de M2_F01)
├── IN_PROPS_LIBRARY/ ← Déposer les props (*.glb, *.fbx, *.blend) — optionnel
├── IN_PRODUCTION_PLAN/ ← Déposer PRODUCTION_PLAN.JSON — optionnel
├── OUT_BAKED_ACTORS/ ← actor_equipped.abc + .blend (ou .glb si bypass)
└── OUT_REPORT/       ← m2_f02_report.json
```

## Utilisation

```bash
# Auto-détection (bypass si pas de props/plan)
python CODEBASE/EXO_M2_F02_LOGISTICS.py

# GLB explicite
python CODEBASE/EXO_M2_F02_LOGISTICS.py --glb avatar_validated.glb

# Bypass forcé (pas de props à attacher)
python CODEBASE/EXO_M2_F02_LOGISTICS.py --bypass

# Dry-run (validation sans exécution)
python CODEBASE/EXO_M2_F02_LOGISTICS.py --dry-run --verbose

# Blender custom
python CODEBASE/EXO_M2_F02_LOGISTICS.py --blender-path /path/to/blender
```

## Bypass automatique

M2_F02 se bypass automatiquement si :
1. `requires_u02 == false` dans `PRODUCTION_PLAN.JSON`
2. Zéro `props_actions` dans toutes les scènes du plan
3. Aucun `PRODUCTION_PLAN.JSON` dans `IN_PRODUCTION_PLAN/`
4. Flag `--bypass` explicite

En mode bypass : le GLB est copié tel quel vers `OUT_BAKED_ACTORS/`.

## Flux Mode 2

```
M2_F01/OUT_VALIDATED/avatar_validated.glb
        ↓  (transfer manuel Opérateur)
IN_GLB_AVATAR/avatar_validated.glb
IN_PROPS_LIBRARY/*.glb   (props optionnels)
IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON  (optionnel)
        ↓  EXO_M2_F02_LOGISTICS.py
        ↓  → Blender headless: import GLB → socketing props → export ABC
OUT_BAKED_ACTORS/actor_equipped.abc + .blend
OUT_REPORT/m2_f02_report.json
        ↓  (transfer manuel Opérateur)
M2_F03/IN_GLB_AVATAR/
```

## Différences Mode 1 vs Mode 2

| Aspect | Mode 1 (U02) | Mode 2 (M2_F02) |
|--------|-------------|-----------------|
| Input avatar | `.blend` de U01 | `.glb` de M2_F01 |
| Phantom Link | Oui | Non (R-01) |
| --drive-root | Requis | Auto (relatif) |
| Isolation | Partagée | Étanche totale |

## Dépendances

- `bpy` : fourni par Blender 4.0 (headless)
- `numpy` : optionnel (scripts helper)
