# Monitoring Design — u3-story-generator

Documentos de entrada: `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. u3 no tiene recursos propios: implementa lo de `observability-design.md` sobre el monitoreo de u1. Sin alarmas en el MVP (decisión confirmada en u1).

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|--------|--------|-----------|----------------|
| `requests_total` | Servicio (u1); u3 no agrega | Sin umbral en el MVP | Uso (NFR3) |
| `errors_total` por `code` | Servicio (u1); u3 aporta TITLE_EMPTY, TITLE_TOO_LONG, CONTEXT_TOO_LONG, NEEDS_CONTEXT e INVALID_MODEL_RESPONSE | Referencia: INVALID_MODEL_RESPONSE mayor que 0 en un día normal revisa las instrucciones | Distingue uso incorrecto de fallo del modelo (NFR4.8) |
| `generation_duration_ms` | Servicio (u1) | Referencia: p95 menor de 40 000 ms | Presupuesto de tiempo (NFR1.1) |
| `u3DurationMs` | Campo del registro por solicitud | Referencia: menor de 50 ms | Parte del plazo que consume u3 (NFR1.10) |
| `internal_error` | Campo del registro por solicitud | Referencia: cualquier valor verdadero se revisa | Distingue un defecto de u3 de un fallo del modelo |

## Alerts

| Alert | Condition | Severity | Routes to |
|-------|-----------|----------|-----------|
| Ninguna en el MVP | Sin alarmas | n/a | n/a |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|-----|------------|--------------------|
| Sin SLO en el MVP (decisión confirmada) | Ninguno | n/a |

La condición para definirlo es la de u1: antes de ofrecer el servicio a más de 5 personas o pasado un mes en uso.

## Logs & Tracing

- Un registro por solicitud con los campos de la lista cerrada de u1, más `u3DurationMs` y `internal_error`; nunca el título, el contexto, la respuesta del modelo ni el Markdown (NFR4.2).
- Sin trazas distribuidas ni panel propio.

## Assumptions & Open Questions

- Decidido: los dos campos nuevos (`u3DurationMs` e `internal_error`) y el código `CONTEXT_TOO_LONG` son solo campos del registro, sin métricas ni filtros nuevos de Terraform. Los agrega el desarrollador de u3 a la lista cerrada de u1 al inicio de su Code Generation y vuelve a ejecutar las pruebas de u1 (deben seguir en verde).
