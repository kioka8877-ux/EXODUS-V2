# ROADMAP U03 — SCENOGRAPHY DOCK (Fonctionnalités Futures)

> Décret I — Codex Imperial v6 — 23.04.2026
> Ce fichier recense les fonctionnalités Tri-Layer D2/D3 retirées du code de
> production actif. Elles ne sont pas supprimées — elles sont tracées ici pour
> implémentation future lorsque les prérequis seront disponibles.

---

## Couche D1 — ACTIVE (production)

| Composant | Fichier | Statut |
|-----------|---------|--------|
| Infinity Dome | `dome_builder.py` | ACTIF |
| Shadow Catcher | `shadow_catcher_builder.py` | ACTIF |
| World Sync (HDRi) | `world_sync.py` | ACTIF |
| Terrain Procédural | `layer_assembler._build_procedural_interior` | ACTIF |
| Caméra default | `layer_assembler.assemble_scene` | ACTIF |

---

## Couche D2 — FUTURE (depth maps)

**Prérequis** : DepthAnything V2 intégré dans F00 (CORTEX) et depth maps disponibles dans `IN_MAP_RAW/DEPTH_MAP/`.

| Fonctionnalité | Fichier de référence | Description |
|----------------|----------------------|-------------|
| Displacement Mesh | `displacement_builder.py` | Plan 128x128 subdivisé + Displace modifier piloté par depth maps PNG |
| Anti-ghosting | `depth_map_cleaner.py` | Nettoyage depth maps via masques SAM avant displacement |
| Profils VRAM | `scene_schema.VRAM_PROFILES` | colab_t4 (128), colab_a100 (256), local_low (64) |

**Pour activer D2** :
1. F00 doit produire `DEPTH_MAP/*.png` dans `IN_MAP_RAW/`
2. Réintroduire `from displacement_builder import build_displacement_mesh` dans `layer_assembler.py`
3. Ajouter le param `depth_map_dir` à `assemble_scene()`
4. Remplacer `_build_procedural_interior()` par `build_displacement_mesh()`

---

## Couche D3 — FUTURE (SAM semantic masks)

**Prérequis** : SAM (Segment Anything) intégré dans F00 et `semantic_masks.json` disponible.

| Fonctionnalité | Fichier de référence | Description |
|----------------|----------------------|-------------|
| PBR Swap | `pbr_swap_builder.py` | Surfaces PBR sur zones foreground SAM (road, grass, wall, water) |
| Glass Planes | `glass_builder.py` | Plans Glass BSDF sur zones vitrées SAM, Z-offset 0.01m |
| Reflectivity Hack | `scene_schema.PBR_MATERIAL_PRESETS` | Presets matériaux SAM-mappés |

**Pour activer D3** :
1. F00 doit produire `semantic_masks.json` dans `IN_MAP_RAW/`
2. Réintroduire imports `pbr_swap_builder`, `glass_builder` dans `layer_assembler.py`
3. Ajouter le param `semantic_masks_path` à `assemble_scene()`
4. Appeler `build_pbr_surfaces()` et `build_glass_planes()` après D2

---

## Notes d'architecture

- Les fichiers `displacement_builder.py`, `pbr_swap_builder.py`, `glass_builder.py`, `depth_map_cleaner.py` restent dans le CODEBASE comme implémentation de référence.
- Aucune modification de `scene_schema.py` n'est nécessaire — les specs D2/D3 y sont déjà définies.
- La doctrine TRI-LAYER est inchangée. Seule la phase de production est allégée en attendant les prérequis.

---

<!-- v1.0 — Décret I Codex v6 — 23.04.2026 -->
