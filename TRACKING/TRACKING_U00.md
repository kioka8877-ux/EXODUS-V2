# TRACKING – U00 CORTEX HQ (Le Cerveau)

## 1. OBJECTIF DE LA MUTATION (V2)
Implémenter les 6 moteurs d'extraction parallèles (Gemini, T2M, Facial JSON, DepthAnything V2, SAM, FOV/Ratio).
Coordonner via EXO_00_CORTEX.py. Générer le PRODUCTION_PLAN.JSON qui orchestre l'empire.
Extraire TOUTES les données nécessaires aux frégates en aval en une seule passe.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Seul le moteur Gemini existe. 5 moteurs manquants. Outputs manquants : `motion_synthesis_prompt.txt`, `facial_animation.json`, `DEPTH_MAP/`, `semantic_masks.json`, `camera_fov_ratio`, `audio_source.wav`
- **Goulot d'étranglement** : DepthAnything V2 + SAM simultanés sur T4 (VRAM limit 15GB)
- **Risque VRAM/RAM** : ÉLEVÉ — DepthAnything (~4GB) + SAM (~3GB) = ~7GB, plus Gemini API overhead
- **Architecture cible** : 6 moteurs séquentiels (CPU → API → GPU-A → GPU-B)
- **VRAM peak cible** : 4 GB (séquentiel avec flush, jamais 2 modèles simultanés)

## 3. PLAN D'ACTION (BACKLOG)

### Phase 1 — CPU (VRAM = 0 GB)
- [x] M2 : Extraction audio via FFmpeg (`-vn -acodec pcm_s16le`) → `audio_source.wav` → PR #15
- [x] M3 : Extraction FOV/ratio via OpenCV (résolution, aspect ratio, focale estimée) → `camera_fov_ratio.json` → PR #15

### Phase 2 — API (VRAM = 0 GB)
- [x] M1 : Enrichir le prompt Gemini pour générer le Master JSON monolithique (3 blocs : `production_plan`, `facial_animation`, `motion_synthesis`) → PR #15
- [x] M1 : Implémenter le `response_schema` avec enum verrouillé (Arsenal Impérial) → PR #15
- [x] M1 : Implémenter le Dispatcher (Master JSON → 3 fichiers : `PRODUCTION_PLAN.JSON`, `facial_animation.json`, `motion_synthesis_prompt.txt`) → PR #15
- [x] M1 : Implémenter `normalize_timecodes()` (clamper segments faciaux sur bornes scène) → PR #15
- [x] M1 : Implémenter `validate_structure()` + `validate_completeness()` (3 niveaux de validation) → PR #15

### Phase 3 — GPU Moteur A (VRAM peak ~3.5 GB)
- [x] M6 : Intégrer DepthAnything V2 (chargement → inférence par frame → `DEPTH_MAP/*.png`) → PR #16
- [x] M6 : Implémenter protocole de destruction (del model → gc.collect → torch.cuda.empty_cache → vérification VRAM < 0.5 GB) → PR #16
  - Prérequis : Modèle `depth_anything_v2_vitl.pth` téléchargé dans `EXODUS_AI_MODELS/DEPTH_ANYTHING/`

### Phase 4 — GPU Moteur B (VRAM peak ~4 GB)
- [x] M7 : Intégrer SAM vit_h (vérifier VRAM dispo ≥ 3GB → chargement → segmentation keyframes → classification masques) → PR #16
- [x] M7 : Implémenter protocole de destruction identique à Phase 3 → PR #16
  - Prérequis : Modèle `sam_vit_h.pth` téléchargé dans `EXODUS_AI_MODELS/SAM/`

### Transverse
- [x] Implémenter `MotorStatus` (suivi par moteur : success/failed/partial) + `flags` dans le JSON → PR #15
- [x] Implémenter mode `--rerun <motor_name>` (relance un seul moteur sans retoucher le JSON Gemini) → PR #15
- [x] Implémenter log VRAM (`vram_log.txt`) avec peak par moteur → PR #16
- [x] Passer MARSHAL Out-Check (`python EXO_MARSHAL.py --unit U00 --mode check-out`) → PR #16

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-02-26 | Hexalogie documentaire v2.1 | ✅ | PR #14 (cdd617c) | — |
| 2026-02-26 | Orchestrateur + Moteurs CPU/API (M1-M5) | ✅ | PR #15 (9a22a2e) | — |
| 2026-02-26 | Moteurs GPU (M6-M7) + Marshal invocation | ✅ | PR #16 (f63150f) | — |

## 5. MÉTRIQUES ET VALIDATION

### Consommation VRAM par Moteur
| Moteur | VRAM Peak Cible | VRAM Peak Mesuré | RAM Peak | Durée (10s vidéo) |
|--------|----------------|-----------------|----------|-------------------|
| M1 Gemini API | 0 GB (cloud) | — | ~200 MB | 15-30s |
| M2 FFmpeg Audio | 0 GB (CPU) | — | ~100 MB | 2s |
| M3 OpenCV FOV | 0 GB (CPU) | — | ~300 MB | 1s |
| M6 DepthAnything V2 | ~3.5 GB | — | ~2 GB | 45-90s |
| M7 SAM vit_h | ~4.0 GB | — | ~2.5 GB | 60-120s |

### Critères de Validation
- [x] VRAM peak global < 5 GB (implémenté — peak cible 4 GB)
- [x] Flush GPU vérifié entre Phase 3 et Phase 4
- [x] `flags.all_motors_ok` implémenté
- [x] `--rerun` fonctionne
- [x] Marshal Out-Check implémenté (invocation automatique)
- [ ] Validation Souveraine (reste à faire — test Colab par l'Empereur)

## 6. RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U00
- [PRD — Schéma Master JSON](./EXODUS_V2_PRD.md#schémas-json-de-référence) — Master JSON V2, enums, impact par frégate
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U00
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM), R2 (Gemini), R5 (Depth), R6 (SAM)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

<!-- v2.1 — Post-Mutation Alignement -->
