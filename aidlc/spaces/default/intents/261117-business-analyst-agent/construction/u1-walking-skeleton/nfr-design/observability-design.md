# Observability Design — u1-walking-skeleton

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. Respuestas: `nfr-design-questions.md` (ND Qn).

## Métricas (NFR3.3, NFR1.4, NFR4.5)

| Métrica | Tipo | Dimensiones | Requisito |
|---------|------|-------------|-----------|
| `requests_total` | Conteo | Ninguna | NFR3.3 |
| `errors_total` | Conteo | `code` (TITLE_EMPTY, TITLE_TOO_LONG, NEEDS_CONTEXT, SESSION_INVALID, RATE_LIMITED, MODEL_FAILURE, INVALID_MODEL_RESPONSE, GENERATION_TIMEOUT) | NFR4.5 |
| `generation_duration_ms` | Medida de tiempo | `model_id` | NFR1.4 |

Alcance: estas métricas cuentan solo las solicitudes que llegan al código del servicio. Los rechazos RATE_LIMITED de la pasarela y del tope de concurrencia ocurren antes y se vigilan con las métricas de la pasarela y de la plataforma (ver `scalability-design.md`); el código RATE_LIMITED aparece en `errors_total` solo si el servicio mismo lo emite.

Las métricas no tienen dimensiones con datos de la persona ni del contenido. Cumplen la guía de operación: una métrica de salud (`requests_total` y `generation_duration_ms`) y una de tasa de error (`errors_total`) por cada componente nuevo. Los nombres son una propuesta de esta etapa.

## Registros estructurados (NFR4.2, NFR4.3)

Un registro por solicitud, en formato estructurado, con una lista cerrada de campos:

| Campo | Contenido |
|-------|-----------|
| `requestId` | Identificador aleatorio de la solicitud, sin datos personales |
| `outcome` | `ok` o el código de error |
| `durationMs` | Duración total de la solicitud |
| `modelId` | Identificador del modelo usado |

Ningún campo contiene el título, el contexto, el Markdown, la credencial ni la cabecera `Authorization`.

## Correlación

El `requestId` se genera al recibir la solicitud, se devuelve en la respuesta (contrato C1) y se incluye en el registro; la persona puede dar ese identificador para buscar una solicitud concreta sin exponer su contenido.

## Alarmas

Sin alarmas en el MVP (ND/NR Q2 de `nfr-requirements-questions.md`). Los umbrales de una alarma futura deben quedar por debajo del SLO, que hoy no existe (`reliability-design.md`). Una alarma sobre la tasa de errores es lo primero que conviene agregar antes de ampliar el uso.

## Trazas y paneles

- Trazas distribuidas: no se diseñan; hay un solo servicio por solicitud.
- Panel: no se diseña un panel propio; las métricas se consultan en la herramienta de monitoreo de AWS.

## Qué se verifica

- Una prueba automática comprueba que ningún registro contiene el título, el Markdown ni una credencial (NFR4.2, NFR4.3).
- El registro de invocaciones del modelo en AWS se comprueba desactivado en `u6-infrastructure`.

## Assumptions & Open Questions

- Supuesto: las métricas se emiten desde el servicio al monitoreo de AWS sin registrar contenido.
- Abierto: los nombres definitivos de las métricas y su espacio de nombres.
