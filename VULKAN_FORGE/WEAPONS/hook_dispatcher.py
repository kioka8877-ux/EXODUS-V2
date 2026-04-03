"""
WEAPON : hook_dispatcher
Role : Dispatcher d'evenements entre Tech-Pretres
       Permet a VULKAN_FORGE de notifier les autres Mini Programs
Usage : python hook_dispatcher.py <event> <payload_json>
Events : fix.applied | fregate.validated | arsenal.updated | session.start
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

MEMORY_PATH = Path(__file__).parent.parent / "MEMORY"
LEDGER_DB = MEMORY_PATH / "experience_ledger.db"


def dispatch(event, payload=None):
    """
    Dispatche un evenement dans le systeme.
    Loggue dans experience_ledger.db.
    Retourne dict avec status et event_id.
    """
    if payload is None:
        payload = {}

    timestamp = datetime.utcnow().isoformat()

    # Log dans ledger
    event_id = _log_to_ledger(event, payload, timestamp)

    # Router selon l'event
    handlers = {
        "fix.applied": _on_fix_applied,
        "fregate.validated": _on_fregate_validated,
        "arsenal.updated": _on_arsenal_updated,
        "session.start": _on_session_start,
    }

    handler = handlers.get(event)
    if handler:
        handler(payload, timestamp)

    print(f"[HOOK] {event} dispatche — id={event_id} — {timestamp}")
    return {"status": "DISPATCHED", "event": event, "event_id": event_id, "timestamp": timestamp}


def _log_to_ledger(event, payload, timestamp):
    if not LEDGER_DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(LEDGER_DB))
        c = conn.cursor()
        c.execute(
            "INSERT INTO entries (date, session, type, description) VALUES (?, ?, ?, ?)",
            (timestamp[:10], event, "fix" if "fix" in event else "decision",
             json.dumps(payload, ensure_ascii=False)[:500])
        )
        event_id = c.lastrowid
        conn.commit()
        conn.close()
        return event_id
    except Exception as e:
        print(f"[HOOK] Warning ledger : {e}")
        return None


def _on_fix_applied(payload, ts):
    fix_id = payload.get("fix_id", "unknown")
    fregate = payload.get("fregate", "unknown")
    print(f"[HOOK] fix.applied -> fix={fix_id}, fregate={fregate}")


def _on_fregate_validated(payload, ts):
    fregate = payload.get("fregate", "unknown")
    print(f"[HOOK] fregate.validated -> {fregate} est validee")


def _on_arsenal_updated(payload, ts):
    item = payload.get("item", "unknown")
    print(f"[HOOK] arsenal.updated -> nouvel item : {item}")


def _on_session_start(payload, ts):
    print(f"[HOOK] session.start -> Vulkan charge son contexte")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hook_dispatcher.py <event> [payload_json]")
        print("Events: fix.applied | fregate.validated | arsenal.updated | session.start")
        sys.exit(1)

    event = sys.argv[1]
    payload = {}
    if len(sys.argv) > 2:
        try:
            payload = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(f"[HOOK] Warning : payload JSON invalide")

    result = dispatch(event, payload)
    print(json.dumps(result, indent=2))
