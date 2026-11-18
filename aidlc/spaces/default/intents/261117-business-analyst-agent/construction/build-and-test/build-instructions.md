# Instrucciones de compilación y verificación — Build and Test

Todos los comandos se ejecutan desde la raíz del repositorio salvo que se indique otro directorio. En Windows se usó Git Bash; los comandos son los mismos en cualquier shell POSIX. Cada comando de abajo se ejecutó una vez en esta etapa; sus resultados están en `test-results.md`.

## 1. Requisitos previos

| Herramienta | Versión usada | Para qué |
|-------------|---------------|----------|
| Python | 3.13.3 (la función Lambda usa `python3.12`) | servicio y scripts de infraestructura |
| Node.js y npm | los de la máquina; `node_modules` ya instalado | pantalla |
| Terraform | 1.16.3 (`required_version >= 1.11`) | `infra/` e `infra/bootstrap/` |

No hace falta ninguna credencial de AWS para nada de lo que sigue.

## 2. Instalación de dependencias

```
python -m pip install -r backend/requirements-dev.txt
cd web && npm ci            # solo si falta node_modules; en esta etapa ya existía y no se ejecutó
cd infra && terraform init -backend=false -input=false
cd infra/bootstrap && terraform init -backend=false -input=false
```

Notas:
- `backend/requirements.txt` fija `PyJWT[crypto]==2.10.1` y `boto3>=1.34,<2`. En el entorno local de esta máquina las dependencias están instaladas en el Python del usuario (sin entorno virtual: la creación falló en u1).
- `terraform init -backend=false` crea `infra/.terraform/` y `infra/bootstrap/.terraform/`; ambos están ignorados por git. Las pruebas y Black/Ruff también dejan `.coverage`, `.pytest_cache` y `.ruff_cache` (ignorados).

## 3. Configuración del entorno

### Servicio (`backend/`)

Las pruebas no necesitan variables: usan modelos simulados y claves RSA generadas dentro de las pruebas. Las variables que lee el servicio desplegado (mismos nombres que fija `infra/main.tf`):

`APP_ENV`, `BEDROCK_MODEL_ID`, `BEDROCK_REGION`, `CORS_ALLOWED_ORIGIN`, `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, `ALLOWED_EMAILS`. Opcionales: `BEDROCK_TIMEOUT_SECONDS_CLAUDE`, `BEDROCK_TIMEOUT_SECONDS_TITAN` (50 s por defecto), `STORY_INSTRUCTIONS`, `ALLOW_SIMULATED_SESSION` (solo con `APP_ENV` en `local` o `test`).

### Pantalla (`web/`)

Cinco variables públicas `VITE_`. Para compilar sin un despliegue real se usaron valores ficticios:

```
export VITE_API_URL=https://example.invalid
export VITE_COGNITO_REGION=us-east-1
export VITE_COGNITO_USER_POOL_ID=us-east-1_dummy
export VITE_COGNITO_DOMAIN=dummy.auth.us-east-1.amazoncognito.com
export VITE_COGNITO_CLIENT_ID=dummy
```

En un despliegue real salen de las salidas de Terraform (`api_url`, `cognito_region`, `cognito_user_pool_id`, `cognito_domain`, `cognito_client_id`).

## 4. Comandos de compilación

| Parte | Comando | Qué produce |
|-------|---------|-------------|
| Pantalla | `cd web && npm run build` (`tsc --noEmit && vite build`) | `web/dist/` con `index.html` y 5 paquetes JS (`index`, `react`, `mui`, `oidc` y `MarkdownPreview` diferido) |
| Servicio | no hay paso de compilación: el código Python se empaqueta tal cual | `infra/build/story_service.zip` lo arma Terraform con `archive_file` sobre `backend/` |
| Terraform | `cd infra && terraform init -backend=false -input=false && terraform validate` | configuración válida |

**Empaquetado de la función (reparado en el regreso 1, hallazgo X7):** `python infra/scripts/build_lambda_package.py` arma `infra/build/package` con `story_service/` y las dependencias de `infra/lambda-requirements.lock.txt` (fijadas con hashes) instaladas para `python3.12` y `manylinux2014_x86_64`, sin `boto3`/`botocore` (los trae Lambda); `data.archive_file` de `infra/main.tf` comprime esa carpeta, y `ci.yml` y `deploy.yml` ejecutan el script antes de Terraform. Para verificar el paquete ya construido sin reconstruirlo: `cd infra/scripts && REQUIRE_REAL_PACKAGE=1 python -m pytest -q`. El script necesita acceso a PyPI y no se volvió a ejecutar en la segunda pasada.

## 5. Verificación de la compilación

```
cd backend && python -m black --check . && python -m ruff check .
cd web && npm run format:check && npm run lint && npm run build
cd web && npm run check:bundle && npm run check:secrets && npm run check:inline
cd web && npm audit --omit=dev --audit-level=high
cd infra && terraform fmt -check -recursive && terraform validate
cd infra/bootstrap && terraform fmt -check -recursive && terraform validate
cd infra/scripts && REQUIRE_REAL_PACKAGE=1 python -m pytest -q --cov=. --cov-fail-under=80
cd infra/scripts && python -m black --check . && python -m ruff check .
python infra/scripts/check_pins.py .github/workflows
python infra/scripts/check_secrets.py infra .github
```

Resultado esperado: todos con código de salida 0. `check:bundle` imprime el total inicial en bytes gzip frente al presupuesto de 409 600.

## 6. Infraestructura como código: comprobaciones estáticas

Para cada raíz de Terraform (`infra/` e `infra/bootstrap/`): `terraform fmt -check -recursive`, `terraform init -backend=false -input=false`, `terraform validate` y `terraform test` (planes simulados con `override_data`; sin AWS). Reglas de política como código que corre el proyecto: `infra/scripts/check_plan.py` (sobre `terraform show -json`), `check_pins.py` y `check_secrets.py`. Checkov (versión 3.4.5) corre solo en CI y no se ejecutó aquí. Nunca se ejecuta `terraform plan` ni `apply` desde esta etapa.

## 7. Solución de problemas

| Síntoma | Causa probable | Qué hacer |
|---------|----------------|-----------|
| `npm run build` falla con "Faltan variables de configuración" en las pruebas o en la compilación | falta alguna de las cinco `VITE_` | exportarlas (valores ficticios sirven para compilar) |
| `terraform init` pide un backend | se olvidó `-backend=false` | repetir con `-backend=false -input=false` |
| `terraform test` pide credenciales | se cambió `command = plan` por `apply` o se quitó el proveedor simulado | restaurar el archivo de prueba; la suite no debe llamar a AWS |
| `pytest` falla una vez en `test_bedrock_client` por tiempo | prueba sensible a la carga de la máquina (u3, desviación 5) | repetir; si persiste, revisar la carga |
| Aviso de `black`/`ruff` por archivos sueltos | `.coverage` y cachés en la carpeta | están ignorados por git; no afectan el resultado |
| La pantalla compila pero `check:secrets` marca `client_secret` | un valor literal asignado a `client_secret` en el paquete | no debe haber secretos en la pantalla; quitar el valor |
