#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      AUDIO SYNC — EXODUS CARRIER                             ║
║                 Mix & Normalisation Multi-Pistes Audio                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Mix de pistes audio (music, sfx, voice) avec normalisation LUFS            ║
║  Synchronisation avec timeline vidéo                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class AudioTrack:
    """Représentation d'une piste audio."""
    path: Path
    track_type: str
    volume: float
    offset_ms: int
    duration: float


class AudioSync:
    """Gestionnaire de synchronisation et mix audio."""
    
    DEFAULT_VOLUMES = {
        "music": -6.0,
        "sfx": -3.0,
        "voice": 0.0,
        "default": -3.0
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[AUDIO_SYNC] {msg}")
    
    def get_audio_info(self, audio_path: Path) -> Optional[dict]:
        """Récupère les informations d'un fichier audio."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels,duration,codec_name",
            "-of", "json",
            str(audio_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data.get("streams", [{}])[0]
                return {
                    "sample_rate": int(stream.get("sample_rate", 48000)),
                    "channels": int(stream.get("channels", 2)),
                    "duration": float(stream.get("duration", 0)),
                    "codec": stream.get("codec_name", "unknown")
                }
        except Exception as e:
            self._log(f"Erreur FFprobe: {e}")
        
        return None
    
    def detect_track_type(self, audio_path: Path) -> str:
        """Détecte le type de piste depuis le nom du fichier."""
        name = audio_path.stem.lower()
        
        if any(kw in name for kw in ["music", "bgm", "ost", "soundtrack"]):
            return "music"
        elif any(kw in name for kw in ["sfx", "sound", "effect", "fx"]):
            return "sfx"
        elif any(kw in name for kw in ["voice", "vocal", "dialogue", "vo"]):
            return "voice"
        
        return "default"
    
    def measure_loudness(self, audio_path: Path) -> Optional[float]:
        """Mesure la loudness LUFS d'un fichier audio."""
        cmd = [
            "ffmpeg", "-i", str(audio_path),
            "-af", "loudnorm=I=-14:print_format=json",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            output = result.stderr
            json_start = output.rfind('{')
            json_end = output.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                lufs_data = json.loads(output[json_start:json_end])
                return float(lufs_data.get("input_i", -14))
        except Exception as e:
            self._log(f"Erreur mesure loudness: {e}")
        
        return None
    
    def normalize_track(
        self,
        input_path: Path,
        output_path: Path,
        target_lufs: float = -14.0
    ) -> bool:
        """
        Normalise une piste audio au niveau LUFS cible.
        
        Args:
            input_path: Fichier audio source
            output_path: Fichier audio normalisé
            target_lufs: Niveau LUFS cible (défaut: -14 pour YouTube)
        
        Returns:
            True si succès
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
            "-ar", "48000",
            "-ac", "2",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode == 0 and output_path.exists()
        except Exception as e:
            self._log(f"Erreur normalisation: {e}")
            return False
    
    def mix_tracks(
        self,
        tracks: List[Dict],
        output_path: Path,
        output_duration: Optional[float] = None
    ) -> bool:
        """
        Mix plusieurs pistes audio avec volumes individuels.
        
        Args:
            tracks: Liste de dict avec 'path', 'volume' (dB), 'offset_ms'
            output_path: Fichier audio mixé
            output_duration: Durée cible en secondes
        
        Returns:
            True si succès
        """
        if not tracks:
            return False
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        inputs = []
        filter_parts = []
        
        for i, track in enumerate(tracks):
            path = track.get("path")
            volume = track.get("volume", 0)
            offset_ms = track.get("offset_ms", 0)
            
            inputs.extend(["-i", str(path)])
            
            delay = f"adelay={offset_ms}|{offset_ms}" if offset_ms > 0 else ""
            vol = f"volume={volume}dB" if volume != 0 else ""
            
            filters = [f for f in [delay, vol] if f]
            if filters:
                filter_parts.append(f"[{i}:a]{','.join(filters)}[a{i}]")
            else:
                filter_parts.append(f"[{i}:a]anull[a{i}]")
        
        mix_inputs = "".join(f"[a{i}]" for i in range(len(tracks)))
        filter_parts.append(f"{mix_inputs}amix=inputs={len(tracks)}:duration=longest:normalize=0[out]")
        
        filter_complex = ";".join(filter_parts)
        
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s24le",
            str(output_path)
        ]
        
        self._log(f"Mix {len(tracks)} pistes...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self._log(f"Erreur mix: {result.stderr[-500:]}")
                return False
            
            return output_path.exists()
        except Exception as e:
            self._log(f"Exception mix: {e}")
            return False
    
    def mix_and_normalize(
        self,
        audio_tracks: List[Path],
        output_path: Path,
        target_lufs: float = -14.0,
        custom_volumes: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Pipeline complet: détection type → volumes → mix → normalisation.
        
        Args:
            audio_tracks: Liste des fichiers audio
            output_path: Fichier de sortie
            target_lufs: Niveau LUFS cible
            custom_volumes: Volumes personnalisés par type
        
        Returns:
            True si succès
        """
        if not audio_tracks:
            self._log("Aucune piste audio fournie")
            return False
        
        volumes = {**self.DEFAULT_VOLUMES}
        if custom_volumes:
            volumes.update(custom_volumes)
        
        tracks_config = []
        
        for audio_path in audio_tracks:
            track_type = self.detect_track_type(audio_path)
            volume = volumes.get(track_type, volumes["default"])
            
            info = self.get_audio_info(audio_path)
            duration = info.get("duration", 0) if info else 0
            
            tracks_config.append({
                "path": audio_path,
                "type": track_type,
                "volume": volume,
                "offset_ms": 0,
                "duration": duration
            })
            
            self._log(f"  Piste: {audio_path.name} ({track_type}, {volume}dB, {duration:.2f}s)")
        
        temp_dir = output_path.parent / "_temp_audio"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if len(tracks_config) == 1:
                mixed_path = tracks_config[0]["path"]
            else:
                mixed_path = temp_dir / "mixed.wav"
                if not self.mix_tracks(tracks_config, mixed_path):
                    self._log("Mix échoué")
                    return False
                self._log("Mix terminé")
            
            self._log(f"Normalisation vers {target_lufs} LUFS...")
            if not self.normalize_track(mixed_path, output_path, target_lufs):
                self._log("Normalisation échouée")
                return False
            
            self._log(f"Audio final: {output_path}")
            return True
            
        finally:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def sync_to_video(
        self,
        audio_path: Path,
        video_duration: float,
        output_path: Path,
        fade_out_duration: float = 2.0
    ) -> bool:
        """
        Ajuste la durée de l'audio pour correspondre à la vidéo.
        
        Args:
            audio_path: Fichier audio source
            video_duration: Durée de la vidéo en secondes
            output_path: Fichier audio ajusté
            fade_out_duration: Durée du fade out en secondes
        
        Returns:
            True si succès
        """
        audio_info = self.get_audio_info(audio_path)
        if not audio_info:
            return False
        
        audio_duration = audio_info.get("duration", 0)
        
        filters = []
        
        if audio_duration < video_duration:
            pad_duration = video_duration - audio_duration
            filters.append(f"apad=pad_dur={pad_duration}")
            self._log(f"Padding audio: +{pad_duration:.2f}s")
        elif audio_duration > video_duration:
            filters.append(f"atrim=0:{video_duration}")
            fade_start = video_duration - fade_out_duration
            if fade_start > 0:
                filters.append(f"afade=t=out:st={fade_start}:d={fade_out_duration}")
            self._log(f"Trim audio: {audio_duration:.2f}s → {video_duration:.2f}s")
        
        if not filters:
            import shutil
            shutil.copy(audio_path, output_path)
            return True
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-af", ",".join(filters),
            "-ar", "48000",
            "-c:a", "pcm_s24le",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode == 0 and output_path.exists()
        except Exception as e:
            self._log(f"Erreur sync: {e}")
            return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python audio_sync.py <output.wav> <input1.wav> [input2.wav] ...")
        print("  Mixe et normalise les pistes audio vers output.wav")
        sys.exit(1)
    
    output_file = Path(sys.argv[1])
    input_files = [Path(f) for f in sys.argv[2:]]
    
    sync = AudioSync(verbose=True)
    success = sync.mix_and_normalize(input_files, output_file)
    
    sys.exit(0 if success else 1)
