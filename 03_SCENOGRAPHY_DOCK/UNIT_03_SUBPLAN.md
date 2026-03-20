# SOUS-PLAN TECHNIQUE — UNITE 03: SCENOGRAPHY DOCK V2

```
╔══════════════════════════════════════════════════════════════════════════════╗
║        FREGATE 03_SCENOGRAPHY — PLAN TECHNIQUE V2 — TRI-LAYER SYSTEM        ║
║                     Chantier Decors de la Flotte EXODUS                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission V2

Construire les decors 3D Tri-Layer depuis depth maps DepthAnything V2 et masques SAM. Plus de templates hardcodes — l'architecture V2 est data-driven. Chaque scene est pilotee par le PRODUCTION_PLAN.JSON du Cortex U00, avec une geometrie extraite des profondeurs video source.

Produire des fichiers `.blend` Tri-Layer avec 5 collections Blender, prets pour le compositing avec les acteurs equipes (de U02).

## WORKFLOW AUTOMATISE (NOUVEAU)

### Lancement en 1 commande
python /content/drive/MyDrive/EXODUS_V2/U03_RUN.py

### Duree
- Session 1: ~15-20 min
- Sessions suivantes: ~10-15 min

### Outputs
- environment_1.blend
- environment_2.blend
- assembler_results.json
- scenography_report.json

---

## Stack Technique V2

| Composant | Version | Usage |
|-----------|---------|-------|
| Blender | 4.0.x | Moteur 3D principal (headless) |
| Python | 3.10+ | Scripts d'orchestration |
| Cycles | - | Moteur de rendu principal |
| Pillow | - | Manipulation depth maps (anti-ghosting) |
| numpy | - | Traitement arrays (depth_map_cleaner) |
| scene_schema.py | 2.0.0 | Contrat inter-fregates |

---

## Architecture V2

```
03_SCENOGRAPHY_DOCK/
├── CODEBASE/
│   ├── EXO_03_SCENOGRAPHY.py        # Orchestrateur CLI V2 (~17KB)
│   ├── layer_assembler.py            # Assembleur Blender headless (~13KB)
│   ├── scene_schema.py               # Contrat inter-fregates (~32KB)
│   ├── dome_builder.py               # Couche A — Infinity Dome (~6KB)
│   ├── shadow_catcher_builder.py     # Shadow Catcher separe (~5KB)
│   ├── world_sync.py                 # World Sync HDRi (~7KB)
│   ├── displacement_builder.py       # Couche B — Displacement Mesh (~6KB)
│   ├── depth_map_cleaner.py          # Anti-ghosting (~9KB)
│   ├── pbr_swap_builder.py           # Couche C — PBR Swap (~6KB)
│   ├── glass_builder.py              # Reflectivity Hack (~5KB)
│   ├── requirements.txt              # Dependances Python
│   ├── EXO_03_CONTROL.ipynb          # Notebook debug V2
│   └── EXO_03_PRODUCTION.ipynb       # Notebook batch V2
├── IN_MAP_RAW/
│   ├── *.png                         # Depth maps DepthAnything V2 (de U00)
│   ├── semantic_masks.json           # Segmentation SAM (de U00)
│   └── *.hdr / *.exr                 # HDRi auto-detecte
├── IN_CORTEX_JSON/
│   └── PRODUCTION_PLAN.JSON          # Input: Instructions (de U00)
├── OUT_ENVIRONMENTS/
│   ├── environment_{scene_id}.blend  # Output: Scene Blender Tri-Layer
│   ├── scenography_report.json       # Output: Rapport V2
│   └── assembler_results.json        # Output: Resultats par scene
├── README_DEV.md                     # Documentation developpeur V2
└── UNIT_03_SUBPLAN.md                # Ce fichier
```

---

## Inputs V2

### 1. PRODUCTION_PLAN.JSON (de U00 Cortex)

```json
{
  "metadata": {
    "source_video": "video.mp4",
    "cortex_version": "2.0",
    "analysis_date": "2026-02-27"
  },
  "scenes": [
    {
      "scene_id": 1,
      "description": "Description scene",
      "environment": {
        "lighting_mood": "neon",
        "description": "Rue de ville avec neons",
        "video_frame_path": "/path/to/frame.png",
        "hdri_path": "/path/to/hdri.hdr"
      }
    }
  ]
}
```

### 2. Depth Maps (IN_MAP_RAW/*.png)

- Generes par DepthAnything V2 (via Cortex U00)
- Format PNG (8-bit grayscale ou 16-bit)
- Utilises par Couche B (Displacement Mesh)
- Nettoyes via anti-ghosting avant consommation

### 3. semantic_masks.json (IN_MAP_RAW)

- Segmentation SAM (via Cortex U00)
- Utilise par : anti-ghosting (depth_map_cleaner), Couche C (PBR Swap), Glass Builder
- Format : `{"image_width": int, "image_height": int, "masks": [{"label": str, "polygon": [[x,y],...]}]}`
- Optionnel — graceful fallback si absent

### 4. HDRi (auto-detecte dans IN_MAP_RAW)

- Formats : `.hdr`, `.exr`, `.hdri`
- Premier fichier trouve est utilise par World Sync
- Optionnel — fallback couleur selon mood

---

## Outputs V2

### 1. environment_{scene_id}.blend

Scene Blender Tri-Layer avec 5 collections obligatoires :

| Collection | Contenu | Statut |
|------------|---------|--------|
| `ENV_DOME` | infinity_dome (demi-sphere UV, normals inversees) | Requis |
| `ENV_TERRAIN` | displacement_mesh (plan subdivise + Displace modifier) | Requis |
| `ENV_SHADOW` | shadow_catcher (plan invisible, is_shadow_catcher=True) | Requis |
| `ENV_GLASS` | glass_plane_* (plans Glass BSDF, z-offset 0.01m) | Optionnel |
| `ENV_PBR` | pbr_surface_* (surfaces PBR Principled BSDF) | Optionnel |

Custom properties : `exodus_schema_version`, `exodus_frigate`, `exodus_validated`, `exodus_layers`.

### 2. scenography_report.json

```json
{
  "version": "2.0.0",
  "status": "SUCCESS",
  "vram_profile": "colab_t4",
  "summary": {
    "total_scenes": 3,
    "scenes_built": 3
  },
  "scenes": [...],
  "schema_validations": [
    {
      "scene_id": 1,
      "collections_present": ["ENV_DOME", "ENV_TERRAIN", "ENV_SHADOW", "ENV_GLASS", "ENV_PBR"],
      "objects_present": ["infinity_dome", "displacement_mesh", "shadow_catcher"],
      "world_use_nodes": true,
      "world_strength": 1.0
    }
  ]
}
```

### 3. assembler_results.json

Resultats detailles par scene produits par layer_assembler.py.

---

## Pipeline V2

### Phase 1 : Validation (CLI — EXO_03_SCENOGRAPHY.py)

```
EXO_03_SCENOGRAPHY.py
    ├── Parse arguments (--vram-profile, --exposure, --depth-map-dir, --semantic-masks)
    ├── Valider PRODUCTION_PLAN.JSON
    ├── Valider VRAM profile via scene_schema
    ├── Auto-detecter HDRi dans IN_MAP_RAW
    └── Verifier Blender disponible
```

### Phase 2 : Dome (Blender — Couche A)

```
dome_builder.py
    └── build_infinity_dome()
        ├── UV Sphere (segments=64, rings=32, radius=100m)
        ├── Supprimer moitie inferieure (z < 0)
        ├── Inverser normales (vue interieure)
        └── Materiau Emission + ImageTexture
```

### Phase 3 : Shadow Catcher

```
shadow_catcher_builder.py
    └── build_shadow_catcher()
        ├── Plan 50x50 au sol (0, 0, 0)
        ├── is_shadow_catcher = True
        ├── visible_camera = False, visible_diffuse = False
        └── Materiau Principled BSDF noir, Alpha=0
```

### Phase 4 : Displacement Mesh (Couche B)

```
displacement_builder.py
    └── build_displacement_mesh()
        ├── depth_map_cleaner.clean_depth_map_batch()  (anti-ghosting SAM)
        ├── Plan subdivise (Subsurf levels selon VRAM profile)
        ├── Displace modifier + texture depth map
        └── VRAM cap : max_subdivisions parametrable
```

### Phase 5 : PBR Swap (Couche C)

```
pbr_swap_builder.py
    └── build_pbr_surfaces()
        ├── Lire semantic_masks.json
        ├── SAM labels → SAM_LABEL_TO_PBR → PBR_MATERIAL_PRESETS
        ├── Exclure sky et glass
        └── Creer plans Principled BSDF par zone foreground
```

### Phase 6 : Glass (Reflectivity Hack)

```
glass_builder.py
    └── build_glass_planes()
        ├── Filtrer label="glass" dans semantic_masks.json
        ├── z_offset = 0.01m (anti z-fighting)
        └── Glass BSDF : transmission=0.9, roughness < 0.1
```

---

## Tri-Layer System

### Couche A : Infinity Dome

Demi-sphere UV rayon 100m avec normales inversees. Texture video source appliquee en Emission shader. Sert de background cinematographique — l'avatar voit la scene video originale tout autour.

- Collection : `ENV_DOME`
- Objet : `infinity_dome`
- Geometrie : UV Sphere segments=64, rings=32, moitie inferieure supprimee
- Materiau : Emission + ImageTexture (placeholder gris fonce si pas de frame video)
- Contrainte : radius dans [50.0, 200.0]

### Couche B : Displacement Mesh

Plan subdivise 128x128 (VRAM cap) avec Displace modifier pilote par depth maps DepthAnything V2. Les zones personnages sont aplatissees par anti-ghosting SAM avant displacement.

- Collection : `ENV_TERRAIN`
- Objet : `displacement_mesh`
- Geometrie : plan subdivise (Subsurf levels selon VRAM profile)
- Modifier : DISPLACE avec texture depth map PNG
- Anti-ghosting : depth_map_cleaner aplatit les zones person/character/human/animal

### Couche C : PBR Swap

Masques SAM traduits en surfaces PBR Principled BSDF. Seules les zones proches (foreground) recoivent des materiaux PBR. Les labels `sky` et `glass` sont exclus (geres par d'autres couches).

- Collection : `ENV_PBR`
- Objets : `pbr_surface_*`
- 10 labels SAM supportes : road, grass, wall, water, glass, sky, dirt, wood, metal, fabric
- Mapping : SAM_LABEL_TO_PBR → PBR_MATERIAL_PRESETS

### Reflectivity Hack (Glass BSDF)

Plans Glass BSDF places sur les surfaces vitrees detectees par SAM. Z-offset contractuel de 0.01m pour anti z-fighting.

- Collection : `ENV_GLASS`
- Objets : `glass_plane_*`
- Contraintes : z_offset=0.01, transmission>=0.9, roughness<=0.1

---

## VRAM Management

| Profil | max_vram_gb | max_subdivisions | max_texture_size | Cas d'usage |
|--------|-------------|------------------|------------------|-------------|
| `colab_t4` | 6.0 GB | 128 (2^7) | 4096 | Google Colab T4 (defaut) |
| `colab_a100` | 20.0 GB | 256 (2^8) | 8192 | Google Colab A100 |
| `local_low` | 4.0 GB | 64 (2^6) | 2048 | GPU locale budget |

Le profil VRAM determine le nombre de subdivisions du displacement mesh et la resolution maximale des textures. Le depassement VRAM est le principal risque sur Colab T4.

---

## Anti-Ghosting

Algorithme (depth_map_cleaner.py) :

1. Lire semantic_masks.json
2. Pour chaque masque avec label dans `[person, character, human, animal]` :
   a. Rasteriser le polygone SAM en masque binaire
   b. Calculer la mediane des pixels bordure (dilatation 3px)
   c. Appliquer BoxBlur (feather_radius=4) pour adoucir les bords
   d. Blender : `depth = depth * (1 - feathered) + fill_value * feathered`
3. Sauvegarder depth map nettoyee
4. Le displacement_builder consomme la version nettoyee

---

## 10 Lois Applicables

1. **Loi d'Etancheite** — Chaque module lit ses inputs, produit ses outputs. Aucune dependance entre fregates.
2. **Loi du Beton** — Chaque entree dans le Registre de Forge pointe vers un commit ou un fichier.
3. **Loi d'Agnosticisme** — Le systeme fonctionne sur Colab T4, A100, ou local. Aucun hardcode d'environnement.

---

## Taches Implementees V2

### Phase D0 — Contrat de Scene (scene_schema.py)
- [x] scene_schema.py — Collections obligatoires (ENV_DOME, ENV_TERRAIN, ENV_SHADOW, ENV_GLASS, ENV_PBR)
- [x] Nomenclature objets (infinity_dome, displacement_mesh, shadow_catcher, glass_plane_*, pbr_surface_*)
- [x] World settings contractuels (use_nodes=True, 3 node types, strength [0.1, 3.0])
- [x] validate_scene() avec 7 sous-validations
- [x] Custom properties .blend (exodus_schema_version, exodus_frigate, exodus_validated, exodus_layers)
- [x] VRAM_PROFILES (colab_t4, colab_a100, local_low)
- [x] SAM_LABEL_TO_PBR (10 labels)
- [x] PBR_MATERIAL_PRESETS (10 presets + default)

### Phase D1 — Infinity Dome + Shadow Catcher + World Sync
- [x] Couche A : Infinity Dome (demi-sphere UV rayon 100m + texture video source)
- [x] Shadow Catcher : plan SEPARE invisible (is_shadow_catcher=True)
- [x] World Sync : HDRi aligne sur exposition video (strength clampee [0.1, 3.0])
- [x] layer_assembler.py : assemble_scene() coordonne les 3 couches + 5 collections
- [x] Suppression environment_builder.py (V1)
- [x] Suppression props_placer.py (V1)
- [x] Suppression hdri_manager.py (V1)

### Phase D2 — Displacement Mesh + Anti-Ghosting
- [x] Couche B : Plan subdivise + Displace modifier + depth maps DepthAnything V2
- [x] Anti-ghosting : depth_map_cleaner.py (SAM mask → border median → feathered blend)
- [x] VRAM cap : max_subdivisions parametrable selon profil

### Phase D3 — PBR Swap + Reflectivity Hack
- [x] Couche C : masques SAM → presets PBR (zones PROCHES uniquement)
- [x] 10 labels SAM supportes : road, grass, wall, water, glass, sky, dirt, wood, metal, fabric
- [x] Reflectivity Hack : plans Glass BSDF (z-offset 0.01m anti z-fighting)
- [x] Suppression pbr_applicator.py (V1)

### Phase D4 — Documentation
- [x] Rewrite EXO_03_CONTROL.ipynb (V2)
- [x] Rewrite EXO_03_PRODUCTION.ipynb (V2)
- [x] Rewrite README_DEV.md (V2)
- [x] Rewrite UNIT_03_SUBPLAN.md (V2)
- [x] Mise a jour TRACKING_U03.md

---

## Contraintes Respectees

1. **Blender 4.0 Portable** — Utilise le Blender sur Drive
2. **LOI D'ISOLATION** — Ne depend d'aucune autre unite
3. **Argument --drive-root** — Obligatoire sur le wrapper CLI
4. **VRAM Cap** — Subdivisions et textures plafonnees par profil
5. **Graceful Fallback** — Fonctionne sans depth maps, sans semantic_masks, sans HDRi
6. **Zero module V1** — Tous les modules obsoletes supprimes

---

## Statut: FORGE

**Date debut forge**: 2026-02-27
**Date fin forge**: 2026-02-27
**Maitre de Forge**: Vulkan

---

*EXODUS SYSTEM — Fregate 03_SCENOGRAPHY v2.0.0 — Tri-Layer System*
