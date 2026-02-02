"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SYNC ENGINE — Body/Face Synchronization                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de synchronisation body/face pour TRANSMUTATION.                      ║
║  Supporte: manuel, marqueurs visuels, corrélation audio.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict
import json


class SyncEngine:
    """Moteur de synchronisation body/face."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def log(self, msg: str):
        if self.verbose:
            print(f"[SYNC] {msg}")
    
    def calculate_offset(
        self,
        method: str = "manual",
        manual_offset: int = 0,
        marker_video: int = None,
        marker_fbx: int = None,
        video_path: str = None,
        audio_path: str = None
    ) -> int:
        """
        Calcule l'offset de synchronisation.
        
        Methods:
            - "manual": Utilise manual_offset directement
            - "marker": Calcule depuis les frames de référence
            - "audio": Corrélation audio (nécessite scipy)
        
        Returns:
            Offset en frames (positif = vidéo en avance sur FBX)
        """
        if method == "manual":
            self.log(f"Mode manuel: offset = {manual_offset}")
            return manual_offset
        
        elif method == "marker":
            if marker_video is None or marker_fbx is None:
                raise ValueError("marker_video et marker_fbx requis pour méthode 'marker'")
            offset = marker_video - marker_fbx
            self.log(f"Mode marqueur: video_frame={marker_video}, fbx_frame={marker_fbx}, offset={offset}")
            return offset
        
        elif method == "audio":
            if not video_path or not audio_path:
                raise ValueError("video_path et audio_path requis pour méthode 'audio'")
            return self._audio_correlation_sync(video_path, audio_path)
        
        return 0
    
    def _audio_correlation_sync(self, video_path: str, audio_path: str) -> int:
        """
        Synchronisation par corrélation croisée audio.
        Extrait l'audio de la vidéo et calcule le décalage optimal.
        """
        self.log("Synchronisation audio en cours...")
        
        try:
            from scipy.signal import correlate
            from scipy.io import wavfile
            import subprocess
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_audio = Path(tmpdir) / "video_audio.wav"
                
                cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-vn", "-acodec", "pcm_s16le",
                    "-ar", "16000", "-ac", "1",
                    str(video_audio)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"FFmpeg erreur: {result.stderr}")
                    return 0
                
                sr1, audio1 = wavfile.read(str(video_audio))
                sr2, audio2 = wavfile.read(audio_path)
                
                if sr1 != sr2:
                    self.log(f"Sample rates différents: {sr1} vs {sr2}")
                    return 0
                
                audio1 = audio1.astype(np.float32) / 32768.0
                audio2 = audio2.astype(np.float32) / 32768.0
                
                max_len = min(len(audio1), len(audio2), sr1 * 60)
                audio1 = audio1[:max_len]
                audio2 = audio2[:max_len]
                
                correlation = correlate(audio1, audio2, mode='full')
                lag = np.argmax(correlation) - len(audio2) + 1
                
                offset_seconds = lag / sr1
                offset_frames = int(offset_seconds * 30)
                
                self.log(f"Corrélation audio: lag={lag} samples, offset={offset_frames} frames")
                return offset_frames
            
        except ImportError as e:
            self.log(f"Dépendances manquantes pour sync audio: {e}")
            return 0
        except Exception as e:
            self.log(f"Erreur sync audio: {e}")
            return 0
    
    def validate_sync(
        self, 
        body_length: int, 
        face_length: int, 
        offset: int
    ) -> Tuple[bool, str]:
        """
        Valide que la synchronisation est cohérente.
        
        Args:
            body_length: Nombre de frames body
            face_length: Nombre de frames faciales
            offset: Offset calculé
        
        Returns:
            (is_valid, message)
        """
        effective_start = max(0, offset)
        effective_end = min(body_length, face_length + offset)
        overlap = effective_end - effective_start
        
        if overlap < 30:
            return False, f"Chevauchement insuffisant ({overlap} frames < 30 minimum)"
        
        if offset > face_length:
            return False, "Offset trop grand - aucune frame faciale utilisable"
        
        if -offset > body_length:
            return False, "Offset négatif trop grand - aucune frame body utilisable"
        
        coverage = overlap / max(body_length, face_length) * 100
        
        return True, f"Sync OK: {overlap} frames de chevauchement ({coverage:.1f}% couverture)"
    
    def get_frame_range(
        self,
        body_length: int,
        face_length: int,
        offset: int
    ) -> Tuple[int, int]:
        """
        Calcule la plage de frames effective après synchronisation.
        
        Returns:
            (start_frame, end_frame)
        """
        start = max(0, offset)
        end = min(body_length, face_length + offset)
        return start, end
    
    def create_sync_report(
        self,
        body_path: str,
        video_path: str,
        offset: int,
        body_length: int,
        face_length: int
    ) -> Dict:
        """
        Génère un rapport de synchronisation.
        """
        is_valid, message = self.validate_sync(body_length, face_length, offset)
        start, end = self.get_frame_range(body_length, face_length, offset)
        
        return {
            "inputs": {
                "body_fbx": body_path,
                "video": video_path
            },
            "sync": {
                "offset_frames": offset,
                "body_length": body_length,
                "face_length": face_length,
                "effective_start": start,
                "effective_end": end,
                "overlap_frames": end - start
            },
            "validation": {
                "is_valid": is_valid,
                "message": message
            }
        }


def calculate_sync_offset(
    method: str = "manual",
    manual_offset: int = 0,
    marker_video: int = None,
    marker_fbx: int = None,
    video_path: str = None,
    fbx_audio_path: str = None
) -> int:
    """
    Fonction utilitaire pour calculer l'offset.
    Wrapper autour de SyncEngine pour compatibilité.
    """
    engine = SyncEngine(verbose=True)
    return engine.calculate_offset(
        method=method,
        manual_offset=manual_offset,
        marker_video=marker_video,
        marker_fbx=marker_fbx,
        video_path=video_path,
        audio_path=fbx_audio_path
    )


def validate_sync(body_length: int, face_length: int, offset: int) -> Tuple[bool, str]:
    """Fonction utilitaire de validation."""
    engine = SyncEngine()
    return engine.validate_sync(body_length, face_length, offset)


if __name__ == "__main__":
    engine = SyncEngine(verbose=True)
    
    print("\n=== Test Sync Engine ===")
    
    offset = engine.calculate_offset(method="marker", marker_video=150, marker_fbx=100)
    print(f"Offset calculé: {offset}")
    
    is_valid, msg = engine.validate_sync(body_length=1000, face_length=900, offset=offset)
    print(f"Validation: {msg}")
    
    start, end = engine.get_frame_range(body_length=1000, face_length=900, offset=offset)
    print(f"Frame range: {start} - {end}")
    
    report = engine.create_sync_report(
        body_path="test.fbx",
        video_path="test.mp4",
        offset=offset,
        body_length=1000,
        face_length=900
    )
    print(f"\nRapport: {json.dumps(report, indent=2)}")
