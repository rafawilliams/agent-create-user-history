# Verificación de fase: Construcción → Operación

Intención: Business Analyst Agent (plan mvp). Documentos revisados: `construction/build-and-test/cross-unit-traceability.md`, `build-and-test-summary.md`, `test-results.md` y los `code-summary.md` y `traceability.json` de las seis unidades.

## Veredicto

**Con excepciones, aceptadas por la persona en Build and Test y presentadas de nuevo en la puerta de esta etapa.** La transición no es limpia: la puerta de trazabilidad entre unidades dio `fail` y quedan hallazgos sin resolver. Este documento no los oculta ni declara la fase como limpia.

## Qué se confirma

| Comprobación | Resultado |
|--------------|-----------|
| Las seis unidades construidas, revisadas y aprobadas | Sí: u1-walking-skeleton, u2-model-gateway, u3-story-generator, u4-access-control, u5-web-app y u6-infrastructure; u4 y u6 se reabrieron una vez por Build and Test y se aprobaron de nuevo |
| Todo lo ejecutable pasa | Sí: 563 pruebas del servicio (99,68 %), 186 de la pantalla (98,4 %), 97 afirmaciones de Terraform, 110 pruebas de scripts (97,65 %) |
| Las puertas de CI aplican los comandos de Build and Test | Sí, con una brecha declarada: las pruebas de los scripts de infraestructura están en un trabajo que no bloquea (Q1 de esta etapa) |
| Cada unidad tiene `traceability.json` | Sí |

## Qué no se cumple (hallazgos sin resolver)

| Hallazgo | Estado | Dueño |
|----------|--------|-------|
| Trazabilidad entre unidades: 10 elementos sin cubrir (`FR3.1`, `FR3.2`, `FR7.1`, `NFR2`, `NFR3`, `NFR5`, `NFR6`, `NFR8`, `AC3.1.2`, `AC7.1.2`) | `fail`. Cinco son pendientes reales de la persona (`AC3.1.2`, `FR3.1`, `FR3.2`, `NFR2` y `AC7.1.2` con `FR7.1`: revisión del Gherkin y evaluación de modelos con el modelo real); `NFR3` es el límite diario por persona (no construido, aceptado); `NFR5`, `NFR6` y `NFR8` son de contabilidad de la trazabilidad (existe cobertura y pruebas, pero el identificador de requisito se reutiliza con significados distintos entre unidades) | Persona y trazabilidad de las unidades |
| `NFR3.2`: límite de 20 solicitudes por persona y día | No cumplido, aceptado | Persona (decisión de requisito) |
| `NFR4.5`: tope de 8 KB frente a 16 KB en el código | No cumplido, aceptado; falta enmendar el requisito | Persona (decisión de requisito) |
| 27 objetivos sin verificar | Necesitan la cuenta de AWS, un navegador real o una revisión manual (Bedrock, Cognito con Google y Microsoft, despliegue, contraste, desbordamiento, lector de pantalla, Gherkin, Jira) | Persona |
| Hallazgos menores abiertos en los resúmenes de código | Registrados en cada `code-summary.md` (por ejemplo: el cierre de sesión mientras `DELETE` sigue pendiente, la edad de la copia de claves, la primera ejecución de Checkov) | Unidades correspondientes |

## Consecuencia

El proyecto no puede darse por listo para operar: falta, como mínimo, el arranque manual, el primer despliegue, las verificaciones de la lista anterior y la decisión sobre los dos requisitos no cumplidos. Esta fase termina con el trabajo construido y probado hasta donde se puede sin AWS, y con esas acciones en manos de la persona.
