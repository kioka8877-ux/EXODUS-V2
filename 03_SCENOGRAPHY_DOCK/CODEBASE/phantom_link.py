#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            PHANTOM LINK — Résolveur Universel Inter-Frégates                ║
║                        EXODUS V2 Phase D.1                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Élimine 100% des copies manuelles entre frégates.                          ║
║  Chaque frégate lit directement depuis le OUT/ de la précédente             ║
║  via un fichier pointeur _LINK.json de 50 octets.                           ║
║                                                                              ║
║  API : create_link(), resolve_input(), validate_link()                      ║
║  Dépendances : zéro (Python standard library)                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
from pathlib import Path
from datetime import datetime, timezone

LINK_FILENAME = "_LINK.json"


def create_link(source_dir: str, target_in_dir: str) -> Path:
    """Crée un _LINK.json dans target_in_dir pointant vers source_dir."""
    source = Path(source_dir)
    if not source.is_dir():
        raise FileNotFoundError(
            f"Source introuvable ou n'est pas un dossier : {source_dir}"
        )

    target = Path(target_in_dir)
    target.mkdir(parents=True, exist_ok=True)

    link_data = {
        "source": str(source.resolve()),
        "created": datetime.now(timezone.utc).isoformat(),
        "created_by": "MARSHAL",
    }

    link_path = target / LINK_FILENAME
    with open(link_path, "w", encoding="utf-8") as f:
        json.dump(link_data, f, indent=2, ensure_ascii=False)

    print(f"[PHANTOM] Link créé : {target_in_dir}/{LINK_FILENAME} → {source_dir}")
    return link_path


def resolve_input(in_dir) -> Path:
    """Résout un dossier IN/ : si _LINK.json existe, retourne la source.

    Sinon retourne in_dir tel quel.
    """
    in_path = Path(in_dir)
    link_file = in_path / LINK_FILENAME

    if not link_file.is_file():
        return in_path

    try:
        with open(link_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        source = data.get("source")
        if not source:
            print(
                f"[PHANTOM:WARN] _LINK.json sans champ 'source' dans {in_dir}, fallback sur {in_dir}"
            )
            return in_path

        source_path = Path(source)
        if source_path.is_dir():
            return source_path

        print(f"[PHANTOM:WARN] Source introuvable: {source}, fallback sur {in_dir}")
        return in_path
    except (json.JSONDecodeError, OSError, KeyError) as exc:
        print(f"[PHANTOM:WARN] Erreur lecture _LINK.json ({exc}), fallback sur {in_dir}")
        return in_path


def validate_link(in_dir: str) -> dict:
    """Valide un lien phantom : existe ? source accessible ? fichiers présents ?"""
    in_path = Path(in_dir)
    link_file = in_path / LINK_FILENAME

    result = {
        "has_link": False,
        "valid": False,
        "source": None,
        "file_count": 0,
        "total_size": 0,
        "total_size_human": "0 B",
    }

    if not link_file.is_file():
        return result

    result["has_link"] = True

    try:
        with open(link_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        source = data.get("source")
        result["source"] = source
    except (json.JSONDecodeError, OSError):
        return result

    if not source:
        return result

    source_path = Path(source)
    if not source_path.is_dir():
        return result

    result["valid"] = True

    files = [f for f in source_path.iterdir() if f.is_file()]
    result["file_count"] = len(files)
    total = sum(f.stat().st_size for f in files)
    result["total_size"] = total
    result["total_size_human"] = _format_size(total)

    return result


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


if __name__ == "__main__":
    import tempfile

    passed = 0
    total = 5

    # Test 1 — create_link avec source valide
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source_out"
        src.mkdir()
        (src / "data.bin").write_bytes(b"x" * 100)
        tgt = Path(tmpdir) / "target_in"

        link_path = create_link(str(src), str(tgt))
        assert link_path.is_file(), "Fichier _LINK.json non créé"
        with open(link_path, "r") as f:
            content = json.load(f)
        assert content["source"] == str(src.resolve()), "Source incorrecte"
        passed += 1
        print(f"[PHANTOM:TEST] {passed}/{total} — create_link avec source valide OK")

    # Test 2 — resolve_input avec lien valide
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source_out"
        src.mkdir()
        (src / "file.txt").write_text("hello")
        tgt = Path(tmpdir) / "target_in"
        create_link(str(src), str(tgt))

        resolved = resolve_input(tgt)
        assert resolved == src.resolve(), f"Attendu {src.resolve()}, obtenu {resolved}"
        passed += 1
        print(f"[PHANTOM:TEST] {passed}/{total} — resolve_input avec lien valide OK")

    # Test 3 — resolve_input sans lien
    with tempfile.TemporaryDirectory() as tmpdir:
        plain_dir = Path(tmpdir) / "plain_in"
        plain_dir.mkdir()

        resolved = resolve_input(plain_dir)
        assert resolved == plain_dir, f"Attendu {plain_dir}, obtenu {resolved}"
        passed += 1
        print(f"[PHANTOM:TEST] {passed}/{total} — resolve_input sans lien OK")

    # Test 4 — resolve_input avec source invalide (fallback + warning)
    with tempfile.TemporaryDirectory() as tmpdir:
        tgt = Path(tmpdir) / "target_in"
        tgt.mkdir()
        link_data = {
            "source": "/nonexistent/path/12345",
            "created": "2026-01-01T00:00:00",
            "created_by": "TEST",
        }
        with open(tgt / LINK_FILENAME, "w") as f:
            json.dump(link_data, f)

        resolved = resolve_input(tgt)
        assert resolved == tgt, f"Fallback attendu {tgt}, obtenu {resolved}"
        passed += 1
        print(
            f"[PHANTOM:TEST] {passed}/{total} — resolve_input avec source invalide (fallback) OK"
        )

    # Test 5 — validate_link retourne les bonnes métriques
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src_out"
        src.mkdir()
        (src / "a.png").write_bytes(b"x" * 500)
        (src / "b.png").write_bytes(b"x" * 300)
        tgt = Path(tmpdir) / "tgt_in"
        create_link(str(src), str(tgt))

        info = validate_link(str(tgt))
        assert info["has_link"] is True
        assert info["valid"] is True
        assert info["file_count"] == 2
        assert info["total_size"] == 800
        passed += 1
        print(f"[PHANTOM:TEST] {passed}/{total} — validate_link métriques OK")

    print(f"\n[PHANTOM:TEST] Résultat final : {passed}/{total} tests passés")

