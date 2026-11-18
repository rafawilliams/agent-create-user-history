# User Stories — Plan y preguntas

Plan propuesto: las historias siguen el formato "Como [persona], quiero [objetivo], para [beneficio]" y los criterios de aceptación usan Dado/Cuando/Entonces. Cada historia cumple los criterios INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) y lleva una prioridad MoSCoW. Cada requisito funcional y no funcional de `requirements.md` queda cubierto por una historia, o diferido a una etapa con nombre, o marcado como no aplicable con su razón.

## Q1. [Producto] ¿Cuántas personas (tipos de usuario) tienen historias propias?

Contexto: en Intent Capture indicaste que los usuarios son analistas de negocio y Product Owners internos. Esto decide si se escriben historias desde un solo punto de vista o desde dos.

- A. Una sola persona: el analista de negocio, que escribe el título, revisa y copia el resultado (el Product Owner usa el agente de la misma forma)
- B. Dos personas: el analista de negocio, que genera el resultado, y el Product Owner, que lo revisa y lo lleva a Jira
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Producto] ¿Cómo se organizan las historias?

Contexto: los requisitos funcionales FR1 a FR7 siguen el recorrido del analista: título, generación, resultado, errores, acceso y elección del modelo.

- A. Por flujo de trabajo: una historia por cada paso del recorrido (entrar, escribir el título, obtener la historia, copiar, recuperarse de errores)
- B. Por funcionalidad: una historia por cada grupo de requisitos funcionales (FR1 a FR7)
- C. Por persona
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q3. [Producto] ¿Cómo se trata la evaluación de Amazon Titan y Claude Sonnet (FR7.1)?

Contexto: es una actividad del equipo, no un comportamiento que ve el analista. Aun así, cada requisito debe quedar cubierto por una historia o diferido con justificación.

- A. Como una historia habilitadora escrita desde el punto de vista del equipo de desarrollo
- B. Sin historia: queda como requisito de proceso, marcado como no aplicable a las historias con esa razón
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Producto] ¿Qué prioridad MoSCoW tienen las historias?

Contexto: el alcance del MVP ya se priorizó en Scope Definition (todas las capacidades dentro del alcance son Must have). El MVP formal se decide después, en Delivery Planning.

- A. Todas las historias de las capacidades dentro del alcance son Must have
- B. Algunas son Should have o Could have (indica cuáles en Other)
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
