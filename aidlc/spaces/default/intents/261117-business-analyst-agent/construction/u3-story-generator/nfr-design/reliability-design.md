# Reliability Design — u3-story-generator

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

El MVP no tiene objetivo formal de disponibilidad (decisión confirmada en u1) y no hay interruptor de circuito: cada solicitud falla de forma independiente con un error claro.

## Respuesta del modelo inválida (NFR1.6)

La validación va por etapas y cualquier etapa que falla produce INVALID_MODEL_RESPONSE (502, reintentable) sin texto parcial:

1. Tamaño (hasta 16 kilobytes en bytes UTF-8).
2. JSON válido, con un único cerco de código opcional.
3. Campos presentes, no vacíos y de hasta 300 caracteres; los saltos de línea se normalizan a espacios (no se rechaza por tenerlos).
4. De 2 a 3 criterios.
5. Heurística de idioma sobre el texto normalizado y sin escapar; el escape se aplica al final, al armar el Markdown.
6. Plazo: si el plazo restante ya se agotó antes de llamar al modelo, no se llama y se devuelve GENERATION_TIMEOUT.

El resultado parcial no existe: el Markdown se arma solo si las cinco etapas pasan.

## Fallos del acceso al modelo y plazo (NFR1.7)

u3 devuelve el error de contrato que corresponde al tipo de error del modelo con la tabla de errores de u1 (transient y unavailable: MODEL_FAILURE 502 reintentable; timeout: GENERATION_TIMEOUT 504 reintentable; access_denied: MODEL_FAILURE 502 no reintentable). El reintento automático lo decide el servicio con el plazo restante, no u3. Un resultado vacío nunca se devuelve como éxito.

## Error interno (NFR1.8)

Todo el cuerpo de u3 corre dentro de un único manejador de errores, que va después de las rutas de errores tipados del acceso al modelo (esos se traducen primero con la tabla de u1): una excepción inesperada se convierte en MODEL_FAILURE 502 no reintentable, sin traza ni detalle interno, y se registra solo el código, la duración y una marca `internal_error` verdadera (sin contenido), para distinguir un defecto de u3 de un fallo del modelo en los registros.

## Recuperación y datos (NFR1.9)

No hay datos que respaldar ni recuperar. El título lo conserva la pantalla (u5-web-app) y reintentar reenvía el mismo título. Recuperarse es volver a enviar la solicitud.

## Assumptions & Open Questions

- Supuesto: reintentar con el mismo título puede dar una respuesta válida (el modelo no es determinista), por eso INVALID_MODEL_RESPONSE es reintentable.
- Abierto: el SLO se define antes de ofrecer el servicio a más de 5 personas (condición de u1).
