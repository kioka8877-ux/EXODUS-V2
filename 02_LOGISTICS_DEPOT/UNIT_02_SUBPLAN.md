# SOUS-PLAN TECHNIQUE — UNITÉ 02: LOGISTICS DEPOT

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              FRÉGATE 02_LOGISTICS — PLAN TECHNIQUE COMPLET                   ║
║                        Armurerie de la Flotte EXODUS                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Mission

Assembler les avatars Roblox animés (de U01) avec leurs props selon les instructions du PRODUCTION_PLAN.JSON (de U00 Cortex). Produire des fichiers Alembic équipés prêts pour le rendu.

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
│   ├── EXO_02_CONTROL.ipynb     # Notebook debug
│   └── EXO_02_PRODUCTION.ipynb  # Notebook batch
├── IN_LOGISTICS/
│   ├── actor_animated.blend     # Input: Avatar animé (de U01)
│   ├── PRODUCTION_PLAN.JSON     # Input: Instructions (de U00)
│   └── props_library/           # Arsenal d'objets
│       ├── gun_pistol.glb
│       ├── phone_smartphone.glb
│       └── generic_prop.glb     # Placeholder
├── OUT_EQUIPPED/
│   ├── actor_equipped.abc       # Output: Alembic final
│   ├── actor_equipped.blend     # Output: Backup éditable
│   └── logistics_report.json    # Output: Rapport
├── README_DEV.md                # Documentation développeur
└── UNIT_02_SUBPLAN.md           # Ce fichier
```

---

## Inputs

### 1. actor_animated.blend (de U01)

Avatar Roblox avec:
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
- Tous les meshes (avatar + props)
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
  "version": "1.0.0",
  "status": "SUCCESS",
  "attachments": [...],
  "logs": [...]
}
```

---

## Pipeline Technique

### Phase 1: Validation

```
EXO_02_LOGISTICS.py
    └── Valider chemins inputs
    └── Charger PRODUCTION_PLAN.JSON
    └── Scanner props_library
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
- [x] Notebook debug (EXO_02_CONTROL)
- [x] Notebook batch (EXO_02_PRODUCTION)

---

## Contraintes Respectées

1. ✅ **Blender 4.0 Portable** — Utilise le Blender sur Drive
2. ✅ **LOI D'ISOLATION** — Ne dépend d'aucune autre unité
3. ✅ **Argument --drive-root** — Obligatoire sur le wrapper
4. ✅ **Gestion d'erreurs** — Log warning, continue sur erreur
5. ✅ **Props manquants** — Placeholder generic_prop.glb

---

## Statut: 🟡 EN FORGE

**Date début forge**: 2026-02-03
**Maître de Forge**: Vulkan

---

*EXODUS SYSTEM — Frégate 02_LOGISTICS v1.0.0*
