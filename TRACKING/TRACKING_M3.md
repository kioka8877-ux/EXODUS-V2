# TRACKING MASTER — MODE III ASCENSION
## CODEX MACHINUS — TOME V

```
╔═══════════════════════════════════════════════════════════════════╗
║  MODE III — ASCENSION — SCELLÉ ✅                                ║
║  6 Frégates — Pipeline Three.js + Flask + Playwright + RIFE      ║
║  Doctrine ATOM-IC — Palette Impériale #c8a96e                    ║
╚═══════════════════════════════════════════════════════════════════╝
```

## TABLEAU DE BORD M3

| ID | Frégate | Mission | Priorité | Statut | Bloqueur |
|----|---------|---------|----------|--------|----------|
| F01 | VALIDATION | GLB + Audio → rapport JSON | P1 | ✅ FORGE | — |
| F02 | LOGISTICS | Attach props → actor_equipped.glb | P2 | ✅ FORGE | F01 |
| F03 | SCENOGRAPHY | Spawn + Trajectoire → spawn_config.json | P0 | ✅ FORGE | — |
| F04 | PHOTOGRAPHY | Camera + Lights → 2 JSONs | P1 | ✅ FORGE | F03 |
| F05 | ALCHEMIST | Render GPU T4 → frames PNG | P0 | ✅ FORGE | F03 F04 |
| F06 | CARRIER | RIFE + ffmpeg → MP4 final | P0 | ✅ FORGE | F05 |

## ORDRE DE FORGE (Pareto)
```
F06 → F01 → F03 → F04 → F02 → F05
```
Raisonnement : valider le pipeline ffmpeg/RIFE et les JSON flows
avant de toucher au GPU headless (F05 = plus critique, forge en dernier).

## PROGRESSION GLOBALE
Mode III Ascension : [████████████████] 100% — 6/6 FRÉGATES FORGÉES ✅

## DECISIONS ARCHITECTURALES SCELLEES

### JS — Three.js retenu (Babylon.js exclu)
- GLTFExporter natif three/addons → F02
- TransformControls + OrbitControls natifs → F03 F04
- EffectComposer pmndrs/postprocessing → F05
- CDN ESM zero-build → compatible Colab Flask

### Viewers
- F01 : Vanilla HTML + GLTFLoader only (zero WebGL renderer)
- F02 : Fork donmccurdy/three-gltf-viewer + SKIP button
- F03 : Fork m2_f03_viewer.html v4.0 + 2 modifs + TRAJECTOIRE
- F04 : Fork donmccurdy/three-gltf-viewer + lil-gui + presets
- F05 : Fork donmccurdy/three-gltf-viewer + EffectComposer + render loop
- F06 : Vanilla HTML monitoring (zero 3D)

### Pipeline avatar
Triposr → Meshy AI (rig) → Deepmotion (animate) → GLB standard bones
Round-trip GLB → Three.js → GLB : SAFE (bones standard, pas d'extensions KHR custom)

### ROOT MOTION — DECISION CRITIQUE
Deepmotion produit des animations IN-PLACE (avatar reste à l'origine 0,0,0).
Solution retenue : TRAJECTOIRE LINEAIRE
- F03 viewer : panneau TRAJECTOIRE — utilisateur positionne avatar au départ
  puis tire vers position d'arrivée → spawn_config.json contient :
  { trajectory: { start: {x,y,z}, end: {x,y,z}, mode: "linear" } }
- F05 viewer : au frame N, avatarRoot.position.lerpVectors(start, end, N/totalFrames)
- Couverture : 80% des cas (déplacement A→B en ligne droite)
- Extension future possible : waypoints bezier (hors scope M3 initial)

## DOSSIERS M3 (structure repo)
```
03_MODE_ASCENSION/
  F01_VALIDATION/
    CODEBASE/
      m3_f01.ipynb          ← Colab notebook Flask
      m3_f01_viewer.html    ← Dashboard validation
  F02_LOGISTICS/
    CODEBASE/
      m3_f02.ipynb
      m3_f02_viewer.html
  F03_SCENOGRAPHY/
    CODEBASE/
      m3_f03.ipynb
      m3_f03_viewer.html
  F04_PHOTOGRAPHY/
    CODEBASE/
      m3_f04.ipynb
      m3_f04_viewer.html
  F05_ALCHEMIST/
    CODEBASE/
      m3_f05.ipynb
      m3_f05_viewer.html
  F06_CARRIER/
    CODEBASE/
      m3_f06.ipynb
      m3_f06_monitor.html
  SHARED/
    flask_drive_utils.py    ← helpers Drive communs
    m3_constants.py         ← chemins Drive constants
```

## LIENS
- [F01](./TRACKING_M3_F01.md) | [F02](./TRACKING_M3_F02.md) | [F03](./TRACKING_M3_F03.md)
- [F04](./TRACKING_M3_F04.md) | [F05](./TRACKING_M3_F05.md) | [F06](./TRACKING_M3_F06.md)
- [MASTER](./TRACKING_MASTER.md)
