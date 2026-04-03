"""
FIX : camera_missing
Frégate : U04 — PHOTOGRAPHY_WING
Commit origine : 0cb3057d
Problème : camera_main absente du scene graph -> render echoue
Solution : injection automatique de camera_main si absente
Validé par : L'Empereur
"""

import bpy


def fix_camera_missing(scene=None):
    """
    Vérifie et injecte une camera_main si absente de la scene.
    Retourne True si fix applique, False si deja OK.
    """
    if scene is None:
        scene = bpy.context.scene

    # Verifier si une camera existe deja
    existing = [obj for obj in scene.objects if obj.type == 'CAMERA']
    if existing:
        print(f"[FIX_CAMERA] OK — camera existante : {existing[0].name}")
        return False

    # Creer camera_main
    bpy.ops.object.camera_add(location=(0, -10, 5))
    cam = bpy.context.active_object
    cam.name = "camera_main"
    scene.camera = cam

    print(f"[FIX_CAMERA] APPLIED — camera_main creee et assignee a la scene")
    return True


if __name__ == "__main__":
    result = fix_camera_missing()
    print(f"[FIX_CAMERA] Resultat : {'FIX APPLIQUE' if result else 'DEJA OK'}")
