# TRACKING – MARSHAL (L'Intendant)

## 1. OBJECTIF DE LA MUTATION (V2)
Créer le module EXO_MARSHAL.py — Ghost script de validation logistique.
3 fonctions : Out-Check (vérifier fichiers OUT/), In-Check (valider fichiers IN/), Campaign Log (horodatage).
CLI : `python EXO_MARSHAL.py --unit F04 --mode validate`

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Module entièrement inexistant. Aucun script, aucun fichier, aucune logique de validation dans le repo.
- **Goulot d'étranglement** : Définition du schéma de validation par unité (quels fichiers attendus dans chaque IN/ et OUT/)
- **Risque VRAM/RAM** : AUCUN — script de validation léger (I/O fichier uniquement)

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Définir le manifeste de fichiers attendus par unité (IN/OUT)
- [ ] Créer EXO_MARSHAL.py avec CLI (--unit, --mode)
- [ ] Implémenter Out-Check (vérification présence+format fichiers OUT/)
- [ ] Implémenter In-Check (validation présence+format fichiers IN/)
- [ ] Implémenter Campaign Log (append horodaté dans EXODUS_CAMPAIGN.LOG)
- [ ] Copier MARSHAL dans chaque CODEBASE/ lors de l'init

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (script CPU)
- Temps d'exécution moyen : À mesurer
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications MARSHAL
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires MARSHAL
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
