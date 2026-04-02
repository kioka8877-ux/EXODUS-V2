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

## 3. USAGE SUR COLAB — AVEC FICHIER .BLEND

### 3.1 Setup initial (à faire une seule fois par session Colab)

```python
# Monter Drive
from google.colab import drive
drive.mount('/content/drive')

# Chemin de base SENTINEL
SENTINEL_BASE = "/content/drive/MyDrive/EXODUS_V2/SENTINEL_CORE"

# Import
import sys
sys.path.insert(0, f"{SENTINEL_BASE}/CODEBASE")
from sentinel_core import Sentinel
```

### 3.2 Lancer SENTINEL sur une frégate avec .blend

```python
s = Sentinel(base_dir=SENTINEL_BASE)

rapport = s.run(
    fregate="U03",
    blend_path="/content/drive/MyDrive/EXODUS_V2/03_SCENOGRAPHY_DOCK/OUT_PREMIUM_SCENE/environment_1.blend"
)

# Lire le verdict
print(rapport["verdict"])          # PASS / FAIL / WARN
print(rapport["prompt_vulkan"])    # Copier-coller dans Claude si FAIL
```

### 3.3 Ce que SENTINEL produit (outputs Colab)

```
SENTINEL_CORE/
├── STATE_SIG_U03.json        ← Résultat B2 (paramètres mesurés)
├── GHOST_U03.json            ← Résultat B3 (luminance)
├── ghost_U03.png             ← Image preview 128x128
├── DIAGNOSTIC_U03.json       ← Résultat B5 (cause racine)
├── prompt_vulkan_U03.txt     ← Prompt à copier dans Claude
├── memory.json               ← Ledger mis à jour (B6)
└── SENTINEL_RAPPORT_U03_*.json ← Rapport complet
```

### 3.4 Pre-check avant exécution (hook Marshal)

```python
# Vérifier AVANT de lancer une frégate longue (ex: U03 qui prend 30 min)
s = Sentinel(base_dir=SENTINEL_BASE)
ok = s.pre_check(
    fregate="U03",
    blend_path="/content/.../environment_1.blend"
)

if ok:
    # Lancer la frégate normalement
    pass
else:
    print("SENTINEL bloque l'exécution — corriger d'abord")
```

---

## 4. USAGE EN LOCAL — AVEC FRAMES DÉJÀ RENDUES

### 4.1 Setup local

```bash
cd /ton/repo/EXODUS-V2
pip install Pillow numpy  # seules dépendances nécessaires
```

### 4.2 Lancer SENTINEL sur un dossier de frames

```python
import sys
sys.path.insert(0, "SENTINEL_CORE/CODEBASE")
from sentinel_core import Sentinel

s = Sentinel(base_dir="SENTINEL_CORE")

rapport = s.run(
    fregate="U04",
    frames_dir="04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/"
)

print(rapport["verdict"])
print(rapport["prompt_vulkan"])
```

### 4.3 Via ligne de commande (CLI)

```bash
# Audit frames U04
python SENTINEL_CORE/CODEBASE/sentinel_core.py \
  --fregate U04 \
  --frames 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/ \
  --base-dir SENTINEL_CORE \
  --print-prompt

# Audit .blend U03 (COLAB UNIQUEMENT — nécessite bpy)
python SENTINEL_CORE/CODEBASE/sentinel_core.py \
  --fregate U03 \
  --blend /path/to/environment_1.blend \
  --base-dir SENTINEL_CORE
```

---

## 5. USAGE PAR BRIQUE INDIVIDUELLE

### B2 — Signature d'État seule

```bash
# Sur frames (local OK)
python SENTINEL_CORE/CODEBASE/brique2_state.py \
  --fregate U04 \
  --frames 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/ \
  --output STATE_SIG_U04.json

# Sur .blend (Colab uniquement)
python SENTINEL_CORE/CODEBASE/brique2_state.py \
  --fregate U03 \
  --blend /content/.../environment_1.blend \
  --output STATE_SIG_U03.json
```

### B3 — Ghost Renderer seul

```bash
# Analyser un dossier de frames (local OK)
python SENTINEL_CORE/CODEBASE/brique3_ghost.py \
  --frames 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/

# Analyser une image unique (local OK)
python SENTINEL_CORE/CODEBASE/brique3_ghost.py \
  --image 04_PHOTOGRAPHY_WING/OUT_CAMERA_FRAMES/frame_001.png

# Rendu ghost sur .blend (Colab uniquement)
python SENTINEL_CORE/CODEBASE/brique3_ghost.py \
  --blend /content/.../environment_1.blend \
  --output ghost_U03.png
```

### B6 — Ledger seul

```bash
# Voir toutes les entrées
python SENTINEL_CORE/CODEBASE/brique6_ledger.py --action list

# Voir les injections pour U03
python SENTINEL_CORE/CODEBASE/brique6_ledger.py --action get --fregate U03

# Ajouter une entrée manuellement
python SENTINEL_CORE/CODEBASE/brique6_ledger.py \
  --action add \
  --fregate U03 \
  --erreur "caméra absente" \
  --cause "layer_assembler non appelé" \
  --correction "appeler layer_assembler.py avant geometry_probe"
```

---

## 6. TABLEAU DE DÉCISION — QUE FAIRE SELON LE VERDICT

| Verdict | Signification | Action |
|---------|--------------|--------|
| `PASS` | Tout est dans les seuils | Continuer vers la frégate suivante |
| `WARN` | Paramètre limite, pas bloquant | Optionnel : ajuster avant de continuer |
| `FAIL` | Paramètre critique hors seuil | Copier `prompt_vulkan_*.txt` dans Claude → attendre prescription |
| `UNKNOWN` | SENTINEL lancé sans .blend ni frames | Normal si test sans fichier |
| `ERROR` | SENTINEL lui-même a crashé | Voir `erreurs_sentinel` dans le rapport |

### Matrice diagnostic B5 (pour comprendre la cause)

| B2 | B3 | Conclusion B5 | Action |
|----|----|--------------|--------|
| PASS | VISIBLE | SUCCES | Rien |
| PASS | DARK | Sous-exposition | +20% sun.energy |
| PASS | BLACK | Conflit shader/compositing | Voir shaders |
| FAIL | BLACK | Cause paramètres (confirmé) | Corriger B2 |
| FAIL | VISIBLE | Régression partielle | Surveiller |
| FAIL | DARK | Énergie lumière critique | Corriger énergie |

---

## 7. WORKFLOW COMPLET — EXEMPLE U03

```
1. [COLAB] Monter Drive + importer Sentinel
      ↓
2. [COLAB] s.pre_check(fregate="U03", blend_path=...)
      → PASS : lancer U03 normalement
      → FAIL : lire prompt_vulkan → corriger → relancer pre_check
      ↓
3. [COLAB] Lancer EXO_03_SCENOGRAPHY.py (frégate U03)
      ↓
4. [COLAB] s.run(fregate="U03", blend_path=...) après exécution
      → Lire verdict final
      → Si FAIL : copier prompt_vulkan dans Claude
      ↓
5. [CLAUDE] Recevoir prescription Vulkan (code à ajouter)
      ↓
6. [COLAB] Appliquer correction + relancer s.run()
      → Attendu : PASS
      ↓
7. [LOCAL ou COLAB] Vérifier ledger
      python brique6_ledger.py --action list
```

---

## 8. STRUCTURE DES FICHIERS SENTINEL

```
SENTINEL_CORE/
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
```

---

## 9. ERREURS FRÉQUENTES ET SOLUTIONS

| Erreur | Cause | Solution |
|--------|-------|---------|
| `bpy non disponible` | Tu lances check_blend en local | Utiliser `--frames` en local, pas `--blend` |
| `Fichier introuvable` | Chemin Drive incorrect | Vérifier le mount Drive + chemin complet |
| `Fregate inconnue` | ID frégate non reconnu | Options valides : U00, U01, U02, U03, U04, U05, U06 |
| `B8 erreur : STATE_SIG non trouvé` | B2 a échoué avant B8 | Corriger l'erreur B2 d'abord |
| `memory.json corrompu` | Écriture interrompue | Supprimer memory.json → il se recrée automatiquement |

---

*Guide généré par Vulkan v9.0 — Incarnation SENTINEL*
*SENTINEL veille. L'Empire est immortel.*
