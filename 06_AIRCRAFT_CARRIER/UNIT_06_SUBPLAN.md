# SOUS-PLAN TECHNIQUE — UNITÉ 06: AIRCRAFT CARRIER

## Mission
Assemblage final de tous les composants et upscale 4K/120FPS via RIFE.

## Stack Technique (Prévu)
- FFmpeg
- RIFE (Real-Time Intermediate Flow Estimation)
- Python orchestration

## Inputs
- `IN_COMPONENTS/graded_*.exr` — Séquences finales
- `IN_COMPONENTS/audio_*.wav` — Pistes audio
- `IN_COMPONENTS/PRODUCTION_PLAN_*.json` — Métadonnées

## Outputs
- `OUT_FINAL/FINAL_OUTPUT_*.mp4` — Vidéo finale 4K/120FPS
- `OUT_FINAL/FINAL_OUTPUT_*.mov` — Version ProRes archivage
- `OUT_FINAL/thumbnail_*.png` — Vignette pour publication

## Tâches Prévues
- [ ] Assemblage séquences vidéo
- [ ] Synchronisation audio multi-pistes
- [ ] Interpolation 30→120 FPS via RIFE
- [ ] Upscale 1080p→4K (si nécessaire)
- [ ] Encodage H.265/ProRes
- [ ] Génération métadonnées export
- [ ] Validation qualité automatique

## Pipeline Final
```
EXR Sequences → FFmpeg Assembly → RIFE 120FPS → 4K Upscale → Final Encode
                      ↓
                 Audio Sync
```

## Statut: ⚪ EN ATTENTE
