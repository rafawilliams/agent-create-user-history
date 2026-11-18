"""Pruebas de check_secrets.py (NFR5.1). Los patrones de prueba se arman por partes para que este
mismo archivo no se marque a si mismo."""

from __future__ import annotations

from pathlib import Path

import pytest

import check_secrets

AKIA = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
ASIA = "AS" + "IA" + "ABCDEFGHIJKLMNOP"
PRIVATE_KEY = "-----BEGIN " + "RSA PRIVATE KEY-----"
LITERAL_SECRET = "client_" + "secret = " + '"abc123"'


def kinds(text: str) -> list[str]:
    return [kind for _, kind in check_secrets.scan_text(text)]


def test_detects_long_term_access_key() -> None:
    assert kinds(f"key = {AKIA}") == ["clave de acceso de AWS (AKIA)"]


def test_detects_temporary_access_key() -> None:
    assert kinds(f"key = {ASIA}") == ["clave temporal de AWS (ASIA)"]


def test_detects_literal_client_secret() -> None:
    assert kinds(f"  {LITERAL_SECRET}") == ["client_secret literal"]


def test_detects_private_key() -> None:
    assert kinds(PRIVATE_KEY) == ["clave privada"]


def test_does_not_flag_sensitive_flag_or_variable_names() -> None:
    text = "\n".join(
        [
            'variable "google_client_secret" {',
            "  sensitive = true",
            "}",
            "client_secret = var.google_client_secret",
            'google_client_secret = "dummy"',
            "TF_VAR_microsoft_client_secret: ${{ secrets.TF_VAR_microsoft_client_secret }}",
        ]
    )
    assert check_secrets.scan_text(text) == []


def test_reports_line_numbers() -> None:
    assert check_secrets.scan_text(f"uno\ndos\n{AKIA}\n") == [(3, "clave de acceso de AWS (AKIA)")]


def test_scan_paths_reports_file_and_line_without_the_secret(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text(f"x = 1\nkey = {AKIA}\n", encoding="utf-8")
    result = check_secrets.scan_paths([tmp_path])
    assert len(result) == 1
    assert "main.tf:2" in result[0] and AKIA not in result[0]


def test_scan_paths_skips_terraform_dir_lock_file_and_binary(tmp_path: Path) -> None:
    hidden = tmp_path / ".terraform"
    hidden.mkdir()
    (hidden / "x.tf").write_text(AKIA, encoding="utf-8")
    (tmp_path / ".terraform.lock.hcl").write_text(AKIA, encoding="utf-8")
    (tmp_path / "datos.bin").write_bytes(b"\xff\xfe\x00" + AKIA.encode())
    (tmp_path / "limpio.tf").write_text("ok = true\n", encoding="utf-8")
    assert check_secrets.scan_paths([tmp_path]) == []


def test_scan_paths_accepts_a_single_file(tmp_path: Path) -> None:
    path = tmp_path / "a.yml"
    path.write_text(ASIA, encoding="utf-8")
    assert len(check_secrets.scan_paths([path])) == 1


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean = tmp_path / "ok.tf"
    clean.write_text("a = 1\n", encoding="utf-8")
    dirty = tmp_path / "bad.tf"
    dirty.write_text(AKIA, encoding="utf-8")
    assert check_secrets.main([str(clean)]) == 0
    assert check_secrets.main([str(dirty)]) == 1
    assert AKIA not in capsys.readouterr().out
    assert check_secrets.main([str(tmp_path / "no-existe")]) == 2
    assert check_secrets.main([]) == 2
