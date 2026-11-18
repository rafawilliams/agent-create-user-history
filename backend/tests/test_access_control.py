"""Pruebas del control de acceso en el servicio: composicion, fallo cerrado, errores y registros."""

import json
import logging
import pathlib
import re

import pytest

from story_service.config import FailClosedSessionVerifier, Settings, build_session_verifier
from story_service.errors import ErrorCode, ServiceError
from story_service.fakes import FakeModelClient, SimulatedSessionVerifier
from story_service.models import ModelResponse, Session
from story_service.service import StoryService
from story_service.token_verifier import CognitoSessionVerifier
from tests.auth_helpers import (
    CLIENT,
    EMAIL,
    NOW,
    OTHER_PRIVATE_KEY,
    POOL,
    REGION,
    FakeKeyServer,
    hs256_token,
    make_store,
    sign,
    unsigned_token,
    valid_claims,
)
from tests.helpers import VALID_JSON, FakeClock

TITLE = "Recuperar contraseña de la cuenta"
COGNITO_ENV = {
    "APP_ENV": "prod",
    "COGNITO_REGION": REGION,
    "COGNITO_USER_POOL_ID": POOL,
    "COGNITO_APP_CLIENT_ID": CLIENT,
    "ALLOWED_EMAILS": f"{EMAIL},otra.persona@ejemplo.com",
}


def make_service(env=None, server=None, model=None):
    env = dict(COGNITO_ENV if env is None else env)
    server = server or FakeKeyServer()
    model = model or FakeModelClient([ModelResponse(VALID_JSON, "m-1")])
    verifier = build_session_verifier(
        Settings.from_env(env), env, jwks_store=make_store(server), clock=lambda: NOW
    )
    service = StoryService(verifier, model, "INSTRUCCIONES", clock=FakeClock(), model_id="m-1")
    return service, model, server, env


def rejection(service, token):
    with pytest.raises(ServiceError) as caught:
        service.generate(token, TITLE)
    return caught.value


# --- Composicion (BR4.5, NFR1.6, NFR1.7) ---


def test_the_real_verifier_is_used_when_the_cognito_configuration_is_present():
    env = {**COGNITO_ENV, "APP_ENV": "prod"}

    verifier = build_session_verifier(Settings.from_env(env), env)

    assert isinstance(verifier, CognitoSessionVerifier)


def test_the_simulated_verifier_is_never_used_with_the_real_configuration():
    env = {**COGNITO_ENV, "APP_ENV": "local", "ALLOW_SIMULATED_SESSION": "true"}

    verifier = build_session_verifier(Settings.from_env(env), env)

    assert isinstance(verifier, CognitoSessionVerifier)
    assert not isinstance(verifier, SimulatedSessionVerifier)


def test_local_with_the_flag_and_no_cognito_configuration_still_uses_the_simulated_one():
    env = {"APP_ENV": "local", "ALLOW_SIMULATED_SESSION": "true"}

    assert isinstance(build_session_verifier(Settings.from_env(env), env), SimulatedSessionVerifier)


@pytest.mark.parametrize(
    "missing", ["COGNITO_REGION", "COGNITO_USER_POOL_ID", "COGNITO_APP_CLIENT_ID", "ALLOWED_EMAILS"]
)
def test_an_incomplete_configuration_in_a_deployed_env_fails_closed(missing):
    env = {key: value for key, value in COGNITO_ENV.items() if key != missing}
    env["ALLOW_SIMULATED_SESSION"] = "true"  # la bandera no basta fuera de local o test
    service, model, _, _ = make_service(env)

    error = rejection(service, sign())

    assert (error.code, error.http_status) == (ErrorCode.SESSION_INVALID, 401)
    assert model.calls == []


def test_a_cognito_value_with_a_broken_format_counts_as_missing_configuration():
    env = {**COGNITO_ENV, "COGNITO_REGION": "us-east-1/../evil"}

    settings = Settings.from_env(env)

    assert settings.identity is None
    assert isinstance(build_session_verifier(settings, env), FailClosedSessionVerifier)


def test_without_any_configuration_every_request_is_rejected_and_the_model_is_not_called():
    service, model, server, _ = make_service({"APP_ENV": "prod"})

    for token in (sign(), "", "basura"):
        assert rejection(service, token).code == ErrorCode.SESSION_INVALID

    assert model.calls == []
    assert server.calls == 0


# --- Respuestas (NFR4.4) ---


def test_a_valid_token_of_an_allowed_account_generates_the_story():
    service, model, _, _ = make_service()

    result = service.generate(sign(), TITLE)

    assert result.markdown.startswith("# ")
    assert len(model.calls) == 1


def _rejected_tokens():
    return {
        "missing": "",
        "malformed": "abc.def",
        "none": unsigned_token(),
        "hs256": hs256_token(),
        "firma": sign(key=OTHER_PRIVATE_KEY),
        "kid": sign(kid="kid-ajeno"),
        "emisor": sign(valid_claims(iss="https://otro.example/pool")),
        "audiencia": sign(valid_claims(aud="otro")),
        "tipo": sign(valid_claims(token_use="access")),
        "vencido": sign(valid_claims(exp=int(NOW) - 600)),
    }


def test_every_token_rejection_reason_returns_the_same_401_session_invalid_body():
    bodies = {}
    for name, token in _rejected_tokens().items():
        service, model, _, _ = make_service()
        error = rejection(service, token)
        body = error.to_body()
        body.pop("requestId")
        bodies[name] = (error.http_status, json.dumps(body, sort_keys=True))
        assert model.calls == []

    assert len(set(bodies.values())) == 1, bodies
    assert next(iter(bodies.values()))[0] == 401
    assert json.loads(next(iter(bodies.values()))[1])["code"] == "SESSION_INVALID"


def test_keys_unavailable_returns_the_same_401_body_as_any_other_rejection():
    down = FakeKeyServer()
    down.error = TimeoutError("caído")
    service, _, _, _ = make_service(server=down)
    reference = rejection(make_service()[0], "abc.def").to_body()

    unavailable = rejection(service, sign()).to_body()

    for body in (reference, unavailable):
        body.pop("requestId")
    assert unavailable == reference


def test_a_token_of_an_account_not_in_the_list_returns_403_account_not_allowed():
    service, model, _, _ = make_service()
    token = sign(valid_claims(email="intrusa@ejemplo.com"))

    error = rejection(service, token)

    assert (error.code, error.http_status, error.retryable) == (
        ErrorCode.ACCOUNT_NOT_ALLOWED,
        403,
        False,
    )
    assert error.message and error.message != rejection(service, "").message
    assert "intrusa" not in error.message
    assert model.calls == []


def test_an_unverified_email_is_account_not_allowed_not_session_invalid():
    service, _, _, _ = make_service()

    error = rejection(service, sign(valid_claims(email_verified=False)))

    assert error.code == ErrorCode.ACCOUNT_NOT_ALLOWED


def test_removing_an_email_from_the_list_cuts_access_on_the_next_request_with_the_same_token():
    service, _, _, env = make_service()
    token = sign()
    assert service.generate(token, TITLE).markdown

    env["ALLOWED_EMAILS"] = "otra.persona@ejemplo.com"

    assert rejection(service, token).code == ErrorCode.ACCOUNT_NOT_ALLOWED


def test_an_error_inside_the_verifier_fails_closed_with_the_reason_unknown(caplog):
    class Exploding:
        def verify_session(self, credential):
            raise RuntimeError("defecto interno")

    model = FakeModelClient([ModelResponse(VALID_JSON, "m-1")])
    service = StoryService(Exploding(), model, "I", clock=FakeClock(), model_id="m-1")
    caplog.set_level(logging.INFO, logger="story_service")

    error = rejection(service, "token")

    assert error.code == ErrorCode.SESSION_INVALID
    assert model.calls == []
    assert _request_record(caplog)["authOutcome"] == "unknown"


def test_valid_and_invalid_tokens_interleaved_do_not_affect_each_other():
    service, model, _, _ = make_service()
    good, bad = sign(), sign(key=OTHER_PRIVATE_KEY)

    outcomes = []
    for token in (good, bad, good, "", good, bad):
        try:
            service.generate(token, TITLE)
            outcomes.append("ok")
        except ServiceError as error:
            outcomes.append(error.code.value)

    assert outcomes == ["ok", "SESSION_INVALID", "ok", "SESSION_INVALID", "ok", "SESSION_INVALID"]
    assert len(model.calls) == 3


# --- Sesion: GET y DELETE de C2 ---


def test_get_session_returns_the_session_and_rejects_invalid_or_not_allowed_credentials():
    service, _, _, _ = make_service()

    session = service.get_session(sign())

    assert isinstance(session, Session)
    assert session.account_id == "sub-de-prueba-1"
    with pytest.raises(ServiceError) as invalid:
        service.get_session("")
    with pytest.raises(ServiceError) as not_allowed:
        service.get_session(sign(valid_claims(email="intrusa@ejemplo.com")))
    assert (invalid.value.http_status, not_allowed.value.http_status) == (401, 403)


def test_end_session_accepts_a_valid_session_and_rejects_the_others():
    service, _, _, _ = make_service()

    assert service.end_session(sign()) is None
    with pytest.raises(ServiceError) as invalid:
        service.end_session("basura")
    with pytest.raises(ServiceError) as not_allowed:
        service.end_session(sign(valid_claims(email_verified=None)))
    assert (invalid.value.http_status, not_allowed.value.http_status) == (401, 403)


# --- Registros y metricas (BR4.8, NFR4.2, NFR4.5, NFR4.6, NFR4.7, NFR1.9) ---


def _records(caplog):
    return [json.loads(record.getMessage()) for record in caplog.records]


def _request_record(caplog):
    return next(item for item in _records(caplog) if "requestId" in item)


def test_the_request_log_carries_auth_outcome_and_duration_for_a_valid_token(caplog):
    caplog.set_level(logging.INFO, logger="story_service")
    service, _, _, _ = make_service()

    service.generate(sign(), TITLE)

    record = _request_record(caplog)
    assert record["authOutcome"] == "ok"
    assert isinstance(record["authDurationMs"], int) and record["authDurationMs"] >= 0
    assert record["outcome"] == "ok"


@pytest.mark.parametrize(
    ("token", "outcome", "code"),
    [
        ("", "missing", "SESSION_INVALID"),
        ("abc.def", "malformed", "SESSION_INVALID"),
        (sign(key=OTHER_PRIVATE_KEY), "bad_signature", "SESSION_INVALID"),
        (sign(valid_claims(iss="https://x.example/p")), "wrong_issuer", "SESSION_INVALID"),
        (sign(valid_claims(aud="otro")), "wrong_audience", "SESSION_INVALID"),
        (sign(valid_claims(token_use="access")), "wrong_token_use", "SESSION_INVALID"),
        (sign(valid_claims(exp=int(NOW) - 600)), "expired", "SESSION_INVALID"),
        (sign(valid_claims(email="x@ejemplo.com")), "account_not_allowed", "ACCOUNT_NOT_ALLOWED"),
    ],
)
def test_each_rejection_logs_its_reason_and_counts_errors_total_with_the_code(
    caplog, token, outcome, code
):
    caplog.set_level(logging.INFO, logger="story_service")
    service, _, _, _ = make_service()

    rejection(service, token)

    records = _records(caplog)
    assert _request_record(caplog)["authOutcome"] == outcome
    assert {"metric": "errors_total", "value": 1, "code": code} in records


def test_keys_unavailable_and_not_configured_are_distinct_outcomes_in_the_log(caplog):
    caplog.set_level(logging.INFO, logger="story_service")
    down = FakeKeyServer()
    down.error = TimeoutError("caído")
    unavailable_service, _, _, _ = make_service(server=down)
    rejection(unavailable_service, sign())
    first = _request_record(caplog)["authOutcome"]
    caplog.clear()
    unconfigured_service, _, _, _ = make_service({"APP_ENV": "prod"})
    rejection(unconfigured_service, sign())
    second = _request_record(caplog)["authOutcome"]

    assert (first, second) == ("keys_unavailable", "not_configured")


def test_no_log_line_contains_the_token_the_email_the_sub_or_the_allowlist(caplog):
    caplog.set_level(logging.INFO, logger="story_service")
    service, _, _, _ = make_service()
    token = sign()
    cases = [token, sign(valid_claims(email="intrusa@ejemplo.com")), "abc.def", ""]
    for case in cases:
        try:
            service.generate(case, TITLE)
        except ServiceError:
            pass
    service.get_session(token)

    text = "\n".join(record.getMessage() for record in caplog.records)
    secrets = [
        token,
        token.split(".")[1],
        EMAIL,
        "intrusa@ejemplo.com",
        "otra.persona@ejemplo.com",
        "sub-de-prueba-1",
        "jti-de-prueba-1",
        "ejemplo.com",
    ]
    for secret in secrets:
        assert secret not in text, secret


_U4_FILES = (
    "story_service/auth_config.py",
    "story_service/jwks_store.py",
    "story_service/token_verifier.py",
    "story_service/account_allowlist.py",
    "story_service/config.py",
    "story_service/service.py",
    "story_service/handler.py",
    ".env.example",
)
_SECRET_PATTERNS = (
    r"AKIA[0-9A-Z]{16}",
    r"ASIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i)aws_secret_access_key\s*[=:]\s*\S{20,}",
    r"(?i)(client_secret|password|api_key)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",  # un token literal
)


def test_u4_code_and_configuration_contain_no_value_shaped_like_a_secret():
    root = pathlib.Path(__file__).resolve().parents[1]

    for name in _U4_FILES:
        text = (root / name).read_text(encoding="utf-8")
        for pattern in _SECRET_PATTERNS:
            assert not re.search(pattern, text), f"{name} coincide con {pattern}"


def test_a_failed_verifier_never_leaves_the_composition_without_a_fail_closed_default():
    assert isinstance(build_session_verifier(Settings.from_env({}), {}), FailClosedSessionVerifier)
