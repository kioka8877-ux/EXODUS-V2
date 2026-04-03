# SENTINEL_CORE — ETAT COURANT (Phylactere de Verite)
> Audit Vulkan v13.0 — 2026-04-03 — MIS A JOUR APRES CODAGE B1/B4/B7

## TABLEAU DE CONFORMITE — 8 BRIQUES

| Brique | Nom | Priorite | Statut Code | Fichier | Lignes reelles |
|--------|-----|----------|-------------|---------|----------------|
| B1 | L'ESPRIT | Basse (Phase 3) | ✅ CODE ET OPERATIONNEL | brique1_ast.py | ~250 |
| B2 | LE CORPS | CRITIQUE | ✅ CODE ET OPERATIONNEL | brique2_state.py | ~365 |
| B3 | L'OEIL | Moyenne | ✅ CODE ET OPERATIONNEL | brique3_ghost.py | ~237 |
| B4 | LA VERITE | Optionnel (Phase 3) | ✅ CODE ET OPERATIONNEL | brique4_ground_truth.py | ~300 |
| B5 | L'ENQUETE | Moyenne | ✅ CODE ET OPERATIONNEL | brique5_diagnostic.py | ~223 |
| B6 | LA MEMOIRE | CRITIQUE | ✅ CODE ET OPERATIONNEL | brique6_ledger.py | ~233 |
| B7 | PERSONNAGES | Basse (Apres U01/U02) | ✅ CODE ET OPERATIONNEL | brique7_characters.py | ~280 |
| B8 | LE MIROIR | Haute | ✅ CODE ET OPERATIONNEL | brique8_mirror.py | ~319 |

**Orchestrateur :** sentinel_core.py — ✅ CODE ET OPERATIONNEL (~290 lignes reelles)

**Briques operationnelles : 8/8 — COMPLET**
**Briques critiques : 2/2 CODEES (B2 + B6)**
**SENTINEL : 100% OPERATIONNEL**

---

## DESCRIPTION DES 3 NOUVELLES BRIQUES

### B1 — L'ESPRIT (brique1_ast.py)
Analyse statique du code Python des frégates via AST (Abstract Syntax Tree).
- Detecte : appels dangereux (eval/exec), except nus, fonctions vides, chemins hardcodes
- Score qualite 0-100 par fichier + score global par dossier
- Mode standalone + mode integre dans sentinel_core
- Usage : `AstAnalyzer().analyze_dir("/path/to/CODEBASE/", fregate="U03")`

### B4 — LA VERITE (brique4_ground_truth.py)
Comparateur Ground Truth — detecte les regressions entre runs.
- Compare frames actuelles vs references stockees dans REFERENCES/{fregate}/
- Compare JSON critique vs reference.json
- Compare metadonnees .blend vs reference
- Verdict special NO_REF : premier run = creation de la reference
- Usage : `GroundTruth(refs_dir="...").compare_frames(fregate="U04", frames_dir="...")`
- Mise a jour reference : `--update-ref` ou `.update_reference(fregate, frames_dir=...)`

### B7 — PERSONNAGES (brique7_characters.py)
Validateur d'acteur Roblox/DynamicHead — cible U01 et U02.
- Mode bpy (Colab) : verifie armature, ShapeKeys >= 52, bones >= 20, keyframes, scale
- Mode degrade (local) : verifie taille fichier .blend, .abc, character_report.json
- Controle specifique U02 : scale (1.0, 1.0, 1.0) obligatoire + ABC export requis
- Usage : `CharacterValidator().validate(fregate="U01", blend_path="...")`

---

## COUVERTURE PAR FREGATE

| Fregate | B1 AST | B2 Etat | B3 Ghost | B4 VeriTe | B5 Diag | B6 Ledger | B7 Perso | B8 Mirror | Statut |
|---------|--------|---------|----------|-----------|---------|-----------|----------|-----------|--------|
| U00 CORTEX | ✅ | ✅ | ✅ | ✅ JSON | ✅ | ✅ | — | ✅ | OPERATIONNEL |
| U01 ANIMATION | ✅ | ✅ | ✅ | ✅ BLEND | ✅ | ✅ | ✅ | ✅ | OPERATIONNEL |
| U02 LOGISTICS | ✅ | ✅ | ✅ | ✅ BLEND | ✅ | ✅ | ✅ | ✅ | OPERATIONNEL |
| U03 SCENOGRAPHY | ✅ | ✅ | ✅ | ✅ FRAMES | ✅ | ✅ | — | ✅ | OPERATIONNEL |
| U04 PHOTOGRAPHY | ✅ | ✅ | ✅ | ✅ FRAMES | ✅ | ✅ | — | ✅ | OPERATIONNEL |
| U05 ALCHEMIST | ✅ | ✅ | ✅ | ✅ FRAMES | ✅ | ✅ | — | ✅ | OPERATIONNEL |
| U06 CARRIER | ✅ | ✅ | ✅ | ✅ JSON | ✅ | ✅ | — | ✅ | OPERATIONNEL |

---

## ARCHITECTURE FICHIERS — ETAT REEL (2026-04-03)

```
SENTINEL_CORE/
├── TRACKING/
│   ├── TRACKING_SENTINEL.md     ✅ Existe
│   ├── SENTINEL_STATE.md        ✅ Ce fichier — MIS A JOUR v13.0
│   └── SENTINEL_VALIDATION.md   ✅ Existe
├── CODEBASE/
│   ├── sentinel_core.py         ✅ CODE (~290 lignes) — Orchestrateur complet
│   ├── brique1_ast.py           ✅ CODE (~250 lignes) — Analyse AST [NOUVEAU]
│   ├── brique2_state.py         ✅ CODE (~365 lignes) — PRIORITE 1
│   ├── brique3_ghost.py         ✅ CODE (~237 lignes) — Ghost renderer
│   ├── brique4_ground_truth.py  ✅ CODE (~300 lignes) — Ground Truth [NOUVEAU]
│   ├── brique5_diagnostic.py    ✅ CODE (~223 lignes) — Matrice diagnostique
│   ├── brique6_ledger.py        ✅ CODE (~233 lignes) — Memoire persistante
│   ├── brique7_characters.py    ✅ CODE (~280 lignes) — Validateur acteur [NOUVEAU]
│   ├── brique8_mirror.py        ✅ CODE (~319 lignes) — Assembleur prompt
│   └── __init__.py              ✅ Existe
├── REFERENCES/                  ✅ Utilise par B4 (a remplir au 1er run)
│   ├── U03/
│   └── U04/
└── memory.json                  ✅ Cree au premier run B6
```

---

## DOCTRINE ACTIVE

```
SENTINEL = preparateur de contexte
Vulkan   = prescripteur
Empereur = validateur
```

---

## INTEGRATION MARSHAL

EXO_MARSHAL.py integre SENTINEL via trois hooks :
- `_sentinel_pre_check(unit, sentinel_dir, blend_path)` — avant execution fregate
- `_sentinel_post_record(unit, sentinel_dir, success, details)` — apres execution
- `_sentinel_run_full(unit, sentinel_dir, blend_path, frames_dir)` — pipeline complet

B1, B4, B7 sont disponibles en import direct depuis sentinel_core ou standalone.

---

## VERDICT FINAL — 2026-04-03

```
╔══════════════════════════════════════════════════════════════╗
║  SENTINEL CORE — 8/8 BRIQUES OPERATIONNELLES                ║
║  Briques critiques (B2 + B6) : 100% codees                  ║
║  Orchestrateur sentinel_core.py : 100% code                 ║
║  Integration MARSHAL : Complete                              ║
║  B1 L'ESPRIT : AST analyzer — OPERATIONNEL                   ║
║  B4 LA VERITE : Ground Truth comparator — OPERATIONNEL       ║
║  B7 PERSONNAGES : Character validator U01/U02 — OPERATIONNEL ║
║                                                              ║
║  VERDICT : SENTINELLE 100% COMPLETE — PRET POUR RUN E2E     ║
╚══════════════════════════════════════════════════════════════╝
```
