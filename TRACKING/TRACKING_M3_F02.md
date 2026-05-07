# TRACKING F02 — LOGISTICS
## "L'Armurerie du Magos"

**Statut** : 🔴 A FORGER
**Priorité** : P2
**Dépendances entrantes** : m3_f01_report.json (has_audio, selected_clip)
**Dépendances sortantes** : actor_equipped.glb OU m3_f02_report.json (SKIPPED)

## MISSION
Attacher props 3D sur les bones de l'avatar dans un viewer interactif.
Output : actor_equipped.glb (avec props) OU rapport SKIPPED (60% des cas).

## INPUTS / OUTPUTS
```
IN  : actor.glb (avatar animé Drive) + props/*.glb (Drive, optionnel)
OUT : actor_equipped.glb  (si props attachés)
  OU m3_f02_report.json { "status": "SKIPPED" }
```

## STACK TECHNIQUE
- Three.js r160 (CDN ESM) — scene complète
- three/addons : GLTFLoader, GLTFExporter, TransformControls, SkeletonHelper
- lil-gui (CDN) — panneau bones
- Fork base : donmccurdy/three-gltf-viewer (structure + camera + lights)
- Flask Python — sert viewer + save GLB/rapport

## TACHES DE FORGE

### SESSION 1 — Flask + structure (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F02-S1-T1 | Créer m3_f02.ipynb : Flask + montage Drive | 🔴 TODO |
| F02-S1-T2 | GET / → viewer HTML | 🔴 TODO |
| F02-S1-T3 | GET /files/avatar → GLB avatar depuis Drive | 🔴 TODO |
| F02-S1-T4 | GET /files/props → liste props disponibles (JSON) | 🔴 TODO |
| F02-S1-T5 | GET /files/prop/{name} → GLB prop depuis Drive | 🔴 TODO |
| F02-S1-T6 | POST /save-actor → écrire GLB binaire sur Drive | 🔴 TODO |
| F02-S1-T7 | POST /save-report → écrire JSON SKIPPED sur Drive | 🔴 TODO |

### SESSION 2 — HTML viewer skeleton + topbar (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F02-S2-T1 | Structure HTML : topbar + viewport + panel 265px + palette | 🔴 TODO |
| F02-S2-T2 | Topbar : bouton [CHARGER AVATAR DRIVE] + [CHARGER PROP +] | 🔴 TODO |
| F02-S2-T3 | Bouton [SKIP — SANS PROPS] gold, très visible, haut du panel | 🔴 TODO |
| F02-S2-T4 | Section panel : liste props chargés + statut | 🔴 TODO |
| F02-S2-T5 | Bouton [CONFIRMER + EXPORT] en bas du panel | 🔴 TODO |

### SESSION 3 — Three.js scene + avatar (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F02-S3-T1 | Renderer WebGL + scene + camera PerspectiveCamera | 🔴 TODO |
| F02-S3-T2 | OrbitControls sur la scene | 🔴 TODO |
| F02-S3-T3 | Lumières : AmbientLight + DirectionalLight | 🔴 TODO |
| F02-S3-T4 | GLTFLoader → charge avatar → add to scene | 🔴 TODO |
| F02-S3-T5 | AnimationMixer sur avatar (loop preview) | 🔴 TODO |

### SESSION 4 — SkeletonHelper + arbre bones (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F02-S4-T1 | SkeletonHelper(avatar) → fil blanc sur bones | 🔴 TODO |
| F02-S4-T2 | Traverser skeleton.bones → générer arbre HTML dans panel | 🔴 TODO |
| F02-S4-T3 | Clic sur bone dans arbre → highlight gold + marque cible | 🔴 TODO |
| F02-S4-T4 | Afficher coordonnées bone sélectionné dans panel | 🔴 TODO |

### SESSION 5 — Props + TransformControls + GLTFExporter (60 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F02-S5-T1 | GLTFLoader → charge prop GLB | 🔴 TODO |
| F02-S5-T2 | bone.attach(propMesh) → prop suit le squelette | 🔴 TODO |
| F02-S5-T3 | TransformControls sur prop sélectionné (XYZ gold) | 🔴 TODO |
| F02-S5-T4 | Dropdown sélecteur bone cible dans panel | 🔴 TODO |
| F02-S5-T5 | GLTFExporter.parse(scene) → Blob → POST /save-actor | 🔴 TODO |
| F02-S5-T6 | Flow SKIP → POST /save-report {status:SKIPPED} | 🔴 TODO |

## VALIDATION SCEAU
- [ ] SKIP fonctionne et sauve rapport SKIPPED
- [ ] Prop visible attaché au bone cible
- [ ] Prop suit l'animation en preview
- [ ] TransformControls permet offset position/rotation
- [ ] GLTFExporter produit un GLB valide
- [ ] GLB sauvé sur Drive
