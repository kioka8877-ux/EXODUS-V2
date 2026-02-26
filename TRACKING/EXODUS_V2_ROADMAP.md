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
- [ ] M2 : Extraction audio FFmpeg → `audio_source.wav`
- [ ] M3 : Extraction FOV/ratio OpenCV → `camera_fov_ratio.json`

#### A3 — U00 Phase 2 API (VRAM = 0 GB)
- [ ] M1 : Prompt Gemini enrichi + `response_schema` avec enum verrouillé
- [ ] M1 : Dispatcher (Master JSON → 3 fichiers)
- [ ] M4 : `facial_animation.json` (extrait par Dispatcher)
- [ ] M5 : `motion_synthesis_prompt.txt` (extrait par Dispatcher)
- [ ] Validation : `normalize_timecodes()`, `validate_structure()`, `validate_completeness()`

#### A4 — U00 Phase 3 GPU-A (VRAM ~3.5 GB)
- [ ] M6 : DepthAnything V2 → `DEPTH_MAP/*.png`
- [ ] Flush GPU vérifié (VRAM < 0.5 GB après destruction modèle)

#### A5 — U00 Phase 4 GPU-B (VRAM ~4 GB)
- [ ] M7 : SAM vit_h → `semantic_masks.json`
- [ ] Flush GPU vérifié

#### A6 — U00 Transverse
- [ ] `MotorStatus` + `flags` dans le JSON final
- [ ] Mode `--rerun <motor>`
- [ ] Log VRAM (`vram_log.txt`)
- [ ] MARSHAL Out-Check passé
- [ ] Alignement documentaire v2.1 (TRACKING, PRD, VALIDATION)

- Statut : 🟡 12% (1/20 tâches — MARSHAL scellé)

### PHASE B : VIE & DÉCOR (Semaines 2-3)
**Priorité : U01 + U03**
- [ ] U01 : Supprimer EMOCA, implémenter Emotional Intent Transfer
- [ ] U01 : Mapping émotions → 52 ARKit Shape Keys
- [ ] U01 : Injection Micro-Jitter (bruit procédural)
- [ ] U01 : Intégration Rhubarb Lip-Sync
- [ ] U03 : Supprimer McPrep, implémenter Tri-Layer System
- [ ] U03 : Couche A — Infinity Dome (video texture on half-sphere)
- [ ] U03 : Couche B — Displacement Mesh (depth maps → Displace)
- [ ] U03 : Couche C — PBR Swap (SAM masks → PBR materials)
- [ ] U03 : Shadow Catcher + Reflectivity Hack + World Sync
- Statut : 🔴 0%

### PHASE C : FINITION (Semaines 3-4)
**Priorité : U02 + U04 + U05 + U06**
- [ ] U02 : Ajouter bypass conditionnel (requires_u02)
- [ ] U04 : Intégrer fSpy perspective lock (±5%)
- [ ] U04 : Auto-DOF (Empty sur buste avatar)
- [ ] U04 : Shake procédural (Noise modifier)
- [ ] U04 : Volume Scatter + lampes invisibles
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
Mutation V2 : [█░░░░░░░░░] 🟡 12%
Phase courante : PHASE A (Cerveau & Logistique — MARSHAL scellé, U00 6-moteurs séquentiels en attente)

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications techniques complètes
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères de succès par phase
- [RISKS](./EXODUS_V2_RISKS.md) — Risques par phase
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque tâche cochée doit pointer vers un commit ou un fichier vérifiable.

<!-- v2.1 — Post-Mutation Alignement -->
