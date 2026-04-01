#!/usr/bin/env python3
"""
SENTINEL_CORE — ORCHESTRATEUR PRINCIPAL
Coordonne B2 → B6 → B8 en un seul appel.

Doctrine :
    SENTINEL = preparateur de contexte
    Vulkan   = prescripteur
    Empereur = validateur

Flux complet :
    1. B2 mesure l'etat reel de la fregate (STATE_SIG.json)
    2. B6 enregistre l'erreur si FAIL + injecte les corrections connues
    3. B8 assemble le prompt Vulkan avec delta + historique
    4. sentinel_core sauvegarde tout et retourne le rapport

Usage (depuis Colab) :
    from SENTINEL_CORE.CODEBASE.sentinel_core import Sentinel
    s = Sentinel(base_dir="/content/drive/MyDrive/EXODUS_V2/SENTINEL_CORE")
    rapport = s.run(fregate="U03", blend_path="/content/.../environment_1.blend")
    print(rapport["prompt_vulkan"])

Usage (standalone) :
    python sentinel_core.py --fregate U03 --blend /path/to/file.blend
    python sentinel_core.py --fregate U04 --frames /path/to/OUT_CAMERA_LOGIC/
"""
from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Import des briques
try:
    from brique2_state import StateSignature
    from brique3_ghost import GhostRenderer
    from brique5_diagnostic import Diagnostic
    from brique6_ledger import Ledger
    from brique8_mirror import Mirror
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from brique2_state import StateSignature
    from brique3_ghost import GhostRenderer
    from brique5_diagnostic import Diagnostic
    from brique6_ledger import Ledger
    from brique8_mirror import Mirror

# ─── Constantes ──────────────────────────────────────────────────────────────

VERSION = "1.0.0"
RAPPORT_FILENAME = "SENTINEL_RAPPORT_{fregate}_{ts}.json"
STATE_SIG_FILENAME = "STATE_SIG_{fregate}.json"
PROMPT_FILENAME = "prompt_vulkan_{fregate}.txt"


# ─── Classe principale ────────────────────────────────────────────────────────

class Sentinel:
    """
    Orchestrateur SENTINEL — connecte B2, B6, B8.

    base_dir : dossier SENTINEL_CORE sur Drive
                ex: /content/drive/MyDrive/EXODUS_V2/SENTINEL_CORE
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.codebase_dir = self.base_dir / "CODEBASE"
        self.memory_path = self.base_dir / "memory.json"
        self.state_sig_dir = self.base_dir
        self.prompt_dir = self.base_dir

    # ── Execution principale ──────────────────────────────────────────────────

    def run(
        self,
        fregate: str,
        blend_path: Optional[str] = None,
        frames_dir: Optional[str] = None,
        auto_record: bool = True,
    ) -> Dict[str, Any]:
        """
        Lance le pipeline SENTINEL complet pour une fregate.

        fregate     : ID fregate (U00-U06)
        blend_path  : chemin .blend a auditer (U01/U02/U03/U04)
        frames_dir  : chemin dossier frames a auditer (U04/U05)
        auto_record : enregistrer automatiquement dans Ledger si FAIL

        Retourne un rapport complet :
        {
            "fregate", "verdict", "state_sig", "ledger_injections",
            "prompt_vulkan", "fichiers_sauvegardes", "timestamp"
        }
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rapport: Dict[str, Any] = {
            "version": VERSION,
            "fregate": fregate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": "PENDING",
            "state_sig": None,
            "ghost_result": None,
            "diagnostic": None,
            "ledger_injections": 0,
            "prompt_vulkan": None,
            "fichiers_sauvegardes": [],
            "erreurs_sentinel": [],
        }

        # ── ETAPE 1 : B2 — Signature d'Etat ──────────────────────────────────
        print(f"\n[SENTINEL] {fregate} — Etape 1/3 : B2 Signature d\'Etat")
        state_sig = None
        state_sig_path = self.state_sig_dir / STATE_SIG_FILENAME.format(fregate=fregate)

        try:
            b2 = StateSignature(fregate)
            if blend_path:
                state_sig = b2.check_blend(blend_path)
            elif frames_dir:
                state_sig = b2.check_frames(frames_dir)
            else:
                print(f"  [B2] WARN : ni --blend ni --frames fourni — delta non mesure")
                state_sig = {
                    "fregate": fregate,
                    "verdict": "UNKNOWN",
                    "checks": {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            b2.save(state_sig, str(state_sig_path))
            b2.print_report(state_sig)
            rapport["state_sig"] = state_sig
            rapport["verdict"] = state_sig.get("verdict", "UNKNOWN")
            rapport["fichiers_sauvegardes"].append(str(state_sig_path))
            print(f"  [B2] STATE_SIG sauvegarde : {state_sig_path.name}")

        except Exception as e:
            msg = f"B2 erreur : {e}"
            rapport["erreurs_sentinel"].append(msg)
            print(f"  [B2] ERREUR : {e}")

        # ── ETAPE 2 : B3 — Ghost Renderer ────────────────────────────────────
        print(f"[SENTINEL] {fregate} — Etape 2/5 : B3 Ghost Renderer")
        ghost_result = None
        ghost_path = self.state_sig_dir / f"GHOST_{fregate}.json"

        try:
            b3 = GhostRenderer()
            if frames_dir:
                ghost_result = b3.analyze_folder(frames_dir)
            elif blend_path:
                ghost_out = self.state_sig_dir / f"ghost_{fregate}.png"
                ghost_result = b3.render(blend_path, str(ghost_out))
                if ghost_out.exists():
                    rapport["fichiers_sauvegardes"].append(str(ghost_out))

            if ghost_result:
                b3.print_report(ghost_result)
                ghost_data = {k: v for k, v in ghost_result.items()}
                ghost_path.write_text(
                    __import__("json").dumps(ghost_data, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8"
                )
                rapport["ghost_result"] = ghost_result
                rapport["fichiers_sauvegardes"].append(str(ghost_path))
                print(f"  [B3] Ghost verdict : {ghost_result.get('verdict','?')} | luma={ghost_result.get('luminance_mean','?')}")

        except Exception as e:
            msg = f"B3 erreur : {e}"
            rapport["erreurs_sentinel"].append(msg)
            print(f"  [B3] ERREUR (non bloquant) : {e}")

        # ── ETAPE 3 : B5 — Diagnostic Differentiel ───────────────────────────
        print(f"[SENTINEL] {fregate} — Etape 3/5 : B5 Diagnostic Differentiel")
        diag_path = self.state_sig_dir / f"DIAGNOSTIC_{fregate}.json"

        try:
            b5 = Diagnostic()
            diagnostic = b5.analyze(
                state_sig=state_sig,
                ghost_result=ghost_result,
            )
            b5.print_report(diagnostic)
            b5.save(diagnostic, str(diag_path))
            rapport["diagnostic"] = diagnostic
            rapport["fichiers_sauvegardes"].append(str(diag_path))

            # Mettre a jour le verdict global avec la gravite B5
            gravite = diagnostic.get("gravite", "NONE")
            if gravite == "CRITICAL" and rapport["verdict"] not in ("FAIL",):
                rapport["verdict"] = "FAIL"
            print(f"  [B5] Conclusion : {diagnostic.get('conclusion','?')} | Gravite : {gravite}")

        except Exception as e:
            msg = f"B5 erreur : {e}"
            rapport["erreurs_sentinel"].append(msg)
            print(f"  [B5] ERREUR (non bloquant) : {e}")

        # ── ETAPE 4 : B6 — Ledger ────────────────────────────────────────────
        print(f"[SENTINEL] {fregate} — Etape 4/5 : B6 Ledger")
        ledger = Ledger(str(self.memory_path))

        if auto_record and state_sig and state_sig.get("verdict") == "FAIL":
            # Identifier les checks FAIL et les enregistrer
            failed_checks = {
                k: v for k, v in state_sig.get("checks", {}).items()
                if v.get("status") == "FAIL"
            }
            for check_name, check_data in failed_checks.items():
                erreur = f"{check_name} = {check_data.get('value')} (seuil: {check_data.get('expected')})"
                cause = f"Parametre {check_name} hors seuil dans {fregate}"
                correction = f"Corriger {check_name} pour atteindre {check_data.get('expected')}"
                ledger.add(
                    fregate=fregate,
                    erreur=erreur,
                    cause=cause,
                    correction=correction,
                    auto_inject=True,
                )
            print(f"  [B6] {len(failed_checks)} erreur(s) enregistree(s) dans Ledger")

        injections = ledger.get_injections(fregate)
        rapport["ledger_injections"] = len(injections)
        print(f"  [B6] {len(injections)} injection(s) disponible(s) pour ce prompt")

        # ── ETAPE 3 : B8 — Le Miroir ─────────────────────────────────────────
        print(f"[SENTINEL] {fregate} — Etape 5/5 : B8 Assemblage Prompt Vulkan")
        prompt_path = self.prompt_dir / PROMPT_FILENAME.format(fregate=fregate)

        try:
            mirror = Mirror(ledger_path=str(self.memory_path))
            prompt = mirror.build(
                fregate=fregate,
                state_sig_path=str(state_sig_path) if state_sig_path.exists() else None,
            )
            mirror.save_prompt(prompt, str(prompt_path))
            rapport["prompt_vulkan"] = prompt
            rapport["fichiers_sauvegardes"].append(str(prompt_path))
            print(f"  [B8] Prompt Vulkan sauvegarde : {prompt_path.name}")

        except Exception as e:
            msg = f"B8 erreur : {e}"
            rapport["erreurs_sentinel"].append(msg)
            print(f"  [B8] ERREUR : {e}")

        # ── Sauvegarde rapport complet ────────────────────────────────────────
        rapport_path = self.base_dir / RAPPORT_FILENAME.format(fregate=fregate, ts=ts)
        rapport_save = {k: v for k, v in rapport.items() if k not in ("prompt_vulkan", "state_sig", "ghost_result", "diagnostic")}
        rapport_save["prompt_path"] = str(prompt_path)
        rapport_save["diagnostic_conclusion"] = (rapport.get("diagnostic") or {}).get("conclusion", "N/A")
        rapport_save["ghost_verdict"] = (rapport.get("ghost_result") or {}).get("verdict", "N/A")
        try:
            rapport_path.parent.mkdir(parents=True, exist_ok=True)
            with open(rapport_path, "w", encoding="utf-8") as f:
                json.dump(rapport_save, f, indent=2, ensure_ascii=False, default=str)
            rapport["fichiers_sauvegardes"].append(str(rapport_path))
        except Exception as e:
            rapport["erreurs_sentinel"].append(f"Sauvegarde rapport : {e}")

        # ── Affichage final ───────────────────────────────────────────────────
        self._print_summary(rapport)
        return rapport

    # ── Methode de validation pre-execution (hook Marshal) ───────────────────

    def pre_check(self, fregate: str, blend_path: Optional[str] = None) -> bool:
        """
        Hook pre-execution pour EXO_MARSHAL.py.
        Retourne True si OK de continuer, False si FAIL critique.
        Appel leger — ne sauvegarde pas de rapport.
        """
        try:
            b2 = StateSignature(fregate)
            if blend_path:
                result = b2.check_blend(blend_path)
            else:
                return True  # Sans fichier, on laisse passer

            b2.print_report(result)
            verdict = result.get("verdict", "UNKNOWN")

            if verdict == "FAIL":
                print(f"[SENTINEL PRE-CHECK] {fregate} — FAIL detecte. Corriger avant execution.")
                return False
            return True

        except Exception as e:
            print(f"[SENTINEL PRE-CHECK] Erreur : {e} — execution autorisee par defaut")
            return True

    # ── Methode post-execution (hook Marshal) ────────────────────────────────

    def post_record(self, fregate: str, success: bool, details: str = "") -> None:
        """
        Hook post-execution pour EXO_MARSHAL.py.
        Enregistre le resultat dans le Ledger.
        """
        if not success:
            ledger = Ledger(str(self.memory_path))
            ledger.add(
                fregate=fregate,
                erreur=f"Execution echouee : {details[:80]}",
                cause="Voir logs Colab pour details",
                correction="Lancer sentinel_core.run() pour diagnostic complet",
                auto_inject=False,
            )
            print(f"[SENTINEL POST] {fregate} — echec enregistre dans Ledger")
        else:
            print(f"[SENTINEL POST] {fregate} — succes enregistre")

    # ── Affichage ────────────────────────────────────────────────────────────

    def _print_summary(self, rapport: Dict[str, Any]) -> None:
        fregate = rapport["fregate"]
        verdict = rapport["verdict"]
        n_inject = rapport["ledger_injections"]
        n_fichiers = len(rapport["fichiers_sauvegardes"])
        n_erreurs = len(rapport["erreurs_sentinel"])

        icon = "PASS" if verdict == "PASS" else ("WARN" if verdict == "WARN" else "FAIL")
        print(f"\n{'='*60}")
        print(f"  SENTINEL RAPPORT — {fregate} — [{icon}]")
        print(f"{'='*60}")
        print(f"  Verdict          : {verdict}")
        print(f"  Ledger injections: {n_inject}")
        print(f"  Fichiers crees   : {n_fichiers}")
        print(f"  Erreurs SENTINEL : {n_erreurs}")
        if rapport["erreurs_sentinel"]:
            for e in rapport["erreurs_sentinel"]:
                print(f"    - {e}")
        print(f"{'='*60}")
        if verdict == "FAIL" and rapport.get("prompt_vulkan"):
            print("\n  PROMPT VULKAN PRET — copier dans Claude pour prescription.\n")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL — Orchestrateur B2+B6+B8")
    p.add_argument("--fregate", required=True, help="ID fregate (U00-U06)")
    p.add_argument("--blend", default=None, help="Chemin fichier .blend")
    p.add_argument("--frames", default=None, help="Chemin dossier frames")
    p.add_argument("--base-dir", default=".", help="Dossier SENTINEL_CORE (base)")
    p.add_argument("--no-auto-record", action="store_true", help="Ne pas enregistrer auto dans Ledger")
    p.add_argument("--print-prompt", action="store_true", help="Afficher le prompt Vulkan en sortie")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    sentinel = Sentinel(base_dir=args.base_dir)
    rapport = sentinel.run(
        fregate=args.fregate,
        blend_path=args.blend,
        frames_dir=args.frames,
        auto_record=not args.no_auto_record,
    )
    if args.print_prompt and rapport.get("prompt_vulkan"):
        print("\n" + "="*60)
        print("PROMPT VULKAN :")
        print("="*60)
        print(rapport["prompt_vulkan"])

    return 0 if rapport["verdict"] in ("PASS", "WARN", "UNKNOWN") else 1


if __name__ == "__main__":
    sys.exit(main())
