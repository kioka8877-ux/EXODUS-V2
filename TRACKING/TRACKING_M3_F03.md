# TRACKING F03 — SCENOGRAPHY
## "Le Cartographe de Bataille"

**Statut** : ✅ SCELLÉ — TEST PROD OK (2026-05-09)
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
          "end":   { "x": 5.2,  "y": 0.0, "z": -2.3 },
          "loop": 1
        }
      }
```

## STACK TECHNIQUE
- Three.js r164 ESM CDN
- OrbitControls + WASD (Q/E = haut/bas)
- TransformControls — gizmo 3 flèches pour positionner l'avatar
- Raycaster → double-clic sol = placement balise/end
- Flask Python — 5 endpoints
- Auto-load Drive au démarrage (fetch /info)

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
| F03-S2-T4 | Raycaster → double-clic sol = balise gold (SphereGeometry) | ✅ DONE |
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

### SESSION 4 — Corrections production (2026-05-09)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S4-T1 | Fix SyntaxError accents bruts dans JS (encode \uXXXX) — v3.0 | ✅ DONE |
| F03-S4-T2 | Fix popup balise + Y offset avatar (feet on floor) — v3.1 | ✅ DONE |
| F03-S4-T3 | Popup type animation STATIQUE/LINÉAIRE après spawn — v3.2 | ✅ DONE |
| F03-S4-T4 | Popup lecture UNE FOIS/LOOP x2 (si LINÉAIRE) — v3.2 | ✅ DONE |
| F03-S4-T5 | Champ `loop` dans trajectory JSON — v3.2 | ✅ DONE |
| F03-S4-T6 | Flèche directionnelle or (rot_y temps réel) — v3.3 | ✅ DONE |
| F03-S4-T7 | Touche P : vue caméra devant avatar (hauteur buste) — v3.3 | ✅ DONE |

## VALIDATION SCEAU
- [x] Chargement GLB depuis Flask (pas de file picker local)
- [x] WASD + OrbitControls + TransformControls + balises gold fonctionnels
- [x] Popup nom balise → popup type anim → popup loop (chain correcte)
- [x] Toggle STATIQUE = spawn_config sans trajectory.start/end
- [x] Toggle LINÉAIRE = spawn_config avec trajectory.start + trajectory.end + loop
- [x] Flèche directionnelle or synchro rot_y
- [x] Touche P = vue caméra devant avatar
- [x] spawn_config.json valide sauvé sur Drive ✅ CONFIRMÉ TEST PROD 2026-05-09

## FICHIERS FORGES
| Fichier | Description | Version |
|---------|-------------|---------|
| `m3_f03_flask.py` | Flask 5 endpoints : `/`, `/info`, `/files/decor`, `/files/avatar`, `/save-config` | v1.0 |
| `m3_f03_viewer.html` | Three.js r164 — WASD, OrbitControls, TransformControls, balises, popups anim+loop, scale/rotY, trajectoire STATIQUE/LINÉAIRE, flèche direction, touche P | v3.3 |
| `m3_f03.ipynb` | 4 cellules Colab : montage Drive, vérif inputs, lancement Flask, lecture config | v1.0 |
