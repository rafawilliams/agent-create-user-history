"""Prueba de smoke_test.sh contra un servidor HTTP local que imita la pantalla y la pasarela.

La prueba de humo real corre tras el despliegue (deploy.yml); aqui se comprueba que el script
acepta el comportamiento correcto y falla ante cada desviacion (cabecera exacta, preflight con el
origen exacto y 401 sin token). No llama a AWS.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("smoke_test.sh")
# Ruta completa: en Windows, `bash` a secas puede resolverse al de WSL en lugar del de Git.
BASH = shutil.which("bash") or "bash"
COGNITO_DOMAIN = "example-prefix.auth.us-east-1.amazoncognito.com"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("curl") is None,
    reason="smoke_test.sh necesita bash y curl",
)


def expected_csp(origin: str) -> str:
    return "; ".join(
        [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            f"connect-src 'self' {origin} https://{COGNITO_DOMAIN} "
            "https://cognito-idp.us-east-1.amazonaws.com",
            "img-src 'self' data:",
            "font-src 'self' data:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


class Behavior:
    """Cambia lo que responde el servidor de prueba."""

    def __init__(self, origin: str) -> None:
        self.origin = origin
        self.csp = expected_csp(origin)
        self.root_status = 200
        self.allow_origin = origin
        self.allow_methods = "GET,POST,DELETE,OPTIONS"
        self.allow_headers = "Authorization,Content-Type"
        self.post_status = 401
        self.post_body = '{"code":"SESSION_INVALID","message":"x","retryable":false}'


def make_server(behavior_holder: dict) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:  # silencio
            return

        def _send(self, status: int, headers: dict[str, str], body: str = "") -> None:
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()
            self.wfile.write(body.encode())

        def do_GET(self) -> None:  # noqa: N802
            b: Behavior = behavior_holder["b"]
            self._send(
                b.root_status,
                {
                    "Content-Security-Policy": b.csp,
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "no-referrer",
                    "Content-Type": "text/html",
                },
                "<html></html>",
            )

        def do_OPTIONS(self) -> None:  # noqa: N802
            b: Behavior = behavior_holder["b"]
            self._send(
                204,
                {
                    "Access-Control-Allow-Origin": b.allow_origin,
                    "Access-Control-Allow-Methods": b.allow_methods,
                    "Access-Control-Allow-Headers": b.allow_headers,
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            b: Behavior = behavior_holder["b"]
            self._send(b.post_status, {"Content-Type": "application/json"}, b.post_body)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def server():
    holder: dict = {}
    srv = make_server(holder)
    origin = f"http://127.0.0.1:{srv.server_address[1]}"
    holder["b"] = Behavior(origin)
    yield origin, holder["b"]
    srv.shutdown()


def run_script(origin: str) -> subprocess.CompletedProcess[str]:
    # La API de prueba cuelga de /live como la etapa real; el origen es el mismo servidor.
    return subprocess.run(
        [BASH, SCRIPT.name, origin, f"{origin}/live", COGNITO_DOMAIN],
        capture_output=True,
        text=True,
        cwd=SCRIPT.parent,
        timeout=60,
        check=False,
        env={**os.environ, "SMOKE_RETRIES": "1", "SMOKE_DELAY": "0"},
    )


def test_passes_when_everything_matches(server) -> None:
    origin, _ = server
    result = run_script(origin)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_fails_when_the_content_security_policy_differs(server) -> None:
    origin, behavior = server
    behavior.csp = behavior.csp.replace("script-src 'self'", "script-src 'self' 'unsafe-inline'")
    result = run_script(origin)
    assert result.returncode != 0
    assert "Content-Security-Policy" in result.stdout + result.stderr


def test_fails_when_the_root_is_not_200(server) -> None:
    origin, behavior = server
    behavior.root_status = 403
    assert run_script(origin).returncode != 0


def test_fails_when_the_preflight_origin_is_not_exact(server) -> None:
    origin, behavior = server
    behavior.allow_origin = "*"
    result = run_script(origin)
    assert result.returncode != 0
    assert "preflight" in (result.stdout + result.stderr).lower()


def test_fails_when_the_preflight_methods_are_incomplete(server) -> None:
    origin, behavior = server
    behavior.allow_methods = "POST,OPTIONS"
    assert run_script(origin).returncode != 0


def test_fails_when_a_request_without_token_is_not_401(server) -> None:
    origin, behavior = server
    behavior.post_status = 200
    assert run_script(origin).returncode != 0


def test_fails_when_the_401_body_is_not_the_c1_error(server) -> None:
    origin, behavior = server
    behavior.post_body = '{"detail":"Unauthorized"}'
    assert run_script(origin).returncode != 0


def test_usage_error_without_arguments() -> None:
    result = subprocess.run(
        [BASH, SCRIPT.name], capture_output=True, text=True, cwd=SCRIPT.parent, check=False
    )
    assert result.returncode == 2
