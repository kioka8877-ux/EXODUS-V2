# TRACKING F01 — VALIDATION
## "Le Scrutateur du Mechanicus"

**Statut** : ✅ FORGE
**Priorité** : P1
**Dépendances entrantes** : aucune
**Dépendances sortantes** : m3_f01_report.json → F02 F03 F04 F05 F06

## MISSION
Lire metadata GLB (durée animations) + durée audio.mp3
→ produire m3_f01_report.json (validation + clip sélectionné + has_audio)

## INPUTS / OUTPUTS
```
IN  : avatar.glb (Drive) + audio.mp3 (Drive, optionnel)
OUT : m3_f01_report.json
      {
        "status": "OK|FAIL",
        "has_audio": true|false,
        "audio_duration": 14.8,
        "anim_duration": 15.2,
        "selected_clip": "Dance_01",
        "all_clips": [...],
        "margin_s": 0.4
      }
```

## STACK TECHNIQUE
- HTML pur, zero Three.js renderer, zero WebGL
- GLTFLoader (ESM CDN) — lecture metadata uniquement
- Web Audio API (natif navigateur) — lecture durée audio
- Flask Python — sert le viewer + save rapport Drive
- ~200 lignes HTML total

## TACHES DE FORGE

### SESSION 1 — Flask + structure (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S1-T1 | Créer m3_f01.ipynb : imports Flask, montage Drive | ✅ DONE |
| F01-S1-T2 | Endpoint GET / → servir m3_f01_viewer.html | ✅ DONE |
| F01-S1-T3 | Endpoint GET /files/avatar → lire GLB depuis Drive | ✅ DONE |
| F01-S1-T4 | Endpoint GET /files/audio → lire MP3 depuis Drive | ✅ DONE |
| F01-S1-T5 | Endpoint POST /save-report → écrire JSON sur Drive | ✅ DONE |

### SESSION 2 — HTML viewer skeleton (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S2-T1 | HTML structure : topbar + main container + palette Impériale | ✅ DONE |
| F01-S2-T2 | Section toggle AVEC/SANS AUDIO | ✅ DONE |
| F01-S2-T3 | Section status GLB : badge chargé/erreur | ✅ DONE |
| F01-S2-T4 | Section status Audio : badge chargé/erreur | ✅ DONE |
| F01-S2-T5 | Bouton CONFIRMER (désactivé par défaut) | ✅ DONE |

### SESSION 3 — Logique JS GLTFLoader (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S3-T1 | Import GLTFLoader ESM depuis CDN (zero renderer) | ✅ DONE |
| F01-S3-T2 | fetch('/files/avatar') → ArrayBuffer → GLTFLoader.parse() | ✅ DONE |
| F01-S3-T3 | Extraire gltf.animations[i].duration → liste clips | ✅ DONE |
| F01-S3-T4 | Rendre liste clips cliquable (sélection du clip de référence) | ✅ DONE |
| F01-S3-T5 | AudioContext.decodeAudioData() → buffer.duration | ✅ DONE |

### SESSION 4 — Validation + rapport + barres CSS (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S4-T1 | Calcul : audio_duration ≤ anim_duration → OK/FAIL | ✅ DONE |
| F01-S4-T2 | Barres CSS proportionnelles (gold = anim, bleu = audio) | ✅ DONE |
| F01-S4-T3 | Badge résultat (vert OK / rouge FAIL) avec marge en secondes | ✅ DONE |
| F01-S4-T4 | JSON preview monospace auto-généré | ✅ DONE |
| F01-S4-T5 | POST /save-report → feedback "Sauvé sur Drive" | ✅ DONE |

## VALIDATION SCEAU
- [x] GLB charge sans renderer WebGL
- [x] Clip sélectionnable dans la liste
- [x] Validation OK si audio ≤ anim
- [x] FAIL bloque bouton CONFIRMER
- [x] JSON valide sauvé sur Drive

## FICHIERS FORGES
| Fichier | Description |
|---------|-------------|
| `m3_f01_flask.py` | Flask 5 endpoints : `/`, `/info`, `/files/avatar`, `/files/audio`, `/save-report` |
| `m3_f01_viewer.html` | HTML pur — GLTFLoader ESM CDN, Web Audio API, zero WebGL, clips cliquables, barres CSS, JSON preview |
| `m3_f01.ipynb` | 4 cellules Colab : montage Drive, vérif inputs, lancement Flask, headless commenté |
