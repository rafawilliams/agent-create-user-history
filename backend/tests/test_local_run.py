"""Pruebas del comando local de punta a punta, con un modelo simulado (nunca AWS)."""

from story_service.fakes import FakeModelClient
from story_service.local_run import main
from story_service.models import ModelResponse
from tests.helpers import VALID_JSON

LOCAL_ENV = {"APP_ENV": "local", "ALLOW_SIMULATED_SESSION": "true"}


def test_success_prints_markdown_and_elapsed_time_and_returns_0(capsys):
    model = FakeModelClient(results=[ModelResponse(VALID_JSON, "m-1")])

    code = main(["Recuperar contraseña"], env=LOCAL_ENV, model_client=model)

    out = capsys.readouterr().out
    assert code == 0
    assert "Como analista de negocio" in out
    assert "# language: es" in out
    assert "Tiempo total" in out


def test_the_optional_second_argument_is_the_context_and_unblocks_a_short_title(capsys):
    model = FakeModelClient(results=[ModelResponse(VALID_JSON, "m-1")])

    code = main(["--local", "Login", "acceso con correo y clave"], env={}, model_client=model)

    out = capsys.readouterr().out
    assert code == 0
    assert "acceso con correo y clave" in model.calls[0].prompt
    assert any(line.startswith("Como analista de negocio, quiero ") for line in out.splitlines())
    assert "# language: es" in out


def test_a_short_title_without_context_reports_needs_context_and_returns_1(capsys):
    model = FakeModelClient(results=[ModelResponse(VALID_JSON, "m-1")])

    code = main(["--local", "Login"], env={}, model_client=model)

    assert code == 1
    assert "NEEDS_CONTEXT" in capsys.readouterr().err
    assert model.calls == []


def test_refuses_to_run_without_explicit_local_simulation(capsys):
    model = FakeModelClient()

    code = main(["Titulo"], env={"APP_ENV": "prod"}, model_client=model)

    assert code == 2
    assert model.calls == []
    assert "APP_ENV=local" in capsys.readouterr().err


def test_local_flag_enables_the_simulated_session_without_environment_variables(capsys):
    # cmd.exe cannot prefix a command with VAR=value, so the flag is the explicit opt-in.
    model = FakeModelClient(results=[ModelResponse(VALID_JSON, "m-1")])

    code = main(["--local", "Recuperar contraseña"], env={}, model_client=model)

    assert code == 0
    assert len(model.calls) == 1
    assert "Como analista de negocio" in capsys.readouterr().out


def test_local_flag_never_overrides_a_deployed_environment(capsys):
    model = FakeModelClient()

    code = main(["--local", "Titulo"], env={"APP_ENV": "prod"}, model_client=model)

    assert code == 2
    assert model.calls == []


def test_local_flag_without_title_returns_usage_error(capsys):
    code = main(["--local"], env={}, model_client=FakeModelClient())

    assert code == 2
    assert "Uso" in capsys.readouterr().err


def test_missing_title_argument_returns_usage_error(capsys):
    code = main([], env=LOCAL_ENV, model_client=FakeModelClient())

    assert code == 2
    assert "Uso" in capsys.readouterr().err


def test_service_error_is_reported_and_returns_1(capsys):
    model = FakeModelClient(results=[ModelResponse("texto sin el rol", "m-1")])

    code = main(["Titulo de prueba valido"], env=LOCAL_ENV, model_client=model)

    assert code == 1
    assert "INVALID_MODEL_RESPONSE" in capsys.readouterr().err
