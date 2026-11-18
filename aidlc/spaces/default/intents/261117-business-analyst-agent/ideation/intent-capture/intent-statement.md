# Intent Statement — Business Analyst Agent

## Problem Statement

- Las historias de usuario que se escriben hoy son inconsistentes entre analistas, en formato, calidad y Gherkin. [Q1]
- Se pide construir un Business Analyst Agent que, a partir de un título funcional, genere una historia de usuario con 2 a 3 criterios de aceptación en Gherkin válido, en español y en Markdown listo para Jira. [desc]

## Target Customer

- Usuarios internos: analistas de negocio y Product Owners que hoy redactan las historias a mano. [Q2]

## Success Metrics

- Tiempo para obtener una historia lista para pegar en Jira (el ejemplo de la opción elegida es menos de 1 minuto). [Q3]
- Porcentaje de historias cuyo Gherkin pasa la validación a la primera. [Q3]

## Initiative Trigger

- Ahorrar tiempo del equipo de análisis. [Q4]

## Initial Scope Signal

- Plan seleccionado por el flujo (workflow-selected): `mvp`. [scope]
- Fuera de la primera versión: procesar varias funcionalidades a la vez (una por solicitud). [Q7]
- Fuera de la primera versión: DynamoDB. [Q7]
- El nuevo agente reemplaza al agente actual que genera historias de usuario a partir de un Excel. [Q8]

## Assumptions & Open Questions

None.
