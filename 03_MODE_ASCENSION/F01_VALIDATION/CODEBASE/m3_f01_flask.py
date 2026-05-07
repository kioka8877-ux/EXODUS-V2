"""
M3_F01 — VALIDATION : Serveur Flask
Endpoints : /, /files/avatar, /files/audio, /info, /save-report
"""
import os, json
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# ─── CONFIG DRIVE ─────────────────────────────────────────────────
DRIVE_ROOT  = Path("/content/drive/MyDrive/EXODUS_V3/M3")
AVATAR_PATH = DRIVE_ROOT / "SHARED" / "avatar.glb"
AUDIO_PATH  = DRIVE_ROOT / "SHARED" / "audio.mp3"
OUT_DIR     = DRIVE_ROOT / "F01_VALIDATION" / "OUT_REPORT"
REPORT_PATH = OUT_DIR / "m3_f01_report.json"
HTML_PATH   = Path(__file__).parent / "m3_f01_viewer.html"

app = Flask(__name__)
CORS(app)

# ─── ENDPOINTS ────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_file(str(HTML_PATH))

@app.route("/info")
def info():
    return jsonify({
        "has_avatar": AVATAR_PATH.exists(),
        "has_audio":  AUDIO_PATH.exists(),
        "avatar_size": AVATAR_PATH.stat().st_size if AVATAR_PATH.exists() else 0,
        "audio_size":  AUDIO_PATH.stat().st_size  if AUDIO_PATH.exists()  else 0,
    })

@app.route("/files/avatar")
def serve_avatar():
    if not AVATAR_PATH.exists():
        return Response("avatar.glb introuvable", status=404)
    return send_file(str(AVATAR_PATH), mimetype="model/gltf-binary")

@app.route("/files/audio")
def serve_audio():
    if not AUDIO_PATH.exists():
        return Response("audio.mp3 introuvable", status=404)
    return send_file(str(AUDIO_PATH), mimetype="audio/mpeg")

@app.route("/save-report", methods=["POST"])
def save_report():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Payload vide"}), 400
    required = {"status", "has_audio", "anim_duration", "selected_clip"}
    missing = required - set(data.keys())
    if missing:
        return jsonify({"error": f"Champs manquants : {missing}"}), 400
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True, "path": str(REPORT_PATH)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
