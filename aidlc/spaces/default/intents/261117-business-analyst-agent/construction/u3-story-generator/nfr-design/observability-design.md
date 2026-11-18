# Observability Design — u3-story-generator

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa. Sin alarmas en el MVP (decisión confirmada en u1).

u3 no define métricas nuevas: aporta valores a las que ya emite el servicio de u1 (`requests_total`, `errors_total` con el código y `generation_duration_ms`).

## Aporte de u3

| Dato | Dónde se registra | Requisito |
|------|-------------------|-----------|
| Código de resultado (`outcome`): `ok` o un código de C1 (TITLE_EMPTY, TITLE_TOO_LONG, CONTEXT_TOO_LONG, NEEDS_CONTEXT, SESSION_INVALID, MODEL_FAILURE, INVALID_MODEL_RESPONSE, GENERATION_TIMEOUT) | Campo `outcome` del registro por solicitud de u1 y dimensión `code` de `errors_total` | NFR4.7, NFR4.8 |
| Duración de la lógica de u3 | Campo nuevo `u3DurationMs` de la lista cerrada del registro de u1 | NFR1.10 |

Los rechazos de validación y de petición de contexto incrementan `errors_total` con su código, para distinguir un uso incorrecto de un fallo del modelo.

## Qué no se registra

El título, el contexto, la respuesta del modelo y el Markdown nunca se registran, ni siquiera en un error. Una prueba lo comprueba capturando todos los registros.

## Trazas y paneles

No se diseñan trazas ni un panel propio; se usa el monitoreo de AWS de u1 y u6.

## Assumptions & Open Questions

- Cambio coordinado de u1 (aditivo), con dueño: u3 agrega `u3DurationMs` a la lista cerrada de campos de registro y `CONTEXT_TOO_LONG` a la lista de códigos de C1 que u1 ya implementa. Lo hace el desarrollador de u3 al inicio de su Code Generation, antes de escribir código que los use, modificando el código de u1 en su sitio y volviendo a ejecutar sus pruebas (que deben seguir en verde); el nombre del campo queda fijado como `u3DurationMs`. El mismo cambio agrega a la lista cerrada de campos el campo booleano `internal_error` (verdadero solo cuando el manejador de errores internos de `reliability-design.md` actúa).
