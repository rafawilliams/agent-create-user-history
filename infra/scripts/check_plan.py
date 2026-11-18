"""Comprueba la ESTRUCTURA de un plan de Terraform (`terraform show -json`), nunca sus valores.

Falla (codigo 1) ante: un tipo de recurso no permitido (NFR4.1), un deposito de S3 distinto del de
la pantalla, la eliminacion o el reemplazo de un tipo protegido (NFR8.2), una variable de secretos
sin `sensitive` (NFR5.1), fuentes de datos `external` y aprovisionadores `local-exec` o
`remote-exec` (NFR5.3) y roles de IAM fuera del prefijo de la aplicacion (NFR5.4).

Uso: python check_plan.py plan.json      (0 = limpio, 1 = incumplimientos, 2 = error de uso)
Solo imprime direcciones y tipos de recurso: ningun valor del plan llega a la salida.
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

# --- Politica: la unica fuente de las listas (tipos permitidos y protegidos) ---------------------

APPLICATION_PREFIX = "business-analyst-agent-"

# Tipos que la aplicacion puede crear. Todo lo demas (tablas, bases de datos, usuarios de IAM,
# terraform_data, null_resource...) falla.
ALLOWED_TYPE_PATTERNS = (
    "aws_lambda_*",
    "aws_api_gateway_*",
    "aws_cloudwatch_log_group",
    "aws_cloudwatch_log_metric_filter",
    "aws_s3_bucket",
    "aws_s3_bucket_*",
    "aws_cloudfront_*",
    "aws_cognito_*",
    "aws_iam_role",
    "aws_iam_role_policy",
    "aws_iam_role_policy_attachment",
)

# Permitidos por patron, pero vetados: son registros de acceso (NFR4.2).
FORBIDDEN_TYPES = frozenset(
    {
        "aws_s3_bucket_logging",
        "aws_cloudfront_realtime_log_config",
        # Una URL de funcion expone la funcion fuera de la pasarela.
        "aws_lambda_function_url",
    }
)

AWS_MANAGED_POLICY_PREFIX = "arn:aws:iam::aws:policy/"

# Los unicos almacenes permitidos: el deposito de la pantalla (direccion y prefijo de nombre).
WEB_BUCKET_ADDRESS = "aws_s3_bucket.web"
WEB_BUCKET_PREFIX = f"{APPLICATION_PREFIX}web-"

# Eliminarlos o reemplazarlos requiere que la persona los aplique a mano.
PROTECTED_TYPES = frozenset(
    {
        "aws_cognito_user_pool",
        "aws_cloudfront_distribution",
        "aws_s3_bucket",
        "aws_lambda_function",
    }
)

SENSITIVE_VARIABLES = (
    "allowed_emails",
    "google_client_id",
    "google_client_secret",
    "microsoft_client_id",
    "microsoft_client_secret",
)

FORBIDDEN_PROVISIONERS = frozenset({"local-exec", "remote-exec"})
FORBIDDEN_DATA_TYPES = frozenset({"external"})


def _is_allowed(resource_type: str) -> bool:
    return any(fnmatch.fnmatchcase(resource_type, pattern) for pattern in ALLOWED_TYPE_PATTERNS)


def _check_resource_change(item: dict[str, Any]) -> list[str]:
    address = item.get("address", "?")
    rtype = item.get("type", "")
    change = item.get("change") or {}
    actions = change.get("actions") or []
    # En una eliminacion pura `after` es nulo: el nombre se lee de `before`.
    after = change.get("after") or change.get("before") or {}

    if item.get("mode") == "data":
        if rtype in FORBIDDEN_DATA_TYPES:
            return [f"{address}: fuente de datos '{rtype}' no permitida (ejecuta codigo)"]
        return []

    found: list[str] = []
    if rtype in FORBIDDEN_TYPES:
        found.append(f"{address}: tipo de recurso '{rtype}' vetado (registro de acceso, NFR4.2)")
        return found
    if not _is_allowed(rtype):
        found.append(f"{address}: tipo de recurso '{rtype}' no permitido")
        return found

    if rtype == "aws_s3_bucket":
        prefix = str(after.get("bucket_prefix") or after.get("bucket") or "")
        if address != WEB_BUCKET_ADDRESS or not prefix.startswith(WEB_BUCKET_PREFIX):
            found.append(f"{address}: deposito de S3 no permitido (solo el de la pantalla)")

    if rtype == "aws_cloudfront_distribution" and after.get("logging_config"):
        found.append(f"{address}: la distribucion no puede tener registro de acceso (NFR4.2)")

    if rtype == "aws_iam_role_policy_attachment" and str(after.get("policy_arn") or "").startswith(
        AWS_MANAGED_POLICY_PREFIX
    ):
        found.append(f"{address}: no se permiten politicas administradas de AWS")

    if rtype == "aws_lambda_permission" and after.get("principal") == "*":
        found.append(f"{address}: el permiso de Lambda no puede tener el principal '*'")

    if rtype == "aws_iam_role" and not str(after.get("name") or "").startswith(APPLICATION_PREFIX):
        found.append(f"{address}: el rol de IAM no lleva el prefijo '{APPLICATION_PREFIX}'")

    if rtype in PROTECTED_TYPES and "delete" in actions:
        found.append(
            f"{address}: eliminar o reemplazar un recurso protegido ({rtype}) "
            "lo aplica la persona a mano"
        )
    return found


def _walk_modules(module: dict[str, Any]):
    """Recorre el modulo raiz y los modulos hijos de la configuracion."""
    yield module
    for call in (module.get("module_calls") or {}).values():
        child = call.get("module") or {}
        yield from _walk_modules(child)


def _check_configuration(plan: dict[str, Any]) -> list[str]:
    root = (plan.get("configuration") or {}).get("root_module") or {}
    found: list[str] = []

    variables = root.get("variables") or {}
    for name in SENSITIVE_VARIABLES:
        if name not in variables:
            found.append(
                f"variable '{name}': falta en la configuracion (debe existir y ser sensitive)"
            )
        elif not variables[name].get("sensitive"):
            found.append(f"variable '{name}': debe ser sensitive (NFR5.1)")

    for module in _walk_modules(root):
        for resource in module.get("resources") or []:
            address = resource.get("address", "?")
            if resource.get("mode") == "data" and resource.get("type") in FORBIDDEN_DATA_TYPES:
                found.append(f"{address}: fuente de datos '{resource['type']}' no permitida")
            for provisioner in resource.get("provisioners") or []:
                if provisioner.get("type") in FORBIDDEN_PROVISIONERS:
                    found.append(f"{address}: aprovisionador '{provisioner['type']}' no permitido")
    return found


def check_plan(plan: dict[str, Any]) -> list[str]:
    """Devuelve la lista de incumplimientos (vacia si el plan es aceptable)."""
    found: list[str] = []
    for item in plan.get("resource_changes") or []:
        found.extend(_check_resource_change(item))
    found.extend(_check_configuration(plan))
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Uso: check_plan.py plan.json", file=sys.stderr)
        return 2
    try:
        plan = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"No se pudo leer el plan: {type(error).__name__}", file=sys.stderr)
        return 2

    found = check_plan(plan)
    if found:
        print("check_plan: el plan incumple la politica:")
        for line in found:
            print(f"  - {line}")
        return 1
    print("check_plan: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
