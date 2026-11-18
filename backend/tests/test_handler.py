"""Pruebas del limite de la API: manejador de la funcion detras de la pasarela REST (C1)."""

import json

import pytest

from story_service.config import FailClosedSessionVerifier, Settings
from story_service.fakes import FakeModelClient, SimulatedSessionVerifier
from story_service.handler import create_handler
from story_service.models import ModelError, ModelErrorKind, ModelResponse, Session, SessionInvalid
from story_service.service import StoryService
from tests.helpers import VALID_JSON

# u3 (BR3.2): un titulo de una palabra pide contexto; estas pruebas de u1 usan un titulo suficiente.
TITLE = "Titulo de prueba valido"

ORIGIN = "https://d111111abcdef8.cloudfront.net"
SETTINGS = Settings.from_env({"CORS_ALLOWED_ORIGIN": ORIGIN})


class Context:
    def __init__(self, remaining_ms: int = 60000) -> None:
        self._remaining_ms = remaining_ms

    def get_remaining_time_in_millis(self) -> int:
        return self._remaining_ms


class RecordingVerifier(SimulatedSessionVerifier):
    def __init__(self) -> None:
        self.credentials: list[str] = []

    def verify_session(self, credential):
        self.credentials.append(credential)
        return super().verify_session(credential)


def make_event(body=None, headers=None, method="POST"):
    return {
        "httpMethod": method,
        "path": "/v1/stories",
        "headers": {"Authorization": "Bearer token-123", **(headers or {})},
        "body": json.dumps(body) if not isinstance(body, str) and body is not None else body,
    }


def make_handler(results=None, verifier=None, settings=SETTINGS):
    model = FakeModelClient(results=results or [ModelResponse(VALID_JSON, "m-1")])
    service = StoryService(
        verifier or SimulatedSessionVerifier(), model, "INSTRUCCIONES", model_id="m-1"
    )
    return create_handler(service, settings), model


def test_valid_post_returns_200_with_request_id_and_markdown():
    handler, _ = make_handler()

    response = handler(make_event({"title": "Recuperar contraseña"}), Context())

    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["markdown"].startswith("# Recuperar contraseña\n")
    assert "Como analista de negocio, quiero poder recuperar mi contraseña" in body["markdown"]
    assert body["requestId"]
    assert response["headers"]["Content-Type"] == "application/json"


def test_bearer_token_is_taken_from_the_authorization_header_case_insensitively():
    verifier = RecordingVerifier()
    handler, _ = make_handler(verifier=verifier)
    event = make_event({"title": TITLE})
    event["headers"] = {"authorization": "bearer abc.def"}

    handler(event, Context())

    assert verifier.credentials == ["abc.def"]


def test_missing_authorization_with_fail_closed_verifier_returns_401():
    handler, model = make_handler(verifier=FailClosedSessionVerifier())
    event = make_event({"title": TITLE})
    event["headers"] = {}

    response = handler(event, Context())

    assert response["statusCode"] == 401
    assert json.loads(response["body"])["code"] == "SESSION_INVALID"
    assert model.calls == []


@pytest.mark.parametrize("body", [None, "no es json", "[]", {}, {"title": "   "}, {"title": 5}])
def test_invalid_or_missing_title_returns_400_with_c1_error_shape(body):
    handler, model = make_handler()

    response = handler(make_event(body), Context())

    parsed = json.loads(response["body"])
    assert response["statusCode"] == 400
    assert parsed["code"] == "TITLE_EMPTY"
    assert set(parsed) >= {"code", "message", "retryable"}
    assert parsed["retryable"] is False
    assert model.calls == []


def test_title_over_200_characters_returns_400_title_too_long():
    handler, _ = make_handler()

    response = handler(make_event({"title": "x" * 201}), Context())

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "TITLE_TOO_LONG"


def test_cors_headers_only_for_the_configured_origin():
    handler, _ = make_handler()

    allowed = handler(make_event({"title": TITLE}, headers={"Origin": ORIGIN}), Context())
    other = handler(
        make_event({"title": TITLE}, headers={"Origin": "https://malo.example"}), Context()
    )
    none = handler(make_event({"title": TITLE}), Context())

    assert allowed["headers"]["Access-Control-Allow-Origin"] == ORIGIN
    for response in (other, none):
        assert "Access-Control-Allow-Origin" not in response["headers"]
    assert "*" not in json.dumps(allowed["headers"])


def test_options_preflight_returns_204_with_cors_for_the_configured_origin():
    handler, model = make_handler()

    response = handler(make_event(method="OPTIONS", headers={"Origin": ORIGIN}), Context())

    assert response["statusCode"] == 204
    assert response["headers"]["Access-Control-Allow-Origin"] == ORIGIN
    assert "Authorization" in response["headers"]["Access-Control-Allow-Headers"]
    assert model.calls == []


def test_remaining_function_time_bounds_the_service_deadline():
    handler, model = make_handler()

    handler(make_event({"title": TITLE}), Context(remaining_ms=10000))

    assert model.calls[0].timeout_seconds <= 9


def test_model_failure_returns_502_without_stack_traces():
    handler, _ = make_handler(
        results=[ModelError(ModelErrorKind.ACCESS_DENIED, "AccessDenied arn:aws:...")]
    )

    response = handler(make_event({"title": TITLE}), Context())

    assert response["statusCode"] == 502
    assert "Traceback" not in response["body"]
    assert "arn:aws" not in response["body"]


def test_unexpected_exception_returns_generic_error_without_trace():
    class Boom:
        def generate(self, *args, **kwargs):
            raise RuntimeError("secreto interno")

    handler = create_handler(Boom(), SETTINGS)

    response = handler(make_event({"title": TITLE}), Context())

    assert response["statusCode"] == 502
    assert "secreto interno" not in response["body"]
    assert "Traceback" not in response["body"]
    assert json.loads(response["body"])["retryable"] is False


# --- u3-story-generator: contexto opcional y codigos de error nuevos (C1) ---


def test_post_accepts_the_optional_context_and_passes_it_to_the_model():
    handler, model = make_handler()

    response = handler(make_event({"title": "Login", "context": "acceso con correo"}), Context())

    assert response["statusCode"] == 200
    assert "acceso con correo" in model.calls[0].prompt
    assert json.loads(response["body"])["markdown"].startswith("# Login\n")


def test_context_over_500_characters_returns_400_context_too_long_with_the_c1_shape():
    handler, model = make_handler()

    response = handler(make_event({"title": TITLE, "context": "c" * 501}), Context())

    parsed = json.loads(response["body"])
    assert response["statusCode"] == 400
    assert parsed["code"] == "CONTEXT_TOO_LONG"
    assert parsed["retryable"] is False
    assert parsed["requestId"] and "500" in parsed["message"]
    assert model.calls == []


def test_short_title_without_context_returns_422_needs_context():
    handler, model = make_handler()

    response = handler(make_event({"title": "Login"}), Context())

    parsed = json.loads(response["body"])
    assert response["statusCode"] == 422
    assert (parsed["code"], parsed["retryable"]) == ("NEEDS_CONTEXT", False)
    assert set(parsed) >= {"code", "message", "retryable", "requestId"}
    assert model.calls == []


@pytest.mark.parametrize("context", [None, "", "   ", 5, ["x"]])
def test_an_absent_blank_or_non_text_context_counts_as_absent(context):
    handler, model = make_handler()

    response = handler(make_event({"title": "Login", "context": context}), Context())

    assert response["statusCode"] == 422
    assert model.calls == []


def test_u3_error_codes_carry_cors_like_the_u1_ones():
    handler, _ = make_handler()
    headers = {"Origin": ORIGIN}

    long_context = {"title": TITLE, "context": "c" * 501}
    needs_context = handler(make_event({"title": "Login"}, headers=headers), Context())
    too_long = handler(make_event(long_context, headers=headers), Context())

    for response in (needs_context, too_long):
        assert response["headers"]["Access-Control-Allow-Origin"] == ORIGIN
    assert (needs_context["statusCode"], too_long["statusCode"]) == (422, 400)


def test_an_unusable_model_response_returns_502_invalid_model_response_without_text():
    handler, _ = make_handler(results=[ModelResponse("texto libre del modelo", "m-1")])

    response = handler(make_event({"title": TITLE}), Context())

    parsed = json.loads(response["body"])
    assert response["statusCode"] == 502
    assert (parsed["code"], parsed["retryable"]) == ("INVALID_MODEL_RESPONSE", True)
    assert "texto libre" not in response["body"]


# --- u4-access-control: GET y DELETE /v1/session (C2) y ACCOUNT_NOT_ALLOWED (C1) ---


class ScriptedVerifier:
    """Doble del verificador (C3): devuelve el veredicto indicado y recuerda la credencial."""

    def __init__(self, verdict) -> None:
        self.verdict = verdict
        self.credentials: list[str] = []

    def verify_session(self, credential):
        self.credentials.append(credential)
        return self.verdict


SESSION = Session("sesion-1", "cuenta-1", "microsoft", "2030-01-01T08:00:00Z")


def session_event(method, headers=None):
    return {
        "httpMethod": method,
        "path": "/v1/session",
        "headers": {"Authorization": "Bearer abc.def.ghi", **(headers or {})},
        "body": None,
    }


def session_handler(verdict):
    verifier = ScriptedVerifier(verdict)
    handler, model = make_handler(verifier=verifier)
    return handler, verifier, model


def test_get_session_returns_200_with_the_four_fields_and_never_the_email_or_the_token():
    handler, verifier, _ = session_handler(SESSION)

    response = handler(session_event("GET"), Context())

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "sessionId": "sesion-1",
        "accountId": "cuenta-1",
        "provider": "microsoft",
        "expiresAt": "2030-01-01T08:00:00Z",
    }
    assert "abc.def.ghi" not in response["body"] and "@" not in response["body"]
    assert verifier.credentials == ["abc.def.ghi"]  # el encabezado Bearer se leyó


def test_get_session_without_a_valid_session_returns_401_session_invalid():
    handler, _, _ = session_handler(SessionInvalid(reason="expired"))

    response = handler(session_event("GET"), Context())

    body = json.loads(response["body"])
    assert response["statusCode"] == 401
    assert (body["code"], body["retryable"]) == ("SESSION_INVALID", False)


def test_get_session_with_an_account_not_allowed_returns_403():
    handler, _, _ = session_handler(SessionInvalid(reason="account_not_allowed"))

    response = handler(session_event("GET"), Context())

    body = json.loads(response["body"])
    assert response["statusCode"] == 403
    assert (body["code"], body["retryable"]) == ("ACCOUNT_NOT_ALLOWED", False)


def test_delete_session_returns_204_without_body_for_a_valid_session():
    handler, _, _ = session_handler(SESSION)

    response = handler(session_event("DELETE"), Context())

    assert response["statusCode"] == 204
    assert response["body"] == ""


@pytest.mark.parametrize(
    ("reason", "status", "code"),
    [("missing", 401, "SESSION_INVALID"), ("account_not_allowed", 403, "ACCOUNT_NOT_ALLOWED")],
)
def test_delete_session_without_a_valid_session_returns_401_or_403(reason, status, code):
    handler, _, _ = session_handler(SessionInvalid(reason=reason))

    response = handler(session_event("DELETE"), Context())

    assert response["statusCode"] == status
    assert json.loads(response["body"])["code"] == code


def test_post_stories_with_an_account_not_allowed_returns_403_and_does_not_call_the_model():
    handler, _, model = session_handler(SessionInvalid(reason="account_not_allowed"))

    response = handler(make_event({"title": TITLE}), Context())

    assert response["statusCode"] == 403
    assert json.loads(response["body"])["code"] == "ACCOUNT_NOT_ALLOWED"
    assert model.calls == []


def test_session_responses_carry_cors_like_the_u1_ones_and_allow_get_and_delete():
    handler, _, _ = session_handler(SessionInvalid(reason="missing"))
    headers = {"Origin": ORIGIN}

    error = handler(session_event("GET", headers), Context())
    ok = session_handler(SESSION)[0](session_event("DELETE", headers), Context())
    preflight = handler({**session_event("OPTIONS", headers)}, Context())

    for response in (error, ok, preflight):
        assert response["headers"]["Access-Control-Allow-Origin"] == ORIGIN
    allowed_methods = preflight["headers"]["Access-Control-Allow-Methods"]
    assert all(method in allowed_methods for method in ("GET", "POST", "DELETE", "OPTIONS"))


def test_session_route_with_any_other_method_returns_405_and_never_generates():
    handler, verifier, model = session_handler(SESSION)

    response = handler(session_event("POST"), Context())

    assert response["statusCode"] == 405
    assert verifier.credentials == [] and model.calls == []


def test_an_unexpected_error_in_a_session_route_returns_a_generic_error_without_trace():
    class Boom:
        def get_session(self, *args, **kwargs):
            raise RuntimeError("secreto interno")

    handler = create_handler(Boom(), SETTINGS)

    response = handler(session_event("GET"), Context())

    assert response["statusCode"] == 401
    assert "secreto interno" not in response["body"]
    assert json.loads(response["body"])["code"] == "SESSION_INVALID"


def test_deployed_entry_point_fails_closed_without_a_real_verifier(monkeypatch):
    from story_service import handler as handler_module

    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("ALLOW_SIMULATED_SESSION", raising=False)
    monkeypatch.setattr(handler_module, "BedrockModelClient", lambda *a, **k: FakeModelClient())
    monkeypatch.setattr(handler_module, "_cached_handler", None)

    response = handler_module.lambda_handler(make_event({"title": TITLE}), Context())

    assert response["statusCode"] == 401
    assert json.loads(response["body"])["code"] == "SESSION_INVALID"
