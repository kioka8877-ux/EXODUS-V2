# M2_F03 — SCENOGRAPHY DOCK

> Mode 2 — Phase 8 — Dual Pipeline Doctrine — v1.0.0

## Rôle

Troisième frégate du pipeline Mode 2. Assemble la scène 3D complète à partir du GLB décor
fourni par l'Opérateur et du GLB avatar validé par M2_F01.

**4 opérations uniquement (Doctrine Codex Brainstorm v1) :**
1. Importer le GLB décor complet (mesh + textures + lumières)
2. Importer le GLB avatar animé
3. Ajouter shadow catcher sur sol Y=0
4. Configurer HDRi éclairage ambiance → exporter .blend

## Lois Impériales appliquées

| Loi | Règle |
|-----|-------|
| R-01 | Isolation stricte — copie indépendante, zéro lien Mode 1 |
| R-05 | GLB décor fourni par Opérateur — M2_F03 gère l'import, ombres, HDRi |

## Structure

```
09_M2_F03_SCENOGRAPHY/
├── CODEBASE/
│   ├── EXO_M2_F03_SCENOGRAPHY.py     ← Orchestrateur + script Blender embarqué
│   ├── EXO_M2_F03_CONTROL.ipynb      ← Diagnostics pré-vol
│   ├── EXO_M2_F03_PRODUCTION.ipynb   ← Notebook de production
│   └── requirements.txt
├── IN_GLB_DECOR/    ← Déposer decor.glb ici (fourni par Opérateur — LOI R-05)
├── IN_GLB_AVATAR/   ← avatar_validated.glb (de M2_F01 OUT_VALIDATED/)
├── IN_AUDIO/        ← audio_validated.* (de M2_F01, transfert manuel)
├── OUT_SCENE/       ← scene_m2.blend + audio transféré
└── OUT_REPORT/      ← m2_f03_report.json + m2_f03_blender_internal.json
```

## Utilisation

```bash
# Mode automatique (auto-détection GLB dans IN_*)
python CODEBASE/EXO_M2_F03_SCENOGRAPHY.py

# Fichiers explicites
python CODEBASE/EXO_M2_F03_SCENOGRAPHY.py --decor decor.glb --avatar avatar.glb

# Avec HDRi explicite
python CODEBASE/EXO_M2_F03_SCENOGRAPHY.py --hdri /path/to/sky.hdr

# Shadow catcher plus grand
python CODEBASE/EXO_M2_F03_SCENOGRAPHY.py --shadow-size 100

# Sans HDRi (ciel neutre)
python CODEBASE/EXO_M2_F03_SCENOGRAPHY.py --skip-hdri

# Dry-run (validation sans Blender)
python CODEBASE/EXO_M2_F03_SCENOGRAPHY.py --dry-run --verbose
```

## Flux Mode 2

```
M2_F01 OUT_VALIDATED/ → (Transfer Manuel) → IN_GLB_AVATAR/
Opérateur fournit decor.glb              → IN_GLB_DECOR/

M2_F03 assemble :
  OP-1 : GLB décor → collection DECOR
  OP-2 : GLB avatar → collection AVATARS
  OP-3 : Shadow catcher Y=0 → collection SHADOW_CATCHERS
  OP-4 : HDRi World (auto-détection ou --hdri explicite)

OUT_SCENE/scene_m2.blend → Transfer Manuel → M2_F04/IN_*/
```
