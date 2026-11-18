# RAID Log — Business Analyst Agent

Documento de entrada: `intent-statement.md`. Respuestas de esta etapa: `feasibility-questions.md`. Las valoraciones de probabilidad e impacto son una evaluación del equipo de análisis (hipótesis), no datos medidos.

## Risks

| ID | Riesgo | Probabilidad | Impacto | Respuesta propuesta | Fuente |
|----|--------|--------------|---------|---------------------|--------|
| RK1 | La habilitación del modelo en Bedrock se retrasa y frena el inicio. | Media | Alto | Solicitar el acceso al modelo de inmediato. | Q10 |
| RK2 | El modelo elegido produce Gherkin o redacción de menor calidad que la esperada. | Media | Alto | Evaluar Amazon Titan y Claude Sonnet con ejemplos reales antes de decidir. | Q9; `intent-statement.md` |
| RK3 | El equipo tarda más de lo previsto con React y AWS serverless. | Media | Medio | Mantener el alcance mínimo y reservar tiempo para aprender. | Q6, Q7 |
| RK4 | La evaluación de dos modelos consume el plazo corto. | Media | Medio | Limitar la evaluación a un conjunto pequeño de títulos de ejemplo. | Q7, Q9 |
| RK5 | Acceso abierto a cualquier cuenta de Gmail u Outlook si no se restringe. | Media | Medio | Definir quién puede entrar antes de publicar. | Q4 |

## Assumptions

| ID | Supuesto | Cómo validarlo | Fuente |
|----|----------|----------------|--------|
| A1 | Los títulos de funcionalidad no contienen datos sensibles. | Confirmar con los analistas con títulos reales. | Q5 |
| A2 | No hay bloqueos organizacionales que retrasen el MVP. | Revisar de nuevo al inicio de Construction. | Q8 |
| A3 | Los modelos a evaluar están disponibles en us-east-1. | Consultar la disponibilidad en la cuenta AWS. | Q2 |

## Issues

| ID | Problema actual | Responsable | Fuente |
|----|-----------------|-------------|--------|
| I1 | La cuenta AWS existe, pero el modelo aún no está habilitado en Bedrock. | Por definir | Q10 |

## Dependencies

| ID | Dependencia | Fuente |
|----|-------------|--------|
| D1 | Habilitar el acceso al modelo en la cuenta AWS (I1). | Q10 |
| D2 | Definir la regla de acceso para el inicio de sesión con Gmail u Outlook. | Q4 |

## Assumptions & Open Questions

- Abierto: responsable de habilitar el modelo en Bedrock (I1).
- Abierto: regla de quién puede iniciar sesión (D2).
