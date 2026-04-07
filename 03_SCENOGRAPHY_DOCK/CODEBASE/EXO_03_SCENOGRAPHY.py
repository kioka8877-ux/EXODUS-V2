#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        EXO_03_SCENOGRAPHY V2 — ORCHESTRATEUR TRI-LAYER SYSTEM               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 2.0.0                                                              ║
║  Mission: Construire les décors 3D Tri-Layer (Dome, Shadow, World Sync)     ║
║  Stack: Blender 4.0 Headless + Cycles — Piloté par scene_schema.py          ║
╚══════════════════════════════════════════════════════════════════════════════╝

LOI D'ISOLATION DES SILOS:
    Cette unité est une île. Elle ne communique avec aucune autre Frégate.
    Elle lit ses inputs, produit ses outputs. Point final.

INPUTS REQUIS:
    - PRODUCTION_PLAN.JSON : Spécifications scènes du Cortex (IN_CORTEX_JSON)
    - Depth maps (IN_MAP_RAW/*.png) — utilisé en D2 futur
    - semantic_masks.json (IN_MAP_RAW) — utilisé en D3 futur

OUTPUTS:
    - environment_{scene_id}.blend : Scène Blender Tri-Layer (OUT_PREMIUM_SCENE)
    - scenography_report.json : Rapport de construction V2

PIPELINE V2:
    1. Valider inputs (PRODUCTION_PLAN, depth maps dir, semantic masks)
    2. Valider VRAM profile via scene_schema
    3. Pour chaque scène → Blender headless (layer_assembler.py)
    4. Générer scenography_report.json V2
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

# ─── VOID-FLUSH integration (Tache 44) ───────────────────────────────────────
try:
    from blender_adapter import flush_before_render, flush_after_render
    _VOID_FLUSH_AVAILABLE = True
except Exception:
    _VOID_FLUSH_AVAILABLE = False

# ─── ATLAS integration (Tache 45) ────────────────────────────────────────────
try:
    from session_store import SessionStore
    _ATLAS_AVAILABLE = True
except Exception:
    _ATLAS_AVAILABLE = False

# AUTO-COPIE phantom_link.py (Patch Session #003)
# Si l'Empereur n'a pas copié la version racine sur le Drive, on la forge depuis ce CODEBASE.
drive_root = Path(__file__).resolve().parents[2]
phantom_src = drive_root / "03_SCENOGRAPHY_DOCK" / "CODEBASE" / "phantom_link.py"
phantom_dst = drive_root / "phantom_link.py"
if phantom_src.exists() and not phantom_dst.exists():
    shutil.copy2(phantom_src, phantom_dst)
    print("[SETUP] ✅ phantom_link.py copié vers la racine Drive")

# Phantom Link — Phase D.1
import importlib.util

_phantom_spec = importlib.util.spec_from_file_location(
    "phantom_link",
    Path(__file__).resolve().parents[2] / "phantom_link.py",
)
if _phantom_spec and _phantom_spec.loader:
    _phantom_mod = importlib.util.module_from_spec(_phantom_spec)
    _phantom_spec.loader.exec_module(_phantom_mod)
    resolve_input = _phantom_mod.resolve_input
else:
    resolve_input = lambda p: Path(p)  # fallback si phantom_link.py absent

SCENOGRAPHY_VERSION = "2.0.0"

AI_MODELS_SUBDIR = "EXODUS_AI_MODELS"
BLENDER_SUBDIR = "blender-4.0.0-linux-x64"

VALID_VRAM_PROFILES = ("colab_t4", "colab_a100", "local_low")


# =============================================================================
# LOGGER
# =============================================================================

class ScenographyLogger:
    """Logger structuré pour SCENOGRAPHY DOCK."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.logs: list = []

    def _record(self, level: str, msg: str) -> None:
        self.logs.append({
            "level": level,
            "message": msg,
            "timestamp": datetime.now().isoformat(),
        })

    def info(self, msg: str) -> None:
        print(f"[SCENOGRAPHY] {msg}")
        self._record("INFO", msg)

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[SCENOGRAPHY:DEBUG] {msg}")
            self._record("DEBUG", msg)

    def error(self, msg: str) -> None:
        print(f"[SCENOGRAPHY:ERROR] {msg}", file=sys.stderr)
        self._record("ERROR", msg)

    def success(self, msg: str) -> None:
        print(f"[SCENOGRAPHY:OK] {msg}")
        self._record("SUCCESS", msg)

    def warn(self, msg: str) -> None:
        print(f"[SCENOGRAPHY:WARN] {msg}")
        self._record("WARN", msg)

    def get_logs(self) -> list:
        return self.logs


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def check_blender(drive_root: Path, logger: ScenographyLogger, custom_path: str = None) -> str:
    """
    Vérifie que Blender 4.0 est disponible.

    Returns:
        Chemin vers l'exécutable Blender.
    """
    if custom_path:
        blender_path = Path(custom_path)
        if blender_path.exists():
            logger.success(f"Blender custom trouvé : {blender_path}")
            return str(blender_path)
        else:
            logger.error(f"Blender custom introuvable : {blender_path}")
            sys.exit(1)

    ai_models_path = drive_root / AI_MODELS_SUBDIR
    blender_path = ai_models_path / BLENDER_SUBDIR / "blender"

    if not blender_path.exists():
        logger.error(f"Blender 4.0 introuvable : {blender_path}")
        logger.info("Téléchargez Blender 4.0 Linux x64 portable et placez-le dans :")
        logger.info(f"  {ai_models_path / BLENDER_SUBDIR}/")
        sys.exit(1)

    logger.success("Blender 4.0 vérifié")
    return str(blender_path)


def validate_production_plan(plan_path: Path, logger: ScenographyLogger) -> dict:
    """
    Valide et charge le PRODUCTION_PLAN.JSON.

    Returns:
        Données du plan.
    """
    if not plan_path.exists():
        logger.error(f"PRODUCTION_PLAN.JSON introuvable : {plan_path}")
        sys.exit(1)

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide dans {plan_path} : {e}")
        sys.exit(1)

    if "scenes" not in plan:
        logger.warn("Aucune scène trouvée dans le plan, création structure vide")
        plan["scenes"] = []

    n_scenes = len(plan["scenes"])
    n_envs = sum(1 for s in plan["scenes"] if "environment" in s)
    logger.success(f"Plan validé : {n_scenes} scènes, {n_envs} environnements")
    return plan


def validate_vram_profile(profile: str, logger: ScenographyLogger) -> None:
    """Valide le profil VRAM via scene_schema."""
    if profile not in VALID_VRAM_PROFILES:
        logger.error(f"Profil VRAM inconnu : '{profile}'. Valides : {list(VALID_VRAM_PROFILES)}")
        sys.exit(1)
    logger.success(f"Profil VRAM : {profile}")


def resolve_hdri(map_raw_dir: Path, plan: dict, logger: ScenographyLogger) -> str:
    """
    Auto-détecte un HDRi dans IN_MAP_RAW.

    Returns:
        Chemin vers le premier HDRi trouvé, ou chaîne vide.
    """
    hdri_extensions = (".hdr", ".exr", ".hdri")
    candidates: list = []

    for ext in hdri_extensions:
        candidates.extend(map_raw_dir.glob(f"*{ext}"))
        candidates.extend(map_raw_dir.glob(f"**/*{ext}"))

    if candidates:
        hdri_path = str(candidates[0])
        logger.success(f"HDRi auto-détecté : {hdri_path}")
        return hdri_path

    logger.warn("Aucun HDRi trouvé dans IN_MAP_RAW — fallback couleur activé")
    return ""


# =============================================================================
# BLENDER EXECUTION
# =============================================================================

def run_blender_scenography(
    blender_path: str,
    production_plan: str,
    hdri_path: str,
    output_dir: str,
    scene_filter: list,
    exposure: float,
    vram_profile: str,
    depth_map_dir: str,
    semantic_masks: str,
    logger: ScenographyLogger,
    actor_blend_dir: str = "",
) -> bool:
    """
    Exécute Blender en mode headless avec layer_assembler.py.

    Returns:
        True si succès.
    """
    # VOID-FLUSH: purge memoire avant lancement Blender
    if _VOID_FLUSH_AVAILABLE:
        flush_result = flush_before_render(fregate_id="U03")
        logger.debug(f"VOID-FLUSH pre-render: {flush_result['status']} — {flush_result.get('actions', [])}")

    logger.info("Lancement Blender Tri-Layer Engine...")

    script_dir = Path(__file__).parent
    assembler_script = script_dir / "layer_assembler.py"

    if not assembler_script.exists():
        logger.error(f"Script assembler introuvable : {assembler_script}")
        return False

    scene_filter_json = json.dumps(scene_filter) if scene_filter else "[]"

    cmd = [
        blender_path,
        "--background",
        "--python", str(assembler_script),
        "--",
        "--production-plan", production_plan,
        "--output-dir", output_dir,
        "--scene-filter", scene_filter_json,
        "--exposure", str(exposure),
        "--vram-profile", vram_profile,
    ]

    if hdri_path:
        cmd.extend(["--hdri-path", hdri_path])
    if depth_map_dir:
        cmd.extend(["--depth-map-dir", depth_map_dir])
    if semantic_masks:
        cmd.extend(["--semantic-masks", semantic_masks])
    if actor_blend_dir:
        cmd.extend(["--actor-blend-dir", actor_blend_dir])

    logger.debug(f"Commande Blender : {' '.join(cmd[:8])}...")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.stdout:
        logger.debug(f"STDOUT (complet) :\n{result.stdout}")
    if result.stderr:
        logger.debug(f"STDERR (complet) :\n{result.stderr}")

    # Détection crash Python Blender : exit code 0 même en cas d'exception Python
    stderr_has_crash = result.stderr and "Traceback" in result.stderr
    if result.returncode != 0 or stderr_has_crash:
        logger.error(f"Blender crash — code={result.returncode}, traceback_détecté={bool(stderr_has_crash)}")
        if result.stderr:
            logger.error(f"STDERR :\n{result.stderr}")
        return False

    logger.success("Blender Tri-Layer Engine terminé")
    return True


# =============================================================================
# REPORT
# =============================================================================

def generate_report(
    output_dir: Path,
    plan: dict,
    scene_filter: list,
    success: bool,
    exposure: float,
    vram_profile: str,
    hdri_path: str,
    logger: ScenographyLogger,
) -> dict:
    """Génère scenography_report.json V2."""
    scenes_built = []
    for scene in plan.get("scenes", []):
        scene_id = scene.get("scene_id")
        if scene_filter and scene_id not in scene_filter:
            continue

        env = scene.get("environment", {})
        scene_info = {
            "scene_id": scene_id,
            "environment_id": env.get("environment_id", "unknown"),
            "layers_active": "dome,shadow,world_sync",
            "exposure_strength": exposure,
            "vram_profile": vram_profile,
            "hdri_used": bool(hdri_path),
            "output_file": f"environment_{scene_id}.blend" if success else None,
        }
        scenes_built.append(scene_info)

    assembler_results = []
    assembler_path = output_dir / "assembler_results.json"
    if assembler_path.exists():
        try:
            with open(assembler_path, "r", encoding="utf-8") as f:
                assembler_results = json.load(f)
        except Exception:
            pass

    schema_validations = []
    for ar in assembler_results:
        sr = ar.get("scene_report", {})
        schema_validations.append({
            "scene_id": ar.get("scene_id"),
            "collections_present": sr.get("collections", []),
            "objects_present": list(sr.get("objects", {}).keys()),
            "world_use_nodes": sr.get("world", {}).get("use_nodes", False),
            "world_strength": sr.get("world", {}).get("strength", 0),
        })

    report = {
        "version": SCENOGRAPHY_VERSION,
        "schema_version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "pipeline": "TRI-LAYER_V2",
        "summary": {
            "total_scenes": len(plan.get("scenes", [])),
            "scenes_built": len(scenes_built),
            "vram_profile": vram_profile,
            "exposure_strength": exposure,
            "hdri_resolved": bool(hdri_path),
            "layers_d1": ["dome", "shadow_catcher", "world_sync"],
            "layers_d2_stub": ["displacement_mesh"],
            "layers_d3_stub": ["pbr_swap", "glass_planes"],
        },
        "scenes": scenes_built,
        "schema_validations": schema_validations,
        "logs": logger.get_logs(),
    }

    report_path = output_dir / "scenography_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.success(f"Rapport V2 généré : {report_path}")
    return report


# =============================================================================
# OUTPUT COPY — U03 → U04
# =============================================================================

def copy_outputs_to_u04(
    output_dir: Path,
    drive_root: Path,
    plan: dict,
    logger: ScenographyLogger,
) -> int:
    """
    Copie et renomme les .blend produits par U03 vers 04_PHOTOGRAPHY_WING/IN_SCENE_REF.

    Mapping :
        OUT_PREMIUM_SCENE/environment_{scene_id}.blend
        → 04_PHOTOGRAPHY_WING/IN_SCENE_REF/scene_ready_{XX:02d}.blend

    Copie aussi assembler_results.json pour traçabilité U04.

    Returns:
        Nombre de fichiers copiés.
    """
    u04_scene_ref = drive_root / "04_PHOTOGRAPHY_WING" / "IN_SCENE_REF"
    u04_scene_ref.mkdir(parents=True, exist_ok=True)

    # Lire assembler_results pour connaître l'ordre des scènes
    assembler_path = output_dir / "assembler_results.json"
    assembler_results = []
    if assembler_path.exists():
        try:
            with open(assembler_path, "r", encoding="utf-8") as f:
                assembler_results = json.load(f)
        except Exception as e:
            logger.warn(f"Impossible de lire assembler_results.json : {e}")

    # Fallback : utiliser l'ordre des scènes du PRODUCTION_PLAN
    if not assembler_results:
        scenes = plan.get("scenes", [])
        assembler_results = [{"scene_id": s.get("scene_id")} for s in scenes]

    copied = 0
    for idx, result in enumerate(assembler_results, start=1):
        scene_id = result.get("scene_id")
        if not scene_id:
            continue

        src = output_dir / f"environment_{scene_id}.blend"
        if not src.exists():
            logger.warn(f"Fichier source introuvable, ignoré : {src.name}")
            continue

        dst = u04_scene_ref / f"scene_ready_{idx:02d}.blend"
        shutil.copy2(src, dst)
        logger.success(f"[U03→U04] {src.name} → {dst.name}")
        copied += 1

    # Copier assembler_results.json pour traçabilité U04
    if assembler_path.exists():
        shutil.copy2(assembler_path, u04_scene_ref / "assembler_results.json")
        logger.success("[U03→U04] assembler_results.json copié vers IN_SCENE_REF")

    logger.success(f"[U03→U04] {copied} scène(s) transférée(s) vers {u04_scene_ref}")
    return copied


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"SCENOGRAPHY DOCK — EXODUS Tri-Layer v{SCENOGRAPHY_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_03_SCENOGRAPHY.py --drive-root /content/drive/MyDrive/DRIVE_EXODUS_V2 \\
    --production-plan PRODUCTION_PLAN.JSON

  python EXO_03_SCENOGRAPHY.py --drive-root /path/to/drive \\
    --production-plan /path/to/plan.json \\
    --vram-profile colab_a100 \\
    --exposure 1.5 \\
    --scene-ids 1,2,3 -v
        """,
    )

    parser.add_argument("--drive-root", required=True,
                        help="Racine du Drive EXODUS")
    parser.add_argument("--production-plan", required=True,
                        help="PRODUCTION_PLAN.JSON du Cortex")
    parser.add_argument("--output-dir",
                        help="Dossier output (défaut : OUT_PREMIUM_SCENE/)")
    parser.add_argument("--scene-ids",
                        help="IDs des scènes à traiter (ex : 1,2,3) — défaut : toutes")
    parser.add_argument("--blender-path",
                        help="Chemin custom vers Blender")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Logs détaillés")
    parser.add_argument("--dry-run", action="store_true",
                        help="Valider les chemins sans exécuter")
    parser.add_argument("--vram-profile", default="colab_t4",
                        choices=["colab_t4", "colab_a100", "local_low"],
                        help="Profil VRAM (défaut : colab_t4)")
    parser.add_argument("--exposure", type=float, default=1.0,
                        help="World Sync strength (défaut : 1.0)")
    parser.add_argument("--actor-blend-dir",
                        help="Répertoire des ACTOR_*.blend (défaut : auto-détection dans U04/IN_SCENE_REF)")

    args = parser.parse_args()
    logger = ScenographyLogger(verbose=args.verbose)

    print("=" * 70)
    print("   FRÉGATE 03_SCENOGRAPHY — EXODUS TRI-LAYER SYSTEM V2")
    print(f"   Version {SCENOGRAPHY_VERSION}")
    print("=" * 70)

    # ATLAS: afficher session precedente si disponible
    if _ATLAS_AVAILABLE:
        _prev = SessionStore("U03")
        if _prev.get("last_run"):
            logger.info(f"ATLAS session U03 — dernier run: {_prev.get('last_run')} | "
                        f"drive_root: {_prev.get('drive_root', '?')} | "
                        f"vram: {_prev.get('vram_profile', '?')}")

    drive_root = Path(args.drive_root)
    unit_root = drive_root / "03_SCENOGRAPHY_DOCK"

    cortex_json_dir = resolve_input(unit_root / "IN_CORTEX_JSON")
    map_raw_dir = resolve_input(unit_root / "IN_MAP_RAW")

    plan_path = Path(args.production_plan)
    if not plan_path.is_absolute():
        plan_path = cortex_json_dir / args.production_plan

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = unit_root / "OUT_PREMIUM_SCENE"

    scene_filter: list = []
    if args.scene_ids:
        scene_filter = [int(x.strip()) for x in args.scene_ids.split(",")]

    logger.info(f"Drive Root : {drive_root}")
    logger.info(f"Production Plan : {plan_path}")
    logger.info(f"Output Dir : {output_dir}")
    logger.info(f"VRAM Profile : {args.vram_profile}")
    logger.info(f"Exposure : {args.exposure}")
    if scene_filter:
        logger.info(f"Scene Filter : {scene_filter}")

    blender_path = check_blender(drive_root, logger, args.blender_path)
    plan = validate_production_plan(plan_path, logger)
    validate_vram_profile(args.vram_profile, logger)

    hdri_path = resolve_hdri(map_raw_dir, plan, logger)

    depth_map_subdir = map_raw_dir / "DEPTH_MAP"
    if depth_map_subdir.exists() and any(depth_map_subdir.glob("*.png")):
        depth_map_dir = str(depth_map_subdir)
        logger.success(f"Depth maps trouvées : {depth_map_subdir}")
    elif map_raw_dir.exists() and any(map_raw_dir.glob("*.png")):
        depth_map_dir = str(map_raw_dir)
        logger.success(f"Depth maps trouvées (racine) : {map_raw_dir}")
    else:
        depth_map_dir = ""
        logger.warn("Aucune depth map trouvée — displacement mesh sans texture")
    semantic_masks = ""
    sm_path = map_raw_dir / "semantic_masks.json"
    if sm_path.exists():
        semantic_masks = str(sm_path)
        logger.success(f"Semantic masks trouvé : {sm_path}")
    else:
        logger.debug("semantic_masks.json non trouvé (D3 futur)")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-détection du répertoire actor blend
    actor_blend_dir = ""
    if args.actor_blend_dir:
        actor_blend_dir = args.actor_blend_dir
        logger.success(f"Actor blend dir (manuel) : {actor_blend_dir}")
    else:
        # Convention : U04/IN_SCENE_REF contient les ACTOR_*.blend
        u04_scene_ref = drive_root / "04_PHOTOGRAPHY_WING" / "IN_SCENE_REF"
        if u04_scene_ref.exists() and list(u04_scene_ref.glob("ACTOR_*.blend")):
            actor_blend_dir = str(u04_scene_ref)
            logger.success(f"Actor blend dir auto-détecté : {actor_blend_dir}")
        else:
            logger.warn("Aucun ACTOR_*.blend trouvé — scènes assemblées sans acteur")

    logger.success("Configuration validée")

    if args.dry_run:
        logger.info("Mode dry-run : arrêt avant traitement")
        print(f"\n{'='*70}")
        print("  DRY-RUN — Résumé")
        print(f"{'='*70}")
        print(f"  Scènes        : {len(plan.get('scenes', []))}")
        print(f"  VRAM Profile   : {args.vram_profile}")
        print(f"  Exposure       : {args.exposure}")
        print(f"  HDRi           : {hdri_path or 'fallback'}")
        print(f"  Depth maps     : {depth_map_dir or 'N/A'}")
        print(f"  Semantic masks : {semantic_masks or 'N/A'}")
        if scene_filter:
            print(f"  Scènes filtrées: {scene_filter}")
        print(f"{'='*70}")
        sys.exit(0)

    success = run_blender_scenography(
        blender_path=blender_path,
        production_plan=str(plan_path),
        hdri_path=hdri_path,
        output_dir=str(output_dir),
        scene_filter=scene_filter,
        exposure=args.exposure,
        vram_profile=args.vram_profile,
        depth_map_dir=depth_map_dir,
        semantic_masks=semantic_masks,
        logger=logger,
        actor_blend_dir=actor_blend_dir,
    )

    report = generate_report(
        output_dir=output_dir,
        plan=plan,
        scene_filter=scene_filter,
        success=success,
        exposure=args.exposure,
        vram_profile=args.vram_profile,
        hdri_path=hdri_path,
        logger=logger,
    )

    if not success:
        logger.error("Construction Tri-Layer échouée")
        sys.exit(1)

    # ATLAS: sauvegarder etat session apres succes
    if _ATLAS_AVAILABLE:
        SessionStore("U03").update({
            "drive_root": str(drive_root),
            "output_dir": str(output_dir),
            "vram_profile": args.vram_profile,
            "exposure": args.exposure,
            "hdri_path": hdri_path,
            "scenes_total": len(plan.get("scenes", [])),
            "last_run": datetime.now().isoformat(),
        }).save()
        logger.info("ATLAS: session U03 sauvegardee")

    # Copie et renommage outputs U03 → U04
    copy_outputs_to_u04(
        output_dir=output_dir,
        drive_root=drive_root,
        plan=plan,
        logger=logger,
    )

    print(f"\n{'='*70}")
    logger.success("CONSTRUCTION TRI-LAYER TERMINÉE")
    print(f"  Pipeline  : TRI-LAYER V2 (D1 — Dome + Shadow + World Sync)")
    print(f"  .blend    : {output_dir}/environment_*.blend")
    print(f"  Rapport   : {output_dir}/scenography_report.json")
    print(f"  VRAM      : {args.vram_profile}")
    print(f"  Exposure  : {args.exposure}")
    print(f"{'='*70}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


