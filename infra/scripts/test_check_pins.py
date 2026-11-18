"""Pruebas de check_pins.py (NFR5.7): cada uses: fijado a un hash con la version comentada."""

from __future__ import annotations

from pathlib import Path

import pytest

import check_pins

SHA = "a" * 40


def test_accepts_sha_with_version_comment() -> None:
    text = f"steps:\n  - uses: actions/checkout@{SHA} # v4.2.2\n"
    assert check_pins.check_workflow_text(text, "ci.yml") == []


def test_rejects_tag() -> None:
    result = check_pins.check_workflow_text("      - uses: actions/checkout@v4\n", "ci.yml")
    assert len(result) == 1 and "ci.yml:1" in result[0]


def test_rejects_short_sha() -> None:
    assert check_pins.check_workflow_text(f"- uses: actions/checkout@{'a' * 39} # v4\n", "ci.yml")


def test_rejects_uppercase_sha() -> None:
    assert check_pins.check_workflow_text(f"- uses: actions/checkout@{'A' * 40} # v4\n", "ci.yml")


def test_rejects_sha_without_version_comment() -> None:
    assert check_pins.check_workflow_text(f"- uses: actions/checkout@{SHA}\n", "ci.yml")


def test_rejects_branch_reference() -> None:
    assert check_pins.check_workflow_text("- uses: hashicorp/setup-terraform@main\n", "ci.yml")


def test_accepts_local_action() -> None:
    assert check_pins.check_workflow_text("- uses: ./.github/actions/algo\n", "ci.yml") == []


def test_ignores_comments_and_run_text() -> None:
    text = "# uses: actions/checkout@v4\n      - run: echo 'uses: foo@v1'\n"
    assert check_pins.check_workflow_text(text, "ci.yml") == []


def test_accepts_quoted_value_and_bare_key() -> None:
    text = f'    uses: "actions/setup-python@{SHA}" # v5.6.0\n'
    assert check_pins.check_workflow_text(text, "ci.yml") == []


def test_docker_reference_needs_digest() -> None:
    assert check_pins.check_workflow_text("- uses: docker://alpine:3.20\n", "ci.yml")
    ok = f"- uses: docker://alpine@sha256:{'b' * 64} # 3.20\n"
    assert check_pins.check_workflow_text(ok, "ci.yml") == []


def test_check_paths_scans_directory_and_reports_every_file(tmp_path: Path) -> None:
    (tmp_path / "a.yml").write_text("- uses: actions/checkout@v4\n", encoding="utf-8")
    (tmp_path / "b.yaml").write_text(f"- uses: actions/checkout@{SHA} # v4\n", encoding="utf-8")
    (tmp_path / "notas.txt").write_text("- uses: x@v1\n", encoding="utf-8")
    result = check_pins.check_paths([tmp_path], [])
    assert len(result) == 1 and "a.yml" in result[0]


def test_missing_required_file_is_a_violation(tmp_path: Path) -> None:
    result = check_pins.check_paths([], [tmp_path / ".terraform.lock.hcl"])
    assert len(result) == 1 and ".terraform.lock.hcl" in result[0]


def test_present_required_file_is_accepted(tmp_path: Path) -> None:
    lock = tmp_path / ".terraform.lock.hcl"
    lock.write_text("# lock\n", encoding="utf-8")
    assert check_pins.check_paths([], [lock]) == []


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = tmp_path / "good.yml"
    good.write_text(f"- uses: actions/checkout@{SHA} # v4\n", encoding="utf-8")
    bad = tmp_path / "bad.yml"
    bad.write_text("- uses: actions/checkout@v4\n", encoding="utf-8")
    assert check_pins.main([str(good)]) == 0
    assert check_pins.main([str(bad)]) == 1
    assert "bad.yml" in capsys.readouterr().out
    assert check_pins.main([str(good), "--require-file", str(tmp_path / "falta.hcl")]) == 1
    assert check_pins.main([str(tmp_path / "no-existe")]) == 2
    assert check_pins.main([]) == 2
