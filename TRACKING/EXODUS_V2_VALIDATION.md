# EXODUS V2 — VALIDATION (Le Juge Impérial)
> Critères de succès binaires : ✅ Validé ou ❌ Hérétique

## U00 — CORTEX HQ

### Outputs (7 fichiers obligatoires)
- [ ] Génère `PRODUCTION_PLAN.JSON` conforme au Master JSON V2 (3 blocs : `production_plan`, `facial_animation`, `motion_synthesis`)
- [ ] Génère `motion_synthesis_prompt.txt` (texte anatomique anglais pour SayMotion, non vide)
- [ ] Génère `facial_animation.json` (segments avec `time_start`, `time_end`, `expression`, `eyes`, `mouth`, `intensity`, `apex_time`, `low_visibility`)
- [ ] Génère `DEPTH_MAP/` (séquence .png depth maps via DepthAnything V2, ≥ 50% des frames)
- [ ] Génère `semantic_masks.json` (zones SAM catégorisées : road, grass, wall, sky, water, glass)
- [ ] Génère `camera_fov_ratio.json` (résolution + ratio + focale estimée)
- [ ] Extrait `audio_source.wav` (PCM 16-bit via FFmpeg, taille > 44 bytes)

### Architecture d'exécution
- [ ] Exécution **séquentielle** avec flush GPU obligatoire entre moteurs (CPU → API → GPU-A → GPU-B)
- [ ] VRAM peak < 5 GB sur Colab T4 (jamais 2 modèles GPU simultanés)
- [ ] Protocole flush vérifié : VRAM résiduelle < 0.5 GB entre Phase 3 (Depth) et Phase 4 (SAM)

### Intégrité du Master JSON
- [ ] `response_schema` avec enum verrouillé : Gemini ne peut PAS retourner d'ID hors Arsenal
- [ ] Pattern anti-null : `"none"` dans les enums au lieu de `null` (ex: `"music_id": "none"`)
- [ ] `normalize_timecodes()` : segments faciaux clampés sur bornes scène, apex_time ∈ [time_start, time_end]
- [ ] `validate_structure()` : 0 erreur FATAL (champs requis, timecodes croissants, intensité ∈ [0.0, 1.0])
- [ ] `validate_completeness()` : cohérence croisée entre les 3 blocs (couverture temporelle, requires_u02 ↔ props)
- [ ] `low_visibility` : segments avec visage non visible → expression "neutral", intensity basse

### Résilience
- [ ] `flags.all_motors_ok` présent dans le JSON final
- [ ] Échec Gemini → TOUT s'arrête (exit 1, rien n'est écrit)
- [ ] Échec Depth/SAM/Audio/FOV → JSON écrit, `flags.partial_failure` liste les moteurs en échec
- [ ] Mode `--rerun <motor>` relance un seul moteur sans retoucher le JSON Gemini

### MARSHAL Out-Check
- [ ] Verdict ✅ : tous fichiers présents, intègres, conformes
- [ ] Verdict 🟡 PARTIEL : fichiers principaux OK mais frames corrompues (< 20%) → transfert autorisé avec avertissement
- [ ] Verdict 🔴 BLOQUÉ : fichier principal absent/corrompu OU > 20% depth maps corrompues → transfert interdit

## U01 — ANIMATION ENGINE
- [ ] N'utilise PAS EMOCA (zéro import EMOCA)
- [ ] Lit `facial_animation.json` de U00
- [ ] Mappe les émotions textuelles vers les 52 ARKit Shape Keys
- [ ] Génère des courbes de Bézier (pas d'interpolation linéaire)
- [ ] Passe par état "neutre" entre émotions opposées
- [ ] Injecte Micro-Jitter sur yeux et bouche
- [ ] Intègre Rhubarb lip-sync (désactive shape keys bouche pendant parole)
- [ ] Export dual : .blend + .abc

## U02 — LOGISTICS DEPOT
- [ ] Lit `requires_u02` du PRODUCTION_PLAN.JSON
- [ ] Skip complet si `requires_u02 == false`
- [ ] Fonctionne normalement si `requires_u02 == true`

## U03 — SCENOGRAPHY DOCK
- [ ] N'utilise PAS McPrep (zéro import McPrep)
- [ ] Couche A : Infinity Dome (demi-sphère avec texture vidéo)
- [ ] Couche B : Displacement Mesh (plan subdivisé + Displace modifier + depth maps)
- [ ] Couche C : PBR Swap (masques SAM → matériaux PBR)
- [ ] Shadow Catcher activé sur le sol
- [ ] Reflectivity Hack (plans Glass BSDF sur surfaces vitrées)
- [ ] World Sync (HDRi aligné sur exposition source)

## U04 — PHOTOGRAPHY WING
- [ ] Perspective lock via fSpy ou tracker Blender (mouvement ±5% max)
- [ ] Auto-DOF avec Empty parenté au buste avatar
- [ ] Shake procédural (Noise modifier sur axes de rotation)
- [ ] Volume Scatter + lampes invisibles alignées sur sources vidéo
- [ ] Alerte si avatar sort du frustum caméra

## U05 — ALCHEMIST LAB
- [ ] Match Color par alignement histogramme (pas de LUT)
- [ ] Film Grain matching (extraction du grain de la vidéo source)
- [ ] Bloom/Glow bleed (hautes lumières bavent sur le décor)
- [ ] Flou de transfert (avatar pas "trop net" vs grain source)
- [ ] Output : .png 16 bits

## U06 — AIRCRAFT CARRIER
- [ ] RIFE 4.0 : 30 → 120 FPS
- [ ] Ratio lock strict (9:16 ou 16:9 depuis métadonnées U00, zéro letterbox)
- [ ] Codec H.265/HEVC, CRF 16-18
- [ ] Poids ~450MB-1.5GB pour 60s
- [ ] Audio sync depuis audio_source.wav de U00

## MARSHAL — L'Intendant
- [ ] Commande CLI : `python EXO_MARSHAL.py --unit F04 --mode validate`
- [ ] Out-Check : vérifie fichiers dans OUT/ avant transfert
- [ ] In-Check : valide formats dans IN/ avant lancement
- [ ] Bloque la frégate si fichier manquant/corrompu
- [ ] Écrit dans EXODUS_CAMPAIGN.LOG (horodaté)

---

## PROTOCOLE DE VALIDATION
1. Chaque critère est **binaire** : ✅ ou ❌ — pas de zone grise
2. Une frégate est **conforme V2** uniquement si TOUS ses critères sont ✅
3. La validation est effectuée par l'Empereur après chaque phase du [ROADMAP](./EXODUS_V2_ROADMAP.md)
4. Les résultats sont consignés dans le [TRACKING](./TRACKING_MASTER.md) correspondant

> **Loi du Béton** : Chaque ✅ doit être prouvable par un test reproductible ou un fichier vérifiable.

<!-- v2.1 — Post-Mutation Alignement -->
