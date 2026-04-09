# EMPIRE_STATE — Etat de la Flotte EXODUS

> Mis a jour apres chaque session. Source de verite pour Vulkan.

---

## Fregate Statuts

| ID | Nom | Statut | Derniere Action | Bloquant |
|----|-----|--------|----------------|----------|
| U00 | CORTEX_HQ | VALIDE | PRODUCTION_PLAN.JSON + depth_maps | — |
| U01 | ANIMATION_ENGINE | FIX INJECTE | FIX #1b — import multi-format + auto-detect + hard-fail | Validation blend |
| U02 | LOGISTICS_DEPOT | EN ATTENTE | Structure creee | Premier run |
| U03 | SCENOGRAPHY_DOCK | FIX INJECTE | FIX #2 — Fallback procedural depth/SAM | Validation blends |
| U04 | PHOTOGRAPHY_WING | FIX INJECTE | FIX #3 — camera_fov_ratio.json + 9:16 | Validation renders |
| U05 | ALCHEMIST_LAB | EN ATTENTE | Structure creee | Premier run |
| U06 | AIRCRAFT_CARRIER | EN ATTENTE | Structure creee | Premier run |

---

## Fixes Appliques

| Commit | Fregate | Fix | Statut |
|--------|---------|-----|--------|
| 0cb3057d | U04 | camera_main ajoutee automatiquement | VALIDE |
| 6db5311f | U03 | depsgraph.update() avant evaluation | VALIDE |
| 80a6d336 | U03 | lit assembler_results.json | VALIDE |
| b753fa30 | U03 | FIX #2 — Fallback procedural depth/SAM + logging [U03] | INJECTE |
| 3bff4a96 | U04 | FIX #3 (1/2) — darkroom_render.py aspect_ratio + lens_mm + [U04] | INJECTE |
| 58f3475b | U04 | FIX #3 (2/2) — EXO_04_DARKROOM.py generate_report + auto-detect FOV | INJECTE |
| 60a6c7a3 | U01 | FIX #1b (1/2) — blender_fusion.py import multi-format + hard-fail + remove placeholder | INJECTE |
| d77942fd | U01 | FIX #1b (2/2) — EXO_01_TRANSMUTATION.py auto-detect modele + --actor-model | INJECTE |

---

## Derniere Session

- Date : 2026-04-09
- Actions : FIX #2 U03 + FIX #3 U04 (2 commits) — TRIPLE FIX EN COURS
- Prochaine : Validation run U01 — deposer modele dans IN_CORTEX_JSON/actor_models/

---

## Ordre Execution Fixes


