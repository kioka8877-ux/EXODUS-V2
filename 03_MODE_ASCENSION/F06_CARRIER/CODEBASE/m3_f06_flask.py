"""
M3_F06 — CARRIER : Serveur Flask
Endpoints : info, encode, status, cancel, download, thumbnail
"""
import os, json, threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# ─── CONFIG DRIVE ─────────────────────────────────────────────────
DRIVE_ROOT   = Path("/content/drive/MyDrive/EXODUS_V3/M3")
IN_FRAMES    = DRIVE_ROOT / "F05_ALCHEMIST" / "OUT_FRAMES"
AUDIO_PATH   = DRIVE_ROOT / "SHARED" / "audio.mp3"
F01_REPORT   = DRIVE_ROOT / "F01_VALIDATION" / "OUT_REPORT" / "m3_f01_report.json"
OUT_DIR      = DRIVE_ROOT / "F06_CARRIER" / "OUT"
RIFE_OUT     = DRIVE_ROOT / "F06_CARRIER" / "RIFE_FRAMES"
HTML_PATH    = Path(__file__).parent / "m3_f06_monitor.html"
SOURCE_FPS   = 24  # frames capturées par F05

# ─── ÉTAT GLOBAL ──────────────────────────────────────────────────
encode_state = {
    "running":     False,
    "done":        False,
    "error":       None,
    "stage":       0,       # 1=RIFE 2=ffmpeg 3=audio 4=overlay
    "stage_pct":   0.0,
    "total_pct":   0.0,
    "frames_done": 0,
    "eta_s":       None,
    "message":     ""
}
cancel_flag = threading.Event()

app = Flask(__name__)
CORS(app)

# ─── ENDPOINTS ────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_file(str(HTML_PATH))

@app.route("/info")
def info():
    frames = sorted(IN_FRAMES.glob("frame_*.png")) if IN_FRAMES.exists() else []
    has_audio = AUDIO_PATH.exists()
    audio_dur = 0.0
    f01_data = {}
    if F01_REPORT.exists():
        with open(F01_REPORT) as f:
            f01_data = json.load(f)
        audio_dur = f01_data.get("audio_duration", 0.0)
    return jsonify({
        "frame_count": len(frames),
        "has_audio": has_audio,
        "audio_duration": audio_dur,
        "source_fps": SOURCE_FPS
    })

@app.route("/files/thumbnail")
def thumbnail():
    frames = sorted(IN_FRAMES.glob("frame_*.png")) if IN_FRAMES.exists() else []
    if not frames:
        return Response("No frames", status=404)
    return send_file(str(frames[0]), mimetype="image/png")

@app.route("/encode", methods=["POST"])
def encode():
    global encode_state, cancel_flag
    if encode_state["running"]:
        return jsonify({"error": "Encodage déjà en cours"}), 400
    config = request.get_json(force=True)
    encode_state = {
        "running": True, "done": False, "error": None,
        "stage": 0, "stage_pct": 0.0, "total_pct": 0.0,
        "frames_done": 0, "eta_s": None, "message": "Démarrage..."
    }
    cancel_flag.clear()
    t = threading.Thread(target=_run_pipeline, args=(config,), daemon=True)
    t.start()
    return jsonify({"ok": True})

@app.route("/status")
def status():
    return jsonify(encode_state)

@app.route("/cancel", methods=["POST"])
def cancel():
    cancel_flag.set()
    encode_state["running"] = False
    encode_state["message"] = "Annulé"
    return jsonify({"ok": True})

@app.route("/download")
def download():
    mp4 = OUT_DIR / "FINAL_OUTPUT.mp4"
    if not mp4.exists():
        return Response("MP4 non trouvé", status=404)
    return send_file(str(mp4), as_attachment=True,
                     download_name="FINAL_OUTPUT.mp4", mimetype="video/mp4")

# ─── PIPELINE (thread background) ─────────────────────────────────
def _update(stage, pct, msg="", frames_done=None):
    encode_state["stage"]     = stage
    encode_state["stage_pct"] = pct
    # total = stage complete * (1/4) + current stage progress * (1/4)
    encode_state["total_pct"] = ((stage - 1) * 25.0) + (pct * 0.25)
    encode_state["message"]   = msg
    if frames_done is not None:
        encode_state["frames_done"] = frames_done

def _run_pipeline(config):
    from m3_f06_pipeline import run_rife, run_ffmpeg_encode, run_audio_mux, run_overlay, cleanup
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RIFE_OUT.mkdir(parents=True, exist_ok=True)
    frames = sorted(IN_FRAMES.glob("frame_*.png"))
    fps_target  = config.get("fps_target", 60)
    text_en     = config.get("text_enabled", False)
    has_audio   = AUDIO_PATH.exists()

    try:
        # ── ETAPE 1 : RIFE ────────────────────────────────────────
        if cancel_flag.is_set(): return _abort()
        _update(1, 0, "Initialisation RIFE...")
        if fps_target in (24, 30):
            # bypass RIFE — copie directe (24fps) ou sous-échantillonnage (30fps)
            import shutil
            # Pour 30fps depuis 24fps : on copie toutes les frames et ffmpeg gère le timing
            for i, f in enumerate(frames):
                if cancel_flag.is_set(): return _abort()
                shutil.copy(f, RIFE_OUT / f.name)
                pct = (i + 1) / max(len(frames), 1) * 100
                _update(1, pct, f"Copie frame {i+1}/{len(frames)}", i + 1)
        else:
            run_rife(IN_FRAMES, RIFE_OUT, fps_target, SOURCE_FPS,
                     progress_cb=lambda p, msg: _update(1, p, msg, int(p/100*len(frames))),
                     cancel_flag=cancel_flag)
        _update(1, 100, "RIFE terminé")

        # ── ETAPE 2 : ffmpeg encode ───────────────────────────────
        if cancel_flag.is_set(): return _abort()
        _update(2, 0, "Encodage H.264...")
        tmp_novid = OUT_DIR / "tmp_novid.mp4"
        run_ffmpeg_encode(RIFE_OUT, tmp_novid, fps_target,
                          progress_cb=lambda p, msg: _update(2, p, msg),
                          cancel_flag=cancel_flag)
        _update(2, 100, "H.264 encodé")

        # ── ETAPE 3 : audio mux ───────────────────────────────────
        if cancel_flag.is_set(): return _abort()
        _update(3, 0, "Mixage audio...")
        tmp_audio = OUT_DIR / "tmp_audio.mp4"
        if has_audio:
            run_audio_mux(tmp_novid, AUDIO_PATH, tmp_audio,
                          progress_cb=lambda p, msg: _update(3, p, msg),
                          cancel_flag=cancel_flag)
            _update(3, 100, "Audio mixé")
        else:
            import shutil; shutil.copy(tmp_novid, tmp_audio)
            _update(3, 100, "Pas d'audio — étape ignorée")

        # ── ETAPE 4 : overlay texte ───────────────────────────────
        if cancel_flag.is_set(): return _abort()
        _update(4, 0, "Overlay texte...")
        final = OUT_DIR / "FINAL_OUTPUT.mp4"
        if text_en and config.get("text"):
            run_overlay(tmp_audio, final, config,
                        progress_cb=lambda p, msg: _update(4, p, msg),
                        cancel_flag=cancel_flag)
            _update(4, 100, "Overlay appliqué")
        else:
            import shutil; shutil.copy(tmp_audio, final)
            _update(4, 100, "Pas de texte — étape ignorée")

        # ── NETTOYAGE ─────────────────────────────────────────────
        cleanup(IN_FRAMES, RIFE_OUT, [tmp_novid, tmp_audio])

        encode_state["running"]   = False
        encode_state["done"]      = True
        encode_state["total_pct"] = 100.0
        encode_state["message"]   = "Encodage terminé"

    except Exception as e:
        encode_state["running"] = False
        encode_state["error"]   = str(e)
        encode_state["message"] = f"Erreur: {e}"

def _abort():
    encode_state["running"] = False
    encode_state["message"] = "Annulé"

# ─── LANCEMENT ────────────────────────────────────────────────────
def start_server(port=8080):
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
