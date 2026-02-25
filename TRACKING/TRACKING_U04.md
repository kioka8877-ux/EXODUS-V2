# TRACKING – U04 PHOTOGRAPHY WING (L'Œil)

## 1. OBJECTIF DE LA MUTATION (V2)
4 piliers optiques : Perspective Lock (fSpy ±5%), Auto-DOF (Empty sur buste avatar),
Shake procédural (Noise modifier dans Graph Editor), Volume Scatter + lampes invisibles.
Fidélité cinématographique — la caméra 3D doit reproduire la caméra source.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : `camera_director.py` existe mais manque fSpy integration, DOF automatique, shake procédural. `lighting_rig.py` manque Volume Scatter.
- **Goulot d'étranglement** : Intégration fSpy (outil externe → Blender)
- **Risque VRAM/RAM** : FAIBLE

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Intégrer fSpy pour perspective lock
- [ ] Limiter mouvement caméra à ±5%
- [ ] Implémenter Auto-DOF (Empty parenté au buste avatar)
- [ ] Ajouter Noise modifier pour shake procédural
- [ ] Ajouter Volume Scatter atmosphérique
- [ ] Placer lampes invisibles sur sources lumineuses vidéo
- [ ] Ajouter alerte frustum (avatar hors champ)

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
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U04
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U04
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
