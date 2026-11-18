"""Verificacion REAL del paquete de la funcion (paso 22).

Corre sobre infra/build/package, construido con `python infra/scripts/build_lambda_package.py`
(acceso a PyPI, sin credenciales de AWS). Sin la carpeta la prueba se omite, salvo que
REQUIRE_REAL_PACKAGE=1 (el trabajo `infra` de ci.yml la construye antes y la exige): asi pytest
local no depende de la red.
"""

from __future__ import annotations

import os
import re
import zipfile
from pathlib import Path

import pytest

import build_lambda_package as blp

PACKAGE = blp.DEFAULT_OUT
LAMBDA_ZIP_LIMIT = 50 * 1024 * 1024
LAMBDA_UNZIPPED_LIMIT = 250 * 1024 * 1024
EM_X86_64 = 0x3E
MAX_GLIBC = (2, 34)

if not PACKAGE.is_dir():
    if os.environ.get("REQUIRE_REAL_PACKAGE") == "1":
        pytest.fail(
            f"falta {PACKAGE}: ejecuta infra/scripts/build_lambda_package.py", pytrace=False
        )
    pytest.skip("paquete real no construido", allow_module_level=True)


def test_contains_the_service_handler_and_jwt() -> None:
    assert (PACKAGE / "story_service" / "handler.py").is_file()
    assert (PACKAGE / "jwt" / "__init__.py").is_file()
    # boto3 y botocore los trae el runtime python3.12 de Lambda: no van en el paquete.
    assert not (PACKAGE / "boto3").exists() and not (PACKAGE / "botocore").exists()


def test_has_no_tests_or_caches() -> None:
    names = [p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*")]
    assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)
    assert not any(n.startswith("story_service/tests") for n in names)
    assert not any(n.endswith(".env") for n in names)


def test_has_no_host_os_leftovers() -> None:
    assert not (PACKAGE / "bin").exists()
    assert not [p for p in PACKAGE.rglob("*") if p.suffix in {".exe", ".bat", ".cmd"}]


def test_binaries_need_glibc_2_34_or_older() -> None:
    """El runtime python3.12 de Lambda (Amazon Linux 2023) trae glibc 2.34.

    Se leen los nombres de version `GLIBC_x.y` de la tabla de simbolos dinamicos de cada `.so`.
    NO se verifica que la funcion arranque en Lambda: importar un `.so` de Linux es imposible
    en Windows, y la carga real solo se confirma en el primer despliegue.
    """
    found = {}
    for binary in PACKAGE.rglob("*.so"):
        versions = {
            tuple(int(n) for n in m.groups(default="0")[:2])
            for m in re.finditer(rb"GLIBC_(\d+)\.(\d+)", binary.read_bytes())
        }
        if versions:
            found[binary.name] = max(versions)
    assert found, "ningun .so declara versiones de glibc: no se pudo comprobar"
    too_new = {name: v for name, v in found.items() if v > MAX_GLIBC}
    assert not too_new, f"requieren una glibc mas nueva que 2.34: {too_new}"


def test_cryptography_ships_a_linux_x86_64_binary() -> None:
    binaries = sorted((PACKAGE / "cryptography").rglob("*.so"))
    assert binaries, "cryptography no trae ningun .so: es la rueda equivocada (no es de Linux)"
    for binary in binaries:
        header = binary.read_bytes()[:20]
        assert header[:4] == b"\x7fELF", f"{binary.name} no es un ELF (no es de Linux)"
        assert header[18] | (header[19] << 8) == EM_X86_64, f"{binary.name} no es x86_64"


def test_zipped_and_unzipped_sizes_fit_the_lambda_limits(tmp_path: Path) -> None:
    archive = tmp_path / "story_service.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(PACKAGE).as_posix())
    unzipped = sum(p.stat().st_size for p in PACKAGE.rglob("*") if p.is_file())
    zipped = archive.stat().st_size
    print(f"\npaquete: zip {zipped / 1048576:.1f} MB, descomprimido {unzipped / 1048576:.1f} MB")
    assert zipped < LAMBDA_ZIP_LIMIT
    assert unzipped < LAMBDA_UNZIPPED_LIMIT
