#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              MODE 2 — FRÉGATE M2_F01 — ANIMATION VALIDATOR                  ║
║              Validation GLB Avatar + Vérification Audio                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0 — Phase 8 — Dual Pipeline Doctrine (02.05.2026)            ║
║  Loi R-01 : Copie indépendante Mode 2 — ZERO contamination Mode 1          ║
║  Loi R-02 : GLB obligatoire avec animations embarquées                      ║
║  Loi R-03 : durée_audio <= durée_animation (animation prime)                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  INPUTS (IN_GLB_AVATAR/):                                                   ║
║    avatar.glb  (avatar Roblox animé — fourni par Opérateur)                ║
║  INPUTS (IN_AUDIO/) [OPTIONNEL]:                                            ║
║    audio.wav / audio.mp3  (piste audio à synchroniser)                      ║
║  OUTPUTS (OUT_VALIDATED/):                                                  ║
║    avatar_validated.glb   (copie validée, prête pour M2_F02)               ║
║  OUTPUTS (OUT_REPORT/):                                                     ║
║    m2_f01_report.json     (rapport de validation complet)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python EXO_M2_F01_ANIMATION.py                      # Mode interactif
    python EXO_M2_F01_ANIMATION.py --glb avatar.glb     # GLB explicite
    python EXO_M2_F01_ANIMATION.py --glb avatar.glb --audio audio.wav
    python EXO_M2_F01_ANIMATION.py --dry-run            # Validation sans copie
    python EXO_M2_F01_ANIMATION.py --verbose
"""

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────
M2_F01_VERSION = "1.0.0"

FREGATE_DIR    = Path(__file__).resolve().parent.parent
IN_GLB_DIR     = FREGATE_DIR / "IN_GLB_AVATAR"
IN_AUDIO_DIR   = FREGATE_DIR / "IN_AUDIO"
OUT_VALID_DIR  = FREGATE_DIR / "OUT_VALIDATED"
OUT_REPORT_DIR = FREGATE_DIR / "OUT_REPORT"

SUPPORTED_AUDIO = {".wav", ".mp3", ".ogg", ".aac", ".flac"}
GLB_MAGIC_BYTES = b"glTF"  # GLB magic header

BANNER = """
╔═══════════════════════════════════════════════════════╗
║     MODE 2 — FRÉGATE M2_F01 — ANIMATION VALIDATOR    ║
║     Validation GLB + Audio Check                      ║
╠═══════════════════════════════════════════════════════╣
║  R-02 : GLB + animations embarquées                   ║
║  R-03 : durée audio <= durée animation                ║
╚═══════════════════════════════════════════════════════╝
"""


# ──────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────
class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def info(self, msg: str):
        print(f"[M2_F01] {msg}")

    def debug(self, msg: str):
        if self.verbose:
            print(f"[M2_F01:DBG] {msg}")

    def ok(self, msg: str):
        print(f"[M2_F01:OK] {msg}")

    def warn(self, msg: str):
        print(f"[M2_F01:WARN] {msg}")

    def error(self, msg: str):
        print(f"[M2_F01:ERR] {msg}", file=sys.stderr)

    def section(self, title: str):
        bar = "─" * (len(title) + 4)
        print(f"\n┌{bar}┐")
        print(f"│  {title}  │")
        print(f"└{bar}┘")


# ──────────────────────────────────────────────────────────────
# GLB VALIDATOR
# ──────────────────────────────────────────────────────────────
class GLBValidator:
    """
    Valide un fichier GLB selon les lois impériales Mode 2.
    Utilise pygltflib si disponible, sinon analyse binaire native.
    """

    def __init__(self, logger: Logger):
        self.log = logger
        self._pygltflib_available = self._check_pygltflib()

    def _check_pygltflib(self) -> bool:
        try:
            import pygltflib  # noqa: F401
            return True
        except ImportError:
            return False

    def validate(self, glb_path: Path) -> Dict:
        """
        Retourne un dict de résultats de validation.
        {
            "valid": bool,
            "errors": [...],
            "warnings": [...],
            "animations": [{"name": str, "duration_s": float}, ...],
            "total_duration_s": float,
            "node_count": int,
            "mesh_count": int,
            "has_animations": bool,
        }
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "animations": [],
            "total_duration_s": 0.0,
            "node_count": 0,
            "mesh_count": 0,
            "has_animations": False,
            "file_size_mb": 0.0,
        }

        # ── Existence & taille
        if not glb_path.exists():
            result["errors"].append(f"Fichier introuvable : {glb_path}")
            return result

        size_mb = glb_path.stat().st_size / (1024 * 1024)
        result["file_size_mb"] = round(size_mb, 2)
        self.log.debug(f"Taille GLB : {size_mb:.2f} MB")

        if size_mb < 0.001:
            result["errors"].append("Fichier GLB vide ou corrompu (< 1 KB)")
            return result

        # ── Magic bytes GLB
        with open(glb_path, "rb") as f:
            magic = f.read(4)
        if magic != GLB_MAGIC_BYTES:
            result["errors"].append(
                f"Magic bytes invalides : attendu 'glTF', obtenu '{magic}'"
            )
            return result

        self.log.debug("Magic bytes GLB : OK")

        # ── Validation approfondie
        if self._pygltflib_available:
            return self._validate_with_pygltflib(glb_path, result)
        else:
            self.log.warn("pygltflib non disponible — validation basique uniquement")
            return self._validate_basic(glb_path, result)

    def _validate_with_pygltflib(self, glb_path: Path, result: Dict) -> Dict:
        """Validation complète via pygltflib."""
        import pygltflib

        try:
            gltf = pygltflib.GLTF2().load(str(glb_path))
        except Exception as e:
            result["errors"].append(f"pygltflib parse error : {e}")
            return result

        # Noeuds & meshes
        result["node_count"] = len(gltf.nodes) if gltf.nodes else 0
        result["mesh_count"] = len(gltf.meshes) if gltf.meshes else 0
        self.log.debug(f"Noeuds : {result['node_count']} | Meshes : {result['mesh_count']}")

        if result["mesh_count"] == 0:
            result["warnings"].append("Aucun mesh détecté dans le GLB")

        # ── Animations (LOI R-02)
        animations = gltf.animations or []
        if not animations:
            result["errors"].append(
                "LOI R-02 VIOLÉE : aucune animation embarquée dans le GLB. "
                "Le GLB Mode 2 doit contenir des animations."
            )
            return result

        # Calcul durée par animation
        accessors = gltf.accessors or []
        for anim in animations:
            anim_duration = 0.0
            for channel in (anim.channels or []):
                sampler = anim.samplers[channel.sampler] if anim.samplers else None
                if sampler and sampler.input < len(accessors):
                    acc = accessors[sampler.input]
                    if acc.max and len(acc.max) > 0:
                        anim_duration = max(anim_duration, acc.max[0])

            anim_name = getattr(anim, "name", None) or f"Animation_{len(result['animations'])}"
            result["animations"].append({
                "name": anim_name,
                "duration_s": round(anim_duration, 4),
            })
            self.log.debug(f"Animation '{anim_name}' : {anim_duration:.3f}s")

        result["has_animations"] = True
        result["total_duration_s"] = max(
            (a["duration_s"] for a in result["animations"]), default=0.0
        )
        self.log.ok(
            f"{len(result['animations'])} animation(s) — durée max : {result['total_duration_s']:.3f}s"
        )

        if result["total_duration_s"] <= 0:
            result["warnings"].append(
                "Animations présentes mais durée = 0s (accessors max non définis)"
            )

        result["valid"] = len(result["errors"]) == 0
        return result

    def _validate_basic(self, glb_path: Path, result: Dict) -> Dict:
        """Validation basique sans pygltflib : parse JSON chunk."""
        try:
            with open(glb_path, "rb") as f:
                f.read(12)  # header (magic + version + length)
                chunk0_len = int.from_bytes(f.read(4), "little")
                chunk0_type = f.read(4)
                if chunk0_type != b"JSON":
                    result["errors"].append("Chunk 0 n'est pas JSON — GLB malformé")
                    return result
                json_data = json.loads(f.read(chunk0_len).decode("utf-8"))
        except Exception as e:
            result["errors"].append(f"Erreur lecture GLB binaire : {e}")
            return result

        animations = json_data.get("animations", [])
        result["node_count"] = len(json_data.get("nodes", []))
        result["mesh_count"] = len(json_data.get("meshes", []))

        if not animations:
            result["errors"].append(
                "LOI R-02 VIOLÉE : aucune animation dans le GLB (validation basique)"
            )
            return result

        for anim in animations:
            result["animations"].append({
                "name": anim.get("name", "unknown"),
                "duration_s": 0.0,  # pas calculable sans accessors complets
            })

        result["has_animations"] = True
        result["warnings"].append(
            "Durée animation non calculable sans pygltflib — installer : pip install pygltflib"
        )
        result["valid"] = len(result["errors"]) == 0
        return result


# ──────────────────────────────────────────────────────────────
# AUDIO CHECKER
# ──────────────────────────────────────────────────────────────
class AudioChecker:
    """
    Vérifie la durée audio et applique la LOI R-03 :
    durée_audio <= durée_animation.
    """

    def __init__(self, logger: Logger):
        self.log = logger

    def get_duration(self, audio_path: Path) -> Optional[float]:
        """
        Retourne la durée en secondes.
        Essaie librosa, puis pydub, puis analyse binaire WAV.
        """
        # Méthode 1 : librosa
        try:
            import librosa
            duration = librosa.get_duration(path=str(audio_path))
            self.log.debug(f"Durée audio (librosa) : {duration:.3f}s")
            return duration
        except ImportError:
            pass
        except Exception as e:
            self.log.debug(f"librosa erreur : {e}")

        # Méthode 2 : pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            duration = len(audio) / 1000.0
            self.log.debug(f"Durée audio (pydub) : {duration:.3f}s")
            return duration
        except ImportError:
            pass
        except Exception as e:
            self.log.debug(f"pydub erreur : {e}")

        # Méthode 3 : WAV natif Python
        if audio_path.suffix.lower() == ".wav":
            try:
                import wave
                with wave.open(str(audio_path), "r") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
                    self.log.debug(f"Durée audio (wave) : {duration:.3f}s")
                    return duration
            except Exception as e:
                self.log.debug(f"wave erreur : {e}")

        self.log.warn(
            "Impossible de calculer la durée audio. "
            "Installer librosa ou pydub : pip install librosa pydub"
        )
        return None

    def check_loi_r03(
        self, audio_duration: float, anim_duration: float
    ) -> Tuple[bool, str]:
        """
        Vérifie LOI R-03 : durée_audio <= durée_animation.
        Retourne (conforme, message).
        """
        if anim_duration <= 0:
            return False, "Durée animation = 0 — impossible de valider R-03"

        if audio_duration <= anim_duration:
            surplus = anim_duration - audio_duration
            return True, (
                f"R-03 CONFORME : audio={audio_duration:.3f}s <= "
                f"anim={anim_duration:.3f}s (surplus={surplus:.3f}s)"
            )
        else:
            excess = audio_duration - anim_duration
            return False, (
                f"LOI R-03 VIOLÉE : audio={audio_duration:.3f}s > "
                f"anim={anim_duration:.3f}s (excès={excess:.3f}s). "
                f"L'animation PRIME — tronquer l'audio ou utiliser un GLB plus long."
            )


# ──────────────────────────────────────────────────────────────
# ORCHESTRATEUR PRINCIPAL
# ──────────────────────────────────────────────────────────────
class M2F01Validator:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.log = Logger(verbose=args.verbose)
        self.glb_validator = GLBValidator(self.log)
        self.audio_checker = AudioChecker(self.log)

        self.report: Dict = {
            "fregate": "M2_F01_ANIMATION",
            "version": M2_F01_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PENDING",
            "glb_validation": {},
            "audio_check": {},
            "loi_r03": {},
            "outputs": {},
            "errors": [],
            "warnings": [],
        }

    # ── Résolution des inputs ────────────────────────────────
    def _resolve_glb(self) -> Optional[Path]:
        if self.args.glb:
            p = Path(self.args.glb)
            if not p.is_absolute():
                p = IN_GLB_DIR / p
            return p

        # Auto-détection dans IN_GLB_AVATAR
        candidates = list(IN_GLB_DIR.glob("*.glb"))
        if not candidates:
            self.log.error(f"Aucun .glb trouvé dans {IN_GLB_DIR}")
            return None
        if len(candidates) > 1:
            self.log.warn(f"{len(candidates)} GLB trouvés — utilisation du premier")
        return candidates[0]

    def _resolve_audio(self) -> Optional[Path]:
        if self.args.audio:
            p = Path(self.args.audio)
            if not p.is_absolute():
                p = IN_AUDIO_DIR / p
            return p if p.exists() else None

        # Auto-détection
        for ext in SUPPORTED_AUDIO:
            candidates = list(IN_AUDIO_DIR.glob(f"*{ext}"))
            if candidates:
                return candidates[0]
        return None

    # ── Validation GLB ──────────────────────────────────────
    def _run_glb_validation(self, glb_path: Path) -> bool:
        self.log.section("VALIDATION GLB")
        self.log.info(f"Fichier : {glb_path.name}")

        result = self.glb_validator.validate(glb_path)
        self.report["glb_validation"] = result

        if result["errors"]:
            for err in result["errors"]:
                self.log.error(err)
            return False

        if result["warnings"]:
            for w in result["warnings"]:
                self.log.warn(w)

        self.log.ok(f"GLB valide — {result['mesh_count']} mesh(es) — "
                    f"{len(result['animations'])} animation(s)")
        return True

    # ── Check Audio ─────────────────────────────────────────
    def _run_audio_check(self, audio_path: Optional[Path], anim_duration: float) -> bool:
        self.log.section("CHECK AUDIO")

        if audio_path is None:
            self.log.info("Aucun audio fourni — étape optionnelle ignorée")
            self.report["audio_check"] = {"status": "NO_AUDIO", "audio_duration_s": 0}
            self.report["loi_r03"] = {"status": "NOT_APPLICABLE", "message": "Pas d'audio"}
            return True

        self.log.info(f"Fichier audio : {audio_path.name}")
        audio_duration = self.audio_checker.get_duration(audio_path)

        if audio_duration is None:
            self.report["audio_check"] = {
                "status": "DURATION_UNKNOWN",
                "file": str(audio_path),
            }
            self.report["loi_r03"] = {
                "status": "SKIPPED",
                "message": "Durée audio incalculable",
            }
            self.log.warn("Durée audio inconnue — R-03 non vérifiable")
            return True  # Non bloquant si pas de lib dispo

        self.report["audio_check"] = {
            "status": "OK",
            "file": audio_path.name,
            "audio_duration_s": round(audio_duration, 4),
        }

        self.log.ok(f"Durée audio : {audio_duration:.3f}s")

        # LOI R-03
        r03_ok, r03_msg = self.audio_checker.check_loi_r03(audio_duration, anim_duration)
        self.report["loi_r03"] = {
            "status": "CONFORME" if r03_ok else "VIOLATION",
            "message": r03_msg,
            "audio_duration_s": round(audio_duration, 4),
            "anim_duration_s": round(anim_duration, 4),
        }

        if r03_ok:
            self.log.ok(r03_msg)
        else:
            self.log.error(r03_msg)

        return r03_ok

    # ── Copie vers OUT_VALIDATED ─────────────────────────────
    def _copy_to_output(self, glb_path: Path, audio_path: Optional[Path]) -> Dict:
        outputs = {}
        OUT_VALID_DIR.mkdir(parents=True, exist_ok=True)

        # GLB validé
        dest_glb = OUT_VALID_DIR / "avatar_validated.glb"
        shutil.copy2(str(glb_path), str(dest_glb))
        self.log.ok(f"GLB copié → {dest_glb}")
        outputs["glb"] = str(dest_glb)

        # Audio si présent
        if audio_path and audio_path.exists():
            dest_audio = OUT_VALID_DIR / f"audio_validated{audio_path.suffix}"
            shutil.copy2(str(audio_path), str(dest_audio))
            self.log.ok(f"Audio copié → {dest_audio}")
            outputs["audio"] = str(dest_audio)

        return outputs

    # ── Sauvegarde rapport ───────────────────────────────────
    def _save_report(self):
        OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = OUT_REPORT_DIR / "m2_f01_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        self.log.ok(f"Rapport sauvegardé → {report_path}")

    # ── RUN PRINCIPAL ────────────────────────────────────────
    def run(self) -> int:
        print(BANNER)
        self.log.info(f"M2_F01 ANIMATION VALIDATOR v{M2_F01_VERSION}")
        self.log.info(f"Timestamp : {self.report['timestamp']}")
        self.log.info(f"Dry-run   : {self.args.dry_run}")

        # 1. Résolution GLB
        glb_path = self._resolve_glb()
        if glb_path is None:
            self.report["status"] = "FAILED"
            self.report["errors"].append("Aucun GLB à valider")
            self._save_report()
            return 1

        # 2. Résolution audio
        audio_path = self._resolve_audio()
        if audio_path:
            self.log.debug(f"Audio détecté : {audio_path}")
        else:
            self.log.info("Mode sans audio (optionnel)")

        # 3. Validation GLB (LOI R-02)
        glb_ok = self._run_glb_validation(glb_path)
        if not glb_ok:
            self.report["status"] = "FAILED_GLB"
            self._save_report()
            return 1

        # 4. Check audio (LOI R-03)
        anim_duration = self.report["glb_validation"].get("total_duration_s", 0.0)
        audio_ok = self._run_audio_check(audio_path, anim_duration)
        if not audio_ok:
            self.report["status"] = "FAILED_LOI_R03"
            self._save_report()
            return 1

        # 5. Copie outputs (si pas dry-run)
        if not self.args.dry_run:
            self.log.section("COPIE OUTPUTS")
            outputs = self._copy_to_output(glb_path, audio_path)
            self.report["outputs"] = outputs
        else:
            self.log.info("DRY-RUN : pas de copie")
            self.report["outputs"] = {"dry_run": True}

        # 6. Rapport final
        self.report["status"] = "SUCCESS"
        self._save_report()

        self.log.section("RÉSULTAT FINAL")
        self.log.ok("M2_F01 VALIDATION : SUCCÈS")
        self.log.ok(f"GLB animations : {len(self.report['glb_validation'].get('animations', []))}")
        self.log.ok(f"Durée animation : {anim_duration:.3f}s")
        if audio_path:
            self.log.ok(f"LOI R-03 : {self.report['loi_r03']['status']}")
        self.log.ok("Prêt pour M2_F02 ─► OUT_VALIDATED/")
        return 0


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M2_F01 — GLB Avatar Validator (Mode 2 EXODUS V2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--glb",
        metavar="FILE",
        help="Chemin vers le fichier GLB avatar (défaut: IN_GLB_AVATAR/*.glb)",
    )
    parser.add_argument(
        "--audio",
        metavar="FILE",
        help="Chemin vers le fichier audio (optionnel, défaut: IN_AUDIO/*)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valide sans copier les fichiers en sortie",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbeux",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    validator = M2F01Validator(args)
    sys.exit(validator.run())


if __name__ == "__main__":
    main()
