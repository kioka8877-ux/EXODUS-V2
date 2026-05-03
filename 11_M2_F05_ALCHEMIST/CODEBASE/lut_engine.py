"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         FRÉGATE 05_ALCHEMIST — LUT ENGINE (Mode C — Python)                 ║
║         Application de LUT .cube 3D via interpolation trilinéaire           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Stack    : numpy pur (défaut) + colour-science optionnel (DECRET IV)        ║
║  Format   : .cube 3D (standard Adobe/DaVinci)                                ║
║  Mission  : Appliquer un grade colorimétrique scriptable et reproductible    ║
╚══════════════════════════════════════════════════════════════════════════════╝

DECRET I — Inventaire et Versionnage des LUTs
    Chaque LUT doit figurer dans LUTS/MANIFEST.json.
    Les .cube sont versionnés dans le repo — aucune dépendance externe.

DECRET III — LUT Engine Python (Mode C)
    Activation : --lut path/to/lut.cube [--lut-intensity 0.8]
    Interpolation trilinéaire 3D — précision identique à DaVinci Resolve.

DECRET IV — colour-science pour Mode C (pipeline Python)
    Activation : --use-colour-science (en combinaison avec --lut)
    colour.io.read_LUT() lit le .cube nativement.
    colour.LUT3D.apply() interpole en espace linéaire.
    imageio lit/écrit les frames EXR (float32 HDR).
    Mode C complet : EXR → colour-science LUT → EXR.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Tuple

try:
    import colour
    import imageio
    HAS_COLOUR_SCIENCE = True
except ImportError:
    HAS_COLOUR_SCIENCE = False


class LUTEngine:
    """
    Charge et applique des LUTs 3D au format .cube via interpolation trilinéaire.

    Le format .cube stocke les entrées avec R le plus rapide :
        index = r_idx + g_idx * size + b_idx * size^2
    → reshape en (size, size, size, 3) donne lut[b_idx, g_idx, r_idx] = [R_out, G_out, B_out]
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._lut_data: Optional[np.ndarray] = None
        self._lut_size: int = 0
        self._lut_path: str = ""

    # ─────────────────────────────────────────────────────────────────────────
    # CHARGEMENT
    # ─────────────────────────────────────────────────────────────────────────

    def load(self, cube_path: Path) -> bool:
        """Charge un fichier .cube. Retourne True si succès."""
        try:
            lut_data, lut_size = self._parse_cube(cube_path)
            self._lut_data = lut_data
            self._lut_size = lut_size
            self._lut_path = str(cube_path)
            if self.verbose:
                print(f"  [LUT] Charge: {cube_path.name} (size={lut_size}, entrees={lut_size**3})")
            return True
        except Exception as e:
            print(f"  [LUT:ERROR] Echec chargement {cube_path}: {e}")
            return False

    def _parse_cube(self, path: Path) -> Tuple[np.ndarray, int]:
        """Parse un fichier .cube 3D. Retourne (lut_array, size)."""
        size = 0
        entries = []

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.upper().startswith("LUT_3D_SIZE"):
                    size = int(line.split()[-1])
                    continue
                if line.upper().startswith(("DOMAIN_", "TITLE", "LUT_1D_SIZE")):
                    continue
                parts = line.split()
                if len(parts) == 3:
                    try:
                        entries.append([float(p) for p in parts])
                    except ValueError:
                        continue

        if size == 0:
            raise ValueError("LUT_3D_SIZE non trouve dans le fichier .cube")

        expected = size ** 3
        if len(entries) != expected:
            raise ValueError(
                f"Entrees attendues: {expected} (size={size}^3), trouvees: {len(entries)}"
            )

        # Reshape C-order → lut[b_idx, g_idx, r_idx] = [R_out, G_out, B_out]
        lut_array = np.array(entries, dtype=np.float32).reshape(size, size, size, 3)
        return lut_array, size

    # ─────────────────────────────────────────────────────────────────────────
    # APPLICATION
    # ─────────────────────────────────────────────────────────────────────────

    def apply(self, frame: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        """
        Applique la LUT chargée à une frame via interpolation trilinéaire.

        Args:
            frame     : Frame BGR (uint8, uint16, ou float32 normalise [0,1])
            intensity : Blend LUT/original [0.0 = original, 1.0 = LUT pur]

        Returns:
            Frame gradée, même dtype que l'input. Passthrough si aucune LUT chargée.
        """
        if self._lut_data is None:
            return frame

        original_dtype = frame.dtype

        # Normaliser en float32 [0, 1]
        if frame.dtype == np.uint8:
            f = frame.astype(np.float32) / 255.0
        elif frame.dtype == np.uint16:
            f = frame.astype(np.float32) / 65535.0
        elif frame.dtype in (np.float32, np.float64):
            f = np.clip(frame.astype(np.float32), 0.0, 1.0)
        else:
            return frame

        result = self._trilinear_interp(f)

        if intensity < 1.0:
            result = f * (1.0 - intensity) + result * intensity

        result = np.clip(result, 0.0, 1.0)

        if original_dtype == np.uint8:
            return (result * 255.0).astype(np.uint8)
        elif original_dtype == np.uint16:
            return (result * 65535.0).astype(np.uint16)
        return result.astype(original_dtype)

    def _trilinear_interp(self, frame: np.ndarray) -> np.ndarray:
        """
        Interpolation trilinéaire 3D sur chaque pixel.

        frame : float32 BGR [0,1], shape (H, W, 3)
        lut   : shape (size, size, size, 3) indexé [b_idx, g_idx, r_idx]
        sortie: float32 BGR [0,1], shape (H, W, 3)
        """
        size = self._lut_size
        lut = self._lut_data
        scale = float(size - 1)

        # Séparer les canaux BGR
        b_ch = frame[:, :, 0]
        g_ch = frame[:, :, 1]
        r_ch = frame[:, :, 2]

        # Coordonnées dans le cube [0, size-1]
        rb = r_ch * scale
        gb = g_ch * scale
        bb = b_ch * scale

        # Indices entiers (floor / ceil), clampés
        r0 = np.clip(np.floor(rb).astype(np.int32), 0, size - 1)
        g0 = np.clip(np.floor(gb).astype(np.int32), 0, size - 1)
        b0 = np.clip(np.floor(bb).astype(np.int32), 0, size - 1)
        r1 = np.clip(r0 + 1, 0, size - 1)
        g1 = np.clip(g0 + 1, 0, size - 1)
        b1 = np.clip(b0 + 1, 0, size - 1)

        # Fractions [0, 1]
        fr = (rb - r0).astype(np.float32)
        fg = (gb - g0).astype(np.float32)
        fb = (bb - b0).astype(np.float32)

        # 8 coins du cube : lut[b_idx, g_idx, r_idx] → [R_out, G_out, B_out]
        c000 = lut[b0, g0, r0]
        c001 = lut[b0, g0, r1]
        c010 = lut[b0, g1, r0]
        c011 = lut[b0, g1, r1]
        c100 = lut[b1, g0, r0]
        c101 = lut[b1, g0, r1]
        c110 = lut[b1, g1, r0]
        c111 = lut[b1, g1, r1]

        fr = fr[:, :, np.newaxis]
        fg = fg[:, :, np.newaxis]
        fb = fb[:, :, np.newaxis]

        # Interpolation le long de r
        c00 = c000 * (1.0 - fr) + c001 * fr
        c01 = c010 * (1.0 - fr) + c011 * fr
        c10 = c100 * (1.0 - fr) + c101 * fr
        c11 = c110 * (1.0 - fr) + c111 * fr

        # Interpolation le long de g
        c0 = c00 * (1.0 - fg) + c01 * fg
        c1 = c10 * (1.0 - fg) + c11 * fg

        # Interpolation le long de b
        c = c0 * (1.0 - fb) + c1 * fb

        # c est [R_out, G_out, B_out] → convertir en BGR pour OpenCV
        return c[:, :, ::-1].copy()

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITAIRES
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def list_available_luts(lut_dir: Path) -> list:
        """Liste les fichiers .cube disponibles dans lut_dir."""
        if not lut_dir.exists():
            return []
        return sorted([f.name for f in lut_dir.iterdir() if f.suffix.lower() == ".cube"])

    @property
    def is_loaded(self) -> bool:
        return self._lut_data is not None

    @property
    def loaded_path(self) -> str:
        return self._lut_path

    # ─────────────────────────────────────────────────────────────────────────
    # DECRET IV — colour-science Mode C (EXR natif)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def is_colour_science_available() -> bool:
        """Retourne True si colour-science + imageio sont disponibles."""
        return HAS_COLOUR_SCIENCE

    def apply_colour_science(
        self,
        frame_path: Path,
        output_path: Path,
        lut_path: Path,
        intensity: float = 1.0,
    ) -> bool:
        """
        Applique une LUT .cube à une frame EXR/PNG via colour-science.

        Lit le fichier source avec imageio (HDR float32 natif pour EXR),
        charge la LUT avec colour.io.read_LUT(), applique via LUT3D.apply(),
        blend avec l'original selon `intensity`, écrit le résultat.

        Args:
            frame_path  : Chemin de la frame source (.exr ou .png)
            output_path : Chemin de sortie (.exr ou .png)
            lut_path    : Fichier .cube 3D
            intensity   : Blend LUT/original [0.0 = original, 1.0 = LUT pur]

        Returns:
            True si succès, False sinon.
        """
        if not HAS_COLOUR_SCIENCE:
            if self.verbose:
                print("  [LUT:WARN] colour-science non disponible — fallback numpy")
            return False

        try:
            # Lecture frame — imageio retourne float32 [0,1] pour EXR
            frame_np = imageio.v3.imread(str(frame_path))
            if frame_np is None:
                print(f"  [LUT:ERROR] imageio: impossible de lire {frame_path}")
                return False

            frame_f32 = frame_np.astype(np.float32)
            # Normaliser si entier (PNG 8/16 bit)
            if frame_np.dtype == np.uint8:
                frame_f32 = frame_f32 / 255.0
            elif frame_np.dtype == np.uint16:
                frame_f32 = frame_f32 / 65535.0

            # Charger LUT avec colour-science
            lut = colour.io.read_LUT(str(lut_path))
            if self.verbose:
                print(f"  [LUT:colour] {lut_path.name} — {type(lut).__name__}")

            # Appliquer la LUT (colour travaille en RGB, imageio retourne RGB)
            graded = lut.apply(np.clip(frame_f32, 0.0, 1.0))
            graded = np.clip(graded, 0.0, 1.0).astype(np.float32)

            # Blend avec original
            if intensity < 1.0:
                graded = frame_f32 * (1.0 - intensity) + graded * intensity

            # Reconvertir au dtype source si PNG entier
            if frame_np.dtype == np.uint8:
                out_arr = (graded * 255.0).astype(np.uint8)
            elif frame_np.dtype == np.uint16:
                out_arr = (graded * 65535.0).astype(np.uint16)
            else:
                out_arr = graded  # float32 pour EXR

            output_path.parent.mkdir(parents=True, exist_ok=True)
            imageio.v3.imwrite(str(output_path), out_arr)

            if self.verbose:
                print(f"  [LUT:colour] Ecrit: {output_path.name}")
            return True

        except Exception as e:
            print(f"  [LUT:ERROR] colour-science: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # AUTO-TEST
    # ─────────────────────────────────────────────────────────────────────────

    def self_test(self) -> Tuple[int, int]:
        """Auto-test du moteur LUT. Retourne (passed, total)."""
        passed = 0
        total = 4

        print("═══════════════════════════════════════════════════")
        print("   LUT ENGINE — SELF TEST")
        print("═══════════════════════════════════════════════════")
        print()

        # Test 1 — Passthrough sans LUT chargée
        t1_ok = True
        dummy = np.full((4, 4, 3), 128, dtype=np.uint8)
        result = self.apply(dummy)
        if not np.array_equal(result, dummy):
            t1_ok = False
            print("  ERREUR apply sans LUT devrait retourner frame originale")
        if t1_ok:
            passed += 1
            print("[TEST 1] Passthrough sans LUT ............ OK")
        else:
            print("[TEST 1] Passthrough sans LUT ............ FAIL")

        # Test 2 — intensity=0 retourne original meme avec LUT chargée
        t2_ok = True
        size = 4
        self._lut_data = np.zeros((size, size, size, 3), dtype=np.float32)
        self._lut_size = size
        frame = np.full((2, 2, 3), 128, dtype=np.uint8)
        result = self.apply(frame, intensity=0.0)
        if not np.allclose(result.astype(np.float32), frame.astype(np.float32), atol=2.0):
            t2_ok = False
            print(f"  ERREUR intensity=0 devrait retourner original, max_diff={np.max(np.abs(result.astype(np.float32) - frame.astype(np.float32))):.1f}")
        if t2_ok:
            passed += 1
            print("[TEST 2] Intensity=0 passthrough ......... OK")
        else:
            print("[TEST 2] Intensity=0 passthrough ......... FAIL")

        # Test 3 — LUT identité retourne ~original
        t3_ok = True
        lut_identity = np.zeros((size, size, size, 3), dtype=np.float32)
        for bi in range(size):
            for gi in range(size):
                for ri in range(size):
                    # Output RGB = input RGB
                    lut_identity[bi, gi, ri] = [ri / (size - 1), gi / (size - 1), bi / (size - 1)]
        self._lut_data = lut_identity
        self._lut_size = size
        frame_f = np.array([[[0.25, 0.5, 0.75]]], dtype=np.float32)  # BGR
        result_f = self.apply(frame_f, intensity=1.0)
        if not np.allclose(result_f, frame_f, atol=0.05):
            t3_ok = False
            print(f"  ERREUR LUT identite: attendu~{frame_f.ravel()}, obtenu {result_f.ravel()}")
        if t3_ok:
            passed += 1
            print("[TEST 3] LUT identite passthrough ........ OK")
        else:
            print("[TEST 3] LUT identite passthrough ........ FAIL")

        # Test 4 — Conversion dtype uint16
        t4_ok = True
        frame_u16 = np.full((2, 2, 3), 32767, dtype=np.uint16)
        result_u16 = self.apply(frame_u16, intensity=0.0)
        if result_u16.dtype != np.uint16:
            t4_ok = False
            print(f"  ERREUR dtype attendu uint16, obtenu {result_u16.dtype}")
        if not np.allclose(result_u16.astype(np.float32), frame_u16.astype(np.float32), atol=300.0):
            t4_ok = False
            print(f"  ERREUR uint16 intensity=0 valeurs incorrectes")
        if t4_ok:
            passed += 1
            print("[TEST 4] Preservation dtype uint16 ....... OK")
        else:
            print("[TEST 4] Preservation dtype uint16 ....... FAIL")

        # Cleanup
        self._lut_data = None
        self._lut_size = 0
        self._lut_path = ""

        print()
        print("═══════════════════════════════════════════════════")
        print(f"   RÉSULTAT : {passed}/{total} TESTS PASSÉS")
        print("═══════════════════════════════════════════════════")
        return (passed, total)


if __name__ == "__main__":
    engine = LUTEngine(verbose=True)
    engine.self_test()
