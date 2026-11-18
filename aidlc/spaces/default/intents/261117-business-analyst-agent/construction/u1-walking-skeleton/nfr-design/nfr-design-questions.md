# NFR Design — u1-walking-skeleton — Preguntas

La revisión de los requisitos no funcionales de esta unidad dejó dos puntos abiertos sobre el límite de 20 solicitudes por persona por día, y un valor de tiempo sin fijar. Estas preguntas los resuelven antes de diseñar.

## Q1. [Arquitectura] ¿Dónde se aplica el límite de solicitudes por persona por día?

Contexto: un límite diario necesita un contador que recuerde cuántas solicitudes hizo cada origen. Tú excluiste guardar datos (sin persistencia, y sin DynamoDB), y en el esqueleto no hay una identidad real de la persona. El contador solo guarda cantidades, no títulos ni historias.

- A. En la pasarela HTTP, con una cuota diaria y un límite de tasa del propio servicio de AWS, sin guardar datos propios en el servicio
- B. Se difiere el límite por persona hasta que exista el control de acceso (u4), y el esqueleto aplica solo un límite de tasa global
- C. En la memoria del servicio: sencillo, pero se reinicia con cada arranque y no es exacto
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q2. [Arquitectura] ¿Qué devuelve el servicio cuando se supera el límite de uso?

Contexto: el contrato C1 no tiene hoy un código para este caso. Añadirlo es un cambio aditivo al contrato.

- A. Un error con código RATE_LIMITED, HTTP 429 y `retryable` falso (la persona debe esperar al día siguiente)
- B. Un error con código RATE_LIMITED, HTTP 429 y `retryable` verdadero
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q3. [Operaciones] ¿A qué segundo responde el servicio, como máximo, dentro de los 60 segundos de la interfaz?

Contexto: el modelo se corta a los 50 segundos y la interfaz espera hasta 60. El servicio necesita tiempo para armar un error claro entre ambos cortes.

- A. A los 55 segundos
- B. A los 58 segundos
- C. A los 52 segundos
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
