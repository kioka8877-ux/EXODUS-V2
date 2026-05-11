"""
M3_F05 — ALCHEMIST : Serveur Flask
Endpoints : /, /info, /files/avatar, /files/decor,
            /config/spawn, /config/camera, /config/light,
            /render, /status, /cancel
"""
import json
import threading
import time
from pathlib import Path

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# ─── CONFIG DRIVE ─────────────────────────────────────────────────
DRIVE_ROOT  = Path("/content/drive/MyDrive/EXODUS_V3/M3")
AVATAR_PATH = DRIVE_ROOT / "SHARED"           / "avatar.glb"
DECOR_PATH  = DRIVE_ROOT / "SHARED"           / "decor.glb"
SPAWN_CFG   = DRIVE_ROOT / "F03_SCENOGRAPHY"  / "OUT" / "spawn_config.json"
CAM_CFG     = DRIVE_ROOT / "F04_PHOTOGRAPHY"  / "OUT" / "camera_config.json"
LIGHT_CFG   = DRIVE_ROOT / "F04_PHOTOGRAPHY"  / "OUT" / "light_config.json"
OUT_FRAMES  = DRIVE_ROOT / "F05_ALCHEMIST"    / "OUT_FRAMES"
CHECKPOINT  = DRIVE_ROOT / "F05_ALCHEMIST"    / "OUT" / "m3_f05_checkpoint.json"
HTML_PATH   = Path(__file__).parent / "m3_f05_viewer.html"

app = Flask(__name__)
CORS(app)

# ─── ÉTAT RENDER ──────────────────────────────────────────────────
_render_state = {
    "running":       False,
    "frame_current": 0,
    "total_frames":  0,
    "pct":           0.0,
    "eta_s":         0,
    "status":        "IDLE",   # IDLE | RUNNING | DONE | CANCELLED | ERROR
    "error":         None,
}
_render_thread = None
_cancel_flag   = threading.Event()


def _playwright_render(fps: int, total_frames: int, port: int) -> None:
    """Thread de capture Playwright — GPU EGL headless."""
    _cancel_flag.clear()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _render_state["status"] = "ERROR"
        _render_state["error"]  = "playwright non installé — lancer : !pip install playwright && playwright install chromium"
        _render_state["running"] = False
        return

    OUT_FRAMES.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)

    # Reprise depuis checkpoint éventuel
    start_frame = 1
    if CHECKPOINT.exists():
        try:
            with open(CHECKPOINT) as f:
                ck = json.load(f)
            start_frame = ck.get("last_frame", 0) + 1
            _render_state["frame_current"] = start_frame - 1
        except Exception:
            pass

    started_at = time.time()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=[
            "--use-gl=egl",
            "--enable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1080,1920",
        ])
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        try:
            url = f"http://localhost:{port}/?render=1&fps={fps}&total={total_frames}"
            page.goto(url, timeout=30_000)
            page.wait_for_selector("#scene-ready", timeout=300_000)

            for frame_n in range(start_frame, total_frames + 1):
                if _cancel_flag.is_set():
                    _render_state["status"] = "CANCELLED"
                    break

                # Réinitialiser le signal avant d'appeler setRenderFrame
                page.evaluate("document.getElementById('frame-done').dataset.ready = '0'")
                page.evaluate(f"window.setRenderFrame({frame_n})")
                page.wait_for_function(
                    "document.getElementById('frame-done').dataset.ready === '1'",
                    timeout=15_000,
                )

                fname = f"frame_{frame_n:04d}.png"
                page.screenshot(path=str(OUT_FRAMES / fname), full_page=False)

                # Mise à jour état
                elapsed = time.time() - started_at
                speed   = frame_n / elapsed if elapsed > 0 else 1
                _render_state["frame_current"] = frame_n
                _render_state["pct"]           = round(frame_n / total_frames * 100, 1)
                _render_state["eta_s"]         = int((total_frames - frame_n) / speed)

                # Checkpoint
                with open(CHECKPOINT, "w") as f:
                    json.dump({"last_frame": frame_n, "total_frames": total_frames, "fps": fps}, f)

            if not _cancel_flag.is_set():
                _render_state["status"] = "DONE"

        except Exception as exc:
            _render_state["status"] = "ERROR"
            _render_state["error"]  = str(exc)
        finally:
            browser.close()

    _render_state["running"] = False


# ─── ROUTES ───────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(str(HTML_PATH))


@app.route("/info")
def info():
    return jsonify({
        "has_avatar":        AVATAR_PATH.exists(),
        "has_decor":         DECOR_PATH.exists(),
        "has_spawn_config":  SPAWN_CFG.exists(),
        "has_camera_config": CAM_CFG.exists(),
        "has_light_config":  LIGHT_CFG.exists(),
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


@app.route("/config/camera")
def get_camera():
    if not CAM_CFG.exists():
        return jsonify({"error": "camera_config.json introuvable — lancer F04 d'abord"}), 404
    with open(CAM_CFG) as f:
        return jsonify(json.load(f))


@app.route("/config/light")
def get_light():
    if not LIGHT_CFG.exists():
        return jsonify({"error": "light_config.json introuvable — lancer F04 d'abord"}), 404
    with open(LIGHT_CFG) as f:
        return jsonify(json.load(f))


@app.route("/render", methods=["POST"])
def start_render():
    global _render_thread
    if _render_state["running"]:
        return jsonify({"error": "Render déjà en cours"}), 400

    data         = request.get_json(force=True) or {}
    fps          = int(data.get("fps", 24))
    total_frames = int(data.get("total_frames", 240))
    port         = int(data.get("port", 5005))

    _render_state.update({
        "running":       True,
        "frame_current": 0,
        "total_frames":  total_frames,
        "pct":           0.0,
        "eta_s":         0,
        "status":        "RUNNING",
        "error":         None,
    })

    _render_thread = threading.Thread(
        target=_playwright_render,
        args=(fps, total_frames, port),
        daemon=True,
    )
    _render_thread.start()
    return jsonify({"ok": True, "fps": fps, "total_frames": total_frames})


@app.route("/status")
def get_status():
    return jsonify(_render_state)


@app.route("/cancel", methods=["POST"])
def cancel_render():
    _cancel_flag.set()
    _render_state["status"]  = "CANCELLED"
    _render_state["running"] = False
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False, threaded=True)
