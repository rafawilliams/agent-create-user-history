"""Pruebas de la evaluación: formato, puntuación, decisión y archivos (BR2.8 a BR2.10)."""

import hashlib

import pytest

from story_service.evaluation import (
    REQUIRED_TITLE_COUNT,
    TitlesFileError,
    approve_titles,
    build_record,
    check_format,
    decide,
    evaluate,
    load_approved_titles,
    render_record,
    score,
    titles_fingerprint,
)
from story_service.fakes import FakeModelClient
from story_service.models import (
    EvaluationOutcome,
    EvaluationResult,
    ModelError,
    ModelErrorKind,
    ModelErrorReason,
    ModelResponse,
)
from tests.helpers import VALID_STORY, FakeClock

DEFAULT = "us.anthropic.claude-sonnet-4-6"
TITAN = "us.amazon.titan-text-premier-v1:0"
TITLES = tuple(f"Titulo inventado {n}" for n in range(1, 6))


def story(scenarios: int = 2, prefix: str = "Como analista de negocio") -> str:
    body = f"{prefix} quiero algo para lograr un beneficio."
    for n in range(scenarios):
        body += f"\n\nEscenario: {n}\n  Dado que a\n  Cuando b\n  Entonces c"
    return body


def blocked_error(reason=ModelErrorReason.ACCESS_NOT_ENABLED) -> ModelError:
    return ModelError(ModelErrorKind.ACCESS_DENIED, "Sin acceso al modelo configurado", reason)


# ---- formato (BR2.8) -------------------------------------------------------------------


@pytest.mark.parametrize("scenarios", [2, 3])
def test_format_ok_with_prefix_and_two_or_three_scenarios(scenarios):
    assert check_format(story(scenarios)) is True


def test_format_ok_with_numbered_scenarios_as_the_real_model_writes_them():
    # The real model answered "Escenario 1: <name>" (verified against Bedrock in u1).
    text = (
        "Como analista de negocio, quiero algo, para algo.\n\n```gherkin\n"
        "Escenario 1: Exitoso\nDado que a\nCuando b\nEntonces c\n\n"
        "Escenario 2: Fallido\nDado que d\nCuando e\nEntonces f\n```"
    )
    assert check_format(text) is True


def test_format_ok_with_the_json_the_service_now_asks_the_model_for():
    # u3 changed the model contract to JSON; the evaluation must judge the same output (BR3.6).
    from tests.helpers import VALID_JSON

    assert check_format(VALID_JSON) is True


def test_format_fails_with_json_that_has_a_single_criterion():
    import json

    from tests.helpers import VALID_JSON

    data = json.loads(VALID_JSON)
    data["criteria"] = data["criteria"][:1]

    assert check_format(json.dumps(data)) is False


def test_format_fails_with_a_single_numbered_scenario():
    text = (
        "Como analista de negocio, quiero algo.\n"
        "Escenario 1: Solo uno\nDado a\nCuando b\nEntonces c"
    )
    assert check_format(text) is False


@pytest.mark.parametrize(
    "text",
    [
        story(1),  # un solo escenario
        story(4),  # demasiados
        story(2, prefix="Como Analista de negocio"),  # el prefijo distingue mayusculas
        "Introduccion\n" + story(2),  # texto previo
        "Como analista de negocio quiero algo\n\nScenario: a\n  Given x\n  When y\n  Then z"
        "\n\nScenario: b\n  Given x\n  When y\n  Then z",  # no esta en espanol
        "",
    ],
)
def test_format_fails_when_any_requirement_is_missing(text):
    assert check_format(text) is False


# ---- un resultado por modelo y titulo, bloqueo y fallo (BR2.8, BR2.10) --------------------


def run(models, clock=None, timeout=50.0):
    return evaluate(
        models, TITLES, "INSTRUCCIONES", clock=clock or FakeClock(), timeout_seconds=timeout
    )


def test_one_result_per_model_and_title_with_format_and_elapsed_time():
    clock = FakeClock()
    ok = FakeModelClient([ModelResponse(story(), DEFAULT)], on_invoke=lambda: clock.advance(2.0))
    bad = FakeModelClient(
        [ModelResponse("sin formato", TITAN)], on_invoke=lambda: clock.advance(1.0)
    )

    results = run([(DEFAULT, ok), (TITAN, bad)], clock=clock)

    assert len(results) == 2 * REQUIRED_TITLE_COUNT
    assert {(r.model_id, r.title) for r in results} == {
        (m, t) for m in (DEFAULT, TITAN) for t in TITLES
    }
    good = [r for r in results if r.model_id == DEFAULT]
    assert all(r.outcome == EvaluationOutcome.GENERATED and r.format_ok for r in good)
    assert all(r.elapsed_seconds == 2.0 for r in good)
    assert not any(r.format_ok for r in results if r.model_id == TITAN)
    assert ok.calls[0].timeout_seconds == 50.0
    assert "Titulo inventado 1" in ok.calls[0].prompt and "INSTRUCCIONES" in ok.calls[0].prompt


@pytest.mark.parametrize(
    "reason", [ModelErrorReason.ACCESS_NOT_ENABLED, ModelErrorReason.MODEL_NOT_FOUND]
)
def test_access_errors_are_blocked_and_do_not_stop_the_other_models(reason):
    blocked = FakeModelClient([blocked_error(reason)])
    fine = FakeModelClient([ModelResponse(story(), DEFAULT)])

    results = run([(TITAN, blocked), (DEFAULT, fine)])

    titan = [r for r in results if r.model_id == TITAN]
    assert len(titan) == REQUIRED_TITLE_COUNT
    assert all(r.outcome == EvaluationOutcome.BLOCKED and r.reason == reason for r in titan)
    assert sum(r.outcome == EvaluationOutcome.GENERATED for r in results) == REQUIRED_TITLE_COUNT


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        (ModelErrorKind.ACCESS_DENIED, ModelErrorReason.INVALID_REQUEST),
        (ModelErrorKind.TRANSIENT, ModelErrorReason.THROTTLED),
        (ModelErrorKind.TIMEOUT, ModelErrorReason.TIMEOUT),
        (ModelErrorKind.UNAVAILABLE, ModelErrorReason.UNAVAILABLE),
    ],
)
def test_other_failures_are_failed_with_their_reason_and_never_retried(kind, reason):
    client = FakeModelClient([ModelError(kind, "mensaje propio", reason)])

    results = run([(TITAN, client)])

    assert all(r.outcome == EvaluationOutcome.FAILED and r.reason == reason for r in results)
    assert len(client.calls) == REQUIRED_TITLE_COUNT  # una llamada por titulo, sin reintentos


def test_an_exception_from_a_client_is_a_failed_result_not_a_crash():
    class Exploding:
        def invoke(self, prompt, timeout_seconds):
            raise RuntimeError("fallo interno")

    results = run([(TITAN, Exploding())])

    assert all(
        r.outcome == EvaluationOutcome.FAILED and r.reason == ModelErrorReason.UNKNOWN
        for r in results
    )


# ---- puntuacion y decision (BR2.8, BR2.10) -------------------------------------------------


def result(model_id, ok=True, outcome=EvaluationOutcome.GENERATED, title="t"):
    if outcome == EvaluationOutcome.GENERATED:
        return EvaluationResult(model_id, title, outcome, text="x", format_ok=ok)
    return EvaluationResult(model_id, title, outcome, reason=ModelErrorReason.ACCESS_NOT_ENABLED)


def test_score_counts_results_with_correct_format_per_model():
    results = [result(DEFAULT), result(DEFAULT), result(DEFAULT, ok=False), result(TITAN, ok=False)]

    assert score(results) == {DEFAULT: 2, TITAN: 0}


def test_highest_score_wins_when_nobody_is_blocked():
    results = [result(DEFAULT, ok=False), result(TITAN), result(TITAN)]

    decision = decide(results, DEFAULT)

    assert TITAN in decision.text and not decision.text.startswith("pendiente")
    assert decision.pending_access == ()


def test_tie_keeps_the_default_model():
    decision = decide([result(DEFAULT), result(TITAN)], DEFAULT)

    assert DEFAULT in decision.text and "empate" in decision.text


def test_all_zero_keeps_the_default_and_notes_that_the_instructions_need_tuning():
    decision = decide([result(DEFAULT, ok=False), result(TITAN, ok=False)], DEFAULT)

    assert DEFAULT in decision.text and "afinar" in decision.text


def test_a_failed_result_counts_as_no_compliance_and_does_not_block_the_decision():
    failed = EvaluationResult(TITAN, "t", EvaluationOutcome.FAILED, reason=ModelErrorReason.TIMEOUT)

    decision = decide([result(DEFAULT), failed], DEFAULT)

    assert not decision.text.startswith("pendiente") and DEFAULT in decision.text


def test_any_blocked_model_makes_the_decision_pending_and_keeps_the_default():
    results = [result(DEFAULT), result(TITAN, outcome=EvaluationOutcome.BLOCKED)]

    decision = decide(results, DEFAULT)

    assert decision.text.startswith("pendiente") and DEFAULT in decision.text
    assert decision.pending_access == (TITAN,)


def test_all_models_blocked_is_pending():
    results = [
        result(DEFAULT, outcome=EvaluationOutcome.BLOCKED),
        result(TITAN, outcome=EvaluationOutcome.BLOCKED),
    ]

    decision = decide(results, DEFAULT)

    assert decision.text.startswith("pendiente")
    assert set(decision.pending_access) == {DEFAULT, TITAN}


# ---- archivo de titulos y registro (BR2.9, NFR4.3) ---------------------------------------------


def write_titles(path, titles=TITLES, approval=None):
    lines = ["# Titulos de evaluacion", "", "Titulos inventados.", ""]
    lines += [f"- {title}" for title in titles]
    if approval:
        lines += ["", f"aprobado: {approval}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_fingerprint_is_the_sha256_of_the_five_titles():
    expected = hashlib.sha256("\n".join(TITLES).encode("utf-8")).hexdigest()

    assert titles_fingerprint(TITLES) == expected


def test_approve_writes_the_fingerprint_and_the_approved_titles_load(tmp_path):
    path = tmp_path / "titulos.md"
    write_titles(path)

    approve_titles(path)

    assert f"aprobado: {titles_fingerprint(TITLES)}" in path.read_text(encoding="utf-8")
    assert load_approved_titles(path) == TITLES
    approve_titles(path)  # aprobar otra vez no duplica la linea
    assert path.read_text(encoding="utf-8").count("aprobado:") == 1


def test_titles_without_approval_are_refused(tmp_path):
    path = tmp_path / "titulos.md"
    write_titles(path)

    with pytest.raises(TitlesFileError, match="aprob"):
        load_approved_titles(path)


def test_changing_a_title_invalidates_the_approval(tmp_path):
    path = tmp_path / "titulos.md"
    write_titles(path)
    approve_titles(path)
    path.write_text(
        path.read_text(encoding="utf-8").replace("Titulo inventado 3", "Otro titulo"),
        encoding="utf-8",
    )

    with pytest.raises(TitlesFileError, match="aprob"):
        load_approved_titles(path)


@pytest.mark.parametrize("count", [0, 4, 6])
def test_exactly_five_titles_are_required(tmp_path, count):
    path = tmp_path / "titulos.md"
    titles = tuple(f"T{n}" for n in range(count))
    write_titles(path, titles, approval=titles_fingerprint(titles))

    with pytest.raises(TitlesFileError, match="5"):
        load_approved_titles(path)


def test_missing_titles_file_is_a_clear_error(tmp_path):
    with pytest.raises(TitlesFileError):
        load_approved_titles(tmp_path / "no-existe.md")


def test_record_markdown_has_titles_results_scores_and_decision_without_aws_text():
    results = [
        EvaluationResult(
            DEFAULT,
            t,
            EvaluationOutcome.GENERATED,
            text=VALID_STORY,
            format_ok=True,
            elapsed_seconds=2.5,
        )
        for t in TITLES
    ] + [
        EvaluationResult(
            TITAN,
            t,
            EvaluationOutcome.BLOCKED,
            elapsed_seconds=0.4,
            reason=ModelErrorReason.ACCESS_NOT_ENABLED,
        )
        for t in TITLES
    ]
    record = build_record(results, TITLES, "2026-11-17T10:00:00Z", DEFAULT)

    markdown = render_record(record)

    for title in TITLES:
        assert title in markdown
    assert "access_not_enabled" in markdown and "2.5" in markdown
    assert "5/5" in markdown and "0/5" in markdown
    assert record.decision in markdown and record.decision.startswith("pendiente")
    assert TITAN in markdown and "arn:aws" not in markdown
    assert record.pending_access == (TITAN,)
