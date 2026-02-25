# TRACKING – U00 CORTEX HQ (Le Cerveau)

## 1. OBJECTIF DE LA MUTATION (V2)
Implémenter les 6 moteurs d'extraction parallèles (Gemini, T2M, Facial JSON, DepthAnything V2, SAM, FOV/Ratio).
Coordonner via EXO_00_CORTEX.py. Générer le PRODUCTION_PLAN.JSON qui orchestre l'empire.
Extraire TOUTES les données nécessaires aux frégates en aval en une seule passe.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Seul le moteur Gemini existe. 5 moteurs manquants. Outputs manquants : `motion_synthesis_prompt.txt`, `facial_animation.json`, `DEPTH_MAP/`, `semantic_masks.json`, `camera_fov_ratio`, `audio_source.wav`
- **Goulot d'étranglement** : DepthAnything V2 + SAM simultanés sur T4 (VRAM limit 15GB)
- **Risque VRAM/RAM** : ÉLEVÉ — DepthAnything (~4GB) + SAM (~3GB) = ~7GB, plus Gemini API overhead

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Intégrer DepthAnything V2 (depth maps .png séquence)
- [ ] Intégrer SAM (semantic_masks.json)
- [ ] Ajouter extraction audio FFmpeg (audio_source.wav)
- [ ] Ajouter extraction FOV/résolution (camera_fov_ratio)
- [ ] Générer facial_animation.json (segments temporels)
- [ ] Générer motion_synthesis_prompt.txt (texte anatomique SayMotion)
- [ ] Orchestrer les 6 moteurs en séquentiel/parallèle selon VRAM disponible

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer (cible < 15GB)
- Temps d'exécution moyen : À mesurer
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U00
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U00
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM), R2 (Gemini), R5 (Depth), R6 (SAM)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
