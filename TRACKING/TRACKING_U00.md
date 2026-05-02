# TRACKING – U00 CORTEX HQ (Le Cerveau)

## 1. OBJECTIF DE LA MUTATION (V2)
Implémenter les 6 moteurs d'extraction parallèles (Gemini, T2M, Facial JSON, DepthAnything V2, SAM, FOV/Ratio).
Coordonner via EXO_00_CORTEX.py. Générer le PRODUCTION_PLAN.JSON qui orchestre l'empire.
Extraire TOUTES les données nécessaires aux frégates en aval en une seule passe.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Seul le moteur Gemini existe. 5 moteurs manquants. Outputs manquants : `motion_synthesis_prompt.txt`, `facial_animation.json`, `DEPTH_MAP/`, `semantic_masks.json`, `camera_fov_ratio`, `audio_source.wav`
- **Goulot d'étranglement** : DepthAnything V2 + SAM simultanés sur T4 (VRAM limit 15GB)
- **Risque VRAM/RAM** : ÉLEVÉ — DepthAnything (~4GB) + SAM (~3GB) = ~7GB, plus Gemini API overhead
- **Architecture cible** : 6 moteurs séquentiels (CPU → API → GPU-A → GPU-B)
- **VRAM peak cible** : 4 GB (séquentiel avec flush, jamais 2 modèles simultanés)

## 3. PLAN D'ACTION (BACKLOG)

### Phase 1 — CPU (VRAM = 0 GB)
- [x] M2 : Extraction audio via FFmpeg (`-vn -acodec pcm_s16le`) → `audio_source.wav` → PR #15
- [x] M3 : Extraction FOV/ratio via OpenCV (résolution, aspect ratio, focale estimée) → `camera_fov_ratio.json` → PR #15

### Phase 2 — API (VRAM = 0 GB)
- [x] M1 : Enrichir le prompt Gemini pour générer le Master JSON monolithique (3 blocs : `production_plan`, `facial_animation`, `motion_synthesis`) → PR #15
- [x] M1 : Implémenter le `response_schema` avec enum verrouillé (Arsenal Impérial) → PR #15
- [x] M1 : Implémenter le Dispatcher (Master JSON → 3 fichiers : `PRODUCTION_PLAN.JSON`, `facial_animation.json`, `motion_synthesis_prompt.txt`) → PR #15
- [x] M1 : Implémenter `normalize_timecodes()` (clamper segments faciaux sur bornes scène) → PR #15
- [x] M1 : Implémenter `validate_structure()` + `validate_completeness()` (3 niveaux de validation) → PR #15

### Phase 3 — GPU Moteur A (VRAM peak ~3.5 GB)
- [x] M6 : Intégrer DepthAnything V2 (chargement → inférence par frame → `DEPTH_MAP/*.png`) → PR #16
- [x] M6 : Implémenter protocole de destruction (del model → gc.collect → torch.cuda.empty_cache → vérification VRAM < 0.5 GB) → PR #16
  - Prérequis : Modèle `depth_anything_v2_vitl.pth` téléchargé dans `EXODUS_AI_MODELS/DEPTH_ANYTHING/`

### Phase 4 — GPU Moteur B (VRAM peak ~4 GB)
- [x] M7 : Intégrer SAM vit_h (vérifier VRAM dispo ≥ 3GB → chargement → segmentation keyframes → classification masques) → PR #16
- [x] M7 : Implémenter protocole de destruction identique à Phase 3 → PR #16
  - Prérequis : Modèle `sam_vit_h.pth` téléchargé dans `EXODUS_AI_MODELS/SAM/`

### Transverse
- [x] Implémenter `MotorStatus` (suivi par moteur : success/failed/partial) + `flags` dans le JSON → PR #15
- [x] Implémenter mode `--rerun <motor_name>` (relance un seul moteur sans retoucher le JSON Gemini) → PR #15
- [x] Implémenter log VRAM (`vram_log.txt`) avec peak par moteur → PR #16
- [x] Passer MARSHAL Out-Check (`python EXO_MARSHAL.py --unit U00 --mode check-out`) → PR #16

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-02-26 | Hexalogie documentaire v2.1 | ✅ | PR #14 (cdd617c) | — |
| 2026-02-26 | Orchestrateur + Moteurs CPU/API (M1-M5) | ✅ | PR #15 (9a22a2e) | — |
| 2026-02-26 | Moteurs GPU (M6-M7) + Marshal invocation | ✅ | PR #16 (f63150f) | — |

## 5. MÉTRIQUES ET VALIDATION

### Consommation VRAM par Moteur
| Moteur | VRAM Peak Cible | VRAM Peak Mesuré | RAM Peak | Durée (10s vidéo) |
|--------|----------------|-----------------|----------|-------------------|
| M1 Gemini API | 0 GB (cloud) | — | ~200 MB | 15-30s |
| M2 FFmpeg Audio | 0 GB (CPU) | — | ~100 MB | 2s |
| M3 OpenCV FOV | 0 GB (CPU) | — | ~300 MB | 1s |
| M6 DepthAnything V2 | ~3.5 GB | — | ~2 GB | 45-90s |
| M7 SAM vit_h | ~4.0 GB | — | ~2.5 GB | 60-120s |

### Critères de Validation
- [x] VRAM peak global < 5 GB (implémenté — peak cible 4 GB)
- [x] Flush GPU vérifié entre Phase 3 et Phase 4
- [x] `flags.all_motors_ok` implémenté
- [x] `--rerun` fonctionne
- [x] Marshal Out-Check implémenté (invocation automatique)
- [ ] Validation Souveraine (reste à faire — test Colab par l'Empereur)

## 6. RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U00
- [PRD — Schéma Master JSON](./EXODUS_V2_PRD.md#schémas-json-de-référence) — Master JSON V2, enums, impact par frégate
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U00
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM), R2 (Gemini), R5 (Depth), R6 (SAM)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.

---

## 7. DÉCRETS IMPÉRIAUX — CODEX v6 (23.04.2026)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx | Statut fregate : EN MUTATION

| # | Décret | Description | Priorité | Complexité | Statut |
|---|--------|-------------|----------|------------|--------|
| D-I | Arsenal externe | Extraire IMPERIAL_ARSENAL vers arsenal.json dynamique — L'Empereur modifie l'arsenal sans ouvrir le code | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-II | Mode --skip-gpu | Flag CLI : si activé, bypasse Phase 3 (DepthAnything) + Phase 4 (SAM) → PRODUCTION_PLAN.JSON sans depth/seg | MOYENNE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-III | Validation JSON Gemini | Schéma strict sur le JSON Gemini avant écriture + retry automatique max 3 tentatives + erreur explicite | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| D-IV | Architecture duale API / Injection | Cellule 0 : MODE="api"\|"injection". Cellule 2 : Gemini API (mode api). Cellule 2b : Widget JSON + métaprompt (mode injection). Convergence : dispatch_master_json(). Phases GPU identiques dans les deux modes | HAUTE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |

**Architecture duale cible (Codex v6) :**
```
Cellule 0  → Choix du mode (MODE = "api" | "injection")
Cellule 1  → Pre-flight + M2 Audio + M3 FOV (commun)
Cellule 2  → M1 Gemini API (mode api seulement)
Cellule 2b → Widget injection JSON + validation schéma (mode injection)
Cellule 3  → M6 Depth + M7 SAM + flags finaux (commun)
```

**Avantage Mode Injection :** Gemini 2.5 Pro Chat surpasse les modèles API gratuits pour analyse vidéo complexe.

<!-- v3.0 — Codex Imperial v6 — 23.04.2026 -->
<!-- v2.1 — Post-Mutation Alignement -->

## 8. REGISTRE DE FORGE — PHASE 6

| Date | Action | Statut | Fichiers modifiés |
|------|--------|--------|-------------------|
| 2026-04-23 | D-I Arsenal externe | ✅ | `00_CORTEX_HQ/arsenal.json` (NEW), `EXO_00_CORTEX.py` (load_arsenal / reload_arsenal_from_drive / _build_arsenal_enums) |
| 2026-04-23 | D-II --skip-gpu | ✅ | `EXO_00_CORTEX.py` (argparse + run_pipeline wrapping phases 3+4) |
| 2026-04-23 | D-III Validation JSON Gemini | ✅ | `EXO_00_CORTEX.py` (validate_structure intégrée dans call_gemini_v2 retry loop) |
| 2026-04-23 | D-IV Architecture duale | ✅ | `EXO_00_CORTEX_PRODUCTION.ipynb` (refonte 7 cellules), `GEMINI_CHAT_METAPROMPT.md` (NEW) |

<!-- v4.0 — Phase 6 Codex Imperial v6 — 4/4 décrets implémentés — 23.04.2026 -->

---

## 9. DÉCRETS — CODEX BRAINSTORM v1 (01.05.2026)

> Source : EXODUS_V2_CODEX_BRAINSTORM_v1.docx | Loi du Levier — Session 01.05.2026

### Contexte
DECRET III du CODEX BRAINSTORM v1 (conditionnel, lie a U03) :
"Les modules DepthAnything V2 et SAM de U00 devront etre evalues lors de l'analyse de U00.
Si aucune autre fregate ne les consomme, ils seront supprimes."

Etat au 02.05.2026 : l'analyse de U00 n'est pas encore close dans ce CODEX (verdict "A ANALYSER").
Le present decret est donc partiellement anticipe sous la forme d'un flag --glb-mode.

### Logique du flag --glb-mode
Quand U03 tourne en mode GLB (decor fourni par Tripo AI / Meshy AI) :
- Couche B (Displacement Mesh) de U03 ne consomme plus les depth maps de M6 (DepthAnything)
- Couche C (PBR Swap) de U03 ne consomme plus les masques semantiques de M7 (SAM)
- Executer M6 et M7 serait du temps GPU gaspille (M6 ~45-90s, M7 ~60-120s sur T4)

Le flag --glb-mode signale a U00 que le pipeline en aval est en mode GLB
et met automatiquement M6 et M7 en stase (equivalentea --skip-gpu mais semantiquement explicite).

### Difference avec --skip-gpu existant
| Flag | Semantique | Effet |
|------|-----------|-------|
| --skip-gpu | Bypass GPU pour raisons techniques (VRAM, tests rapides) | Skip M6 + M7 |
| --glb-mode | Le decor vient d'un service externe GLB — M6/M7 inutiles | Skip M6 + M7 + tag explicite dans le rapport |

--glb-mode est une stase semantique : le rapport indique que M6/M7 sont en stase par choix architectural, pas par contrainte technique.

### Ce qui est MIS EN STASE en mode --glb-mode
| Moteur | Phase | Raison |
|--------|-------|--------|
| M6 DepthAnything V2 | Phase 3 GPU-A | Depth maps uniquement utilisees par Couche B U03 (en stase) |
| M7 SAM vit_h | Phase 4 GPU-B | Masques semantiques uniquement utilises par Couche C U03 (en stase) |

### Plan d'implementation — Phase 7 (CODEX BRAINSTORM v1)

#### E7-A — Flag --glb-mode dans EXO_00_CORTEX.py
- [ ] Ajouter --glb-mode au parser argparse (bool flag, defaut False)
- [ ] Dans run_pipeline() : si --glb-mode actif, skip Phase 3 (M6) et Phase 4 (M7)
  - Meme comportement que --skip-gpu mais avec statut "STASE_GLB" au lieu de "SKIPPED"
  - motor_status.mark_failed("depth_anything", "STASE_GLB — mode GLB actif, depth maps non requises")
  - motor_status.mark_failed("sam_segmentation", "STASE_GLB — mode GLB actif, masques SAM non requis")
- [ ] Ajouter dans le rapport final : "glb_mode": true et "tri_layer_consumers_in_stasis": ["depth_anything", "sam"]
- [ ] --glb-mode et --skip-gpu peuvent coexister (--glb-mode prend priorite sur M6+M7)
- [ ] Mettre a jour la version CORTEX -> 4.1.0 (ou version courante +0.1)

#### E7-B — Documentation inline
- [ ] Commentaire dans EXO_00_CORTEX.py au-dessus de la Phase 3 :
  "# STASE conditionnelle : si --glb-mode, M6 non execute (depth maps non consommees par U03 GLB)"
- [ ] Commentaire dans EXO_00_CORTEX.py au-dessus de la Phase 4 :
  "# STASE conditionnelle : si --glb-mode, M7 non execute (masques SAM non consommes par U03 GLB)"

### Registre de Forge — Phase E7
| Date | Action | Statut | Fichiers modifies |
|------|--------|--------|-------------------|
| 02.05.2026 | E7 documente dans TRACKING_U00.md | OK | TRACKING_U00.md |
| 02.05.2026 | E7-A — Flag --glb-mode EXO_00_CORTEX.py v4.1.0 | ✅ IMPLÉMENTÉ | EXO_00_CORTEX.py |
| 02.05.2026 | E7-B — Commentaires inline stase conditionnelle | ✅ IMPLÉMENTÉ | EXO_00_CORTEX.py |

### Criteres de validation Phase E7
- [x] python EXO_00_CORTEX.py --help : --glb-mode present dans l'aide
- [ ] python EXO_00_CORTEX.py --drive-root X --input-video Y --glb-mode --dry-run : valide sans erreur
- [x] Rapport JSON final : "glb_mode": true, moteurs M6+M7 marques STASE_GLB
- [x] Sans --glb-mode : comportement identique a avant (M6 et M7 s'executent normalement)
- [x] --glb-mode + --skip-gpu ensemble : M6/M7 en stase (pas de crash, pas de doublon)

### Note sur DECRET III CODEX BRAINSTORM v1 (conditionnel)
Le DECRET III original dit : "si aucune autre fregate ne consomme M6/M7, ils seront supprimes".
Au 02.05.2026 : seule U03 consommait M6/M7 (Couche B + C). Aucune autre fregate ne les utilise.
Verdict conditionnel : si le run E2E confirme que le mode GLB est le chemin principal,
M6 et M7 pourront etre supprimes definitivement lors de la prochaine session CODEX.
Pour l'instant : stase via --glb-mode, suppression reportee apres validation E2E.

<!-- v5.2 — CODEX BRAINSTORM v1 — E7-A + E7-B implementees — Phase E7 SCELLÉE — 02.05.2026 -->

---

## 10. DÉCRET V — BLOC actors_placement (SESSION_STATE Codex v4 — 02.05.2026)

> Source : EXODUS_V2_SESSION_STATE.md | Consomme exclusivement par F03 SCENOGRAPHY DOCK

### Objectif
Gemini analyse la video et estime les positions relatives des acteurs dans chaque scene.
Le bloc `actors_placement` est ecrit dans PRODUCTION_PLAN.JSON et consomme par F03
pour positionner les avatars Roblox dans le decor 3D.

### Format cible (par scene)
```json
"actors_placement": [
  { "avatar_id": 0, "position": [0.0, 0.0, 0.0], "facing_target": 1 },
  { "avatar_id": 1, "position": [1.5, 0.0, 0.0], "facing_target": 0 }
]
```
- `avatar_id` : index 0-based de l'avatar dans la scene
- `position` : [x, y, z] en coordonnees Blender relatives (origine = centre scene au sol)
- `facing_target` : avatar_id de la cible, ou -1 si face cam / avatar isole

### Plan d'implementation — Phase E8

#### E8-A — actors_placement dans RESPONSE_SCHEMA
- [x] Ajouter `actors_placement` comme propriete de chaque scene dans RESPONSE_SCHEMA
- [x] Schema : array de {avatar_id: integer, position: [number, number, number], facing_target: integer}
- [x] Champ requis dans la liste `required` de chaque scene

#### E8-B — Instructions dans MASTER_PROMPT
- [x] Ajouter consigne 8 dans MASTER_PROMPT : instructions detaillees pour actors_placement
- [x] Exemples concrets : face-a-face, cote-a-cote, monologue face cam
- [x] facing_target=-1 documente comme convention pour face cam / avatar isole
- [x] BLOC 1 description mise a jour pour mentionner actors_placement

#### E8-C — Validation dans validate_structure()
- [x] actors_placement ajoute dans la liste des champs requis par scene
- [x] Validation : tableau obligatoire, entrees [avatar_id, position, facing_target]
- [x] position validee comme [x, y, z] exactement 3 nombres

### Registre de Forge — Phase E8
| Date | Action | Statut | Fichiers modifies |
|------|--------|--------|-------------------|
| 02.05.2026 | E8-A — actors_placement dans RESPONSE_SCHEMA | ✅ IMPLÉMENTÉ | EXO_00_CORTEX.py |
| 02.05.2026 | E8-B — Instructions Gemini dans MASTER_PROMPT | ✅ IMPLÉMENTÉ | EXO_00_CORTEX.py |
| 02.05.2026 | E8-C — Validation dans validate_structure() | ✅ IMPLÉMENTÉ | EXO_00_CORTEX.py |
| 02.05.2026 | E8-D — Documentation DECRET V TRACKING_U00.md | ✅ IMPLÉMENTÉ | TRACKING_U00.md |

### Criteres de validation Phase E8
- [x] RESPONSE_SCHEMA : actors_placement dans required de chaque scene
- [x] MASTER_PROMPT : consigne 8 presente avec exemples
- [x] validate_structure() : erreur si actors_placement absent ou mal forme
- [ ] Test injection : JSON avec actors_placement valide → dispatch sans erreur
- [ ] Test injection : JSON sans actors_placement → validate_structure() retourne erreur explicite
- [ ] Run Gemini : actors_placement present dans le JSON genere automatiquement

### Note
Precision centimetrique non requise pour contenu Roblox stylise.
L'estimation visuelle de Gemini est suffisante pour le positionnement dans F03.

<!-- v6.0 — DECRET V actors_placement — Phase E8 SCELLÉE — 02.05.2026 -->
