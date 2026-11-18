"""Comprueba que cada `uses:` de los flujos de GitHub Actions este fijado a un hash de commit de 40
caracteres con la version como comentario (NFR5.7), y que existan los archivos exigidos (por ejemplo
el archivo de bloqueo de Terraform).

Uso: python check_pins.py <archivo-o-carpeta>... [--require-file ruta]...
(0 = limpio, 1 = incumplimientos, 2 = error de uso)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_USES = re.compile(
    r"""^\s*(?:-\s+)?uses:\s*["']?(?P<ref>[^\s"'#]+)["']?\s*(?:#\s*(?P<comment>.*))?$"""
)
_PINNED = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}$")
_DOCKER_PINNED = re.compile(r"^docker://[^@\s]+@sha256:[0-9a-f]{64}$")
_WORKFLOW_SUFFIXES = {".yml", ".yaml"}


def check_workflow_text(text: str, name: str) -> list[str]:
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        match = _USES.match(line)
        if not match:
            continue
        ref = match.group("ref")
        if ref.startswith("./"):
            continue
        pinned = bool(_PINNED.match(ref) or _DOCKER_PINNED.match(ref))
        if not pinned:
            found.append(f"{name}:{number}: '{ref}' no esta fijado a un hash de 40 caracteres")
        elif not (match.group("comment") or "").strip():
            found.append(f"{name}:{number}: '{ref}' no lleva la version como comentario")
    return found


def _workflow_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.suffix in _WORKFLOW_SUFFIXES)
    return [path]


def check_paths(paths: list[Path], required_files: list[Path]) -> list[str]:
    found: list[str] = []
    for path in paths:
        for file in _workflow_files(path):
            found.extend(check_workflow_text(file.read_text(encoding="utf-8"), str(file)))
    for required in required_files:
        if not required.is_file():
            found.append(f"{required}: falta el archivo exigido")
    return found


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    required: list[Path] = []
    paths: list[Path] = []
    while args:
        item = args.pop(0)
        if item == "--require-file" and args:
            required.append(Path(args.pop(0)))
        else:
            paths.append(Path(item))
    if not paths and not required:
        print("Uso: check_pins.py <archivo-o-carpeta>... [--require-file ruta]...", file=sys.stderr)
        return 2
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"No existe: {missing[0]}", file=sys.stderr)
        return 2

    found = check_paths(paths, required)
    if found:
        print("check_pins: incumplimientos:")
        for line in found:
            print(f"  - {line}")
        return 1
    print("check_pins: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
