"""Pruebas de la verificacion de tokens de Cognito con claves y tokens de prueba (BR4.2, BR4.4)."""

import statistics
import time
import warnings

import jwt
import pytest
from jwt.api_jws import encode as jws_encode

from story_service.account_allowlist import AccountAllowlist
from story_service.models import Session, SessionInvalid
from story_service.token_verifier import CognitoSessionVerifier
from tests.auth_helpers import (
    CONFIG,
    EIGHT_HOURS,
    EMAIL,
    KID,
    NOW,
    OTHER_PRIVATE_KEY,
    PRIVATE_KEY,
    FakeClock,
    FakeKeyServer,
    hs256_token,
    jwk_for,
    jwks_bytes,
    make_store,
    sign,
    unsigned_token,
    valid_claims,
)


def build(server=None, env=None, now=NOW):
    server = server or FakeKeyServer()
    allowed_env = {"ALLOWED_EMAILS": EMAIL} if env is None else env
    verifier = CognitoSessionVerifier(
        CONFIG, make_store(server), AccountAllowlist(allowed_env), clock=lambda: now
    )
    return verifier, server


def reason_of(result) -> str:
    assert isinstance(result, SessionInvalid), result
    return result.reason


def test_a_valid_token_returns_the_session_with_the_four_c3_fields():
    verifier, _ = build()

    session = verifier.verify_session(sign())

    assert isinstance(session, Session)
    assert session.session_id == "jti-de-prueba-1"
    assert session.account_id == "sub-de-prueba-1"
    assert session.provider == "google"
    # el menor entre exp y auth_time + 8 horas
    assert session.expires_at == time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(NOW) + 3600))


def test_session_id_falls_back_to_sub_and_microsoft_is_recognised():
    verifier, _ = build()
    claims = valid_claims(jti=None, identities=[{"providerName": "Microsoft"}])

    session = verifier.verify_session(sign(claims))

    assert (session.session_id, session.provider) == ("sub-de-prueba-1", "microsoft")


def test_expires_at_is_capped_at_eight_hours_from_auth_time():
    verifier, _ = build()
    auth_time = int(NOW) - 7 * 3600
    claims = valid_claims(auth_time=auth_time, exp=int(NOW) + 5 * 3600, iat=int(NOW) - 60)

    session = verifier.verify_session(sign(claims))

    assert session.expires_at == time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(auth_time + EIGHT_HOURS)
    )


@pytest.mark.parametrize("credential", ["", "   ", None])
def test_no_credential_is_missing(credential):
    verifier, server = build()

    assert reason_of(verifier.verify_session(credential)) == "missing"
    assert server.calls == 0


@pytest.mark.parametrize("credential", ["abc", "a.b", "a.b.c.d", "...", "!!!.@@@.###"])
def test_a_credential_without_the_shape_of_a_token_is_malformed(credential):
    verifier, server = build()

    assert reason_of(verifier.verify_session(credential)) == "malformed"
    assert server.calls == 0


@pytest.mark.parametrize(
    "token",
    [
        unsigned_token(),
        hs256_token(),
        sign(algorithm="RS384"),
        sign(kid=None),
    ],
    ids=["none", "hs256", "rs384", "sin-kid"],
)
def test_wrong_algorithm_or_missing_kid_is_bad_signature_before_any_key_is_looked_up(token):
    verifier, server = build()

    assert reason_of(verifier.verify_session(token)) == "bad_signature"
    assert server.calls == 0  # el encabezado no puede elegir el metodo ni provocar una descarga


def test_unknown_kid_after_a_successful_download_is_bad_signature():
    verifier, server = build()

    assert reason_of(verifier.verify_session(sign(kid="kid-ajeno"))) == "bad_signature"
    assert server.calls == 1


def test_unknown_kid_with_keys_unavailable_and_no_copy_is_keys_unavailable():
    server = FakeKeyServer()
    server.error = TimeoutError("caído")
    verifier, _ = build(server)

    assert reason_of(verifier.verify_session(sign())) == "keys_unavailable"


def test_a_signature_made_with_another_key_or_a_swapped_signature_is_bad_signature():
    verifier, _ = build()
    forged = sign(key=OTHER_PRIVATE_KEY)
    header, payload, _ = sign().split(".")
    swapped = f"{header}.{payload}.{sign(valid_claims(sub='otra')).split('.')[2]}"

    assert reason_of(verifier.verify_session(forged)) == "bad_signature"
    assert reason_of(verifier.verify_session(swapped)) == "bad_signature"


@pytest.mark.parametrize("payload", [b"[1, 2]", b"no es json", b'"texto"'])
def test_a_validly_signed_payload_that_is_not_a_json_object_is_malformed(payload):
    verifier, _ = build()
    token = jws_encode(payload, PRIVATE_KEY, algorithm="RS256", headers={"kid": KID})

    assert reason_of(verifier.verify_session(token)) == "malformed"


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Otro"}, "wrong_issuer"),
        ({"iss": None}, "wrong_issuer"),
        ({"aud": "otro-cliente"}, "wrong_audience"),
        ({"aud": None}, "wrong_audience"),
        ({"token_use": "access"}, "wrong_token_use"),
        ({"token_use": None}, "wrong_token_use"),
    ],
)
def test_issuer_audience_and_token_use_must_match(override, expected):
    verifier, _ = build()

    assert reason_of(verifier.verify_session(sign(valid_claims(**override)))) == expected


@pytest.mark.parametrize(
    ("override", "accepted"),
    [
        ({"exp": int(NOW) - 59}, True),
        ({"exp": int(NOW) - 61}, False),
        ({"exp": None}, False),
        ({"iat": int(NOW) + 59}, True),
        ({"iat": int(NOW) + 61, "auth_time": None}, False),
        ({"iat": None, "nbf": int(NOW) - 5}, True),
        ({"iat": None, "nbf": int(NOW) + 59}, True),
        ({"iat": None, "nbf": int(NOW) + 61}, False),
        ({"iat": None, "nbf": None}, False),
        ({"auth_time": int(NOW) - EIGHT_HOURS - 1, "exp": int(NOW) + 3600}, False),
        ({"auth_time": int(NOW) - EIGHT_HOURS + 30}, True),
        ({"auth_time": None, "iat": int(NOW) - EIGHT_HOURS - 1}, False),
        ({"auth_time": None, "iat": int(NOW) - EIGHT_HOURS + 30}, True),
    ],
)
def test_dates_use_a_60_second_tolerance_and_an_eight_hour_cap(override, accepted):
    verifier, _ = build()

    result = verifier.verify_session(sign(valid_claims(**override)))

    if accepted:
        assert isinstance(result, Session)
    else:
        assert reason_of(result) == "expired"


def test_a_token_with_no_subject_is_malformed():
    verifier, _ = build()

    assert reason_of(verifier.verify_session(sign(valid_claims(sub=None)))) == "malformed"


def test_an_unexpected_internal_error_fails_closed_with_the_reason_unknown():
    verifier, _ = build()

    def boom(kid):
        raise RuntimeError("defecto interno con datos sensibles")

    verifier._jwks.get_key = boom

    assert reason_of(verifier.verify_session(sign())) == "unknown"


def test_a_missing_or_broken_allowlist_is_not_configured():
    for env in ({}, {"ALLOWED_EMAILS": ""}, {"ALLOWED_EMAILS": "no-es-correo"}):
        verifier, server = build(env=env)

        assert reason_of(verifier.verify_session(sign())) == "not_configured"
        assert server.calls == 0


def test_a_garbled_part_after_the_key_lookup_is_malformed_or_bad_signature(monkeypatch):
    verifier, _ = build()
    header, payload, signature = sign().split(".")

    assert reason_of(verifier.verify_session(f"{header}.a.{signature}")) == "malformed"
    assert reason_of(verifier.verify_session(f"{header}.{payload}.!!!")) == "bad_signature"

    def refuse(*args, **kwargs):
        raise jwt.InvalidTokenError("otro defecto de la biblioteca")

    monkeypatch.setattr("story_service.token_verifier.decode_complete", refuse)
    assert reason_of(verifier.verify_session(sign())) == "bad_signature"


def test_a_provider_that_is_not_google_or_microsoft_fails_closed():
    verifier, _ = build()

    for identities in (None, [], [{"providerName": "Facebook"}], [{"providerName": 5}], "texto"):
        token = sign(valid_claims(identities=identities))
        assert reason_of(verifier.verify_session(token)) == "unknown"


def test_verification_with_keys_in_memory_is_under_20_ms_median_and_makes_no_network_calls():
    verifier, server = build()
    token = sign()
    for _ in range(5):  # calentamiento (la primera llamada descarga las claves)
        verifier.verify_session(token)
    server.urls.clear()

    medians = []
    for _attempt in range(3):  # el maximo solo avisa; la mediana decide, con hasta 3 intentos
        samples = []
        for _ in range(20):
            started = time.perf_counter()
            result = verifier.verify_session(token)
            samples.append((time.perf_counter() - started) * 1000)
        assert isinstance(result, Session)
        medians.append(statistics.median(samples))
        if medians[-1] < 20:
            break

    assert medians[-1] < 20, medians
    assert server.calls == 0
    if max(samples) >= 20:  # el maximo solo avisa
        warnings.warn(
            f"una verificacion tardo {max(samples):.1f} ms (decide la mediana)", stacklevel=2
        )


def test_the_kid_rule_a_valid_copy_with_the_kid_is_used_even_if_the_server_is_down():
    server = FakeKeyServer()
    verifier, _ = build(server)
    assert isinstance(verifier.verify_session(sign()), Session)
    server.error = OSError("caído")
    server.urls.clear()

    assert isinstance(verifier.verify_session(sign()), Session)
    assert server.calls == 0


def test_a_rotated_key_is_picked_up_by_one_refresh_after_a_minute():
    server = FakeKeyServer(jwks_bytes(jwk_for(OTHER_PRIVATE_KEY, kid="kid-viejo")))
    clock = FakeClock()
    verifier = CognitoSessionVerifier(
        CONFIG,
        make_store(server, clock),
        AccountAllowlist({"ALLOWED_EMAILS": EMAIL}),
        clock=lambda: NOW,
    )
    assert reason_of(verifier.verify_session(sign())) == "bad_signature"
    server.body = jwks_bytes(
        jwk_for(OTHER_PRIVATE_KEY, kid="kid-viejo"), jwk_for(PRIVATE_KEY, kid=KID)
    )
    clock.advance(61)

    assert isinstance(verifier.verify_session(sign()), Session)
    assert server.calls == 2


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("claim", ["exp", "iat", "nbf"])
def test_non_finite_dates_never_disable_the_expiry_checks(claim, value):
    # json.loads turns NaN/Infinity into floats; a comparison with NaN is always false, which
    # would silently skip the expiry check (review finding).
    verifier, _ = build()
    claims = valid_claims(**{claim: value})
    if claim == "iat":
        claims.pop("auth_time")

    result = verifier.verify_session(sign(claims))

    assert reason_of(result) == "expired"


def test_a_non_finite_auth_time_falls_back_to_iat_for_the_eight_hour_cap():
    verifier, _ = build()
    claims = valid_claims(auth_time=float("nan"), iat=int(NOW) - 9 * 3600, exp=int(NOW) + 3600)

    assert reason_of(verifier.verify_session(sign(claims))) == "expired"


def test_a_crit_header_is_rejected_because_critical_extensions_are_not_supported():
    verifier, _ = build()
    token = jwt.encode(
        valid_claims(), PRIVATE_KEY, algorithm="RS256", headers={"kid": KID, "crit": ["exp"]}
    )

    assert reason_of(verifier.verify_session(token)) == "bad_signature"


@pytest.mark.parametrize(
    "extra", [{"jku": "https://atacante.example/jwks"}, {"x5u": "https://atacante.example/x"}]
)
def test_jku_and_x5u_headers_never_change_where_the_key_comes_from(extra):
    verifier, server = build()
    token = jwt.encode(
        valid_claims(), PRIVATE_KEY, algorithm="RS256", headers={"kid": KID, **extra}
    )

    assert isinstance(verifier.verify_session(token), Session)
    assert server.calls == 1


@pytest.mark.parametrize("name", ["GoogleOtro", "microsoft-corp", "Facebook", ""])
def test_the_provider_name_must_be_exactly_google_or_microsoft(name):
    verifier, _ = build()
    claims = valid_claims(identities=[{"providerName": name}])

    assert reason_of(verifier.verify_session(sign(claims))) == "unknown"
