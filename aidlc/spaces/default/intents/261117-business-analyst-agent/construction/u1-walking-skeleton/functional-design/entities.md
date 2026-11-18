# Entities — u1-walking-skeleton

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`.

U1 es el esqueleto ambulante: la versión mínima que corre de principio a fin. Aquí solo se definen las entidades que el corte delgado necesita; el modelo completo lo amplían las demás unidades. Ninguna entidad se guarda (`requirements.md`, NFR4). Los nombres siguen el código nuevo, en inglés (`team-practices.md`, Code Style).

```yaml
entities:
  - name: StoryRequest
    description: La solicitud de generar una historia, creada por la interfaz y recibida por el servicio.
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
        constraints: [no vacío después de quitar espacios]
    constraints:
      - El esqueleto no usa el campo de contexto; lo agrega u3-story-generator.
    relationships: []

  - name: StoryResult
    description: El resultado de la generación que el servicio devuelve a la interfaz.
    owner: StoryGenerator
    attributes:
      - name: requestId
        logical_type: text
        required: true
        references: StoryRequest.requestId
      - name: markdown
        logical_type: text
        required: true
        constraints: [empieza con "Como analista de negocio"]
    constraints:
      - El resultado contiene solo el Markdown y el identificador de la solicitud (contrato C1).
    relationships:
      - target: StoryRequest
        cardinality: "1 a 1"
        direction: StoryResult responde a StoryRequest

  - name: ModelResponse
    description: La respuesta del modelo de IA, tal como la devuelve el acceso al modelo.
    owner: ModelGateway
    attributes:
      - name: text
        logical_type: text
        required: true
      - name: modelId
        logical_type: text
        required: true
    constraints:
      - Es un dato de entrada del servicio; el servicio no interpreta nada más que el texto en el esqueleto.
    relationships: []

  - name: ModelError
    description: Un fallo del acceso al modelo, traducido a un error propio.
    owner: ModelGateway
    attributes:
      - name: kind
        logical_type: text
        required: true
        allowed_values: [transient, timeout, unavailable, access_denied]
      - name: message
        logical_type: text
        required: true
    constraints:
      - Los valores de kind son los del contrato C4.
    relationships: []

  - name: Session
    description: La sesión que devuelve el verificador de sesión (contrato C3); en el esqueleto la entrega el verificador simulado.
    owner: AccessControl
    attributes:
      - name: sessionId
        logical_type: text
        required: true
        unique: true
      - name: accountId
        logical_type: text
        required: true
      - name: provider
        logical_type: text
        required: true
        allowed_values: [google, microsoft]
      - name: expiresAt
        logical_type: datetime
        required: true
    constraints:
      - Los atributos son los que define el contrato C3; el verificador simulado entrega valores fijos de prueba.
      - En el esqueleto no hay inicio de sesión real; la verificación real la agrega u4-access-control.
    relationships: []

  - name: SessionInvalid
    description: El resultado de verificar una credencial que no corresponde a una sesión válida (contrato C3).
    owner: AccessControl
    attributes:
      - name: reason
        logical_type: text
        required: true
    constraints:
      - El servicio traduce este resultado al error SESSION_INVALID del contrato C1.
    relationships: []
```

## Resumen

U1 trabaja con seis entidades: la solicitud y el resultado (en StoryGenerator), la respuesta y el error del modelo (en ModelGateway) y la sesión y el resultado de sesión inválida (en AccessControl, con la forma del contrato C3). Los demás atributos de `components.md` que el esqueleto no usa (por ejemplo `context`, `role`, `action`, `benefit` y `criteria`) los agregan las unidades que los usan.

## Assumptions & Open Questions

- Abierto: formato del identificador de la solicitud (`requestId`); se fija en Code Generation.
- Supuesto: el campo `markdown` del resultado es lo único que el esqueleto devuelve; la interfaz lo muestra tal cual.
