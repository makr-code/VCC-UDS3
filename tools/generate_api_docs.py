#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generiert API-Dokumentations-Seiten für MkDocs (mkdocstrings).

- Scannt ausgewählte Pakete (database, search)
- Erstellt Markdown-Dateien unter docs/api/
- Jede Datei enthält einen mkdocstrings-Block '::: paket.modul'
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
API_DIR = DOCS_DIR / "api"

# Pakete, die dokumentiert werden sollen (müssen Python-Pakete sein)
PACKAGES = [
    (REPO_ROOT / "database", "database"),
    (REPO_ROOT / "search", "search"),
]

# Ordner, die explizit ausgeschlossen werden (keine Python-Pakete oder nicht dokumentationsrelevant)
EXCLUDE_SUBDIRS = {
    REPO_ROOT / "database" / "scripts",
    REPO_ROOT / "database" / "tests",
}

HEADER = """---
title: {title}
---

# {title}

::: {module}
"""

INDEX_HEADER = """# API-Referenz

Automatisch generierte API-Referenz aus dem Quellcode mittels mkdocstrings.

"""

def is_within_python_package(file_path: Path, package_root: Path) -> bool:
    """Prüft, ob alle Teilpfade vom Paket-Root bis zum Modulordner __init__.py enthalten.

    Mkdocstrings kann nur importierbare Module dokumentieren. Daher müssen alle
    Unterordner Python-Pakete sein.
    """
    cursor = file_path.parent
    while True:
        if cursor == package_root:
            return True
        if not (cursor / "__init__.py").exists():
            return False
        cursor = cursor.parent


def find_modules(package_path: Path, package_name: str) -> list[tuple[str, Path]]:
    modules: list[tuple[str, Path]] = []
    for path in package_path.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        # Ausschlüsse
        if any(str(path).startswith(str(ex)) for ex in EXCLUDE_SUBDIRS):
            continue
        # Module nur innerhalb des Pakets
        rel = path.relative_to(REPO_ROOT)
        # Baue Modulpfad mit Punkten
        mod_name = str(rel.with_suffix("")).replace(os.sep, ".")
        # Sicherheitsfilter: Muss mit package_name beginnen
        if not mod_name.startswith(package_name + ".") and mod_name != package_name:
            continue
        # Nur Module in echten Python-Packages zulassen
        if not is_within_python_package(path, package_path):
            continue
        modules.append((mod_name, path))
    modules.sort()
    return modules


def main() -> int:
    # API-Verzeichnis säubern, um veraltete Dateien zu entfernen
    if API_DIR.exists():
        for p in sorted(API_DIR.rglob("*"), reverse=True):
            try:
                if p.is_file() or p.is_symlink():
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
            except Exception:
                pass
    API_DIR.mkdir(parents=True, exist_ok=True)

    all_modules: list[str] = []

    for pkg_path, pkg_name in PACKAGES:
        if not pkg_path.exists():
            continue
        for mod_name, file_path in find_modules(pkg_path, pkg_name):
            all_modules.append(mod_name)
            out_path = API_DIR / f"{mod_name.replace('.', '/')}.md"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            content = HEADER.format(title=mod_name, module=mod_name)
            out_path.write_text(content, encoding="utf-8")

    # Index erzeugen
    index_md = [INDEX_HEADER]
    for mod in sorted(all_modules):
        index_md.append(f"- [{mod}](./{mod.replace('.', '/')}.md)")
    (API_DIR / "index.md").write_text("\n".join(index_md) + "\n", encoding="utf-8")

    print(f"Generated {len(all_modules)} API pages under {API_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
