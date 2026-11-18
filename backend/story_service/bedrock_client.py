"""Cliente real de Amazon Bedrock (C4). El modelo y la region vienen de la configuracion."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any

from story_service.error_translation import timeout_error, translate_error
from story_service.models import ModelError, ModelResponse

MAX_TOKENS = 1024
_CONNECT_TIMEOUT_SECONDS = 5
_READ_TIMEOUT_SECONDS = 50
_MAX_POOL_CONNECTIONS = 10  # cubre la concurrencia maxima de 5 mas los hilos abandonados
CALL_LOGGER_NAME = "story_service.model_call"
_SDK_LOGGERS = ("boto3", "botocore")

_call_logger = logging.getLogger(CALL_LOGGER_NAME)


def _keep_sdk_loggers_quiet() -> None:
    """Los registros de depuracion del SDK pueden llevar la peticion: minimo WARNING."""
    for name in _SDK_LOGGERS:
        sdk_logger = logging.getLogger(name)
        if sdk_logger.getEffectiveLevel() < logging.WARNING:
            sdk_logger.setLevel(logging.WARNING)


def _create_runtime_client(region: str, read_timeout_seconds: float = _READ_TIMEOUT_SECONDS) -> Any:
    import boto3
    from botocore.config import Config

    # Solo la cadena de credenciales estandar del SDK (NFR5.1): no se pasan claves.
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(
            connect_timeout=_CONNECT_TIMEOUT_SECONDS,
            read_timeout=read_timeout_seconds,
            # Un solo intento en total: `max_attempts=1` daria un reintento (NFR1.4). El unico
            # reintento lo decide el servicio (NFR1.6).
            retries={"total_max_attempts": 1},
            max_pool_connections=_MAX_POOL_CONNECTIONS,
        ),
    )


class BedrockModelClient:
    """El cliente `bedrock-runtime` se crea una vez por instancia y se reutiliza."""

    def __init__(
        self,
        model_id: str,
        region: str = "us-east-1",
        bedrock_client: Any | None = None,
        read_timeout_seconds: float = _READ_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        _keep_sdk_loggers_quiet()
        self._model_id = model_id
        self._clock = clock
        self._client = bedrock_client or _create_runtime_client(region, read_timeout_seconds)

    def invoke(self, prompt: str, timeout_seconds: float) -> ModelResponse | ModelError:
        # El tiempo de espera de lectura del cliente es fijo; el limite por llamada (menor
        # cuando queda poco plazo, y con fracciones) se aplica esperando el resultado con ese
        # limite sobre un hilo de trabajo (BR2.6, NFR1.1).
        started = self._clock()
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._converse, prompt)
        try:
            result = future.result(timeout=timeout_seconds)
        except FutureTimeout:
            result = timeout_error()
        finally:
            executor.shutdown(wait=False)
        self._log_call(result, started)
        return result

    def _converse(self, prompt: str) -> ModelResponse | ModelError:
        try:
            response = self._client.converse(
                modelId=self._model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": MAX_TOKENS},
            )
        except Exception as error:
            # Devuelve un ModelError nuevo; el texto de AWS no se conserva (NFR4.2).
            return translate_error(error)
        return ModelResponse(text=self._extract_text(response), model_id=self._model_id)

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        content = response.get("output", {}).get("message", {}).get("content", [])
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))

    def _log_call(self, result: ModelResponse | ModelError, started: float) -> None:
        """Cuatro campos por llamada y nada mas (NFR4.2). Si falla, la llamada sigue."""
        try:
            failed = isinstance(result, ModelError)
            _call_logger.info(
                json.dumps(
                    {
                        "modelId": self._model_id,
                        "outcome": result.kind.value if failed else "ok",
                        "reason": result.reason.value if failed and result.reason else None,
                        "durationMs": int((self._clock() - started) * 1000),
                    }
                )
            )
        except Exception:  # pragma: no cover - el registro nunca rompe la llamada
            pass
