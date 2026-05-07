# TRACKING F04 — PHOTOGRAPHY
## "L'Oeil du Psyker"

**Statut** : 🔴 A FORGER
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
      { "preset": "STUDIO",
        "ambient":     { "intensity": 1.5, "color": "#ffffff" },
        "directional": { "intensity": 2.0, "color": "#fff4e0", "shadows": true,
                         "position": {x,y,z} },
        "hemisphere":  { "sky": "#8888ff", "ground": "#443322", "intensity": 0.6 },
        "hdri": "studio_soft" }
```

## STACK TECHNIQUE
- Fork donmccurdy/three-gltf-viewer (base)
- Three.js r160 : CameraHelper, lights, OrbitControls
- lil-gui (CDN ESM) : sliders live
- Flask Python — auto-load spawn_config.json au démarrage

## TACHES DE FORGE

### SESSION 1 — Flask (20 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S1-T1 | Créer m3_f04.ipynb : Flask + montage Drive | 🔴 TODO |
| F04-S1-T2 | GET / → viewer HTML | 🔴 TODO |
| F04-S1-T3 | GET /files/avatar + /files/decor → GLBs Drive | 🔴 TODO |
| F04-S1-T4 | GET /config/spawn → retourner spawn_config.json | 🔴 TODO |
| F04-S1-T5 | POST /save-config → écrire camera_config.json + light_config.json | 🔴 TODO |

### SESSION 2 — HTML skeleton + topbar (25 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S2-T1 | Structure HTML : topbar + viewport + panel 265px + palette | 🔴 TODO |
| F04-S2-T2 | Topbar : [CHARGER AVATAR DRIVE] [CHARGER DECOR DRIVE] [AUTO: spawn_config ✓] | 🔴 TODO |
| F04-S2-T3 | Panel : 3 boutons PRESET [STUDIO] [OUTDOOR] [NEON ROBLOX] | 🔴 TODO |
| F04-S2-T4 | Panel : sections séparées CAMERA / AMBIANTE / DIRECTIONNELLE / HEMISPHERE | 🔴 TODO |
| F04-S2-T5 | Bouton [CONFIRMER DRIVE] en bas panel | 🔴 TODO |

### SESSION 3 — Three.js scene + spawn_config (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S3-T1 | Renderer + scene + camera editeur (OrbitControls) | 🔴 TODO |
| F04-S3-T2 | Camera principale séparée (celle qu'on configure = mainCam) | 🔴 TODO |
| F04-S3-T3 | Auto-fetch /config/spawn au démarrage → positionner avatar selon spawn | 🔴 TODO |
| F04-S3-T4 | Charger avatar + décor depuis Drive | 🔴 TODO |
| F04-S3-T5 | Lumières : AmbientLight + DirectionalLight + HemisphereLight | 🔴 TODO |

### SESSION 4 — lil-gui sliders + CameraHelper + presets (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F04-S4-T1 | lil-gui import CDN + GUI panel | 🔴 TODO |
| F04-S4-T2 | Sliders FOV, PosX/Y/Z caméra → mise à jour live mainCam | 🔴 TODO |
| F04-S4-T3 | CameraHelper(mainCam) → frustum cone visible (translucide gold) | 🔴 TODO |
| F04-S4-T4 | Sliders intensité/couleur : Ambient + Directionnel + Hemisphere | 🔴 TODO |
| F04-S4-T5 | Bouton preset STUDIO → applique valeurs STUDIO dans tous les sliders | 🔴 TODO |
| F04-S4-T6 | Bouton preset OUTDOOR → valeurs OUTDOOR | 🔴 TODO |
| F04-S4-T7 | Bouton preset NEON ROBLOX → valeurs NEON | 🔴 TODO |
| F04-S4-T8 | POST /save-config → envoyer {camera_config, light_config} | 🔴 TODO |

## PRESETS ECLAIRAGE DEFINIS
| Preset | Ambient | Directionnel | Hemisphere | HDRI |
|--------|---------|-------------|-----------|------|
| STUDIO | 1.5 #fff | 2.0 #fff4e0 + ombres | sky#8888ff gnd#443322 0.6 | studio_soft |
| OUTDOOR | 0.8 #fff | 3.5 #fffbe0 + ombres | sky#87ceeb gnd#556644 0.8 | outdoor_clear |
| NEON ROBLOX | 2.0 #ff00ff | 0.5 desactivé | sky#00ffff gnd#ff00ff 1.2 | neutre |

## VALIDATION SCEAU
- [ ] spawn_config chargé auto → avatar positionné correctement
- [ ] CameraHelper visible (frustum cone)
- [ ] 3 presets fonctionnels
- [ ] Sliders lil-gui mise à jour live
- [ ] 2 JSONs valides sauvés sur Drive
