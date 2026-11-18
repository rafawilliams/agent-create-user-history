# Rules — u2-model-gateway

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Entidades: `entities.md`. Respuestas: `functional-design-questions.md` (FD Qn).

Las reglas de u2 completan el acceso al modelo que u1 dejó mínimo: elegir el modelo por configuración, traducir fallos y tiempos de espera, y evaluar Titan frente a Claude Sonnet. u2 no interpreta el contenido de la respuesta (eso es de u3).

```yaml
rules:
  - id: BR2.1
    statement: El modelo que se usa se elige por configuración, entre Claude Sonnet y Amazon Titan, sin cambiar la lógica de generación.
    category: policy
    applies_to: ModelProfile
    trigger: Cuando el servicio arranca y arma el acceso al modelo
    logic: >
      SI la configuración da un identificador de modelo de proveedor anthropic o amazon
      ENTONCES el acceso al modelo usa ese modelo, y cualquier cambio de modelo se hace
      solo cambiando la configuración. SI no hay configuración, ENTONCES usa el modelo
      por defecto del proyecto.
    violation: Un cambio de modelo que obliga a tocar la lógica de generación incumple esta regla.
    source: FR7.1

  - id: BR2.2
    statement: Un identificador de modelo no soportado se rechaza al arrancar, no en la primera solicitud.
    category: validation
    applies_to: ModelProfile.modelId
    trigger: Cuando el servicio arma el acceso al modelo con su configuración
    logic: >
      SI el identificador del modelo no es de un proveedor soportado (anthropic o amazon)
      ENTONCES el servicio no arranca con ese acceso y informa un error de configuración
      que nombra el valor no soportado, sin llamar a AWS.
    violation: Un identificador no soportado no llega a una solicitud de una persona.
    source: FR7.1

  - id: BR2.3
    statement: Un fallo del servicio del modelo se traduce a uno de los cuatro tipos de error propios, nunca se deja pasar el error de AWS sin traducir.
    category: constraint
    applies_to: ModelError
    trigger: Cuando la llamada a Amazon Bedrock falla
    logic: >
      SI Bedrock indica límite de uso o fallo interno pasajero ENTONCES kind es transient.
      SI la llamada supera el tiempo de espera pedido, o la lectura de red se agota,
      ENTONCES kind es timeout. SI Bedrock indica servicio no disponible o no responde
      ENTONCES kind es unavailable. SI Bedrock indica acceso denegado, modelo no
      habilitado o no encontrado ENTONCES kind es access_denied (reintentar no ayuda).
      SI Bedrock indica petición no válida (los parámetros enviados no sirven para ese
      modelo) ENTONCES kind es access_denied también, porque C4 solo tiene cuatro tipos y
      reintentar no ayuda, pero el error lleva un motivo propio distinto (invalid_request).
      SI el código de error es otro y no se conoce ENTONCES kind es unavailable.
      Además de kind, el error lleva un motivo (reason) de una lista cerrada y propia, sin
      texto de AWS: access_not_enabled (acceso denegado o modelo no habilitado),
      model_not_found, invalid_request, timeout, throttled, unavailable, unknown. El motivo
      es un dato de u2 que el servicio puede ignorar; la evaluación lo usa para distinguir
      un modelo bloqueado de un parámetro rechazado.
    violation: Un error de AWS sin traducir, o uno traducido a un tipo equivocado, rompe el contrato C4 y la tabla de reintentos del servicio.
    source: FR5.2

  - id: BR2.4
    statement: El mensaje de un error del modelo es propio y no copia el detalle de AWS.
    category: constraint
    applies_to: ModelError.message
    trigger: Cuando se arma un ModelError
    logic: >
      SIEMPRE que se arma el error, ENTONCES el mensaje es el texto propio del tipo
      (por ejemplo "Fallo pasajero del modelo"); el detalle de AWS, que puede traer
      identificadores de cuenta o ARN, no se copia al mensaje, al motivo ni a los
      registros, ni al archivo de evaluación. Lo que la evaluación registra de un fallo es
      el tipo, el motivo de la lista cerrada de BR2.3 y el mensaje propio, nunca texto de
      AWS.
    violation: Un mensaje con un ARN o con datos de la cuenta es una fuga de información.
    source: NFR4

  - id: BR2.5
    statement: El acceso al modelo no interpreta el texto de la respuesta.
    category: constraint
    applies_to: ModelResponse.text
    trigger: Cuando el modelo responde
    logic: >
      SI el modelo responde ENTONCES el acceso devuelve el texto tal cual, aunque esté
      vacío o no tenga la estructura esperada; decidir si la respuesta sirve es de
      u3-story-generator (INVALID_MODEL_RESPONSE).
    violation: Una validación del contenido dentro del acceso al modelo mezcla responsabilidades de u2 y u3.
    source: FR5.2

  - id: BR2.6
    statement: El tiempo de espera de una llamada se respeta tal como lo pide el servicio, en segundos, incluso con fracciones.
    category: constraint
    applies_to: ModelClient.invoke
    trigger: Cuando el servicio pide una llamada con un tiempo de espera
    logic: >
      SI el servicio pide un tiempo de espera de N segundos (que puede ser un número con
      fracciones) ENTONCES la llamada no espera más de N segundos y, pasado ese tiempo,
      devuelve el error timeout. El contrato C4 lo define como número, no como entero
      (cambio aditivo respecto a la versión anterior de C4).
    violation: Una llamada que espera más de lo pedido hace que el servicio pierda el plazo de 55 segundos.
    source: NFR1.1, AC5.1.4

  - id: BR2.7
    statement: El tipo de error del modelo determina si reintentar puede ayudar; u2 no agrega un campo de reintento.
    category: policy
    applies_to: ModelError.kind
    trigger: Cuando el servicio convierte un ModelError en un error de contrato
    logic: >
      El tipo (kind) fija la indicación de reintento, y el servicio la deriva con la tabla
      de errores de u1: transient, timeout y unavailable se informan como reintentables
      para la persona (botón "Reintentar"); access_denied no. Esto no contradice que un
      tiempo agotado no se reintente de forma automática: el reintento automático lo
      decide el servicio con el plazo restante, y el indicador es para el reintento manual
      de la persona. ModelError no lleva un campo de reintento.
    violation: Un error no reintentable que ofrece "Reintentar" hace perder tiempo a la persona.
    source: AC5.1.2

  - id: BR2.8
    statement: La evaluación genera un resultado de cada modelo para cada título de ejemplo y decide por el cumplimiento automático del formato.
    category: policy
    applies_to: EvaluationRecord
    trigger: Cuando el equipo ejecuta la evaluación de modelos
    logic: >
      SI se evalúan los modelos con los 5 títulos de ejemplo aprobados ENTONCES hay un
      EvaluationResult por modelo y título, y el modelo por defecto del proyecto siempre
      está entre los evaluados. Cada resultado tiene un outcome: generated (el modelo
      respondió), blocked (BR2.10) o failed (el modelo no respondió por un error de tipo
      transient, timeout o unavailable, o por una petición no válida; la evaluación no
      reintenta). Un resultado generated cumple el formato (formatOk) cuando el texto
      empieza con "Como analista de negocio" y trae de 2 a 3 escenarios que incluyen las
      palabras Dado, Cuando y Entonces (la señal de que están en español); esta comprobación
      mínima es propia de la evaluación y no reemplaza la de u3-story-generator.
      La puntuación de un modelo es su número de resultados con formatOk. La decisión se
      toma así: (1) SI algún modelo evaluado tiene un resultado blocked ENTONCES la decisión
      es "pendiente" y el modelo por defecto sigue en uso; (2) SI ningún modelo está
      bloqueado y uno tiene la puntuación más alta ENTONCES se elige ese; (3) SI hay
      empate, incluido cero cumplimientos en todos, ENTONCES se conserva el modelo por
      defecto, y cuando todas las puntuaciones son cero se anota que las instrucciones
      necesitan afinarse (u3-story-generator). Un resultado failed cuenta como no
      cumplimiento y no bloquea la decisión.
    violation: Una evaluación sin resultado para algún modelo y título, o una decisión sin criterio, no sirve como evidencia.
    source: FR7.1, AC7.1.1

  - id: BR2.9
    statement: Los títulos de la evaluación los aprueba la persona antes de ejecutar y el resultado y la decisión se guardan en un archivo Markdown del proyecto.
    category: policy
    applies_to: EvaluationRecord
    trigger: Cuando se prepara y se termina la evaluación
    logic: >
      SI no hay 5 títulos aprobados por la persona ENTONCES la evaluación no se ejecuta.
      Los títulos de ejemplo son inventados: no contienen datos reales de personas ni de la
      empresa, y la persona lo comprueba al aprobarlos.
      SI la evaluación termina ENTONCES se escribe `docs/evaluacion-modelos.md` con los
      títulos, el resultado de cada modelo y la decisión.
    violation: Un registro que falta o que no nombra la decisión incumple AC7.1.2.
    source: AC7.1.2

  - id: BR2.10
    statement: Un modelo no habilitado se registra como bloqueado, sin descartarlo, y la evaluación sigue con los demás.
    category: constraint
    applies_to: EvaluationResult
    trigger: Cuando un modelo devuelve un error de acceso al evaluarlo
    logic: >
      SI un modelo devuelve un error cuyo motivo (BR2.3) es access_not_enabled o
      model_not_found ENTONCES se registra un resultado blocked con ese motivo y el
      mensaje propio (nunca texto de AWS, BR2.4), el modelo queda como pendiente de
      solicitar el acceso y no se descarta, y la evaluación continúa con los demás modelos.
      SI el motivo es invalid_request ENTONCES el resultado es failed (el parámetro se
      corrige en el acceso al modelo), no blocked. SI todos los modelos están bloqueados
      ENTONCES la decisión es "pendiente" y el modelo por defecto sigue en uso.
    violation: Descartar el modelo por no estar habilitado, o detener la evaluación, incumple AC7.1.3.
    source: AC7.1.3
```

## Resumen

| Regla | Qué fija | Categoría | Fuente |
|-------|----------|-----------|--------|
| BR2.1 | El modelo se elige por configuración | policy | FR7.1 |
| BR2.2 | Un modelo no soportado se rechaza al arrancar | validation | FR7.1 |
| BR2.3 | Los fallos se traducen a los cuatro tipos de error | constraint | FR5.2 |
| BR2.4 | El mensaje de error es propio, sin detalle de AWS | constraint | NFR4 |
| BR2.5 | El acceso no interpreta el texto de la respuesta | constraint | FR5.2 |
| BR2.6 | El tiempo de espera se respeta, con fracciones | constraint | NFR1.1, AC5.1.4 |
| BR2.7 | Cada error indica si reintentar sirve | policy | AC5.1.2 |
| BR2.8 | Un resultado por modelo y título; decisión por formato | policy | FR7.1, AC7.1.1 |
| BR2.9 | Títulos aprobados antes; registro en Markdown | policy | AC7.1.2 |
| BR2.10 | Un modelo bloqueado se registra y no se descarta | constraint | AC7.1.3 |

## Assumptions & Open Questions

- Decidido (FD Q1): el criterio de decisión es el cumplimiento automático del formato; no incluye calidad subjetiva.
- Supuesto: el desempate conserva el modelo por defecto del proyecto (Claude Sonnet); la persona no lo definió y lo confirma en la decisión final.
- Decidido en BR2.8: la comprobación "en español" de la evaluación es la presencia de Dado, Cuando y Entonces; la comprobación completa de idioma es de u3-story-generator.
- Supuesto: si el empate de la decisión no incluye al modelo por defecto, que siempre se evalúa (BR2.8), el desempate lo resuelve conservando el modelo por defecto.
- Cambios de contrato C4 (aditivos), que se registran en `contract-summary.md` al inicio de Code Generation de esta unidad, antes de escribir código que los use: `timeoutSeconds` pasa de entero a número (BR2.6) y `ModelError` gana el campo opcional `reason` con la lista cerrada de BR2.3.
- Abierto, trasladado a NFR Requirements de esta unidad: los valores de tiempo de espera por modelo (pregunta abierta de C4).
