# TRACKING F04 — PHOTOGRAPHY
## "L'Oeil du Psyker"

**Statut** : ✅ VALIDE EN PRODUCTION
**Priorité** : P1
**Dépendances entrantes** : spawn_config.json (F03)
**Dépendances sortantes** : camera_config.json + light_config.json → F05

## MISSION
Configurer la caméra (position, FOV) et l'éclairage (3 types + presets).
Output : 2 JSONs de config visuelle pour le rendu F05.

## INPUTS / OUTPUTS
```
IN  : actor.glb + decor.glb + spawn_config.json
OUT : camera_config.json
      { "fov": 55, "position": {x,y,z}, "near": 0.01, "far": 10000 }
      light_config.json
      { "preset": "studio_soft",
        "ambient":     { "intensity": 1.5, "color": "#ffffff" },
        "directional": { "intensity": 2.0, "color": "#fff4e0", "shadows": true,
                         "position": {x,y,z} },
        "hemisphere":  { "sky": "#8888ff", "ground": "#443322", "intensity": 0.6 },
        "hdri": "studio_soft" }
```

## STACK TECHNIQUE
- Three.js r160 ESM CDN
- Deux caméras : editorCam (OrbitControls) + mainCam (CameraHelper gold)
- Flask Python — auto-load spawn_config.json au démarrage

## TACHES DE FORGE

### SESSION 1 — Flask (20 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S1-T1 | Créer m3_f04.ipynb : Flask + montage Drive | ✅ DONE |
| F04-S1-T2 | GET / → viewer HTML | ✅ DONE |
| F04-S1-T3 | GET /files/avatar + /files/decor → GLBs Drive | ✅ DONE |
| F04-S1-T4 | GET /config/spawn → retourner spawn_config.json | ✅ DONE |
| F04-S1-T5 | POST /save-config → écrire camera_config.json + light_config.json | ✅ DONE |

### SESSION 2 — HTML skeleton + topbar (25 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S2-T1 | Structure HTML : topbar + viewport + panel 270px + palette | ✅ DONE |
| F04-S2-T2 | Topbar : [DRIVE: Avatar] [DRIVE: Décor] + chip Spawn auto | ✅ DONE |
| F04-S2-T3 | Panel : 3 boutons PRESET [STUDIO] [OUTDOOR] [NEON] | ✅ DONE |
| F04-S2-T4 | Panel : sections CAMERA / AMBIANTE / DIRECTIONNELLE / HEMISPHERE | ✅ DONE |
| F04-S2-T5 | Bouton [CONFIRMER DRIVE] en bas panel | ✅ DONE |

### SESSION 3 — Three.js scene + spawn_config (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S3-T1 | editorCam (OrbitControls) + mainCam séparé | ✅ DONE |
| F04-S3-T2 | CameraHelper(mainCam) — couleur gold translucide | ✅ DONE |
| F04-S3-T3 | Auto-fetch /config/spawn → positionner avatar (scale + rot_y) | ✅ DONE |
| F04-S3-T4 | Charger avatar + décor via fetch('/files/...') | ✅ DONE |
| F04-S3-T5 | AmbientLight + DirectionalLight + HemisphereLight | ✅ DONE |

### SESSION 4 — Sliders + CameraHelper + presets (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S4-T1 | Sliders FOV + PosX/Y/Z → mise à jour live mainCam | ✅ DONE |
| F04-S4-T2 | CameraHelper.update() dans render loop | ✅ DONE |
| F04-S4-T3 | Sliders intensité/couleur Ambient + Directionnel + Hemisphere | ✅ DONE |
| F04-S4-T4 | Slider position directionnelle X/Y/Z | ✅ DONE |
| F04-S4-T5 | Preset STUDIO applique toutes les valeurs | ✅ DONE |
| F04-S4-T6 | Preset OUTDOOR applique toutes les valeurs | ✅ DONE |
| F04-S4-T7 | Preset NEON ROBLOX applique toutes les valeurs | ✅ DONE |
| F04-S4-T8 | POST /save-config → {camera_config, light_config} | ✅ DONE |

### SESSION 5 — Hotfixes + Validation production (2026-05-09)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S5-T1 | Fix : editorCam ne framait pas l'avatar après apply spawn_config — box2/ctr2/sz2 ajouté | ✅ DONE |
| F04-S5-T2 | Analyse fonctionnelle : F04 viewer passif, pas de TransformControls nécessaire | ✅ DONE |
| F04-S5-T3 | Outputs vérifiés manuellement : camera_config.json + light_config.json structurellement valides | ✅ DONE |
| F04-S5-T4 | Confirmation pipeline : F03 → spawn_config → F04 → camera_config + light_config → F05 | ✅ DONE |

## PRESETS ECLAIRAGE
| Preset | Ambient | Directionnel | Hemisphere | HDRI |
|--------|---------|-------------|-----------|------|
| STUDIO | 1.5 #fff | 2.0 #fff4e0 + ombres | sky#8888ff gnd#443322 0.6 | studio_soft |
| OUTDOOR | 0.8 #fff | 3.5 #fffbe0 + ombres | sky#87ceeb gnd#556644 0.8 | outdoor_clear |
| NEON | 2.0 #ff00ff | 0.5 desactivé | sky#00ffff gnd#ff00ff 1.2 | neutre |

## VALIDATION SCEAU
- [x] spawn_config chargé auto → avatar positionné (scale + rot_y)
- [x] CameraHelper visible (frustum cone gold)
- [x] 3 presets fonctionnels
- [x] Sliders mise à jour live
- [x] 2 JSONs valides sauvés sur Drive
- [x] camera_config.json validé en production (fov:55, position:{0,3,6}, near:0.01, far:10000)
- [x] light_config.json validé en production (preset:studio_soft, ambient/directional/hemisphere complets)
- [x] Fix framing avatar (commit 5b935f492e71) — editorCam recadre l'avatar après spawn_config apply

## DECLARATION DE VICTOIRE
> *« F04 — L'Oeil du Psyker voit. Les configs sont forgées. Le pipeline tient. Au nom de l'Empereur, F04 est VALIDE. »*
>
> — Sceau apposé le 2026-05-09. La flotte peut avancer vers F05.

## FICHIERS FORGES
| Fichier | Description |
|---------|-------------|
| `m3_f04_flask.py` | Flask 6 endpoints : `/`, `/info`, `/files/avatar`, `/files/decor`, `/config/spawn`, `/save-config` |
| `m3_f04_viewer.html` | Three.js r160 — editorCam + mainCam + CameraHelper gold, AmbientLight + DirLight + HemiLight, 3 presets, sliders live, fix framing avatar |
| `m3_f04.ipynb` | 4 cellules Colab : montage Drive, vérif inputs, lancement Flask, lecture configs |
