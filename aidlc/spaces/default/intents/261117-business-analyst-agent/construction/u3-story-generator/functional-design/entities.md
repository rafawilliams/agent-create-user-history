# Entities — u3-story-generator

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Respuestas: `functional-design-questions.md` (FD Qn). Base: las entidades de `u1-walking-skeleton` (`StoryRequest` con `requestId` y `title`, y `StoryResult` con `requestId` y `markdown`) que u3 amplía sin cambiar su forma externa. Los nombres siguen el código nuevo, en inglés.

Ninguna entidad se guarda (NFR4). Todas viven en memoria durante la solicitud.

```yaml
entities:
  - name: StoryRequest
    description: La solicitud de generar una historia, recibida por el servicio (ampliada con el contexto opcional).
    owner: StoryGenerator
    attributes:
      - name: requestId
        logical_type: text
        required: true
        unique: true
        constraints: [identificador generado por el servicio para cada solicitud]
      - name: title
        logical_type: text
        required: true
        constraints: [sin espacios al inicio ni al final; de 1 a 200 caracteres después de recortar]
      - name: context
        logical_type: text
        required: false
        constraints: [sin espacios al inicio ni al final; vacío equivale a ausente; máximo 500 caracteres]
    constraints:
      - El título y el contexto son datos del analista; nunca son instrucciones para el modelo (BR3.4).
    relationships: []

  - name: StoryDraft
    description: La historia y los criterios que el modelo propone, ya validados, antes de armar el Markdown.
    owner: StoryGenerator
    attributes:
      - name: action
        logical_type: text
        required: true
        constraints: [no vacío después de recortar]
      - name: benefit
        logical_type: text
        required: true
        constraints: [no vacío después de recortar]
      - name: criteria
        logical_type: text
        required: true
        constraints: [de 2 a 3 elementos Criterion]
    constraints:
      - El rol no es un atributo del borrador: siempre es "analista de negocio" y lo fija el servicio (BR3.5).
    relationships:
      - target: Criterion
        cardinality: "1 a 2..3"
        direction: StoryDraft contiene Criterion

  - name: Criterion
    description: Un criterio de aceptación con sus tres partes del Gherkin.
    owner: StoryGenerator
    attributes:
      - name: name
        logical_type: text
        required: true
        constraints: [no vacío; una sola línea]
      - name: given
        logical_type: text
        required: true
        constraints: [no vacío; una sola línea]
      - name: when
        logical_type: text
        required: true
        constraints: [no vacío; una sola línea]
      - name: then
        logical_type: text
        required: true
        constraints: [no vacío; una sola línea]
    constraints:
      - Las palabras clave Dado, Cuando y Entonces y la línea de idioma las agrega el servicio, no el modelo (BR3.9).
    relationships: []

  - name: StoryResult
    description: El resultado que se devuelve a la interfaz (entidad de u1, sin cambios de forma externa).
    owner: StoryGenerator
    attributes:
      - name: requestId
        logical_type: text
        required: true
        references: StoryRequest.requestId
      - name: markdown
        logical_type: text
        required: true
        constraints: [armado por el servicio con la estructura de BR3.9]
    constraints:
      - El resultado contiene solo el Markdown y el identificador de la solicitud (contrato C1).
    relationships:
      - target: StoryRequest
        cardinality: "1 a 1"
        direction: StoryResult responde a StoryRequest

  - name: PromptTemplate
    description: El texto de las instrucciones al modelo, editable sin cambiar el código (ADR-003).
    owner: StoryGenerator
    attributes:
      - name: instructions
        logical_type: text
        required: true
        constraints: [vive en configuración; pide la respuesta en JSON y el contenido del analista dentro de delimitadores]
    constraints:
      - Las instrucciones quedan fuera del contenido del analista (BR3.4).
    relationships: []
```

## Resumen

u3 trabaja con cinco entidades: la solicitud ampliada con el contexto, el borrador validado del modelo (`StoryDraft` con sus `Criterion`), el resultado y la plantilla de instrucciones. El rol, las palabras clave del Gherkin y la estructura del Markdown no los decide el modelo: los fija el servicio.

## Assumptions & Open Questions

- Supuesto: `StoryDraft` y `Criterion` son entidades internas, no cruzan el contrato C1.
- Abierto: nombre exacto de los campos del JSON que se pide al modelo; se fija en Code Generation.
