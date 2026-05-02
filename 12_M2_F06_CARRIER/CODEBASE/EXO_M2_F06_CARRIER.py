#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         MODE 2 — FRÉGATE M2_F06 — AIRCRAFT CARRIER                          ║
║         Assembly Final + Overlay Binaire → FINAL.mp4                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0 — Phase 8 — Dual Pipeline Doctrine (02.05.2026)            ║
║  Loi R-01 : Copie indépendante Mode 2 — ZERO contamination Mode 1          ║
║  Loi R-04 : Overlay BINAIRE — OUI (audio + texte) ou NON (vidéo brute)    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PIPELINE MODE 2 :                                                          ║
║    1. Assembler séquence PNG → vidéo intermédiaire (ffmpeg)                ║
║    2. RIFE interpolation frames (24→60 ou 24→120 FPS) [optionnel]         ║
║    3. Upscale Real-CUGAN [optionnel]                                        ║
║    4. OVERLAY BINAIRE (LOI R-04) :                                          ║
║       OUI → mixer audio + graver sous-titres/texte overlay                 ║
║       NON → vidéo brute sans traitement                                    ║
║    5. Encode final H.265/AV1/ProRes                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  INPUTS :                                                                   ║
║    IN_FINAL_FRAMES/ ← frames PNG de M2_F05 (ou M2_F04 si bypass F05)      ║
║    IN_AUDIO/        ← audio.wav (optionnel — requis si overlay OUI)        ║
║  OUTPUTS :                                                                  ║
║    OUT_FINAL_MOVIE/ ← FINAL_M2.mp4 (+ .mov ProRes si demandé)             ║
║    OUT_REPORT/      ← m2_f06_report.json                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python EXO_M2_F06_CARRIER.py                          # Menu interactif overlay
    python EXO_M2_F06_CARRIER.py --overlay yes            # Overlay activé
    python EXO_M2_F06_CARRIER.py --overlay no             # Vidéo brute
    python EXO_M2_F06_CARRIER.py --overlay yes --text "Titre de la vidéo"
    python EXO_M2_F06_CARRIER.py --target-fps 60          # RIFE 24→60
    python EXO_M2_F06_CARRIER.py --target-fps 120         # RIFE 24→120
    python EXO_M2_F06_CARRIER.py --no-rife --no-upscale   # Encode direct
    python EXO_M2_F06_CARRIER.py --format prores          # ProRes archivage
    python EXO_M2_F06_CARRIER.py --dry-run
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────
M2_F06_VERSION = "1.0.0"

FREGATE_DIR       = Path(__file__).resolve().parent.parent
IN_FRAMES_DIR     = FREGATE_DIR / "IN_FINAL_FRAMES"
IN_AUDIO_DIR      = FREGATE_DIR / "IN_AUDIO"
OUT_MOVIE_DIR     = FREGATE_DIR / "OUT_FINAL_MOVIE"
OUT_REPORT_DIR    = FREGATE_DIR / "OUT_REPORT"

OUTPUT_FILENAME   = "FINAL_M2.mp4"
OUTPUT_PRORES     = "FINAL_M2_PRORES.mov"
REPORT_FILENAME   = "m2_f06_report.json"
INTERMEDIATE_FILE = "intermediate_m2.mp4"

RIFE_SUBDIR       = "rife"
REALCUGAN_SUBDIR  = "realcugan"

DEFAULT_SOURCE_FPS = 24
DEFAULT_TARGET_FPS = 60
DEFAULT_SCALE      = 2  # Real-CUGAN upscale factor

ENCODING_PRESETS = {
    "h265": {
        "vcodec": "libx265",
        "crf": "18",
        "preset": "slow",
        "ext": "mp4",
        "pix_fmt": "yuv420p",
    },
    "av1": {
        "vcodec": "libsvtav1",
        "crf": "28",
        "preset": "4",
        "ext": "mp4",
        "pix_fmt": "yuv420p",
    },
    "prores": {
        "vcodec": "prores_ks",
        "profile": "3",
        "ext": "mov",
        "pix_fmt": "yuv422p10le",
    },
}

BANNER = """
╔═══════════════════════════════════════════════════════╗
║      MODE 2 — FRÉGATE M2_F06 — AIRCRAFT CARRIER      ║
║      Assembly + Overlay Binaire → FINAL.mp4           ║
╠═══════════════════════════════════════════════════════╣
║  R-04 : Overlay OUI (audio+texte) / NON (brute)       ║
║  R-01 : Isolation stricte Mode 2                       ║
╚═══════════════════════════════════════════════════════╝
"""


# ──────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────
class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def info(self, msg: str):
        print(f"[M2_F06] {msg}")

    def debug(self, msg: str):
        if self.verbose:
            print(f"[M2_F06:DBG] {msg}")

    def ok(self, msg: str):
        print(f"[M2_F06:OK] {msg}")

    def warn(self, msg: str):
        print(f"[M2_F06:WARN] {msg}")
        self.warnings.append(msg)

    def error(self, msg: str):
        print(f"[M2_F06:ERR] {msg}", file=sys.stderr)
        self.errors.append(msg)

    def section(self, title: str):
        bar = "─" * (len(title) + 4)
        print(f"\n┌{bar}┐")
        print(f"│  {title}  │")
        print(f"└{bar}┘")


# ──────────────────────────────────────────────────────────────
# UTILITAIRES
# ──────────────────────────────────────────────────────────────
def check_ffmpeg() -> bool:
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_frame_list(frames_dir: Path) -> List[Path]:
    """Retourne la liste triée des frames PNG/EXR."""
    frames = sorted(
        [f for f in frames_dir.iterdir() if f.suffix.lower() in (".png", ".exr")]
    )
    return frames


def get_frame_pattern(frames: List[Path]) -> Tuple[str, int]:
    """
    Détecte le pattern numérique des frames pour ffmpeg.
    Retourne (pattern, start_number).
    """
    if not frames:
        return ("%04d.png", 0)
    # Détecter le format de numérotation
    name = frames[0].stem
    suffix = frames[0].suffix
    # Extraire les digits
    digits = "".join(c for c in name if c.isdigit())
    prefix = "".join(c for c in name if not c.isdigit())
    pad = len(digits) if digits else 4
    pattern = f"{prefix}%0{pad}d{suffix}"
    start = int(digits) if digits else 0
    return (str(frames[0].parent / pattern), start)


def find_tool(name: str, subdir: str, drive_root: Path) -> Optional[str]:
    """Cherche un binaire dans PATH ou dans le sous-dossier EXODUS."""
    from shutil import which
    path = which(name)
    if path:
        return path
    for candidate in drive_root.rglob(f"**/{subdir}/{name}"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


# ──────────────────────────────────────────────────────────────
# ORCHESTRATEUR
# ──────────────────────────────────────────────────────────────
class M2F06Carrier:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.log = Logger(verbose=args.verbose)
        self.drive_root = FREGATE_DIR.parent
        self.report: Dict = {
            "fregate": "M2_F06_CARRIER",
            "version": M2_F06_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PENDING",
            "overlay_mode": None,
            "steps": {},
            "outputs": {},
            "errors": [],
            "warnings": [],
        }

    # ── Overlay binaire (LOI R-04) ───────────────────────────
    def _ask_overlay(self) -> bool:
        """
        LOI R-04 : choix binaire OUI / NON.
        Si --overlay passé en CLI, utiliser directement.
        Sinon, demander interactivement.
        """
        if self.args.overlay:
            choice = self.args.overlay.lower()
            return choice in ("yes", "oui", "1", "true")

        print("\n" + "═" * 50)
        print("  LOI R-04 — OVERLAY BINAIRE")
        print("═" * 50)
        print("  [O] OUI — Ajouter audio + texte overlay")
        print("  [N] NON — Vidéo brute (aucun traitement)")
        print("═" * 50)
        while True:
            choice = input("  Votre choix (O/N) : ").strip().upper()
            if choice in ("O", "OUI", "Y", "YES", "1"):
                return True
            elif choice in ("N", "NON", "NO", "0"):
                return False
            print("  Répondre O ou N")

    # ── Résolution audio ─────────────────────────────────────
    def _resolve_audio(self) -> Optional[Path]:
        if self.args.audio:
            p = Path(self.args.audio)
            return p if p.is_absolute() else IN_AUDIO_DIR / p
        for ext in [".wav", ".mp3", ".ogg", ".aac", ".flac"]:
            candidates = list(IN_AUDIO_DIR.glob(f"*{ext}"))
            if candidates:
                return candidates[0]
        return None

    # ── ÉTAPE 1 : Assembler frames → vidéo intermédiaire ─────
    def _assemble_frames(self, frames: List[Path]) -> Optional[Path]:
        self.log.section("ÉTAPE 1 — ASSEMBLY FRAMES → MP4")

        if not frames:
            self.log.error(f"Aucune frame PNG/EXR dans {IN_FRAMES_DIR}")
            return None

        self.log.info(f"{len(frames)} frame(s) détectée(s)")
        pattern, start = get_frame_pattern(frames)
        self.log.debug(f"Pattern ffmpeg : {pattern} (start={start})")

        OUT_MOVIE_DIR.mkdir(parents=True, exist_ok=True)
        inter_path = OUT_MOVIE_DIR / INTERMEDIATE_FILE

        fps = self.args.source_fps
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-start_number", str(start),
            "-i", pattern,
            "-c:v", "libx264",
            "-crf", "0",        # Lossless intermédiaire
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            str(inter_path),
        ]

        self.log.debug(f"FFmpeg assembly : {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=not self.args.verbose, text=True, timeout=600)

        if result.returncode != 0:
            if not self.args.verbose and result.stderr:
                print(result.stderr[-500:], file=sys.stderr)
            self.log.error("Échec assembly FFmpeg")
            return None

        self.log.ok(f"Vidéo intermédiaire : {inter_path.name}")
        self.report["steps"]["assembly"] = {"ok": True, "frames": len(frames), "fps": fps}
        return inter_path

    # ── ÉTAPE 2 : RIFE interpolation ─────────────────────────
    def _run_rife(self, input_video: Path) -> Path:
        if self.args.no_rife:
            self.log.info("ÉTAPE 2 — RIFE : SKIPPED (--no-rife)")
            self.report["steps"]["rife"] = {"ok": True, "skipped": True}
            return input_video

        self.log.section("ÉTAPE 2 — RIFE INTERPOLATION")
        target_fps = self.args.target_fps
        rife_bin = find_tool("rife-ncnn-vulkan", RIFE_SUBDIR, self.drive_root)

        if not rife_bin:
            self.log.warn("RIFE non trouvé — étape skippée")
            self.report["steps"]["rife"] = {"ok": True, "skipped": True, "reason": "binary not found"}
            return input_video

        rife_out = OUT_MOVIE_DIR / "rife_out"
        rife_out.mkdir(exist_ok=True)

        # Calcul du multiplicateur
        multiplier = target_fps // self.args.source_fps
        if multiplier < 2:
            multiplier = 2

        cmd = [
            rife_bin,
            "-i", str(input_video),
            "-o", str(rife_out),
            "-m", str(multiplier),
        ]
        self.log.info(f"RIFE {self.args.source_fps}→{target_fps} FPS (x{multiplier})")
        result = subprocess.run(cmd, capture_output=not self.args.verbose, text=True, timeout=600)

        if result.returncode != 0:
            self.log.warn("RIFE a échoué — utilisation vidéo source")
            self.report["steps"]["rife"] = {"ok": False, "fallback": True}
            return input_video

        # Réassembler les frames RIFE
        rife_frames = sorted(rife_out.glob("*.png"))
        if not rife_frames:
            self.log.warn("RIFE : aucune frame produite")
            return input_video

        rife_video = OUT_MOVIE_DIR / "rife_assembled.mp4"
        cmd2 = [
            "ffmpeg", "-y",
            "-framerate", str(target_fps),
            "-i", str(rife_out / "%08d.png"),
            "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(rife_video),
        ]
        subprocess.run(cmd2, capture_output=not self.args.verbose, timeout=600)

        if rife_video.exists():
            self.log.ok(f"RIFE OK : {len(rife_frames)} frames → {target_fps} FPS")
            self.report["steps"]["rife"] = {"ok": True, "target_fps": target_fps, "frames": len(rife_frames)}
            return rife_video
        return input_video

    # ── ÉTAPE 3 : Upscale Real-CUGAN ─────────────────────────
    def _run_upscale(self, input_video: Path) -> Path:
        if self.args.no_upscale:
            self.log.info("ÉTAPE 3 — UPSCALE : SKIPPED (--no-upscale)")
            self.report["steps"]["upscale"] = {"ok": True, "skipped": True}
            return input_video

        self.log.section("ÉTAPE 3 — REAL-CUGAN UPSCALE")
        cugan_bin = find_tool("realcugan-ncnn-vulkan", REALCUGAN_SUBDIR, self.drive_root)

        if not cugan_bin:
            self.log.warn("Real-CUGAN non trouvé — upscale skippé")
            self.report["steps"]["upscale"] = {"ok": True, "skipped": True, "reason": "binary not found"}
            return input_video

        scale = self.args.upscale_factor
        self.log.info(f"Upscale x{scale}")

        # Extraire frames, upscale, réassembler
        frames_dir = OUT_MOVIE_DIR / "cugan_frames_in"
        upscaled_dir = OUT_MOVIE_DIR / "cugan_frames_out"
        frames_dir.mkdir(exist_ok=True)
        upscaled_dir.mkdir(exist_ok=True)

        # Extraire
        subprocess.run([
            "ffmpeg", "-y", "-i", str(input_video),
            str(frames_dir / "%08d.png")
        ], capture_output=not self.args.verbose, timeout=300)

        in_frames = sorted(frames_dir.glob("*.png"))
        if not in_frames:
            self.log.warn("Extraction frames pour CUGAN a échoué")
            return input_video

        # Upscale par batch
        cmd = [cugan_bin, "-i", str(frames_dir), "-o", str(upscaled_dir), "-s", str(scale), "-n", "0"]
        result = subprocess.run(cmd, capture_output=not self.args.verbose, text=True, timeout=600)

        upscaled_frames = sorted(upscaled_dir.glob("*.png"))
        if not upscaled_frames or result.returncode != 0:
            self.log.warn("Real-CUGAN a échoué — utilisation vidéo source")
            self.report["steps"]["upscale"] = {"ok": False, "fallback": True}
            return input_video

        # Réassembler
        fps = self.args.target_fps if not self.args.no_rife else self.args.source_fps
        upscaled_video = OUT_MOVIE_DIR / "upscaled.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(upscaled_dir / "%08d.png"),
            "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", str(upscaled_video),
        ], capture_output=not self.args.verbose, timeout=600)

        if upscaled_video.exists():
            self.log.ok(f"Upscale x{scale} : OK ({len(upscaled_frames)} frames)")
            self.report["steps"]["upscale"] = {"ok": True, "scale": scale}
            return upscaled_video
        return input_video

    # ── ÉTAPE 4 : OVERLAY BINAIRE (LOI R-04) ─────────────────
    def _apply_overlay(self, input_video: Path, audio_path: Optional[Path], overlay_yes: bool) -> Path:
        self.log.section("ÉTAPE 4 — OVERLAY BINAIRE (LOI R-04)")
        self.log.info(f"Mode overlay : {'OUI — Audio + Texte' if overlay_yes else 'NON — Vidéo brute'}")
        self.report["overlay_mode"] = "YES" if overlay_yes else "NO"

        if not overlay_yes:
            self.log.ok("Overlay NON — vidéo brute conservée")
            self.report["steps"]["overlay"] = {"ok": True, "mode": "BRUTE"}
            return input_video

        # Mode OUI : mixage audio + texte overlay
        overlay_out = OUT_MOVIE_DIR / "overlaid.mp4"
        text = self.args.text or ""
        font_size = self.args.font_size

        # Construire la commande ffmpeg
        cmd = ["ffmpeg", "-y", "-i", str(input_video)]
        filter_parts = []

        # Audio
        if audio_path and audio_path.exists():
            cmd += ["-i", str(audio_path)]
            # Shortest : la vidéo détermine la durée (LOI R-03 déjà vérifiée par M2_F01)
            cmd += ["-shortest"]
            self.log.ok(f"Audio : {audio_path.name}")
        else:
            self.log.warn("Overlay OUI mais pas d'audio — vidéo sans son")

        # Texte overlay
        if text:
            # Escape les caractères spéciaux ffmpeg
            escaped_text = text.replace(":", "\\:").replace("'", "\\'")
            drawtext = (
                f"drawtext=text='{escaped_text}':"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"shadowcolor=black:shadowx=2:shadowy=2:"
                f"x=(w-text_w)/2:y=h-th-40"
            )
            filter_parts.append(drawtext)

        if filter_parts:
            cmd += ["-vf", ",".join(filter_parts)]

        # Codec de sortie
        fps = self.args.target_fps if not self.args.no_rife else self.args.source_fps
        cmd += [
            "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
        ]
        if audio_path and audio_path.exists():
            cmd += ["-c:a", "aac", "-b:a", "192k"]

        cmd.append(str(overlay_out))

        result = subprocess.run(cmd, capture_output=not self.args.verbose, text=True, timeout=300)

        if result.returncode == 0 and overlay_out.exists():
            self.log.ok("Overlay OUI appliqué")
            self.report["steps"]["overlay"] = {
                "ok": True, "mode": "YES",
                "audio": str(audio_path) if audio_path else None,
                "text": text,
            }
            return overlay_out
        else:
            if not self.args.verbose and hasattr(result, 'stderr') and result.stderr:
                print(result.stderr[-500:], file=sys.stderr)
            self.log.warn("Overlay a échoué — utilisation vidéo sans overlay")
            self.report["steps"]["overlay"] = {"ok": False, "fallback": "source"}
            return input_video

    # ── ÉTAPE 5 : Encode final ────────────────────────────────
    def _final_encode(self, input_video: Path) -> Optional[Path]:
        self.log.section("ÉTAPE 5 — ENCODE FINAL")

        fmt = self.args.format.lower()
        preset = ENCODING_PRESETS.get(fmt, ENCODING_PRESETS["h265"])
        ext = preset["ext"]

        final_name = f"FINAL_M2.{ext}"
        final_path = OUT_MOVIE_DIR / final_name

        fps = self.args.target_fps if not self.args.no_rife else self.args.source_fps

        cmd = ["ffmpeg", "-y", "-i", str(input_video)]

        if fmt == "prores":
            cmd += [
                "-c:v", "prores_ks",
                "-profile:v", preset.get("profile", "3"),
                "-pix_fmt", preset["pix_fmt"],
                "-r", str(fps),
            ]
        else:
            cmd += [
                "-c:v", preset["vcodec"],
                "-crf", preset.get("crf", "18"),
                "-preset", preset.get("preset", "slow"),
                "-pix_fmt", preset["pix_fmt"],
                "-r", str(fps),
            ]

        cmd.append(str(final_path))

        self.log.info(f"Encoder en {fmt.upper()} → {final_name}")
        result = subprocess.run(cmd, capture_output=not self.args.verbose, text=True, timeout=600)

        if result.returncode != 0:
            if not self.args.verbose and hasattr(result, 'stderr') and result.stderr:
                print(result.stderr[-500:], file=sys.stderr)
            self.log.error(f"Encode final échoué : {fmt}")
            return None

        size_mb = final_path.stat().st_size / (1024 * 1024) if final_path.exists() else 0
        self.log.ok(f"Encode final OK : {final_name} ({size_mb:.1f} MB)")
        self.report["steps"]["encode"] = {"ok": True, "format": fmt, "size_mb": round(size_mb, 2)}
        self.report["outputs"]["final"] = str(final_path)
        return final_path

    # ── Nettoyage intermédiaires ──────────────────────────────
    def _cleanup(self):
        if self.args.keep_intermediates:
            return
        for name in [INTERMEDIATE_FILE, "rife_assembled.mp4", "upscaled.mp4", "overlaid.mp4"]:
            p = OUT_MOVIE_DIR / name
            if p.exists():
                p.unlink()
                self.log.debug(f"Nettoyé : {name}")
        for d in ["rife_out", "cugan_frames_in", "cugan_frames_out"]:
            p = OUT_MOVIE_DIR / d
            if p.exists():
                shutil.rmtree(p)

    # ── Sauvegarde rapport ────────────────────────────────────
    def _save_report(self):
        OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_REPORT_DIR / REPORT_FILENAME
        self.report["warnings"] = self.log.warnings
        self.report["errors"] = self.log.errors
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        self.log.ok(f"Rapport → {path}")

    # ── RUN PRINCIPAL ─────────────────────────────────────────
    def run(self) -> int:
        print(BANNER)
        self.log.info(f"M2_F06 CARRIER v{M2_F06_VERSION}")

        # ── Vérification FFmpeg
        if not check_ffmpeg():
            self.log.error("FFmpeg introuvable — requis pour M2_F06")
            self.report["status"] = "FAILED_FFMPEG"
            self._save_report()
            return 1

        # ── Résolution inputs
        frames = get_frame_list(IN_FRAMES_DIR)
        audio_path = self._resolve_audio()

        self.report["inputs"] = {
            "frame_count": len(frames),
            "frames_dir": str(IN_FRAMES_DIR),
            "audio": str(audio_path) if audio_path else None,
        }

        if not frames:
            self.log.error(f"Aucune frame dans {IN_FRAMES_DIR}")
            self.report["status"] = "FAILED_NO_FRAMES"
            self._save_report()
            return 1

        self.log.ok(f"Frames : {len(frames)}")
        if audio_path:
            self.log.ok(f"Audio  : {audio_path.name}")

        # ── Dry-run
        if self.args.dry_run:
            self.log.info("DRY-RUN — inspection sans traitement")
            self.report["status"] = "DRY_RUN"
            self._save_report()
            return 0

        # ── LOI R-04 : Choix overlay
        overlay_yes = self._ask_overlay()
        self.log.info(f"Overlay : {'OUI' if overlay_yes else 'NON'}")

        # ── Pipeline
        # 1. Assembly
        inter = self._assemble_frames(frames)
        if inter is None:
            self.report["status"] = "FAILED_ASSEMBLY"
            self._save_report()
            return 1

        # 2. RIFE
        rife_out = self._run_rife(inter)

        # 3. Upscale
        upscaled = self._run_upscale(rife_out)

        # 4. Overlay binaire
        overlaid = self._apply_overlay(upscaled, audio_path, overlay_yes)

        # 5. Encode final
        final = self._final_encode(overlaid)
        if final is None:
            self.report["status"] = "FAILED_ENCODE"
            self._save_report()
            return 1

        # ── Nettoyage
        self._cleanup()

        # ── Succès
        self.report["status"] = "SUCCESS"
        self._save_report()

        self.log.section("RÉSULTAT FINAL")
        self.log.ok(f"M2_F06 CARRIER : SUCCÈS")
        self.log.ok(f"Overlay : {'OUI — Audio+Texte' if overlay_yes else 'NON — Brute'}")
        self.log.ok(f"Fichier final : {final.name}")
        self.log.ok("Pipeline Mode 2 TERMINÉ ─► OUT_FINAL_MOVIE/")
        return 0


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M2_F06 — Aircraft Carrier Mode 2 (Assembly + Overlay → FINAL.mp4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # LOI R-04 overlay
    parser.add_argument(
        "--overlay",
        choices=["yes", "no", "oui", "non"],
        metavar="yes|no",
        help="Overlay binaire (LOI R-04) : oui = audio+texte, non = vidéo brute",
    )
    parser.add_argument("--text",      metavar="STR",   help="Texte overlay (si --overlay yes)")
    parser.add_argument("--font-size", type=int, default=40, metavar="N", help="Taille police overlay (défaut: 40)")
    parser.add_argument("--audio",     metavar="FILE",  help="Fichier audio (défaut: IN_AUDIO/*)")

    # Encode
    parser.add_argument("--format",    choices=["h265", "av1", "prores"], default="h265",
                        help="Format encodage final (défaut: h265)")
    parser.add_argument("--source-fps", type=int, default=DEFAULT_SOURCE_FPS,
                        metavar="FPS", help=f"FPS source frames (défaut: {DEFAULT_SOURCE_FPS})")

    # RIFE
    parser.add_argument("--target-fps", type=int, default=DEFAULT_TARGET_FPS,
                        metavar="FPS", help=f"FPS cible RIFE (défaut: {DEFAULT_TARGET_FPS})")
    parser.add_argument("--no-rife",    action="store_true", help="Désactiver RIFE interpolation")

    # Upscale
    parser.add_argument("--upscale-factor", type=int, default=DEFAULT_SCALE, metavar="N",
                        help=f"Facteur upscale Real-CUGAN (défaut: {DEFAULT_SCALE})")
    parser.add_argument("--no-upscale", action="store_true", help="Désactiver Real-CUGAN upscale")

    # Divers
    parser.add_argument("--keep-intermediates", action="store_true",
                        help="Conserver les fichiers intermédiaires")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    carrier = M2F06Carrier(args)
    sys.exit(carrier.run())


if __name__ == "__main__":
    main()
