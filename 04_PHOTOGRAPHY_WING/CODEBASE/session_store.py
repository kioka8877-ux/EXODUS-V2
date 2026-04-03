"""
ATLAS — Session Store
Role : Persistance de l'etat d'une session de production
       Chaque run de fregate ecrit son etat ici pour les suivants

Usage :
  from session_store import SessionStore
  store = SessionStore("U03")
  store.set("vertex_count", 16641)
  store.set("scene_type", "cinematic")
  store.save()

  # Session suivante
  store = SessionStore("U03")
  count = store.get("vertex_count")  # 16641
"""

import json
import os
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path(__file__).parent / "sessions"


class SessionStore:
    """Store de session par fregate. Persiste sur disque."""

    def __init__(self, fregate_id, auto_load=True):
        self.fregate_id = fregate_id.upper()
        self.session_file = SESSIONS_DIR / f"session_{self.fregate_id}.json"
        self._data = {}

        SESSIONS_DIR.mkdir(exist_ok=True)

        if auto_load and self.session_file.exists():
            self._data = json.loads(self.session_file.read_text())

    def set(self, key, value):
        """Ecrit une valeur dans le store."""
        self._data[key] = value
        self._data["_last_updated"] = datetime.utcnow().isoformat()
        return self

    def get(self, key, default=None):
        """Lit une valeur depuis le store."""
        return self._data.get(key, default)

    def update(self, mapping):
        """Met a jour plusieurs cles en une fois."""
        for k, v in mapping.items():
            self.set(k, v)
        return self

    def save(self):
        """Persiste le store sur disque."""
        self._data["_fregate"] = self.fregate_id
        self._data["_saved_at"] = datetime.utcnow().isoformat()
        self.session_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))
        return self

    def clear(self):
        """Vide le store (garde les metadonnees)."""
        self._data = {}
        if self.session_file.exists():
            self.session_file.unlink()
        return self

    def snapshot(self):
        """Retourne une copie du store actuel."""
        return dict(self._data)

    def __repr__(self):
        return f"SessionStore(fregate={self.fregate_id}, keys={list(self._data.keys())})"


def get_all_sessions():
    """Retourne l'etat de toutes les sessions actives."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    sessions = {}
    for f in sorted(SESSIONS_DIR.glob("session_*.json")):
        fregate_id = f.stem.replace("session_", "")
        try:
            data = json.loads(f.read_text())
            sessions[fregate_id] = {
                "last_updated": data.get("_last_updated", "unknown"),
                "keys": [k for k in data.keys() if not k.startswith("_")],
            }
        except Exception as e:
            sessions[fregate_id] = {"error": str(e)}
    return sessions


if __name__ == "__main__":
    import sys

    if "--demo" in sys.argv:
        print("[SESSION_STORE] Demo run...")
        store = SessionStore("U03")
        store.update({
            "vertex_count": 16641,
            "scene_type": "cinematic",
            "camera": "camera_main",
            "last_run": datetime.utcnow().isoformat(),
        })
        store.save()
        print(f"[SESSION_STORE] Sauvegarde : {store.session_file}")
        print(json.dumps(store.snapshot(), indent=2))

    elif "--all" in sys.argv:
        sessions = get_all_sessions()
        print(json.dumps(sessions, indent=2, ensure_ascii=False))

    else:
        fregate_id = sys.argv[1] if len(sys.argv) > 1 else None
        if fregate_id:
            store = SessionStore(fregate_id)
            print(json.dumps(store.snapshot(), indent=2, ensure_ascii=False))
        else:
            print("Usage: python session_store.py <fregate_id>")
            print("       python session_store.py --all")
            print("       python session_store.py --demo")
