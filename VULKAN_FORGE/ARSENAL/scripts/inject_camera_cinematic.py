"""
ARSENAL SCRIPT — inject_camera_cinematic
Fregate : U04 — PHOTOGRAPHY_WING
Fix ID  : VULKAN_CAMERA_FIX_v1
Role    : Injecte une camera cinematique dans un .blend si absente
          Appele par Blender headless AVANT DARKROOM

Usage (via Blender headless) :
    blender --background scene.blend --python inject_camera_cinematic.py

Specs camera :
    Position : (0, -8, 4)
    Rotation : (75deg, 0, 0)
    Focal    : 35mm
    DOF      : f/2.8, focus 6.0m, 6 blades
    Sun      : energy=15 si absent
    Point    : energy=500 si absent
"""

import bpy
import math
import json


def log(msg):
    print(f"[INJECT_CAMERA] {msg}")


def inject_camera(scene=None):
    if scene is None:
        scene = bpy.context.scene

    existing = [obj for obj in scene.objects if obj.type == "CAMERA"]
    if existing:
        scene.camera = existing[0]
        log(f"OK — camera existante : {existing[0].name}")
        return False

    bpy.ops.object.camera_add(
        location=(0.0, -8.0, 4.0),
        rotation=(math.radians(75), 0.0, 0.0)
    )
    cam_obj = bpy.context.active_object
    cam_obj.name = "camera_main"
    cam = cam_obj.data
    cam.name = "camera_main_data"
    cam.lens = 35.0
    cam.sensor_width = 36.0
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 2.8
    cam.dof.aperture_blades = 6
    cam.dof.focus_distance = 6.0
    scene.camera = cam_obj

    log("APPLIED — camera_main : pos=(0,-8,4), 35mm, DOF f/2.8, 6 blades")
    return True


def inject_lighting(scene=None):
    if scene is None:
        scene = bpy.context.scene

    lights = [obj for obj in scene.objects if obj.type == "LIGHT"]
    if lights:
        for light in lights:
            if light.data.energy < 5.0:
                light.data.energy = 15.0
                log(f"Lumiere boostee : {light.name} -> energy=15")
        return False

    bpy.ops.object.light_add(type="SUN", location=(5.0, -5.0, 10.0))
    sun = bpy.context.active_object
    sun.name = "light_sun"
    sun.data.energy = 15.0
    sun.data.angle = math.radians(5)
    log("Sun ajoute : energy=15")

    bpy.ops.object.light_add(type="POINT", location=(0.0, 0.0, 4.0))
    point = bpy.context.active_object
    point.name = "light_fill"
    point.data.energy = 500.0
    point.data.shadow_soft_size = 1.0
    log("Point ajoute : energy=500")
    return True


def inject_world(scene=None):
    if scene is None:
        scene = bpy.context.scene

    world = bpy.data.worlds.get("World_VULKAN") or bpy.data.worlds.new("World_VULKAN")
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
    log("World override : (0.6,0.65,0.75) strength=2.5")


def main():
    scene = bpy.context.scene
    results = {
        "camera_injected": inject_camera(scene),
        "lighting_injected": inject_lighting(scene),
    }
    inject_world(scene)
    bpy.ops.wm.save_mainfile()
    log("Scene sauvegardee")
    report = {
        "fix_id": "VULKAN_CAMERA_FIX_v1",
        "blend_file": bpy.data.filepath,
        "camera_name": scene.camera.name if scene.camera else None,
        "camera_location": list(scene.camera.location) if scene.camera else None,
        "camera_injected": results["camera_injected"],
        "lighting_injected": results["lighting_injected"],
        "status": "OK"
    }
    print(f"[INJECT_CAMERA] RAPPORT : {json.dumps(report)}")


if __name__ == "__main__":
    main()
