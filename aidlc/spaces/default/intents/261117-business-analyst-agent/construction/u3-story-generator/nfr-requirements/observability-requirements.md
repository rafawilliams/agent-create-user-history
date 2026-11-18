# Observability Requirements — u3-story-generator

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa. Sin alarmas en el MVP (decisión confirmada en u1).

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR4.7 | u3 aporta al registro de la solicitud solo el código de resultado (`outcome`) con la lista cerrada de códigos de C1 (TITLE_EMPTY, TITLE_TOO_LONG, CONTEXT_TOO_LONG, NEEDS_CONTEXT, SESSION_INVALID, MODEL_FAILURE, INVALID_MODEL_RESPONSE, GENERATION_TIMEOUT), nunca contenido | Una prueba recorre cada resultado y comprueba que el registro lleva solo el código | `requirements.md` NFR4; `contract-summary.md` |
| NFR4.8 | Los rechazos de validación y de petición de contexto cuentan en la métrica de errores por código del servicio (`errors_total` con el código), para distinguir un uso incorrecto de un fallo del modelo | Una prueba comprueba que cada código de validación incrementa la métrica con su código | `requirements.md` NFR4; observabilidad de u1 |
| NFR1.10 | La duración de la lógica propia de u3 se registra aparte de la llamada al modelo, para ver qué parte del plazo consume | Una prueba comprueba que el registro de duración incluye la parte de u3 separada de la del modelo | `requirements.md` NFR1 |

## Assumptions & Open Questions

- Supuesto: las métricas y los registros los emite el servicio de u1; u3 solo aporta los valores.
- Abierto: los nombres definitivos de las métricas siguen siendo los de u1.
