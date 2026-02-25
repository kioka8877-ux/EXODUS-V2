# TRACKING – U06 AIRCRAFT CARRIER (Le Vaisseau-Mère)

## 1. OBJECTIF DE LA MUTATION (V2)
RIFE 4.0 (30→120FPS), ratio lock strict depuis métadonnées U00 (zéro letterbox),
H.265/HEVC CRF 16-18, poids cible ~450MB-1.5GB par 60s.
Le produit fini sort d'ici — dernière frégate de la chaîne.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : `rife_interpolator.py` et `final_encoder.py` existent. Manque : vérification ratio lock depuis PRODUCTION_PLAN.JSON, enforcement CRF 16-18 spécifique.
- **Goulot d'étranglement** : Faible — extensions mineures du code existant
- **Risque VRAM/RAM** : ÉLEVÉ — RIFE sur T4 pour 120FPS (~8-10GB)

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Ajouter lecture ratio depuis PRODUCTION_PLAN.JSON
- [ ] Enforcer zéro letterbox (adaptation dynamique)
- [ ] Forcer CRF 16-18 dans FFmpeg H.265
- [ ] Ajouter check-sum résolution (sortie = entrée U00)
- [ ] Optimiser batch RIFE par segments de 10s

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : À mesurer (cible < 10GB pour RIFE)
- Temps d'exécution moyen : À mesurer (estimation 30-60 min pour 60s vidéo)
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U06
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U06
- [RISKS](./EXODUS_V2_RISKS.md) — R1 (VRAM RIFE), R3 (temps rendu)
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
