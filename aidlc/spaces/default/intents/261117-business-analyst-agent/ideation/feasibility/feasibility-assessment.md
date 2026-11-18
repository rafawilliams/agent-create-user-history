# Feasibility Assessment — Business Analyst Agent

Documento de entrada: `intent-statement.md` (etapa Intent Capture). Respuestas de esta etapa: `feasibility-questions.md` (Q1 a Q10).

## Conclusión

**Viable con condiciones.** Con la información confirmada no hay un bloqueo que impida el MVP, pero hay una condición previa (habilitar el modelo de IA en la cuenta AWS) y dos riesgos que conviene validar pronto: la calidad del texto generado según el modelo y la experiencia del equipo con la tecnología elegida. Esta conclusión es una evaluación del equipo de análisis (hipótesis), no una garantía.

## Evaluación por dimensión

| Dimensión | Evaluación | Base |
|-----------|-----------|------|
| Plataforma en la nube | Viable con condición: la cuenta AWS existe, pero el modelo aún no está habilitado en Bedrock. | Respuestas Q1 y Q10 |
| Modelo de IA | Abierto: se evaluarán Amazon Titan y Claude Sonnet antes de decidir cuál usar. | Respuestas Q1 y Q9; `intent-statement.md` (el problema es la inconsistencia de las historias y el Gherkin) |
| Región | Definida: us-east-1. | Respuesta Q2 |
| Integraciones | Sin integraciones en el MVP; el analista copia el resultado. | Respuesta Q3 |
| Acceso y seguridad | Inicio de sesión con Gmail u Outlook. | Respuesta Q4 |
| Datos y cumplimiento | Sin requisitos regulatorios ni datos sensibles. | Respuesta Q5 |
| Equipo | Riesgo medio: perfil principalmente Python, con poca experiencia en React y AWS serverless. | Respuesta Q6 |
| Plazo y costo | Restringido: plazo corto y costo de AWS mínimo. | Respuesta Q7 |
| Bloqueos organizacionales | Ninguno conocido. | Respuesta Q8 |

## Hipótesis a validar

- **Hipótesis 1 — calidad del modelo.** La calidad del Gherkin y de la redacción puede variar entre Amazon Titan y Claude Sonnet. Se valida con una evaluación comparativa de ambos modelos con ejemplos reales de títulos de funcionalidad. Origen: Q9 y la métrica de Gherkin válido a la primera en `intent-statement.md`.
- **Hipótesis 2 — disponibilidad en la región.** Los modelos que se quieran evaluar podrían no estar disponibles en us-east-1 o requerir una solicitud de acceso. Se valida consultando la cuenta AWS. Origen: Q2 y Q10.
- **Hipótesis 3 — acceso con cuentas personales.** Permitir inicio de sesión con Gmail u Outlook podría abrir el agente a personas ajenas a la organización si no se restringe quién entra. Se valida definiendo la regla de acceso permitido. Origen: Q4.

## Riesgos principales

- Retraso por la habilitación del modelo en Bedrock (condición previa; Q10).
- Curva de aprendizaje de React y AWS serverless con un equipo de perfil Python (Q6) en un plazo corto (Q7).
- Evaluar dos modelos compite con el plazo corto (Q7, Q9).

El detalle está en `raid-log.md`; las restricciones, en `constraint-register.md`.

## Assumptions & Open Questions

- Los títulos de funcionalidad no contienen datos sensibles, como indicó la respuesta Q5. Si cambia, hay que revisar seguridad y residencia de datos.
- Abierto: qué cuentas de Gmail u Outlook pueden entrar al agente (cualquiera, una lista o un dominio). No fue respondido en Q4.
- Abierto: criterio para elegir entre Amazon Titan y Claude Sonnet tras la evaluación (Q9).
