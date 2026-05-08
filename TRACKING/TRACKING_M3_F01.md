# TRACKING F01 — VALIDATION
## "Le Scrutateur du Mechanicus"

**Statut** : ✅ SCELLÉ — TEST PROD OK (2026-05-08)
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


## SCEAU DE TEST EN PRODUCTION

**Date** : 2026-05-08
**Environnement** : Google Colab — proxy `*.colab.dev` — Flask local

### Résultat JSON validé

```json
{
  "status": "OK",
  "has_audio": false,
  "anim_duration": 4.133,
  "selected_clip": "A-person-runnin"
}
```

### Post-Mortem — Erreurs détectées et patchées

| # | Problème | Cause | Patch appliqué |
|---|----------|-------|----------------|
| 1 | `ReferenceError: setAudio is not defined` | `<script type="module">` isole les fonctions — `onclick=` inline ne trouve rien en scope global | `<script type="module">` → `<script>` classique |
| 2 | `Failed to resolve module specifier "three"` | Proxy Colab bloque les bare module specifiers | Retrait imports ES · Three.js chargé via CDN `three@0.128.0` |
| 3 | Cache agressif proxy Colab | Ctrl+Shift+R insuffisant | Cache-busting `?v=N` dans l'URL |
| 4 | Cellule Flask écrase le patch HTML | `shutil.copy` re-exécuté après patch local | Ne pas re-exécuter la cellule Flask après patch |

### Règle de doctrine généralisée
> Ne jamais utiliser `onclick=` inline quand les fonctions sont définies dans un `<script>`.
> Toujours câbler via `addEventListener`. Jamais `type="module"` avec Three.js CDN classic.

### Impact frégates sœurs
Post-mortem appliqué en audit préventif F02–F06 (2026-05-08) :
- **F02** : SAFE — onclick inline non-critique (script classique) → nettoyé
- **F03** : CRITIQUE → patché (commit `66f7b3d203`)
- **F04** : CRITIQUE → patché (commit `6030c50b09`)
- **F05** : CRITIQUE (importmap + bare specifiers) → patché (commit `5d871b57d7`)
- **F06** : SAFE — onclick inline non-critique → nettoyé (commit `e9683a60ad`)

---
**Verdict final** : F01 VALIDATION scellée. Pipeline JSON opérationnel. Frégate prête à transmettre `m3_f01_report.json` aux frégates aval (F02–F06).

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
