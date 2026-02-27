# SOUS-PLAN TECHNIQUE — UNITÉ 02: LOGISTICS DEPOT V2

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              FRÉGATE 02_LOGISTICS — PLAN TECHNIQUE V2                          ║
║                        Armurerie de la Flotte EXODUS                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

Attacher les props (armes, objets) sur l'acteur animé de U01, selon les instructions du PRODUCTION_PLAN.JSON (de U00 Cortex). Bypass conditionnel si `requires_u02 == false`. Produire des fichiers Alembic équipés prêts pour le rendu.

---

## Stack Technique

| Composant | Version | Usage |
|-----------|---------|-------|
| Blender | 4.0.x | Moteur 3D principal |
| Python | 3.10+ | Scripts d'orchestration |
| Alembic | - | Format export animation |
| GLTF/GLB | 2.0 | Format props recommandé |

---

## Architecture

```
02_LOGISTICS_DEPOT/
├── CODEBASE/
│   ├── EXO_02_LOGISTICS.py      # Wrapper principal CLI
│   ├── props_loader.py          # Chargement assets props
│   ├── socketing_engine.py      # Attachement bones (Blender)
│   ├── timeline_manager.py      # Gestion visibilité keyframes
│   ├── final_baker.py           # Export Alembic/Blend
│   ├── requirements.txt         # Dépendances Python
│   ├── EXO_02_CONTROL.ipynb     # Notebook debug V2
│   └── EXO_02_PRODUCTION.ipynb  # Notebook batch V2
├── IN_MOTION_DATA/
│   ├── actor_animated.blend     # Input: Acteur animé (de U01)
│   └── PRODUCTION_PLAN.JSON     # Input: Instructions (de U00)
├── IN_PROPS_LIBRARY/
│   ├── gun_pistol.glb
│   ├── phone_smartphone.glb
│   └── generic_prop.glb         # Placeholder
├── OUT_BAKED_ACTORS/
│   ├── actor_equipped.abc       # Output: Alembic final
│   ├── actor_equipped.blend     # Output: Backup éditable
│   └── logistics_report.json    # Output: Rapport
├── README_DEV.md                # Documentation développeur
└── UNIT_02_SUBPLAN.md           # Ce fichier
```

---

## Inputs

### 1. actor_animated.blend (de U01)

Acteur animé avec:
- Mesh riggé
- Armature active avec bones nommés
- Animation bakée sur timeline
- Textures packées

### 2. PRODUCTION_PLAN.JSON (de U00 Cortex)

```json
{
  "scenes": [
    {
      "scene_id": 1,
      "props_actions": [
        {
          "frame": 100,
          "action": "GRAB",
          "prop_id": "gun_pistol",
          "actor": "Actor_1",
          "socket": "hand_right"
        }
      ]
    }
  ]
}
```

### 3. props_library/

Dossier contenant les props au format:
- `.glb` / `.gltf` (recommandé)
- `.fbx`
- `.blend`
- `.obj`

---

## Outputs

### 1. actor_equipped.abc

Fichier Alembic contenant:
- Tous les meshes (acteur + props)
- Animations avec props attachés
- Transformations évaluées

### 2. actor_equipped.blend

Backup éditable avec:
- Contraintes Child Of actives
- Keyframes de visibilité
- Textures packées

### 3. logistics_report.json

Rapport de production:
```json
{
  "version": "2.0.0",
  "status": "SUCCESS",
  "attachments": [...],
  "logs": [...]
}
```

En mode bypass:
```json
{
  "version": "2.0.0",
  "status": "SKIPPED",
  "reason": "requires_u02 == false"
}
```

---

## Pipeline Technique

### Phase 0: Bypass Check (V2)

```
EXO_02_LOGISTICS.py
    └── Charger PRODUCTION_PLAN.JSON
    └── Lire production_notes.requires_u02
    └── Si false:
        └── Copier acteur U01 → OUT_BAKED_ACTORS/
        └── Générer logistics_report.json (status: SKIPPED)
        └── Exit 0
```

### Phase 1: Validation

```
EXO_02_LOGISTICS.py
    └── Valider chemins inputs
    └── Scanner IN_PROPS_LIBRARY/
    └── Vérifier Blender disponible
```

### Phase 2: Socketing (Blender Headless)

```
socketing_engine.py
    └── Trouver armature
    └── Résoudre sockets → bones
    └── Pour chaque action GRAB:
        └── Importer prop (props_loader.py)
        └── Créer contrainte Child Of
        └── Appliquer offset/rotation
```

### Phase 3: Timeline

```
timeline_manager.py
    └── Pour chaque prop:
        └── Keyframe hide_viewport/hide_render @ frame 0
        └── Pour chaque événement:
            └── GRAB: show + activate constraint
            └── DROP: deactivate constraint
            └── HIDE: hide prop
```

### Phase 4: Export

```
final_baker.py
    └── Valider scène
    └── Export Alembic (.abc)
    └── Save Blend backup (.blend)
    └── Générer rapport
```

---

## Socket Mapping

Le système résout automatiquement les noms de bones selon l'armature:

| Socket | Bones reconnus |
|--------|----------------|
| `hand_right` | hand.R, RightHand, mixamorig:RightHand |
| `hand_left` | hand.L, LeftHand, mixamorig:LeftHand |
| `back` | spine.003, Spine3, UpperBack |
| `head` | head, Head, mixamorig:Head |
| `hip_holster` | pelvis, Hips, mixamorig:Hips |
| `chest` | spine.002, Chest |
| `shoulder_*` | shoulder.R/L, RightShoulder, LeftShoulder |
| `foot_*` | foot.R/L, RightFoot, LeftFoot |

---

## Contrainte Child Of

```python
def attach_prop_to_bone(prop_obj, armature, bone_name, offset):
    constraint = prop_obj.constraints.new('CHILD_OF')
    constraint.target = armature
    constraint.subtarget = bone_name
    constraint.use_scale_x = False
    constraint.use_scale_y = False
    constraint.use_scale_z = False
    
    # Reset inverse matrix
    bpy.ops.constraint.childof_set_inverse(constraint=constraint.name)
    
    # Apply offset
    prop_obj.location = offset
```

---

## Actions Supportées

| Action | Effet |
|--------|-------|
| `GRAB` | Attach + Show + Activate constraint |
| `DROP` | Deactivate constraint (prop falls) |
| `HIDE` | Hide prop |
| `SHOW` | Show prop (no attach) |
| `SWITCH_SOCKET` | Change socket |

---

## Gestion d'Erreurs

### Props Manquants

Si un prop_id n'existe pas dans la library:
1. Log warning
2. Utiliser `generic_prop.glb` si disponible
3. Sinon, skip l'action

### Bones Non Trouvés

Si un socket ne résout vers aucun bone:
1. Tenter fuzzy matching
2. Log warning
3. Skip l'attachement

### Export Échoué

Si l'export Alembic échoue:
1. Log erreur détaillée
2. Tenter export Blend seul
3. Retourner code erreur

---

## Tâches Implémentées

- [x] Import automatique props (GLB, FBX, BLEND, OBJ)
- [x] Résolution socket → bone avec fallback
- [x] Attachement via contrainte Child Of
- [x] Keyframes visibilité (hide_viewport, hide_render)
- [x] Keyframes influence contrainte
- [x] Export Alembic avec évaluation RENDER
- [x] Backup Blend avec textures packées
- [x] Rapport JSON détaillé
- [x] Mode dry-run pour validation
- [x] Notebook debug V2 (EXO_02_CONTROL)
- [x] Notebook batch V2 (EXO_02_PRODUCTION)
- [x] Bypass conditionnel requires_u02
- [x] Rapport skip (status: SKIPPED)

---

## Contraintes Respectées

1. ✅ **Blender 4.0 Portable** — Utilise le Blender sur Drive
2. ✅ **LOI D'ISOLATION** — Ne dépend d'aucune autre unité
3. ✅ **Argument --drive-root** — Obligatoire sur le wrapper
4. ✅ **Gestion d'erreurs** — Log warning, continue sur erreur
5. ✅ **Props manquants** — Placeholder generic_prop.glb

---

## Statut: 🟢 SCELLÉ

**Version**: v2.0.0
**Date scellement**: 2026-02-27
**Maître de Forge**: Vulkan

---

*EXODUS SYSTEM — Frégate 02_LOGISTICS v2.0.0*
