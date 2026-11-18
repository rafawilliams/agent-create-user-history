"""Pruebas de la traducción de errores de AWS (BR2.3, BR2.4, NFR4.2)."""

import logging

import pytest
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from story_service.error_translation import MESSAGES_BY_KIND, timeout_error, translate_error
from story_service.models import ModelError, ModelErrorKind, ModelErrorReason

ARN = "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude-x"
ACCOUNT_ID = "123456789012"


def aws_error(code: str, message: str = "detalle de AWS") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "Converse")


@pytest.mark.parametrize(
    ("aws_code", "kind", "reason"),
    [
        ("ThrottlingException", ModelErrorKind.TRANSIENT, ModelErrorReason.THROTTLED),
        ("ServiceQuotaExceededException", ModelErrorKind.TRANSIENT, ModelErrorReason.THROTTLED),
        ("InternalServerException", ModelErrorKind.TRANSIENT, ModelErrorReason.UNAVAILABLE),
        ("ModelNotReadyException", ModelErrorKind.TRANSIENT, ModelErrorReason.UNAVAILABLE),
        ("ModelErrorException", ModelErrorKind.TRANSIENT, ModelErrorReason.UNAVAILABLE),
        ("ModelTimeoutException", ModelErrorKind.TIMEOUT, ModelErrorReason.TIMEOUT),
        ("ServiceUnavailableException", ModelErrorKind.UNAVAILABLE, ModelErrorReason.UNAVAILABLE),
        (
            "AccessDeniedException",
            ModelErrorKind.ACCESS_DENIED,
            ModelErrorReason.ACCESS_NOT_ENABLED,
        ),
        (
            "ResourceNotFoundException",
            ModelErrorKind.ACCESS_DENIED,
            ModelErrorReason.MODEL_NOT_FOUND,
        ),
        ("ValidationException", ModelErrorKind.ACCESS_DENIED, ModelErrorReason.INVALID_REQUEST),
    ],
)
def test_each_aws_code_in_the_table_gives_its_kind_and_reason(aws_code, kind, reason):
    result = translate_error(aws_error(aws_code))

    assert (result.kind, result.reason) == (kind, reason)
    assert result.message == MESSAGES_BY_KIND[kind]


def test_unknown_aws_code_becomes_unavailable_unknown():
    result = translate_error(aws_error("CodigoQueNadieConoce"))

    assert (result.kind, result.reason) == (ModelErrorKind.UNAVAILABLE, ModelErrorReason.UNKNOWN)


def test_error_without_an_aws_code_is_translated_by_its_type():
    timeouts = [
        ReadTimeoutError(endpoint_url="https://x"),
        ConnectTimeoutError(endpoint_url="https://x"),
    ]
    for error in timeouts:
        result = translate_error(error)
        assert (result.kind, result.reason) == (ModelErrorKind.TIMEOUT, ModelErrorReason.TIMEOUT)

    network = translate_error(EndpointConnectionError(endpoint_url="https://x"))
    assert (network.kind, network.reason) == (
        ModelErrorKind.UNAVAILABLE,
        ModelErrorReason.UNAVAILABLE,
    )
    other = translate_error(RuntimeError("algo raro"))
    assert (other.kind, other.reason) == (ModelErrorKind.UNAVAILABLE, ModelErrorReason.UNKNOWN)


def test_requested_time_exhausted_is_a_timeout_error():
    result = timeout_error()

    assert (result.kind, result.reason) == (ModelErrorKind.TIMEOUT, ModelErrorReason.TIMEOUT)
    assert result.message == MESSAGES_BY_KIND[ModelErrorKind.TIMEOUT]


def test_messages_are_own_texts_one_per_kind():
    assert set(MESSAGES_BY_KIND) == set(ModelErrorKind)
    assert all(text.strip() for text in MESSAGES_BY_KIND.values())


@pytest.mark.parametrize(
    "code",
    ["AccessDeniedException", "ValidationException", "ThrottlingException", "Desconocido"],
)
def test_aws_text_with_arn_and_account_never_reaches_the_error_or_the_logs(code, caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="boto3")
    caplog.set_level(logging.DEBUG, logger="botocore")

    result = translate_error(
        aws_error(code, f"User is not authorized on {ARN} account {ACCOUNT_ID}")
    )

    assert isinstance(result, ModelError)
    visible = repr(result) + "\n".join(record.getMessage() for record in caplog.records)
    assert ARN not in visible and ACCOUNT_ID not in visible
    assert result.message in MESSAGES_BY_KIND.values()


def test_translation_returns_a_new_error_and_does_not_chain_the_original():
    original = aws_error("AccessDeniedException", ARN)

    result = translate_error(original)

    # Un ModelError no es una excepcion: no hay causa ni contexto que guardar.
    assert not isinstance(result, BaseException)
    assert all(ARN not in str(value) for value in vars(result).values())
