# Entities — u2-model-gateway

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Respuestas: `functional-design-questions.md` (FD Qn). Entidades heredadas de `u1-walking-skeleton/functional-design/entities.md`: `ModelResponse` y `ModelError`, que u1 dejó definidas y u2 amplía sin cambiar su forma. Los nombres siguen el código nuevo, en inglés.

Ninguna entidad se guarda en el servicio (NFR4). `EvaluationResult` y `EvaluationRecord` viven solo en el archivo de evaluación del equipo (FD Q3), con títulos de ejemplo, nunca con contenido de personas.

```yaml
entities:
  - name: ModelProfile
    description: La descripción de un modelo que el acceso al modelo sabe usar, elegida por configuración.
    owner: ModelGateway
    attributes:
      - name: modelId
        logical_type: text
        required: true
        unique: true
        constraints: [identificador del modelo o del perfil de inferencia en Amazon Bedrock]
      - name: provider
        logical_type: text
        required: true
        allowed_values: [anthropic, amazon]
      - name: region
        logical_type: text
        required: true
        defaults: us-east-1
    constraints:
      - El proveedor se deduce del identificador del modelo (anthropic para Claude Sonnet, amazon para Amazon Titan); un identificador de otro proveedor no es un perfil válido.
    relationships: []

  - name: ModelResponse
    description: La respuesta del modelo, tal como la devuelve el acceso al modelo (entidad de u1, sin cambios).
    owner: ModelGateway
    attributes:
      - name: text
        logical_type: text
        required: true
      - name: modelId
        logical_type: text
        required: true
        references: ModelProfile.modelId
    constraints:
      - El acceso al modelo no interpreta el texto; solo lo devuelve (BR2.5).
    relationships:
      - target: ModelProfile
        cardinality: "muchos a 1"
        direction: ModelResponse la produjo un ModelProfile

  - name: ModelError
    description: Un fallo del acceso al modelo, traducido a un error propio (entidad de u1, sin cambios de forma).
    owner: ModelGateway
    attributes:
      - name: kind
        logical_type: text
        required: true
        allowed_values: [transient, timeout, unavailable, access_denied]
      - name: message
        logical_type: text
        required: true
      - name: reason
        logical_type: text
        required: false
        allowed_values: [access_not_enabled, model_not_found, invalid_request, timeout, throttled, unavailable, unknown]
    constraints:
      - El mensaje es propio y no copia el detalle de AWS (BR2.4).
      - El motivo (reason) es un campo opcional nuevo de u2, de lista cerrada y sin texto de AWS; el servicio puede ignorarlo (cambio aditivo de C4, BR2.3).
    relationships: []

  - name: EvaluationResult
    description: El resultado de un modelo para un título de ejemplo en la evaluación de US7.1.
    owner: ModelGateway
    attributes:
      - name: modelId
        logical_type: text
        required: true
        references: ModelProfile.modelId
      - name: title
        logical_type: text
        required: true
      - name: outcome
        logical_type: text
        required: true
        allowed_values: [generated, blocked, failed]
      - name: text
        logical_type: text
        required: false
        constraints: [presente solo cuando outcome es generated]
      - name: formatOk
        logical_type: boolean
        required: false
        constraints: [presente solo cuando outcome es generated; cumple el formato automático de BR2.8]
      - name: elapsedSeconds
        logical_type: number
        required: false
      - name: reason
        logical_type: text
        required: false
        allowed_values: [access_not_enabled, model_not_found, invalid_request, timeout, throttled, unavailable, unknown]
        constraints: [presente solo cuando outcome es blocked o failed; es el motivo de lista cerrada de ModelError (BR2.3), nunca texto de AWS (BR2.4)]
    constraints:
      - Hay un EvaluationResult por cada combinación de modelo y título (AC7.1.1).
    relationships:
      - target: ModelProfile
        cardinality: "muchos a 1"
        direction: EvaluationResult es de un ModelProfile

  - name: EvaluationRecord
    description: El registro de la evaluación terminada, con el resultado de cada modelo y la decisión (AC7.1.2).
    owner: ModelGateway
    attributes:
      - name: evaluatedAt
        logical_type: datetime
        required: true
      - name: titles
        logical_type: text
        required: true
        constraints: [lista de los 5 títulos de ejemplo aprobados por la persona]
      - name: results
        logical_type: text
        required: true
        references: EvaluationResult
      - name: decision
        logical_type: text
        required: true
        constraints: [el modelo elegido y por qué, con el criterio de BR2.8; o "pendiente" si algún modelo evaluado está bloqueado o todos lo están, y en ese caso el modelo por defecto sigue en uso]
      - name: pendingAccess
        logical_type: text
        required: false
        constraints: [modelos bloqueados cuyo acceso queda por solicitar (AC7.1.3)]
    constraints:
      - El registro se guarda como archivo del equipo, no en el servicio.
    relationships:
      - target: EvaluationResult
        cardinality: "1 a muchos"
        direction: EvaluationRecord agrupa EvaluationResult
```

## Resumen

u2 define cinco entidades: el perfil del modelo (`ModelProfile`), las dos entidades que u1 dejó (`ModelResponse` y `ModelError`, sin cambios de forma) y las dos de la evaluación (`EvaluationResult` y `EvaluationRecord`). `ModelProfile` solo existe en configuración; el servicio no guarda nada.

## Assumptions & Open Questions

- Supuesto: el proveedor se deduce del identificador (`anthropic.`, `us.anthropic.`, `global.anthropic.` o `amazon.`, `us.amazon.`); no se agrega un campo de configuración aparte.
- Abierto: el identificador exacto de Amazon Titan a evaluar y su disponibilidad en la cuenta; se fija en Code Generation al ver los perfiles de la cuenta.
- Supuesto: `EvaluationResult` guarda el texto generado de los 5 títulos de ejemplo, que son inventados y no contienen datos reales (BR2.9).
