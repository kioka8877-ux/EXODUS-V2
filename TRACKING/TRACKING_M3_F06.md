# TRACKING F06 — CARRIER
## "Le Transporteur de Croisière"

**Statut** : ✅ FORGE
**Priorité** : P0 (premier à forger — valide le pipeline encode)
**Dépendances entrantes** : OUT_FRAMES/*.png (F05) + audio.mp3 (Drive)
**Dépendances sortantes** : FINAL_OUTPUT.mp4

## MISSION
Interpoler 24fps → 60fps via RIFE, encoder H.264 via ffmpeg,
muxer l'audio, appliquer overlay texte → MP4 final 1080x1920.

## INPUTS / OUTPUTS
```
IN  : Drive/OUT_FRAMES/frame_*.png (F05)
      Drive/audio.mp3 (si has_audio: true)
      Drive/F01/m3_f01_report.json (has_audio, audio_duration)
OUT : Drive/FINAL/FINAL_OUTPUT.mp4
      Nettoyage auto : OUT_FRAMES/ et RIFE_FRAMES/ supprimés après succès
```

## STACK TECHNIQUE
- Python 95% : RIFE PyTorch + ffmpeg subprocess
- HTML 5% : monitoring vanilla JS (zero Three.js, zero WebGL)
- hzwer/ECCV2022-RIFE (pip install ou clone)
- ffmpeg préinstallé Colab

## TACHES DE FORGE

### SESSION 1 — Flask + endpoints (25 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F06-S1-T1 | Créer m3_f06.ipynb : Flask + montage Drive | ✅ DONE |
| F06-S1-T2 | GET / → monitor HTML | ✅ DONE |
| F06-S1-T3 | GET /info → retourner {frame_count, has_audio, audio_duration} | ✅ DONE |
| F06-S1-T4 | GET /files/thumbnail → première frame PNG (preview) | ✅ DONE |
| F06-S1-T5 | POST /encode → lancer pipeline encode en thread background | ✅ DONE |
| F06-S1-T6 | GET /status → {stage: 1-4, pct: 0-100, eta_s, message} | ✅ DONE |
| F06-S1-T7 | GET /download → servir FINAL_OUTPUT.mp4 (Content-Disposition) | ✅ DONE |

### SESSION 2 — HTML monitor (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F06-S2-T1 | Structure HTML : topbar + main container + palette Impériale | ✅ DONE |
| F06-S2-T2 | Topbar : infos auto-chargées (N frames, durée, has_audio) | ✅ DONE |
| F06-S2-T3 | Section : toggle AVEC/SANS TEXTE + config overlay (texte, couleur, position, taille) | ✅ DONE |
| F06-S2-T4 | Preview miniature thumbnail + simulation CSS overlay texte | ✅ DONE |
| F06-S2-T5 | Section : choix fps final (24 / 30 / 60 fps) | ✅ DONE |
| F06-S2-T6 | 4 barres de progression (RIFE / ffmpeg / Audio mux / Overlay) | ✅ DONE |
| F06-S2-T7 | Bouton [ENCODER] gold + bouton [TELECHARGER MP4] (actif si DONE) | ✅ DONE |
| F06-S2-T8 | setInterval fetch('/status') toutes 2s → mise à jour barres | ✅ DONE |

### SESSION 3 — Pipeline RIFE (45 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F06-S3-T1 | pip install RIFE (hzwer/ECCV2022-RIFE ou via requirements Colab) | ✅ DONE |
| F06-S3-T2 | Charger modèle RIFE_HDv3 depuis Drive ou download auto | ✅ DONE |
| F06-S3-T3 | Fonction interpolate(IN_FRAMES, RIFE_FRAMES, target_fps) | ✅ DONE |
| F06-S3-T4 | Boucle avec mise à jour statut stage 1 + pct | ✅ DONE |
| F06-S3-T5 | Si fps == 24 ou 30 : bypass RIFE, copier frames directement | ✅ DONE |

### SESSION 4 — Pipeline ffmpeg (30 min)
| ID | Tâche | Statut |
|----|-------|--------|
| F06-S4-T1 | ETAPE 2 : ffmpeg encode H.264 depuis RIFE_FRAMES → temp_novid.mp4 | ✅ DONE |
| F06-S4-T2 | ETAPE 3 : ffmpeg mux audio si has_audio → temp_audio.mp4 | ✅ DONE |
| F06-S4-T3 | ETAPE 4 : ffmpeg drawtext overlay si text_enabled → FINAL_OUTPUT.mp4 | ✅ DONE |
| F06-S4-T4 | Mise à jour statut stage 2/3/4 + pct à chaque étape | ✅ DONE |
| F06-S4-T5 | Nettoyage auto : supprimer OUT_FRAMES/ + RIFE_FRAMES/ après succès | ✅ DONE |

## COMMANDES FFMPEG DEFINITIVES
```bash
# ETAPE 2 — Encode H.264
ffmpeg -r {fps} -i RIFE_FRAMES/frame_%04d.png \
       -vcodec libx264 -pix_fmt yuv420p -crf 18 -preset fast \
       -y temp_novid.mp4

# ETAPE 3 — Mux audio (si has_audio)
ffmpeg -i temp_novid.mp4 -i audio.mp3 \
       -c:v copy -c:a aac -shortest -y temp_audio.mp4

# ETAPE 4 — Overlay texte (si text_enabled)
ffmpeg -i temp_audio.mp4 \
       -vf "drawtext=text='{TEXT}':fontcolor={COLOR}:fontsize={SIZE}:
            x=(w-text_w)/2:y=h-80:shadowcolor=black:shadowx=2:shadowy=2" \
       -y FINAL_OUTPUT.mp4
```

## VALIDATION SCEAU
- [x] RIFE produit ~912 frames depuis 365 (24→60fps)
- [x] ffmpeg encode sans erreur H.264 1080x1920
- [x] Audio synchronisé sur première frame (pas de décalage)
- [x] Overlay texte visible aux bonnes coordonnées
- [x] FINAL_OUTPUT.mp4 jouable (VLC / navigateur)
- [x] OUT_FRAMES/ supprimé après succès
- [x] Bouton TELECHARGER actif après DONE

## FICHIERS FORGES
| Fichier | Description |
|---------|-------------|
| `m3_f06_monitor.html` | HTML complet — topbar, config overlay texte, preview thumbnail CSS, choix fps 24/30/60, 4 barres de progression, boutons Encoder/Telecharger, polling live |
| `m3_f06_flask.py` | Flask 7 endpoints : `/info`, `/encode`, `/status`, `/cancel`, `/download`, `/files/thumbnail`, `/` |
| `m3_f06_pipeline.py` | Pipeline complet : RIFE (install auto + inference loop), ffmpeg H.264, mux audio, overlay drawtext, cleanup auto |
| `m3_f06.ipynb` | 4 cellules Colab : montage Drive + install, verification inputs, lancement Flask, mode headless commenté |
