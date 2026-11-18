# Rules — u3-story-generator

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Entidades: `entities.md`. Respuestas: `functional-design-questions.md` (FD Qn).

u3 completa la generación: valida la entrada, pide contexto, trata el título como dato, interpreta la respuesta del modelo y arma el Markdown. El plazo de 55 segundos, el reintento único y la verificación de sesión siguen siendo del servicio de u1; el acceso al modelo es de u2.

```yaml
rules:
  - id: BR3.1
    statement: El título se valida antes de llamar al modelo.
    category: validation
    applies_to: StoryRequest.title
    trigger: Cuando el servicio recibe la solicitud
    logic: >
      SI el título, sin espacios al inicio ni al final, está vacío ENTONCES no se llama
      al modelo y se devuelve el error TITLE_EMPTY. SI el título recortado tiene más de
      200 caracteres ENTONCES no se llama al modelo y se devuelve TITLE_TOO_LONG con el
      máximo de 200 en el mensaje. Un título de exactamente 200 caracteres es válido.
      SI el título es válido ENTONCES continúa la generación.
    violation: Un título vacío o de 201 caracteres que llega al modelo incumple esta regla.
    source: FR1.1, FR1.2, FR1.3

  - id: BR3.2
    statement: Un título muy corto o ambiguo pide contexto, y se pide una sola vez.
    category: validation
    applies_to: StoryRequest
    trigger: Cuando el título es válido
    logic: >
      La longitud se mide en caracteres Unicode (puntos de código) después de recortar los
      espacios (cualquier espacio Unicode) al inicio y al final; una palabra es una
      secuencia de caracteres sin espacios, separada por uno o más espacios. SI el título
      tiene menos de 2 palabras o menos de 12 caracteres, Y no viene un contexto no vacío
      ENTONCES no se llama al modelo y se devuelve NEEDS_CONTEXT (HTTP 422) con un mensaje
      que pide contexto. "Login" (1 palabra, 5 caracteres) pide contexto; "Recuperar
      contraseña" (2 palabras, 20 caracteres, el ejemplo de AC2.1.1) se genera. SI viene
      un contexto no vacío ENTONCES se genera aunque el título siga siendo corto. "Una
      sola vez" lo garantiza la pantalla (u5-web-app), que reenvía el mismo título con el
      contexto; el servicio no guarda estado y cualquier contexto no vacío desbloquea la
      generación. Un título que cumple ambos mínimos nunca pide contexto.
    violation: Una historia generada a partir de "Login" sin contexto incumple esta regla; que la pantalla pida contexto una segunda vez es de u5-web-app.
    source: FR1.4

  - id: BR3.3
    statement: El contexto es opcional, tiene un máximo y vacío equivale a ausente.
    category: validation
    applies_to: StoryRequest.context
    trigger: Cuando la solicitud trae un campo de contexto
    logic: >
      SI el contexto, sin espacios al inicio ni al final, está vacío ENTONCES se trata
      como ausente (y BR3.2 puede pedirlo). SI el contexto recortado tiene más de 500
      caracteres ENTONCES no se llama al modelo y se devuelve CONTEXT_TOO_LONG (HTTP 400)
      con el máximo de 500 en el mensaje. Un contexto de exactamente 500 caracteres es
      válido.
    violation: Un contexto de más de 500 caracteres que llega al modelo incumple esta regla.
    source: FR1.4

  - id: BR3.4
    statement: El título y el contexto son datos, nunca instrucciones para el modelo.
    category: policy
    applies_to: PromptTemplate
    trigger: Cuando el servicio arma la petición al modelo
    logic: >
      SIEMPRE que se arma la petición, ENTONCES las instrucciones fijas (en configuración)
      van aparte del contenido del analista; el título y el contexto van dentro de
      delimitadores y las instrucciones dicen que ese contenido es solo un dato. Aunque el
      título pida cambiar las instrucciones, el formato o el idioma, el resultado se
      arma igual con BR3.6 y BR3.9: el formato de salida lo garantiza el servicio y no lo
      que diga el título. Si el contenido del analista contiene los delimitadores de la
      petición, se neutralizan antes de insertarlo reemplazando esas cadenas por un texto
      visible distinto, de modo que el contenido nunca pueda cerrar el delimitador.
    violation: Un título que cambie la estructura del resultado o inserte instrucciones en la petición incumple esta regla.
    source: FR2.5

  - id: BR3.5
    statement: El rol de la historia siempre es "analista de negocio" y lo fija el servicio.
    category: policy
    applies_to: StoryResult.markdown
    trigger: Cuando el servicio arma la historia
    logic: >
      SIEMPRE que se arma la historia, ENTONCES la línea es "Como analista de negocio,
      quiero {acción}, para {beneficio}", con la acción y el beneficio que propone el
      modelo; el modelo no decide el rol. La acción y el beneficio se espera que estén
      relacionados con el título; esa relación se revisa a mano con los títulos de
      prueba, no automáticamente.
    violation: Una historia con otro rol, o que no empieza con "Como analista de negocio", incumple esta regla.
    source: FR2.1, FR2.2

  - id: BR3.6
    statement: La respuesta del modelo debe ser un JSON con la estructura esperada; si no, es un fallo y no se muestra texto parcial.
    category: validation
    applies_to: StoryDraft
    trigger: Cuando el modelo responde
    logic: >
      SI el texto de la respuesta (sin el cerco de código que el modelo pudiera agregar)
      no es un JSON válido con una acción y un beneficio no vacíos y de 2 a 3 criterios,
      cada uno con nombre, dado, cuando y entonces no vacíos y de una sola línea ENTONCES
      el servicio informa INVALID_MODEL_RESPONSE (HTTP 502, reintentable) y no devuelve
      texto parcial. Solo se acepta un cerco de código alrededor del JSON; cualquier otro
      texto antes o después hace la respuesta inválida. Cada campo de texto tiene como
      máximo 300 caracteres (más de 300 hace la respuesta inválida), y un campo con saltos
      de línea se normaliza a una sola línea (los saltos pasan a espacios) antes de
      validar que no esté vacío y de usarse. SI cumple ENTONCES se continúa con
      BR3.9. Con menos de 2 o más de 3 criterios, la respuesta es inválida.
    violation: Mostrar un resultado armado con una respuesta incompleta, o con 1 o 4 criterios, incumple esta regla.
    source: FR2.3, FR5.3

  - id: BR3.7
    statement: Todo el texto generado está en español.
    category: policy
    applies_to: PromptTemplate
    trigger: Cuando se arma la petición
    logic: >
      SIEMPRE que se arma la petición, ENTONCES las instrucciones piden la respuesta en
      español. El servicio hace una comprobación mínima y automática: la acción y el
      beneficio deben contener al menos dos palabras comunes del español (por ejemplo "el",
      "la", "de", "que", "para", "poder", "quiero", "un", "una", "con") y, si no las
      contienen, la respuesta es inválida (INVALID_MODEL_RESPONSE, reintentable), así que
      una respuesta completa en inglés no llega a la persona. Es una heurística: no
      detecta un texto mezclado; la revisión del idioma de los títulos de prueba sigue
      siendo manual (NFR2). Las palabras clave y la línea de idioma del Gherkin las agrega
      el servicio en español.
    violation: Un resultado en otro idioma que se entrega sin revisión incumple esta regla.
    source: FR2.4

  - id: BR3.8
    statement: Los caracteres del título con significado en Markdown no rompen el formato del resultado.
    category: constraint
    applies_to: StoryResult.markdown
    trigger: Cuando el servicio arma el Markdown
    logic: >
      SIEMPRE que el título del analista aparece en el Markdown fuera del bloque de código,
      ENTONCES sus caracteres con significado en Markdown o en HTML (asterisco, guion bajo,
      corchetes, paréntesis, almohadilla, acento grave, mayor que, menor que, ampersand,
      barra vertical, tilde, barra invertida y el signo de exclamación) se escapan, y un
      guion, un signo más o un número seguido de punto al inicio de una línea también se
      escapan para que no se conviertan en una lista. El título y el contexto se
      normalizan a una sola línea (los saltos pasan a espacios) antes de usarse. El texto de la historia y de los criterios que propone
      el modelo se escapa de la misma forma fuera del bloque de código. Dentro del bloque
      de código no se escapa nada, y si el contenido incluye una secuencia de tres acentos
      graves, el cerco del bloque usa más acentos que la secuencia más larga que contenga.
    violation: Un título como "Exportar *todo* a [CSV]" que cambie el formato de la historia o cierre el bloque de código incumple esta regla.
    source: FR4.4

  - id: BR3.9
    statement: El Markdown final tiene una estructura fija y el Gherkin lo arma el servicio.
    category: policy
    applies_to: StoryResult.markdown
    trigger: Cuando el borrador es válido
    logic: >
      El Markdown tiene, en orden: un encabezado con el título del analista (escapado,
      BR3.8); la historia en una línea (BR3.5); una lista numerada con los nombres de los
      criterios; y un único bloque de código con el Gherkin completo, que empieza con la
      línea "# language: es" y, por cada criterio, un escenario con las palabras Dado,
      Cuando y Entonces que agrega el servicio delante de las partes que dio el modelo. La
      plantilla exacta del bloque es: la línea "# language: es"; la línea "Característica:"
      seguida del título del analista en una sola línea; y por cada criterio la línea
      "  Escenario:" con su nombre y, indentadas, las líneas "Dado", "Cuando" y "Entonces"
      con sus partes. El
      resultado es Markdown estándar que se pega en Jira conservando títulos, lista y
      bloque de código. El Gherkin se muestra tal como se arma, sin validación automática
      adicional (FR3.2).
    violation: Un resultado sin la línea de idioma, sin las tres palabras clave o con el Gherkin fuera de un bloque de código incumple esta regla.
    source: FR3.1, FR3.2, FR4.1

  - id: BR3.10
    statement: Un fallo del servicio o un plazo agotado se informa con el indicador de reintento y sin perder el título.
    category: constraint
    applies_to: StoryResult
    trigger: Cuando la generación falla o se agota el plazo
    logic: >
      SI el modelo falla, la respuesta no se puede interpretar o se agota el plazo de 55
      segundos ENTONCES el servicio devuelve el error de contrato con su indicación de
      reintento (tabla de errores de u1 y BR3.6), sin texto parcial; el título se conserva
      en la pantalla (u5-web-app). SI el servicio no falla ENTONCES el resultado llega
      dentro del plazo de 60 segundos de la interfaz.
    violation: Un fallo silencioso, un resultado parcial o una respuesta después de los 60 segundos incumple esta regla.
    source: FR5.2, FR5.3, NFR1
```

## Resumen

| Regla | Qué fija | Categoría | Fuente |
|-------|----------|-----------|--------|
| BR3.1 | El título se valida (1 a 200 caracteres) antes del modelo | validation | FR1.1, FR1.2, FR1.3 |
| BR3.2 | Título corto o ambiguo pide contexto, una sola vez | validation | FR1.4 |
| BR3.3 | Contexto opcional, máximo 500, vacío es ausente | validation | FR1.4 |
| BR3.4 | El título y el contexto son datos | policy | FR2.5 |
| BR3.5 | El rol "analista de negocio" lo fija el servicio | policy | FR2.1, FR2.2 |
| BR3.6 | La respuesta del modelo es un JSON con la estructura esperada | validation | FR2.3, FR5.3 |
| BR3.7 | Todo el texto generado en español | policy | FR2.4 |
| BR3.8 | Los caracteres de Markdown del título no rompen el formato | constraint | FR4.4 |
| BR3.9 | Estructura fija del Markdown; el Gherkin lo arma el servicio | policy | FR3.1, FR3.2, FR4.1 |
| BR3.10 | Los fallos se informan con indicador de reintento, sin texto parcial | constraint | FR5.2, FR5.3, NFR1 |

## Assumptions & Open Questions

- Ajuste a FD Q1 (pendiente de confirmar con la persona): la respuesta A decía "menos de 3 palabras o menos de 12 caracteres", pero eso habría pedido contexto para "Recuperar contraseña", el ejemplo de AC2.1.1 que debe generar. Se bajó el mínimo de palabras de 3 a 2 y se mantiene el de 12 caracteres: "Login" pide contexto y "Recuperar contraseña" se genera.
- Pendiente de comprobar con el editor de Jira real: la fidelidad del pegado (títulos, lista, bloque de código) se verifica a mano con un resultado de ejemplo; el Markdown es estándar.
- Decidido (FD Q2): contexto de máximo 500 caracteres, pedido una sola vez.
- Decidido (FD Q3): el modelo responde en JSON y el servicio lo valida.
- Decidido (FD Q4): un único bloque de código con el Gherkin completo.
- Cambios de contrato C1 (aditivos): el campo `context` ya existe en C1; lo nuevo es el código `CONTEXT_TOO_LONG` (HTTP 400) y el máximo de 500 del contexto. También se cierran las dos preguntas abiertas de C1 (umbral de NEEDS_CONTEXT y límite del contexto); se registran en `contract-summary.md` al inicio de Code Generation, antes de escribir código que los use.
- Supuesto: la relación de la acción y el beneficio con el título (AC2.1.1) y el idioma (AC2.1.3) se revisan a mano con el conjunto de títulos de prueba de NFR2; no hay comprobación automática.
- Abierto: el conjunto de títulos de prueba de NFR2 (pregunta abierta de `requirements.md`).
