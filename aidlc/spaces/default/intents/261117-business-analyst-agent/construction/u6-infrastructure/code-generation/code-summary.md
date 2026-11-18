# Code Summary — u6-infrastructure

## Archivos creados

- **`infra/` (aplicación):** `cognito.tf` (grupo, dominio, cliente público y proveedores `Google` y `Microsoft`), `api_session.tf` (`/v1/session`, preflight y respuestas de error de la pasarela), `web_headers.tf` (política de cabeceras con la política de contenido exacta y la caché), `iam.tf` (rol de la función con `jsonencode`), `README.md` (lista de verificación del arranque) y `.checkov.yaml`.
- **`infra/bootstrap/`:** depósito de estado con bloqueo nativo, proveedor OIDC de GitHub, límite de permisos y los roles `pipeline-business-analyst-agent-plan`, `-apply` y `-boundary`, con sus pruebas.
- **`infra/tests/`:** tres archivos de `terraform test` (variables, pasarela y aplicación) con proveedor simulado.
- **`infra/scripts/`:** `check_plan.py` (tipos permitidos, vetados y protegidos, sensibilidad, `external` y aprovisionadores), `check_pins.py` (acciones fijadas por hash y archivo de bloqueo), `check_secrets.py`, `smoke_test.sh` y sus pruebas de Python.
- **`.github/workflows/deploy.yml`:** guarda `AWS_APPLY_ROLE_ARN`, concurrencia, plan, `check_plan.py`, aplicación del mismo plan, publicación de la pantalla sin `--delete`, invalidación, prueba de humo y reversión del alias.

## Archivos modificados

`infra/main.tf`, `variables.tf`, `outputs.tf` y `versions.tf`, `infra/.gitignore`, `infra/.terraform.lock.hcl` (hashes de cinco plataformas) y `.github/workflows/ci.yml` (trabajos `infra`, `infra-scripts` e `infra-plan` nuevos o reescritos; los de servicio y pantalla solo cambian por el fijado de acciones). `backend/`, `web/` y los archivos de la raíz no se tocaron.

## Decisiones de implementación

- Acciones de GitHub fijadas por hash de 40 caracteres, resueltos con la API pública de GitHub (solo lectura) y verificados como el commit de la etiqueta: `actions/checkout` v4.4.0, `actions/setup-python` v5.6.0, `actions/setup-node` v4.4.0, `hashicorp/setup-terraform` v3.1.2 y `aws-actions/configure-aws-credentials` v4.3.1; se mantuvieron los mayores que ya usaba el repositorio.
- Terraform 1.16.3 probado localmente (`required_version` en `>= 1.11`), proveedor `aws` acotado a `>= 5.90, < 6.0` con el archivo de bloqueo versionado. Checkov se instala con `pip` en versión fija (3.4.5) y corre solo en CI.
- Las afirmaciones que `terraform test` no puede expresar (ausencia de recursos, registros de acceso, sensibilidad en el plan real) las cubre `check_plan.py` con una lista de tipos permitidos y vetados, y dos comprobaciones de `grep` del trabajo `security`.

## Cobertura y resultados

| Parte | Pruebas | Resultado |
|-------|---------|-----------|
| `terraform test` en `infra/` | 46 en verde | `fmt -check` y `validate` limpios |
| `terraform test` en `infra/bootstrap/` | 33 en verde | `fmt -check` y `validate` limpios |
| Scripts de Python | 65 en verde | 98,09 % de cobertura (piso 80 %), Black y Ruff limpios |
| Comprobaciones | `check_pins` y `check_secrets` en OK sobre los flujos y `infra/` | — |
| Servicio y pantalla (sin cambios) | 558 y 186 en verde | — |

Verificado de forma independiente por el conductor al cerrar la etapa (mismos resultados). Una prueba de control con mutaciones (romper el `sub` de `main`, `s3:GetObject` del plan y un comodín en la confianza) hizo fallar cuatro afirmaciones.

## Correcciones de la revisión adversarial (pasada 1)

- **Crítico, resuelto:** el límite de permisos no obligaba a que los roles nuevos llevaran el límite, lo que permitía escalar a un administrador sin límite. Ahora hay dos límites (el de los roles creados, sin IAM ni S3, y el techo del rol de aplicación), una denegación `DenyUnboundedRoles` de `iam:CreateRole` e `iam:PutRolePermissionsBoundary` sin el límite esperado y una condición `iam:PermissionsBoundary` en la creación permitida; con pruebas que fallan si falta.
- **Aviso de seguridad, resuelto:** el rol de plan ya no tiene acceso al depósito de estado (el plan de las solicitudes corre sin estado), así que no puede leer los secretos de las federaciones.
- **Mayores, resueltos:** el retroceso del alias es durable con la variable de GitHub `LIVE_VERSION` y está documentado qué fallos cubre; los `triggers` del despliegue de la pasarela hashean el contenido; el modelo base solo recorta los prefijos `us.` y `global.`.
- **Menores, resueltos:** `check_plan.py` valida adjuntos de políticas administradas, URL de función y permisos con principal `*` y lee el nombre desde `before` en eliminaciones; `get-alias` distingue el primer despliegue de otros errores; las herramientas de CI tienen versiones exactas; la limitación de `ListBucket` sin prefijo se documentó como aceptada. Totales tras estas correcciones: 54 afirmaciones en `infra/`, 35 en `infra/bootstrap/`, 80 pruebas de Python con 98,13 % de cobertura.
- **Pasada 2 (revisión READY con un Mayor y dos Menores, resueltos después):** el rol de plan quedó con el único permiso `sts:GetCallerIdentity` y denegaciones explícitas de las lecturas que devuelven secretos (`DescribeIdentityProvider`, `GetFunction*`, Secrets Manager, SSM y el estado), porque `cognito-idp:Describe*` y `lambda:Get*` exponían el secreto de cliente de las federaciones y la lista de correos; el límite de los roles creados restringe `bedrock:InvokeModel` a las familias `anthropic.claude-*` y `amazon.titan-*`; la región se valida como `us-east-1` en las dos raíces. Estos tres cambios se verificaron con pruebas escritas primero y por el conductor (56 afirmaciones en `infra/`, 38 en `infra/bootstrap/`, 80 pruebas de Python con 98,13 %), pero no tuvieron una tercera revisión adversarial. Pendiente: confirmar en el primer `plan` de una solicitud que el proveedor de AWS solo necesita `sts:GetCallerIdentity`.

## Reparación X7 (regreso desde Build and Test, entrada 1 del Loop-Back Log)

- **Hallazgo:** la función Lambda se empaquetaba solo con `backend/` y sin `requirements*.txt`, de modo que `PyJWT[crypto]` y `cryptography` (que `token_verifier.py` y `jwks_store.py` importan al arrancar) no estaban en el paquete y todo despliegue habría fallado al importar. Lo encontró la etapa Build and Test al cruzar las unidades; ninguna prueba de una sola unidad lo veía.
- **Corrección:** `infra/scripts/build_lambda_package.py` construye `infra/build/package` (ignorada por git) con `backend/story_service` como paquete de nivel superior y las dependencias de `backend/requirements.txt` instaladas para Lambda (`python3.12`, `manylinux2014_x86_64`, solo ruedas binarias), de forma determinista y fallando si falta `jwt` o `cryptography`; `data.archive_file.story_service` de `infra/main.tf` comprime esa carpeta; `ci.yml` y `deploy.yml` ejecutan el script antes de validar, planificar y aplicar.
- **Dependencias fijadas:** la revisión de la reparación (READY, con un punto mayor y cuatro menores) pidió fijarlas. `infra/lambda-requirements.lock.txt` fija PyJWT 2.10.1, cffi 2.1.1, cryptography 50.0.2 y pycparser 3.12 con `--hash=sha256` calculados de las ruedas reales; el script instala con `--no-deps --require-hashes --only-binary=:all:` y las etiquetas `manylinux2014`, `manylinux_2_17` y `manylinux_2_28`. `boto3` y `botocore` quedan fuera del paquete porque el tiempo de ejecución `python3.12` de Lambda ya los trae (la versión de `boto3` la fija AWS, no el repositorio). Se quitan `bin/` y los `.exe`, `.bat` y `.cmd` del sistema donde se construye y se normalizan los `RECORD`; dos construcciones reales seguidas dieron el mismo contenido (214 archivos).
- **Verificación real (acceso a PyPI, sin AWS):** el paquete final tiene 214 archivos y pesa 4,8 MB comprimido (límite de Lambda 50 MB) y 15,3 MB descomprimido (límite 250 MB); contiene `story_service/handler.py`, `jwt/__init__.py` y las ruedas de Linux de `cryptography` (binarios ELF x86_64 con glibc 2.17 como máximo, compatible con la 2.34 de Lambda). Totales: 59 afirmaciones en `infra/`, 38 en `infra/bootstrap/`, 110 pruebas de Python con 97,65 % de cobertura; verificado de forma independiente por el conductor.
- **No verificado:** que el proveedor real de `archive_file` genere el zip desde la carpeta (solo el origen está afirmado), que `pip --platform` funcione en el ejecutor de GitHub y el arranque real de la función en Lambda (solo se comprobó la presencia y la arquitectura de los binarios).

## Pruebas existentes que cambiaron, y por qué

Ninguna prueba del servicio ni de la pantalla se modificó. Las direcciones de los recursos de preflight de la pasarela cambiaron a `aws_api_gateway_method.options["stories"]` y similares (por `for_each`), lo que ajusta las afirmaciones nuevas de u6 y no las de otras unidades.

## Pruebas escritas pero no ejecutadas en esta etapa

- `terraform plan`, `terraform apply`, el arranque y `terraform import`: nunca se ejecutaron ni se llamó a AWS.
- Checkov: las 31 omisiones de `infra/.checkov.yaml` se escribieron por expectativa, sin verificar; pueden necesitar ajuste tras la primera ejecución en CI.
- Ningún flujo de GitHub corrió (ambos parsean como YAML, pero no se ejecutó `actionlint`) y la prueba de humo real contra AWS solo se probó contra un servidor HTTP local.
- La verificación del arranque, de la protección de `main`, de las cuotas, del acceso a Bedrock, del efecto real del límite de permisos y del dominio de Cognito: manuales en `infra/README.md`.

## Desviaciones y brechas

1. Variable nueva `microsoft_tenant_id` (no secreta, por defecto el inquilino de cuentas personales de Microsoft): Cognito exige el emisor exacto y `common` no sirve; fuera del plan, a confirmar con la persona.
2. Salida nueva `web_distribution_id` para la invalidación de `/index.html`.
3. Los roles del arranque se llaman `pipeline-business-analyst-agent-*`, fuera del prefijo de la aplicación, para que el rol de aplicación no pueda administrarlos; el límite de los roles creados es `...-boundary` y el techo del rol de aplicación es `...-apply-boundary`.
4. `bedrock:InvokeModel` está solo en el límite de permisos y en el rol de la función, no en la política del rol de aplicación (la canalización no debe invocar el modelo).
5. El límite de permisos usa acciones con comodín por servicio, acotadas por recurso, por el tope de 6 144 caracteres de una política administrada; permite `cognito-idp:*` sobre `*`, más ancho que la política del rol de aplicación.
6. Prefijo del dominio de Cognito propuesto: `business-analyst-agent-x7k2m9`; si está tomado, la persona lo cambia en `infra/variables.tf`.
7. AC7.1.1 a AC7.1.3 (evaluación de modelos) son de u2; u6 solo concede el permiso de invocación.
