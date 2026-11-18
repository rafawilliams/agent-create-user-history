# Rough Mockups — Preguntas

## Q1. [Diseño] ¿Cuántas pantallas tiene el MVP?

Contexto: en Scope Definition indicaste una pantalla donde el analista escribe el título, ve la historia y copia el Markdown, y en Feasibility indicaste inicio de sesión con Gmail u Outlook.

- A. Dos pantallas: una de acceso (Gmail u Outlook) y una principal con el título y el resultado
- B. Una sola pantalla principal; el inicio de sesión lo muestra directamente el proveedor de identidad
- C. Más de dos pantallas (indícalas en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Diseño] ¿Cómo se muestra el resultado de la historia en la pantalla principal?

Contexto: el analista copia el Markdown a Jira; esto define cómo lo ve antes de copiarlo.

- A. Como vista previa ya formateada (títulos, listas y bloques de Gherkin)
- B. Como el texto Markdown tal cual, listo para copiar
- C. Con una pestaña para alternar entre la vista previa y el texto Markdown
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q3. [Diseño] ¿Cómo se le pide más contexto al analista cuando el título es muy corto o ambiguo?

Contexto: en Scope Definition elegiste que el agente pida más contexto antes de generar. Falta definir cómo aparece esa petición.

- A. Un mensaje bajo el campo del título y un campo adicional de contexto que el analista completa
- B. Un mensaje que explica qué falta y el analista corrige el título en el mismo campo
- C. Una ventana emergente con la petición y un campo de contexto
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Diseño] ¿Qué debe ver el analista mientras se genera la historia y si el servicio falla?

Contexto: generar con el modelo de IA toma tiempo y puede fallar; el analista debe saber qué pasa y qué hacer.

- A. Un indicador de carga con mensaje y, si falla, un mensaje claro con un botón para reintentar
- B. Un indicador de carga y, si falla, un mensaje claro sin botón de reintento (el analista vuelve a enviar)
- C. Un indicador de carga con botón para cancelar y, si falla, un mensaje claro con botón para reintentar
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q5. [Diseño] ¿Qué dispositivos debe soportar la interfaz del MVP?

Contexto: define si el diseño se piensa primero para escritorio o también para pantallas pequeñas.

- A. Solo escritorio
- B. Escritorio y móvil
- C. Escritorio y tablet
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q6. [Diseño] ¿Hay guías de marca o un sistema de diseño que seguir?

Contexto: define el estilo visual de los bocetos y de la interfaz.

- A. Ninguna: un estilo simple y neutro
- B. Hay guías de la organización (indica dónde están en Other)
- C. Usar una librería estándar de componentes (indica cuál en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: X: utiliza material design

## Q7. [Diseño] ¿Hay requisitos de accesibilidad?

Contexto: define si hace falta cumplir un nivel formal y qué debe poder hacerse solo con teclado.

- A. Cumplir WCAG 2.1 nivel AA y poder usar toda la pantalla solo con teclado
- B. Poder usar toda la pantalla solo con teclado, sin un nivel formal
- C. Sin requisitos de accesibilidad en el MVP
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
