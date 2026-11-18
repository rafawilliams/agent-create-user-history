# User Flow — Business Analyst Agent

Documentos de entrada: `intent-statement.md`, `scope-document.md` e `intent-backlog.md`. Respuestas de esta etapa: `rough-mockups-questions.md` (RM Q1 a Q4). Pantallas: `wireframes.md`.

## Flujo principal: generar una historia

Flow: Generar una historia de usuario a partir de un título
Persona: analista de negocio o Product Owner interno (`intent-statement.md`, Target Customer)
Trigger: el analista necesita una historia con criterios de aceptación para una funcionalidad
Steps:

1. S1 Acceso -> el analista elige Gmail u Outlook -> el sistema inicia la sesión y muestra S2
2. S2 vacío -> el analista escribe el título y pulsa Generar historia -> el sistema muestra el estado cargando
3. S2 cargando -> el sistema genera la historia en español -> muestra el resultado con las pestañas Vista previa y Markdown
4. S2 con resultado -> el analista revisa y pulsa Copiar Markdown -> el sistema confirma que se copió
5. Fuera del agente -> el analista pega el Markdown en Jira (paso manual)

Success outcome: el analista tiene en el portapapeles una historia con 2 a 3 criterios en Gherkin, lista para pegar en Jira.

## Rutas de error y alternativas

| Condición | Qué ve el analista | Recuperación | Fuente |
|-----------|--------------------|--------------|--------|
| Título muy corto o ambiguo | Mensaje bajo el título y un campo adicional de contexto | Completa el contexto y vuelve a pulsar Generar historia | RM Q3 |
| El servicio falla al generar | Mensaje claro y botón Reintentar; el título escrito se conserva | Pulsa Reintentar | RM Q4 |
| Falla el inicio de sesión | Se mantiene en S1 con un mensaje claro | Vuelve a elegir Gmail u Outlook | RM Q1 |

La última fila es una propuesta de diseño: no fue una decisión confirmada y su texto queda como borrador.

## Diagrama del flujo

```
[S1 Acceso] --> [S2 vacio] --> [S2 cargando] --> [S2 con resultado]
                    ^               |                    |
                    |               | falla              v
                    |               v           [Copiar Markdown]
                    |        [S2 error servicio]         |
                    |               |                    v
                    +-- Reintentar -+          [Pegar en Jira (manual)]
                    |
   titulo ambiguo --+--> [S2 pedir contexto] --> [S2 cargando]
```
<!-- Text fallback: el flujo va del acceso a la pantalla vacía, luego a cargando y al resultado; desde el resultado se copia el Markdown y se pega manualmente en Jira. Si el servicio falla, se muestra un error y el botón Reintentar vuelve a intentar; si el título es ambiguo, se pide contexto y se vuelve a cargar. -->

## Jerarquía de información de la pantalla principal

1. Título de la funcionalidad y botón Generar historia (acción principal).
2. Resultado, con pestañas Vista previa y Markdown.
3. Botón Copiar Markdown.

Fuente: RM Q1, RM Q2 y `scope-document.md` (pantalla del MVP).

## Assumptions & Open Questions

- Abierto: qué mensaje exacto se muestra si falla el inicio de sesión (ruta propuesta, no confirmada).
- Abierto: cuántas veces puede pedirse contexto para un mismo título.
