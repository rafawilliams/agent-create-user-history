# Monitoring Design — u5-web-app

Documentos de entrada: `performance-design.md`, `security-design.md`, `logical-components.md` y `infrastructure-specification.md`. No hubo preguntas en esta etapa: la persona ya confirmó en u1 que el MVP no lleva objetivos de nivel de servicio ni alarmas.

## Sources

- [scope] Decisión de u1 (sin objetivos ni alarmas en el MVP); `security-design.md` NFR4.2 (sin datos de la persona en registros).

## Metrics & KPIs

| Métrica | Fuente | Uso |
|---------|--------|-----|
| Solicitudes y tasa de errores 4xx y 5xx de la distribución | Métricas estándar de CloudFront | Se consultan a mano en la consola; sin panel propio |
| Tamaño de la carga inicial | `npm run check:bundle` en cada integración | Presupuesto de 400 KB (NFR1.3) |

## Alerts

Ninguna en el MVP, por decisión confirmada en u1.

## SLIs / SLOs

Sin objetivos de nivel de servicio en el MVP. La disponibilidad de la pantalla es la de CloudFront y S3.

## Logs & Tracing

La pantalla no envía telemetría: sin monitoreo de usuarios reales, sin rastreo ni registros en el navegador con datos (NFR4.2). La distribución no guarda registros de acceso. Los registros del servicio son los de u1.

## Assumptions & Open Questions

- Supuesto: con 5 personas y uso ocasional basta consultar las métricas estándar a mano.
- Abierto: monitoreo de usuarios reales y alarmas quedan después del MVP.
