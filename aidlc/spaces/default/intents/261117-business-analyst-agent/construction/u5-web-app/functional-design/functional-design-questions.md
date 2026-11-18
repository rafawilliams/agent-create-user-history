# Functional Design — u5-web-app — Preguntas

Contexto: u5 amplía la pantalla mínima de u1 hasta la interfaz completa (US1.1, US4.1, US5.1 y US6.1: 15 criterios). Los componentes, el sistema de diseño (Material Design con MUI), los temas claro y oscuro y la accesibilidad ya están definidos en `interaction-spec.md`, `design-system-mapping.md` y `accessibility-checklist.md`. Quedan tres decisiones abiertas de esos documentos que afectan al comportamiento.

## Q1. [Arquitectura] ¿Dónde guarda la pantalla el token de la sesión?

Contexto: el token que emite Cognito (con PKCE desde el navegador) vale 8 horas. Guardarlo en el almacenamiento del navegador lo expone a un script malicioso; guardarlo solo en memoria obliga a volver a pasar por Cognito al recargar la página (con la sesión de Cognito activa, es casi inmediato).

- A. Solo en memoria de la página: al recargar, la pantalla vuelve a pedir el token a Cognito, que no pide credenciales si la sesión sigue activa
- B. En el almacenamiento de sesión de la pestaña: sobrevive a una recarga, pero queda al alcance de cualquier script de la página
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Arquitectura] ¿Cómo se muestra la vista previa del Markdown?

Contexto: la vista previa muestra texto que viene del modelo y del título de la persona; el servicio ya escapa el HTML, pero la pantalla no debe confiar solo en eso (NFR4).

- A. Una biblioteca de Markdown para React que no interpreta HTML en bruto (por ejemplo react-markdown), sin dependencias de saneamiento aparte
- B. Un convertidor de Markdown a HTML con un saneador de HTML aparte (por ejemplo marked con DOMPurify)
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Producto] ¿Qué pasa con lo escrito si la sesión vence mientras la persona trabaja o genera?

Contexto: pasado el límite de 8 horas, el servicio responde SESSION_INVALID. Una generación en curso no se corta, pero la siguiente solicitud falla. Es una pregunta abierta de `interaction-spec.md`.

- A. Se conserva el título y el contexto: la pantalla muestra un mensaje con un botón para iniciar sesión de nuevo y, al volver, los campos reaparecen (se guardan solo durante esa redirección)
- B. Se vuelve a la pantalla de acceso y se pierde lo escrito
- C. Not yet defined
- X. Other (please specify)

[Answer]: A
