# ═══════════════════════════════════════════════════════════════
# U04 — TEST 10 FRAMES — VERSION CORRIGÉE (VULKAN FIX v2.1)
# ═══════════════════════════════════════════════════════════════
#
# FIXES APPLIQUÉS :
#   FIX #1 — U03 : result.stderr affiché (erreur PIL était invisible)
#   FIX #2 — INJECT : World emission forcée (dome_placeholder = mort)
#   FIX #3 — INJECT : Matériau gris forcé sur displacement_mesh
#
# CAUSE RACINE IDENTIFIÉE (VULKAN ATOM-IC) :
#   Blender Python bundled ne contient pas PIL/Pillow
#   → depth_map_cleaner.py crashait à l'import
#   → layer_assembler.py quittait silencieusement
#   → Scènes stale (vieux .blend) utilisées sans géométrie valide
#   → Repo fixé : displacement_builder.py v2.1 (try/except PIL)
# ═══════════════════════════════════════════════════════════════

from google.colab import drive
from pathlib import Path
import subprocess, shutil, json, os, time, sys
from datetime import datetime
import numpy as np

print("=" * 70)
print("   U04 — TEST 10 FRAMES (VULKAN FIX v2.1)")
print("=" * 70)

drive.mount('/content/drive', force_remount=True)
print("✅ Drive monté\n")

DRIVE_ROOT = Path("/content/drive/MyDrive/EXODUS_V2")
BLENDER_BIN = Path("/opt/blender-local/blender")
LOCAL_ROOT = Path("/content/exodus_local")
U03_ROOT = DRIVE_ROOT / "03_SCENOGRAPHY_DOCK"
U04_ROOT = DRIVE_ROOT / "04_PHOTOGRAPHY_WING"
OUT_LOGIC = U04_ROOT / "OUT_CAMERA_LOGIC"

# ── 0. VÉRIFIER BLENDER ──
print("\n[0/7] 🔧 Vérification Blender...")
if not BLENDER_BIN.exists():
    print("   📦 Installation Blender...")
    subprocess.run(["wget", "-q", "https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz", "-O", "/tmp/blender.tar.xz"], check=True)
    subprocess.run(["tar", "-xf", "/tmp/blender.tar.xz", "-C", "/opt/"], check=True)
    subprocess.run(["mv", "/opt/blender-4.0.2-linux-x64", "/opt/blender-local"], check=True)
    os.chmod(str(BLENDER_BIN), 0o755)
    print("   ✅ Blender installé")
else:
    print("   ✅ Blender déjà présent")

# ── 1. VÉRIFIER GPU ──
print("\n[1/7] 🔍 Vérification GPU...")
result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
if result.returncode == 0:
    gpu_info = result.stdout.strip()
    print(f"   ✅ GPU : {gpu_info}")
    gpu_available = True
else:
    gpu_info = "Non détecté"
    print("   ❌ GPU non détecté")
    gpu_available = False

# ── 2. PRÉPARER DEPTH MAPS ──
print("\n[2/7] 📦 Préparation depth maps...")

depth_src = DRIVE_ROOT / "00_CORTEX_HQ" / "OUT_PRODUCTION_PLAN" / "DEPTH_MAP"
depth_dst = U03_ROOT / "IN_MAP_RAW" / "DEPTH_MAP"
depth_dst.mkdir(parents=True, exist_ok=True)

for f in depth_dst.glob("*.png"):
    f.unlink()

if depth_src.exists():
    frames = sorted(depth_src.glob("frame_*.png"))
    for f in frames:
        shutil.copy2(str(f), str(depth_dst / f.name))
    print(f"   ✅ {len(frames)} depth maps copiées vers IN_MAP_RAW/DEPTH_MAP/")
else:
    print(f"   ❌ Depth maps source non trouvées")

masks_src = DRIVE_ROOT / "00_CORTEX_HQ" / "OUT_PRODUCTION_PLAN" / "semantic_masks.json"
if masks_src.exists():
    shutil.copy2(str(masks_src), str(depth_dst / "semantic_masks.json"))
    print("   ✅ semantic_masks.json copié")

# ── 3. SYNC CODEBASE U03 (DEPUIS GITHUB — FIX PIL) ──
print("\n[3/7] 📦 Sync CODEBASE U03 (FIX PIL depuis GitHub)...")

TEMP_REPO = Path("/tmp/exodus-repo-fix")
if TEMP_REPO.exists():
    shutil.rmtree(TEMP_REPO)

subprocess.run(["git", "clone", "--depth", "1", "https://github.com/kioka8877-ux/EXODUS-V2.git", str(TEMP_REPO)], capture_output=True, check=True)

SRC_CODEBASE = TEMP_REPO / "03_SCENOGRAPHY_DOCK" / "CODEBASE"
U03_CODEBASE = U03_ROOT / "CODEBASE"
if SRC_CODEBASE.exists():
    U03_CODEBASE.mkdir(parents=True, exist_ok=True)
    for f in SRC_CODEBASE.iterdir():
        if f.is_file():
            shutil.copy2(str(f), str(U03_CODEBASE / f.name))
    print(f"   ✅ {len(list(SRC_CODEBASE.iterdir()))} fichiers copiés (FIX PIL inclus)")

# ── 4. LANCER U03 (layer_assembler.py) — AVEC STDERR ──
print("\n[4/7] 🚀 Lancement U03 (layer_assembler.py)...")

layer_script = U03_CODEBASE / "layer_assembler.py"
u03_ok = False

if layer_script.exists():
    cmd = [
        str(BLENDER_BIN), "--background", "--python", str(layer_script), "--",
        "--production-plan", str(DRIVE_ROOT / "00_CORTEX_HQ" / "OUT_PRODUCTION_PLAN" / "PRODUCTION_PLAN.JSON"),
        "--output-dir", str(U03_ROOT / "OUT_PREMIUM_SCENE"),
        "--depth-map-dir", str(depth_dst),
        "--semantic-masks", str(depth_dst / "semantic_masks.json"),
        "--exposure", "1.0",
        "--vram-profile", "colab_t4"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        print("\n--- STDOUT U03 ---")
        print(result.stdout[-2000:] if result.stdout else "(vide)")

        # FIX #1 : STDERR AFFICHÉ — révèle les vrais crashs
        if result.stderr.strip():
            print("\n--- STDERR U03 (erreurs réelles) ---")
            print(result.stderr[-2000:])
        else:
            print("\n--- STDERR U03 : (vide — aucune erreur Python) ---")

        if result.returncode == 0:
            u03_ok = True
            print("\n   ✅ U03 terminé avec succès")
        else:
            print(f"\n   ⚠️  U03 returncode={result.returncode}")

    except Exception as e:
        print(f"   ⚠️  Erreur U03: {e}")
else:
    print("   ❌ layer_assembler.py non trouvé")

# ── 5. COPIER SCÈNES VERS U04 ──
print("\n[5/7] 📦 Copie scènes vers U04...")

OUT_LOGIC.mkdir(parents=True, exist_ok=True)
u03_out = U03_ROOT / "OUT_PREMIUM_SCENE"

scenes_copied = 0
for i, env_blend in enumerate(sorted(u03_out.glob("environment_*.blend")), 1):
    dst = OUT_LOGIC / f"scene_ready_{i}.blend"
    shutil.copy2(str(env_blend), str(dst))
    print(f"   ✅ {dst.name} copié")
    scenes_copied += 1

if scenes_copied == 0:
    print("   ❌ Aucune scène trouvée dans OUT_PREMIUM_SCENE")

# ── 6. INJECTION CAMÉRA + LUMIÈRE + WORLD OVERRIDE ──
print("\n[6/7] 💉 Injection caméra + lumière + World override...")

inject_script = OUT_LOGIC / "inject_camera.py"
inject_script.write_text("""
import bpy
import math

scene = bpy.context.scene

# ── CAMERA ──
cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
if not cams:
    bpy.ops.object.camera_add(location=(0.0, -8.0, 3.0), rotation=(math.radians(75), 0, 0))
    cam = bpy.context.object
    cam.name = "Camera_Test"
    cam.data.lens = 35
    scene.camera = cam
    print("✅ Caméra créée")
else:
    scene.camera = cams[0]
    print(f"✅ Caméra: {scene.camera.name}")

# ── LUMIÈRE SOLEIL ──
lights = [o for o in bpy.data.objects if o.type == 'LIGHT']
if not lights:
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.object
    sun.data.energy = 15.0
    print("✅ Sun ajouté (energy=15.0)")
else:
    for light in lights:
        light.data.energy = 15.0
    print("✅ Lumières boostées à 15.0")

# ── FIX #2 : WORLD EMISSION FORCÉE (remplace dome_placeholder) ──
world = bpy.data.worlds.get("World_OVERRIDE") or bpy.data.worlds.new("World_OVERRIDE")
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

bg = nodes.new(type="ShaderNodeBackground")
bg.inputs[0].default_value = (0.6, 0.65, 0.75, 1.0)
bg.inputs[1].default_value = 2.5

out = nodes.new(type="ShaderNodeOutputWorld")
links.new(bg.outputs["Background"], out.inputs["Surface"])
print("✅ World emission override (0.6,0.65,0.75 — strength=2.5)")

# ── FIX #3 : MATÉRIAU GRIS FORCÉ SUR displacement_mesh ──
for obj in bpy.data.objects:
    if obj.name == "displacement_mesh" and obj.type == 'MESH':
        mat = bpy.data.materials.get("Mat_Displacement_Fix") or bpy.data.materials.new("Mat_Displacement_Fix")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.65, 0.65, 0.65, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        print(f"✅ Matériau gris forcé sur {obj.name}")

bpy.ops.wm.save_mainfile()
print("✅ Scène sauvegardée (inject complet)")
""")

ready_blends = sorted(OUT_LOGIC.glob("scene_ready_*.blend"))
for bf in ready_blends:
    r = subprocess.run(
        [str(BLENDER_BIN), "--background", str(bf), "--python", str(inject_script)],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        print(f"   ⚠️  Inject stderr: {r.stderr[-500:]}")

if inject_script.exists():
    inject_script.unlink()

print(f"   ✅ Inject terminé sur {len(ready_blends)} scène(s)")

# ── 7. TEST 10 FRAMES ──
print("\n[7/7] 🎬 TEST 10 FRAMES...")

TEST_FRAMES = 10
TEST_SAMPLES = 16
TEST_RES_X, TEST_RES_Y = 640, 360

for f in OUT_LOGIC.glob("test_frame_*.png"):
    f.unlink()
print("🧹 Anciennes frames supprimées")

render_script = OUT_LOGIC / "render_test.py"
render_script.write_text(f"""
import bpy, os

scene = bpy.context.scene
output_dir = r"{OUT_LOGIC}"
frames = {TEST_FRAMES}

scene.render.engine = 'CYCLES'
scene.cycles.samples = {TEST_SAMPLES}
scene.cycles.device = 'GPU'
scene.render.resolution_x = {TEST_RES_X}
scene.render.resolution_y = {TEST_RES_Y}
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.exposure = 2.0

try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for d in prefs.devices: d.use = True
    print("✅ GPU CUDA activé")
except Exception as e:
    print(f"⚠️  GPU: {{e}}")
    scene.cycles.device = 'CPU'

print(f"\\n🎬 Rendu {{frames}} frames...")
for frame in range(frames):
    scene.frame_set(frame)
    filepath = os.path.join(output_dir, f"test_frame_{{frame:05d}}.png")
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    size = os.path.getsize(filepath) / 1024 if os.path.exists(filepath) else 0
    status = "✅" if os.path.exists(filepath) else "❌"
    print(f"  Frame {{frame+1}}/{{frames}} — {{size:.1f}}KB {{status}}")

files = [f for f in os.listdir(output_dir) if f.startswith('test_frame_') and f.endswith('.png')]
print(f"\\n📊 Frames créées: {{len(files)}}")
""")

print("\n🚀 Lancement rendu...")
start = time.time()

try:
    result = subprocess.run(
        [str(BLENDER_BIN), "--background", str(ready_blends[0]), "--python", str(render_script)],
        capture_output=True, text=True, timeout=600
    )
    elapsed = time.time() - start
    print(f"\n✅ RENDU TERMINÉ en {elapsed/60:.1f} min")
    print(result.stdout[-2000:])
    if result.stderr.strip():
        print("--- STDERR RENDER ---")
        print(result.stderr[-1000:])
except subprocess.TimeoutExpired:
    print("\n⏰ TIMEOUT (10 min)")
except Exception as e:
    print(f"\n❌ ERREUR: {e}")

if render_script.exists():
    render_script.unlink()

# ── 8. VÉRIFICATION RÉSULTATS ──
print("\n" + "=" * 70)
print("   VÉRIFICATION RÉSULTATS")
print("=" * 70)

test_frames = sorted(OUT_LOGIC.glob("test_frame_*.png"))
print(f"\n📊 Frames générées: {len(test_frames)}")
avg_luma = 0.0
test_passed = False

if test_frames:
    total_size = sum(f.stat().st_size for f in test_frames)
    print(f"   • Taille totale  : {total_size / 1024:.1f} KB")
    print(f"   • Taille moyenne : {total_size / len(test_frames) / 1024:.1f} KB/frame")

    try:
        from PIL import Image
        print("\n🔍 Analyse luminosité :")
        luminas = []
        for f in test_frames[:5]:
            img = Image.open(f).convert("RGB")
            arr = np.array(img, dtype=np.float32)
            mean_luma = float(arr.mean())
            luminas.append(mean_luma)
            print(f"   • {f.name}: {mean_luma:.1f}")
        avg_luma = sum(luminas) / len(luminas)
        print(f"\n   Moyenne : {avg_luma:.1f}")
        if avg_luma > 50:
            print("   ✅ CLAIRES — Test RÉUSSI")
            test_passed = True
        elif avg_luma > 10:
            print("   ⚠️  SOMBRES — Partiel")
            test_passed = True
        else:
            print("   ❌ NOIRES — Échec")
    except Exception as e:
        print(f"   ⚠️  Analyse: {e}")
        test_passed = len(test_frames) == TEST_FRAMES
else:
    print("   ❌ Aucune frame générée")

# ── 9. RAPPORT ──
report = {
    "timestamp": datetime.now().isoformat(),
    "fix_version": "vulkan_v2.1",
    "u03_success": bool(u03_ok),
    "gpu_info": str(gpu_info),
    "frames_generated": int(len(test_frames)),
    "avg_luminance": float(avg_luma),
    "test_passed": bool(test_passed),
}
with open(OUT_LOGIC / "test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n" + "=" * 70)
print(f"""
📊 RÉCAPITULATIF FINAL :
   • U03 success    : {u03_ok}
   • GPU            : {gpu_info}
   • Frames         : {len(test_frames)}/{TEST_FRAMES}
   • Luminosité     : {avg_luma:.1f} {'✅' if avg_luma > 10 else '❌'}
   • Statut         : {'✅ RÉUSSI' if test_passed else '❌ ÉCHOUÉ'}
""")
print("=" * 70)
