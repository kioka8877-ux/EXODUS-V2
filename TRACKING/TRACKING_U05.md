# TRACKING – U05 ALCHEMIST LAB (Le Philtre)

## 1. OBJECTIF DE LA MUTATION (V2) — SCELLÉE 2026-04-23
Fusion visuelle totale entre le rendu 3D (U04) et la vidéo source (U00).
L'avatar Roblox doit être indistinguable de la vidéo. 4 transformations mathématiques :
Match Color (histogramme LAB), Film Grain matching (extraction grain source),
Bloom/Glow bleed, Sharpness transfer. + LUT .cube optionnel (Mode C).

**Shift V1 → V2** : Blender Compositor + LUTs → **OpenCV + Pillow** (CPU pur, zéro Blender).

**Architecture** : Bible-first (alchemist_schema.py) + 4 modules OpenCV + orchestrateur CLI + LUT engine numpy.

**3 Modes validés (session 2026-04-23) :**
- Mode A — Bypass (`--bypass`) : transit direct F04 → F06, aucun traitement
- Mode B — DaVinci Resolve : grade manuel hors EXODUS (outil externe gratuit)
- Mode C — Python LUT (`--lut`) : `lut_engine.py` + interpolation trilinéaire numpy

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : `color_grader.py` utilise des LUTs au lieu du Match Color par histogramme. Pas de grain matching. `effects_forge.py` manque bloom/glow spécifique. Tout le pipeline est Blender-dépendant.
- **Goulot d'étranglement** : AUCUN — traitement CPU ~1s/frame (100× plus rapide que U04-B)
- **Risque VRAM/RAM** : NUL — 1.5 GB RAM peak sur 12 GB Colab T4

## 3. PLAN D'ACTION (BACKLOG)

### Task A — Bible Alchimique ✅ (PR #38)
- [x] `alchemist_schema.py` — 7 piliers, 5 pipeline presets, classe AlchemistSchema, self_test 8/8
- [x] Dossier `IN_SOURCE_REF/` créé (.gitkeep)

### Task B — Match Color + Grain Matcher ✅ (PR #40)
- [x] `match_color.py` — Histogram Specification en espace LAB (OpenCV)
    - Histogramme de référence par scène (anti-flicker, ~20 frames échantillonnées)
    - Blend avec intensité configurable
- [x] `grain_matcher.py` — Extraction grain source + application procédurale
    - Calibration par scène (~10 frames, bilateral filter decomposition)
    - Grain procédural calibré sur stats source (np.random.normal)

### Task C — Bloom + Sharpness + Orchestrateur CLI + Docs ✅ (PR #41)
- [x] `bloom_engine.py` — Luminance threshold → Gaussian blur → additive blend
- [x] `sharpness_transfer.py` — Laplacian variance matching + Gaussian blur/unsharp mask
- [x] Rewrite `EXO_05_ALCHEMIST.py` v2.0.0 — Pipeline OpenCV, CLI avec --preset, extraction frames source via cv2.VideoCapture
- [x] Mise à jour `requirements.txt` (numpy, opencv-python-headless, Pillow, tqdm)
- [x] Mise à jour `README_DEV.md`
- [x] Mise à jour `UNIT_05_SUBPLAN.md`

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-03-06 | alchemist_schema.py (Bible Alchimique, 479 lignes, self_test 8/8) + IN_SOURCE_REF/ | 🟢 | PR #38 | N/A (Python pur) |
| 2026-03-06 | match_color.py (305 lignes, histogram LAB) + grain_matcher.py (317 lignes, bilateral decomposition) | 🟢 | PR #40 | N/A (CPU) |
| 2026-03-06 | bloom_engine.py + sharpness_transfer.py + EXO_05_ALCHEMIST.py v2.0.0 + requirements.txt + README_DEV.md + UNIT_05_SUBPLAN.md | 🟢 | PR #41 | N/A (CPU) |
| 2026-04-23 | lut_engine.py (LUT .cube 3D, trilineaire numpy) + LUTS/MANIFEST.json + --bypass flag + --lut/--lut-intensity dans EXO_05_ALCHEMIST.py — DECRETS I/II/III valides en session | 🟢 | SESSION 2026-04-23 | N/A (CPU) |
| 2026-04-23 | DECRET IV — LUTEngine.apply_colour_science() + is_colour_science_available() dans lut_engine.py. --use-colour-science flag + wiring EXR-natif dans EXO_05_ALCHEMIST.py. requirements.txt: colour-science + imageio. | 🟢 | SESSION 2026-04-23 | N/A (CPU) |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (CPU processing — OpenCV + Pillow)
- RAM peak estimé : ~1.5 GB
- Temps d'exécution estimé : ~1s/frame 4K → ~15 min pour 30s vidéo
- Stockage estimé : ~32 GB (input + output) pour 30s vidéo

### Inputs
| Fichier | Format | De | Poids estimé (30s) |
|---------|--------|----|--------------------|
| raw_frames/ | .exr ou .png (Combined pass) | U04 | ~14-27 GB |
| source_video.mp4 | .mp4 | U00 | ~10-100 MB |
| PRODUCTION_PLAN.JSON | .json | U00 | ~20 KB |

### Outputs
| Fichier | Format | Vers | Poids estimé (30s) |
|---------|--------|------|--------------------|
| graded_frames/ | .png 16-bit 4K | U06 | ~13-22 GB |
| alchemist_report.json | .json | — | ~20 KB |

### Critères VALIDATION.md
- [x] Match Color par alignement histogramme (pas de LUT)
- [x] Film Grain matching (extraction du grain de la vidéo source)
- [x] Bloom/Glow bleed (hautes lumières bavent sur le décor)
- [x] Flou de transfert (avatar pas "trop net" vs grain source)
- [x] Output : .png 16 bits
- [x] lut_engine.py — LUT .cube 3D numpy (DECRET III)
- [x] LUTS/MANIFEST.json — Inventaire LUTs (DECRET I)
- [x] --bypass flag — Transit direct F04→F06 (DECRET II)
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U05
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U05
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 6. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : VALIDÉE (architecture tri-mode confirmée)

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Inventaire et versionnage LUTs | LUTS/MANIFEST.json listant chaque LUT (nom, source, version, usage). LUTs inclus dans le repo GitHub. Garantit reproductibilité des rendus. | MOYENNE | FAIBLE | ✅ VALIDÉ (session 23.04 + LUTS/MANIFEST.json) |
| D-II | Flag --bypass-grading | Si activé : frames EXR transmises directement à F06 sans traitement LUT. Utile tests rapides. Mode A = équivalent bypass F02. | FAIBLE | FAIBLE | ✅ VALIDÉ (session 23.04 + --bypass flag) |
| D-III | DaVinci Resolve (Mode B — outil externe) | Opérateur ouvre Resolve Free, importe séquence EXR, applique LUT, exporte. Lecture EXR native + export EXR/PNG 16-bit. Manuel, non scriptable. | MOYENNE | FAIBLE | ✅ VALIDÉ (session 23.04 — outil externe documenté) |
| D-IV | colour-science pour Mode C (pipeline Python) | colour-science = solution Python 100% gratuite, lit .cube nativement, écrit EXR, compatible imageio. Mode C = automatisation complète sans outil externe. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — LUTEngine.apply_colour_science() + is_colour_science_available() dans lut_engine.py, --use-colour-science flag dans EXO_05_ALCHEMIST.py + requirements.txt mis à jour) |

**Architecture tri-mode finale :**
```
MODE A : --bypass-grading → copie directe EXR vers F06
MODE B : DaVinci Resolve Free → transit manuel opérateur
MODE C : colour-science + imageio → LUT .cube → EXR (automatique)
```

<!-- v3.0 — Codex Imperial v6 — Architecture tri-mode — 23.04.2026 -->
