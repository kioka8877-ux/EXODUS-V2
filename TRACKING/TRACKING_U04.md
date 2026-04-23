# TRACKING – U04 PHOTOGRAPHY WING (L'Œil)

## 1. OBJECTIF DE LA MUTATION (V2)
4 piliers optiques : Perspective Lock (fSpy ±5%), Auto-DOF (Empty sur buste avatar),
Shake procédural (Noise modifier dans Graph Editor), Volume Scatter + lampes invisibles.
Fidélité cinématographique — la caméra 3D doit reproduire la caméra source.

**Architecture** : U04 est séparée en deux sous-frégates (voir [ARCHITECTURE_U04.md](../04_PHOTOGRAPHY_WING/ARCHITECTURE_U04.md)) :
- **U04-A (Director)** : Configure le .blend (caméra, DOF, shake, atmosphère, Cycles). ~30s. Output = .blend.
- **U04-B (Darkroom)** : Lance le rendu batch ATOM-IC. ~2-4h (1080p + AI upscale). Output = frames PNG 16-bit. ✅ SCELLÉ (PR #48-#49).

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

### U04-B — DARKROOM (Rendu ATOM-IC) ✅ SCELLÉ
**Décision ATOM-IC** : Rendre en 1080p @ 128 samples (pas 4K @ 256) — U06 Real-ESRGAN upscale → 4K.
Résultat : ~2-4h de rendu au lieu de 15-45h. Fits dans une session Colab.

- [x] Brainstorming infrastructure rendu → Google Colab T4 (ATOM-IC Inversion : 1080p + AI upscale) — PR #48
- [x] Nouveau preset `darkroom` dans `camera_schema.py` (1080p, 128 samples, OIDN, PNG 16-bit) — PR #49
- [x] `darkroom_render.py` — Script Blender headless (chunk rendering 300 frames + checkpoint JSON) — PR #49
- [x] `EXO_04_DARKROOM.py` — Orchestrateur CLI Python pur (valide inputs, lance blender, gère resume) — PR #49
- [x] `EXO_04_DARKROOM.ipynb` — Notebook Colab (mount Drive, auto-resume, progress bar) — PR #49
- [x] Mise à jour documentation (README_DEV.md, UNIT_04_SUBPLAN.md, ARCHITECTURE_U04.md) — PR #49
- [ ] Intégration Marshal Out-Check pour frames rendues PNG 16-bit

### U04-D — FIX RESOLUTION 9:16 (VULKAN_U04_RESOLUTION_FIX_v1)
- [x] `render_forge.py` — `override_resolution_from_fov_json()` : lit camera_fov_ratio.json et override resolution Blender
- [x] `darkroom_render.py` — `override_resolution_from_fov_json()` + arg `--camera-fov-json` : override au moment du render
- [x] `EXO_04_DARKROOM.py` — arg `--camera-fov-json` + transmission au darkroom_render.py
- [x] `EXO_04_DARKROOM.ipynb` — variable `CAMERA_FOV_JSON` + passage automatique si fichier present

### U04-C — ADAPTABILITÉ MULTI-SCÈNE (ATOM-IC D5)
- [x] `camera_schema.py` — LIGHTING_PRESET_TO_STYLE : mapping preset_id U00 → style U04 (10 presets) — commit 9b43190b
- [x] `camera_schema.py` — SCENE_TYPE_TO_LIGHTING : mapping scene_type U03 → profil complet (4 types) — commit 9b43190b
- [x] `camera_director.py` — Chaîne de priorité 3 niveaux (explicit > scene_type > preset_id) — commit f8a1d70b

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | Documents architecture (split A/B) | 🟢 | PR #32 | N/A |
| - | camera_schema.py (Bible Optique, 533 lignes) | 🟢 | PR #34 | N/A |
| - | fspy_tracker.py + auto_dof.py + render_forge.py | 🟢 | PR #35 | N/A |
| - | camera_director.py (Noise shake + frustum) + lighting_rig.py (Volume Scatter) | 🟢 | PR #36 | N/A |
| - | cuts_engine.py refactor + EXO_04 câblage + docs | 🟢 | PR #37 | N/A |
| 2026-03-06 | Brainstorming ATOM-IC U04-B : 1080p + chunks + checkpoint + AI upscale | ✅ | — | — |
| 2026-03-06 | U04-B Darkroom complet : darkroom_render.py + EXO_04_DARKROOM.py + notebook + docs | ✅ | PR #49 | — |
| 2026-03-28 | U04-C LIGHTING_PRESET_TO_STYLE + SCENE_TYPE_TO_LIGHTING (camera_schema) | ✅ | commit 9b43190b | N/A |
| 2026-03-28 | U04-C chaîne priorité éclairage adaptatif (camera_director) | ✅ | commit f8a1d70b | N/A |
| 2026-04-03 | Phase 5 T44 — VOID-FLUSH: blender_adapter.py + hook pre-render | ✅ | Phase 5 commit | N/A |
| 2026-04-03 | Phase 5 T45 — ATLAS: session_store.py + SessionStore integration | ✅ | Phase 5 commit | N/A |
| 2026-04-03 | Phase 5 T46 — VOX: RULES.md + test_u04.py (37 tests Pytest) | ✅ | Phase 5 commit | N/A |
| 2026-04-09 | U04-D FIX RESOLUTION 9:16 : override depuis camera_fov_ratio.json dans render_forge + darkroom + orchestrateur + notebook | ✅ | VULKAN_U04_RESOLUTION_FIX_v1 | N/A |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (U04-A ne rend pas)
- Temps d'exécution moyen : ~30s (configuration .blend)
- [x] 5/5 critères VALIDATION.md satisfaits par U04-A
- [ ] Marshal Out-Check passé (*.blend dans OUT_CAMERA_LOGIC/) — nécessite test intégration
- Temps d'exécution estimé U04-B : ~2-4h pour 60s vidéo (1080p @ 128 samples)
- Taille output U04-B : ~1.5 GB pour 60s vidéo (1800 frames PNG 16-bit)
- [x] 8/8 critères VALIDATION.md satisfaits par U04-B (sauf Marshal Out-Check)
- [x] camera_schema.py self_test 8/8 (inclut test darkroom preset)
- [x] Adaptabilité multi-scène : 10 preset_id + 4 scene_type → style automatique
- [x] VOID-FLUSH intégré (blender_adapter.py + hook pre-render)
- [x] ATLAS intégré (session_store.py + SessionStore save)
- [x] RULES.md créé (7 règles archit. + 2 VOID-FLUSH + 2 ATLAS + 2 éclairage)
- [x] test_u04.py — 37 tests Pytest (structure, syntax, intégrations, A/B séparation)

## RÉFÉRENCES
- [ARCHITECTURE U04](../04_PHOTOGRAPHY_WING/ARCHITECTURE_U04.md) — **Note technique split A/B**
- [PRD §U04](./EXODUS_V2_PRD.md) — Spécifications U04
- [VALIDATION §U04](./EXODUS_V2_VALIDATION.md) — Critères binaires U04
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 6. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : VALIDÉE (4/4 décrets confirmés session)

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Mode manuel guidé (Phase 1 prioritaire) | Intentions de cadrage depuis PRODUCTION_PLAN.JSON → keyframes caméra cohérents. Tracking auto (COLMAP/OpenCV) reporté en Phase 2. | HAUTE | MOYENNE | ✅ VALIDÉ |
| D-II | Notebook de production unifié | Un seul EXO_04_PRODUCTION.ipynb avec cellules conditionnelles (mode manuel / auto). Remplace l'architecture split A/B complexe. | HAUTE | FAIBLE | ✅ VALIDÉ |
| D-III | Reference Frame Background | Extraire frame de référence par scène (ffmpeg). L'importer comme Background Image viewport Blender. L'opérateur aligne caméra manuellement sur référence. Commande : `ffmpeg -i video_source.mp4 -vf "select=eq(n\,FRAME)" -vsync 0 ref_frame.png` | HAUTE | FAIBLE | ✅ VALIDÉ |
| D-IV | Arsenal lumineux 3-Point + HDRi Poly Haven | Couche 1 : HDRi Poly Haven (gratuit, libre) via bpy sur World Blender. Couche 2 : rig 3 points (Key + Fill + Rim) scripté bpy par acteur. Addons natifs : Sun Position + Dynamic Sky. Aucun addon externe requis. | HAUTE | FAIBLE | ✅ VALIDÉ |

**Note :** U04 est la frégate la mieux alignée avec le Codex v6 — les 4 décrets sont déjà validés en session brainstorming. Implémentation à confirmer en code.

<!-- v3.0 — Codex Imperial v6 — 23.04.2026 — 4/4 validés -->
<!-- v2.1 — U04 TRACKING C — ADAPTIVE LIGHTING -->
