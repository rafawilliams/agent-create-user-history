# Code Summary — u3-story-generator

## Archivos creados

- **`backend/story_service/`**: `input_validation.py` (validación del título y del contexto, y la petición de contexto; el umbral de 2 palabras y 12 caracteres está en una sola constante), `response_parsing.py` (JSON del modelo con tope de 16 KB, cerco opcional, campos de hasta 300 caracteres, 2 a 3 criterios y heurística de idioma), `markdown_builder.py` (escape y armado del Markdown con el Gherkin).
- **`backend/tests/`**: `test_input_validation.py`, `test_prompt.py`, `test_response_parsing.py`, `test_markdown_builder.py`, `test_story_generation.py`.
- **`docs/titulos-prueba-nfr2.md`**: 10 títulos inventados para la revisión manual de NFR2, sin la línea de aprobación.

## Archivos modificados

- `errors.py` (códigos `CONTEXT_TOO_LONG` 400 y `NEEDS_CONTEXT` 422, ambos no reintentables), `models.py` (`StoryRequest` con contexto, `Criterion`, `StoryDraft`), `logging_utils.py` (`u3DurationMs` e `internal_error` en la lista cerrada), `prompt.py` (marcas y neutralización), `service.py` (nueva orquestación con manejador de errores internos después de los errores tipados), `config.py` (instrucciones por defecto que piden JSON; `STORY_INSTRUCTIONS` sigue funcionando), `handler.py` (lee `context`), `local_run.py` (contexto como segundo argumento), `fakes.py` (el modelo simulado devuelve JSON), `backend/.env.example`.
- `contract-summary.md`: `CONTEXT_TOO_LONG` y el máximo de 500 caracteres del contexto registrados en C1, con las dos preguntas abiertas de C1 cerradas.
- No se tocaron los archivos de la raíz del proyecto.

## Decisiones de implementación

- El modelo ya no devuelve el Markdown: devuelve JSON y el servicio arma el Markdown (ADR-005). El rol, las palabras clave del Gherkin y la línea `# language: es` los fija el servicio. Es un cambio deliberado de comportamiento respecto de u1.
- Umbral de contexto: menos de 2 palabras o menos de 12 caracteres (ajuste a la respuesta Q1 de la persona, **pendiente de su confirmación**).
- La neutralización de las marcas ignora mayúsculas y espacios y se repite hasta que no queda ninguna marca.

## Cobertura y resultados

| Parte | Pruebas | Cobertura de líneas | Herramientas de estilo |
|-------|---------|---------------------|------------------------|
| Suite completa del servicio | 356 en verde (209 anteriores y las nuevas de u3) | 99,65 % (piso 80 %, `fail_under = 80` intacto) | Black y Ruff sin errores |
| Archivos de u3 | 185 en verde con el comando de la unidad | `input_validation.py`, `markdown_builder.py`, `response_parsing.py`, `service.py`, `prompt.py`, `logging_utils.py`, `handler.py`, `errors.py` y `config.py` al 100 %; `models.py` 99 %; `local_run.py` 98 % | — |

Se volvió a ejecutar la suite completa al cerrar la etapa: 356 pruebas en verde y 99,65 %.

## Pruebas existentes que cambiaron, y por qué

- `test_service.py`: las pruebas de las instrucciones por defecto y las aserciones sobre el resultado cambiaron porque el modelo ahora devuelve JSON; los títulos de una sola palabra pasaron a títulos suficientes porque ahora piden contexto (BR3.2).
- `test_logging.py`, `test_handler.py`, `test_local_run.py`: la lista cerrada de campos incluye `u3DurationMs`; los títulos de prueba pasaron a títulos suficientes y el cuerpo esperado es el Markdown armado.

## Pruebas escritas pero no ejecutadas en esta etapa

- **El comando de punta a punta contra Amazon Bedrock** (`local_run`): no se ejecutó en esta etapa; se ejecuta en la verificación de la unidad.
- **La revisión manual de NFR2** (80 % de Gherkin válido con los 10 títulos de prueba) y la **comprobación de pegado en Jira**: las hace la persona; por eso AC3.1.2 queda diferido.
- `terraform plan` y el despliegue: sin cambios de infraestructura en u3.

## Desviaciones y brechas

1. **Brecha de u2, resuelta tras la revisión:** `evaluation.py` (el comando `evaluate_models`) exigía que el texto del modelo empezara con "Como analista de negocio", y con las instrucciones nuevas, que piden JSON, `format_ok` habría salido falso en una evaluación real. Se escribieron primero dos pruebas en rojo y luego `check_format` pasó a aceptar el JSON que el servicio acepta (usa el mismo análisis de u3) y a mantener la comprobación anterior como respaldo; la suite quedó en 358 pruebas en verde con 99,65 %.
2. `NEEDS_CONTEXT` no estaba en el enumerado de errores del código; se agregó (ya estaba en C1).
3. El comando local ahora comprueba que haya una línea que empieza con "Como analista de negocio" y la línea `# language: es`, porque el Markdown empieza con el encabezado del título (BR3.9).
4. La heurística de idioma (al menos 2 palabras comunes del español en la acción y el beneficio) puede rechazar una respuesta real muy corta en español; se confirma con la revisión manual.
5. Una prueba de u2 sobre el tiempo de espera (`test_bedrock_client.py`) falló una vez por carga de la máquina y pasó al repetirla; es sensible al tiempo.
6. Pendientes de la persona: aprobar los títulos de `docs/titulos-prueba-nfr2.md` y confirmar el umbral de contexto.
