# SOUS-PLAN TECHNIQUE — UNITÉ 01: ANIMATION ENGINE (Pivot V1)

## Mission
Recevoir un corps animé (.blend) depuis un outil externe, ajouter les expressions faciales
(EMOCA sur visage humain réel), le lip-sync (Rhubarb + pyannote.audio), et orchestrer
l'ensemble en multi-avatar. Livrer un .blend + .abc par avatar.

## PIVOT V1 (Codex v6 — 23.04.2026)

> **Avant le pivot :** EXODUS animait le corps (FBX Mixamo/SayMotion) + le visage
> (EMOCA sur avatar Roblox = précision dégradée).
>
> **Après le pivot :** Un outil externe (hors EXODUS) anime le corps et retargète sur Roblox.
> EXODUS reçoit le `.blend` corps animé et se concentre sur visage (EMOCA sur humain réel
> = précision maximale) + lip-sync + multi-avatar.

## Stack Technique
- Python 3.10+
- InsightFace (face tracking stable, Face_ID par personne)
- EMOCA (expression faciale sur visage humain réel)
- pyannote.audio (diarisation — piste propre par speaker)
- Rhubarb (lip-sync — toujours actif si audio présent)
- Blender 4.0 headless (fusion NLA + export)

## Flux Pipeline V1

```
INPUTS :
    avatar-ferrus-N.blend   (outil externe — corps animé + retarget Roblox)
    video_source.mp4        (vidéo humaine originale 9:16)
    audio_original.wav      (une seule piste, toutes voix mélangées)
    PRODUCTION_PLAN.JSON    (de F00)

for N in avatars:
    1. InsightFace  → Face_ID stable → crop visage N dans video_source.mp4
    2. pyannote     → timeline speaker N → piste audio propre (silence hors parole)
    3. EMOCA        → shape keys visage depuis visage humain réel
    4. Rhubarb      → shape keys bouche depuis piste audio propre
    5. Blender      → fusion NLA dans avatar-ferrus-N.blend

OUTPUTS :
    avatar-ferrus-N_animated.blend  (corps + visage + lip-sync)
    avatar-ferrus-N.abc             (Alembic cache)
```

## Tâches Complétées

### ✅ Base V2 (pré-pivot)
- expression_schema.py — Bible Anatomique (7 Piliers, 52 ARKit Shape Keys) — PR #19
- Pipeline V2 facial_extractor + blender_fusion + sync_engine + TRANSMUTATION — PR #20
- Rhubarb lip-sync NLA — PR #22
- Notebooks V2 + README_DEV.md — PR #23
- FIX #1b — import multi-format .blend/.fbx/.glb + auto-detect modèle — VULKAN_U01_BACON_v1

### ✅ DÉCRETS CODEX v6 — Pivot V1 (23.04.2026)
- D-I Corps animé outil externe — `blender_fusion.py` (--body-blend, load_preanimated, main V3), `EXO_01_TRANSMUTATION.py` (IN_BODY_ANIMATED/ discovery), dossier `IN_BODY_ANIMATED/`
- D-II EMOCA sur visage humain réel — `insightface_tracker.py` (NEW), `emoca_extractor.py` (NEW + VOID-FLUSH), dossier `IN_VIDEO_SOURCE/`
- D-III Lip-sync obligatoire — `pyannote_diarizer.py` (NEW + VOID-FLUSH), Rhubarb systématique si audio présent
- D-IV Orchestration multi-avatar — `EXO_01_TRANSMUTATION.py` v3 (boucle for N in avatars, scalable 1→N)

### ✅ SENTINEL Fixes (23.04.2026)
- FIX #1 — typo PyannoteDialrizer → PyannoteDiarizer (alias backward-compat)
- FIX #2 — smoothing.py intégré dans emoca_extractor (_smooth_frame_intensities, SavGol w=5)
- FIX #3 — NLA fusionné: N tracks/N actions → 1 track/1 action globale (perf O(1))
- FIX #4 — EMOCA shared: modèle hoissté avant boucle multi-avatar (évite N rechargements)

### ✅ VOX (23.04.2026)
- RULES.md créé
- test_u01.py — 27 tests Pytest (schema + translator + smoothing + diarizer)

## Statut: 🟢 SCELLÉE — VALIDATION SOUVERAINE PASSÉE
Date de scellage CODEX v6 : 2026-04-23

## Fichiers Clés
| Fichier | Rôle |
|---------|------|
| `CODEBASE/EXO_01_TRANSMUTATION.py` | Orchestrateur V3 (boucle multi-avatar) |
| `CODEBASE/blender_fusion.py` | Fusion Blender headless (NLA + body-blend) |
| `CODEBASE/insightface_tracker.py` | Face tracking stable (Face_ID par personne) |
| `CODEBASE/emoca_extractor.py` | Extraction expressions depuis visage humain |
| `CODEBASE/pyannote_diarizer.py` | Diarisation audio (piste propre par speaker) |
| `CODEBASE/rhubarb_bridge.py` | Lip-sync (NLA strip dédié) |
| `CODEBASE/expression_schema.py` | Bible Anatomique (7 Piliers, 52 ARKit) |

## Dossiers I/O
| Dossier | Direction | Contenu |
|---------|-----------|---------|
| `IN_BODY_ANIMATED/` | IN | avatar-ferrus-N.blend (outil externe) |
| `IN_VIDEO_SOURCE/` | IN | video_source.mp4 (vidéo humaine originale) |
| `IN_CORTEX_JSON/` | IN | PRODUCTION_PLAN.JSON + facial_animation.json |
| `OUT_ANIMATED_ACTORS/` | OUT | avatar-ferrus-N_animated.blend + .abc |

<!-- v3.0 — Pivot V1 + CODEX v6 — 23.04.2026 -->
