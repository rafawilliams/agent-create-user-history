# Team Allocation — Business Analyst Agent

Documentos de entrada: `requirements.md`, `unit-of-work.md`, `unit-of-work-dependency.md`, `contract-summary.md` y `team-practices.md`. Secuencia: `bolt-plan.md`. Respuestas: `delivery-planning-questions.md` (DP Qn).

Una **Bolt** es una pasada de construcción sobre una parte del trabajo (una o más unidades) que termina en algo que corre. Un **mob** es un grupo que trabaja junto en lo mismo; aquí no hay un grupo de personas asignado a la construcción.

El plan es para el alcance `mvp`, donde no se forma un equipo por separado. Por eso cada Bolt la construye el agente de desarrollo (una IA) y la persona decide en los puntos de control. No hay varios equipos, así que no hace falta un tablero de coordinación entre ellos.

## Asignación por Bolt

| Bolt | Unidad | Quién la construye | Quién decide |
|------|--------|--------------------|--------------|
| B1 | U1 u1-walking-skeleton | Agente de desarrollo | La persona, en el punto de control del esqueleto ambulante |
| B2 | U6 u6-infrastructure | Agente de desarrollo | La persona, en el punto de control de la unidad |
| B3 | U2 u2-model-gateway | Agente de desarrollo | La persona, que además decide qué modelo usar tras la evaluación |
| B4 | U3 u3-story-generator | Agente de desarrollo | La persona, en el punto de control de la unidad |
| B5 | U5 u5-web-app | Agente de desarrollo | La persona, en el punto de control de la unidad |
| B6 | U4 u4-access-control | Agente de desarrollo | La persona, en el punto de control de la unidad |

## Ejecución

Las Bolts se construyen una tras otra (DP Q4). El motivo es que U2, U3, U4 y U5 comparten archivos y contratos que fija U1, y la revisión de Units Generation advirtió que construirlas a la vez puede producir conflictos de integración.

## Roles de la persona

- **Patrocinador y decisor de alcance y prioridad:** el Product Owner (`intent-statement.md`, `stakeholder-map.md`).
- **Tareas externas a cargo de la persona:** registrar la aplicación en Google y en Microsoft para el inicio de sesión (DP Q6; ver `external-dependency-map.md`).
- **Reporte:** semanal al patrocinador (`stakeholder-map.md`).

## Capacidades que el trabajo exige y quién las aporta

| Capacidad | Aporta |
|-----------|--------|
| Código del servicio en Python | Agente de desarrollo |
| Código de la interfaz en React | Agente de desarrollo |
| Infraestructura con Terraform en AWS | Agente de desarrollo |
| Evaluación de la calidad del Gherkin a mano | La persona (analista de negocio) |

El equipo tiene un perfil principalmente Python y poca experiencia en React y en servicios sin servidor en AWS (FE Q6 de `feasibility-questions.md`); esa brecha la cubre el agente de desarrollo, pero la revisión de cada punto de control recae en la persona.

## Assumptions & Open Questions

- Supuesto: no hay un equipo de personas dedicado a la construcción; si lo hubiera, se reasigna esta tabla.
- Abierto: quién evalúa a mano el Gherkin de los títulos de prueba (NFR2) y cuántos títulos se usan.
