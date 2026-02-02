"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  SMOOTHING ENGINE — Savitzky-Golay Filtering                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module de lissage pour animations faciales.                                 ║
║  Préserve les peaks tout en supprimant le bruit.                             ║
║  Adaptatif: moins de lissage sur les mouvements rapides (micro-expressions). ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import List, Dict, Optional, Union


def savgol_smooth(
    data: np.ndarray,
    window: int = 5,
    order: int = 2
) -> np.ndarray:
    """
    Applique le filtre Savitzky-Golay.
    Préserve les peaks tout en supprimant le bruit haute fréquence.
    
    Args:
        data: Array de données (1D ou 2D avec frames en lignes)
        window: Taille de la fenêtre (doit être impair)
        order: Ordre du polynôme (doit être < window)
    
    Returns:
        Données lissées de même shape que l'input
    """
    from scipy.signal import savgol_filter
    
    if window < 3:
        return data
    
    if window % 2 == 0:
        window += 1
    
    order = min(order, window - 1)
    
    if len(data) < window:
        return data
    
    if data.ndim == 1:
        return savgol_filter(data, window, order)
    else:
        return savgol_filter(data, window, order, axis=0)


def adaptive_smooth(
    data: np.ndarray,
    base_window: int = 5,
    velocity_threshold: float = 0.1,
    fast_window: int = 3
) -> np.ndarray:
    """
    Lissage adaptatif basé sur la vélocité.
    
    - Mouvements lents → plus de lissage (supprime le jitter)
    - Mouvements rapides → moins de lissage (préserve les micro-expressions)
    
    Args:
        data: Array 2D (frames x blendshapes)
        base_window: Fenêtre pour zones lentes
        velocity_threshold: Seuil de vélocité pour distinction lent/rapide
        fast_window: Fenêtre pour zones rapides
    
    Returns:
        Données lissées
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    n_frames, n_features = data.shape
    
    if n_frames < base_window:
        return data
    
    velocity = np.abs(np.diff(data, axis=0))
    velocity = np.vstack([velocity, velocity[-1:]])
    
    result = data.copy()
    
    for i in range(n_features):
        col_data = data[:, i]
        col_velocity = velocity[:, i]
        
        slow_mask = col_velocity < velocity_threshold
        
        slow_segments = _get_segments(slow_mask, min_length=base_window)
        for start, end in slow_segments:
            segment = col_data[start:end]
            if len(segment) >= base_window:
                window = min(base_window, len(segment))
                if window % 2 == 0:
                    window -= 1
                if window >= 3:
                    result[start:end, i] = savgol_smooth(segment, window, 2)
        
        fast_mask = ~slow_mask
        fast_segments = _get_segments(fast_mask, min_length=fast_window)
        for start, end in fast_segments:
            segment = col_data[start:end]
            if len(segment) >= fast_window:
                window = min(fast_window, len(segment))
                if window % 2 == 0:
                    window -= 1
                if window >= 3:
                    result[start:end, i] = savgol_smooth(segment, window, 1)
    
    return result


def _get_segments(mask: np.ndarray, min_length: int = 3) -> List[tuple]:
    """
    Trouve les segments contigus dans un masque booléen.
    
    Returns:
        Liste de tuples (start, end) pour chaque segment
    """
    segments = []
    in_segment = False
    start = 0
    
    for i, val in enumerate(mask):
        if val and not in_segment:
            start = i
            in_segment = True
        elif not val and in_segment:
            if i - start >= min_length:
                segments.append((start, i))
            in_segment = False
    
    if in_segment and len(mask) - start >= min_length:
        segments.append((start, len(mask)))
    
    return segments


def smooth_blendshapes(
    face_data: Dict,
    window: int = 5,
    adaptive: bool = True,
    velocity_threshold: float = 0.1
) -> Dict:
    """
    Lisse les données de blendshapes d'un dictionnaire facial.
    
    Args:
        face_data: Dictionnaire avec structure {"frames": [{"blendshapes": {...}}, ...]}
        window: Taille de fenêtre Savitzky-Golay
        adaptive: Utiliser le lissage adaptatif
        velocity_threshold: Seuil pour le mode adaptatif
    
    Returns:
        Dictionnaire avec blendshapes lissées
    """
    if not face_data.get('frames'):
        return face_data
    
    blendshape_names = list(face_data['frames'][0]['blendshapes'].keys())
    n_frames = len(face_data['frames'])
    n_blendshapes = len(blendshape_names)
    
    data_matrix = np.zeros((n_frames, n_blendshapes))
    
    for i, frame in enumerate(face_data['frames']):
        for j, name in enumerate(blendshape_names):
            data_matrix[i, j] = frame['blendshapes'].get(name, 0.0)
    
    if adaptive:
        smoothed = adaptive_smooth(
            data_matrix,
            base_window=window,
            velocity_threshold=velocity_threshold
        )
    else:
        smoothed = savgol_smooth(data_matrix, window)
    
    result = face_data.copy()
    result['frames'] = []
    
    for i in range(n_frames):
        frame_data = {
            'frame': face_data['frames'][i]['frame'],
            'blendshapes': {},
            'confidence': face_data['frames'][i].get('confidence', 1.0)
        }
        
        for j, name in enumerate(blendshape_names):
            frame_data['blendshapes'][name] = float(np.clip(smoothed[i, j], 0, 1))
        
        result['frames'].append(frame_data)
    
    return result


def compute_smoothing_metrics(original: np.ndarray, smoothed: np.ndarray) -> Dict:
    """
    Calcule des métriques de qualité du lissage.
    
    Returns:
        Dict avec MSE, réduction de jitter, préservation des peaks
    """
    mse = np.mean((original - smoothed) ** 2)
    
    original_diff = np.abs(np.diff(original, axis=0))
    smoothed_diff = np.abs(np.diff(smoothed, axis=0))
    
    jitter_original = np.mean(original_diff)
    jitter_smoothed = np.mean(smoothed_diff)
    jitter_reduction = 1.0 - (jitter_smoothed / (jitter_original + 1e-8))
    
    from scipy.signal import find_peaks
    
    peak_preservation = []
    for i in range(original.shape[1] if original.ndim > 1 else 1):
        col_orig = original[:, i] if original.ndim > 1 else original
        col_smooth = smoothed[:, i] if smoothed.ndim > 1 else smoothed
        
        peaks_orig, _ = find_peaks(col_orig, height=0.3)
        peaks_smooth, _ = find_peaks(col_smooth, height=0.3)
        
        if len(peaks_orig) > 0:
            preserved = len(set(peaks_smooth) & set(peaks_orig)) / len(peaks_orig)
            peak_preservation.append(preserved)
    
    avg_peak_preservation = np.mean(peak_preservation) if peak_preservation else 1.0
    
    return {
        "mse": float(mse),
        "jitter_reduction": float(jitter_reduction),
        "peak_preservation": float(avg_peak_preservation)
    }


if __name__ == "__main__":
    print("=== Test Smoothing Module ===\n")
    
    np.random.seed(42)
    n_frames = 200
    t = np.linspace(0, 4 * np.pi, n_frames)
    
    clean_signal = np.sin(t) * 0.5 + 0.5
    clean_signal[50:70] = np.linspace(0.5, 1.0, 20)
    clean_signal[70:80] = 1.0
    clean_signal[80:100] = np.linspace(1.0, 0.5, 20)
    
    noisy_signal = clean_signal + np.random.normal(0, 0.05, n_frames)
    noisy_signal = np.clip(noisy_signal, 0, 1)
    
    smoothed_basic = savgol_smooth(noisy_signal, window=5)
    
    data_2d = noisy_signal.reshape(-1, 1)
    smoothed_adaptive = adaptive_smooth(data_2d, base_window=7).flatten()
    
    metrics_basic = compute_smoothing_metrics(
        noisy_signal.reshape(-1, 1), 
        smoothed_basic.reshape(-1, 1)
    )
    metrics_adaptive = compute_smoothing_metrics(
        noisy_signal.reshape(-1, 1), 
        smoothed_adaptive.reshape(-1, 1)
    )
    
    print("Basic Savitzky-Golay:")
    print(f"  MSE: {metrics_basic['mse']:.6f}")
    print(f"  Jitter Reduction: {metrics_basic['jitter_reduction']:.2%}")
    print(f"  Peak Preservation: {metrics_basic['peak_preservation']:.2%}")
    
    print("\nAdaptive Smoothing:")
    print(f"  MSE: {metrics_adaptive['mse']:.6f}")
    print(f"  Jitter Reduction: {metrics_adaptive['jitter_reduction']:.2%}")
    print(f"  Peak Preservation: {metrics_adaptive['peak_preservation']:.2%}")
    
    test_face_data = {
        "fps": 30,
        "frames": [
            {"frame": i, "blendshapes": {"mouthSmileLeft": float(noisy_signal[i])}}
            for i in range(n_frames)
        ]
    }
    
    smoothed_data = smooth_blendshapes(test_face_data, window=5, adaptive=True)
    print(f"\nsmooth_blendshapes: {len(smoothed_data['frames'])} frames traitées")
