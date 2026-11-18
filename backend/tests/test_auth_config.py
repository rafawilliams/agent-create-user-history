"""Pruebas de la configuracion del grupo de usuarios y de la lista de correos (entities.md)."""

import pytest

from story_service.auth_config import (
    MAX_ALLOWED_EMAILS,
    IdentityProviderConfig,
    parse_allowed_emails,
)

REGION = "us-east-1"
POOL = "us-east-1_AbC123xyz"
CLIENT = "client-id-de-prueba"


def test_config_derives_issuer_and_keys_url_only_from_region_and_pool():
    config = IdentityProviderConfig(REGION, POOL, CLIENT)

    assert config.issuer == f"https://cognito-idp.{REGION}.amazonaws.com/{POOL}"
    assert config.jwks_url == f"{config.issuer}/.well-known/jwks.json"
    assert CLIENT not in config.jwks_url


@pytest.mark.parametrize(
    ("region", "pool", "client"),
    [
        ("", POOL, CLIENT),
        (REGION, "", CLIENT),
        (REGION, POOL, ""),
        ("   ", POOL, CLIENT),
        (REGION, POOL, "  "),
        (None, POOL, CLIENT),
    ],
)
def test_config_rejects_empty_values(region, pool, client):
    with pytest.raises(ValueError):
        IdentityProviderConfig(region, pool, client)


@pytest.mark.parametrize(
    ("region", "pool"),
    [
        ("us-east-1/../x", POOL),
        ("evil.example.com#", POOL),
        (REGION, "us-east-1_x/../../y"),
        (REGION, "pool con espacios"),
    ],
)
def test_config_rejects_values_that_could_alter_the_keys_address(region, pool):
    with pytest.raises(ValueError):
        IdentityProviderConfig(region, pool, CLIENT)


def test_config_from_env_reads_the_three_values_or_returns_none_when_any_is_missing():
    full = {
        "COGNITO_REGION": REGION,
        "COGNITO_USER_POOL_ID": POOL,
        "COGNITO_APP_CLIENT_ID": CLIENT,
    }

    assert IdentityProviderConfig.from_env(full) == IdentityProviderConfig(REGION, POOL, CLIENT)
    for missing in full:
        partial = {key: value for key, value in full.items() if key != missing}
        assert IdentityProviderConfig.from_env(partial) is None
    assert IdentityProviderConfig.from_env({**full, "COGNITO_APP_CLIENT_ID": "  "}) is None
    assert IdentityProviderConfig.from_env({}) is None


def test_parse_allowed_emails_lowercases_trims_and_removes_duplicates():
    emails = parse_allowed_emails(" Ana@Ejemplo.com, luis@ejemplo.com ,ANA@ejemplo.com ")

    assert emails == frozenset({"ana@ejemplo.com", "luis@ejemplo.com"})


@pytest.mark.parametrize("raw", [None, "", "   ", " , ,"])
def test_parse_allowed_emails_with_nothing_returns_an_empty_set(raw):
    assert parse_allowed_emails(raw) == frozenset()


def test_parse_allowed_emails_accepts_exactly_the_maximum_and_rejects_one_more():
    fifty = ",".join(f"persona{i}@ejemplo.com" for i in range(MAX_ALLOWED_EMAILS))
    fifty_one = fifty + ",extra@ejemplo.com"

    assert len(parse_allowed_emails(fifty)) == 50
    with pytest.raises(ValueError, match="50"):
        parse_allowed_emails(fifty_one)


@pytest.mark.parametrize("raw", ["ana@ejemplo.com,no-es-correo", "ana@ejemplo.com;luis@x.com"])
def test_parse_allowed_emails_rejects_an_entry_that_does_not_look_like_an_email(raw):
    with pytest.raises(ValueError):
        parse_allowed_emails(raw)


def test_dots_and_plus_aliases_are_kept_as_written():
    emails = parse_allowed_emails("a.b+c@gmail.com")

    assert emails == frozenset({"a.b+c@gmail.com"})
