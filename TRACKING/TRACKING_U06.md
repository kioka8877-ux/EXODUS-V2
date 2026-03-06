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
- [ ] Créer `carrier_schema.py` (Bible du Vaisseau-Mère — 6 piliers + self_test)
- [ ] Pilier 1 : Constantes canoniques (ratios valides, CRF range 16-22, FPS cibles, poids cibles)
- [ ] Pilier 2 : Format metadata parser (lit format.resolution array, format.ratio, format.fps_source)
- [ ] Pilier 3 : Encoding presets (distribution AV1, distribution_h265 fallback, master ProRes)
- [ ] Pilier 4 : RIFE config (batch 10s, VRAM budget <10GB, fallback chain)
- [ ] Pilier 5 : Upscale config (scale factor, model candidates, fallback chain)
- [ ] Pilier 6 : Validation + self_test (validate_ratio, validate_crf, validate_output_weight, checksum_resolution)

### Phase B — Pipeline Frame-Based
- [ ] Refactor sequence_assembler.py → Frame Indexer (valide + trie + manifeste, ZÉRO FFmpeg)
- [ ] Refactor rife_interpolator.py → Chunk-based frame-to-frame (lit PNG direct, batch 10s, checkpoint)
- [ ] Refactor upscaler.py → Chunk-based frame-to-frame (fusionné avec RIFE dans le pipeline)
- [ ] Refactor final_encoder.py → Encode unique depuis frames PNG (AV1 + H.265 tune animation + ProRes)
- [ ] Refactor EXO_06_CARRIER.py → Orchestrateur V2 (preset CLI, checkpoint, progress, frame pipeline)

### Phase C — Finition
- [ ] Mettre à jour requirements.txt (ajouter svt-av1 optionnel)
- [ ] Mettre à jour EXO_06_CONTROL.ipynb et EXO_06_PRODUCTION.ipynb
- [ ] Mettre à jour README_DEV.md et UNIT_06_SUBPLAN.md

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| | | | | |

## 5. MÉTRIQUES ET VALIDATION
- Compressions lossy intermédiaires : cible 0 (actuellement 4)
- Pic disque temporaire : cible <5GB (actuellement ~50GB)
- Poids livrable 60s distribution : cible 200-400MB (actuellement ~1.5GB)
- VRAM peak RIFE : cible <10GB (T4 safe)
- Temps pipeline 60s vidéo sur T4 : à mesurer
- [ ] carrier_schema.py self_test passé
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U06
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U06
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM RIFE), R3 (temps rendu), R8 (AV1 Colab)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
