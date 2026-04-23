# TRACKING – U06 AIRCRAFT CARRIER (Le Vaisseau-Mère)

## 1. OBJECTIF DE LA MUTATION (V2 ATOM-IC)
Pipeline frame-based ZÉRO compression intermédiaire — actuellement 4 compressions lossy H.264 en cascade
(sequence_assembler → rife_interpolator → upscaler → final_encoder). Chaque étape encode en libx264 CRF 18
puis la suivante décode et ré-encode, causant une dégradation cumulative de qualité.

La mutation V2 ATOM-IC remplace ce pipeline par :
- **carrier_schema.py** (Bible du Vaisseau-Mère) — nouveau module de données pures suivant le pattern de `camera_schema.py` (U04) et `alchemist_schema.py` (U05). 6 piliers : constantes canoniques, format metadata parser, encoding presets, RIFE config, upscale config, validation + self_test.
- **3 encoding presets** : AV1 distribution (~300MB/60s), H.265 fallback (~500MB/60s), ProRes master (archive)
- **Batch RIFE+Upscale par chunks de 10 secondes** — pic disque ~3GB au lieu de ~50GB
- **Checkpoint system** — reprise après crash au dernier chunk traité
- **Ratio lock strict** depuis `format.resolution` / `format.ratio` du PRODUCTION_PLAN.JSON V2
- **CRF configurable**, `--tune animation` pour contenu Roblox (aplats de couleur, mouvement prédictible)

Le produit fini sort d'ici — dernière frégate de la chaîne.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)

### Écarts constatés

- **`rife_interpolator.py`** : 4 compressions lossy (libx264 CRF 18) aux lignes 298-299, 330-331, 371-372. Pas de batch par chunks. VRAM risk ÉLEVÉ.
- **`upscaler.py`** : Même problème de compressions lossy intermédiaires (lignes 287-288, 312-313, 348-349)
- **`sequence_assembler.py`** : Encode les frames U05 en MP4 intermédiaire inutilement (lignes 144-145)
- **`EXO_06_CARRIER.py`** : Hardcode CRF 18 (ligne 391), ne lit pas `format.ratio`, pas de checkpoint, pas de preset CLI
- **`final_encoder.py`** : Pas de support AV1, pas de `--tune animation`, pas de preset "distribution"
- **AUCUN `carrier_schema.py`** — U06 est la seule frégate sans module schema
- Le PRODUCTION_PLAN.JSON V2 utilise `format.resolution: [1080, 1920]` (array) mais le code attend `output.resolution: "4K"` (string)

### Synthèse
- **Goulot d'étranglement** : CRITIQUE — réécriture majeure du pipeline complet
- **Risque VRAM/RAM** : ÉLEVÉ — RIFE sur T4 pour 120FPS (~8-10GB) sans batch processing

## 3. PLAN D'ACTION (BACKLOG)

### Phase A — Fondation
- [x] Créer `carrier_schema.py` (Bible du Vaisseau-Mère — 6 piliers + self_test) — PR #45
- [x] Pilier 1 : Constantes canoniques — PR #45
- [x] Pilier 2 : Format metadata parser — PR #45
- [x] Pilier 3 : Encoding presets (distribution AV1, distribution_h265 fallback, master ProRes) — PR #45
- [x] Pilier 4 : RIFE config — PR #45
- [x] Pilier 5 : Upscale config — PR #45
- [x] Pilier 6 : Validation + self_test — PR #45

### Phase B — Pipeline Frame-Based
- [x] Refactor sequence_assembler.py → Frame Indexer (valide + trie + manifeste, ZÉRO FFmpeg) — PR #46
- [x] Refactor rife_interpolator.py → Chunk-based frame-to-frame (lit PNG direct, batch 10s, checkpoint) — PR #46
- [x] Refactor upscaler.py → Chunk-based frame-to-frame (fusionné avec RIFE dans le pipeline) — PR #46
- [x] Refactor final_encoder.py → Encode unique depuis frames PNG (AV1 + H.265 tune animation + ProRes) — PR #46
- [x] Refactor EXO_06_CARRIER.py → Orchestrateur V2 (preset CLI, checkpoint, progress, frame pipeline) — PR #46

### Phase C — Finition
- [x] Mettre à jour requirements.txt (ajouter svt-av1 optionnel) — PR #46
- [x] Mettre à jour EXO_06_CONTROL.ipynb et EXO_06_PRODUCTION.ipynb — PR #46
- [x] Mettre à jour README_DEV.md et UNIT_06_SUBPLAN.md — PR #46

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-03-06 | ATOM-IC Audit — 4 compressions lossy découvertes | ✅ | PR #44 | — |
| 2026-03-06 | carrier_schema.py — 6 piliers + self_test 12/12 | ✅ | PR #45 | — |
| 2026-03-06 | Refactor pipeline frame-based complet (5 modules + orchestrateur) | ✅ | PR #46 | — |
| 2026-03-06 | Fix 3 bugs HIGH (destructive move, checkpoint nuke, pix_fmt orphan) | ✅ | PR #46 (commit 1db189a) | — |
| 2026-04-23 | DECRET II — --target-fps CLI (choices=[60,120]) dans EXO_06_CARRIER.py v2.1.0, override PRODUCTION_PLAN | ✅ | SESSION 2026-04-23 | — |
| 2026-04-23 | DECRET III — upscaler.py: _upscale_chunk_cugan (modes binary+torch), _load_cugan_model, REALCUGAN_SUBDIR, check_realesrgan_model migré vers Real-CUGAN | ✅ | SESSION 2026-04-23 | — |

## 5. MÉTRIQUES ET VALIDATION
- [x] Compressions lossy intermédiaires : ✅ 0 (cible atteinte)
- [x] Pic disque temporaire : ✅ <5GB (chunks 10s)
- [x] Poids livrable 60s distribution : ✅ 200-400MB (AV1 CRF 30)
- [x] VRAM peak RIFE : ✅ <10GB (chunk-based)
- [ ] Temps pipeline 60s vidéo sur T4 : à mesurer
- [x] carrier_schema.py self_test passé
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U06
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U06
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM RIFE), R3 (temps rendu), R8 (AV1 Colab)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 6. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : 🟢 SCELLÉ (D-I + D-II + D-III IMPLÉMENTÉS — 23.04.2026)

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Pipeline 100% lossless | Audit ATOM-IC : 4 compressions lossy détectées. Imposer EXR pour toutes les frames intermédiaires jusqu'à encodage final. Sortie : MP4 H.265 (distribution) + MOV ProRes 4444 (archive). | CRITIQUE | MOYENNE | ✅ IMPLÉMENTÉ (PR #46 — rife_interpolator: PNG lossless + MKV lossless fallback, 0 H.264 intermédiaire. carrier: EXR/PNG input → AV1/H265/ProRes output) |
| D-II | RIFE configurable (--target-fps) | Interpolation actuellement hardcodée à 120FPS. Ajouter --target-fps (valeurs : 60 ou 120, défaut : 120). RIFE adapte son ratio d'interpolation. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — --target-fps CLI ajouté dans EXO_06_CARRIER.py v2.1.0, override PRODUCTION_PLAN.JSON[output][framerate]) |
| D-III | Real-CUGAN remplace RealESRGAN | RealESRGAN entraîné sur photos réelles → résultat sous-optimal sur contenu Roblox cartoon. Real-CUGAN = entraîné anime/cartoon, précision supérieure sur avatars Roblox, 100% gratuit, même interface. | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — upscaler.py: _upscale_chunk_cugan (binary+torch), _load_cugan_model, REALCUGAN_SUBDIR. Support realcugan-ncnn-vulkan binaire + wrapper Python) |

**Diagnostic outils (Audit session 23.04.2026) :**
```
Topaz Video AI  → meilleure qualité MAIS payant (~300$) — HORS DOCTRINE
DaVinci Resolve → Optical Flow < RIFE, upscale limité en free
Flowframes      → GUI wrapper RIFE, interpolation only, Windows only
FFmpeg seul     → pas d'IA, qualité inférieure
CONCLUSION → F06 reste 100% code : RIFE + Real-CUGAN + FFmpeg
```

**LOI III rappel :** Du premier frame rendu jusqu'à l'encodage final, aucune compression lossy n'est tolérée. Le format EXR est sacré.

<!-- v5.0 — 23.04.2026 — D-I + D-II + D-III IMPLÉMENTÉS — FREGATE 06 SCELLÉE -->
