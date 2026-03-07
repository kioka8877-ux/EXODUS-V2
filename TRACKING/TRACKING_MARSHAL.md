# TRACKING – MARSHAL (L'Intendant)

## 1. OBJECTIF DE LA MUTATION (V2)
Créer le module EXO_MARSHAL.py — Ghost script de validation logistique.
3 fonctions : Out-Check (vérifier fichiers OUT/), In-Check (valider fichiers IN/), Campaign Log (horodatage).
CLI : `python EXO_MARSHAL.py --unit F04 --mode validate`

## 2. ÉTAT POST-FORGE (ÉCARTS RÉSOLUS)
- **Écarts résolus** : ✅ Module complet — `EXO_MARSHAL.py` (578 lignes), `README_MARSHAL.md` (138 lignes)
- **Localisation** : `/EXODUS-V2/EXO_MARSHAL.py` (racine du repo)
- **CLI** : `python EXO_MARSHAL.py --unit U00 --mode check-out`
- **PR** : #12 (mergée 2026-02-26)
- **Test** : U00 check-out confirmé ❌ 0/7 (attendu — U00 non muté V2)

## 3. PLAN D'ACTION (BACKLOG)
- [x] Définir le manifeste de fichiers attendus par unité (IN/OUT)
- [x] Créer EXO_MARSHAL.py avec CLI (--unit, --mode)
- [x] Implémenter Out-Check (vérification présence+format fichiers OUT/)
- [x] Implémenter In-Check (validation présence+format fichiers IN/)
- [x] Implémenter Campaign Log (append horodaté dans EXODUS_CAMPAIGN.LOG)
- [x] Copier MARSHAL dans chaque CODEBASE/ lors de l'init

### D.1 — Phantom Link (EN ATTENTE DEV)
- [x] Architecture Phantom Link documentée (ARCHITECTURE_PHANTOM_LINK.md)
- [ ] Implémenter phantom_link.py (resolve_input + create_link + validate_link)
- [ ] Ajouter --mode link (crée _LINK.json via TRANSFER_ROUTES)
- [ ] Ajouter --mode cleanup (supprime OUT/ intermédiaires après production)
- [ ] Mettre à jour check-in pour résoudre les phantom links

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| 2026-02-26 | Création EXO_MARSHAL.py + README | 🟢 | PR #12 | N/A |
| 2026-02-26 | Test check-out U00 (0/7 — attendu) | 🟢 | EXODUS_CAMPAIGN.LOG | < 1s |
| 2026-03-07 | Phase D.1 Architecture Phantom Link | 🟡 | ARCHITECTURE_PHANTOM_LINK.md | N/A |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (pure Python CPU)
- Temps d'exécution moyen : < 1s
- [x] Marshal Out-Check passé
- [x] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications MARSHAL
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires MARSHAL
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
