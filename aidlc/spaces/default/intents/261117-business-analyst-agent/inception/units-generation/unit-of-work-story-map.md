# Unit of Work Story Map — Business Analyst Agent

Documentos de entrada: `components.md`, `decisions.md`, `requirements.md` y `stories.md`. Unidades: `unit-of-work.md`. Dependencias: `unit-of-work-dependency.md`.

Una fila por historia. Cada unidad que aparece en una fila implementa parte de esa historia.

| Story | Units | Directories |
|-------|-------|-------------|
| US1.1 | U3; U5 | u3-story-generator; u5-web-app |
| US2.1 | U1; U3 | u1-walking-skeleton; u3-story-generator |
| US3.1 | U3 | u3-story-generator |
| US4.1 | U5; U3 | u5-web-app; u3-story-generator |
| US5.1 | U5; U3; U2 | u5-web-app; u3-story-generator; u2-model-gateway |
| US6.1 | U4; U5; U6 | u4-access-control; u5-web-app; u6-infrastructure |
| US7.1 | U2; U6 | u2-model-gateway; u6-infrastructure |

La unidad que cada fila nombra primero es la unidad principal de esa historia (se usa como destino en `traceability.json`).

## Filas que abarcan varias unidades

- US1.1: la validación del título vive en U3 (fuente de verdad) y U5 (ayuda en pantalla).
- US2.1: U1 aporta la versión mínima de la generación y U3 la completa.
- US4.1: U3 arma el Markdown y U5 lo muestra y lo copia (ADR-005).
- US5.1: U5 muestra los estados, U3 impone el tiempo máximo y U2 traduce los fallos del modelo.
- US6.1: U4 gestiona la sesión, U5 muestra el acceso y U6 configura los permisos de los proveedores de identidad.
- US7.1: U2 ejecuta la evaluación de modelos y U6 da los permisos para llamar al modelo desde la cuenta de AWS.

## Orden de implementación dentro de cada unidad

- U1: pantalla mínima, servicio mínimo y llamada al modelo, de punta a punta.
- U2: configuración del modelo; llamada y traducción de errores; evaluación de Titan frente a Claude Sonnet.
- U3: reglas de entrada y de título ambiguo; armado de la petición y del Markdown; manejo de respuestas inválidas y del tiempo máximo.
- U4: verificación de sesión; inicio y cierre de sesión.
- U5: pantalla de acceso; pantalla principal con sus estados; pestañas y copiado; accesibilidad y móvil.
- U6: infraestructura de los dos despliegues; permisos; despliegue automático y prueba de humo.

## Verificación de cobertura

- Las 7 historias (US1.1 a US7.1) tienen al menos una unidad.
- Las 6 unidades (U1 a U6) tienen al menos una fila.
- Los requisitos no funcionales NFR3 a NFR8 se difieren a la etapa de requisitos no funcionales, como indica `traceability.json` de User Stories; no tienen fila propia aquí.

## Assumptions & Open Questions

- Supuesto: U6 aparece en US6.1 y US7.1 porque aporta los permisos de identidad y de acceso al modelo; si se prefiere que la infraestructura no figure en historias, se ajusta en el gate.
- Abierto: qué unidad es dueña de la configuración del prompt (ADR-003); se asigna a U3 por ahora.
