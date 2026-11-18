"""Comando de evaluación de modelos (US7.1). Se ejecuta a mano, nunca en CI ni en el servicio.

Uso (desde backend/):
    python -m story_service.evaluate_models approve   # la persona aprueba los 5 títulos
    python -m story_service.evaluate_models run       # llama a Bedrock con la cuenta local

`run` se niega si el archivo de títulos no tiene exactamente 5 títulos con la aprobación
vigente (NFR4.3). Escribe un solo archivo: `docs/evaluacion-modelos.md` (NFR4.1). Los modelos
se leen de EVALUATION_MODEL_IDS (lista separada por comas); el modelo por defecto del proyecto
siempre se evalúa. Las credenciales son las de la cadena estándar de AWS (NFR5.1).
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from story_service.bedrock_client import BedrockModelClient
from story_service.config import DEFAULT_MODEL_ID, DEFAULT_TIMEOUT_SECONDS, Settings
from story_service.evaluation import (
    TitlesFileError,
    approve_titles,
    build_record,
    evaluate,
    load_approved_titles,
    write_record,
)
from story_service.model_profile import ModelProfile
from story_service.ports import ModelClient

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TITLES_PATH = _ROOT / "docs" / "titulos-evaluacion.md"
DEFAULT_RECORD_PATH = _ROOT / "docs" / "evaluacion-modelos.md"
# El identificador de Titan se confirma contra los perfiles de la cuenta antes de la primera
# ejecución real; mientras tanto, este valor es la propuesta.
DEFAULT_EVALUATION_MODEL_IDS = f"{DEFAULT_MODEL_ID},us.amazon.titan-text-premier-v1:0"

ClientFactory = Callable[[str, str], ModelClient]


def _default_factory(model_id: str, region: str) -> ModelClient:
    return BedrockModelClient(model_id, region)


def _model_ids(env: Mapping[str, str]) -> list[str]:
    configured = (env.get("EVALUATION_MODEL_IDS") or DEFAULT_EVALUATION_MODEL_IDS).split(",")
    ids = [DEFAULT_MODEL_ID]  # el modelo por defecto siempre se evalúa (BR2.8)
    for model_id in (item.strip() for item in configured if item.strip()):
        ModelProfile.from_model_id(model_id)  # lista cerrada, antes de cualquier llamada
        if model_id not in ids:
            ids.append(model_id)
    return ids


def main(
    argv: Sequence[str],
    env: Mapping[str, str] | None = None,
    client_factory: ClientFactory | None = None,
    titles_path: Path | None = None,
    record_path: Path | None = None,
    clock: Callable[[], float] = time.monotonic,
    now: Callable[[], str] | None = None,
) -> int:
    env = os.environ if env is None else env
    titles_path = titles_path or DEFAULT_TITLES_PATH
    record_path = record_path or DEFAULT_RECORD_PATH
    args = list(argv)
    if len(args) != 1 or args[0] not in ("approve", "run"):
        print("Uso: python -m story_service.evaluate_models approve|run", file=sys.stderr)
        return 2
    try:
        if args[0] == "approve":
            fingerprint = approve_titles(titles_path)
            print(f"Títulos aprobados (huella {fingerprint}).")
            return 0
        titles = load_approved_titles(titles_path)
        model_ids = _model_ids(env)
        settings = Settings.from_env(env)
    except (TitlesFileError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    factory = client_factory or _default_factory
    models = [(model_id, factory(model_id, settings.region)) for model_id in model_ids]
    results = evaluate(
        models,
        titles,
        settings.instructions,
        clock=clock,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    evaluated_at = now() if now else datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = build_record(results, titles, evaluated_at, DEFAULT_MODEL_ID)
    write_record(record_path, record)
    print(f"Registro escrito en {record_path}. Decisión: {record.decision}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
