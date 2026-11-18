# Constraint Register — Business Analyst Agent

Documento de entrada: `intent-statement.md`. Respuestas de esta etapa: `feasibility-questions.md`.

## Restricciones técnicas

| ID | Restricción | Fuente |
|----|-------------|--------|
| C1 | La solución se ejecuta en AWS, región us-east-1. | Q2 |
| C2 | El modelo de IA se accede mediante Amazon Bedrock; hay que habilitar el modelo en la cuenta antes de usarlo. | Q10 |
| C3 | Se evaluarán Amazon Titan y Claude Sonnet y se decide después cuál usar. | Q1, Q9 |
| C4 | Sin integraciones con otros sistemas en el MVP. | Q3 |
| C5 | Sin persistencia en la primera versión, y DynamoDB queda fuera. | `intent-statement.md` (Initial Scope Signal) |
| C6 | El acceso se hace con inicio de sesión de Gmail u Outlook. | Q4 |

## Restricciones organizacionales

| ID | Restricción | Fuente |
|----|-------------|--------|
| O1 | Plazo corto y costo de AWS mínimo. | Q7 |
| O2 | El equipo tiene perfil principalmente Python, con poca experiencia en React y AWS serverless. | Q6 |
| O3 | Ningún bloqueo organizacional conocido (sin aprobaciones pendientes, congelamientos ni prioridades en competencia). | Q8 |

## Restricciones regulatorias

| ID | Restricción | Fuente |
|----|-------------|--------|
| R1 | Ninguna identificada: sin requisitos regulatorios ni datos sensibles. | Q5 |

## Assumptions & Open Questions

- Se asume que los títulos de funcionalidad no contendrán datos sensibles (Q5); ver `feasibility-assessment.md`.
- Abierto: regla de quién puede iniciar sesión con Gmail u Outlook (C6).
