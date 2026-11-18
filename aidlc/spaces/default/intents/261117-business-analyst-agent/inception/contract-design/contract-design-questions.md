# Contract Design — Preguntas

Plan: fijar los contratos entre las unidades que se integran. Las fronteras son: la interfaz (U5) con el servicio de generación (U3), la interfaz (U5) con el control de acceso (U4), el servicio (U3) con el control de acceso (U4) y el servicio (U3) con el acceso al modelo (U2). El sistema no expone una API a consumidores externos distintos de la interfaz propia (`components.md`).

## Q1. [Arquitectura] ¿Qué operaciones ofrece el servicio a la interfaz?

Contexto: hoy la interfaz valida el título en pantalla y el servicio lo valida de nuevo (ADR-001; requisito FR1). La operación de generar es la principal.

- A. Una sola operación: generar la historia a partir del título (y del contexto si lo hay), que valida y devuelve el resultado (recomendado)
- B. Dos operaciones: una para validar el título y otra para generar
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Arquitectura] ¿Qué devuelve el servicio cuando genera la historia?

Contexto: en Domain Design el servicio devuelve el Markdown ya armado (ADR-005); quedó abierto si además devuelve la historia y los criterios en campos separados.

- A. Solo el Markdown final y un identificador de la solicitud
- B. El Markdown y también la historia y los criterios en campos separados
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Arquitectura] ¿Cómo se versiona el contrato entre la interfaz y el servicio?

Contexto: la interfaz y el servicio los construye el mismo equipo y se despliegan por separado (UG Q3). Un cambio incompatible entre ambos rompería la pantalla.

- A. La versión va en la dirección del servicio (por ejemplo, v1) y un cambio incompatible crea una versión nueva
- B. Sin versión explícita en el MVP, porque hay un solo consumidor; los cambios se coordinan entre equipos
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Arquitectura] ¿Cómo se informan los errores a la interfaz?

Contexto: la interfaz distingue título inválido, título ambiguo, sesión inválida y fallo del servicio, y para fallos muestra un botón "Reintentar" (FR5.2).

- A. Una respuesta de error con un código estable, un mensaje en español y una indicación de si se puede reintentar (recomendado)
- B. Solo el código HTTP y un mensaje de texto
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q5. [Arquitectura] ¿Cómo se reparte el máximo de 60 segundos entre la interfaz, el servicio y el modelo?

Contexto: la generación debe terminar en menos de 60 segundos (NFR1). Para que el servicio alcance a responder con un error claro, el modelo debería cortar antes que el servicio, y el servicio antes que la interfaz.

- A. El modelo se corta a los 50 segundos, el servicio responde antes de los 60 y la interfaz espera hasta 60 (recomendado)
- B. Un solo límite de 60 segundos en la interfaz y sin cortes intermedios
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q6. [Arquitectura] ¿Reintenta el servicio automáticamente cuando el modelo falla?

Contexto: la interfaz ya ofrece un botón "Reintentar". Un reintento automático puede ocultar fallos pasajeros, pero consume parte del máximo de 60 segundos y puede multiplicar el costo.

- A. No: el servicio devuelve el error y la persona reintenta con el botón
- B. Sí, un reintento automático ante un fallo pasajero, si queda tiempo dentro del máximo
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q7. [Arquitectura] ¿Cómo viaja la identidad de la sesión de la interfaz al servicio?

Contexto: el servicio verifica la sesión en cada solicitud de generación (ADR-006).

- A. La interfaz envía una credencial de la sesión en cada solicitud y el servicio la verifica (recomendado)
- B. Una cookie de sesión que el navegador envía sola
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q8. [Arquitectura] ¿Cómo se comunican entre sí los componentes del servicio?

Contexto: StoryGenerator, AccessControl y ModelGateway se despliegan juntos como un solo servicio (UG Q3).

- A. Con llamadas directas dentro del mismo servicio, a través de interfaces tipadas que cada unidad respeta (recomendado)
- B. Con llamadas de red entre ellos, como si fueran servicios separados
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
