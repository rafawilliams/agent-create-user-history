# Monitoring Design — u4-access-control

Documentos de entrada: `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. u4 no agrega recursos de monitoreo propios: implementa lo de `observability-design.md` sobre el monitoreo de u1. Sin alarmas en el MVP (decisión confirmada en u1).

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|--------|--------|-----------|----------------|
| `requests_total` | Servicio (u1); u4 no agrega | Sin umbral en el MVP | Uso |
| `errors_total` por `code` | Servicio (u1); u4 aporta SESSION_INVALID y ACCOUNT_NOT_ALLOWED | Referencia: ACCOUNT_NOT_ALLOWED mayor que 0 revisa la lista de correos; SESSION_INVALID sostenido con personas conocidas revisa el despliegue | Distingue falta de sesión de cuenta no permitida (NFR4.6) |
| `authOutcome` | Campo del registro por solicitud | Referencia: `keys_unavailable` o `not_configured` mayor que 0 se revisa de inmediato | Problema del proveedor o del despliegue, no del uso (NFR4.7) |
| `authDurationMs` | Campo del registro por solicitud | Referencia: menor de 20 ms con claves en memoria; hasta 3 000 ms en una descarga de claves | Parte del plazo que consume la verificación (NFR1.9) |
| Métricas nativas de Cognito | Servicio de Cognito en CloudWatch | Sin umbral | Inicios de sesión y errores del proveedor |

## Alerts

| Alert | Condition | Severity | Routes to |
|-------|-----------|----------|-----------|
| Ninguna en el MVP | Sin alarmas | n/a | n/a |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|-----|------------|--------------------|
| Sin SLO en el MVP (decisión confirmada) | Ninguno | n/a |

Condición para definirlo: la de u1 (antes de ofrecer el servicio a más de 5 personas o pasado un mes en uso).

## Logs & Tracing

- Un registro por solicitud con los campos de la lista cerrada de u1 más `authOutcome` y `authDurationMs`; nunca el token, el correo, el `sub` ni la lista de correos (NFR4.2).
- Los registros de Cognito de la cuenta se consultan en CloudWatch; sin trazas ni panel propio.

## Assumptions & Open Questions

- Decidido: los campos nuevos de registro los agrega el desarrollador de u4 a la lista cerrada de u1 al inicio de Code Generation, volviendo a ejecutar las pruebas de u1, u2 y u3 (deben seguir en verde).
