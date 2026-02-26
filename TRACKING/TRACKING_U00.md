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
- [ ] M2 : Extraction audio via FFmpeg (`-vn -acodec pcm_s16le`) → `audio_source.wav`
- [ ] M3 : Extraction FOV/ratio via OpenCV (résolution, aspect ratio, focale estimée) → `camera_fov_ratio.json`

### Phase 2 — API (VRAM = 0 GB)
- [ ] M1 : Enrichir le prompt Gemini pour générer le Master JSON monolithique (3 blocs : `production_plan`, `facial_animation`, `motion_synthesis`)
- [ ] M1 : Implémenter le `response_schema` avec enum verrouillé (Arsenal Impérial)
- [ ] M1 : Implémenter le Dispatcher (Master JSON → 3 fichiers : `PRODUCTION_PLAN.JSON`, `facial_animation.json`, `motion_synthesis_prompt.txt`)
- [ ] M1 : Implémenter `normalize_timecodes()` (clamper segments faciaux sur bornes scène)
- [ ] M1 : Implémenter `validate_structure()` + `validate_completeness()` (3 niveaux de validation)

### Phase 3 — GPU Moteur A (VRAM peak ~3.5 GB)
- [ ] M6 : Intégrer DepthAnything V2 (chargement → inférence par frame → `DEPTH_MAP/*.png`)
- [ ] M6 : Implémenter protocole de destruction (del model → gc.collect → torch.cuda.empty_cache → vérification VRAM < 0.5 GB)
  - Prérequis : Modèle `depth_anything_v2_vitl.pth` téléchargé dans `EXODUS_AI_MODELS/DEPTH_ANYTHING/`

### Phase 4 — GPU Moteur B (VRAM peak ~4 GB)
- [ ] M7 : Intégrer SAM vit_h (vérifier VRAM dispo ≥ 3GB → chargement → segmentation keyframes → classification masques)
- [ ] M7 : Implémenter protocole de destruction identique à Phase 3
  - Prérequis : Modèle `sam_vit_h.pth` téléchargé dans `EXODUS_AI_MODELS/SAM/`

### Transverse
- [ ] Implémenter `MotorStatus` (suivi par moteur : success/failed/partial) + `flags` dans le JSON
- [ ] Implémenter mode `--rerun <motor_name>` (relance un seul moteur sans retoucher le JSON Gemini)
- [ ] Implémenter log VRAM (`vram_log.txt`) avec peak par moteur
- [ ] Passer MARSHAL Out-Check (`python EXO_MARSHAL.py --unit U00 --mode check-out`)

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

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
- [ ] VRAM peak global < 5 GB (marge 1 GB sur cible 4 GB)
- [ ] Flush GPU vérifié entre Phase 3 et Phase 4 (VRAM résiduelle < 0.5 GB)
- [ ] `flags.all_motors_ok == true` en conditions normales
- [ ] `--rerun` fonctionne sans retoucher les fichiers Gemini existants
- [ ] Marshal Out-Check passé (7/7 fichiers, verdict ✅ ou 🟡)
- [ ] Validation Souveraine

## 6. RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U00
- [PRD — Schéma Master JSON](./EXODUS_V2_PRD.md#schémas-json-de-référence) — Master JSON V2, enums, impact par frégate
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U00
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM), R2 (Gemini), R5 (Depth), R6 (SAM)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

<!-- v2.1 — Post-Mutation Alignement -->
