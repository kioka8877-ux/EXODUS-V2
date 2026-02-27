"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FRÉGATE 03_SCENOGRAPHY_DOCK — SCENE SCHEMA (Contrat Tri-Layer)           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de données pures : définit TOUTE la structure obligatoire des      ║
║  fichiers .blend produits par la Scenography Dock (Tri-Layer System).       ║
║  Zéro dépendance Blender. Zéro traitement. Données + Validation.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import re
from typing import Dict, List, Optional, Tuple


# =============================================================================
# VERSION CANONIQUE
# =============================================================================

SCENE_SCHEMA_VERSION: str = "2.0.0"


# =============================================================================
# SECTION 1 — COLLECTIONS OBLIGATOIRES
# =============================================================================
# Chaque collection Blender attendue dans le .blend final.
# "required_objects" : objets qui DOIVENT exister dans la collection.
# "optional_objects" : objets facultatifs (wildcards autorisés).

REQUIRED_COLLECTIONS: Dict[str, dict] = {
    "ENV_DOME": {
        "description": "Infinity Dome — demi-sphère background vidéo source",
        "required_objects": ["infinity_dome"],
        "optional_objects": [],
    },
    "ENV_TERRAIN": {
        "description": "Displacement Mesh — géométrie 3D via depth maps",
        "required_objects": ["displacement_mesh"],
        "optional_objects": ["terrain_proxy"],
    },
    "ENV_SHADOW": {
        "description": "Shadow Catcher — plan invisible capteur d'ombres",
        "required_objects": ["shadow_catcher"],
        "optional_objects": [],
    },
    "ENV_GLASS": {
        "description": "Reflectivity Hack — plans Glass BSDF sur surfaces vitrées",
        "required_objects": [],
        "optional_objects": ["glass_plane_*"],
    },
    "ENV_PBR": {
        "description": "PBR Swap — surfaces proches avec matériaux PBR",
        "required_objects": [],
        "optional_objects": ["pbr_surface_*"],
    },
}


# =============================================================================
# SECTION 2 — NOMENCLATURE OBJETS
# =============================================================================
# Spécifications par nom d'objet (ou pattern wildcard).
# Chaque spec contient : type Blender, géométrie attendue, type de matériau,
# et contraintes spécifiques.

OBJECT_SPECS: Dict[str, dict] = {
    "infinity_dome": {
        "type": "MESH",
        "expected_geometry": "UV_SPHERE_HALF",
        "material_type": "IMAGE_TEXTURE",
        "constraints": {
            "min_radius": 50.0,
            "max_radius": 200.0,
            "normals": "INWARD",
        },
    },
    "displacement_mesh": {
        "type": "MESH",
        "expected_geometry": "SUBDIVIDED_PLANE",
        "material_type": "DEPTH_DISPLACED",
        "constraints": {
            "min_subdivisions": 64,
            "max_subdivisions": 256,
            "default_subdivisions": 128,
            "modifier_type": "DISPLACE",
            "texture_source": "DEPTH_MAP_PNG",
        },
    },
    "shadow_catcher": {
        "type": "MESH",
        "expected_geometry": "PLANE",
        "material_type": "SHADOW_ONLY",
        "constraints": {
            "is_shadow_catcher": True,
            "visible_camera": False,
            "visible_diffuse": False,
        },
    },
    "glass_plane_*": {
        "type": "MESH",
        "expected_geometry": "PLANE",
        "material_type": "GLASS_BSDF",
        "constraints": {
            "z_offset": 0.01,
            "transmission": 0.9,
            "roughness_max": 0.1,
        },
    },
    "pbr_surface_*": {
        "type": "MESH",
        "expected_geometry": "PLANE_OR_CUSTOM",
        "material_type": "PBR_PRINCIPLED",
        "constraints": {},
    },
}


# =============================================================================
# SECTION 3 — WORLD SETTINGS CONTRACTUELS
# =============================================================================
# Paramètres World obligatoires pour le HDRi / World Sync.
# strength_range : plage d'exposition alignée sur la vidéo source.

WORLD_SETTINGS: Dict = {
    "use_nodes": True,
    "required_node_types": [
        "ShaderNodeTexEnvironment",
        "ShaderNodeBackground",
        "ShaderNodeOutputWorld",
    ],
    "strength_range": (0.1, 3.0),
    "default_strength": 1.0,
}


# =============================================================================
# SECTION 4 — CUSTOM PROPERTIES .BLEND
# =============================================================================
# Propriétés personnalisées apposées sur la scène Blender pour traçabilité.

CUSTOM_PROPERTIES: Dict[str, dict] = {
    "exodus_schema_version": {
        "type": "str",
        "value": "2.0.0",
        "description": "Version du scene_schema utilisé pour la construction",
    },
    "exodus_frigate": {
        "type": "str",
        "value": "U03",
        "description": "Frégate source du .blend",
    },
    "exodus_validated": {
        "type": "bool",
        "default": False,
        "description": "True si validate_scene() a passé",
    },
    "exodus_layers": {
        "type": "str",
        "value": "",
        "description": "Couches actives dans ce .blend (CSV)",
    },
}


# =============================================================================
# SECTION 5 — SAM LABELS → PBR MAPPING (Couche C — PBR Swap)
# =============================================================================
# Correspondance entre les labels de segmentation SAM et les presets PBR.
# None signifie que le label est ignoré (géré par une autre couche).

SAM_LABEL_TO_PBR: Dict[str, Optional[str]] = {
    "road": "asphalt",
    "grass": "grass",
    "wall": "concrete",
    "water": "water_surface",
    "glass": "glass_clear",
    "sky": None,
    "dirt": "dirt_ground",
    "wood": "wood_planks",
    "metal": "metal_steel",
    "fabric": "fabric_generic",
}

VALID_SAM_LABELS: List[str] = list(SAM_LABEL_TO_PBR.keys())


# =============================================================================
# SECTION 6 — PBR MATERIAL PRESETS V2
# =============================================================================
# Presets Principled BSDF pour le Tri-Layer System.
# Valeurs V1 conservées pour asphalt, concrete, grass, metal_steel, glass_clear.
# Nouveaux presets : water_surface, dirt_ground, wood_planks, fabric_generic.
# Chaque preset : base_color (RGBA), roughness, metallic, specular,
# et optionnellement transmission (verre/eau), emission.

PBR_MATERIAL_PRESETS: Dict[str, dict] = {
    "asphalt": {
        "base_color": (0.15, 0.15, 0.15, 1.0),
        "roughness": 0.8,
        "metallic": 0.0,
        "specular": 0.3,
    },
    "grass": {
        "base_color": (0.15, 0.35, 0.1, 1.0),
        "roughness": 0.95,
        "metallic": 0.0,
        "specular": 0.2,
    },
    "concrete": {
        "base_color": (0.5, 0.5, 0.5, 1.0),
        "roughness": 0.9,
        "metallic": 0.0,
        "specular": 0.3,
    },
    "water_surface": {
        "base_color": (0.01, 0.04, 0.08, 1.0),
        "roughness": 0.05,
        "metallic": 0.0,
        "specular": 0.9,
        "transmission": 0.85,
    },
    "glass_clear": {
        "base_color": (0.9, 0.95, 1.0, 0.3),
        "roughness": 0.05,
        "metallic": 0.0,
        "specular": 1.0,
        "transmission": 0.9,
    },
    "dirt_ground": {
        "base_color": (0.35, 0.22, 0.1, 1.0),
        "roughness": 0.95,
        "metallic": 0.0,
        "specular": 0.15,
    },
    "wood_planks": {
        "base_color": (0.4, 0.25, 0.12, 1.0),
        "roughness": 0.6,
        "metallic": 0.0,
        "specular": 0.4,
    },
    "metal_steel": {
        "base_color": (0.6, 0.6, 0.65, 1.0),
        "roughness": 0.3,
        "metallic": 0.9,
        "specular": 0.8,
    },
    "fabric_generic": {
        "base_color": (0.3, 0.28, 0.25, 1.0),
        "roughness": 0.95,
        "metallic": 0.0,
        "specular": 0.1,
    },
    "default": {
        "base_color": (0.5, 0.5, 0.5, 1.0),
        "roughness": 0.7,
        "metallic": 0.0,
        "specular": 0.4,
    },
}


# =============================================================================
# SECTION 7 — VRAM CONSTRAINTS
# =============================================================================
# Profils de budget VRAM pour adapter les résolutions et subdivisions.

VRAM_PROFILES: Dict[str, dict] = {
    "colab_t4": {
        "max_vram_gb": 6.0,
        "max_subdivisions": 128,
        "max_texture_size": 4096,
        "description": "Google Colab T4 (15GB GPU, 6GB budget U03)",
    },
    "colab_a100": {
        "max_vram_gb": 20.0,
        "max_subdivisions": 256,
        "max_texture_size": 8192,
        "description": "Google Colab A100 (40GB GPU)",
    },
    "local_low": {
        "max_vram_gb": 4.0,
        "max_subdivisions": 64,
        "max_texture_size": 2048,
        "description": "GPU locale budget (<6GB)",
    },
}

DEFAULT_VRAM_PROFILE: str = "colab_t4"


# =============================================================================
# HELPERS INTERNES
# =============================================================================

_WILDCARD_RE = re.compile(r"^(.+?)_\*$")

_REQUIRED_OBJECT_SPEC_FIELDS = {"type", "expected_geometry", "material_type", "constraints"}

_REQUIRED_PBR_FIELDS = {"base_color", "roughness", "metallic", "specular"}


def _matches_wildcard(name: str, pattern: str) -> bool:
    """Vérifie si un nom d'objet correspond à un pattern wildcard (ex: glass_plane_*)."""
    m = _WILDCARD_RE.match(pattern)
    if not m:
        return name == pattern
    prefix = m.group(1) + "_"
    return name.startswith(prefix)


def _find_object_spec(name: str) -> Optional[dict]:
    """Retourne le spec d'objet correspondant (exact ou wildcard)."""
    if name in OBJECT_SPECS:
        return OBJECT_SPECS[name]
    for pattern, spec in OBJECT_SPECS.items():
        if _WILDCARD_RE.match(pattern) and _matches_wildcard(name, pattern):
            return spec
    return None


# =============================================================================
# CLASSE PRINCIPALE — SceneSchema
# =============================================================================

class SceneSchema:
    """Contrat de Scène U03 — définit et valide la structure des .blend produits."""

    def __init__(self, vram_profile: str = "colab_t4") -> None:
        if vram_profile not in VRAM_PROFILES:
            raise ValueError(
                f"Profil VRAM inconnu : '{vram_profile}'. "
                f"Valides : {list(VRAM_PROFILES.keys())}"
            )
        self.vram_profile: str = vram_profile
        self.collections: Dict[str, dict] = dict(REQUIRED_COLLECTIONS)
        self.object_specs: Dict[str, dict] = dict(OBJECT_SPECS)
        self.world_settings: Dict = dict(WORLD_SETTINGS)
        self.custom_properties: Dict[str, dict] = dict(CUSTOM_PROPERTIES)
        self.sam_label_to_pbr: Dict[str, Optional[str]] = dict(SAM_LABEL_TO_PBR)
        self.pbr_presets: Dict[str, dict] = dict(PBR_MATERIAL_PRESETS)
        self.vram_profiles: Dict[str, dict] = dict(VRAM_PROFILES)

    # -----------------------------------------------------------------
    # Validation — Collections
    # -----------------------------------------------------------------

    def validate_collections(self, collection_names: List[str]) -> Tuple[bool, List[str]]:
        """Vérifie que toutes les collections obligatoires sont présentes."""
        errors: List[str] = []
        for coll_name in REQUIRED_COLLECTIONS:
            if coll_name not in collection_names:
                errors.append(f"Collection manquante : '{coll_name}'")
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # Validation — Nomenclature objets
    # -----------------------------------------------------------------

    def validate_object_naming(self, objects: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Vérifie la nomenclature des objets (nom → type attendu).

        Args:
            objects: dict {nom_objet: type_blender} ex: {"infinity_dome": "MESH"}
        """
        errors: List[str] = []
        for coll_name, coll_def in REQUIRED_COLLECTIONS.items():
            for req_obj in coll_def["required_objects"]:
                if req_obj not in objects:
                    errors.append(f"Objet requis manquant : '{req_obj}' (collection '{coll_name}')")
        for obj_name, obj_type in objects.items():
            spec = _find_object_spec(obj_name)
            if spec is None:
                continue
            if obj_type != spec["type"]:
                errors.append(
                    f"Type incorrect pour '{obj_name}' : attendu '{spec['type']}', reçu '{obj_type}'"
                )
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # Validation — World Settings
    # -----------------------------------------------------------------

    def validate_world_settings(self, world_info: Dict) -> Tuple[bool, List[str]]:
        """Vérifie les settings World (use_nodes, node types, strength range).

        Args:
            world_info: dict {use_nodes: bool, node_types: list[str], strength: float}
        """
        errors: List[str] = []
        if not world_info.get("use_nodes", False):
            errors.append("World.use_nodes doit être True")
        present_nodes = set(world_info.get("node_types", []))
        for req_node in WORLD_SETTINGS["required_node_types"]:
            if req_node not in present_nodes:
                errors.append(f"Node World manquant : '{req_node}'")
        strength = world_info.get("strength", WORLD_SETTINGS["default_strength"])
        lo, hi = WORLD_SETTINGS["strength_range"]
        if strength < lo or strength > hi:
            errors.append(
                f"World strength {strength} hors plage [{lo}, {hi}]"
            )
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # Validation — Custom Properties
    # -----------------------------------------------------------------

    def validate_custom_properties(self, properties: Dict) -> Tuple[bool, List[str]]:
        """Vérifie les custom properties exodus_*.

        Args:
            properties: dict {prop_name: value}
        """
        errors: List[str] = []
        for prop_name, prop_def in CUSTOM_PROPERTIES.items():
            if prop_name not in properties:
                errors.append(f"Custom property manquante : '{prop_name}'")
                continue
            val = properties[prop_name]
            expected_type = prop_def["type"]
            if expected_type == "str" and not isinstance(val, str):
                errors.append(f"'{prop_name}' doit être str, reçu {type(val).__name__}")
            elif expected_type == "bool" and not isinstance(val, bool):
                errors.append(f"'{prop_name}' doit être bool, reçu {type(val).__name__}")
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # Validation — Displacement Mesh
    # -----------------------------------------------------------------

    def validate_displacement_mesh(self, mesh_info: Dict) -> Tuple[bool, List[str]]:
        """Vérifie les contraintes du displacement mesh.

        Args:
            mesh_info: dict {subdivisions: int, has_displace_modifier: bool, texture_type: str}
        """
        errors: List[str] = []
        spec = OBJECT_SPECS["displacement_mesh"]["constraints"]
        vram = VRAM_PROFILES[self.vram_profile]
        subdivisions = mesh_info.get("subdivisions", 0)
        min_sub = spec["min_subdivisions"]
        max_sub = min(spec["max_subdivisions"], vram["max_subdivisions"])
        if subdivisions < min_sub or subdivisions > max_sub:
            errors.append(
                f"Subdivisions {subdivisions} hors plage [{min_sub}, {max_sub}] "
                f"(profil '{self.vram_profile}')"
            )
        if not mesh_info.get("has_displace_modifier", False):
            errors.append("Modifier DISPLACE manquant sur displacement_mesh")
        tex_type = mesh_info.get("texture_type", "")
        if tex_type != spec["texture_source"]:
            errors.append(
                f"Texture source attendue '{spec['texture_source']}', reçue '{tex_type}'"
            )
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # Validation — Shadow Catcher
    # -----------------------------------------------------------------

    def validate_shadow_catcher(self, object_info: Dict) -> Tuple[bool, List[str]]:
        """Vérifie les flags du shadow catcher.

        Args:
            object_info: dict {is_shadow_catcher: bool, visible_camera: bool, visible_diffuse: bool}
        """
        errors: List[str] = []
        spec = OBJECT_SPECS["shadow_catcher"]["constraints"]
        if object_info.get("is_shadow_catcher") is not True:
            errors.append("shadow_catcher.is_shadow_catcher doit être True")
        if object_info.get("visible_camera") is not False:
            errors.append("shadow_catcher.visible_camera doit être False")
        if object_info.get("visible_diffuse") is not False:
            errors.append("shadow_catcher.visible_diffuse doit être False")
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # Validation — Glass Planes
    # -----------------------------------------------------------------

    def validate_glass_planes(self, planes: List[Dict]) -> Tuple[bool, List[str]]:
        """Vérifie les plans glass (z_offset, transmission, roughness).

        Args:
            planes: list[dict] — chaque dict: {z_offset, transmission, roughness}
        """
        errors: List[str] = []
        spec = OBJECT_SPECS["glass_plane_*"]["constraints"]
        for i, plane in enumerate(planes):
            z = plane.get("z_offset", 0.0)
            if abs(z - spec["z_offset"]) > 1e-6:
                errors.append(
                    f"glass_plane[{i}] z_offset={z}, attendu {spec['z_offset']}"
                )
            transmission = plane.get("transmission", 0.0)
            if transmission < spec["transmission"]:
                errors.append(
                    f"glass_plane[{i}] transmission={transmission}, "
                    f"minimum attendu {spec['transmission']}"
                )
            roughness = plane.get("roughness", 1.0)
            if roughness > spec["roughness_max"]:
                errors.append(
                    f"glass_plane[{i}] roughness={roughness}, "
                    f"maximum attendu {spec['roughness_max']}"
                )
        return (len(errors) == 0, errors)

    # -----------------------------------------------------------------
    # VALIDATION MAÎTRE — validate_scene()
    # -----------------------------------------------------------------

    def validate_scene(self, scene_report: Dict) -> Tuple[bool, List[str]]:
        """Exécute TOUTES les validations sur un rapport de scène complet.

        Args:
            scene_report: dict avec les clés:
                - "collections": list[str] — noms des collections présentes
                - "objects": dict[str, str] — {nom_objet: type_blender}
                - "world": dict — {use_nodes, node_types, strength}
                - "custom_properties": dict — {prop_name: value}
                - "displacement_mesh": dict — {subdivisions, has_displace_modifier, texture_type}
                - "shadow_catcher": dict — {is_shadow_catcher, visible_camera, visible_diffuse}
                - "glass_planes": list[dict] — [{z_offset, transmission, roughness}]

        Returns:
            (passed: bool, errors: list[str])
        """
        all_errors: List[str] = []

        ok, errs = self.validate_collections(scene_report.get("collections", []))
        all_errors.extend(errs)

        ok, errs = self.validate_object_naming(scene_report.get("objects", {}))
        all_errors.extend(errs)

        ok, errs = self.validate_world_settings(scene_report.get("world", {}))
        all_errors.extend(errs)

        ok, errs = self.validate_custom_properties(scene_report.get("custom_properties", {}))
        all_errors.extend(errs)

        ok, errs = self.validate_displacement_mesh(scene_report.get("displacement_mesh", {}))
        all_errors.extend(errs)

        ok, errs = self.validate_shadow_catcher(scene_report.get("shadow_catcher", {}))
        all_errors.extend(errs)

        ok, errs = self.validate_glass_planes(scene_report.get("glass_planes", []))
        all_errors.extend(errs)

        return (len(all_errors) == 0, all_errors)

    # -----------------------------------------------------------------
    # Accesseurs
    # -----------------------------------------------------------------

    def get_marshal_manifest(self) -> Dict:
        """Retourne un résumé de la structure attendue pour le MARSHAL."""
        required_objs: List[str] = []
        for coll_def in REQUIRED_COLLECTIONS.values():
            required_objs.extend(coll_def["required_objects"])
        return {
            "schema_version": SCENE_SCHEMA_VERSION,
            "frigate": "U03",
            "collections": list(REQUIRED_COLLECTIONS.keys()),
            "required_objects": required_objs,
            "vram_profile": self.vram_profile,
            "vram_limits": self.get_vram_limits(),
            "pbr_presets_available": list(PBR_MATERIAL_PRESETS.keys()),
            "sam_labels_supported": VALID_SAM_LABELS,
        }

    def get_vram_limits(self) -> Dict:
        """Retourne les limites VRAM du profil actif."""
        return dict(VRAM_PROFILES[self.vram_profile])

    def get_sam_pbr_mapping(self, sam_label: str) -> Optional[str]:
        """Retourne le preset PBR pour un label SAM donné."""
        if sam_label not in SAM_LABEL_TO_PBR:
            raise ValueError(
                f"Label SAM inconnu : '{sam_label}'. Valides : {VALID_SAM_LABELS}"
            )
        return SAM_LABEL_TO_PBR[sam_label]

    def get_pbr_preset(self, preset_name: str) -> Dict:
        """Retourne un preset PBR par nom."""
        if preset_name not in PBR_MATERIAL_PRESETS:
            raise ValueError(
                f"Preset PBR inconnu : '{preset_name}'. "
                f"Valides : {list(PBR_MATERIAL_PRESETS.keys())}"
            )
        return dict(PBR_MATERIAL_PRESETS[preset_name])


# =============================================================================
# RAPPORT DE VALIDATION — exécution standalone
# =============================================================================

if __name__ == "__main__":
    schema = SceneSchema()
    passed = 0
    total = 10

    print("=== SCENE SCHEMA — RAPPORT DE VALIDATION ===")

    # --- TEST 1 : Collections définies ---
    t1_ok = True
    n_colls = len(REQUIRED_COLLECTIONS)
    n_req_objs = sum(
        len(c["required_objects"]) for c in REQUIRED_COLLECTIONS.values()
    )
    for coll_name, coll_def in REQUIRED_COLLECTIONS.items():
        if not isinstance(coll_def.get("description"), str):
            t1_ok = False
        if not isinstance(coll_def.get("required_objects"), list):
            t1_ok = False
        if not isinstance(coll_def.get("optional_objects"), list):
            t1_ok = False
    if t1_ok:
        passed += 1
        print(f"[TEST 1] Collections définies........... \u2713 ({n_colls} collections, {n_req_objs} objets requis)")
    else:
        print(f"[TEST 1] Collections définies........... \u2717")

    # --- TEST 2 : Object specs complets ---
    t2_ok = True
    n_specs = len(OBJECT_SPECS)
    n_constrained = 0
    for spec_name, spec_def in OBJECT_SPECS.items():
        for field in _REQUIRED_OBJECT_SPEC_FIELDS:
            if field not in spec_def:
                t2_ok = False
                print(f"  ERREUR spec '{spec_name}': champ '{field}' manquant")
        if isinstance(spec_def.get("constraints"), dict):
            n_constrained += 1
    if t2_ok:
        passed += 1
        print(f"[TEST 2] Object specs complets.......... \u2713 ({n_specs} specs, tous contraints)")
    else:
        print(f"[TEST 2] Object specs complets.......... \u2717")

    # --- TEST 3 : World settings valides ---
    t3_ok = True
    n_nodes = len(WORLD_SETTINGS.get("required_node_types", []))
    if not WORLD_SETTINGS.get("use_nodes"):
        t3_ok = False
    if n_nodes != 3:
        t3_ok = False
    lo, hi = WORLD_SETTINGS.get("strength_range", (0, 0))
    if lo >= hi:
        t3_ok = False
    if t3_ok:
        passed += 1
        print(f"[TEST 3] World settings valides......... \u2713 ({n_nodes} node types requis)")
    else:
        print(f"[TEST 3] World settings valides......... \u2717")

    # --- TEST 4 : Custom properties ---
    t4_ok = True
    n_props = len(CUSTOM_PROPERTIES)
    for prop_name, prop_def in CUSTOM_PROPERTIES.items():
        if "type" not in prop_def:
            t4_ok = False
            print(f"  ERREUR prop '{prop_name}': champ 'type' manquant")
        if "description" not in prop_def:
            t4_ok = False
            print(f"  ERREUR prop '{prop_name}': champ 'description' manquant")
    if t4_ok:
        passed += 1
        print(f"[TEST 4] Custom properties.............. \u2713 ({n_props} propriétés définies)")
    else:
        print(f"[TEST 4] Custom properties.............. \u2717")

    # --- TEST 5 : SAM → PBR mapping ---
    t5_ok = True
    n_labels = len(SAM_LABEL_TO_PBR)
    n_pbr_targets = sum(1 for v in SAM_LABEL_TO_PBR.values() if v is not None)
    for label, preset_name in SAM_LABEL_TO_PBR.items():
        if preset_name is not None and preset_name not in PBR_MATERIAL_PRESETS:
            t5_ok = False
            print(f"  ERREUR SAM '{label}' → preset '{preset_name}' inexistant")
    if t5_ok:
        passed += 1
        print(f"[TEST 5] SAM \u2192 PBR mapping.............. \u2713 ({n_labels} labels, {n_pbr_targets} presets PBR)")
    else:
        print(f"[TEST 5] SAM \u2192 PBR mapping.............. \u2717")

    # --- TEST 6 : PBR presets complets ---
    t6_ok = True
    n_presets = len(PBR_MATERIAL_PRESETS)
    for preset_name, preset_def in PBR_MATERIAL_PRESETS.items():
        for field in _REQUIRED_PBR_FIELDS:
            if field not in preset_def:
                t6_ok = False
                print(f"  ERREUR PBR '{preset_name}': champ '{field}' manquant")
    if t6_ok:
        passed += 1
        print(f"[TEST 6] PBR presets complets........... \u2713 ({n_presets} presets, champs requis OK)")
    else:
        print(f"[TEST 6] PBR presets complets........... \u2717")

    # --- TEST 7 : VRAM profiles ---
    t7_ok = True
    n_profiles = len(VRAM_PROFILES)
    for profile_name, profile_def in VRAM_PROFILES.items():
        for field in ("max_vram_gb", "max_subdivisions", "max_texture_size"):
            if field not in profile_def:
                t7_ok = False
                print(f"  ERREUR VRAM '{profile_name}': champ '{field}' manquant")
        if profile_def.get("max_vram_gb", 0) <= 0:
            t7_ok = False
        if profile_def.get("max_subdivisions", 0) <= 0:
            t7_ok = False
        if profile_def.get("max_texture_size", 0) <= 0:
            t7_ok = False
    if t7_ok:
        passed += 1
        print(f"[TEST 7] VRAM profiles.................. \u2713 ({n_profiles} profils, limites cohérentes)")
    else:
        print(f"[TEST 7] VRAM profiles.................. \u2717")

    # --- TEST 8 : validate_scene() scénario OK ---
    t8_ok = True
    valid_report = {
        "collections": list(REQUIRED_COLLECTIONS.keys()),
        "objects": {
            "infinity_dome": "MESH",
            "displacement_mesh": "MESH",
            "shadow_catcher": "MESH",
        },
        "world": {
            "use_nodes": True,
            "node_types": [
                "ShaderNodeTexEnvironment",
                "ShaderNodeBackground",
                "ShaderNodeOutputWorld",
            ],
            "strength": 1.0,
        },
        "custom_properties": {
            "exodus_schema_version": "2.0.0",
            "exodus_frigate": "U03",
            "exodus_validated": True,
            "exodus_layers": "dome,terrain,shadow",
        },
        "displacement_mesh": {
            "subdivisions": 128,
            "has_displace_modifier": True,
            "texture_type": "DEPTH_MAP_PNG",
        },
        "shadow_catcher": {
            "is_shadow_catcher": True,
            "visible_camera": False,
            "visible_diffuse": False,
        },
        "glass_planes": [],
    }
    ok8, errs8 = schema.validate_scene(valid_report)
    if not ok8:
        t8_ok = False
        for e in errs8:
            print(f"  ERREUR scénario OK : {e}")
    if t8_ok:
        passed += 1
        print(f"[TEST 8] validate_scene() scénario OK... \u2713 (scène conforme acceptée)")
    else:
        print(f"[TEST 8] validate_scene() scénario OK... \u2717")

    # --- TEST 9 : validate_scene() scénario KO ---
    t9_ok = True
    bad_report = {
        "collections": ["ENV_DOME"],
        "objects": {},
        "world": {"use_nodes": False, "node_types": [], "strength": 0.0},
        "custom_properties": {},
        "displacement_mesh": {"subdivisions": 10, "has_displace_modifier": False, "texture_type": ""},
        "shadow_catcher": {"is_shadow_catcher": False, "visible_camera": True, "visible_diffuse": True},
        "glass_planes": [{"z_offset": 0.5, "transmission": 0.1, "roughness": 0.9}],
    }
    ok9, errs9 = schema.validate_scene(bad_report)
    if ok9:
        t9_ok = False
        print("  ERREUR : scène non-conforme acceptée à tort")
    if len(errs9) == 0:
        t9_ok = False
        print("  ERREUR : aucune erreur détectée sur scène invalide")
    if t9_ok:
        passed += 1
        print(f"[TEST 9] validate_scene() scénario KO... \u2713 (scène non-conforme rejetée)")
    else:
        print(f"[TEST 9] validate_scene() scénario KO... \u2717")

    # --- TEST 10 : Expressions hérétiques ---
    t10_ok = True

    try:
        schema.get_sam_pbr_mapping("unicorn")
        t10_ok = False
        print("  ERREUR : label SAM 'unicorn' accepté à tort")
    except ValueError:
        pass

    mesh_too_low = {"subdivisions": 2, "has_displace_modifier": True, "texture_type": "DEPTH_MAP_PNG"}
    ok_low, _ = schema.validate_displacement_mesh(mesh_too_low)
    if ok_low:
        t10_ok = False
        print("  ERREUR : subdivisions=2 acceptées à tort")

    mesh_too_high = {"subdivisions": 9999, "has_displace_modifier": True, "texture_type": "DEPTH_MAP_PNG"}
    ok_high, _ = schema.validate_displacement_mesh(mesh_too_high)
    if ok_high:
        t10_ok = False
        print("  ERREUR : subdivisions=9999 acceptées à tort")

    if t10_ok:
        passed += 1
        print(f"[TEST 10] Expressions hérétiques........ \u2713 (label SAM inconnu rejeté, subdivisions hors range rejetées)")
    else:
        print(f"[TEST 10] Expressions hérétiques........ \u2717")

    print(f"=== VALIDATION COMPLÈTE : {passed}/{total} TESTS PASSÉS ===")
