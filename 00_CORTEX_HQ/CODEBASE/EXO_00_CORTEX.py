#!/usr/bin/env python3
"""
EXODUS V2 — FRÉGATE 00: CORTEX HQ
Orchestrateur 6-moteurs séquentiel → Master JSON V2

Phases:
    Phase 1 CPU (0 VRAM)  : M2 Audio + M3 FOV
    Phase 2 API (0 VRAM)  : M1 Gemini (response_schema) → Dispatcher → M4 + M5
    Phase 3 GPU-A (~3.5GB) : M6 DepthAnything [STUB]
    Phase 4 GPU-B (~4GB)   : M7 SAM [STUB]

Usage:
    python EXO_00_CORTEX.py --drive-root /path/to/EXODUS --input-video video.mp4
    python EXO_00_CORTEX.py --drive-root /path/to/EXODUS --input-video video.mp4 --dry-run
    python EXO_00_CORTEX.py --drive-root /path/to/EXODUS --input-video video.mp4 --rerun audio_extraction
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from math import gcd
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
    from google.generativeai import types as content_types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARN] google-generativeai non installé. Mode dry-run uniquement.")

try:
    import subprocess
    SUBPROCESS_AVAILABLE = True
except ImportError:
    SUBPROCESS_AVAILABLE = False


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
# ENUMS EXTRAITS DE L'ARSENAL (pour response_schema + validation)
# ============================================================================

CHARACTER_IDS = [c["id"] for c in IMPERIAL_ARSENAL["roblox_characters"]["items"]]

PROP_IDS = []
for _category in IMPERIAL_ARSENAL["props"]["categories"].values():
    PROP_IDS.extend([p["id"] for p in _category])
PROP_IDS.append("none")

ENVIRONMENT_IDS = [e["id"] for e in IMPERIAL_ARSENAL["environments"]["items"]]
ANIMATION_IDS = [a["id"] for a in IMPERIAL_ARSENAL["animations"]["items"]]
CAMERA_IDS = [c["id"] for c in IMPERIAL_ARSENAL["camera_styles"]["items"]]
LIGHTING_IDS = [l["id"] for l in IMPERIAL_ARSENAL["lighting_presets"]["items"]]
AUDIO_IDS = [a["id"] for a in IMPERIAL_ARSENAL["audio"]["items"]] + ["none"]

EXPRESSION_ENUM = [
    "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral",
    "suspicious", "determined", "confused", "pain", "love", "bored",
    "excited", "shocked"
]
EYES_ENUM = [
    "focused_forward", "looking_left", "looking_right", "looking_up",
    "looking_down", "narrowed", "wide_open", "closed", "winking"
]
MOUTH_ENUM = [
    "closed_tight", "slightly_open", "wide_open", "smiling", "frowning",
    "pursed_lips", "shouting", "neutral"
]
ROLE_ENUM = ["protagonist", "antagonist", "background"]
INTERACTION_ENUM = ["held", "placed", "animated", "worn"]
RATIO_ENUM = ["9:16", "16:9", "4:3", "1:1"]
MOTION_STYLE_ENUM = [
    "casual", "athletic", "dramatic", "comedic", "aggressive",
    "elegant", "robotic", "urgent"
]


# ============================================================================
# RESPONSE SCHEMA — MASTER JSON V2
# ============================================================================

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "production_plan": {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "source_video": {"type": "string"},
                        "duration_seconds": {"type": "number"},
                        "fps": {"type": "integer"},
                        "resolution": {"type": "string"},
                        "analysis_date": {"type": "string"},
                        "cortex_version": {"type": "string"}
                    },
                    "required": ["source_video", "duration_seconds", "fps",
                                 "resolution", "analysis_date", "cortex_version"]
                },
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "scene_id": {"type": "integer"},
                            "timecode_start": {"type": "number"},
                            "timecode_end": {"type": "number"},
                            "description": {"type": "string"},
                            "characters": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "character_id": {"type": "string", "enum": CHARACTER_IDS},
                                        "role": {"type": "string", "enum": ROLE_ENUM},
                                        "actions": {
                                            "type": "array",
                                            "items": {"type": "string", "enum": ANIMATION_IDS}
                                        }
                                    },
                                    "required": ["character_id", "role", "actions"]
                                }
                            },
                            "props": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "prop_id": {"type": "string", "enum": PROP_IDS},
                                        "quantity": {"type": "integer"},
                                        "interaction": {"type": "string", "enum": INTERACTION_ENUM}
                                    },
                                    "required": ["prop_id", "quantity", "interaction"]
                                }
                            },
                            "environment": {
                                "type": "object",
                                "properties": {
                                    "environment_id": {"type": "string", "enum": ENVIRONMENT_IDS},
                                    "modifications": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["environment_id", "modifications"]
                            },
                            "camera": {
                                "type": "object",
                                "properties": {
                                    "style_id": {"type": "string", "enum": CAMERA_IDS},
                                    "movements": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["style_id", "movements"]
                            },
                            "lighting": {
                                "type": "object",
                                "properties": {
                                    "preset_id": {"type": "string", "enum": LIGHTING_IDS},
                                    "adjustments": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["preset_id", "adjustments"]
                            },
                            "audio": {
                                "type": "object",
                                "properties": {
                                    "music_id": {"type": "string", "enum": AUDIO_IDS},
                                    "sfx": {
                                        "type": "array",
                                        "items": {"type": "string", "enum": AUDIO_IDS}
                                    },
                                    "ambient_id": {"type": "string", "enum": AUDIO_IDS}
                                },
                                "required": ["music_id", "sfx", "ambient_id"]
                            }
                        },
                        "required": ["scene_id", "timecode_start", "timecode_end",
                                     "description", "characters", "props",
                                     "environment", "camera", "lighting", "audio"]
                    }
                },
                "production_notes": {
                    "type": "object",
                    "properties": {
                        "complexity_score": {"type": "integer"},
                        "estimated_render_hours": {"type": "number"},
                        "special_requirements": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "warnings": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "requires_u02": {"type": "boolean"}
                    },
                    "required": ["complexity_score", "estimated_render_hours",
                                 "special_requirements", "warnings", "requires_u02"]
                }
            },
            "required": ["metadata", "scenes", "production_notes"]
        },
        "facial_animation": {
            "type": "object",
            "properties": {
                "sequence_id": {"type": "string"},
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "time_start": {"type": "number"},
                            "time_end": {"type": "number"},
                            "character_id": {"type": "string", "enum": CHARACTER_IDS},
                            "expression": {"type": "string", "enum": EXPRESSION_ENUM},
                            "intensity": {"type": "number"},
                            "eyes": {"type": "string", "enum": EYES_ENUM},
                            "mouth": {"type": "string", "enum": MOUTH_ENUM},
                            "apex_time": {"type": "number"},
                            "low_visibility": {"type": "boolean"}
                        },
                        "required": ["time_start", "time_end", "character_id",
                                     "expression", "intensity", "eyes", "mouth",
                                     "apex_time", "low_visibility"]
                    }
                }
            },
            "required": ["sequence_id", "segments"]
        },
        "motion_synthesis": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "duration_seconds": {"type": "number"},
                "style": {"type": "string", "enum": MOTION_STYLE_ENUM},
                "ratio": {"type": "string", "enum": RATIO_ENUM}
            },
            "required": ["prompt", "duration_seconds", "style", "ratio"]
        }
    },
    "required": ["production_plan", "facial_animation", "motion_synthesis"]
}


# ============================================================================
# MASTER PROMPT — GEMINI V2
# ============================================================================

MASTER_PROMPT = """Tu es CORTEX, le moteur d'analyse sémantique du pipeline EXODUS V2.

MISSION : Analyser cette vidéo et produire un plan de production en 3 blocs pour recréer la scène en animation Roblox.

## ARSENAL IMPÉRIAL — IDs disponibles

Personnages : {character_ids}
Props : {prop_ids}
Environnements : {environment_ids}
Animations : {animation_ids}
Caméra : {camera_ids}
Éclairage : {lighting_ids}
Audio : {audio_ids}

## MÉTADONNÉES SOURCE

Fichier : {source_video}
Durée : {duration_seconds}s | FPS : {fps} | Résolution : {resolution}

## CONSIGNES

1. Découpe la vidéo en scènes logiques (changement de plan = nouvelle scène).
2. Utilise UNIQUEMENT les IDs listés ci-dessus. Si un élément n'existe pas, utilise l'alternative la plus proche ou "generic_prop" / "none".
3. Le mot-clé "none" remplace null — ne jamais renvoyer de valeur nulle.
4. Timecodes en secondes avec 3 décimales (ex: 1.250, 3.750).
5. Intensité faciale entre 0.0 et 1.0.
6. Si le visage d'un personnage n'est pas visible dans un segment, mets low_visibility à true mais remplis quand même les champs expression/eyes/mouth avec une estimation contextuelle.
7. Le champ requires_u02 dans production_notes doit être true si au moins un prop est utilisé dans les scènes, false sinon.

## BLOC 1 — production_plan
Plan de production complet avec metadata, scenes[], et production_notes.
Chaque scène contient : characters, props, environment, camera, lighting, audio.

## BLOC 2 — facial_animation
Séquence d'animation faciale. sequence_id = nom du fichier source sans extension.
Chaque segment couvre un intervalle temporel pour un personnage avec expression, intensité, yeux, bouche, apex_time (moment du pic d'émotion dans le segment).

## BLOC 3 — motion_synthesis
Un prompt textuel décrivant le mouvement global de la scène pour un moteur de synthèse de mouvement.
Inclut durée, style de mouvement, et ratio d'image.

Analyse la vidéo et remplis les 3 blocs. Le format est contraint par le schéma — concentre-toi sur le contenu."""


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
# JSON EXTRACTION (FALLBACK)
# ============================================================================

def extract_json_from_response(response_text: str, logger: CortexLogger) -> Optional[dict]:
    """Extrait et parse le JSON depuis la réponse Gemini."""
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
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
                start = text.find('{')
                if start != -1:
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
# MOTOR STATUS — SUIVI DES MOTEURS
# ============================================================================

class MotorStatus:
    """Suivi de l'état de chaque moteur d'extraction."""
    
    MOTORS = [
        "gemini_semantic", "audio_extraction", "fov_extraction",
        "depth_anything", "sam_segmentation"
    ]
    
    IMPACT_MAP = {
        "gemini_semantic":  ["U01", "U02", "U03", "U04", "U05", "U06"],
        "depth_anything":   ["U03"],
        "sam_segmentation": ["U03"],
        "audio_extraction": ["U06"],
        "fov_extraction":   ["U04"],
    }
    
    def __init__(self):
        self.results = {
            m: {"status": "pending", "output": None, "error": None}
            for m in self.MOTORS
        }
    
    def mark_success(self, motor: str, output_path: Optional[str] = None):
        self.results[motor]["status"] = "success"
        self.results[motor]["output"] = str(output_path) if output_path else None
    
    def mark_failed(self, motor: str, error: str):
        self.results[motor]["status"] = "failed"
        self.results[motor]["error"] = error
    
    def mark_partial(self, motor: str, done: int, total: int,
                     output_path: Optional[str] = None):
        self.results[motor]["status"] = "partial"
        self.results[motor]["frames_done"] = done
        self.results[motor]["frames_total"] = total
        self.results[motor]["output"] = str(output_path) if output_path else None
    
    def get_flags(self) -> dict:
        """Génère le bloc flags pour PRODUCTION_PLAN.JSON."""
        failed = [m for m, r in self.results.items() if r["status"] == "failed"]
        partial = [m for m, r in self.results.items() if r["status"] == "partial"]
        return {
            "all_motors_ok": len(failed) == 0 and len(partial) == 0,
            "partial_failure": [
                {
                    "motor": m,
                    "error": self.results[m]["error"],
                    "impact": self.IMPACT_MAP.get(m, [])
                }
                for m in failed
            ],
            "partial_success": [
                {
                    "motor": m,
                    "frames_done": self.results[m].get("frames_done", 0),
                    "frames_total": self.results[m].get("frames_total", 0)
                }
                for m in partial
            ],
            "manual_review_required": len(failed) > 0,
            "warnings": []
        }


# ============================================================================
# M2 — AUDIO EXTRACTION (FFmpeg)
# ============================================================================

def run_audio_extraction(video_path: Path, output_path: Path,
                         logger: CortexLogger) -> bool:
    """M2 — Extrait la piste audio via FFmpeg."""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 44:
            logger.info(f"Audio extrait: {output_path} ({output_path.stat().st_size} bytes)")
            return True
        else:
            logger.error(f"FFmpeg échoué: {result.stderr[:500]}")
            return False
    except FileNotFoundError:
        logger.error("FFmpeg non trouvé. Installer: apt install ffmpeg")
        return False
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout (120s)")
        return False
    except Exception as e:
        logger.error(f"Erreur audio extraction: {e}")
        return False


# ============================================================================
# M3 — FOV / RATIO EXTRACTION (OpenCV)
# ============================================================================

def run_fov_extraction(video_path: Path, output_path: Path,
                       logger: CortexLogger) -> bool:
    """M3 — Extrait FOV, ratio et métadonnées optiques."""
    
    if not CV2_AVAILABLE:
        logger.error("OpenCV requis pour l'extraction FOV")
        return False
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Impossible d'ouvrir: {video_path}")
        return False
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    g = gcd(width, height) if width > 0 and height > 0 else 1
    ratio_w, ratio_h = width // g, height // g
    ratio_str = f"{ratio_w}:{ratio_h}"
    
    standard_ratios = {"9:16": (9, 16), "16:9": (16, 9), "4:3": (4, 3), "1:1": (1, 1)}
    best_ratio = min(
        standard_ratios.keys(),
        key=lambda r: abs(standard_ratios[r][0] / standard_ratios[r][1] - width / height)
    ) if height > 0 else "16:9"
    
    estimated_fov = 70.0 if width > height else 60.0
    
    fov_data = {
        "resolution": [width, height],
        "ratio": best_ratio,
        "ratio_raw": ratio_str,
        "fps_source": fps,
        "frame_count": frame_count,
        "duration_seconds": round(frame_count / fps, 3) if fps > 0 else 0,
        "estimated_fov_degrees": estimated_fov
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fov_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"FOV extrait: {best_ratio}, {width}x{height}, {fps}fps")
    return True


# ============================================================================
# M6 — DEPTH ANYTHING V2 [STUB]
# ============================================================================

def run_depth_anything(video_path: Path, output_dir: Path,
                       logger: CortexLogger,
                       model_path: Optional[Path] = None) -> bool:
    """M6 — DepthAnything V2 [STUB — implémenté dans Task B]."""
    logger.warn("MOTEUR DEPTH_ANYTHING: STUB — pas encore implémenté")
    logger.warn("Ce moteur sera ajouté dans la prochaine mise à jour")
    return False


# ============================================================================
# M7 — SAM SEGMENTATION [STUB]
# ============================================================================

def run_sam_segmentation(video_path: Path, output_path: Path,
                         logger: CortexLogger,
                         model_path: Optional[Path] = None) -> bool:
    """M7 — SAM Segmentation [STUB — implémenté dans Task B]."""
    logger.warn("MOTEUR SAM: STUB — pas encore implémenté")
    logger.warn("Ce moteur sera ajouté dans la prochaine mise à jour")
    return False


# ============================================================================
# M1 — GEMINI V2 (response_schema)
# ============================================================================

def call_gemini_v2(video_path: Path, metadata: dict, logger: CortexLogger,
                   model_name: str = "gemini-2.0-flash",
                   max_retries: int = 3) -> Optional[dict]:
    """Appelle Gemini avec response_schema pour obtenir le Master JSON V2."""
    
    if not GENAI_AVAILABLE:
        logger.error("google-generativeai non installé")
        return None
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY non définie")
        return None
    
    genai.configure(api_key=api_key)
    
    prompt = MASTER_PROMPT.format(
        character_ids=", ".join(CHARACTER_IDS),
        prop_ids=", ".join(PROP_IDS),
        environment_ids=", ".join(ENVIRONMENT_IDS),
        animation_ids=", ".join(ANIMATION_IDS),
        camera_ids=", ".join(CAMERA_IDS),
        lighting_ids=", ".join(LIGHTING_IDS),
        audio_ids=", ".join(AUDIO_IDS),
        source_video=metadata.get("source_video", "unknown"),
        duration_seconds=metadata.get("duration_seconds", 0),
        fps=metadata.get("fps", 30),
        resolution=metadata.get("resolution", "1920x1080"),
    )
    
    logger.info(f"Upload vidéo vers Gemini: {video_path.name}")
    try:
        video_file = genai.upload_file(path=str(video_path))
        logger.info(f"Upload terminé: {video_file.uri}")
        
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
    
    model = genai.GenerativeModel(model_name)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Appel Gemini (tentative {attempt + 1}/{max_retries})")
            
            response = model.generate_content(
                [video_file, prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.2,
                    max_output_tokens=16384,
                ),
            )
            
            if response.text:
                logger.info("Réponse reçue, extraction JSON...")
                try:
                    json_data = json.loads(response.text)
                except json.JSONDecodeError:
                    logger.warn("response_schema parse échoué, fallback extraction...")
                    json_data = extract_json_from_response(response.text, logger)
                
                if json_data:
                    logger.info("Master JSON V2 obtenu avec succès")
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
# NORMALIZE TIMECODES
# ============================================================================

def normalize_timecodes(master_json: dict, logger: CortexLogger) -> dict:
    """Force la cohérence temporelle entre les 3 blocs.
    Les timecodes de production_plan.scenes sont la RÉFÉRENCE.
    Les segments facial_animation sont RECALÉS dessus."""
    
    pp = master_json.get("production_plan", {})
    fa = master_json.get("facial_animation", {})
    ms = master_json.get("motion_synthesis", {})
    scenes = pp.get("scenes", [])
    segments = fa.get("segments", [])
    
    if not scenes:
        logger.warn("Aucune scène dans production_plan — skip normalisation")
        return master_json
    
    scene_boundaries = [
        (s.get("timecode_start", 0), s.get("timecode_end", 0))
        for s in scenes
    ]
    total_start = scene_boundaries[0][0]
    total_end = scene_boundaries[-1][1]
    total_duration = total_end - total_start
    
    for seg in segments:
        t_start = seg.get("time_start", 0)
        t_end = seg.get("time_end", 0)
        midpoint = (t_start + t_end) / 2.0
        
        parent_scene = None
        for sb_start, sb_end in scene_boundaries:
            if sb_start <= midpoint <= sb_end:
                parent_scene = (sb_start, sb_end)
                break
        
        if parent_scene is None:
            dists = [(abs(midpoint - (s + e) / 2), (s, e)) for s, e in scene_boundaries]
            parent_scene = min(dists, key=lambda x: x[0])[1]
        
        seg["time_start"] = round(max(seg["time_start"], parent_scene[0]), 3)
        seg["time_end"] = round(min(seg["time_end"], parent_scene[1]), 3)
        
        if seg["time_start"] >= seg["time_end"]:
            seg["time_end"] = round(seg["time_start"] + 0.1, 3)
        
        apex = seg.get("apex_time", seg["time_start"])
        seg["apex_time"] = round(max(seg["time_start"], min(apex, seg["time_end"])), 3)
    
    segments.sort(key=lambda s: s["time_start"])
    for i in range(len(segments) - 1):
        if segments[i]["time_end"] > segments[i + 1]["time_start"]:
            segments[i]["time_end"] = segments[i + 1]["time_start"]
            if segments[i]["time_start"] >= segments[i]["time_end"]:
                segments[i]["time_end"] = round(segments[i]["time_start"] + 0.001, 3)
            segments[i]["apex_time"] = round(
                max(segments[i]["time_start"],
                    min(segments[i]["apex_time"], segments[i]["time_end"])),
                3
            )
    
    if total_duration > 0 and ms.get("duration_seconds"):
        ms_dur = ms["duration_seconds"]
        if abs(ms_dur - total_duration) > 1.0:
            logger.warn(f"motion_synthesis.duration_seconds recalé: {ms_dur} → {total_duration}")
            ms["duration_seconds"] = round(total_duration, 3)
    
    logger.info(f"Timecodes normalisés: {len(segments)} segments, durée totale {total_duration:.3f}s")
    return master_json


# ============================================================================
# VALIDATION — STRUCTURE (Niveau 2)
# ============================================================================

def validate_structure(master_json: dict, logger: CortexLogger) -> tuple:
    """Niveau 2 — Vérifie que la structure est complète.
    Retourne (is_valid: bool, errors: list[str])."""
    
    errors = []
    
    pp = master_json.get("production_plan")
    if not pp:
        errors.append("production_plan manquant")
        return (False, errors)
    
    scenes = pp.get("scenes", [])
    if not scenes:
        errors.append("production_plan.scenes vide")
    
    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", i + 1)
        prefix = f"scene[{sid}]"
        
        for field in ["scene_id", "timecode_start", "timecode_end", "description",
                       "characters", "environment", "camera", "lighting", "audio"]:
            if field not in scene:
                errors.append(f"{prefix}: champ '{field}' manquant")
        
        t_start = scene.get("timecode_start", 0)
        t_end = scene.get("timecode_end", 0)
        if t_start >= t_end:
            errors.append(f"{prefix}: timecode_start ({t_start}) >= timecode_end ({t_end})")
        
        chars = scene.get("characters", [])
        if not chars:
            errors.append(f"{prefix}: aucun character")
        
        for j, ch in enumerate(chars):
            cid = ch.get("character_id", "")
            if cid and cid not in CHARACTER_IDS:
                errors.append(f"{prefix}.characters[{j}]: ID inconnu '{cid}'")
            for action in ch.get("actions", []):
                if action not in ANIMATION_IDS:
                    errors.append(f"{prefix}.characters[{j}].actions: ID inconnu '{action}'")
        
        for j, prop in enumerate(scene.get("props", [])):
            pid = prop.get("prop_id", "")
            if pid and pid not in PROP_IDS:
                errors.append(f"{prefix}.props[{j}]: ID inconnu '{pid}'")
        
        env = scene.get("environment", {})
        eid = env.get("environment_id", "")
        if eid and eid not in ENVIRONMENT_IDS:
            errors.append(f"{prefix}.environment: ID inconnu '{eid}'")
        
        cam = scene.get("camera", {})
        csid = cam.get("style_id", "")
        if csid and csid not in CAMERA_IDS:
            errors.append(f"{prefix}.camera: ID inconnu '{csid}'")
        
        lit = scene.get("lighting", {})
        lid = lit.get("preset_id", "")
        if lid and lid not in LIGHTING_IDS:
            errors.append(f"{prefix}.lighting: ID inconnu '{lid}'")
        
        aud = scene.get("audio", {})
        for aid_field in ["music_id", "ambient_id"]:
            aid = aud.get(aid_field, "")
            if aid and aid not in AUDIO_IDS:
                errors.append(f"{prefix}.audio.{aid_field}: ID inconnu '{aid}'")
        for sfx in aud.get("sfx", []):
            if sfx and sfx not in AUDIO_IDS:
                errors.append(f"{prefix}.audio.sfx: ID inconnu '{sfx}'")
    
    fa = master_json.get("facial_animation")
    if not fa:
        errors.append("facial_animation manquant")
    else:
        segs = fa.get("segments", [])
        if not segs:
            errors.append("facial_animation.segments vide")
        for k, seg in enumerate(segs):
            prefix = f"facial_segment[{k}]"
            for field in ["time_start", "time_end", "expression", "intensity"]:
                if field not in seg:
                    errors.append(f"{prefix}: champ '{field}' manquant")
            intensity = seg.get("intensity", 0)
            if not (0.0 <= intensity <= 1.0):
                errors.append(f"{prefix}: intensity {intensity} hors [0.0, 1.0]")
    
    ms = master_json.get("motion_synthesis")
    if not ms:
        errors.append("motion_synthesis manquant")
    elif not ms.get("prompt"):
        errors.append("motion_synthesis.prompt vide")
    
    is_valid = len(errors) == 0
    if errors:
        logger.warn(f"Validation structure: {len(errors)} erreur(s)")
        for e in errors[:10]:
            logger.debug(f"  • {e}")
    else:
        logger.info("Validation structure: OK")
    
    return (is_valid, errors)


# ============================================================================
# VALIDATION — COMPLÉTUDE (Niveau 3)
# ============================================================================

def validate_completeness(master_json: dict, logger: CortexLogger) -> list:
    """Niveau 3 — Cohérence croisée entre les blocs.
    Retourne list[str] de warnings."""
    
    warnings = []
    
    pp = master_json.get("production_plan", {})
    fa = master_json.get("facial_animation", {})
    ms = master_json.get("motion_synthesis", {})
    scenes = pp.get("scenes", [])
    segments = fa.get("segments", [])
    
    if scenes:
        total_start = scenes[0].get("timecode_start", 0)
        total_end = scenes[-1].get("timecode_end", 0)
        total_duration = total_end - total_start
        
        if total_duration > 0 and segments:
            facial_coverage = sum(
                s.get("time_end", 0) - s.get("time_start", 0)
                for s in segments
            )
            coverage_pct = (facial_coverage / total_duration) * 100
            if coverage_pct < 50:
                warnings.append(
                    f"Couverture faciale faible: {coverage_pct:.1f}% "
                    f"({facial_coverage:.1f}s / {total_duration:.1f}s)"
                )
        
        ms_dur = ms.get("duration_seconds", 0)
        if total_duration > 0 and abs(ms_dur - total_duration) > 1.0:
            warnings.append(
                f"motion_synthesis.duration_seconds ({ms_dur}) != "
                f"durée totale vidéo ({total_duration})"
            )
        
        has_props = any(
            prop.get("prop_id", "none") != "none"
            for scene in scenes
            for prop in scene.get("props", [])
        )
        requires_u02 = pp.get("production_notes", {}).get("requires_u02", False)
        
        if requires_u02 and not has_props:
            warnings.append("requires_u02=true mais aucun prop détecté dans les scènes")
        if not requires_u02 and has_props:
            warnings.append("requires_u02=false mais des props sont présents dans les scènes")
    
    return warnings


# ============================================================================
# DISPATCHER — DÉCOUPE DU MASTER JSON
# ============================================================================

def dispatch_master_json(master_json: dict, output_dir: Path,
                         motor_status: MotorStatus,
                         logger: CortexLogger) -> dict:
    """Découpe le Master JSON en 3 fichiers séparés + ajoute les flags."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    
    # --- 1. PRODUCTION_PLAN.JSON ---
    pp = master_json.get("production_plan", {})
    pp["schema_version"] = "2.0"
    pp["generated_at"] = datetime.now(timezone.utc).isoformat()
    pp["flags"] = motor_status.get_flags()
    
    pp_path = output_dir / "PRODUCTION_PLAN.JSON"
    with open(pp_path, 'w', encoding='utf-8') as f:
        json.dump(pp, f, indent=2, ensure_ascii=False)
    logger.info(f"Écrit: {pp_path} ({pp_path.stat().st_size} bytes)")
    written["production_plan"] = str(pp_path)
    
    # --- 2. facial_animation.json ---
    fa = master_json.get("facial_animation", {})
    fa_path = output_dir / "facial_animation.json"
    with open(fa_path, 'w', encoding='utf-8') as f:
        json.dump(fa, f, indent=2, ensure_ascii=False)
    logger.info(f"Écrit: {fa_path} ({fa_path.stat().st_size} bytes)")
    written["facial_animation"] = str(fa_path)
    
    # --- 3. motion_synthesis_prompt.txt ---
    ms = master_json.get("motion_synthesis", {})
    ms_path = output_dir / "motion_synthesis_prompt.txt"
    ms_text = ms.get("prompt", "")
    ms_text += f"\nDuration: {ms.get('duration_seconds', 0)} seconds."
    ms_text += f" Style: {ms.get('style', 'casual')}."
    ms_text += f" Ratio: {ms.get('ratio', '16:9')}."
    with open(ms_path, 'w', encoding='utf-8') as f:
        f.write(ms_text)
    logger.info(f"Écrit: {ms_path} ({ms_path.stat().st_size} bytes)")
    written["motion_synthesis"] = str(ms_path)
    
    return written


# ============================================================================
# UPDATE FLAGS — POST-PIPELINE
# ============================================================================

def update_flags(pp_path: Path, motor_status: MotorStatus,
                 logger: CortexLogger):
    """Met à jour le bloc flags dans PRODUCTION_PLAN.JSON après toutes les phases."""
    
    if not pp_path.exists():
        logger.warn(f"PRODUCTION_PLAN.JSON introuvable pour mise à jour flags: {pp_path}")
        return
    
    try:
        with open(pp_path, 'r', encoding='utf-8') as f:
            pp = json.load(f)
        
        pp["flags"] = motor_status.get_flags()
        
        with open(pp_path, 'w', encoding='utf-8') as f:
            json.dump(pp, f, indent=2, ensure_ascii=False)
        
        logger.info("Flags mis à jour dans PRODUCTION_PLAN.JSON")
    except Exception as e:
        logger.error(f"Erreur mise à jour flags: {e}")


# ============================================================================
# DRY-RUN — MOCK MASTER JSON V2
# ============================================================================

def generate_mock_master_json(metadata: dict) -> dict:
    """Génère un Master JSON V2 de test pour le mode dry-run."""
    
    duration = metadata.get("duration_seconds", 10)
    mid = round(duration / 2, 3)
    video_stem = Path(metadata.get("source_video", "test")).stem
    
    return {
        "production_plan": {
            "metadata": metadata,
            "scenes": [
                {
                    "scene_id": 1,
                    "timecode_start": 0.0,
                    "timecode_end": mid,
                    "description": "[DRY-RUN] Scène d'ouverture",
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
                        "music_id": "none",
                        "sfx": ["oof"],
                        "ambient_id": "none"
                    }
                },
                {
                    "scene_id": 2,
                    "timecode_start": mid,
                    "timecode_end": round(duration, 3),
                    "description": "[DRY-RUN] Scène d'action",
                    "characters": [
                        {
                            "character_id": "bacon_hair",
                            "role": "protagonist",
                            "actions": ["run", "sword_slash"]
                        },
                        {
                            "character_id": "noob",
                            "role": "antagonist",
                            "actions": ["idle", "death"]
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
                        "environment_id": "grass_terrain",
                        "modifications": []
                    },
                    "camera": {
                        "style_id": "follow",
                        "movements": ["tracking du protagoniste"]
                    },
                    "lighting": {
                        "preset_id": "dramatic",
                        "adjustments": []
                    },
                    "audio": {
                        "music_id": "action_electronic",
                        "sfx": ["sword_hit", "oof"],
                        "ambient_id": "none"
                    }
                }
            ],
            "production_notes": {
                "complexity_score": 5,
                "estimated_render_hours": 2,
                "special_requirements": ["[DRY-RUN] Aucune analyse réelle effectuée"],
                "warnings": ["Mode test uniquement"],
                "requires_u02": True
            }
        },
        "facial_animation": {
            "sequence_id": video_stem,
            "segments": [
                {
                    "time_start": 0.0,
                    "time_end": mid,
                    "character_id": "bacon_hair",
                    "expression": "neutral",
                    "intensity": 0.3,
                    "eyes": "focused_forward",
                    "mouth": "closed_tight",
                    "apex_time": round(mid / 2, 3),
                    "low_visibility": False
                },
                {
                    "time_start": mid,
                    "time_end": round(duration, 3),
                    "character_id": "bacon_hair",
                    "expression": "determined",
                    "intensity": 0.8,
                    "eyes": "narrowed",
                    "mouth": "closed_tight",
                    "apex_time": round(mid + (duration - mid) * 0.7, 3),
                    "low_visibility": False
                }
            ]
        },
        "motion_synthesis": {
            "prompt": "Un personnage marche puis court vers un adversaire et effectue une attaque à l'épée.",
            "duration_seconds": round(duration, 3),
            "style": "dramatic",
            "ratio": "16:9"
        }
    }


# ============================================================================
# ORCHESTRATEUR — PIPELINE PRINCIPAL
# ============================================================================

def run_pipeline(args, logger: CortexLogger):
    """Orchestrateur principal — exécute les 4 phases séquentiellement."""
    
    drive_root = Path(args.drive_root).resolve()
    cortex_dir = drive_root / "00_CORTEX_HQ"
    input_dir = cortex_dir / "IN_VIDEO_SOURCE"
    output_dir = cortex_dir / "OUT_PRODUCTION_PLAN"
    
    video_path = input_dir / args.input_video
    
    if not drive_root.exists():
        logger.error(f"Drive root non trouvé: {drive_root}")
        sys.exit(1)
    
    if not video_path.exists():
        video_path = Path(args.input_video).resolve()
        if not video_path.exists():
            logger.error(f"Vidéo non trouvée: {args.input_video}")
            logger.info(f"Chemins vérifiés:")
            logger.info(f"  - {input_dir / args.input_video}")
            logger.info(f"  - {video_path}")
            sys.exit(1)
    
    logger.info(f"Vidéo source: {video_path}")
    logger.info(f"Output dir: {output_dir}")
    
    metadata = get_video_metadata(video_path, logger)
    motor_status = MotorStatus()
    
    # =================================================================
    # MODE DRY-RUN
    # =================================================================
    if args.dry_run:
        logger.info("=== MODE DRY-RUN ===")
        
        master_json = generate_mock_master_json(metadata)
        master_json = normalize_timecodes(master_json, logger)
        
        is_valid, errors = validate_structure(master_json, logger)
        if not is_valid:
            logger.warn(f"Mock validation: {errors}")
        
        warnings = validate_completeness(master_json, logger)
        for w in warnings:
            logger.warn(f"Cohérence: {w}")
        
        motor_status.mark_success("gemini_semantic")
        motor_status.mark_success("audio_extraction")
        motor_status.mark_success("fov_extraction")
        motor_status.mark_failed("depth_anything", "Stub not implemented")
        motor_status.mark_failed("sam_segmentation", "Stub not implemented")
        
        dispatch_master_json(master_json, output_dir, motor_status, logger)
        update_flags(output_dir / "PRODUCTION_PLAN.JSON", motor_status, logger)
        
        logger.info("=== DRY-RUN TERMINÉ ===")
        
        flags = motor_status.get_flags()
        logger.info("═══ RAPPORT FINAL ═══")
        for m, r in motor_status.results.items():
            icon = ("✅" if r["status"] == "success"
                    else "🟡" if r["status"] == "partial"
                    else "❌" if r["status"] == "failed"
                    else "⏳")
            logger.info(f"  {icon} {m}: {r['status']}")
        
        logger.info("MISSION ACCOMPLIE — CORTEX DRY-RUN TERMINÉ")
        sys.exit(0)
    
    # =================================================================
    # PHASE 1 — CPU (VRAM = 0)
    # =================================================================
    logger.info("═══ PHASE 1 — CPU ═══")
    
    # M2: Audio
    if not args.rerun or args.rerun == "audio_extraction":
        audio_out = output_dir / "audio_source.wav"
        audio_ok = run_audio_extraction(video_path, audio_out, logger)
        if audio_ok:
            motor_status.mark_success("audio_extraction", audio_out)
        else:
            motor_status.mark_failed("audio_extraction", "FFmpeg failed")
    else:
        logger.info("M2 Audio: skip (--rerun != audio_extraction)")
    
    # M3: FOV
    if not args.rerun or args.rerun == "fov_extraction":
        fov_out = output_dir / "camera_fov_ratio.json"
        fov_ok = run_fov_extraction(video_path, fov_out, logger)
        if fov_ok:
            motor_status.mark_success("fov_extraction", fov_out)
        else:
            motor_status.mark_failed("fov_extraction", "OpenCV failed")
    else:
        logger.info("M3 FOV: skip (--rerun != fov_extraction)")
    
    # =================================================================
    # PHASE 2 — API (VRAM = 0)
    # =================================================================
    logger.info("═══ PHASE 2 — API ═══")
    
    if not args.rerun or args.rerun == "gemini_semantic":
        master_json = call_gemini_v2(
            video_path, metadata, logger, model_name=args.model
        )
        
        if master_json is None:
            logger.error("FATAL: Gemini a échoué. Pipeline arrêté.")
            motor_status.mark_failed("gemini_semantic", "Gemini returned None after retries")
            update_flags(output_dir / "PRODUCTION_PLAN.JSON", motor_status, logger)
            sys.exit(1)
        
        motor_status.mark_success("gemini_semantic")
        
        master_json = normalize_timecodes(master_json, logger)
        
        is_valid, errors = validate_structure(master_json, logger)
        if not is_valid:
            logger.error(f"Validation FATALE: {len(errors)} erreur(s)")
            for e in errors[:10]:
                logger.error(f"  • {e}")
        
        warnings = validate_completeness(master_json, logger)
        for w in warnings:
            logger.warn(f"Cohérence: {w}")
        
        dispatch_master_json(master_json, output_dir, motor_status, logger)
    else:
        logger.info("M1 Gemini: skip (--rerun != gemini_semantic)")
    
    # =================================================================
    # PHASE 3 — GPU-A (DepthAnything)
    # =================================================================
    logger.info("═══ PHASE 3 — GPU-A (DepthAnything) ═══")
    
    if not args.rerun or args.rerun == "depth_anything":
        depth_dir = output_dir / "DEPTH_MAP"
        depth_dir.mkdir(parents=True, exist_ok=True)
        depth_ok = run_depth_anything(video_path, depth_dir, logger)
        if depth_ok:
            motor_status.mark_success("depth_anything", depth_dir)
        else:
            motor_status.mark_failed("depth_anything", "Stub not implemented")
    else:
        logger.info("M6 DepthAnything: skip (--rerun != depth_anything)")
    
    # =================================================================
    # PHASE 4 — GPU-B (SAM)
    # =================================================================
    logger.info("═══ PHASE 4 — GPU-B (SAM) ═══")
    
    if not args.rerun or args.rerun == "sam_segmentation":
        sam_out = output_dir / "semantic_masks.json"
        sam_ok = run_sam_segmentation(video_path, sam_out, logger)
        if sam_ok:
            motor_status.mark_success("sam_segmentation", sam_out)
        else:
            motor_status.mark_failed("sam_segmentation", "Stub not implemented")
    else:
        logger.info("M7 SAM: skip (--rerun != sam_segmentation)")
    
    # =================================================================
    # FINALISATION
    # =================================================================
    update_flags(output_dir / "PRODUCTION_PLAN.JSON", motor_status, logger)
    
    flags = motor_status.get_flags()
    logger.info("═══ RAPPORT FINAL ═══")
    for m, r in motor_status.results.items():
        icon = ("✅" if r["status"] == "success"
                else "🟡" if r["status"] == "partial"
                else "❌" if r["status"] == "failed"
                else "⏳")
        logger.info(f"  {icon} {m}: {r['status']}")
    
    if flags["all_motors_ok"]:
        logger.info("TOUS LES MOTEURS OK")
    else:
        failed_count = len(flags["partial_failure"])
        logger.warn(f"{failed_count} moteur(s) en échec — revue manuelle recommandée")
    
    logger.info("═══ MISSION ACCOMPLIE — CORTEX TERMINÉ ═══")


# ============================================================================
# CLI — MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EXODUS V2 — CORTEX: Orchestrateur 6-moteurs → Master JSON V2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s --drive-root /content/drive/MyDrive/EXODUS --input-video video.mp4
  %(prog)s --drive-root ./EXODUS --input-video test.mp4 --dry-run
  %(prog)s --drive-root /data/EXODUS --input-video source.mp4 --model gemini-2.0-flash
  %(prog)s --drive-root ./EXODUS --input-video video.mp4 --rerun audio_extraction
        """
    )
    
    parser.add_argument(
        "--drive-root", type=str, required=True,
        help="Chemin racine EXODUS (contient 00_CORTEX_HQ/)"
    )
    parser.add_argument(
        "--input-video", type=str, required=True,
        help="Nom du fichier vidéo (cherché dans IN_VIDEO_SOURCE/)"
    )
    parser.add_argument(
        "--output-name", type=str, default=None,
        help="Nom du fichier JSON de sortie (défaut: PRODUCTION_PLAN.JSON)"
    )
    parser.add_argument(
        "--model", type=str, default="gemini-2.0-flash",
        help="Modèle Gemini à utiliser (défaut: gemini-2.0-flash)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Exécute sans appeler Gemini (test local)"
    )
    parser.add_argument(
        "--rerun", type=str, default=None,
        choices=["gemini_semantic", "audio_extraction", "fov_extraction",
                 "depth_anything", "sam_segmentation"],
        help="Relance un seul moteur sans retoucher les autres outputs"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Active les logs DEBUG"
    )
    
    args = parser.parse_args()
    
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = CortexLogger(level=log_level)
    
    logger.info("=" * 60)
    logger.info("EXODUS V2 — FRÉGATE 00: CORTEX HQ — ORCHESTRATEUR V2")
    logger.info("=" * 60)
    
    run_pipeline(args, logger)


if __name__ == "__main__":
    main()
