# TRACKING – U04 PHOTOGRAPHY WING (L'Œil)

## 1. OBJECTIF DE LA MUTATION (V2)
4 piliers optiques : Perspective Lock (fSpy ±5%), Auto-DOF (Empty sur buste avatar),
Shake procédural (Noise modifier dans Graph Editor), Volume Scatter + lampes invisibles.
Fidélité cinématographique — la caméra 3D doit reproduire la caméra source.

**Architecture** : U04 est séparée en deux sous-frégates (voir [ARCHITECTURE_U04.md](../04_PHOTOGRAPHY_WING/ARCHITECTURE_U04.md)) :
- **U04-A (Director)** : Configure le .blend (caméra, DOF, shake, atmosphère, Cycles). ~30s. Output = .blend.
- **U04-B (Darkroom)** : Lance le rendu batch. ~15-45h. Output = frames EXR/PNG. PLANIFIÉ.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : `camera_director.py` existe mais manque fSpy integration, DOF automatique, shake procédural (utilise random.gauss au lieu de Noise modifier). `lighting_rig.py` manque Volume Scatter + lampes invisibles. Presets dupliqués entre `camera_director.py` et `cuts_engine.py`.
- **Goulot d'étranglement** : Rendu GPU (résolu par séparation A/B)
- **Risque VRAM/RAM** : FAIBLE (U04-A ne fait pas de rendu)
- **Fondation manquante** : Pas de `camera_schema.py` (Bible Optique) — les presets sont éparpillés et dupliqués.

## 3. PLAN D'ACTION (BACKLOG)

### U04-A — DIRECTOR (Configuration .blend)
- [ ] `camera_schema.py` — Bible Optique (fondation, Python pur, zéro Blender, self_test)
- [ ] `fspy_tracker.py` — Pilier A : Perspective Lock fSpy ±5%
- [ ] `auto_dof.py` — Pilier B : Empty parenté au buste avatar → DOF automatique
- [ ] Réécrire shake `camera_director.py` — Pilier C : Noise modifier (remplacer random.gauss)
- [ ] `lighting_rig.py` : apply_atmosphere() + place_invisible_lamps() — Pilier D
- [ ] `camera_director.py` : check_frustum() — Alerte avatar hors champ
- [ ] `render_forge.py` — Config Cycles + passes + résolution (PAS de rendu)
- [ ] Centraliser presets dans `camera_schema.py` (supprimer duplication CUT_TYPES/CUT_PRESETS)
- [ ] Câbler `EXO_04_PHOTOGRAPHY.py` (nouveaux modules + arguments CLI)
- [ ] Mettre à jour documentation (UNIT_04_SUBPLAN.md, README_DEV.md)

### U04-B — DARKROOM (Rendu — PLANIFIÉ, PAS DÉVELOPPÉ)
- [ ] Brainstorming infrastructure rendu (Colab Pro / Cloud / Local)
- [ ] Script batch rendering EXR 4K
- [ ] Optimisation VRAM / tiling / progressive rendering
- [ ] Intégration Marshal Out-Check pour frames rendues

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | Documents architecture (split A/B) | 🟢 | PR #XX | N/A |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (U04-A ne rend pas)
- Temps d'exécution moyen : ~30s (configuration .blend)
- [ ] Marshal Out-Check passé (*.blend dans OUT_CAMERA_LOGIC/)
- [ ] Validation Souveraine (5/5 critères VALIDATION.md)

## RÉFÉRENCES
- [ARCHITECTURE U04](../04_PHOTOGRAPHY_WING/ARCHITECTURE_U04.md) — **Note technique split A/B**
- [PRD §U04](./EXODUS_V2_PRD.md) — Spécifications U04
- [VALIDATION §U04](./EXODUS_V2_VALIDATION.md) — Critères binaires U04
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
