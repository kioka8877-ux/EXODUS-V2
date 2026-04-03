"""
WEAPON : diff_analyzer
Role : Analyser les differences entre deux versions d'un fichier
Usage : python diff_analyzer.py <fichier_avant> <fichier_apres>
       python diff_analyzer.py --commit <hash> <fichier>
"""

import sys
import difflib
import json
from pathlib import Path


def analyze_diff(before_path, after_path):
    """
    Compare deux fichiers et retourne un rapport structure.
    """
    before = Path(before_path)
    after = Path(after_path)

    if not before.exists():
        return {"error": f"Fichier avant introuvable : {before_path}"}
    if not after.exists():
        return {"error": f"Fichier apres introuvable : {after_path}"}

    before_lines = before.read_text().splitlines(keepends=True)
    after_lines = after.read_text().splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        before_lines, after_lines,
        fromfile=f"avant: {before.name}",
        tofile=f"apres: {after.name}"
    ))

    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))

    return {
        "avant": str(before),
        "apres": str(after),
        "lignes_ajoutees": added,
        "lignes_supprimees": removed,
        "delta_net": added - removed,
        "diff_preview": "".join(diff[:30]) if diff else "(aucun changement)",
        "verdict": "MODIFIE" if diff else "IDENTIQUE"
    }


def analyze_string_diff(before_content, after_content, label="fichier"):
    """
    Compare deux strings directement (utile pour tests inline).
    """
    before_lines = before_content.splitlines(keepends=True)
    after_lines = after_content.splitlines(keepends=True)
    diff = list(difflib.unified_diff(before_lines, after_lines))
    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
    return {
        "label": label,
        "lignes_ajoutees": added,
        "lignes_supprimees": removed,
        "verdict": "MODIFIE" if diff else "IDENTIQUE"
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python diff_analyzer.py <avant> <apres>")
        sys.exit(1)

    result = analyze_diff(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if "diff_preview" in result:
        print("\n--- DIFF PREVIEW ---")
        print(result["diff_preview"])
