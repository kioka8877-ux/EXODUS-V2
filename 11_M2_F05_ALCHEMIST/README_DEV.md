# M2_F05 — ALCHEMIST (Mode 2)

> Mode 2 — Phase 8 — Dual Pipeline Doctrine — v1.0.0

## Rôle

Cinquième frégate du pipeline Mode 2 (From Scratch).
Fusionne visuellement les frames rendues (de M2_F04) avec une vidéo source de référence.
Pipeline OpenCV CPU pur : match_color → grain → bloom → sharpness.

## Lois Impériales appliquées

| Loi | Règle |
|-----|-------|
| R-01 | Isolation stricte — copie indépendante, zéro lien Mode 1, zéro Phantom Link |
| R-04 | Overlay binaire OUI/NON géré par M2_F06 en aval |

## Structure

```
11_M2_F05_ALCHEMIST/
├── CODEBASE/
│   ├── EXO_M2_F05_ALCHEMIST.py      ← Script principal CLI v1.0.0
│   ├── alchemist_schema.py           ← Bible Alchimique (copie M1)
│   ├── match_color.py                ← Transfert couleur LAB (copie M1)
│   ├── grain_matcher.py              ← Transfert grain filmique (copie M1)
│   ├── bloom_engine.py               ← Bloom additif (copie M1)
│   ├── sharpness_transfer.py         ← Alignement netteté (copie M1)
│   ├── lut_engine.py                 ← LUT .cube Mode C (copie M1)
│   ├── EXO_M2_F05_CONTROL.ipynb     ← Diagnostics pré-vol
│   ├── EXO_M2_F05_PRODUCTION.ipynb  ← Notebook de production
│   └── requirements.txt
├── IN_RAW_FRAMES/     ← Déposer frames EXR/PNG/TIFF (de M2_F04)
├── IN_SOURCE_REF/     ← Déposer vidéo source .mp4/.mov (optionnel)
├── IN_PRODUCTION_PLAN/ ← Déposer PRODUCTION_PLAN.JSON
├── OUT_FINAL_FRAMES/  ← Frames fusionnées PNG 16-bit
└── OUT_REPORT/        ← m2_f05_report.json
```

## Utilisation

```bash
# Production standard (vidéo source auto-détectée dans IN_SOURCE_REF/)
python CODEBASE/EXO_M2_F05_ALCHEMIST.py \
  --production-plan IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON

# Avec preset et vidéo source explicite
python CODEBASE/EXO_M2_F05_ALCHEMIST.py \
  --production-plan IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON \
  --source-video ref.mp4 \
  --preset cinema_fusion

# Bypass (frames copiées sans traitement)
python CODEBASE/EXO_M2_F05_ALCHEMIST.py \
  --production-plan IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON \
  --bypass

# Dry-run (validation sans traitement)
python CODEBASE/EXO_M2_F05_ALCHEMIST.py \
  --production-plan IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON \
  --dry-run --verbose

# Bloom seul (pas de vidéo source)
python CODEBASE/EXO_M2_F05_ALCHEMIST.py \
  --production-plan IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON \
  --skip-match --skip-grain --skip-sharpness

# Avec LUT (Mode C)
python CODEBASE/EXO_M2_F05_ALCHEMIST.py \
  --production-plan IN_PRODUCTION_PLAN/PRODUCTION_PLAN.JSON \
  --lut /path/to/cinematic_cold.cube \
  --lut-intensity 0.8
```

## Pipeline

```
Render Frame ─┬─► [1] Match Color ──► [2] Grain ──► [3] Bloom ──► [4] Sharpness ──► PNG 16-bit
              │         ▲                  ▲                             ▲
Source Vidéo ─┼─► histogrammes ref   grain stats                  source frame
              └──────────────────────────────────────────────────────────┘
```

Si pas de vidéo source : seul bloom est actif (match_color, grain, sharpness désactivés automatiquement).

## Presets

| Preset | Description |
|--------|-------------|
| `cinema_fusion` | Look standard — fusion invisible (défaut) |
| `subtle_blend` | Fusion légère — garde l'identité CG |
| `neon_blast` | Style cyberpunk — bloom agressif |
| `raw_match` | Match Color pur |
| `full_nuke` | Tout à fond |

## Différences vs Mode 1 (05_ALCHEMIST_LAB)

| Aspect | Mode 1 | Mode 2 |
|--------|--------|--------|
| Phantom Link | Actif | Supprimé (R-01) |
| drive-root | Requis | Supprimé |
| Chemins | drive_root / "05_ALCHEMIST_LAB" | FREGATE_DIR relatif |
| Auto-détection vidéo | Non | Oui (IN_SOURCE_REF/) |
| Rapport | alchemist_report.json | m2_f05_report.json |
| Version | 2.0.0 | 1.0.0 |
