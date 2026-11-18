"""Comando local de punta a punta contra Amazon Bedrock (NFR1.3, comprobacion manual).

Uso (desde backend/, con credenciales de AWS validas):
    python -m story_service.local_run --local "Recuperar contraseña" ["contexto opcional"]

La bandera --local equivale a APP_ENV=local y ALLOW_SIMULATED_SESSION=true (funciona
tambien en cmd.exe). Un APP_ENV ya definido en el entorno no se sobrescribe.
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Mapping, Sequence

from story_service.bedrock_client import BedrockModelClient
from story_service.config import Settings, build_session_verifier
from story_service.errors import ServiceError
from story_service.fakes import SimulatedSessionVerifier
from story_service.markdown_builder import GHERKIN_LANGUAGE_LINE, STORY_PREFIX
from story_service.ports import ModelClient
from story_service.service import StoryService


def main(
    argv: Sequence[str],
    env: Mapping[str, str] | None = None,
    model_client: ModelClient | None = None,
) -> int:
    env = os.environ if env is None else env
    args = list(argv)
    if "--local" in args:
        # Explicit local opt-in that also works in shells without VAR=value prefixes (cmd.exe).
        # An APP_ENV already set in the environment still wins, so a deployed value is never
        # overridden.
        args.remove("--local")
        env = {"APP_ENV": "local", "ALLOW_SIMULATED_SESSION": "true", **env}
    argv = args
    if not argv:
        print('Uso: python -m story_service.local_run "<titulo>" ["<contexto>"]', file=sys.stderr)
        return 2
    settings = Settings.from_env(env)
    verifier = build_session_verifier(settings)
    if not isinstance(verifier, SimulatedSessionVerifier):
        print(
            "Este comando solo corre en local: defina APP_ENV=local "
            "y ALLOW_SIMULATED_SESSION=true.",
            file=sys.stderr,
        )
        return 2
    client = model_client or BedrockModelClient(
        settings.model_id, settings.region, read_timeout_seconds=settings.timeout_seconds
    )
    service = StoryService(verifier, client, settings.instructions, model_id=settings.model_id)

    started = time.monotonic()
    context = argv[1] if len(argv) > 1 else None
    try:
        result = service.generate("local", argv[0], context=context)
    except ServiceError as error:
        print(f"Error {error.code.value}: {error.message}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - started

    print(result.markdown)
    print(f"\nTiempo total: {elapsed:.1f} s")
    return 0 if _has_story_and_gherkin(result.markdown) else 1


def _has_story_and_gherkin(markdown: str) -> bool:
    """La historia empieza con el rol fijo y el bloque de codigo trae la linea de idioma."""
    lines = markdown.splitlines()
    has_story = any(line.startswith(STORY_PREFIX) for line in lines)
    return has_story and GHERKIN_LANGUAGE_LINE in lines


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
