# TRACKING F03 — SCENOGRAPHY
## "Le Cartographe de Bataille"

**Statut** : 🔴 A FORGER
**Priorité** : P0 (premier fork réel à forger après F06)
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

## POURQUOI TRAJECTOIRE ICI — ROOT MOTION DEEPMOTION
Deepmotion génère des animations IN-PLACE (avatar marche/court mais
reste à l'origine XYZ 0,0,0). Pour simuler un déplacement réel dans F05 :
- F03 : l'utilisateur définit une position de départ ET d'arrivée
- F05 : à chaque frame N, avatarRoot.position.lerpVectors(start, end, N/totalFrames)
Résultat : avatar semble se déplacer dans la scène.

## STACK TECHNIQUE
- Fork DIRECT de m2_f03_viewer.html v4.0
- Modifications minimales : 3 changements de code + 1 nouvelle section
- Three.js r160 : déjà présent dans le fork
- Flask Python — adapté depuis M2_F03

## TACHES DE FORGE

### SESSION 1 — Flask (20 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S1-T1 | Créer m3_f03.ipynb : Flask + montage Drive | 🔴 TODO |
| F03-S1-T2 | GET / → viewer HTML | 🔴 TODO |
| F03-S1-T3 | GET /files/decor → GLB décor depuis Drive | 🔴 TODO |
| F03-S1-T4 | GET /files/avatar → GLB avatar depuis Drive | 🔴 TODO |
| F03-S1-T5 | POST /save-config → écrire spawn_config.json sur Drive | 🔴 TODO |

### SESSION 2 — Fork m2_f03_viewer.html : 3 modifications (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S2-T1 | Copier m2_f03_viewer.html → m3_f03_viewer.html | 🔴 TODO |
| F03-S2-T2 | MOD 1 — Topbar : remplacer input[type=file] → boutons [DRIVE: Décor] [DRIVE: Avatar] qui appellent fetch('/files/decor') | 🔴 TODO |
| F03-S2-T3 | MOD 2 — confirmSpawn() : remplacer download local → POST /save-config | 🔴 TODO |
| F03-S2-T4 | MOD 3 — Logo/titre : "M3_F03 v1.0" + "SCENOGRAPHIE" | 🔴 TODO |

### SESSION 3 — Section TRAJECTOIRE (nouveau dans M3) (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F03-S3-T1 | Ajouter section "TRAJECTOIRE" dans le panel droit (sous BALISES) | 🔴 TODO |
| F03-S3-T2 | Toggle MODE : "STATIQUE" (pas de déplacement) / "LINEAIRE A→B" | 🔴 TODO |
| F03-S3-T3 | Si LINEAIRE : afficher coords START (= position courante balise active) | 🔴 TODO |
| F03-S3-T4 | Bouton [DEFINIR POINT D'ARRIVEE] → mode placement END : clic sur sol = end_pos | 🔴 TODO |
| F03-S3-T5 | Indicateur END placé dans la scene (sphère rouge) | 🔴 TODO |
| F03-S3-T6 | Ligne reliant sphère START (gold) et sphère END (rouge) dans viewport | 🔴 TODO |
| F03-S3-T7 | Inclure trajectory dans le JSON généré au CONFIRMER | 🔴 TODO |

## VALIDATION SCEAU
- [ ] Chargement GLB depuis Flask fonctionne (pas de file local picker)
- [ ] WASD, OrbitControls, balises, gizmo : identiques M2_F03
- [ ] Toggle STATIQUE = spawn_config sans trajectory
- [ ] Toggle LINEAIRE = spawn_config avec trajectory.start + trajectory.end
- [ ] spawn_config.json valide sauvé sur Drive
