# Infrastructure Specification — u3-story-generator

Documentos de entrada: `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: u3 es código dentro de la función de generación de `u1-walking-skeleton`, así que no agrega recursos de AWS propios; este documento dice qué espera u3 de la infraestructura existente.

## Deployment

| Facet | Choice | Rationale |
|-------|--------|-----------|
| Modelo de cómputo | Dentro de la función de AWS Lambda de u1 (Python); sin función ni servicio nuevo | u3 forma parte del despliegue del servicio (`unit-of-work.md`) |
| Entrada de la API | La pasarela REST de u1; u3 agrega el código `CONTEXT_TOO_LONG` (400) y reusa NEEDS_CONTEXT (422) de C1 | Cambio aditivo de contrato registrado en Code Generation de u3 |
| Red | Sin cambios | u3 no habla con AWS ni con otro servicio |
| Almacenamiento | Ninguno (NFR4.1) | Sin persistencia |
| Entornos | Uno solo, al integrar en `main` | Práctica del equipo |
| IaC | Sin cambios de Terraform: los campos nuevos (`u3DurationMs`, `internal_error`) y el código `CONTEXT_TOO_LONG` son solo campos y valores del registro por solicitud, que se consultan en los registros de CloudWatch; no hay métricas ni filtros nuevos. `STORY_INSTRUCTIONS` es opcional y su valor por defecto está en el código; si `u6-infrastructure` la pasa por Terraform, lo decide allí | ADR-003: las instrucciones viven en configuración |
| Código de error nuevo en la pasarela | `CONTEXT_TOO_LONG` (400) lo devuelve la función con el cuerpo de error de C1, igual que TITLE_*; la pasarela no lo interpreta; la política de CORS de u1 ya cubre las respuestas de la función | Cambio aditivo de C1 |
| Riesgo de la prueba de humo | La prueba de humo de u1 solo ejercita SESSION_INVALID y no pasa por u3; la generación de u3 se comprueba con el comando de punta a punta de u1 (a mano) hasta que exista el verificador real | Limitación aceptada y registrada |
| Dimensionado | Sin cambios: la lógica de u3 añade menos de 50 ms y su memoria es la de unos pocos kilobytes por solicitud; la función de u1 (512 MB, 57 s) la cubre | NFR1.2, NFR1.5 |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---------|------|---------------|-------|
| AWS Lambda (de u1) | Ejecuta u3 | La variable de entorno `STORY_INSTRUCTIONS` es opcional; sin ella se usan las instrucciones por defecto del código; la variable no contiene credenciales (NFR5.2) | Sin permisos nuevos: u3 no llama a AWS (NFR5.1) |
| API Gateway REST (de u1) | Entrada HTTPS y límite de tasa | Sin cambios; el tope de 5 ejecuciones y el límite de tasa de u1 y u6 cubren NFR3.1 y NFR3.2 | El tope de bytes del cuerpo no se asume: u3 valida sus propios límites de caracteres (NFR4.4) |
| CloudWatch (de u1) | Registros y métricas | El registro por solicitud gana los campos `u3DurationMs` y `internal_error` y el código `CONTEXT_TOO_LONG` (cambio coordinado de u1 hecho en Code Generation de u3) | NFR1.10, NFR4.2, NFR4.7, NFR4.8 |
| IAM (de u1) | Permisos de la función | Sin cambios | u3 no pide permisos |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|-----------------|------------|----------------|-----------------|
| Función de generación y pasarela REST | u1-walking-skeleton | u3-story-generator, u4-access-control | La función es una; u3 extiende su código, no crea otra |
| Registros y métricas de CloudWatch | u1-walking-skeleton | u3-story-generator | Solo los campos de la lista cerrada, sin contenido |

## Qué se puede verificar en AWS y qué no

Con el entorno desplegado sin verificador real (u1), el servicio rechaza toda solicitud con SESSION_INVALID; por eso la ruta de éxito de u3 de extremo a extremo solo se comprueba en local con el modelo real (comando de punta a punta de u1) y en AWS solo cuando exista el verificador de `u4-access-control`.

## Costo (orientativo, propuesta)

u3 no agrega costo de infraestructura; el costo variable sigue siendo el de las llamadas al modelo (acotado por el tope de 5 ejecuciones y el límite de tasa).

## Assumptions & Open Questions

- Supuesto: el nombre `STORY_INSTRUCTIONS` y el valor por defecto en el código bastan para el MVP; `u6-infrastructure` decide si la variable pasa por Terraform.
- Abierto: confirmar en `u6-infrastructure` si hay un tope de bytes del cuerpo en la pasarela.
