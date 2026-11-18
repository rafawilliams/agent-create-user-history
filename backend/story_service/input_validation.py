"""Validacion de la entrada y peticion de contexto (BR3.1 a BR3.3, NFR4.4)."""

from __future__ import annotations

from typing import NamedTuple

from story_service.errors import ErrorCode, ServiceError
from story_service.models import StoryRequest


class ContextThreshold(NamedTuple):
    min_words: int
    min_chars: int


# Umbral de BR3.2, en un solo sitio: un titulo con menos palabras o menos caracteres que esto
# pide contexto. Ajuste a la respuesta FD Q1, que la persona aun debe confirmar.
CONTEXT_THRESHOLD = ContextThreshold(min_words=2, min_chars=12)

NEEDS_CONTEXT_MESSAGE = (
    "El título es muy corto o ambiguo. Agrega un poco de contexto (qué quieres lograr y para "
    "quién) y vuelve a generar la historia."
)


def needs_context(title: str) -> bool:
    """`title` ya viene normalizado: recortado y en una sola línea (puntos de código)."""
    return (
        len(title.split()) < CONTEXT_THRESHOLD.min_words or len(title) < CONTEXT_THRESHOLD.min_chars
    )


def validate_story_input(
    title: object, context: object = None, request_id: str | None = None
) -> StoryRequest:
    """Orden fijo: recortar, normalizar, validar longitudes (en StoryRequest) y pedir contexto.

    Lanza ServiceError (TITLE_EMPTY, TITLE_TOO_LONG, CONTEXT_TOO_LONG o NEEDS_CONTEXT) antes de
    cualquier llamada al modelo.
    """
    request = StoryRequest.create(title, request_id=request_id, context=context)
    if request.context is None and needs_context(request.title):
        raise ServiceError(
            ErrorCode.NEEDS_CONTEXT, NEEDS_CONTEXT_MESSAGE, request_id=request.request_id
        )
    return request
