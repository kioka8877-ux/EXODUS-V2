"""
FIX : low_luminance
Frégate : U04 — PHOTOGRAPHY_WING
Problème : rendu trop sombre -> frames illisibles
Solution : ajustement exposure + ajout light de secours si aucune
Validé par : L'Empereur
"""

import bpy


def fix_low_luminance(scene=None, exposure_boost=1.5, min_lights=1):
    """
    Corrige la luminance faible.
    - Booste l'exposure de la scene
    - Ajoute une sun lamp si aucune lumiere presente
    Retourne dict avec actions appliquees.
    """
    if scene is None:
        scene = bpy.context.scene

    actions = []

    # Boost exposure
    if scene.view_settings.exposure < exposure_boost:
        scene.view_settings.exposure = exposure_boost
        actions.append(f"exposure -> {exposure_boost}")

    # Verifier lights
    lights = [obj for obj in scene.objects if obj.type == 'LIGHT']
    if len(lights) < min_lights:
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
        sun = bpy.context.active_object
        sun.name = "sun_emergency"
        sun.data.energy = 3.0
        actions.append("sun_emergency ajoutee (energy=3.0)")

    if actions:
        print(f"[FIX_LUMINANCE] APPLIED — {', '.join(actions)}")
    else:
        print("[FIX_LUMINANCE] OK — luminance dans les normes")

    return {"fixed": bool(actions), "actions": actions}


if __name__ == "__main__":
    result = fix_low_luminance()
    print(f"[FIX_LUMINANCE] Resultat : {result}")
