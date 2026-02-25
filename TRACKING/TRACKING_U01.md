# TRACKING – U01 ANIMATION ENGINE (Le Souffle)

## 1. OBJECTIF DE LA MUTATION (V2)
Remplacer EMOCA par Emotional Intent Transfer. Gemini text → Python → 52 ARKit Shape Keys.
Injection Micro-Jitter (bruit procédural yeux+bouche) + intégration Rhubarb lip-sync.
Export dual : `.blend` + `.abc` (Alembic cache).

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : Paradigme actuel (EMOCA mathématique) incompatible V2. `facial_extractor.py` (355 lignes) à réécrire. `blender_fusion.py` et `sync_engine.py` impactés.
- **Goulot d'étranglement** : Mapping complet des expressions textuelles vers les 52 ARKit Shape Keys
- **Risque VRAM/RAM** : MOYEN — Blender headless (~2-4GB)

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Supprimer toute dépendance EMOCA
- [ ] Créer le dictionnaire emotion→shape keys (52 ARKit)
- [ ] Implémenter courbes de Bézier pour transitions
- [ ] Ajouter passage par "neutre" entre émotions opposées
- [ ] Implémenter Micro-Jitter (bruit procédural yeux+bouche)
- [ ] Intégrer Rhubarb lip-sync
- [ ] Gérer conflit lip-sync/expressions (priorité Rhubarb pour bouche)
- [ ] Export dual .blend + .abc

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer (cible < 4GB)
- Temps d'exécution moyen : À mesurer
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U01
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U01
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM Blender)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
