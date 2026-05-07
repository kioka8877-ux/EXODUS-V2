# TRACKING F01 — VALIDATION
## "Le Scrutateur du Mechanicus"

**Statut** : 🔴 A FORGER
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
| F01-S1-T1 | Créer m3_f01.ipynb : imports Flask, montage Drive | 🔴 TODO |
| F01-S1-T2 | Endpoint GET / → servir m3_f01_viewer.html | 🔴 TODO |
| F01-S1-T3 | Endpoint GET /files/avatar → lire GLB depuis Drive | 🔴 TODO |
| F01-S1-T4 | Endpoint GET /files/audio → lire MP3 depuis Drive | 🔴 TODO |
| F01-S1-T5 | Endpoint POST /save-report → écrire JSON sur Drive | 🔴 TODO |

### SESSION 2 — HTML viewer skeleton (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S2-T1 | HTML structure : topbar + main container + palette Impériale | 🔴 TODO |
| F01-S2-T2 | Section toggle AVEC/SANS AUDIO | 🔴 TODO |
| F01-S2-T3 | Section status GLB : badge chargé/erreur | 🔴 TODO |
| F01-S2-T4 | Section status Audio : badge chargé/erreur | 🔴 TODO |
| F01-S2-T5 | Bouton CONFIRMER (désactivé par défaut) | 🔴 TODO |

### SESSION 3 — Logique JS GLTFLoader (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S3-T1 | Import GLTFLoader ESM depuis CDN (zero renderer) | 🔴 TODO |
| F01-S3-T2 | fetch('/files/avatar') → ArrayBuffer → GLTFLoader.parse() | 🔴 TODO |
| F01-S3-T3 | Extraire gltf.animations[i].duration → liste clips | 🔴 TODO |
| F01-S3-T4 | Rendre liste clips cliquable (sélection du clip de référence) | 🔴 TODO |
| F01-S3-T5 | AudioContext.decodeAudioData() → buffer.duration | 🔴 TODO |

### SESSION 4 — Validation + rapport + barres CSS (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F01-S4-T1 | Calcul : audio_duration ≤ anim_duration → OK/FAIL | 🔴 TODO |
| F01-S4-T2 | Barres CSS proportionnelles (gold = anim, bleu = audio) | 🔴 TODO |
| F01-S4-T3 | Badge résultat (vert OK / rouge FAIL) avec marge en secondes | 🔴 TODO |
| F01-S4-T4 | JSON preview monospace auto-généré | 🔴 TODO |
| F01-S4-T5 | POST /save-report → feedback "Sauvé sur Drive" | 🔴 TODO |

## VALIDATION SCEAU
- [ ] GLB charge sans renderer WebGL
- [ ] Clip sélectionnable dans la liste
- [ ] Validation OK si audio ≤ anim
- [ ] FAIL bloque bouton CONFIRMER
- [ ] JSON valide sauvé sur Drive
