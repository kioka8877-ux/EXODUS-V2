"""
M3_F06 — CARRIER : Pipeline RIFE + ffmpeg
Fonctions : run_rife, run_ffmpeg_encode, run_audio_mux, run_overlay, cleanup
"""
import os, json, subprocess, shutil, time
from pathlib import Path


# ──────────────────────────────────────────────────────────────────
# CHECKPOINT RIFE — reprise après interruption
# ──────────────────────────────────────────────────────────────────
def save_rife_checkpoint(checkpoint_path: Path, last_pair: int, out_idx: int):
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w") as f:
        json.dump({"last_pair": last_pair, "out_idx": out_idx}, f)


def load_rife_checkpoint(checkpoint_path: Path):
    """Retourne (last_pair, out_idx) ou (0, 0) si absent/corrompu."""
    if not checkpoint_path or not checkpoint_path.exists():
        return 0, 0
    try:
        with open(checkpoint_path) as f:
            ck = json.load(f)
        return int(ck.get("last_pair", 0)), int(ck.get("out_idx", 0))
    except Exception:
        return 0, 0


# ──────────────────────────────────────────────────────────────────
# ETAPE 1 — RIFE : interpolation 24fps → 60fps (ou 120fps)
# ──────────────────────────────────────────────────────────────────
def run_rife(in_dir: Path, out_dir: Path, fps_target: int, fps_source: int,
             progress_cb=None, cancel_flag=None, checkpoint_path=None):
    """
    Interpole les frames de in_dir vers out_dir avec RIFE.
    fps_target  : 60 (x2.5) ou 120 (x5)
    checkpoint_path : Path vers le JSON de reprise (None = pas de checkpoint)
    """
    try:
        from model.RIFE_HDv3 import Model
        import torch
        import numpy as np
        from PIL import Image
    except ImportError:
        _install_rife()
        from model.RIFE_HDv3 import Model
        import torch
        import numpy as np
        from PIL import Image

    frames = sorted(in_dir.glob("frame_*.png"))
    if not frames:
        raise FileNotFoundError(f"Aucune frame dans {in_dir}")

    n = len(frames)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Reprise depuis checkpoint ─────────────────────────────────
    start_pair, out_idx = load_rife_checkpoint(checkpoint_path)
    if start_pair > 0:
        if progress_cb:
            progress_cb(start_pair / max(n - 1, 1) * 100,
                        f"Reprise depuis paire {start_pair}/{n-1} (frame out {out_idx})")
    else:
        # Nouveau départ — vider le dossier de sortie
        if out_dir.exists():
            shutil.rmtree(str(out_dir), ignore_errors=True)
        out_dir.mkdir(parents=True, exist_ok=True)

    # ── Charger le modèle ─────────────────────────────────────────
    if progress_cb: progress_cb(0, "Chargement modèle RIFE...")
    model = Model()
    model_path = _get_rife_model_path()
    model.load_model(str(model_path), -1)
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.flownet.to(device)

    start = time.time()

    for i in range(start_pair, n - 1):
        if cancel_flag and cancel_flag.is_set():
            return

        img0 = _load_frame(frames[i],     device)
        img1 = _load_frame(frames[i + 1], device)

        # Écrire frame de départ
        _save_frame(img0, out_dir / f"frame_{out_idx:06d}.png")
        out_idx += 1

        # Interpoler frames intermédiaires
        n_mid = _n_intermediates(fps_source, fps_target, i, n)
        for k in range(n_mid):
            t_val = (k + 1) / (n_mid + 1)
            with torch.no_grad():
                mid = model.inference(img0, img1, t_val)
            _save_frame(mid, out_dir / f"frame_{out_idx:06d}.png")
            out_idx += 1

        # Checkpoint après chaque paire
        if checkpoint_path:
            save_rife_checkpoint(checkpoint_path, i + 1, out_idx)

        # Progression
        pct = (i + 1) / (n - 1) * 100
        elapsed = time.time() - start
        eta = int(elapsed / max(i - start_pair + 1, 1) * (n - 1 - i)) if i > start_pair else None
        msg = f"Frame {i+1}/{n-1}" + (f" — ETA {_fmt_eta(eta)}" if eta else "")
        if progress_cb: progress_cb(pct, msg)

    # Écrire la dernière frame
    img_last = _load_frame(frames[-1], device)
    _save_frame(img_last, out_dir / f"frame_{out_idx:06d}.png")

    # Checkpoint final — effacer pour indiquer terminé
    if checkpoint_path and checkpoint_path.exists():
        checkpoint_path.unlink(missing_ok=True)


def _n_intermediates(src_fps, tgt_fps, frame_idx, total):
    """
    Calcule le nombre de frames intermédiaires à insérer entre frame i et i+1.
    Stratégie : distribuer les frames supplémentaires uniformément.
    24→60 : ratio = 2.5, donc on alterne 2 et 3 intermédiaires
    24→120 : ratio = 5, donc 4 intermédiaires systématiques
    """
    ratio = tgt_fps / src_fps
    base  = int(ratio) - 1
    extra = ratio - int(ratio)
    if extra == 0:
        return base
    threshold = frame_idx * extra
    prev      = (frame_idx - 1) * extra if frame_idx > 0 else 0
    return base + (1 if int(threshold) > int(prev) else 0)


def _load_frame(path, device):
    import torch
    import numpy as np
    from PIL import Image
    img = Image.open(str(path)).convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    t   = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(device)
    return t


def _save_frame(tensor, path):
    import numpy as np
    from PIL import Image
    arr = tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
    arr = (arr * 255).clip(0, 255).astype(np.uint8)
    Image.fromarray(arr).save(str(path))


def _get_rife_model_path():
    candidates = [
        Path("/content/drive/MyDrive/EXODUS_V3/MODELS/RIFE/train_log"),
        Path("/content/ECCV2022-RIFE/train_log"),
    ]
    for p in candidates:
        if p.exists(): return p.parent
    _install_rife()
    return Path("/content/ECCV2022-RIFE")


def _install_rife():
    import sys
    rife_dir = Path("/content/ECCV2022-RIFE")
    if not rife_dir.exists():
        subprocess.run(
            ["git", "clone", "https://github.com/hzwer/ECCV2022-RIFE.git",
             str(rife_dir)], check=True)
    if str(rife_dir) not in sys.path:
        sys.path.insert(0, str(rife_dir))


# ──────────────────────────────────────────────────────────────────
# ETAPE 2 — ffmpeg : encode H.264
# ──────────────────────────────────────────────────────────────────
def run_ffmpeg_encode(frames_dir: Path, out_mp4: Path, fps: int,
                      progress_cb=None, cancel_flag=None):
    cmd = [
        "ffmpeg", "-y",
        "-r", str(fps),
        "-i", str(frames_dir / "frame_%06d.png"),
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        str(out_mp4)
    ]
    _run_cmd(cmd, "Encodage H.264", progress_cb, cancel_flag)


# ──────────────────────────────────────────────────────────────────
# ETAPE 3 — ffmpeg : mux audio
# ──────────────────────────────────────────────────────────────────
def run_audio_mux(video: Path, audio: Path, out_mp4: Path,
                  progress_cb=None, cancel_flag=None):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(out_mp4)
    ]
    _run_cmd(cmd, "Mixage audio", progress_cb, cancel_flag)


# ──────────────────────────────────────────────────────────────────
# ETAPE 4 — ffmpeg : overlay texte
# ──────────────────────────────────────────────────────────────────
def run_overlay(video: Path, out_mp4: Path, config: dict,
                progress_cb=None, cancel_flag=None):
    text  = config.get("text", "").replace("'", r"\'")
    color = config.get("text_color", "#ffdf00").lstrip("#")
    size  = config.get("text_size", 48)
    pos   = config.get("text_position", "bottom")

    y_expr = {
        "top":    "60",
        "center": "(h-text_h)/2",
        "bottom": "h-80"
    }.get(pos, "h-80")

    vf = (
        f"drawtext=text='{text}'"
        f":fontcolor=0x{color}"
        f":fontsize={size}"
        f":x=(w-text_w)/2"
        f":y={y_expr}"
        f":shadowcolor=0x000000"
        f":shadowx=2:shadowy=2"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vf", vf,
        "-c:a", "copy",
        str(out_mp4)
    ]
    _run_cmd(cmd, "Overlay texte", progress_cb, cancel_flag)


# ──────────────────────────────────────────────────────────────────
# NETTOYAGE
# ──────────────────────────────────────────────────────────────────
def cleanup(in_frames: Path, rife_frames: Path, tmp_files: list):
    """Supprime OUT_FRAMES et RIFE_FRAMES + fichiers temporaires après succès."""
    for p in [in_frames, rife_frames]:
        if p.exists():
            shutil.rmtree(str(p), ignore_errors=True)
    for f in tmp_files:
        if Path(f).exists():
            Path(f).unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────────────────────────
def _run_cmd(cmd, label, progress_cb, cancel_flag):
    """Lance une commande ffmpeg et reporte la progression (simulée)."""
    if progress_cb: progress_cb(5, f"{label} — démarrage...")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1
    )
    start = time.time()
    for line in proc.stdout:
        if cancel_flag and cancel_flag.is_set():
            proc.kill(); return
        elapsed = time.time() - start
        pct = min(90, elapsed * 3)
        if progress_cb: progress_cb(pct, f"{label}...")
    proc.wait()
    if proc.returncode != 0 and not (cancel_flag and cancel_flag.is_set()):
        raise RuntimeError(f"{label} échoué (code {proc.returncode})")
    if progress_cb: progress_cb(100, f"{label} — terminé")


def _fmt_eta(s):
    if s < 60: return f"{s}s"
    return f"{s//60}min{s%60:02d}s"
