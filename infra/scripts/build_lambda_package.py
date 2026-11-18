"""Construye la carpeta de empaquetado de la funcion Lambda (infra/build/package).

Contenido: el codigo de `backend/story_service` (como paquete de nivel superior, porque el
manejador es `story_service.handler.lambda_handler`) mas las dependencias de EJECUCION fijadas en
`infra/lambda-requirements.lock.txt` (versiones y hashes exactos), instaladas para Lambda (Python
3.12, Linux x86_64, solo ruedas binarias, sin resolver dependencias). Sin PyJWT[crypto] la funcion
falla al importar `jwt`, por eso el script falla si el resultado no trae `jwt/` y `cryptography/`.

boto3 y botocore NO van en el paquete: el runtime python3.12 de Lambda ya los trae.

Terraform comprime esa carpeta con `data.archive_file.story_service`; el script debe correr antes de
`terraform plan` y `apply` (ci.yml y deploy.yml lo hacen).

Determinista dado el archivo de bloqueo: mismas ruedas (hash), sin cachés de compilacion, sin
restos del sistema de quien construye y con marcas de tiempo fijas, de modo que el hash del zip de
`archive_file` es estable. Si se cambia el bloqueo, el paquete cambia a proposito.

Uso: python build_lambda_package.py [--backend backend] [--lock bloqueo] [--out carpeta]
Codigos de salida: 0 correcto, 1 fallo del empaquetado, 2 uso incorrecto.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKEND = REPO_ROOT / "backend"
DEFAULT_LOCK = REPO_ROOT / "infra" / "lambda-requirements.lock.txt"
DEFAULT_OUT = REPO_ROOT / "infra" / "build" / "package"

# 2020-01-01T00:00:00Z: marca fija para que dos construcciones den el mismo resultado.
FIXED_MTIME = 1577836800

REQUIRED_PACKAGES = ("jwt", "cryptography")
# Dependencias de backend/requirements.txt que el runtime python3.12 de Lambda ya trae.
RUNTIME_PROVIDED = frozenset({"boto3", "botocore"})
# Cadena de PyJWT[crypto] que el bloqueo debe fijar (los extras no se resuelven con --no-deps).
REQUIRED_LOCK_NAMES = ("pyjwt", "cryptography", "cffi", "pycparser")
HOST_LEFTOVER_SUFFIXES = (".exe", ".bat", ".cmd")
PLATFORMS = ("manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_28_x86_64")
IGNORE_PATTERNS = ("__pycache__", "*.pyc", ".env*", ".pytest_cache", ".ruff_cache", "tests")

Runner = Callable[[list[str]], int]


class BuildError(Exception):
    """El empaquetado no se pudo completar."""


def run_command(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def pip_command(lock: Path, target: Path) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-compile",
        "--no-deps",
        "--require-hashes",
        "--only-binary=:all:",
    ]
    for platform in PLATFORMS:
        command += ["--platform", platform]
    return command + [
        "--python-version",
        "3.12",
        "--implementation",
        "cp",
        "--target",
        str(target),
        "-r",
        str(lock),
    ]


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _logical_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").replace("\\\r\n", " ").replace("\\\n", " ")
    lines = (line.strip() for line in text.splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def check_lock(requirements: Path, lock: Path) -> list[str]:
    """Incumplimientos del bloqueo (vacia si es correcto): `==`, `--hash` y cobertura."""
    errors: list[str] = []
    locked: set[str] = set()
    for line in _logical_lines(lock):
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==[^\s=;]+", line)
        if not match:
            errors.append(f"bloqueo: la linea '{line.split()[0]}' no fija la version con ==")
            continue
        name = _normalize(match.group(1))
        locked.add(name)
        if not re.search(r"--hash=sha256:[0-9a-f]{64}", line):
            errors.append(f"bloqueo: '{name}' no lleva --hash=sha256")
        if name in RUNTIME_PROVIDED:
            errors.append(
                f"bloqueo: '{name}' lo trae el runtime de Lambda y no debe ir en el paquete"
            )

    for name in REQUIRED_LOCK_NAMES:
        if name not in locked:
            errors.append(
                f"bloqueo: falta '{name}' (PyJWT[crypto] necesita cryptography, cffi y pycparser)"
            )

    for line in _logical_lines(requirements):
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if match:
            name = _normalize(match.group(1))
            if name not in locked and name not in RUNTIME_PROVIDED:
                errors.append(f"backend/requirements.txt pide '{name}' y el bloqueo no lo cubre")
    return errors


def _strip_caches(root: Path) -> None:
    for cache in sorted(root.rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)
    for pyc in root.rglob("*.pyc"):
        pyc.unlink()


def _fix_times(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if not path.is_symlink():
            os.utime(path, (FIXED_MTIME, FIXED_MTIME))
    os.utime(root, (FIXED_MTIME, FIXED_MTIME))


def _remove_host_leftovers(root: Path) -> None:
    """Quita lo que depende del sistema operativo de quien construye (ejecutables y lanzadores)."""
    shutil.rmtree(root / "bin", ignore_errors=True)
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in HOST_LEFTOVER_SUFFIXES:
            path.unlink()


def _sort_records(root: Path) -> None:
    """Deja RECORD estable: lineas ordenadas y sin las de archivos que ya no estan.

    pip escribe el orden variable y registra los lanzadores `bin/*.exe` del sistema de quien
    construye (con un hash distinto en cada ejecucion); esos archivos se borraron antes.
    """
    for record in root.glob("*.dist-info/RECORD"):
        kept = []
        for line in record.read_text(encoding="utf-8").splitlines():
            relative = line.split(",")[0]
            if (
                relative.endswith("RECORD")
                or (root / relative).resolve().is_relative_to(root.resolve())
                and (root / relative).exists()
            ):
                kept.append(line)
        record.write_text("\n".join(sorted(kept)) + "\n", encoding="utf-8", newline="\n")


def build_package(
    backend: Path, out: Path, runner: Runner = run_command, lock: Path = DEFAULT_LOCK
) -> None:
    service = backend / "story_service"
    requirements = backend / "requirements.txt"
    if not (service / "handler.py").is_file():
        raise BuildError(f"falta {service / 'handler.py'}")
    if not requirements.is_file():
        raise BuildError(f"falta el archivo de requirements: {requirements}")
    if not lock.is_file():
        raise BuildError(f"falta el archivo de bloqueo: {lock}")
    problems = check_lock(requirements, lock)
    if problems:
        raise BuildError("; ".join(problems))

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    code = runner(pip_command(lock, out))
    if code != 0:
        raise BuildError(f"pip install fallo con el codigo {code}")

    shutil.copytree(service, out / "story_service", ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
    _strip_caches(out)
    _remove_host_leftovers(out)
    _sort_records(out)

    for name in REQUIRED_PACKAGES:
        if not (out / name).is_dir():
            raise BuildError(f"el paquete no contiene '{name}' (dependencia obligatoria)")
    _fix_times(out)


def main(argv: list[str] | None = None, runner: Runner = run_command) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backend", type=Path, default=DEFAULT_BACKEND)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if not args.backend.is_dir():
        print(f"No existe la carpeta del servicio: {args.backend}", file=sys.stderr)
        return 2
    try:
        build_package(args.backend, args.out, runner, args.lock)
    except BuildError as error:
        print(f"FALLO: {error}", file=sys.stderr)
        return 1
    print(f"build_lambda_package: OK ({args.out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
