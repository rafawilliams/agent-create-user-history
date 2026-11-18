# Code Summary — u1-walking-skeleton

## Archivos creados

- **`backend/`** (servicio en Python): `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.env.example`, `.gitignore`; `story_service/` con `models.py`, `errors.py`, `ports.py` (C3 `SessionVerifier` y C4 `ModelClient`), `prompt.py`, `config.py`, `fakes.py`, `service.py`, `logging_utils.py`, `bedrock_client.py`, `handler.py`, `local_run.py`; `tests/` con 8 archivos de prueba.
- **`web/`** (pantalla en React con MUI): `App.tsx`, `api.ts`, `main.tsx` y sus pruebas, más configuración de Vite, TypeScript, ESLint y Prettier.
- **`infra/`** (Terraform mínimo): `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`.
- **`.github/workflows/ci.yml`**: etapas 1 a 4 de `cicd-pipeline.md` (estilo, pruebas con cobertura, Terraform, pruebas de seguridad del diseño).

## Archivos modificados

- `inception/contract-design/contract-summary.md`: respuesta 429 `RATE_LIMITED` añadida a C1 (cambio aditivo, Step 2).
- `functional-design/functional-spec.md`: nota del cambio aditivo bajo la tabla de W3.
- No se tocaron `.env`, `.env.example`, `.gitignore`, `README.md`, `requirements.txt`, los Excel ni `generador_historias.py` de la raíz.

## Decisiones de implementación

- Interfaces C3 y C4 como `Protocol`, con un modelo simulado y un verificador simulado; el verificador simulado solo se enlaza con `APP_ENV` en `local` o `test` y `ALLOW_SIMULATED_SESSION` verdadero; en cualquier otro caso se enlaza uno que falla cerrado (BR1.5).
- Plazo de 55 s con reloj inyectable; el tiempo de espera del modelo es el menor entre 50 s y el tiempo restante; un solo reintento ante `transient` o `unavailable` y solo si queda tiempo; sin reintento tras `timeout`.
- Los registros llevan solo `requestId`, `outcome`, `durationMs` y `modelId`; las métricas salen como registros JSON y `main.tf` crea filtros de métricas de CloudWatch.
- `requestId` es un UUID versión 4.
- Modelo por defecto: `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (`BEDROCK_MODEL_ID`), **sin verificar contra la cuenta**.
- Un cuerpo ausente, no JSON o sin título devuelve `TITLE_EMPTY` 400; una excepción inesperada devuelve `MODEL_FAILURE` 502 no reintentable, sin traza.
- El tiempo de espera por llamada del cliente de Bedrock se aplica esperando el resultado en un hilo con ese tope; el hilo puede seguir hasta su propio tope de 50 s sin afectar a la solicitud.

## Cobertura y resultados

| Parte | Pruebas | Cobertura de líneas | Herramientas de estilo |
|-------|---------|---------------------|------------------------|
| Servicio (Python) | 95 en verde | 98,66 % (piso 80 %, `fail_under = 80` intacto) | Black y Ruff sin errores |
| Pantalla (React) | 12 en verde | 100 % | Prettier, ESLint, `tsc` y `npm run build` sin errores |
| Terraform 1.16.3 | `fmt -check` y `validate` correctos | No aplica | Sin `plan` ni `apply` |

Se volvió a ejecutar la suite del servicio al cerrar la etapa: 95 pruebas en verde y 98,66 %.

## Hallazgos de la revisión resueltos o abiertos

- **Resuelto:** el nivel del registro no estaba fijado, y el entorno de ejecución de AWS deja el registrador raíz en WARNING, así que los registros y las métricas no se habrían emitido. Se escribió primero una prueba en rojo y luego se fijó el nivel INFO en `logging_utils.py`; la suite quedó en 96 pruebas en verde con 98,67 % de cobertura. Hay que confirmar la emisión en el primer despliegue real.
- **Abierto (menor):** el ARN del modelo base usa región comodín; se puede acotar a las regiones de EE. UU. en `u6-infrastructure`.
- **Abierto (menor):** una excepción inesperada del manejador no emite registro ni métrica, y un fallo al crear el cliente de Bedrock sale como error de la función sin cuerpo de C1 ni CORS.
- **Abierto (menor):** solo la respuesta de limitación de la pasarela lleva CORS; un 504 o 5XX generado por la pasarela llegaría al navegador como fallo de red.
- **Abierto (menor):** la prueba del punto de entrada de la función solo cubre `APP_ENV=prod` sin bandera; los otros casos se prueban en `build_session_verifier`.

## Verificación de punta a punta (ejecutada)

El comando aprobado (`cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"`) pasó: 100 pruebas en verde y una llamada real a Amazon Bedrock con `us.anthropic.claude-sonnet-4-6` que devolvió una historia que empieza con "Como analista de negocio" con 3 escenarios en Gherkin, en 4,5 s (NFR1.3). Para llegar ahí se corrigieron dos cosas: (1) el modelo por defecto pasó a Sonnet 4.6 (en `config.py` y `infra/variables.tf`), porque Sonnet 4.5 está marcado como heredado en la cuenta y Sonnet 5.5 no está disponible todavía; (2) las instrucciones piden ahora empezar la respuesta sin encabezados, porque el modelo la abría con "# Historia de Usuario" y se rechazaba con `INVALID_MODEL_RESPONSE` (prueba escrita antes). La relación de la historia con el título (BR1.2) sigue siendo una revisión manual. El modelo se cambia a Sonnet 5.5 cuando la cuenta lo habilite.

## Pruebas escritas pero no ejecutadas en esta etapa

- **`terraform plan` y `apply`**, y el despliegue y la prueba de humo (etapas 5 y 6 del flujo): necesitan la cuenta de AWS y el estado remoto de `u6-infrastructure`; las etapas 5 y 6 no se escribieron, como pedía el plan.
- **`ci.yml`** no se ejecutó en GitHub Actions; el plan de Terraform solo corre si existe la variable `AWS_PLAN_ROLE_ARN`.

## Cómo ejecutar el comando de punta a punta

Desde `backend/`, con `APP_ENV=local` y `ALLOW_SIMULATED_SESSION=true`, y credenciales de AWS válidas con acceso al modelo en us-east-1.

## Desviaciones y brechas

1. **Sin entorno virtual:** la creación falló en esta máquina; las dependencias de desarrollo se instalaron en el Python del usuario (3.13.3). Anotado en `unit-test-instructions.md`.
2. **Instalación de npm:** se hace desde `web/` (`cd web && npm install`).
3. **`timeoutSeconds` fraccionario:** C4 dice entero; la interfaz lo recibe como decimal porque el plazo restante puede serlo. Es un desajuste con C4 que debe resolverse con `u2-model-gateway` (cambio de contrato a coordinar).
4. **Métricas:** `errors_total` no lleva la dimensión `code` en CloudWatch (sí aparece en el registro); los filtros de métricas no estaban en el plan escrito y se añadieron para que las métricas existan en AWS.
5. **IAM de Bedrock:** el ARN del modelo base usa región comodín porque el perfil de inferencia enruta entre regiones; es un permiso más amplio que el diseño, a revisar en `u6-infrastructure`.
6. **Supuestos de infraestructura sin confirmar:** la integración de 58 s y la concurrencia reservada de 5 dependen de cuotas de la cuenta; si no se pueden obtener, usar `reserved_concurrency = -1` o la alternativa de `infrastructure-specification.md`.
7. **Reglas de herramientas:** el desarrollador usó el shell en lugar de las herramientas de archivo en tres ediciones puntuales (`sed`, una edición con Python y un `cat >>`) y borró con `rm` un `.venv` roto y el `.coverage` que había generado. El resultado se comprobó volviendo a ejecutar la suite.
8. **Estado previo del repositorio:** `.gitignore` y `generador_historias.py` ya aparecían modificados antes de empezar y no se tocaron.
