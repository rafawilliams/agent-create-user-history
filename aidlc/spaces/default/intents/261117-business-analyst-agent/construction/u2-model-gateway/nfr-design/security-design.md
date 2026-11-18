# Security Design — u2-model-gateway

Documentos de entrada: `security-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md`, `rules.md` y `contract-summary.md`. No hubo preguntas en esta etapa. u2 es una biblioteca dentro del servicio; no tiene red, personas ni almacenamiento propios.

## Sin persistencia (NFR4.1)

- El acceso al modelo trabaja solo con valores en memoria: recibe la petición, llama a Bedrock y devuelve `ModelResponse` o `ModelError`. No escribe archivos, no usa caché y no comparte estado entre llamadas.
- El único código de u2 que escribe un archivo es el comando de evaluación, y solo escribe `docs/evaluacion-modelos.md`. No registra nada más ni lo envía a otro lugar.
- El cliente de Bedrock se crea una vez por proceso y se reutiliza; no guarda historial de peticiones.

## Registros sin contenido ni detalle de AWS (NFR4.2)

- Por llamada, u2 registra solo cuatro campos: identificador del modelo, resultado (`ok` o el `kind` del error), motivo de la lista cerrada (`reason`) y duración. No registra la petición, el texto de la respuesta, el título ni el mensaje de AWS.
- La traducción de errores es una tabla fija de código de AWS a (`kind`, `reason`), con un valor por defecto (`unavailable`, `unknown`) para códigos desconocidos:

  | Origen del error | `kind` | `reason` |
  |------------------|--------|----------|
  | `ThrottlingException`, `ServiceQuotaExceededException` | transient | throttled |
  | `InternalServerException`, `ModelNotReadyException`, `ModelErrorException` | transient | unavailable |
  | `ModelTimeoutException`; tiempo de lectura o de conexión agotado del cliente; el tiempo pedido agotado | timeout | timeout |
  | `ServiceUnavailableException`; error de red o de punto de conexión | unavailable | unavailable |
  | `AccessDeniedException` | access_denied | access_not_enabled |
  | `ResourceNotFoundException` (incluye "detalles de uso no enviados") | access_denied | model_not_found |
  | `ValidationException` | access_denied | invalid_request |
  | Cualquier otro error | unavailable | unknown |

- **Cómo se descarta el texto de AWS:** el traductor devuelve un `ModelError` nuevo (no relanza la excepción) construido solo con valores de tablas propias, y la excepción original no se encadena ni se guarda en ningún campo (sin causa ni traza que llegue a un registro de la plataforma). Los registradores del SDK de AWS (`boto3`, `botocore`) quedan en nivel de advertencia o superior; el código nunca los pone en depuración, porque esos registros podrían llevar la petición.
- **Cómo se prueba (NFR4.2):** un doble del cliente de AWS lanza un error con un ARN y un identificador de cuenta en su texto; la prueba captura todos los registros (incluidos los de `boto3` y `botocore`) y comprueba que ningún registro, mensaje, motivo ni causa del `ModelError` contiene ese ARN ni ese identificador.
- El mensaje del `ModelError` sale de una tabla de textos propios por `kind`.
- El comando de evaluación escribe en el archivo solo el motivo de lista cerrada y el mensaje propio, no el texto de AWS.

## Evaluación solo con títulos inventados y aprobados (NFR4.3)

- El comando lee los títulos de un archivo de títulos de ejemplo que la persona edita. La aprobación está atada al contenido: la persona ejecuta un subcomando `approve` que escribe en el archivo la línea `aprobado: <huella>`, donde la huella es el hash SHA-256 de los 5 títulos. El comando se niega a correr si el archivo no tiene exactamente 5 títulos o si la huella no coincide con los títulos actuales, así que cambiar un título obliga a aprobar de nuevo. Esto es una comprobación de integridad, no una prueba de que sean inventados: eso lo confirma la persona al aprobar.
- El registro de evaluación guarda el texto generado para cada título de ejemplo (son inventados).
- El archivo de títulos y el registro de evaluación viven en `docs/`, versionados; la persona confirma al aprobar que los títulos son inventados.

## Credenciales (NFR5.1)

- u2 no recibe ni guarda claves. Para llamar a Bedrock usa la cadena de credenciales estándar del SDK de AWS: el rol de ejecución de la función en AWS, o el perfil local de quien ejecuta el comando.
- No hay variables de entorno con claves en la configuración de u2; solo el identificador del modelo, la región y los tiempos de espera.
- El repositorio tiene una comprobación automática que busca patrones de claves de AWS en el código y en las pruebas; la ejecuta el flujo de CI y su dueño es la etapa de CI de `u6-infrastructure` (ya existe una etapa de pruebas de seguridad en `cicd-pipeline.md`).

## Permiso mínimo y modelo no soportado (NFR5.2, NFR5.3)

- **Lista cerrada de identificadores:** el perfil del modelo solo acepta identificadores que cumplen un patrón exacto por proveedor: `(us.|global.)?anthropic.claude-<resto>` o `(us.)?amazon.titan-<resto>`. Cualquier otro valor, incluido un error de escritura dentro de un proveedor válido, se rechaza al armar el acceso, antes de crear el cliente de AWS y de hacer cualquier llamada (NFR5.3). La validación ocurre al inicializar el servicio; en la función de AWS un valor inválido haría fallar la inicialización y por tanto cada invocación, y por eso la prueba de humo de `u6-infrastructure` debe cubrirlo.
- **Una sola fuente para el permiso y la configuración:** el identificador del modelo configurado entra al servicio como variable de entorno y al permiso del rol como variable de Terraform, y ambos salen de la misma variable de `u6-infrastructure` (en `u1-walking-skeleton` ya es una variable de Terraform que alimenta ambos); así no pueden divergir.
- **Qué permiso pide un perfil de inferencia:** invocar con un identificador con prefijo `us.` o `global.` exige permiso sobre el perfil de inferencia (ARN de la cuenta) y sobre el modelo base en cada región de destino; el modelo base se nombra por su identificador y se deja la región como comodín solo para ese modelo, nunca un comodín sobre todos los modelos.
- **Lista incompleta de Titan:** el identificador de Titan se fija en Code Generation al ver los modelos de la cuenta y se registra en el archivo de evaluación; hasta entonces `u6-infrastructure` recibe solo el modelo por defecto.
- **Registro de invocaciones del modelo:** debe seguir desactivado en la cuenta (por defecto puede capturar el contenido); `u6-infrastructure` lo verifica en su prueba de humo.
- **Qué se prueba aquí:** que un identificador de otro proveedor o mal escrito no genera ninguna llamada a AWS y el error nombra el valor.

## Superficie de ataque y mitigaciones

| Amenaza | Mitigación |
|---------|-----------|
| Una variable de entorno mal escrita llama a un modelo no previsto | NFR5.3: lista cerrada de proveedores, rechazo antes de cualquier llamada |
| Texto de AWS con ARN o identificadores en registros o en el archivo de evaluación | NFR4.2: descartar el texto en el punto de captura, motivos de lista cerrada |
| Contenido de títulos o de historias en registros | NFR4.1 y NFR4.2: cuatro campos fijos por llamada |
| Datos reales en la evaluación | NFR4.3: archivo de títulos con marca de aprobación y exactamente 5 títulos |
| Claves en el código | NFR5.1: cadena de credenciales estándar y comprobación de patrones en CI |

## Riesgo con Amazon Titan

Algunos modelos de Titan para texto no admiten un mensaje de sistema. El acceso de u1 ya envía toda la petición como un único mensaje de usuario, así que no depende de eso. Si Titan rechaza la petición con una validación, cada título daría `invalid_request` (resultado `failed`, no bloqueo) y la puntuación sería cero: el archivo de evaluación debe mostrar el motivo por título para que no se confunda con una mala calidad del modelo.

## Assumptions & Open Questions

- Supuesto: la comprobación de patrones de claves de AWS en CI es una herramienta estándar que se elige en `u6-infrastructure` o en Code Generation.
- Abierto: el formato exacto del archivo de títulos (se fija en Code Generation).
