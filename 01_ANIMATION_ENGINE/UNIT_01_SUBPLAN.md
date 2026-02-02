# SOUS-PLAN TECHNIQUE — UNITÉ 01: ANIMATION ENGINE

## Mission
Extraire les données de motion capture (corps + visage) à partir des vidéos sources et générer des fichiers d'animation exploitables.

## Stack Technique (Prévu)
- Python 3.10+
- MediaPipe / MoveNet (pose estimation)
- OpenCV (traitement vidéo)
- Blender Python API (export BVH)

## Inputs
- `IN_MANIFEST/PRODUCTION_PLAN_*.json` — Plan de production CORTEX

## Outputs
- `OUT_ANIMATION/animation_*.pkl` — Données de pose sérialisées
- `OUT_ANIMATION/motion_*.bvh` — Fichiers motion capture Blender

## Tâches Prévues
- [ ] Configuration environnement MediaPipe
- [ ] Extraction landmarks corps (33 points)
- [ ] Extraction landmarks visage (468 points)
- [ ] Conversion coordonnées → rotation joints
- [ ] Export format BVH
- [ ] Gestion multi-personnages
- [ ] Interpolation frames manquantes

## Statut: ⚪ EN ATTENTE
