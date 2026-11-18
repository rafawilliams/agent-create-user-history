# Observability Requirements — u4-access-control

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa. Sin alarmas en el MVP (decisión confirmada en u1).

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR4.5 | Cada verificación aporta al registro de la solicitud un resultado de lista cerrada: `ok` o uno de los motivos de `SessionInvalid` (missing, malformed, bad_signature, wrong_issuer, wrong_audience, expired, wrong_token_use, keys_unavailable, not_configured, account_not_allowed, unknown; `unknown` se agrega a la lista cerrada de motivos de `SessionInvalid` en el cambio coordinado de C3) | Una prueba recorre cada motivo y comprueba que el registro lleva solo ese valor | `rules.md` BR4.8; `entities.md` |
| NFR4.6 | Los rechazos de sesión cuentan en la métrica de errores por código del servicio (SESSION_INVALID y ACCOUNT_NOT_ALLOWED), para distinguir un uso sin sesión de una cuenta no permitida | Una prueba comprueba que cada rechazo incrementa `errors_total` con su código | `requirements.md` NFR4; observabilidad de u1 |
| NFR1.9 | La duración de la verificación se registra aparte (`authDurationMs`) para ver cuánto del plazo consume | Una prueba comprueba que el registro incluye `authDurationMs` | `requirements.md` NFR1 |
| NFR4.7 | `keys_unavailable` y `not_configured` son visibles en los registros como motivos distintos, porque indican un problema de despliegue y no del uso | Una prueba comprueba que el registro distingue esos dos motivos de los demás | `rules.md` BR4.5 |

## Assumptions & Open Questions

- Supuesto: las métricas y los registros los emite el servicio de u1; u4 aporta los valores.
- Abierto: agregar `authDurationMs` y los motivos a las listas cerradas de registro y de códigos de u1 es un cambio coordinado del desarrollador de u4 al inicio de su Code Generation.
