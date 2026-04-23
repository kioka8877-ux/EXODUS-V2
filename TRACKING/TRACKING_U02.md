# TRACKING – U02 LOGISTICS DEPOT (L'Armurerie)

## 1. OBJECTIF DE LA MUTATION (V2)
Activation conditionnelle via `requires_u02` boolean du PRODUCTION_PLAN.JSON.
Si `requires_u02 == false` : skip complet, copie directe acteur U01 → OUT_BAKED_ACTORS.
Si `requires_u02 == true` : pipeline normal (props_loader → socketing_engine → timeline_manager → final_baker).
Suppression de l'input fantôme IN_ROBLOX_AVATAR (l'avatar brut est consommé par U01 uniquement).

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Bypass conditionnel manquant. IN_ROBLOX_AVATAR fantôme dans Marshal manifest. Documentation V1 non alignée.
- **Goulot d'étranglement** : Faible — simple condition à ajouter + nettoyage manifest
- **Risque VRAM/RAM** : FAIBLE

## 3. PLAN D'ACTION (BACKLOG)

**Phase C1 — Bypass Conditionnel**
- [x] Lire `requires_u02` du PRODUCTION_PLAN.JSON (production_notes.requires_u02)
- [x] Implémenter skip complet si `requires_u02 == false` (copie directe + rapport SKIPPED)
- [x] Tester le pipeline avec et sans props

**Phase C2 — Nettoyage IN_ROBLOX_AVATAR**
- [x] Supprimer IN_ROBLOX_AVATAR du manifest U02 dans EXO_MARSHAL.py
- [x] Supprimer références IN_ROBLOX_AVATAR dans EXO_02_LOGISTICS.py
- [x] Supprimer argument CLI --roblox-avatar
- [x] Ajouter PRODUCTION_PLAN.JSON comme input required dans Marshal manifest

**Phase C3 — Documentation V2**
- [x] Mettre à jour notebooks (EXO_02_CONTROL.ipynb, EXO_02_PRODUCTION.ipynb)
- [x] Mettre à jour README_DEV.md
- [x] Mettre à jour UNIT_02_SUBPLAN.md

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-02-27 | Bypass requires_u02 + suppression IN_ROBLOX_AVATAR + Docs V2 | ✅ | PR #25 | N/A |

## 5. MÉTRIQUES ET VALIDATION
- [x] Marshal In-Check passé
- [x] Marshal Out-Check passé
- [x] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U02
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U02
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 6. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : SCELLÉE

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Validation pré-socketing | Avant socketing : vérifier que chaque bone cible existe dans l'armature. Lister bones manquants + interrompre avec rapport d'erreur explicite. Fin des props flottants silencieux. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-II | Fusion socketing + timeline | Fusionner socketing_engine.py + timeline_manager.py en actor_assembly.py. Interface externe identique — aucun notebook cassé. Réduit la complexité de maintenance. | FAIBLE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-III | Bypass props automatique | Double mécanisme : (1) PRODUCTION_PLAN.JSON[production_notes][requires_u02]==false, (2) auto-détection 0 props_actions. En bypass : copie F01 → OUT_BAKED_ACTORS + logistics_report.json status:SKIPPED | FAIBLE | FAIBLE | ✅ VALIDÉ (session 21.04 + PR #25) |

## 7. REGISTRE DE FORGE — PHASE 6 (Codex Imperial v6)

| Date | Action | Statut | Fichiers modifiés |
|------|--------|--------|-------------------|
| 23.04.2026 | D-I Validation pré-socketing | ✅ | `socketing_engine.py` (validate_sockets_for_plan + appel en tête de process_production_plan) |
| 23.04.2026 | D-II Fusion socketing + timeline | ✅ | `actor_assembly.py` (NEW — module unifié), `socketing_engine.py` (thin wrapper), `timeline_manager.py` (thin wrapper) |

<!-- v4.0 — Phase 6 Codex Imperial v6 — 3/3 décrets IMPLÉMENTÉS — 23.04.2026 -->
<!-- v3.0 — Codex Imperial v6 — 23.04.2026 -->
<!-- v2.0 — U02 SCELLÉ 100% -->
