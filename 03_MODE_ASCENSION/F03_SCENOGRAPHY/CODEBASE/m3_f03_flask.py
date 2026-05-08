"""
M3_F03 — SCENOGRAPHY : Serveur Flask
Endpoints : /, /files/decor, /files/avatar, /save-config, /info
"""
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# ─── CONFIG PATHS ─────────────────────────────────────────────────
DRIVE_ROOT   = Path("/content/drive/MyDrive/EXODUS_V3/M3")
DECOR_PATH   = DRIVE_ROOT / "SHARED" / "decor.glb"
AVATAR_PATH  = DRIVE_ROOT / "SHARED" / "avatar.glb"
OUT_DIR      = DRIVE_ROOT / "F03_SCENOGRAPHY" / "OUT"
CONFIG_PATH  = OUT_DIR / "spawn_config.json"
HTML_PATH    = Path(__file__).parent / "m3_f03_viewer.html"

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_file(str(HTML_PATH))

@app.route("/info")
def info():
    return jsonify({
        "has_decor":   DECOR_PATH.exists(),
        "has_avatar":  AVATAR_PATH.exists(),
        "decor_size":  DECOR_PATH.stat().st_size  if DECOR_PATH.exists()  else 0,
        "avatar_size": AVATAR_PATH.stat().st_size if AVATAR_PATH.exists() else 0,
    })

@app.route("/files/decor")
def serve_decor():
    if not DECOR_PATH.exists():
        return Response(f"decor.glb introuvable ({DECOR_PATH})", status=404)
    return send_file(str(DECOR_PATH), mimetype="model/gltf-binary")

@app.route("/files/avatar")
def serve_avatar():
    if not AVATAR_PATH.exists():
        return Response(f"avatar.glb introuvable ({AVATAR_PATH})", status=404)
    return send_file(str(AVATAR_PATH), mimetype="model/gltf-binary")

@app.route("/save-config", methods=["POST"])
def save_config():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Payload vide"}), 400
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True, "path": str(CONFIG_PATH)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
