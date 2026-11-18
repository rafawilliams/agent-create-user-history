# Scope Document — Business Analyst Agent

Documentos de entrada: `intent-statement.md`, `feasibility-assessment.md` y `constraint-register.md`.

Claves de fuente: **SD Qn** = respuesta n de `scope-definition-questions.md`; **FE Qn** = respuesta n de `feasibility-questions.md`; **IS** = `intent-statement.md`; **CR** = `constraint-register.md`.

## Objetivo del MVP

Que un analista de negocio escriba el título de una funcionalidad y obtenga una historia de usuario con sus criterios de aceptación en Gherkin, en español y en Markdown listo para pegar en Jira. Fuente: IS (Problem Statement) y descripción inicial.

Meta de aceptación: menos de 1 minuto por historia y Gherkin válido a la primera en al menos 80% de los títulos de prueba, revisados a mano. Fuente: SD Q5, que concreta las dos métricas de IS (Success Metrics). Esto reemplaza la ausencia de umbral que quedó abierta en IS.

## Dentro del alcance (MVP)

| Capacidad | Prioridad | Fuente |
|-----------|-----------|--------|
| Generar la historia de usuario y sus criterios de aceptación en Gherkin a partir del título, en español | Must have | Descripción inicial; IS |
| Usar un rol genérico fijo en la historia (por ejemplo, "usuario") | Must have | SD Q10 |
| Pedir más contexto al analista cuando el título es muy corto o ambiguo | Must have | SD Q4 |
| Entregar el resultado en Markdown listo para Jira | Must have | Descripción inicial |
| Pantalla donde el analista escribe el título, ve la historia generada y copia el Markdown con un botón | Must have | SD Q2 |
| Acceso mediante inicio de sesión con Gmail u Outlook | Must have (restricción) | FE Q4; CR C6 |
| Habilitar el modelo de IA y evaluar Amazon Titan y Claude Sonnet antes de decidir cuál usar | Must have (condición previa) | FE Q9, FE Q10; CR C2, C3 |

## Fuera del alcance de la primera versión

| Elemento | Fuente |
|----------|--------|
| Validación automática del formato Gherkin (y regeneración si es inválido) | SD Q1, SD Q9 |
| Determinación automática del rol | SD Q1, SD Q10 |
| Procesar varias funcionalidades a la vez | IS (Initial Scope Signal) |
| Persistencia de datos (DynamoDB) | IS (Initial Scope Signal); CR C5 |
| Integraciones con otros sistemas, incluido Jira | FE Q3; CR C4 |

## Cambios respecto de la descripción inicial

La descripción inicial pedía determinar el rol automáticamente y validar el formato Gherkin. Por decisión confirmada, ambas capacidades quedan para una segunda versión (SD Q1, SD Q9, SD Q10). Consecuencias:

- El Gherkin se muestra tal como lo genera el modelo; su validez se comprueba a mano durante la evaluación (SD Q5, SD Q9).
- La respuesta de SD Q3 (regenerar si el Gherkin es inválido) no aplica a esta versión, porque depende de la validación automática (SD Q9).
- La historia usa un rol genérico fijo, así que no refleja el rol real de cada funcionalidad (SD Q10).

## Secuencia preferida

Riesgo primero: habilitar el modelo y evaluar Amazon Titan y Claude Sonnet antes de construir la interfaz. Fuente: SD Q7. El orden de las piezas está en `intent-backlog.md`.

## Fechas

Demostración del MVP en dos semanas. Fuente: SD Q8, SD Q11. No se indicó una fecha por capacidad.

## Agente actual de Excel

Se mantiene en uso hasta que el nuevo MVP sea aceptado. Fuente: SD Q6. El reemplazo final del agente actual es lo indicado en IS (Initial Scope Signal); la fecha de su retiro no está definida.

## Assumptions & Open Questions

- Hipótesis: el alcance del MVP puede no caber en dos semanas, porque el modelo aún no está habilitado (FE Q10), el equipo tiene perfil principalmente Python (FE Q6) y se evalúan dos modelos antes de construir (SD Q7). Se valida al planificar la entrega.
- Abierto: fecha exacta de la demostración; solo se indicó "en dos semanas" (SD Q11).
- Abierto: cuándo se retira el agente actual de Excel una vez aceptado el MVP (SD Q6).
- Abierto: cómo se pide más contexto al analista en la pantalla y cuántas veces puede repetirse (SD Q4).
- Abierto: regla de quién puede iniciar sesión con Gmail u Outlook (FE Q4; `raid-log.md`, D2).
