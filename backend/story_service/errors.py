"""Errores del contrato C1 y tabla de traduccion de fallos del modelo (BR1.4)."""

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from story_service.models import ModelError


class ErrorCode(StrEnum):
    TITLE_EMPTY = "TITLE_EMPTY"
    TITLE_TOO_LONG = "TITLE_TOO_LONG"
    CONTEXT_TOO_LONG = "CONTEXT_TOO_LONG"  # cambio aditivo de C1 (u3, BR3.3)
    NEEDS_CONTEXT = "NEEDS_CONTEXT"  # C1: título corto o ambiguo (u3, BR3.2)
    SESSION_INVALID = "SESSION_INVALID"
    ACCOUNT_NOT_ALLOWED = "ACCOUNT_NOT_ALLOWED"  # cambio aditivo de C1 y C2 (u4, BR4.3)
    RATE_LIMITED = "RATE_LIMITED"
    MODEL_FAILURE = "MODEL_FAILURE"
    INVALID_MODEL_RESPONSE = "INVALID_MODEL_RESPONSE"
    GENERATION_TIMEOUT = "GENERATION_TIMEOUT"


# code -> (HTTP status, retryable por defecto)
_CODE_TABLE: dict[ErrorCode, tuple[int, bool]] = {
    ErrorCode.TITLE_EMPTY: (400, False),
    ErrorCode.TITLE_TOO_LONG: (400, False),
    ErrorCode.CONTEXT_TOO_LONG: (400, False),
    ErrorCode.NEEDS_CONTEXT: (422, False),
    ErrorCode.SESSION_INVALID: (401, False),
    ErrorCode.ACCOUNT_NOT_ALLOWED: (403, False),
    ErrorCode.RATE_LIMITED: (429, True),
    ErrorCode.MODEL_FAILURE: (502, True),
    ErrorCode.INVALID_MODEL_RESPONSE: (502, True),
    ErrorCode.GENERATION_TIMEOUT: (504, True),
}

# kind del ModelError -> (codigo C1, retryable); BR1.4
# Las claves son los valores de ModelErrorKind (StrEnum, igual que su texto).
_MODEL_KIND_TABLE: dict[str, tuple[ErrorCode, bool]] = {
    "transient": (ErrorCode.MODEL_FAILURE, True),
    "timeout": (ErrorCode.GENERATION_TIMEOUT, True),
    "unavailable": (ErrorCode.MODEL_FAILURE, True),
    "access_denied": (ErrorCode.MODEL_FAILURE, False),
}

_MODEL_FAILURE_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.MODEL_FAILURE: "No se pudo generar la historia por un fallo del modelo.",
    ErrorCode.GENERATION_TIMEOUT: "La generación superó el tiempo máximo. Inténtalo de nuevo.",
}


class ServiceError(Exception):
    """Error del servicio con la forma del cuerpo de error de C1."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        retryable: bool | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        status, default_retryable = _CODE_TABLE[code]
        self.code = code
        self.message = message
        self.http_status = status
        self.retryable = default_retryable if retryable is None else retryable
        self.request_id = request_id

    def to_body(self) -> dict[str, object]:
        body: dict[str, object] = {
            "code": self.code.value,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.request_id is not None:
            body["requestId"] = self.request_id
        return body


def error_from_model_error(error: "ModelError", request_id: str | None) -> ServiceError:
    """Traduce un ModelError al error de C1 (BR1.4). No expone el detalle interno."""
    code, retryable = _MODEL_KIND_TABLE[error.kind]
    return ServiceError(
        code,
        _MODEL_FAILURE_MESSAGES[code],
        retryable=retryable,
        request_id=request_id,
    )
