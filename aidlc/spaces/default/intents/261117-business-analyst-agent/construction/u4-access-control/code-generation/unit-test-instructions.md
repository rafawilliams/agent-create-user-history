# Unit Test Instructions — u4-access-control

Estrategia de pruebas: Standard (5 a 8 pruebas por componente, más pruebas de integración de los límites clave). Metodología: TDD; cada prueba se escribe antes del código, se ejecuta en rojo y luego se implementa lo mínimo para que pase.

## Requisitos previos

- Python 3.11 o superior con las dependencias de desarrollo ya instaladas por u1 (`python -m pip install -r backend/requirements-dev.txt`) y las dependencias de ejecución del servicio, incluida la biblioteca de JWT que este plan agrega a `backend/requirements.txt` (`python -m pip install -r backend/requirements.txt`).
- Sin credenciales de AWS y sin acceso a Cognito: las pruebas automáticas firman sus tokens con un par de claves RSA generado en las propias pruebas y simulan el servidor de claves.

## Configuración de las herramientas

| Parte | Herramienta | Configuración |
|-------|-------------|---------------|
| Servicio | `pytest` y `pytest-cov` | `backend/pyproject.toml` (ya existe) |
| Servicio | Black y Ruff | `backend/pyproject.toml` (ya existe) |

## Comandos para ejecutar las pruebas de ESTA unidad

Las pruebas de u4 están en estos archivos de `backend/tests/`: `test_auth_config.py`, `test_jwks_store.py`, `test_token_verifier.py`, `test_account_allowlist.py`, `test_access_control.py`, y las pruebas nuevas de `test_models_errors.py` y `test_handler.py`. El comando se limita a esos archivos:

```bash
cd backend && python -m pytest tests/test_auth_config.py tests/test_jwks_store.py tests/test_token_verifier.py tests/test_account_allowlist.py tests/test_access_control.py tests/test_models_errors.py tests/test_handler.py -q
```

Ninguno es un comando general del proyecto.

## Cobertura

- **Piso:** 80 % de cobertura de líneas (`team.md`, `mvp`). Es un piso del proyecto entero: lo comprueba Build and Test sobre la suite completa del proyecto ensamblado. Una ejecución con el umbral puede fallar por el umbral aunque todas las pruebas pasen; por eso se ejecuta en un comando aparte, sin pasos después, y nunca se baja el umbral para que pase.

```bash
cd backend && python -m pytest tests -q --cov=story_service --cov-report=term-missing --cov-fail-under=80
```

- **Objetivo de esta unidad:** 80 % o más en los archivos de u4 (`auth_config.py`, `jwks_store.py`, `token_verifier.py`, `account_allowlist.py` y los cambios de `models.py`, `errors.py`, `config.py`, `service.py`, `logging_utils.py` y `handler.py`), informado aparte del piso del proyecto.

## Comando de punta a punta (manual, aprobado como comando de verificación)

```bash
cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"
```

Corre la suite y luego el servicio completo contra el modelo real de Amazon Bedrock con el verificador simulado local; necesita credenciales de AWS con acceso al modelo. No ejercita Cognito: la verificación real con inicio de sesión de Google o Microsoft solo es posible cuando `u6-infrastructure` cree el grupo de usuarios y la persona entregue las credenciales de las federaciones.

## Dobles de prueba (mocking)

- Un par de claves RSA generado en las pruebas firma los tokens; las pruebas arman tokens con cada defecto (algoritmo, `kid`, firma, claims, fechas).
- El servidor de claves se simula con respuestas válidas, mal formadas, de más de 64 KB, con una redirección a otro host, con tiempo agotado y caído; el reloj es inyectable.
- Nunca se llama a Cognito ni a AWS.

## Datos de prueba

- Correos inventados de ejemplo y una lista de 0, 1, 50 y 51 entradas; los tokens llevan `sub`, `email` y `email_verified` de prueba.
- Todo vive dentro de los archivos de prueba; no hay datos guardados.

## Pruebas que no corren en esta etapa

- La verificación real contra Cognito con un inicio de sesión de Google o de Microsoft: necesita el grupo de usuarios de `u6-infrastructure` y las credenciales de las federaciones de la persona.
- `terraform plan` y el despliegue.
