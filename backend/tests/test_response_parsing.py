"""Interpretacion de la respuesta del modelo, que no es confiable (BR3.6, BR3.7, NFR1.6, NFR4.5)."""

import copy
import json

import pytest

from story_service.errors import ErrorCode, ServiceError
from story_service.models import StoryDraft
from story_service.response_parsing import MAX_RESPONSE_BYTES, parse_story_draft
from tests.helpers import VALID_JSON, draft_dict


def _invalid(text: str) -> ServiceError:
    with pytest.raises(ServiceError) as caught:
        parse_story_draft(text, "req-1")
    return caught.value


def _dumps(data) -> str:
    return json.dumps(data, ensure_ascii=False)


def test_a_valid_json_with_two_criteria_is_accepted():
    draft = parse_story_draft(VALID_JSON, "req-1")

    assert isinstance(draft, StoryDraft)
    assert draft.action == "poder recuperar mi contraseña"
    assert len(draft.criteria) == 2
    assert draft.criteria[0].given == "que la persona olvidó su contraseña"


def test_three_criteria_are_accepted():
    data = draft_dict()
    data["criteria"].append(copy.deepcopy(data["criteria"][0]))

    assert len(parse_story_draft(_dumps(data), "r").criteria) == 3


@pytest.mark.parametrize("fence", ["```json\n{}\n```", "```\n{}\n```", "  ```JSON\n{}\n```  \n"])
def test_a_single_code_fence_around_the_json_is_accepted(fence):
    draft = parse_story_draft(fence.replace("{}", VALID_JSON), "r")

    assert len(draft.criteria) == 2


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Como analista de negocio quiero algo",
        "no es json",
        "[]",
        '"texto"',
        "Aquí está la historia:\n" + VALID_JSON,
        VALID_JSON + "\nEspero que sirva.",
        "```json\n" + VALID_JSON + "\n``` y más texto",
        "```json\n```json\n" + VALID_JSON + "\n```\n```",
    ],
)
def test_text_that_is_not_exactly_a_json_is_invalid_without_partial_text(text):
    error = _invalid(text)

    assert error.code == ErrorCode.INVALID_MODEL_RESPONSE
    assert (error.http_status, error.retryable, error.request_id) == (502, True, "req-1")
    assert "Como analista" not in error.message and "historia:" not in error.message


@pytest.mark.parametrize("missing", ["action", "benefit", "criteria"])
def test_a_missing_top_level_field_is_invalid(missing):
    data = draft_dict()
    del data[missing]

    assert _invalid(_dumps(data)).code == ErrorCode.INVALID_MODEL_RESPONSE


@pytest.mark.parametrize("field", ["name", "given", "when", "then"])
@pytest.mark.parametrize("bad", [None, "", "   ", "\n", 7, ["x"]])
def test_a_missing_empty_or_non_text_criterion_field_is_invalid(field, bad):
    data = draft_dict()
    data["criteria"][0][field] = bad

    assert _invalid(_dumps(data)).code == ErrorCode.INVALID_MODEL_RESPONSE


def test_a_criterion_that_is_not_an_object_is_invalid():
    data = draft_dict()
    data["criteria"][1] = "texto"

    assert _invalid(_dumps(data)).code == ErrorCode.INVALID_MODEL_RESPONSE


def test_a_field_of_300_characters_is_valid_and_301_is_invalid():
    ok = draft_dict(action="poder " + "a" * 294)  # 300 en total
    assert len(ok["action"]) == 300
    assert parse_story_draft(_dumps(ok), "r").action == ok["action"]

    too_long = draft_dict(benefit="para " + "b" * 296)  # 301
    assert _invalid(_dumps(too_long)).code == ErrorCode.INVALID_MODEL_RESPONSE

    deep = draft_dict()
    deep["criteria"][1]["then"] = "t" * 301
    assert _invalid(_dumps(deep)).code == ErrorCode.INVALID_MODEL_RESPONSE


@pytest.mark.parametrize("count", [0, 1, 4])
def test_one_four_or_no_criteria_are_invalid(count):
    data = draft_dict()
    data["criteria"] = [copy.deepcopy(data["criteria"][0]) for _ in range(count)]

    assert _invalid(_dumps(data)).code == ErrorCode.INVALID_MODEL_RESPONSE


def test_a_response_over_16_kilobytes_is_invalid_even_if_it_is_a_valid_json():
    padding = " " * (MAX_RESPONSE_BYTES - len(VALID_JSON.encode("utf-8")))
    assert len((VALID_JSON + padding).encode("utf-8")) == MAX_RESPONSE_BYTES
    assert parse_story_draft(VALID_JSON + padding, "r")  # el limite exacto se acepta

    assert _invalid(VALID_JSON + padding + " ").code == ErrorCode.INVALID_MODEL_RESPONSE


def test_the_size_is_measured_in_utf8_bytes_not_characters():
    chars = MAX_RESPONSE_BYTES // 2  # con acentos son mas bytes que caracteres
    text = _dumps(draft_dict()) + "é" * chars

    assert _invalid(text).code == ErrorCode.INVALID_MODEL_RESPONSE


def test_a_complete_english_response_is_rejected_by_the_language_heuristic():
    english = draft_dict(
        action="to reset my password",
        benefit="log back in to my account",
    )
    english["criteria"][0]["given"] = "the user forgot the password"

    error = _invalid(_dumps(english))

    assert error.code == ErrorCode.INVALID_MODEL_RESPONSE
    assert error.retryable is True


def test_line_breaks_inside_a_field_become_spaces_and_are_not_rejected():
    data = draft_dict(action="poder recuperar\nmi contraseña\r\ncon el correo")
    data["criteria"][0]["name"] = "Primera\nlínea"

    draft = parse_story_draft(_dumps(data), "r")

    assert draft.action == "poder recuperar mi contraseña  con el correo"
    assert draft.criteria[0].name == "Primera línea"
    assert "\n" not in draft.action
