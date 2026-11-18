"""Entidades del esqueleto (entities.md). Ninguna se guarda: viven en la solicitud."""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass
from enum import StrEnum

from story_service.errors import ErrorCode, ServiceError

MAX_TITLE_LENGTH = 200
MAX_CONTEXT_LENGTH = 500
MIN_CRITERIA = 2
MAX_CRITERIA = 3
# Saltos de línea y caracteres de control (categorías Unicode) que pasan a espacios.
_LINE_BREAK_CATEGORIES = frozenset({"Cc", "Zl", "Zp"})


def _require_text(**fields: object) -> None:
    for name, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"El campo obligatorio '{name}' no puede estar vacío")


def normalize_line(value: str) -> str:
    """Recorta, pasa saltos de línea y caracteres de control a espacios y recorta otra vez.

    Orden de la entrada del analista (security-design.md): recortar, normalizar, validar.
    `str.strip` recorta cualquier espacio Unicode; la longitud se mide en puntos de código.
    """
    flattened = "".join(
        " " if unicodedata.category(char) in _LINE_BREAK_CATEGORIES else char
        for char in value.strip()
    )
    return flattened.strip()


@dataclass(frozen=True)
class StoryRequest:
    request_id: str
    title: str
    context: str | None = None

    def __post_init__(self) -> None:
        _require_text(request_id=self.request_id, title=self.title)

    @classmethod
    def create(
        cls, title: object, request_id: str | None = None, context: object = None
    ) -> StoryRequest:
        """Normaliza y valida titulo y contexto (BR3.1, BR3.3, NFR4.4); genera un requestId.

        Un contexto vacio o que no es texto equivale a ausente.
        """
        rid = request_id or str(uuid.uuid4())
        trimmed = normalize_line(title) if isinstance(title, str) else ""
        if not trimmed:
            raise ServiceError(
                ErrorCode.TITLE_EMPTY, "Escribe un título para generar la historia.", request_id=rid
            )
        if len(trimmed) > MAX_TITLE_LENGTH:
            raise ServiceError(
                ErrorCode.TITLE_TOO_LONG,
                f"El título no puede superar {MAX_TITLE_LENGTH} caracteres.",
                request_id=rid,
            )
        clean_context = normalize_line(context) if isinstance(context, str) else ""
        if len(clean_context) > MAX_CONTEXT_LENGTH:
            raise ServiceError(
                ErrorCode.CONTEXT_TOO_LONG,
                f"El contexto no puede superar {MAX_CONTEXT_LENGTH} caracteres.",
                request_id=rid,
            )
        return cls(request_id=rid, title=trimmed, context=clean_context or None)


def _require_line(**fields: object) -> None:
    """Texto no vacío y de una sola línea (Criterion)."""
    _require_text(**fields)
    for name, value in fields.items():
        if "\n" in str(value) or "\r" in str(value):
            raise ValueError(f"El campo '{name}' debe ser de una sola línea")


@dataclass(frozen=True)
class Criterion:
    """Un criterio de aceptación con las tres partes del Gherkin (entities.md)."""

    name: str
    given: str
    when: str
    then: str

    def __post_init__(self) -> None:
        _require_line(name=self.name, given=self.given, when=self.when, then=self.then)


@dataclass(frozen=True)
class StoryDraft:
    """Historia y criterios que propone el modelo, ya validados. El rol no es un atributo."""

    action: str
    benefit: str
    criteria: tuple[Criterion, ...]

    def __post_init__(self) -> None:
        _require_text(action=self.action, benefit=self.benefit)
        if not MIN_CRITERIA <= len(self.criteria) <= MAX_CRITERIA:
            raise ValueError(f"Se esperan de {MIN_CRITERIA} a {MAX_CRITERIA} criterios")


@dataclass(frozen=True)
class StoryResult:
    request_id: str
    markdown: str

    def __post_init__(self) -> None:
        _require_text(request_id=self.request_id, markdown=self.markdown)

    def to_dict(self) -> dict[str, str]:
        return {"requestId": self.request_id, "markdown": self.markdown}


@dataclass(frozen=True)
class ModelResponse:
    text: str
    model_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise ValueError("El campo obligatorio 'text' debe ser texto")
        _require_text(model_id=self.model_id)


class ModelErrorKind(StrEnum):
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    ACCESS_DENIED = "access_denied"


class ModelErrorReason(StrEnum):
    """Motivo de lista cerrada y propia, sin texto de AWS (BR2.3, BR2.4)."""

    ACCESS_NOT_ENABLED = "access_not_enabled"
    MODEL_NOT_FOUND = "model_not_found"
    INVALID_REQUEST = "invalid_request"
    TIMEOUT = "timeout"
    THROTTLED = "throttled"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


def _check_reason(reason: object) -> None:
    if reason not in {item.value for item in ModelErrorReason}:
        raise ValueError("El motivo del error no está en la lista cerrada de motivos")


@dataclass(frozen=True)
class ModelError:
    kind: ModelErrorKind
    message: str
    reason: ModelErrorReason | None = None  # opcional (cambio aditivo de C4); el servicio lo ignora

    def __post_init__(self) -> None:
        _require_text(message=self.message)
        if self.reason is not None:
            _check_reason(self.reason)


class EvaluationOutcome(StrEnum):
    GENERATED = "generated"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class EvaluationResult:
    """Resultado de un modelo para un título de ejemplo (US7.1). Solo vive en el registro."""

    model_id: str
    title: str
    outcome: EvaluationOutcome
    text: str | None = None
    format_ok: bool | None = None
    elapsed_seconds: float | None = None
    reason: ModelErrorReason | None = None

    def __post_init__(self) -> None:
        _require_text(model_id=self.model_id, title=self.title)
        generated = self.outcome == EvaluationOutcome.GENERATED
        if generated and (self.text is None or self.format_ok is None):
            raise ValueError("Un resultado 'generated' exige 'text' y 'format_ok'")
        if not generated and (self.text is not None or self.format_ok is not None):
            raise ValueError("'text' y 'format_ok' solo existen en un resultado 'generated'")
        if generated and self.reason is not None:
            raise ValueError("'reason' solo existe en un resultado 'blocked' o 'failed'")
        if not generated:
            if self.reason is None:
                raise ValueError("Un resultado 'blocked' o 'failed' exige 'reason'")
            _check_reason(self.reason)


@dataclass(frozen=True)
class EvaluationRecord:
    """Registro de la evaluación terminada (AC7.1.2)."""

    evaluated_at: str
    titles: tuple[str, ...]
    results: tuple[EvaluationResult, ...]
    decision: str
    pending_access: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(evaluated_at=self.evaluated_at, decision=self.decision)
        if not self.titles:
            raise ValueError("El campo obligatorio 'titles' no puede estar vacío")
        if not self.results:
            raise ValueError("El campo obligatorio 'results' no puede estar vacío")


PROVIDERS = frozenset({"google", "microsoft"})
_EMAIL_SHAPE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")


@dataclass(frozen=True)
class Session:
    session_id: str
    account_id: str
    provider: str
    expires_at: str

    def __post_init__(self) -> None:
        _require_text(
            session_id=self.session_id,
            account_id=self.account_id,
            provider=self.provider,
            expires_at=self.expires_at,
        )
        if self.provider not in PROVIDERS:
            raise ValueError("El proveedor de la sesión debe ser google o microsoft")


class SessionInvalidReason(StrEnum):
    """Motivo de lista cerrada y propio; nunca copia texto del token (entities.md, C3)."""

    MISSING = "missing"
    MALFORMED = "malformed"
    BAD_SIGNATURE = "bad_signature"
    WRONG_ISSUER = "wrong_issuer"
    WRONG_AUDIENCE = "wrong_audience"
    EXPIRED = "expired"
    WRONG_TOKEN_USE = "wrong_token_use"
    KEYS_UNAVAILABLE = "keys_unavailable"
    NOT_CONFIGURED = "not_configured"
    ACCOUNT_NOT_ALLOWED = "account_not_allowed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SessionInvalid:
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or self.reason not in {
            item.value for item in SessionInvalidReason
        }:
            raise ValueError("El motivo de la sesión no está en la lista cerrada de motivos")


@dataclass(frozen=True)
class AllowedAccount:
    """Un correo permitido: en minúsculas y sin espacios, sin normalizar puntos ni alias (BR4.3)."""

    email: str

    def __post_init__(self) -> None:
        if not isinstance(self.email, str) or self.email != self.email.strip().lower():
            raise ValueError("El correo permitido debe estar en minúsculas y sin espacios")
        if not _EMAIL_SHAPE.match(self.email):
            raise ValueError("El valor de la lista de correos no parece un correo")

    @classmethod
    def create(cls, raw: object) -> AllowedAccount:
        if not isinstance(raw, str):
            raise ValueError("El valor de la lista de correos no parece un correo")
        return cls(email=raw.strip().lower())
