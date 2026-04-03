# VOX — Tech-Pretre Scribe de l'Empire

> "Ce qui n'est pas ecrit n'existe pas. Ce qui est ecrit ne meurt jamais."
> Constitution : Les Mini Programs servent. L'Empereur valide.

---

## Pourquoi

Sans VOX, les rapports etaient ecrits a la main et souvent oublies.
Sans VOX, les erreurs se repetaient faute de memoire institutionnelle.
Sans VOX, personne ne validait systematiquement les contrats des fregates.

VOX resout les trois.

---

## Commandes

```bash
# Rapport global de la flotte
python vox.py --report

# Rapport d'une fregate specifique
python vox.py --report U03

# Tests de validation (toutes les fregates)
python test_runner_vox.py --all

# Tests d'une fregate avec details
python test_runner_vox.py --fregate U04 --verbose

# Lancer le cycle d'apprentissage
python self_learner.py --learn

# Voir les regles apprises
python self_learner.py --rules

# Ajouter une regle manuelle
python self_learner.py --add-rule "Toujours verifier scene.camera avant render"

# Mettre a jour tous les .md de tracking
python fleet_reporter.py
```

---

## Cycle Self-Learning

```
VULKAN_FORGE/MEMORY/what_failed.json
VULKAN_FORGE/MEMORY/what_worked.json
           |
           v
    self_learner.py
    extract_rules()
           |
           v
       RULES.md
    (DO + AVOID + manuel)
```

---

## Responsabilites .md

VOX cree et maintient :

| Fichier | Quand |
|---------|-------|
| `TRACKING/TRACKING_MASTER.md` | Apres chaque run fleet_reporter |
| `TRACKING/TRACKING_UXX.md` | Apres chaque changement d'etat fregate |
| `ADEPTUS_EXODUS/{nom}/TRACKING_{NOM}.md` | A la creation de chaque Tech-Pretre |
| `ADEPTUS_EXODUS/{nom}/README_{NOM}.md` | A la creation de chaque Tech-Pretre |

VOX ne touche PAS :
- `VULKAN_FORGE/CONTEXT/*.md`
- `VULKAN_FORGE/WEAPONS/TRACKING_WEAPONS.md`
- `VULKAN_FORGE/ARSENAL/fixes/TRACKING_FIXES.md`

---

## Integration avec KRONOS (Phase 4)

KRONOS lira les rapports de VOX pour son audit de coherence.
VOX ecrira les resultats d'audit de KRONOS dans les TRACKING_UXX.md correspondants.
