"""Comprobaciones de texto sobre los flujos: retroceso duradero, primer despliegue y versiones."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
REQUIREMENTS = (Path(__file__).with_name("requirements-ci.txt")).read_text(encoding="utf-8")


def test_deploy_passes_live_version_from_the_repository_variable_to_every_terraform_run() -> None:
    """Sin esto el siguiente apply vuelve a promover la version mala (el retroceso no dura)."""
    assert DEPLOY.count("TF_VAR_live_version: ${{ vars.LIVE_VERSION }}") >= 2


def test_rollback_documents_that_the_person_must_set_live_version() -> None:
    step = DEPLOY[DEPLOY.index("Retroceso del alias live") :]
    assert "LIVE_VERSION" in step
    assert "${PREVIOUS_VERSION}" in step


def test_misleading_comment_about_drift_is_gone() -> None:
    assert "el siguiente apply no vuelve a promover" not in DEPLOY


def test_get_alias_distinguishes_first_deploy_from_other_errors() -> None:
    assert "ResourceNotFoundException" in DEPLOY
    assert "2>/dev/null || true" not in DEPLOY


def test_ci_installs_exact_tool_versions_from_the_requirements_file() -> None:
    assert "requirements-ci.txt" in CI
    assert "'pytest>=8'" not in CI


def test_requirements_pin_every_tool_exactly() -> None:
    lines = [ln for ln in REQUIREMENTS.splitlines() if ln.strip() and not ln.startswith("#")]
    names = {ln.split("==")[0] for ln in lines}
    assert {"pytest", "pytest-cov", "black", "ruff"} <= names
    assert all("==" in ln and ">" not in ln and "<" not in ln for ln in lines)
