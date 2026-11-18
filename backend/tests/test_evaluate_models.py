"""Pruebas del comando de evaluación con modelos simulados, sin AWS (NFR4.1, NFR4.3)."""

import pytest

from story_service.evaluate_models import main
from story_service.evaluation import titles_fingerprint
from story_service.fakes import FakeModelClient
from story_service.models import ModelError, ModelErrorKind, ModelErrorReason, ModelResponse
from tests.helpers import FakeClock

DEFAULT = "us.anthropic.claude-sonnet-4-6"
TITAN = "us.amazon.titan-text-premier-v1:0"
TITLES = tuple(f"Titulo inventado {n}" for n in range(1, 6))
GOOD = (
    "Como analista de negocio quiero algo para lograr un beneficio.\n\n"
    "Escenario: uno\n  Dado que a\n  Cuando b\n  Entonces c\n\n"
    "Escenario: dos\n  Dado que a\n  Cuando b\n  Entonces c"
)
ENV = {"EVALUATION_MODEL_IDS": f"{DEFAULT},{TITAN}"}


@pytest.fixture
def files(tmp_path):
    titles = tmp_path / "titulos.md"
    titles.write_text(
        "# Titulos\n\nInventados.\n\n" + "\n".join(f"- {t}" for t in TITLES) + "\n",
        encoding="utf-8",
    )
    return titles, tmp_path / "salida" / "evaluacion-modelos.md"


def factory_for(clients):
    created = []

    def factory(model_id, region):
        created.append(model_id)
        return clients[model_id]

    factory.created = created
    return factory


def run_command(files, clients, argv=("run",), env=ENV):
    titles, record = files
    clock = FakeClock()
    factory = factory_for(clients)
    code = main(
        list(argv),
        env=env,
        client_factory=factory,
        titles_path=titles,
        record_path=record,
        clock=clock,
        now=lambda: "2026-11-17T10:00:00Z",
    )
    return code, factory


def test_approve_writes_the_fingerprint_of_the_titles(files):
    titles, _ = files

    code, _ = run_command(files, {}, argv=("approve",))

    assert code == 0
    assert f"aprobado: {titles_fingerprint(TITLES)}" in titles.read_text(encoding="utf-8")


def test_run_refuses_without_approved_titles_and_calls_no_model(files, capsys):
    _, record = files

    code, factory = run_command(files, {DEFAULT: FakeModelClient()})

    assert code == 2
    assert "aprob" in capsys.readouterr().err
    assert factory.created == [] and not record.exists()


def test_run_refuses_after_a_title_changes(files):
    titles, record = files
    run_command(files, {}, argv=("approve",))
    titles.write_text(
        titles.read_text(encoding="utf-8").replace("Titulo inventado 2", "Otro"), encoding="utf-8"
    )

    code, factory = run_command(files, {DEFAULT: FakeModelClient()})

    assert code == 2 and factory.created == [] and not record.exists()


def test_run_with_simulated_models_writes_one_result_per_model_and_title(files):
    _, record = files
    run_command(files, {}, argv=("approve",))
    clients = {
        DEFAULT: FakeModelClient([ModelResponse(GOOD, DEFAULT)]),
        TITAN: FakeModelClient([ModelResponse("sin formato", TITAN)]),
    }

    code, factory = run_command(files, clients)

    markdown = record.read_text(encoding="utf-8")
    assert code == 0 and factory.created == [DEFAULT, TITAN]
    assert markdown.count(f"| {DEFAULT} |") == 5 and markdown.count(f"| {TITAN} |") == 5
    assert f"- {DEFAULT}: 5/5" in markdown and f"- {TITAN}: 0/5" in markdown
    assert f"Se elige {DEFAULT}" in markdown
    assert all(title in markdown for title in TITLES)
    assert all(len(client.calls) == 5 for client in clients.values())


def test_a_blocked_model_is_recorded_and_the_command_continues(files):
    _, record = files
    run_command(files, {}, argv=("approve",))
    blocked = ModelError(
        ModelErrorKind.ACCESS_DENIED, "Sin acceso", ModelErrorReason.ACCESS_NOT_ENABLED
    )
    clients = {
        DEFAULT: FakeModelClient([ModelResponse(GOOD, DEFAULT)]),
        TITAN: FakeModelClient([blocked]),
    }

    code, _ = run_command(files, clients)

    markdown = record.read_text(encoding="utf-8")
    assert code == 0
    assert markdown.count("blocked") >= 5 and "access_not_enabled" in markdown
    assert "pendiente" in markdown and "## Acceso pendiente" in markdown
    assert len(clients[DEFAULT].calls) == 5


def test_the_record_is_the_only_file_written(files):
    titles, record = files
    run_command(files, {}, argv=("approve",))
    before = {p.name for p in titles.parent.rglob("*") if p.is_file()}

    run_command(
        files, {DEFAULT: FakeModelClient([ModelResponse(GOOD, DEFAULT)]), TITAN: FakeModelClient()}
    )

    after = {p for p in titles.parent.rglob("*") if p.is_file()}
    assert {p.name for p in after} - before == {record.name}


def test_the_default_model_is_always_evaluated_and_an_invalid_model_id_is_refused(files, capsys):
    run_command(files, {}, argv=("approve",))

    code, factory = run_command(
        files,
        {DEFAULT: FakeModelClient([ModelResponse(GOOD, DEFAULT)]), TITAN: FakeModelClient()},
        env={"EVALUATION_MODEL_IDS": TITAN},
    )
    assert code == 0 and factory.created == [DEFAULT, TITAN]

    code, factory = run_command(files, {}, env={"EVALUATION_MODEL_IDS": "us.meta.llama3-70b"})
    assert code == 2 and factory.created == []
    assert "us.meta.llama3-70b" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [(), ("otra",), ("run", "extra")])
def test_unknown_usage_returns_2(files, argv):
    code, factory = run_command(files, {}, argv=argv)

    assert code == 2 and factory.created == []
