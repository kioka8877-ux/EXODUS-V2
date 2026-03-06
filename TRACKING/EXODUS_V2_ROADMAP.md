# EXODUS V2 — ROADMAP (Plan de Conquête)

## PHASES DE MUTATION

### PHASE 0 : FONDATION (Semaine 1)
- [x] Ériger le sanctuaire TRACKING/ (PR #11 — 2026-02-26)
- [x] Valider l'Hexalogie avec l'Empereur
- [ ] Corriger EXODUS_CAMPAIGN_LOG.md (désynchronisé)
- Statut : 🟡 66%

### PHASE A : CERVEAU & LOGISTIQUE (Semaines 1-2)
**Priorité : MARSHAL + U00**

#### A1 — MARSHAL (✅ SCELLÉ)
- [x] Créer EXO_MARSHAL.py (Out-Check, In-Check, Campaign Log) — PR #12 (2026-02-26)
- [ ] Déployer MARSHAL dans chaque CODEBASE/

#### A2 — U00 Phase 1 CPU (VRAM = 0 GB)
- [x] M2 : Extraction audio FFmpeg → `audio_source.wav` → PR #15
- [x] M3 : Extraction FOV/ratio OpenCV → `camera_fov_ratio.json` → PR #15

#### A3 — U00 Phase 2 API (VRAM = 0 GB)
- [x] M1 : Prompt Gemini enrichi + `response_schema` avec enum verrouillé → PR #15
- [x] M1 : Dispatcher (Master JSON → 3 fichiers) → PR #15
- [x] M4 : `facial_animation.json` (extrait par Dispatcher) → PR #15
- [x] M5 : `motion_synthesis_prompt.txt` (extrait par Dispatcher) → PR #15
- [x] Validation : `normalize_timecodes()`, `validate_structure()`, `validate_completeness()` → PR #15

#### A4 — U00 Phase 3 GPU-A (VRAM ~3.5 GB)
- [x] M6 : DepthAnything V2 → `DEPTH_MAP/*.png` → PR #16
- [x] Flush GPU vérifié (VRAM < 0.5 GB après destruction modèle) → PR #16

#### A5 — U00 Phase 4 GPU-B (VRAM ~4 GB)
- [x] M7 : SAM vit_h → `semantic_masks.json` → PR #16
- [x] Flush GPU vérifié → PR #16

#### A6 — U00 Transverse
- [x] `MotorStatus` + `flags` dans le JSON final → PR #15
- [x] Mode `--rerun <motor>` → PR #15
- [x] Log VRAM (`vram_log.txt`) → PR #16
- [x] MARSHAL Out-Check passé → PR #16
- [x] Alignement documentaire v2.1 (TRACKING, PRD, VALIDATION) → PR #14

- Statut : ✅ 100% (MARSHAL + U00 scellés — PRs #12-#16)

### PHASE B : VIE & DÉCOR (Semaines 2-3)
**Priorité : U01 + U03**

#### B1.1 — expression_schema.py (Bible Anatomique) ✅ SCELLÉ
- [x] U01 : Créer expression_schema.py — PR #19
- [x] U01 : Rapport validation "Expression Hérétique" — PR #19
- [x] U01 : Marshal In-Check passé — PR #19

#### B1.2 — Réécriture Pipeline U01 ✅ SCELLÉ
- [x] U01 : Supprimer EMOCA, réécrire facial_extractor.py — PR #20
- [x] U01 : Adapter blender_fusion.py (NLA + F-Curve Noise + Bézier natif) — PR #20
- [x] U01 : Simplifier sync_engine.py, adapter EXO_01_TRANSMUTATION.py — PR #20
- [x] U01 : Mettre à jour notebooks — PR #23

#### B1.3 — Rhubarb Lip-Sync ✅ SCELLÉ
- [x] U01 : Intégrer Rhubarb lip-sync (NLA strip, priorité bouche) — PR #22
- Statut : ✅ 100% SCELLÉ (PR #19-#23)

#### B2 — U03 Scenography (Tri-Layer System)

##### B2.0 — scene_schema.py (Contrat de Scène)
- [ ] Créer scene_schema.py — Collections, objets, World settings, validate_scene()
- [ ] Custom properties .blend (exodus_schema_version, exodus_frigate)

##### B2.1 — Phase D1 (Quick Wins)
- [ ] Couche A — Infinity Dome (demi-sphère + texture vidéo)
- [ ] Shadow Catcher (plan séparé)
- [ ] World Sync (exposition alignée)
- [ ] Supprimer props_placer.py + environment_builder.py

##### B2.2 — Phase D2 (Core technique)
- [ ] Couche B — Displacement Mesh (128×128 + Displace + depth maps)
- [ ] Anti-ghosting (nettoyage depth maps via SAM)
- [ ] VRAM cap (max_subdivisions)

##### B2.3 — Phase D3 (Polish)
- [ ] Couche C — PBR Swap zones proches (SAM → PBR)
- [ ] Reflectivity Hack (Glass BSDF + Z-offset 0.01m)
- [ ] Refactor pbr_applicator.py + hdri_manager.py

##### B2.4 — Documentation
- [ ] Notebooks V2 + README_DEV.md + UNIT_03_SUBPLAN.md

- Statut : 🔴 0%

### PHASE C : FINITION (Semaines 3-4)
**Priorité : U02 + U04 + U05 + U06**
- [x] U02 : Ajouter bypass conditionnel (requires_u02)
#### C1 — U04 Architecture (Documentation) ✅
- [x] ARCHITECTURE_U04.md (note technique split A/B)
- [x] Mise à jour TRACKING_U04.md, TRACKING_MASTER.md
- Statut : ✅ SCELLÉ

#### C2 — U04-A Director (Configuration .blend) ✅
- [x] camera_schema.py (Bible Optique — fondation)
- [x] fspy_tracker.py (Pilier A — Perspective Lock ±5%)
- [x] auto_dof.py (Pilier B — Empty sur buste avatar)
- [x] Réécrire shake → Noise modifier (Pilier C)
- [x] apply_atmosphere() + invisible lamps (Pilier D)
- [x] check_frustum() (Alerte frustum)
- [x] render_forge.py (config Cycles — PAS de rendu)
- [x] Câblage EXO_04_PHOTOGRAPHY.py
- Statut : ✅ SCELLÉ (PR #34-#37)

#### C3 — U04-B Darkroom (Rendu ATOM-IC)
- [x] Brainstorming ATOM-IC : 1080p @ 128 samples + OIDN → U06 AI upscale 4K
- [ ] Preset `darkroom` dans camera_schema.py (1080p, 128 samples, Combined, PNG 16-bit)
- [ ] `darkroom_render.py` (Blender headless, chunks 300 frames, checkpoint JSON)
- [ ] `EXO_04_DARKROOM.py` (orchestrateur CLI + resume)
- [ ] `EXO_04_DARKROOM.ipynb` (Colab notebook)
- [ ] Documentation V2 (README_DEV.md, UNIT_04_SUBPLAN.md, ARCHITECTURE_U04.md)
- Statut : 🟡 EN FORGE (brainstorming validé, implémentation en cours)

#### C5 — U06 Aircraft Carrier (Pipeline Frame-Based V2) ✅
- [x] carrier_schema.py (Bible du Vaisseau-Mère — 6 piliers) — PR #45
- [x] Pipeline frame-based ZÉRO lossy intermédiaire — PR #46
- [x] 3 presets (AV1 distribution, H.265 fallback, ProRes master) — PR #46
- [x] Checkpoint system + chunks 10s + ratio lock — PR #46
- [x] Fix 3 bugs HIGH (destructive move, checkpoint nuke, pix_fmt) — PR #46
- Statut : ✅ 100% SCELLÉ (PR #44-#46)

#### C4 — U05 Alchemist Lab (Fusion Visuelle V2) ✅

##### C4.1 — alchemist_schema.py (Bible Alchimique) ✅
- [x] alchemist_schema.py — 7 piliers, presets, validation, self_test 8/8 — PR #38
- [x] Dossier IN_SOURCE_REF/ — PR #38

##### C4.2 — Match Color + Grain Matcher (Cœur Nucléaire) ✅
- [x] match_color.py (Histogram Specification LAB, référence par scène) — PR #40
- [x] grain_matcher.py (Bilateral filter decomposition, grain procédural calibré) — PR #40

##### C4.3 — Bloom + Sharpness + Orchestrateur ✅
- [x] bloom_engine.py (Luminance threshold + Gaussian blur + additive blend) — PR #41
- [x] sharpness_transfer.py (Laplacian variance matching) — PR #41
- [x] Rewrite EXO_05_ALCHEMIST.py v2.0.0 (Pipeline OpenCV, --preset CLI) — PR #41
- [x] Documentation (README_DEV.md, UNIT_05_SUBPLAN.md, requirements.txt) — PR #41

- Statut : ✅ 100% SCELLÉ (PR #38, #40, #41)

### PHASE D : SCALE (Semaine 4+)
- [ ] Test end-to-end (vidéo Brookhaven complète)
- [ ] Optimisation VRAM pour batch processing
- [ ] Documentation finale et formation
- Statut : 🔴 0%

## ORDRE DE FRAPPE
MARSHAL & U00 → U01 → U03 → U02/U04/U05/U06

## PROGRESSION GLOBALE
Mutation V2 : [█████████░] 🟢 95% — MARSHAL + U00 + U01 + U02 + U03 + U04-A + U05 + U06 scellés
Phase courante : PHASE D (Scale — U04-B Darkroom + test end-to-end restants)

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications techniques complètes
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères de succès par phase
- [RISKS](./EXODUS_V2_RISKS.md) — Risques par phase
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque tâche cochée doit pointer vers un commit ou un fichier vérifiable.

<!-- v2.8 — U06 SCELLÉ 100% (PR #44-#46) -->
