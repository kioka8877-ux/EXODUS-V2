"""
VOX — Fleet Reporter
Role : Genere et ecrit les rapports de la flotte en Markdown
       Cree + met a jour TRACKING_UXX.md et TRACKING_MASTER.md
"""

import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent
TRACKING_DIR = BASE / "TRACKING"
ATLAS_PATH = Path(__file__).parent.parent.parent / "magos_logis" / "ATLAS"


def load_pipeline_state():
    state_file = ATLAS_PATH / "pipeline_state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def update_tracking_master(state=None):
    """
    Met a jour TRACKING_MASTER.md avec l'etat actuel de la flotte.
    """
    if state is None:
        state = load_pipeline_state()

    fregates = state.get("fregates", {})
    health = state.get("pipeline_health", {})
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# TRACKING_MASTER — Vue Globale de la Flotte EXODUS",
        "",
        f"> Mis a jour par VOX le {now}",
        "",
        "---",
        "",
        "## Etat de la Flotte",
        "",
        f"- Fregates validees : **{health.get('fregates_validees', '?')}/{health.get('fregates_total', '?')}**",
        f"- Tech-Pretres operationnels : **{health.get('tech_pretres_operationnels', '?')}/{health.get('tech_pretres_total', '?')}**",
        f"- Progression checklist : **{health.get('progression_checklist', '?')}**",
        "",
        "---",
        "",
        "## Fregates",
        "",
        "| ID | Nom | Statut | Dernier Output | Bloquant |",
        "|----|-----|--------|----------------|----------|",
    ]

    for fid in sorted(fregates.keys()):
        f = fregates[fid]
        status = f.get("status", "?")
        icon = "V" if status == "VALIDE" else "~"
        lines.append(
            f"| {fid} | {f.get('name','?')} | {icon} {status} "
            f"| {f.get('last_output') or '—'} "
            f"| {f.get('blocking') or '—'} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Tech-Pretres",
        "",
        "| Nom | Statut | Priorite |",
        "|-----|--------|----------|",
    ]

    for name, tp in sorted(state.get("tech_pretres", {}).items()):
        s = tp.get("status", "?")
        p = tp.get("priorite", "?")
        icon = "V" if "OPERATIONNEL" in s else "~"
        lines.append(f"| {name} | {icon} {s} | P{p} |")

    content = "\n".join(lines) + "\n"
    out_path = TRACKING_DIR / "TRACKING_MASTER.md"
    out_path.write_text(content)
    return {"updated": str(out_path), "timestamp": now}


def update_tracking_fregate(fregate_id, extra_info=None, state=None):
    """
    Met a jour ou cree TRACKING_UXX.md pour une fregate.
    extra_info : dict optionnel avec infos supplementaires a logguer.
    """
    if state is None:
        state = load_pipeline_state()

    fregate_id = fregate_id.upper()
    fregates = state.get("fregates", {})
    fregate = fregates.get(fregate_id, {})
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    tracking_file = TRACKING_DIR / f"TRACKING_{fregate_id}.md"

    # Lire contenu existant si present
    existing = ""
    if tracking_file.exists():
        existing = tracking_file.read_text()

    # Construire entree de mise a jour
    update_section = [
        "",
        f"## Mise a jour VOX — {now}",
        "",
        f"- Statut : **{fregate.get('status', 'INCONNU')}**",
        f"- Dernier output : {fregate.get('last_output') or '—'}",
        f"- Bloquant : {fregate.get('blocking') or 'Aucun'}",
    ]

    if extra_info:
        update_section.append("")
        update_section.append("### Details")
        for k, v in extra_info.items():
            update_section.append(f"- {k} : {v}")

    update_block = "\n".join(update_section) + "\n"

    # Prepend si le fichier existe, sinon creer
    if existing:
        new_content = existing.rstrip() + "\n\n---\n" + update_block
    else:
        header = [
            f"# TRACKING_{fregate_id} — {fregate.get('name', fregate_id)}",
            "",
            "> Responsable : VOX (Scribe de l'Empire)",
            "",
            "---",
        ]
        new_content = "\n".join(header) + "\n" + update_block

    tracking_file.write_text(new_content)
    return {"updated": str(tracking_file), "fregate": fregate_id, "timestamp": now}


if __name__ == "__main__":
    import sys

    if "--master" in sys.argv:
        result = update_tracking_master()
        print(f"[FLEET_REPORTER] {result}")

    elif "--fregate" in sys.argv:
        idx = sys.argv.index("--fregate")
        fid = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if fid:
            result = update_tracking_fregate(fid)
            print(f"[FLEET_REPORTER] {result}")
        else:
            print("[FLEET_REPORTER] Usage: --fregate <fregate_id>")

    else:
        # Tout mettre a jour
        state = load_pipeline_state()
        print("[FLEET_REPORTER] Mise a jour TRACKING_MASTER.md...")
        r = update_tracking_master(state)
        print(f"  -> {r['updated']}")
        for fid in sorted(state.get("fregates", {}).keys()):
            r = update_tracking_fregate(fid, state=state)
            print(f"  -> {r['updated']}")
        print("[FLEET_REPORTER] Done.")
