"""Pruebas del cliente real de Bedrock con un doble de prueba: nunca se llama a AWS."""

import json
import logging
import time

import pytest
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

from story_service import bedrock_client as bedrock_module
from story_service.bedrock_client import BedrockModelClient
from story_service.models import ModelError, ModelErrorKind, ModelErrorReason, ModelResponse


def aws_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "detalle"}}, "Converse")


class FakeBedrock:
    def __init__(self, response=None, error=None, delay=0.0):
        self.response = response
        self.error = error
        self.delay = delay
        self.requests = []

    def converse(self, **kwargs):
        self.requests.append(kwargs)
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise self.error
        return self.response


def ok_response(text="Como analista de negocio quiero"):
    return {"output": {"message": {"role": "assistant", "content": [{"text": text}]}}}


def test_translates_the_converse_response_into_model_response():
    fake = FakeBedrock(response=ok_response("Como analista de negocio hola"))
    client = BedrockModelClient(model_id="modelo-x", bedrock_client=fake)

    result = client.invoke("PETICION", 50)

    assert result == ModelResponse(text="Como analista de negocio hola", model_id="modelo-x")


def test_sends_model_id_and_prompt_to_bedrock():
    fake = FakeBedrock(response=ok_response())
    BedrockModelClient(model_id="modelo-x", bedrock_client=fake).invoke("PETICION", 50)

    request = fake.requests[0]
    assert request["modelId"] == "modelo-x"
    assert request["messages"][0]["content"][0]["text"] == "PETICION"


@pytest.mark.parametrize(
    ("aws_code", "kind"),
    [
        ("ThrottlingException", ModelErrorKind.TRANSIENT),
        ("ServiceUnavailableException", ModelErrorKind.UNAVAILABLE),
        ("InternalServerException", ModelErrorKind.TRANSIENT),  # tabla de security-design.md
        ("AccessDeniedException", ModelErrorKind.ACCESS_DENIED),
        ("ModelTimeoutException", ModelErrorKind.TIMEOUT),
        ("ValidationException", ModelErrorKind.ACCESS_DENIED),
        ("CodigoDesconocido", ModelErrorKind.UNAVAILABLE),
    ],
)
def test_aws_client_errors_map_to_model_error_kinds(aws_code, kind):
    client = BedrockModelClient(model_id="m", bedrock_client=FakeBedrock(error=aws_error(aws_code)))

    result = client.invoke("p", 50)

    assert isinstance(result, ModelError)
    assert result.kind == kind


def test_botocore_timeouts_map_to_timeout():
    for error in (
        ReadTimeoutError(endpoint_url="https://x"),
        ConnectTimeoutError(endpoint_url="https://x"),
    ):
        client = BedrockModelClient(model_id="m", bedrock_client=FakeBedrock(error=error))
        result = client.invoke("p", 50)
        assert isinstance(result, ModelError) and result.kind == ModelErrorKind.TIMEOUT


def test_call_exceeding_the_per_call_timeout_returns_timeout():
    client = BedrockModelClient(
        model_id="m", bedrock_client=FakeBedrock(response=ok_response(), delay=0.5)
    )

    result = client.invoke("p", 0.05)

    assert isinstance(result, ModelError) and result.kind == ModelErrorKind.TIMEOUT


def test_malformed_response_becomes_an_empty_text_that_the_service_rejects():
    client = BedrockModelClient(model_id="m", bedrock_client=FakeBedrock(response={"output": {}}))

    result = client.invoke("p", 50)

    assert result == ModelResponse(text="", model_id="m")


def test_error_message_does_not_leak_the_aws_detail():
    client = BedrockModelClient(
        model_id="m", bedrock_client=FakeBedrock(error=aws_error("AccessDeniedException"))
    )

    result = client.invoke("p", 50)

    assert "detalle" not in result.message


# ---- u2-model-gateway: configuracion del cliente, un solo intento, tiempo, registro --------------


def test_aws_client_is_created_with_zero_own_retries_and_the_fixed_timeouts(monkeypatch):
    captured = {}

    def fake_boto_client(service, **kwargs):
        captured.update(kwargs, service=service)
        return FakeBedrock()

    monkeypatch.setattr("boto3.client", fake_boto_client)

    BedrockModelClient(model_id="us.anthropic.claude-sonnet-4-6", region="us-east-1")

    config = captured["config"]
    assert captured["service"] == "bedrock-runtime" and captured["region_name"] == "us-east-1"
    assert (config.connect_timeout, config.read_timeout) == (5, 50)
    # total_max_attempts=1 es un solo intento; max_attempts=1 daria un reintento (NFR1.4).
    assert config.retries == {"total_max_attempts": 1}
    assert "aws_access_key_id" not in captured  # solo la cadena de credenciales estandar


def test_a_transient_failure_makes_a_single_call_to_bedrock():
    fake = FakeBedrock(error=aws_error("ThrottlingException"))

    result = BedrockModelClient(model_id="m", bedrock_client=fake).invoke("p", 50)

    assert len(fake.requests) == 1
    assert (result.kind, result.reason) == (ModelErrorKind.TRANSIENT, ModelErrorReason.THROTTLED)


@pytest.mark.parametrize(("requested", "delay"), [(2, 2.6), (0.3, 1.2), (0.75, 1.5)])
def test_control_returns_within_the_requested_time_plus_one_second(requested, delay):
    client = BedrockModelClient(
        model_id="m", bedrock_client=FakeBedrock(response=ok_response(), delay=delay)
    )

    started = time.monotonic()
    result = client.invoke("p", requested)
    elapsed = time.monotonic() - started

    assert isinstance(result, ModelError)
    assert (result.kind, result.reason) == (ModelErrorKind.TIMEOUT, ModelErrorReason.TIMEOUT)
    assert elapsed <= requested + 1.0


@pytest.mark.parametrize("text", ["", "   ", "texto sin la estructura esperada"])
def test_the_text_is_returned_as_is_even_when_empty_or_unstructured(text):
    client = BedrockModelClient(
        model_id="m", bedrock_client=FakeBedrock(response=ok_response(text))
    )

    assert client.invoke("p", 50) == ModelResponse(text=text, model_id="m")


def _call_records(caplog):
    return [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == bedrock_module.CALL_LOGGER_NAME
    ]


def test_each_call_logs_only_model_id_outcome_reason_and_duration(caplog):
    caplog.set_level(logging.DEBUG)
    prompt, answer = "PETICION-SECRETA con titulo", "Como analista de negocio RESPUESTA-SECRETA"
    ok = BedrockModelClient(
        model_id="m-1", bedrock_client=FakeBedrock(response=ok_response(answer))
    )
    denied = BedrockModelClient(
        model_id="m-2", bedrock_client=FakeBedrock(error=aws_error("AccessDeniedException"))
    )

    ok.invoke(prompt, 50)
    denied.invoke(prompt, 50)

    first, second = _call_records(caplog)
    keys = {"modelId", "outcome", "reason", "durationMs"}
    assert set(first) == keys and set(second) == keys
    assert (first["modelId"], first["outcome"], first["reason"]) == ("m-1", "ok", None)
    assert (second["modelId"], second["outcome"], second["reason"]) == (
        "m-2",
        "access_denied",
        "access_not_enabled",
    )
    assert isinstance(first["durationMs"], int)
    everything = "\n".join(record.getMessage() for record in caplog.records)
    assert "SECRETA" not in everything and "detalle" not in everything


def test_a_timeout_is_logged_with_its_reason(caplog):
    caplog.set_level(logging.INFO)
    client = BedrockModelClient(
        model_id="m", bedrock_client=FakeBedrock(response=ok_response(), delay=0.4)
    )

    client.invoke("p", 0.05)

    (record,) = _call_records(caplog)
    assert (record["outcome"], record["reason"]) == ("timeout", "timeout")


def test_aws_arn_and_account_id_reach_neither_the_result_nor_any_log(caplog):
    arn = "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude-x"
    for name in ("boto3", "botocore"):
        logging.getLogger(name).setLevel(logging.DEBUG)  # el cliente debe subirlos
    caplog.set_level(logging.DEBUG)
    error = ClientError({"Error": {"Code": "AccessDeniedException", "Message": arn}}, "Converse")

    result = BedrockModelClient(model_id="m", bedrock_client=FakeBedrock(error=error)).invoke(
        "p", 50
    )

    visible = repr(result) + "\n".join(r.getMessage() for r in caplog.records)
    assert arn not in visible and "123456789012" not in visible


def test_sdk_loggers_stay_at_warning_or_above():
    for name in ("boto3", "botocore"):
        logging.getLogger(name).setLevel(logging.DEBUG)

    BedrockModelClient(model_id="m", bedrock_client=FakeBedrock())

    assert logging.getLogger("boto3").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("botocore").getEffectiveLevel() >= logging.WARNING
