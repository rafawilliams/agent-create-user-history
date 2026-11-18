# Infraestructura (u6-infrastructure)

Terraform y canalización de GitHub Actions de la aplicación (React + API Gateway + Lambda + Bedrock + Cognito en AWS, región `us-east-1`, un solo entorno). No hay ningún valor real en el repositorio: los secretos y la lista de correos llegan por GitHub.

## Estructura

| Ruta | Quién la aplica | Qué crea |
|------|-----------------|----------|
| `infra/bootstrap/` | La persona, **una sola vez**, con credenciales administrativas | Depósito de estado (S3), proveedor OIDC de GitHub, límite de permisos y los roles de plan y de aplicación |
| `infra/` | La canalización (`deploy.yml` en `main`) | Función Lambda y su rol, API Gateway (`/v1/stories`, `/v1/session`, CORS), pantalla (S3 privado + CloudFront con política de cabeceras), Cognito (grupo, dominio, Google y Microsoft, cliente público) y métricas |
| `infra/tests/`, `infra/bootstrap/tests/` | CI y la persona | Afirmaciones de `terraform test` con proveedor simulado (sin AWS) |
| `infra/scripts/` | CI y `deploy.yml` | `check_plan.py`, `check_pins.py`, `check_secrets.py`, `smoke_test.sh` y sus pruebas |
| `.github/workflows/ci.yml`, `deploy.yml` | GitHub | Validación en cada solicitud y despliegue en `main` |

El rol de aplicación no puede modificar nada de `infra/bootstrap/` (límite de permisos y denegaciones explícitas): quien controla la canalización no controla las identidades que la gobiernan.

## Lista de verificación del arranque (una sola vez, por la persona)

Antes de este arranque la canalización solo valida: `ci.yml` omite el plan y `deploy.yml` termina en verde con un aviso mientras no exista la variable `AWS_APPLY_ROLE_ARN`.

1. **Aplicar el arranque.** Con credenciales administrativas de AWS, desde `infra/bootstrap/`:

   ```bash
   cd infra/bootstrap
   terraform init
   terraform apply -var github_repository=<organizacion>/<repositorio> -var state_bucket_name=<deposito-unico>
   ```

   Anotar las salidas (`state_bucket`, `plan_role_arn`, `apply_role_arn`). **Respaldar `terraform.tfstate` de esta carpeta fuera del repositorio** (está ignorado por git). Si se pierde, se reconstruye con `terraform import` de los pocos recursos del arranque (depósito y sus configuraciones, proveedor OIDC, límite y dos roles con sus políticas).
2. **Cuotas de la cuenta** (pedir la ampliación si hace falta, antes del primer despliegue):
   - Ejecuciones concurrentes de Lambda: AWS exige dejar 10 sin reservar, así que reservar 5 necesita una cuota de 15 o más. Si no se amplía, fijar `reserved_concurrency = -1` (el tope lo da el límite de la pasarela).
   - Tiempo máximo de integración de la pasarela REST: 58 000 ms (sin ampliación el tope es 29 000 ms y el `apply` falla).
   - Acceso de la cuenta al modelo de Bedrock configurado (`bedrock_model_id`).
3. **Prefijo del dominio de Cognito.** Está en `cognito_domain_prefix` de `infra/variables.tf` (valor fijo). Si ya está tomado en la región, cambiarlo ahí antes de seguir. Con él, crear la aplicación de Google y la de Microsoft Entra con la dirección de retorno `https://<prefijo>.auth.us-east-1.amazoncognito.com/oauth2/idpresponse` y copiar sus identificadores y secretos. En Entra, confirmar el inquilino: `microsoft_tenant_id` (por defecto el de las cuentas personales de Microsoft; el emisor `common` no sirve con Cognito).
4. **Secretos y variables de GitHub** (Settings > Secrets and variables > Actions; los nombres de las variables de entorno de Terraform distinguen mayúsculas y minúsculas):

   | Tipo | Nombre | Valor |
   |------|--------|-------|
   | Secreto | `TF_VAR_google_client_id`, `TF_VAR_google_client_secret` | Aplicación de Google |
   | Secreto | `TF_VAR_microsoft_client_id`, `TF_VAR_microsoft_client_secret` | Aplicación de Microsoft Entra |
   | Variable | `TF_VAR_allowed_emails` | Hasta 50 correos separados por comas, en minúsculas y sin espacios |
   | Variable | `STATE_BUCKET_NAME` | Salida `state_bucket` |
   | Variable | `AWS_PLAN_ROLE_ARN` | Salida `plan_role_arn` |
   | Variable | `AWS_APPLY_ROLE_ARN` | Salida `apply_role_arn` (al crearla se activa el despliegue) |
   | Variable (opcional) | `LIVE_VERSION` | Vacía en el uso normal (el alias `live` apunta a la última versión publicada). Solo se fija tras un retroceso (ver Retroceso) |

5. **Proteger `main`** (la persona lo confirma aquí; el `GITHUB_TOKEN` de los flujos no puede leer esta configuración): solo por solicitud, con la comprobación de CI obligatoria, sin envíos directos y **sin excepción para administradores**. Con un repositorio de una sola persona el autor no puede aprobar su propia solicitud: la revisión se cumple con la del propio autor sobre el plan que muestra CI y con la revisión asistida; es un riesgo aceptado y declarado (NFR5.7).
6. **Primer despliegue.** Integrar en `main` la solicitud con este código: el primer `deploy.yml` hace el primer `apply` y publica la pantalla. Un primer despliegue fallido no tiene versión previa a la que volver: se corrige hacia adelante en una nueva solicitud (o se destruye lo creado a mano).

## Paquete de la función (Lambda)

El zip de la función **no** sale de `backend/` a secas: `data.archive_file.story_service` comprime `infra/build/package`, que construye `infra/scripts/build_lambda_package.py`:

- el código de `backend/story_service` como paquete de nivel superior (el manejador es `story_service.handler.lambda_handler`);
- las dependencias de **ejecución** fijadas en `infra/lambda-requirements.lock.txt` (versiones exactas y `--hash=sha256`, calculados de las ruedas reales para Linux x86_64): PyJWT, cryptography, cffi y pycparser. Se instalan con `--no-deps --require-hashes --only-binary=:all:`, `--python-version 3.12 --implementation cp` y las etiquetas `manylinux2014_x86_64`, `manylinux_2_17_x86_64` y `manylinux_2_28_x86_64`. Los hashes se generaron con `pip download` para esas plataformas y `sha256` de cada rueda; no dependen de lo que PyPI publique después.

**Decisión: `boto3` y `botocore` no van en el paquete.** `story_service` los importa (cliente de Bedrock), pero el runtime `python3.12` de Lambda ya los trae y `backend/requirements.txt` pide `boto3>=1.34,<2`. Así el zip pesa 4,8 MB en lugar de 21 MB y no depende de una versión que PyPI cambie. Contrapartida: la versión de `boto3` la fija AWS con el runtime, no este repositorio.

**Determinismo (dado el archivo de bloqueo).** Mismas ruedas (por hash), sin cachés de compilación (`--no-compile`, sin `__pycache__`), sin restos del sistema de quien construye (`bin/`, `.exe`, `.bat`, `.cmd` y sus líneas en `RECORD`), `RECORD` ordenado y marcas de tiempo fijas: dos construcciones dan el mismo contenido byte a byte (verificado) y, por tanto, el hash del zip de `archive_file` es estable. Si se cambia el bloqueo, el paquete cambia a propósito. No se afirma que el zip sea idéntico entre versiones distintas de `pip` o de Python.

**El bloqueo no se desvía en silencio.** El script falla si una línea del bloqueo no lleva `==` y `--hash`, si falta alguna de PyJWT, cryptography, cffi o pycparser, si `boto3`/`botocore` aparecen en él, o si `backend/requirements.txt` pide una dependencia que el bloqueo no cubre (salvo las que trae el runtime). Para actualizar una dependencia: subir la versión en el bloqueo, descargar las ruedas con `pip download --no-deps --only-binary=:all: --platform ... -d <carpeta>` y recalcular su `sha256`.

**Hay que ejecutarlo antes de `terraform plan` y `apply`** (con el proveedor simulado de `terraform test` no hace falta). `ci.yml` (trabajos `infra` e `infra-plan`) y `deploy.yml` ya lo hacen, con `actions/setup-python` fijado por hash. Necesita acceso a PyPI y no usa credenciales de AWS:

```bash
python infra/scripts/build_lambda_package.py
REQUIRE_REAL_PACKAGE=1 python -m pytest infra/scripts/test_real_package.py -q -s   # contenido, binarios, glibc y tamaño
```

La carpeta `infra/build/` está ignorada por git. Medido en la verificación: 214 archivos, zip de 4,8 MB (límite de Lambda: 50 MB) y 15,3 MB descomprimido (límite: 250 MB). Los `.so` de Linux requieren glibc 2.17 como máximo (el runtime trae 2.34). **No verificado:** que la función arranque de verdad en Lambda (importar un `.so` de Linux es imposible desde Windows); eso se confirma en el primer despliegue.

## Flujos

- **`ci.yml`** (solicitudes y `main`): servicio, pantalla, scripts de infraestructura (Black, Ruff, pytest con 80 %), y para Terraform `fmt -check`, `validate`, `terraform test` en ambas raíces, fijado de acciones por hash y archivos de bloqueo (`check_pins.py`), patrones de secretos (`check_secrets.py`) y Checkov (versión fijada; omisiones documentadas en `infra/.checkov.yaml`). El plan de solo lectura (`infra-plan`) corre solo para solicitudes del propio repositorio y con `AWS_PLAN_ROLE_ARN`, con valores ficticios de secretos; usa estado vacío (`-backend=false`), así que sirve para `check_plan.py` y no detecta eliminaciones.
- **`deploy.yml`** (solo `main`, grupo de concurrencia `deploy` sin cancelar): `init` con `-backend-config`, captura de la versión del alias `live`, `plan -out`, `check_plan.py` sobre ese plan, `apply` de ese mismo archivo, compilación y publicación de la pantalla **sin `--delete`**, invalidación de `/index.html` y `smoke_test.sh`. El plan no se sube ni se imprime (solo un resumen por acción) y se borra de la máquina.

## Retroceso

- **Servicio:** si la prueba de humo falla, `deploy.yml` hace un segundo `apply` con `live_version` igual a la versión que tenía el alias antes del despliegue. **El retroceso no es duradero por sí solo:** `deploy.yml` pasa `TF_VAR_live_version` desde la variable de GitHub `LIVE_VERSION`; si sigue vacía, el siguiente despliegue vuelve a promover la última versión publicada (la mala). Tras un retroceso la persona debe fijar `LIVE_VERSION` a la versión previa que imprime el flujo, hasta liberar la corrección, y vaciarla después. Manual: `terraform apply -var live_version=<n>` con los mismos `TF_VAR_*`.
- **Qué fallos de la prueba de humo cubre el retroceso:** solo los del servicio (por ejemplo, `POST /v1/stories` sin token que no responde 401 con `SESSION_INVALID`, o un preflight roto por la función). Los fallos de la política de contenido, de las cabeceras, de CORS de la pasarela o de la pantalla no dependen de la versión de la función: se corrigen con un arreglo de la pantalla o de Terraform en una nueva solicitud (el retroceso del alias no los arregla).
- **Pantalla:** volver a desplegar el commit anterior (el depósito está versionado y conserva `index.html` anteriores). Tras un retroceso del servicio, la pantalla se vuelve a desplegar a mano.
- **Terraform:** revertir el commit en una nueva solicitud y aplicar. Las eliminaciones o reemplazos de recursos protegidos (grupo de usuarios, distribución, depósitos, función) los bloquea `check_plan.py`: la persona los aplica a mano si son intencionales.

## Verificación local (sin credenciales de AWS)

```bash
cd infra && terraform init -backend=false && terraform test
cd infra/bootstrap && terraform init -backend=false && terraform test
cd infra && terraform fmt -check -recursive && terraform validate
cd infra/scripts && python -m pytest -q --cov=. --cov-report=term-missing --cov-fail-under=80
cd infra/scripts && python -m black --check . && python -m ruff check .
python infra/scripts/check_pins.py .github/workflows --require-file infra/.terraform.lock.hcl --require-file infra/bootstrap/.terraform.lock.hcl
```

Nunca se ejecuta `terraform plan` ni `apply` contra AWS desde una máquina de trabajo: lo hace la canalización con sus roles.

## Prueba de humo

`infra/scripts/smoke_test.sh <web_url> <api_url> <cognito_domain>` comprueba que la raíz de la pantalla responde 200 con la política de contenido exacta y las demás cabeceras, que el preflight de `/v1/stories` y `/v1/session` responde con el origen exacto, `GET,POST,DELETE,OPTIONS` y `Authorization,Content-Type`, y que `POST /v1/stories` sin token responde 401 con `SESSION_INVALID`. No llama al modelo ni inicia sesión.

## Riesgos aceptados y supuestos

- El rol de plan lee el estado (que contiene el secreto de cliente de las federaciones) y ejecuta código de una rama del propio repositorio; el control es que solo una persona escribe en el repositorio y la protección de `main`.
- El secreto de cliente de las federaciones queda en el estado de Terraform (cifrado y restringido): es una limitación del proveedor.
- **Rol de plan sin acceso al estado:** el estado contiene los secretos de cliente de las federaciones, y el plan de las solicitudes corre con `init -backend=false`; por eso el rol de plan solo permite `sts:GetCallerIdentity` y niega explícitamente las lecturas que devuelven secretos (`cognito-idp:DescribeIdentityProvider`, `lambda:GetFunction*`, `secretsmanager:*`, `ssm:GetParameter*`) y los objetos del depósito de estado. Con `-backend=false` el plan parte de un estado vacío y no refresca nada. Si en el futuro el plan necesitara refrescar (estado remoto), habría que ampliar el rol con lecturas no secretas, una a una.
- **Dos límites de permisos:** el de los roles que Terraform crea (`pipeline-business-analyst-agent-boundary`: solo registros y `bedrock:InvokeModel`, sin IAM) y el techo del rol de aplicación (`...-apply-boundary`). Ambos y la política del rol de aplicación niegan `iam:CreateRole` e `iam:PutRolePermissionsBoundary` cuando el límite pedido no es el de los roles creados.
- **Limitación aceptada de `s3:ListBucket`:** la condición `StringLikeIfExists` sobre `s3:prefix` es necesaria para que un primer `init` devuelva 404 y no 403; como contrapartida, un listado sin prefijo (clave `s3:prefix` ausente) también se permite al rol de aplicación sobre el depósito de estado. No se endurece para no romper `init`.
- La lista de correos permitidos (`ALLOWED_EMAILS`) llega a la función como variable de entorno de texto: es visible para quien administra la cuenta de AWS y quien escribe en el repositorio.
- Las pruebas con proveedor simulado comprueban atributos declarados, no su efecto real en AWS: la efectividad del límite de permisos, la cuota de la pasarela y la propagación de CloudFront se confirman en el primer despliegue.
- `unsafe-inline` solo en estilos (MUI con emotion): riesgo aceptado de u5; los scripts no permiten código en línea.
