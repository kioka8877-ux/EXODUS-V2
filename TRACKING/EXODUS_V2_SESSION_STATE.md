# EXODUS V2 — SESSION STATE
> Document de reprise de session. Si le chat lache, donner ce fichier + CODEX_IMPERIAL_v4.docx.
> Derniere mise a jour : 2026-04-23

---

## SECTION 1 — ETAT DE LA FLOTTE

| Fregate | Nom | Statut | Decrets valides | Note |
|---|---|---|---|---|
| F00 | CORTEX HQ | EN MUTATION | 5 | Architecture duale API/Injection + bloc actors_placement ajoute |
| F01 | ANIMATION ENGINE | EN MUTATION | 4 | Pivot V1 canonise — outil externe + multi-avatar |
| F02 | LOGISTICS DEPOT | VALIDEE | 3 | Bypass props implementee |
| F03 | SCENOGRAPHY DOCK | VALIDEE | 4 | Fregate d'integration — HunyuanWorld-Mirror + actors_placement |
| F04 | PHOTOGRAPHY WING | VALIDEE | 4 | Workflow Manuel Guide — Reference Frame + Arsenal Lumineux 3-Point + HDRi Poly Haven |
| F05 | ALCHEMIST LAB | VALIDEE/SCELLE | 3 | 3 modes (Bypass/Resolve/Python LUT) + lut_engine.py + MANIFEST.json |
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

**DECRET V — Bloc actors_placement dans PRODUCTION_PLAN.JSON (VALIDE EN SESSION — 2026-04-23)**
F00 (Gemini analyse la video) genere un bloc `actors_placement` pour chaque scene.
Gemini observe la video et estime les positions relatives des acteurs (gauche/droite, distance approximative)
et leur orientation (face-a-face, meme direction, etc.).
Ce bloc est ecrit dans PRODUCTION_PLAN.JSON et consomme exclusivement par F03.

Format cible :
```json
"actors_placement": [
  { "avatar_id": 0, "position": [0.0, 0.0, 0.0], "facing_target": 1 },
  { "avatar_id": 1, "position": [1.5, 0.0, 0.0], "facing_target": 0 }
]
```
Note : precision centimetrique non requise pour contenu Roblox stylise. Estimation Gemini suffisante.

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
3. Flag CLI : `--bypass` pour forcer manuellement

En mode bypass, F02 copie directement les fichiers F01 (`.blend` + `.abc`) vers `OUT_BAKED_ACTORS/`
et genere un `logistics_report.json` avec `status: "SKIPPED"`.
F00 (CORTEX) est responsable de renseigner `requires_u02` dans `production_notes`.

---

### F03 — SCENOGRAPHY DOCK (VALIDEE EN SESSION — 2026-04-23)

**Pivot architectural : F03 devient une fregate d'INTEGRATION, pas de construction.**

Outil externe : HunyuanWorld-Mirror reconstruit le decor 3D depuis la video source.
Il livre un fichier `decor_{scene_id}.glb` complet : mesh + textures PBR + lighting bake.

**Nouveau flux F03 :**
```
INPUTS :
    actor_equipped-N.blend + .abc  (de F02, ou F01 si bypass)
    PRODUCTION_PLAN.JSON           (de F00 — contient actors_placement)
    decor_{scene_id}.glb           (outil externe HunyuanWorld-Mirror)

F03 PROCESS (4 operations uniquement) :
    1. Importer le .glb complet (mesh + textures + lumieres)
    2. Ajouter shadow catcher sur le sol (Y=0)
    3. Positionner les acteurs selon actors_placement du plan
    4. Exporter

OUTPUT :
    environment_{scene_id}.blend → F04
```

**DECRET I — Externalisation Complete vers HunyuanWorld-Mirror**
F03 ne construit plus rien. HunyuanWorld-Mirror reconstruit le decor depuis la video source.
10 operations → 4 operations. Coherence visuelle garantie (le decor EST le vrai decor de la video).

**DECRET II — Import .glb Complet**
Validation du .glb a l'import (schema materiaux, presence ground plane a Y=0).
Erreur explicite si sol non detecte — requis pour positionner les acteurs.

**DECRET III — Shadow Catcher Unique sur Sol Y=0**
Seule operation de construction conservee dans F03.
Le shadow catcher depend de la position exacte des acteurs — ne peut pas etre dans le .glb externe.

**DECRET IV — Positionnement Acteurs via actors_placement**
F03 lit le bloc `actors_placement` de PRODUCTION_PLAN.JSON (genere par F00).
`facing_target` = index de l'avatar vers lequel regarder → rotation automatique.
Scalable : 1 acteur ou N acteurs en interaction (notamment face-a-face).

---

### F04 — PHOTOGRAPHY WING (VALIDEE EN SESSION — 2026-04-23)

**DECRET I — Priorite au Mode Manuel Guide**
Architecture split A/B simplifiee. Phase 1 = Mode Manuel uniquement.
Intentions de cadrage depuis PRODUCTION_PLAN.JSON → keyframes camera a la main.
Tracking auto (COLMAP/OpenCV) reporte en Phase 2.

**DECRET II — Notebook de Production Unifie**
Un seul notebook `EXO_04_PRODUCTION.ipynb` avec cellules conditionnelles (mode manuel / auto).

**DECRET III — Reference Frame Background**
Extraire une frame de reference par scene depuis `video_source.mp4` via ffmpeg.
Importer comme Background Image dans le viewport Blender (natif, aucun addon requis).
L'operateur aligne la camera manuellement sur cette reference visuelle.
Commande : `ffmpeg -i video_source.mp4 -vf "select=eq(n\,FRAME)" -vsync 0 ref_frame.png`
Garantit la coherence visuelle entre video source et rendu Roblox.

**DECRET IV — Arsenal Lumineux Standard (3-Point + HDRi Poly Haven)**
Deux couches, 100% gratuit, 100% scriptable via bpy.
- Couche 1 (ambiance) : HDRi Poly Haven (polyhaven.com) applique sur le World Blender via script Python.
- Couche 2 (acteurs) : rig 3 points (Key + Fill + Rim) genere par script bpy, attache a chaque acteur.
- Aucun addon tiers requis. Addons natifs Blender 4.x utiles : Sun Position, Dynamic Sky.
- Fichier .hdr Poly Haven = telechargement manuel unique, a versionner dans le repo.

**Flux F04 :**
```
INPUTS :
    environment_{scene_id}.blend  (de F03 — decor + acteurs positionnes)
    PRODUCTION_PLAN.JSON           (de F00 — intentions de cadrage par scene)
    video_source.mp4               (reference visuelle — extraction ref frame)

F04 PROCESS :
    1. Extraire ref frame(s) depuis video_source.mp4 (ffmpeg)
    2. Importer ref frame comme Background Image dans Blender
    3. Placer camera + keyframes selon guides PRODUCTION_PLAN.JSON
    4. Appliquer HDRi Poly Haven sur le World
    5. Generer rig 3-point lighting pour chaque acteur (script bpy)
    6. Exporter

OUTPUT :
    scene_with_camera_{scene_id}.blend → F05
```

---

### F05 — ALCHEMIST LAB (VALIDEE EN SESSION — 2026-04-23)

**Pipeline OpenCV CPU pur (deja implemente v2.0.0) :**
match_color → grain → bloom → sharpness → [LUT optionnel] → PNG 16-bit

**Mode A — Bypass (DECRET II)**
Flag `--bypass` : F05 skippee, frames copiees directement vers `OUT_FINAL_FRAMES/`.
Genere `alchemist_report.json` avec `status: "SKIPPED"`.
Utile si rendu Blender Cycles deja satisfaisant → transit direct F04 → F06.

**Mode B — DaVinci Resolve (outil externe, hors scope code)**
Operateur importe sequence EXR dans Resolve Free, applique LUT, exporte.
Non scriptable — manuel uniquement. Documente ici pour reference.

**Mode C — Python LUT Engine (DECRET III)**
Module `lut_engine.py` : lecture .cube + interpolation trilineaire 3D, 100% numpy.
Activation : `--lut LUTS/cinematic_cold.cube [--lut-intensity 0.8]`
Step ajoute apres le pipeline OpenCV existant.

**DECRET I — Inventaire et Versionnage des LUTs**
`LUTS/MANIFEST.json` cree. 4 LUTs versionnees dans le repo :
- `cinematic_cold.cube` — Look froid, ambiances nocturnes
- `cinematic_warm.cube` — Look chaud, eclairages dores
- `natural.cube` — Grade neutre
- `neon_nights.cube` — Cyberpunk

**Flux F05 :**
```
INPUTS :
    IN_RAW_FRAMES/     (frames .exr rendues par Blender — de F04)
    PRODUCTION_PLAN.JSON
    video_source.mp4   (reference couleur — optionnel)
    LUTS/*.cube        (optionnel — Mode C)

F05 PROCESS :
    Mode A  → copie directe → OUT_FINAL_FRAMES/
    Mode B  → DaVinci Resolve (manuel, hors EXODUS)
    Mode C  → match_color → grain → bloom → sharpness → [LUT] → PNG 16-bit

OUTPUT :
    OUT_FINAL_FRAMES/final_{scene}_{frame}.png → F06
```

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
Session actuelle         : 02.05.2026.M41
Phase courante           : PHASE 8 — DUAL PIPELINE DOCTRINE
Doctrine validee         : EXODUS_V2_CODEX_BRAINSTORM_MODE2.docx (v1)

MODE 1 (Video-to-Video)  : COMPLET — INTOUCHABLE — 7 fregates scellees (U00-U06)
MODE 2 (From Scratch)    : EN FORGE — 0/7 modules crees

Prochaine action         : Forger LAUNCHER + M2_F01 a M2_F06
Questions ouvertes       : aucune — doctrine scellee par decret imperial

Lois inviolables Mode 2  :
  R-01 : Etancheite — copies independantes, zero contamination Mode 1
  R-02 : Format avatar — GLB avec animations embarquees obligatoires
  R-03 : Loi audio — duree_audio <= duree_animation (animation prime)
  R-04 : Overlay binaire — fin M2_F06 : OUI (audio+texte) ou NON (video brute)
  R-05 : Decor — GLB fourni par Operateur, gere par M2_F03
  R-06 : Launcher — zero logique metier, routing pur

CODEX version courante   : EXODUS_V2_CODEX_BRAINSTORM_MODE2.docx (v1 — 02.05.2026)
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
| Bypass F02 | F02 skippee automatiquement si requires_u02==false ou 0 props dans le plan |
| actors_placement | Bloc JSON dans PRODUCTION_PLAN.JSON — positions + orientations des acteurs par scene |
| HunyuanWorld-Mirror | Outil externe (Tencent) — reconstruit un decor 3D depuis une video source |
| Shadow catcher | Plan invisible qui capte les ombres des acteurs sur le sol — ajoute par F03 |
| Reference Frame | Frame extraite de video_source.mp4 via ffmpeg — importee dans Blender comme guide camera |
| Poly Haven | Site de ressources gratuites (polyhaven.com) — HDRi utilises par F04 pour l'eclairage d'ambiance |
| Rig 3-Point | Configuration Key + Fill + Rim generee par script bpy — eclairage dedie aux acteurs Roblox dans F04 |
| Bypass F05 | F05 skippee avec --bypass : frames F04 copiees directement vers F06, aucun traitement |
| LUT Engine | Module lut_engine.py — applique un .cube 3D via interpolation trilineaire numpy (Mode C F05) |

---

## SECTION 6 — CONTEXTE DE REPRISE

> Copier-coller ce bloc au debut d'une nouvelle session apres avoir fourni ce fichier + le CODEX.

```
Nous travaillons sur le projet EXODUS V2 (repo : kioka8877-ux/EXODUS-V2).
Architecture : DUAL PIPELINE DOCTRINE (02.05.2026) — deux modes, un Launcher, un output.

=== MODE 1 — VIDEO-TO-VIDEO (COMPLET, INTOUCHABLE) ===
7 fregates scellees (U00 a U06). Ne pas modifier.
Pipeline : video virale → U00 analyse → U01 animation → U02 logistics →
           U03 scenography → U04 photography → U05 alchemist → U06 carrier → FINAL.mp4

=== MODE 2 — FROM SCRATCH (EN FORGE) ===
Input : avatar GLB anime (fourni par Operateur) + audio optionnel
Pipeline a forger : LAUNCHER → M2_F01 → M2_F02 → M2_F03 → M2_F04 → M2_F05 → M2_F06 → FINAL.mp4

LAUNCHER  : menu CLI binaire (1=Mode1, 2=Mode2), zero logique metier
M2_F01    : valide le GLB (pygltflib) + verifie duree audio <= duree animation (LOI R-03)
M2_F02    : assemble acteur + props (copie etanche M1_F02 — bpy)
M2_F03    : importe GLB decor fourni + shadow catcher + HDRi (bpy — LOI R-05)
M2_F04    : camera + lumieres (copie etanche M1_F04 — bpy)
M2_F05    : post-prod + color grading (copie etanche M1_F05 — OpenCV/numpy)
M2_F06    : assembly + choix binaire overlay OUI/NON → FINAL.mp4 (ffmpeg, RIFE, Real-CUGAN)

LOI D'ETANCHEITE (R-01) : chaque fregate Mode 2 est une copie independante.
Si Mode 2 brise, Mode 1 fonctionne. Zero contamination croisee.

Etat Phase 8 : 0/7 modules crees. Forge ordonnee par decret imperial 02.05.2026.
CODEX source : EXODUS_V2_CODEX_BRAINSTORM_MODE2.docx (v1)
```
