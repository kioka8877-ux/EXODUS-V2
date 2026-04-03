"""
FIX : displacement_vertices (depsgraph stale)
Frégate : U03 — SCENOGRAPHY_DOCK
Commit origine : 6db5311f
Problème : depsgraph stale -> geometry_probe retourne 4 vertices
Solution : depsgraph.update() avant toute evaluation de geometrie
Validé par : L'Empereur
"""

import bpy


def fix_displacement_vertices(obj_name=None, scene=None):
    """
    Force la mise a jour du depsgraph avant evaluation geometrique.
    Garantit que le vertex count est reel (>10K pour scenes complexes).
    Retourne le nombre de vertices apres fix.
    """
    if scene is None:
        scene = bpy.context.scene

    # CRITIQUE : mettre a jour le depsgraph avant evaluation
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

    if obj_name:
        obj = scene.objects.get(obj_name)
        if not obj:
            print(f"[FIX_VERTICES] ERREUR — objet '{obj_name}' introuvable")
            return 0
        obj_eval = obj.evaluated_get(depsgraph)
        mesh_eval = obj_eval.to_mesh()
        count = len(mesh_eval.vertices)
        obj_eval.to_mesh_clear()
        print(f"[FIX_VERTICES] APPLIED — {obj_name} : {count} vertices (depsgraph force)")
        return count

    # Sans objet specifie : compter total scene
    total = 0
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj_eval = obj.evaluated_get(depsgraph)
            mesh_eval = obj_eval.to_mesh()
            total += len(mesh_eval.vertices)
            obj_eval.to_mesh_clear()

    print(f"[FIX_VERTICES] APPLIED — total scene : {total} vertices")
    return total


if __name__ == "__main__":
    count = fix_displacement_vertices()
    print(f"[FIX_VERTICES] Resultat : {count} vertices")
