# TRACKING_VOX — Tech-Pretre VOX

> Responsable : VOX (se documente lui-meme — cas unique)
> Priorite : P3

---

## Identite

| Champ | Valeur |
|-------|--------|
| Nom | VOX |
| Type | Tech-Pretre / Mini Program |
| Priorite | P3 |
| Statut | OPERATIONNEL |
| Cree le | 2026-04-03 |
| Valide par | Empereur |

---

## Role

Scribe de l'Empire. Responsable de :
- Rapports de flotte (etat des 7 fregates)
- Creation et mise a jour de TOUS les .md de tracking (sauf VULKAN_FORGE/CONTEXT/)
- Tests de validation par fregate (contrats entree/sortie)
- Self-learning loop : erreurs -> regles -> RULES.md

---

## Fichiers

| Fichier | Role |
|---------|------|
| `vox.py` | Orchestrateur CLI principal |
| `fleet_reporter.py` | Genere TRACKING_MASTER.md et TRACKING_UXX.md |
| `test_runner_vox.py` | Tests de validation par fregate (7 contrats) |
| `self_learner.py` | Apprentissage : MEMORY/ -> RULES.md |
| `RULES.md` | Regles apprises (DO + AVOID + manuelles) |

---

## Contrats

**Entree :** Acces en lecture a ATLAS/pipeline_state.json + VULKAN_FORGE/MEMORY/

**Sortie :**
- Rapports Markdown dans TRACKING/
- Rapport JSON de tests par fregate
- RULES.md mis a jour apres chaque cycle d'apprentissage

---

## Exception Canonique

VOX ne touche PAS :
- `VULKAN_FORGE/CONTEXT/*.md` → gere par VULKAN_FORGE
- `VULKAN_FORGE/WEAPONS/TRACKING_WEAPONS.md` → gere par VULKAN_FORGE
- `VULKAN_FORGE/ARSENAL/fixes/TRACKING_FIXES.md` → gere par VULKAN_FORGE

---

## Phases

| Phase | Description | Statut |
|-------|-------------|--------|
| P3.0 | Creation structure + code | COMPLETE |
| P3.1 | Premier run --learn | EN ATTENTE |
| P3.2 | Premier run --test --all | EN ATTENTE |
| P3.3 | Integration avec KRONOS | EN ATTENTE |

---

## Decisions

| Date | Decision | Raison |
|------|----------|--------|
| 2026-04-03 | VOX se documente lui-meme | Exception unique — le Scribe ecrit son propre tracking |
| 2026-04-03 | RULES.md dans VOX/ | Les regles apprises appartiennent au Scribe |
| 2026-04-03 | fleet_reporter met a jour TRACKING_MASTER | VOX maintient la vue globale de la flotte |

---

## Bloquants Actuels

- Premier run --learn requis pour peupler RULES.md
- Premier run --test --all pour valider les 7 fregates
