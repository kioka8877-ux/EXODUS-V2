# RULES — U04 PHOTOGRAPHY WING

> Loi de l'Empire : Les frégates produisent. Les Mini Programs servent.

## Contrat d'Interface

### Inputs obligatoires
| Fichier / Dossier | Type | Description |
|---|---|---|
| `IN_SCENE_REF/environment_*.blend` | Blender | Scènes Tri-Layer de U03 |
| `IN_SCENE_REF/PRODUCTION_PLAN.JSON` | JSON | Spécifications caméra/éclairage (U00 → U04) |
| `--drive-root` | CLI arg | Chemin racine Drive EXODUS |

### Outputs garantis (U04-A Director)
| Fichier | Type | Description |
|---|---|---|
| `OUT_CAMERA_LOGIC/scene_ready_{scene_id}.blend` | Blender | Scène prête au rendu |
| `OUT_CAMERA_LOGIC/camera_data_{scene_id}.json` | JSON | Export données caméra |
| `OUT_CAMERA_LOGIC/photography_report.json` | JSON | Rapport complet |

### Outputs garantis (U04-B Darkroom)
| Fichier | Type | Description |
|---|---|---|
| `OUT_FRAMES/chunk_{n}/frame_{f:04d}.png` | PNG 16-bit | Frames rendues |
| `OUT_FRAMES/render_checkpoint.json` | JSON | État du rendu (resume support) |

## Règles Architecturales

### R1 — Isolation des Silos
U04 ne communique avec aucune autre Frégate directement.
Elle lit IN_SCENE_REF (produit par U03) et écrit OUT_CAMERA_LOGIC (consommé par U05/U06).
**Toute dépendance directe inter-frégates est une hérésie.**

### R2 — Séparation A/B
- **U04-A (Director)** : Configure `.blend` uniquement — PAS de rendu. ~30s.
- **U04-B (Darkroom)** : Lance le rendu batch — NE modifie PAS la configuration caméra.
Ces deux sous-frégates ne se font PAS appel mutuellement.

### R3 — Perspective Lock (Pilier A)
Toute caméra configurée DOIT avoir `fSpy perspective lock` appliqué si `camera_fov_ratio.json` est fourni.
Tolérance : ±5% sur le FOV. Au-delà = warning dans le rapport.

### R4 — DOF Automatique (Pilier B)
`auto_dof.py` DOIT créer un Empty parenté au buste avatar et le lier au paramètre DOF.
Si l'avatar n'est pas présent, DOF est désactivé (pas d'erreur).

### R5 — Shake Procédural (Pilier C)
Le shake caméra DOIT utiliser le Noise Modifier de Blender (Graph Editor).
`random.gauss` est INTERDIT — résultats non reproductibles.

### R6 — Preset Darkroom
Pour U04-B, le preset DOIT être `darkroom` (1080p, 128 samples, OIDN, PNG 16-bit).
Le preset `production` est réservé à U04-A.

### R7 — Rapports
`photography_report.json` DOIT être généré même si certaines scènes échouent.
Status = `"SUCCESS"`, `"PARTIAL"`, ou `"FAILED"`.

## Règles VOID-FLUSH

### VF1 — Pre-render Flush
`flush_before_render(fregate_id="U04")` DOIT être appelé avant chaque subprocess Blender.
Objectif : Purge mémoire GPU/VRAM + GC Python.

### VF2 — Graceful Fallback
Si `blender_adapter` est indisponible, U04 continue sans interruption.

## Règles ATLAS

### AT1 — Session Persistence
Après chaque run réussi, SessionStore("U04") DOIT être sauvegardé avec :
- `drive_root`, `output_dir`, `preset`, `shake_preset`, `scenes_total`, `last_run`

### AT2 — Aucun Hardcode Drive
Les chemins Drive ne sont JAMAIS hardcodés dans le code source.

## Règles d'Éclairage Adaptatif

### EA1 — Chaîne de Priorité
L'éclairage est déterminé selon l'ordre de priorité suivant :
1. Valeurs explicites JSON (`lighting.style`) → Priority 1
2. `scene_type` fourni par U03 → Priority 2 (SCENE_TYPE_TO_LIGHTING)
3. `preset_id` fourni par U00 → Priority 3 (LIGHTING_PRESET_TO_STYLE)

### EA2 — Fallback
Si aucune priorité ne matche, le style par défaut est `"3point"`.

## Versions et Compatibilité

| Composant | Version requise |
|---|---|
| Blender | 4.0.0 Linux x64 |
| Python | 3.10+ |
| camera_schema.py | 2.0+ (self_test 8/8) |
| camera_director.py | 2.0+ (frustum + matchmove) |

<!-- VOX-RULES-U04 v1.0 — Tache 46 Phase 5 -->
