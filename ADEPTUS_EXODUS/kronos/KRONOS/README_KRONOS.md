# KRONOS — Tech-Pretre Gardien de la Coherence

> "Ce qui n'est pas coherent se brise. Ce qui est scelle tient."
> Constitution : Les Mini Programs servent. L'Empereur valide.

---

## Pourquoi

Sans KRONOS, les derives passent inapercues.
Un fichier manquant, un contrat brise, une fregate degradee — personne ne le detecte.
KRONOS est le juge de l'Empire : il audite, compare, et scelle.

---

## Commandes

```bash
# Audit complet de la flotte (coherence par fregate)
python kronos.py --audit

# Parity check entre deux fregates
python kronos.py --parity U03 U04

# Voir le registre (sceaux + executions)
python kronos.py --registry

# Sceller l'etat actuel (snapshot immutable)
python kronos.py --seal

# Audit des Tech-Pretres
python kronos.py --tech-pretres

# Verifier tous les contrats
python parity_checker.py --contracts

# Detecter les derives vs dernier sceau
python parity_checker.py --drift
```

---

## Audit de Coherence

KRONOS verifie pour chaque fregate :

| Check | Description |
|-------|-------------|
| `dir_exists` | Dossier fregate present |
| `codebase_exists` | Dossier CODEBASE present |
| `tracking_md_exists` | TRACKING_UXX.md present dans TRACKING/ |
| `readme_dev_exists` | README_DEV.md present |
| `subplan_exists` | UNIT_XX_SUBPLAN.md present |
| `pipeline_state_known` | Fregate referencee dans ATLAS/pipeline_state.json |

Score : 6/6 = 100% coherence

---

## Sceaux

Un sceau est un snapshot immutable de l'etat de l'Empire.
Il est cree manuellement (sur ordre de l'Empereur) ou automatiquement apres chaque phase majeure.

```json
{
  "seal_id": "SEAL_20260403_PHASE4",
  "fleet_coherence": "~85%",
  "tech_pretres_present": 5,
  "validated_by": "Empereur"
}
```

Les sceaux ne se suppriment pas. Ils s'accumulent dans `execution_registry.json`.

---

## Relation avec VOX

- KRONOS genere les rapports d'audit
- VOX ecrit ces rapports dans les TRACKING_UXX.md
- Ensemble : detection derive + documentation automatique

---

## Relation avec ATLAS

- KRONOS lit `pipeline_state.json` d'ATLAS pour connaitre l'etat declare
- KRONOS compare l'etat declare a l'etat reel (fichiers sur disque)
- Les ecarts = derives a corriger
