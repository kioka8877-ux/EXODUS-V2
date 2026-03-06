# TRACKING – U04 PHOTOGRAPHY WING (L'Œil)

## 1. OBJECTIF DE LA MUTATION (V2)
4 piliers optiques : Perspective Lock (fSpy ±5%), Auto-DOF (Empty sur buste avatar),
Shake procédural (Noise modifier dans Graph Editor), Volume Scatter + lampes invisibles.
Fidélité cinématographique — la caméra 3D doit reproduire la caméra source.

**Architecture** : U04 est séparée en deux sous-frégates (voir [ARCHITECTURE_U04.md](../04_PHOTOGRAPHY_WING/ARCHITECTURE_U04.md)) :
- **U04-A (Director)** : Configure le .blend (caméra, DOF, shake, atmosphère, Cycles). ~30s. Output = .blend.
- **U04-B (Darkroom)** : Lance le rendu batch ATOM-IC. ~2-4h (1080p + AI upscale). Output = frames PNG 16-bit. EN FORGE.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : TOUS CORRIGÉS par U04-A.
- **Goulot d'étranglement** : Rendu GPU (résolu par séparation A/B)
- **Risque VRAM/RAM** : FAIBLE (U04-A ne fait pas de rendu)
- **Fondation** : `camera_schema.py` (Bible Optique) — source unique de vérité pour presets.

## 3. PLAN D'ACTION (BACKLOG)

### U04-A — DIRECTOR (Configuration .blend) ✅ SCELLÉ
- [x] `camera_schema.py` — Bible Optique (533 lignes, 8 piliers, self_test 7/7) — PR #34
- [x] `fspy_tracker.py` — Pilier A : Perspective Lock fSpy ±5% — PR #35
- [x] `auto_dof.py` — Pilier B : Empty parenté au buste avatar → DOF automatique — PR #35
- [x] `render_forge.py` — Config Cycles + passes + résolution (PAS de rendu) — PR #35
- [x] Réécrire shake `camera_director.py` — Pilier C : Noise modifier (random.gauss supprimé) — PR #36
- [x] `lighting_rig.py` : apply_atmosphere() + place_invisible_lamps() — Pilier D — PR #36
- [x] `camera_director.py` : check_frustum() + matchmove style — PR #36
- [x] Centraliser presets dans `camera_schema.py` (duplication CUT_PRESETS/TRANSITION_TYPES supprimée) — PR #37
- [x] Câbler `EXO_04_PHOTOGRAPHY.py` v2.0.0 (nouveaux modules + arguments CLI) — PR #37
- [x] Mettre à jour documentation (UNIT_04_SUBPLAN.md, README_DEV.md) — PR #37

### U04-B — DARKROOM (Rendu ATOM-IC — EN FORGE)
**Décision ATOM-IC** : Rendre en 1080p @ 128 samples (pas 4K @ 256) — U06 Real-ESRGAN upscale → 4K.
Résultat : ~2-4h de rendu au lieu de 15-45h. Fits dans une session Colab.

- [x] Brainstorming infrastructure rendu → Google Colab T4 (ATOM-IC Inversion : 1080p + AI upscale)
- [ ] Nouveau preset `darkroom` dans `camera_schema.py` (1080p, 128 samples, OIDN, PNG 16-bit)
- [ ] `darkroom_render.py` — Script Blender headless (chunk rendering 300 frames + checkpoint JSON)
- [ ] `EXO_04_DARKROOM.py` — Orchestrateur CLI Python pur (valide inputs, lance blender, gère resume)
- [ ] `EXO_04_DARKROOM.ipynb` — Notebook Colab (mount Drive, auto-resume, progress bar)
- [ ] Mise à jour documentation (README_DEV.md, UNIT_04_SUBPLAN.md, ARCHITECTURE_U04.md)
- [ ] Intégration Marshal Out-Check pour frames rendues PNG 16-bit

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | Documents architecture (split A/B) | 🟢 | PR #32 | N/A |
| - | camera_schema.py (Bible Optique, 533 lignes) | 🟢 | PR #34 | N/A |
| - | fspy_tracker.py + auto_dof.py + render_forge.py | 🟢 | PR #35 | N/A |
| - | camera_director.py (Noise shake + frustum) + lighting_rig.py (Volume Scatter) | 🟢 | PR #36 | N/A |
| - | cuts_engine.py refactor + EXO_04 câblage + docs | 🟢 | PR #37 | N/A |
| 2026-03-06 | Brainstorming ATOM-IC U04-B : 1080p + chunks + checkpoint + AI upscale | ✅ | — | — |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (U04-A ne rend pas)
- Temps d'exécution moyen : ~30s (configuration .blend)
- [x] 5/5 critères VALIDATION.md satisfaits par U04-A
- [ ] Marshal Out-Check passé (*.blend dans OUT_CAMERA_LOGIC/) — nécessite test intégration

## RÉFÉRENCES
- [ARCHITECTURE U04](../04_PHOTOGRAPHY_WING/ARCHITECTURE_U04.md) — **Note technique split A/B**
- [PRD §U04](./EXODUS_V2_PRD.md) — Spécifications U04
- [VALIDATION §U04](./EXODUS_V2_VALIDATION.md) — Critères binaires U04
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
