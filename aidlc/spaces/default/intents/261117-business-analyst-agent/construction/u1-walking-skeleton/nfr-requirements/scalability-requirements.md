# Scalability Requirements — u1-walking-skeleton

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (NR Qn).

Cada requisito hereda el ID de Inception y le agrega un subnúmero.

| ID | Requisito | Medida | Fuente |
|----|-----------|--------|--------|
| NFR3.1 | El esqueleto atiende al menos 5 solicitudes simultáneas sin errores atribuibles al servicio | 5 solicitudes simultáneas completadas, o rechazadas por el límite de uso, sin errores del servicio | `requirements.md` NFR3 (hasta 5 personas con uso ocasional) |
| NFR3.3 | El número de solicitudes se mide, para vigilar el uso frente al límite de 20 por persona por día | Una métrica de conteo de solicitudes, sin contenido | NR Q2 y Q4 |

## Proyecciones de carga

- Usuarios: hasta 5 personas, con uso ocasional (`requirements.md`, NFR3).
- Volumen máximo por persona: 20 solicitudes por día (NFR3.2 en `security-requirements.md`).
- Crecimiento: no hay proyección; el MVP no prevé más de 5 personas.

## Estrategia de escalado

El esqueleto no necesita una estrategia de escalado más allá de atender las solicitudes simultáneas del MVP. El servicio no guarda estado entre solicitudes (`entities.md`), así que varias solicitudes se pueden atender a la vez sin coordinación. El escalado horizontal y la capacidad se revisan si el uso crece más allá de 5 personas.

## Assumptions & Open Questions

- Supuesto: la concurrencia de 5 solicitudes simultáneas es un máximo de diseño, no un valor medido.
- Abierto: límites de concurrencia por servicio de AWS (por ejemplo, del modelo), que se verifican en `u6-infrastructure` y `u2-model-gateway`.
