"""
M3_F02 — LOGISTICS : Serveur Flask
Endpoints : /, /files/avatar, /files/props, /files/prop/<name>,
            /save-actor, /save-report, /info
"""
import os, json
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# ─── CONFIG DRIVE ─────────────────────────────────────────────────
DRIVE_ROOT   = Path("/content/drive/MyDrive/EXODUS_V3/M3")
AVATAR_PATH  = DRIVE_ROOT / "SHARED" / "avatar.glb"
PROPS_DIR    = DRIVE_ROOT / "SHARED" / "props"
F01_REPORT   = DRIVE_ROOT / "F01_VALIDATION" / "OUT_REPORT" / "m3_f01_report.json"
OUT_DIR      = DRIVE_ROOT / "F02_LOGISTICS" / "OUT"
ACTOR_PATH   = OUT_DIR / "actor_equipped.glb"
REPORT_PATH  = OUT_DIR / "m3_f02_report.json"
HTML_PATH    = Path(__file__).parent / "m3_f02_viewer.html"

app = Flask(__name__)
CORS(app)

# ─── ENDPOINTS ────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_file(str(HTML_PATH))

@app.route("/info")
def info():
    f01 = {}
    if F01_REPORT.exists():
        with open(F01_REPORT) as f:
            f01 = json.load(f)
    props = []
    if PROPS_DIR.exists():
        props = [p.name for p in sorted(PROPS_DIR.glob("*.glb"))]
    return jsonify({
        "has_avatar":    AVATAR_PATH.exists(),
        "avatar_size":   AVATAR_PATH.stat().st_size if AVATAR_PATH.exists() else 0,
        "props":         props,
        "selected_clip": f01.get("selected_clip", ""),
        "has_audio":     f01.get("has_audio", False),
    })

@app.route("/files/avatar")
def serve_avatar():
    if not AVATAR_PATH.exists():
        return Response("avatar.glb introuvable", status=404)
    return send_file(str(AVATAR_PATH), mimetype="model/gltf-binary")

@app.route("/files/props")
def list_props():
    if not PROPS_DIR.exists():
        return jsonify([])
    props = [{"name": p.name, "size": p.stat().st_size}
             for p in sorted(PROPS_DIR.glob("*.glb"))]
    return jsonify(props)

@app.route("/files/prop/<name>")
def serve_prop(name):
    path = PROPS_DIR / name
    if not path.exists() or not path.suffix == ".glb":
        return Response(f"{name} introuvable", status=404)
    return send_file(str(path), mimetype="model/gltf-binary")

@app.route("/save-actor", methods=["POST"])
def save_actor():
    data = request.get_data()
    if not data:
        return jsonify({"error": "GLB vide"}), 400
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTOR_PATH, "wb") as f:
        f.write(data)
    return jsonify({"ok": True, "path": str(ACTOR_PATH), "size": len(data)})

@app.route("/save-report", methods=["POST"])
def save_report():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Payload vide"}), 400
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True, "path": str(REPORT_PATH)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
