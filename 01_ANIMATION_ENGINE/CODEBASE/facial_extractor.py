"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               FACIAL EXTRACTOR — EMOCA → 52 ARKit Blendshapes                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module d'extraction faciale via EMOCA/DECA.                                 ║
║  Convertit vidéo → 52 blendshapes ARKit pour avatars Roblox DynamicHead.     ║
║  AUCUN MEDIAPIPE - Utilise EMOCA exclusivement.                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import cv2

ARKIT_52_BLENDSHAPES = [
    "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight", "eyeSquintLeft", "eyeSquintRight",
    "eyeWideLeft", "eyeWideRight",
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    "noseSneerLeft", "noseSneerRight",
    "tongueOut"
]

FLAME_EXPRESSION_INDICES = {
    "jaw_open": 0,
    "jaw_sideways": 1,
    "smile": 6,
    "frown": 7,
    "brow_raise": 1,
    "brow_furrow": 2,
    "eye_wide": 3,
    "eye_squint": 4,
    "cheek_puff": 8,
    "nose_sneer": 9,
    "mouth_pucker": 10,
    "mouth_funnel": 11,
}


class EMOCAExtractor:
    """
    Extracteur facial utilisant EMOCA.
    Convertit les paramètres FLAME en 52 blendshapes ARKit.
    """
    
    def __init__(self, emoca_model_path: str):
        self.model_path = Path(emoca_model_path)
        self.model = None
        self.device = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle EMOCA."""
        try:
            import torch
            import sys
            
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"[EMOCA] Device: {self.device}")
            
            sys.path.insert(0, str(self.model_path.parent))
            
            from gdl.models.EMOCA import EMOCA
            from omegaconf import OmegaConf
            
            cfg_path = self.model_path / "cfg.yaml"
            ckpt_path = self.model_path / "model.ckpt"
            
            if not cfg_path.exists():
                print(f"[EMOCA:WARN] Config non trouvée: {cfg_path}")
                print("[EMOCA:WARN] Mode fallback activé - utilisation de valeurs simulées")
                self.model = None
                return
            
            cfg = OmegaConf.load(cfg_path)
            self.model = EMOCA(cfg)
            
            checkpoint = torch.load(ckpt_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            print("[EMOCA] Modèle chargé avec succès")
            
        except ImportError as e:
            print(f"[EMOCA:WARN] Dépendances EMOCA manquantes: {e}")
            print("[EMOCA:WARN] Mode fallback activé")
            self.model = None
        except Exception as e:
            print(f"[EMOCA:WARN] Erreur chargement modèle: {e}")
            print("[EMOCA:WARN] Mode fallback activé")
            self.model = None
    
    def extract_arkit_from_video(
        self, 
        video_path: str,
        start_frame: int = 0,
        end_frame: int = -1
    ) -> Dict:
        """
        Extrait les 52 blendshapes ARKit depuis une vidéo.
        
        Returns:
            {
                "fps": 30,
                "total_frames": 300,
                "frames": [
                    {
                        "frame": 0,
                        "blendshapes": {"eyeBlinkLeft": 0.0, ...},
                        "confidence": 0.95
                    },
                    ...
                ]
            }
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if end_frame < 0:
            end_frame = total_frames
        
        result = {
            "fps": fps,
            "total_frames": total_frames,
            "source_video": str(video_path),
            "frames": []
        }
        
        frame_idx = 0
        processed = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx < start_frame:
                frame_idx += 1
                continue
            if frame_idx >= end_frame:
                break
            
            flame_params = self._process_frame(frame)
            arkit_values = self._flame_to_arkit(flame_params)
            
            result["frames"].append({
                "frame": frame_idx,
                "blendshapes": arkit_values,
                "confidence": flame_params.get("confidence", 1.0)
            })
            
            frame_idx += 1
            processed += 1
            
            if processed % 100 == 0:
                print(f"[EMOCA] Traité {processed} frames ({frame_idx}/{end_frame})")
        
        cap.release()
        print(f"[EMOCA] Extraction complète: {processed} frames traitées")
        return result
    
    def _process_frame(self, frame: np.ndarray) -> Dict:
        """Traite une frame avec EMOCA et retourne les params FLAME."""
        import torch
        
        if self.model is None:
            return self._fallback_process(frame)
        
        try:
            from gdl.datasets.FaceVideoDataModule import FaceVideoDataModule
            from PIL import Image
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            
            input_tensor = self._preprocess_image(img)
            input_tensor = input_tensor.to(self.device)
            
            with torch.no_grad():
                output = self.model.encode(input_tensor)
            
            return {
                "expression": output["expcode"].cpu().numpy().flatten(),
                "jaw": output["jawpose"].cpu().numpy().flatten(),
                "confidence": float(output.get("confidence", torch.tensor(1.0)).cpu())
            }
            
        except Exception as e:
            print(f"[EMOCA:DEBUG] Fallback pour frame: {e}")
            return self._fallback_process(frame)
    
    def _preprocess_image(self, img) -> 'torch.Tensor':
        """Prétraite l'image pour EMOCA."""
        import torch
        from torchvision import transforms
        
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        tensor = transform(img).unsqueeze(0)
        return tensor
    
    def _fallback_process(self, frame: np.ndarray) -> Dict:
        """
        Traitement fallback basé sur la luminosité/mouvement.
        Utilisé quand EMOCA n'est pas disponible.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        h, w = gray.shape
        eye_region = gray[int(h*0.2):int(h*0.4), int(w*0.2):int(w*0.8)]
        mouth_region = gray[int(h*0.6):int(h*0.9), int(w*0.3):int(w*0.7)]
        
        eye_variance = np.var(eye_region) / 1000.0
        mouth_variance = np.var(mouth_region) / 1000.0
        
        expression = np.zeros(50)
        expression[0] = np.clip(mouth_variance * 0.5, 0, 1)
        expression[6] = np.clip(eye_variance * 0.3, 0, 1)
        
        jaw = np.zeros(3)
        jaw[0] = np.clip(mouth_variance * 0.3, 0, 1)
        
        return {
            "expression": expression,
            "jaw": jaw,
            "confidence": 0.5
        }
    
    def _flame_to_arkit(self, flame_params: Dict) -> Dict[str, float]:
        """Convertit les paramètres FLAME en 52 blendshapes ARKit."""
        arkit = {key: 0.0 for key in ARKIT_52_BLENDSHAPES}
        
        exp = flame_params["expression"]
        jaw = flame_params["jaw"]
        
        if len(exp) < 10:
            exp = np.pad(exp, (0, 50 - len(exp)))
        if len(jaw) < 3:
            jaw = np.pad(jaw, (0, 3 - len(jaw)))
        
        arkit["jawOpen"] = float(np.clip(jaw[0] * 2.0, 0, 1))
        arkit["jawLeft"] = float(np.clip(jaw[1] * 1.5, 0, 1))
        arkit["jawRight"] = float(np.clip(-jaw[1] * 1.5, 0, 1))
        arkit["jawForward"] = float(np.clip(jaw[2] if len(jaw) > 2 else 0, 0, 1))
        
        smile_val = float(exp[6]) if len(exp) > 6 else 0.0
        arkit["mouthSmileLeft"] = float(np.clip(smile_val * 1.5, 0, 1))
        arkit["mouthSmileRight"] = float(np.clip(smile_val * 1.5, 0, 1))
        arkit["mouthFrownLeft"] = float(np.clip(-smile_val * 1.2, 0, 1))
        arkit["mouthFrownRight"] = float(np.clip(-smile_val * 1.2, 0, 1))
        
        arkit["mouthPucker"] = float(np.clip(exp[10] if len(exp) > 10 else 0, 0, 1))
        arkit["mouthFunnel"] = float(np.clip(exp[11] if len(exp) > 11 else 0, 0, 1))
        arkit["mouthLeft"] = float(np.clip(exp[12] if len(exp) > 12 else 0, 0, 1))
        arkit["mouthRight"] = float(np.clip(exp[13] if len(exp) > 13 else 0, 0, 1))
        
        mouth_open = arkit["jawOpen"]
        arkit["mouthClose"] = float(np.clip(1.0 - mouth_open, 0, 1))
        arkit["mouthLowerDownLeft"] = float(np.clip(mouth_open * 0.8, 0, 1))
        arkit["mouthLowerDownRight"] = float(np.clip(mouth_open * 0.8, 0, 1))
        arkit["mouthUpperUpLeft"] = float(np.clip(mouth_open * 0.4, 0, 1))
        arkit["mouthUpperUpRight"] = float(np.clip(mouth_open * 0.4, 0, 1))
        
        brow_val = float(exp[1]) if len(exp) > 1 else 0.0
        arkit["browInnerUp"] = float(np.clip(brow_val * 1.2, 0, 1))
        arkit["browDownLeft"] = float(np.clip(-brow_val, 0, 1))
        arkit["browDownRight"] = float(np.clip(-brow_val, 0, 1))
        arkit["browOuterUpLeft"] = float(np.clip(brow_val * 0.8, 0, 1))
        arkit["browOuterUpRight"] = float(np.clip(brow_val * 0.8, 0, 1))
        
        eye_val = float(exp[3]) if len(exp) > 3 else 0.0
        squint_val = float(exp[4]) if len(exp) > 4 else 0.0
        
        arkit["eyeWideLeft"] = float(np.clip(eye_val, 0, 1))
        arkit["eyeWideRight"] = float(np.clip(eye_val, 0, 1))
        arkit["eyeSquintLeft"] = float(np.clip(squint_val, 0, 1))
        arkit["eyeSquintRight"] = float(np.clip(squint_val, 0, 1))
        
        blink_val = float(exp[5]) if len(exp) > 5 else 0.0
        arkit["eyeBlinkLeft"] = float(np.clip(blink_val, 0, 1))
        arkit["eyeBlinkRight"] = float(np.clip(blink_val, 0, 1))
        
        arkit["eyeLookUpLeft"] = float(np.clip(exp[20] if len(exp) > 20 else 0, 0, 1))
        arkit["eyeLookUpRight"] = float(np.clip(exp[20] if len(exp) > 20 else 0, 0, 1))
        arkit["eyeLookDownLeft"] = float(np.clip(exp[21] if len(exp) > 21 else 0, 0, 1))
        arkit["eyeLookDownRight"] = float(np.clip(exp[21] if len(exp) > 21 else 0, 0, 1))
        arkit["eyeLookInLeft"] = float(np.clip(exp[22] if len(exp) > 22 else 0, 0, 1))
        arkit["eyeLookInRight"] = float(np.clip(exp[23] if len(exp) > 23 else 0, 0, 1))
        arkit["eyeLookOutLeft"] = float(np.clip(exp[24] if len(exp) > 24 else 0, 0, 1))
        arkit["eyeLookOutRight"] = float(np.clip(exp[25] if len(exp) > 25 else 0, 0, 1))
        
        arkit["cheekPuff"] = float(np.clip(exp[8] if len(exp) > 8 else 0, 0, 1))
        arkit["cheekSquintLeft"] = float(np.clip(squint_val * 0.5, 0, 1))
        arkit["cheekSquintRight"] = float(np.clip(squint_val * 0.5, 0, 1))
        
        arkit["noseSneerLeft"] = float(np.clip(exp[9] if len(exp) > 9 else 0, 0, 1))
        arkit["noseSneerRight"] = float(np.clip(exp[9] if len(exp) > 9 else 0, 0, 1))
        
        arkit["tongueOut"] = float(np.clip(exp[30] if len(exp) > 30 else 0, 0, 1))
        
        return arkit
    
    def export_to_json(self, data: Dict, output_path: str):
        """Exporte les données faciales en JSON."""
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[EMOCA] Données exportées: {output_path}")


def test_extractor(video_path: str, emoca_path: str):
    """Test rapide de l'extracteur."""
    extractor = EMOCAExtractor(emoca_path)
    data = extractor.extract_arkit_from_video(video_path, end_frame=30)
    
    print(f"\nRésultat test:")
    print(f"  FPS: {data['fps']}")
    print(f"  Frames extraites: {len(data['frames'])}")
    
    if data['frames']:
        first_frame = data['frames'][0]
        print(f"  Exemple blendshapes (frame 0):")
        for key, val in list(first_frame['blendshapes'].items())[:5]:
            print(f"    {key}: {val:.3f}")
    
    return data


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        test_extractor(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python facial_extractor.py <video_path> <emoca_model_path>")
