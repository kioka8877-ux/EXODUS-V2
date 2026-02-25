# EXODUS V2 — ROADMAP (Plan de Conquête)

## PHASES DE MUTATION

### PHASE 0 : FONDATION (Semaine 1)
- [ ] Ériger le sanctuaire TRACKING/ (CE DOCUMENT)
- [ ] Valider l'Hexalogie avec l'Empereur
- [ ] Corriger EXODUS_CAMPAIGN_LOG.md (désynchronisé)
- Statut : 🔴 0%

### PHASE A : CERVEAU & LOGISTIQUE (Semaines 1-2)
**Priorité : MARSHAL + U00**
- [ ] Créer EXO_MARSHAL.py (Out-Check, In-Check, Campaign Log)
- [ ] Déployer MARSHAL dans chaque CODEBASE/
- [ ] U00 : Ajouter moteur DepthAnything V2 (depth maps .png)
- [ ] U00 : Ajouter moteur SAM (semantic_masks.json)
- [ ] U00 : Ajouter moteur T2M (motion_synthesis_prompt.txt)
- [ ] U00 : Ajouter moteur Facial JSON (facial_animation.json)
- [ ] U00 : Ajouter extraction FOV/Ratio (camera_fov_ratio)
- [ ] U00 : Ajouter extraction audio (audio_source.wav)
- Statut : 🔴 0%

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
Mutation V2 : [░░░░░░░░░░] 🔴 0%
Phase courante : PHASE 0 (Fondation documentaire)

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications techniques complètes
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères de succès par phase
- [RISKS](./EXODUS_V2_RISKS.md) — Risques par phase
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque tâche cochée doit pointer vers un commit ou un fichier vérifiable.
