# RULES — U03 SCENOGRAPHY DOCK

> Loi de l'Empire : Les frégates produisent. Les Mini Programs servent.

## Contrat d'Interface

### Inputs obligatoires
| Fichier / Dossier | Type | Description |
|---|---|---|
| `IN_CORTEX_JSON/PRODUCTION_PLAN.JSON` | JSON | Spécifications scènes (U00 → U03) |
| `IN_MAP_RAW/` | Dossier | Depth maps PNG + semantic_masks.json |
| `--drive-root` | CLI arg | Chemin racine Drive EXODUS |

### Outputs garantis
| Fichier | Type | Description |
|---|---|---|
| `OUT_PREMIUM_SCENE/environment_{scene_id}.blend` | Blender | Scène Tri-Layer construite |
| `OUT_PREMIUM_SCENE/scenography_report.json` | JSON | Rapport de construction V2 |
| `OUT_PREMIUM_SCENE/assembler_results.json` | JSON | Résultats par scène (scene_type, env_id) |

## Règles Architecturales

### R1 — Isolation des Silos
U03 ne communique avec aucune autre Frégate directement.
Elle lit IN_CORTEX_JSON (produit par U00) et écrit OUT_PREMIUM_SCENE (consommé par U04).
**Toute dépendance directe inter-frégates est une hérésie.**

### R2 — Tri-Layer System Obligatoire
Toute scène produite DOIT contenir les 3 couches :
- **Couche A** : Infinity Dome (collection ENV_DOME)
- **Couche B** : Displacement Mesh (collection ENV_TERRAIN)
- **Couche C** : PBR Swap + Reflectivity Hack (collections ENV_GLASS, ENV_SHADOW)

### R3 — VRAM Cap
Le paramètre `max_subdivisions` DOIT respecter le profil VRAM :
- `colab_t4` → max 96x96
- `colab_a100` → max 256x256
- `local_low` → max 64x64

### R4 — Camera Placeholder
Toute scène `.blend` générée DOIT contenir une `camera_main` (lens=35mm).
U04 peut l'overrider, mais le placeholder DOIT exister pour éviter le BUG D6.

### R5 — World Sync
`world.use_nodes = True` est obligatoire.
`world.node_tree` DOIT contenir un nœud Environment Texture OU une couleur solide.
`strength` = valeur du paramètre `--exposure` (défaut 1.0).

### R6 — Rapports
`scenography_report.json` DOIT être généré même en cas d'échec partiel.
Status = `"SUCCESS"`, `"PARTIAL"`, ou `"FAILED"` — jamais absent.

## Règles VOID-FLUSH

### VF1 — Pre-render Flush
`flush_before_render(fregate_id="U03")` DOIT être appelé avant chaque subprocess Blender.
Objectif : Purge mémoire GPU/VRAM + GC Python.

### VF2 — Graceful Fallback
Si `blender_adapter` est indisponible, U03 continue sans interruption.
Le flag `_VOID_FLUSH_AVAILABLE` contrôle ce comportement.

## Règles ATLAS

### AT1 — Session Persistence
Après chaque run réussi, SessionStore("U03") DOIT être sauvegardé avec :
- `drive_root`, `output_dir`, `vram_profile`, `exposure`, `last_run`

### AT2 — Aucun Hardcode Drive
Les chemins Drive ne sont JAMAIS hardcodés dans le code source.
Ils passent par `--drive-root` (CLI) ou `SessionStore` (session précédente).

## Règles de Validation

### V1 — Schema Validation
`scene_schema.validate_scene()` DOIT passer sur chaque `.blend` produit.
Violations = build failed (non bloquant en dry-run).

### V2 — Marshal Check
`EXO_MARSHAL.py` doit valider la structure IN/OUT avant et après chaque run.

## Versions et Compatibilité

| Composant | Version requise |
|---|---|
| Blender | 4.0.0 Linux x64 |
| Python | 3.10+ |
| scene_schema.py | 2.0+ |
| layer_assembler.py | 2.1+ |

<!-- VOX-RULES-U03 v1.0 — Tache 46 Phase 5 -->
