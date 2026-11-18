"""Pruebas de la lista de correos permitidos (BR4.3, NFR5.3, NFR5.6)."""

import pytest

from story_service.account_allowlist import AccountAllowlist, is_verified_email


def allowlist(raw):
    return AccountAllowlist({"ALLOWED_EMAILS": raw})


def test_a_listed_email_is_allowed_whatever_its_capitalization():
    accounts = allowlist("ana.perez@ejemplo.com, Luis@Ejemplo.com")

    assert accounts.is_allowed("ana.perez@ejemplo.com")
    assert accounts.is_allowed("ANA.PEREZ@EJEMPLO.COM")
    assert accounts.is_allowed("luis@ejemplo.com")


def test_an_unlisted_email_is_not_allowed():
    assert not allowlist("ana@ejemplo.com").is_allowed("otra@ejemplo.com")


@pytest.mark.parametrize(
    "candidate",
    ["a.na@gmail.com", "ana+x@gmail.com", "an.a+x@gmail.com", "ana@googlemail.com"],
)
def test_gmail_dots_and_plus_aliases_do_not_match(candidate):
    assert not allowlist("ana@gmail.com").is_allowed(candidate)


@pytest.mark.parametrize("candidate", [None, "", "   ", 5, ["ana@ejemplo.com"]])
def test_an_absent_or_non_text_email_is_never_allowed(candidate):
    assert not allowlist("ana@ejemplo.com").is_allowed(candidate)


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_an_empty_list_lets_nobody_in(raw):
    accounts = allowlist(raw)

    assert accounts.emails() == frozenset()
    assert not accounts.is_allowed("ana@ejemplo.com")


def test_a_list_of_50_is_read_and_a_list_of_51_is_a_configuration_error():
    fifty = ",".join(f"p{n}@ejemplo.com" for n in range(50))

    assert len(allowlist(fifty).emails()) == 50
    with pytest.raises(ValueError):
        allowlist(fifty + ",p50@ejemplo.com").emails()


def test_an_entry_that_is_not_an_email_is_a_configuration_error():
    with pytest.raises(ValueError):
        allowlist("ana@ejemplo.com,esto-no-es-correo").emails()


def test_the_list_is_read_from_the_environment_on_every_request():
    env = {"ALLOWED_EMAILS": "ana@ejemplo.com,luis@ejemplo.com"}
    accounts = AccountAllowlist(env)
    assert accounts.is_allowed("luis@ejemplo.com")

    env["ALLOWED_EMAILS"] = "ana@ejemplo.com"  # se quita un correo entre dos solicitudes

    assert not accounts.is_allowed("luis@ejemplo.com")
    assert accounts.is_allowed("ana@ejemplo.com")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, True), (False, False), (None, False), ("true", False), (1, False), (0, False)],
)
def test_only_the_boolean_true_counts_as_a_verified_email(value, expected):
    assert is_verified_email(value) is expected
