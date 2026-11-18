"""Busca patrones de claves y secretos literales en el repositorio de infraestructura (NFR5.1).

Patrones: clave de acceso de AWS (AKIA y ASIA), un client_secret con valor literal entre
comillas y claves privadas.
No marca `sensitive = true` ni nombres de variables. Nunca imprime el texto encontrado, solo
archivo, linea y tipo.

Uso: python check_secrets.py <archivo-o-carpeta>...   (0 = limpio, 1 = hallazgos, 2 = error de uso)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PATTERNS = (
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "clave de acceso de AWS (AKIA)"),
    (re.compile(r"\bASIA[0-9A-Z]{16}\b"), "clave temporal de AWS (ASIA)"),
    (re.compile(r"""\bclient_secret\s*=\s*["']"""), "client_secret literal"),
    (re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"), "clave privada"),
)
_SKIP_DIRS = {
    ".terraform",
    "build",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}
_SKIP_FILES = {".terraform.lock.hcl"}


def scan_text(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern, kind in _PATTERNS:
            if pattern.search(line):
                found.append((number, kind))
    return found


def _files(path: Path):
    if path.is_file():
        yield path
        return
    for file in sorted(path.rglob("*")):
        if (
            file.is_file()
            and file.name not in _SKIP_FILES
            and not _SKIP_DIRS.intersection(file.parts)
        ):
            yield file


def scan_paths(paths: list[Path]) -> list[str]:
    found: list[str] = []
    for path in paths:
        for file in _files(path):
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            found.extend(f"{file}:{number}: {kind}" for number, kind in scan_text(text))
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Uso: check_secrets.py <archivo-o-carpeta>...", file=sys.stderr)
        return 2
    paths = [Path(item) for item in args]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"No existe: {missing[0]}", file=sys.stderr)
        return 2

    found = scan_paths(paths)
    if found:
        print("check_secrets: posibles secretos literales:")
        for line in found:
            print(f"  - {line}")
        return 1
    print("check_secrets: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
