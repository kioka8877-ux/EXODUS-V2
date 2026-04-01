#!/usr/bin/env python3
"""
SENTINEL B5 — L'ENQUETE (DIAGNOSTIC DIFFERENTIEL)
Croise les resultats de B2 (etat) et B3 (visuel) pour identifier la cause racine.

Principe : Deux indices, une conclusion.
    B2 dit "QUELS parametres sont hors seuil"
    B3 dit "COMMENT ca se voit visuellement"
    B5 croise les deux et dit "POURQUOI ca echoue"

Matrice de diagnostic :
    B2=PASS + B3=BLACK   → Conflit Shader/Compositing (parametres ok mais rendu noir)
    B2=FAIL + B3=BLACK   → Cause parametres (confirme : corriger B2 suffit)
    B2=FAIL + B3=VISIBLE → Regression partielle (parametres hors seuil mais visible)
    B2=PASS + B3=VISIBLE → Tout ok — succes
    B2=PASS + B3=DARK    → Sous-exposition (lumiere trop faible mais non detectee par B2)
    B2=FAIL + B3=DARK    → Energie lumiere critique

Usage :
    from brique5_diagnostic import Diagnostic
    d = Diagnostic()
    verdict = d.analyze(state_sig_path="STATE_SIG_U03.json", ghost_result={"verdict": "BLACK", ...})
    print(verdict["conclusion"])
"""
from __future__ import annotations

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

VERSION = "1.0.0"


# ─── Matrice de diagnostic ────────────────────────────────────────────────────

# (b2_verdict, b3_verdict) → (conclusion, gravite, action_recommandee)
DIAGNOSTIC_MATRIX: Dict[Tuple[str, str], Dict[str, str]] = {
    ("PASS", "VISIBLE"): {
        "conclusion": "SUCCES",
        "gravite": "NONE",
        "cause": "Tous les parametres sont dans les seuils. Rendu visible.",
        "action": "Aucune action requise. Passer a la fregate suivante.",
    },
    ("PASS", "DARK"): {
        "conclusion": "SOUS_EXPOSITION",
        "gravite": "WARN",
        "cause": "Parametres dans les seuils mais rendu sombre. Energy possiblement en limite basse.",
        "action": "Augmenter sun.energy de 20%. Verifier world.strength.",
    },
    ("PASS", "BLACK"): {
        "conclusion": "CONFLIT_SHADER_COMPOSITING",
        "gravite": "CRITICAL",
        "cause": "Parametres OK mais rendu noir. Probleme de shader, compositing ou camera mal orientee.",
        "action": "Verifier : (1) camera pointe vers la scene, (2) materials assigns, (3) compositing nodes actifs.",
    },
    ("FAIL", "VISIBLE"): {
        "conclusion": "REGRESSION_PARTIELLE",
        "gravite": "WARN",
        "cause": "Parametres hors seuil mais rendu encore visible. Degradation en cours.",
        "action": "Corriger les FAIL B2 en priorite avant que le rendu devienne noir.",
    },
    ("FAIL", "DARK"): {
        "conclusion": "ENERGIE_CRITIQUE",
        "gravite": "CRITICAL",
        "cause": "Parametres hors seuil ET rendu sombre. Energie lumiere probablement tres basse.",
        "action": "Correction urgente : sun.energy et world.strength. Voir patches B8.",
    },
    ("FAIL", "BLACK"): {
        "conclusion": "DEFAILLANCE_CONFIRMEE",
        "gravite": "CRITICAL",
        "cause": "Parametres hors seuil ET rendu noir. Cause racine confirmee dans les parametres B2.",
        "action": "Appliquer patches Vulkan (B8) en priorite. Ne pas relancer avant correction.",
    },
    ("WARN", "VISIBLE"): {
        "conclusion": "AVERTISSEMENT_MINEUR",
        "gravite": "WARN",
        "cause": "Avertissements parametres mais rendu acceptable.",
        "action": "Surveiller. Corriger avant la prochaine session.",
    },
    ("WARN", "DARK"): {
        "conclusion": "DEGRADATION_PROGRESSIVE",
        "gravite": "WARN",
        "cause": "Avertissements parametres et rendu sombre. Tendance negative.",
        "action": "Corriger les warnings B2. Priorite moderee.",
    },
    ("WARN", "BLACK"): {
        "conclusion": "CONFLIT_SHADER_POSSIBLE",
        "gravite": "CRITICAL",
        "cause": "Warnings parametres et rendu noir. Interaction inattendue entre parametres.",
        "action": "Investiguer shaders et nodes de compositing.",
    },
    ("ERROR", "VISIBLE"): {
        "conclusion": "B2_INACCESSIBLE",
        "gravite": "INFO",
        "cause": "B2 n\'a pas pu mesurer l\'etat (fichier inaccessible?). Rendu visuellement ok.",
        "action": "Relancer B2 avec le bon chemin de fichier.",
    },
    ("ERROR", "BLACK"): {
        "conclusion": "DOUBLE_ECHEC",
        "gravite": "CRITICAL",
        "cause": "B2 inaccessible ET rendu noir. Impossible de diagnostiquer precisement.",
        "action": "Verifier acces au fichier .blend. Relancer sentinel_core.run() complet.",
    },
    ("UNKNOWN", "VISIBLE"): {
        "conclusion": "ETAT_INCONNU_OK_VISUEL",
        "gravite": "INFO",
        "cause": "B2 non execute. Rendu visuellement acceptable.",
        "action": "Lancer B2 pour diagnostic complet.",
    },
    ("UNKNOWN", "BLACK"): {
        "conclusion": "ETAT_INCONNU_RENDU_NOIR",
        "gravite": "CRITICAL",
        "cause": "B2 non execute et rendu noir. Cause inconnue.",
        "action": "Lancer sentinel_core.run() complet avec --blend.",
    },
}

# Fallback pour combinaisons non definies
FALLBACK_MATRIX = {
    "conclusion": "CAS_NON_REPERTORIE",
    "gravite": "INFO",
    "cause": "Combinaison B2/B3 non encore repertoriee dans la matrice.",
    "action": "Ajouter ce cas a DIAGNOSTIC_MATRIX dans brique5_diagnostic.py.",
}


# ─── Classe principale ────────────────────────────────────────────────────────

class Diagnostic:
    """
    SENTINEL B5 — Diagnostic Differentiel.
    Croise B2 (etat) + B3 (visuel) pour identifier la cause racine.
    """

    def analyze(
        self,
        state_sig: Optional[Dict[str, Any]] = None,
        state_sig_path: Optional[str] = None,
        ghost_result: Optional[Dict[str, Any]] = None,
        ghost_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Lance le diagnostic differentiel.

        state_sig / state_sig_path : resultat B2 (dict ou chemin JSON)
        ghost_result / ghost_path  : resultat B3 (dict ou chemin JSON)

        Retourne le rapport de diagnostic.
        """
        start = time.time()

        # Charger les inputs
        b2 = self._load_input(state_sig, state_sig_path, "B2")
        b3 = self._load_input(ghost_result, ghost_path, "B3")

        b2_verdict = b2.get("verdict", "UNKNOWN") if b2 else "UNKNOWN"
        b3_verdict = b3.get("verdict", "UNKNOWN") if b3 else "UNKNOWN"

        # Extraire details des FAIL B2
        failed_checks = self._extract_failed_checks(b2)
        fregate = (b2 or {}).get("fregate", "UNKNOWN")

        # Lookup dans la matrice
        key = (b2_verdict, b3_verdict)
        matrix_entry = DIAGNOSTIC_MATRIX.get(key, FALLBACK_MATRIX)

        # Enrichir avec les checks FAIL specifiques
        enriched_action = matrix_entry["action"]
        if failed_checks and matrix_entry["gravite"] == "CRITICAL":
            fail_list = ", ".join(failed_checks[:3])
            enriched_action = f"{matrix_entry['action']} | Checks FAIL : {fail_list}"

        rapport = {
            "version": VERSION,
            "fregate": fregate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "b2_verdict": b2_verdict,
            "b3_verdict": b3_verdict,
            "conclusion": matrix_entry["conclusion"],
            "gravite": matrix_entry["gravite"],
            "cause": matrix_entry["cause"],
            "action": enriched_action,
            "failed_checks": failed_checks,
            "elapsed_sec": round(time.time() - start, 3),
        }

        return rapport

    def analyze_from_files(self, state_sig_path: str, ghost_json_path: str) -> Dict[str, Any]:
        """Shortcut : charger depuis fichiers et analyser."""
        return self.analyze(
            state_sig_path=state_sig_path,
            ghost_path=ghost_json_path,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_input(
        self,
        data: Optional[Dict],
        path: Optional[str],
        label: str,
    ) -> Optional[Dict[str, Any]]:
        if data:
            return data
        if path:
            p = Path(path)
            if p.exists():
                try:
                    with open(p, encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"[B5] Erreur lecture {label} ({path}) : {e}")
        return None

    def _extract_failed_checks(self, state_sig: Optional[Dict]) -> List[str]:
        """Retourne la liste des noms de checks FAIL depuis STATE_SIG."""
        if not state_sig:
            return []
        checks = state_sig.get("checks", {})
        return [
            f"{k}={v.get('value')} (seuil:{v.get('expected')})"
            for k, v in checks.items()
            if v.get("status") == "FAIL"
        ]

    def save(self, rapport: Dict[str, Any], output_path: str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)

    def print_report(self, rapport: Dict[str, Any]) -> None:
        gravite = rapport.get("gravite", "?")
        conclusion = rapport.get("conclusion", "?")
        fregate = rapport.get("fregate", "?")
        icon = "OK" if gravite == "NONE" else ("!!" if gravite == "CRITICAL" else "--")

        print(f"\n{'='*65}")
        print(f"  SENTINEL B5 — {fregate} — [{icon}] {conclusion}")
        print(f"{'='*65}")
        print(f"  B2 : {rapport.get('b2_verdict','?'):<10}  B3 : {rapport.get('b3_verdict','?')}")
        print(f"  Gravite    : {gravite}")
        print(f"  Cause      : {rapport.get('cause','?')}")
        print(f"  Action     : {rapport.get('action','?')}")
        if rapport.get("failed_checks"):
            print(f"  Checks FAIL:")
            for c in rapport["failed_checks"]:
                print(f"    - {c}")
        print(f"{'='*65}\n")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B5 — Diagnostic Differentiel")
    p.add_argument("--state", required=True, help="Chemin STATE_SIG.json (B2 output)")
    p.add_argument("--ghost", required=True, help="Chemin ghost_result.json (B3 output)")
    p.add_argument("--output", default=None, help="Sauvegarder rapport JSON")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    d = Diagnostic()
    rapport = d.analyze(state_sig_path=args.state, ghost_path=args.ghost)
    d.print_report(rapport)
    if args.output:
        d.save(rapport, args.output)
    return 0 if rapport.get("gravite") in ("NONE", "INFO") else 1


if __name__ == "__main__":
    sys.exit(main())
