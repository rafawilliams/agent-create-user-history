# Code Generation Plan — u2-model-gateway

## Summary

- Builds: el acceso completo al modelo (ModelGateway): perfil de modelo validado por configuración (Claude Sonnet o Amazon Titan), traducción de errores con motivo de lista cerrada, y el comando de evaluación de modelos con su archivo de títulos aprobado y su registro en Markdown.
- Touches: `backend/story_service/` (archivos nuevos `error_translation.py`, `model_profile.py`, `evaluation.py`, `evaluate_models.py`; cambios en `models.py`, `bedrock_client.py`, `config.py`, `ports.py`), sus pruebas en `backend/tests/`, la validación de la variable de Terraform en `infra/variables.tf`, y los documentos `docs/titulos-evaluacion.md` y `docs/evaluacion-modelos.md`; el script y los archivos existentes de la raíz no se modifican.
- Tests: unas 45 pruebas nuevas (unitarias por componente más pruebas de integración con el cliente de AWS simulado), escritas antes del código (TDD), con piso de 80 % de cobertura de líneas sobre la suite completa.

Idioma de los artefactos de esta etapa: español. Identificadores del código nuevo: inglés (`team.md`, Code Style).

## Entradas

`functional-spec.md`, `rules.md` (BR2.1 a BR2.10), `entities.md`, `contract-summary.md` (C4), `security-design.md`, `logical-components.md`, `cicd-pipeline.md` de u2, `tech-stack-decisions.md` y `security-requirements.md` de u2, `unit-of-work.md` y `requirements.md`. El código de u1 (`backend/story_service/`) ya existe y se modifica en su sitio, sin crear duplicados.

## Decisiones de construcción

- **Proyecto existente (brownfield):** se modifican `models.py`, `bedrock_client.py`, `config.py` y `ports.py` en su sitio. Los archivos de la raíz del proyecto (`generador_historias.py`, `README.md`, `requirements.txt`, `.env`, etc.) no se tocan.
- **Compatibilidad con u1:** `ModelError` gana el campo opcional `reason`; el servicio de u1 sigue funcionando sin cambios porque lo ignora. `timeout_seconds` ya es decimal en el código; el cambio es solo de contrato.
- **Titan por la API de conversación:** el identificador exacto de Amazon Titan se fija al ver los perfiles de la cuenta (lista de perfiles con `bedrock list-inference-profiles`, solo lectura); si ninguno sirve, queda como pendiente de acceso en el registro, sin descartarlo.
- **Evaluación contra AWS:** el comando real llama a Bedrock con la cuenta de la persona y no corre en CI ni en esta etapa. Esta etapa deja el comando probado con modelos simulados y el archivo de títulos propuesto, sin aprobar: **la persona aprueba los 5 títulos** (decisión FD Q2) con el subcomando `approve` antes de la primera ejecución real.
- **Sin persistencia:** ningún paso crea tablas ni almacenes de datos.

## Pasos

### Preparación

- [x] **Step 1 — Cambio de contrato C4.** Registrar en `contract-summary.md`, como cambios aditivos, que `timeoutSeconds` es un número y que `ModelError` gana el campo opcional `reason` con la lista cerrada (`access_not_enabled`, `model_not_found`, `invalid_request`, `timeout`, `throttled`, `unavailable`, `unknown`), y cerrar la pregunta abierta de C4 sobre el tiempo de espera por modelo con 50 segundos para ambos modelos. Sin código.
- [x] **Step 2 — Verificar el ejecutor de pruebas y registrar el comando por unidad.** Comprobar que `cd backend && python -m pytest tests -q` corre con las pruebas de u1 en verde, y registrar el comando de u2 (solo los archivos de prueba de u2) en `unit-test-instructions.md`, antes de la primera prueba en rojo.

### Modelo de datos (comportamiento de las entidades) — `models.py`, `model_profile.py`

Entidades nombradas, con origen en `entities.md`: `ModelError` (`kind`, `message`, y el campo opcional nuevo `reason`), `ModelErrorReason` (lista cerrada de siete valores) y `ModelProfile` (`modelId`, `provider`, `region`), más `EvaluationResult` (`modelId`, `title`, `outcome`, `text`, `formatOk`, `elapsedSeconds`, `reason`) y `EvaluationRecord` (`evaluatedAt`, `titles`, `results`, `decision`, `pendingAccess`) con las restricciones de `entities.md`. Sin base de datos ni migraciones.

- [x] **Step 3 — Rojo.** Pruebas de entidades: `ModelError` con y sin `reason`, y rechaza un motivo fuera de la lista; `ModelProfile` acepta `(us.|global.)?anthropic.claude-*` y `(us.)?amazon.titan-*` y rechaza otro proveedor, un error de escritura dentro de un proveedor válido y un valor vacío (BR2.2, NFR5.3), deduciendo el proveedor; `EvaluationResult` exige `text` y `formatOk` solo con `generated` y `reason` solo con `blocked` o `failed`. Ejecutar y guardar la salida en rojo.
- [x] **Step 4 — Verde.** Implementar lo mínimo en `models.py` y `model_profile.py`.
- [x] **Step 5 — Refactor.** Mejorar con las pruebas en verde.

### Acceso a datos

Este nivel no aplica: el servicio no guarda nada (NFR4.1). El único archivo que se escribe es el registro de evaluación (ver lógica de negocio).

### Lógica de negocio — `error_translation.py`, `config.py`, `evaluation.py`

- [x] **Step 6 — Rojo.** Pruebas:
  - Traducción de errores (BR2.3, BR2.4): cada código de AWS de la tabla de `security-design.md` produce el `kind` y el `reason` correctos; un código desconocido da `unavailable` y `unknown`; errores sin código (lectura o conexión agotada, error de red) dan `timeout` o `unavailable`; el mensaje es el propio del tipo; con un error de AWS cuyo texto lleva un ARN y un identificador de cuenta, ni el mensaje, ni el motivo, ni la causa de la excepción, ni ningún registro (incluidos los de `boto3` y `botocore`) contienen esos datos, y la excepción original no queda encadenada (NFR4.2).
  - Configuración (BR2.1, BR2.2, NFR1.2): `Settings` toma el modelo, la región y los tiempos de espera de las variables de entorno; sin configuración usa el modelo por defecto y 50 s; un identificador no soportado hace fallar al armar la configuración, sin llamar a AWS, y el error nombra el valor.
  - Evaluación (BR2.8 a BR2.10): un resultado por modelo y título; `formatOk` solo si el texto empieza con "Como analista de negocio" y trae de 2 a 3 escenarios con Dado, Cuando y Entonces; `blocked` para `access_not_enabled` y `model_not_found`, `failed` para `invalid_request` y para fallos de tipo transient, timeout y unavailable; decisión: pendiente con algún modelo bloqueado o todos, mayor puntuación gana, empate (incluido cero en todos) conserva el modelo por defecto con la nota de afinar instrucciones; un modelo bloqueado no detiene a los demás.
  - Archivo de títulos (BR2.9, NFR4.3): exige exactamente 5 títulos y la línea `aprobado: <huella SHA-256 de los títulos>`; cambiar un título invalida la aprobación; el subcomando `approve` escribe la huella; el registro `docs/evaluacion-modelos.md` incluye títulos, resultado por modelo y título con tiempo y motivo, puntuación y decisión, y no incluye texto de AWS.
  - Ejecutar y guardar la salida en rojo.
- [x] **Step 7 — Verde.** Implementar `error_translation.py` (tabla fija, devuelve un `ModelError` nuevo sin encadenar la excepción), el selector en `config.py` con la validación al inicializar, y `evaluation.py` (puntuación, decisión, archivo de títulos con huella y registro en Markdown). El reloj de la evaluación es inyectable para probar el tiempo por llamada (NFR1.3).
- [x] **Step 8 — Refactor.** Simplificar con las pruebas en verde; todo sin estado entre llamadas (NFR4.1).

### API / punto de entrada — `bedrock_client.py`, `ports.py`, `evaluate_models.py`

- [x] **Step 9 — Rojo.** Pruebas con un doble del cliente de AWS (nunca se llama a AWS):
  - Cliente de Bedrock: el cliente de AWS se crea con cero reintentos propios, tiempo de conexión de 5 s y de lectura de 50 s (NFR1.2, NFR1.4); ante un fallo pasajero hace una sola llamada; con un tiempo pedido de 2 s devuelve el control en 3 s o menos (NFR1.1), también con valores con fracciones; devuelve el texto tal cual, vacío o sin estructura (BR2.5); registra solo identificador del modelo, resultado, motivo y duración (NFR4.2); los registradores de `boto3` y `botocore` quedan en advertencia o superior.
  - Comando de evaluación: `approve` escribe la huella; `run` se niega sin 5 títulos aprobados (NFR4.3); con modelos simulados produce el registro con un resultado por modelo y título, el tiempo por llamada (NFR1.3) y la puntuación (NFR2.1); un modelo bloqueado se registra y el comando sigue; el único archivo que escribe es `docs/evaluacion-modelos.md` (NFR4.1).
  - Ejecutar y guardar la salida en rojo.
- [x] **Step 10 — Verde.** Integrar el traductor y los cuatro campos de registro en `bedrock_client.py`, ajustar `ports.py` (el tiempo en segundos como número y la referencia al motivo), y escribir `evaluate_models.py` con los subcomandos `approve` y `run`.
- [x] **Step 11 — Refactor.** Pruebas en verde; sin credenciales en el código (NFR5.1): solo la cadena de credenciales estándar de AWS.
- [x] **Step 12 — Archivo de títulos y comando de evaluación real.** Proponer los 5 títulos inventados en `docs/titulos-evaluacion.md`, sin la línea de aprobación (la persona aprueba con `python -m story_service.evaluate_models approve`), y documentar el comando de evaluación real contra Bedrock en `unit-test-instructions.md` como comando manual. No se ejecuta aquí: necesita la aprobación de la persona, el identificador de Amazon Titan de la cuenta y credenciales de AWS.

### Comportamiento de la interfaz

Este nivel no aplica: u2 no tiene interfaz.

### Infraestructura y entrega

- [x] **Step 13 — Validación de la variable de Terraform.** Agregar en `infra/variables.tf` una validación del patrón exacto de identificadores para la variable del modelo, de modo que un valor mal escrito se detenga en `terraform validate` y `plan` (NFR5.3), manteniendo una sola variable como fuente del permiso y de la configuración (NFR5.2). Verificar con `terraform fmt -check` y `terraform validate`; nunca se aplica ni se despliega desde esta etapa.

### Cierre

- [x] **Step 14 — Configuración y documentación.** Documentar en `backend/.env.example` las variables nuevas (modelo, región, tiempos de espera por modelo) sin valores reales; comentarios en línea donde el diseño lo pide. No se modifica el `README.md` de la raíz.
- [ ] **Step 15 — Trazabilidad y resumen.** Escribir `code-summary.md`, `source-manifest.json` y `traceability.json` (cada identificador asignado apunta a un archivo de código o de prueba existente).

## Trazabilidad de requisitos a pasos

| Requisito | Pasos |
|-----------|-------|
| AC7.1.1 (un resultado por modelo y título) | 6, 7, 9, 10 |
| AC7.1.2 (registro con resultado y decisión) | 6, 7, 9, 10, 12 |
| AC7.1.3 (modelo bloqueado se registra, no se descarta) | 6, 7, 9, 10 |
| AC5.1.2 (tipo de error fija la indicación de reintento) | 3, 4, 6, 7 |
| AC5.1.4 (tiempo de espera respetado) | 9, 10 |
| BR2.1, BR2.2 | 3, 4, 6, 7, 13 |
| BR2.3, BR2.4 | 6, 7, 9, 10 |
| BR2.5 | 9, 10 |
| BR2.6 | 1, 9, 10 |
| BR2.7 | 3, 4 |
| BR2.8, BR2.9, BR2.10 | 6, 7, 9, 10, 12 |
| NFR1.1, NFR1.4 | 9, 10 |
| NFR1.2 | 6, 7, 9, 10 |
| NFR1.3, NFR2.1 | 6, 7, 9, 10 |
| NFR4.1 | 6, 9, 10 |
| NFR4.2 | 6, 7, 9, 10 |
| NFR4.3 | 6, 7, 9, 10, 12 |
| NFR5.1 | 11 |
| NFR5.2, NFR5.3 | 3, 6, 7, 13 |
| NFR8.1 a NFR8.4 | todos los pasos de Rojo, Verde y Refactor |

## Pruebas (estrategia Standard, piso de 80 %)

| Componente | Pruebas previstas | Tipo |
|------------|-------------------|------|
| Entidades (`ModelError`, `ModelProfile`, evaluación) | 6 a 8 | Unitarias |
| Traducción de errores | 8 a 10 | Unitarias |
| Selector de configuración | 5 a 6 | Unitarias |
| Evaluación (puntuación y decisión) | 8 a 10 | Unitarias |
| Archivo de títulos y registro | 5 a 6 | Unitarias |
| Cliente de Bedrock | 6 a 8 | De integración con doble de prueba |
| Comando de evaluación | 5 a 6 | De integración con modelos simulados |
| Terraform | validaciones estáticas | Estáticas |

Los casos incluyen el camino feliz y al menos dos casos de error o límite por componente.

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
