# Observability Requirements — u1-walking-skeleton

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (NR Qn).

Cada requisito hereda el ID de Inception y le agrega un subnúmero.

## Qué se mide (NR Q2)

| ID | Métrica | Tipo | Fuente |
|----|---------|------|--------|
| NFR3.3 | Número de solicitudes de generación | Conteo | `scalability-requirements.md`; NR Q2 |
| NFR4.5 | Errores por código (TITLE_EMPTY, TITLE_TOO_LONG, SESSION_INVALID, MODEL_FAILURE, INVALID_MODEL_RESPONSE, GENERATION_TIMEOUT) | Conteo por código | NR Q2; `contract-summary.md` (C1) |
| NFR1.4 | Duración de cada generación | Medida de tiempo | `performance-requirements.md`; NR Q2 |

Cumplen la guía de operación de tener al menos una métrica de salud (número de solicitudes y duración) y una de tasa de error (errores por código) por cada componente nuevo.

## Registros (logs)

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR4.2 | Los registros contienen solo errores y métricas, sin el contenido de los títulos ni de las historias; el registro de invocaciones del modelo queda sin contenido | `requirements.md` NFR4; NR Q2 |
| NFR4.3 | No se registran credenciales ni la cabecera `Authorization`; el `requestId` no lleva datos personales | `contract-summary.md` |

Formato: un registro por solicitud, con el `requestId`, el código del resultado (éxito o código de error) y la duración. Sin el título, sin el Markdown generado y sin credenciales.

## Alarmas

Sin alarmas en el MVP (NR Q2). El resultado esperado de esta decisión es que los fallos se descubran al revisar las métricas o por el reporte de las personas; conviene agregar una alarma sobre la tasa de error antes de ampliar el uso. Los umbrales de alarma, cuando se definan, deben quedar por debajo del SLO (guía de operación), que hoy no existe (`reliability-requirements.md`).

## Trazas y paneles

- Trazas distribuidas: no se requieren en el MVP; la solicitud pasa por un solo servicio.
- Panel: no se requiere un panel; las métricas se consultan en la herramienta de monitoreo de AWS.

## Assumptions & Open Questions

- Supuesto: las métricas se pueden obtener sin registrar contenido con los servicios de monitoreo de AWS; se confirma en `u6-infrastructure`.
- Abierto: el nombre y las dimensiones exactas de cada métrica (se definen en NFR Design).
