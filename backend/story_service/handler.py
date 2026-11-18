"""Entrada de la funcion Lambda detras de la pasarela REST (C1: POST /v1/stories; C2: GET y
DELETE /v1/session)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping
from typing import Any

from story_service.bedrock_client import BedrockModelClient
from story_service.config import Settings, build_session_verifier
from story_service.errors import ErrorCode, ServiceError
from story_service.service import SERVICE_DEADLINE_SECONDS, StoryService

_SAFETY_MARGIN_SECONDS = 1.0
_BEARER = re.compile(r"^\s*bearer\s+(.+?)\s*$", re.IGNORECASE)
_SESSION_PATH = "/v1/session"
_SESSION_INVALID_MESSAGE = "Tu sesión no es válida. Inicia sesión de nuevo."

Handler = Callable[[dict[str, Any], Any], dict[str, Any]]


def _header(headers: Mapping[str, str] | None, name: str) -> str | None:
    for key, value in (headers or {}).items():
        if key.lower() == name.lower():
            return value
    return None


def _bearer_token(headers: Mapping[str, str] | None) -> str:
    value = _header(headers, "Authorization") or ""
    match = _BEARER.match(value)
    return match.group(1) if match else ""


def _cors_headers(headers: Mapping[str, str] | None, allowed_origin: str) -> dict[str, str]:
    origin = _header(headers, "Origin")
    if allowed_origin and origin == allowed_origin:
        return {
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
            "Vary": "Origin",
        }
    return {}


def _fields_from_body(raw_body: str | None) -> tuple[object, object]:
    """`title` y el `context` opcional del cuerpo; el servicio los valida (BR3.1 a BR3.3)."""
    try:
        parsed = json.loads(raw_body or "")
    except (TypeError, ValueError):
        return None, None
    if not isinstance(parsed, dict):
        return None, None
    return parsed.get("title"), parsed.get("context")


def _response(status: int, body: dict[str, object] | None, extra: dict[str, str]) -> dict:
    headers = {"Content-Type": "application/json", **extra}
    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(body, ensure_ascii=False) if body is not None else "",
    }


def _is_session_route(event: Mapping[str, Any]) -> bool:
    path = str(event.get("path") or event.get("resource") or "").rstrip("/")
    return path.endswith(_SESSION_PATH)


def _session_response(
    service: Any, method: str, headers: Mapping[str, str] | None, cors: dict[str, str]
) -> dict[str, Any]:
    """C2: GET devuelve la identidad (sin correo ni token) y DELETE cierra la sesión (BR4.6)."""
    if method not in ("GET", "DELETE"):
        message = {"message": "Método no permitido."}
        return _response(405, message, {**cors, "Allow": "GET,DELETE,OPTIONS"})
    try:
        if method == "DELETE":
            service.end_session(_bearer_token(headers))
            return _response(204, None, cors)
        session = service.get_session(_bearer_token(headers))
        body = {
            "sessionId": session.session_id,
            "accountId": session.account_id,
            "provider": session.provider,
            "expiresAt": session.expires_at,
        }
        return _response(200, body, cors)
    except ServiceError as error:
        return _response(error.http_status, error.to_body(), cors)
    except Exception:  # falla cerrado: sin traza ni detalle interno
        fallback = ServiceError(ErrorCode.SESSION_INVALID, _SESSION_INVALID_MESSAGE)
        return _response(fallback.http_status, fallback.to_body(), cors)


def create_handler(service: Any, settings: Settings) -> Handler:
    def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
        headers = event.get("headers")
        cors = _cors_headers(headers, settings.cors_allowed_origin)
        method = str(event.get("httpMethod", "")).upper()
        if method == "OPTIONS":
            return {"statusCode": 204, "headers": cors, "body": ""}
        if _is_session_route(event):
            return _session_response(service, method, headers, cors)
        remaining = context.get_remaining_time_in_millis() / 1000 - _SAFETY_MARGIN_SECONDS
        deadline = max(0.0, min(SERVICE_DEADLINE_SECONDS, remaining))
        title, context_text = _fields_from_body(event.get("body"))
        try:
            result = service.generate(
                _bearer_token(headers), title, deadline_seconds=deadline, context=context_text
            )
            return _response(200, result.to_dict(), cors)
        except ServiceError as error:
            return _response(error.http_status, error.to_body(), cors)
        except Exception:  # nunca se devuelve una traza al cliente
            fallback = ServiceError(
                ErrorCode.MODEL_FAILURE,
                "No se pudo generar la historia. Inténtalo de nuevo más tarde.",
                retryable=False,
            )
            return _response(fallback.http_status, fallback.to_body(), cors)

    return handler


_cached_handler: Handler | None = None


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Punto de entrada de Lambda. La composicion se arma una vez por instancia."""
    global _cached_handler
    if _cached_handler is None:
        settings = Settings.from_env(os.environ)
        service = StoryService(
            session_verifier=build_session_verifier(settings),
            model_client=BedrockModelClient(
                settings.model_id,
                settings.region,
                read_timeout_seconds=settings.timeout_seconds,
            ),
            instructions=settings.instructions,
            model_id=settings.model_id,
        )
        _cached_handler = create_handler(service, settings)
    return _cached_handler(event, context)
