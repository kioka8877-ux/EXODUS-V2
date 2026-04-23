# TRACKING – U01 ANIMATION ENGINE (Le Souffle)

## 1. OBJECTIF DE LA MUTATION (V2)
Suppression totale d'EMOCA. Module fondation `expression_schema.py` (Bible Anatomique — 7 Piliers) qui définit le mapping complet des 52 ARKit Shape Keys.
Emotional Intent Transfer via `facial_animation.json` généré par U00 (Gemini text → segments émotionnels).
3 leviers natifs Blender (Pareto 80/20) : F-Curve Bézier (interpolation), F-Curve Noise Modifier (Micro-Jitter yeux+bouche), NLA Editor (layering multicouche expression + eyes override + mouth override).
Injection Micro-Jitter via F-Curve Noise Modifier natif Blender (pas numpy custom).
Rhubarb lip-sync via rhubarb_bridge.py (NLA strip dédié, priorité bouche pendant parole).
Export dual : `.blend` + `.abc` (Alembic cache).

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Paradigme EMOCA incompatible V2. `facial_extractor.py` (355 lignes) à réécrire. Nouveau module `expression_schema.py` à créer. `blender_fusion.py` à adapter pour NLA + F-Curve Noise. `sync_engine.py` à simplifier (plus de sync audio/marqueur vidéo).
- **Goulot d'étranglement** : Mapping complet expressions textuelles (15 émotions + 9 états yeux + 8 états bouche) vers 52 ARKit Shape Keys avec règle de fusion
- **Risque VRAM/RAM** : MOYEN — Blender headless (~2-4GB). RÉDUIT grâce à suppression EMOCA (0 GB GPU pour facial extraction)

## 3. PLAN D'ACTION (BACKLOG)

**Phase B1.1 — expression_schema.py (Bible Anatomique)**
- [x] Pilier 1 : 15 EXPRESSION_PRESETS × 52 ARKit Shape Keys (joy, sadness, anger, fear, surprise, disgust, neutral, suspicious, determined, confused, pain, love, bored, excited, shocked)
- [x] Pilier 2 : Matrice des Conflits (combinaisons anatomiques interdites : mouthSmile+mouthFrown, eyeBlink+eyeWide, jawOpen+mouthClose)
- [x] Pilier 3 : Table des Oppositions (émotions antagonistes obligeant passage par neutre : joy↔sadness, joy↔anger, anger↔fear, surprise↔bored, love↔disgust)
- [x] Pilier 4 : Ranges Anatomiques (clampage esthétique Roblox : jaw max 0.8, tongueOut max 0.5)
- [x] Pilier 5 : Courbes d'Intensité (scaling : linear, quadratic, ease-in-out — intensity U00 ≠ multiplication brute)
- [x] Pilier 6 : Micro-Expressions Involontaires (presets blink/tics pour briser la rigidité)
- [x] Pilier 7 : EYE_PRESETS (9 états : focused_forward, looking_left, looking_right, looking_up, looking_down, narrowed, wide_open, closed, winking) + MOUTH_PRESETS (8 états : closed_tight, slightly_open, wide_open, smiling, frowning, pursed_lips, shouting, neutral) + Règle de fusion (expression base + eyes override zone oculaire + mouth override zone buccale)
- [x] Rapport de validation : démonstration blocage "Expression Hérétique" (intensité > 1.0, conflit shape keys)
- [x] Marshal In-Check passé sur expression_schema.py

**Phase B1.2 — Réécriture Pipeline (consommateurs du schema)**
- [x] Supprimer toute dépendance EMOCA (zéro import EMOCA dans tout U01)
- [x] Réécrire `facial_extractor.py` : lecture `facial_animation.json` → application presets du schema
- [x] Adapter `blender_fusion.py` : NLA strips pour layering (expression + eyes override + mouth override)
- [x] Levier Blender : F-Curve Bézier natif (zéro code custom Bézier — `handle_right_type = 'AUTO_CLAMPED'`)
- [x] Levier Blender : F-Curve Noise Modifier pour Micro-Jitter (strength=0.01-0.03, scale≈8-12Hz, blend_type='ADD')
- [x] Levier Blender : NLA strips pour layering multicouche (influence keyframable = intensity)
- [x] Simplifier `sync_engine.py` (aligner timecodes JSON sur FBX, supprimer sync audio/marqueur vidéo)
- [x] Adapter `EXO_01_TRANSMUTATION.py` (nouveau flow I/O : lire facial_animation.json, supprimer check EMOCA)
- [x] Mettre à jour les notebooks (EXO_01_CONTROL.ipynb, EXO_01_PRODUCTION.ipynb)
- [x] Export dual .blend + .abc

**Phase B1.3 — Rhubarb Lip-Sync**
- [x] Intégrer Rhubarb lip-sync (NLA strip dédié, priorité sur zone bouche)
- [x] Gérer conflit lip-sync/expressions (désactive shape keys bouche pendant parole)


### U01-D — FIX #1b ACTOR MODEL LOADING (VULKAN_U01_BACON_v1)
- [x] `blender_fusion.py` — `import_actor_model()` : import multi-format .blend/.fbx/.glb/.gltf/.obj + hard-fail + remove placeholder
- [x] `EXO_01_TRANSMUTATION.py` — `auto_detect_actor_model()` : scan IN_CORTEX_JSON/actor_models/ + --actor-model optionnel + alias --actor-blend legacy

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-02-26 | expression_schema.py — Bible Anatomique (794 lignes, 7 Piliers) | ✅ | PR #19 | N/A (pure Python) |
| 2026-02-26 | Pipeline V2 — facial_extractor + blender_fusion + sync_engine + TRANSMUTATION | ✅ | PR #20 | N/A (pure Python + bpy) |
| 2026-02-26 | Rhubarb lip-sync — rhubarb_bridge.py + NLA integration blender_fusion.py | ✅ | PR #22 | N/A (pure Python + bpy) |
| 2026-02-27 | Notebooks V2 + README_DEV.md — Documentation Armour | ✅ | PR #23 | N/A (docs) |
| 2026-04-09 | U01-D FIX #1b — blender_fusion import multi-format + EXO_01 auto-detect modele | ✅ | VULKAN_U01_BACON_v1 | N/A |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer (cible < 4GB — RÉDUIT vs V1 car zéro EMOCA)
- Temps d'exécution moyen : À mesurer
- [x] expression_schema.py : test "Expression Hérétique" passé
- [x] expression_schema.py : 15 expressions + 9 yeux + 8 bouche = 32 presets complets
- [x] Marshal In-Check passé
- [x] Marshal Out-Check passé
- [x] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U01
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U01
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM Blender)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 6. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : EN MUTATION (Pivot V1)

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Externalisation corps animé | Outil externe livre avatar-ferrus-N.blend par personnage (corps + retarget Roblox). EXODUS reçoit ce .blend comme input. Mixamo éliminé. | MOYENNE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-II | EMOCA sur visage humain réel | EMOCA opère sur le vrai visage humain de la vidéo source (non plus sur avatar Roblox). InsightFace isole la crop par avatar. Précision maximale dans la plage d'entraînement naturelle. | MOYENNE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-III | Lip-sync obligatoire | Rhubarb TOUJOURS activé si audio_original.wav présent. pyannote.audio génère piste propre par avatar (silence hors parole). Plus de flag optionnel — obligation de qualité. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-IV | Orchestration multi-avatar | Boucle for N in avatars. Pour chaque avatar : InsightFace → Face_ID stable, pyannote → piste propre, EMOCA + Rhubarb dédiés. Scalable 1→N sans modification de code. | HAUTE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |

**Schéma architectural cible V1 :**
```
INPUTS : avatar-ferrus-N.blend (outil ext.) + video_source.mp4 + audio_original.wav + PRODUCTION_PLAN.JSON
         ↓                  ↓               ↓
    InsightFace          pyannote         EMOCA
    face tracking       diarisation     visage reel
         ↓                  ↓               ↓
         for N in avatars: [BLENDER 4.0 HEADLESS]
              +-- EMOCA  --> shape keys visage
              +-- Rhubarb --> shape keys bouche
              ↓
         avatar-ferrus-N_animated.blend + .abc
```

## 8. REGISTRE DE FORGE — PHASE 6 (Codex Imperial v6)

| Date | Action | Statut | Fichiers modifiés |
|------|--------|--------|-------------------|
| 23.04.2026 | D-I Corps animé .blend | ✅ | `blender_fusion.py` (--body-blend, load_preanimated, main V3), `EXO_01_TRANSMUTATION.py` (IN_BODY_ANIMATED/ discovery), `IN_BODY_ANIMATED/` (NEW dir) |
| 23.04.2026 | D-II EMOCA visage humain | ✅ | `insightface_tracker.py` (NEW), `emoca_extractor.py` (NEW + VOID-FLUSH), `IN_VIDEO_SOURCE/` (NEW dir) |
| 23.04.2026 | D-III Lip-sync obligatoire | ✅ | `pyannote_diarizer.py` (NEW + VOID-FLUSH), `EXO_01_TRANSMUTATION.py` (Rhubarb systématique + warn explicite si absent) |
| 23.04.2026 | D-IV Multi-avatar orchestration | ✅ | `EXO_01_TRANSMUTATION.py` (rewrite v3 — boucle for N in avatars, scalable 1→N), `OUT_ANIMATED_ACTORS/` (NEW dir) |
| 23.04.2026 | requirements.txt V3 | ✅ | `requirements.txt` (numpy, opencv, insightface, onnxruntime-gpu, pyannote.audio, soundfile, torch) |
| 23.04.2026 | SENTINEL FIX #1 — typo PyannoteDialrizer → PyannoteDiarizer (alias backward-compat) | ✅ | `pyannote_diarizer.py` |
| 23.04.2026 | SENTINEL FIX #2 — smoothing.py intégré dans emoca_extractor (_smooth_frame_intensities, SavGol w=5) | ✅ | `emoca_extractor.py` |
| 23.04.2026 | SENTINEL FIX #3 — NLA fusionné: N tracks/N actions → 1 track/1 action globale (perf O(1)) | ✅ | `blender_fusion.py` (apply_nla_facial_animation rewrite) |
| 23.04.2026 | SENTINEL FIX #4 — EMOCA shared: modèle hoisté avant boucle multi-avatar (évite N rechargements) | ✅ | `EXO_01_TRANSMUTATION.py` (process_avatar + main VOID-FLUSH) |
| 23.04.2026 | VOX — RULES.md + test_u01.py (27 tests Pytest, couverture schema+translator+smoothing+diarizer) | ✅ | `RULES.md` (NEW), `CODEBASE/test_u01.py` (NEW) |

<!-- v6.0 — SENTINEL AUDIT + 4 FIXES + VOX tests — 23.04.2026 -->
<!-- v5.0 — Phase 6 Codex Imperial v6 — 4/4 décrets D-I D-II D-III D-IV IMPLÉMENTÉS — 23.04.2026 -->
<!-- v4.0 — Codex Imperial v6 — Pivot V1 — 23.04.2026 -->
<!-- v3.0 — U01 SCELLÉ 100% — B1.1 + B1.2 + B1.3 complétées -->
