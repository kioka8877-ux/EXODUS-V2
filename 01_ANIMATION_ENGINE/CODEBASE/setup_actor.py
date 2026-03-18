#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     EXODUS V2 — SETUP ACTOR — Conversion avatar.glb → actor_arkit.blend    ║
║     Importe un GLB et ajoute les 52 blendshapes ARKit manquants.            ║
║     Usage: python setup_actor.py --drive-root /content/drive/MyDrive/EXODUS_V2
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import subprocess
import sys
import argparse
import json
import os
from pathlib import Path

ARKIT_52 = [
    "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight", "eyeSquintLeft", "eyeSquintRight",
    "eyeWideLeft", "eyeWideRight",
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    "noseSneerLeft", "noseSneerRight",
    "tongueOut",
]

BLENDER_SCRIPT = '''
import bpy, sys, json
from pathlib import Path

argv = sys.argv[sys.argv.index("--") + 1:]
glb_path   = argv[0]
blend_path = argv[1]
arkit_json = argv[2]

ARKIT_52 = json.loads(Path(arkit_json).read_text())

EXCLUDE_KW = ["handle", "hair", "accessory", "hat", "tool", "weapon"]

def is_excluded(name):
    n = name.lower()
    return any(kw in n for kw in EXCLUDE_KW)

# Import GLB
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_path)

# Trouver le mesh principal (plus de vertices, pas accessoire)
meshes = [o for o in bpy.data.objects if o.type == "MESH" and not is_excluded(o.name)]
if not meshes:
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]

if not meshes:
    print("[SETUP:ERROR] Aucun mesh dans le GLB")
    sys.exit(1)

obj = max(meshes, key=lambda m: len(m.data.vertices))
print(f"[SETUP:OK] Mesh principal: {obj.name} ({len(obj.data.vertices)} vertices)")

# Ajouter Basis si absent
if not obj.data.shape_keys:
    obj.shape_key_add(name="Basis")
    print("[SETUP:OK] Basis créé")

existing = {k.name for k in obj.data.shape_keys.key_blocks}
added = 0
for name in ARKIT_52:
    if name not in existing:
        obj.shape_key_add(name=name)
        added += 1

print(f"[SETUP:OK] {added} blendshapes ARKit ajoutés ({len(existing)-1} déjà présents)")

bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"[SETUP:OK] Sauvegardé: {blend_path}")
'''


def main():
    parser = argparse.ArgumentParser(description="EXODUS V2 — Setup Actor ARKit")
    parser.add_argument("--drive-root", required=True)
    parser.add_argument("--glb", default=None, help="Chemin vers avatar.glb (défaut: 01_ANIMATION_ENGINE/avatar.glb)")
    parser.add_argument("--output", default=None, help="Chemin output .blend (défaut: 01_ANIMATION_ENGINE/actor_arkit.blend)")
    parser.add_argument("--blender-path", default=None)
    args = parser.parse_args()

    drive_root = Path(args.drive_root)
    u01_root = drive_root / "01_ANIMATION_ENGINE"

    glb_path   = Path(args.glb)   if args.glb    else u01_root / "avatar.glb"
    blend_path = Path(args.output) if args.output else u01_root / "actor_arkit.blend"

    # Trouver Blender
    blender = (
        args.blender_path or
        os.environ.get("BLENDER_PATH") or
        str(drive_root / "EXODUS_AI_MODELS" / "blender-4.0.0-linux-x64" / "blender")
    )

    print("═" * 60)
    print("  EXODUS V2 — SETUP ACTOR ARKit")
    print("═" * 60)

    if not glb_path.exists():
        print(f"❌ GLB non trouvé: {glb_path}")
        print("   Déposez votre avatar.glb dans 01_ANIMATION_ENGINE/")
        sys.exit(1)

    if blend_path.exists():
        print(f"⏭️  actor_arkit.blend déjà présent: {blend_path}")
        sys.exit(0)

    if not Path(blender).exists():
        print(f"❌ Blender non trouvé: {blender}")
        print("   Lancez d'abord setup_blender.py")
        sys.exit(1)

    # Écrire script Blender et liste ARKit
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(BLENDER_SCRIPT)
        script_path = f.name

    arkit_tmp = blend_path.parent / "_arkit_52.json"
    arkit_tmp.write_text(json.dumps(ARKIT_52))

    print(f"🔧 Conversion: {glb_path.name} → {blend_path.name}")
    result = subprocess.run(
        [blender, "--background", "--python", script_path,
         "--", str(glb_path), str(blend_path), str(arkit_tmp)],
        capture_output=True, text=True
    )

    # Cleanup
    Path(script_path).unlink(missing_ok=True)
    arkit_tmp.unlink(missing_ok=True)

    # Résultat
    for line in result.stdout.splitlines():
        if "[SETUP:" in line:
            print(f"  {line}")

    if result.returncode == 0 and blend_path.exists():
        size_mb = blend_path.stat().st_size / 1024 / 1024
        print(f"\n✅ actor_arkit.blend créé ({size_mb:.2f} MB)")
        print(f"   → {blend_path}")
    else:
        print(f"❌ Échec conversion")
        if result.stderr:
            print(result.stderr[-2000:])
        sys.exit(1)

    print("═" * 60)


if __name__ == "__main__":
    main()
