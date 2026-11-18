# Wireframes — Business Analyst Agent

Documentos de entrada: `intent-statement.md`, `scope-document.md` e `intent-backlog.md`. Respuestas de esta etapa: `rough-mockups-questions.md` (RM Q1 a Q7).

Son bocetos de baja fidelidad para validar estructura, no diseño final. Estilo: Material Design (RM Q6). Dispositivos: escritorio y móvil (RM Q5). Accesibilidad: WCAG 2.1 nivel AA y uso completo solo con teclado (RM Q7). Las dos pantallas salen de RM Q1 y de las capacidades B5 y B6 de `intent-backlog.md`.

## Pantallas

| ID | Pantalla | Propósito | Fuente |
|----|----------|-----------|--------|
| S1 | Acceso | Iniciar sesión con Gmail u Outlook | RM Q1; `scope-document.md` (acceso con Gmail u Outlook) |
| S2 | Principal | Escribir el título, ver la historia y copiar el Markdown | RM Q1, RM Q2; `scope-document.md` (pantalla del MVP) |

## S1 — Acceso

```
+--------------------------------------------------+
| Business Analyst Agent                           |
+--------------------------------------------------+
|                                                  |
|  Iniciar sesion                                  |
|  Usa tu cuenta de Gmail u Outlook                |
|                                                  |
|  [ Continuar con Gmail   ]                       |
|  [ Continuar con Outlook ]                       |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: encabezado con el nombre del agente; debajo, el título "Iniciar sesion", una frase y dos botones, uno para Gmail y otro para Outlook. -->

Accesibilidad: título de pantalla en h1; regiones header y main; el teclado entra por el primer botón de acceso.

## S2 — Principal

### Estado vacío (inicial)

```
+--------------------------------------------------+
| Business Analyst Agent              [ Cerrar ses]|
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Ej: Recuperar contrasena                   |  |
|  +--------------------------------------------+  |
|  [ Generar historia ]                            |
|                                                  |
|  Aun no hay resultado. Escribe un titulo y       |
|  pulsa Generar historia.                         |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: encabezado con botón para cerrar sesión; un campo para el título de la funcionalidad, un botón "Generar historia" y un mensaje que explica que aún no hay resultado. -->

Accesibilidad: título de la sección en h1; regiones header y main; el teclado entra por el campo del título y el botón se activa con Enter.

### Estado cargando

```
+--------------------------------------------------+
| Business Analyst Agent              [ Cerrar ses]|
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Recuperar contrasena                       |  |
|  +--------------------------------------------+  |
|  [ Generar historia ] (desactivado)              |
|                                                  |
|  ( ... ) Generando la historia...                |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: igual que la pantalla inicial, pero el botón está desactivado y aparece un indicador de carga con el mensaje "Generando la historia...". -->

Accesibilidad: el mensaje de carga se anuncia con una región de estado (aria-live polite) para lectores de pantalla.

### Estado con resultado

```
+--------------------------------------------------+
| Business Analyst Agent              [ Cerrar ses]|
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Recuperar contrasena                       |  |
|  +--------------------------------------------+  |
|  [ Generar historia ]                            |
|                                                  |
|  [ Vista previa ] [ Markdown ]                   |
|  +--------------------------------------------+  |
|  | Como usuario, quiero ..., para ...         |  |
|  | Criterios de aceptacion (2 a 3, Gherkin)   |  |
|  +--------------------------------------------+  |
|  [ Copiar Markdown ]                             |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: igual que la pantalla inicial, más dos pestañas (Vista previa y Markdown), un recuadro con la historia y sus criterios de aceptación en Gherkin, y un botón "Copiar Markdown". -->

Accesibilidad: las pestañas se cambian con las teclas de flecha y se anuncia la pestaña activa; el botón de copiar confirma con un mensaje de estado, no solo con un cambio de color.

### Estado título ambiguo (pedir contexto)

```
+--------------------------------------------------+
| Business Analyst Agent              [ Cerrar ses]|
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Login                                      |  |
|  +--------------------------------------------+  |
|  (!) El titulo es muy corto. Agrega contexto:    |
|      que debe poder hacer el usuario?            |
|  Contexto                                        |
|  +--------------------------------------------+  |
|  |                                            |  |
|  +--------------------------------------------+  |
|  [ Generar historia ]                            |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: bajo el campo del título aparece un mensaje con un icono de aviso que pide más contexto, y un campo adicional "Contexto" que el analista completa antes de volver a generar. -->

Accesibilidad: el mensaje usa icono y texto, no solo color; el foco pasa al campo de contexto cuando aparece, y el mensaje se asocia al campo con aria-describedby.

### Estado error del servicio

```
+--------------------------------------------------+
| Business Analyst Agent              [ Cerrar ses]|
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Recuperar contrasena                       |  |
|  +--------------------------------------------+  |
|  (x) No se pudo generar la historia.             |
|      Intenta de nuevo en unos segundos.          |
|  [ Reintentar ]                                  |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: el título escrito se conserva; debajo aparece un mensaje de error con un icono, que explica que no se pudo generar la historia, y un botón "Reintentar". -->

Accesibilidad: el error se anuncia con una región de alerta (role alert); el título escrito se conserva y el botón de reintentar recibe el foco.

## Comportamiento en móvil

En pantallas pequeñas (menos de 768 px) los elementos de S2 se apilan en una sola columna: título, botón de generar, pestañas y resultado, con el botón de copiar al final. Los botones miden al menos 44 por 44 píxeles. Fuente: RM Q5; guía de diseño de accesibilidad de la etapa.

## Notas de contenido

- El rol de la historia es genérico y fijo en el MVP, así que la vista de resultado no ofrece elegir el rol. Fuente: `scope-document.md` (SD Q10).
- El Gherkin se muestra tal como lo genera el modelo, sin validación automática ni aviso de formato inválido en esta versión. Fuente: `scope-document.md` (SD Q9).
- No hay historial ni pantalla de historias guardadas, porque el MVP no guarda datos. Fuente: `intent-statement.md` (Initial Scope Signal).
- La pantalla no incluye edición del texto generado; no fue seleccionada para el MVP. Fuente: `scope-document.md` (SD Q2).

## Assumptions & Open Questions

- Abierto: textos exactos de los mensajes (por ejemplo, el de título ambiguo); aquí son borradores.
- Abierto: cuántas veces puede pedirse contexto para un mismo título.
- Abierto: si el botón de cerrar sesión entra en el MVP; se muestra como propuesta para que haya una forma de salir de la sesión.
