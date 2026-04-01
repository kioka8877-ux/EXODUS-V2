#!/usr/bin/env python3
"""
SENTINEL B8 — LE MIROIR (INGENIERIE INVERSE)
Assemble dynamiquement le prompt Vulkan a partir de :
    - L'identite de la fregate
    - Le delta detecte par B2 (STATE_SIG.json)
    - L'historique injecte par B6 (memory.json)
    - Les templates par fregate

Analogie fondatrice :
    Equation  = Input de la fregate
    Reponse   = Output parfait (reference doree)
    Methode   = Le prompt que B8 construit pour que Vulkan trouve le code

Usage (depuis sentinel_core) :
    from brique8_mirror import Mirror
    mirror = Mirror(ledger_path="memory.json")
    prompt = mirror.build(fregate="U03", state_sig_path="STATE_SIG.json")
    print(prompt)
    mirror.save_prompt(prompt, "prompt_vulkan_U03.txt")

Usage (standalone) :
    python brique8_mirror.py --fregate U03 --state STATE_SIG.json --memory memory.json --output prompt_vulkan.txt
"""
from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ─── Constantes ──────────────────────────────────────────────────────────────

VERSION = "1.0.0"

# ─── Identite Vulkan — fixe pour toutes les frégates ─────────────────────────

BLOC_IDENTITE = """[IDENTITE]
Tu es Vulkan, Architecte du pipeline EXODUS.
Methode : ATOM-IC
Role    : prescrire le code MINIMAL pour combler un delta detecte.
Regles  :
  - Ne pas refactoriser ce qui fonctionne
  - Une correction = un fichier + une ligne ciblee
  - Si plusieurs corrections : ordre de priorite obligatoire
  - Format de sortie : liste de patches, pas de prose
  - Chercher la cause racine, pas le symptome"""

# ─── Contrats par fregate ─────────────────────────────────────────────────────

CONTRATS: Dict[str, Dict[str, Any]] = {
    "U00": {
        "nom": "CORTEX HQ",
        "output": "PRODUCTION_PLAN.JSON",
        "contrainte": "JSON parseable, scenes[] non vide, camera{} et lighting{} par scene",
        "fichiers_cibles": ["EXO_00_CORTEX.py"],
        "parametres": {
            "scenes.count":           {"seuil": ">= 1",    "critique": True},
            "scene.camera.present":   {"seuil": "True",    "critique": True},
            "scene.lighting.preset_id": {"seuil": "in_liste", "critique": True},
            "json.parseable":         {"seuil": "True",    "critique": True},
        },
    },
    "U01": {
        "nom": "ANIMATION ENGINE",
        "output": "ACTOR_01.blend + preview.abc",
        "contrainte": "Blender 4.0 headless, DynamicHead Roblox, 52 ARKit ShapeKeys",
        "fichiers_cibles": ["blender_fusion.py", "sync_engine.py", "setup_actor.py"],
        "parametres": {
            "armature.present":                {"seuil": "True",  "critique": True},
            "armature.action.keyframes":       {"seuil": "> 0",   "critique": True},
            "armature.bones.count":            {"seuil": ">= 20", "critique": True},
            "shapekeys.count":                 {"seuil": ">= 52", "critique": True},
            "timeline.covers_source_duration": {"seuil": "True",  "critique": True},
            "unparented_bones.main_chain":     {"seuil": "== 0",  "critique": False},
            "abc_export.present":              {"seuil": "True",  "critique": False},
        },
    },
    "U02": {
        "nom": "LOGISTICS DEPOT",
        "output": "actor_equipped.blend + actor_equipped.abc",
        "contrainte": "scale (1,1,1) obligatoire, bypass si requires_u02 == false",
        "fichiers_cibles": ["socketing_engine.py", "final_baker.py", "props_loader.py"],
        "parametres": {
            "armature.present":              {"seuil": "True",      "critique": True},
            "armature.keyframes_preserved":  {"seuil": "True",      "critique": True},
            "mesh_children.count":           {"seuil": ">= 1",      "critique": True},
            "materials.empty_slots":         {"seuil": "== 0",      "critique": False},
            "rig.scale":                     {"seuil": "(1,1,1)",   "critique": True},
            "modifiers.blocking_unapplied":  {"seuil": "== 0",      "critique": False},
            "alembic_export.present":        {"seuil": "True",      "critique": False},
        },
    },
    "U03": {
        "nom": "SCENOGRAPHY DOCK",
        "output": "environment_{scene_id}.blend",
        "contrainte": "Blender 4.0 headless, Colab T4, budget 30 min, CYCLES GPU",
        "fichiers_cibles": ["geometry_probe_u03.py", "layer_assembler.py", "EXO_03_SCENOGRAPHY.py"],
        "parametres": {
            "displacement_mesh.vertices":  {"seuil": "> 10000",  "critique": True},
            "sun.energy":                  {"seuil": "> 1.0",    "critique": True},
            "camera_main.present":         {"seuil": "True",     "critique": True},
            "camera_main.position_ok":     {"seuil": "True",     "critique": True},
            "render.engine":               {"seuil": "CYCLES",   "critique": True},
            "render.device":               {"seuil": "GPU",      "critique": True},
            "world.use_nodes":             {"seuil": "True",     "critique": False},
            "scene_type":                  {"seuil": "!= unknown","critique": True},
        },
    },
    "U04": {
        "nom": "PHOTOGRAPHY WING",
        "output": "render_XXXX.png x10 + photography_report.json",
        "contrainte": "resolution 360x640, luminance 50-200, sequences continues",
        "fichiers_cibles": ["EXO_04_PHOTOGRAPHY.py", "camera_engine.py"],
        "parametres": {
            "frames.count":              {"seuil": ">= 10",      "critique": True},
            "frame.luminance_moyenne":   {"seuil": "[50, 200]",  "critique": True},
            "frame.resolution":          {"seuil": "360x640",    "critique": True},
            "frame.taille_min_kb":       {"seuil": "> 50",       "critique": False},
            "sequence.gaps":             {"seuil": "== 0",       "critique": True},
            "camera_main.keyframes":     {"seuil": "> 0",        "critique": False},
            "lighting.EXODUS_count":     {"seuil": ">= 2",       "critique": False},
            "render.samples":            {"seuil": ">= 16",      "critique": False},
        },
    },
    "U05": {
        "nom": "ALCHEMIST LAB",
        "output": "final_{scene}_{frame}.png + alchemist_report.json",
        "contrainte": "CPU pur, OpenCV headless, PNG 16-bit, pipeline 4 etapes",
        "fichiers_cibles": ["match_color.py", "alchemist_schema.py", "EXO_05_ALCHEMIST.py"],
        "parametres": {
            "frames_processed":              {"seuil": "== frames_input", "critique": True},
            "luminance.delta_vs_reference":  {"seuil": "< 20%",           "critique": True},
            "rgb.canal_sature_moyen":        {"seuil": "< 250",           "critique": True},
            "grain.present":                 {"seuil": "True si !clean",  "critique": False},
            "banding.detected":              {"seuil": "False",            "critique": False},
            "output_filesize_ratio":         {"seuil": ">= 1.0",          "critique": False},
            "alchemist_report.status":       {"seuil": "SUCCESS",          "critique": True},
        },
    },
    "U06": {
        "nom": "AIRCRAFT CARRIER",
        "output": "final_movie.mp4",
        "contrainte": "AV1/H265, zero compression lossy intermediaire, frames PNG tout le pipeline",
        "fichiers_cibles": ["sequence_assembler.py", "audio_sync.py", "final_encoder.py"],
        "parametres": {
            "output.present":            {"seuil": "True",       "critique": True},
            "output.size_mb":            {"seuil": "> 5",        "critique": True},
            "duration.delta_vs_source":  {"seuil": "< 0.5 sec",  "critique": True},
            "resolution.minimum":        {"seuil": "360x640",    "critique": True},
            "framerate":                 {"seuil": "24 ou 30",   "critique": True},
            "audio.present_synced":      {"seuil": "True",       "critique": True},
            "black_frames.start_end":    {"seuil": "< 0.5 sec",  "critique": False},
            "codec.readable":            {"seuil": "H264/H265",  "critique": False},
        },
    },
}

# ─── Bloc QUESTION — fixe ─────────────────────────────────────────────────────

BLOC_QUESTION = """[QUESTION]
Liste de patches pour fermer TOUS les gaps marques FAIL ci-dessus.
Format obligatoire pour chaque patch :
  fichier  : {nom_du_fichier}
  ligne    : {numero_de_ligne}
  avant    : {code_actuel}
  apres    : {code_corrige}
  raison   : {explication_en_une_ligne}

Regles :
  - Ordre : patches critiques en premier
  - Ne pas modifier ce qui n\'a pas de gap
  - Si le gap necessite un nouveau bloc de code : indiquer la ligne d\'insertion
  - Maximum 5 patches par reponse"""


# ─── Classe principale ────────────────────────────────────────────────────────

class Mirror:
    """
    SENTINEL B8 — Le Miroir.
    Assemble le prompt Vulkan a partir du delta B2 et de l\'historique B6.
    """

    def __init__(self, ledger_path: str = "memory.json"):
        self.ledger_path = Path(ledger_path)
        self._ledger_data = self._load_ledger()

    # ── Chargement ────────────────────────────────────────────────────────────

    def _load_ledger(self) -> Dict[str, Any]:
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"entries": []}

    def _load_state_sig(self, state_sig_path: str) -> Optional[Dict[str, Any]]:
        p = Path(state_sig_path)
        if not p.exists():
            return None
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ── Construction du prompt ────────────────────────────────────────────────

    def build(
        self,
        fregate: str,
        state_sig_path: Optional[str] = None,
        manual_delta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Assemble le prompt Vulkan complet.

        fregate       : ID de la fregate (U00-U06)
        state_sig_path: Chemin vers STATE_SIG.json produit par B2 (optionnel)
        manual_delta  : Delta saisi manuellement si B2 non disponible (optionnel)

        Retourne le prompt complet sous forme de string.
        """
        if fregate not in CONTRATS:
            raise ValueError(f"Fregate inconnue : {fregate}. Options : {list(CONTRATS)}")

        contrat = CONTRATS[fregate]
        state_sig = None

        if state_sig_path:
            state_sig = self._load_state_sig(state_sig_path)

        # Assembler les 4 blocs
        bloc_contrat = self._build_contrat(fregate, contrat)
        bloc_delta = self._build_delta(fregate, contrat, state_sig, manual_delta)
        bloc_historique = self._build_historique(fregate)
        bloc_question = BLOC_QUESTION

        prompt = "\n\n".join([
            BLOC_IDENTITE,
            bloc_contrat,
            bloc_delta,
            bloc_historique,
            bloc_question,
        ])

        return prompt

    def _build_contrat(self, fregate: str, contrat: Dict[str, Any]) -> str:
        fichiers = ", ".join(contrat["fichiers_cibles"])
        return (
            f"[CONTRAT {fregate}]\n"
            f"Fregate    : {fregate} — {contrat['nom']}\n"
            f"Output     : {contrat['output']}\n"
            f"Contrainte : {contrat['contrainte']}\n"
            f"Fichiers   : {fichiers}"
        )

    def _build_delta(
        self,
        fregate: str,
        contrat: Dict[str, Any],
        state_sig: Optional[Dict[str, Any]],
        manual_delta: Optional[Dict[str, Any]],
    ) -> str:
        """Construit le tableau de delta Niveau 3."""
        lines = ["[DELTA DETECTE — Niveau 3]"]
        lines.append(f"{'Parametre':<40} {'Actuel':<20} {'Seuil':<20} {'Statut'}")
        lines.append("-" * 95)

        parametres = contrat["parametres"]
        checks = {}

        # Recuperer les checks depuis STATE_SIG si disponible
        if state_sig and "checks" in state_sig:
            checks = state_sig["checks"]

        for param_name, param_info in parametres.items():
            seuil = param_info["seuil"]
            critique = "[CRITIQUE]" if param_info["critique"] else "[INFO]"

            # Chercher la valeur actuelle dans state_sig ou manual_delta
            actuel = "?"
            statut = "NON_MESURE"

            # Mapping nom parametre → cle dans STATE_SIG.checks
            check_key = param_name.replace(".", "_").replace(" ", "_")
            if check_key in checks:
                c = checks[check_key]
                actuel = str(c.get("value", "?"))
                statut = c.get("status", "?")
            elif manual_delta and param_name in manual_delta:
                actuel = str(manual_delta[param_name])
                statut = "MANUEL"

            # Formater la ligne
            statut_icon = "FAIL !!" if statut == "FAIL" else ("PASS" if statut == "PASS" else statut)
            lines.append(f"{param_name:<40} {actuel:<20} {seuil:<20} {statut_icon} {critique}")

        # Compter les FAIL
        fail_count = sum(1 for c in checks.values() if c.get("status") == "FAIL")
        if fail_count > 0:
            lines.append(f"\n=> {fail_count} gap(s) FAIL detecte(s) — prescription requise")
        elif checks:
            lines.append("\n=> Aucun gap FAIL — verification preventive")
        else:
            lines.append("\n=> Delta non mesure — fournir valeurs manuellement ou lancer B2")

        return "\n".join(lines)

    def _build_historique(self, fregate: str) -> str:
        """Injecte les corrections connues depuis le Ledger B6."""
        entries = self._get_ledger_injections(fregate)

        if not entries:
            return "[HISTORIQUE LEDGER]\nAucune erreur connue pour cette fregate.\n"

        lines = ["[HISTORIQUE LEDGER]"]
        for i, e in enumerate(entries, 1):
            occ = e.get("occurrences", 1)
            lines.append(f"Erreur {i} (vue {occ}x) :")
            lines.append(f"  Erreur     : {e.get('erreur', '?')}")
            lines.append(f"  Cause      : {e.get('cause', '?')}")
            lines.append(f"  Correction : {e.get('correction', '?')}")
            lines.append(f"  Auto-inject: {e.get('auto_inject', False)}")
            lines.append("")
        return "\n".join(lines)

    def _get_ledger_injections(self, fregate: str, max_entries: int = 3) -> List[Dict[str, Any]]:
        entries = [
            e for e in self._ledger_data.get("entries", [])
            if e.get("fregate") == fregate
            and e.get("auto_inject", False)
            and not e.get("resolu", False)
        ]
        entries.sort(key=lambda e: (-e.get("occurrences", 0), e.get("derniere_vue", "")))
        return entries[:max_entries]

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save_prompt(self, prompt: str, output_path: str) -> None:
        """Sauvegarde le prompt Vulkan dans un fichier texte."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(prompt)

    def save_manifest(self, fregate: str, state_sig_path: Optional[str], output_path: str) -> None:
        """Sauvegarde un manifest JSON avec metadata de l\'assemblage."""
        manifest = {
            "version": VERSION,
            "fregate": fregate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_sig_used": state_sig_path is not None,
            "ledger_injections": len(self._get_ledger_injections(fregate)),
            "fichiers_cibles": CONTRATS[fregate]["fichiers_cibles"],
        }
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B8 — Le Miroir")
    p.add_argument("--fregate", required=True, choices=list(CONTRATS), help="ID fregate")
    p.add_argument("--state", default=None, help="Chemin vers STATE_SIG.json (B2 output)")
    p.add_argument("--memory", default="memory.json", help="Chemin vers memory.json (B6)")
    p.add_argument("--output", default="prompt_vulkan.txt", help="Fichier prompt de sortie")
    p.add_argument("--manifest", default=None, help="Fichier manifest JSON (optionnel)")
    p.add_argument("--print", action="store_true", dest="do_print", help="Afficher le prompt")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    mirror = Mirror(ledger_path=args.memory)
    prompt = mirror.build(fregate=args.fregate, state_sig_path=args.state)
    mirror.save_prompt(prompt, args.output)

    if args.manifest:
        mirror.save_manifest(args.fregate, args.state, args.manifest)

    if args.do_print:
        print(prompt)
    else:
        print(f"[B8] Prompt Vulkan sauvegarde : {args.output}")
        print(f"[B8] Fregate : {args.fregate} | Ledger injections : {len(mirror._get_ledger_injections(args.fregate))}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
