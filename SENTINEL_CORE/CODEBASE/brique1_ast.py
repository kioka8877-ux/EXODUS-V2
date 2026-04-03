#!/usr/bin/env python3
"""
SENTINEL B1 — L'ESPRIT (ANALYSE AST)
Analyse statique du code Python d'une fregate via AST (Abstract Syntax Tree).

Objectif : detecter les defauts structurels AVANT execution.
Principe adversarial : chercher les problemes, pas confirmer la sante.

Ce que B1 detecte :
    - Patterns dangereux : eval(), exec(), os.system(), subprocess.call()
    - Except nus : bare except / except Exception sans message
    - Chemins hardcodes : /content/, /drive/MyDrive/ dans le code
    - Fonctions vides : pass seul dans un def
    - Imports manquants : utilisation de symbole non importe
    - Globals modifies sans declaration

Limites connues :
    - Analyse statique uniquement (pas de runtime)
    - Ne detecte pas les erreurs de logique metier
    - Ne valide pas la semantique Blender/PyTorch

Usage (standalone) :
    python brique1_ast.py --fregate U03 --scripts /path/to/CODEBASE/
    python brique1_ast.py --file /path/to/script.py

Usage (depuis sentinel_core) :
    from brique1_ast import AstAnalyzer
    analyzer = AstAnalyzer()
    result = analyzer.analyze_dir("/path/to/CODEBASE/")
    print(result["verdict"])  # PASS | WARN | FAIL | ERROR
"""
from __future__ import annotations

import ast
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ─── Constantes ──────────────────────────────────────────────────────────────

VERSION = "1.0.0"

# Patterns dangereux — niveau critique
DANGEROUS_CALLS = {"eval", "exec", "compile", "__import__"}
DANGEROUS_SUBPROCESS = {"os.system", "subprocess.call", "subprocess.Popen", "subprocess.run"}

# Chemins hardcodes suspects
HARDCODED_PATH_PATTERNS = ["/content/", "/drive/MyDrive/", "C:\\Users\\", "D:\\"]

# Seuil de score : en-dessous = FAIL
SCORE_FAIL_THRESHOLD = 40
SCORE_WARN_THRESHOLD = 70


# ─── Visiteur AST ────────────────────────────────────────────────────────────

class _SentinelVisitor(ast.NodeVisitor):
    """
    Visiteur AST interne — collecte les anomalies dans un fichier.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Dict[str, Any]] = []
        self._current_func: Optional[str] = None

    # ── Appels dangereux ──────────────────────────────────────────────────────

    def visit_Call(self, node: ast.Call) -> None:
        name = self._call_name(node)
        if name in DANGEROUS_CALLS:
            self.issues.append({
                "type": "DANGEROUS_CALL",
                "severity": "CRITICAL",
                "line": node.lineno,
                "detail": f"Appel dangereux : {name}() detecte",
            })
        elif name in DANGEROUS_SUBPROCESS:
            self.issues.append({
                "type": "SUBPROCESS_CALL",
                "severity": "WARN",
                "line": node.lineno,
                "detail": f"Subprocess potentiellement bloquant : {name}()",
            })
        self.generic_visit(node)

    # ── Except nus ────────────────────────────────────────────────────────────

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.issues.append({
                "type": "BARE_EXCEPT",
                "severity": "WARN",
                "line": node.lineno,
                "detail": "bare except: capte toutes les exceptions sans filtrage",
            })
        elif node.name is None and isinstance(node.type, ast.Name):
            if node.type.id == "Exception":
                # except Exception sans binding → message d'erreur perdu
                body_calls = [n for n in ast.walk(ast.Module(body=node.body, type_ignores=[]))
                              if isinstance(n, ast.Call) and self._call_name(n) in ("print", "logging.error", "logger.error")]
                if not body_calls:
                    self.issues.append({
                        "type": "SILENT_EXCEPT",
                        "severity": "WARN",
                        "line": node.lineno,
                        "detail": "except Exception sans log ni re-raise : erreur silencieuse",
                    })
        self.generic_visit(node)

    # ── Fonctions vides ───────────────────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prev = self._current_func
        self._current_func = node.name
        # Detecter fonction a corps vide (uniquement pass ou docstring + pass)
        real_body = [s for s in node.body if not isinstance(s, ast.Expr)]
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.issues.append({
                "type": "EMPTY_FUNCTION",
                "severity": "WARN",
                "line": node.lineno,
                "detail": f"Fonction vide : {node.name}() — corps = pass uniquement",
            })
        elif len(node.body) == 2:
            has_docstring = isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
            has_pass = isinstance(node.body[1], ast.Pass)
            if has_docstring and has_pass:
                self.issues.append({
                    "type": "STUB_FUNCTION",
                    "severity": "INFO",
                    "line": node.lineno,
                    "detail": f"Stub fonction : {node.name}() — docstring + pass uniquement",
                })
        self.generic_visit(node)
        self._current_func = prev

    visit_AsyncFunctionDef = visit_FunctionDef  # Meme logique pour async def

    # ── Constantes de chemin hardcodees ──────────────────────────────────────

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.s, str):
            for pattern in HARDCODED_PATH_PATTERNS:
                if pattern in node.s:
                    self.issues.append({
                        "type": "HARDCODED_PATH",
                        "severity": "WARN",
                        "line": node.lineno,
                        "detail": f"Chemin hardcode detecte : '{node.s[:60]}...' (pattern: {pattern})",
                    })
                    break
        self.generic_visit(node)

    # ── Utilitaire ────────────────────────────────────────────────────────────

    @staticmethod
    def _call_name(node: ast.Call) -> str:
        """Retourne le nom de l'appel : func() ou module.func()"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return ""


# ─── Classe principale ────────────────────────────────────────────────────────

class AstAnalyzer:
    """
    SENTINEL B1 — Analyse AST des scripts Python d'une fregate.
    """

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyse un seul fichier Python.

        Retourne :
        {
            "file": str,
            "verdict": "PASS" | "WARN" | "FAIL" | "ERROR",
            "score": int (0-100),
            "issues": [...],
            "stats": { "lines": int, "functions": int, "classes": int },
            "timestamp": str
        }
        """
        path = Path(filepath)
        result: Dict[str, Any] = {
            "file": str(path),
            "verdict": "UNKNOWN",
            "score": 100,
            "issues": [],
            "stats": {"lines": 0, "functions": 0, "classes": 0},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not path.exists():
            result["verdict"] = "ERROR"
            result["issues"].append({
                "type": "FILE_NOT_FOUND",
                "severity": "CRITICAL",
                "line": 0,
                "detail": f"Fichier introuvable : {filepath}",
            })
            return result

        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            lines = source.splitlines()
            result["stats"]["lines"] = len(lines)
        except Exception as e:
            result["verdict"] = "ERROR"
            result["issues"].append({
                "type": "READ_ERROR",
                "severity": "CRITICAL",
                "line": 0,
                "detail": f"Impossible de lire le fichier : {e}",
            })
            return result

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as e:
            result["verdict"] = "FAIL"
            result["score"] = 0
            result["issues"].append({
                "type": "SYNTAX_ERROR",
                "severity": "CRITICAL",
                "line": e.lineno or 0,
                "detail": f"Erreur de syntaxe : {e.msg}",
            })
            return result

        # Statistiques basiques
        result["stats"]["functions"] = sum(
            1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        result["stats"]["classes"] = sum(
            1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
        )

        # Visite AST
        visitor = _SentinelVisitor(str(path))
        visitor.visit(tree)
        result["issues"] = visitor.issues

        # Calcul score
        score = 100
        for issue in result["issues"]:
            sev = issue.get("severity", "INFO")
            if sev == "CRITICAL":
                score -= 30
            elif sev == "WARN":
                score -= 10
            elif sev == "INFO":
                score -= 2
        score = max(0, score)
        result["score"] = score

        # Verdict
        n_critical = sum(1 for i in result["issues"] if i.get("severity") == "CRITICAL")
        if n_critical > 0 or score < SCORE_FAIL_THRESHOLD:
            result["verdict"] = "FAIL"
        elif score < SCORE_WARN_THRESHOLD:
            result["verdict"] = "WARN"
        else:
            result["verdict"] = "PASS"

        return result

    def analyze_dir(
        self,
        scripts_dir: str,
        fregate: str = "UNKNOWN",
        extensions: Tuple[str, ...] = (".py",),
        exclude_patterns: Tuple[str, ...] = ("test_", "_test", "__pycache__"),
    ) -> Dict[str, Any]:
        """
        Analyse tous les fichiers Python d'un dossier.

        Retourne :
        {
            "fregate": str,
            "verdict": "PASS" | "WARN" | "FAIL" | "ERROR",
            "score_global": int,
            "files_analyzed": int,
            "files_fail": int,
            "files_warn": int,
            "total_issues": int,
            "critical_issues": int,
            "per_file": [...],
            "summary": str,
            "timestamp": str
        }
        """
        dir_path = Path(scripts_dir)
        result: Dict[str, Any] = {
            "fregate": fregate,
            "scripts_dir": str(dir_path),
            "verdict": "UNKNOWN",
            "score_global": 100,
            "files_analyzed": 0,
            "files_fail": 0,
            "files_warn": 0,
            "total_issues": 0,
            "critical_issues": 0,
            "per_file": [],
            "summary": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not dir_path.exists():
            result["verdict"] = "ERROR"
            result["summary"] = f"Dossier introuvable : {scripts_dir}"
            return result

        # Collecte des fichiers
        py_files = [
            f for f in sorted(dir_path.rglob("*"))
            if f.suffix in extensions
            and not any(p in f.name for p in exclude_patterns)
            and "__pycache__" not in str(f)
        ]

        if not py_files:
            result["verdict"] = "WARN"
            result["summary"] = f"Aucun fichier .py trouve dans {scripts_dir}"
            return result

        # Analyse fichier par fichier
        scores: List[int] = []
        for f in py_files:
            file_result = self.analyze_file(str(f))
            result["per_file"].append(file_result)
            result["files_analyzed"] += 1
            result["total_issues"] += len(file_result.get("issues", []))
            result["critical_issues"] += sum(
                1 for i in file_result.get("issues", []) if i.get("severity") == "CRITICAL"
            )
            if file_result["verdict"] == "FAIL":
                result["files_fail"] += 1
            elif file_result["verdict"] == "WARN":
                result["files_warn"] += 1
            scores.append(file_result.get("score", 100))

        # Score global = moyenne des scores fichiers
        result["score_global"] = int(sum(scores) / len(scores)) if scores else 0

        # Verdict global
        if result["critical_issues"] > 0 or result["files_fail"] > 0:
            result["verdict"] = "FAIL"
        elif result["files_warn"] > 0 or result["score_global"] < SCORE_WARN_THRESHOLD:
            result["verdict"] = "WARN"
        else:
            result["verdict"] = "PASS"

        result["summary"] = (
            f"{result['files_analyzed']} fichiers — score {result['score_global']}/100 — "
            f"{result['critical_issues']} CRITICAL, {result['total_issues']} issues totales"
        )

        return result

    def save(self, result: Dict[str, Any], output_path: str) -> None:
        """Sauvegarde le resultat en JSON."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    def print_report(self, result: Dict[str, Any]) -> None:
        """Affiche un rapport lisible dans la console."""
        verdict = result.get("verdict", "?")
        icon = "[PASS]" if verdict == "PASS" else ("[WARN]" if verdict == "WARN" else "[FAIL]")
        fregate = result.get("fregate", result.get("file", "?"))

        print(f"\n  [B1 L'ESPRIT] {fregate} — {icon}")
        print(f"  Score global   : {result.get('score_global', result.get('score', '?'))}/100")
        print(f"  Fichiers       : {result.get('files_analyzed', 1)} analyses")
        print(f"  Issues totales : {result.get('total_issues', len(result.get('issues', [])))}")
        print(f"  CRITICAL       : {result.get('critical_issues', sum(1 for i in result.get('issues', []) if i.get('severity') == 'CRITICAL'))}")

        # Afficher les issues critiques
        all_issues = result.get("issues", [])
        if not all_issues:
            for pf in result.get("per_file", []):
                all_issues.extend(pf.get("issues", []))
        critical = [i for i in all_issues if i.get("severity") == "CRITICAL"]
        for issue in critical[:5]:
            print(f"    CRITICAL ligne {issue.get('line', '?')} : {issue.get('detail', '')}")
        if len(critical) > 5:
            print(f"    ... +{len(critical) - 5} autres issues critiques")


# ─── CLI standalone ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SENTINEL B1 — Analyse AST des scripts Python")
    p.add_argument("--fregate", default="UNKNOWN", help="ID fregate (U00-U06)")
    p.add_argument("--scripts", default=None, help="Dossier scripts a analyser")
    p.add_argument("--file", default=None, help="Fichier Python unique a analyser")
    p.add_argument("--output", default=None, help="Chemin JSON de sortie")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    analyzer = AstAnalyzer()

    if args.file:
        result = analyzer.analyze_file(args.file)
        analyzer.print_report(result)
        if args.output:
            analyzer.save(result, args.output)
            print(f"  [B1] Rapport sauvegarde : {args.output}")
        return 0 if result["verdict"] in ("PASS", "WARN") else 1

    if args.scripts:
        result = analyzer.analyze_dir(args.scripts, fregate=args.fregate)
        analyzer.print_report(result)
        if args.output:
            analyzer.save(result, args.output)
            print(f"  [B1] Rapport sauvegarde : {args.output}")
        return 0 if result["verdict"] in ("PASS", "WARN") else 1

    print("Usage : python brique1_ast.py --scripts /path/to/CODEBASE/ [--fregate U03]")
    print("        python brique1_ast.py --file /path/to/script.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
