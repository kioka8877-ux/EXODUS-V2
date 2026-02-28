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
#### C1 — U04 Architecture (Documentation)
- [ ] ARCHITECTURE_U04.md (note technique split A/B)
- [ ] Mise à jour TRACKING_U04.md, TRACKING_MASTER.md
- Statut : 🟢 EN COURS

#### C2 — U04-A Director (Configuration .blend)
- [ ] camera_schema.py (Bible Optique — fondation)
- [ ] fspy_tracker.py (Pilier A — Perspective Lock ±5%)
- [ ] auto_dof.py (Pilier B — Empty sur buste avatar)
- [ ] Réécrire shake → Noise modifier (Pilier C)
- [ ] apply_atmosphere() + invisible lamps (Pilier D)
- [ ] check_frustum() (Alerte frustum)
- [ ] render_forge.py (config Cycles — PAS de rendu)
- [ ] Câblage EXO_04_PHOTOGRAPHY.py
- Statut : 🟡 EN ATTENTE (après C1)

#### C3 — U04-B Darkroom (Rendu — PLANIFIÉ)
- [ ] Brainstorming infrastructure (Colab/Cloud/Local)
- [ ] Implémentation batch rendering
- Statut : 🔴 PLANIFIÉ (après C2)
- [ ] U05 : Match Color (alignement histogramme)
- [ ] U05 : Film Grain matching (extraction grain source)
- [ ] U05 : Bloom/Glow bleed
- [ ] U06 : Ratio lock strict (métadonnées U00)
- [ ] U06 : Forcer H.265 CRF 16-18
- Statut : 🔴 0%

### PHASE D : SCALE (Semaine 4+)
- [ ] Test end-to-end (vidéo Brookhaven complète)
- [ ] Optimisation VRAM pour batch processing
- [ ] Documentation finale et formation
- Statut : 🔴 0%

## ORDRE DE FRAPPE
MARSHAL & U00 → U01 → U03 → U02/U04/U05/U06

## PROGRESSION GLOBALE
Mutation V2 : [█████░░░░░] 🟢 50% — MARSHAL + U00 + U01 + U02 scellés
Phase courante : PHASE B2 (Décor — U03 Tri-Layer System)

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications techniques complètes
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères de succès par phase
- [RISKS](./EXODUS_V2_RISKS.md) — Risques par phase
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque tâche cochée doit pointer vers un commit ou un fichier vérifiable.

<!-- v2.5 — U04 Split A/B -->
