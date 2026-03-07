```
╔══════════════════════════════════════════════════════════════════════════════╗
║             ARCHITECTURE PHANTOM LINK — EXODUS V2 Phase D.1                  ║
║              Zéro Copie Inter-Frégates · Blueprint Survivable                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Date: 2026-03-07                                                            ║
║  Mission: Éliminer 100% des copies manuelles entre frégates                  ║
║  Doctrine: Si le Captain meurt, ce fichier suffit à reconstruire             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. PROBLÈME (Le Cancer de la Copie)

Le pipeline EXODUS V2 impose des **copies manuelles** entre frégates. L'Empereur doit copier les fichiers OUT/ d'une frégate vers les dossiers IN/ de la suivante.

**Chiffres pour 5 vidéos en pipeline :**

| Métrique | Actuel | Après Phantom Link |
|----------|--------|--------------------|
| Copies manuelles | ~94 GB | 0 GB |
| Stockage résiduel (frames intermédiaires) | ~97 GB | ~10 GB |
| Temps transfert | 2h+ | 0 sec |
| Forfait mobile | ~370 MB | ~370 MB |
| Compatible plan gratuit 15 GB ? | ❌ | ✅ |

**Route des copies actuelles** (extraites de `TRANSFER_ROUTES` dans `EXO_MARSHAL.py`) :

```
U00 → U01 : PRODUCTION_PLAN.JSON, facial_animation.json
U00 → U03 : PRODUCTION_PLAN.JSON, DEPTH_MAP/*.png, semantic_masks.json
U00 → U04 : camera_fov_ratio.json
U00 → U06 : audio_source.wav
U01 → U02 : *.blend, *.abc
U02 → U04 : *.abc, *.blend
U03 → U04 : *.blend
U04 → U05 : *.exr, *.png (RENDU — le plus lourd, ~1.8 GB/vidéo)
U05 → U06 : *.png (FRAMES GRADÉES — ~1.8 GB/vidéo)
```

Chaque vidéo traitée génère ~19 GB de copies redondantes. Sur un pipeline de 5 vidéos, cela représente ~94 GB de données dupliquées qui saturent le Drive et exigent 2h+ de transfert manuel.

---

## 2. SOLUTION (Phantom Link)

**Principe en une phrase :** On ne copie plus RIEN. Chaque frégate lit directement depuis le OUT/ de la frégate précédente via un fichier pointeur de 50 octets.

**2 composants à forger :**

### ① `phantom_link.py` — Le Résolveur Universel (NOUVEAU FICHIER RACINE)

```python
# phantom_link.py — EXODUS V2 Phantom Link Resolver
# Fichier racine : /EXODUS-V2/phantom_link.py

import json
from pathlib import Path
from datetime import datetime, timezone


# API publique :

def create_link(source_dir: str, target_in_dir: str) -> Path:
    """Crée un _LINK.json dans target_in_dir pointant vers source_dir."""
    # Écrit : {"source": "/content/drive/.../04_PHOTOGRAPHY_WING/OUT_CAMERA_LOGIC", "created": "2026-03-07T..."}
    # Valide que source_dir existe
    # Retourne le chemin du _LINK.json créé


def resolve_input(in_dir: str) -> Path:
    """Résout un dossier IN/ : si _LINK.json existe, retourne la source. Sinon retourne in_dir tel quel."""
    # Cherche _LINK.json dans in_dir
    # Si trouvé et source valide → retourne Path(source)
    # Si trouvé mais source invalide → raise avec message clair
    # Si pas trouvé → retourne Path(in_dir) (rétrocompatible)


def validate_link(in_dir: str) -> dict:
    """Valide un lien phantom : existe ? source accessible ? fichiers présents ?"""
    # Retourne {"valid": bool, "source": str, "file_count": int, "total_size": int}
```

**Format `_LINK.json` :**

```json
{
  "source": "/content/drive/MyDrive/DRIVE_EXODUS_V2/04_PHOTOGRAPHY_WING/OUT_CAMERA_LOGIC",
  "created": "2026-03-07T14:30:00",
  "created_by": "MARSHAL"
}
```

### ② `EXO_MARSHAL.py` V2 — 2 nouveaux modes

```python
# Mode LINK : remplace la copie manuelle
python EXO_MARSHAL.py --unit U05 --mode link
# → Lit TRANSFER_ROUTES pour U04→U05
# → Valide que OUT_CAMERA_LOGIC/ existe et contient des fichiers
# → Crée _LINK.json dans IN_RAW_FRAMES/ pointant vers OUT_CAMERA_LOGIC/
# → Affiche le résultat

# Mode CLEANUP : libère le stockage après production
python EXO_MARSHAL.py --unit U04 --mode cleanup
# → Supprime les fichiers dans OUT_CAMERA_LOGIC/ (frames rendues)
# → Vérifie d'abord que U05 a terminé (OUT_FINAL_FRAMES/ non vide)
# → Affiche l'espace libéré
```

---

## 3. FRÉGATES MODIFIÉES (Impact minimal)

Tableau des modifications à apporter dans chaque orchestrateur :

| Fichier | Modification | Lignes | Effort |
|---------|-------------|--------|--------|
| `phantom_link.py` | NOUVEAU — resolve_input() + create_link() + validate_link() | ~80-100 | Création |
| `EXO_MARSHAL.py` | Ajouter --mode link + --mode cleanup + import phantom_link | Lignes 179, 508-530 | Moyen |
| `EXO_01_TRANSMUTATION.py` | `cortex_json_dir = resolve_input(unit_root / "IN_CORTEX_JSON")` et `mixamo_base_dir = resolve_input(unit_root / "IN_MIXAMO_BASE")` | Lignes 242-243 | 3 lignes |
| `EXO_02_LOGISTICS.py` | `motion_data_dir = resolve_input(unit_root / "IN_MOTION_DATA")` | Ligne 340 | 3 lignes |
| `EXO_03_SCENOGRAPHY.py` | `cortex_json_dir = resolve_input(unit_root / "IN_CORTEX_JSON")` et `map_raw_dir = resolve_input(unit_root / "IN_MAP_RAW")` | Lignes 384-385 | 3 lignes |
| `EXO_04_PHOTOGRAPHY.py` | `video_source_dir = resolve_input(unit_root / "IN_VIDEO_SOURCE")` et `scene_ref_dir = resolve_input(unit_root / "IN_SCENE_REF")` | Lignes 362-363 | 3 lignes |
| `EXO_05_ALCHEMIST.py` | `render_dir = resolve_input(unit_root / "IN_RAW_FRAMES")` | Ligne 324 | 3 lignes |
| `EXO_06_CARRIER.py` | `assembly_kit_dir = resolve_input(unit_root / "IN_ASSEMBLY_KIT")` | Ligne 748 | 3 lignes |
| 7 notebooks PRODUCTION | Remplacer instructions "copier manuellement" par cellule `MARSHAL --mode link` | Léger | Léger |
| Tracking docs | Documenter le Phantom Link | Léger | Léger |

**Ce qui NE BOUGE PAS :**
- U00 (premier de la chaîne, pas d'input inter-frégate)
- U04-B Darkroom (lit depuis son propre OUT/)
- Tous les schemas (*_schema.py)
- Tous les modules internes de chaque frégate

---

## 4. RÉTROCOMPATIBILITÉ

`resolve_input()` est **100% rétrocompatible** :

- Si `_LINK.json` n'existe pas → retourne le chemin local (comportement actuel)
- Si `_LINK.json` existe → redirige vers la source
- L'Empereur peut toujours copier manuellement s'il le souhaite
- MARSHAL `check-in` doit être mis à jour pour vérifier les liens phantom en plus des fichiers locaux

Aucune frégate existante ne casse. Le Phantom Link est une **couche d'indirection optionnelle** qui se greffe sans chirurgie sur le pipeline actuel.

---

## 5. DIAGRAMME DE FLUX (AVANT / APRÈS)

**AVANT (copie physique) :**

```
U00/OUT_PRODUCTION_PLAN/ ──COPIE 120MB──► U01/IN_CORTEX_JSON/
U00/OUT_PRODUCTION_PLAN/ ──COPIE 800MB──► U03/IN_MAP_RAW/
U01/OUT_MOTION_DATA/     ──COPIE 200MB──► U02/IN_MOTION_DATA/
...
U04/OUT_CAMERA_LOGIC/    ──COPIE 1.8GB──► U05/IN_RAW_FRAMES/   ← LE PLUS LOURD
U05/OUT_FINAL_FRAMES/    ──COPIE 1.8GB──► U06/IN_ASSEMBLY_KIT/  ← LE PLUS LOURD
```

**APRÈS (phantom link) :**

```
U01/IN_CORTEX_JSON/_LINK.json ──50 bytes──► pointe vers U00/OUT_PRODUCTION_PLAN/
U03/IN_MAP_RAW/_LINK.json     ──50 bytes──► pointe vers U00/OUT_PRODUCTION_PLAN/
U02/IN_MOTION_DATA/_LINK.json ──50 bytes──► pointe vers U01/OUT_MOTION_DATA/
...
U05/IN_RAW_FRAMES/_LINK.json  ──50 bytes──► pointe vers U04/OUT_CAMERA_LOGIC/
U06/IN_ASSEMBLY_KIT/_LINK.json──50 bytes──► pointe vers U05/OUT_FINAL_FRAMES/
```

**Gain net par vidéo :** ~19 GB de copies évitées → remplacées par ~350 octets de pointeurs JSON.

---

## 6. CLEANUP (Libération Stockage)

Après que U06 a produit le film final :

```bash
python EXO_MARSHAL.py --unit U04 --mode cleanup  # Supprime les frames rendues (~1.8 GB)
python EXO_MARSHAL.py --unit U05 --mode cleanup  # Supprime les frames gradées (~1.8 GB)
```

**Garde-fous :**

- Ne supprime QUE les fichiers dans OUT/ de l'unité ciblée
- Vérifie que la frégate suivante a terminé son travail (OUT/ non vide)
- Demande confirmation avant suppression (sauf `--force`)
- Log dans EXODUS_CAMPAIGN.LOG

**Économie totale pour 5 vidéos :** ~87 GB de frames intermédiaires récupérables après production.

---

## 7. ORDRE DE FRAPPE (Plan d'Implémentation)

```
Étape 1 : phantom_link.py (création)
         └── resolve_input() + create_link() + validate_link()
         └── Tests unitaires intégrés (__main__)
         └── ~80-100 lignes, zéro dépendance externe

Étape 2 : EXO_MARSHAL.py (ajout --mode link et --mode cleanup)
         └── import phantom_link
         └── Lecture TRANSFER_ROUTES inversées (dest → source)
         └── Validation source avant création lien
         └── Cleanup avec garde-fous

Étape 3 : 6 orchestrateurs (resolve_input, ~3 lignes chacun)
         └── EXO_01 → EXO_06 : from phantom_link import resolve_input
         └── Remplacer chaque Path(in_dir) par resolve_input(in_dir)
         └── Impact chirurgical : 3 lignes max par fichier

Étape 4 : 7 notebooks PRODUCTION (cellule MARSHAL --mode link)
         └── Remplacer instructions manuelles par :
             !python EXO_MARSHAL.py --unit U0X --mode link

Étape 5 : Tracking docs (mise à jour)
         └── ROADMAP, MASTER, MARSHAL, CAMPAIGN_LOG
```

---

## RÉFÉRENCES

- [TRANSFER_ROUTES](./EXO_MARSHAL.py) — Lignes 146-177 : Matrice des routes inter-frégates
- [TRANSFER_LOG](./TRACKING/EXODUS_V2_TRANSFER_LOG.md) — Registre des transferts manuels
- [SACRED_ARCHITECTURE](./EXO_GENESIS_DRIVE.py) — Structure Drive canonique
- [ROADMAP](./TRACKING/EXODUS_V2_ROADMAP.md) — Plan de conquête Phase D
- [TRACKING_MARSHAL](./TRACKING/TRACKING_MARSHAL.md) — Suivi MARSHAL

> **Loi du Béton** : Ce document est la source unique de vérité pour le Phantom Link. Si un agent doit implémenter D.1, il commence ici.

<!-- v1.0 — Phase D.1 Architecture Phantom Link documentée (2026-03-07) -->
