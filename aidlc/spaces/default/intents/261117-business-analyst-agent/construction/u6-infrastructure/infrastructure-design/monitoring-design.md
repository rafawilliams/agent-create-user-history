# Monitoring Design — u6-infrastructure

Documentos de entrada: `security-design.md`, `infrastructure-specification.md` y `contract-summary.md`. No hubo preguntas en esta etapa: la persona ya confirmó en u1 que el MVP no lleva objetivos de nivel de servicio ni alarmas.

## Sources

- [scope] Decisión de u1 (sin objetivos ni alarmas en el MVP); NFR4.2 (retención de 14 días, sin registro de invocaciones ni de acceso).

## Metrics & KPIs

| Métrica | Fuente | Uso |
|---------|--------|-----|
| `requests_total`, `errors_total` y `generation_duration_ms` | Filtros de métricas de los registros de la función (ya existen) | Se consultan a mano en la consola |
| Solicitudes y errores 4xx y 5xx de la distribución | Métricas estándar de CloudFront | Consulta a mano |
| Resultado de cada despliegue y de la prueba de humo | Registro del flujo `deploy.yml` en GitHub Actions | Un despliegue fallido deja el flujo en rojo y GitHub avisa por correo a quien lo lanzó |

## Alerts

Ninguna alarma de AWS en el MVP, por decisión confirmada en u1. El aviso de un flujo fallido de GitHub Actions es el único aviso de la canalización.

## SLIs / SLOs

Sin objetivos de nivel de servicio en el MVP; la disponibilidad es la de los servicios administrados de AWS.

## Logs & Tracing

Registros solo de la función, con retención de 14 días y la lista cerrada de campos de u1 (sin títulos, historias, token, correo ni `sub`). Sin registro de invocaciones de Bedrock, sin registros de acceso de la distribución ni del depósito de la pantalla, y sin rastreo distribuido. Los registros de los flujos de GitHub Actions no imprimen valores sensibles (solo el resumen del plan).

## Assumptions & Open Questions

- Supuesto: con 5 personas y uso ocasional basta consultar las métricas a mano.
- Abierto: un presupuesto de costos con aviso (AWS Budgets) queda fuera del MVP; la persona puede agregarlo después.
