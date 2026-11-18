# Code Generation Plan — u6-infrastructure

## Summary

- Builds: la infraestructura completa en Terraform y su canalización: la raíz de arranque manual (`infra/bootstrap/`: depósito de estado, proveedor OIDC, límite de permisos y roles de plan y de aplicación), la ampliación de la raíz de la aplicación (`infra/`: Cognito con Google y Microsoft, `/v1/session` y CORS, respuestas de error de la pasarela, política de cabeceras de la pantalla, variables de entorno de la función, rol de ejecución escrito con `jsonencode`), las comprobaciones (`terraform test`, `check_plan.py`, fijado de acciones y patrones de secretos), los flujos `ci.yml` y `deploy.yml`, la prueba de humo y la lista de verificación del arranque.
- Touches: `infra/` (archivos nuevos y cambios en `main.tf`, `variables.tf`, `outputs.tf` y `versions.tf`), `infra/bootstrap/`, `infra/tests/`, `infra/scripts/`, `.github/workflows/` (`ci.yml` y `deploy.yml` nuevo) y `infra/README.md`; no se tocan `backend/` ni `web/` ni los archivos de la raíz del proyecto.
- Tests: unas 60 afirmaciones de `terraform test` (proveedor simulado) y unas 25 pruebas de Python para los scripts, escritas antes del código (TDD). El piso de 80 % de cobertura de líneas aplica a los scripts de Python; el código de Terraform se cubre con las afirmaciones del plan.

Idioma de los artefactos de esta etapa: español. Identificadores del código nuevo: inglés (`team.md`, Code Style).

## Entradas

`security-design.md`, `infrastructure-specification.md`, `monitoring-design.md` y `cicd-pipeline.md` de u6; `security-requirements.md` y `tech-stack-decisions.md` (NFR1.1 a NFR8.2); `contract-summary.md` (C1, C2 y los requisitos de alojamiento); `unit-of-work.md` y `requirements.md`. El código de `infra/` de u1 y el `ci.yml` de u1 y u5 se modifican en su sitio.

## Decisiones de construcción

- **Proyecto existente (brownfield):** el servicio (558 pruebas) y la pantalla (186 pruebas) siguen en verde; no se modifican. Los cambios en `infra/main.tf` solo agregan o ajustan lo que las especificaciones piden.
- **Nunca se aplica nada:** `terraform apply`, `terraform plan` contra AWS, el arranque y cualquier llamada a AWS no se ejecutan en esta etapa. Solo `terraform init -backend=false`, `fmt`, `validate` y `terraform test` con proveedor simulado.
- **Acciones de GitHub fijadas por hash:** los hashes de commit de 40 caracteres se resuelven de forma real con la API pública de GitHub (`gh api`, solo lectura); si no se pueden resolver, se detiene y se informa, sin inventar ni dejar etiquetas.
- **Checkov:** se ejecuta solo en CI (no se instala localmente en esta etapa); sus omisiones se documentan una a una en la configuración.
- **Sin secretos:** ningún valor real; las variables sensibles no tienen valores por defecto con datos reales.
- **Verificación de la unidad:** los comandos de `unit-test-instructions.md`; el comando aprobado del proyecto (`cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"`) se vuelve a ejecutar al cerrar.

## Pasos

### Preparación

- [ ] **Step 1 — Estructura y configuración.** Subir `required_version` a 1.11 o más y acotar el proveedor `aws`; crear `infra/.gitignore` (`*.tfvars`, estado local del arranque), `infra/tests/`, `infra/scripts/` y `infra/bootstrap/`; backend `s3` con configuración parcial (`use_lockfile = true`; el depósito llega por `-backend-config`).
- [ ] **Step 2 — Verificar el ejecutor de pruebas y registrar el comando por unidad.** Comprobar que `cd infra && terraform init -backend=false && terraform test` corre (con una primera afirmación mínima) y que `cd infra/scripts && python -m pytest` corre; registrar los comandos de u6 en `unit-test-instructions.md` antes de la primera prueba en rojo.

### Modelo de datos (variables, validaciones y datos)

Entidades: las variables de Terraform (`allowed_emails`, `google_*` y `microsoft_*`, `cognito_domain_prefix`, `github_repository`, `state_bucket_name`, las existentes) y sus validaciones. Sin base de datos.

- [ ] **Step 3 — Rojo.** Afirmaciones: `allowed_emails` acepta 1 y 50 correos y rechaza 51, mayúsculas, formato inválido y vacío; todas las variables de secretos y de correos son `sensitive`; `cognito_domain_prefix` y `github_repository` validan su formato; `bedrock_model_id` mantiene su validación. Ejecutar y guardar la salida en rojo.
- [ ] **Step 4 — Verde.** Implementar las variables en `infra/variables.tf` y `infra/bootstrap/variables.tf`.
- [ ] **Step 5 — Refactor.** Mejorar con las pruebas en verde.

### Acceso a datos

Este nivel no aplica: la unidad no crea almacenes de datos de las personas (NFR4.1); la comprobación de ausencia está en el paso 8.

### Lógica de negocio — `check_plan.py`, `check_pins.py`, `check_secrets.py`

- [ ] **Step 6 — Rojo.** Pruebas de Python con planes de ejemplo (`terraform show -json` reducido): `check_plan.py` acepta un plan limpio, rechaza un tipo de recurso no permitido, un depósito o una tabla adicional, la eliminación o el reemplazo de un tipo protegido, una variable de secretos sin `sensitive`, y las fuentes de datos `external` y los aprovisionadores `local-exec` y `remote-exec`; no se confunde con valores ficticios; `check_pins.py` rechaza un `uses:` sin hash de 40 caracteres y acepta el que tiene hash con versión comentada; `check_secrets.py` detecta `AKIA`, `ASIA`, `client_secret = "`, claves privadas y no marca `sensitive` ni variables. Ejecutar y guardar la salida en rojo.
- [ ] **Step 7 — Verde.** Implementar los tres scripts en `infra/scripts/`.
- [ ] **Step 8 — Refactor.** Simplificar con las pruebas en verde; la lista de tipos permitidos y protegidos vive en un solo lugar.

### API / punto de entrada — pasarela y CORS

- [ ] **Step 9 — Rojo.** Afirmaciones sobre el plan: recurso `/v1/session` con `GET` y `DELETE` hacia la misma integración; preflight (OPTIONS) en `/v1/stories` y `/v1/session` con `GET,POST,DELETE,OPTIONS` y `Authorization,Content-Type` y el origen exacto de la distribución; respuestas de pasarela `THROTTLED`, `DEFAULT_4XX` y `DEFAULT_5XX` con la cabecera de origen; integración de 58 000 ms, función de 57 s y concurrencia reservada de 5; límite de 1 solicitud por segundo y ráfaga de 5; el `triggers` del despliegue incluye los recursos nuevos. Ejecutar y guardar la salida en rojo.
- [ ] **Step 10 — Verde.** Implementar `api_session.tf` y ajustar `main.tf`.
- [ ] **Step 11 — Refactor.** Pruebas en verde.

### Infraestructura — arranque, Cognito, pantalla e IAM

- [ ] **Step 12 — Rojo (arranque).** Afirmaciones sobre `infra/bootstrap/` con proveedor simulado, políticas con `jsonencode` y datos de cuenta con `override_data`: depósito de estado privado, versionado, cifrado y con política de TLS; permisos del estado (objeto y `.tflock`; `s3:ListBucket` con `StringLikeIfExists` y la lista de prefijos; nada más sobre el depósito); proveedor OIDC con `aud`; confianza del rol de plan con el `sub` de `pull_request` y la del rol de aplicación con el `sub` de `main`, sin comodines; permisos de lectura enumerados del rol de plan; rol de aplicación con límite, creación de roles solo con el límite, acciones de política y `PassRole` acotadas por prefijo y denegaciones explícitas sobre los recursos del arranque. Ejecutar y guardar la salida en rojo.
- [ ] **Step 13 — Verde (arranque).** Implementar `infra/bootstrap/`.
- [ ] **Step 14 — Rojo (aplicación).** Afirmaciones: Cognito (sin registro propio, protección contra eliminación, cliente público sin secreto, solo flujo de código, vigencias de 8 horas, retorno y cierre con la distribución, revocación activada, proveedores `Google` y `Microsoft` con el mapeo de `email` y `email_verified`, dominio con el prefijo); política de cabeceras con la política de contenido exacta y las demás cabeceras, caché por tipo de archivo y depósito privado; rol de la función con `bedrock:InvokeModel` sobre el perfil y el modelo base y nada de IAM, Cognito ni S3; variables de entorno de la función (`CORS_ALLOWED_ORIGIN`, `COGNITO_*`, `ALLOWED_EMAILS`, sin `ALLOW_SIMULATED_SESSION`); retención de 14 días, sin registro de invocaciones ni de acceso; salidas de Cognito; ningún recurso de datos fuera de los dos depósitos. Ejecutar y guardar la salida en rojo.
- [ ] **Step 15 — Verde (aplicación).** Implementar `cognito.tf`, `web_headers.tf`, `iam.tf` y los cambios de `main.tf` y `outputs.tf`.
- [ ] **Step 16 — Refactor.** Pruebas en verde; `terraform fmt` y `terraform validate` limpios.

### Comportamiento de la interfaz

Este nivel no aplica: u6 no tiene interfaz.

### Canalización y entrega

- [ ] **Step 17 — Flujos y prueba de humo.** Con pruebas primero donde se pueda (los scripts de los pasos 6 a 8): actualizar `ci.yml` (Terraform 1.11 o más, `fmt`, `validate`, `terraform test`, `check_plan.py`, `check_pins.py`, `check_secrets.py`, Checkov, `plan` solo del propio repositorio con valores ficticios y guarda `AWS_PLAN_ROLE_ARN`), crear `deploy.yml` (guarda `AWS_APPLY_ROLE_ARN`, concurrencia, `init` con `-backend-config`, `plan -out`, `check_plan.py`, `apply` del mismo plan, publicación de la pantalla sin `--delete`, invalidación, prueba de humo y reversión del alias), escribir `infra/scripts/smoke_test.sh`, fijar todas las acciones por hash con la API de GitHub y escribir `infra/README.md` con la lista de verificación del arranque.

### Cierre

- [ ] **Step 18 — Verificación completa.** Ejecutar: `terraform fmt -check -recursive`, `terraform validate` y `terraform test` en `infra/` y en `infra/bootstrap/`; `python -m pytest` de los scripts con el piso de 80 %; Black y Ruff sobre `infra/scripts/`; `check_pins.py` sobre los flujos; y las suites del servicio y de la pantalla sin cambios. No se ejecuta `plan` ni `apply`.
- [ ] **Step 19 — Trazabilidad y resumen.** Escribir `code-summary.md`, `source-manifest.json` y `traceability.json` (cada identificador asignado apunta a un archivo de código o de prueba existente).

### Reparación (regreso desde Build and Test)

Build and Test encontró que la función Lambda se empaqueta sin `PyJWT[crypto]` ni `cryptography` (`data.archive_file` solo comprime `backend/` y excluye `requirements*.txt`), así que todo despliegue fallaría al importar `jwt` al arrancar. Los pasos 1 a 18 ya construidos no se rehacen; estos pasos agregan la reparación (hallazgo X7 de `build-and-test/test-results.md`, `## Loop-Back Log`, entrada 1). La reparación del plazo total de la descarga de claves es de `u4-access-control`.

- [x] **Step 20 — Rojo (empaquetado).** Pruebas de Python en `infra/scripts/` con un ejecutor de `pip` simulado: el script de empaquetado construye una carpeta con el código de `backend/story_service` y las dependencias de `backend/requirements.txt` instaladas para Lambda (`python3.12`, `manylinux2014_x86_64`, solo ruedas binarias, `--target`), excluye pruebas y cachés, falla si una dependencia no se instala o si el resultado no contiene `jwt` y `cryptography` y es determinista (mismo contenido, mismo resultado); y una afirmación de `terraform test` de que `data.archive_file.story_service` comprime la carpeta de empaquetado y no `backend/` a secas. Ejecutar y guardar la salida en rojo.
- [x] **Step 21 — Verde.** Implementar `infra/scripts/build_lambda_package.py` y cambiar `infra/main.tf` para que el archivo comprimido salga de la carpeta de empaquetado; `ci.yml` (trabajos `infra` e `infra-plan`) y `deploy.yml` ejecutan el script antes de `terraform validate`, `terraform test`, `plan` y `apply`; actualizar `infra/README.md` y `.gitignore` de `infra/` (carpeta de empaquetado ignorada).
- [x] **Step 22 — Verificación real del paquete.** Ejecutar el script una vez de verdad (acceso a PyPI, sin credenciales de AWS) y comprobar con una prueba que el archivo comprimido contiene `story_service/handler.py`, `jwt/__init__.py` y una rueda de `cryptography` para Linux (`.so` de `manylinux`), y que pesa menos de 50 MB (límite de Lambda); `terraform fmt -check`, `validate`, `terraform test` en las dos raíces, pytest de los scripts con el piso de 80 % y `check_pins.py`/`check_secrets.py` limpios. Sin `plan` ni `apply`.
- [ ] **Step 23 — Resumen.** Actualizar `code-summary.md` y `traceability.json` con la reparación (X7) y las verificaciones del paso 22.

## Trazabilidad de requisitos a pasos

| Requisito | Pasos |
|-----------|-------|
| NFR5.1 | 3, 4, 6, 7, 14, 15 |
| NFR5.2, NFR5.3 | 12, 13, 17 |
| NFR5.4 | 12, 13 |
| NFR5.5 | 14, 15 |
| NFR5.6 | 12, 13 |
| NFR5.7 | 6, 7, 17 |
| NFR5.8 | 14, 15 |
| NFR5.9 | 9, 10, 14, 15 |
| NFR4.1, NFR4.2 | 6, 7, 14, 15 |
| NFR4.3 | 3, 4 |
| NFR3.1, NFR1.1 | 9, 10 |
| NFR8.1, NFR8.2 | todos los pasos de Rojo, Verde y Refactor, y 17 |

## Pruebas (estrategia Standard, piso de 80 %)

| Componente | Pruebas previstas | Tipo |
|------------|-------------------|------|
| Variables y validaciones | 8 a 10 | `terraform test` |
| `check_plan.py` | 10 a 12 | Python con planes de ejemplo |
| `check_pins.py` y `check_secrets.py` | 8 a 10 | Python |
| Pasarela y CORS | 10 a 12 | `terraform test` |
| Arranque (estado, OIDC, roles, límite) | 16 a 20 | `terraform test` |
| Cognito, pantalla e IAM de la función | 18 a 22 | `terraform test` |

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
