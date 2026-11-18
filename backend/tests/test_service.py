"""Pruebas del servicio con el modelo y el verificador simulados (W1 a W4, NFR1, NFR4.4)."""

import pytest

from story_service.errors import ErrorCode, ServiceError
from story_service.fakes import FakeModelClient, SimulatedSessionVerifier
from story_service.models import ModelError, ModelErrorKind, ModelResponse, SessionInvalid
from story_service.prompt import TITLE_CLOSE, TITLE_OPEN
from tests.helpers import VALID_JSON, FakeClock, build_service

# u3 (BR3.2): un titulo de una palabra pide contexto; estas pruebas de u1 usan un titulo suficiente.
TITLE = "Titulo de prueba valido"


def ok(text: str = VALID_JSON) -> ModelResponse:
    return ModelResponse(text=text, model_id="test-model")


def err(kind: ModelErrorKind) -> ModelError:
    return ModelError(kind=kind, message="fallo")


def test_happy_path_returns_request_id_and_markdown():
    model = FakeModelClient(results=[ok()])
    service = build_service(model)

    result = service.generate("token", "  Recuperar contraseña ")

    # u3 (BR3.5, BR3.9): el modelo devuelve JSON y el servicio arma el Markdown.
    assert result.markdown.startswith("# Recuperar contraseña\n")
    assert "Como analista de negocio, quiero poder recuperar mi contraseña" in result.markdown
    assert result.request_id
    assert len(model.calls) == 1


def test_prompt_asks_for_story_and_gherkin_criteria_with_title_inside_fixed_delimiter():
    model = FakeModelClient(results=[ok()])
    service = build_service(model, instructions="Pide 2 a 3 criterios Gherkin en español")

    service.generate("token", "Recuperar contraseña")

    prompt = model.calls[0].prompt
    assert prompt.startswith("Pide 2 a 3 criterios Gherkin en español")
    assert f"{TITLE_OPEN}\nRecuperar contraseña\n{TITLE_CLOSE}" in prompt
    assert prompt.index("Pide 2 a 3") < prompt.index(TITLE_OPEN)


def test_default_instructions_ask_for_gherkin_criteria_in_spanish():
    # u3 reemplaza la peticion de u1 (Markdown completo con "Como analista de negocio") por
    # una peticion de JSON: el servicio fija el rol y las palabras clave (BR3.5, BR3.9).
    from story_service.config import DEFAULT_INSTRUCTIONS

    for word in ("Gherkin", "español", "2 a 3"):
        assert word in DEFAULT_INSTRUCTIONS


def test_default_instructions_ask_for_json_only_without_surrounding_text():
    # Sustituye la prueba de u1 que exigia no poner encabezados antes de la historia: ahora la
    # respuesta es un JSON y cualquier texto fuera del JSON es una respuesta invalida (BR3.6).
    from story_service.config import DEFAULT_INSTRUCTIONS

    assert "JSON" in DEFAULT_INSTRUCTIONS
    assert "sin texto" in DEFAULT_INSTRUCTIONS


@pytest.mark.parametrize("title", ["", "   ", "\n"])
def test_empty_title_does_not_call_the_model(title):
    model = FakeModelClient(results=[ok()])

    with pytest.raises(ServiceError) as caught:
        build_service(model).generate("token", title)

    assert caught.value.code == ErrorCode.TITLE_EMPTY
    assert caught.value.request_id
    assert model.calls == []


def test_title_over_200_characters_is_rejected_without_calling_the_model():
    model = FakeModelClient(results=[ok()])

    with pytest.raises(ServiceError) as caught:
        build_service(model).generate("token", "x" * 201)

    assert caught.value.code == ErrorCode.TITLE_TOO_LONG
    assert model.calls == []


@pytest.mark.parametrize(
    ("kind", "code", "status", "retryable"),
    [
        (ModelErrorKind.ACCESS_DENIED, ErrorCode.MODEL_FAILURE, 502, False),
        (ModelErrorKind.TIMEOUT, ErrorCode.GENERATION_TIMEOUT, 504, True),
        (ModelErrorKind.TRANSIENT, ErrorCode.MODEL_FAILURE, 502, True),
        (ModelErrorKind.UNAVAILABLE, ErrorCode.MODEL_FAILURE, 502, True),
    ],
)
def test_model_failures_map_to_the_br1_4_table(kind, code, status, retryable):
    model = FakeModelClient(results=[err(kind)])

    with pytest.raises(ServiceError) as caught:
        build_service(model).generate("token", TITLE)

    assert (caught.value.code, caught.value.http_status, caught.value.retryable) == (
        code,
        status,
        retryable,
    )


@pytest.mark.parametrize("text", ["como analista de negocio quiero", "Historia sin rol", ""])
def test_out_of_contract_response_is_invalid_model_response_without_partial_text(text):
    model = FakeModelClient(results=[ok(text)])

    with pytest.raises(ServiceError) as caught:
        build_service(model).generate("token", TITLE)

    assert caught.value.code == ErrorCode.INVALID_MODEL_RESPONSE
    assert caught.value.http_status == 502
    assert caught.value.retryable is True
    assert text.strip() not in caught.value.message or not text.strip()


def test_leading_whitespace_in_model_response_is_still_valid():
    model = FakeModelClient(results=[ok("\n  \t" + VALID_JSON + "\n")])

    result = build_service(model).generate("token", TITLE)

    assert result.markdown.startswith(f"# {TITLE}\n")


def test_model_timeout_is_the_smaller_of_50_seconds_and_the_time_left():
    clock = FakeClock()
    model = FakeModelClient(results=[ok()])
    build_service(model, clock=clock).generate("token", TITLE)
    assert model.calls[0].timeout_seconds == 50

    short = FakeModelClient(results=[ok()])
    build_service(short, clock=clock).generate("token", TITLE, deadline_seconds=12)
    assert short.calls[0].timeout_seconds == 12


def test_timeout_error_is_not_retried():
    model = FakeModelClient(results=[err(ModelErrorKind.TIMEOUT), ok()])

    with pytest.raises(ServiceError) as caught:
        build_service(model).generate("token", TITLE)

    assert caught.value.code == ErrorCode.GENERATION_TIMEOUT
    assert len(model.calls) == 1


def test_transient_failure_is_retried_once_when_time_remains():
    clock = FakeClock()
    model = FakeModelClient(
        results=[err(ModelErrorKind.TRANSIENT), ok()], on_invoke=lambda: clock.advance(2)
    )

    result = build_service(model, clock=clock).generate("token", TITLE)

    assert result.markdown.startswith(f"# {TITLE}\n")
    assert len(model.calls) == 2
    assert model.calls[1].timeout_seconds == 50  # min(50, 55 - 2) = 50


def test_retry_uses_the_remaining_time_as_timeout():
    clock = FakeClock()
    model = FakeModelClient(
        results=[err(ModelErrorKind.UNAVAILABLE), ok()], on_invoke=lambda: clock.advance(20)
    )

    build_service(model, clock=clock).generate("token", TITLE)

    assert model.calls[1].timeout_seconds == pytest.approx(55 - 20 - 0)  # el 2.o intento


def test_only_one_retry_even_if_the_failure_repeats():
    model = FakeModelClient(results=[err(ModelErrorKind.TRANSIENT)])

    with pytest.raises(ServiceError) as caught:
        build_service(model).generate("token", TITLE)

    assert caught.value.code == ErrorCode.MODEL_FAILURE
    assert len(model.calls) == 2


def test_no_retry_and_generation_timeout_when_no_time_is_left():
    clock = FakeClock()
    model = FakeModelClient(
        results=[err(ModelErrorKind.TRANSIENT), ok()], on_invoke=lambda: clock.advance(56)
    )

    with pytest.raises(ServiceError) as caught:
        build_service(model, clock=clock).generate("token", TITLE)

    assert caught.value.code == ErrorCode.GENERATION_TIMEOUT
    assert caught.value.retryable is True
    assert len(model.calls) == 1


def test_invalid_session_is_rejected_without_calling_the_model():
    model = FakeModelClient(results=[ok()])

    class Rejecting:
        def verify_session(self, credential):
            return SessionInvalid(reason="expired")

    with pytest.raises(ServiceError) as caught:
        build_service(model, verifier=Rejecting()).generate("token", TITLE)

    assert caught.value.code == ErrorCode.SESSION_INVALID
    assert caught.value.http_status == 401
    assert model.calls == []


def test_verifier_that_raises_fails_closed():
    class Broken:
        def verify_session(self, credential):
            raise RuntimeError("boom")

    model = FakeModelClient(results=[ok()])

    with pytest.raises(ServiceError) as caught:
        build_service(model, verifier=Broken()).generate("token", TITLE)

    assert caught.value.code == ErrorCode.SESSION_INVALID
    assert model.calls == []


def test_model_client_that_raises_is_reported_as_model_failure_not_swallowed():
    class Exploding:
        def invoke(self, prompt, timeout_seconds):
            raise RuntimeError("boom")

    service = build_service(FakeModelClient(results=[ok()]))
    service._model_client = Exploding()  # noqa: SLF001 - doble de prueba

    with pytest.raises(ServiceError) as caught:
        service.generate("token", TITLE)

    assert caught.value.code == ErrorCode.MODEL_FAILURE
    assert "boom" not in caught.value.message


def test_service_keeps_no_state_between_requests():
    model = FakeModelClient(results=[ok()])
    service = build_service(model, verifier=SimulatedSessionVerifier())

    first = service.generate("token", "Titulo Uno completo")
    second = service.generate("token", "Titulo Dos completo")

    assert first.request_id != second.request_id
    assert "Uno" not in model.calls[1].prompt
