# TRACKING – U03 SCENOGRAPHY DOCK (La Forge du Décor)

## 1. OBJECTIF DE LA MUTATION (V2)
Remplacement complet de l'architecture V1 (templates hardcodés) par le Tri-Layer System data-driven.
3 Couches : A) Infinity Dome, B) Displacement Mesh, C) PBR Swap.
Modules complémentaires : Shadow Catcher (plan séparé), Reflectivity Hack (Glass BSDF + Z-offset), World Sync (exposition alignée).
Nouveau contrat inter-frégates : scene_schema.py (même doctrine que expression_schema.py de U01).
Anti-ghosting : nettoyage des depth maps via masques SAM avant displacement.
VRAM cap : limitation des subdivisions pour compatibilité Colab T4 (<6GB).

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Architecture V1 basée sur templates hardcodés (urban_street, indoor, outdoor, studio). Génération de géométrie générique sans lien avec la vidéo source. 4 modules obsolètes sur 5.
- **Modules V1** : environment_builder.py (REWRITE), pbr_applicator.py (REFACTOR → Couche C), hdri_manager.py (REFACTOR → World Sync), props_placer.py (SUPPRIMER), EXO_03_SCENOGRAPHY.py (REFACTOR)
- **Goulot d'étranglement** : Tri-Layer System est une architecture inédite — rewrite quasi-total (~2170 lignes)
- **Risque VRAM/RAM** : MOYEN — Blender avec subdivision 128×128 + depth maps (~4-6GB)

## 3. PLAN D'ACTION (BACKLOG)

### Phase D0 — Contrat de Scène (scene_schema.py)
- [ ] Créer scene_schema.py — Collections obligatoires (ENV_DOME, ENV_TERRAIN, ENV_SHADOW, ENV_GLASS)
- [ ] Définir nomenclature objets (infinity_dome, displacement_mesh, shadow_catcher, glass_plane_*)
- [ ] Définir World settings contractuels (use_nodes=True, Environment Texture, strength)
- [ ] Implémenter validate_scene() pour le Marshal
- [ ] Définir custom properties .blend (exodus_schema_version, exodus_frigate, exodus_validated)

### Phase D1 — Infinity Dome + Shadow Catcher + World Sync (Quick Wins)
- [ ] Couche A : Infinity Dome (demi-sphère UV rayon ~100m + texture vidéo source)
- [ ] Shadow Catcher : plan SÉPARÉ invisible (is_shadow_catcher=True) — PAS sur le displacement mesh
- [ ] World Sync : HDRi aligné sur exposition vidéo (Strength du World Shader)
- [ ] Supprimer props_placer.py (inutile en V2)
- [ ] Supprimer environment_builder.py (remplacé par les 3 couches)

### Phase D2 — Displacement Mesh (Core technique)
- [ ] Couche B : Plan subdivisé 128×128 + Displace modifier + depth maps DepthAnything
- [ ] Anti-ghosting : Nettoyer depth maps via masques SAM (aplatir zones personnages) AVANT displacement
- [ ] VRAM cap : max_subdivisions paramétrable pour limiter la consommation mémoire

### Phase D3 — PBR Swap + Reflectivity Hack (Polish)
- [ ] Couche C : masques SAM → presets PBR (zones PROCHES uniquement, pas les zones lointaines)
- [ ] Labels SAM supportés : road, grass, wall, water, glass, sky
- [ ] Reflectivity Hack : plans Glass BSDF sur surfaces vitrées (Z-offset 0.01m anti z-fighting)
- [ ] Refactor pbr_applicator.py pour SAM mapping
- [ ] Refactor hdri_manager.py → World Sync

### Phase D4 — Documentation
- [ ] Rewrite EXO_03_CONTROL.ipynb (V2)
- [ ] Rewrite EXO_03_PRODUCTION.ipynb (V2)
- [ ] Rewrite README_DEV.md (V2)
- [ ] Mettre à jour UNIT_03_SUBPLAN.md (V2)

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer (cible < 6GB)
- Temps d'exécution moyen : À mesurer
- [ ] scene_schema.py validate_scene() passé
- [ ] Marshal In-Check passé
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U03
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U03
- [RISKS](./EXODUS_V2_RISKS.md) — R5 (Depth flickering), R6 (SAM qualité)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

<!-- v2.0 — U03 TRACKING PREP -->
