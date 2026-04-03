# TRACKING_VOID_FLUSH — Tech-Pretre VOID-FLUSH

> Responsable : VOX (Scribe de l'Empire)
> Priorite : P1

---

## Identite

| Champ | Valeur |
|-------|--------|
| Nom | VOID-FLUSH |
| Type | Tech-Pretre / Mini Program |
| Priorite | P1 |
| Statut | OPERATIONNEL |
| Cree le | 2026-04-03 |
| Valide par | Empereur |

---

## Role

Nettoyage GPU/VRAM avant et apres les rendus lourds.
Purge les data-blocks Blender orphelins entre les executions de frégates.

---

## Fichiers

| Fichier | Role |
|---------|------|
| `void_flush.py` | Orchestrateur principal — CLI |
| `blender_adapter.py` | Interface avec l'API Blender (hooks pre/post-render) |
| `feature_flags.json` | Activation/desactivation des etapes de flush |

---

## Contrats

**Entree :** Contexte Blender actif OU mode standalone (Python pur)

**Sortie :** Rapport JSON `{ status, fregate, actions, timestamp }`

**Garantie :** Apres flush, depsgraph est a jour (FIX D6_depsgraph inclus)

---

## Phases

| Phase | Description | Statut |
|-------|-------------|--------|
| P1.0 | Creation structure + code | COMPLETE |
| P1.1 | Integration dans U03 | EN ATTENTE |
| P1.2 | Integration dans U04 | EN ATTENTE |
| P1.3 | Tests sur donnees reelles | EN ATTENTE |

---

## Decisions

| Date | Decision | Raison |
|------|----------|--------|
| 2026-04-03 | VOID-FLUSH integre le fix D6_depsgraph (depsgraph.update()) | Pattern deja valide, reutilisation directe |
| 2026-04-03 | feature_flags.json pour activer/desactiver chaque etape | Flexibilite sans modifier le code |

---

## Bloquants Actuels

- Aucun — prêt pour integration dans les frégates
