# Observability Design — u4-access-control

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa. Sin alarmas en el MVP (decisión confirmada en u1).

u4 no define métricas nuevas: aporta valores a las que ya emite el servicio de u1.

## Aporte de u4

| Dato | Dónde se registra | Requisito |
|------|-------------------|-----------|
| Resultado de la verificación: `ok` o un motivo de lista cerrada (missing, malformed, bad_signature, wrong_issuer, wrong_audience, expired, wrong_token_use, keys_unavailable, not_configured, account_not_allowed, unknown) | Campo `authOutcome` del registro por solicitud (lista cerrada de u1) | NFR4.5 |
| Duración de la verificación | Campo `authDurationMs` del registro por solicitud | NFR1.9 |
| Rechazo de sesión por código | `errors_total` con el código SESSION_INVALID o ACCOUNT_NOT_ALLOWED, con la dimensión `code` de u1 | NFR4.6 |

`keys_unavailable` y `not_configured` son visibles como motivos distintos: indican un problema de despliegue o del proveedor, no del uso (NFR4.7).

## Qué no se registra

Ni el token, ni el correo, ni el `sub`, ni la lista de correos. Una prueba captura todos los registros de un caso feliz y de cada motivo de rechazo y busca esos valores (NFR4.2).

## Cambio coordinado de las listas cerradas de u1

Al inicio de Code Generation de u4, el desarrollador de u4 agrega a las listas cerradas de u1 los campos de registro `authOutcome` y `authDurationMs`, el código ACCOUNT_NOT_ALLOWED y el motivo `unknown` de `SessionInvalid`, modificando el código de u1 en su sitio y volviendo a ejecutar las pruebas de u1 y de las unidades ya hechas (deben seguir en verde). Son solo campos y valores del registro: no hay métricas ni filtros de Terraform nuevos.

## Assumptions & Open Questions

- Supuesto: se consulta en los registros de CloudWatch; no hay panel propio ni trazas.
