"""Dobles que entrega U1 para que U2 a U6 se construyan en paralelo (BR1.5)."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from story_service.models import ModelError, ModelResponse, Session, SessionInvalid

# Respuesta simulada del modelo con la forma que u3 espera (JSON, BR3.6); el servicio arma el
# Markdown y fija el rol y las palabras clave del Gherkin.
DEFAULT_FAKE_STORY = (
    '{"action": "completar la tarea indicada en el título", '
    '"benefit": "obtener el beneficio esperado de la funcionalidad", '
    '"criteria": [{"name": "Camino feliz", "given": "que la persona está lista", '
    '"when": "completa la tarea", "then": "obtiene el beneficio"}, '
    '{"name": "Datos incompletos", "given": "que faltan datos", '
    '"when": "intenta completar la tarea", "then": "ve un aviso con lo que falta"}]}'
)


@dataclass(frozen=True)
class ModelCall:
    prompt: str
    timeout_seconds: float


class FakeModelClient:
    """Modelo simulado (C4): devuelve resultados fijos, en orden; el ultimo se repite."""

    def __init__(
        self,
        results: Sequence[ModelResponse | ModelError] | None = None,
        on_invoke: Callable[[], None] | None = None,
    ) -> None:
        self._results = list(results or [ModelResponse(DEFAULT_FAKE_STORY, "fake-model")])
        self._on_invoke = on_invoke
        self.calls: list[ModelCall] = []

    def invoke(self, prompt: str, timeout_seconds: float) -> ModelResponse | ModelError:
        self.calls.append(ModelCall(prompt, timeout_seconds))
        index = min(len(self.calls) - 1, len(self._results) - 1)
        if self._on_invoke is not None:
            self._on_invoke()
        return self._results[index]


class SimulatedSessionVerifier:
    """Verificador simulado (C3): acepta toda solicitud. Solo local y pruebas (BR1.5)."""

    def verify_session(self, credential: str) -> Session | SessionInvalid:
        return Session(
            session_id="simulated-session",
            account_id="simulated-account",
            provider="google",
            expires_at="2999-12-31T23:59:59Z",
        )
