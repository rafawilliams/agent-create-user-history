# Mockups — Business Analyst Agent

Documentos de entrada: `wireframes.md`, `user-flow.md`, `stories.md`, `requirements.md` y `team-practices.md`. Respuestas de esta etapa: `refined-mockups-questions.md` (RF Q1 a Q7).

Estos mockups refinan los bocetos de `wireframes.md` con las decisiones confirmadas: MUI (Material Design) con tema claro y oscuro y paleta por defecto (RF Q1, Q2, Q3), botón de cerrar sesión en el encabezado (RF Q4), una columna en móvil con botones a todo el ancho (RF Q5), contador de caracteres y mensaje de error en el título (RF Q6) y mensaje en la pantalla de acceso cuando falla el inicio de sesión (RF Q7). Los mockups son en ASCII; los colores y tipografía se definen en `design-system-mapping.md`.

## Historias que representa cada pantalla

| Pantalla | Historias | Requisitos |
|----------|-----------|------------|
| S1 Acceso | US6.1 | FR6.1 |
| S2 Principal | US1.1, US2.1, US3.1, US4.1, US5.1 | FR1 a FR5, NFR1, NFR2 |

La historia US7.1 (evaluación del modelo) es una actividad del equipo y no tiene pantalla.

## S1 — Acceso

### Estado inicial

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

### Estado fallo de inicio de sesión

```
+--------------------------------------------------+
| Business Analyst Agent                           |
+--------------------------------------------------+
|                                                  |
|  Iniciar sesion                                  |
|  (x) No se pudo iniciar sesion. Intenta de       |
|      nuevo con Gmail u Outlook.                  |
|                                                  |
|  [ Continuar con Gmail   ]                       |
|  [ Continuar con Outlook ]                       |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: igual que el estado inicial, con un mensaje de error con icono arriba de los botones; los botones de Gmail y Outlook siguen disponibles. -->

Fuente: RF Q7; AC6.1.1 y AC6.1.3 de `stories.md`. El texto del mensaje es un borrador.

## S2 — Principal

### Estado vacío

```
+--------------------------------------------------+
| Business Analyst Agent         [ Cerrar sesion ] |
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Ej: Recuperar contrasena                   |  |
|  +--------------------------------------------+  |
|                                          0 / 200 |
|  [ Generar historia ]                            |
|                                                  |
|  Aun no hay resultado. Escribe un titulo y       |
|  pulsa Generar historia.                         |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: encabezado con el botón Cerrar sesion; un campo para el título con un contador 0 / 200 debajo, el botón Generar historia y un mensaje que explica que aún no hay resultado. -->

### Estado error de validación del título

```
+--------------------------------------------------+
| Business Analyst Agent         [ Cerrar sesion ] |
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | (texto de mas de 200 caracteres)           |  |
|  +--------------------------------------------+  |
|  (x) El titulo no puede superar 200    231 / 200 |
|      caracteres.                                 |
|  [ Generar historia ]                            |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: el campo del título contiene más de 200 caracteres; debajo aparece un mensaje de error con icono que indica el máximo y el contador marca 231 / 200. El mismo patrón, con otro texto, se usa cuando el título está vacío. -->

Fuente: RF Q6; AC1.1.2 y AC1.1.3 de `stories.md`. Los textos exactos son borradores.

### Estado título ambiguo (pedir contexto)

```
+--------------------------------------------------+
| Business Analyst Agent         [ Cerrar sesion ] |
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Login                                      |  |
|  +--------------------------------------------+  |
|                                          5 / 200 |
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
<!-- Text fallback: bajo el título "Login" aparece un mensaje con un icono de aviso que pide contexto y un campo adicional "Contexto" que el analista completa antes de volver a generar. -->

Fuente: SD Q4 y RM Q3 de las etapas previas; AC1.1.4 de `stories.md`. Los requisitos propios del campo de contexto (límite, vacío) siguen abiertos.

### Estado cargando

```
+--------------------------------------------------+
| Business Analyst Agent         [ Cerrar sesion ] |
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Recuperar contrasena                       |  |
|  +--------------------------------------------+  |
|                                         20 / 200 |
|  [ Generar historia ] (desactivado)              |
|                                                  |
|  ( ... ) Generando la historia...                |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: igual que la pantalla vacía con el título escrito; el botón está desactivado y aparece un indicador de carga con el mensaje "Generando la historia...". -->

Fuente: AC5.1.1 de `stories.md`.

### Estado con resultado

```
+--------------------------------------------------+
| Business Analyst Agent         [ Cerrar sesion ] |
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Recuperar contrasena                       |  |
|  +--------------------------------------------+  |
|                                         20 / 200 |
|  [ Generar historia ]                            |
|                                                  |
|  [ Vista previa ] [ Markdown ]                   |
|  +--------------------------------------------+  |
|  | Como analista de negocio, quiero ...,      |  |
|  | para ...                                   |  |
|  | Criterios de aceptacion (2 a 3, Gherkin)   |  |
|  +--------------------------------------------+  |
|  [ Copiar Markdown ]                             |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: igual que el estado cargando, más dos pestañas (Vista previa y Markdown), un recuadro con la historia y los criterios en Gherkin y un botón "Copiar Markdown". -->

Fuente: AC2.1.1 a AC2.1.3, AC3.1.1, AC4.1.1 y AC4.1.2 de `stories.md`.

### Estado copiado

```
+--------------------------------------------------+
|  ...                                             |
|  [ Copiar Markdown ]  (ok) Markdown copiado      |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: junto al botón Copiar Markdown aparece un mensaje con icono de confirmación que dice "Markdown copiado". -->

Fuente: AC4.1.2 de `stories.md`. El mensaje desaparece solo; su duración se fija en Construction.

### Estado error del servicio

```
+--------------------------------------------------+
| Business Analyst Agent         [ Cerrar sesion ] |
+--------------------------------------------------+
|                                                  |
|  Titulo de la funcionalidad                      |
|  +--------------------------------------------+  |
|  | Recuperar contrasena                       |  |
|  +--------------------------------------------+  |
|                                         20 / 200 |
|  (x) No se pudo generar la historia.             |
|      Intenta de nuevo en unos segundos.          |
|  [ Reintentar ]                                  |
|                                                  |
+--------------------------------------------------+
```
<!-- Text fallback: el título escrito se conserva; debajo aparece un mensaje de error con icono que explica que no se pudo generar la historia y un botón "Reintentar". -->

Fuente: AC5.1.2 y AC5.1.3 de `stories.md`.

## S2 en móvil (estado con resultado)

```
+------------------------------+
| Business Analyst Agent  [=]  |
+------------------------------+
|                              |
| Titulo de la funcionalidad   |
| +--------------------------+ |
| | Recuperar contrasena     | |
| +--------------------------+ |
|                     20 / 200 |
| [   Generar historia     ]   |
|                              |
| [ Vista previa ][ Markdown ] |
| +--------------------------+ |
| | Como analista de         | |
| | negocio, quiero ...      | |
| +--------------------------+ |
| [   Copiar Markdown      ]   |
|                              |
+------------------------------+
```
<!-- Text fallback: en móvil todo se apila en una columna: el título con su contador, el botón Generar historia a todo el ancho, las dos pestañas, el recuadro del resultado y el botón Copiar Markdown a todo el ancho. El icono [=] abre el menú con Cerrar sesion. -->

Fuente: RF Q5. En móvil, el botón Cerrar sesion pasa a un menú del encabezado ([=]); esa agrupación es una decisión de diseño de esta etapa y no una respuesta confirmada.

## Assumptions & Open Questions

- Los textos de todos los mensajes (error de acceso, validación, contexto, error del servicio, copiado) son borradores a confirmar.
- Abierto: el ancho exacto a partir del cual la pantalla pasa a una columna (la propuesta anterior era menos de 768 px) y la agrupación de Cerrar sesion en un menú en móvil.
- Abierto: límite y validación del campo de contexto (requisitos de `requirements.md` sin definir).
- Abierto: duración del mensaje "Markdown copiado" y expiración de la sesión a mitad de una generación.
