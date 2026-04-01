#!/usr/bin/env python3
"""
SENTINEL B6 — LEDGER PERSISTANT (LA MEMOIRE)
Memoire persistante de toutes les erreurs, causes, et corrections du pipeline EXODUS.

Principe fondamental :
    - Zero erreur repetee deux fois sur une meme fregate.
    - Si une correction a fonctionne une fois, elle est injectee automatiquement la prochaine fois.
    - La memoire survit aux sessions Colab grace au stockage Drive.

Usage (standalone) :
    python brique6_ledger.py --action add --fregate U03 --erreur "camera absente" --cause "layer_assembler pas appele" --correction "appeler layer_assembler.py avant geometry_probe"
    python brique6_ledger.py --action get --fregate U03
    python brique6_ledger.py --action list

Usage (depuis sentinel_core) :
    from brique6_ledger import Ledger
    ledger = Ledger("/content/drive/MyDrive/EXODUS_V2/SENTINEL_CORE/memory.json")
    ledger.add(fregate="U03", erreur="camera absente", cause="...", correction="...")
    injections = ledger.get_injections("U03")
"""
from __future__ import annotations

import json
import os
import sys
import uuid
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ─── Constantes ──────────────────────────────────────────────────────────────

VERSION = "1.0.0"
DEFAULT_MEMORY_PATH = "memory.json"
MAX_INJECT_PER_FREGATE = 3       # Nombre max d'entrees injectees dans le prompt Vulkan
AUTO_INJECT_THRESHOLD = 1        # Injecter auto si occurrences >= ce seuil


# ─── Classe principale ────────────────────────────────────────────────────────

class Ledger:
    """
    Ledger SENTINEL B6 — Memoire persistante.

    Structure memory.json :
    {
      "version": "1.0.0",
      "last_updated": "ISO8601",
      "entries": [
        {
          "id": "uuid",
          "fregate": "U03",
          "timestamp": "ISO8601",
          "erreur": "description courte",
          "cause": "parametres incrimines",
          "correction": "patch applique",
          "auto_inject": true,
          "occurrences": 2,
          "derniere_vue": "ISO8601",
          "resolu": false
        }
      ]
    }
    """

    def __init__(self, memory_path: str = DEFAULT_MEMORY_PATH):
        self.memory_path = Path(memory_path)
        self._data: Dict[str, Any] = self._load()

    # ── Chargement / Sauvegarde ───────────────────────────────────────────────

    def _load(self) -> Dict[str, Any]:
        """Charge memory.json depuis le disque ou cree un nouveau."""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, encoding="utf-8") as f:
                    data = json.load(f)
                # Migration si format ancien
                if "entries" not in data:
                    data["entries"] = []
                return data
            except (json.JSONDecodeError, KeyError):
                print(f"[LEDGER] Fichier corrompu, reinitialisation : {self.memory_path}")
        return {
            "version": VERSION,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "entries": [],
        }

    def _save(self) -> None:
        """Sauvegarde memory.json sur le disque."""
        self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ── CRUD entrees ──────────────────────────────────────────────────────────

    def add(
        self,
        fregate: str,
        erreur: str,
        cause: str,
        correction: str,
        auto_inject: bool = True,
        resolu: bool = False,
    ) -> str:
        """
        Ajoute ou met a jour une entree dans le Ledger.
        Si la meme (fregate + erreur) existe deja : increment occurrences.
        Retourne l'ID de l'entree.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Deduplication — chercher entree existante
        existing = self._find_entry(fregate, erreur)
        if existing:
            existing["occurrences"] += 1
            existing["derniere_vue"] = now
            existing["cause"] = cause
            existing["correction"] = correction
            existing["resolu"] = resolu
            if existing["occurrences"] >= AUTO_INJECT_THRESHOLD:
                existing["auto_inject"] = True
            self._save()
            return existing["id"]

        # Nouvelle entree
        entry_id = str(uuid.uuid4())[:8]
        entry = {
            "id": entry_id,
            "fregate": fregate,
            "timestamp": now,
            "erreur": erreur,
            "cause": cause,
            "correction": correction,
            "auto_inject": auto_inject,
            "occurrences": 1,
            "derniere_vue": now,
            "resolu": resolu,
        }
        self._data["entries"].append(entry)
        self._save()
        return entry_id

    def get_injections(self, fregate: str) -> List[Dict[str, Any]]:
        """
        Retourne les N dernieres entrees auto_inject=True pour une fregate.
        Ce sont les entrees a injecter dans le prompt Vulkan via B8.
        """
        entries = [
            e for e in self._data["entries"]
            if e["fregate"] == fregate
            and e.get("auto_inject", False)
            and not e.get("resolu", False)
        ]
        # Tri par occurrences desc, puis par date desc
        entries.sort(key=lambda e: (-e.get("occurrences", 0), e.get("derniere_vue", "")))
        return entries[:MAX_INJECT_PER_FREGATE]

    def get_all(self, fregate: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retourne toutes les entrees, optionnellement filtrees par fregate."""
        entries = self._data["entries"]
        if fregate:
            entries = [e for e in entries if e["fregate"] == fregate]
        return sorted(entries, key=lambda e: e.get("derniere_vue", ""), reverse=True)

    def mark_resolved(self, entry_id: str) -> bool:
        """Marque une entree comme resolue (ne sera plus injectee)."""
        for entry in self._data["entries"]:
            if entry["id"] == entry_id:
                entry["resolu"] = True
                entry["auto_inject"] = False
                self._save()
                return True
        return False

    def stats(self) -> Dict[str, Any]:
        """Statistiques globales du Ledger."""
        entries = self._data["entries"]
        by_fregate: Dict[str, int] = {}
        for e in entries:
            f = e.get("fregate", "?")
            by_fregate[f] = by_fregate.get(f, 0) + 1

        return {
            "total_entries": len(entries),
            "total_occurrences": sum(e.get("occurrences", 1) for e in entries),
            "auto_inject_active": sum(1 for e in entries if e.get("auto_inject") and not e.get("resolu")),
            "resolved": sum(1 for e in entries if e.get("resolu")),
            "by_fregate": by_fregate,
            "last_updated": self._data.get("last_updated"),
        }

    # ── Formatage prompt Vulkan ───────────────────────────────────────────────

    def format_for_prompt(self, fregate: str) -> str:
        """
        Formate les injections pour insertion dans le prompt Vulkan (B8).
        Retourne un bloc texte pret a l'emploi.
        """
        injections = self.get_injections(fregate)
        if not injections:
            return "[HISTORIQUE LEDGER]
Aucune erreur connue pour cette fregate.
"

        lines = ["[HISTORIQUE LEDGER]"]
        for i, e in enumerate(injections, 1):
            lines.append(f"Erreur {i} (vue {e['occurrences']}x) :")
            lines.append(f"  Erreur     : {e['erreur']}")
            lines.append(f"  Cause      : {e['cause']}")
            lines.append(f"  Correction : {e['correction']}")
            lines.append(f"  Auto-inject: {e['auto_inject']}")
            lines.append("")
        return "\n".join(lines)

    # ── Helpers internes ──────────────────────────────────────────────────────

    def _find_entry(self, fregate: str, erreur: str) -> Optional[Dict[str, Any]]:
        """Cherche une entree existante par (fregate, erreur) — matching partiel."""
        erreur_lower = erreur.lower().strip()
        for entry in self._data["entries"]:
            if entry["fregate"] == fregate:
                existing_lower = entry["erreur"].lower().strip()
                # Match exact ou inclusion
                if erreur_lower == existing_lower or erreur_lower in existing_lower:
                    return entry
        return None

    # ── Affichage console ─────────────────────────────────────────────────────

    def print_table(self, fregate: Optional[str] = None) -> None:
        """Affiche le Ledger sous forme de tableau lisible."""
        entries = self.get_all(fregate)
        title = f"SENTINEL B6 — LEDGER{f' ({fregate})' if fregate else ''}"
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
        if not entries:
            print("  (aucune entree)")
        for e in entries:
            status = "RESOLU" if e.get("resolu") else ("AUTO" if e.get("auto_inject") else "MANUEL")
            print(f"  [{e['id']}] {e['fregate']} | {status} | x{e['occurrences']} | {e['erreur'][:50]}")
        s = self.stats()
        print(f"{'='*70}")
        print(f"  Total: {s['total_entries']} entrees | {s['auto_inject_active']} actives | {s['resolved']} resolues")
        print(f"{'='*70}\n")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B6 — Ledger Persistant")
    p.add_argument("--memory", default=DEFAULT_MEMORY_PATH, help="Chemin vers memory.json")
    sub = p.add_subparsers(dest="action", required=True)

    # add
    add = sub.add_parser("add", help="Ajouter une entree")
    add.add_argument("--fregate", required=True)
    add.add_argument("--erreur", required=True)
    add.add_argument("--cause", required=True)
    add.add_argument("--correction", required=True)
    add.add_argument("--no-auto-inject", action="store_true")

    # get
    get = sub.add_parser("get", help="Voir les injections pour une fregate")
    get.add_argument("--fregate", required=True)

    # list
    lst = sub.add_parser("list", help="Lister toutes les entrees")
    lst.add_argument("--fregate", default=None)

    # resolve
    res = sub.add_parser("resolve", help="Marquer une entree comme resolue")
    res.add_argument("--id", required=True)

    # stats
    sub.add_parser("stats", help="Statistiques du Ledger")

    return p.parse_args()


def main() -> int:
    args = _parse_args()
    ledger = Ledger(args.memory)

    if args.action == "add":
        entry_id = ledger.add(
            fregate=args.fregate,
            erreur=args.erreur,
            cause=args.cause,
            correction=args.correction,
            auto_inject=not args.no_auto_inject,
        )
        print(f"[LEDGER] Entree ajoutee/mise a jour : {entry_id}")

    elif args.action == "get":
        print(ledger.format_for_prompt(args.fregate))

    elif args.action == "list":
        ledger.print_table(getattr(args, "fregate", None))

    elif args.action == "resolve":
        ok = ledger.mark_resolved(args.id)
        print(f"[LEDGER] Entree {args.id} : {'resolue' if ok else 'non trouvee'}")

    elif args.action == "stats":
        s = ledger.stats()
        print(json.dumps(s, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
