"""
WEAPON : sentinel_bridge
Role : Interface entre VULKAN_FORGE et SENTINEL_CORE
       Permet a Vulkan de lancer des diagnostics SENTINEL sur une fregate
Usage : python sentinel_bridge.py <fregate_path> [--state] [--ghost] [--full]
"""

import sys
import json
import subprocess
from pathlib import Path

SENTINEL_PATH = Path(__file__).parent.parent.parent / "SENTINEL_CORE" / "CODEBASE"
SENTINEL_CORE = SENTINEL_PATH / "sentinel_core.py"


def check_sentinel_available():
    """Verifie que SENTINEL_CORE est accessible."""
    if not SENTINEL_CORE.exists():
        return False, f"sentinel_core.py introuvable : {SENTINEL_CORE}"
    return True, "SENTINEL disponible"


def run_sentinel_on(fregate_path, mode="state"):
    """
    Lance SENTINEL_CORE sur une fregate donnee.
    mode : 'state' | 'ghost' | 'full'
    Retourne le resultat JSON de SENTINEL.
    """
    ok, msg = check_sentinel_available()
    if not ok:
        return {"error": msg, "status": "SENTINEL_UNAVAILABLE"}

    fregate = Path(fregate_path)
    if not fregate.exists():
        return {"error": f"Fregate introuvable : {fregate_path}", "status": "NOT_FOUND"}

    # Construire la commande selon le mode
    cmd = [sys.executable, str(SENTINEL_CORE), str(fregate), f"--mode={mode}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"status": "OK", "output": result.stdout[:500]}
        else:
            return {"status": "ERROR", "stderr": result.stderr[:500]}
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "detail": "SENTINEL n'a pas repondu en 60s"}
    except Exception as e:
        return {"status": "EXCEPTION", "detail": str(e)}


def get_sentinel_state(fregate_path):
    """Raccourci : lire l'etat d'une fregate via SENTINEL."""
    return run_sentinel_on(fregate_path, mode="state")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sentinel_bridge.py <fregate_path> [--state|--ghost|--full]")
        sys.exit(1)

    fregate_path = sys.argv[1]
    mode = "state"
    if "--ghost" in sys.argv:
        mode = "ghost"
    elif "--full" in sys.argv:
        mode = "full"

    ok, msg = check_sentinel_available()
    print(f"[SENTINEL_BRIDGE] {msg}")

    result = run_sentinel_on(fregate_path, mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
