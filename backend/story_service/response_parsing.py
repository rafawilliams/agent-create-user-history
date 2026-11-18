"""Interpretacion de la respuesta del modelo, que no es confiable (BR3.6, BR3.7, NFR4.5).

Etapas (reliability-design.md): tamano, JSON con un cerco opcional, campos presentes y de hasta
300 caracteres normalizados a una linea, de 2 a 3 criterios y heuristica de idioma. Cualquier
etapa que falla es INVALID_MODEL_RESPONSE; nunca se devuelve texto parcial.
"""

from __future__ import annotations

import json
import re

from story_service.errors import ErrorCode, ServiceError
from story_service.models import MAX_CRITERIA, MIN_CRITERIA, Criterion, StoryDraft, normalize_line

MAX_RESPONSE_BYTES = 16 * 1024
MAX_FIELD_LENGTH = 300
MIN_SPANISH_WORDS = 2

INVALID_MESSAGE = "El modelo devolvió una respuesta que no se pudo usar. Inténtalo de nuevo."

_FENCE = re.compile(r"^```[A-Za-z]*[ \t]*\n(.*)\n```$", re.DOTALL)
_WORD = re.compile(r"[a-záéíóúüñ]+")
_SPANISH_WORDS = frozenset(
    "el la los las de del que para poder quiero un una con y en por mi mis tu su sus al se lo "
    "como sin sobre más cuando si todo todos cada".split()
)
_CRITERION_KEYS = ("name", "given", "when", "then")


def _invalid(request_id: str | None) -> ServiceError:
    return ServiceError(ErrorCode.INVALID_MODEL_RESPONSE, INVALID_MESSAGE, request_id=request_id)


def _unfence(text: str) -> str:
    """Quita un unico cerco de codigo; cualquier otro texto alrededor queda y falla despues."""
    stripped = text.strip()
    match = _FENCE.match(stripped)
    return match.group(1).strip() if match else stripped


def _field(value: object) -> str | None:
    """Campo de texto normalizado a una linea; None si no es texto, esta vacio o pasa de 300."""
    if not isinstance(value, str):
        return None
    line = normalize_line(value)
    if not line or len(line) > MAX_FIELD_LENGTH:
        return None
    return line


def _looks_spanish(*texts: str) -> bool:
    words = _WORD.findall(" ".join(texts).lower())
    return sum(1 for word in words if word in _SPANISH_WORDS) >= MIN_SPANISH_WORDS


def parse_story_draft(text: str, request_id: str | None = None) -> StoryDraft:
    """Devuelve el borrador validado o lanza INVALID_MODEL_RESPONSE (502, reintentable)."""
    if len(text.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise _invalid(request_id)
    try:
        data = json.loads(_unfence(text))
    except (ValueError, RecursionError):  # un JSON anidado en exceso tambien es invalido
        raise _invalid(request_id) from None
    if not isinstance(data, dict):
        raise _invalid(request_id)

    action = _field(data.get("action"))
    benefit = _field(data.get("benefit"))
    raw_criteria = data.get("criteria")
    if action is None or benefit is None or not isinstance(raw_criteria, list):
        raise _invalid(request_id)
    if not MIN_CRITERIA <= len(raw_criteria) <= MAX_CRITERIA:
        raise _invalid(request_id)

    criteria = []
    for raw in raw_criteria:
        if not isinstance(raw, dict):
            raise _invalid(request_id)
        parts = {key: _field(raw.get(key)) for key in _CRITERION_KEYS}
        if any(value is None for value in parts.values()):
            raise _invalid(request_id)
        criteria.append(Criterion(**parts))  # type: ignore[arg-type]

    if not _looks_spanish(action, benefit):
        raise _invalid(request_id)
    return StoryDraft(action=action, benefit=benefit, criteria=tuple(criteria))
