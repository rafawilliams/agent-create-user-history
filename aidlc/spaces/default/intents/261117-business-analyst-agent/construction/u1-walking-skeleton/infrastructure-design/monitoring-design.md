# Monitoring Design — u1-walking-skeleton

Implementa `nfr-design/observability-design.md` sobre CloudWatch. Sin alarmas en el MVP (NR Q2): la tabla de alertas lista solo lo que se agrega primero cuando se amplíe el uso.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|--------|--------|-----------|----------------|
| `requests_total` | Función (métrica personalizada, sin dimensiones) | Sin umbral en el MVP | Mide el uso (NFR3.3) |
| `errors_total` por `code` | Función | Sin umbral en el MVP | Distingue fallos por código (NFR4.5) |
| `generation_duration_ms` por `model_id` | Función | Referencia: p95 por debajo de 40 000 ms (valor inicial, a ajustar con mediciones reales; el límite duro es 55 000 ms) | Verifica el presupuesto de tiempo (NFR1.4) |
| Solicitudes limitadas (429) | Métricas de la pasarela | Referencia: más de 0 en un día normal | Rechazos antes del código (`scalability-design.md`) |
| Limitaciones de la función (throttles) | Métricas de la función | Referencia: más de 0 en un día normal | Tope de concurrencia de 5 |
| Invocaciones del modelo | Métricas de Bedrock | Sin umbral | Vigila el costo |
| Errores 5XX de la pasarela | Métricas de la pasarela | Referencia: más de 0 en un día normal | Tasa de error del punto de entrada |
| Errores y duración de la función | Métricas nativas de la función | Referencia: errores mayores que 0 en un día normal | Salud y errores de la función, además de las propias |
| Errores 5XX de la distribución | Métricas de CloudFront | Referencia: más de 0 en un día normal | Salud de la pantalla |

## Alerts

| Alert | Condition | Severity | Routes to |
|-------|-----------|----------|-----------|
| Ninguna en el MVP (NR Q2) | Sin alarmas | n/a | n/a |
| Candidata inicial futura: tasa de errores | `errors_total` supera el umbral por debajo del SLO que se defina | A definir | A definir |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|-----|------------|--------------------|
| Sin SLO en el MVP (NR Q1) | Ninguno | n/a |

Condición para definirlo: antes de ofrecer el servicio a más de 5 personas, o pasado un mes en uso (`reliability-design.md`).

## Logs & Tracing

- Un registro estructurado por solicitud con los campos `requestId`, `outcome`, `durationMs`, `modelId`; nada de contenido ni de la cabecera `Authorization` (NFR4.2, NFR4.3).
- Retención de 14 días en CloudWatch (propuesta).
- Registro de la pasarela: solo estado y duración, sin cuerpos de solicitud ni de respuesta.
- Registro de invocaciones del modelo: desactivado y verificado como tal (ver `cicd-pipeline.md`).
- Sin trazas distribuidas ni panel propio; se consulta CloudWatch directamente.

## Assumptions & Open Questions

- Supuesto: las métricas personalizadas se publican desde la función en un espacio de nombres propio.
- Abierto: nombres definitivos de métricas y espacio de nombres.
