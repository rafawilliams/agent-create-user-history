# Code Generation Plan — u4-access-control

## Summary

- Builds: el control de acceso del servicio: verificación real de la sesión con tokens de Amazon Cognito (algoritmo RS256, claves públicas con copia en memoria, lista de correos permitidos), las rutas `GET` y `DELETE /v1/session` (contrato C2) y los cambios coordinados de C1, C3 y de las listas cerradas de registro.
- Touches: `backend/story_service/` (archivos nuevos `auth_config.py`, `jwks_store.py`, `token_verifier.py`, `account_allowlist.py`; cambios en `models.py`, `errors.py`, `config.py`, `service.py`, `logging_utils.py`, `handler.py` y `ports.py`), sus pruebas en `backend/tests/`, `backend/requirements.txt` y `backend/.env.example`, y los cambios de contrato en `contract-summary.md`; el script y los archivos existentes de la raíz no se modifican. La infraestructura de Cognito la escribe `u6-infrastructure`.
- Tests: unas 70 pruebas nuevas (unitarias por componente más pruebas de integración con claves y tokens de prueba), escritas antes del código (TDD), con piso de 80 % de cobertura de líneas sobre la suite completa.

Idioma de los artefactos de esta etapa: español. Identificadores del código nuevo: inglés (`team.md`, Code Style).

## Entradas

`functional-spec.md`, `rules.md` (BR4.1 a BR4.8), `entities.md`, `contract-summary.md` (C1, C2, C3), `security-design.md`, `performance-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `infrastructure-specification.md` y `cicd-pipeline.md` de u4, `unit-of-work.md` y `requirements.md`. El código de u1, u2 y u3 ya existe y se modifica en su sitio, sin crear duplicados.

## Decisiones de construcción

- **Proyecto existente (brownfield):** las 358 pruebas existentes deben seguir en verde (salvo las que contradigan una regla nueva de u4, que se cambian con la razón registrada).
- **Cambio coordinado primero:** registrar en `contract-summary.md` el código `ACCOUNT_NOT_ALLOWED` (403) en C1 y C2, las rutas de C2 con ese caso y los motivos de `SessionInvalid` en C3 (incluido `unknown`); agregar a las listas cerradas de u1 el código, los campos de registro `authOutcome` y `authDurationMs` y el motivo `unknown`, y volver a ejecutar las pruebas de u1, u2 y u3 antes de seguir.
- **Biblioteca de tokens (propuesta, a confirmar con este plan):** una biblioteca de JWT mantenida para Python con soporte de RS256 y claves JWK (por ejemplo PyJWT con `cryptography`), con la versión fijada en `backend/requirements.txt`. El algoritmo se fija en RS256 y la clave se pasa por separado: la verificación no deja que el encabezado elija el método. Si se prefiere no agregar dependencias de criptografía, hay que decirlo al aprobar el plan.
- **Descarga de claves:** con la biblioteca estándar de Python, sin dependencias nuevas; la dirección se construye solo con la región y el identificador del grupo.
- **Sin llamadas a Cognito ni a AWS en pruebas:** los tokens se firman con un par de claves RSA generado en las pruebas y el servidor de claves se simula.
- **Sin infraestructura en esta unidad:** el grupo de usuarios, las federaciones, el CORS de la pasarela y los criterios verificables del plan de Terraform los crea y comprueba `u6-infrastructure`.
- **Verificación de la unidad:** el comando aprobado sigue corriendo con el verificador simulado local (`--local`); la verificación real contra Cognito no es posible hasta que exista el grupo de usuarios (`u6-infrastructure`) y las credenciales de Google y Microsoft de la persona.

## Pasos

### Preparación

- [ ] **Step 1 — Cambios de contrato y de las listas cerradas de u1.** Registrar en `contract-summary.md` los cambios aditivos de C1, C2 y C3 de `rules.md` y de `observability-design.md`, y agregar el código, los campos de registro y el motivo a las listas de u1 en el código; volver a ejecutar la suite completa (debe seguir en verde).
- [ ] **Step 2 — Verificar el ejecutor de pruebas y registrar el comando por unidad.** Comprobar que `cd backend && python -m pytest tests -q` corre en verde y registrar el comando de u4 (solo sus archivos de prueba) en `unit-test-instructions.md`, antes de la primera prueba en rojo; agregar la biblioteca de JWT a `backend/requirements.txt` con la versión fijada y comprobar que se instala.

### Modelo de datos (comportamiento de las entidades) — `models.py`, `errors.py`, `auth_config.py`

Entidades nombradas, con origen en `entities.md`: `Session` (`sessionId`, `accountId`, `provider`, `expiresAt`), `SessionInvalid` (`reason` de lista cerrada de once valores), `AllowedAccount` (`email`) y `IdentityProviderConfig` (`region`, `userPoolId`, `appClientId`), y el código de error `ACCOUNT_NOT_ALLOWED`. Sin base de datos ni migraciones.

- [ ] **Step 3 — Rojo.** Pruebas: `SessionInvalid` solo acepta los motivos de la lista; `Session` con el proveedor `google` o `microsoft`; `IdentityProviderConfig` rechaza valores vacíos y deriva el emisor y la dirección de claves solo de la región y del grupo; `AllowedAccount` en minúsculas y sin espacios; la lista de más de 50 correos o con una entrada que no parece un correo se rechaza; `ACCOUNT_NOT_ALLOWED` tiene HTTP 403 y no es reintentable. Ejecutar y guardar la salida en rojo.
- [ ] **Step 4 — Verde.** Implementar lo mínimo en `models.py`, `errors.py` y `auth_config.py`.
- [ ] **Step 5 — Refactor.** Mejorar con las pruebas en verde.

### Acceso a datos

Este nivel no aplica: u4 no guarda nada (NFR4.1). La única memoria es la copia de claves públicas.

### Lógica de negocio — `jwks_store.py`, `token_verifier.py`, `account_allowlist.py`, `config.py`, `service.py`, `logging_utils.py`

- [ ] **Step 6 — Rojo.** Pruebas con claves y tokens de prueba:
  - Verificación (BR4.2, NFR5.1, NFR5.2): token válido; algoritmo "none" y simétrico; sin `kid`; `kid` desconocido; firma alterada; emisor, audiencia y `token_use` incorrectos; vencido; `iat` y `nbf` futuros con la tolerancia de 60 s; sin `exp`; sin fechas de inicio; más de 8 horas desde `auth_time` y la caída a `iat`; la regla única del `kid` (copia vigente con el `kid`, copia vencida, `kid` ausente tras descarga exitosa: `bad_signature`; descarga no posible: `keys_unavailable`).
  - Claves (BR4.7, NFR5.7, NFR1.2, NFR1.3, NFR3.2, NFR1.5): dirección derivada solo de la configuración (el `iss` y `jku` del token se ignoran); redirección a otro host rechazada; respuesta de más de 64 KB; conjunto mal formado o con otro algoritmo: `keys_unavailable` sin modificar la copia; una descarga a la vez y una por minuto contando los fallos, con el servidor caído y 100 tokens de `kid` desconocido; quien no toma el cerrojo falla cerrado de inmediato; copia de menos de 1 hora sirve con la descarga caída y de más de 1 hora no; reemplazo atómico de la copia y 20 verificaciones simultáneas.
  - Cuentas (BR4.3, NFR5.3, NFR5.6, NFR3.3): `email_verified` verdadero, falso, ausente y de otro tipo; correo ausente; otra capitalización; punto de Gmail y alias "+" que no coinciden; lista vacía; lista de 50 y de 51; quitar un correo entre dos solicitudes con el mismo token.
  - Servicio (BR4.5, NFR5.4, NFR1.6, NFR1.7, NFR4.4): sin configuración, rechaza toda solicitud con SESSION_INVALID y sin llamar al modelo; el verificador simulado solo con `APP_ENV` local o test y la bandera, y nunca con la configuración real; el mismo cuerpo y código 401 para todos los motivos de token; ACCOUNT_NOT_ALLOWED (403) distinto; un error interno falla cerrado con el motivo `unknown`; tokens válidos e inválidos intercalados.
  - Registros (BR4.8, NFR4.2, NFR4.5, NFR4.6, NFR4.7, NFR1.9): `authOutcome` y `authDurationMs` en el registro; ni el token, ni el correo, ni el `sub`, ni la lista; `errors_total` con el código; `keys_unavailable` y `not_configured` como motivos distintos.
  - Tiempo (NFR1.1, NFR1.4): la verificación con claves en memoria tarda menos de 20 ms (mediana de 20 repeticiones tras calentamiento, repetida hasta 3 veces antes de fallar; el máximo solo avisa) y no hace llamadas de red cuando la copia sirve.
  - Ejecutar y guardar la salida en rojo.
- [ ] **Step 7 — Verde.** Implementar `jwks_store.py` (descarga acotada, copia, cerrojo y límite por minuto), `token_verifier.py` (orden fijo de `security-design.md`), `account_allowlist.py`, la composición en `config.py` y la integración con `service.py` y `logging_utils.py`.
- [ ] **Step 8 — Refactor.** Simplificar con las pruebas en verde; sin estado entre solicitudes salvo la copia de claves (NFR3.1, NFR4.1).

### API / punto de entrada — `handler.py`, `ports.py`

- [ ] **Step 9 — Rojo.** Pruebas del manejador con un doble del servicio y de las claves (nunca AWS): `GET /v1/session` devuelve 200 con `sessionId`, `accountId`, `provider` y `expiresAt` y nunca el correo ni el token (NFR4.3); 401 sin sesión válida y 403 con una cuenta no permitida; `DELETE /v1/session` devuelve 204 con una sesión válida, 401 sin ella y 403 con una cuenta no permitida; el encabezado `Authorization: Bearer` se lee sin registrarse; `POST /v1/stories` con una cuenta no permitida devuelve 403 y no llama al modelo; las respuestas de error llevan CORS como las de u1. Ejecutar y guardar la salida en rojo.
- [ ] **Step 10 — Verde.** Implementar las rutas y el mapeo de `account_not_allowed` a 403 en `handler.py` y la adopción de ese mapeo en el servicio de u3.
- [ ] **Step 11 — Refactor.** Pruebas en verde; sin credenciales en el código (NFR5.5): solo claves públicas y valores de configuración, con una prueba de patrones de claves sobre los archivos de u4.
- [ ] **Step 12 — Comando de punta a punta.** Comprobar que el comando de verificación aprobado (`cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"`) sigue funcionando con el verificador simulado local y la nueva composición; la verificación real con Cognito queda para cuando exista el grupo de usuarios.

### Comportamiento de la interfaz

Este nivel no aplica: u4 no tiene interfaz (la pantalla de acceso es de `u5-web-app`).

### Infraestructura y entrega

Sin cambios de Terraform ni de CI en esta unidad (`infrastructure-specification.md`): el grupo de usuarios, las federaciones, el CORS de la pasarela y los criterios del plan los entrega `u6-infrastructure`.

### Cierre

- [ ] **Step 13 — Configuración y documentación.** Documentar en `backend/.env.example` las variables nuevas (región del grupo, identificador del grupo, cliente de la aplicación y lista de correos permitidos), sin valores reales. No se modifica el `README.md` de la raíz.
- [ ] **Step 14 — Trazabilidad y resumen.** Escribir `code-summary.md`, `source-manifest.json` y `traceability.json` (cada identificador asignado apunta a un archivo de código o de prueba existente).

### Reparación (regreso desde Build and Test)

Build and Test encontró que el corte de 3 s de la descarga de claves públicas (`HttpsJwksFetcher` en `jwks_store.py`) es un plazo por operación de socket (`urlopen(timeout=3)`) y no un plazo total: un servidor que envía los bytes con cuentagotas puede tardar mucho más de 3 s hasta el tope de 64 KB y mantener el cerrojo de intento único, de modo que las demás solicitudes fallan con `keys_unavailable` (NFR1.2; hallazgo registrado como menor abierto por la revisión de esta unidad y confirmado en `build-and-test/test-results.md`, `## Loop-Back Log`, entrada 1). Los pasos 1 a 14 ya construidos no se rehacen.

- [x] **Step 15 — Rojo (plazo total).** Pruebas en `backend/tests/test_jwks_store.py`: con un servidor simulado que responde en trozos pequeños con pausas, la descarga se abandona al superar 3 s en total (reloj inyectable, sin esperas reales) y se informa como `keys_unavailable` sin modificar la copia; una respuesta que llega completa dentro de 3 s sigue funcionando; el plazo cuenta desde el inicio de la conexión, incluidas las lecturas parciales; el tope de 64 KB y el resto de las reglas existentes siguen igual. Ejecutar y guardar la salida en rojo.
- [x] **Step 16 — Verde.** Implementar el plazo total en `HttpsJwksFetcher` con `time.monotonic()` (comprobar el tiempo transcurrido entre lecturas parciales y abortar al pasar 3 s), sin dependencias nuevas, sin cambiar la interfaz del puerto y sin reintentos; Black y Ruff limpios; suite completa del servicio en verde con el piso de 80 %.
- [ ] **Step 17 — Resumen.** Actualizar `code-summary.md` y `traceability.json` de la unidad con la reparación (NFR1.2) y quitar el punto menor abierto correspondiente.

## Trazabilidad de requisitos a pasos

| Requisito | Pasos |
|-----------|-------|
| AC6.1.1 (parte de u4: el token y su verificación) | 6, 7, 9, 10 |
| AC6.1.2 (parte de u4: SESSION_INVALID sin llamar al modelo) | 6, 7, 9, 10 |
| AC6.1.3 (parte de u4: ACCOUNT_NOT_ALLOWED) | 3, 4, 6, 7, 9, 10 |
| BR4.1 | 6, 7 |
| BR4.2 | 6, 7 |
| BR4.3 | 3, 4, 6, 7 |
| BR4.4 | 6, 7 |
| BR4.5 | 6, 7, 12 |
| BR4.6 | 9, 10 |
| BR4.7 | 6, 7 |
| BR4.8 | 6, 7, 9, 10 |
| NFR1.1 a NFR1.9 | 6, 7 |
| NFR3.1 a NFR3.4 | 6, 7 |
| NFR4.1 a NFR4.7 | 6, 7, 9, 10 |
| NFR5.1 a NFR5.7 | 6, 7, 11 |
| NFR8.1 a NFR8.4 | todos los pasos de Rojo, Verde y Refactor |

## Pruebas (estrategia Standard, piso de 80 %)

| Componente | Pruebas previstas | Tipo |
|------------|-------------------|------|
| Entidades, errores y configuración | 8 a 10 | Unitarias |
| Verificación de tokens | 18 a 22 | Unitarias con claves de prueba |
| Claves públicas (descarga, copia, cerrojo) | 12 a 14 | Unitarias con servidor de claves simulado |
| Lista de cuentas | 8 a 10 | Unitarias |
| Servicio (fallo cerrado, errores, registros, tiempo) | 8 a 10 | Unitarias |
| Manejador de la función | 8 a 10 | De integración con doble de prueba |

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
