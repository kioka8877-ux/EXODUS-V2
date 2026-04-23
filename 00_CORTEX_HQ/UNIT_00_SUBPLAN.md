# SOUS-PLAN TECHNIQUE — UNITÉ 00: CORTEX HQ

## Mission
Analyser une vidéo source et générer un PRODUCTION_PLAN.JSON structuré.
Architecture duale API / Injection JSON (Codex v6). Cerveau de la flotte.

## Stack Technique
- Python 3.10+
- Gemini 2.5 Flash (API) ou Gemini 2.5 Pro Chat (mode injection)
- OpenCV (métadonnées vidéo / FOV)
- DepthAnything V2 (profondeur — Phase GPU-A)
- SAM vit_h (segmentation — Phase GPU-B)

## Architecture Pipeline (Codex v6)

```
Cellule 0  → Choix du mode  (MODE = "api" | "injection")
Cellule 1  → Pre-flight + M2 Audio (FFmpeg) + M3 FOV (OpenCV)  [commun]
Cellule 2  → M1 Gemini API auto                                  [mode api]
Cellule 2b → Widget injection JSON + validation schéma           [mode injection]
Cellule 3  → M6 DepthAnything V2 + M7 SAM + flags finaux         [commun]
             dispatch_master_json()  ← point de convergence unique
```

## Tâches Complétées

### ✅ Phase 1 CPU
- M2 Extraction audio (FFmpeg → audio_source.wav) — PR #15
- M3 Extraction FOV/ratio (OpenCV → camera_fov_ratio.json) — PR #15

### ✅ Phase 2 API
- M1 Gemini API — Master JSON monolithique (3 blocs) — PR #15
- response_schema avec enum verrouillé — PR #15
- Dispatcher (Master JSON → 3 fichiers séparés) — PR #15
- normalize_timecodes() — PR #15
- validate_structure() + validate_completeness() (3 niveaux) — PR #15

### ✅ Phase 3 GPU-A
- M6 DepthAnything V2 (DEPTH_MAP/*.png) + protocole destruction VRAM — PR #16

### ✅ Phase 4 GPU-B
- M7 SAM vit_h (semantic_masks.json) + protocole destruction VRAM — PR #16

### ✅ Transverse
- MotorStatus + flags JSON — PR #15
- Mode --rerun <motor_name> — PR #15
- Log VRAM (vram_log.txt) — PR #16
- Marshal Out-Check automatique — PR #16

### ✅ DÉCRETS CODEX v6 (23.04.2026)
- D-I : arsenal.json externe — load_arsenal / reload_arsenal_from_drive / _build_arsenal_enums
- D-II : --skip-gpu — bypasse Phase 3 + Phase 4
- D-III : Validation JSON Gemini stricte — retry loop x3 + erreur explicite
- D-IV : Architecture duale API / Injection — EXO_00_CORTEX_PRODUCTION.ipynb refonte 7 cellules + GEMINI_CHAT_METAPROMPT.md

## Statut: 🟡 IMPLÉMENTÉE — VALIDATION SOUVERAINE MANQUANTE
Date d'implémentation CODEX v6 : 2026-04-23
Validation Souveraine : ⬜ NON FAITE — test Colab sur vraie vidéo par l'Empereur requis

## Fichiers Clés
| Fichier | Rôle |
|---------|------|
| `CODEBASE/EXO_00_CORTEX.py` | Orchestrateur principal (6 moteurs) |
| `CODEBASE/EXO_00_CORTEX_PRODUCTION.ipynb` | Notebook production (7 cellules, dual mode) |
| `CODEBASE/EXO_00_CORTEX_CONTROL.ipynb` | Notebook debug |
| `arsenal.json` | Arsenal Impérial externe (personnages, armes, véhicules) |
| `GEMINI_CHAT_METAPROMPT.md` | Metaprompt pour mode injection (Gemini Chat) |

## Inputs / Outputs
| Direction | Fichier | Format |
|-----------|---------|--------|
| IN | video_source.mp4 | .mp4 |
| OUT | PRODUCTION_PLAN.JSON | .json |
| OUT | facial_animation.json | .json |
| OUT | motion_synthesis_prompt.txt | .txt |
| OUT | DEPTH_MAP/*.png | séquence PNG |
| OUT | semantic_masks.json | .json |
| OUT | audio_source.wav | .wav |
| OUT | camera_fov_ratio.json | .json |

<!-- v2.0 — CODEX v6 — 23.04.2026 -->
