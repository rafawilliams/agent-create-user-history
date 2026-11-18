# Resultados de pruebas — Build and Test

Fecha de ejecución: 2026-11-18 (primera pasada) y segunda pasada completa tras el regreso 1 (se volvieron a ejecutar todos los comandos de abajo; los resultados de esta tabla son los de la segunda pasada). Máquina: Windows 11, Python 3.13.3, Terraform 1.16.3, Node con `node_modules` ya instalado (no se ejecutó `npm ci`). Cada comando distinto se ejecutó una sola vez; las ejecuciones por unidad y por límite entre unidades son subconjuntos de la suite completa y no se suman a los totales.

No se llamó a AWS, a Cognito ni a ningún modelo. No se ejecutó `terraform plan` ni `apply`. **No se ejecutó el comando de verificación aprobado** (`python -m story_service.local_run --local "Recuperar contraseña"`), porque llama al modelo real de Amazon Bedrock; queda `Unverified` donde corresponde (ver `build-and-test-summary.md`).

Ningún navegador real corrió en esta etapa: todas las pruebas de la pantalla corren en Node con jsdom (emulador de DOM) y son evidencia de integración, no de navegador.

## Resumen de ejecución

| ID | Comando (directorio) | Código de salida | Resultado |
|----|----------------------|------------------|-----------|
| BE-1 | `python -m pytest tests -q --cov=story_service --cov-report=term-missing --cov-fail-under=80` (`backend/`) | 0 | 563 passed, 0 failed, 0 skipped (antes 558; +5 pruebas del plazo total de `HttpsJwksFetcher`); cobertura de líneas 99,68 % (1269 sentencias, 4 sin cubrir); umbral 80 % alcanzado |
| BE-2 | `python -m black --check .` (`backend/`) | 0 | 47 archivos sin cambios |
| BE-3 | `python -m ruff check .` (`backend/`) | 0 | All checks passed |
| BE-U2 | subconjunto de u2 (6 archivos de prueba, comando de `unit-test-instructions.md`) | 0 | 187 passed |
| BE-U3 | subconjunto de u3 (7 archivos) | 0 | 218 passed |
| BE-U4 | subconjunto de u4 (7 archivos) | 0 | 279 passed (antes 274) |
| BE-I | `python -m pytest tests/test_composition.py tests/test_access_control.py tests/test_story_generation.py -q` | 0 | 69 passed (ya incluidas en BE-1; sin cambios) |
| WEB-1 | `npm run format:check` (`web/`) | 0 | Prettier: todos los archivos con el estilo correcto |
| WEB-2 | `npm run lint` | 0 | ESLint sin hallazgos |
| WEB-3 | `npm run build` (con las cinco variables `VITE_` ficticias) | 0 | `tsc --noEmit` y `vite build` correctos; 1100 módulos; 5 paquetes |
| WEB-4 | `npm run coverage` | 0 | 12 archivos de prueba, 186 passed, 0 failed; cobertura de líneas 98,4 % (ramas 94,35 %, funciones 96,7 %); umbral `lines: 80` alcanzado |
| WEB-5 | `npm run check:bundle` | 0 | Carga inicial 142 960 bytes gzip frente a 409 600; la vista previa queda fuera |
| WEB-6 | `npm run check:secrets` | 0 | Sin secretos ni claves en `dist` |
| WEB-7 | `npm run check:inline` | 0 | `index.html` sin scripts en línea |
| WEB-8 | `npm audit --omit=dev --audit-level=high` | 0 | found 0 vulnerabilities |
| WEB-I | `npx vitest run src/__tests__/bootstrap.test.tsx src/__tests__/screens.test.tsx` | 0 | 2 archivos, 38 passed (ya incluidas en WEB-4) |
| TF-1 | `terraform fmt -check -recursive` (`infra/`) | 0 | Sin diferencias |
| TF-2 | `terraform init -backend=false -input=false` | 0 | Inicializado |
| TF-3 | `terraform validate` | 0 | The configuration is valid |
| TF-4 | `terraform test` | 0 | 59 passed, 0 failed (antes 56; `api`, `app`, `package` —nuevo, 3 afirmaciones—, `variables`) |
| TFB-1 | `terraform fmt -check -recursive` (`infra/bootstrap/`) | 0 | Sin diferencias |
| TFB-2 | `terraform init -backend=false -input=false` | 0 | Inicializado |
| TFB-3 | `terraform validate` | 0 | The configuration is valid |
| TFB-4 | `terraform test` | 0 | 38 passed, 0 failed (`roles`, `state_bucket`, `variables`) |
| IS-1 | `REQUIRE_REAL_PACKAGE=1 python -m pytest -q --cov=. --cov-fail-under=80` (`infra/scripts/`) | 0 | 110 passed, 0 skipped (antes 80), incluidas las pruebas del paquete real `infra/build/package` (`test_real_package.py`); cobertura 97,65 % (`build_lambda_package.py` 97 %, `check_pins.py` 98 %, `check_plan.py` 98 %, `check_secrets.py` 98 %); umbral 80 % alcanzado. No se volvió a ejecutar el script de empaquetado ni ningún `pip install` |
| IS-2 | `python -m black --check .` (`infra/scripts/`) | 0 | 11 archivos sin cambios |
| IS-3 | `python -m ruff check .` (`infra/scripts/`) | 0 | All checks passed |
| IS-4 | `python infra/scripts/check_pins.py .github/workflows` (raíz) | 0 | `check_pins: OK` |
| IS-5 | `python infra/scripts/check_secrets.py infra .github` (raíz) | 0 | `check_secrets: OK` |
| TR | `aidlc engine sensor-traceability --stage build-and-test` (segunda pasada) | 0 (la herramienta sale con 0; el veredicto va en el JSON: `pass: false`) | Los mismos 10 elementos sin cubrir; ver `cross-unit-traceability.md` |

Totales sin doble conteo: **pytest 563 + 110 = 673; Vitest 186; `terraform test` 59 + 38 = 97**. Ningún comando falló. Los subconjuntos BE-U2 (187), BE-U3 (218), BE-I (69) y WEB-I (38) dieron los mismos resultados que en la primera pasada.

### Comprobaciones puntuales de solo lectura (no son pruebas del repositorio)

| ID | Comando | Resultado |
|----|---------|-----------|
| G-1 | `grep -rnE "AKIA[0-9A-Z]{16}\|ASIA[0-9A-Z]{16}\|BEGIN (RSA \|EC )?PRIVATE KEY\|client_secret *= *\""` sobre `backend`, `web/src`, `web/scripts`, `infra` y `.github` (sin `node_modules`, `dist`, `.terraform`) | Solo coincidencias dentro de archivos de prueba, con valores de ejemplo (`AKIAABCDEFGHIJKLMNOP`, `dummy`); ninguna en código de producción |
| G-2 | búsqueda de `eval(` y `new Function(` en `web/dist/assets/*.js` | 0 coincidencias en los 5 paquetes |
| G-3 | búsqueda de identificadores en español (`def`, `class`, `const`, `let`, `function`) en `backend/story_service` y `web/src` (sin pruebas) | Ninguno (`Criterion` es una palabra inglesa válida) |
| G-4 | script en línea (`python -I -c`, no guardado) que genera con el modelo simulado un título de 200 caracteres, un contexto de 500 y una respuesta de 3 criterios con campos de 300 caracteres (3145 bytes), 20 repeticiones tras calentamiento | mediana 0,59 ms, máximo 1,11 ms (meta de u3: menos de 50 ms) |
| G-5 | script en línea que genera con título vacío, de 201 caracteres, contexto de 501 y título corto sin contexto, y lee los registros | Cada rechazo emite `errors_total` con su código (`TITLE_EMPTY`, `TITLE_TOO_LONG`, `CONTEXT_TOO_LONG`, `NEEDS_CONTEXT`). No hay una prueba automática del repositorio que lo afirme (ver hallazgos menores) |

## Cobertura de líneas

### Servicio (BE-1, suite completa; piso del proyecto 80 %)

Total 99,68 % (`jwks_store.py` 100 % con el plazo total). Líneas sin cubrir: `evaluate_models.py:46`, `local_run.py:79`, `models.py:133`, `token_verifier.py:125`. Cobertura por archivo de cada unidad (se informa aparte, como piden NFR8.2 de u2, u3 y u4):

| Unidad | Archivos | Cobertura |
|--------|----------|-----------|
| u1 | `service.py`, `handler.py`, `config.py`, `logging_utils.py`, `prompt.py`, `errors.py`, `fakes.py`, `ports.py`, `bedrock_client.py`, `local_run.py` | 100 % salvo `local_run.py` 98 % |
| u2 | `bedrock_client.py`, `config.py`, `error_translation.py`, `evaluation.py`, `model_profile.py` 100 %; `evaluate_models.py` 98 %; `models.py` 99 % | todos ≥ 98 % |
| u3 | `input_validation.py`, `markdown_builder.py`, `response_parsing.py`, `service.py`, `prompt.py` 100 %; `models.py` 99 % | todos ≥ 99 % |
| u4 | `auth_config.py`, `jwks_store.py`, `account_allowlist.py` 100 %; `token_verifier.py` 99 %; `models.py` 99 % | todos ≥ 99 % |

### Pantalla (WEB-4; umbral `lines: 80` en `vite.config.ts`)

Total 98,4 % de líneas. Archivos más bajos: `bootstrap.tsx` 88,88 %, `config.ts` 92,3 %, `StatusMessage.tsx` 94,54 %, `useStoryScreen.ts` 96,68 %.

### Scripts de infraestructura (IS-1; piso 80 %)

Total 97,65 % (340 sentencias, 8 sin cubrir: `build_lambda_package.py` 111, 134, 181, 225; `check_pins.py` 88; `check_plan.py` 93, 193; `check_secrets.py` 91). Terraform (HCL) no tiene medición de cobertura de líneas: se comprueba con 97 afirmaciones de `terraform test`.

## Fallos

Ningún comando falló. Los hallazgos `Not Met` X7 (empaquetado de la función) y u4/NFR1.2 (plazo total de la descarga de claves) tienen una causa en el código generado con una corrección identificable, por lo que se abre el regreso autónomo de abajo; u1/NFR3.2 y u3/NFR4.5 son decisiones de la persona y se presentan en la puerta de aprobación.

## Loop-Back Log

### Loop-back 1 — 2026-11-18T20:00:00Z

- **Diagnosis:** (1) X7: `data.archive_file.story_service` de `infra/main.tf` empaqueta solo `backend/` y excluye `requirements*.txt`; ningún paso instala `PyJWT[crypto]` ni `cryptography`, que `token_verifier.py` y `jwks_store.py` importan al arrancar y que el tiempo de ejecución `python3.12` de Lambda no trae: toda solicitud desplegada fallaría al importar. (2) u4/NFR1.2: `urlopen(timeout=3)` es un plazo por operación de socket y la lectura de la respuesta no tiene un plazo total de 3 s.
- **Root-cause stage:** code-generation de u6-infrastructure (empaquetado) y de u4-access-control (descarga de claves).
- **Planned fix:** u6: instalar las dependencias de ejecución (`backend/requirements.txt`) para Lambda (`python3.12`, `manylinux2014_x86_64`, solo ruedas binarias) en una carpeta de empaquetado que el archivo comprimido incluya, con una prueba que falle si el paquete no contiene `jwt` ni `cryptography`, sin ejecutar `plan` ni `apply`; u4: plazo total de 3 s con `time.monotonic()` entre lecturas parciales y una prueba con un servidor que responde gota a gota.
- **Estimated impact:** X7: esfuerzo bajo a medio (un paso de empaquetado reproducible más pruebas), riesgo alto si no se corrige (el despliegue no sirve ninguna solicitud), sin costo adicional; NFR1.2: esfuerzo bajo, riesgo bajo.

## Hallazgos `Not Met`: estado tras la segunda pasada

Esta etapa corre en modo autónomo y no cambia código ni estado del flujo. El regreso 1 (ver `## Loop-Back Log`) reparó los dos hallazgos que tenían una corrección identificable en el código; la segunda pasada los volvió a medir.

| ID | Estado en la primera pasada | Estado ahora | Evidencia de la segunda pasada |
|----|-----------------------------|--------------|--------------------------------|
| X7 | `Not Met`: la función se empaquetaba sin `PyJWT[crypto]` ni `cryptography` | **`Met`** (más una fila `X7b` `Unverified` para lo que exige AWS o GitHub) | `infra/scripts/build_lambda_package.py` arma `infra/build/package`; `data.archive_file` comprime esa carpeta; `TF-4` (3 afirmaciones de `package.tftest.hcl`) e `IS-1` con `REQUIRE_REAL_PACKAGE=1` (`test_real_package.py`: contiene `handler.py` y `jwt`, sin pruebas ni cachés, binarios ELF x86_64 con glibc ≤ 2.34, tamaños dentro de los límites de Lambda) |
| u4/NFR1.2 | `Not Met`: el corte de 3 s era por operación de socket | **`Met`** con la limitación declarada (ver el motivo en la matriz) | `BE-1`: `test_a_slow_drip_download_is_abandoned_once_3_seconds_have_passed_in_total`, `test_time_spent_connecting_counts_towards_the_total_deadline`, `test_a_total_deadline_failure_is_keys_unavailable_leaves_the_copy_and_frees_the_lock`; `jwks_store.py` 100 % |
| u1/NFR3.2 | `Not Met` | `Not Met` (sin cambio): decisión de la persona | Sin contador por persona; diferido por u1 y u4 |
| u3/NFR4.5 | `Not Met` | `Not Met` (sin cambio): decisión de la persona | Requisito 8 KB frente a código y diseño de 16 KB |

Escalera de fallo: ningún comando falló; los dos `Not Met` restantes no tienen una corrección dentro de esta etapa (son decisiones de requisito) y se presentan en la puerta de aprobación.

## Fallo aceptado por la persona

La persona eligió «Accept failure» (mensaje `cc2b374b`, 2026-11-19) ante la pregunta de la etapa, con 1 de 3 regresos usados. Queda registrado como fallo aceptado de la etapa, sin debilitar ningún objetivo:

- **u1/NFR3.2** (límite de 20 solicitudes por persona y día): decisión de requisito pendiente para después del MVP; arreglarlo exige un contador por cuenta con estado, lo que choca con NFR4.1.
- **u3/NFR4.5** (tope de la respuesta del modelo): pendiente de enmendar el requisito a 16 KB, que es lo que usan el código y el diseño (el peor caso válido ocupa unos 8,6 KB).
- **27 objetivos sin verificar:** acciones de la persona o revisiones manuales con cuenta de AWS, navegador real o proveedor de identidad (ver la matriz).

## Pruebas existentes que no se ejecutaron aquí

- Comando de punta a punta contra Amazon Bedrock (`local_run`) y `evaluate_models approve|run`: requieren credenciales de AWS y acceso al modelo.
- `terraform plan`/`apply`, Checkov, `actionlint`, ejecución de los flujos de GitHub: requieren cuenta de AWS, GitHub o instalación de herramientas no solicitadas.
- Revisiones manuales (contraste, desbordamiento, lector de pantalla, Gherkin de NFR2, pegado en Jira) e inicio de sesión real con Cognito, Google y Microsoft.
