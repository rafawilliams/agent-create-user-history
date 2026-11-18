"""Traducción de errores de AWS a ModelError con tabla fija (BR2.3, BR2.4, NFR4.2).

El texto de AWS puede traer ARN e identificadores de cuenta. Se descarta aquí, en el punto
de captura: el ModelError nuevo se arma solo con valores de las tablas de este archivo y la
excepción original no se encadena ni se guarda en ningún campo.
"""

from __future__ import annotations

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    ReadTimeoutError,
)
from botocore.exceptions import (
    ConnectionError as BotoConnectionError,
)

from story_service.models import ModelError, ModelErrorKind, ModelErrorReason

_K = ModelErrorKind
_R = ModelErrorReason

# Código de error de AWS -> (kind, reason). Lo desconocido es (unavailable, unknown).
_AWS_CODE_TABLE: dict[str, tuple[ModelErrorKind, ModelErrorReason]] = {
    "ThrottlingException": (_K.TRANSIENT, _R.THROTTLED),
    "ServiceQuotaExceededException": (_K.TRANSIENT, _R.THROTTLED),
    "InternalServerException": (_K.TRANSIENT, _R.UNAVAILABLE),
    "ModelNotReadyException": (_K.TRANSIENT, _R.UNAVAILABLE),
    "ModelErrorException": (_K.TRANSIENT, _R.UNAVAILABLE),
    "ModelTimeoutException": (_K.TIMEOUT, _R.TIMEOUT),
    "ServiceUnavailableException": (_K.UNAVAILABLE, _R.UNAVAILABLE),
    "AccessDeniedException": (_K.ACCESS_DENIED, _R.ACCESS_NOT_ENABLED),
    "ResourceNotFoundException": (_K.ACCESS_DENIED, _R.MODEL_NOT_FOUND),
    "ValidationException": (_K.ACCESS_DENIED, _R.INVALID_REQUEST),
}
_UNKNOWN = (_K.UNAVAILABLE, _R.UNKNOWN)

# Mensajes propios por tipo: nunca se copia el detalle de AWS.
MESSAGES_BY_KIND: dict[ModelErrorKind, str] = {
    ModelErrorKind.TRANSIENT: "Fallo pasajero del modelo",
    ModelErrorKind.TIMEOUT: "El modelo no respondió a tiempo",
    ModelErrorKind.UNAVAILABLE: "El modelo no está disponible",
    ModelErrorKind.ACCESS_DENIED: "Sin acceso al modelo configurado",
}


def _build(kind: ModelErrorKind, reason: ModelErrorReason) -> ModelError:
    return ModelError(kind=kind, message=MESSAGES_BY_KIND[kind], reason=reason)


def timeout_error() -> ModelError:
    """El tiempo pedido por el servicio se agotó (BR2.6)."""
    return _build(_K.TIMEOUT, _R.TIMEOUT)


def translate_error(error: BaseException) -> ModelError:
    """Devuelve un ModelError nuevo; no relanza ni conserva la excepción original."""
    if isinstance(error, ReadTimeoutError | ConnectTimeoutError):
        return timeout_error()
    if isinstance(error, ClientError):
        code = error.response.get("Error", {}).get("Code", "")
        return _build(*_AWS_CODE_TABLE.get(code, _UNKNOWN))
    if isinstance(error, BotoConnectionError | BotoCoreError):
        return _build(_K.UNAVAILABLE, _R.UNAVAILABLE)
    return _build(*_UNKNOWN)
