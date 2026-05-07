# TRACKING F05 — ALCHEMIST
## "La Forge d'Âme — Rendu GPU T4"

**Statut** : 🔴 A FORGER
**Priorité** : P0 (forge en dernier — le plus critique)
**Dépendances entrantes** : spawn_config.json (F03) + camera_config.json + light_config.json (F04)
**Dépendances sortantes** : OUT_FRAMES/frame_0001.png ... frame_NNNN.png → F06

## MISSION
Rendre toutes les frames PNG de l'animation via Playwright headless + GPU T4 Colab.
Appliquer post-FX (Bloom, Vignette, Saturation) + ROOT MOTION trajectoire.

## INPUTS / OUTPUTS
```
IN  : actor.glb + decor.glb + spawn_config.json + camera_config.json + light_config.json
OUT : Drive/OUT_FRAMES/frame_0001.png ... frame_NNNN.png
      Drive/F05/m3_f05_checkpoint.json (reprise si interruption)
```

## ROOT MOTION — IMPLEMENTATION CRITIQUE
```
Problème : Deepmotion génère animations IN-PLACE (reste à XYZ 0,0,0)
Solution  : F03 a défini trajectory { start, end }
Application dans F05 :
  const start = new THREE.Vector3(spawn_config.trajectory.start)
  const end   = new THREE.Vector3(spawn_config.trajectory.end)

  // Dans la boucle de capture, frame N sur totalFrames
  window.setRenderFrame = function(frameN) {
    const t = frameN / totalFrames
    avatarRoot.position.lerpVectors(start, end, t)
    mixer.setTime(frameN / fps)
    composer.render()
    document.getElementById('frame-done').style.display = 'block'
  }

Si trajectory.mode === "static" : pas de lerp, avatar reste au spawn.
```

## STACK TECHNIQUE
- Three.js r160 (CDN ESM) — scene complète
- pmndrs/postprocessing (CDN ESM) — EffectComposer
  · BloomEffect, VignetteEffect, HueSaturationEffect, FXAAEffect
- Playwright Python (Colab) — headless GPU avec flags EGL
- Flask Python — sert le viewer + endpoints render + status

## FLAGS PLAYWRIGHT GPU (CRITIQUES)
```python
browser = playwright.chromium.launch(args=[
    '--use-gl=egl',
    '--enable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--window-size=1080,1920'
])
```

## TACHES DE FORGE

### SESSION 1 — Flask + endpoints (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F05-S1-T1 | Créer m3_f05.ipynb : Flask + montage Drive + Playwright install | 🔴 TODO |
| F05-S1-T2 | GET / → viewer HTML | 🔴 TODO |
| F05-S1-T3 | GET /files/avatar + /files/decor → GLBs | 🔴 TODO |
| F05-S1-T4 | GET /config/spawn + /config/camera + /config/light → JSONs | 🔴 TODO |
| F05-S1-T5 | POST /render → lancer thread Playwright en background | 🔴 TODO |
| F05-S1-T6 | GET /status → retourner {frame_current, total_frames, pct, eta_s} | 🔴 TODO |
| F05-S1-T7 | POST /cancel → stopper le thread Playwright | 🔴 TODO |

### SESSION 2 — HTML viewer skeleton + panel PostFX (40 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F05-S2-T1 | Structure HTML : topbar + viewport + panel 265px + palette | 🔴 TODO |
| F05-S2-T2 | Topbar : auto-load indicator + barre progression si render actif | 🔴 TODO |
| F05-S2-T3 | Panel sections : BLOOM / VIGNETTE / COULEUR / STYLE / FPS RENDER | 🔴 TODO |
| F05-S2-T4 | Sliders : Bloom strength/radius/threshold, Vignette offset/darkness | 🔴 TODO |
| F05-S2-T5 | Sliders : Saturation, Brightness, Contrast | 🔴 TODO |
| F05-S2-T6 | Toggles : FXAA ON/OFF, Toon Shader ON/OFF | 🔴 TODO |
| F05-S2-T7 | Boutons fps : 24fps (recommandé) / 30fps / 60fps | 🔴 TODO |
| F05-S2-T8 | Bouton [LANCER RENDER] gold + barre progression + [ANNULER] | 🔴 TODO |

### SESSION 3 — Three.js scene complète (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F05-S3-T1 | Renderer WebGL, canvas 1080x1920, pixelRatio(1) | 🔴 TODO |
| F05-S3-T2 | Auto-fetch /config/* → appliquer camera_config + light_config + spawn_config | 🔴 TODO |
| F05-S3-T3 | GLTFLoader : charger avatar + decor + positionner selon spawn | 🔴 TODO |
| F05-S3-T4 | AnimationMixer sur avatar (sélectionner clip depuis f01_report) | 🔴 TODO |
| F05-S3-T5 | Appliquer ROOT MOTION : lire trajectory de spawn_config | 🔴 TODO |
| F05-S3-T6 | Div #scene-ready → reveler quand tous assets chargés (signal Playwright) | 🔴 TODO |

### SESSION 4 — EffectComposer pmndrs + PostFX (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F05-S4-T1 | Import pmndrs/postprocessing depuis CDN ESM | 🔴 TODO |
| F05-S4-T2 | EffectComposer → RenderPass + EffectPass | 🔴 TODO |
| F05-S4-T3 | BloomEffect : strength/radius/threshold depuis sliders panel | 🔴 TODO |
| F05-S4-T4 | VignetteEffect : offset/darkness | 🔴 TODO |
| F05-S4-T5 | HueSaturationEffect : saturation/brightness | 🔴 TODO |
| F05-S4-T6 | FXAAEffect (toggle) | 🔴 TODO |
| F05-S4-T7 | Toon shader : toggle MeshToonMaterial sur tous meshes avatar | 🔴 TODO |
| F05-S4-T8 | Preview live : composer.render() dans requestAnimationFrame | 🔴 TODO |

### SESSION 5 — Boucle capture Playwright (60 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F05-S5-T1 | window.setRenderFrame(n) : mixer.setTime + lerpVectors + render + signal | 🔴 TODO |
| F05-S5-T2 | Div #frame-done : toggle ON après render, OFF avant (signal Playwright) | 🔴 TODO |
| F05-S5-T3 | Python Playwright : launch avec flags GPU EGL | 🔴 TODO |
| F05-S5-T4 | Playwright : page.goto → wait_for_selector('#scene-ready') | 🔴 TODO |
| F05-S5-T5 | Playwright : boucle for frame_n → evaluate + wait #frame-done + screenshot | 🔴 TODO |
| F05-S5-T6 | Playwright : upload frame sur Drive après chaque capture | 🔴 TODO |
| F05-S5-T7 | Checkpoint : save_checkpoint(frame_n) → f05_checkpoint.json Drive | 🔴 TODO |
| F05-S5-T8 | Reprise : si checkpoint existe → reprendre depuis frame N+1 | 🔴 TODO |

### SESSION 6 — Monitoring HTML + polling (20 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F05-S6-T1 | setInterval fetch('/status') toutes 2s si render actif | 🔴 TODO |
| F05-S6-T2 | Barre progression mise à jour live (frame_current / total_frames) | 🔴 TODO |
| F05-S6-T3 | Afficher ETA calculé en minutes | 🔴 TODO |
| F05-S6-T4 | Bouton ANNULER → POST /cancel → stopper thread | 🔴 TODO |
| F05-S6-T5 | Quand status == DONE → feedback "Render terminé — N frames" | 🔴 TODO |

## VALIDATION SCEAU
- [ ] Playwright charge le viewer sans erreur WebGL
- [ ] GPU T4 actif (flags EGL vérifiés via GPU info console)
- [ ] root motion : avatar se déplace de start à end sur durée anim
- [ ] root motion mode STATIC : avatar reste fixe
- [ ] PostFX Bloom visible dans le preview
- [ ] Frame 0001.png capturée et uploadée Drive
- [ ] Checkpoint créé et reprise fonctionnelle
- [ ] 365 frames complètes sans corruption
