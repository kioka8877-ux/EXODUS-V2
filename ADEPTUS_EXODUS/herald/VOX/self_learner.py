"""
VOX — Self Learner
Role : Apprendre depuis les echecs et succes passes
       Transformer erreurs -> regles -> RULES.md

Cycle d'apprentissage :
  1. Lire VULKAN_FORGE/MEMORY/what_failed.json
  2. Lire VULKAN_FORGE/MEMORY/what_worked.json
  3. Extraire les patterns (lecons)
  4. Ecrire/mettre a jour RULES.md

Usage :
  python self_learner.py --learn
  python self_learner.py --rules
  python self_learner.py --add-rule "Toujours X avant Y"
"""

import sys
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent
VULKAN_MEMORY = BASE / "VULKAN_FORGE" / "MEMORY"
RULES_FILE = Path(__file__).parent / "RULES.md"


def load_memory():
    """Charge les fichiers de memoire de VULKAN_FORGE."""
    memory = {"worked": [], "failed": []}

    worked_file = VULKAN_MEMORY / "what_worked.json"
    failed_file = VULKAN_MEMORY / "what_failed.json"

    if worked_file.exists():
        memory["worked"] = json.loads(worked_file.read_text())
    if failed_file.exists():
        memory["failed"] = json.loads(failed_file.read_text())

    return memory


def extract_rules(memory):
    """
    Extrait des regles depuis les entrees de memoire.
    Retourne une liste de regles sous forme de strings.
    """
    rules = []

    for win in memory.get("worked", []):
        pattern = win.get("pattern_extrait")
        if pattern:
            rules.append({
                "source": f"WIN_{win.get('id', '?')}",
                "fregate": win.get("fregate", "?"),
                "rule": pattern,
                "type": "DO",
            })

    for fail in memory.get("failed", []):
        lecon = fail.get("lecon")
        if lecon:
            rules.append({
                "source": f"FAIL_{fail.get('id', '?')}",
                "fregate": fail.get("fregate", "?"),
                "rule": lecon,
                "type": "AVOID",
            })

    return rules


def write_rules_md(rules, extra_rules=None):
    """
    Ecrit RULES.md avec toutes les regles apprises.
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# RULES.md — Regles Apprises par VOX",
        "",
        f"> Mis a jour le {now}",
        "> Source : VULKAN_FORGE/MEMORY/ + apprentissage en continu",
        "",
        "---",
        "",
        "## Regles DO (ce qui fonctionne)",
        "",
    ]

    do_rules = [r for r in rules if r["type"] == "DO"]
    for i, r in enumerate(do_rules, 1):
        lines.append(f"### DO-{i:02d} [{r['fregate']}]")
        lines.append(f"{r['rule']}")
        lines.append(f"*Source : {r['source']}*")
        lines.append("")

    if not do_rules:
        lines.append("*(aucune regle DO pour l'instant)*")
        lines.append("")

    lines += [
        "---",
        "",
        "## Regles AVOID (ce qui echoue)",
        "",
    ]

    avoid_rules = [r for r in rules if r["type"] == "AVOID"]
    for i, r in enumerate(avoid_rules, 1):
        lines.append(f"### AVOID-{i:02d} [{r['fregate']}]")
        lines.append(f"{r['rule']}")
        lines.append(f"*Source : {r['source']}*")
        lines.append("")

    if not avoid_rules:
        lines.append("*(aucune regle AVOID pour l'instant)*")
        lines.append("")

    # Regles manuelles
    if extra_rules:
        lines += [
            "---",
            "",
            "## Regles Manuelles (ajoutees par l'Empereur ou Vulkan)",
            "",
        ]
        for r in extra_rules:
            lines.append(f"- {r}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Constitution Imperiale (Immuable)",
        "",
        "```",
        "Les fregates produisent.",
        "Les Mini Programs servent.",
        "L'Empereur regne.",
        "```",
    ]

    content = "\n".join(lines) + "\n"
    RULES_FILE.write_text(content)
    return len(rules)


def run_learning_cycle():
    """
    Execute le cycle complet d'apprentissage.
    1. Charge memoire
    2. Extrait regles
    3. Ecrit RULES.md
    """
    memory = load_memory()
    rules = extract_rules(memory)

    # Lire regles existantes manuelles si RULES.md existe
    extra_rules = []
    if RULES_FILE.exists():
        content = RULES_FILE.read_text()
        if "## Regles Manuelles" in content:
            section = content.split("## Regles Manuelles")[1]
            for line in section.splitlines():
                if line.startswith("- "):
                    extra_rules.append(line[2:].strip())

    count = write_rules_md(rules, extra_rules)

    result = {
        "status": "LEARNED",
        "rules_extracted": count,
        "wins_processed": len(memory["worked"]),
        "fails_processed": len(memory["failed"]),
        "rules_file": str(RULES_FILE),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return result


def add_manual_rule(rule_text):
    """Ajoute une regle manuelle et relance le cycle."""
    memory = load_memory()
    rules = extract_rules(memory)

    existing_manual = []
    if RULES_FILE.exists():
        content = RULES_FILE.read_text()
        if "## Regles Manuelles" in content:
            section = content.split("## Regles Manuelles")[1]
            for line in section.splitlines():
                if line.startswith("- "):
                    existing_manual.append(line[2:].strip())

    if rule_text not in existing_manual:
        existing_manual.append(rule_text)

    write_rules_md(rules, existing_manual)
    return {"added": rule_text, "total_manual": len(existing_manual)}


if __name__ == "__main__":
    if "--learn" in sys.argv:
        result = run_learning_cycle()
        print(json.dumps(result, indent=2))

    elif "--rules" in sys.argv:
        if RULES_FILE.exists():
            print(RULES_FILE.read_text())
        else:
            print("[SELF_LEARNER] Aucune regle — lancer --learn d'abord")

    elif "--add-rule" in sys.argv:
        idx = sys.argv.index("--add-rule")
        rule = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if rule:
            result = add_manual_rule(rule)
            print(json.dumps(result, indent=2))
        else:
            print("Usage: --add-rule 'Texte de la regle'")
    else:
        print(__doc__)
