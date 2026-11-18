"""Registro estructurado con lista cerrada de campos y metricas por registro (NFR4.2 a NFR4.5)."""

import json
import logging

logger = logging.getLogger("story_service")
# The Lambda runtime leaves the root logger at WARNING; set the level explicitly so the
# request log and the metric records are emitted.
logger.setLevel(logging.INFO)

# Lista cerrada. u3 agrega u3DurationMs e internal_error (observability-design.md de u3);
# u4 agrega authOutcome y authDurationMs (observability-design.md de u4).
_REQUEST_FIELDS = (
    "requestId",
    "outcome",
    "durationMs",
    "modelId",
    "u3DurationMs",
    "internal_error",
    "authOutcome",
    "authDurationMs",
)


def log_request(
    request_id: str,
    outcome: str,
    duration_ms: int,
    model_id: str | None,
    u3_duration_ms: int | None = None,
    internal_error: bool = False,
    auth_outcome: str | None = None,
    auth_duration_ms: int | None = None,
) -> None:
    """Un registro por solicitud. Solo los campos de la lista cerrada; nada de contenido."""
    record: dict[str, object] = {
        "requestId": request_id,
        "outcome": outcome,
        "durationMs": duration_ms,
    }
    if model_id is not None:  # las rutas de sesión (C2) no llaman al modelo
        record["modelId"] = model_id
    if u3_duration_ms is not None:
        record["u3DurationMs"] = u3_duration_ms
    if internal_error:  # solo aparece, verdadero, cuando actua el manejador de errores internos
        record["internal_error"] = True
    if auth_outcome is not None:  # u4: "ok" o un motivo de lista cerrada, nunca datos de la persona
        record["authOutcome"] = auth_outcome
    if auth_duration_ms is not None:
        record["authDurationMs"] = auth_duration_ms
    logger.info(json.dumps({key: record[key] for key in _REQUEST_FIELDS if key in record}))


def emit_metrics(outcome: str, duration_ms: int, model_id: str) -> None:
    """Metricas requests_total, errors_total{code} y generation_duration_ms{model_id}."""
    _metric("requests_total", 1)
    if outcome != "ok":
        _metric("errors_total", 1, code=outcome)
    _metric("generation_duration_ms", duration_ms, model_id=model_id)


def emit_error_metric(outcome: str) -> None:
    """Rutas de sesión (C2): solo errors_total{code}; no hay generación que medir."""
    if outcome != "ok":
        _metric("errors_total", 1, code=outcome)


def _metric(name: str, value: int, **dimensions: str) -> None:
    logger.info(json.dumps({"metric": name, "value": value, **dimensions}))
