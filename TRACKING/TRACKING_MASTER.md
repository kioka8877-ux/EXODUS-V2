# TRACKING MASTER — Vue Impériale à 360°

## TABLEAU DE BORD GLOBAL

| # | Unité | Nom | Priorité | Conformité V2 | Statut Mutation | Bloqueur |
|---|-------|-----|----------|----------------|-----------------|----------|
| 0 | U00 | CORTEX HQ | ✅ Done | 100% | 🟢 CODEX v6 — 4/4 décrets IMPLÉMENTÉS (23.04.2026) | — |
| 1 | U01 | ANIMATION ENGINE | ✅ Done | 100% | 🟢 CODEX v6 — 4/4 décrets + SENTINEL 4 fixes + VOX tests (23.04.2026) | — |
| 2 | U02 | LOGISTICS DEPOT | ✅ Done | 100% | 🟡 CODEX v6 — 2 décrets à implémenter | — |
| 3 | U03 | SCENOGRAPHY DOCK | ✅ Done | 100% | 🟡 CODEX v6 — 3 décrets à implémenter | — |
| 4 | U04 | PHOTOGRAPHY WING | ✅ Done | 100% | 🟢 CODEX v6 — 4 décrets VALIDÉS | — |
| 5 | U05 | ALCHEMIST LAB | ✅ Done | 100% | 🟢 CODEX v6 — 4/4 décrets IMPLÉMENTÉS (23.04.2026) | — |
| 6 | U06 | AIRCRAFT CARRIER | ✅ Done | 100% | 🟢 CODEX v6 — 3/3 décrets IMPLÉMENTÉS (23.04.2026) | — |
| M | MARSHAL | L'INTENDANT | ✅ Done | 100% | 🟢 SCELLÉ (PR #12) | — |

## PROGRESSION GLOBALE
Empire EXODUS Base V2 : [████████████] 100% — Phase 5 complete — 48/48 taches
Codex Imperial v6 (Phase 6) : [████████████] 100% — 25/25 décrets IMPLÉMENTÉS — PHASE 6 SCELLÉE (23.04.2026)
Fregates conformes : 7/7 — Contrats 4/4 chacune (KRONOS audit 2026-04-03)
Tech-Pretres actifs : 6/6 (SENTINEL, VULKAN_FORGE, VOID-FLUSH, ATLAS, VOX, KRONOS)
Phase courante : PHASE 6 — FORGE DES DÉCRETS IMPÉRIAUX (Codex v6 — 23.04.2026)

## PHASE 5 — INTEGRATION FREGATES (COMPLETE)

| Tâche | Description | Statut | Date |
|-------|-------------|--------|------|
| T44 | VOID-FLUSH → U03 + U04 (blender_adapter + hook) | ✅ COMPLETE | 2026-04-03 |
| T45 | ATLAS → U03 + U04 (session_store + SessionStore) | ✅ COMPLETE | 2026-04-03 |
| T46 | VOX → U03 + U04 (RULES.md + Pytest tests) | ✅ COMPLETE | 2026-04-03 |
| T47 | KRONOS → Audit U00-U06 (7/7 contracts OK) | ✅ COMPLETE | 2026-04-03 |
| T48 | VOX → Documentation finale + commit | ✅ COMPLETE | 2026-04-03 |

## FLEET SEAL — VALIDATION END-TO-END

| Couche | Description | Statut |
|--------|-------------|--------|
| Layer 1 — Quick | Fichiers existent, taille OK | ✅ OK (KRONOS 7/7) |
| Layer 2 — Deep | JSON valides, scripts OK, formats corrects | ✅ OK (syntaxe validee) |
| Layer 3 — Cross | Phantom Links, dependances inter-fregates | ✅ OK (VOID-FLUSH + ATLAS) |

**Fleet Seal** : ✅ PHASE 5 SCELLE — EMPIRE COMPLET
Derniere frappe : Phase 5 complete — 48/48 taches — 6 Tech-Pretres — 7 Fregates integrees

## LÉGENDE
- 🔴 BLOQUÉ : Écart majeur, réécriture nécessaire
- 🟡 EN ATTENTE : Écart partiel, extension nécessaire
- 🟢 CONFORME : Prêt ou quasi-prêt V2
- P0 = Critique | P1 = Important | P2 = Normal

## LIENS
- [STATE](./EXODUS_V2_STATE.md) | [PRD](./EXODUS_V2_PRD.md) | [ROADMAP](./EXODUS_V2_ROADMAP.md)
- [VALIDATION](./EXODUS_V2_VALIDATION.md) | [RISKS](./EXODUS_V2_RISKS.md) | [TRANSFERS](./EXODUS_V2_TRANSFER_LOG.md)
- [U00](./TRACKING_U00.md) | [U01](./TRACKING_U01.md) | [U02](./TRACKING_U02.md) | [U03](./TRACKING_U03.md) | [U04](./TRACKING_U04.md) | [U05](./TRACKING_U05.md) | [U06](./TRACKING_U06.md) | [MARSHAL](./TRACKING_MARSHAL.md)

## PHASE D.1 — PHANTOM LINK (COMPLETE)
Architecture validée — ARCHITECTURE_PHANTOM_LINK.md créé.
phantom_link.py implementé et actif dans U03 + U04.

## EMPIRE EXODUS — ETAT FINAL

```
╔═══════════════════════════════════════════════════════════════╗
║  EMPIRE EXODUS — 100% — Phase 5 Complete                     ║
║  48/48 taches — 6 Tech-Pretres — 7 Fregates integrees        ║
╚═══════════════════════════════════════════════════════════════╝

Tech-Pretres :
  [V] SENTINEL    — Systeme immunitaire (8 Briques)
  [V] VULKAN_FORGE — Arsenal + Memoire persistante
  [V] VOID-FLUSH  — Purge GPU/VRAM (U03 + U04)
  [V] ATLAS       — Session store (U03 + U04)
  [V] VOX         — Rapports + Tests (U03 + U04)
  [V] KRONOS      — Audit coherence (7/7 contracts OK)

Fregates :
  [V] U00 CORTEX_HQ       — 4/4 contrats
  [V] U01 ANIMATION_ENGINE — 4/4 contrats
  [V] U02 LOGISTICS_DEPOT  — 4/4 contrats
  [V] U03 SCENOGRAPHY_DOCK — 4/4 contrats + VOID-FLUSH + ATLAS + RULES + tests
  [V] U04 PHOTOGRAPHY_WING — 4/4 contrats + VOID-FLUSH + ATLAS + RULES + tests
  [V] U05 ALCHEMIST_LAB    — 4/4 contrats
  [V] U06 AIRCRAFT_CARRIER — 4/4 contrats
```

---

## PHASE 6 — FORGE DES DÉCRETS IMPÉRIAUX (Codex v6)

> Source : EXODUS_V2_CODEX_IMPERIAL_v6.docx — Session 21-23.04.2026.M41
> Maître de Forge : Vulkan | Scribe : CAPY-01

### REGISTRE DES 20 DÉCRETS

| Frégate | Décret | Titre | Priorité | Complexité | Statut |
|---------|--------|-------|----------|------------|--------|
| U00 | D-I | Arsenal externe (arsenal.json) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U00 | D-II | Mode --skip-gpu | MOYENNE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U00 | D-III | Validation JSON Gemini (retry x3) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U00 | D-IV | Architecture duale API / Injection | HAUTE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U01 | D-I | Externalisation corps animé (outil ext.) | MOYENNE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U01 | D-II | EMOCA sur visage humain réel | MOYENNE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U01 | D-III | Lip-sync obligatoire (Rhubarb + pyannote) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U01 | D-IV | Orchestration multi-avatar (N personnages) | HAUTE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U02 | D-I | Validation pré-socketing (bones check) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U02 | D-II | Fusion socketing + timeline (actor_assembly.py) | FAIBLE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U02 | D-III | Bypass props automatique | FAIBLE | FAIBLE | ✅ VALIDÉ (session 21.04) |
| U03 | D-I | Suppression code mort D2/D3 | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U03 | D-II | Classe de base BlenderLayerBuilder | MOYENNE | MOYENNE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U03 | D-III | Stabilisation Phantom Link (racine Drive) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026) |
| U04 | D-I | Mode manuel guidé (priorité Phase 1) | HAUTE | MOYENNE | ✅ VALIDÉ |
| U04 | D-II | Notebook de production unifié | HAUTE | FAIBLE | ✅ VALIDÉ |
| U04 | D-III | Reference Frame Background (ffmpeg + Blender) | HAUTE | FAIBLE | ✅ VALIDÉ |
| U04 | D-IV | Arsenal lumineux 3-Point + HDRi Poly Haven | HAUTE | FAIBLE | ✅ VALIDÉ |
| U05 | D-I | Inventaire et versionnage LUTs (MANIFEST.json) | MOYENNE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — LUTS/MANIFEST.json + lut_engine.py) |
| U05 | D-II | Flag --bypass-grading | FAIBLE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — --bypass flag dans EXO_05_ALCHEMIST.py) |
| U05 | D-III | DaVinci Resolve comme outil externe (Mode B) | MOYENNE | FAIBLE | ✅ VALIDÉ (session) |
| U05 | D-IV | colour-science pour Mode C (pipeline Python) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — lut_engine.py apply_colour_science + --use-colour-science + requirements.txt) |
| U06 | D-I | Pipeline 100% lossless (EXR intermédiaire) | CRITIQUE | MOYENNE | ✅ IMPLÉMENTÉ (PR #46 — rife: PNG lossless + MKV lossless fallback, carrier: EXR/PNG→AV1/H265/ProRes) |
| U06 | D-II | RIFE configurable (--target-fps 60/120) | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — --target-fps CLI dans EXO_06_CARRIER.py v2.1.0, override PRODUCTION_PLAN) |
| U06 | D-III | Real-CUGAN remplace RealESRGAN | HAUTE | FAIBLE | ✅ IMPLÉMENTÉ (23.04.2026 — upscaler.py: _upscale_chunk_cugan binary+torch, _load_cugan_model, REALCUGAN_SUBDIR) |

> Compte (23.04.2026 — PHASE 6 SCELLÉE) : 25/25 IMPLÉMENTÉS/VALIDÉS — CODEX IMPERIAL v6 COMPLET

### DOCTRINE IMPÉRIALE (LOIs INVIOLABLES — Codex v6)

| Loi | Titre | Règle |
|-----|-------|-------|
| I | Isolation des Silos | Chaque Frégate lit ses IN_* et écrit ses OUT_* uniquement |
| II | Transit Manuel | L'Empereur transfère les fichiers entre Frégates. Aucun script inter-frégate |
| III | Qualité Lossless | EXR obligatoire du premier frame jusqu'à l'encodage final |
| IV | Notebook Unique | Un seul notebook de production par Frégate |
| V | Commande Unique | Chaque Frégate se lance par une seule commande CLI |

---

<!-- v6.0 — Phase 6 SCELLÉE — 25/25 décrets — 23.04.2026 -->
<!-- v4.0 — Phase 5 Complete — Empire EXODUS 100% — 2026-04-03 -->

---

## PHASE 7 — CODEX BRAINSTORM v1 (Loi du Levier)

> Source : EXODUS_V2_CODEX_BRAINSTORM_v1.docx | Session 01-02.05.2026.M41
> Maitre de Forge : Vulkan | Scribe : CAPY-01
> Loi du Levier : identifier les elements remplacables par services externes (effort min, resultat max)

### Etat du Conseil (01.05.2026)
Le Conseil a examine une seule fregate lors de la session initiale. Six restent a analyser.

| Fregate | Verdict | Service retenu | Note |
|---------|---------|----------------|------|
| U03 SCENOGRAPHY DOCK | ACTIVE (ALLEGEE ~70%) | Tripo AI / Meshy AI (GLB) | Tri-Layer -> 3 etapes si GLB fourni |
| U00 CORTEX HQ | A ANALYSER | — | DECRET III conditionnel (M6/M7 evaluation reportee) |
| U01 ANIMATION ENGINE | A ANALYSER | — | Session suivante |
| U02 LOGISTICS DEPOT | A ANALYSER | — | Session suivante |
| U04 PHOTOGRAPHY WING | A ANALYSER | — | Session suivante |
| U05 ALCHEMIST LAB | A ANALYSER | — | Session suivante |
| U06 AIRCRAFT CARRIER | A ANALYSER | — | Session suivante |

### Travaux en cours (02.05.2026)

**U03 — Phase D7 (3 taches, EN ATTENTE DE FORGE)**
- D7-A : Mode GLB dans layer_assembler.py (--glb-path + _import_glb() + branchement)
- D7-B : Pass-through --glb-path dans EXO_03_SCENOGRAPHY.py
- D7-C : Sarcophage banner sur 5 modules (dome, displacement, pbr_swap, depth_cleaner, glass)

**U00 — Phase E7 (2 taches, EN ATTENTE DE FORGE)**
- E7-A : Flag --glb-mode dans EXO_00_CORTEX.py (stase M6+M7 quand GLB actif)
- E7-B : Commentaires inline stase conditionnelle

### Tableau de bord Phase 7
| Unite | Phase | Taches totales | Taches OK | Statut |
|-------|-------|----------------|-----------|--------|
| U03 | D7 | 3 | 2 | EN COURS (D7-A ✅ D7-B ✅) |
| U00 | E7 | 2 | 0 | EN ATTENTE |

### Coherence pipeline GLB
```
U00 --glb-mode active :
    M6 DepthAnything -> STASE_GLB (depth maps non generees)
    M7 SAM           -> STASE_GLB (masques SAM non generes)

U03 --glb-path fourni :
    Dome / Displacement / PBR / Glass -> STASE (non executes)
    GLB importe + Shadow + HDRi       -> ACTIFS
```
Les deux flags sont independants mais complementaires. L'operateur les active ensemble
quand il fournit un GLB depuis Tripo AI / Meshy AI.

<!-- v7.0 — CODEX BRAINSTORM v1 — Phase 7 ouverte — 02.05.2026 -->
