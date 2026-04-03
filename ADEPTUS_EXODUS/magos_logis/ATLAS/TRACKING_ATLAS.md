# TRACKING_ATLAS — Tech-Pretre ATLAS

> Responsable : VOX (Scribe de l'Empire)
> Priorite : P2

---

## Identite

| Champ | Valeur |
|-------|--------|
| Nom | ATLAS |
| Type | Tech-Pretre / Mini Program |
| Priorite | P2 |
| Statut | OPERATIONNEL |
| Cree le | 2026-04-03 |
| Valide par | Empereur |

---

## Role

Source de verite pour tous les chemins de l'Empire.
Centralise les chemins absolus de chaque fregate, persiste l'etat du pipeline,
et fournit un store de session par fregate pour eviter les recalculs.

---

## Fichiers

| Fichier | Role |
|---------|------|
| `atlas.py` | CLI — resolution chemins, health check, etat pipeline |
| `session_store.py` | Persistance session par fregate (JSON sur disque) |
| `pipeline_state.json` | Etat global du pipeline (fregates + tech-pretres) |
| `sessions/` | Dossier auto-cree — une session JSON par fregate |

---

## Contrats

**Entree :** fregate_id (U00-U06), folder name, ou aucun (etat global)

**Sortie :**
- `resolve_path(fregate_id, folder)` → Path absolu
- `get_fregate_paths(fregate_id)` → dict complet inputs/outputs/codebase
- `check_fregate_health(fregate_id)` → rapport N/N checks OK
- `SessionStore(fregate_id)` → store persistant cle/valeur

---

## Phases

| Phase | Description | Statut |
|-------|-------------|--------|
| P2.0 | Creation structure + code | COMPLETE |
| P2.1 | Integration dans U03 (session_store) | EN ATTENTE |
| P2.2 | Integration dans U04 (chemins render) | EN ATTENTE |
| P2.3 | pipeline_state.json mis a jour automatiquement | EN ATTENTE |

---

## Decisions

| Date | Decision | Raison |
|------|----------|--------|
| 2026-04-03 | ATLAS centralise tous les chemins | Eviter les chemins hardcodes dans chaque fregate |
| 2026-04-03 | SessionStore par fregate (JSON) | Persistance legere sans dependance externe |
| 2026-04-03 | pipeline_state.json comme source de verite | KRONOS et VOX pourront le lire directement |

---

## Bloquants Actuels

- Aucun — prêt pour integration dans les frégates
