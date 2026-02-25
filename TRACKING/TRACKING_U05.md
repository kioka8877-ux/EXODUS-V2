# TRACKING – U05 ALCHEMIST LAB (Le Philtre)

## 1. OBJECTIF DE LA MUTATION (V2)
Fusion visuelle totale — Match Color (alignement histogramme), Film Grain matching (extraction grain source),
Bloom/Glow bleed, Sharpness transfer. L'avatar doit être indistinguable de la vidéo source.
Moteur : OpenCV + Pillow.

## 2. ÉTAT J0 (DIAGNOSTIC DES ÉCARTS)
- **Écarts constatés** : `color_grader.py` utilise des LUTs au lieu du Match Color par histogramme. Pas de grain matching (extraction du grain source). `effects_forge.py` manque bloom/glow spécifique.
- **Goulot d'étranglement** : Match Color par histogramme (OpenCV) — algorithme plus complexe que LUT
- **Risque VRAM/RAM** : FAIBLE — traitement CPU (OpenCV+Pillow)

## 3. PLAN D'ACTION (BACKLOG)
- [ ] Remplacer LUT grading par Match Color histogramme (OpenCV)
- [ ] Implémenter extraction et application du grain source
- [ ] Ajouter Bloom/Glow bleed (hautes lumières)
- [ ] Implémenter flou de transfert (netteté avatar → grain source)
- [ ] Output en .png 16 bits

## 4. REGISTRE DE FORGE (LOGS)
| Date | Action | Statut | Commit/Lien | VRAM/Temps |
|------|--------|--------|-------------|------------|
| - | - | 🔴 | - | - |

## 5. MÉTRIQUES ET VALIDATION
- Consommation VRAM Max : N/A (CPU processing)
- Temps d'exécution moyen : À mesurer
- [ ] Marshal Out-Check passé
- [ ] Validation Souveraine

## RÉFÉRENCES
- [PRD](./EXODUS_V2_PRD.md) — Spécifications U05
- [VALIDATION](./EXODUS_V2_VALIDATION.md) — Critères binaires U05
- [MASTER](./TRACKING_MASTER.md) — Vue d'ensemble

> **Loi du Béton** : Chaque entrée dans le Registre de Forge doit pointer vers un commit ou un fichier.
