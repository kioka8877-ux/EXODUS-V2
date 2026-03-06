# EXODUS V2 — PRD (Bible de l'Arme)
> Spécifications techniques consolidées — 7 Frégates + MARSHAL

## VISION
Transmuter n'importe quelle vidéo virale en animation Roblox cinématique 4K/120FPS.
**Objectif** : 300 000 USD / 30 jours.

## LES 10 LOIS
1. **Loi du Levier** : Effort 1 / Résultat 100
2. **Loi du Flux Sacré** : Stratégie → IA → Code → Cash
3. **Loi de l'Étanchéité** : Les Frégates sont des îles (Silos)
4. **Loi du Goulot** : Toute la puissance sur le maillon faible
5. **Loi de la Surqualité** : Transmuter la source (4K/120FPS)
6. **Loi de l'Agnosticisme** : Indépendance totale des sources
7. **Loi du Miroir** : Fidélité temporelle à la frame près
8. **Loi de la Télécommande** : Calcul déporté (Cloud/Colab)
9. **Loi du Béton** : Pas de fichier, pas d'existence
10. **Loi de l'Empire** : Objectif unique (300k$ / 30 jours)

## ARSENAL IMPÉRIAL (IDs fixes)
- Gemini 2.5 Flash (API) — Semantic analysis
- DepthAnything V2 — Depth map generation
- SAM (Segment Anything) — Semantic segmentation
- T2M / SayMotion / MDM — Motion synthesis
- RIFE 4.0 — Frame interpolation (30→120 FPS)
- Real-ESRGAN — Upscaling
- Rhubarb Lip-Sync — Audio-based lip sync
- fSpy — Camera perspective extraction
- Blender 4.0 — 3D engine (headless)
- FFmpeg — Encoding (H.265/HEVC, CRF 16-18)
- OpenCV + Pillow — Image processing

---

## SPÉCIFICATIONS PAR FRÉGATE

### U00 — CORTEX HQ (Le Cerveau)

**Mission** : Analyser la vidéo source via 6 moteurs parallèles. Extraire TOUTES les données nécessaires aux frégates en aval. Générer le PRODUCTION_PLAN.JSON qui orchestre l'empire.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| Vidéo source | .mp4 | Empereur (upload) |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| PRODUCTION_PLAN.JSON | .json | ALL (U01-U06, MARSHAL) |
| motion_synthesis_prompt.txt | .txt | Empereur → SayMotion |
| facial_animation.json | .json | U01 |
| DEPTH_MAP/ (séquence) | .png | U03 |
| semantic_masks.json | .json | U03 |
| camera_fov_ratio | .json (metadata) | U04 |
| audio_source.wav | .wav | U06 |

**Key Technical Specs**

**Architecture 6-Moteurs (exécution séquentielle) :**

| Phase | Moteur | Technologie | VRAM | Output |
|-------|--------|-------------|------|--------|
| 1-CPU | M2 Audio | FFmpeg `-vn -acodec pcm_s16le` | 0 GB | `audio_source.wav` |
| 1-CPU | M3 FOV | OpenCV métadonnées vidéo | 0 GB | `camera_fov_ratio.json` |
| 2-API | M1 Gemini | Gemini 2.5 Flash + `response_schema` | 0 GB | Master JSON (3 blocs) |
| 2-API | M4 Facial | Dispatcher (extraction bloc) | 0 GB | `facial_animation.json` |
| 2-API | M5 Motion | Dispatcher (extraction bloc) | 0 GB | `motion_synthesis_prompt.txt` |
| 3-GPU | M6 Depth | DepthAnything V2 (vitl) | ~3.5 GB | `DEPTH_MAP/*.png` |
| 4-GPU | M7 SAM | SAM vit_h | ~4 GB | `semantic_masks.json` |

**Protocole VRAM (Loi VIII) :**
- Exécution strictement séquentielle : jamais 2 modèles GPU chargés simultanément
- Entre Phase 3 et Phase 4 : `del model` → `gc.collect()` → `torch.cuda.empty_cache()` → vérification VRAM < 0.5 GB
- VRAM peak global : ~4 GB (27% de la capacité T4)

**Verrouillage Arsenal (`response_schema`) :**
- Tous les IDs (characters, props, environments, animations, camera, lighting, audio) contraints par `enum` dans le `response_schema` Gemini
- Si aucun match : Gemini est forcé de choisir `"generic_prop"` (seul fallback dans l'enum)
- Pattern anti-null : `"none"` comme valeur enum au lieu de `null` pour les champs optionnels
- Double sécurité : `validate_json_output()` en post-traitement (ceinture + bretelles)

**Dispatcher :**
- Gemini retourne UN Master JSON monolithique avec 3 blocs (`production_plan`, `facial_animation`, `motion_synthesis`)
- Le script Python découpe en 3 fichiers séparés : `PRODUCTION_PLAN.JSON`, `facial_animation.json`, `motion_synthesis_prompt.txt`
- `normalize_timecodes()` force la cohérence temporelle (segments faciaux clampés sur bornes scène)

**Résilience :**
- `MotorStatus` : suivi par moteur (success/failed/partial)
- `flags` dans le JSON final : `all_motors_ok`, `partial_failure[]`, `manual_review_required`
- Mode `--rerun <motor>` : relance un seul moteur sans retoucher les fichiers Gemini existants

---

### U01 — ANIMATION ENGINE (Le Souffle)

**Mission** : Donner vie à l'avatar Roblox via Emotional Intent Transfer. Convertir les descriptions émotionnelles de Gemini en 52 ARKit Shape Keys avec Micro-Jitter et lip-sync Rhubarb.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| PRODUCTION_PLAN.JSON | .json | U00 |
| facial_animation.json | .json | U00 |
| body_motion.fbx | .fbx | Empereur (SayMotion) |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| actor_animated.blend | .blend | U02 |
| actor_animated.abc | .abc | U02 (backup) |

**Key Technical Specs**
- **ZÉRO EMOCA** — suppression totale de la dépendance EMOCA
- **Module fondation : `expression_schema.py`** (Bible Anatomique — 7 Piliers) :
  - Pilier 1 : 15 EXPRESSION_PRESETS (joy, sadness, anger, fear, surprise, disgust, neutral, suspicious, determined, confused, pain, love, bored, excited, shocked) × 52 ARKit Shape Keys
  - Pilier 2 : Matrice des Conflits (combinaisons anatomiques interdites)
  - Pilier 3 : Table des Oppositions (passage obligatoire par neutre entre émotions antagonistes)
  - Pilier 4 : Ranges Anatomiques (clampage esthétique Roblox)
  - Pilier 5 : Courbes d'Intensité (scaling non-linéaire de l'intensity U00)
  - Pilier 6 : Micro-Expressions Involontaires (presets blink/tics)
  - Pilier 7 : EYE_PRESETS (9 états) + MOUTH_PRESETS (8 états) + Règle de fusion (expression base + overrides par zone)
- **3 Leviers natifs Blender (Pareto 80/20)** :
  - F-Curve Bézier natif : interpolation Bézier entre keyframes (zéro code custom)
  - F-Curve Noise Modifier : Micro-Jitter sur yeux+bouche (amplitude 0.01-0.03, fréquence 8-12Hz, blend ADD)
  - NLA Editor : layering multicouche (expression strip + eyes override strip + mouth override strip), influence = intensity
- Rhubarb lip-sync (Phase 2) : NLA strip dédié, priorité bouche pendant parole
- Export dual : `.blend` + `.abc` (Alembic cache)
- Format JSON d'entrée : segments avec `time_start`, `time_end`, `expression`, `eyes`, `mouth`, `intensity`, `apex_time`

---

### U02 — LOGISTICS DEPOT (L'Armurerie)

**Mission** : Équiper l'avatar avec les props détectés par U00. Activation conditionnelle uniquement — skip complet si aucun prop nécessaire.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| actor_animated.blend | .blend | U01 |
| PRODUCTION_PLAN.JSON | .json | U00 |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| actor_equipped.blend | .blend | U04 |
| actor_equipped.abc | .abc | U04 (backup) |

**Key Technical Specs**
- Activation conditionnelle via `requires_u02` boolean dans PRODUCTION_PLAN.JSON
- Si `requires_u02 == false` : skip complet, transfert direct U01 → U04
- Si `requires_u02 == true` : exécution normale (props_loader → socketing_engine → timeline_manager → final_baker)
- MVP : aucune amélioration complexe nécessaire au-delà du bypass conditionnel

---

### U03 — SCENOGRAPHY DOCK (La Forge du Décor)

**Mission** : Construire l'environnement 3D via le Tri-Layer System. Remplacer McPrep par une architecture basée sur depth maps et segmentation sémantique.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| DEPTH_MAP/ (séquence) | .png | U00 |
| semantic_masks.json | .json | U00 |
| PRODUCTION_PLAN.JSON | .json | U00 |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| environment.blend | .blend | U04 |

**Key Technical Specs**
- **ZÉRO McPrep** — suppression totale de la dépendance McPrep
- **Couche A — Infinity Dome** : demi-sphère avec texture vidéo source (background distant)
- **Couche B — Displacement Mesh** : plan subdivisé (128x128 minimum) + Displace modifier alimenté par les depth maps de DepthAnything V2. Crée la géométrie 3D du sol et des structures proches.
- **Couche C — PBR Swap** : masques SAM identifient les surfaces (route, herbe, mur, eau, verre) → remplacement par matériaux PBR haute qualité
- **Shadow Catcher** : plan invisible sous l'avatar pour capter les ombres portées
- **Reflectivity Hack** : plans Glass BSDF positionnés sur les surfaces vitrées détectées par SAM
- **World Sync** : HDRi environnemental aligné sur l'exposition de la vidéo source

---

### U04 — PHOTOGRAPHY WING (L'Œil)

**Mission** : Placer la caméra avec fidélité cinématographique. 4 piliers : perspective lock, profondeur de champ automatique, shake procédural, éclairage volumétrique.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| actor_equipped.abc / .blend | .abc, .blend | U02 |
| environment.blend | .blend | U03 |
| camera_fov_ratio | .json | U00 |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| raw_frames/ | .exr, .png | U05 |
| render passes | .exr | U05 |

**Key Technical Specs**
- **Pilier A — Perspective Lock** : fSpy ou tracker Blender pour verrouiller la perspective source. Mouvement caméra limité à ±5% maximum.
- **Pilier B — Auto-DOF** : Empty parenté au buste de l'avatar → Depth of Field automatique. Arrière-plan flou naturel.
- **Pilier C — Shake Procédural** : Noise modifier sur les axes de rotation de la caméra dans le Graph Editor. Simule le tremblement d'une caméra portée.
- **Pilier D — Volume Scatter + Lampes Invisibles** : Volume Scatter atmosphérique + lampes invisibles alignées sur les sources lumineuses de la vidéo source.
- Alerte automatique si l'avatar sort du frustum caméra

---

### U05 — ALCHEMIST LAB (Le Philtre)

**Mission** : Fusion visuelle totale entre le rendu 3D et la vidéo source. L'avatar doit être indistinguable de l'environnement vidéo. Match Color, Grain, Bloom, Sharpness.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| raw_frames/ + render passes | .exr, .png | U04 |
| source_video_ref | .mp4 | U00 |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| graded_frames/ | .png (16 bits) | U06 |

**Key Technical Specs**
- **Match Color** : alignement histogramme (OpenCV) entre le rendu et la vidéo source — PAS de LUT
- **Film Grain Matching** : extraction du grain de la vidéo source → application sur le rendu. Pas juste ajouter du grain — matcher le grain existant.
- **Bloom/Glow Bleed** : les hautes lumières du rendu bavent sur le décor environnant
- **Sharpness Transfer** : flou de transfert — l'avatar ne doit pas être "trop net" par rapport au grain de la source
- Output en `.png 16 bits` pour préserver la dynamique
- Moteur : OpenCV + Pillow

---

### U06 — AIRCRAFT CARRIER (Le Vaisseau-Mère)

**Mission** : Assemblage final — interpolation 120FPS, upscale, encodage H.265, synchronisation audio. Le produit fini sort d'ici.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| graded_frames/ | .png | U05 |
| audio_source.wav | .wav | U00 |
| format metadata (ratio, resolution) | .json | U00 |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| final_video.mp4 | .mp4 (H.265) | Empereur (livrable) |

**Key Technical Specs**
- **Pipeline Frame-Based** : ZÉRO compression intermédiaire. Les frames PNG 16-bit de U05 traversent RIFE et Upscale sans JAMAIS être encodées en vidéo lossy. Seul l'encodage final compresse.
- **carrier_schema.py** (Bible du Vaisseau-Mère) : module de données pures (6 piliers), zéro dépendance externe, validation + self_test. Suit le pattern de camera_schema.py (U04) et alchemist_schema.py (U05).
- **3 Encoding Presets** :
  - `distribution` : SVT-AV1 CRF 30, ~300MB/60s — optimisé YouTube/TikTok
  - `distribution_h265` : libx265 CRF 20 + `--tune animation`, ~500MB/60s — fallback si AV1 indisponible
  - `master` : ProRes 422 HQ — archive lossless pour réédition
- **RIFE 4.0** : interpolation 30 → 120 FPS par chunks de 10 secondes (pic VRAM <10GB, pic disque ~3GB)
- **Ratio Lock Strict** : résolution et ratio (9:16 ou 16:9) depuis `format.resolution` et `format.ratio` du PRODUCTION_PLAN.JSON V2 — zéro letterbox
- **Checkpoint System** : reprise après crash au dernier chunk traité
- **Batch RIFE+Upscale fusionné** : chunk source → RIFE → upscale → append final video → delete chunk
- **Poids cible distribution** : 200-400MB pour 60 secondes (÷5 vs ancien pipeline)
- **`--tune animation`** : optimisation x265 pour contenu Roblox (aplats de couleur, mouvement prédictible)

---

### MARSHAL — L'INTENDANT (Le Fantôme)

**Mission** : Valider l'intégrité logistique entre chaque frégate. Ghost script qui vérifie les fichiers entrants et sortants. Bloque si corruption ou absence.

**Inputs**

| Source | Format | From |
|--------|--------|------|
| Fichiers OUT/ de la frégate source | Variés | Frégate source |
| Fichiers IN/ de la frégate destination | Variés | Frégate destination |

**Outputs**

| Element | Format | To |
|---------|--------|----|
| EXODUS_CAMPAIGN.LOG | .log (append) | Racine projet |
| Validation report | stdout | Empereur (CLI) |

**Key Technical Specs**
- CLI : `python EXO_MARSHAL.py --unit F04 --mode validate`
- **Out-Check** : vérifie la présence et le format des fichiers dans OUT/ avant transfert
- **In-Check** : valide la présence et le format des fichiers dans IN/ avant lancement
- **Bloque la frégate** si fichier manquant ou corrompu (exit code non-zero)
- **Campaign Log** : append horodaté dans `EXODUS_CAMPAIGN.LOG`
- Ghost script : copié dans chaque `CODEBASE/` lors de l'initialisation
- Manifeste de validation défini par unité (fichiers attendus par IN/ et OUT/)

---

## SCHÉMAS JSON DE RÉFÉRENCE

### Master JSON V2 (Généré par Gemini, découpé par Dispatcher)

Le Master JSON est la structure monolithique retournée par Gemini via `response_schema`. Le Dispatcher le découpe en 3 fichiers.

#### Bloc 1 — `production_plan` → `PRODUCTION_PLAN.JSON`

```json
{
  "production_plan": {
    "project_id": "EXO_SOURCE_001",
    "format": {
      "resolution": [1080, 1920],
      "ratio": "9:16",
      "fps_source": 30
    },
    "scenes": [
      {
        "scene_id": 1,
        "timecode_start": 0.0,
        "timecode_end": 5.200,
        "description": "Two characters running across a grass field",
        "characters": [
          {
            "character_id": "bacon_hair",
            "role": "protagonist",
            "actions": ["run", "jump"]
          }
        ],
        "props": [
          {
            "prop_id": "linked_sword",
            "quantity": 1,
            "interaction": "held"
          }
        ],
        "environment": {
          "environment_id": "grass_terrain",
          "vibe": "open_field_sunny",
          "pbr_targets": ["grass", "dirt_path"],
          "lighting_ref": "daylight"
        },
        "camera": {
          "style_id": "follow",
          "movements": ["tracking right to left"]
        },
        "audio": {
          "music_id": "epic_orchestral",
          "sfx": ["footstep", "sword_hit"],
          "ambient_id": "ambient_nature"
        }
      }
    ],
    "requires_u02": true,
    "production_notes": {
      "complexity_score": 6,
      "warnings": []
    }
  },
  "flags": {
    "all_motors_ok": true,
    "partial_failure": [],
    "partial_success": [],
    "manual_review_required": false,
    "warnings": []
  }
}
```

#### Bloc 2 — `facial_animation` → `facial_animation.json`

```json
{
  "sequence_id": "ACTOR_01",
  "facial_animation": [
    {
      "time_start": 0.0,
      "time_end": 2.500,
      "expression": "determined",
      "eyes": "focused_forward",
      "mouth": "closed_tight",
      "intensity": 0.8,
      "apex_time": 1.200,
      "low_visibility": false
    }
  ]
}
```

#### Bloc 3 — `motion_synthesis` → `motion_synthesis_prompt.txt`

Contenu texte brut (pas JSON) :
```
Human actor sprinting across open field, holding sword in right hand, jumps over obstacle at 3.5 seconds, lands firmly on both feet.
Duration: 8.0 seconds. Style: athletic_urgent.
```

### Enums Complets (contraints par `response_schema`)

#### Expressions faciales
`joy`, `sadness`, `anger`, `fear`, `surprise`, `disgust`, `neutral`, `suspicious`, `determined`, `confused`, `pain`, `love`, `bored`, `excited`, `shocked`

#### Direction des yeux
`focused_forward`, `looking_left`, `looking_right`, `looking_up`, `looking_down`, `narrowed`, `wide_open`, `closed`, `winking`

#### État de la bouche
`closed_tight`, `slightly_open`, `wide_open`, `smiling`, `frowning`, `pursed_lips`, `shouting`, `neutral`

#### Style de mouvement (motion_synthesis)
`casual`, `athletic`, `dramatic`, `comedic`, `aggressive`, `elegant`, `robotic`, `urgent`

#### Rôle personnage
`protagonist`, `antagonist`, `background`

#### Interaction prop
`held`, `placed`, `animated`, `worn`

#### Ratio vidéo
`9:16`, `16:9`, `4:3`, `1:1`

#### Valeur "none" (anti-null)
Tout champ optionnel utilise la valeur string `"none"` au lieu de `null`. Exemple :
- `"music_id": "none"` → pas de musique
- `"ambient_id": "none"` → pas d'ambiance

Les scripts aval testent : `if value != "none": # utiliser la valeur`

### Impact par Frégate

| Frégate | Fichier(s) consommé(s) | Champs clés lus |
|---------|----------------------|-----------------|
| U01 | `PRODUCTION_PLAN.JSON`, `facial_animation.json` | `scenes[].characters[].actions`, `facial_animation[].*` |
| U02 | `PRODUCTION_PLAN.JSON` | `requires_u02`, `scenes[].props[]` |
| U03 | `PRODUCTION_PLAN.JSON`, `DEPTH_MAP/*.png`, `semantic_masks.json` | `scenes[].environment.*`, depth maps, masks |
| U04 | `PRODUCTION_PLAN.JSON`, `camera_fov_ratio.json` | `format.*`, `scenes[].camera.*`, FOV data |
| U05 | `PRODUCTION_PLAN.JSON` | `scenes[].environment.lighting_ref` |
| U06 | `PRODUCTION_PLAN.JSON`, `audio_source.wav` | `format.*`, audio track |

---

## MATRICE DES FLUX

```
Vidéo Source → [U00 CORTEX] → PRODUCTION_PLAN.JSON → ALL
                    ├→ facial_animation.json → U01
                    ├→ DEPTH_MAP/ + semantic_masks.json → U03
                    ├→ camera_fov_ratio → U04
                    ├→ source_video_ref → U05
                    ├→ audio_source.wav → U06
                    └→ motion_synthesis_prompt.txt → Empereur → SayMotion → body_motion.fbx → U01

U01 → actor_animated.blend → U02 → actor_equipped.blend → U04
U03 → environment.blend → U04
U04 → raw_frames/ → U05 → graded_frames/ → U06 → final_video.mp4

MARSHAL : vérifie chaque transfert (Out-Check → In-Check)
```

---

## RÉFÉRENCES
- [STATE](./EXODUS_V2_STATE.md) — Diagnostic J0
- [ROADMAP](./EXODUS_V2_ROADMAP.md) — Plan de conquête
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires
- [RISKS](./EXODUS_V2_RISKS.md) — Analyse forensique
- [TRANSFERS](./EXODUS_V2_TRANSFER_LOG.md) — Registre des flux

> **Loi du Béton** : Pas de fichier, pas d'existence. Chaque spécification ci-dessus doit se traduire en code traçable par commit.
<!-- v2.3 — U06 ATOM-IC Specs -->

