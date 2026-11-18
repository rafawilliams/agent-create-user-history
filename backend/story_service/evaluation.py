"""Evaluación de modelos (US7.1): resultados, puntuación, decisión, archivo de títulos y registro.

Sin estado entre llamadas (NFR4.1). El reloj es inyectable para probar el tiempo por llamada
(NFR1.3). Nada de lo que se registra contiene texto de AWS (BR2.4): solo motivos de lista
cerrada.
"""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from story_service.errors import ServiceError
from story_service.models import (
    EvaluationOutcome,
    EvaluationRecord,
    EvaluationResult,
    ModelError,
    ModelErrorKind,
    ModelErrorReason,
    ModelResponse,
)
from story_service.ports import ModelClient
from story_service.prompt import build_prompt
from story_service.response_parsing import parse_story_draft

REQUIRED_TITLE_COUNT = 5
REQUIRED_PREFIX = "Como analista de negocio"
_BLOCKING_REASONS = frozenset(
    {ModelErrorReason.ACCESS_NOT_ENABLED, ModelErrorReason.MODEL_NOT_FOUND}
)
_APPROVAL_LINE = re.compile(r"^aprobado:\s*([0-9a-f]{64})\s*$", re.MULTILINE)


class TitlesFileError(ValueError):
    """El archivo de títulos no sirve para evaluar (BR2.9, NFR4.3)."""


# ---- formato y resultados ---------------------------------------------------------------------


_SCENARIO_HEADER = re.compile(r"^\W*Escenario\b[^:\n]*:", re.MULTILINE)


def check_format(text: str) -> bool:
    """Comprobación mínima de la evaluación (BR2.8); no reemplaza la de u3-story-generator."""
    # The service now asks the model for JSON (u3, BR3.6): a response that parses as the
    # expected draft has the right format by construction (the service builds the Gherkin).
    try:
        parse_story_draft(text)
        return True
    except ServiceError:
        pass
    if not text.startswith(REQUIRED_PREFIX):
        return False
    # Accepts "Escenario:" and numbered forms such as "Escenario 1:" at the start of a line.
    scenarios = _SCENARIO_HEADER.split(text)[1:]
    if not 2 <= len(scenarios) <= 3:
        return False
    return all(
        all(word in scenario for word in ("Dado", "Cuando", "Entonces")) for scenario in scenarios
    )


def _to_result(
    model_id: str, title: str, outcome: ModelResponse | ModelError, elapsed: float
) -> EvaluationResult:
    if isinstance(outcome, ModelResponse):
        return EvaluationResult(
            model_id,
            title,
            EvaluationOutcome.GENERATED,
            text=outcome.text,
            format_ok=check_format(outcome.text),
            elapsed_seconds=elapsed,
        )
    reason = outcome.reason or ModelErrorReason.UNKNOWN
    status = EvaluationOutcome.BLOCKED if reason in _BLOCKING_REASONS else EvaluationOutcome.FAILED
    return EvaluationResult(model_id, title, status, elapsed_seconds=elapsed, reason=reason)


def evaluate(
    models: Sequence[tuple[str, ModelClient]],
    titles: Sequence[str],
    instructions: str,
    clock: Callable[[], float] = time.monotonic,
    timeout_seconds: float = 50.0,
) -> list[EvaluationResult]:
    """Un resultado por modelo y título, sin reintentos; un modelo bloqueado no detiene a otros."""
    results: list[EvaluationResult] = []
    for model_id, client in models:
        for title in titles:
            prompt = build_prompt(instructions, title)
            started = clock()
            try:
                outcome = client.invoke(prompt, timeout_seconds)
            except Exception:  # el cliente no debería lanzar; un fallo no detiene la evaluación
                outcome = ModelError(
                    kind=ModelErrorKind.UNAVAILABLE,
                    message="El modelo no está disponible",
                    reason=ModelErrorReason.UNKNOWN,
                )
            results.append(_to_result(model_id, title, outcome, clock() - started))
    return results


# ---- puntuación y decisión ---------------------------------------------------------------------


def score(results: Sequence[EvaluationResult]) -> dict[str, int]:
    """Puntuación de un modelo: número de resultados con formato correcto."""
    totals: dict[str, int] = {}
    for item in results:
        totals[item.model_id] = totals.get(item.model_id, 0) + (1 if item.format_ok else 0)
    return totals


@dataclass(frozen=True)
class Decision:
    text: str
    pending_access: tuple[str, ...] = ()


def decide(results: Sequence[EvaluationResult], default_model_id: str) -> Decision:
    """Criterio de BR2.8 y BR2.10."""
    totals = score(results)
    blocked = tuple(
        dict.fromkeys(r.model_id for r in results if r.outcome == EvaluationOutcome.BLOCKED)
    )
    if blocked:
        return Decision(
            f"pendiente: acceso por solicitar para {', '.join(blocked)}; "
            f"el modelo por defecto {default_model_id} sigue en uso.",
            blocked,
        )
    top = max(totals.values(), default=0)
    leaders = [model for model, value in totals.items() if value == top]
    if len(leaders) == 1:
        return Decision(f"Se elige {leaders[0]} con la mayor puntuación ({top}).")
    text = (
        f"Hay un empate en la puntuación ({top}): "
        f"se conserva el modelo por defecto {default_model_id}."
    )
    if top == 0:
        text += (
            " Todas las puntuaciones son cero: hay que afinar las instrucciones "
            "(u3-story-generator)."
        )
    return Decision(text)


def build_record(
    results: Sequence[EvaluationResult],
    titles: Sequence[str],
    evaluated_at: str,
    default_model_id: str,
) -> EvaluationRecord:
    decision = decide(results, default_model_id)
    return EvaluationRecord(
        evaluated_at=evaluated_at,
        titles=tuple(titles),
        results=tuple(results),
        decision=decision.text,
        pending_access=decision.pending_access,
    )


# ---- archivo de títulos con aprobación atada al contenido (BR2.9, NFR4.3) ----------


def titles_fingerprint(titles: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(titles).encode("utf-8")).hexdigest()


def _read(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise TitlesFileError(f"No se pudo leer el archivo de títulos: {path}") from error


def _titles_in(content: str) -> tuple[str, ...]:
    titles = tuple(
        line[2:].strip()
        for line in content.splitlines()
        if line.startswith("- ") and line[2:].strip()
    )
    if len(titles) != REQUIRED_TITLE_COUNT:
        raise TitlesFileError(
            f"El archivo de títulos debe tener exactamente {REQUIRED_TITLE_COUNT} títulos "
            f"(líneas que empiezan con '- '); tiene {len(titles)}."
        )
    return titles


def load_approved_titles(path: Path) -> tuple[str, ...]:
    """Devuelve los 5 títulos solo si la línea `aprobado:` coincide con su huella."""
    content = _read(path)
    titles = _titles_in(content)
    match = _APPROVAL_LINE.search(content)
    if match is None:
        raise TitlesFileError(
            "Los títulos no están aprobados: falta la línea 'aprobado: <huella>'. "
            "Apruébalos con: python -m story_service.evaluate_models approve"
        )
    if match.group(1) != titles_fingerprint(titles):
        raise TitlesFileError(
            "La aprobación ya no coincide con los títulos (cambió alguno): apruébalos de nuevo."
        )
    return titles


def approve_titles(path: Path) -> str:
    """Escribe la línea `aprobado: <huella>` y devuelve la huella."""
    content = _read(path)
    fingerprint = titles_fingerprint(_titles_in(content))
    without = _APPROVAL_LINE.sub("", content).rstrip("\n")
    Path(path).write_text(f"{without}\n\naprobado: {fingerprint}\n", encoding="utf-8")
    return fingerprint


# ---- registro en Markdown ----------------------------------------------------------


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_record(record: EvaluationRecord) -> str:
    totals = score(record.results)
    total_titles = len(record.titles)
    lines = [
        "# Evaluación de modelos",
        "",
        f"Fecha: {record.evaluated_at}",
        "",
        "## Títulos de ejemplo (inventados y aprobados)",
        "",
        *[f"{n}. {title}" for n, title in enumerate(record.titles, start=1)],
        "",
        "## Resultados por modelo y título",
        "",
        "| Modelo | Título | Resultado | Formato | Tiempo (s) | Motivo |",
        "|--------|--------|-----------|---------|------------|--------|",
    ]
    for item in record.results:
        fmt = "" if item.format_ok is None else ("sí" if item.format_ok else "no")
        elapsed = "" if item.elapsed_seconds is None else f"{item.elapsed_seconds:.1f}"
        lines.append(
            f"| {_cell(item.model_id)} | {_cell(item.title)} | {item.outcome.value} | {fmt} "
            f"| {elapsed} | {item.reason.value if item.reason else ''} |"
        )
    lines += ["", "## Puntuación (resultados con formato correcto)", ""]
    lines += [f"- {model}: {value}/{total_titles}" for model, value in totals.items()]
    lines += ["", "## Decisión", "", record.decision, ""]
    if record.pending_access:
        lines += ["## Acceso pendiente", ""]
        lines += [f"- {model}" for model in record.pending_access]
        lines.append("")
    generated = [r for r in record.results if r.outcome == EvaluationOutcome.GENERATED]
    if generated:
        lines += ["## Textos generados", ""]
        for item in generated:
            lines += [
                f"### {item.model_id} — {item.title}",
                "",
                "~~~~",
                item.text or "",
                "~~~~",
                "",
            ]
    return "\n".join(lines)


def write_record(path: Path, record: EvaluationRecord) -> None:
    """El único archivo que escribe la evaluación (NFR4.1)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_record(record), encoding="utf-8")
