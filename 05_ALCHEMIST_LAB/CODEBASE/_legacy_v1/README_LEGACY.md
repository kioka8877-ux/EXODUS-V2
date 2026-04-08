# LEGACY V1 — Fichiers Inactifs

> Archive : [VULKAN_FORGE] — 2026-04-08

Ces fichiers appartiennent a la V1 du pipeline Alchemist Lab.
Ils dependaient de **Blender Compositor**, **LUTs .cube**, **OptiX/OIDN**
et sont **incompatibles** avec la stack V2 (OpenCV CPU pur).

**Ne pas importer. Ne pas executer.**

## Fichiers archivés

| Fichier | Role V1 | Raison archivage |
|---------|---------|-----------------|
| `compositor_pipeline.py` | Blender Compositor nodes | Remplace par EXO_05_ALCHEMIST.py |
| `color_grader.py` | LUTs .cube | Remplace par match_color.py |
| `effects_forge.py` | Effets Blender (bloom, grain) | Remplace par bloom_engine.py + grain_matcher.py |
| `denoiser.py` | OptiX/OIDN GPU | Hors scope V2 CPU pur |

## Stack V2 Active

```
alchemist_schema.py      — Bible Alchimique (7 piliers, 5 presets)
match_color.py           — Transfert couleur LAB
grain_matcher.py         — Transfert grain filmique
bloom_engine.py          — Bloom additif OpenCV
sharpness_transfer.py    — Alignement nettete Laplacian
EXO_05_ALCHEMIST.py      — Orchestrateur CLI V2
```
