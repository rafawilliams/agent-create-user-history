"""Pruebas de las entidades y de la tabla de errores (BR1.3, BR1.4, NFR4.4)."""

import uuid

import pytest

from story_service.errors import (
    ErrorCode,
    ServiceError,
    error_from_model_error,
)
from story_service.models import (
    AllowedAccount,
    Criterion,
    EvaluationOutcome,
    EvaluationRecord,
    EvaluationResult,
    ModelError,
    ModelErrorKind,
    ModelErrorReason,
    ModelResponse,
    Session,
    SessionInvalid,
    SessionInvalidReason,
    StoryDraft,
    StoryRequest,
    StoryResult,
)


def test_story_request_trims_title_and_generates_uuid4_request_id():
    request = StoryRequest.create("  Recuperar contraseña \n")

    assert request.title == "Recuperar contraseña"
    parsed = uuid.UUID(request.request_id)
    assert parsed.version == 4


@pytest.mark.parametrize("title", ["", "   ", "\n\t "])
def test_story_request_rejects_empty_or_blank_title(title):
    with pytest.raises(ServiceError) as caught:
        StoryRequest.create(title)

    assert caught.value.code == ErrorCode.TITLE_EMPTY
    assert caught.value.http_status == 400
    assert caught.value.retryable is False


def test_story_request_rejects_title_longer_than_200_characters():
    with pytest.raises(ServiceError) as caught:
        StoryRequest.create("a" * 201)

    assert caught.value.code == ErrorCode.TITLE_TOO_LONG
    assert caught.value.http_status == 400


def test_story_request_accepts_title_of_exactly_200_characters():
    assert len(StoryRequest.create("a" * 200).title) == 200


def test_story_request_rejects_non_text_title():
    with pytest.raises(ServiceError) as caught:
        StoryRequest.create(None)  # type: ignore[arg-type]

    assert caught.value.code == ErrorCode.TITLE_EMPTY


def test_entities_require_their_mandatory_fields():
    with pytest.raises(ValueError):
        StoryResult(request_id="", markdown="Como analista de negocio")
    with pytest.raises(ValueError):
        StoryResult(request_id="abc", markdown="")
    with pytest.raises(ValueError):
        ModelResponse(text="x", model_id="")
    with pytest.raises(ValueError):
        ModelError(kind=ModelErrorKind.TRANSIENT, message="")
    with pytest.raises(ValueError):
        Session(session_id="", account_id="a", provider="google", expires_at="2030-01-01T00:00:00Z")
    with pytest.raises(ValueError):
        SessionInvalid(reason="")
    with pytest.raises(TypeError):
        StoryResult(request_id="abc")  # type: ignore[call-arg]


def test_story_result_serialises_to_the_c1_response_shape():
    result = StoryResult(request_id="r-1", markdown="Como analista de negocio quiero algo")

    assert result.to_dict() == {
        "requestId": "r-1",
        "markdown": "Como analista de negocio quiero algo",
    }


def test_model_error_kinds_are_the_four_of_contract_c4():
    assert {kind.value for kind in ModelErrorKind} == {
        "transient",
        "timeout",
        "unavailable",
        "access_denied",
    }


@pytest.mark.parametrize(
    ("kind", "code", "status", "retryable"),
    [
        (ModelErrorKind.TRANSIENT, ErrorCode.MODEL_FAILURE, 502, True),
        (ModelErrorKind.TIMEOUT, ErrorCode.GENERATION_TIMEOUT, 504, True),
        (ModelErrorKind.UNAVAILABLE, ErrorCode.MODEL_FAILURE, 502, True),
        (ModelErrorKind.ACCESS_DENIED, ErrorCode.MODEL_FAILURE, 502, False),
    ],
)
def test_model_error_kind_maps_to_the_br1_4_table(kind, code, status, retryable):
    error = error_from_model_error(ModelError(kind=kind, message="detalle interno"), "req-1")

    assert (error.code, error.http_status, error.retryable) == (code, status, retryable)
    assert error.request_id == "req-1"


def test_error_body_has_the_c1_shape_with_optional_request_id():
    with_id = ServiceError(ErrorCode.SESSION_INVALID, "Sesión no válida", request_id="r-9")
    without_id = ServiceError(ErrorCode.RATE_LIMITED, "Demasiadas solicitudes")

    assert with_id.to_body() == {
        "code": "SESSION_INVALID",
        "message": "Sesión no válida",
        "retryable": False,
        "requestId": "r-9",
    }
    assert "requestId" not in without_id.to_body()
    assert without_id.to_body()["retryable"] is True
    assert without_id.http_status == 429


def test_model_error_reason_is_the_closed_list_of_seven_values():
    assert {reason.value for reason in ModelErrorReason} == {
        "access_not_enabled",
        "model_not_found",
        "invalid_request",
        "timeout",
        "throttled",
        "unavailable",
        "unknown",
    }


def test_model_error_reason_is_optional_and_u1_construction_still_works():
    without = ModelError(kind=ModelErrorKind.TRANSIENT, message="Fallo pasajero del modelo")
    with_reason = ModelError(
        kind=ModelErrorKind.ACCESS_DENIED,
        message="Sin acceso",
        reason=ModelErrorReason.ACCESS_NOT_ENABLED,
    )

    assert without.reason is None
    assert with_reason.reason == "access_not_enabled"


def test_model_error_rejects_a_reason_outside_the_closed_list():
    with pytest.raises(ValueError, match="motivo"):
        ModelError(kind=ModelErrorKind.TIMEOUT, message="x", reason="texto libre de AWS")


def test_service_ignores_the_reason_when_building_the_contract_error():
    error = error_from_model_error(
        ModelError(
            kind=ModelErrorKind.ACCESS_DENIED,
            message="m",
            reason=ModelErrorReason.INVALID_REQUEST,
        ),
        "req-2",
    )

    assert (error.http_status, error.retryable) == (502, False)


def _generated(**overrides):
    values = {
        "model_id": "us.anthropic.claude-sonnet-4-6",
        "title": "Titulo inventado",
        "outcome": EvaluationOutcome.GENERATED,
        "text": "Como analista de negocio quiero algo",
        "format_ok": True,
        "elapsed_seconds": 1.5,
    }
    values.update(overrides)
    return EvaluationResult(**values)


def test_evaluation_result_generated_requires_text_and_format_flag():
    result = _generated()

    assert result.format_ok is True and result.reason is None
    with pytest.raises(ValueError):
        _generated(text=None)
    with pytest.raises(ValueError):
        _generated(format_ok=None)


def test_evaluation_result_text_and_format_only_with_generated():
    with pytest.raises(ValueError):
        EvaluationResult(
            model_id="m",
            title="t",
            outcome=EvaluationOutcome.FAILED,
            text="texto",
            reason=ModelErrorReason.TIMEOUT,
        )
    with pytest.raises(ValueError):
        EvaluationResult(
            model_id="m",
            title="t",
            outcome=EvaluationOutcome.BLOCKED,
            format_ok=False,
            reason=ModelErrorReason.MODEL_NOT_FOUND,
        )


def test_evaluation_result_reason_only_with_blocked_or_failed():
    blocked = EvaluationResult(
        model_id="m",
        title="t",
        outcome=EvaluationOutcome.BLOCKED,
        reason=ModelErrorReason.ACCESS_NOT_ENABLED,
    )

    assert blocked.reason == "access_not_enabled"
    with pytest.raises(ValueError):
        _generated(reason=ModelErrorReason.TIMEOUT)
    with pytest.raises(ValueError):
        EvaluationResult(model_id="m", title="t", outcome=EvaluationOutcome.FAILED)


def test_evaluation_record_requires_its_mandatory_fields():
    record = EvaluationRecord(
        evaluated_at="2026-11-17T10:00:00Z",
        titles=("a", "b"),
        results=(_generated(),),
        decision="pendiente",
        pending_access=("us.amazon.titan-text-premier-v1:0",),
    )

    assert record.pending_access == ("us.amazon.titan-text-premier-v1:0",)
    with pytest.raises(ValueError):
        EvaluationRecord(evaluated_at="", titles=("a",), results=(_generated(),), decision="x")
    with pytest.raises(ValueError):
        EvaluationRecord(evaluated_at="t", titles=(), results=(_generated(),), decision="x")
    with pytest.raises(ValueError):
        EvaluationRecord(evaluated_at="t", titles=("a",), results=(), decision="x")


def test_error_message_is_spanish_and_does_not_leak_the_model_detail():
    error = error_from_model_error(
        ModelError(kind=ModelErrorKind.ACCESS_DENIED, message="arn:aws:secret-detail"), "r"
    )

    assert "arn:aws" not in error.message
    assert error.message


# --- u3-story-generator: cambio coordinado de las listas cerradas de u1 y entidades nuevas ---


@pytest.mark.parametrize(
    ("code", "status", "retryable"),
    [
        (ErrorCode.CONTEXT_TOO_LONG, 400, False),
        (ErrorCode.NEEDS_CONTEXT, 422, False),
    ],
)
def test_u3_error_codes_have_the_http_status_and_are_not_retryable(code, status, retryable):
    error = ServiceError(code, "mensaje", request_id="r-1")

    assert (error.http_status, error.retryable) == (status, retryable)
    assert error.to_body()["code"] == code.value


def test_u1_error_table_is_unchanged_by_u3():
    expected = {
        ErrorCode.TITLE_EMPTY: (400, False),
        ErrorCode.TITLE_TOO_LONG: (400, False),
        ErrorCode.SESSION_INVALID: (401, False),
        ErrorCode.RATE_LIMITED: (429, True),
        ErrorCode.MODEL_FAILURE: (502, True),
        ErrorCode.INVALID_MODEL_RESPONSE: (502, True),
        ErrorCode.GENERATION_TIMEOUT: (504, True),
    }
    for code, (status, retryable) in expected.items():
        error = ServiceError(code, "m")
        assert (error.http_status, error.retryable) == (status, retryable)


def test_story_request_trims_and_normalizes_the_context_and_empty_means_absent():
    with_context = StoryRequest.create("Login", context="  datos\nde acceso\t ")
    blank = StoryRequest.create("Login", context="   \n ")
    absent = StoryRequest.create("Login")

    assert with_context.context == "datos de acceso"
    assert blank.context is None
    assert absent.context is None


def test_story_request_normalizes_control_characters_and_unicode_spaces_in_the_title():
    request = StoryRequest.create("  Recuperar\ncontraseña\x00 ahora　")

    assert request.title == "Recuperar contraseña  ahora"


def test_story_request_measures_length_in_code_points():
    emojis = "é😀" * 100  # 200 puntos de código
    assert len(StoryRequest.create(emojis).title) == 200
    with pytest.raises(ServiceError) as caught:
        StoryRequest.create(emojis + "x")
    assert caught.value.code == ErrorCode.TITLE_TOO_LONG


def test_story_request_context_limit_is_500_inclusive():
    assert len(StoryRequest.create("Login", context="c" * 500).context) == 500
    with pytest.raises(ServiceError) as caught:
        StoryRequest.create("Login", context="c" * 501)
    assert caught.value.code == ErrorCode.CONTEXT_TOO_LONG
    assert caught.value.http_status == 400
    assert "500" in caught.value.message


def _criterion(**overrides):
    values = {"name": "Éxito", "given": "una cuenta", "when": "entra", "then": "ve su panel"}
    values.update(overrides)
    return Criterion(**values)


@pytest.mark.parametrize("field", ["name", "given", "when", "then"])
@pytest.mark.parametrize("bad", ["", "   ", "dos\nlíneas", "dos\rlíneas"])
def test_criterion_requires_four_non_empty_single_line_parts(field, bad):
    with pytest.raises(ValueError):
        _criterion(**{field: bad})


# --- u4-access-control: entidades de acceso y codigo ACCOUNT_NOT_ALLOWED (entities.md) ---

SESSION_INVALID_REASONS = {
    "missing",
    "malformed",
    "bad_signature",
    "wrong_issuer",
    "wrong_audience",
    "expired",
    "wrong_token_use",
    "keys_unavailable",
    "not_configured",
    "account_not_allowed",
    "unknown",
}


def test_session_invalid_reason_is_the_closed_list_of_eleven_values():
    assert {reason.value for reason in SessionInvalidReason} == SESSION_INVALID_REASONS
    for value in SESSION_INVALID_REASONS:
        assert SessionInvalid(reason=value).reason == value
    assert SessionInvalid(reason=SessionInvalidReason.EXPIRED).reason == "expired"


@pytest.mark.parametrize("bad", ["", "texto libre", "EXPIRED", "caducada", None, 5])
def test_session_invalid_rejects_a_reason_outside_the_closed_list(bad):
    with pytest.raises(ValueError, match="motivo"):
        SessionInvalid(reason=bad)


@pytest.mark.parametrize("provider", ["google", "microsoft"])
def test_session_accepts_google_and_microsoft_providers(provider):
    session = Session("s-1", "a-1", provider, "2030-01-01T00:00:00Z")

    assert session.provider == provider


@pytest.mark.parametrize("provider", ["facebook", "Google", "", "cognito"])
def test_session_rejects_any_other_provider(provider):
    with pytest.raises(ValueError):
        Session("s-1", "a-1", provider, "2030-01-01T00:00:00Z")


def test_allowed_account_is_lowercase_and_trimmed_without_touching_dots_or_aliases():
    account = AllowedAccount.create("  Ana.Perez+Test@Gmail.COM \n")

    assert account.email == "ana.perez+test@gmail.com"


@pytest.mark.parametrize("bad", ["", "   ", "sin-arroba", "a@b", "dos@@a.com", "a b@c.com", None])
def test_allowed_account_rejects_values_that_do_not_look_like_an_email(bad):
    with pytest.raises(ValueError):
        AllowedAccount.create(bad)


def test_allowed_account_constructor_requires_an_already_normalized_email():
    with pytest.raises(ValueError):
        AllowedAccount(email="Ana@Ejemplo.com")


def test_account_not_allowed_is_http_403_and_not_retryable():
    error = ServiceError(ErrorCode.ACCOUNT_NOT_ALLOWED, "Cuenta no permitida", request_id="r-1")

    assert (error.http_status, error.retryable) == (403, False)
    assert error.to_body() == {
        "code": "ACCOUNT_NOT_ALLOWED",
        "message": "Cuenta no permitida",
        "retryable": False,
        "requestId": "r-1",
    }


def test_story_draft_requires_action_benefit_and_two_to_three_criteria():
    draft = StoryDraft(action="entrar", benefit="ver mi panel", criteria=(_criterion(),) * 2)
    assert len(draft.criteria) == 2
    assert len(StoryDraft("a", "b", (_criterion(),) * 3).criteria) == 3
    for bad in ((), (_criterion(),), (_criterion(),) * 4):
        with pytest.raises(ValueError):
            StoryDraft(action="a", benefit="b", criteria=bad)
    with pytest.raises(ValueError):
        StoryDraft(action="", benefit="b", criteria=(_criterion(),) * 2)
    with pytest.raises(ValueError):
        StoryDraft(action="a", benefit=" ", criteria=(_criterion(),) * 2)
