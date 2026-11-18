"""Interfaces fijas que usan las demas unidades: C3 (SessionVerifier) y C4 (ModelClient)."""

from typing import Protocol

from story_service.models import ModelError, ModelResponse, Session, SessionInvalid


class SessionVerifier(Protocol):
    """C3 (propietaria: u4-access-control).

    Devuelve `SessionInvalid` con un motivo de la lista cerrada de once valores; solo
    `account_not_allowed` se traduce a 403, el resto a 401 (BR4.3, BR4.5). No lanza.
    """

    def verify_session(self, credential: str) -> Session | SessionInvalid: ...


class ModelClient(Protocol):
    """C4 (propietaria: u2-model-gateway). Devuelve el resultado, no lanza por fallos del modelo.

    `timeout_seconds` es un número de segundos (puede tener fracciones, BR2.6). Un `ModelError`
    puede traer `reason`, un motivo de lista cerrada que el servicio puede ignorar (BR2.3).
    """

    def invoke(self, prompt: str, timeout_seconds: float) -> ModelResponse | ModelError: ...
