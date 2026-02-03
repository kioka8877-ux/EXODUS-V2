#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    EXODUS SETUP — AI Models Downloader                       ║
║              Multi-Mirror Architecture with Integrity Checks                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Version: 1.0.0                                                              ║
║  Mission: Download all AI assets required for EXODUS pipeline                ║
║  Stack: requests + tqdm + multi-mirror fallback                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

ASSETS TÉLÉCHARGÉS:
    - RIFE flownet.pkl : Modèle d'interpolation de frames
    - MCprep addon : Plugin Blender pour Minecraft
    - HDRi studio : Éclairage studio PolyHaven
    - EMOCA : Extraction faciale 3D

UTILISATION:
    python EXO_SETUP_MODELS.py                    # Télécharge tout
    python EXO_SETUP_MODELS.py --dry-run          # Vérifie les URLs sans télécharger
    python EXO_SETUP_MODELS.py --asset rife       # Télécharge seulement RIFE
    python EXO_SETUP_MODELS.py --asset mcprep     # Télécharge seulement MCprep
    python EXO_SETUP_MODELS.py --asset hdri       # Télécharge seulement HDRi
    python EXO_SETUP_MODELS.py --asset emoca      # Télécharge seulement EMOCA
"""

import argparse
import json
import os
import sys
import time
import ssl
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

SETUP_VERSION = "1.0.0"

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


ASSETS: Dict[str, dict] = {
    "rife_flownet": {
        "filename": "flownet.pkl",
        "mirrors": [
            "https://huggingface.co/jbilcke-hf/varnish/resolve/main/rife/flownet.pkl",
            "https://huggingface.co/jbilcke-hf/LTX-Video-0.9.1-HFIE/resolve/main/varnish/rife/flownet.pkl",
            "https://huggingface.co/camenduru/FILM/resolve/main/rife/flownet.pkl",
        ],
        "min_size_mb": 10,
        "category": "RIFE",
        "description": "RIFE FlowNet model for frame interpolation"
    },
    "rife_flownet_v4": {
        "filename": "rife46.pkl",
        "mirrors": [
            "https://huggingface.co/camenduru/FILM/resolve/main/rife/rife46.pkl",
            "https://huggingface.co/NimVideo/RIFE/resolve/main/flownet.pkl",
        ],
        "min_size_mb": 10,
        "category": "RIFE",
        "description": "RIFE v4.6 FlowNet model (alternative)"
    },
    "mcprep_addon": {
        "filename": "MCprep_addon.zip",
        "mirrors": [
            "https://github.com/Moo-Ack-Productions/MCprep/releases/download/3.6.2/MCprep_addon_3.6.2.zip",
            "https://github.com/Moo-Ack-Productions/MCprep/releases/download/3.6.1.2/MCprep_addon_3.6.1.2.zip",
            "https://github.com/Moo-Ack-Productions/MCprep/releases/download/3.6.0/MCprep_addon_3.6.0.zip",
        ],
        "min_size_mb": 0.5,
        "category": "McPrep",
        "description": "MCprep Blender addon for Minecraft workflow"
    },
    "hdri_studio_1k": {
        "filename": "studio_small_09_1k.exr",
        "mirrors": [
            "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/1k/studio_small_09_1k.exr",
        ],
        "min_size_mb": 1,
        "category": "HDRi",
        "description": "PolyHaven studio HDRI (1K resolution)"
    },
    "hdri_studio_2k": {
        "filename": "studio_small_09_2k.exr",
        "mirrors": [
            "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/2k/studio_small_09_2k.exr",
        ],
        "min_size_mb": 3,
        "category": "HDRi",
        "description": "PolyHaven studio HDRI (2K resolution)"
    },
    "hdri_studio_4k": {
        "filename": "studio_small_09_4k.exr",
        "mirrors": [
            "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/4k/studio_small_09_4k.exr",
        ],
        "min_size_mb": 10,
        "category": "HDRi",
        "description": "PolyHaven studio HDRI (4K resolution)"
    },
    "emoca_model": {
        "filename": "EMOCA.zip",
        "mirrors": [
            "https://download.is.tue.mpg.de/emoca/assets/EMOCA/models/EMOCA.zip",
            "https://download.is.tue.mpg.de/emoca/EMOCA.zip",
        ],
        "min_size_mb": 50,
        "category": "EMOCA",
        "description": "EMOCA facial capture model (may require registration)"
    },
    "emoca_deca": {
        "filename": "DECA.zip",
        "mirrors": [
            "https://download.is.tue.mpg.de/emoca/assets/EMOCA/models/DECA.zip",
            "https://download.is.tue.mpg.de/download.php?domain=emoca&sfile=DECA.zip",
        ],
        "min_size_mb": 50,
        "category": "EMOCA",
        "description": "DECA model for 3D face reconstruction"
    },
    "flame_model": {
        "filename": "FLAME2020.zip",
        "mirrors": [
            "https://download.is.tue.mpg.de/download.php?domain=flame&sfile=FLAME2020.zip",
        ],
        "min_size_mb": 10,
        "category": "EMOCA",
        "description": "FLAME head model (requires MPI registration)"
    }
}


class SetupLogger:
    """Logger structuré pour SETUP."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def info(self, msg: str):
        print(f"[SETUP] {msg}")
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[SETUP:DEBUG] {msg}")
    
    def error(self, msg: str):
        print(f"[SETUP:ERROR] {msg}", file=sys.stderr)
    
    def success(self, msg: str):
        print(f"[SETUP:OK] ✓ {msg}")
    
    def warn(self, msg: str):
        print(f"[SETUP:WARN] ⚠ {msg}")
    
    def skip(self, msg: str):
        print(f"[SETUP:SKIP] ○ {msg}")
    
    def fail(self, msg: str):
        print(f"[SETUP:FAIL] ✗ {msg}")


class ExodusModelDownloader:
    """
    Téléchargeur de modèles IA avec architecture multi-miroirs.
    Gère les fallbacks automatiques et la validation d'intégrité.
    """
    
    def __init__(
        self,
        base_path: str = "/content/drive/MyDrive/EXODUS_AI_MODELS",
        verbose: bool = False,
        timeout: int = 60
    ):
        self.base_path = Path(base_path)
        self.logger = SetupLogger(verbose=verbose)
        self.timeout = timeout
        self.assets = ASSETS
        self.session = None
        
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "EXODUS-Setup/1.0 (AI Pipeline Downloader)"
            })
    
    def _ensure_directories(self) -> None:
        """Crée la structure de dossiers nécessaire."""
        categories = set(asset["category"] for asset in self.assets.values())
        for category in categories:
            category_path = self.base_path / category
            category_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Dossier créé/vérifié: {category_path}")
    
    def _get_file_size_mb(self, filepath: Path) -> float:
        """Retourne la taille du fichier en MB."""
        if not filepath.exists():
            return 0.0
        return filepath.stat().st_size / (1024 * 1024)
    
    def verify_integrity(self, filepath: Path, min_size_mb: float) -> bool:
        """Vérifie que le fichier dépasse la taille minimale requise."""
        if not filepath.exists():
            return False
        actual_size = self._get_file_size_mb(filepath)
        return actual_size >= min_size_mb
    
    def _download_with_requests(
        self,
        url: str,
        dest_path: Path,
        show_progress: bool = True
    ) -> bool:
        """Télécharge avec requests + tqdm."""
        if not REQUESTS_AVAILABLE:
            return False
        
        try:
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if show_progress and TQDM_AVAILABLE and total_size > 0:
                progress_bar = tqdm(
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    desc=f"  ↳ {dest_path.name}",
                    ncols=80
                )
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))
                progress_bar.close()
            else:
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"Requests error: {e}")
            return False
    
    def _download_with_urllib(
        self,
        url: str,
        dest_path: Path,
        show_progress: bool = True
    ) -> bool:
        """Télécharge avec urllib (fallback)."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "EXODUS-Setup/1.0"}
            )
            
            with urllib.request.urlopen(req, context=ctx, timeout=self.timeout) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if show_progress and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            bar_len = 40
                            filled = int(bar_len * downloaded / total_size)
                            bar = '█' * filled + '░' * (bar_len - filled)
                            print(f"\r  ↳ {dest_path.name}: [{bar}] {percent:.1f}%", end='')
                
                if show_progress:
                    print()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Urllib error: {e}")
            return False
    
    def _download_file(
        self,
        url: str,
        dest_path: Path,
        show_progress: bool = True
    ) -> bool:
        """Télécharge un fichier en utilisant la méthode disponible."""
        if REQUESTS_AVAILABLE:
            if self._download_with_requests(url, dest_path, show_progress):
                return True
        
        return self._download_with_urllib(url, dest_path, show_progress)
    
    def check_url_availability(self, url: str) -> Tuple[bool, Optional[int]]:
        """Vérifie si une URL est accessible et retourne la taille."""
        try:
            if REQUESTS_AVAILABLE:
                response = self.session.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    size = int(response.headers.get('content-length', 0))
                    return True, size
                elif response.status_code in (302, 301, 405):
                    response = self.session.get(url, stream=True, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        size = int(response.headers.get('content-length', 0))
                        return True, size
            else:
                req = urllib.request.Request(url, method='HEAD')
                req.add_header("User-Agent", "EXODUS-Setup/1.0")
                with urllib.request.urlopen(req, timeout=10) as response:
                    size = int(response.headers.get('Content-Length', 0))
                    return True, size
        except Exception as e:
            self.logger.debug(f"URL check failed for {url}: {e}")
        
        return False, None
    
    def download_with_fallback(
        self,
        asset_key: str,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Tente chaque miroir jusqu'au succès.
        
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        if asset_key not in self.assets:
            return False, f"Asset inconnu: {asset_key}"
        
        asset = self.assets[asset_key]
        category = asset["category"]
        filename = asset["filename"]
        min_size_mb = asset["min_size_mb"]
        mirrors = asset["mirrors"]
        
        dest_dir = self.base_path / category
        dest_path = dest_dir / filename
        
        if self.verify_integrity(dest_path, min_size_mb):
            actual_size = self._get_file_size_mb(dest_path)
            self.logger.skip(f"{filename} existe déjà ({actual_size:.2f} MB)")
            return True, "already_exists"
        
        if dry_run:
            self.logger.info(f"[DRY-RUN] Vérification des miroirs pour {filename}...")
            for i, mirror in enumerate(mirrors, 1):
                available, size = self.check_url_availability(mirror)
                size_str = f"{size / (1024*1024):.2f} MB" if size else "taille inconnue"
                status = "✓ OK" if available else "✗ FAIL"
                self.logger.info(f"  Miroir {i}: {status} ({size_str})")
                self.logger.debug(f"    URL: {mirror}")
            return True, "dry_run_complete"
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for i, mirror_url in enumerate(mirrors, 1):
            self.logger.info(f"Tentative miroir {i}/{len(mirrors)} pour {filename}...")
            self.logger.debug(f"URL: {mirror_url}")
            
            try:
                temp_path = dest_path.with_suffix(dest_path.suffix + '.tmp')
                
                if self._download_file(mirror_url, temp_path, show_progress=True):
                    if self.verify_integrity(temp_path, min_size_mb):
                        temp_path.rename(dest_path)
                        actual_size = self._get_file_size_mb(dest_path)
                        self.logger.success(f"{filename} téléchargé ({actual_size:.2f} MB)")
                        return True, f"downloaded_from_mirror_{i}"
                    else:
                        actual_size = self._get_file_size_mb(temp_path)
                        self.logger.warn(f"Fichier trop petit ({actual_size:.2f} MB < {min_size_mb} MB)")
                        temp_path.unlink(missing_ok=True)
                else:
                    self.logger.warn(f"Échec du téléchargement depuis miroir {i}")
                    temp_path.unlink(missing_ok=True)
                    
            except Exception as e:
                self.logger.debug(f"Exception: {e}")
                continue
        
        self.logger.fail(f"Tous les miroirs ont échoué pour {filename}")
        return False, "all_mirrors_failed"
    
    def download_all(
        self,
        dry_run: bool = False,
        categories: Optional[List[str]] = None
    ) -> Dict[str, dict]:
        """
        Télécharge tous les assets et retourne un rapport détaillé.
        
        Args:
            dry_run: Si True, vérifie seulement les URLs sans télécharger
            categories: Liste de catégories à télécharger (None = toutes)
        
        Returns:
            Dict avec le statut de chaque asset
        """
        self._ensure_directories()
        
        report = {}
        assets_to_download = []
        
        for key, asset in self.assets.items():
            if categories is None or asset["category"].lower() in [c.lower() for c in categories]:
                assets_to_download.append(key)
        
        if not assets_to_download:
            self.logger.warn("Aucun asset à télécharger")
            return report
        
        self.logger.info(f"{'Vérification' if dry_run else 'Téléchargement'} de {len(assets_to_download)} assets...")
        print()
        
        for i, asset_key in enumerate(assets_to_download, 1):
            asset = self.assets[asset_key]
            self.logger.info(f"[{i}/{len(assets_to_download)}] {asset['description']}")
            
            success, status = self.download_with_fallback(asset_key, dry_run=dry_run)
            
            dest_path = self.base_path / asset["category"] / asset["filename"]
            report[asset_key] = {
                "success": success,
                "status": status,
                "filename": asset["filename"],
                "category": asset["category"],
                "path": str(dest_path),
                "size_mb": self._get_file_size_mb(dest_path) if dest_path.exists() else 0
            }
            print()
        
        return report
    
    def print_report(self, report: Dict[str, dict]) -> None:
        """Affiche un rapport formaté des téléchargements."""
        print()
        print("=" * 70)
        print("                    RAPPORT DE TÉLÉCHARGEMENT")
        print("=" * 70)
        
        success_count = sum(1 for r in report.values() if r["success"])
        total_count = len(report)
        
        for asset_key, result in report.items():
            status_icon = "✅" if result["success"] else "❌"
            size_str = f"{result['size_mb']:.2f} MB" if result['size_mb'] > 0 else "N/A"
            print(f"{status_icon} {result['filename']:<40} [{result['category']:<8}] {size_str}")
        
        print("-" * 70)
        print(f"Total: {success_count}/{total_count} assets téléchargés avec succès")
        
        if success_count == total_count:
            print("\n🎉 Tous les modèles IA sont prêts pour EXODUS!")
        else:
            print("\n⚠️  Certains téléchargements ont échoué.")
            print("   Vérifiez votre connexion ou les URLs des miroirs.")
            
            failed = [k for k, v in report.items() if not v["success"]]
            if failed:
                print("\n   Assets manquants:")
                for key in failed:
                    asset = self.assets[key]
                    print(f"   - {asset['filename']} ({asset['category']})")
                    if "emoca" in key.lower() or "flame" in key.lower():
                        print("     ⚠️  Ce modèle nécessite peut-être une inscription sur https://emoca.is.tue.mpg.de/")
        
        print("=" * 70)


def get_category_from_asset_name(name: str) -> Optional[List[str]]:
    """Convertit un nom d'asset en liste de catégories."""
    name = name.lower()
    mapping = {
        "rife": ["RIFE"],
        "mcprep": ["McPrep"],
        "hdri": ["HDRi"],
        "emoca": ["EMOCA"],
        "all": None
    }
    return mapping.get(name)


def main():
    parser = argparse.ArgumentParser(
        description=f'EXODUS SETUP — AI Models Downloader v{SETUP_VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python EXO_SETUP_MODELS.py                    # Télécharge tous les modèles
  python EXO_SETUP_MODELS.py --dry-run          # Vérifie les URLs sans télécharger
  python EXO_SETUP_MODELS.py --asset rife       # Télécharge seulement RIFE
  python EXO_SETUP_MODELS.py --asset hdri       # Télécharge seulement les HDRi
  python EXO_SETUP_MODELS.py -v                 # Mode verbose

Assets disponibles:
  rife    - Modèles RIFE pour l'interpolation de frames
  mcprep  - MCprep addon pour Blender
  hdri    - HDRi studio de PolyHaven
  emoca   - EMOCA/DECA/FLAME pour la capture faciale
  all     - Tous les assets (défaut)
        """
    )
    
    parser.add_argument(
        '--base-path',
        default="/content/drive/MyDrive/EXODUS_AI_MODELS",
        help='Chemin de base pour les téléchargements'
    )
    parser.add_argument(
        '--asset', '-a',
        choices=['rife', 'mcprep', 'hdri', 'emoca', 'all'],
        default='all',
        help='Asset spécifique à télécharger'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Vérifie les URLs sans télécharger'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Affiche les logs détaillés'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=120,
        help='Timeout en secondes pour les téléchargements'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='Liste tous les assets disponibles'
    )
    
    args = parser.parse_args()
    
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    EXODUS SETUP — AI Models Downloader                       ║")
    print(f"║                              Version {SETUP_VERSION}                                   ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if args.list:
        print("Assets disponibles:")
        print("-" * 70)
        for key, asset in ASSETS.items():
            print(f"  {key:<20} [{asset['category']:<8}] {asset['description']}")
            print(f"    Fichier: {asset['filename']}, Min: {asset['min_size_mb']} MB")
            print(f"    Miroirs: {len(asset['mirrors'])}")
        print("-" * 70)
        return 0
    
    if not REQUESTS_AVAILABLE:
        print("[SETUP:WARN] ⚠ Module 'requests' non disponible, utilisation de urllib")
        print("             Installez avec: pip install requests")
        print()
    
    if not TQDM_AVAILABLE:
        print("[SETUP:WARN] ⚠ Module 'tqdm' non disponible, barres de progression simplifiées")
        print("             Installez avec: pip install tqdm")
        print()
    
    downloader = ExodusModelDownloader(
        base_path=args.base_path,
        verbose=args.verbose,
        timeout=args.timeout
    )
    
    print(f"[SETUP] Chemin de destination: {args.base_path}")
    print(f"[SETUP] Mode: {'Dry-run (vérification)' if args.dry_run else 'Téléchargement'}")
    print()
    
    categories = get_category_from_asset_name(args.asset)
    
    report = downloader.download_all(
        dry_run=args.dry_run,
        categories=categories
    )
    
    downloader.print_report(report)
    
    success_count = sum(1 for r in report.values() if r["success"])
    total_count = len(report)
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
