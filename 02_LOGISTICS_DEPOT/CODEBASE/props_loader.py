#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PROPS LOADER — EXODUS LOGISTICS                           ║
║                  Chargement Assets depuis Bibliothèque                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour charger les props depuis différents formats (GLB, FBX, BLEND, OBJ)
et les préparer pour l'attachement aux bones de l'avatar.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("[PROPS_LOADER] Warning: bpy non disponible, mode standalone")


SUPPORTED_FORMATS = {
    ".glb": "GLTF",
    ".gltf": "GLTF",
    ".fbx": "FBX",
    ".blend": "BLEND",
    ".obj": "OBJ"
}

PROP_DEFAULTS = {
    "scale": (1.0, 1.0, 1.0),
    "rotation": (0.0, 0.0, 0.0),
    "offset": (0.0, 0.0, 0.0)
}

GENERIC_PLACEHOLDER_NAME = "generic_prop"


class PropsLoader:
    """Gestionnaire de chargement des props."""
    
    def __init__(self, library_path: str, verbose: bool = False):
        self.library_path = Path(library_path)
        self.verbose = verbose
        self.loaded_props: Dict[str, Any] = {}
        self.prop_cache: Dict[str, str] = {}
        
        if not self.library_path.exists():
            self._log(f"Warning: Library path does not exist: {self.library_path}")
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[PROPS_LOADER] {msg}")
    
    def scan_library(self) -> Dict[str, str]:
        """
        Scanne la bibliothèque et retourne un mapping prop_id -> filepath.
        """
        if not self.library_path.exists():
            return {}
        
        prop_map = {}
        
        for ext in SUPPORTED_FORMATS.keys():
            for filepath in self.library_path.glob(f"*{ext}"):
                prop_id = filepath.stem
                if prop_id not in prop_map:
                    prop_map[prop_id] = str(filepath)
                    self._log(f"Found: {prop_id} -> {filepath.name}")
        
        self.prop_cache = prop_map
        self._log(f"Total props found: {len(prop_map)}")
        return prop_map
    
    def get_prop_path(self, prop_id: str) -> Optional[str]:
        """
        Retourne le chemin vers un prop par son ID.
        Utilise le placeholder générique si non trouvé.
        """
        if not self.prop_cache:
            self.scan_library()
        
        if prop_id in self.prop_cache:
            return self.prop_cache[prop_id]
        
        if GENERIC_PLACEHOLDER_NAME in self.prop_cache:
            self._log(f"Using placeholder for missing prop: {prop_id}")
            return self.prop_cache[GENERIC_PLACEHOLDER_NAME]
        
        self._log(f"Prop not found and no placeholder: {prop_id}")
        return None
    
    def load_prop(self, prop_id: str, prop_path: Optional[str] = None) -> Optional[Any]:
        """
        Charge un prop dans la scène Blender.
        Retourne l'objet principal du prop.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required for loading props")
        
        if prop_id in self.loaded_props:
            self._log(f"Prop already loaded: {prop_id}")
            return self._duplicate_prop(prop_id)
        
        if prop_path is None:
            prop_path = self.get_prop_path(prop_id)
        
        if prop_path is None:
            self._log(f"Cannot load prop: {prop_id} (not found)")
            return None
        
        filepath = Path(prop_path)
        ext = filepath.suffix.lower()
        
        if ext not in SUPPORTED_FORMATS:
            self._log(f"Unsupported format: {ext}")
            return None
        
        existing_objects = set(bpy.data.objects.keys())
        
        if ext in [".glb", ".gltf"]:
            self._import_gltf(str(filepath))
        elif ext == ".fbx":
            self._import_fbx(str(filepath))
        elif ext == ".blend":
            self._import_blend(str(filepath))
        elif ext == ".obj":
            self._import_obj(str(filepath))
        
        new_objects = [obj for obj in bpy.data.objects if obj.name not in existing_objects]
        
        if not new_objects:
            self._log(f"No objects imported from: {filepath}")
            return None
        
        main_obj = self._find_main_object(new_objects)
        
        self._rename_prop_objects(new_objects, prop_id)
        
        self.loaded_props[prop_id] = main_obj.name
        self._log(f"Loaded prop: {prop_id} -> {main_obj.name}")
        
        return main_obj
    
    def _import_gltf(self, filepath: str):
        """Import GLB/GLTF file."""
        bpy.ops.import_scene.gltf(filepath=filepath)
    
    def _import_fbx(self, filepath: str):
        """Import FBX file."""
        bpy.ops.import_scene.fbx(filepath=filepath)
    
    def _import_blend(self, filepath: str):
        """Import objects from another .blend file."""
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects]
        
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
    
    def _import_obj(self, filepath: str):
        """Import OBJ file."""
        bpy.ops.wm.obj_import(filepath=filepath)
    
    def _find_main_object(self, objects: List[Any]) -> Any:
        """
        Trouve l'objet principal parmi les objets importés.
        Priorité: mesh > armature > empty > autres
        """
        meshes = [obj for obj in objects if obj.type == 'MESH']
        if meshes:
            return max(meshes, key=lambda o: len(o.data.vertices) if o.data else 0)
        
        armatures = [obj for obj in objects if obj.type == 'ARMATURE']
        if armatures:
            return armatures[0]
        
        return objects[0]
    
    def _rename_prop_objects(self, objects: List[Any], prop_id: str):
        """Renomme les objets du prop avec un préfixe unique."""
        for i, obj in enumerate(objects):
            if i == 0:
                obj.name = f"PROP_{prop_id}"
            else:
                obj.name = f"PROP_{prop_id}_{i:02d}"
    
    def _duplicate_prop(self, prop_id: str) -> Optional[Any]:
        """Duplique un prop déjà chargé."""
        if prop_id not in self.loaded_props:
            return None
        
        original_name = self.loaded_props[prop_id]
        original = bpy.data.objects.get(original_name)
        
        if original is None:
            return None
        
        duplicate = original.copy()
        if original.data:
            duplicate.data = original.data.copy()
        
        bpy.context.collection.objects.link(duplicate)
        
        counter = 1
        while f"PROP_{prop_id}_{counter:03d}" in bpy.data.objects:
            counter += 1
        duplicate.name = f"PROP_{prop_id}_{counter:03d}"
        
        self._log(f"Duplicated prop: {prop_id} -> {duplicate.name}")
        return duplicate
    
    def unload_prop(self, prop_id: str):
        """Supprime un prop de la scène."""
        if not BLENDER_AVAILABLE:
            return
        
        objects_to_remove = [obj for obj in bpy.data.objects if obj.name.startswith(f"PROP_{prop_id}")]
        
        for obj in objects_to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)
        
        if prop_id in self.loaded_props:
            del self.loaded_props[prop_id]
        
        self._log(f"Unloaded prop: {prop_id}")
    
    def get_loaded_props(self) -> List[str]:
        """Retourne la liste des props chargés."""
        return list(self.loaded_props.keys())
    
    def create_placeholder(self) -> Any:
        """
        Crée un placeholder générique si aucun n'existe.
        Un simple cube rouge semi-transparent.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender (bpy) required")
        
        placeholder_name = f"PROP_{GENERIC_PLACEHOLDER_NAME}"
        
        if placeholder_name in bpy.data.objects:
            return bpy.data.objects[placeholder_name]
        
        bpy.ops.mesh.primitive_cube_add(size=0.1)
        placeholder = bpy.context.active_object
        placeholder.name = placeholder_name
        
        mat = bpy.data.materials.new(name="Placeholder_Material")
        mat.use_nodes = True
        mat.blend_method = 'BLEND'
        
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 0.5)
            bsdf.inputs["Alpha"].default_value = 0.5
        
        placeholder.data.materials.append(mat)
        
        self.loaded_props[GENERIC_PLACEHOLDER_NAME] = placeholder_name
        self._log("Created generic placeholder prop")
        
        return placeholder


def load_props_from_mapping(props_mapping: Dict[str, str], verbose: bool = False) -> Dict[str, Any]:
    """
    Charge tous les props depuis un mapping prop_id -> filepath.
    Retourne un mapping prop_id -> blender_object.
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender (bpy) required")
    
    if not props_mapping:
        return {}
    
    library_path = str(Path(next(iter(props_mapping.values()))).parent)
    loader = PropsLoader(library_path, verbose=verbose)
    
    loaded = {}
    for prop_id, filepath in props_mapping.items():
        obj = loader.load_prop(prop_id, filepath)
        if obj:
            loaded[prop_id] = obj
    
    return loaded


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python props_loader.py <library_path>")
        print("\nScan a props library directory and list available props.")
        sys.exit(1)
    
    library_path = sys.argv[1]
    loader = PropsLoader(library_path, verbose=True)
    props = loader.scan_library()
    
    print(f"\n=== Props Library: {library_path} ===")
    for prop_id, filepath in sorted(props.items()):
        print(f"  {prop_id}: {filepath}")
    print(f"\nTotal: {len(props)} props")
