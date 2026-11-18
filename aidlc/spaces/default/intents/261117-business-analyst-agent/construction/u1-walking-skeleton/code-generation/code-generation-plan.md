# Code Generation Plan — u1-walking-skeleton

## Summary

- Builds: el esqueleto ambulante: servicio de generación en Python (interfaces C3 y C4, modelos simulados, llamada real a Amazon Bedrock, forma de C1), pantalla mínima en React y la infraestructura mínima en Terraform con su flujo de CI.
- Touches: carpetas nuevas `backend/`, `web/`, `infra/` y `.github/workflows/`; el script y los archivos existentes de la raíz no se modifican.
- Tests: unas 45 pruebas automáticas (unitarias por componente más pruebas de integración de los límites clave), escritas antes del código (TDD), con piso de 80 % de cobertura de líneas.

Idioma de los artefactos de esta etapa: español. Identificadores del código nuevo: inglés (`team.md`, Code Style).

## Entradas

`functional-spec.md`, `rules.md` (BR1.1 a BR1.6), `entities.md`, `contract-summary.md` (C1, C3, C4), `performance-design.md`, `security-design.md`, `scalability-design.md`, `observability-design.md`, `infrastructure-specification.md`, `cicd-pipeline.md`, `unit-of-work.md`, `requirements.md`.

## Decisiones de construcción

- **Proyecto existente:** `generador_historias.py`, `README.md`, `requirements.txt`, `.env`, `.env.example`, `.gitignore` y los Excel son de la persona y no se tocan (el script sigue intacto hasta aceptar el MVP). Las dependencias nuevas van en archivos propios de `backend/`.
- **Lenguajes y herramientas:** Python 3.11 o superior con `pytest`, `pytest-cov`, Black y Ruff; React con TypeScript, Vite, Vitest, Testing Library, Prettier y ESLint (elección de herramientas de prueba que el equipo dejó pendiente para el diseño; es una propuesta que se aprueba con este plan). La interfaz usa Material Design con MUI (decisión de la persona).
- **Formato del `requestId`:** UUID versión 4 como texto (abierto en `entities.md`; se fija aquí).
- **Sin persistencia:** ningún paso crea tablas ni almacenes de datos (NFR4.1).
- **Cambio de contrato RATE_LIMITED:** aditivo; se registra en C1 antes de escribir código que lo use (ver Step 2).

## Estructura prevista

```
backend/
  pyproject.toml            (Black, Ruff, pytest, cobertura 80 %)
  requirements.txt          (boto3)
  requirements-dev.txt      (pytest, pytest-cov, black, ruff)
  story_service/
    models.py  ports.py  errors.py  prompt.py  config.py
    fakes.py   service.py  bedrock_client.py  logging_utils.py
    handler.py  local_run.py
  tests/
web/
  package.json  vite.config.ts  tsconfig.json  eslint y prettier
  src/ (App.tsx, api.ts, main.tsx)  src/__tests__/
infra/
  main.tf  variables.tf  outputs.tf  versions.tf  (Terraform)
.github/workflows/ci.yml
```

## Pasos

### Preparación

- [x] **Step 1 — Estructura del proyecto y configuración de producción.** Crear las carpetas `backend/`, `web/`, `infra/` y `.github/workflows/`, `pyproject.toml` (Black, Ruff, pytest, umbral de cobertura 80 % en `[tool.coverage.report] fail_under`), `requirements.txt` y `requirements-dev.txt`. Sin código de negocio. NFR8.2, NFR8.3.
- [x] **Step 2 — Cambio de contrato RATE_LIMITED.** Añadir el código `RATE_LIMITED` (HTTP 429, `retryable` verdadero) a C1 en `contract-summary.md` y a la tabla de W3 de `functional-spec.md` como cambio aditivo registrado, indicando que lo produce solo el límite de uso de la pasarela. Referencia: `scalability-design.md`. No hay código en este paso.
- [x] **Step 3 — Verificar el ejecutor de pruebas y registrar el comando por unidad.** Instalar las dependencias de desarrollo en un entorno virtual local, comprobar que `python -m pytest backend/tests` y `npm --prefix web run test` arrancan (aunque aún no haya pruebas), y registrar los comandos exactos en `unit-test-instructions.md`. Debe ocurrir antes de la primera prueba en rojo.

### Modelo de datos (comportamiento de las entidades) — `models.py`, `errors.py`

Entidades nombradas, todas con origen en `entities.md`: `StoryRequest` (`requestId`, `title`; BR1.3, FR1.3), `StoryResult` (`requestId`, `markdown`; BR1.1), `ModelResponse` (`text`, `modelId`), `ModelError` (`kind` con `transient`, `timeout`, `unavailable`, `access_denied`; `message`), `Session` (`sessionId`, `accountId`, `provider`, `expiresAt`), `SessionInvalid` (`reason`), y el cuerpo de error de C1 (`code`, `message`, `retryable`, `requestId` opcional). Sin base de datos ni migraciones.

- [x] **Step 4 — Rojo.** Escribir las pruebas de las entidades: el título se recorta, un título vacío o de solo espacios es inválido, no hay entidades sin los campos obligatorios, la tabla de códigos de error (BR1.4: `transient`→`MODEL_FAILURE` 502 reintentable; `timeout`→`GENERATION_TIMEOUT` 504; `unavailable`→`MODEL_FAILURE` 502; `access_denied`→`MODEL_FAILURE` 502 no reintentable) y el cuerpo de error con la forma de C1. Ejecutar y guardar la salida en rojo. Cubre BR1.3, BR1.4, AC2.1.4 (parte N/A).
- [x] **Step 5 — Verde.** Implementar solo lo necesario en `models.py` y `errors.py` para pasar.
- [x] **Step 6 — Refactor.** Mejorar nombres y duplicación con las pruebas en verde.

### Acceso a datos

Este nivel no aplica: el servicio no guarda nada (NFR4.1). No hay pasos de repositorio.

### Lógica de negocio — `ports.py`, `prompt.py`, `config.py`, `fakes.py`, `service.py`, `logging_utils.py`

- [x] **Step 7 — Rojo.** Escribir las pruebas con el modelo simulado y el verificador simulado:
  - Camino feliz (W1): sesión válida, título válido, el modelo devuelve "Como analista de negocio …" y el servicio devuelve `StoryResult` con el `requestId` y el Markdown (AC2.1.1, AC2.1.2, BR1.1, BR1.2).
  - Título vacío (W2): no llama al modelo, devuelve `TITLE_EMPTY` (BR1.3).
  - Título de más de 200 caracteres: `TITLE_TOO_LONG` (NFR4.4).
  - Fallo del modelo (W3) para cada `kind` con la tabla de BR1.4.
  - Respuesta fuera de contrato (W4): `INVALID_MODEL_RESPONSE` 502 reintentable, sin texto parcial; con espacios y saltos al inicio sigue siendo válida; distingue mayúsculas (BR1.1).
  - La petición al modelo pide la historia y de 2 a 3 criterios en Gherkin en español con Dado, Cuando y Entonces (BR1.6, AC2.1.3 parcial) y el título va dentro de un delimitador fijo, separado de las instrucciones (NFR4.4).
  - Plazo: el tiempo de espera del modelo es el menor entre 50 s y el tiempo restante hasta 55 s con un reloj inyectable (NFR1.1, NFR1.2); un `timeout` no se reintenta; un fallo `transient` o `unavailable` se reintenta una sola vez y solo si queda tiempo (NFR1.6); sin tiempo, devuelve `GENERATION_TIMEOUT` (NFR1.5).
  - Verificador de sesión: `SessionInvalid` devuelve `SESSION_INVALID` 401 sin llamar al modelo (NFR5.2).
  - Composición (BR1.5): el verificador simulado solo se enlaza con `APP_ENV` igual a `local` o `test` y `ALLOW_SIMULATED_SESSION` verdadero; con cualquier otro valor, sin él o con la variable por defecto, se enlaza un verificador que falla cerrado y rechaza todo con `SESSION_INVALID`.
  - Registros: la salida de registro tiene solo `requestId`, `outcome`, `durationMs`, `modelId` y no contiene el título, el Markdown ni la cabecera `Authorization` (NFR4.2, NFR4.3).
  - Ejecutar y guardar la salida en rojo.
- [x] **Step 8 — Verde.** Implementar las interfaces `SessionVerifier` (C3) y `ModelClient` (C4) como `Protocol`, el modelo simulado de respuesta fija, el verificador simulado, el verificador que falla cerrado, la composición por entorno, el armado de la petición con las instrucciones en configuración (ADR-003) y el servicio con el plazo y el reintento acotado, más el registro con lista cerrada de campos y las métricas `requests_total`, `errors_total` y `generation_duration_ms` emitidas por registro estructurado (NFR1.4, NFR3.3, NFR4.5).
- [x] **Step 9 — Refactor.** Simplificar con las pruebas en verde; el servicio queda sin estado entre solicitudes (NFR3.1).

### API / punto de entrada — `bedrock_client.py`, `handler.py`, `local_run.py`

- [x] **Step 10 — Rojo.** Pruebas del manejador de la función y del cliente real, ambas sin llamar a AWS (cliente de Bedrock simulado con un doble de prueba):
  - Manejador: `POST /v1/stories` con cuerpo válido devuelve 200 con `requestId` y `markdown`; el token Bearer sale de la cabecera `Authorization`; cuerpo inválido o sin título devuelve 400 con la forma del error de C1; cabeceras CORS solo para el origen configurado; el tiempo de ejecución restante de la función se usa como plazo; ninguna respuesta de error incluye rastros de pila.
  - Cliente de Bedrock: traduce la respuesta a `ModelResponse` y las excepciones de AWS a `ModelError` (`ThrottlingException`→`transient`, tiempo agotado→`timeout`, `ServiceUnavailable`→`unavailable`, `AccessDeniedException`→`access_denied`); el registro de invocaciones no es parte del código.
  - Ejecutar y guardar la salida en rojo.
- [x] **Step 11 — Verde.** Implementar `handler.py` (entrada de la función Lambda detrás de la pasarela REST), `bedrock_client.py` con el cliente `bedrock-runtime` creado una vez por instancia (reuso de conexión, NFR1.x) y el modelo y la región por configuración, y `local_run.py`.
- [x] **Step 12 — Refactor.** Pruebas en verde; sin credenciales en el código (NFR5.1), configuración solo por variables de entorno.
- [x] **Step 13 — Comando local de punta a punta.** `local_run.py` ejecuta el servicio completo en local (con `APP_ENV=local` y el verificador simulado habilitado de forma explícita) contra el modelo real de Amazon Bedrock con un título de ejemplo y comprueba que el Markdown devuelto empieza con "Como analista de negocio". Es la comprobación de punta a punta de `functional-spec.md`; requiere credenciales de AWS válidas en la máquina de quien lo ejecuta y no corre en la suite automática. Cubre NFR1.3 (medición manual del tiempo total, impresa por el comando).

### Comportamiento de la interfaz — `web/`

- [x] **Step 14 — Rojo.** Pruebas con Vitest y Testing Library, con la llamada de red simulada: se escribe un título, se pulsa "Generar historia" y se ve el Markdown tal cual (W1); título vacío muestra el mensaje que pide escribir un título (W2); un error del servicio muestra su mensaje como texto simple y sin "Reintentar" (W3, W4); el botón se desactiva mientras espera y la espera es de hasta 60 s. Elementos interactivos con `data-testid`. Ejecutar y guardar la salida en rojo.
- [x] **Step 15 — Verde.** Implementar la pantalla mínima en React con TypeScript y MUI (`App.tsx`, `api.ts`, `main.tsx`), con la dirección de la API por variable de entorno de Vite y el texto devuelto mostrado como texto simple (sin interpretar HTML).
- [x] **Step 16 — Refactor.** Pruebas en verde; Prettier y ESLint sin errores.

### Infraestructura y entrega

- [x] **Step 17 — Terraform mínimo.** Escribir en `infra/` la versión mínima de `infrastructure-specification.md`: pasarela REST con límite de uso (ráfaga 5, tasa sostenida 1 por segundo) y respuesta 429 personalizada con la forma de C1, integración de 58 s, función Lambda de 57 s con concurrencia reservada de 5 (sujeta a la cuota de la cuenta), rol de ejecución con permiso mínimo al modelo configurado, `APP_ENV` en `prod` sin `ALLOW_SIMULATED_SESSION`, grupo de registros de 14 días, depósito privado de S3 con versionado y control de acceso al origen, distribución de CloudFront y CORS limitado a esa distribución; el registro de invocaciones del modelo queda desactivado y se declara explícitamente. Las verificaciones son `terraform fmt -check` y `terraform validate`; **nunca se aplica ni se despliega desde esta etapa**. Cubre NFR1.1, NFR1.2, NFR3.1, NFR3.2 (parcial, ver `nfr-design`), NFR4.2, NFR5.1, NFR5.2. Si Terraform no está instalado, el paso se escribe y queda sin validar, anotado en `code-summary.md`.
- [x] **Step 18 — Flujo de CI de GitHub Actions.** Escribir `.github/workflows/ci.yml` con las etapas 1 a 4 de `cicd-pipeline.md`: Black y Ruff, Prettier y ESLint, pruebas con cobertura mínima de 80 %, `terraform fmt`, `validate` y `plan`, y las pruebas automáticas de seguridad del diseño (verificador simulado, registros, plan sin `ALLOW_SIMULATED_SESSION`). El despliegue y la prueba de humo (etapas 5 y 6) quedan como flujo aparte que solo corre en `main` y que depende del paso manual de crear el estado remoto de Terraform (`u6-infrastructure`); no se ejecuta aquí.

### Cierre

- [x] **Step 19 — Configuración de entorno y documentación.** Variables de entorno documentadas (`APP_ENV`, `ALLOW_SIMULATED_SESSION`, modelo y región, origen CORS, dirección de la API), `backend/.env.example` sin valores reales, comentarios en línea donde el diseño lo pide. No se modifica el `README.md` de la raíz; las notas de uso van en `code-summary.md`.
- [ ] **Step 20 — Trazabilidad y resumen.** Escribir `code-summary.md`, `source-manifest.json` y `traceability.json` (cada identificador asignado apunta a un archivo de código o de prueba existente).

## Trazabilidad de requisitos a pasos

| Requisito | Pasos |
|-----------|-------|
| AC2.1.1, AC2.1.2 (historia con acción y beneficio relacionados con el título) | 7, 8, 13 |
| AC2.1.3 (parte: petición de 2 a 3 criterios en español) | 7, 8 |
| AC2.1.4 (título como dato; defensa completa en `u3-story-generator`) | 4, 7, 8 |
| BR1.1, BR1.3, BR1.4 | 4, 7, 8 |
| BR1.2 (se revisa a mano) | 13 |
| BR1.5 | 7, 8, 17 |
| BR1.6 | 7, 8 |
| NFR1.1, NFR1.2, NFR1.5, NFR1.6 | 7, 8, 11, 17 |
| NFR1.3 | 13 |
| NFR1.4, NFR3.3 | 8 |
| NFR3.1, NFR3.2 | 8, 17 |
| NFR4.1 | 1, 8, 17 |
| NFR4.2, NFR4.3 | 7, 8, 17, 18 |
| NFR4.4 | 4, 7, 8 |
| NFR5.1 | 12, 17 |
| NFR5.2 | 7, 8, 17 |
| FR1.3 (parte de la pantalla) | 14, 15 |

## Pruebas (estrategia Standard, piso de 80 %)

| Componente | Pruebas previstas | Tipo |
|------------|-------------------|------|
| Entidades y errores | 6 a 8 | Unitarias |
| Servicio (lógica de negocio) | 8 a 12 | Unitarias con modelo simulado |
| Composición y seguridad | 5 a 6 | Unitarias |
| Registros | 3 a 4 | Unitarias |
| Manejador de la función | 6 a 8 | De integración del límite de la API |
| Cliente de Bedrock | 5 a 6 | De integración con doble de prueba |
| Pantalla de React | 6 a 8 | Unitarias de comportamiento |
| Infraestructura | validaciones estáticas de Terraform | Estáticas |

Los casos incluyen el camino feliz y al menos dos casos de error o límite por componente (`construction.md`, Testing Standards).

## Testing Contract

```json
{
  "version": 1,
  "methodology": "tdd",
  "source": "team",
  "ordering": "Escribir cada prueba antes del código que la satisface, ejecutarla en rojo y luego implementar lo mínimo para que pase.",
  "scope": "mvp",
  "test_strategy": "standard",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop`, `classic` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: tdd\n- **Methodology evidence**: La persona afirmó TDD en la entrevista (Q5): cada prueba se escribe antes del código. El repositorio no tiene pruebas hoy (`code-quality-assessment.md`: presencia de pruebas `poor`), así que no hay práctica previa que contradiga la elección.\n- **Ordering**: Escribir cada prueba antes del código que la satisface, ejecutarla en rojo y luego implementar lo mínimo para que pase.\n- **Cobertura y ejecución**: mínimo 80 % de cobertura de líneas, y las pruebas se ejecutan en CI antes de integrar.\n- **Herramientas de prueba**: no afirmadas (pytest y la herramienta estándar de React/TypeScript siguen como sugerencia, a decidir en el diseño). Pendiente.\n- **Pruebas existentes**: ninguna que deba mantenerse verde; `generador_historias.py` no tiene pruebas."
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Meet an 80% line-coverage floor.",
      "Run the selected tests in CI before merge."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "tdd",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Data model / database behavior - Red: write the failing tests and record the failing command output.",
      "Data model / database behavior - Green: implement only enough behavior to pass.",
      "Data model / database behavior - Refactor: improve the implementation while tests stay green.",
      "Repository / data access - Red: write the failing tests and record the failing command output.",
      "Repository / data access - Green: implement only enough behavior to pass.",
      "Repository / data access - Refactor: improve the implementation while tests stay green.",
      "Business logic - Red: write the failing tests and record the failing command output.",
      "Business logic - Green: implement only enough behavior to pass.",
      "Business logic - Refactor: improve the implementation while tests stay green.",
      "API / endpoint - Red: write the failing tests and record the failing command output.",
      "API / endpoint - Green: implement only enough behavior to pass.",
      "API / endpoint - Refactor: improve the implementation while tests stay green.",
      "Frontend behavior - Red: write the failing tests and record the failing command output.",
      "Frontend behavior - Green: implement only enough behavior to pass.",
      "Frontend behavior - Refactor: improve the implementation while tests stay green.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:ff7a48f7affb83e71fc0a5d891c2db54072c13f8ebc97ba727b40f29bcc7b711",
  "contract_sha256": "sha256:30e89bb88362bb70e02b1cff522b13b8db1ad3cdbd3ad1a38c63ba692fd1157a"
}
```
