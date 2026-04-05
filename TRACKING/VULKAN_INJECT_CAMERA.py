# ═══════════════════════════════════════════════════════════════════════
# VULKAN_FORGE — CAMERA INJECTION + RENDER U04-B
# Fix ID  : VULKAN_CAMERA_FIX_v1
# Tech-Pretre : VULKAN_FORGE
# Arme utilisee : ARSENAL/scripts/inject_camera_cinematic.py
#               + WEAPONS/hook_dispatcher.py
# Role    : Injecte camera dans les scene_ready_*.blend puis lance DARKROOM
# ═══════════════════════════════════════════════════════════════════════

from google.colab import drive
from pathlib import Path
import subprocess, shutil, json, os, sys, tempfile
from datetime import datetime

print("=" * 70)
print("   VULKAN_FORGE — CAMERA INJECTION PROTOCOL — VULKAN_CAMERA_FIX_v1")
print("=" * 70)

drive.mount("/content/drive", force_remount=True)
print("Drive monte")

# ── PATHS ──
DRIVE_ROOT   = Path("/content/drive/MyDrive/EXODUS_V2_FRESH")
REPO_ROOT    = Path("/tmp/exodus-repo-vulkan")
BLENDER_BIN  = Path("/opt/blender-local/blender")
U04_ROOT     = DRIVE_ROOT / "04_PHOTOGRAPHY_WING"
OUT_LOGIC    = U04_ROOT / "OUT_CAMERA_LOGIC"

OUT_LOGIC.mkdir(parents=True, exist_ok=True)

# ── 0. BLENDER ──
print("\n[0/4] Verification Blender...")
if not BLENDER_BIN.exists():
    print("   Installation Blender 4.0.2...")
    subprocess.run(["wget", "-q",
        "https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz",
        "-O", "/tmp/blender.tar.xz"], check=True)
    subprocess.run(["tar", "-xf", "/tmp/blender.tar.xz", "-C", "/opt/"], check=True)
    subprocess.run(["mv", "/opt/blender-4.0.2-linux-x64", "/opt/blender-local"], check=True)
    os.chmod(str(BLENDER_BIN), 0o755)
    print("   Blender installe")
else:
    print("   Blender OK")

# ── 1. SYNC VULKAN_FORGE DEPUIS GITHUB ──
print("\n[1/4] Sync VULKAN_FORGE depuis GitHub...")
if REPO_ROOT.exists():
    shutil.rmtree(REPO_ROOT)
subprocess.run(["git", "clone", "--depth", "1",
    "https://github.com/kioka8877-ux/EXODUS-V2.git", str(REPO_ROOT)],
    capture_output=True, check=True)

INJECT_SCRIPT = REPO_ROOT / "VULKAN_FORGE" / "ARSENAL" / "scripts" / "inject_camera_cinematic.py"
HOOK_DISPATCHER = REPO_ROOT / "VULKAN_FORGE" / "WEAPONS" / "hook_dispatcher.py"

if not INJECT_SCRIPT.exists():
    raise FileNotFoundError(f"inject_camera_cinematic.py non trouve : {INJECT_SCRIPT}")
print(f"   inject_camera_cinematic.py : OK")
print(f"   hook_dispatcher.py : {'OK' if HOOK_DISPATCHER.exists() else 'absent'}")

# ── 2. DETECTION DES BLENDS ──
print("\n[2/4] Detection scene_ready_*.blend...")

blends = sorted(OUT_LOGIC.glob("scene_ready_*.blend"))
if not blends:
    # Copier depuis U03 si absent
    u03_out = DRIVE_ROOT / "03_SCENOGRAPHY_DOCK" / "OUT_PREMIUM_SCENE"
    env_blends = sorted(u03_out.glob("environment_*.blend")) if u03_out.exists() else []
    if env_blends:
        for i, src in enumerate(env_blends, 1):
            dst = OUT_LOGIC / f"scene_ready_{i:02d}.blend"
            shutil.copy2(str(src), str(dst))
            print(f"   Copie U03 -> {dst.name}")
        blends = sorted(OUT_LOGIC.glob("scene_ready_*.blend"))
    else:
        print("   ERREUR : Aucun .blend source trouve (U03 OUT_PREMIUM_SCENE vide)")
        raise FileNotFoundError("Aucun .blend disponible pour injection")

print(f"   {len(blends)} blend(s) a traiter")

# ── 3. INJECTION CAMERA + LUMIERE DANS CHAQUE BLEND ──
print("\n[3/4] INJECTION CAMERA + LUMIERE (VULKAN_CAMERA_FIX_v1)...")

inject_results = []
all_ok = True

for blend in blends:
    print(f"\n   >> {blend.name}")
    cmd = [
        str(BLENDER_BIN), "--background", str(blend),
        "--python", str(INJECT_SCRIPT)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    stdout_lines = [l for l in result.stdout.splitlines() if "[INJECT_CAMERA]" in l]
    for line in stdout_lines:
        print(f"      {line}")
    
    if result.returncode != 0:
        print(f"      STDERR : {result.stderr[-300:]}")
        all_ok = False
        inject_results.append({"blend": blend.name, "status": "ERROR"})
    else:
        inject_results.append({"blend": blend.name, "status": "OK"})
        print(f"      status : OK")

# ── HOOK : fix.applied ──
if HOOK_DISPATCHER.exists():
    payload = json.dumps({
        "fix_id": "VULKAN_CAMERA_FIX_v1",
        "fregate": "U04",
        "blends_treated": len(blends),
        "all_ok": all_ok
    })
    r = subprocess.run(
        [sys.executable, str(HOOK_DISPATCHER), "fix.applied", payload],
        capture_output=True, text=True, cwd=str(REPO_ROOT / "VULKAN_FORGE")
    )
    if "[HOOK]" in r.stdout:
        print(f"\n   {r.stdout.strip().splitlines()[-1]}")

# ── 4. LANCEMENT DARKROOM ──
print("\n[4/4] LANCEMENT DARKROOM (EXO_04_DARKROOM.py)...")

U04_CODEBASE = DRIVE_ROOT / "04_PHOTOGRAPHY_WING" / "CODEBASE"
DARKROOM_PY = U04_CODEBASE / "EXO_04_DARKROOM.py"

if not DARKROOM_PY.exists():
    # Sync depuis repo
    src = REPO_ROOT / "04_PHOTOGRAPHY_WING" / "CODEBASE" / "EXO_04_DARKROOM.py"
    if src.exists():
        U04_CODEBASE.mkdir(parents=True, exist_ok=True)
        for f in (REPO_ROOT / "04_PHOTOGRAPHY_WING" / "CODEBASE").iterdir():
            if f.is_file():
                shutil.copy2(str(f), str(U04_CODEBASE / f.name))
        print(f"   Codebase U04 synced depuis GitHub")

cmd_darkroom = [
    sys.executable, str(DARKROOM_PY),
    "--drive-root", str(DRIVE_ROOT),
    "--project-name", "EXODUS_TEST_01",
    "--blender-path", str(BLENDER_BIN),
    "--chunk-size", "10",
    "--preset", "preview",
    "--resume", "-v"
]

print(f"   Commande : {" ".join(cmd_darkroom[:4])} ...")
import time
start = time.time()
result = subprocess.run(cmd_darkroom, capture_output=True, text=True, timeout=900)
elapsed = time.time() - start

print(f"\n   Duree : {elapsed/60:.1f} min")
print(f"   Code retour : {result.returncode}")

important_lines = [l for l in result.stdout.splitlines()
    if any(k in l for k in ["[DARKROOM]", "Frame", "Error", "OK", "render"])]
for line in important_lines[-30:]:
    print(f"   {line}")

if result.stderr.strip():
    print("\n   STDERR :")
    for line in result.stderr.splitlines()[-10:]:
        print(f"   {line}")

# ── RAPPORT FINAL ──
frames = sorted(OUT_LOGIC.glob("render_*.png"))
print("\n" + "=" * 70)
report = {
    "timestamp": datetime.now().isoformat(),
    "fix_id": "VULKAN_CAMERA_FIX_v1",
    "inject_results": inject_results,
    "darkroom_returncode": result.returncode,
    "frames_rendered": len(frames),
    "elapsed_min": round(elapsed / 60, 2),
    "status": "SUCCESS" if len(frames) > 0 else "PARTIAL" if all_ok else "FAILED"
}
report_path = OUT_LOGIC / "vulkan_camera_fix_report.json"
report_path.write_text(json.dumps(report, indent=2))

print(f"""
   RAPPORT VULKAN_CAMERA_FIX_v1 :
   • Blends traites  : {len(blends)}
   • Inject OK       : {all_ok}
   • Frames rendues  : {len(frames)}
   • Statut          : {report["status"]}
   • Rapport         : {report_path.name}
""")
print("=" * 70)
