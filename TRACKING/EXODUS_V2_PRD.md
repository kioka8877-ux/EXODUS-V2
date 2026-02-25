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
- 6 moteurs parallèles : Gemini (narrative), T2M (motion prompt), Facial JSON (ARKit timing), DepthAnything V2 (depth maps), SAM (segmentation), FOV/Ratio (camera metadata)
- Exécution séquentielle si VRAM < 15GB (Colab T4)
- DepthAnything V2 : génère une séquence .png de depth maps (1 par frame ou keyframe)
- SAM : segmentation sémantique des surfaces (route, herbe, mur, ciel, eau, verre)
- Gemini 2.5 Flash API : analyse narrative + émotionnelle segment par segment
- Extraction audio via FFmpeg (`-vn -acodec pcm_s16le`)
- FOV/Ratio : extraction des métadonnées de résolution + estimation de focale

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
- 3 couches : Observation (données Gemini U00), Translation (émotion → 52 ARKit Shape Keys), Micro-Jitter (bruit procédural)
- Courbes de Bézier pour transitions (pas d'interpolation linéaire)
- Passage obligatoire par état "neutre" entre émotions opposées (ex: joie → neutre → colère)
- Micro-Jitter : bruit procédural sur yeux et bouche (amplitude 0.01-0.03, fréquence 8-12Hz)
- Rhubarb lip-sync : désactive les shape keys bouche pendant les segments de parole (priorité Rhubarb)
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
- **RIFE 4.0** : interpolation 30 → 120 FPS
- **Ratio Lock Strict** : résolution et ratio (9:16 ou 16:9) depuis métadonnées U00 — zéro letterbox
- **Codec** : H.265/HEVC, CRF 16-18
- **Poids cible** : ~450MB-1.5GB pour 60 secondes
- **Audio Sync** : synchronisation depuis `audio_source.wav` de U00
- Batch processing par segments de 10s pour optimiser VRAM
- Check-sum résolution : sortie = entrée U00

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

### PRODUCTION_PLAN.JSON (Généré par U00)

```json
{
  "project_id": "EXO_BROOKHAVEN_01",
  "format": { "resolution": [1080, 1920], "ratio": "9:16", "fps_source": 30 },
  "motion_engine": {
    "saymotion_prompt": "Human actor kneeling...",
    "requires_u02": true,
    "props_detected": ["rat_model", "phone"]
  },
  "facial_engine": {
    "segments": [
      { "start": 0.0, "end": 2.5, "expression": "joy", "intensity": 0.8 }
    ]
  },
  "scenography_logic": {
    "vibe": "luxury_villa",
    "pbr_targets": ["road", "pool_water", "glass_windows"],
    "lighting_ref": "sunset_golden_hour"
  }
}
```

### facial_animation.json (Généré par U00, Consommé par U01)

```json
{
  "sequence_id": "ACTOR_01_SCENE_0",
  "facial_animation": [
    {
      "time_start": 0.0,
      "time_end": 1.5,
      "expression": "suspicious",
      "eyes": "narrowed",
      "mouth": "pursed lips",
      "intensity": 0.7,
      "apex_time": 0.8
    }
  ]
}
```

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
