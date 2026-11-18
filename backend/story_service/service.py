"""Servicio de generacion: sesion, validacion, peticion al modelo, plazo y reintento acotado.

u3 completa la generacion: valida el titulo y el contexto, trata el contenido como dato,
interpreta el JSON del modelo y arma el Markdown (BR3.1 a BR3.10).
"""

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from story_service.errors import ErrorCode, ServiceError, error_from_model_error
from story_service.input_validation import validate_story_input
from story_service.logging_utils import emit_error_metric, emit_metrics, log_request
from story_service.markdown_builder import build_markdown
from story_service.models import (
    ModelError,
    ModelErrorKind,
    ModelResponse,
    Session,
    SessionInvalid,
    SessionInvalidReason,
    StoryRequest,
    StoryResult,
)
from story_service.ports import ModelClient, SessionVerifier
from story_service.prompt import build_prompt
from story_service.response_parsing import parse_story_draft

SERVICE_DEADLINE_SECONDS = 55.0
MODEL_TIMEOUT_SECONDS = 50.0
_RETRYABLE_KINDS = (ModelErrorKind.TRANSIENT, ModelErrorKind.UNAVAILABLE)
_INTERNAL_ERROR_MESSAGE = "No se pudo generar la historia por un fallo del modelo."


@dataclass
class _AuthTrace:
    """Resultado y duración de la verificación de una solicitud; vive solo dentro de ella."""

    outcome: str | None = None
    duration_ms: int | None = None


class StoryService:
    """Sin estado entre solicitudes (NFR3.1): todo el estado vive dentro de `generate`."""

    def __init__(
        self,
        session_verifier: SessionVerifier,
        model_client: ModelClient,
        instructions: str,
        clock: Callable[[], float] = time.monotonic,
        model_id: str = "unknown",
    ) -> None:
        self._session_verifier = session_verifier
        self._model_client = model_client
        self._instructions = instructions
        self._clock = clock
        self._model_id = model_id

    def generate(
        self,
        credential: str | None,
        title: object,
        deadline_seconds: float = SERVICE_DEADLINE_SECONDS,
        request_id: str | None = None,
        context: object = None,
    ) -> StoryResult:
        """Devuelve el resultado o lanza ServiceError (nunca un resultado vacio)."""
        started = self._clock()
        rid = request_id or str(uuid.uuid4())
        model_id = self._model_id
        outcome = "ok"
        internal_error = False
        u3_seconds = 0.0  # tiempo de la logica propia: sin la sesion ni la espera del modelo
        trace = _AuthTrace()
        try:
            self._check_session(credential, rid, trace)
            mark = self._clock()
            request = validate_story_input(title, context, request_id=rid)
            prompt = build_prompt(self._instructions, request.title, request.context)
            u3_seconds += self._clock() - mark
            response = self._call_model(
                request, prompt, started + min(deadline_seconds, SERVICE_DEADLINE_SECONDS)
            )
            model_id = response.model_id
            mark = self._clock()
            draft = parse_story_draft(response.text, rid)
            markdown = build_markdown(request.title, draft)
            u3_seconds += self._clock() - mark
            return StoryResult(request_id=rid, markdown=markdown)
        except ServiceError as error:
            outcome = error.code.value
            raise
        except Exception:  # defecto de u3: nunca se filtra una traza ni un detalle interno
            outcome = ErrorCode.MODEL_FAILURE.value
            internal_error = True
            raise ServiceError(
                ErrorCode.MODEL_FAILURE,
                _INTERNAL_ERROR_MESSAGE,
                retryable=False,
                request_id=rid,
            ) from None
        finally:
            duration_ms = int((self._clock() - started) * 1000)
            log_request(
                rid,
                outcome,
                duration_ms,
                model_id,
                u3_duration_ms=int(u3_seconds * 1000),
                internal_error=internal_error,
                auth_outcome=trace.outcome,
                auth_duration_ms=trace.duration_ms,
            )
            emit_metrics(outcome, duration_ms, model_id)

    def get_session(self, credential: str | None, request_id: str | None = None) -> Session:
        """C2 `GET /v1/session`: la identidad de la sesión, o ServiceError (401 o 403)."""
        return self._session_operation(credential, request_id)

    def end_session(self, credential: str | None, request_id: str | None = None) -> None:
        """C2 `DELETE /v1/session`: no guarda sesiones; solo exige una válida (BR4.6)."""
        self._session_operation(credential, request_id)

    def _session_operation(self, credential: str | None, request_id: str | None) -> Session:
        started = self._clock()
        rid = request_id or str(uuid.uuid4())
        trace = _AuthTrace()
        outcome = "ok"
        try:
            return self._check_session(credential, rid, trace)
        except ServiceError as error:
            outcome = error.code.value
            raise
        finally:
            log_request(
                rid,
                outcome,
                int((self._clock() - started) * 1000),
                None,
                auth_outcome=trace.outcome,
                auth_duration_ms=trace.duration_ms,
            )
            emit_error_metric(outcome)

    def _check_session(
        self, credential: str | None, request_id: str, trace: "_AuthTrace | None" = None
    ) -> Session:
        """Verifica la credencial y falla cerrado. account_not_allowed es 403; el resto, 401."""
        trace = trace or _AuthTrace()
        started = self._clock()
        try:
            verdict = self._session_verifier.verify_session(credential or "")
        except Exception:
            verdict = SessionInvalid(reason=SessionInvalidReason.UNKNOWN)  # falla cerrado
        trace.duration_ms = int((self._clock() - started) * 1000)
        if isinstance(verdict, SessionInvalid):
            trace.outcome = verdict.reason
            if verdict.reason == SessionInvalidReason.ACCOUNT_NOT_ALLOWED:
                raise ServiceError(
                    ErrorCode.ACCOUNT_NOT_ALLOWED,
                    "Tu cuenta no tiene permiso para usar esta aplicación. "
                    "Inicia sesión con otra cuenta.",
                    request_id=request_id,
                )
            raise ServiceError(  # el mismo cuerpo para todo rechazo de token (NFR4.4)
                ErrorCode.SESSION_INVALID,
                "Tu sesión no es válida. Inicia sesión de nuevo.",
                request_id=request_id,
            )
        trace.outcome = "ok"
        return verdict

    def _call_model(self, request: StoryRequest, prompt: str, deadline: float) -> ModelResponse:
        retried = False
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise self._timeout(request.request_id)
            try:
                result = self._model_client.invoke(prompt, min(MODEL_TIMEOUT_SECONDS, remaining))
            except Exception as unexpected:
                raise ServiceError(
                    ErrorCode.MODEL_FAILURE,
                    _INTERNAL_ERROR_MESSAGE,
                    retryable=False,
                    request_id=request.request_id,
                ) from unexpected
            if isinstance(result, ModelResponse):
                return result
            if result.kind in _RETRYABLE_KINDS and not retried:
                retried = True
                continue  # el siguiente giro vuelve a comprobar el tiempo que queda
            raise error_from_model_error(result, request.request_id)

    @staticmethod
    def _timeout(request_id: str) -> ServiceError:
        return error_from_model_error(
            ModelError(ModelErrorKind.TIMEOUT, "plazo agotado"), request_id
        )
