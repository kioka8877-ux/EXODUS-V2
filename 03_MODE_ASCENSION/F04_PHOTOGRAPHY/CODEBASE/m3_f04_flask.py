"""
M3_F04 — PHOTOGRAPHY : Serveur Flask
Endpoints : /, /files/avatar, /files/decor, /config/spawn, /save-config, /info
"""
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# ─── CONFIG DRIVE ─────────────────────────────────────────────────
DRIVE_ROOT   = Path("/content/drive/MyDrive/EXODUS_V3/M3")
AVATAR_PATH  = DRIVE_ROOT / "SHARED"         / "avatar.glb"
DECOR_PATH   = DRIVE_ROOT / "SHARED"         / "decor.glb"
SPAWN_CFG    = DRIVE_ROOT / "F03_SCENOGRAPHY" / "OUT" / "spawn_config.json"
OUT_DIR      = DRIVE_ROOT / "F04_PHOTOGRAPHY" / "OUT"
CAM_PATH     = OUT_DIR / "camera_config.json"
LIGHT_PATH   = OUT_DIR / "light_config.json"
HTML_PATH    = Path(__file__).parent / "m3_f04_viewer.html"

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_file(str(HTML_PATH))

@app.route("/info")
def info():
    return jsonify({
        "has_avatar":      AVATAR_PATH.exists(),
        "has_decor":       DECOR_PATH.exists(),
        "has_spawn_config": SPAWN_CFG.exists(),
    })

@app.route("/files/avatar")
def serve_avatar():
    if not AVATAR_PATH.exists():
        return Response("avatar.glb introuvable", status=404)
    return send_file(str(AVATAR_PATH), mimetype="model/gltf-binary")

@app.route("/files/decor")
def serve_decor():
    if not DECOR_PATH.exists():
        return Response("decor.glb introuvable", status=404)
    return send_file(str(DECOR_PATH), mimetype="model/gltf-binary")

@app.route("/config/spawn")
def get_spawn():
    if not SPAWN_CFG.exists():
        return jsonify({"error": "spawn_config.json introuvable — lancer F03 d'abord"}), 404
    with open(SPAWN_CFG) as f:
        return jsonify(json.load(f))

@app.route("/save-config", methods=["POST"])
def save_config():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Payload vide"}), 400
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cam   = data.get("camera_config", {})
    light = data.get("light_config",  {})
    with open(CAM_PATH,   "w") as f: json.dump(cam,   f, indent=2, ensure_ascii=False)
    with open(LIGHT_PATH, "w") as f: json.dump(light, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True, "camera": str(CAM_PATH), "light": str(LIGHT_PATH)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False)
