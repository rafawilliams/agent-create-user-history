# Unit Test Instructions — u2-model-gateway

Estrategia de pruebas: Standard (5 a 8 pruebas por componente, más pruebas de integración de los límites clave). Metodología: TDD; cada prueba se escribe antes del código, se ejecuta en rojo y luego se implementa lo mínimo para que pase.

## Requisitos previos

- Python 3.11 o superior con las dependencias de desarrollo ya instaladas por u1 (`python -m pip install -r backend/requirements-dev.txt`).
- Sin credenciales de AWS: las pruebas automáticas no llaman a Bedrock ni a ningún servicio de AWS.

## Configuración de las herramientas

| Parte | Herramienta | Configuración |
|-------|-------------|---------------|
| Servicio | `pytest` y `pytest-cov` | `backend/pyproject.toml` (ya existe) |
| Servicio | Black y Ruff | `backend/pyproject.toml` (ya existe) |
| Infraestructura | `terraform fmt` y `terraform validate` | `infra/` |

## Comandos para ejecutar las pruebas de ESTA unidad

Las pruebas de u2 están en estos archivos de `backend/tests/`: `test_error_translation.py`, `test_model_profile.py`, `test_evaluation.py`, `test_evaluate_models.py`, y las pruebas nuevas de `test_bedrock_client.py` y `test_models_errors.py`. El comando se limita a esos archivos:

```bash
cd backend && python -m pytest tests/test_error_translation.py tests/test_model_profile.py tests/test_evaluation.py tests/test_evaluate_models.py tests/test_bedrock_client.py tests/test_models_errors.py -q
```

Ninguno es un comando general del proyecto.

```bash
cd infra && terraform fmt -check && terraform validate
```

## Cobertura

- **Piso:** 80 % de cobertura de líneas (`team.md`, `mvp`). Es un piso del proyecto entero: lo comprueba Build and Test sobre la suite completa del proyecto ensamblado. Una ejecución con el umbral puede fallar por el umbral aunque todas las pruebas pasen; por eso se ejecuta en un comando aparte, sin pasos después, y nunca se baja el umbral para que pase.

```bash
cd backend && python -m pytest tests -q --cov=story_service --cov-report=term-missing --cov-fail-under=80
```

- **Objetivo de esta unidad:** 80 % o más en los archivos de u2 (`error_translation.py`, `model_profile.py`, `evaluation.py`, `evaluate_models.py`, y los cambios de `bedrock_client.py` y `config.py`), informado aparte del piso del proyecto.

## Comando de evaluación real (manual)

Genera con cada modelo los 5 títulos aprobados y escribe `docs/evaluacion-modelos.md`. Requiere que la persona apruebe los títulos, el identificador de Amazon Titan de la cuenta y credenciales de AWS con acceso a los modelos en us-east-1; no se ejecuta en la suite automática ni en CI.

```bash
cd backend && python -m story_service.evaluate_models approve
cd backend && python -m story_service.evaluate_models run
```

- Los 5 títulos propuestos están en `docs/titulos-evaluacion.md` (sin la línea `aprobado:`); la persona los revisa y ejecuta `approve`.
- Los modelos salen de la variable `EVALUATION_MODEL_IDS` (lista separada por comas; el modelo por defecto siempre se evalúa). Sin ella se evalúan `us.anthropic.claude-sonnet-4-6` y la propuesta `us.amazon.titan-text-premier-v1:0`, que hay que confirmar contra los perfiles de la cuenta (`aws bedrock list-inference-profiles`, solo lectura) antes de la primera ejecución real.

## Dobles de prueba (mocking)

- El cliente `bedrock-runtime` se sustituye con un doble de prueba que lanza errores con códigos de AWS y textos con un ARN falso; nunca se llama a AWS.
- Los modelos de la evaluación se simulan con el modelo simulado de u1 (`fakes.py`), con respuestas válidas, sin el formato esperado, bloqueadas (`access_not_enabled`) y fallidas.
- El reloj es inyectable para probar el tiempo por llamada y la tolerancia de 1 s.

## Datos de prueba

- Títulos inventados de ejemplo dentro de los archivos de prueba; el archivo de títulos de una prueba se escribe en un directorio temporal.
- Identificadores de modelo: válidos (`us.anthropic.claude-sonnet-4-6`, `us.amazon.titan-text-premier-v1:0`) e inválidos (otro proveedor, con un error de escritura dentro de un proveedor válido, vacío).
- No hay datos guardados ni archivos de datos externos.

## Pruebas que no corren en esta etapa

- La evaluación real contra Bedrock (necesita aprobación de los títulos, el identificador de Titan y credenciales de AWS).
- `terraform plan` y el despliegue (necesitan la cuenta de AWS y el estado remoto de Terraform).
