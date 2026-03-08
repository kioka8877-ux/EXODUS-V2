# 📖 GUIDE UTILISATEUR — EXODUS V2

> Transforme n'importe quelle vidéo virale en animation Roblox cinématique 4K/120FPS

---

## Table des Matières

1. [Qu'est-ce qu'EXODUS V2 ?](#1-quest-ce-quexodus-v2-)
2. [Prérequis](#2-prérequis)
3. [Installation Express (5 minutes)](#3-installation-express-5-minutes)
4. [Architecture de la Flotte](#4-architecture-de-la-flotte)
5. [Workflow : De la Vidéo Source au Film Final](#5-workflow--de-la-vidéo-source-au-film-final)
6. [Commandes Marshal (Transferts Inter-Frégates)](#6-commandes-marshal-transferts-inter-frégates)
7. [Les Modèles IA](#7-les-modèles-ia)
8. [Dépannage](#8-dépannage)
9. [FAQ](#9-faq)
10. [Glossaire](#10-glossaire)

---

## 1. Qu'est-ce qu'EXODUS V2 ?

EXODUS V2 est un pipeline de production automatisé qui transforme des vidéos sources (clips viraux, scènes de référence) en animations Roblox de qualité cinématique, en 4K et 120 images par seconde.

Le système est découpé en **7 unités autonomes** appelées « frégates ». Chaque frégate gère une étape précise de la production : analyse de la vidéo, capture de mouvement, assemblage de l'acteur, construction des décors, mise en caméra, post-production, et enfin assemblage final.

**Ce que tu obtiens à la fin** : un fichier vidéo MP4 (ou MOV) en 4K/120FPS, prêt à être publié.

**Comment ça fonctionne** :
- Tu fournis une vidéo source (un clip viral par exemple)
- La frégate U00 (CORTEX) l'analyse et génère un plan de production JSON
- Chaque frégate suivante prend le relais automatiquement
- U06 (AIRCRAFT CARRIER) produit le film final avec interpolation RIFE 120FPS

**Où ça tourne** :
- **Google Colab** — Les notebooks s'exécutent gratuitement dans ton navigateur
- **Google Drive** — Tous les fichiers, modèles IA et rendus sont stockés sur ton Drive personnel
- Pas besoin d'installer quoi que ce soit sur ton ordinateur

**Points forts** :
- 100% cloud, exécutable depuis un téléphone ou un Chromebook
- Zéro copie manuelle grâce aux Phantom Links entre frégates
- Les modèles IA sont téléchargés une seule fois et persistent sur le Drive
- Chaque frégate fonctionne de manière autonome (pas de dépendance cachée)

---

## 2. Prérequis

**Obligatoire** :
- Un **compte Google** (gratuit) — pour accéder à Colab et au Drive
- **~1 Go d'espace Drive libre** minimum (installation standard sans GPU)
- Un **navigateur web récent** (Chrome, Firefox, Edge)

**Optionnel** :
- **~5 Go d'espace Drive** si tu veux les modèles GPU (DepthAnything + SAM)
- Une **clé API Gemini** (gratuite sur [aistudio.google.com](https://aistudio.google.com)) — nécessaire pour U00 CORTEX (analyse vidéo)
- Un **runtime GPU** sur Colab — recommandé pour U03 (décors) et U06 (assemblage final)

**Scénarios de stockage** :

| Scénario | Espace Drive | Contenu |
|----------|-------------|---------|
| Minimum | ~300 MB | Blender uniquement |
| Standard | ~420 MB | Blender + RIFE + MCprep + HDRi + Real-ESRGAN |
| Complet GPU | ~4.2 GB | Standard + DepthAnything V2 + SAM |

---

## 3. Installation Express (5 minutes)

L'installation complète se fait depuis un seul notebook : **`EXO_00_GENESIS.ipynb`**.

### Étape 1 — Ouvrir le notebook dans Colab

1. Va sur le dépôt GitHub du projet
2. Ouvre le fichier `EXO_00_GENESIS.ipynb`
3. Clique sur le bouton **"Open in Colab"** (ou copie l'URL dans `colab.research.google.com`)

### Étape 2 — Exécuter les cellules 1 à 5

Exécute chaque cellule dans l'ordre avec le bouton ▶️ (ou `Ctrl+Entrée`) :

| Cellule | Durée | Ce qu'elle fait |
|---------|-------|-----------------|
| 1 — Mount Drive | ~10s | Monte ton Google Drive |
| 2 — Structure | ~30s | Clone le repo et crée les dossiers sur le Drive |
| 3 — Déploiement | ~15s | Copie les scripts dans chaque frégate |
| 4 — Blender | ~2 min | Télécharge Blender 4.0 (~300 MB) |
| 5 — Modèles IA | ~1 min | Télécharge RIFE, MCprep, HDRi, Real-ESRGAN (~120 MB) |

La cellule 1 te demandera d'autoriser l'accès à ton Drive — accepte.

La cellule 4 (Blender) est la plus longue : compte environ 2 minutes. L'archive est téléchargée directement sur le Drive (pas de transit par la mémoire Colab).

### Étape 3 — (Optionnel) Modèles GPU

Si tu as un runtime GPU activé et que tu comptes utiliser U03 (décors avec DepthAnything + SAM) :

1. Va dans **Runtime → Change runtime type → GPU**
2. Exécute la **cellule 6** (~3.8 GB à télécharger, ~5 min)

Tu peux ignorer cette cellule et y revenir plus tard sans problème.

### Étape 4 — Vérifier l'installation

Exécute la **cellule 7** (diagnostic). Tu devrais voir quelque chose comme :

```
🏗️ STRUCTURE DES FRÉGATES
──────────────────────────────────────────────────
  ✅ 00_CORTEX_HQ — Cerveau — Analyse vidéo (6 fichiers code)
  ✅ 01_ANIMATION_ENGINE — Âme — MoCap + Facial (8 fichiers code)
  ✅ 02_LOGISTICS_DEPOT — Arsenal — Props (9 fichiers code)
  ...

🎨 BLENDER
──────────────────────────────────────────────────
  ✅ Blender 4.0.0

🤖 MODÈLES IA
──────────────────────────────────────────────────
  ✅ RIFE FlowNet (14.2 MB)
  ✅ RIFE v4.6 (14.8 MB)
  ✅ MCprep Addon (2.1 MB)
  ...

🎉 EXODUS EST OPÉRATIONNEL — L'Empire peut commencer la production !
```

Si des ❌ apparaissent, relance la cellule correspondante (4 pour Blender, 5 pour les modèles).

---

## 4. Architecture de la Flotte

### Les 7 Frégates

| Unité | Nom | Mission | Entrée | Sortie |
|-------|-----|---------|--------|--------|
| U00 | CORTEX HQ | Analyse vidéo par IA | Vidéo source (.mp4) | PRODUCTION_PLAN.JSON |
| U01 | ANIMATION ENGINE | Extraction MoCap corps + visage | PRODUCTION_PLAN.JSON + body_motion.fbx | Animation fusionnée (.blend/.abc) |
| U02 | LOGISTICS DEPOT | Assemblage Acteur + Props | Animation .blend + Avatar Roblox | Acteur équipé (.abc) |
| U03 | SCENOGRAPHY DOCK | Construction décors PBR/HDRi | Carte brute + PRODUCTION_PLAN.JSON | Environnement (.blend) |
| U04 | PHOTOGRAPHY WING | Tracking caméra + Éclairage | Vidéo ref + Scène 3D | Scène prête au rendu (.blend) |
| U05 | ALCHEMIST LAB | Post-production + Color Grading | Séquences EXR rendues | Frames gradées (.png) |
| U06 | AIRCRAFT CARRIER | Assemblage final + RIFE 120FPS | Frames finales + audio | Vidéo 4K/120FPS (.mp4) |

### Flux de production

```
  [VIDÉO SOURCE]
       │
       ▼
  ┌──────────┐
  │ U00      │──────► PRODUCTION_PLAN.JSON
  │ CORTEX   │
  └──────────┘
       │
       ▼
  ┌──────────┐
  │ U01      │──────► Animation fusionnée (.blend/.abc)
  │ ANIMATION│
  └──────────┘
       │
       ▼
  ┌──────────┐
  │ U02      │──────► Acteur équipé (.abc)
  │ LOGISTICS│
  └──────────┘
       │
       │      ┌──────────┐
       │      │ U03      │──────► Environnement (.blend)
       │      │SCENOGRAPH│
       │      └──────────┘
       │           │
       ▼           ▼
  ┌──────────────────────┐
  │ U04                  │──────► Scène prête au rendu (.blend)
  │ PHOTOGRAPHY          │        [RENDU DANS BLENDER]
  └──────────────────────┘
              │
              ▼
  ┌──────────┐
  │ U05      │──────► Frames gradées (.exr/.png)
  │ ALCHEMIST│
  └──────────┘
              │
              ▼
  ┌──────────┐
  │ U06      │──────► VIDÉO FINALE 4K/120FPS
  │ CARRIER  │        (.mp4 + .mov)
  └──────────┘
```

### Doctrine d'Étanchéité

Chaque frégate est une **île autonome**. Les scripts d'une frégate n'accèdent jamais aux dossiers d'une autre frégate. Elles communiquent uniquement via leurs dossiers `IN_*/` (entrée) et `OUT_*/` (sortie).

Les **Phantom Links** (`_LINK.json`) permettent à une frégate de lire directement le dossier `OUT/` de la précédente sans copie physique. C'est un fichier de 50 octets qui pointe vers la source — zéro duplication, zéro transfert.

### Le dossier EXODUS_AI_MODELS

C'est le dépôt partagé pour tous les modèles IA et outils :

```
EXODUS_AI_MODELS/
├── blender-4.0.0-linux-x64/   ← Blender portable
├── RIFE/                       ← Modèles interpolation frames
├── REALESRGAN/                 ← Modèle upscale x4
├── McPrep/                     ← Addon Minecraft pour Blender
├── HDRi/                       ← Éclairages studio .exr
├── DepthAnything/              ← Estimation de profondeur (GPU)
└── SAM/                        ← Segmentation (GPU)
```

---

## 5. Workflow : De la Vidéo Source au Film Final

Chaque frégate dispose de **2 notebooks** :
- **CONTROL** (`EXO_XX_CONTROL.ipynb`) — Mode debug, traitement d'une seule vidéo, étape par étape
- **PRODUCTION** (`EXO_XX_PRODUCTION.ipynb`) — Mode batch, traitement automatique de toutes les vidéos

### U00 — CORTEX HQ (Analyse Vidéo)

Analyse ta vidéo source avec Gemini (IA Google) et génère un `PRODUCTION_PLAN.JSON`.

- **Entrée** : Vidéo source dans `00_CORTEX_HQ/IN_VIDEO_SOURCE/`
- **Sortie** : `PRODUCTION_PLAN.JSON` dans `OUT_PRODUCTION_PLAN/`
- **Notebook** : `EXO_00_CORTEX_PRODUCTION.ipynb` (nécessite clé API Gemini)

```bash
python EXO_00_CORTEX.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 --input-video source.mp4
```

### U01 — ANIMATION ENGINE (MoCap)

Extrait le mouvement corporel et les expressions faciales, fusionne en animation Blender.

- **Entrée** : `PRODUCTION_PLAN.JSON` (U00) + `body_motion.fbx` (MoCap Mixamo)
- **Sortie** : Animation `.blend` / `.abc` dans `OUT_MOTION_DATA/`
- **Phantom Link** : `!python EXO_MARSHAL.py --unit U01 --mode link`

### U02 — LOGISTICS DEPOT (Assemblage Acteur)

Assemble l'avatar Roblox + animation U01 + props. Bypass auto si `requires_u02: false`.

- **Entrée** : Animation `.blend` (U01) + Avatar Roblox + Props
- **Sortie** : Acteur équipé `.abc` dans `OUT_BAKED_ACTORS/`
- **Phantom Link** : `!python EXO_MARSHAL.py --unit U02 --mode link`

### U03 — SCENOGRAPHY DOCK (Décors)

Construit les environnements 3D (PBR, HDRi). Utilise DepthAnything + SAM si disponibles.

- **Entrée** : Carte brute `IN_MAP_RAW/` + `PRODUCTION_PLAN.JSON` (U00)
- **Sortie** : Environnement `.blend` dans `OUT_PREMIUM_SCENE/`
- **Phantom Link** : `!python EXO_MARSHAL.py --unit U03 --mode link`
- Active le runtime GPU si tu utilises DepthAnything/SAM

### U04 — PHOTOGRAPHY WING (Caméra)

Configure le tracking caméra et l'éclairage cinématique. Après cette étape, tu lances le **rendu Blender** manuellement.

- **Entrée** : Vidéo de référence + Scène 3D (`.blend` de U02 et U03)
- **Sortie** : Scènes avec caméra/lumières dans `OUT_CAMERA_LOGIC/`

### U05 — ALCHEMIST LAB (Post-Production)

Applique le color grading, les LUTs, et le compositing.

- **Entrée** : Séquences EXR rendues (U04) dans `IN_RAW_FRAMES/`
- **Sortie** : Frames gradées `.png` dans `OUT_FINAL_FRAMES/`
- **Phantom Link** : `!python EXO_MARSHAL.py --unit U05 --mode link`

### U06 — AIRCRAFT CARRIER (Assemblage Final)

Interpolation RIFE → 120FPS, upscale Real-ESRGAN → 4K, encodage final AV1/H.265/ProRes.

- **Entrée** : Frames finales + audio dans `IN_ASSEMBLY_KIT/`
- **Sortie** : Vidéo 4K/120FPS dans `OUT_FINAL_MOVIE/`
- **Phantom Link** : `!python EXO_MARSHAL.py --unit U06 --mode link`
- Active le runtime GPU pour RIFE

---

## 6. Commandes Marshal (Transferts Inter-Frégates)

Le **Marshal** (`EXO_MARSHAL.py`) est le validateur logistique du pipeline. Il ne déplace et ne supprime jamais rien — il vérifie et crée des liens.

### Phantom Link — Lier les frégates

Au lieu de copier manuellement les fichiers d'une frégate à l'autre, crée un Phantom Link :

```bash
python EXO_MARSHAL.py --unit U05 --mode link --verbose
```

Cela crée un fichier `_LINK.json` (50 octets) dans chaque dossier `IN_*/` de U05, pointant vers les `OUT_*/` de la frégate source. Zéro copie, zéro espace disque consommé.

### Check-out — Valider les sorties

Vérifie que les sorties d'une frégate sont complètes avant de passer à la suivante :

```bash
python EXO_MARSHAL.py --unit U04 --mode check-out --verbose
```

### Check-in — Valider les entrées

Vérifie que les entrées d'une frégate sont disponibles (via fichiers locaux ou Phantom Links) :

```bash
python EXO_MARSHAL.py --unit U05 --mode check-in --verbose
```

### Validate — Vérification complète

Exécute check-out + check-in en une seule commande :

```bash
python EXO_MARSHAL.py --unit U05 --mode validate --verbose
```

### Cleanup — Libérer l'espace

Après la production complète, libère l'espace des frames intermédiaires :

```bash
python EXO_MARSHAL.py --unit U04 --mode cleanup
```

Le cleanup vérifie que la frégate suivante a terminé son travail avant de supprimer quoi que ce soit. Utilise `--force` pour passer outre (à tes risques).

---

## 7. Les Modèles IA

### Récapitulatif

| Modèle | Taille | Frégate | Usage | Criticité |
|--------|--------|---------|-------|-----------|
| Blender 4.0 | ~300 MB | Toutes | Rendu 3D, compositing | 🔴 Critique |
| RIFE flownet.pkl | ~15 MB | U06 | Interpolation de frames | 🟢 Standard |
| RIFE rife46.pkl | ~15 MB | U06 | Interpolation (alt.) | 🟢 Standard |
| MCprep addon | ~2 MB | U03 | Workflow Minecraft → Blender | 🟢 Standard |
| HDRi studio 1K/2K/4K | ~15 MB | U03 | Éclairage studio | 🟢 Standard |
| Real-ESRGAN x4v3 | ~64 MB | U06 | Upscale IA | 🟢 Standard |
| DepthAnything V2 ViT-L | ~1.4 GB | U03 | Estimation de profondeur | 🟡 GPU optionnel |
| SAM ViT-H | ~2.4 GB | U03 | Segmentation d'image | 🟡 GPU optionnel |

### Re-télécharger un modèle manquant

Si un modèle est manquant ou corrompu, relance simplement la cellule correspondante dans `EXO_00_GENESIS.ipynb` :
- **Cellule 4** pour Blender
- **Cellule 5** pour les modèles standard (RIFE, MCprep, HDRi, Real-ESRGAN)
- **Cellule 6** pour les modèles GPU (DepthAnything, SAM)

Les cellules vérifient si le fichier existe déjà avant de télécharger — seuls les fichiers manquants sont re-téléchargés.

### Alternative CLI

Tu peux aussi utiliser `EXO_SETUP_MODELS.py` directement :

```bash
python EXO_SETUP_MODELS.py --asset rife       # RIFE uniquement
python EXO_SETUP_MODELS.py --asset mcprep      # MCprep uniquement
python EXO_SETUP_MODELS.py --asset hdri        # HDRi uniquement
python EXO_SETUP_MODELS.py --dry-run           # Vérifier sans télécharger
python EXO_SETUP_MODELS.py --list              # Lister tous les assets
```

---

## 8. Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| « Drive non monté » / `FileNotFoundError` | Drive pas monté | Relance cellule 1 du Genesis |
| « Blender non trouvé » | Téléchargement incomplet | Relance cellule 4. Si ça persiste, supprime `EXODUS_AI_MODELS/blender-4.0.0-linux-x64/` et relance |
| « Out of memory » / Crash | RAM insuffisante | Passe en runtime GPU (Runtime → Change runtime type → GPU) ou réduis la résolution |
| « Permission denied » | Droits Drive insuffisants | Déconnecte/reconnecte le Drive, vérifie que `DRIVE_EXODUS_V2` existe |
| « Modèle manquant » | Téléchargement échoué | Relance cellule 5 (standard) ou 6 (GPU) — les fichiers existants sont ignorés |
| « Phantom Link cassé » | Frégate source n'a pas produit ses outputs | Vérifie les `OUT_*/` de la source, relance `EXO_MARSHAL.py --unit UXX --mode link` |
| Timeout / Déconnexion Colab | Session expirée (~12h inactivité) | Tes fichiers Drive sont intacts. Reconnecte, monte le Drive, reprends. U06 supporte le checkpoint (`resume: True`) |
| « wget: unable to resolve host » | Réseau temporaire | Attends 30s et relance la cellule. Sinon : Runtime → Restart runtime |

---

## 9. FAQ

**C'est payant ?**
Non. Google Colab offre un tier gratuit avec accès GPU limité. Google Drive offre 15 Go gratuits. EXODUS V2 est un projet open source.

**Combien de temps pour produire un film ?**
Ça dépend de la durée de la vidéo source et du runtime Colab. En ordre de grandeur : ~15 minutes pour 1 minute de vidéo source sur un GPU T4. Sur A100 (Colab Pro), c'est 2 à 3 fois plus rapide.

**Puis-je utiliser EXODUS sur mon PC local ?**
Oui. Les scripts Python fonctionnent en local si tu as Blender 4.0 installé et les modèles IA téléchargés. Remplace simplement les chemins `/content/drive/...` par tes chemins locaux.

**Quel GPU est recommandé ?**
- **T4** (Colab gratuit) : fonctionne pour toutes les frégates, suffisant pour la plupart des productions
- **A100** (Colab Pro, ~10$/mois) : 3x plus rapide, recommandé pour les vidéos longues (>3 min)
- **CPU seul** : possible pour U00-U02 et U05, mais U03, U04 et U06 sont très lents sans GPU

**Mes fichiers sont-ils en sécurité ?**
Tout reste sur ton Google Drive personnel. Aucun fichier n'est envoyé vers des serveurs tiers. Les sessions Colab sont éphémères, mais le Drive persiste.

**Est-ce que je perds tout si Colab se déconnecte ?**
Non. Seule la session de calcul est perdue. Tous les fichiers sur le Drive (modèles, rendus, plans de production) sont intacts. Reconnecte-toi et reprends.

**Puis-je traiter plusieurs vidéos en parallèle ?**
Chaque frégate traite les vidéos en batch (mode PRODUCTION). Cependant, les frégates doivent s'exécuter séquentiellement : U00 → U01 → U02 → ... → U06.

**Comment mettre à jour EXODUS V2 ?**
Relance la cellule 2 du notebook Genesis. Si le repo est déjà cloné, supprime le dossier `/content/EXODUS-V2` puis relance la cellule pour obtenir la dernière version.

---

## 10. Glossaire

| Terme | Définition |
|-------|-----------|
| **Frégate / Unité** | Module autonome du pipeline EXODUS. Chaque frégate gère une étape de production (U00 à U06). |
| **PRODUCTION_PLAN.JSON** | Plan de production généré par U00 CORTEX. Décrit chaque scène, les personnages, mouvements, accessoires. |
| **Phantom Link** | Lien virtuel zero-copy entre frégates. Un fichier `_LINK.json` de 50 octets qui pointe vers le dossier source. |
| **Marshal** | Validateur logistique inter-frégates. Vérifie les entrées/sorties et crée les Phantom Links. |
| **Scellée** | Statut d'une frégate qui a été validée, testée et déclarée stable. |
| **CODEBASE/** | Sous-dossier de chaque frégate contenant les scripts Python et notebooks. |
| **IN_* / OUT_*** | Dossiers d'entrée et de sortie de chaque frégate. |
| **RIFE** | Real-Time Intermediate Flow Estimation — modèle IA d'interpolation de frames (30FPS → 120FPS). |
| **Real-ESRGAN** | Modèle IA d'upscale — augmente la résolution des images (1080p → 4K). |
| **MCprep** | Addon Blender pour importer et améliorer les mondes Minecraft. |
| **HDRi** | High Dynamic Range Image — image panoramique utilisée pour l'éclairage réaliste en 3D. |
| **PBR** | Physically Based Rendering — matériaux réalistes basés sur les propriétés physiques de la lumière. |
| **Architecture Sacrée** | Nom donné à la structure de dossiers standardisée créée par `EXO_GENESIS_DRIVE.py`. |
| **Bypass** | Mode de U02 qui saute l'assemblage si le plan de production indique qu'aucun prop n'est nécessaire. |
| **Drive Root** | Dossier racine sur le Drive : `DRIVE_EXODUS_V2/`. Toute la structure EXODUS vit ici. |
