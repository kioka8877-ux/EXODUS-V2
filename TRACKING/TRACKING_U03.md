# TRACKING – U03 SCENOGRAPHY DOCK (La Forge du Décor)

## 1. OBJECTIF DE LA MUTATION (V2)
Remplacer McPrep par le Tri-Layer System : A) Infinity Dome (vidéo sur demi-sphère),
B) Displacement Mesh (depth maps DepthAnything → Displace modifier), C) PBR Swap (masques SAM → matériaux PBR).
Plus Shadow Catcher, Reflectivity Hack (plans Glass BSDF), World Sync (HDRi ↔ exposition).

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Architecture actuelle (McPrep Minecraft import) entièrement incompatible V2. Les 4 modules (`environment_builder.py`, `hdri_manager.py`, `pbr_applicator.py`, `props_placer.py`) sont obsolètes.
- **Goulot d'étranglement** : Le Tri-Layer System est une architecture complexe inédite — aucun code existant réutilisable
- **Risque VRAM/RAM** : MOYEN — Blender avec subdivision élevée (~4-6GB)

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Supprimer dépendance McPrep
- [ ] Implémenter Couche A (Infinity Dome — demi-sphère + texture vidéo)
- [ ] Implémenter Couche B (Displacement Mesh — plan subdivisé + Displace modifier + depth maps)
- [ ] Implémenter Couche C (PBR Swap — masques SAM → matériaux PBR)
- [ ] Activer Shadow Catcher (plan invisible pour ombres portées)
- [ ] Implémenter Reflectivity Hack (plans Glass BSDF sur surfaces vitrées)
- [ ] Implémenter World Sync (HDRi ↔ exposition source)

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer (cible < 6GB)
- Temps d'exécution moyen : À mesurer
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U03
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U03
- [RISKS](./EXODUS_V2_RISKS.md) — R5 (Depth flickering), R6 (SAM qualité)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
