# Contract Summary — Business Analyst Agent

Documentos de entrada: `unit-of-work.md`, `unit-of-work-dependency.md`, `components.md` y `requirements.md`. Respuestas: `contract-design-questions.md` (CD Qn). Decisiones previas: `decisions.md` (ADR-NNN).

Un contrato es el acuerdo en una frontera: qué datos cruzan, con qué forma, por qué medio y qué pasa cuando algo falla. El sistema no expone ninguna API a consumidores fuera de él distinto de su propia interfaz, así que los contratos son los que unen unidades. Las unidades se llaman por su ID: U1 `u1-walking-skeleton`, U2 `u2-model-gateway`, U3 `u3-story-generator`, U4 `u4-access-control`, U5 `u5-web-app` y U6 `u6-infrastructure`.

## Contracts

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---------------|----------|-----------|-------|
| C1 | U3 (u3-story-generator) | U5 (u5-web-app) | HTTP con JSON (REST), una sola operación `POST /v1/stories` (CD Q1, Q3) | U3 |
| C2 | U4 (u4-access-control) | U5 (u5-web-app) | HTTP con JSON (REST) para la identidad de la sesión, con la credencial en cada solicitud (CD Q7) | U4 |
| C3 | U4 (u4-access-control) | U3 (u3-story-generator) | Llamada directa dentro del servicio, a través de una interfaz tipada (CD Q8) | U4 |
| C4 | U2 (u2-model-gateway) | U3 (u3-story-generator) | Llamada directa dentro del servicio, a través de una interfaz tipada (CD Q8) | U2 |

U6 (u6-infrastructure) no es proveedora ni consumidora de un contrato de datos: despliega las dos piezas. Los contratos C3 y C4 se definen en esta etapa y los entrega U1 como interfaces y como un modelo simulado, para que U3, U4 y U2 se construyan en paralelo (ver "Reglas de propiedad").

## C1 — Generar la historia (U3 → U5)

Una sola operación que valida el título, pide contexto si hace falta, genera y devuelve el Markdown ya armado (CD Q1, Q2; ADR-005). La respuesta lleva solo el Markdown y un identificador de la solicitud (CD Q2). Cada solicitud lleva la credencial de la sesión (CD Q7). Los errores traen un código estable, un mensaje en español y si se puede reintentar (CD Q4).

```yaml
openapi: 3.0.3
info:
  title: Business Analyst Agent - generacion de historias
  version: v1
paths:
  /v1/stories:
    post:
      summary: Genera una historia de usuario con criterios en Gherkin a partir de un titulo
      security:
        - sessionCredential: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/StoryRequest'
      responses:
        '200':
          description: Historia generada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StoryResponse'
        '400':
          description: Titulo vacio o con mas de 200 caracteres, o contexto con mas de 500 caracteres (codigos TITLE_EMPTY, TITLE_TOO_LONG, CONTEXT_TOO_LONG)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Sin sesion valida (codigo SESSION_INVALID)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Sesion valida de una cuenta que no esta en la lista de correos permitidos (codigo ACCOUNT_NOT_ALLOWED; cambio aditivo de u4-access-control)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Titulo muy corto o ambiguo; se pide contexto (codigo NEEDS_CONTEXT)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Limite de uso de la pasarela superado (codigo RATE_LIMITED, retryable verdadero; cambio aditivo registrado en u1-walking-skeleton Code Generation Step 2; lo produce solo el limite de uso de la pasarela, sin requestId)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '502':
          description: Fallo del modelo o respuesta no interpretable (codigos MODEL_FAILURE, INVALID_MODEL_RESPONSE)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '504':
          description: La generacion supero el tiempo maximo (codigo GENERATION_TIMEOUT)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
components:
  securitySchemes:
    sessionCredential:
      type: http
      scheme: bearer
  schemas:
    StoryRequest:
      type: object
      required: [title]
      properties:
        title:
          type: string
          minLength: 1
          maxLength: 200
        context:
          type: string
          maxLength: 500
          description: Opcional; vacio equivale a ausente (cambio aditivo de u3-story-generator)
    StoryResponse:
      type: object
      required: [requestId, markdown]
      properties:
        requestId:
          type: string
        markdown:
          type: string
    Error:
      type: object
      required: [code, message, retryable]
      properties:
        code:
          type: string
        message:
          type: string
          description: Mensaje en espanol para mostrar a la persona
        retryable:
          type: boolean
        requestId:
          type: string
```

**Tiempos y reintentos (CD Q5, Q6; NFR1):** el modelo se corta a los 50 segundos, el servicio responde antes de los 60 y la interfaz espera hasta 60. El servicio hace como máximo un reintento automático ante un fallo pasajero del modelo, solo si queda tiempo dentro del máximo; con el corte a 50 segundos eso significa que el reintento aplica a fallos rápidos y no a un tiempo de espera agotado. Un error de tiempo agotado se informa con `retryable: true` y la persona reintenta con el botón.

**Cambios de contrato C1 de u3-story-generator (aditivos, registrados al inicio de Code Generation, antes de escribir código que los use):**

- Nuevo código de error `CONTEXT_TOO_LONG` (HTTP 400, `retryable` falso) cuando el contexto, recortado, supera 500 caracteres (BR3.3). Un contexto de exactamente 500 es válido; vacío equivale a ausente.
- El código `NEEDS_CONTEXT` (HTTP 422, `retryable` falso) ya estaba en C1; u3 lo implementa en el servicio con el umbral de BR3.2.
- Pregunta abierta de C1 cerrada (umbral de `NEEDS_CONTEXT`): se pide contexto cuando el título recortado tiene menos de 2 palabras o menos de 12 caracteres y no viene un contexto no vacío ("Login" pide contexto; "Recuperar contraseña" se genera). El umbral es un ajuste a la respuesta FD Q1 que la persona aún debe confirmar. El servicio no guarda estado: la pantalla pide el contexto una sola vez y reenvía el mismo título con el contexto.
- Pregunta abierta de C1 cerrada (límite del contexto): máximo 500 caracteres Unicode después de recortar; la longitud se mide en puntos de código.
- Cambio coordinado de las listas cerradas de u1 (observabilidad): el código `CONTEXT_TOO_LONG` (y `NEEDS_CONTEXT`) en la lista de códigos, y los campos de registro `u3DurationMs` e `internal_error`.

**Comportamiento del contenido:** el texto del título se trata como dato (FR2.5) y el Markdown devuelto tiene escapados los caracteres del título que tendrían significado en Markdown (FR4.4; `requirements.md`). El servicio no registra el contenido (NFR4).

## C2 — Identidad de la sesión (U4 → U5)

La interfaz inicia la sesión con Gmail u Outlook y recibe una credencial de la sesión, que envía en cada solicitud a C1 (CD Q7). Este contrato fija solo lo que la interfaz necesita para mostrar el estado de sesión y cerrarla. El detalle del flujo de inicio de sesión con los proveedores se define en Functional Design.

```yaml
openapi: 3.0.3
info:
  title: Business Analyst Agent - sesion
  version: v1
paths:
  /v1/session:
    get:
      summary: Devuelve la identidad de la sesion actual
      security:
        - sessionCredential: []
      responses:
        '200':
          description: Sesion valida
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Sin sesion valida (codigo SESSION_INVALID)
        '403':
          description: Cuenta no permitida (codigo ACCOUNT_NOT_ALLOWED; cambio aditivo de u4-access-control)
    delete:
      summary: Cierra la sesion actual
      security:
        - sessionCredential: []
      responses:
        '204':
          description: Sesion cerrada
        '401':
          description: Sin sesion valida (codigo SESSION_INVALID)
        '403':
          description: Cuenta no permitida (codigo ACCOUNT_NOT_ALLOWED; cambio aditivo de u4-access-control)
components:
  securitySchemes:
    sessionCredential:
      type: http
      scheme: bearer
  schemas:
    Session:
      type: object
      required: [sessionId, accountId, provider, expiresAt]
      properties:
        sessionId:
          type: string
        accountId:
          type: string
          description: Identificador estable de la cuenta (claim sub); nunca el correo
        provider:
          type: string
          enum: [google, microsoft]
        expiresAt:
          type: string
          format: date-time
```

## C3 — Verificar la sesión (U4 → U3)

Interfaz tipada dentro del servicio (CD Q8; ADR-006). U3 la llama antes de generar y rechaza la solicitud si la sesión no es válida.

```yaml
interface: SessionVerifier
owner: u4-access-control
operations:
  verifySession:
    input:
      credential: string
    output:
      one_of:
        - Session:
            sessionId: string
            accountId: string
            provider: string
            expiresAt: datetime
        - SessionInvalid:
            reason: enum [missing, malformed, bad_signature, wrong_issuer, wrong_audience, expired, wrong_token_use, keys_unavailable, not_configured, account_not_allowed, unknown]
```

**Cambios de contrato C1, C2 y C3 de u4-access-control (aditivos, registrados al inicio de Code Generation, antes de escribir código que los use):**

- Nuevo código de error `ACCOUNT_NOT_ALLOWED` (HTTP 403, `retryable` falso) en C1 y C2: sesión válida de una cuenta que no está en la lista de correos permitidos (BR4.3). Solo este motivo devuelve 403; todos los demás rechazos de token devuelven el mismo 401 SESSION_INVALID.
- C2: `GET /v1/session` y `DELETE /v1/session` pueden responder 403; `Session` gana `accountId` (claim `sub`, nunca el correo).
- C3: `SessionInvalid.reason` pasa de texto libre a una lista cerrada de once valores: missing, malformed, bad_signature, wrong_issuer, wrong_audience, expired, wrong_token_use, keys_unavailable, not_configured, account_not_allowed y unknown. u3 traduce `account_not_allowed` a ACCOUNT_NOT_ALLOWED (403) y los demás motivos a SESSION_INVALID (401).
- Cambio coordinado de las listas cerradas de u1 (observabilidad): el código `ACCOUNT_NOT_ALLOWED` en la lista de códigos, los campos de registro `authOutcome` y `authDurationMs`, y el motivo `unknown`.

## C4 — Llamar al modelo (U2 → U3)

Interfaz tipada dentro del servicio (CD Q8; ADR-002). U3 envía una petición ya armada y recibe la respuesta del modelo configurado, sin interpretar su contenido.

```yaml
interface: ModelClient
owner: u2-model-gateway
operations:
  invoke:
    input:
      prompt: string
      timeoutSeconds: number
    output:
      one_of:
        - ModelResponse:
            text: string
            modelId: string
        - ModelError:
            kind: enum [transient, timeout, unavailable, access_denied]
            message: string
            reason: enum [access_not_enabled, model_not_found, invalid_request, timeout, throttled, unavailable, unknown]  # opcional
```

**Cambios de contrato C4 de u2-model-gateway (aditivos, registrados al inicio de Code Generation, antes de escribir código que los use):**

- `timeoutSeconds` pasa de entero a número (puede tener fracciones; BR2.6). El código de u1 ya lo trata como decimal; el cambio es solo del contrato.
- `ModelError` gana el campo opcional `reason`, de lista cerrada y sin texto de AWS (BR2.3, BR2.4): `access_not_enabled`, `model_not_found`, `invalid_request`, `timeout`, `throttled`, `unavailable`, `unknown`. Los consumidores que no lo conocen lo ignoran; `kind` sigue fijando la indicación de reintento (BR2.7).
- Pregunta abierta de C4 cerrada: el tiempo de espera por modelo es de 50 segundos para Claude Sonnet y para Amazon Titan (NFR1.2).

## Reglas de propiedad

- Cada contrato lo posee la unidad proveedora (columna Owner de la tabla). Un cambio incompatible lo acuerdan el proveedor y el consumidor antes de construirse (CD Q3).
- C1 y C2 llevan la versión en la dirección (`/v1`): un cambio incompatible crea `/v2` y se mantiene `/v1` hasta migrar la interfaz (CD Q3). Un cambio aditivo (un campo nuevo) es seguro porque los consumidores ignoran los campos que no conocen.
- C3 y C4 son interfaces dentro del mismo servicio, sin versión de red; un cambio en ellas se coordina entre U3, U4 y U2 en el mismo cambio.
- **Lo que entrega U1 para que las unidades se construyan en paralelo:** las interfaces C3 y C4 y un modelo simulado que responde a `ModelClient`, junto con la forma de C1. Con eso, U3 se prueba sin U2 ni U4, y U5 se prueba contra un servicio simulado sin U3 ni U4. Este contrato recoge ese entregable como responsabilidad de U1.

## Open questions

| Contract | Question | Blocks |
|----------|----------|--------|
| C1 | ~~Umbral de `NEEDS_CONTEXT`~~ Cerrada en u3: menos de 2 palabras o menos de 12 caracteres, una sola vez (lo garantiza la pantalla) | cerrada |
| C1 | ~~Límite y validación del contexto~~ Cerrada en u3: máximo 500 caracteres, vacío equivale a ausente, `CONTEXT_TOO_LONG` 400 | cerrada |
| C1 | Si la respuesta debe llevar también el modelo usado, para la evaluación de modelos | U2, U3 |
| C2 | Flujo exacto de inicio de sesión con Gmail y Outlook y forma de la credencial | U4, U5 |
| C2 | Qué cuentas pueden entrar (cualquiera, una lista o un dominio) | U4 |
| C2 | Qué ve la persona si la sesión expira a mitad de una generación | U4, U5 |
| C3 | Cómo U4 responde ante una credencial caducada o revocada | U3, U4 |
| C4 | Valores de tiempo de espera del modelo por cada modelo (Amazon Titan y Claude Sonnet) | U2 |

## Assumptions & Open Questions

- Supuesto: el servicio y la interfaz se comunican por HTTP con JSON, porque el pedido original nombra un API Gateway; la tecnología exacta se fija en NFR Design.
- Supuesto: los códigos de error son un conjunto inicial (TITLE_EMPTY, TITLE_TOO_LONG, NEEDS_CONTEXT, SESSION_INVALID, MODEL_FAILURE, INVALID_MODEL_RESPONSE, GENERATION_TIMEOUT); se completan en Functional Design.
- Supuesto: el grafo de dependencias aprobado en Units Generation (U2 a U6 dependen solo de U1) se sostiene únicamente si U1 entrega las interfaces C3 y C4 y el modelo simulado; si no, hay que añadir las dependencias entre U3, U2, U4 y U5. Delivery Planning debe confirmarlo.
- Abierto: reparto del máximo de 60 segundos en el cliente de la interfaz (qué mensaje muestra a los 60 segundos) y política de reintentos de la interfaz.

## Requisitos de alojamiento de la interfaz (entregados a u6-infrastructure por u5-web-app)

- La pantalla se sirve por HTTPS con la cabecera `Content-Security-Policy` exacta de `security-requirements.md` NFR5.4 de u5 (estilos en línea permitidos solo por MUI, y `font-src 'self' data:` con emotion; scripts sin código en línea) y `frame-ancestors 'none'`.
- El cliente de Cognito es público (sin secreto), usa código con PKCE y registra como dirección de retorno y de cierre de sesión la raíz del sitio, valor exacto.
- Los destinos de conexión permitidos son el origen del servicio, el dominio alojado del grupo de usuarios y el servicio de identidad de Cognito de la región.
- Los proveedores de identidad del grupo de usuarios se llaman exactamente `Google` y `Microsoft` (la pantalla los envía como `identity_provider` y el servicio los reconoce como `google` y `microsoft`).
