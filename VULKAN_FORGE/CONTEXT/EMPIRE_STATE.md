# EMPIRE_STATE — Etat de la Flotte EXODUS

> Mis a jour apres chaque session. Source de verite pour Vulkan.

---

## Fregate Statuts

| ID | Nom | Statut | Derniere Action | Bloquant |
|----|-----|--------|----------------|----------|
| U00 | CORTEX_HQ | VALIDE | PRODUCTION_PLAN.JSON + depth_maps | — |
| U01 | ANIMATION_ENGINE | EN ATTENTE | Structure creee | Premier run |
| U02 | LOGISTICS_DEPOT | EN ATTENTE | Structure creee | Premier run |
| U03 | SCENOGRAPHY_DOCK | VALIDE | 16,641 vertices, camera, GPU | — |
| U04 | PHOTOGRAPHY_WING | FIX INJECTE | VULKAN_CAMERA_FIX_v1 dans EXO_04_DARKROOM.ipynb | Validation frames PNG |
| U05 | ALCHEMIST_LAB | EN ATTENTE | Structure creee | Premier run |
| U06 | AIRCRAFT_CARRIER | EN ATTENTE | Structure creee | Premier run |

---

## Tech-Pretres Statuts

| Nom | Statut | Priorite |
|-----|--------|----------|
| SENTINEL | OPERATIONNEL | — |
| MARSHAL | EXISTE (a formaliser) | — |
| PHANTOM_LINK | EXISTE (a formaliser) | — |
| VULKAN_FORGE | OPERATIONNEL | P0 |
| VOID-FLUSH | OPERATIONNEL | P1 |
| ATLAS | OPERATIONNEL | P2 |
| VOX | A CREER | P3 |
| KRONOS | A CREER | P4 |

---

## Fixes Appliques

| Commit | Fregate | Fix | Statut |
|--------|---------|-----|--------|
| 0cb3057d | U04 | camera_main ajoutee automatiquement | VALIDE |
| 6db5311f | U03 | depsgraph.update() avant evaluation | VALIDE |
| 80a6d336 | U03 | lit assembler_results.json | VALIDE |
| 81ca3426 | U03 | Documentation phase D6 | VALIDE |
| 6ea607a4 | U04 | ARSENAL inject_camera_cinematic.py (35mm/DOF) | VALIDE |
| a80a85a7 | U04 | EXO_04_DARKROOM.ipynb cellule injection + VOID-FLUSH | VALIDE |

---

## Derniere Session

- Date : 2026-04-05
- Actions : VULKAN_CAMERA_FIX_v1 — injection camera dans EXO_04_DARKROOM.ipynb
- Prochaine : Executer EXO_04_DARKROOM.ipynb -> valider frames PNG -> U04 VALIDE
