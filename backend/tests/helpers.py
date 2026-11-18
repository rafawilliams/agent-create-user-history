"""Ayudas de prueba: reloj inyectable y construccion del servicio con dobles."""

import json

from story_service.fakes import FakeModelClient, SimulatedSessionVerifier
from story_service.service import StoryService

VALID_STORY = (
    "Como analista de negocio quiero recuperar mi contraseña para volver a entrar.\n\n"
    "Escenario: Recuperación\n  Dado que olvidé mi contraseña\n  Cuando la solicito\n"
    "  Entonces recibo un enlace"
)


def draft_dict(**overrides) -> dict:
    """Respuesta valida del modelo (u3): JSON con accion, beneficio y 2 criterios."""
    values = {
        "action": "poder recuperar mi contraseña",
        "benefit": "volver a entrar a mi cuenta con el acceso de siempre",
        "criteria": [
            {
                "name": "Recuperación con correo registrado",
                "given": "que la persona olvidó su contraseña",
                "when": "solicita el enlace de recuperación",
                "then": "recibe un correo con el enlace",
            },
            {
                "name": "Correo desconocido",
                "given": "que el correo no está registrado",
                "when": "solicita el enlace",
                "then": "ve un aviso sin revelar si la cuenta existe",
            },
        ],
    }
    values.update(overrides)
    return values


VALID_JSON = json.dumps(draft_dict(), ensure_ascii=False)


class FakeClock:
    """Reloj monotono controlable para probar el plazo sin esperar."""

    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def build_service(model: FakeModelClient, verifier=None, clock=None, **kwargs) -> StoryService:
    return StoryService(
        session_verifier=verifier or SimulatedSessionVerifier(),
        model_client=model,
        instructions=kwargs.pop("instructions", "INSTRUCCIONES FIJAS"),
        clock=clock or FakeClock(),
        model_id="test-model",
        **kwargs,
    )
