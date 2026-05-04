#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         MODE 2 — FRÉGATE M2_F03 — SCENOGRAPHY DOCK                          ║
║         Import GLB Décor + Shadow Catcher + HDRi Éclairage                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0 — Phase 8 — Dual Pipeline Doctrine (02.05.2026)            ║
║  Loi R-01 : Copie indépendante Mode 2 — ZERO contamination Mode 1          ║
║  Loi R-05 : GLB décor fourni par Opérateur — géré ici                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  4 OPÉRATIONS UNIQUEMENT (Doctrine Codex Brainstorm v1) :                   ║
║    1. Importer le GLB décor complet (mesh + textures + lumières)            ║
║    2. Importer le GLB avatar animé                                           ║
║    3. Ajouter shadow catcher sur sol Y=0                                    ║
║    4. Configurer HDRi éclairage ambiance + exporter .blend                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  INPUTS :                                                                   ║
║    IN_GLB_DECOR/   ← decor.glb (GLB décor fourni par Opérateur)            ║
║    IN_GLB_AVATAR/  ← avatar_validated.glb (de M2_F01)                      ║
║    IN_AUDIO/       ← audio_validated.* (optionnel, transféré tel quel)     ║
║  OUTPUTS :                                                                  ║
║    OUT_SCENE/      ← scene_m2.blend (prêt pour M2_F04)                     ║
║    OUT_REPORT/     ← m2_f03_report.json                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage (orchestrateur Python — lance Blender headless) :
    python EXO_M2_F03_SCENOGRAPHY.py
    python EXO_M2_F03_SCENOGRAPHY.py --decor decor.glb --avatar avatar.glb
    python EXO_M2_F03_SCENOGRAPHY.py --hdri path/to/sky.hdr
    python EXO_M2_F03_SCENOGRAPHY.py --skip-hdri
    python EXO_M2_F03_SCENOGRAPHY.py --shadow-size 80
    python EXO_M2_F03_SCENOGRAPHY.py --dry-run
    python EXO_M2_F03_SCENOGRAPHY.py --verbose

Usage (Blender headless interne — NE PAS appeler directement) :
    blender --background --python EXO_M2_F03_SCENOGRAPHY.py -- --blender-mode ...
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ──────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────
M2_F03_VERSION = "1.0.0"

FREGATE_DIR    = Path(__file__).resolve().parent.parent
IN_DECOR_DIR   = FREGATE_DIR / "IN_GLB_DECOR"
IN_AVATAR_DIR  = FREGATE_DIR / "IN_GLB_AVATAR"
IN_AUDIO_DIR   = FREGATE_DIR / "IN_AUDIO"
OUT_SCENE_DIR  = FREGATE_DIR / "OUT_SCENE"
OUT_REPORT_DIR = FREGATE_DIR / "OUT_REPORT"

BLENDER_SUBDIR  = "blender-4.0.0-linux-x64"
BLENDER_BINARY  = "blender"  # Override via --blender si besoin

OUTPUT_BLEND    = "scene_m2.blend"
REPORT_FILENAME = "m2_f03_report.json"

BANNER = """
╔═══════════════════════════════════════════════════════╗
║     MODE 2 — FRÉGATE M2_F03 — SCENOGRAPHY DOCK       ║
║     GLB Décor + Shadow Catcher + HDRi                 ║
╠═══════════════════════════════════════════════════════╣
║  4 ops : Import Décor | Import Avatar                 ║
║          Shadow Catcher | HDRi → .blend               ║
╚═══════════════════════════════════════════════════════╝
"""

# ──────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────
class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def info(self, msg: str):
        print(f"[M2_F03] {msg}")

    def debug(self, msg: str):
        if self.verbose:
            print(f"[M2_F03:DBG] {msg}")

    def ok(self, msg: str):
        print(f"[M2_F03:OK] {msg}")

    def warn(self, msg: str):
        print(f"[M2_F03:WARN] {msg}")

    def error(self, msg: str):
        print(f"[M2_F03:ERR] {msg}", file=sys.stderr)

    def section(self, title: str):
        bar = "─" * (len(title) + 4)
        print(f"\n┌{bar}┐")
        print(f"│  {title}  │")
        print(f"└{bar}┘")


# ──────────────────────────────────────────────────────────────
# SCRIPT BLENDER HEADLESS (injecté dynamiquement)
# ──────────────────────────────────────────────────────────────
BLENDER_SCRIPT = '''
import bpy
import sys
import json
import math
from pathlib import Path

# ── Lecture arguments injectés ────────────────────────────────
args_raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
params = {}
for i, a in enumerate(args_raw):
    if a.startswith("--") and i + 1 < len(args_raw):
        params[a[2:]] = args_raw[i + 1]
    elif a.startswith("--"):
        params[a[2:]] = "true"

decor_glb   = params.get("decor-glb", "")
avatar_glb  = params.get("avatar-glb", "")
hdri_path   = params.get("hdri-path", "")
skip_hdri   = params.get("skip-hdri", "false").lower() == "true"
shadow_size = float(params.get("shadow-size", "50.0"))
output_path = params.get("output", "scene_m2.blend")
res_x       = int(params.get("res-x", "1920"))
res_y       = int(params.get("res-y", "1080"))

print(f"[BLENDER] M2_F03 SCENOGRAPHY — Blender {bpy.app.version_string}")
print(f"[BLENDER] GLB Décor  : {decor_glb}")
print(f"[BLENDER] GLB Avatar : {avatar_glb}")
print(f"[BLENDER] HDRi       : {hdri_path or 'SKIP' if skip_hdri else 'auto'}")
print(f"[BLENDER] Shadow     : {shadow_size}m")
print(f"[BLENDER] Output     : {output_path}")
print(f"[BLENDER] Resolution : {res_x}x{res_y}")

# ── 1. Scène propre ───────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "M2_SCENE"
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.render.resolution_x = res_x
scene.render.resolution_y = res_y
scene.render.resolution_percentage = 100
print(f"[BLENDER] Resolution settee : {res_x}x{res_y}")

def ensure_collection(name):
    if name not in bpy.data.collections:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return bpy.data.collections[name]

# ── 2. OPÉRATION 1 : Import GLB Décor ─────────────────────────
decor_ok = False
if decor_glb and Path(decor_glb).exists():
    print("[BLENDER] OP-1 : Import GLB Décor...")
    try:
        bpy.ops.import_scene.gltf(filepath=decor_glb)
        decor_objects = [o for o in bpy.context.selected_objects]
        coll_decor = ensure_collection("DECOR")
        for obj in decor_objects:
            for c in obj.users_collection:
                c.objects.unlink(obj)
            coll_decor.objects.link(obj)
        print(f"[BLENDER] OP-1 OK : {len(decor_objects)} objet(s) importés dans DECOR")
        decor_ok = True
    except Exception as e:
        print(f"[BLENDER] OP-1 ERREUR : {e}")
else:
    print(f"[BLENDER] OP-1 SKIP : GLB décor absent ou non fourni")

# ── 3. OPÉRATION 2 : Import GLB Avatar ────────────────────────
avatar_ok = False
if avatar_glb and Path(avatar_glb).exists():
    print("[BLENDER] OP-2 : Import GLB Avatar...")
    try:
        bpy.ops.import_scene.gltf(filepath=avatar_glb)
        avatar_objects = [o for o in bpy.context.selected_objects]
        coll_avatar = ensure_collection("AVATARS")
        for obj in avatar_objects:
            for c in obj.users_collection:
                c.objects.unlink(obj)
            coll_avatar.objects.link(obj)
        print(f"[BLENDER] OP-2 OK : {len(avatar_objects)} objet(s) importés dans AVATARS")
        avatar_ok = True
    except Exception as e:
        print(f"[BLENDER] OP-2 ERREUR : {e}")
else:
    print("[BLENDER] OP-2 SKIP : GLB avatar absent")

# ── 4. OPÉRATION 3 : Shadow Catcher sur sol Y=0 ───────────────
print("[BLENDER] OP-3 : Shadow Catcher Y=0...")
bpy.ops.mesh.primitive_plane_add(size=shadow_size, location=(0, 0, 0))
sc_obj = bpy.context.active_object
sc_obj.name = "shadow_catcher_m2"

sc_obj.is_shadow_catcher = True
sc_obj.visible_camera = False
sc_obj.visible_diffuse = False
sc_obj.visible_glossy = False
sc_obj.visible_transmission = False
sc_obj.visible_volume_scatter = False

mat = bpy.data.materials.new(name="MAT_ShadowCatcher_M2")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()
output_node = nodes.new("ShaderNodeOutputMaterial")
output_node.location = (300, 0)
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.location = (0, 0)
bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
bsdf.inputs["Alpha"].default_value = 0.0
links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])
mat.blend_method = "CLIP"
mat.shadow_method = "CLIP"
if sc_obj.data.materials:
    sc_obj.data.materials[0] = mat
else:
    sc_obj.data.materials.append(mat)

coll_sc = ensure_collection("SHADOW_CATCHERS")
for c in sc_obj.users_collection:
    c.objects.unlink(sc_obj)
coll_sc.objects.link(sc_obj)
print(f"[BLENDER] OP-3 OK : shadow_catcher_m2 (size={shadow_size}m, Y=0)")

# ── 5. OPÉRATION 4 : HDRi éclairage ambiance ──────────────────
hdri_ok = False
if not skip_hdri:
    print("[BLENDER] OP-4 : Configuration HDRi...")
    world = bpy.data.worlds.new("M2_World")
    scene.world = world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()

    bg_node = wn.new("ShaderNodeBackground")
    bg_node.location = (0, 0)

    output_w = wn.new("ShaderNodeOutputWorld")
    output_w.location = (300, 0)

    if hdri_path and Path(hdri_path).exists():
        # HDRi explicite fourni
        env_tex = wn.new("ShaderNodeTexEnvironment")
        env_tex.location = (-300, 0)
        try:
            img = bpy.data.images.load(hdri_path)
            env_tex.image = img
            wl.new(env_tex.outputs["Color"], bg_node.inputs["Color"])
            hdri_ok = True
            print(f"[BLENDER] OP-4 OK : HDRi chargé depuis {hdri_path}")
        except Exception as e:
            print(f"[BLENDER] OP-4 WARN HDRi : {e} — utilisation couleur neutre")
            bg_node.inputs["Color"].default_value = (0.5, 0.5, 0.7, 1.0)
            bg_node.inputs["Strength"].default_value = 1.0
    else:
        # Pas de HDRi : ciel neutre par défaut (gris-bleu doux)
        bg_node.inputs["Color"].default_value = (0.5, 0.5, 0.7, 1.0)
        bg_node.inputs["Strength"].default_value = 1.0
        print("[BLENDER] OP-4 : Ciel neutre par défaut (no HDRi provided)")
        hdri_ok = True

    wl.new(bg_node.outputs["Background"], output_w.inputs["Surface"])
else:
    print("[BLENDER] OP-4 SKIP : --skip-hdri activé")
    hdri_ok = True

# ── Rapport interne Blender ────────────────────────────────────
report = {
    "blender_version": list(bpy.app.version),
    "decor_imported": decor_ok,
    "avatar_imported": avatar_ok,
    "shadow_catcher": True,
    "hdri_applied": hdri_ok,
    "collections": list(bpy.data.collections.keys()),
    "object_count": len(list(bpy.data.objects)),
}

report_path = str(Path(output_path).parent.parent / "OUT_REPORT" / "m2_f03_blender_internal.json")
try:
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as rf:
        json.dump(report, rf, indent=2)
    print(f"[BLENDER] Rapport interne : {report_path}")
except Exception as e:
    print(f"[BLENDER] Rapport interne non sauvegardé : {e}")

# ── Export .blend ──────────────────────────────────────────────
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"[BLENDER] .blend exporté : {output_path}")
print("[BLENDER] M2_F03 TERMINÉ")
'''


# ──────────────────────────────────────────────────────────────
# ORCHESTRATEUR
# ──────────────────────────────────────────────────────────────
class M2F03Scenography:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.log = Logger(verbose=args.verbose)
        self.report: Dict = {
            "fregate": "M2_F03_SCENOGRAPHY",
            "version": M2_F03_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PENDING",
            "inputs": {},
            "blender_run": {},
            "outputs": {},
            "errors": [],
            "warnings": [],
        }

    def _read_output_format(self):
        """Lit output_format depuis exodus_session.json (ecrit par le Launcher)."""
        session_path = FREGATE_DIR.parent / "exodus_session.json"
        if session_path.exists():
            try:
                with open(session_path, encoding="utf-8") as f:
                    data = json.load(f)
                fmt = data.get("output_format", {})
                w = int(fmt.get("width", 1920))
                h = int(fmt.get("height", 1080))
                orient = fmt.get("orientation", "?")
                self.log.ok(f"Format session : {w}x{h} ({orient})")
                return w, h
            except Exception as e:
                self.log.warn(f"Session JSON illisible ({e}) — format HOR par defaut")
        return 1920, 1080

    def _find_blender(self) -> str:
        if self.args.blender:
            return self.args.blender
        # Cherche blender dans PATH ou dans sous-dossier EXODUS
        from shutil import which
        blender_path = which("blender")
        if blender_path:
            return blender_path
        # Recherche dans Drive (pattern EXODUS)
        drive_root = FREGATE_DIR.parent
        for pattern in [f"**/{BLENDER_SUBDIR}/blender", "**/blender"]:
            candidates = list(drive_root.glob(pattern))
            if candidates:
                return str(candidates[0])
        return BLENDER_BINARY

    def _resolve_decor(self) -> Optional[Path]:
        if self.args.decor:
            p = Path(self.args.decor)
            return p if p.is_absolute() else IN_DECOR_DIR / p
        candidates = list(IN_DECOR_DIR.glob("*.glb"))
        return candidates[0] if candidates else None

    def _resolve_avatar(self) -> Optional[Path]:
        if self.args.avatar:
            p = Path(self.args.avatar)
            return p if p.is_absolute() else IN_AVATAR_DIR / p
        candidates = list(IN_AVATAR_DIR.glob("*.glb"))
        return candidates[0] if candidates else None

    def _resolve_hdri(self) -> Optional[Path]:
        if self.args.hdri:
            return Path(self.args.hdri)
        # Auto-détection HDRi dans le repo
        drive_root = FREGATE_DIR.parent
        for ext in ["*.hdr", "*.exr", "*.HDR"]:
            candidates = list(drive_root.rglob(ext))
            if candidates:
                self.log.debug(f"HDRi auto-détecté : {candidates[0]}")
                return candidates[0]
        return None

    def _write_blender_script(self, tmp_path: Path) -> Path:
        script_path = tmp_path / "m2_f03_blender_scene.py"
        script_path.write_text(BLENDER_SCRIPT, encoding="utf-8")
        return script_path

    def _run_blender(
        self,
        decor_path: Optional[Path],
        avatar_path: Optional[Path],
        hdri_path: Optional[Path],
        output_blend: Path,
    ) -> bool:
        blender = self._find_blender()
        self.log.info(f"Blender : {blender}")

        # Script temporaire
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = self._write_blender_script(Path(tmpdir))

            cmd = [blender, "--background", "--python", str(script_path), "--"]
            if decor_path:
                cmd += ["--decor-glb", str(decor_path)]
            if avatar_path:
                cmd += ["--avatar-glb", str(avatar_path)]
            if hdri_path and not self.args.skip_hdri:
                cmd += ["--hdri-path", str(hdri_path)]
            if self.args.skip_hdri:
                cmd.append("--skip-hdri")
            cmd += ["--shadow-size", str(self.args.shadow_size)]
            cmd += ["--res-x", str(self._res_x)]
            cmd += ["--res-y", str(self._res_y)]
            cmd += ["--output", str(output_blend)]

            self.log.debug(f"Commande : {' '.join(cmd)}")
            self.report["blender_run"]["command"] = cmd

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=not self.args.verbose,
                    text=True,
                    timeout=300,
                )
                if self.args.verbose and proc.stdout:
                    print(proc.stdout)
                if proc.stderr and self.args.verbose:
                    print(proc.stderr, file=sys.stderr)

                self.report["blender_run"]["returncode"] = proc.returncode
                return proc.returncode == 0

            except FileNotFoundError:
                self.log.error(f"Blender introuvable : {blender}")
                self.report["errors"].append(f"Blender introuvable : {blender}")
                return False
            except subprocess.TimeoutExpired:
                self.log.error("Timeout Blender (300s)")
                self.report["errors"].append("Timeout Blender")
                return False

    def _copy_audio(self):
        """Transfert audio tel quel vers OUT_SCENE (transit vers M2_F04)."""
        audio_files = []
        for ext in [".wav", ".mp3", ".ogg", ".aac", ".flac"]:
            audio_files.extend(IN_AUDIO_DIR.glob(f"*{ext}"))
        for af in audio_files:
            dest = OUT_SCENE_DIR / af.name
            shutil.copy2(str(af), str(dest))
            self.log.ok(f"Audio transféré → {dest.name}")

    def _save_report(self):
        OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_REPORT_DIR / REPORT_FILENAME
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        self.log.ok(f"Rapport → {path}")

    def run(self) -> int:
        print(BANNER)
        self.log.info(f"M2_F03 SCENOGRAPHY v{M2_F03_VERSION}")
        self.log.info(f"Timestamp : {self.report['timestamp']}")

        # ── Format de sortie depuis session JSON
        self._res_x, self._res_y = self._read_output_format()

        # ── Résolution inputs
        self.log.section("RÉSOLUTION INPUTS")
        decor_path  = self._resolve_decor()
        avatar_path = self._resolve_avatar()
        hdri_path   = self._resolve_hdri() if not self.args.skip_hdri else None

        self.report["inputs"]["decor"]  = str(decor_path) if decor_path else None
        self.report["inputs"]["avatar"] = str(avatar_path) if avatar_path else None
        self.report["inputs"]["hdri"]   = str(hdri_path) if hdri_path else None

        if decor_path:
            self.log.ok(f"GLB Décor  : {decor_path.name}")
        else:
            self.log.warn("GLB Décor absent — scène sans décor")

        if avatar_path:
            self.log.ok(f"GLB Avatar : {avatar_path.name}")
        else:
            self.log.warn("GLB Avatar absent — scène sans avatar")

        if hdri_path:
            self.log.ok(f"HDRi       : {hdri_path.name}")
        elif not self.args.skip_hdri:
            self.log.info("HDRi non trouvé — ciel neutre par défaut")

        # ── Dry-run
        if self.args.dry_run:
            self.log.info("DRY-RUN — pas d'exécution Blender")
            self.report["status"] = "DRY_RUN"
            self._save_report()
            return 0

        # ── Création output dir
        OUT_SCENE_DIR.mkdir(parents=True, exist_ok=True)
        output_blend = OUT_SCENE_DIR / OUTPUT_BLEND

        # ── Lancement Blender
        self.log.section("BLENDER HEADLESS")
        self.log.info("4 opérations : Décor | Avatar | Shadow Catcher | HDRi")

        blender_ok = self._run_blender(decor_path, avatar_path, hdri_path, output_blend)

        if not blender_ok:
            self.report["status"] = "FAILED_BLENDER"
            self._save_report()
            return 1

        if not output_blend.exists():
            self.log.error(f".blend non généré : {output_blend}")
            self.report["status"] = "FAILED_OUTPUT"
            self._save_report()
            return 1

        blend_size_mb = output_blend.stat().st_size / (1024 * 1024)
        self.log.ok(f".blend généré : {output_blend.name} ({blend_size_mb:.2f} MB)")
        self.report["outputs"]["blend"] = str(output_blend)

        # ── Transit audio
        self.log.section("TRANSIT AUDIO")
        self._copy_audio()

        # ── Lecture rapport interne Blender
        internal_report_path = OUT_REPORT_DIR / "m2_f03_blender_internal.json"
        if internal_report_path.exists():
            with open(internal_report_path) as f:
                self.report["blender_run"]["internal"] = json.load(f)

        # ── Succès
        self.report["status"] = "SUCCESS"
        self._save_report()

        self.log.section("RÉSULTAT FINAL")
        self.log.ok("M2_F03 SCENOGRAPHY : SUCCÈS")
        self.log.ok(f"Scene blend : {output_blend.name}")
        self.log.ok("Prêt pour M2_F04 ─► OUT_SCENE/")
        return 0


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M2_F03 — Scenography Dock Mode 2 (GLB Décor + Shadow + HDRi)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--decor",  metavar="FILE", help="GLB décor (défaut: IN_GLB_DECOR/*.glb)")
    parser.add_argument("--avatar", metavar="FILE", help="GLB avatar (défaut: IN_GLB_AVATAR/*.glb)")
    parser.add_argument("--hdri",   metavar="FILE", help="Fichier HDRi .hdr/.exr (auto-détecté si absent)")
    parser.add_argument("--skip-hdri", action="store_true", help="Ne pas appliquer de HDRi")
    parser.add_argument("--shadow-size", type=float, default=50.0, metavar="M",
                        help="Taille du shadow catcher en mètres (défaut: 50)")
    parser.add_argument("--blender", metavar="PATH", help="Chemin vers binaire Blender")
    parser.add_argument("--dry-run", action="store_true", help="Validation sans exécution Blender")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main():
    # Si lancé depuis Blender headless (--python), le script BLENDER_SCRIPT est
    # injecté directement — ce main() ne s'exécute pas dans ce cas.
    # Ce main() = point d'entrée orchestrateur Python normal.
    args = parse_args()
    m2f03 = M2F03Scenography(args)
    sys.exit(m2f03.run())


if __name__ == "__main__":
    main()
