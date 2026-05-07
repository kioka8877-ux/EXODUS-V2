# TRACKING F03 — SCENOGRAPHY
## "Le Cartographe de Bataille"

**Statut** : ✅ FORGE
**Priorité** : P0
**Dépendances entrantes** : aucune
**Dépendances sortantes** : spawn_config.json → F04 F05

## MISSION
Positionner avatar dans un décor 3D + définir trajectoire de déplacement.
Output : spawn_config.json (position spawn + trajectoire A→B pour root motion).

## INPUTS / OUTPUTS
```
IN  : actor.glb (avatar) + decor.glb (scène)
OUT : spawn_config.json
      {
        "active_beacon": "Balise_01",
        "beacons": [...],
        "spawn": { "x": 12.4, "y": 0.0, "z": -8.1 },
        "scale": 0.857,
        "rot_y": 10,
        "trajectory": {
          "mode": "linear",
          "start": { "x": 12.4, "y": 0.0, "z": -8.1 },
          "end":   { "x": 5.2,  "y": 0.0, "z": -2.3 }
        }
      }
```

## STACK TECHNIQUE
- Three.js r160 ESM CDN
- OrbitControls + WASD (Q/E = haut/bas)
- Raycaster → clic sol = placement balise/end
- Flask Python — 5 endpoints

## TACHES DE FORGE

### SESSION 1 — Flask (20 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S1-T1 | Créer m3_f03.ipynb : Flask + montage Drive | ✅ DONE |
| F03-S1-T2 | GET / → viewer HTML | ✅ DONE |
| F03-S1-T3 | GET /files/decor → GLB décor depuis Drive | ✅ DONE |
| F03-S1-T4 | GET /files/avatar → GLB avatar depuis Drive | ✅ DONE |
| F03-S1-T5 | POST /save-config → écrire spawn_config.json sur Drive | ✅ DONE |

### SESSION 2 — HTML viewer + topbar (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S2-T1 | Structure HTML : topbar + viewport + panel 270px + palette | ✅ DONE |
| F03-S2-T2 | Topbar : boutons [DRIVE: Décor] [DRIVE: Avatar] → fetch('/files/...') | ✅ DONE |
| F03-S2-T3 | WASD (+ Q/E vertical) + OrbitControls | ✅ DONE |
| F03-S2-T4 | Raycaster → clic sol = balise gold (SphereGeometry) | ✅ DONE |
| F03-S2-T5 | Scale + Rot Y sliders → avatar suit balise active | ✅ DONE |

### SESSION 3 — Section TRAJECTOIRE (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S3-T1 | Section "TRAJECTOIRE" dans panel (sous Balises) | ✅ DONE |
| F03-S3-T2 | Toggle STATIQUE / LINÉAIRE A→B | ✅ DONE |
| F03-S3-T3 | START = position balise active (mise à jour auto) | ✅ DONE |
| F03-S3-T4 | Bouton [DÉFINIR POINT D'ARRIVÉE] → mode END : clic sol = end_pos | ✅ DONE |
| F03-S3-T5 | Sphère rouge END placée dans la scene | ✅ DONE |
| F03-S3-T6 | Ligne rouge reliant START et END dans viewport | ✅ DONE |
| F03-S3-T7 | trajectory incluse dans JSON au CONFIRMER | ✅ DONE |

## VALIDATION SCEAU
- [x] Chargement GLB depuis Flask (pas de file picker local)
- [x] WASD + OrbitControls + balises gold fonctionnels
- [x] Toggle STATIQUE = spawn_config sans trajectory.start/end
- [x] Toggle LINÉAIRE = spawn_config avec trajectory.start + trajectory.end
- [x] spawn_config.json valide sauvé sur Drive

## FICHIERS FORGES
| Fichier | Description |
|---------|-------------|
| `m3_f03_flask.py` | Flask 5 endpoints : `/`, `/info`, `/files/decor`, `/files/avatar`, `/save-config` |
| `m3_f03_viewer.html` | Three.js r160 — WASD, OrbitControls, balises, scale/rotY, trajectoire STATIQUE/LINÉAIRE, ligne de traj |
| `m3_f03.ipynb` | 4 cellules Colab : montage Drive, vérif inputs, lancement Flask, lecture config |
