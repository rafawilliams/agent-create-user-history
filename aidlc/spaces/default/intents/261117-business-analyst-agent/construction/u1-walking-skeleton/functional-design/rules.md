# Rules — u1-walking-skeleton

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Entidades: `entities.md`.

Las reglas de U1 son las mínimas para que el corte delgado corra de punta a punta. Las reglas completas de cada historia las agregan las demás unidades.

```yaml
rules:
  - id: BR1.1
    statement: La historia generada empieza con "Como analista de negocio".
    category: policy
    applies_to: StoryResult.markdown
    trigger: Cuando el servicio arma el resultado a partir de la respuesta del modelo
    logic: >
      SI la respuesta del modelo, sin espacios ni saltos de línea al inicio, no
      empieza con el texto exacto "Como analista de negocio" (se distingue
      entre mayúsculas y minúsculas)
      ENTONCES el servicio la trata como una respuesta fuera de contrato.
    violation: El servicio informa un error con código INVALID_MODEL_RESPONSE y retryable verdadero, y no muestra texto parcial.
    source: FR2.2

  - id: BR1.2
    statement: La historia tiene un rol, una acción y un beneficio relacionados con el título.
    category: policy
    applies_to: StoryResult.markdown
    trigger: Cuando se genera la historia
    logic: >
      SI el título es "Recuperar contraseña"
      ENTONCES la historia expresa una acción y un beneficio relacionados con recuperar una contraseña.
    violation: La relación con el título se comprueba revisando a mano; no hay comprobación automática en el esqueleto.
    source: FR2.1

  - id: BR1.3
    statement: Un título vacío o con solo espacios no se envía al modelo.
    category: validation
    applies_to: StoryRequest.title
    trigger: Cuando el servicio recibe la solicitud
    logic: >
      SI el título, sin espacios al inicio ni al final, está vacío
      ENTONCES el servicio no llama al modelo y devuelve un error.
    violation: Error con código TITLE_EMPTY (contrato C1).
    source: FR1.3

  - id: BR1.4
    statement: Un fallo del modelo se informa como error, nunca como un resultado vacío.
    category: constraint
    applies_to: ModelError
    trigger: Cuando el acceso al modelo devuelve un error
    logic: >
      SI el acceso al modelo devuelve un error ModelError
      ENTONCES el servicio devuelve el error de contrato C1 que corresponde a su
      tipo (kind): transient da MODEL_FAILURE (HTTP 502) con retryable verdadero;
      timeout da GENERATION_TIMEOUT (HTTP 504) con retryable verdadero;
      unavailable da MODEL_FAILURE (HTTP 502) con retryable verdadero;
      access_denied da MODEL_FAILURE (HTTP 502) con retryable falso, porque
      reintentar sin cambiar los permisos no ayuda.
    violation: Un fallo silencioso o un resultado vacío no se permite (guarda de Construction: los errores no pueden quedar sin informar).
    source: FR5.2

  - id: BR1.5
    statement: El verificador de sesión simulado solo existe para ejecuciones locales y pruebas; un entorno desplegado sin verificador real rechaza toda solicitud.
    category: authorization
    applies_to: Session
    trigger: Cuando el servicio recibe una solicitud de generación
    logic: >
      SI el servicio corre en local o en pruebas automáticas y se configura el
      verificador simulado explícitamente, ENTONCES se acepta la solicitud como
      si tuviera una sesión válida.
      SI el servicio corre en un entorno desplegado y no hay un verificador real
      configurado, ENTONCES no se usa el simulado y se rechaza toda solicitud
      con el error SESSION_INVALID (falla cerrado).
    violation: El verificador simulado no se enlaza por defecto ni en ningún entorno desplegado; un entorno desplegado sin verificador real no genera historias.
    source: FR6.1

  - id: BR1.6
    statement: La petición del esqueleto al modelo pide la historia y de 2 a 3 criterios de aceptación en Gherkin en español.
    category: policy
    applies_to: StoryRequest
    trigger: Cuando el servicio arma la petición al modelo
    logic: >
      SIEMPRE que se arma la petición, ENTONCES las instrucciones piden al modelo
      la historia y de 2 a 3 criterios en Gherkin en español con las palabras
      Dado, Cuando y Entonces. El esqueleto no comprueba que el modelo cumpla el
      conteo ni el idioma; esa comprobación la agrega u3-story-generator.
    violation: El esqueleto no detecta que el modelo incumpla el conteo o el idioma.
    source: FR2.3, FR2.4 y FR3.1 (decisión de la persona en Q2 de functional-design-questions.md)
```

## Resumen

| Regla | Qué fija | Categoría | Fuente |
|-------|----------|-----------|--------|
| BR1.1 | La historia empieza con "Como analista de negocio" | policy | FR2.2 |
| BR1.2 | Rol, acción y beneficio relacionados con el título | policy | FR2.1 |
| BR1.3 | Un título vacío no se envía al modelo | validation | FR1.3 |
| BR1.4 | Un fallo del modelo se informa como error | constraint | FR5.2 |
| BR1.5 | Verificador de sesión simulado solo en local y pruebas; desplegado sin verificador real, falla cerrado | authorization | FR6.1 |
| BR1.6 | La petición pide la historia y de 2 a 3 criterios en Gherkin en español | policy | FR2.3, FR2.4, FR3.1 |

BR1.5 no es una regla de negocio de la historia, sino una concesión del esqueleto para que corra sin inicio de sesión real: hace explícito cómo U1 corre aunque C1 pida una credencial. Se retira cuando u4-access-control agrega la verificación real.

## Assumptions & Open Questions

- Supuesto: BR1.2 se comprueba a mano en el esqueleto, porque comprobar la relación con el título requiere una revisión humana (NFR2).
- Abierto: el texto exacto de las instrucciones al modelo; viven en configuración (ADR-003) y las afina u3-story-generator.
