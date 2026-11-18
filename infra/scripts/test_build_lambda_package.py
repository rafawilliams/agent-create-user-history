"""Pruebas de build_lambda_package.py con un ejecutor de pip simulado (sin red).

La funcion Lambda debe llevar `story_service/` como paquete de nivel superior (el manejador
es `story_service.handler.lambda_handler`) y las dependencias de backend/requirements.txt
instaladas para Linux x86_64 con Python 3.12; sin PyJWT[crypto] todo arranque fallaria al
importar `jwt`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import build_lambda_package as blp

FIXED_MTIME = blp.FIXED_MTIME


def make_backend(root: Path) -> Path:
    backend = root / "backend"
    service = backend / "story_service"
    (service / "__pycache__").mkdir(parents=True)
    (service / "__init__.py").write_text("", encoding="utf-8")
    (service / "handler.py").write_text(
        "def lambda_handler(event, context): ...\n", encoding="utf-8"
    )
    (service / "mod.cpython-312.pyc").write_bytes(b"pyc")
    (service / "__pycache__" / "handler.cpython-312.pyc").write_bytes(b"pyc")
    (service / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (backend / "tests").mkdir()
    (backend / "tests" / "test_x.py").write_text("def test_x(): ...\n", encoding="utf-8")
    (backend / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (backend / "requirements.txt").write_text(
        "boto3>=1.34,<2\nPyJWT[crypto]==2.10.1\n", encoding="utf-8"
    )
    return backend


HASH = "sha256:" + "a" * 64
LOCK_TEXT = "".join(
    f"{name}=={version} \\\n    --hash={HASH}\n"
    for name, version in [
        ("PyJWT", "2.10.1"),
        ("cffi", "2.1.1"),
        ("cryptography", "50.0.2"),
        ("pycparser", "3.12"),
    ]
)


def make_lock(root: Path, text: str = LOCK_TEXT) -> Path:
    lock = root / "lambda-requirements.lock.txt"
    lock.write_text(text, encoding="utf-8")
    return lock


class FakePip:
    """Imita `pip install --target`: escribe jwt, cryptography y un cache que debe desaparecer."""

    def __init__(
        self, returncode: int = 0, packages: tuple[str, ...] = ("jwt", "cryptography")
    ) -> None:
        self.returncode = returncode
        self.packages = packages
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str]) -> int:
        self.calls.append(command)
        if self.returncode == 0:
            target = Path(command[command.index("--target") + 1])
            for name in self.packages:
                (target / name).mkdir(parents=True, exist_ok=True)
                (target / name / "__init__.py").write_text("", encoding="utf-8")
                (target / name / "__pycache__").mkdir(exist_ok=True)
                (target / name / "__pycache__" / "x.pyc").write_bytes(b"pyc")
            # Restos del sistema operativo de quien construye: no deben llegar al paquete.
            (target / "jwt-1.dist-info").mkdir(exist_ok=True)
            (target / "jwt-1.dist-info" / "RECORD").write_text(
                "jwt/__init__.py,,\n../../bin/tool.exe,sha256=x,2\ncryptography/__init__.py,,\n",
                encoding="utf-8",
            )
            (target / "bin").mkdir(exist_ok=True)
            (target / "bin" / "tool.exe").write_bytes(b"MZ")
            (target / "bin" / "tool.py").write_text("#!python\n", encoding="utf-8")
            (target / "launcher.bat").write_text("@echo off\n", encoding="utf-8")
        return self.returncode


def files_of(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def build(tmp_path: Path, runner: FakePip | None = None) -> tuple[Path, FakePip]:
    backend = make_backend(tmp_path)
    out = tmp_path / "build" / "package"
    pip = runner or FakePip()
    blp.build_package(backend, out, runner=pip, lock=make_lock(tmp_path))
    return out, pip


def test_package_has_story_service_as_top_level_package(tmp_path: Path) -> None:
    out, _ = build(tmp_path)
    assert (out / "story_service" / "handler.py").is_file()
    assert (out / "story_service" / "__init__.py").is_file()


def test_package_excludes_tests_caches_env_and_project_files(tmp_path: Path) -> None:
    out, _ = build(tmp_path)
    names = set(files_of(out))
    assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)
    assert not any(n.endswith(".env") for n in names)
    assert not any(n.startswith("tests/") or n.startswith("story_service/tests") for n in names)
    assert "pyproject.toml" not in names and "requirements.txt" not in names


def test_pip_is_called_for_lambda_python312_linux_binary_wheels(tmp_path: Path) -> None:
    out, pip = build(tmp_path)
    (command,) = pip.calls
    assert command[1:4] == ["-m", "pip", "install"]
    platforms = [command[i + 1] for i, a in enumerate(command) if a == "--platform"]
    assert platforms == ["manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_28_x86_64"]
    assert "--no-deps" in command and "--require-hashes" in command
    for flag, value in [
        ("--python-version", "3.12"),
        ("--implementation", "cp"),
        ("--target", str(out)),
    ]:
        assert command[command.index(flag) + 1] == value
    assert "--only-binary=:all:" in command
    assert "--no-compile" in command
    assert command[command.index("-r") + 1].endswith("lambda-requirements.lock.txt")


def test_fails_when_pip_fails(tmp_path: Path) -> None:
    with pytest.raises(blp.BuildError, match="pip"):
        build(tmp_path, FakePip(returncode=1))


@pytest.mark.parametrize("missing", ["jwt", "cryptography"])
def test_fails_when_a_required_dependency_is_missing(tmp_path: Path, missing: str) -> None:
    packages = tuple(p for p in ("jwt", "cryptography") if p != missing)
    with pytest.raises(blp.BuildError, match=missing):
        build(tmp_path, FakePip(packages=packages))


def test_fails_when_the_service_code_is_missing(tmp_path: Path) -> None:
    backend = make_backend(tmp_path)
    (backend / "story_service" / "handler.py").unlink()
    with pytest.raises(blp.BuildError, match="handler.py"):
        blp.build_package(backend, tmp_path / "out", runner=FakePip(), lock=make_lock(tmp_path))


def test_fails_when_requirements_are_missing(tmp_path: Path) -> None:
    backend = make_backend(tmp_path)
    (backend / "requirements.txt").unlink()
    with pytest.raises(blp.BuildError, match="requirements"):
        blp.build_package(backend, tmp_path / "out", runner=FakePip(), lock=make_lock(tmp_path))


def test_a_second_build_gives_identical_content_and_times(tmp_path: Path) -> None:
    out, _ = build(tmp_path)
    first = files_of(out)
    times = {p.name: int(p.stat().st_mtime) for p in out.rglob("*")}
    blp.build_package(tmp_path / "backend", out, runner=FakePip(), lock=make_lock(tmp_path))
    assert files_of(out) == first
    assert {p.name: int(p.stat().st_mtime) for p in out.rglob("*")} == times
    assert set(times.values()) == {FIXED_MTIME}


def test_a_rebuild_removes_stale_files(tmp_path: Path) -> None:
    out, _ = build(tmp_path)
    (out / "stale.txt").write_text("old", encoding="utf-8")
    blp.build_package(tmp_path / "backend", out, runner=FakePip(), lock=make_lock(tmp_path))
    assert not (out / "stale.txt").exists()


def test_main_builds_with_injected_runner_and_returns_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    backend = make_backend(tmp_path)
    out = tmp_path / "out"
    lock = make_lock(tmp_path)
    code = blp.main(
        ["--backend", str(backend), "--out", str(out), "--lock", str(lock)], runner=FakePip()
    )
    assert code == 0
    assert "OK" in capsys.readouterr().out
    assert (out / "jwt" / "__init__.py").is_file()


def test_main_returns_one_on_build_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    backend = make_backend(tmp_path)
    lock = make_lock(tmp_path)
    code = blp.main(
        ["--backend", str(backend), "--out", str(tmp_path / "o"), "--lock", str(lock)],
        runner=FakePip(1),
    )
    assert code == 1
    assert "FALLO" in capsys.readouterr().err


def test_main_returns_two_for_a_missing_backend_directory(tmp_path: Path) -> None:
    assert blp.main(["--backend", str(tmp_path / "no"), "--out", str(tmp_path / "o")]) == 2


def test_default_runner_runs_a_command_and_returns_its_exit_code() -> None:
    import sys

    assert blp.run_command([sys.executable, "-c", "raise SystemExit(0)"]) == 0
    assert blp.run_command([sys.executable, "-c", "raise SystemExit(3)"]) == 3


def test_default_paths_point_at_the_repository(tmp_path: Path) -> None:
    root = Path(blp.__file__).resolve().parents[2]
    assert blp.DEFAULT_BACKEND == root / "backend"
    assert blp.DEFAULT_LOCK == root / "infra" / "lambda-requirements.lock.txt"
    assert blp.DEFAULT_OUT == root / "infra" / "build" / "package"
    assert os.path.isdir(blp.DEFAULT_BACKEND / "story_service")


# ---- Cierre de dependencias (archivo de bloqueo) ----------------------------------------------


def test_host_os_leftovers_are_removed_from_the_package(tmp_path: Path) -> None:
    out, _ = build(tmp_path)
    names = set(files_of(out))
    assert not (out / "bin").exists()
    assert not any(n.endswith((".exe", ".bat", ".cmd")) for n in names)


def test_lock_without_exact_pin_is_rejected(tmp_path: Path) -> None:
    lock = make_lock(tmp_path, "PyJWT>=2.10 \\\n    --hash=" + HASH + "\n")
    errors = blp.check_lock(make_backend(tmp_path) / "requirements.txt", lock)
    assert any("==" in e for e in errors)


def test_lock_line_without_a_hash_is_rejected(tmp_path: Path) -> None:
    text = LOCK_TEXT.replace(" \\\n    --hash=" + HASH, "", 1)
    errors = blp.check_lock(make_backend(tmp_path) / "requirements.txt", make_lock(tmp_path, text))
    assert any("hash" in e for e in errors)


def test_backend_dependency_missing_from_the_lock_is_rejected(tmp_path: Path) -> None:
    backend = make_backend(tmp_path)
    with (backend / "requirements.txt").open("a", encoding="utf-8") as handle:
        handle.write("requests>=2\n")
    errors = blp.check_lock(backend / "requirements.txt", make_lock(tmp_path))
    assert any("requests" in e for e in errors)


def test_boto3_is_provided_by_the_runtime_and_not_required_in_the_lock(tmp_path: Path) -> None:
    backend = make_backend(tmp_path)
    assert "boto3" in (backend / "requirements.txt").read_text(encoding="utf-8")
    assert blp.check_lock(backend / "requirements.txt", make_lock(tmp_path)) == []
    assert "boto3" in blp.RUNTIME_PROVIDED


def test_lock_must_include_the_crypto_chain(tmp_path: Path) -> None:
    text = "".join(line for line in LOCK_TEXT.splitlines(keepends=True) if "cffi" not in line)
    text = text.replace("cryptography==50.0.2 \\\n", "cryptography==50.0.2 \\\n", 1)
    lock = make_lock(tmp_path, "PyJWT==2.10.1 \\\n    --hash=" + HASH + "\n")
    errors = blp.check_lock(make_backend(tmp_path) / "requirements.txt", lock)
    assert any("cryptography" in e for e in errors)
    assert text  # el texto de apoyo se construye sin errores


def test_build_fails_when_the_lock_is_stale(tmp_path: Path) -> None:
    backend = make_backend(tmp_path)
    with (backend / "requirements.txt").open("a", encoding="utf-8") as handle:
        handle.write("requests>=2\n")
    with pytest.raises(blp.BuildError, match="requests"):
        blp.build_package(backend, tmp_path / "o", runner=FakePip(), lock=make_lock(tmp_path))


def test_real_lock_covers_the_real_backend_requirements() -> None:
    """Falla si backend/requirements.txt gana una dependencia que el bloqueo no cubre."""
    assert blp.check_lock(blp.DEFAULT_BACKEND / "requirements.txt", blp.DEFAULT_LOCK) == []


def test_record_files_are_sorted_so_the_package_is_deterministic(tmp_path: Path) -> None:
    """RECORD: lineas ordenadas y sin los lanzadores del sistema de quien construye (variables)."""
    out, _ = build(tmp_path)
    record = (out / "jwt-1.dist-info" / "RECORD").read_text(encoding="utf-8")
    assert record == "cryptography/__init__.py,,\njwt/__init__.py,,\n"
