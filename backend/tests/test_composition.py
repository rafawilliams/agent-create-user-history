"""Composicion del verificador de sesion (BR1.5, NFR5.2): el simulado solo en local o test."""

import pytest

from story_service.config import (
    FailClosedSessionVerifier,
    Settings,
    build_session_verifier,
)
from story_service.fakes import SimulatedSessionVerifier
from story_service.models import Session, SessionInvalid


@pytest.mark.parametrize("app_env", ["local", "test"])
def test_simulated_verifier_is_bound_only_with_local_or_test_and_explicit_flag(app_env):
    settings = Settings.from_env({"APP_ENV": app_env, "ALLOW_SIMULATED_SESSION": "true"})

    verifier = build_session_verifier(settings)

    assert isinstance(verifier, SimulatedSessionVerifier)
    assert isinstance(verifier.verify_session("cualquier-cosa"), Session)


@pytest.mark.parametrize("app_env", ["prod", "production", "staging", "dev", "", "LOCAL "])
def test_other_environments_never_bind_the_simulated_verifier(app_env):
    settings = Settings.from_env({"APP_ENV": app_env, "ALLOW_SIMULATED_SESSION": "true"})

    verifier = build_session_verifier(settings)

    assert isinstance(verifier, FailClosedSessionVerifier)


def test_without_the_explicit_flag_even_local_fails_closed():
    verifier = build_session_verifier(Settings.from_env({"APP_ENV": "local"}))

    assert isinstance(verifier, FailClosedSessionVerifier)


def test_default_settings_fail_closed():
    verifier = build_session_verifier(Settings.from_env({}))

    assert isinstance(verifier, FailClosedSessionVerifier)
    assert Settings.from_env({}).allow_simulated_session is False


@pytest.mark.parametrize("value", ["false", "0", "no", "", "talvez"])
def test_non_true_flag_values_are_false(value):
    settings = Settings.from_env({"APP_ENV": "local", "ALLOW_SIMULATED_SESSION": value})

    assert settings.allow_simulated_session is False


def test_fail_closed_verifier_rejects_everything_including_valid_looking_tokens():
    verifier = FailClosedSessionVerifier()

    for credential in ("", "Bearer abc", "token-valido"):
        assert isinstance(verifier.verify_session(credential), SessionInvalid)


def test_settings_read_model_region_cors_and_instructions_from_environment():
    settings = Settings.from_env(
        {
            "BEDROCK_MODEL_ID": "us.amazon.titan-text-premier-v1:0",
            "BEDROCK_REGION": "us-east-1",
            "CORS_ALLOWED_ORIGIN": "https://ejemplo.cloudfront.net",
            "STORY_INSTRUCTIONS": "Instrucciones propias",
        }
    )

    assert settings.model_id == "us.amazon.titan-text-premier-v1:0"
    assert settings.region == "us-east-1"
    assert settings.cors_allowed_origin == "https://ejemplo.cloudfront.net"
    assert settings.instructions == "Instrucciones propias"
