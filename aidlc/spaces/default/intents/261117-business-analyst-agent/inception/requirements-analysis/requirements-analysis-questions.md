# Requirements Analysis — Preguntas

## Q1. [Producto] ¿En qué idioma van las palabras clave del Gherkin (Dado/Cuando/Entonces)?

Contexto: el agente responde en español. El Gherkin en español exige una línea `# language: es` y las palabras Dado, Cuando y Entonces; en inglés se usan Given, When y Then. El agente actual genera Dado/Cuando/Entonces.

- A. En español: Dado, Cuando, Entonces (con `# language: es`)
- B. En inglés: Given, When, Then
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Producto] ¿Qué formato exacto debe tener el resultado para que esté "listo para Jira"?

Contexto: Jira acepta pegar Markdown en su editor actual, pero el formato clásico de Jira usa otra sintaxis (wiki). El resultado se copia y se pega a mano.

- A. Markdown estándar: títulos, listas y un bloque de código para el Gherkin
- B. La sintaxis wiki clásica de Jira
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Producto] ¿Qué rol fijo se usa en la historia mientras el rol automático espera a la segunda versión?

Contexto: en Scope Definition elegiste un rol genérico fijo. La frase será "Como [rol], quiero ..., para ...".

- A. "usuario"
- B. "analista de negocio"
- C. Otro rol fijo (indícalo en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q4. [Producto] ¿Cuál es la longitud máxima aceptada para el título de la funcionalidad?

Contexto: un título muy largo puede ser un texto pegado por error y encarece cada llamada al modelo. Un título más corto que el mínimo ya se trata como ambiguo (se pide contexto).

- A. Hasta 200 caracteres
- B. Hasta 500 caracteres
- C. Sin límite definido
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q5. [Operaciones] ¿Cuánto tiempo máximo puede esperar el analista por una historia?

Contexto: la meta del MVP es menos de 1 minuto por historia. Esta pregunta fija el máximo tolerable antes de mostrar un error con el botón de reintentar.

- A. Hasta 30 segundos
- B. Hasta 60 segundos
- C. Sin límite definido
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q6. [Operaciones] ¿Cuántas personas usarán el agente en el MVP?

Contexto: define cuánta capacidad hay que prever y si hace falta un límite de uso para controlar el costo del modelo.

- A. Hasta 5 personas, con uso ocasional
- B. Entre 6 y 50 personas
- C. Más de 50 personas
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q7. [Seguridad] ¿Se pueden guardar los títulos y las historias generadas en los registros (logs) de la nube?

Contexto: el MVP no guarda datos, pero los servicios de AWS pueden registrar el contenido de las solicitudes. Esto decide si se registran solo errores y métricas, o también el contenido.

- A. Solo errores y métricas, sin el contenido de los títulos ni de las historias
- B. También el contenido, para poder depurar problemas
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
