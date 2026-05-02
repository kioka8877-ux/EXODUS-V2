# M2_F01 — ANIMATION VALIDATOR

> Mode 2 — Phase 8 — Dual Pipeline Doctrine — v1.0.0

## Rôle

Première frégate du pipeline Mode 2 (From Scratch).
Valide le GLB avatar animé fourni par l'Opérateur et vérifie la conformité audio.

## Lois Impériales appliquées

| Loi | Règle |
|-----|-------|
| R-01 | Isolation stricte — copie indépendante, zéro lien Mode 1 |
| R-02 | GLB obligatoire avec animations embarquées |
| R-03 | durée_audio <= durée_animation (animation prime) |

## Structure

```
07_M2_F01_ANIMATION/
├── CODEBASE/
│   ├── EXO_M2_F01_ANIMATION.py     ← Script principal CLI
│   ├── EXO_M2_F01_CONTROL.ipynb    ← Diagnostics pré-vol
│   ├── EXO_M2_F01_PRODUCTION.ipynb ← Notebook de production
│   └── requirements.txt
├── IN_GLB_AVATAR/   ← Déposer avatar.glb ici
├── IN_AUDIO/        ← Déposer audio.wav ici (optionnel)
├── OUT_VALIDATED/   ← avatar_validated.glb + audio_validated.*
└── OUT_REPORT/      ← m2_f01_report.json
```

## Utilisation

```bash
# Mode interactif (auto-détection des inputs)
python CODEBASE/EXO_M2_F01_ANIMATION.py

# GLB explicite
python CODEBASE/EXO_M2_F01_ANIMATION.py --glb avatar.glb

# Avec audio (vérifie LOI R-03)
python CODEBASE/EXO_M2_F01_ANIMATION.py --glb avatar.glb --audio audio.wav

# Dry-run (validation sans copie)
python CODEBASE/EXO_M2_F01_ANIMATION.py --dry-run --verbose
```

## Flux Mode 2

```
Opérateur fournit :
  avatar.glb (GLB avec animations embarquées) → IN_GLB_AVATAR/
  audio.wav  (optionnel)                      → IN_AUDIO/

M2_F01 valide :
  ✓ Magic bytes GLB
  ✓ Présence animations (LOI R-02)
  ✓ durée_audio <= durée_animation (LOI R-03, si audio)

Sortie → OUT_VALIDATED/ → Transfer Manuel → M2_F02/IN_*/
```

## Dépendances

```bash
pip install pygltflib librosa soundfile
```

- `pygltflib` : analyse complète du GLB (animations, durées)
- `librosa` / `pydub` : mesure durée audio (au moins l'un des deux)
- Fallback natif : `wave` module Python (WAV uniquement)
