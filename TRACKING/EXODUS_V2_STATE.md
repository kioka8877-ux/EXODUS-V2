# EXODUS V2 — ÉTAT J0 (Phylactère de Vérité)
> Diagnostic de mutation — Point de départ 0%

## TABLEAU DE CONFORMITÉ V2

| Unité | Nom | Statut Code Actuel | Conformité V2 | Écart Principal |
|-------|-----|--------------------|----------------|-----------------|
| U00 | CORTEX HQ | 🟢 Scellée (V1) | 🔴 16% | 5/6 moteurs manquants |
| U01 | ANIMATION ENGINE | 🟢 Forgé (V1) | 🔴 10% | Paradigme EMOCA ≠ Emotional Intent |
| U02 | LOGISTICS DEPOT | 🟡 En Forge | 🟡 70% | Bypass conditionnel absent |
| U03 | SCENOGRAPHY DOCK | 🟢 Forgé (V1) | 🔴 5% | McPrep ≠ Tri-Layer System |
| U04 | PHOTOGRAPHY WING | 🟢 Opérationnel (V1) | 🟡 40% | Manque fSpy, DOF, Shake |
| U05 | ALCHEMIST LAB | 🟢 Opérationnel (V1) | 🟡 50% | Manque Match Color, Grain |
| U06 | AIRCRAFT CARRIER | ✅ Opérationnel (V1) | 🔴 40% | 4 compressions lossy + schema manquant |
| MARSHAL | INTENDANT | ✅ Scellé (PR #12) | 🟢 100% | — |

## ÉCARTS DÉTAILLÉS

### U00 — CORTEX HQ
- **Code actuel** : `EXO_00_CORTEX.py` — Gemini narrative analysis only
- **V2 exige** : 6 moteurs parallèles (Gemini, T2M/SayMotion, Facial JSON, DepthAnything V2, SAM segmentation, FOV/Ratio extraction)
- **Manquant** : DepthAnything V2 (depth maps .png sequence), SAM (semantic masks), T2M (motion synthesis prompt), Facial JSON (ARKit timing), FOV extraction (camera metadata)
- **Outputs manquants** : `motion_synthesis_prompt.txt`, `facial_animation.json`, `DEPTH_MAP/` sequence, `semantic_masks.json`, `camera_fov_ratio` metadata, `audio_source.wav`

### U01 — ANIMATION ENGINE
- **Code actuel** : `facial_extractor.py` (355 lines) uses EMOCA mathematical extraction — trained on human faces, fails on Roblox avatars
- **V2 exige** : "Emotional Intent Transfer" — Gemini text → Python → ARKit 52 Shape Keys. 3 layers: Observation (U00 Gemini), Translation (emotion→shape keys), Micro-Jitter injection. Plus Rhubarb lip-sync.
- **Impact** : Complete rewrite of facial pipeline. `blender_fusion.py` and `sync_engine.py` also affected.

### U02 — LOGISTICS DEPOT
- **Code actuel** : Full module exists (props_loader, socketing_engine, timeline_manager, final_baker)
- **V2 exige** : Conditional activation via `requires_u02` boolean from PRODUCTION_PLAN.JSON. Skip if no props detected.
- **Impact** : Minor — add bypass logic to `EXO_02_LOGISTICS.py`

### U03 — SCENOGRAPHY DOCK
- **Code actuel** : Uses McPrep (Minecraft addon) to import map → PBR + HDRi. Files: `environment_builder.py`, `hdri_manager.py`, `pbr_applicator.py`, `props_placer.py`
- **V2 exige** : Tri-Layer System — A) Infinity Dome (video on half-sphere), B) Displacement Mesh (DepthAnything depth maps → Blender Displace modifier on subdivided plane), C) PBR Swap (SAM masks → replace near surfaces). Plus Shadow Catcher, Reflectivity Hack (glass planes), World Sync.
- **Impact** : Complete architecture rewrite. All 4 modules obsolete.

### U04 — PHOTOGRAPHY WING
- **Code actuel** : `camera_director.py`, `lighting_rig.py`, `cuts_engine.py`, `keyframe_animator.py` — has camera tracking and lighting
- **V2 exige** : 4 pillars — A) fSpy/Blender tracker perspective lock (±5% movement limit), B) Auto-DOF with Empty on avatar bust, C) Procedural camera shake (Noise modifier in Graph Editor), D) Volume Scatter + invisible lights aligned to video sources
- **Impact** : Partial rewrite — extend existing camera_director, add DOF and shake systems

### U05 — ALCHEMIST LAB
- **Code actuel** : `color_grader.py`, `compositor_pipeline.py`, `denoiser.py`, `effects_forge.py` — has LUT grading and denoising
- **V2 exige** : Match Color (histogram alignment to source video), Film Grain matching (not just adding grain — matching source grain), Bloom/Glow bleed, Sharpness transfer blur. Uses OpenCV+Pillow.
- **Impact** : Partial rewrite — needs histogram-based color matching instead of LUT, grain extraction from source

### U06 — AIRCRAFT CARRIER
- **Code actuel** : `rife_interpolator.py`, `final_encoder.py`, `upscaler.py`, `audio_sync.py`, `sequence_assembler.py` — Pipeline fonctionnel V1
- **V2 exige** : Pipeline frame-based ZÉRO compression intermédiaire, carrier_schema.py, 3 encoding presets (AV1/H.265/ProRes), batch RIFE+upscale par chunks 10s, checkpoint system, ratio lock strict, CRF configurable avec tune animation
- **Écarts critiques découverts** :
  1. **4 compressions lossy H.264 en cascade** : sequence_assembler (libx264 CRF 18) → rife_interpolator (libx264 CRF 18) → upscaler (libx264 CRF 18) → final_encoder (libx265 CRF 18). Dégradation cumulative de qualité.
  2. **Absence de carrier_schema.py** : U06 est la seule frégate sans module de données pures. Toutes les constantes sont éparpillées ou hardcodées.
  3. **Schema JSON V2 non lu** : Le code attend `output.resolution` (string) mais le PRD définit `format.resolution` (array) et `format.ratio` (string).
  4. **Aucun batch processing** : RIFE traite toute la vidéo d'un coup (~50GB de frames temp, risque OOM T4)
  5. **Aucun checkpoint** : crash = restart total
- **Impact** : Réécriture majeure — nouveau carrier_schema.py + refactor complet des 5 modules + nouveau pipeline

### MARSHAL — L'Intendant ✅ SCELLÉ
- **Code actuel** : `EXO_MARSHAL.py` (578 lignes) — Python pur, zéro dépendance
- **V2 exige** : Ghost script per unit. 3 fonctions : Out-Check, In-Check, Campaign Log ✅
- **Localisation** : `/EXODUS-V2/EXO_MARSHAL.py` + `/EXODUS-V2/README_MARSHAL.md`
- **PR** : #12 (mergée 2026-02-26)
- **Impact** : ✅ Module complet — manifeste 7 unités, routage, SHA256, CLI opérationnelle

## DÉSYNCHRONISATION CAMPAIGN_LOG
Le fichier `EXODUS_CAMPAIGN_LOG.md` racine montre U01-U06 comme "EN ATTENTE" alors que les UNIT_XX_SUBPLAN.md confirment :
- U01: 🟢 FORGÉ | U03: 🟢 FORGÉ | U04: 🟢 OPÉRATIONNEL | U05: 🟢 OPÉRATIONNEL | U06: ✅ OPÉRATIONNEL
