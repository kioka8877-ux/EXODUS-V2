# EXODUS V2 — RISKS (Analyse Forensique)

## RISQUES CRITIQUES

### R1 — VRAM Colab T4 (15GB limit)
- **Unités touchées** : U00 (DepthAnything + SAM séquentiels), U01 (Blender headless), U06 (RIFE)
- **Probabilité** : MOYENNE (réduite grâce au protocole séquentiel)
- **Impact** : OOM crash, perte du runtime Colab
- **Mitigation** :
  - Exécution séquentielle obligatoire : Depth → flush → SAM → flush (jamais simultanés)
  - Protocole de flush : `del model` → `gc.collect()` → `torch.cuda.empty_cache()` → vérification < 0.5 GB
  - VRAM peak cible : ~4 GB (27% de la capacité T4)
  - Inférence en `float16` et `torch.no_grad()` systématique
  - Mode `--rerun` en cas d'OOM partiel (relance sans perdre les outputs précédents)

### R2 — Quotas API Gemini
- **Unités touchées** : U00 (analyse vidéo), U01 (si fallback Gemini)
- **Probabilité** : MOYENNE
- **Impact** : Rate limiting, blocage pipeline
- **Mitigation** : Retry avec exponential backoff, cache des résultats, quota monitoring

### R3 — Temps de rendu RIFE sur T4
- **Unités touchées** : U06
- **Probabilité** : MOYENNE (réduite grâce au batch par chunks)
- **Impact** : 60s vidéo → estimation 20-40 min grâce au pipeline fusionné RIFE+Upscale
- **Mitigation** : Batch 10s, checkpoint system (reprise après crash), pipeline frame-based (zéro décodage intermédiaire)

### R4 — Shadowban Google Colab
- **Probabilité** : MOYENNE
- **Impact** : Perte accès GPU pendant 24-48h
- **Mitigation** : Rotation de comptes, sessions < 8h, pas de boucles infinies

### R5 — Stabilité DepthAnything V2 sur séquences vidéo
- **Probabilité** : MOYENNE
- **Impact** : Flickering des depth maps entre frames, mesh instable en U03
- **Mitigation** : Temporal smoothing, médiane sur 3 frames consécutives

### R6 — Qualité SAM sur scènes Roblox/Brookhaven
- **Probabilité** : MOYENNE
- **Impact** : Mauvaise segmentation des surfaces → PBR Swap incorrect
- **Mitigation** : Prompts spécifiques pour SAM, validation manuelle des masques critiques

### R7 — Transferts manuels (facteur humain)
- **Probabilité** : HAUTE
- **Impact** : Fichiers manquants/corrompus entre frégates, rendus gaspillés
- **Mitigation** : MARSHAL module (Out-Check + In-Check obligatoires)

### R8 — Disponibilité SVT-AV1 sur Colab
- **Probabilité** : MOYENNE
- **Impact** : Codec AV1 potentiellement absent du FFmpeg Colab → fallback H.265
- **Mitigation** : Fallback automatique vers libx265 --tune animation. Vérification au démarrage du pipeline.

---

## MATRICE DE RISQUES PAR FRÉGATE

| Unité | R1 (VRAM) | R2 (Gemini) | R3 (RIFE) | R4 (Colab) | R5 (Depth) | R6 (SAM) | R7 (Transfert) | R8 (AV1) |
|-------|-----------|-------------|-----------|------------|------------|----------|-----------------|----------|
| U00 | 🔴 | 🔴 | ⬜ | 🟡 | 🔴 | 🔴 | 🟡 | ⬜ |
| U01 | 🟡 | 🟡 | ⬜ | 🟡 | ⬜ | ⬜ | 🟡 | ⬜ |
| U02 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | 🟡 | ⬜ |
| U03 | 🟡 | ⬜ | ⬜ | 🟡 | 🔴 | 🔴 | 🟡 | ⬜ |
| U04 | ⬜ | ⬜ | ⬜ | 🟡 | ⬜ | ⬜ | 🟡 | ⬜ |
| U05 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | 🟡 | ⬜ |
| U06 | 🔴 | ⬜ | 🟡 | 🟡 | ⬜ | ⬜ | 🟡 | 🟡 |
| MARSHAL | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

**Légende** : 🔴 Critique | 🟡 Modéré | ⬜ Non concerné

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Arsenal et specs techniques
- [ROADMAP](./EXODUS_V2_ROADMAP.md) — Phases de mitigation
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères d'acceptation

<!-- v2.1 — Post-Mutation Alignement -->
