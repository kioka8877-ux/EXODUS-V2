# SOUS-PLAN TECHNIQUE — UNITÉ 03: SCENOGRAPHY DOCK

```
╔══════════════════════════════════════════════════════════════════════════════╗
║            FRÉGATE 03_SCENOGRAPHY — PLAN TECHNIQUE COMPLET                   ║
║                     Chantier Décors de la Flotte EXODUS                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

Construire les environnements 3D avec matériaux PBR et éclairage HDRi selon le PRODUCTION_PLAN.JSON (de U00 Cortex). Produire des fichiers .blend prêts pour le compositing avec les acteurs équipés (de U02).

---

## Stack Technique

| Composant | Version | Usage |
|-----------|---------|-------|
| Blender | 4.0.x | Moteur 3D principal |
| Python | 3.10+ | Scripts d'orchestration |
| Cycles/EEVEE | - | Moteur de rendu |
| PBR | - | Matériaux physiquement réalistes |
| HDRi | - | Éclairage basé image |

---

## Architecture

```
03_SCENOGRAPHY_DOCK/
├── CODEBASE/
│   ├── EXO_03_SCENOGRAPHY.py      # Wrapper principal CLI
│   ├── environment_builder.py      # Construction scène (Blender)
│   ├── pbr_applicator.py          # Application matériaux PBR
│   ├── hdri_manager.py            # Gestion éclairage HDRi
│   ├── props_placer.py            # Placement props environnement
│   ├── requirements.txt           # Dépendances Python
│   ├── EXO_03_CONTROL.ipynb       # Notebook debug
│   └── EXO_03_PRODUCTION.ipynb    # Notebook batch
├── IN_MAPS/
│   ├── PRODUCTION_PLAN.JSON       # Input: Instructions (de U00)
│   ├── hdri_library/              # Fichiers HDRi (.hdr, .exr)
│   │   ├── neon.hdr
│   │   ├── dramatic.hdr
│   │   ├── natural.hdr
│   │   └── studio.hdr
│   └── environment_assets/        # Assets décors
│       ├── urban_street.blend
│       ├── indoor.blend
│       └── props/
│           ├── streetlight.glb
│           ├── bench.glb
│           └── ...
├── OUT_ENVIRONMENTS/
│   ├── environment_1.blend        # Output: Scène Blender
│   ├── environment_2.blend
│   └── scenography_report.json    # Output: Rapport production
├── README_DEV.md                  # Documentation développeur
└── UNIT_03_SUBPLAN.md             # Ce fichier
```

---

## Inputs

### 1. PRODUCTION_PLAN.JSON (de U00 Cortex)

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "environment": {
        "type": "urban_street|indoor|outdoor|studio",
        "description": "Description de l'environnement",
        "lighting_mood": "neon|dramatic|natural|studio",
        "props": ["streetlight", "bench", "car"]
      }
    }
  ]
}
```

### 2. hdri_library/

Fichiers HDRi organisés par mood:
- `.hdr` / `.exr` format supportés
- Nommage: `{mood}.hdr` (ex: neon.hdr, dramatic.hdr)
- Résolution recommandée: 4K+

### 3. environment_assets/

Assets 3D pour les environnements:
- `.blend` — Natif Blender (recommandé)
- `.glb` / `.gltf` — Format web 3D
- `.fbx` — Format échange
- `.obj` — Format legacy

---

## Outputs

### 1. environment_{scene_id}.blend

Scène Blender complète contenant:
- Géométrie environnement (sol, murs, cyclorama)
- Matériaux PBR appliqués
- HDRi configuré dans World shader
- Props placés
- Prêt pour import acteur équipé

### 2. scenography_report.json

Rapport de production:
```json
{
  "version": "1.0.0",
  "status": "SUCCESS",
  "summary": {
    "total_scenes": 3,
    "scenes_built": 3,
    "hdri_resolved": 2,
    "assets_resolved": 5
  },
  "scenes": [...],
  "logs": [...]
}
```

---

## Pipeline Technique

### Phase 1: Validation (CLI)

```
EXO_03_SCENOGRAPHY.py
    └── Parse arguments
    └── Valider PRODUCTION_PLAN.JSON
    └── Scanner hdri_library/
    └── Scanner environment_assets/
    └── Vérifier Blender disponible
```

### Phase 2: Construction (Blender Headless)

```
environment_builder.py
    └── Pour chaque scène:
        └── Nettoyer scène Blender
        └── Créer collection
        └── Construire environnement selon type:
            └── create_ground()
            └── create_walls() [si indoor]
            └── create_ceiling() [si indoor]
            └── create_cyclorama() [si studio]
        └── Appliquer matériaux PBR
        └── Configurer HDRi / fallback
        └── Placer props
        └── Sauvegarder .blend
```

### Phase 3: PBR Materials

```
pbr_applicator.py
    └── create_basic_material(preset)
    └── create_textured_material(textures)
    └── auto_apply_materials(collection)
```

### Phase 4: HDRi Lighting

```
hdri_manager.py
    └── setup_hdri_lighting(path, mood)
    └── setup_fallback_lighting(style)
    └── create_scene_lights(style)
```

### Phase 5: Props Placement

```
props_placer.py
    └── place_props(list, mapping)
    └── import_prop_asset(path)
    └── create_placeholder()
    └── generate_random_positions()
```

---

## Types d'Environnement

| Type | Description | Éléments |
|------|-------------|----------|
| `urban_street` | Rue de ville | Sol asphalte, lampadaires, voitures |
| `indoor` | Intérieur | Sol bois, 4 murs, plafond |
| `outdoor` | Extérieur nature | Sol herbe, arbres, rochers |
| `studio` | Studio photo | Cyclorama blanc, 3-point lighting |

---

## Moods d'Éclairage

| Mood | HDRi | Fallback | Description |
|------|------|----------|-------------|
| `neon` | neon.hdr | Violet/bleu froid | Ambiance cyberpunk |
| `dramatic` | dramatic.hdr | Orange/doré | Coucher de soleil |
| `natural` | natural.hdr | Ciel bleu | Lumière du jour |
| `studio` | studio.hdr | Gris neutre | Éclairage contrôlé |

---

## Presets Matériaux PBR

| Preset | Base Color | Roughness | Metallic |
|--------|------------|-----------|----------|
| `asphalt` | Gris foncé | 0.8 | 0.0 |
| `concrete` | Gris moyen | 0.9 | 0.0 |
| `grass` | Vert | 0.95 | 0.0 |
| `wood_floor` | Marron | 0.6 | 0.0 |
| `plaster` | Blanc cassé | 0.85 | 0.0 |
| `studio_white` | Blanc | 0.8 | 0.0 |
| `metal_steel` | Gris clair | 0.3 | 0.9 |
| `glass` | Transparent | 0.05 | 0.0 |

---

## Gestion d'Erreurs

### HDRi Manquant

Si le fichier HDRi n'existe pas:
1. Log warning
2. Créer World avec couleur de fallback selon mood
3. Créer lumières de scène selon style

### Asset Manquant

Si un asset environnement ou prop n'existe pas:
1. Log warning
2. Créer placeholder (cube magenta semi-transparent)
3. Continuer la construction

### Type Environnement Inconnu

Si le type n'est pas reconnu:
1. Log warning
2. Fallback vers "studio" (cyclorama vide)

---

## Commandes CLI

### Dry-Run (validation uniquement)

```bash
python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/drive \
    --production-plan PRODUCTION_PLAN.JSON \
    --dry-run -v
```

### Production complète

```bash
python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/drive \
    --production-plan PRODUCTION_PLAN.JSON \
    --blender-path /path/to/blender \
    -v
```

### Scènes spécifiques

```bash
python EXO_03_SCENOGRAPHY.py \
    --drive-root /path/to/drive \
    --production-plan PRODUCTION_PLAN.JSON \
    --scene-ids 1,3,5 \
    -v
```

---

## Tâches Implémentées

- [x] Wrapper CLI avec --drive-root obligatoire
- [x] Validation PRODUCTION_PLAN.JSON
- [x] Scan hdri_library avec mapping mood
- [x] Scan environment_assets
- [x] Mode dry-run pour validation
- [x] Mode verbose pour debug
- [x] Construction environnement par type
- [x] Sol avec matériau PBR
- [x] Murs et plafond (intérieur)
- [x] Cyclorama (studio)
- [x] Application HDRi World shader
- [x] Fallback éclairage si HDRi manquant
- [x] Placement props avec positions prédéfinies
- [x] Import assets multi-format
- [x] Placeholder pour assets manquants
- [x] Export .blend avec textures packées
- [x] Rapport JSON détaillé
- [x] Notebook debug (EXO_03_CONTROL)
- [x] Notebook batch (EXO_03_PRODUCTION)

---

## Contraintes Respectées

1. ✅ **Blender 4.0 Portable** — Utilise le Blender sur Drive
2. ✅ **LOI D'ISOLATION** — Ne dépend d'aucune autre unité
3. ✅ **Argument --drive-root** — Obligatoire sur le wrapper
4. ✅ **Gestion d'erreurs** — Log warning, continue sur erreur
5. ✅ **Assets manquants** — Placeholder généré automatiquement
6. ✅ **HDRi manquants** — Fallback éclairage procédural

---

## Statut: 🟢 FORGÉ

**Date début forge**: 2026-02-03
**Date fin forge**: 2026-02-03
**Maître de Forge**: Vulkan

---

*EXODUS SYSTEM — Frégate 03_SCENOGRAPHY v1.0.0*
