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

### expression_schema.py (Bible Anatomique)
- [ ] Module `expression_schema.py` existe et est importable (Python pur, zéro dépendance Blender)
- [ ] 15 EXPRESSION_PRESETS définis, chacun avec exactement 52 valeurs ARKit (toutes les clés présentes)
- [ ] 9 EYE_PRESETS définis (focused_forward, looking_left, looking_right, looking_up, looking_down, narrowed, wide_open, closed, winking)
- [ ] 8 MOUTH_PRESETS définis (closed_tight, slightly_open, wide_open, smiling, frowning, pursed_lips, shouting, neutral)
- [ ] Matrice des Conflits : bloque les combinaisons anatomiques impossibles (test : mouthSmileLeft + mouthFrownLeft simultanés → rejeté)
- [ ] Table des Oppositions : 5+ paires d'émotions antagonistes définies (joy↔sadness, joy↔anger, anger↔fear, surprise↔bored, love↔disgust)
- [ ] Ranges Anatomiques : toutes les valeurs clampées dans les bornes esthétiques Roblox (test : jawOpen > 0.8 → clampé à 0.8)
- [ ] Courbes d'Intensité : au moins 3 modes de scaling (linear, quadratic, ease-in-out)
- [ ] Micro-Expressions Involontaires : presets blink/tics définis avec amplitude et fréquence
- [ ] Règle de fusion : expression (base) + eyes (override oculaire) + mouth (override buccal) → résultat 52 keys
- [ ] Test "Expression Hérétique" : le module rejette intensity > 1.0, conflits shape keys, et ID expression inconnu

### Pipeline (consommateurs)
- [ ] N'utilise PAS EMOCA (zéro import EMOCA dans tout le CODEBASE/)
- [ ] Lit `facial_animation.json` de U00 (champs : time_start, time_end, expression, eyes, mouth, intensity, apex_time)
- [ ] Utilise F-Curve Bézier natif Blender (zéro code custom de courbes Bézier)
- [ ] Utilise F-Curve Noise Modifier pour Micro-Jitter (pas numpy/scipy custom pour le bruit)
- [ ] Utilise NLA strips pour layering (expression + eyes + mouth comme strips séparés)
- [ ] Passe par état "neutre" entre émotions opposées (via Table des Oppositions du schema)
- [ ] Export dual : .blend + .abc

### Rhubarb (Phase 2)
- [ ] Intègre Rhubarb lip-sync (NLA strip dédié)
- [ ] Désactive shape keys bouche pendant segments de parole (priorité Rhubarb)

## U02 — LOGISTICS DEPOT
- [x] Lit `requires_u02` du PRODUCTION_PLAN.JSON
- [x] Skip complet si `requires_u02 == false`
- [x] Fonctionne normalement si `requires_u02 == true`

## U03 — SCENOGRAPHY DOCK
- [ ] N'utilise PAS McPrep (zéro import McPrep)
- [ ] scene_schema.py définit collections, objets, world settings
- [ ] validate_scene() passé sur chaque environment.blend produit
- [ ] Custom properties présentes (.blend contient exodus_schema_version, exodus_frigate)
- [ ] Couche A : Infinity Dome (demi-sphère UV + texture vidéo source)
- [ ] Couche B : Displacement Mesh (plan 128×128 + Displace modifier + depth maps)
- [ ] Anti-ghosting : depth maps nettoyées via SAM masks avant displacement
- [ ] VRAM cap : max_subdivisions paramétrable (cible < 6GB)
- [ ] Couche C : PBR Swap zones PROCHES uniquement (SAM labels → PBR presets)
- [ ] Shadow Catcher = plan SÉPARÉ (is_shadow_catcher=True, distinct du displacement mesh)
- [ ] Reflectivity Hack : plans Glass BSDF avec Z-offset 0.01m (anti z-fighting)
- [ ] World Sync : Strength du World Shader aligné sur exposition vidéo source

## U04 — PHOTOGRAPHY WING
- [ ] Perspective lock via fSpy ou tracker Blender (mouvement ±5% max)
- [ ] Auto-DOF avec Empty parenté au buste avatar
- [ ] Shake procédural (Noise modifier sur axes de rotation)
- [ ] Volume Scatter + lampes invisibles alignées sur sources vidéo
- [ ] Alerte si avatar sort du frustum caméra

### U04-B — DARKROOM (Rendu Batch)
- [ ] Preset `darkroom` dans camera_schema.py (1080p, 128 samples, OIDN, Combined pass)
- [ ] Script Blender headless rend des frames PNG 16-bit dans OUT_CAMERA_LOGIC/
- [ ] Chunk-based rendering (300 frames/chunk) avec checkpoint JSON pour reprise
- [ ] Checkpoint survit au cleanup (pas dans temp_dir — même pattern que U06)
- [ ] CLI : `python EXO_04_DARKROOM.py --blend scene.blend --chunk-size 300 --resume`
- [ ] Output compatible U05 : scan_render_frames() trouve les PNG dans IN_RAW_FRAMES/
- [ ] GPU auto-detection (CUDA → OPTIX → CPU fallback)
- [ ] Notebook Colab fonctionnel avec mount Drive + auto-resume

## U05 — ALCHEMIST LAB
- [ ] Match Color par alignement histogramme (pas de LUT)
- [ ] Film Grain matching (extraction du grain de la vidéo source)
- [ ] Bloom/Glow bleed (hautes lumières bavent sur le décor)
- [ ] Flou de transfert (avatar pas "trop net" vs grain source)
- [ ] Output : .png 16 bits

## U06 — AIRCRAFT CARRIER

### carrier_schema.py (Bible du Vaisseau-Mère)
- [x] Module `carrier_schema.py` existe et est importable (Python pur, zéro dépendance externe)
- [x] 3 ENCODING_PRESETS définis (distribution, distribution_h265, master) avec tous les paramètres codec
- [x] VALID_RATIOS définis : "9:16", "16:9", "4:3", "1:1"
- [x] CRF_RANGE : [16, 22] avec default approprié par preset
- [x] WEIGHT_TARGETS : dict duration → (min_mb, max_mb) par preset
- [x] validate_ratio(width, height, expected_ratio) : retourne True si zéro letterbox
- [x] validate_crf(value) : retourne True si dans CRF_RANGE
- [x] validate_output_weight(file_bytes, duration_s, preset) : retourne True si dans la cible
- [x] checksum_resolution(output_res, format_res) : retourne True si sortie = entrée U00
- [x] parse_format_metadata(plan_json) : lit format.resolution (array), format.ratio (string), format.fps_source (int)
- [x] self_test() : ≥ 8 tests passent, exécutable standalone

### Pipeline Frame-Based
- [x] ZÉRO compression lossy intermédiaire (grep "libx264" dans les modules → 0 occurrences sauf final_encoder)
- [x] sequence_assembler.py ne produit PAS de vidéo MP4 — retourne un manifeste/index de frames
- [x] rife_interpolator.py lit des frames PNG directement (pas un MP4)
- [x] rife_interpolator.py traite par chunks de 10 secondes (pas toute la vidéo d'un coup)
- [x] upscaler.py lit des frames PNG directement (pas un MP4)
- [x] Pipeline fusionné : chunk → RIFE → upscale → append video final (pas 2 passes séparées)
- [x] Pic disque temporaire < 5GB pour 60s de vidéo

### Encodage Final
- [x] Preset `distribution` : SVT-AV1, poids 200-400MB/60s
- [x] Preset `distribution_h265` : libx265 + `--tune animation`, poids 350-600MB/60s
- [x] Preset `master` : ProRes 422 HQ
- [x] Support fallback : si AV1 indisponible → H.265 automatiquement

### Conformité V2
- [x] Ratio lock strict depuis format.ratio du PRODUCTION_PLAN.JSON V2 (zéro letterbox)
- [x] Résolution lue depuis format.resolution (array [height, width])
- [x] Audio sync depuis audio_source.wav de U00
- [x] Checkpoint system : reprise après crash au dernier chunk
- [x] CLI preset : `--preset distribution|master|custom`
- [x] carrier_report.json généré avec métriques complètes

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

<!-- v2.2 — B1.1 Cathédrale de Chair -->
