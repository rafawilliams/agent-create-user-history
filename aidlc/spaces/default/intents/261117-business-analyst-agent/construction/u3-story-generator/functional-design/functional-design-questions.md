# Functional Design — u3-story-generator — Preguntas

Contexto: u1 dejó una generación mínima (el modelo devuelve el Markdown completo y el servicio solo comprueba que empiece con "Como analista de negocio"). u3 la completa (US1.1 a US5.1): validar el título y pedir contexto cuando no basta, armar la petición, interpretar la respuesta del modelo y armar el Markdown final (ADR-005), con el título tratado como dato. Estas preguntas cierran cuatro decisiones abiertas en `requirements.md` y en el contrato C1.

## Q1. [Producto] ¿Cuándo un título es "muy corto o ambiguo" y se pide contexto?

Contexto: el umbral está abierto (FR1.4, AC1.1.4 usa "Login" como ejemplo). La regla debe ser comprobable sin llamar al modelo.

- A. Con menos de 3 palabras o menos de 12 caracteres se pide contexto
- B. Con menos de 2 palabras se pide contexto
- C. Siempre se genera; el modelo decide si falta contexto y lo indica en su respuesta
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Producto] ¿Cómo funciona el campo de contexto?

Contexto: el contrato C1 acepta un campo `context` opcional; su largo máximo y el número de veces que se puede pedir contexto están abiertos.

- A. Máximo 500 caracteres; se pide contexto una sola vez, y si con el contexto sigue siendo corto, igual se genera
- B. Máximo 1 000 caracteres; se pide contexto una sola vez, y si con el contexto sigue siendo corto, igual se genera
- C. Máximo 500 caracteres; se puede pedir contexto las veces que haga falta hasta que no esté vacío
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Arquitectura] ¿En qué forma responde el modelo, para que el servicio la interprete?

Contexto: ADR-005 dice que el servicio arma el Markdown final. Para armarlo y para detectar una respuesta sin la estructura esperada (FR5.3), el servicio debe poder leer la respuesta.

- A. El modelo responde en JSON con la historia (acción, beneficio) y de 2 a 3 criterios en Gherkin; el servicio valida el JSON y arma el Markdown
- B. El modelo responde ya en Markdown con la estructura fija y el servicio la valida con reglas de texto
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Producto] ¿Qué estructura tiene el Markdown final que se copia a Jira?

Contexto: FR4.1 pide un título, la historia, la lista de criterios y el Gherkin en un bloque de código, con la línea `# language: es`.

- A. Un título con el texto del título del analista, la historia en una línea, una lista numerada de los nombres de los criterios, y un único bloque de código con el Gherkin completo (`# language: es` primero)
- B. Un título, la historia, y un bloque de código de Gherkin por cada criterio
- C. Not yet defined
- X. Other (please specify)

[Answer]: A
