"""Pruebas del perfil de modelo: lista cerrada de identificadores (BR2.1, BR2.2, NFR5.3)."""

import pytest

from story_service.config import DEFAULT_MODEL_ID, Settings
from story_service.model_profile import InvalidModelIdError, ModelProfile

TITAN_ID = "us.amazon.titan-text-premier-v1:0"


@pytest.mark.parametrize(
    ("model_id", "provider"),
    [
        ("us.anthropic.claude-sonnet-4-6", "anthropic"),
        ("global.anthropic.claude-sonnet-4-6", "anthropic"),
        ("anthropic.claude-3-haiku-20240307-v1:0", "anthropic"),
        ("us.amazon.titan-text-premier-v1:0", "amazon"),
        ("amazon.titan-text-express-v1", "amazon"),
    ],
)
def test_supported_identifiers_are_accepted_and_the_provider_is_deduced(model_id, provider):
    profile = ModelProfile.from_model_id(model_id)

    assert profile.model_id == model_id
    assert profile.provider == provider
    assert profile.region == "us-east-1"


def test_region_is_kept_from_configuration():
    assert ModelProfile.from_model_id("us.anthropic.claude-sonnet-4-6", "us-west-2").region == (
        "us-west-2"
    )


@pytest.mark.parametrize(
    "model_id",
    [
        "us.meta.llama3-70b-instruct-v1:0",  # otro proveedor
        "us.anthropic.claud-sonnet-4-6",  # error de escritura dentro de un proveedor valido
        "eu.anthropic.claude-sonnet-4-6",  # prefijo fuera de la lista
        "global.amazon.titan-text-premier-v1:0",  # global solo existe para anthropic
        "us.anthropic.claude-",  # sin resto
        "us.anthropic.claude-sonnet 4",  # caracter no permitido
        "us.anthropic.claude-sonnet-4-6\n",  # salto de linea final
        "",
        "   ",
    ],
)
def test_unsupported_identifiers_are_rejected_naming_the_value(model_id):
    with pytest.raises(InvalidModelIdError) as caught:
        ModelProfile.from_model_id(model_id)

    assert repr(model_id) in str(caught.value) or model_id.strip() == ""
    assert isinstance(caught.value, ValueError)


def test_non_text_identifier_is_rejected():
    with pytest.raises(InvalidModelIdError):
        ModelProfile.from_model_id(None)  # type: ignore[arg-type]


# ---- Settings: modelo, region y tiempos de espera por configuracion (BR2.1, BR2.2, NFR1.2) ----


def test_settings_without_configuration_use_the_default_model_and_50_seconds():
    settings = Settings.from_env({})

    assert settings.model_id == DEFAULT_MODEL_ID == "us.anthropic.claude-sonnet-4-6"
    assert settings.region == "us-east-1"
    assert settings.timeout_seconds == 50.0


def test_settings_take_model_region_and_per_model_timeouts_from_the_environment():
    claude = Settings.from_env(
        {
            "BEDROCK_MODEL_ID": "global.anthropic.claude-sonnet-4-6",
            "BEDROCK_REGION": "us-west-2",
            "BEDROCK_TIMEOUT_SECONDS_CLAUDE": "40.5",
            "BEDROCK_TIMEOUT_SECONDS_TITAN": "20",
        }
    )
    titan = Settings.from_env({"BEDROCK_MODEL_ID": TITAN_ID, "BEDROCK_TIMEOUT_SECONDS_TITAN": "20"})

    assert (claude.model_id, claude.region, claude.timeout_seconds) == (
        "global.anthropic.claude-sonnet-4-6",
        "us-west-2",
        40.5,
    )
    assert (titan.provider, titan.timeout_seconds) == ("amazon", 20.0)


def test_unsupported_model_fails_when_building_settings_without_calling_aws(monkeypatch):
    import boto3

    def forbidden(*args, **kwargs):
        raise AssertionError("no debe llamarse a AWS")

    monkeypatch.setattr(boto3, "client", forbidden)

    with pytest.raises(InvalidModelIdError, match="us.meta.llama3"):
        Settings.from_env({"BEDROCK_MODEL_ID": "us.meta.llama3-70b-instruct-v1:0"})


@pytest.mark.parametrize("value", ["abc", "0", "-5", "nan", "inf"])
def test_invalid_timeout_fails_naming_the_variable(value):
    with pytest.raises(ValueError, match="BEDROCK_TIMEOUT_SECONDS_CLAUDE"):
        Settings.from_env({"BEDROCK_TIMEOUT_SECONDS_CLAUDE": value})


def test_empty_model_variable_falls_back_to_the_default():
    assert Settings.from_env({"BEDROCK_MODEL_ID": ""}).model_id == DEFAULT_MODEL_ID


def test_empty_region_is_rejected():
    with pytest.raises(ValueError):
        ModelProfile.from_model_id("us.anthropic.claude-sonnet-4-6", "")
