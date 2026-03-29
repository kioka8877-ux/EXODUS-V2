#!/usr/bin/env python3
"""
geometry_probe_u03.py — Probe U03 .blend (Blender 3.x / 4.x)

À lancer en HEADLESS :
  blender --background environment_1.blend --python geometry_probe_u03.py -- --output /path/to/probe.json

Variables d'environnement (optionnel) :
  GEOMETRY_PROBE_OUT  — chemin JSON si --output absent

Sortie : fichier JSON uniquement (pas de parse de stdout Blender).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import bpy


def _argv_after_dd() -> List[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _parse_output_path() -> Optional[Path]:
    args = _argv_after_dd()
    for i, a in enumerate(args):
        if a in ("--output", "-o") and i + 1 < len(args):
            return Path(args[i + 1])
    env = os.environ.get("GEOMETRY_PROBE_OUT", "").strip()
    if env:
        return Path(env)
    return None


def _modifier_summary(mod: bpy.types.Modifier) -> dict:
    info: dict = {"name": mod.name, "type": mod.type}
    if mod.type == "SUBSURF":
        info["levels"] = getattr(mod, "levels", None)
        info["render_levels"] = getattr(mod, "render_levels", None)
    if mod.type == "DISPLACE":
        info["strength"] = getattr(mod, "strength", None)
        mid = getattr(mod, "texture", None)
        info["texture"] = mid.name if mid else None
    return info


def _evaluated_vertex_count(obj: bpy.types.Object) -> Optional[int]:
    """Nombre de vertices après depsgraph (subdiv/displace pris en compte)."""
    if obj.type != "MESH" or obj.data is None:
        return None
    try:
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        ev_obj = obj.evaluated_get(depsgraph)
        mesh = ev_obj.to_mesh()
        try:
            return len(mesh.vertices)
        finally:
            ev_obj.to_mesh_clear()
    except Exception:
        return None


def _probe_object(obj: bpy.types.Object) -> dict:
    row: dict = {
        "name": obj.name,
        "type": obj.type,
        "raw_vertices": None,
        "evaluated_vertices": None,
        "modifiers": [],
    }
    if obj.type != "MESH" or obj.data is None:
        return row
    row["raw_vertices"] = len(obj.data.vertices)
    row["evaluated_vertices"] = _evaluated_vertex_count(obj)
    row["modifiers"] = [_modifier_summary(m) for m in obj.modifiers]
    return row


def _status_for_u03(objects: List[dict]) -> Tuple[str, List[str]]:
    """
    Ne se base PAS sur un seuil magique de 'raw vertices'.
    Regarde displacement_mesh + stack modificateurs typique.
    """
    notes: List[str] = []
    by_name = {o["name"]: o for o in objects}

    disp = None
    for k, o in by_name.items():
        if "displacement" in k.lower() and o.get("type") == "MESH":
            disp = o
            break

    if disp is None:
        return "MISSING_DISPLACEMENT_MESH", ["Aucun objet mesh dont le nom contient 'displacement'"]

    mods = [m.get("type") for m in disp.get("modifiers", [])]
    has_sub = "SUBSURF" in mods
    has_displace = "DISPLACE" in mods

    ev = disp.get("evaluated_vertices")
    raw = disp.get("raw_vertices")

    if has_sub and has_displace:
        notes.append("SUBSURF + DISPLACE présents sur displacement_mesh")
        if ev is not None and ev > 100:
            notes.append(f"evaluated_vertices={ev} (mesh dense côté rendu)")
        elif ev is not None:
            notes.append(f"evaluated_vertices={ev} (faible — vérifier texture / strength)")
        else:
            notes.append("evaluated_vertices indisponible")
        return "OK", notes

    if raw is not None and raw <= 8:
        notes.append(f"raw_vertices={raw} — typique d'un plan sans modificateurs visibles au rendu")
    return "WARN", notes + [
        f"Modificateurs trouvés: {mods}",
        "Attendu: au moins SUBSURF + DISPLACE sur displacement_mesh",
    ]


def main() -> None:
    out = _parse_output_path()
    if out is None:
        sys.stderr.write(
            "geometry_probe_u03: précise --output /chemin/probe.json ou GEOMETRY_PROBE_OUT\n"
        )
        sys.exit(2)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    objects_payload = [_probe_object(o) for o in meshes]

    status, notes = _status_for_u03(objects_payload)

    report = {
        "blender_version": ".".join(str(x) for x in bpy.app.version),
        "blend_file": bpy.data.filepath or "",
        "status": status,
        "notes": notes,
        "objects": objects_payload,
        "summary": {
            "mesh_object_count": len(meshes),
            "total_raw_vertices": sum(
                (o.get("raw_vertices") or 0) for o in objects_payload if o.get("raw_vertices") is not None
            ),
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Une ligne propre pour debug humain (facultatif)
    print(f"[geometry_probe_u03] écrit: {out}", flush=True)


if __name__ == "__main__":
    main()
