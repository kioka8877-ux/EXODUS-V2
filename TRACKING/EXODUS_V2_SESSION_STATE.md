# EXODUS V2 — SESSION STATE
> Document de reprise de session. Si le chat lache, donner ce fichier + CODEX_IMPERIAL_v2.docx.
> Derniere mise a jour : 2026-04-21

---

## SECTION 1 — ETAT DE LA FLOTTE

| Fregate | Nom | Statut | Decrets valides | Note |
|---|---|---|---|---|
| F00 | CORTEX HQ | EN MUTATION | 4 | Architecture duale API/Injection validee |
| F01 | ANIMATION ENGINE | EN MUTATION | 4 | Pivot V1 canonise — outil externe + multi-avatar |
| F02 | LOGISTICS DEPOT | VALIDEE | 3 | Bypass props implemente — seule amelioration retenue |
| F03 | SCENOGRAPHY DOCK | SCELLE (brainstorming init) | 3 | Pas encore approfondie |
| F04 | PHOTOGRAPHY WING | EN COURS (brainstorming init) | 1 | Pas encore approfondie |
| F05 | ALCHEMIST LAB | SCELLE (brainstorming init) | 2 | Pas encore approfondie |
| F06 | AIRCRAFT CARRIER | EN MUTATION (brainstorming init) | 2 | ATOM-IC frame-based en cours |

---

## SECTION 2 — DECISIONS VALIDEES PAR FREGATE

### F00 — CORTEX HQ

**DECRET I — Externalisation IMPERIAL_ARSENAL**
Sortir l'arsenal du code Python vers un fichier `arsenal.json` externe. Modifiable sans toucher au code.

**DECRET II — Mode skip-gpu**
Ajouter un flag `--skip-gpu` pour bypasser Depth+SAM sur les videos simples.

**DECRET III — Validation JSON Gemini stricte**
Valider le JSON Gemini en sortie contre un schema strict avant ecriture. Evite les erreurs en cascade.

**DECRET IV — Architecture Duale API / Injection JSON (VALIDE EN SESSION)**
```
Cellule 0  → Choix du mode  (MODE = "api" | "injection")
Cellule 1  → Pre-flight + M2 Audio + M3 FOV       (les deux modes)
Cellule 2  → M1 Gemini API                        (mode api seulement)
Cellule 2b → Widget injection JSON                (mode injection seulement)
Cellule 3  → M6 Depth + M7 SAM + flags finaux     (les deux modes)
```
- Le mode injection remplace exactement le bloc M1 Gemini
- JSON injecte contient les 3 blocs : `production_plan`, `facial_animation`, `motion_synthesis`
- `dispatch_master_json` est le point de convergence unique des deux modes
- Les phases M2/M3/M6/M7 s'executent dans les deux modes sans modification
- Metaprompt CORTEX (`GEMINI_CHAT_METAPROMPT.md`) a creer — base existante, a affiner en production
- Reference : pattern ANIMA-MECHANICUS (depot kioka8877-ux/ANIMA-MECHANICUS/U-ALPHA)

---

### F01 — ANIMATION ENGINE

**DECRET I — Externalisation du Corps Anime (Outil Externe) (VALIDE EN SESSION)**
Un outil externe (developpe hors EXODUS) prend la video humaine reelle, extrait l'animation de chaque personnage et retargete sur avatar Roblox. Livre un fichier `avatar-ferrus-N.blend` par personnage. EXODUS recoit ce .blend corps anime comme input. Mixamo elimine de la chaine.

**DECRET II — EMOCA sur Visage Humain Reel (VALIDE EN SESSION)**
EMOCA tourne desormais sur le vrai visage humain de la video source (plage d'entrainement naturelle = precision maximale). InsightFace isole la crop du bon visage par avatar avant chaque passage EMOCA.

**DECRET III — Lip-Sync Obligatoire par Piste Audio Propre (VALIDE EN SESSION)**
Rhubarb TOUJOURS actif si `audio_original.wav` present (systematique en V1). pyannote.audio genere une piste propre par avatar (silence la ou l'avatar ne parle pas) avant passage a Rhubarb. Plus de flag optionnel.

**DECRET IV — Orchestration Multi-Avatar (VALIDE EN SESSION)**
F01 tourne en boucle sur chaque `avatar-ferrus-N.blend` recu. Pour chaque avatar :
1. InsightFace assigne un Face_ID stable dans la video source
2. pyannote.audio genere la piste propre du speaker correspondant
3. EMOCA + Rhubarb tournent sur cet avatar uniquement

Scalable : 1 avatar ou 5 avatars, meme code sans modification.

**Nouveau flux F01 :**
```
INPUTS :
    avatar-ferrus-N.blend  (outil externe, corps anime)
    video_source.mp4       (video humaine originale 9:16)
    audio_original.wav     (une seule piste, toutes voix melangees)
    PRODUCTION_PLAN.JSON   (F00)

F01 PROCESS :
    for N in avatars:
        1. InsightFace  → Face_ID stable → crop visage N
        2. pyannote     → timeline speaker N → piste propre
        3. EMOCA        → shape keys visage
        4. Rhubarb      → shape keys bouche
        5. Fusion dans avatar-ferrus-N.blend

OUTPUTS :
    avatar-ferrus-N_animated.blend + avatar-ferrus-N.abc
```

---

### F02 — LOGISTICS DEPOT (VALIDEE EN SESSION — 2026-04-21)

**DECRET I** — Validation pre-socketing (verifier que chaque bone cible existe avant d'attacher les props)
**DECRET II** — Fusionner `socketing_engine.py` + `timeline_manager.py` en un seul module

**DECRET III — Bypass Props (VALIDE EN SESSION)**
Si la video source ne contient aucun prop, F02 est bypasse automatiquement.

Mecanisme en deux couches :
1. Flag explicite : `PRODUCTION_PLAN.JSON["production_notes"]["requires_u02"] == false`
2. Auto-detection : si 0 `props_actions` dans toutes les scenes → bypass automatique
3. Flag CLI : `--bypass` force le bypass manuel

En mode bypass, F02 copie directement les fichiers F01 (`.blend` + `.abc`) vers `OUT_BAKED_ACTORS/`
et genere un `logistics_report.json` avec `status: "SKIPPED"`.
F00 (CORTEX) genere le champ `requires_u02` dans `production_notes` — deja implemente dans le code.

**Implemente dans :**
- `EXO_02_LOGISTICS.py` lignes 406-488
- `EXO_02_PRODUCTION.ipynb` cellule "Bypass Check"

---

### F03 — SCENOGRAPHY DOCK (brainstorming initial, pas approfondie)

**DECRET I** — Supprimer le code mort des phases D2/D3 tant qu'elles ne sont pas implementees
**DECRET II** — Regrouper `dome_builder`, `glass_builder`, `shadow_catcher_builder` en un seul `environment_builder.py` avec modes
**DECRET III** — Stabiliser `phantom_link.py` : une seule copie en racine, ne plus auto-copier

---

### F04 — PHOTOGRAPHY WING (brainstorming initial, pas approfondie)

**DECRET I** — Simplifier vers camera manuelle avec guides plutot que tracking automatique (plus fiable pour contenu Roblox stylise)
Note : architecture split A/B actuelle a reevaluer en session dediee.

---

### F05 — ALCHEMIST LAB (brainstorming initial, pas approfondie)

**DECRET I** — Verifier que les LUTs sont incluses dans le repo ou documentees (source externe = risque)
**DECRET II** — Permettre de bypasser le color grading si le rendu est deja satisfaisant

---

### F06 — AIRCRAFT CARRIER (brainstorming initial, pas approfondie)

**DECRET I** — Forcer pipeline 100% lossless jusqu'au rendu final (EXR tout le long, 4 compressions lossy eliminées)
**DECRET II** — Rendre RIFE configurable : 24→60 ou 24→120 selon besoin

---

## SECTION 3 — PIVOT V1 (memo global)

Le projet EXODUS V2 a pivote vers une architecture V1 basee sur des videos humaines reelles.

**Avant le pivot :**
- Input : video Roblox
- Probleme : modeles AI entraines sur humains → precision degradee sur Roblox
- Mixamo FBX requis manuellement pour chaque sequence

**Apres le pivot V1 :**
- Input : video humaine reelle 9:16 (tronc ou tete, souvent interactions 2 personnes)
- Corps anime : outil externe (hors EXODUS) → retargeting Roblox → `avatar-ferrus-N.blend`
- EXODUS recoit le .blend, ajoute visage (EMOCA) + lip-sync (Rhubarb) + multi-avatar
- Audio : une seule piste originale, diarisation automatique par pyannote.audio
- Tous les modeles AI (Depth, SAM, EMOCA) operent sur humains reels = precision maximale

**Impact : F01 plus simple** — la partie la plus complexe (retargeting) est externalisee. F01 ne traite que des problemes bien resolus (diarisation, face tracking, EMOCA, Rhubarb).

---

## SECTION 4 — POSITION COURANTE

```
Derniere fregate traitee : F02 — LOGISTICS DEPOT — VALIDEE
Prochaine fregate        : F03 — SCENOGRAPHY DOCK
Questions ouvertes       : aucune sur F00, aucune sur F01, aucune sur F02
CODEX version courante   : EXODUS_V2_CODEX_IMPERIAL_v2.docx (454 paragraphes)
```

---

## SECTION 5 — LEXIQUE

| Terme | Definition |
|---|---|
| Fregate | Module autonome du pipeline EXODUS (F00 a F06) |
| CORTEX | F00 — analyse la video source et genere le PRODUCTION_PLAN.JSON |
| PRODUCTION_PLAN.JSON | Fichier central qui orchestre toutes les frigates en aval |
| dispatch_master_json | Fonction de convergence F00 — recoit le JSON API ou injecte |
| avatar-ferrus-N | Fichier .blend d'un avatar Roblox avec corps anime (outil externe) |
| InsightFace | Librairie de face tracking stable — assigne Face_ID par personne |
| pyannote.audio | Librairie de diarisation — detecte qui parle quand |
| Rhubarb | Outil de lip-sync — genere les phonemes bouche depuis audio |
| EMOCA | Modele d'expression faciale — genere shape keys depuis visage humain |
| Transit manuel | Passage de fichiers entre frigates fait a la main par l'operateur |
| ATOM-IC | Architecture frame-based en cours sur F06 |
| Mode API | F00 appelle Gemini API automatiquement pour analyser la video |
| Mode Injection | F00 recoit un JSON colle manuellement depuis Gemini Chat |
| Retargeting | Conversion squelette humain → rig Roblox (fait par outil externe, hors EXODUS) |
| Bypass F02 | F02 skippee si requires_u02==false ou 0 props dans le plan |

---

## SECTION 6 — CONTEXTE DE REPRISE

> Copier-coller ce bloc au debut d'une nouvelle session apres avoir fourni ce fichier + le CODEX.

```
Nous travaillons sur le projet EXODUS V2 (repo : kioka8877-ux/EXODUS-V2).
C'est un pipeline de production video en 7 frigates (F00 a F06) qui transforme
des videos humaines reelles 9:16 en videos Roblox avec animation, lip-sync et rendu.

F00, F01 et F02 ont ete completement brainstormees et validees dans le SESSION STATE.
F00 a une architecture duale API/Injection JSON canonisee.
F01 recoit des fichiers .blend d'un outil externe (corps anime, retargeting deja fait)
et ajoute EMOCA (visage) + Rhubarb (lip-sync) + orchestration multi-avatar via
InsightFace et pyannote.audio.
F02 a un systeme de bypass automatique : si la video n'a pas de props,
F02 est skippee et les fichiers F01 transitent directement vers F03.

Nous sommes sur le point d'approfondir F03 — SCENOGRAPHY DOCK.
Les decisions prises sont dans le CODEX IMPERIAL v2 (EXODUS_V2_CODEX_IMPERIAL_v2.docx).
```
