# GEMINI CHAT METAPROMPT — Mode Injection EXODUS V2

## Utilisation

Ce fichier contient le metaprompt à coller dans **gemini.google.com** (Gemini 2.5 Pro)  
pour obtenir le JSON d'analyse vidéo de qualité supérieure à l'API gratuite.

---

## Étapes

1. Ouvrez [gemini.google.com](https://gemini.google.com) avec un compte Google
2. Sélectionnez **Gemini 2.5 Pro** (modèle le plus puissant)
3. Uploadez votre vidéo source (bouton trombone ou glisser-déposer)
4. Copiez-collez le prompt ci-dessous dans le champ de texte
5. Récupérez le JSON retourné
6. Collez-le dans la variable `INJECTED_JSON_RAW` de la **Cellule 2b** du notebook

---

## Prompt à copier

```
Analyse cette vidéo et génère un JSON structuré pour le pipeline EXODUS V2.

Le JSON doit contenir exactement 3 blocs : production_plan, facial_animation, motion_synthesis.

## BLOC 1 — production_plan

{
  "production_plan": {
    "source_video": "[nom_du_fichier]",
    "total_duration_seconds": [durée_totale],
    "scenes": [
      {
        "scene_id": "scene_001",
        "timecode_start": 0.0,
        "timecode_end": [fin_en_secondes],
        "description": "[description courte de ce qui se passe]",
        "characters": [
          {
            "character_id": "[ID depuis liste autorisée]",
            "actions": ["[animation_id]"],
            "props_actions": []
          }
        ],
        "environment": "[environment_id depuis liste autorisée]",
        "camera": {
          "style": "[camera_id depuis liste autorisée]",
          "ratio": "9:16"
        },
        "lighting": "[lighting_id depuis liste autorisée]",
        "audio": "[audio_id depuis liste autorisée]",
        "production_notes": {
          "requires_u02": false,
          "vfx_notes": ""
        }
      }
    ],
    "global_notes": "[observations globales sur la vidéo]"
  }
}

## BLOC 2 — facial_animation

{
  "facial_animation": {
    "segments": [
      {
        "time_start": 0.0,
        "time_end": 2.0,
        "apex_time": 1.0,
        "character_id": "[même ID que dans production_plan]",
        "expression": "[joy|sadness|anger|fear|surprise|disgust|neutral|suspicious|determined|confused|pain|love|bored|excited|shocked]",
        "intensity": 0.7,
        "eyes": "[focused_forward|looking_left|looking_right|looking_up|looking_down|narrowed|wide_open|closed|winking]",
        "mouth": "[closed_tight|slightly_open|wide_open|smiling|frowning|pursed_lips|shouting|neutral]",
        "head_tilt_deg": 0.0
      }
    ]
  }
}

## BLOC 3 — motion_synthesis

{
  "motion_synthesis": {
    "duration_seconds": [même que total_duration_seconds],
    "segments": [
      {
        "time_start": 0.0,
        "time_end": [fin_en_secondes],
        "character_id": "[même ID]",
        "primary_action": "[description du mouvement principal]",
        "intensity": "medium",
        "style": "natural"
      }
    ]
  }
}

## IDs AUTORISÉS

Personnages : bacon_hair, noob, guest, builderman, robloxian_2_0, rthro_normal, rthro_slender, korblox_deathspeaker, headless_horseman, dominus_infernus

Environnements : classic_baseplate, grass_terrain, desert_terrain, snow_terrain, water_terrain, mountain_terrain, forest, city_street, office_interior, house_interior, school_interior, hospital_interior, space_station, medieval_castle, pirate_ship, obby_course, tycoon_base, murder_mystery_mansion, jailbreak_prison, adopt_me_house

Animations : idle, walk, run, jump, fall, climb, swim, sit, lay, wave, point, dance1, dance2, dance3, laugh, cheer, salute, sword_slash, punch, kick, death, victory

Caméra : static, follow, orbit, dolly, pan, tilt, crane, handheld, first_person, cinematic

Éclairage : daylight, sunset, sunrise, night, overcast, foggy, neon, dramatic, soft, horror

Audio : oof, sword_hit, explosion_sfx, coin_collect, level_up, door_open, footstep, ambient_nature, ambient_city, ambient_horror, epic_orchestral, chill_lofi, action_electronic, comedy_quirky, horror_tension, none

## INSTRUCTIONS

- Génère UN SEUL JSON valide contenant les 3 blocs.
- Ne génère PAS de texte avant ou après le JSON — uniquement le JSON brut.
- Utilise uniquement les IDs listés ci-dessus.
- Les timecodes doivent être cohérents avec la durée réelle de la vidéo.
- Chaque scène doit avoir au moins 1 personnage.
- Les segments facial_animation doivent rester dans les bornes de leur scène parente.
```

---

## Avantage Mode Injection

Gemini 2.5 Pro Chat surpasse les modèles API gratuits pour :
- Vidéos longues (> 2 minutes)
- Scènes complexes avec plusieurs personnages
- Dialogues et interactions nuancées
- Analyse émotionnelle précise

## Note Technique

Le JSON injecté est validé par le schéma EXODUS V2 avant toute utilisation.  
En cas d'erreur de validation, corrigez le JSON ou régénérez-le avec ce prompt.

---

*EXODUS V2 — Décret D-IV — Architecture Duale API/Injection*  
*Maître de Forge : Vulkan | Scribe : CAPY-01 | 23.04.2026.M41*
