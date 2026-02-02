#!/usr/bin/env python3
"""
EXODUS V2 — FRÉGATE 00: CORTEX HQ
Analyse vidéo source → PRODUCTION_PLAN.JSON

Mission: Analyser une vidéo et générer un plan de production structuré
         utilisant exclusivement l'Arsenal Impérial approuvé.

Usage:
    python EXO_00_CORTEX.py --drive-root /path/to/EXODUS --input-video video.mp4
    python EXO_00_CORTEX.py --drive-root /path/to/EXODUS --input-video video.mp4 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ============================================================================
# CONDITIONAL IMPORTS
# ============================================================================

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARN] opencv-python non installé. Métadonnées vidéo limitées.")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARN] google-generativeai non installé. Mode dry-run uniquement.")


# ============================================================================
# IMPERIAL ARSENAL — ASSETS AUTORISÉS (HARDCODÉ)
# ============================================================================

IMPERIAL_ARSENAL = {
    "roblox_characters": {
        "description": "Personnages Roblox officiels disponibles",
        "items": [
            {"id": "bacon_hair", "name": "Bacon Hair", "type": "classic_avatar"},
            {"id": "noob", "name": "Noob (Oof)", "type": "classic_avatar"},
            {"id": "guest", "name": "Guest 666", "type": "classic_avatar"},
            {"id": "builderman", "name": "Builderman", "type": "classic_avatar"},
            {"id": "robloxian_2_0", "name": "Robloxian 2.0", "type": "modern_avatar"},
            {"id": "rthro_normal", "name": "Rthro Normal", "type": "rthro_avatar"},
            {"id": "rthro_slender", "name": "Rthro Slender", "type": "rthro_avatar"},
            {"id": "korblox_deathspeaker", "name": "Korblox Deathspeaker", "type": "premium_avatar"},
            {"id": "headless_horseman", "name": "Headless Horseman", "type": "premium_avatar"},
            {"id": "dominus_infernus", "name": "Dominus Infernus", "type": "legendary_avatar"}
        ]
    },
    "props": {
        "description": "Objets et accessoires disponibles",
        "categories": {
            "weapons": [
                {"id": "linked_sword", "name": "Linked Sword"},
                {"id": "firebrand", "name": "Firebrand"},
                {"id": "darkheart", "name": "Darkheart"},
                {"id": "ghostwalker", "name": "Ghostwalker"},
                {"id": "illumina", "name": "Illumina"},
                {"id": "venomshank", "name": "Venomshank"},
                {"id": "icedagger", "name": "Icedagger"},
                {"id": "windforce", "name": "Windforce"},
                {"id": "classic_bomb", "name": "Classic Bomb"},
                {"id": "rocket_launcher", "name": "Rocket Launcher"},
                {"id": "gravity_coil", "name": "Gravity Coil"},
                {"id": "speed_coil", "name": "Speed Coil"}
            ],
            "vehicles": [
                {"id": "classic_jeep", "name": "Classic Jeep"},
                {"id": "motorcycle", "name": "Motorcycle"},
                {"id": "helicopter", "name": "Helicopter"},
                {"id": "plane", "name": "Plane"},
                {"id": "boat", "name": "Boat"},
                {"id": "skateboard", "name": "Skateboard"},
                {"id": "magic_carpet", "name": "Magic Carpet"}
            ],
            "furniture": [
                {"id": "wooden_chair", "name": "Wooden Chair"},
                {"id": "office_chair", "name": "Office Chair"},
                {"id": "couch", "name": "Couch"},
                {"id": "bed", "name": "Bed"},
                {"id": "table", "name": "Table"},
                {"id": "desk", "name": "Desk"},
                {"id": "lamp", "name": "Lamp"},
                {"id": "bookshelf", "name": "Bookshelf"}
            ],
            "effects": [
                {"id": "sparkles", "name": "Sparkles"},
                {"id": "fire", "name": "Fire"},
                {"id": "smoke", "name": "Smoke"},
                {"id": "explosion", "name": "Explosion"},
                {"id": "confetti", "name": "Confetti"},
                {"id": "hearts", "name": "Hearts"},
                {"id": "music_notes", "name": "Music Notes"},
                {"id": "rain", "name": "Rain"},
                {"id": "snow", "name": "Snow"},
                {"id": "lightning", "name": "Lightning"}
            ],
            "generic": [
                {"id": "generic_prop", "name": "Generic Prop", "note": "Placeholder for unmatched items"}
            ]
        }
    },
    "environments": {
        "description": "Décors et environnements disponibles",
        "items": [
            {"id": "classic_baseplate", "name": "Classic Baseplate", "type": "basic"},
            {"id": "grass_terrain", "name": "Grass Terrain", "type": "nature"},
            {"id": "desert_terrain", "name": "Desert Terrain", "type": "nature"},
            {"id": "snow_terrain", "name": "Snow Terrain", "type": "nature"},
            {"id": "water_terrain", "name": "Water Terrain", "type": "nature"},
            {"id": "mountain_terrain", "name": "Mountain Terrain", "type": "nature"},
            {"id": "forest", "name": "Forest", "type": "nature"},
            {"id": "city_street", "name": "City Street", "type": "urban"},
            {"id": "office_interior", "name": "Office Interior", "type": "interior"},
            {"id": "house_interior", "name": "House Interior", "type": "interior"},
            {"id": "school_interior", "name": "School Interior", "type": "interior"},
            {"id": "hospital_interior", "name": "Hospital Interior", "type": "interior"},
            {"id": "space_station", "name": "Space Station", "type": "scifi"},
            {"id": "medieval_castle", "name": "Medieval Castle", "type": "fantasy"},
            {"id": "pirate_ship", "name": "Pirate Ship", "type": "fantasy"},
            {"id": "obby_course", "name": "Obby Course", "type": "game"},
            {"id": "tycoon_base", "name": "Tycoon Base", "type": "game"},
            {"id": "murder_mystery_mansion", "name": "Murder Mystery Mansion", "type": "game"},
            {"id": "jailbreak_prison", "name": "Jailbreak Prison", "type": "game"},
            {"id": "adopt_me_house", "name": "Adopt Me House", "type": "game"}
        ]
    },
    "animations": {
        "description": "Animations de base disponibles",
        "items": [
            {"id": "idle", "name": "Idle", "type": "basic"},
            {"id": "walk", "name": "Walk", "type": "locomotion"},
            {"id": "run", "name": "Run", "type": "locomotion"},
            {"id": "jump", "name": "Jump", "type": "locomotion"},
            {"id": "fall", "name": "Fall", "type": "locomotion"},
            {"id": "climb", "name": "Climb", "type": "locomotion"},
            {"id": "swim", "name": "Swim", "type": "locomotion"},
            {"id": "sit", "name": "Sit", "type": "pose"},
            {"id": "lay", "name": "Lay Down", "type": "pose"},
            {"id": "wave", "name": "Wave", "type": "emote"},
            {"id": "point", "name": "Point", "type": "emote"},
            {"id": "dance1", "name": "Dance 1", "type": "emote"},
            {"id": "dance2", "name": "Dance 2", "type": "emote"},
            {"id": "dance3", "name": "Dance 3", "type": "emote"},
            {"id": "laugh", "name": "Laugh", "type": "emote"},
            {"id": "cheer", "name": "Cheer", "type": "emote"},
            {"id": "salute", "name": "Salute", "type": "emote"},
            {"id": "sword_slash", "name": "Sword Slash", "type": "combat"},
            {"id": "punch", "name": "Punch", "type": "combat"},
            {"id": "kick", "name": "Kick", "type": "combat"},
            {"id": "death", "name": "Death", "type": "combat"},
            {"id": "victory", "name": "Victory", "type": "combat"}
        ]
    },
    "audio": {
        "description": "Sons et musiques disponibles",
        "items": [
            {"id": "oof", "name": "Oof Sound", "type": "sfx"},
            {"id": "sword_hit", "name": "Sword Hit", "type": "sfx"},
            {"id": "explosion_sfx", "name": "Explosion", "type": "sfx"},
            {"id": "coin_collect", "name": "Coin Collect", "type": "sfx"},
            {"id": "level_up", "name": "Level Up", "type": "sfx"},
            {"id": "door_open", "name": "Door Open", "type": "sfx"},
            {"id": "footstep", "name": "Footstep", "type": "sfx"},
            {"id": "ambient_nature", "name": "Ambient Nature", "type": "ambient"},
            {"id": "ambient_city", "name": "Ambient City", "type": "ambient"},
            {"id": "ambient_horror", "name": "Ambient Horror", "type": "ambient"},
            {"id": "epic_orchestral", "name": "Epic Orchestral", "type": "music"},
            {"id": "chill_lofi", "name": "Chill Lo-Fi", "type": "music"},
            {"id": "action_electronic", "name": "Action Electronic", "type": "music"},
            {"id": "comedy_quirky", "name": "Comedy Quirky", "type": "music"},
            {"id": "horror_tension", "name": "Horror Tension", "type": "music"}
        ]
    },
    "camera_styles": {
        "description": "Styles de caméra disponibles",
        "items": [
            {"id": "static", "name": "Static Shot", "description": "Caméra fixe"},
            {"id": "follow", "name": "Follow Cam", "description": "Suit le personnage"},
            {"id": "orbit", "name": "Orbit Cam", "description": "Tourne autour du sujet"},
            {"id": "dolly", "name": "Dolly Shot", "description": "Travelling avant/arrière"},
            {"id": "pan", "name": "Pan Shot", "description": "Panoramique horizontal"},
            {"id": "tilt", "name": "Tilt Shot", "description": "Panoramique vertical"},
            {"id": "crane", "name": "Crane Shot", "description": "Mouvement vertical"},
            {"id": "handheld", "name": "Handheld", "description": "Caméra à l'épaule"},
            {"id": "first_person", "name": "First Person", "description": "Vue subjective"},
            {"id": "cinematic", "name": "Cinematic", "description": "Plans cinématographiques variés"}
        ]
    },
    "lighting_presets": {
        "description": "Préréglages d'éclairage disponibles",
        "items": [
            {"id": "daylight", "name": "Daylight", "description": "Lumière du jour standard"},
            {"id": "sunset", "name": "Sunset", "description": "Coucher de soleil chaud"},
            {"id": "sunrise", "name": "Sunrise", "description": "Lever de soleil doux"},
            {"id": "night", "name": "Night", "description": "Nuit avec lune"},
            {"id": "overcast", "name": "Overcast", "description": "Ciel couvert"},
            {"id": "foggy", "name": "Foggy", "description": "Brouillard atmosphérique"},
            {"id": "neon", "name": "Neon", "description": "Éclairage néon cyberpunk"},
            {"id": "dramatic", "name": "Dramatic", "description": "Contraste élevé dramatique"},
            {"id": "soft", "name": "Soft", "description": "Lumière douce diffuse"},
            {"id": "horror", "name": "Horror", "description": "Éclairage sombre inquiétant"}
        ]
    }
}


# ============================================================================
# SCENE ANALYSIS PROMPT
# ============================================================================

SCENE_ANALYSIS_PROMPT = """Tu es CORTEX, l'IA d'analyse du pipeline EXODUS V2.

MISSION: Analyser cette vidéo et générer un PRODUCTION_PLAN.JSON pour recréer la scène en animation Roblox.

## ARSENAL IMPÉRIAL (Assets autorisés UNIQUEMENT)
{arsenal_json}

## RÈGLES STRICTES
1. Utilise UNIQUEMENT les IDs de l'Arsenal ci-dessus
2. Si un élément n'existe pas dans l'Arsenal, utilise "generic_prop" ou l'alternative la plus proche
3. Chaque scène doit avoir: characters, props, environment, animations, camera, lighting, audio
4. Découpe la vidéo en scènes logiques (changement de plan = nouvelle scène)
5. Estime les timecodes en secondes

## FORMAT DE SORTIE (JSON STRICT)
```json
{{
  "metadata": {{
    "source_video": "nom_fichier",
    "duration_seconds": 0,
    "fps": 0,
    "resolution": "WxH",
    "analysis_date": "YYYY-MM-DD",
    "cortex_version": "2.0"
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "timecode_start": 0.0,
      "timecode_end": 0.0,
      "description": "Description courte de la scène",
      "characters": [
        {{
          "character_id": "id_from_arsenal",
          "role": "protagonist/antagonist/background",
          "actions": ["animation_id_1", "animation_id_2"]
        }}
      ],
      "props": [
        {{
          "prop_id": "id_from_arsenal",
          "quantity": 1,
          "interaction": "held/placed/animated"
        }}
      ],
      "environment": {{
        "environment_id": "id_from_arsenal",
        "modifications": ["description des modifications si nécessaire"]
      }},
      "camera": {{
        "style_id": "id_from_arsenal",
        "movements": ["description des mouvements"]
      }},
      "lighting": {{
        "preset_id": "id_from_arsenal",
        "adjustments": ["modifications si nécessaire"]
      }},
      "audio": {{
        "music_id": "id_from_arsenal_or_null",
        "sfx": ["sfx_id_1", "sfx_id_2"],
        "ambient_id": "id_from_arsenal_or_null"
      }}
    }}
  ],
  "production_notes": {{
    "complexity_score": 1-10,
    "estimated_render_hours": 0,
    "special_requirements": ["liste des besoins spéciaux"],
    "warnings": ["problèmes potentiels identifiés"]
  }}
}}
```

Analyse la vidéo et génère le JSON complet. Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
"""


# ============================================================================
# LOGGING
# ============================================================================

class CortexLogger:
    """Logger structuré pour CORTEX."""
    
    LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "WARN": 2,
        "ERROR": 3
    }
    
    def __init__(self, level: str = "INFO"):
        self.level = self.LEVELS.get(level.upper(), 1)
        self.start_time = datetime.now()
    
    def _log(self, level: str, message: str, **kwargs):
        if self.LEVELS.get(level, 0) >= self.level:
            timestamp = datetime.now().strftime("%H:%M:%S")
            elapsed = (datetime.now() - self.start_time).total_seconds()
            prefix = f"[{timestamp}][+{elapsed:.1f}s][{level}]"
            
            extra = ""
            if kwargs:
                extra = " | " + " ".join(f"{k}={v}" for k, v in kwargs.items())
            
            print(f"{prefix} {message}{extra}")
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        self._log("WARN", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)


# ============================================================================
# VIDEO METADATA
# ============================================================================

def get_video_metadata(video_path: Path, logger: CortexLogger) -> dict:
    """Extrait les métadonnées de la vidéo source."""
    
    metadata = {
        "source_video": video_path.name,
        "duration_seconds": 0,
        "fps": 30,
        "resolution": "1920x1080",
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "cortex_version": "2.0"
    }
    
    if not CV2_AVAILABLE:
        logger.warn("OpenCV non disponible, métadonnées par défaut utilisées")
        return metadata
    
    try:
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            metadata["fps"] = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            metadata["duration_seconds"] = round(frame_count / metadata["fps"], 2) if metadata["fps"] > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            metadata["resolution"] = f"{width}x{height}"
            cap.release()
            logger.info(f"Métadonnées extraites", **metadata)
        else:
            logger.warn(f"Impossible d'ouvrir la vidéo: {video_path}")
    except Exception as e:
        logger.error(f"Erreur extraction métadonnées: {e}")
    
    return metadata


# ============================================================================
# JSON VALIDATION
# ============================================================================

def validate_json_output(json_data: dict, logger: CortexLogger) -> dict:
    """Valide et corrige le JSON de sortie."""
    
    valid_ids = set()
    
    # Collect all valid IDs from arsenal
    for category, content in IMPERIAL_ARSENAL.items():
        if "items" in content:
            for item in content["items"]:
                valid_ids.add(item["id"])
        if "categories" in content:
            for cat_items in content["categories"].values():
                for item in cat_items:
                    valid_ids.add(item["id"])
    
    corrections = []
    
    def validate_id(id_value: str, context: str) -> str:
        if id_value is None or id_value == "null":
            return None
        if id_value in valid_ids:
            return id_value
        # Auto-correct to generic_prop
        corrections.append(f"{context}: '{id_value}' → 'generic_prop'")
        return "generic_prop"
    
    # Validate scenes
    if "scenes" in json_data:
        for i, scene in enumerate(json_data["scenes"]):
            # Validate characters
            if "characters" in scene:
                for char in scene["characters"]:
                    if "character_id" in char:
                        char["character_id"] = validate_id(
                            char["character_id"], 
                            f"Scene {i+1} character"
                        )
                    if "actions" in char:
                        char["actions"] = [
                            validate_id(a, f"Scene {i+1} action") or "idle"
                            for a in char["actions"]
                        ]
            
            # Validate props
            if "props" in scene:
                for prop in scene["props"]:
                    if "prop_id" in prop:
                        prop["prop_id"] = validate_id(
                            prop["prop_id"],
                            f"Scene {i+1} prop"
                        )
            
            # Validate environment
            if "environment" in scene and "environment_id" in scene["environment"]:
                scene["environment"]["environment_id"] = validate_id(
                    scene["environment"]["environment_id"],
                    f"Scene {i+1} environment"
                ) or "classic_baseplate"
            
            # Validate camera
            if "camera" in scene and "style_id" in scene["camera"]:
                scene["camera"]["style_id"] = validate_id(
                    scene["camera"]["style_id"],
                    f"Scene {i+1} camera"
                ) or "static"
            
            # Validate lighting
            if "lighting" in scene and "preset_id" in scene["lighting"]:
                scene["lighting"]["preset_id"] = validate_id(
                    scene["lighting"]["preset_id"],
                    f"Scene {i+1} lighting"
                ) or "daylight"
            
            # Validate audio
            if "audio" in scene:
                audio = scene["audio"]
                if "music_id" in audio:
                    audio["music_id"] = validate_id(audio["music_id"], f"Scene {i+1} music")
                if "ambient_id" in audio:
                    audio["ambient_id"] = validate_id(audio["ambient_id"], f"Scene {i+1} ambient")
                if "sfx" in audio:
                    audio["sfx"] = [
                        validate_id(s, f"Scene {i+1} sfx") or "oof"
                        for s in audio["sfx"] if s
                    ]
    
    if corrections:
        logger.warn(f"Auto-corrections appliquées: {len(corrections)}")
        for c in corrections[:5]:
            logger.debug(c)
        if len(corrections) > 5:
            logger.debug(f"... et {len(corrections) - 5} autres corrections")
    
    return json_data


def extract_json_from_response(response_text: str, logger: CortexLogger) -> Optional[dict]:
    """Extrait et parse le JSON depuis la réponse Gemini."""
    
    # Try direct parse first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in markdown code blocks
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response_text)
        for match in matches:
            try:
                text = match if isinstance(match, str) else match[0]
                # Find the JSON object
                start = text.find('{')
                if start != -1:
                    # Find matching closing brace
                    depth = 0
                    for i, char in enumerate(text[start:], start):
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                json_str = text[start:i+1]
                                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue
    
    logger.error("Impossible d'extraire le JSON de la réponse")
    return None


# ============================================================================
# GEMINI API
# ============================================================================

def call_gemini(
    video_path: Path,
    metadata: dict,
    logger: CortexLogger,
    max_retries: int = 3,
    model_name: str = "gemini-2.5-flash"
) -> Optional[dict]:
    """Appelle Gemini pour analyser la vidéo avec retry logic."""
    
    if not GENAI_AVAILABLE:
        logger.error("google-generativeai non installé")
        return None
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY non définie")
        return None
    
    genai.configure(api_key=api_key)
    
    # Prepare prompt with arsenal
    arsenal_json = json.dumps(IMPERIAL_ARSENAL, indent=2, ensure_ascii=False)
    prompt = SCENE_ANALYSIS_PROMPT.format(arsenal_json=arsenal_json)
    
    # Upload video
    logger.info(f"Upload vidéo vers Gemini: {video_path.name}")
    try:
        video_file = genai.upload_file(path=str(video_path))
        logger.info(f"Upload terminé: {video_file.uri}")
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            logger.debug("Traitement vidéo en cours...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            logger.error(f"Échec traitement vidéo: {video_file.state.name}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur upload: {e}")
        return None
    
    # Call model with retry
    model = genai.GenerativeModel(model_name)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Appel Gemini (tentative {attempt + 1}/{max_retries})")
            
            response = model.generate_content(
                [video_file, prompt],
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=8192
                )
            )
            
            if response.text:
                logger.info("Réponse reçue, extraction JSON...")
                json_data = extract_json_from_response(response.text, logger)
                
                if json_data:
                    # Inject metadata
                    json_data["metadata"] = metadata
                    # Validate and correct
                    json_data = validate_json_output(json_data, logger)
                    logger.info("JSON validé avec succès")
                    return json_data
                else:
                    logger.warn(f"Tentative {attempt + 1}: JSON invalide")
            else:
                logger.warn(f"Tentative {attempt + 1}: Réponse vide")
                
        except Exception as e:
            logger.error(f"Tentative {attempt + 1} échouée: {e}")
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 5
            logger.info(f"Attente {wait_time}s avant retry...")
            time.sleep(wait_time)
    
    logger.error(f"Échec après {max_retries} tentatives")
    return None


# ============================================================================
# OUTPUT
# ============================================================================

def finalize_output(
    json_data: dict,
    output_path: Path,
    logger: CortexLogger,
    dry_run: bool = False
) -> bool:
    """Finalise et écrit le fichier de sortie."""
    
    if dry_run:
        logger.info("=== MODE DRY-RUN ===")
        logger.info(f"Output path: {output_path}")
        logger.info("JSON preview:")
        print(json.dumps(json_data, indent=2, ensure_ascii=False)[:2000])
        if len(json.dumps(json_data)) > 2000:
            print("... [truncated]")
        return True
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"PRODUCTION_PLAN.JSON écrit: {output_path}")
        logger.info(f"Taille: {output_path.stat().st_size} bytes")
        
        # Summary
        if "scenes" in json_data:
            logger.info(f"Scènes analysées: {len(json_data['scenes'])}")
        if "production_notes" in json_data:
            notes = json_data["production_notes"]
            if "complexity_score" in notes:
                logger.info(f"Score complexité: {notes['complexity_score']}/10")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur écriture: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EXODUS V2 — CORTEX: Analyse vidéo → PRODUCTION_PLAN.JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s --drive-root /content/drive/MyDrive/EXODUS --input-video video.mp4
  %(prog)s --drive-root ./EXODUS --input-video test.mp4 --dry-run
  %(prog)s --drive-root /data/EXODUS --input-video source.mp4 --model gemini-2.0-flash
        """
    )
    
    parser.add_argument(
        "--drive-root",
        type=str,
        required=True,
        help="Chemin racine EXODUS (contient 00_CORTEX_HQ/)"
    )
    
    parser.add_argument(
        "--input-video",
        type=str,
        required=True,
        help="Nom du fichier vidéo (cherché dans IN_VIDEO_SOURCE/)"
    )
    
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Nom du fichier JSON de sortie (défaut: PRODUCTION_PLAN_<video>.json)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Modèle Gemini à utiliser (défaut: gemini-2.5-flash)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exécute sans appeler Gemini (test local)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Active les logs DEBUG"
    )
    
    args = parser.parse_args()
    
    # Initialize logger
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = CortexLogger(level=log_level)
    
    logger.info("=" * 60)
    logger.info("EXODUS V2 — FRÉGATE 00: CORTEX HQ")
    logger.info("=" * 60)
    
    # Resolve paths
    drive_root = Path(args.drive_root).resolve()
    cortex_dir = drive_root / "00_CORTEX_HQ"
    input_dir = cortex_dir / "IN_VIDEO_SOURCE"
    output_dir = cortex_dir / "OUT_MANIFEST"
    
    video_path = input_dir / args.input_video
    
    # Validate paths
    if not drive_root.exists():
        logger.error(f"Drive root non trouvé: {drive_root}")
        sys.exit(1)
    
    if not video_path.exists():
        # Try direct path
        video_path = Path(args.input_video).resolve()
        if not video_path.exists():
            logger.error(f"Vidéo non trouvée: {args.input_video}")
            logger.info(f"Chemins vérifiés:")
            logger.info(f"  - {input_dir / args.input_video}")
            logger.info(f"  - {video_path}")
            sys.exit(1)
    
    logger.info(f"Vidéo source: {video_path}")
    logger.info(f"Output dir: {output_dir}")
    
    # Get video metadata
    metadata = get_video_metadata(video_path, logger)
    
    # Determine output filename
    if args.output_name:
        output_name = args.output_name
    else:
        video_stem = video_path.stem
        output_name = f"PRODUCTION_PLAN_{video_stem}.json"
    
    output_path = output_dir / output_name
    
    # Dry run mode
    if args.dry_run:
        logger.info("Mode dry-run activé")
        
        # Generate mock output
        mock_output = {
            "metadata": metadata,
            "scenes": [
                {
                    "scene_id": 1,
                    "timecode_start": 0.0,
                    "timecode_end": 5.0,
                    "description": "[DRY-RUN] Scène de test",
                    "characters": [
                        {
                            "character_id": "bacon_hair",
                            "role": "protagonist",
                            "actions": ["idle", "walk"]
                        }
                    ],
                    "props": [
                        {
                            "prop_id": "linked_sword",
                            "quantity": 1,
                            "interaction": "held"
                        }
                    ],
                    "environment": {
                        "environment_id": "classic_baseplate",
                        "modifications": []
                    },
                    "camera": {
                        "style_id": "static",
                        "movements": []
                    },
                    "lighting": {
                        "preset_id": "daylight",
                        "adjustments": []
                    },
                    "audio": {
                        "music_id": None,
                        "sfx": ["oof"],
                        "ambient_id": None
                    }
                }
            ],
            "production_notes": {
                "complexity_score": 3,
                "estimated_render_hours": 1,
                "special_requirements": ["[DRY-RUN] Aucune analyse réelle effectuée"],
                "warnings": ["Mode test uniquement"]
            }
        }
        
        finalize_output(mock_output, output_path, logger, dry_run=True)
        logger.info("Dry-run terminé avec succès")
        sys.exit(0)
    
    # Real execution
    logger.info("Démarrage analyse Gemini...")
    
    result = call_gemini(
        video_path=video_path,
        metadata=metadata,
        logger=logger,
        model_name=args.model
    )
    
    if result:
        success = finalize_output(result, output_path, logger)
        if success:
            logger.info("=" * 60)
            logger.info("MISSION ACCOMPLIE — CORTEX TERMINÉ")
            logger.info("=" * 60)
            sys.exit(0)
        else:
            logger.error("Échec écriture fichier")
            sys.exit(1)
    else:
        logger.error("Échec analyse Gemini")
        sys.exit(1)


if __name__ == "__main__":
    main()
