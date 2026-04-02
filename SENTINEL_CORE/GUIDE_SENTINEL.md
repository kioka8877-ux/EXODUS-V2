# GUIDE D'UTILISATION — SENTINEL v2.0

```
Doctrine : SENTINEL prépare le contexte. Vulkan prescrit. L'Empereur valide.
```

---

## 1. ARCHITECTURE — CE QUE FAIT CHAQUE BRIQUE

| Brique | Fichier | Dépendance | Rôle |
|--------|---------|-----------|------|
| **B2** | `brique2_state.py` | `bpy` si `.blend` / Python pur si frames | Mesure les paramètres critiques (caméra, vertices, GPU, énergie) |
| **B3** | `brique3_ghost.py` | `bpy` si rendu / `PIL+numpy` si images existantes | Détecte frames noires (luminance 128x128) |
| **B5** | `brique5_diagnostic.py` | Python pur | Croise B2+B3 → cause racine |
| **B6** | `brique6_ledger.py` | Python pur | Mémoire persistante des erreurs/corrections |
| **B8** | `brique8_mirror.py` | Python pur | Assemble le prompt Vulkan avec le delta |
| **CORE** | `sentinel_core.py` | Orchestre B2→B3→B5→B6→B8 | Un seul appel `.run()` |

---

## 2. RÈGLE FONDAMENTALE — QUI TOURNE OÙ

```
┌─────────────────────────────────────────────────────────────┐
│  COLAB (Blender installé)        LOCAL (Python pur)         │
│                                                             │
│  Audit d'un fichier .blend  ←→  Audit de frames rendues    │
│  B2.check_blend()               B2.check_frames()          │
│  B3.render()                    B3.analyze_folder()        │
│                                 B3.analyze_existing()      │
│                                                             │
│  B5, B6, B8 = partout (pas besoin de Blender)              │
└─────────────────────────────────────────────────────────────┘
```

**Résumé en une ligne :**
- Tu as un **fichier .blend** → tu es sur **Colab**
- Tu as un **dossier de frames déjà rendues** → tu peux tourner **en local**

---

## 3. OÙ LANCER SENTINEL — 3 POINTS D'ENTRÉE

| Point d'entrée | Fichier | Quand l'utiliser |
|----------------|---------|-----------------|
| **Cellules intégrées U03** | `EXO_03_PRODUCTION.ipynb` | Workflow normal — automatique |
| **Cellules intégrées U04** | `EXO_04_PRODUCTION.ipynb` | Workflow normal — automatique |
| **Notebook dédié** | `SENTINEL_CORE/EXO_SENTINEL.ipynb` | Audit manuel, debug, relecture ledger |

**Règle :** Pour U03 et U04, SENTINEL est déjà intégré dans le notebook de production — tu n'as rien à faire de plus. Pour les autres cas, utilise `EXO_SENTINEL.ipynb`.

---

## 4. USAGE DANS LES NOTEBOOKS DE FRÉGATE (U03 / U04)

### Comment ça fonctionne

Deux cellules SENTINEL sont injectées dans chaque notebook de production :

**Cellule Pre-Check** — s'exécute **avant** le lancement de la frégate :
```python
# Cellule [10] dans EXO_03_PRODUCTION.ipynb
# Cellule [8]  dans EXO_04_PRODUCTION.ipynb

sentinel = Sentinel(base_dir=str(DRIVE_ROOT / 'SENTINEL_CORE'))
sentinel_precheck = sentinel.run(fregate='U03', blend_path=...)

# Si FAIL → raise RuntimeError et bloque la suite
# Si PASS / WARN → continue automatiquement
```

**Cellule Post-Run** — s'exécute **après** la frégate :
```python
# Cellule [15] dans EXO_03_PRODUCTION.ipynb
# Cellule [13] dans EXO_04_PRODUCTION.ipynb

sentinel_rapport = sentinel.run(fregate='U03', blend_path=...)

# Affiche verdict + met à jour le ledger
# Si FAIL → affiche le prompt Vulkan à copier dans Claude
```

### Ce que tu dois faire

- **Rien de spécial.** Exécuter les cellules dans l'ordre normal du notebook.
- Si la cellule pre-check **bloque** avec `RuntimeError` → lire le prompt Vulkan affiché → corriger → relancer depuis la cellule pre-check.
- Si la cellule post-run affiche `FAIL` → copier le prompt Vulkan dans Claude.

### Paramètres U03 vs U04

| Frégate | Mode | Variable chemin |
|---------|------|----------------|
| U03 | `blend_path` | `OUT_PREMIUM_SCENE/*.blend` (généré par la frégate) |
| U04 | `frames_dir` | `OUT_CAMERA` (frames rendues par U04) |

---

## 5. USAGE AVEC EXO_SENTINEL.ipynb — AUDIT MANUEL

`SENTINEL_CORE/EXO_SENTINEL.ipynb` est le notebook dédié pour tout ce qui sort du workflow normal.

### 5.1 Setup

```python
from google.colab import drive
drive.mount('/content/drive')

import sys
from pathlib import Path

DRIVE_ROOT = Path('/content/drive/MyDrive/EXODUS_V2')
SENTINEL_BASE = DRIVE_ROOT / 'SENTINEL_CORE'

sys.path.insert(0, str(SENTINEL_BASE / 'CODEBASE'))
from sentinel_core import Sentinel

sentinel = Sentinel(base_dir=str(SENTINEL_BASE))
```

### 5.2 Sections disponibles dans EXO_SENTINEL.ipynb

| Section | Contenu |
|---------|---------|
| **2. Audit Manuel** | Lancer `.run()` sur n'importe quelle frégate (blend ou frames) |
| **3. Ledger** | Lister toutes les entrées / filtrer par frégate |
| **4. Simulation d'erreur** | Tester que SENTINEL détecte bien un problème |
| **5. Analyse frames** | Analyser un dossier de frames avec B3 seul |
| **6. Rapport multi-frégate** | Auditer U04 + U05 en un seul run |

### 5.3 Audit manuel rapide (depuis EXO_SENTINEL.ipynb)

```python
# Configurer
FREGATE = 'U03'
MODE    = 'blend'   # 'blend' ou 'frames'

# Lancer
if MODE == 'blend':
    rapport = sentinel.run(fregate=FREGATE, blend_path=BLEND_PATH)
else:
    rapport = sentinel.run(fregate=FREGATE, frames_dir=FRAMES_PATH)

print(rapport["verdict"])
if rapport["verdict"] == "FAIL":
    print(rapport["prompt_vulkan"])  # Copier dans Claude
```

---

## 6. USAGE EN LOCAL — SANS COLAB

### 6.1 Setup

```bash
cd /ton/repo/EXODUS-V2
pip install Pillow numpy  # seules dépendances nécessaires
```

### 6.2 Lancer SENTINEL sur frames locales

```python
import sys
sys.path.insert(0, "SENTINEL_CORE/CODEBASE")
from sentinel_core import Sentinel

s = Sentinel(base_dir="SENTINEL_CORE")
rapport = s.run(fregate="U04", frames_dir="04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/")

print(rapport["verdict"])
print(rapport["prompt_vulkan"])
```

### 6.3 Via CLI

```bash
# Audit frames
python SENTINEL_CORE/CODEBASE/sentinel_core.py \
  --fregate U04 \
  --frames 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/ \
  --base-dir SENTINEL_CORE

# Audit .blend (Colab uniquement — nécessite bpy)
python SENTINEL_CORE/CODEBASE/sentinel_core.py \
  --fregate U03 \
  --blend /path/to/environment_1.blend \
  --base-dir SENTINEL_CORE
```

---

## 7. USAGE PAR BRIQUE INDIVIDUELLE

### B2 — Signature d'État seule

```bash
# Sur frames (local OK)
python SENTINEL_CORE/CODEBASE/brique2_state.py \
  --fregate U04 --frames 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/ --output STATE_SIG_U04.json

# Sur .blend (Colab uniquement)
python SENTINEL_CORE/CODEBASE/brique2_state.py \
  --fregate U03 --blend /content/.../environment_1.blend --output STATE_SIG_U03.json
```

### B3 — Ghost Renderer seul

```bash
# Dossier de frames (local OK)
python SENTINEL_CORE/CODEBASE/brique3_ghost.py --frames 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/

# Image unique (local OK)
python SENTINEL_CORE/CODEBASE/brique3_ghost.py --image frame_001.png

# Rendu .blend (Colab uniquement)
python SENTINEL_CORE/CODEBASE/brique3_ghost.py --blend /content/.../environment_1.blend --output ghost_U03.png
```

### B6 — Ledger seul

```bash
python SENTINEL_CORE/CODEBASE/brique6_ledger.py --action list
python SENTINEL_CORE/CODEBASE/brique6_ledger.py --action get --fregate U03
python SENTINEL_CORE/CODEBASE/brique6_ledger.py --action add \
  --fregate U03 --erreur "caméra absente" --cause "layer_assembler non appelé" \
  --correction "appeler layer_assembler.py avant geometry_probe"
```

---

## 8. TABLEAU DE DÉCISION — QUE FAIRE SELON LE VERDICT

| Verdict | Signification | Action |
|---------|--------------|--------|
| `PASS` | Tout est dans les seuils | Continuer vers la frégate suivante |
| `WARN` | Paramètre limite, pas bloquant | Optionnel : ajuster avant de continuer |
| `FAIL` | Paramètre critique hors seuil | Copier `prompt_vulkan_*.txt` dans Claude → attendre prescription |
| `UNKNOWN` | SENTINEL lancé sans .blend ni frames | Normal si test sans fichier |
| `ERROR` | SENTINEL lui-même a crashé | Voir `erreurs_sentinel` dans le rapport |

### Matrice diagnostic B5

| B2 | B3 | Conclusion | Action |
|----|----|-----------|--------|
| PASS | VISIBLE | SUCCES | Rien |
| PASS | DARK | Sous-exposition | +20% sun.energy |
| PASS | BLACK | Conflit shader/compositing | Voir shaders |
| FAIL | BLACK | Cause paramètres (confirmé) | Corriger B2 |
| FAIL | VISIBLE | Régression partielle | Surveiller |
| FAIL | DARK | Énergie lumière critique | Corriger énergie |

---

## 9. WORKFLOW COMPLET — EXEMPLE U03

```
1. [COLAB] Ouvrir EXO_03_PRODUCTION.ipynb
      ↓
2. [COLAB] Exécuter cellules dans l'ordre normal
      ↓
3. [COLAB] Cellule [10] — SENTINEL Pre-Check (automatique)
      → PASS : continue vers LANCEMENT PRODUCTION
      → FAIL : RuntimeError affiché + prompt Vulkan → corriger → relancer depuis [10]
      ↓
4. [COLAB] Cellule [12] — LANCEMENT PRODUCTION (frégate U03 tourne)
      ↓
5. [COLAB] Cellule [15] — SENTINEL Post-Run (automatique)
      → PASS : ledger mis à jour, frégate validée
      → FAIL : prompt Vulkan affiché → copier dans Claude
      ↓
6. [CLAUDE] Recevoir prescription Vulkan (code exact à ajouter)
      ↓
7. [COLAB] Appliquer correction + relancer depuis cellule [10]
      → Attendu : PASS du premier coup
```

---

## 10. STRUCTURE DES FICHIERS SENTINEL

```
SENTINEL_CORE/
├── EXO_SENTINEL.ipynb        ← Notebook audit autonome (6 sections)
├── CODEBASE/
│   ├── sentinel_core.py      ← POINT D'ENTRÉE PRINCIPAL
│   ├── brique2_state.py      ← B2 : mesure paramètres
│   ├── brique3_ghost.py      ← B3 : détection frames noires
│   ├── brique5_diagnostic.py ← B5 : cause racine
│   ├── brique6_ledger.py     ← B6 : mémoire persistante
│   └── brique8_mirror.py     ← B8 : prompt Vulkan
├── memory.json               ← Ledger (à garder sur Drive)
├── REFERENCES/               ← Références parfaites par frégate
│   ├── U03/
│   └── U04/
├── DNA_SAMPLES/              ← Échantillons ADN visuels
└── TRACKING/
    ├── SENTINEL_STATE.md
    ├── SENTINEL_VALIDATION.md
    └── TRACKING_SENTINEL.md

Notebooks frégate avec SENTINEL intégré :
├── 03_SCENOGRAPHY_DOCK/CODEBASE/EXO_03_PRODUCTION.ipynb  ← cellules [10] + [15]
└── 04_PHOTOGRAPHY_WING/CODEBASE/EXO_04_PRODUCTION.ipynb  ← cellules [8] + [13]
```

---

## 11. ERREURS FRÉQUENTES ET SOLUTIONS

| Erreur | Cause | Solution |
|--------|-------|---------|
| `bpy non disponible` | Tu lances check_blend en local | Utiliser `--frames` en local, pas `--blend` |
| `RuntimeError: Fregate bloquée` | Pre-check FAIL | Lire prompt Vulkan affiché → corriger → relancer depuis cellule pre-check |
| `Fichier introuvable` | Chemin Drive incorrect | Vérifier le mount Drive + chemin complet |
| `Fregate inconnue` | ID frégate non reconnu | Options valides : U00, U01, U02, U03, U04, U05, U06 |
| `B8 erreur : STATE_SIG non trouvé` | B2 a échoué avant B8 | Corriger l'erreur B2 d'abord |
| `memory.json corrompu` | Écriture interrompue | Supprimer memory.json → il se recrée automatiquement |

---

*Guide v2 — mis à jour après intégration EXO_SENTINEL.ipynb + cellules U03/U04*
*SENTINEL veille. L'Empire est immortel.*
