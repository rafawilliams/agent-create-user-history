# Code Generation Plan — u5-web-app

## Summary

- Builds: la interfaz completa de la pantalla en `web/`: acceso con Google y Microsoft (Cognito, código con PKCE, token solo en memoria), pantalla principal con título y contador, contexto, generación con carga y reintento, resultado en dos pestañas con vista previa segura y copiado, vencimiento de sesión con copia temporal, cierre de sesión y los temas claro y oscuro.
- Touches: `web/src/` (módulos `config`, `auth/`, `api/`, `state/`, `draft/`, `components/`, `theme`), sus pruebas en `web/src/__tests__/` (o junto a cada módulo), `web/package.json` y su archivo de bloqueo (dependencias y scripts), `web/vite.config.ts` (umbral de cobertura y partición del paquete), `web/scripts/` (tres comprobaciones del paquete), `web/.env.example`, `.github/workflows/ci.yml` (pasos de la pantalla) y los archivos de registro de esta unidad. No se tocan `backend/` ni `infra/` ni los archivos de la raíz del proyecto.
- Tests: unas 90 pruebas nuevas de la pantalla (hoy hay 12), escritas antes del código (TDD), con piso de 80 % de cobertura de líneas en `web/`.

Idioma de los artefactos de esta etapa: español. Identificadores del código nuevo: inglés (`team.md`, Code Style); el texto visible de la pantalla va en español.

## Entradas

`functional-spec.md`, `rules.md` (BR5.1 a BR5.10), `entities.md`, `frontend-components.md`, `performance-design.md`, `security-design.md`, `logical-components.md`, `infrastructure-specification.md` y `cicd-pipeline.md` de u5, `contract-summary.md` (C1, C2 y los requisitos de alojamiento), `unit-of-work.md` y `requirements.md`. La pantalla mínima de u1 (`web/src/App.tsx`, `web/src/api.ts` y sus 12 pruebas) se modifica en su sitio, sin duplicados.

## Decisiones de construcción

- **Proyecto existente (brownfield):** las 12 pruebas de la pantalla y las 558 del servicio siguen en verde, salvo las de la pantalla mínima que contradigan una regla nueva de u5 (se cambian con la razón registrada). El servicio no se modifica.
- **Dependencias nuevas, a fijar con versión exacta al instalarlas:** `oidc-client-ts` y `react-markdown` (producción) y `vitest-axe` (desarrollo); se instalan con `npm ci`/`npm install` y se comprueban con `npm audit --omit=dev --audit-level=high`. Si alguna tiene un hallazgo alto sin parche, se informa a la persona antes de seguir.
- **Estructura:** la de `logical-components.md`; el cliente de C1 de u1 se reorganiza en `api/client` con la tabla de errores de BR5.4.
- **Sin llamadas a AWS, a Cognito ni al servicio en pruebas:** `fetch` y la biblioteca de inicio de sesión se simulan; el reloj es simulado donde hay temporizadores.
- **Sin infraestructura en esta unidad:** el hospedaje, la política de contenido, el cliente de Cognito y el CORS los crea `u6-infrastructure`; la pantalla se configura con variables `VITE_` públicas.
- **Verificación de la unidad:** el comando aprobado del proyecto (`cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"`) no ejercita la pantalla; los comandos de la pantalla (`npm run lint`, `format:check`, `build`, `coverage`, `check:bundle`, `check:secrets` y `check:inline`) se ejecutan en `web/` al cerrar cada capa y quedan registrados en `unit-test-instructions.md`.

## Pasos

### Preparación

- [x] **Step 1 — Estructura y configuración.** Instalar `oidc-client-ts`, `react-markdown` y `vitest-axe` con versión exacta; añadir `browserslist` (últimas dos versiones de Chrome y Edge y Chrome en Android); agregar el umbral de 80 % de líneas a la configuración de Vitest y la partición del paquete (React, MUI y `oidc-client-ts` en grupos propios); crear `web/.env.example` con las variables `VITE_` sin valores reales.
- [x] **Step 2 — Verificar el ejecutor de pruebas y registrar el comando por unidad.** Comprobar que `cd web && npx vitest run` corre en verde (las 12 pruebas de u1) y registrar en `unit-test-instructions.md` el comando de u5 (solo sus archivos de prueba) antes de la primera prueba en rojo.

### Modelo de datos (comportamiento de las entidades) — `config`, `state/screenState`, `draft/draftStore`, validación

Entidades de `entities.md`: `AccessToken`, `ScreenState` (los nueve estados), `Draft` (título, contexto y `accountId`) y `StoryResult`. Sin base de datos.

- [x] **Step 3 — Rojo.** Pruebas: `config` falla por variables ausentes o vacías y no acepta valores con credenciales; validación del título y del contexto (recorte, puntos de código Unicode, 200 y 500, vacío o solo espacios, mensajes literales de BR5.1 y BR5.3); transiciones de `screenState` incluidos accessDenied y sessionExpired y la imposibilidad de dos envíos a la vez; `draftStore` guarda título, contexto y `accountId`, lo restaura solo con la misma cuenta y se borra en cada salida de NFR4.4. Ejecutar y guardar la salida en rojo.
- [x] **Step 4 — Verde.** Implementar lo mínimo en esos módulos.
- [x] **Step 5 — Refactor.** Mejorar con las pruebas en verde.

### Acceso a datos

Este nivel no aplica: la pantalla no guarda datos en el servidor; la copia temporal en sessionStorage se cubre en el paso 3.

### Lógica de negocio — `auth/authClient`, `auth/sessionHolder`, `api/client`

- [x] **Step 6 — Rojo.** Pruebas con la biblioteca y `fetch` simulados:
  - Inicio de sesión (BR5.7, BR5.10, NFR5.2, NFR5.5): `identity_provider` igual a `Google` o `Microsoft`; retorno con `code` y `state` válidos, con `state` distinto o ausente, con `error` (con y sin `state`); la dirección se limpia en éxito y en fallo con la dirección capturada antes; el doble efecto de `StrictMode` no consume el código dos veces; cierre en el orden DELETE, `removeUser()`, borrado de la copia y navegación a la dirección de cierre exacta.
  - Token (BR5.6, NFR4.1, NFR4.2): `sessionHolder` lo guarda solo en memoria (localStorage y sessionStorage no lo contienen), entrega nada si venció y expone `exp`; el almacén de usuario es el de memoria; la consola no recibe token ni títulos.
  - Cliente de C1 y C2 (BR5.2, BR5.4, NFR1.1, NFR3.1): `Authorization: Bearer`; corte a los 60 s con reloj simulado y respuesta tardía descartada; un solo envío por clic; cada fila de la tabla de errores (NEEDS_CONTEXT, CONTEXT_TOO_LONG, TITLE_*, RATE_LIMITED con "Reintentar" bloqueado 30 s, SESSION_INVALID, ACCOUNT_NOT_ALLOWED, GENERATION_TIMEOUT y los demás, cuerpos no JSON, red caída, 200 sin `markdown`); nunca se muestra texto del servidor; sin solicitudes sin acción de la persona.
  - Ejecutar y guardar la salida en rojo.
- [x] **Step 7 — Verde.** Implementar `authClient`, `sessionHolder` y `api/client`.
- [x] **Step 8 — Refactor.** Simplificar con las pruebas en verde.

### API / punto de entrada

Este nivel no aplica: la pantalla es un cliente; el cliente de C1 y C2 se prueba en los pasos 6 a 8. El contrato C1 y C2 lo implementan u1, u3 y u4.

### Comportamiento de la interfaz — `components/*`, `ResultView`, `MarkdownPreview`, `theme`, `App`

- [x] **Step 9 — Rojo.** Pruebas de componentes con Testing Library y `vitest-axe`:
  - S1 y S2 (BR5.1 a BR5.4, BR5.7, BR5.8; AC1.1.1 a AC1.1.4, AC5.1.1 a AC5.1.3, AC6.1.1 a AC6.1.3): sin token solo se ve S1 y no redirige sola; "Iniciando sesión"; mensaje de acceso con `role="alert"` y botones disponibles; título vacío con foco al campo; 201 caracteres y exactamente 200; contador "N / 200"; contexto con foco y 500 caracteres; indicador de carga en el mismo ciclo del clic y botón desactivado; doble clic envía una sola solicitud; fallos con "Reintentar" y el título conservado; accessDenied con "Cerrar sesión"; sesión vencida con la copia temporal y restauración con la misma cuenta; recarga durante generating vuelve a S2 vacío; cerrar sesión.
  - Resultado (BR5.5; AC4.1.1 a AC4.1.4, NFR4.3): pestañas "Vista previa" y "Markdown" con el mismo contenido y flechas del teclado; copiado exacto con "Markdown copiado" en región de estado y aviso si el navegador rechaza la copia; la vista previa no ejecuta HTML (etiqueta de script, controlador de evento, enlace `javascript:` e imagen remota); solo `http`, `https` y `mailto`, con `rel="noopener noreferrer"`; fallo de la carga diferida con aviso y reintento que recrea la importación y la pestaña Markdown y el botón de copiar siguen funcionando.
  - Accesibilidad y diseño (NFR6.1, NFR7.1, BR5.9): sin violaciones de `vitest-axe` en S1, S2 vacío, cargando, error, contexto y resultado; el tema define `minHeight` y `minWidth` de 44 px; los dos temas.
  - Ejecutar y guardar la salida en rojo.
- [x] **Step 10 — Verde.** Implementar los componentes, la vista previa diferida con `React.lazy`, el tema y la composición de `App`/`main.tsx` (con `StrictMode`).
- [x] **Step 11 — Refactor.** Pruebas en verde; sin credenciales ni secretos en el código (NFR5.1).

### Infraestructura y entrega

- [x] **Step 12 — Comprobaciones del paquete y CI.** Escribir con prueba primero las tres comprobaciones de `web/scripts/` (`check:bundle` con el presupuesto de 400 KB gzip y la vista previa fuera de la carga inicial, `check:secrets` con los patrones de `cicd-pipeline.md` y `check:inline` sobre `dist/index.html`), añadir los scripts a `package.json` y los pasos de la pantalla a `.github/workflows/ci.yml` con valores ficticios de las variables `VITE_` en los pull requests y `npm ci`, `npm audit --omit=dev --audit-level=high`. Los recursos de AWS son de `u6-infrastructure`.

### Cierre

- [x] **Step 13 — Verificación completa.** Ejecutar en `web/`: `npm run format:check`, `npm run lint`, `npm run build`, `npm run coverage` (piso de 80 %), `npm run check:bundle`, `npm run check:secrets`, `npm run check:inline` y `npm audit --omit=dev --audit-level=high`; ejecutar también la suite del servicio sin cambios (`cd backend && python -m pytest tests -q`).
- [ ] **Step 14 — Trazabilidad y resumen.** Escribir `code-summary.md`, `source-manifest.json` y `traceability.json` (cada identificador asignado apunta a un archivo de código o de prueba existente).

## Trazabilidad de requisitos a pasos

| Requisito | Pasos |
|-----------|-------|
| AC1.1.1 a AC1.1.4 | 3, 4, 9, 10 |
| AC4.1.1 a AC4.1.4 | 9, 10 |
| AC5.1.1 a AC5.1.4 | 6, 7, 9, 10 |
| AC6.1.1 a AC6.1.3 | 6, 7, 9, 10 |
| BR5.1 a BR5.3 | 3, 4, 9, 10 |
| BR5.4 | 6, 7, 9, 10 |
| BR5.5 | 9, 10 |
| BR5.6 | 3, 4, 6, 7, 9, 10 |
| BR5.7, BR5.8 | 6, 7, 9, 10 |
| BR5.9 | 9, 10 |
| BR5.10 | 6, 7 |
| NFR1.1 a NFR1.3 | 6, 7, 10, 12 |
| NFR3.1 | 6, 7 |
| NFR4.1 a NFR4.4 | 3, 4, 6, 7, 9, 10 |
| NFR5.1 a NFR5.3 | 6, 7, 11, 12 |
| NFR5.4 | 12 (la cabecera la sirve u6) |
| NFR5.5 | 6, 7 |
| NFR6.1 | 9, 10 |
| NFR7.1, NFR7.2 | 1, 9, 10 |
| NFR8.1, NFR8.2 | todos los pasos de Rojo, Verde y Refactor, y 13 |

## Pruebas (estrategia Standard, piso de 80 %)

| Componente | Pruebas previstas | Tipo |
|------------|-------------------|------|
| Configuración, validación y estado | 12 a 15 | Unitarias |
| Copia temporal | 6 a 8 | Unitarias con sessionStorage simulado |
| Inicio y cierre de sesión | 12 a 14 | Unitarias con la biblioteca simulada |
| Token en memoria | 5 a 6 | Unitarias |
| Cliente de C1 y C2 | 16 a 20 | Unitarias con `fetch` simulado y reloj simulado |
| Pantallas S1 y S2 | 18 a 22 | De componentes |
| Resultado y vista previa | 12 a 14 | De componentes |
| Accesibilidad y tema | 5 a 6 | De componentes con `vitest-axe` |
| Comprobaciones del paquete | 6 a 8 | Unitarias de los scripts |

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
