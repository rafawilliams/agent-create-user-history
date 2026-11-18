"""Validacion de la entrada y peticion de contexto (BR3.1 a BR3.3, NFR4.4, NFR1.3)."""

import pytest

from story_service.errors import ErrorCode, ServiceError
from story_service.fakes import FakeModelClient
from story_service.input_validation import CONTEXT_THRESHOLD, validate_story_input
from story_service.models import ModelResponse
from tests.helpers import VALID_JSON, build_service


def _code(title, context=None) -> ErrorCode:
    with pytest.raises(ServiceError) as caught:
        validate_story_input(title, context)
    return caught.value.code


@pytest.mark.parametrize("title", ["", "   ", "\n\t", " 　", None, 5])
def test_empty_or_blank_title_is_title_empty(title):
    assert _code(title) == ErrorCode.TITLE_EMPTY


def test_title_of_200_is_valid_and_201_is_title_too_long():
    long_title = ("palabra " * 40)[:199] + "x"
    assert len(long_title) == 200
    assert validate_story_input(long_title).title == long_title
    assert _code(long_title + "x") == ErrorCode.TITLE_TOO_LONG


def test_context_of_500_is_valid_and_501_is_context_too_long():
    assert len(validate_story_input("Login", "c" * 500).context) == 500
    assert _code("Login", "c" * 501) == ErrorCode.CONTEXT_TOO_LONG


def test_short_title_without_context_asks_for_context_with_http_422():
    with pytest.raises(ServiceError) as caught:
        validate_story_input("Login")

    assert caught.value.code == ErrorCode.NEEDS_CONTEXT
    assert caught.value.http_status == 422
    assert caught.value.retryable is False
    assert caught.value.request_id
    assert "contexto" in caught.value.message.lower()


def test_two_words_and_twenty_characters_generates_without_context():
    request = validate_story_input("Recuperar contraseña")

    assert request.title == "Recuperar contraseña"
    assert request.context is None


@pytest.mark.parametrize(
    "title",
    [
        "Login",  # una palabra
        "Subir fotos",  # 2 palabras pero 11 caracteres
        "Exportación_de_reportes_completos",  # 33 caracteres pero una palabra
    ],
)
def test_title_below_either_minimum_asks_for_context(title):
    assert _code(title) == ErrorCode.NEEDS_CONTEXT


def test_short_title_with_context_generates_and_blank_context_counts_as_absent():
    assert validate_story_input("Login", "acceso con correo y clave").context
    assert _code("Login", "   \n ") == ErrorCode.NEEDS_CONTEXT


def test_the_threshold_lives_in_one_constant():
    assert (CONTEXT_THRESHOLD.min_words, CONTEXT_THRESHOLD.min_chars) == (2, 12)


def test_length_is_measured_in_code_points_and_unicode_spaces_are_trimmed():
    emoji_title = "Añadir 😀 al carrito de compras " + "é😀" * 20
    request = validate_story_input(" " + emoji_title + " ")

    assert request.title == emoji_title.strip()
    assert len(request.title) == len(emoji_title.strip())


def test_the_model_is_not_called_when_validation_fails():
    model = FakeModelClient(results=[ModelResponse(VALID_JSON, "m")])
    service = build_service(model)

    for title, context in [("", None), ("Login", None), ("x" * 201, None), ("Login", "c" * 501)]:
        with pytest.raises(ServiceError):
            service.generate("token", title, context=context)

    assert model.calls == []
