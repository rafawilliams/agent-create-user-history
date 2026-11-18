"""Registros estructurados y metricas (NFR4.2, NFR4.3, NFR1.4, NFR3.3, NFR4.5)."""

import json
import logging

import pytest

from story_service.errors import ServiceError
from story_service.fakes import FakeModelClient
from story_service.models import ModelError, ModelErrorKind, ModelResponse
from tests.helpers import VALID_JSON, build_service

# u3 (BR3.2): dos palabras y mas de 12 caracteres, para que el titulo no pida contexto.
TITLE = "Titulo-secreto del-usuario"
CREDENTIAL = "Bearer token-super-secreto"


def test_service_logger_emits_info_without_external_configuration():
    # In AWS Lambda the root logger defaults to WARNING; without an explicit level the
    # request log and the metrics would never be emitted (NFR1.4, NFR3.3, NFR4.5).
    assert logging.getLogger("story_service").getEffectiveLevel() <= logging.INFO


def _records(caplog):
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == "story_service"]


def test_request_log_has_only_the_closed_field_list(caplog):
    caplog.set_level(logging.INFO, logger="story_service")
    model = FakeModelClient(results=[ModelResponse(text=VALID_JSON, model_id="m-1")])

    build_service(model).generate(CREDENTIAL, TITLE)

    request_logs = [r for r in _records(caplog) if "outcome" in r]
    assert len(request_logs) == 1
    # u3 amplia la lista cerrada con u3DurationMs (observability-design.md); internal_error
    # solo aparece cuando el manejador de errores internos actua. u4 agrega authOutcome y
    # authDurationMs (observability-design.md de u4).
    assert set(request_logs[0]) == {
        "requestId",
        "outcome",
        "durationMs",
        "modelId",
        "u3DurationMs",
        "authOutcome",
        "authDurationMs",
    }
    assert request_logs[0]["authOutcome"] == "ok"
    assert isinstance(request_logs[0]["u3DurationMs"], int)
    assert request_logs[0]["outcome"] == "ok"
    assert request_logs[0]["modelId"] == "m-1"
    assert isinstance(request_logs[0]["durationMs"], int)


def test_no_record_contains_title_markdown_or_authorization(caplog):
    caplog.set_level(logging.DEBUG)
    model = FakeModelClient(results=[ModelResponse(text=VALID_JSON, model_id="m-1")])

    build_service(model).generate(CREDENTIAL, TITLE)

    everything = "\n".join(r.getMessage() for r in caplog.records)
    assert TITLE not in everything
    assert VALID_JSON not in everything
    assert "token-super-secreto" not in everything
    assert "Authorization" not in everything


def test_error_log_carries_the_error_code_and_no_content(caplog):
    caplog.set_level(logging.DEBUG)
    model = FakeModelClient(results=[ModelError(kind=ModelErrorKind.ACCESS_DENIED, message="x")])

    with pytest.raises(ServiceError):
        build_service(model).generate(CREDENTIAL, TITLE)

    records = _records(caplog)
    request_log = next(r for r in records if "outcome" in r)
    assert request_log["outcome"] == "MODEL_FAILURE"
    assert TITLE not in json.dumps(records)


def test_metrics_requests_errors_and_duration_are_emitted_without_content(caplog):
    caplog.set_level(logging.INFO, logger="story_service")
    ok_model = FakeModelClient(results=[ModelResponse(text=VALID_JSON, model_id="m-1")])
    build_service(ok_model).generate(CREDENTIAL, TITLE)
    bad_model = FakeModelClient(results=[ModelError(kind=ModelErrorKind.TIMEOUT, message="x")])
    with pytest.raises(ServiceError):
        build_service(bad_model).generate(CREDENTIAL, TITLE)

    metrics = [r for r in _records(caplog) if "metric" in r]
    names = [m["metric"] for m in metrics]
    assert names.count("requests_total") == 2
    assert names.count("generation_duration_ms") == 2
    errors = [m for m in metrics if m["metric"] == "errors_total"]
    assert [e["code"] for e in errors] == ["GENERATION_TIMEOUT"]
    assert TITLE not in json.dumps(metrics)
