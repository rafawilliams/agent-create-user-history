# Trazabilidad entre unidades — Build and Test

Comando: `aidlc engine sensor-traceability --stage build-and-test` (ejecutado como comando propio, sin tubería; código de salida 0). Se volvió a ejecutar en la segunda pasada, tras el regreso 1 (cambiaron los `traceability.json` de u4 y u6): el resultado es el mismo, 52 elementos rastreados y los mismos 10 sin cubrir. La herramienta devolvió `"pass": false` con 10 elementos sin cubrir.

## Veredicto

**Fail.** Hay 10 elementos sin cubrir: `FR3.1`, `FR3.2`, `FR7.1`, `NFR2`, `NFR3`, `NFR5`, `NFR6`, `NFR8`, `AC3.1.2` y `AC7.1.2`. Cada elemento sin cubrir es un hallazgo de esta etapa que se presenta en la puerta de aprobación. Ningún elemento queda marcado como cubierto solo por estar en el plan: la columna "Construido en" sale de la salida de la herramienta (`through` y `built_in`).

La herramienta rastreó 52 elementos (20 `FR`, 24 `AC`, 8 `NFR`): 42 con cobertura y 10 sin cubrir. Más abajo está la cobertura de cada identificador.

## Elementos sin cubrir

| ID | Qué es | Por qué no está cubierto (salida de la herramienta) | Causa real (leída de los `traceability.json` y resúmenes de las unidades) | Qué hace falta |
|----|--------|-------------------------------------------------------|----------------------------------------------------------------------------|----------------|
| `AC3.1.2` | Criterio de aceptación de la revisión manual del 80 % de Gherkin válido (con `NFR2`) | `not_built` | u3 lo dejó `Deferred`: la revisión la hace la persona con los 10 títulos de `docs/titulos-prueba-nfr2.md`, que aún no tienen la línea de aprobación | La persona aprueba los títulos, corre el comando con el modelo real y registra cuántos producen un Gherkin válido a la primera (meta 80 %) |
| `FR3.1`, `FR3.2` | Requisitos funcionales que dependen de `AC3.1.1` y `AC3.1.2` | `AC3.1.2` no construido | Misma causa que `AC3.1.2` | Igual |
| `NFR2` | Meta de 80 % de calidad del Gherkin | `AC3.1.2` no construido | Misma causa | Igual |
| `AC7.1.2` | Registro de la evaluación de modelos con el resultado de cada modelo y la decisión | sin código ni prueba que lo "construya" como entregable | u2 lo dejó `Deferred`: el comando `evaluate_models` está probado con modelos simulados, pero `docs/evaluacion-modelos.md` no existe | La persona aprueba los 5 títulos de `docs/titulos-evaluacion.md`, confirma el identificador de Amazon Titan y ejecuta `evaluate_models approve` y `run` con acceso a Bedrock |
| `FR7.1` | Requisito funcional de la evaluación de modelos | `AC7.1.2` no construido | Misma causa | Igual |
| `NFR3` | Capacidad (hasta 5 personas, 20 solicitudes por persona y día) | `u1-walking-skeleton: NFR3.2` marcado `not_built` | u1 difirió el límite diario por persona a u4 (desviación registrada en `nfr-design/scalability-design.md`); u4 lo difirió a "una versión posterior" (`u4 NFR3.4`). Nadie lo construye. Coincide con la fila `u1/NFR3.2` en `Not Met` del resumen (sigue `Not Met`) | Decisión de la persona: implementar un contador por cuenta (requiere estado) o cambiar el requisito |
| `NFR5` | Seguridad y secretos | `u5-web-app: NFR5.4` marcado `not_built` | u5 difirió la política de contenido a u6. La cabecera exacta existe en `infra/web_headers.tf` y la afirma `infra/tests/app.tftest.hcl::content_security_policy_is_exact` (pasa), pero el `traceability.json` de u6 no lleva ese identificador de u5 (el `NFR5.4` de u6 es el límite de permisos de IAM: las unidades reutilizan los mismos números) | Corregir la trazabilidad: registrar en u6 la cobertura de la política de contenido de u5 (con otro identificador) o marcar en u5 el destino |
| `NFR6` | Accesibilidad | la herramienta no encontró ninguna fila en ninguna unidad (ni `through` ni `built_in`) | Ningún `traceability.json` de `code-generation` lista `NFR6.1` ni `NFR6.2`, aunque existen pruebas (`web/src/__tests__/accessibility.test.tsx`, marcadas `NFR6.1`) y la revisión manual de contraste sigue pendiente | Añadir `NFR6.1` y `NFR6.2` a la trazabilidad de u5 (`NFR6.2` como diferido a revisión manual) |
| `NFR8` | Mantenibilidad (TDD, 80 %, Black/Ruff/Prettier/ESLint, nombres en inglés) | ninguna fila en ninguna unidad | Ningún `traceability.json` de `code-generation` lista `NFR8.1` a `NFR8.4`, aunque las siguientes unidades los citan en sus planes | Añadir `NFR8.x` a la trazabilidad de cada unidad (u1 a u6) |

## Cobertura por identificador

### Requisitos funcionales

| ID | Cubierto | Mediante |
|----|----------|----------|
| `FR1.1`, `FR1.2`, `FR1.3`, `FR1.4` | sí | `AC1.1.1` a `AC1.1.4` |
| `FR2.1` a `FR2.5` | sí | `AC2.1.1` a `AC2.1.4` |
| `FR3.1`, `FR3.2` | **no** | `AC3.1.1` (sí) y `AC3.1.2` (no construido) |
| `FR4.1` a `FR4.4` | sí | `AC4.1.1` a `AC4.1.4` |
| `FR5.1` a `FR5.3` | sí | `AC5.1.1` a `AC5.1.4` |
| `FR6.1` | sí | `AC6.1.1` a `AC6.1.3` |
| `FR7.1` | **no** | `AC7.1.1` y `AC7.1.3` (sí), `AC7.1.2` (no construido) |

### Criterios de aceptación

| ID | Cubierto | Construido en (unidad: archivo) |
|----|----------|--------------------------------|
| `AC1.1.1` | sí | u3: `backend/story_service/input_validation.py`; u5: `web/src/__tests__/screens.test.tsx` |
| `AC1.1.2` | sí | u3: `backend/tests/test_input_validation.py`; u5: `web/src/validation.ts` |
| `AC1.1.3` | sí | u3: `backend/tests/test_input_validation.py`; u5: `web/src/__tests__/validation.test.ts` |
| `AC1.1.4` | sí | u3: `backend/tests/test_story_generation.py`; u5: `web/src/components/ContextField.tsx` |
| `AC2.1.1` | sí | u1 y u3: `backend/story_service/service.py` |
| `AC2.1.2` | sí | u1: `backend/tests/test_service.py`; u3: `backend/story_service/markdown_builder.py` |
| `AC2.1.3` | sí | u1: `backend/story_service/prompt.py`; u3: `backend/story_service/response_parsing.py` |
| `AC2.1.4` | sí | u3: `backend/tests/test_prompt.py` |
| `AC3.1.1` | sí | u3: `backend/tests/test_markdown_builder.py` |
| `AC3.1.2` | **no** | — (revisión manual; ver arriba) |
| `AC4.1.1` | sí | u5: `web/src/components/ResultView.tsx` |
| `AC4.1.2` | sí | u5: `web/src/__tests__/resultView.test.tsx` |
| `AC4.1.3` | sí | u3: `backend/story_service/markdown_builder.py` |
| `AC4.1.4` | sí | u3: `backend/tests/test_markdown_builder.py`; u5: `web/src/__tests__/resultView.test.tsx` |
| `AC5.1.1` | sí | u5: `web/src/state/useStoryScreen.ts` |
| `AC5.1.2` | sí | u2: `backend/story_service/error_translation.py`; u3: `backend/tests/test_story_generation.py`; u5: `web/src/__tests__/apiClient.test.ts` |
| `AC5.1.3` | sí | u3: `backend/tests/test_response_parsing.py`; u5: `web/src/api/client.ts` |
| `AC5.1.4` | sí | u2: `backend/story_service/bedrock_client.py`; u3: `backend/story_service/service.py` |
| `AC6.1.1` | sí | u4: `backend/story_service/token_verifier.py`; u5: `web/src/auth/authClient.ts`; u6: `infra/cognito.tf` |
| `AC6.1.2` | sí | u4: `backend/tests/test_access_control.py`; u5: `web/src/__tests__/screens.test.tsx`; u6: `infra/tests/api.tftest.hcl` |
| `AC6.1.3` | sí | u4: `backend/tests/test_account_allowlist.py`; u5: `web/src/components/LoginButtons.tsx`; u6: `infra/tests/app.tftest.hcl` |
| `AC7.1.1` | sí | u2: `backend/story_service/evaluation.py` |
| `AC7.1.2` | **no** | — (necesita la ejecución real con Bedrock; ver arriba) |
| `AC7.1.3` | sí | u2: `backend/tests/test_evaluation.py` |

### Requisitos no funcionales

| ID | Cubierto | Unidades y filas (`through`) | `N/A` registrados con su motivo |
|----|----------|------------------------------|---------------------------------|
| `NFR1` | sí | u1: NFR1.1 a NFR1.6; u3: NFR1.1 a NFR1.9; u4: NFR1.1 a NFR1.8; u5: NFR1.1 a NFR1.3; u6: NFR1.1 | u3 `NFR1.9` (sin datos que respaldar; el título lo conserva u5); u4 `NFR1.8` (sin datos que respaldar) |
| `NFR2` | **no** | `AC3.1.1`, `AC3.1.2` | — |
| `NFR3` | **no** | u1: NFR3.1 a NFR3.3 (`NFR3.2` `not_built`); u3: NFR3.1 a NFR3.3; u4: NFR3.1 a NFR3.4; u5: NFR3.1; u6: NFR3.1 | u3 `NFR3.2` y `NFR3.3`; u4 `NFR3.4` (el tope y el límite de tasa son de u1 y u6; el límite por persona queda fuera del MVP) |
| `NFR4` | sí | u1: NFR4.1 a NFR4.4; u2: NFR4.1 a NFR4.3; u3: NFR4.1 a NFR4.6; u4: NFR4.1 a NFR4.4; u5: NFR4.1 a NFR4.4; u6: NFR4.1 a NFR4.3 | — |
| `NFR5` | **no** | u1: NFR5.1, NFR5.2; u2: NFR5.1 a NFR5.3; u3: NFR5.1, NFR5.2; u4: NFR5.1 a NFR5.7; u5: NFR5.1 a NFR5.5 (`NFR5.4` `not_built`); u6: NFR5.1 a NFR5.9 | — |
| `NFR6` | **no** | ninguna fila | — |
| `NFR7` | sí | u5: NFR7.1, NFR7.2 | — |
| `NFR8` | **no** | ninguna fila | — |

## Observación de esta etapa

Los números de requisito por unidad (`NFR5.4`, `NFR3.2`, …) se reutilizan con significados distintos en cada unidad, y la herramienta los suma por unidad. Eso explica por qué una cobertura real (la política de contenido de u5 está construida en u6 y probada) aparece como no construida. La corrección es de trazabilidad, no de código. Los demás hallazgos de esta tabla son pendientes reales de la persona (revisión manual, evaluación con modelo real) o una decisión de requisito (`NFR3`).
