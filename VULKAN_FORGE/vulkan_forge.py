"""
VULKAN_FORGE — Orchestrateur Principal
Version : 1.0
Role : Command layer de l'Arsenal de Vulkan

Commandes :
  status          — Etat de l'Empire (fregates + tech-pretres)
  arsenal         — Lister les scripts/patterns/fixes disponibles
  test [fix_id]   — Tester un fix ou tous les fixes
  dispatch <event> — Dispatcher un evenement
  ledger          — Voir les dernieres entrees du ledger

Usage :
  python vulkan_forge.py status
  python vulkan_forge.py arsenal
  python vulkan_forge.py test --all
  python vulkan_forge.py dispatch session.start
"""

import sys
import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
CONTEXT = BASE / "CONTEXT"
ARSENAL = BASE / "ARSENAL"
MEMORY = BASE / "MEMORY"
WEAPONS = BASE / "WEAPONS"
LEDGER_DB = MEMORY / "experience_ledger.db"


def cmd_status():
    """Affiche l'etat de l'Empire depuis EMPIRE_STATE.md"""
    state_file = CONTEXT / "EMPIRE_STATE.md"
    if not state_file.exists():
        print("[FORGE] EMPIRE_STATE.md introuvable")
        return
    print("[FORGE] === EMPIRE STATE ===")
    print(state_file.read_text())


def cmd_arsenal():
    """Liste tous les elements de l'Arsenal."""
    print("[FORGE] === ARSENAL ===\n")

    categories = {
        "scripts": ARSENAL / "scripts",
        "patterns": ARSENAL / "patterns",
        "fixes": ARSENAL / "fixes",
    }

    for cat, path in categories.items():
        items = list(path.glob("*")) if path.exists() else []
        items = [i for i in items if not i.name.endswith('.md')]
        print(f"  {cat.upper()} ({len(items)}) :")
        for item in sorted(items):
            print(f"    - {item.name}")
        print()


def cmd_test(fix_id=None):
    """Lance test_runner sur un fix ou tous."""
    test_runner = WEAPONS / "test_runner.py"
    if not test_runner.exists():
        print("[FORGE] test_runner.py introuvable")
        return

    import subprocess
    args = [sys.executable, str(test_runner)]
    if fix_id:
        args.append(fix_id)
    else:
        args.append("--all")

    result = subprocess.run(args, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"[FORGE] STDERR: {result.stderr}")


def cmd_dispatch(event, payload=None):
    """Dispatche un evenement via hook_dispatcher."""
    dispatcher = WEAPONS / "hook_dispatcher.py"
    if not dispatcher.exists():
        print("[FORGE] hook_dispatcher.py introuvable")
        return

    import subprocess
    args = [sys.executable, str(dispatcher), event]
    if payload:
        args.append(json.dumps(payload))

    result = subprocess.run(args, capture_output=True, text=True)
    print(result.stdout)


def cmd_ledger(limit=10):
    """Affiche les dernieres entrees du ledger."""
    if not LEDGER_DB.exists():
        print("[FORGE] experience_ledger.db introuvable")
        return

    conn = sqlite3.connect(str(LEDGER_DB))
    c = conn.cursor()
    c.execute("SELECT id, date, type, description FROM entries ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()

    print(f"[FORGE] === LEDGER — {len(rows)} dernieres entrees ===\n")
    for row in rows:
        print(f"  [{row[0]}] {row[1]} | {row[2]} | {row[3][:80]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "status":
        cmd_status()
    elif cmd == "arsenal":
        cmd_arsenal()
    elif cmd == "test":
        fix_id = args[0] if args and args[0] != "--all" else None
        cmd_test(fix_id)
    elif cmd == "dispatch":
        if not args:
            print("[FORGE] Usage: dispatch <event> [payload_json]")
            sys.exit(1)
        payload = json.loads(args[1]) if len(args) > 1 else None
        cmd_dispatch(args[0], payload)
    elif cmd == "ledger":
        limit = int(args[0]) if args else 10
        cmd_ledger(limit)
    else:
        print(f"[FORGE] Commande inconnue : {cmd}")
        print("Commandes : status | arsenal | test | dispatch | ledger")
        sys.exit(1)


if __name__ == "__main__":
    main()
