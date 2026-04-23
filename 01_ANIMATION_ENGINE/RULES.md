# RULES — FRÉGATE 01 ANIMATION ENGINE

> Loi IV (Notebook Unique) | Loi I (Isolation des Silos) | Doctrine Codex v6

## RÈGLES IMPÉRIALES

### R1 — LOI D'ENTRÉE
- `IN_BODY_ANIMATED/` : OBLIGATOIRE — au moins un `avatar-ferrus-N.blend`
- `IN_VIDEO_SOURCE/video_source.mp4` : OBLIGATOIRE
- `IN_VIDEO_SOURCE/audio_original.wav` : OBLIGATOIRE si lip-sync actif (D-III)
- `IN_CORTEX_JSON/PRODUCTION_PLAN.JSON` : OBLIGATOIRE
- Aucun autre IN n'est lu

### R2 — LOI DE SORTIE
- `OUT_ANIMATED_ACTORS/avatar-ferrus-N_animated.blend` : OBLIGATOIRE
- `OUT_ANIMATED_ACTORS/avatar-ferrus-N_animated.abc` : OBLIGATOIRE
- `OUT_ANIMATED_ACTORS/transmutation_report.json` : OBLIGATOIRE
- Aucun fichier n'est écrit hors de `OUT_ANIMATED_ACTORS/` et `TMP_TRANSMUTATION/`

### R3 — LOI DE NON-POLLUTION GPU (VOID-FLUSH)
- InsightFace : `teardown()` appelé dans le bloc `finally` de `run_insightface_tracking()`
- EMOCA partagé : `teardown()` appelé dans le `finally` de la boucle principale (main)
- pyannote : `teardown()` appelé dans le bloc `finally` de `run_diarization()`
- Aucun modèle ne reste actif entre deux avatars sauf l'instance EMOCA partagée (intentionnel)

### R4 — LOI DU LIP-SYNC OBLIGATOIRE (D-III)
- Si `audio_original.wav` est présent ET Rhubarb est trouvé → lip-sync TOUJOURS activé
- Si Rhubarb introuvable : warning explicite, pas d'échec silencieux
- NLA lip-sync = track prioritaire (`blend_type = 'REPLACE'`) au-dessus des émotions

### R5 — LOI NLA FUSIONNÉE (SENTINEL FIX)
- L'animation faciale utilise UNE SEULE action NLA fusionnée (`facial_animation`)
- Interdit : créer une action par segment (N tracks = O(N) évaluation NLA)
- Le lip-sync Rhubarb reste sur un track séparé (`lip_sync`)

### R6 — SMOOTHING OBLIGATOIRE (SENTINEL FIX)
- Les intensités EMOCA brutes passent par `_smooth_frame_intensities()` (SavGol w=5)
- Cela réduit le jitter d'expression frame-à-frame avant segmentation
- Si scipy absent : dégradation gracieuse (pas d'échec)

### R7 — LOI DU NOTEBOOK UNIQUE (LOI IV)
- Un seul notebook de production : `EXO_01_PRODUCTION.ipynb`
- `EXO_01_CONTROL.ipynb` est réservé aux diagnostics / tests
- Les cellules complexes sont déléguées aux modules Python

### R8 — SCALABILITÉ (D-IV)
- La boucle `for N in avatars` doit fonctionner pour 1 à N avatars sans modification
- L'instance EMOCA est hoistée avant la boucle si `--skip-emoca` est absent
- Chaque avatar produit ses propres fichiers de sortie nommés `avatar-ferrus-N_*`

## CONTRAT D'INTERFACE (pour KRONOS)

| Entrée | Type | Obligatoire |
|--------|------|-------------|
| `IN_BODY_ANIMATED/avatar-ferrus-N.blend` | .blend | OUI |
| `IN_VIDEO_SOURCE/video_source.mp4` | .mp4 | OUI |
| `IN_VIDEO_SOURCE/audio_original.wav` | .wav | NON (warn si absent) |
| `IN_CORTEX_JSON/PRODUCTION_PLAN.JSON` | .json | OUI |

| Sortie | Type | Obligatoire |
|--------|------|-------------|
| `OUT_ANIMATED_ACTORS/avatar-ferrus-N_animated.blend` | .blend | OUI |
| `OUT_ANIMATED_ACTORS/avatar-ferrus-N_animated.abc` | .abc | OUI |
| `OUT_ANIMATED_ACTORS/transmutation_report.json` | .json | OUI |

## COMMANDE UNIQUE (LOI V)

```bash
python EXO_01_TRANSMUTATION.py --drive-root /path/to/drive
```

Options notables :
- `--skip-emoca` : fallback expressions neutres (tests rapides)
- `--skip-diarization` : piste audio globale (1 speaker)
- `--fps 30` : FPS cible (défaut: 30)
- `--dry-run` : validation sans exécution Blender
- `--device cpu` : mode CPU (sans GPU)

---

*Signé : CAPY-01 — Scribe de la Frégate 01 — Codex Imperial v6 — 23.04.2026*
