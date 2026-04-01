# SENTINEL_VALIDATION — Contrats de Sortie des 8 Briques
> Version D7 — 2026-04-01

---

## B2 — SIGNATURE D'ETAT (LE CORPS)

```json
STATE_SIG.json :
  fregate       : string (U00-U06)
  timestamp     : ISO 8601
  checks : {
    vertices    : { value: int, threshold: int, status: PASS|FAIL }
    camera      : { present: bool, position_non_nulle: bool, status: PASS|FAIL }
    gpu_active  : { value: bool, status: PASS|FAIL }
    energy_max  : { value: float, threshold: 1.0, status: PASS|FAIL }
    luminance   : { value: float, range: [50,200], status: PASS|FAIL }
    scene_type  : { value: string, not_unknown: bool, status: PASS|FAIL }
  }
  verdict       : PASS | WARN | FAIL
  elapsed_sec   : float (<30.0)
```

---

## B6 — LEDGER PERSISTANT (LA MEMOIRE)

```json
memory.json :
  version       : string
  entries : [
    {
      id          : string (UUID)
      fregate     : string
      timestamp   : ISO 8601
      erreur      : string (description courte)
      cause       : string (parametres incrimines)
      correction  : string (patch applique)
      auto_inject : bool
      occurrences : int
      derniere_vue: ISO 8601
    }
  ]
```

Contrat :
  - Deduplication : meme fregate + meme erreur = increment occurrences
  - auto_inject=True : correction injectee sans confirmation si occurrences > 1
  - Persistance : fichier Drive, pas memoire Python

---

## B8 — LE MIROIR (TEMPLATE ASSEMBLER)

### Structure du Prompt Assemble

```
[IDENTITE]
Tu es Vulkan, Architecte du pipeline EXODUS.
Methode : ATOM-IC
Role : prescrire le code MINIMAL pour combler un delta detecte.
Regles :
  - Ne pas refactoriser ce qui fonctionne
  - Une correction = un fichier + une ligne ciblee
  - Si plusieurs corrections : ordre de priorite obligatoire
  - Format de sortie : liste de patches, pas de prose

[CONTRAT {FREGATE}]
Fregate    : {fregate_id}
Output     : {output_attendu}
Contrainte : {contraintes_specifiques}

[DELTA DETECTE — Niveau 3]
{tableau_parametres_avec_gaps}

[HISTORIQUE LEDGER]
{inject:B6.{fregate}.last_3_errors}

[QUESTION]
Patches minimaux pour fermer tous les gaps.
Format :
  fichier: {nom_fichier}
  ligne  : {numero}
  avant  : {code_actuel}
  apres  : {code_corrige}
  raison : {explication_une_ligne}
```

### Parametres par Fregate

| Fregate | Parametres surveilles | Fichiers cibles |
|---------|----------------------|-----------------|
| U00 | scenes.count, camera.present, json.parseable | — |
| U01 | armature.keyframes, shapekeys.count, bones.count | blender_fusion.py, sync_engine.py |
| U02 | rig.scale, mesh_children, modifiers.blocking | socketing_engine.py, final_baker.py |
| U03 | vertices, energy, camera_main, render.engine, gpu | geometry_probe_u03.py, layer_assembler.py |
| U04 | luminance, resolution, frames_count, camera.keyframes | EXO_04_PHOTOGRAPHY.py |
| U05 | frames_processed, luminance.delta, rgb.sature | match_color.py, alchemist_schema.py |
| U06 | duration.delta, audio.sync, black_frames, codec | audio_sync.py, final_encoder.py |

---

## SENTINEL_CORE — ORCHESTRATEUR

```
sentinel_core.py contrats :
  Input  : fregate_id + blend_file ou output_dir
  Output : rapport complet {B2, B6_injections, B8_prompt, verdict}
  Timeout global : 90 secondes
  On FAIL : generer prompt Vulkan automatiquement
  On PASS : enregistrer dans Ledger comme reference
```

---

## INTEGRATION MARSHAL

```
EXO_MARSHAL.py hooks :
  pre_run  : sentinel_core.check(fregate_id) → STATE_SIG.json
  post_run : sentinel_core.record(fregate_id, resultat) → memory.json
  on_fail  : sentinel_core.prescribe(fregate_id) → prompt_vulkan.txt
```
