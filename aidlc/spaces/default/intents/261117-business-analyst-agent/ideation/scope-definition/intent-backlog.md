# Intent Backlog — Business Analyst Agent

Documentos de entrada: `intent-statement.md`, `feasibility-assessment.md` y `constraint-register.md`. Alcance: `scope-document.md`.

Claves de fuente: **SD Qn** = `scope-definition-questions.md`; **FE Qn** = `feasibility-questions.md`.

Método de prioridad: MoSCoW. Orden de construcción: riesgo primero (SD Q7).

## Backlog priorizado (proto-unidades)

| Orden | ID | Elemento | MoSCoW | Fuente |
|-------|----|----------|--------|--------|
| 1 | B1 | Habilitar el modelo en Bedrock y evaluar Amazon Titan y Claude Sonnet con títulos de ejemplo | Must have | FE Q9, FE Q10, SD Q7 |
| 2 | B2 | Generar historia y criterios de aceptación en Gherkin a partir del título, en español, con rol genérico fijo | Must have | Descripción inicial; SD Q10 |
| 3 | B3 | Pedir más contexto cuando el título es muy corto o ambiguo | Must have | SD Q4 |
| 4 | B4 | Entregar el resultado en Markdown listo para Jira | Must have | Descripción inicial |
| 5 | B5 | Pantalla: escribir el título, ver la historia y copiar el Markdown con un botón | Must have | SD Q2 |
| 6 | B6 | Acceso con inicio de sesión de Gmail u Outlook | Must have (restricción) | FE Q4 |
| — | B7 | Validación automática del Gherkin y regeneración si es inválido | Won't have (this time) | SD Q1, SD Q9 |
| — | B8 | Determinación automática del rol | Won't have (this time) | SD Q1, SD Q10 |

El orden del 1 al 6 es una propuesta del análisis a partir de la secuencia de riesgo primero; la secuencia detallada se fija en Delivery Planning.

## Dependencias entre elementos

- B2, B3 y B4 dependen de que B1 haya definido el modelo a usar.
- B5 depende de B2 y B4, porque muestra y copia su resultado.
- B6 es independiente de B2 a B4, pero debe estar antes de publicar B5 a otras personas.

## Value stream map

```
Título de la funcionalidad
  -> [título ambiguo] pedir más contexto al analista (B3)
  -> generar historia + criterios Gherkin, en español (B2)
  -> dar formato Markdown listo para Jira (B4)
  -> mostrar en pantalla y copiar con un botón (B5)
  -> el analista pega el Markdown en Jira (paso manual; FE Q3)
```
<!-- Text fallback: el flujo va del título a una pregunta de contexto si es ambiguo, luego a la generación de la historia y los criterios, el formato Markdown, la pantalla con botón de copiar y, al final, el pegado manual en Jira. -->

## Assumptions & Open Questions

- Hipótesis: las 6 piezas Must have pueden no caber en dos semanas (SD Q11); si no caben, hay que acordar cuál se difiere.
- Abierto: criterio para elegir entre Amazon Titan y Claude Sonnet tras la evaluación de B1 (FE Q9).
- Abierto: cómo se mide a mano "Gherkin válido a la primera" y con qué conjunto de títulos de prueba (SD Q5).
