# SENTINEL_CORE — ETAT COURANT (Phylactere de Verite)
> Phase D7 — Initialisation — 2026-04-01

## TABLEAU DE CONFORMITE — 8 BRIQUES

| Brique | Nom | Phase | Priorite | Statut Code | Fichier |
|--------|-----|-------|----------|-------------|---------|
| B1 | L'ESPRIT | 3 | Basse | ❌ A coder | brique1_ast.py |
| B2 | LE CORPS | 1 | CRITIQUE | ❌ A coder | brique2_state.py |
| B3 | L'OEIL | 2 | Moyenne | ❌ A coder | brique3_ghost.py |
| B4 | LA VERITE | 3 | Optionnel | ❌ A coder | brique4_ground_truth.py |
| B5 | L'ENQUETE | 2 | Moyenne | ❌ A coder | brique5_diagnostic.py |
| B6 | LA MEMOIRE | 1 | CRITIQUE | ❌ A coder | brique6_ledger.py |
| B7 | PERSONNAGES | 3 | Basse | ❌ Apres U01/U02 | brique7_characters.py |
| B8 | LE MIROIR | 2 | Haute | ❌ A coder | brique8_mirror.py |

**Orchestrateur :** sentinel_core.py — ❌ A coder

---

## COUVERTURE PAR FREGATE

| Fregate | B2 Etat | B6 Ledger | B8 Template | Statut |
|---------|---------|-----------|-------------|--------|
| U00 CORTEX | ⏳ | ⏳ | ✅ Defini | Template pret |
| U01 ANIMATION | ⏳ | ⏳ | ✅ Defini | Template pret |
| U02 LOGISTICS | ⏳ | ⏳ | ✅ Defini | Template pret |
| U03 SCENOGRAPHY | ⏳ | ⏳ | ✅ Defini | Template pret — reference validee (16641 vertices) |
| U04 PHOTOGRAPHY | ⏳ | ⏳ | ✅ Defini | Template pret — test 10 frames en attente |
| U05 ALCHEMIST | ⏳ | ⏳ | ✅ Defini | Template pret |
| U06 CARRIER | ⏳ | ⏳ | ✅ Defini | Template pret |

---

## ARCHITECTURE FICHIERS — ETAT ACTUEL

```
SENTINEL_CORE/
├── TRACKING/
│   ├── TRACKING_SENTINEL.md     ✅ Cree (D7)
│   ├── SENTINEL_STATE.md        ✅ Ce fichier (D7)
│   └── SENTINEL_VALIDATION.md   ✅ Cree (D7)
├── CODEBASE/                    ❌ A creer
│   ├── sentinel_core.py         ❌
│   ├── brique2_state.py         ❌ PRIORITE 1
│   ├── brique6_ledger.py        ❌ PRIORITE 2
│   ├── brique8_mirror.py        ❌ PRIORITE 3
│   └── templates/               ❌ (7 templates definis, a coder)
├── REFERENCES/                  ❌ DNA samples (Phase 2)
└── memory.json                  ❌ Cree au premier run B6
```

---

## DOCTRINE ACTIVE

```
SENTINEL = preparateur de contexte
Vulkan   = prescripteur
Empereur = validateur
```

Principe de verification adversariale (inspire Verification Agent) :
- Chercher les echecs, pas confirmer le succes
- Le premier 80% est facile — la valeur est dans les 20% restants
- Chaque check doit produire une commande verifiable, pas une narration

---

## PROCHAINE ACTION — D7

```
1. Coder brique2_state.py (B2 — Signature d'Etat)
   → Mesure : vertices, camera, GPU, energy, luminance
   → Output : STATE_SIG.json
   → Timeout : 30 secondes

2. Coder brique6_ledger.py (B6 — Ledger)
   → Persistance : memory.json
   → Auto-inject : True
   → Survit aux sessions Colab

3. Coder brique8_mirror.py (B8 — Le Miroir)
   → Assemble templates dynamiquement
   → Injecte Ledger B6
   → Construit prompt Vulkan

4. Coder sentinel_core.py (Orchestrateur)
   → Coordonne B2 → B5 → B8 → Vulkan
   → Hooks Marshal
```
