# ARCHITECTURE U04 — PHOTOGRAPHY WING
> Note Technique : Séparation Director / Darkroom

## 1. CONTEXTE

L'Unité 04 (Photography Wing) a pour mission de transformer le .blend assemblé (acteur + environnement) en image finale. Le PRD définit 4 piliers :
- **Pilier A** — Perspective Lock (fSpy, ±5% mouvement max)
- **Pilier B** — Auto-DOF (Empty parenté au buste avatar, Bokeh automatique)
- **Pilier C** — Shake Procédural (Noise modifier sur F-Curves rotation, PAS de keyframes aléatoires)
- **Pilier D** — Volume Scatter + Lampes Invisibles (atmosphère cinématographique)

Plus un critère de validation : **Alerte Frustum** (avatar hors champ).

## 2. PROBLÈME : LE POIDS DU RENDU

Le pipeline cible 4K/30FPS. Pour une vidéo de 60 secondes :

| Format | Par frame | 1800 frames (60s) | Viable ? |
|--------|-----------|-------------------|----------|
| EXR Multi-Layer 32-bit (toutes passes) | ~150 MB | **~270 GB** | ❌ IMPOSSIBLE |
| EXR Multi-Layer 16-bit (toutes passes) | ~75 MB | ~135 GB | ❌ Trop lourd |
| EXR Half-Float (passes critiques) | ~20 MB | ~36 GB | 🟡 Possible mais lourd |
| PNG 16-bit (Combined only) | ~2 MB | ~3.6 GB | 🟡 Trop basique pour U05 |
| **.blend configuré (ZÉRO frames)** | **~200 MB** | **~200 MB** | ✅ **OPTIMAL** |

**Constat** : Le rendu est le goulot d'étranglement. Sur Google Colab (T4 16GB), un rendu 4K Cycles à 256 samples prend ~30-90 secondes par frame. Pour 1800 frames : **15-45 heures de GPU**.

## 3. DÉCISION : SÉPARER DIRECTOR ET DARKROOM

### Principe
Séparer la **configuration caméra** (rapide, ~30 secondes) du **rendu** (lent, 15-45 heures).

### U04-A — DIRECTOR (Configuration)
- **Mission** : Configurer le .blend avec caméra, DOF, shake, atmosphère, et réglages Cycles.
- **Durée** : ~30 secondes
- **Input** : `*.blend` (U02 + U03) + `camera_fov_ratio.json` (U00)
- **Output** : `*.blend` configuré (~200 MB) dans `OUT_CAMERA_LOGIC/`
- **Contenu du .blend** : Caméra positionnée (fSpy), DOF actif (Empty→buste), Noise modifier (shake), Volume Scatter, lampes invisibles, Cycles configuré, passes activées, résolution 4K
- **NE FAIT PAS** : Aucun rendu. Zéro frame produite.

### U04-B — DARKROOM (Rendu)
- **Mission** : Ouvrir le .blend de U04-A et lancer le rendu batch.
- **Durée** : 15-45 heures (GPU dépendant)
- **Input** : `*.blend` configuré par U04-A
- **Output** : Frames EXR/PNG dans `OUT_CAMERA_LOGIC/` pour U05/Alchemist
- **Infrastructure** : Google Colab Pro, cloud GPU, ou local — à définir
- **STATUT** : 🔴 PLANIFIÉ — PAS DÉVELOPPÉ. Nécessite un brainstorming infrastructure séparé.

### Pourquoi cette séparation ?

| Critère | Monolithique (A+B ensemble) | Séparé (A puis B) |
|---------|---------------------------|-------------------|
| Développement | Bloqué par infra GPU | A développable immédiatement |
| Test | Impossible sans GPU dédié | A testable sur CPU |
| Itération | Chaque modif = re-rendu complet | A modifiable sans re-rendu |
| Debug | Difficile de savoir si bug = config ou rendu | Responsabilité claire |
| CI/CD | Impossible d'intégrer | A intégrable dans le pipeline |
| Budget GPU | Tout ou rien | Rendu lancé uniquement quand config validée |

### Schéma du flux

```
U02 (actor.blend) ──┐
                     ├──→ [U04-A DIRECTOR] ──→ scene_configured.blend ──→ [U04-B DARKROOM] ──→ frames.exr ──→ U05
U03 (environment.blend)┘          ~30s                 ~200 MB                    ~15-45h              ~36 GB
U00 (camera_fov_ratio.json)┘
```

## 4. FONDATION : camera_schema.py (Bible Optique)

Avant les 4 piliers, un module de données pures centralise TOUTES les constantes et presets :

| Pilier Schema | Contenu | Remplace |
|---------------|---------|----------|
| Constantes canoniques | PERSPECTIVE_LOCK_TOLERANCE (±5%), DEFAULT_FSTOP, etc. | Valeurs hardcodées |
| Camera Style Presets | 6 styles (static, dolly, orbit, handheld, tracking, matchmove) | CAMERA_STYLES dans camera_director.py |
| Cut Presets | 8 types de plans (wide→over_shoulder) | CUT_TYPES (camera_director.py) + CUT_PRESETS (cuts_engine.py) — **DÉDUPLIQUÉ** |
| Lighting Presets | 5 styles + couleurs | LIGHTING_STYLES, COLOR_TEMPS, NEON_COLORS (lighting_rig.py) |
| Bust Bone Chain | 16 noms de bones (fallback Mixamo→Generic→Rigify→3dsMax) | Nouveau |
| Render Presets | production (256 samples) / preview (64 samples) | Nouveau |
| Shake Presets | handheld / subtle / aggressive (Noise modifier params) | Nouveau |
| Validation | Matrice style↔features, contrôle ±5%, self_test() | Nouveau |

**Pattern** : identique à `expression_schema.py` de U01 (Python pur, zéro Blender, self_test standalone).

## 5. ARCHITECTURE DES FICHIERS (U04-A)

```
04_PHOTOGRAPHY_WING/
├── ARCHITECTURE_U04.md            ← CE DOCUMENT
├── CODEBASE/
│   ├── camera_schema.py           ← NOUVEAU (Bible — Python pur)
│   ├── fspy_tracker.py            ← NOUVEAU (Pilier A)
│   ├── auto_dof.py                ← NOUVEAU (Pilier B)
│   ├── render_forge.py            ← NOUVEAU (Config Cycles — PAS de rendu)
│   ├── camera_director.py         ← MODIFIÉ (Pilier C shake + matchmove + frustum)
│   ├── cuts_engine.py             ← MODIFIÉ (imports depuis camera_schema)
│   ├── lighting_rig.py            ← MODIFIÉ (Pilier D atmosphère + lampes)
│   ├── EXO_04_PHOTOGRAPHY.py      ← MODIFIÉ (câblage)
│   ├── keyframe_animator.py       ✅ INCHANGÉ
│   ├── requirements.txt           ← MODIFIÉ
│   ├── EXO_04_CONTROL.ipynb       ✅ INCHANGÉ
│   └── EXO_04_PRODUCTION.ipynb    ✅ INCHANGÉ
├── IN_VIDEO_SOURCE/
├── IN_SCENE_REF/
├── OUT_CAMERA_LOGIC/              → Output : *.blend UNIQUEMENT
├── UNIT_04_SUBPLAN.md             ← MODIFIÉ
└── README_DEV.md                  ← MODIFIÉ
```

## 6. CRITÈRES DE VALIDATION (5/5 dans U04-A)

Tous les critères de `EXODUS_V2_VALIDATION.md §U04` sont satisfaits par U04-A :

| # | Critère | Module U04-A | Comment vérifier |
|---|---------|-------------|-----------------|
| 1 | Perspective lock fSpy ±5% | fspy_tracker.py | camera_schema.validate_perspective_deviation() |
| 2 | Auto-DOF Empty sur buste | auto_dof.py | Vérifier camera.dof.focus_object != None |
| 3 | Shake Noise modifier | camera_director.py | Vérifier fcurve.modifiers contient type='NOISE' |
| 4 | Volume Scatter + lampes | lighting_rig.py | Vérifier World shader contient VolumeScatter |
| 5 | Alerte frustum | camera_director.py | check_frustum() retourne warning si hors champ |

## 7. MARSHAL — CONTRAT IN/OUT

Conformément à `EXO_MARSHAL.py` (lignes 96-111) :

**IN** (ce que U04-A reçoit) :
- `IN_SCENE_REF/*.blend` — scène (U03) + acteur (U02)
- `IN_VIDEO_SOURCE/*.mp4` — vidéo source (pour référence)
- `IN_VIDEO_SOURCE/camera_fov_ratio.json` — métadonnées caméra (U00)

**OUT** (ce que U04-A produit) :
- `OUT_CAMERA_LOGIC/*.blend` — scène avec caméra configurée ✅ (required: True)
- ~~`OUT_CAMERA_LOGIC/*.exr`~~ — frames rendues ❌ (U04-B, pas U04-A)
- ~~`OUT_CAMERA_LOGIC/*.png`~~ — frames rendues ❌ (U04-B, pas U04-A)

> **Note** : Le Marshal actuel a `*.exr` et `*.png` en `required: False` dans le manifest U05. U04-A ne les produit pas — c'est U04-B qui le fera.

## 8. TIMELINE

| Phase | Quoi | Quand | Statut |
|-------|------|-------|--------|
| C1 | Documents d'architecture (ce fichier) | Maintenant | 🟢 |
| C2 | U04-A Director (camera_schema + 4 piliers) | Prochain sprint | 🟡 EN ATTENTE |
| C3 | U04-B Darkroom (brainstorming infra) | Après C2 | 🔴 PLANIFIÉ |
| C4 | U04-B Darkroom (implémentation) | Après C3 | 🔴 PLANIFIÉ |

## RÉFÉRENCES
- [PRD §U04](../TRACKING/EXODUS_V2_PRD.md) — Spécifications techniques
- [VALIDATION §U04](../TRACKING/EXODUS_V2_VALIDATION.md) — 5 critères binaires
- [TRACKING U04](../TRACKING/TRACKING_U04.md) — Backlog détaillé
- [ROADMAP](../TRACKING/EXODUS_V2_ROADMAP.md) — Plan de conquête

> **Loi du Béton** : Ce document est la source de vérité pour l'architecture U04.
