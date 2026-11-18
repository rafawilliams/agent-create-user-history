# Personas — Business Analyst Agent

Documentos de entrada: `requirements.md`, `business-overview.md`, `component-inventory.md` y `team-practices.md`. Plan: `user-stories-questions.md` (Q1: una sola persona).

## Persona principal

| Campo | Valor |
|-------|-------|
| Nombre | Analista de negocio |
| Rol | Analista de negocio o Product Owner interno que prepara el backlog |
| Objetivos | Obtener rápido una historia de usuario con criterios de aceptación listos para Jira; mantener un formato uniforme |
| Puntos de dolor | Redactar las historias a mano toma tiempo y el formato, la calidad y el Gherkin cambian entre analistas |
| Comodidad técnica | Media (escribe criterios en Gherkin, no programa) |
| Frecuencia de uso | Ocasional; se prevén hasta 5 personas |
| Contexto | Escritorio y móvil; se identifica con una cuenta de Gmail u Outlook |

Fuentes: `intent-statement.md` (Target Customer, Problem Statement); `requirements.md` (NFR3, NFR7, FR6.1); `user-stories-questions.md` (Q1). El Product Owner usa el agente de la misma forma que el analista, por lo que no tiene persona propia.

## Actor habilitador

| Campo | Valor |
|-------|-------|
| Nombre | Equipo de desarrollo |
| Rol | Quien construye el agente |
| Objetivo | Elegir el modelo de IA con evidencia antes de construir (US7.1) |

No es una persona de usuario. Se nombra porque el plan eligió expresar la evaluación del modelo como una historia habilitadora desde su punto de vista (`user-stories-questions.md`, Q3).

## Prioridad entre personas

1. Analista de negocio (única persona de usuario).
2. Equipo de desarrollo (solo para la historia habilitadora).
