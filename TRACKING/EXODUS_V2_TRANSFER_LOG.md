# EXODUS V2 — TRANSFER LOG (Registre de l'Intendant)
> Matrice de traçabilité des flux — Rempli par l'Empereur lors des transferts manuels

## MODE D'EMPLOI
1. Avant chaque transfert : lancer `python EXO_MARSHAL.py --unit [SOURCE] --mode check-out`
2. Après chaque transfert : lancer `python EXO_MARSHAL.py --unit [DEST] --mode check-in`
3. Inscrire le résultat ci-dessous

## REGISTRE DES TRANSFERTS

| # | Date | Projet | Source | Destination | Fichiers | Marshal Out | Marshal In | Statut |
|---|------|--------|--------|-------------|----------|-------------|------------|--------|
| 1 | 2026-02-26 | TEST_MARSHAL | U00 | — | 0/7 | ❌ (0/7) | ⬜ | 🔴 Attendu — U00 non muté |

## MATRICE DES FLUX STANDARD

| De → Vers | Fichiers transférés | Format |
|-----------|---------------------|--------|
| U00 → U01 | PRODUCTION_PLAN.JSON, facial_animation.json | .json |
| U00 → U03 | DEPTH_MAP/, semantic_masks.json, PRODUCTION_PLAN.JSON | .png, .json |
| U00 → U04 | camera_fov_ratio metadata | .json |
| U00 → U05 | source_video_ref | .mp4 |
| U00 → U06 | audio_source.wav, format metadata | .wav, .json |
| U00 → Empereur | motion_synthesis_prompt.txt | .txt |
| Empereur → U01 | body_motion.fbx (from SayMotion) | .fbx |
| U01 → U02 | actor_animated.blend | .blend |
| U02 → U04 | actor_equipped.abc + .blend | .abc, .blend |
| U03 → U04 | environment.blend | .blend |
| U04 → U05 | raw_frames/ + render passes | .exr, .png |
| U05 → U06 | graded_frames/ | .png |

**Légende** : ⬜ Non vérifié | ✅ Validé | ❌ Échoué

## RÉFÉRENCES
- [MARSHAL](./TRACKING_MARSHAL.md) — Suivi du module de validation
- [PRD](./EXODUS_V2_PRD.md) — Schéma des flux complet
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Aucun transfert n'existe sans inscription dans ce registre.
