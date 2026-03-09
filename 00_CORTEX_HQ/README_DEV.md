# Documentation Technique — FRÉGATE 00: CORTEX HQ

## 📋 Vue d'ensemble

CORTEX est le cerveau analytique du pipeline EXODUS V2. Il analyse des vidéos sources et génère des plans de production structurés (JSON) pour les autres frégates.

**Stack:** Python 3.10+ | Gemini 2.5 Flash | OpenCV

---

## 🚀 Installation

### Option A: Environnement Local

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la clé API
export GEMINI_API_KEY='votre_clé_api'
```

### Option B: Google Colab

```python
# Dans une cellule Colab
!pip install google-generativeai opencv-python-headless

import os
os.environ['GEMINI_API_KEY'] = 'votre_clé_api'

# Monter Google Drive
from google.colab import drive
drive.mount('/content/drive')
```

---

## 🎮 Interfaces Colab

Deux notebooks sont disponibles pour des usages différents:

### EXO_00_CORTEX_CONTROL.ipynb — Mode Développement

**Quand l'utiliser:**
- Pendant la phase de test (DELTA)
- Pour debugger des erreurs
- Pour tester différents prompts/modèles
- Pour inspecter les résultats en détail

**Fonctionnalités:**
- ✅ Vérification API
- 🖼️ Preview vidéo (frame + métadonnées)
- ✏️ Prompt éditable
- 🤖 Sélection de modèle
- 📋 Inspection JSON détaillée
- 🧪 Tests unitaires
- 🛡️ Validation Arsenal

**Cellules:** 13 cellules exécutables individuellement

### EXO_00_CORTEX_PRODUCTION.ipynb — Mode Batch

**Quand l'utiliser:**
- Après le scellage de l'unité
- Pour traiter plusieurs vidéos d'un coup
- Production de masse

**Fonctionnalités:**
- ⚡ Setup one-click
- 🏭 Traitement automatique de toutes les vidéos
- ⏭️ Skip des vidéos déjà traitées
- 📊 Rapport de batch

**Cellules:** 4 cellules seulement (Setup → Tir → Rapport)

### Accès aux notebooks

```
00_CORTEX_HQ/CODEBASE/
├── EXO_00_CORTEX.py               # Script principal
├── EXO_00_CORTEX_CONTROL.ipynb    # Notebook DEBUG
├── EXO_00_CORTEX_PRODUCTION.ipynb # Notebook BATCH
└── requirements.txt
```

---

## 🔑 Configuration API Gemini

1. Obtenir une clé API sur [Google AI Studio](https://aistudio.google.com/)
2. Configurer la variable d'environnement:

```bash
# Linux/Mac (temporaire)
export GEMINI_API_KEY='AIza...'

# Linux/Mac (permanent - ajouter à ~/.bashrc)
echo "export GEMINI_API_KEY='AIza...'" >> ~/.bashrc

# Windows PowerShell
$env:GEMINI_API_KEY='AIza...'

# Google Colab
import os
os.environ['GEMINI_API_KEY'] = 'AIza...'
```

---

## 📖 Utilisation

### Commande de Base

```bash
python EXO_00_CORTEX.py \
  --drive-root /chemin/vers/EXODUS \
  --input-video ma_video.mp4
```

### Options Complètes

| Option | Requis | Défaut | Description |
|--------|--------|--------|-------------|
| `--drive-root` | ✅ | - | Chemin racine EXODUS |
| `--input-video` | ✅ | - | Nom du fichier vidéo |
| `--output-name` | ❌ | Auto | Nom du fichier JSON |
| `--model` | ❌ | gemini-2.5-flash-lite | Modèle Gemini |
| `--dry-run` | ❌ | False | Mode test sans API |
| `--verbose` | ❌ | False | Logs détaillés |

### Exemples

```bash
# Analyse standard
python EXO_00_CORTEX.py \
  --drive-root /content/drive/MyDrive/EXODUS \
  --input-video tiktok_dance.mp4

# Mode test (sans API)
python EXO_00_CORTEX.py \
  --drive-root ./EXODUS_TEST \
  --input-video test.mp4 \
  --dry-run

# Avec modèle alternatif
python EXO_00_CORTEX.py \
  --drive-root /data/EXODUS \
  --input-video source.mp4 \
  --model gemini-2.5-flash-lite \
  --verbose
```

---

## 📁 Structure des Fichiers

```
00_CORTEX_HQ/
├── CODEBASE/
│   ├── EXO_00_CORTEX.py               # Script principal
│   ├── EXO_00_CORTEX_CONTROL.ipynb    # Notebook DEBUG
│   ├── EXO_00_CORTEX_PRODUCTION.ipynb # Notebook BATCH
│   └── requirements.txt                # Dépendances
├── IN_VIDEO_SOURCE/                    # Déposer les vidéos ici
│   └── video.mp4
├── OUT_MANIFEST/                       # JSON générés ici
│   └── PRODUCTION_PLAN_video.json
├── UNIT_00_SUBPLAN.md                  # Sous-plan technique
└── README_DEV.md                       # Cette documentation
```

---

## 📊 Format PRODUCTION_PLAN.JSON

### Structure Complète

```json
{
  "metadata": {
    "source_video": "video.mp4",
    "duration_seconds": 30.5,
    "fps": 30,
    "resolution": "1920x1080",
    "analysis_date": "2026-02-02",
    "cortex_version": "2.0"
  },
  "scenes": [
    {
      "scene_id": 1,
      "timecode_start": 0.0,
      "timecode_end": 5.0,
      "description": "Introduction avec personnage principal",
      "characters": [
        {
          "character_id": "bacon_hair",
          "role": "protagonist",
          "actions": ["idle", "wave"]
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
        "environment_id": "city_street",
        "modifications": ["Ajouter néons"]
      },
      "camera": {
        "style_id": "dolly",
        "movements": ["Travelling arrière lent"]
      },
      "lighting": {
        "preset_id": "neon",
        "adjustments": ["Renforcer bleu"]
      },
      "audio": {
        "music_id": "action_electronic",
        "sfx": ["sword_hit"],
        "ambient_id": "ambient_city"
      }
    }
  ],
  "production_notes": {
    "complexity_score": 7,
    "estimated_render_hours": 12,
    "special_requirements": ["Motion capture requis"],
    "warnings": ["Scène 3 contient mouvements rapides"]
  }
}
```

### IDs Valides (Arsenal Impérial)

Le script n'accepte QUE les IDs de l'Arsenal Impérial hardcodé:

- **Characters:** bacon_hair, noob, guest, builderman, robloxian_2_0, etc.
- **Props:** linked_sword, firebrand, classic_jeep, wooden_chair, sparkles, etc.
- **Environments:** classic_baseplate, grass_terrain, city_street, medieval_castle, etc.
- **Animations:** idle, walk, run, jump, wave, dance1, sword_slash, etc.
- **Camera:** static, follow, orbit, dolly, pan, cinematic, etc.
- **Lighting:** daylight, sunset, night, neon, dramatic, horror, etc.
- **Audio:** oof, sword_hit, epic_orchestral, ambient_city, etc.

Les IDs non reconnus sont automatiquement remplacés par `generic_prop`.

---

## 🔧 Troubleshooting

### Erreur: "GEMINI_API_KEY non définie"

```bash
# Vérifier la variable
echo $GEMINI_API_KEY

# Si vide, la définir
export GEMINI_API_KEY='votre_clé'
```

### Erreur: "Vidéo non trouvée"

Vérifier que la vidéo est dans:
- `00_CORTEX_HQ/IN_VIDEO_SOURCE/video.mp4`
- Ou spécifier le chemin complet avec `--input-video`

### Erreur: "opencv-python non installé"

```bash
pip install opencv-python-headless
```

### Erreur: "Échec après 3 tentatives"

- Vérifier la connexion internet
- Vérifier la validité de la clé API
- Réduire la taille de la vidéo (< 100MB recommandé)
- Essayer un autre modèle: `--model gemini-2.5-flash-lite`

### Mode Debug

```bash
python EXO_00_CORTEX.py \
  --drive-root ./EXODUS \
  --input-video test.mp4 \
  --verbose
```

---

## 🔄 Flux de Travail

```
1. Déposer vidéo dans IN_VIDEO_SOURCE/
          ↓
2. Lancer EXO_00_CORTEX.py
          ↓
3. CORTEX analyse via Gemini 2.5 Flash
          ↓
4. Validation Arsenal Impérial
          ↓
5. JSON généré dans OUT_MANIFEST/
          ↓
6. Transférer vers 01_ANIMATION_ENGINE/IN_MANIFEST/
```

---

## 📜 Changelog

### v2.0 (2026-02-02)
- Arsenal Impérial hardcodé
- Auto-correction IDs invalides → generic_prop
- Retry logic 3x avec backoff exponentiel
- Support Gemini 2.5 Flash
- Mode --dry-run pour tests
- Logging structuré (INFO/DEBUG/WARN/ERROR)

---

## 🛡️ Statut: SCELLÉE

Cette frégate est **scellée** et ne doit plus être modifiée sauf:
- Correction de bugs critiques
- Mise à jour de l'Arsenal Impérial
- Adaptation à nouvelles versions Gemini
