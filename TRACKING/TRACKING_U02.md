# TRACKING – U02 LOGISTICS DEPOT (L'Armurerie)

## 1. OBJECTIF DE LA MUTATION (V2)
Ajouter activation conditionnelle via `requires_u02` boolean du PRODUCTION_PLAN.JSON.
Skip complet si pas de props détectés. MVP : pas d'améliorations complexes.
Le workflow actuel (props_loader → socketing_engine → timeline_manager → final_baker) reste intact.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Le bypass conditionnel n'existe pas dans `EXO_02_LOGISTICS.py`. Le workflow actuel exécute toujours U02 sans condition.
- **Goulot d'étranglement** : Faible — simple condition à ajouter
- **Risque VRAM/RAM** : FAIBLE

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Lire `requires_u02` du PRODUCTION_PLAN.JSON
- [ ] Implémenter skip complet si `requires_u02 == false`
- [ ] Tester le pipeline avec et sans props

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer
- Temps d'exécution moyen : À mesurer
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U02
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U02
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
