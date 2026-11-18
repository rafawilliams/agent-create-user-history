# Phase Check — Inception a Construction

**Veredicto: PASS** (cobertura de trazabilidad).

Se leyeron las tres tablas de trazabilidad de las etapas de Inception que las producen y no queda ningún hallazgo de cobertura: no hay filas `GAP`, no hay `ORPHAN`, no hay destinos inválidos ni identificadores de origen sin cubrir. Contract Design no produce tabla de trazabilidad (define contratos, no cobertura de requisitos), así que no entra en esta comprobación.

## Resumen por etapa

| Etapa | Tabla | Identificadores de origen | OK | Deferred | N/A | GAP | ORPHAN |
|-------|-------|---------------------------|----|----------|-----|-----|--------|
| user-stories | `inception/user-stories/traceability.json` | 28 (FR y NFR de `requirements.md`) | 22 | 6 | 0 | 0 | 0 |
| domain-design | `inception/domain-design/traceability.json` | 7 (US1.1 a US7.1) | 7 | 0 | 0 | 0 | 0 |
| units-generation | `inception/units-generation/traceability.json` | 7 (US1.1 a US7.1) | 7 | 0 | 0 | 0 | 0 |

## Requisitos diferidos

NFR3, NFR4, NFR5, NFR6, NFR7 y NFR8 están diferidos a la etapa de requisitos no funcionales (`nfr-requirements`), que sigue en el plan y es etapa de Construcción. Quedan cubiertos allí; ningún requisito queda sin dueño.

## Coherencia entre las tablas

- Las 7 historias (US1.1 a US7.1) aparecen en las tres tablas y apuntan a destinos existentes: componentes de `components.md` en domain-design y unidades de `unit-of-work.md` en units-generation.
- Los 22 requisitos cubiertos en user-stories trazan a una historia de `stories.md`.

## Riesgos aceptados al aprobar etapas con revisión abierta

Estos puntos no son hallazgos de cobertura, pero la persona los aceptó como riesgo al aprobar cada etapa y conviene tenerlos presentes antes de construir:

- **Units Generation:** el mapa de dependencias dice que U2 a U6 solo dependen de U1, pero U3 usa a U2 y a U4 y U5 usa a U3 y a U4. La revisión lo calificó como crítico. Este riesgo se sostiene solo si U1 entrega las interfaces C3 y C4, un modelo simulado y un servicio simulado con la forma de C1 (`contract-summary.md`, Reglas de propiedad); las unidades aprobadas no los listan todavía como entregables de U1. B1 de `bolt-plan.md` los incluye en su Definition of Done.
- **Units Generation:** U2, U3 y U5 amplían los mismos componentes mínimos de U1; por eso las Bolts se construyen una tras otra (`bolt-plan.md`, DP Q4).
- **Contract Design:** falta una consideración de seguridad para la credencial de la sesión y C2 está incompleto (no define cómo se obtiene la credencial).
- **Refined Mockups:** la revisión salió NOT-READY: el mapeo a MUI bloquea la escritura a 200 caracteres, mientras los mockups y AC1.1.2 muestran el error con 231 caracteres; solo hay un mockup móvil; el tamaño táctil de 44 por 44 píxeles no es un requisito confirmado.

## Assumptions & Open Questions

- Supuesto: las tablas se consolidaron a partir de los archivos de trazabilidad tal como están escritos; no se re-ejecutó la comprobación automática de cada etapa en este paso.
- Abierto: si se corrigen los riesgos aceptados antes de construir o durante la Bolt B1.
