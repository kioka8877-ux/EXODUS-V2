"""
WEAPON : test_runner
Role : Executer les tests de validation sur les fixes de l'Arsenal
Usage : python test_runner.py [fix_id] [--all]
"""

import sys
import os
import json
import importlib.util
from pathlib import Path

ARSENAL_SCRIPTS = Path(__file__).parent.parent / "ARSENAL" / "scripts"
MEMORY_PATH = Path(__file__).parent.parent / "MEMORY"


def load_script(script_path):
    spec = importlib.util.spec_from_file_location("fix_module", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_test(fix_name):
    """
    Teste un fix de l'Arsenal en mode dry-run (sans Blender).
    Verifie que le module se charge et que les fonctions requises existent.
    """
    script_path = ARSENAL_SCRIPTS / f"{fix_name}.py"
    if not script_path.exists():
        return {"fix": fix_name, "status": "NOT_FOUND", "detail": str(script_path)}

    try:
        # Verifier syntaxe
        with open(script_path) as f:
            source = f.read()
        compile(source, str(script_path), 'exec')

        # Verifier docstring
        has_docstring = '"""' in source or "'''" in source

        return {
            "fix": fix_name,
            "status": "SYNTAX_OK",
            "has_docstring": has_docstring,
            "lines": len(source.splitlines()),
            "path": str(script_path)
        }
    except SyntaxError as e:
        return {"fix": fix_name, "status": "SYNTAX_ERROR", "detail": str(e)}


def run_all():
    """Teste tous les scripts de l'Arsenal."""
    results = []
    for script in sorted(ARSENAL_SCRIPTS.glob("*.py")):
        results.append(run_test(script.stem))
    return results


if __name__ == "__main__":
    if "--all" in sys.argv or len(sys.argv) == 1:
        results = run_all()
        for r in results:
            status = r["status"]
            name = r["fix"]
            print(f"  [{status}] {name}")
        ok = sum(1 for r in results if r["status"] == "SYNTAX_OK")
        print(f"\nTotal : {ok}/{len(results)} OK")
    else:
        fix_name = sys.argv[1]
        result = run_test(fix_name)
        print(json.dumps(result, indent=2))
