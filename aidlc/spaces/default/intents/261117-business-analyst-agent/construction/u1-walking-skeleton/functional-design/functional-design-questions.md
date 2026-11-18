# Functional Design — u1-walking-skeleton — Preguntas

U1 es el esqueleto ambulante: la versión mínima que corre de principio a fin. La mayor parte del diseño ya está decidido en etapas anteriores; estas preguntas cubren lo que el esqueleto todavía no tiene definido.

## Q1. [Desarrollo] ¿Con qué modelo se prueba el esqueleto?

Contexto: el acceso a Amazon Bedrock ya está habilitado (`delivery-planning-questions.md`, Q5). La elección definitiva entre Amazon Titan y Claude Sonnet se decide después, en la unidad del acceso al modelo, pero el esqueleto necesita llamar a uno desde el principio.

- A. Claude Sonnet
- B. Amazon Titan
- C. Configurable, sin fijar uno por defecto (se indica al ejecutar)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Desarrollo] ¿Qué le pide el esqueleto al modelo?

Contexto: el formato completo (2 a 3 criterios en Gherkin, en español) lo implementa la unidad de generación. El esqueleto solo necesita demostrar que el camino completo funciona.

- A. Solo la historia con el formato "Como analista de negocio, quiero ..., para ...", sin criterios (lo más simple para probar la conexión)
- B. La historia y 2 a 3 criterios en Gherkin en español, el formato final
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q3. [Calidad] ¿Cómo se comprueba que el esqueleto corre de punta a punta?

Contexto: este proyecto no tiene hoy pruebas ni un comando de verificación. La comprobación real es la que el motor usa en cada punto de control, y debe demostrar el resultado de punta a punta (`bolt-plan.md`, B1).

- A. Un comando que ejecuta el servicio completo en local contra el modelo real de Bedrock, más pruebas automáticas con el modelo simulado
- B. Solo pruebas automáticas con el modelo simulado, y la llamada real se prueba a mano una vez
- C. Desplegado en AWS (exige haber hecho antes la infraestructura)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Calidad] ¿Qué muestra la pantalla mínima cuando el servicio devuelve un error?

Contexto: el esqueleto no tiene "Reintentar" ni los estados completos de la interfaz (los agrega la unidad de la interfaz); aun así, un error nunca puede quedar en silencio.

- A. Un mensaje de texto simple con el mensaje que devuelve el servicio
- B. Un mensaje genérico fijo, sin el texto del servicio
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
