# TRACKING – U03 SCENOGRAPHY DOCK (La Forge du Decor)

## 1. OBJECTIF DE LA MUTATION (V2)
Remplacement complet de l'architecture V1 (templates hardcodes) par le Tri-Layer System data-driven.
3 Couches : A) Infinity Dome, B) Displacement Mesh, C) PBR Swap.
Modules complementaires : Shadow Catcher (plan separe), Reflectivity Hack (Glass BSDF + Z-offset), World Sync (exposition alignee).
Nouveau contrat inter-fregates : scene_schema.py (meme doctrine que expression_schema.py de U01).
Anti-ghosting : nettoyage des depth maps via masques SAM avant displacement.
VRAM cap : limitation des subdivisions pour compatibilite Colab T4 (<6GB).

## 2. ETAT J0 (DIAGNOSTIC DES ECARTS)
- **Ecarts constates** : Architecture V1 basee sur templates hardcodes (urban_street, indoor, outdoor, studio). Generation de geometrie generique sans lien avec la video source. 4 modules obsoletes sur 5.
- **Modules V1** : environment_builder.py (REWRITE), pbr_applicator.py (REFACTOR → Couche C), hdri_manager.py (REFACTOR → World Sync), props_placer.py (SUPPRIMER), EXO_03_SCENOGRAPHY.py (REFACTOR)
- **Goulot d'etranglement** : Tri-Layer System est une architecture inedite — rewrite quasi-total (~2170 lignes)
- **Risque VRAM/RAM** : MOYEN — Blender avec subdivision 128x128 + depth maps (~4-6GB)

## 3. PLAN D'ACTION (BACKLOG)

### Phase D0 — Contrat de Scene (scene_schema.py)
- [x] Creer scene_schema.py — Collections obligatoires (ENV_DOME, ENV_TERRAIN, ENV_SHADOW, ENV_GLASS)
- [x] Definir nomenclature objets (infinity_dome, displacement_mesh, shadow_catcher, glass_plane_*)
- [x] Definir World settings contractuels (use_nodes=True, Environment Texture, strength)
- [x] Implementer validate_scene() pour le Marshal
- [x] Definir custom properties .blend (exodus_schema_version, exodus_frigate, exodus_validated)

### Phase D1 — Infinity Dome + Shadow Catcher + World Sync (Quick Wins)
- [x] Couche A : Infinity Dome (demi-sphere UV rayon ~100m + texture video source)
- [x] Shadow Catcher : plan SEPARE invisible (is_shadow_catcher=True) — PAS sur le displacement mesh
- [x] World Sync : HDRi aligne sur exposition video (Strength du World Shader)
- [x] Supprimer props_placer.py (inutile en V2)
- [x] Supprimer environment_builder.py (remplace par les 3 couches)

### Phase D2 — Displacement Mesh (Core technique)
- [x] Couche B : Plan subdivise 128x128 + Displace modifier + depth maps DepthAnything
- [x] Anti-ghosting : Nettoyer depth maps via masques SAM (aplatir zones personnages) AVANT displacement
- [x] VRAM cap : max_subdivisions parametrable pour limiter la consommation memoire

### Phase D3 — PBR Swap + Reflectivity Hack (Polish)
- [x] Couche C : masques SAM → presets PBR (zones PROCHES uniquement, pas les zones lointaines)
- [x] Labels SAM supportes : road, grass, wall, water, glass, sky
- [x] Reflectivity Hack : plans Glass BSDF sur surfaces vitrees (Z-offset 0.01m anti z-fighting)
- [x] Refactor pbr_applicator.py pour SAM mapping
- [x] Refactor hdri_manager.py → World Sync

### Phase D4 — Documentation
- [x] Rewrite EXO_03_CONTROL.ipynb (V2)
- [x] Rewrite EXO_03_PRODUCTION.ipynb (V2)
- [x] Rewrite README_DEV.md (V2)
- [x] Mettre a jour UNIT_03_SUBPLAN.md (V2)

### Phase D5 — Adaptabilite Multi-Scene (ATOM-IC)
- [x] Ajouter ENVIRONMENT_TO_SCENE_PROFILE dans scene_schema.py — 18 environment_id mappes
- [x] Ajouter DEFAULT_SCENE_PROFILE comme fallback universel
- [x] Ajouter param fallback_color a apply_dome_material() dans dome_builder.py
- [x] layer_assembler.py v2.1.0 — derive scene_type/mood/dome_fallback depuis environment_id
- [x] Priority logic : lighting_mood explicite JSON > profil automatique
- [x] Result dict enrichi : environment_id + scene_type trackes dans assembler_results.json

### Phase D6 — Corrections Validation Pipeline (ATOM-IC)
- [x] Fix #1 : Ajouter camera_main default dans assemble_scene() — lens=35mm, pos=(0,-15,8), rot=75deg
      → layer_assembler.py : cam placeholder overridable par U04, active_layers += "camera"
- [x] Fix #2 : Ajouter view_layer.update() + depsgraph.update() dans geometry_probe_u03.py
      → _evaluated_vertex_count() : depsgraph non actualise en background mode → 4 vertices faux
- [x] Fix #3 : EXO_03_PRODUCTION.ipynb Cell 9 — afficher scene_type depuis assembler_results.json
      → scene_type n'existe pas dans PRODUCTION_PLAN.JSON — seulement dans assembler_results.json

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-02-27 | Phase D0 — scene_schema.py (822 lignes) | ✅ | PR #27 merged | N/A |
| 2026-02-27 | Phase D1 — Dome + Shadow + World + layer_assembler | ✅ | PR #28 merged | N/A |
| 2026-02-27 | Phase D2 — Displacement Mesh + Anti-ghosting + VRAM cap | ✅ | PR #29 merged | N/A |
| 2026-02-27 | Phase D3 — PBR Swap + Glass BSDF + Suppression V1 | ✅ | PR #30 merged | N/A |
| 2026-02-27 | Phase D4 — Documentation V2 | ✅ | PR #31 merged | N/A |
| 2026-03-28 | Phase D5 — ENVIRONMENT_TO_SCENE_PROFILE (scene_schema) | ✅ | commit 7284ee9c | N/A |
| 2026-03-28 | Phase D5 — fallback_color param (dome_builder) | ✅ | commit c2637c90 | N/A |
| 2026-03-28 | Phase D5 — layer_assembler v2.1.0 adaptif | ✅ | commit 532a22ae | N/A |
| 2026-03-29 | Fix #1 — camera_main default dans assemble_scene() | ✅ | commit 0cb3057d | N/A |
| 2026-03-29 | Fix #2 — dg.update() dans geometry_probe_u03.py | ✅ | a livrer | N/A |
| 2026-03-29 | Fix #3 — EXO_03_PRODUCTION Cell 9 scene_type | ✅ | a livrer | N/A |
| 2026-04-03 | Phase 5 T44 — VOID-FLUSH: blender_adapter.py + hook pre-render | ✅ | Phase 5 commit | N/A |
| 2026-04-03 | Phase 5 T45 — ATLAS: session_store.py + SessionStore integration | ✅ | Phase 5 commit | N/A |
| 2026-04-03 | Phase 5 T46 — VOX: RULES.md + test_u03.py (35 tests Pytest) | ✅ | Phase 5 commit | N/A |

## 5. METRIQUES ET VALIDATION
- Consommation VRAM Max : A mesurer (cible < 6GB)
- Temps d'execution moyen : A mesurer
- [x] scene_schema.py validate_scene() passe
- [x] Marshal In-Check passe (structure conforme)
- [x] Marshal Out-Check passe (5 collections, custom properties)
- [x] Adaptabilite multi-scene : 18 environment_id → profil automatique
- [x] VOID-FLUSH intégré (blender_adapter.py + hook pre-render)
- [x] ATLAS intégré (session_store.py + SessionStore save)
- [x] RULES.md créé (lois de la fregate documentées)
- [x] test_u03.py — 35 tests Pytest (structure, syntax, intégrations)
- [ ] Validation Souveraine (test Colab par l'Empereur)

## REFERENCES
- [PRD](./EXODUS_V2_PRD.md) — Specifications U03
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Criteres binaires U03
- [RISKS](./EXODUS_V2_RISKS.md) — R5 (Depth flickering), R6 (SAM qualite)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Beton** : Chaque entree dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 6. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : SCELLÉE

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Suppression code mort D2/D3 | Supprimer toutes les références aux phases D2 (depth maps) et D3 (semantic masks) du code de production actif. Créer ROADMAP_U03.md pour tracer les fonctionnalités futures. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-II | Classe de base BlenderLayerBuilder | dome_builder + glass_builder + shadow_catcher_builder partagent ~60% logique init Blender. Créer classe de base commune. Centralise gestion erreurs, réduit duplication. | MOYENNE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-III | Stabilisation Phantom Link | phantom_link.py vit uniquement à la racine Drive. Chaque frégate lit depuis la racine. Supprimer l'auto-copie depuis U03/CODEBASE. L'Empereur est garant de sa présence. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |

**D-I :** imports D2/D3 supprimés de layer_assembler.py. `_build_procedural_interior()` = seul chemin actif. ROADMAP_U03.md créé. ASSEMBLER_VERSION → 3.0.0.

**D-II :** `blender_layer_base.py` créé avec `BlenderLayerBuilder._ensure_collection()`. dome_builder, shadow_catcher_builder, glass_builder utilisent la classe de base.

**D-III :** Auto-copie phantom_link supprimée de EXO_03_SCENOGRAPHY.py. Contrat documenté : L'Empereur est garant de la présence à la racine.

<!-- v4.0 — Décrets D-I/D-II/D-III IMPLÉMENTÉS — 23.04.2026 -->
<!-- v3.0 — Codex Imperial v6 — 23.04.2026 -->
<!-- v2.1 — U03 TRACKING D5 ADAPTIVE SCENE PROFILE -->
