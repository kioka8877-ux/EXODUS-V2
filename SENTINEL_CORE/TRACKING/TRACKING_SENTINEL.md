# TRACKING – SENTINEL_CORE (Systeme Immunitaire de l'Empire)

## 1. OBJECTIF DE SENTINEL

SENTINEL est le systeme immunitaire du pipeline EXODUS.
Il ne remplace pas les frégates. Il les surveille, diagnostique et corrige.

Doctrine fondamentale :
- SENTINEL est le preparateur de contexte
- Vulkan est le prescripteur
- L'Empereur valide

Architecture : 8 Briques complementaires formant un systeme auto-correcteur.
Cible : Zero regression entre sessions. Zero erreur repetee deux fois.

## 2. ETAT J0 — DIAGNOSTIC INITIAL

- **Probleme racine** : Les frégates echouent sans diagnostic clair. On corrige a l'aveugle.
- **Manquant** : Mesure de delta, memoire des corrections, generation de prompts structures.
- **Risque** : Sans SENTINEL, chaque session Colab repart de zero.
- **Solution** : 8 Briques progressives — B2+B6 en Phase 1, B8 en Phase 2.

## 3. PLAN D'ACTION — BACKLOG PAR PHASE

### Phase 1 — SENTINEL CORE (Priorite absolue)

#### B2 — Signature d'Etat
- [ ] Mesurer : vertices, camera, GPU, energy, luminance
- [ ] Output : STATE_SIG.json
- [ ] Logique adversariale : chercher les echecs, pas confirmer le succes
- [ ] Timeout : 30 secondes max
- [ ] Couverture : U03 + U04 en priorite

#### B6 — Ledger Persistant
- [ ] Stocker : erreur, cause, correction, fregate, timestamp
- [ ] Persistance : memory.json sur Drive (survit aux sessions Colab)
- [ ] Auto-inject : True par defaut
- [ ] Deduplication : meme erreur = meme entree incrementee

#### Integration Marshal
- [ ] Hook pre-execution : B2 avant chaque fregate
- [ ] Hook post-execution : B6 apres chaque resultat
- [ ] Interface EXO_MARSHAL.py

### Phase 2 — SENTINEL ADVANCED

#### B8 — Le Miroir (Ingenierie Inverse)
- [ ] Templates par fregate : U00 a U06 definis (voir SENTINEL_VALIDATION.md)
- [ ] Delta Niveau 3 : comparaison JSON parametres Blender
- [ ] Assemblage dynamique du prompt Vulkan
- [ ] DNA_SAMPLES/ : paires (input, output_parfait)
- [ ] Injection Ledger B6 dans le prompt

#### B3 — Ghost Renderer
- [ ] Rendu Workbench 128x128
- [ ] Temps cible : <3 secondes
- [ ] Output : ghost_frame.png pour B5

#### B5 — Diagnostic Differentiel
- [ ] Inputs : B2 (etat) + B3 (visuel)
- [ ] Matrice : etat_ok + visuel_noir = conflit shaders
- [ ] Output : verdict + cause racine

### Phase 3 — SENTINEL COMPLET

#### B1 — AST Reduit
- [ ] Verification statique avant execution
- [ ] Cibles : camera presente, engine = CYCLES
- [ ] Pas de energy thresholds (trop de faux positifs)

#### B4 — Ground Truth (Optionnel)
- [ ] Comparaison OpenCV source vs rendu
- [ ] Timeout : 30 secondes
- [ ] Seuil : gap_percentage > 50% = alerte

#### B7 — Personnages (Apres U01/U02)
- [ ] Signatures biometriques par acteur
- [ ] Ballerine, Dim Dread, etc.
- [ ] Validation shapekeys + shaders

## 4. JOURNAL DES PHASES

### Phase D7 — Initialisation SENTINEL (2026-04-01)
- [x] Doctrine definie : SENTINEL prepares → Vulkan prescrit → Empereur valide
- [x] 8 Briques specifiees avec priorites
- [x] Templates U00-U06 avec deltas Niveau 3 definis
- [x] Architecture SENTINEL_CORE/ etablie
- [x] Fichiers de tracking crees (ce fichier + SENTINEL_STATE.md + SENTINEL_VALIDATION.md)
- [ ] B2 brique2_state.py — A coder
- [ ] B6 brique6_ledger.py — A coder
- [ ] B8 brique8_mirror.py — A coder
- [ ] sentinel_core.py orchestrateur — A coder

## 5. LECONS APPRISES

| Session | Lecon | Application |
|---------|-------|-------------|
| D6 | depsgraph stale sans .update() | B2 force depsgraph.update() avant mesure |
| D6 | camera absente = rendu noir | B2 verifie camera_main.present en premier |
| D6 | scene_type unknown = mauvais template | B8 lit assembler_results.json directement |
| D7 | Templates doivent etre dynamiques | B8 assemble par modules, pas monolithique |

## 6. DEFINITION DE DONE — SENTINEL

SENTINEL est operationnel quand :
- B2 detecte un delta avant que l'Empereur le voit
- B6 injecte automatiquement la correction connue
- B8 construit un prompt que Vulkan transforme en patch actionnable
- Zero erreur repetee deux fois sur une meme fregate
