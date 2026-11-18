# Security Design — u4-access-control

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

## Orden fijo de la verificación (NFR5.1, NFR5.2, NFR5.3, NFR5.4)

La verificación de una credencial recorre estos pasos en este orden; el primero que falla corta y devuelve su motivo (BR4.2), sin llamar al modelo:

1. **Configuración presente:** región, identificador del grupo, cliente de la aplicación y lista de correos. Si falta alguno: `not_configured`.
2. **Credencial presente y con forma de token** (tres partes): si no, `missing` o `malformed`.
3. **Encabezado:** el algoritmo debe ser exactamente `RS256` y debe traer `kid`; cualquier otro algoritmo (incluido `none` y los simétricos) o sin `kid`: `bad_signature`. Esto se decide **antes** de buscar ninguna clave, para que el encabezado no pueda elegir el método de verificación.
4. **Clave del `kid`:** regla única. (a) Si la copia tiene menos de 1 hora y contiene el `kid`, se usa. (b) Si no (el `kid` no está, o la copia tiene más de 1 hora), esta solicitud intenta la renovación acotada (ver abajo). (c) Si esta solicitud realizó la descarga con éxito y el `kid` sigue sin estar: `bad_signature`. (d) Si esta solicitud no pudo realizar la descarga (no obtuvo el cerrojo, ya hubo un intento en el último minuto, o la descarga falló) y no hay una copia vigente con el `kid`: `keys_unavailable`. Una copia de más de 1 hora nunca se usa para verificar.
5. **Firma** con esa clave pública: si no coincide, `bad_signature`.
6. **Claims:** emisor exacto (derivado de la configuración), audiencia igual al cliente de la aplicación, `token_use` igual a `id`, y las fechas (`exp`, `iat`, `nbf`) con 60 segundos de tolerancia y el máximo de 8 horas desde `auth_time` (o `iat` si falta). Si falta `exp` o ambas fechas de inicio: rechazado.
7. **Cuenta:** `email` y `email_verified` verdadero (booleano) y correo en minúsculas exactamente en la lista permitida (BR4.3), si no, `account_not_allowed`.
8. **Resultado:** una `Session` con `sessionId` (`jti`, o `sub` si no hay), `accountId` (`sub`), `provider` y `expiresAt`.

Todo error inesperado dentro de estos pasos se captura y se trata como sesión inválida con el motivo `unknown` (NFR1.6): falla cerrado y sin traza.

## Descarga y copia de las claves públicas (NFR5.7)

- **Dirección fija:** la dirección HTTPS del conjunto de claves se construye solo con la región y el identificador del grupo de la configuración. Nunca se usa `iss`, `jku`, `x5u` ni ningún valor del token.
- **Descarga acotada:** solo HTTPS con el certificado validado, sin seguir redirecciones a otro servidor, con un tope de 64 kilobytes y un tiempo de espera de 3 segundos; el cliente HTTP se configura con cero reintentos.
- **Conjunto mal formado:** si la respuesta no es un conjunto de claves válido, no trae la clave pedida o la clave no es RSA para RS256, el resultado es `keys_unavailable` y la copia anterior no se modifica.
- **Copia en memoria:** una por instancia, con la hora de la última descarga exitosa; sirve mientras tenga menos de 1 hora; contiene solo claves públicas.
- **Una descarga a la vez y una por minuto:** una descarga en curso bloquea a las demás con un cerrojo de intento único: una solicitud que no obtiene el cerrojo **no espera ni reutiliza el resultado**: falla cerrado de inmediato con `keys_unavailable` (la siguiente solicitud ya usará la copia renovada); un intento fallido (error de red, tiempo agotado, conjunto inválido) cuenta para el límite de uno por minuto.

## Lista de correos y comparación (NFR5.3, NFR5.6)

- La lista se lee del entorno en cada solicitud, se normaliza a minúsculas y sin espacios, y se compara de forma exacta con el correo del token (también en minúsculas). No se normalizan puntos ni alias.
- No se exige comparación en tiempo constante: la lista no es un secreto y el riesgo de temporización es bajo (decisión registrada en los requisitos).
- Una lista de más de 50 correos o con una entrada que no parece un correo se rechaza al iniciar con un error de configuración (`not_configured`), de modo que nadie entra con una lista rota.

## Respuestas y registros (NFR4.1 a NFR4.4)

- Todo rechazo de token (sin credencial, forma, firma, emisor, audiencia, tipo, vigencia, claves, configuración, error interno) devuelve **la misma** respuesta: 401 con el cuerpo SESSION_INVALID y el mismo mensaje en español, sin indicar el motivo. Solo `account_not_allowed` devuelve 403 ACCOUNT_NOT_ALLOWED con su mensaje propio (riesgo aceptado de divulgación a quien ya tiene un token válido del grupo).
- El motivo de lista cerrada va únicamente al registro. El registro no lleva el token, el correo, el `sub` ni la lista de correos.
- `GET /v1/session` devuelve `sessionId`, `accountId`, `provider` y `expiresAt`: nunca el correo ni el token.

## Secretos (NFR5.5)

u4 no usa secretos: solo claves públicas y valores de configuración. La aplicación cliente de Cognito se define sin secreto de cliente (flujo con código y PKCE desde la pantalla). La comprobación de patrones de claves de AWS en CI es de `u6-infrastructure`; u4 verifica por su cuenta, con una prueba, que su configuración y su código no contienen ningún valor con forma de secreto.

## Superficie de ataque y mitigaciones

| Amenaza | Mitigación |
|---------|-----------|
| Confusión de algoritmo, "none" o clave simétrica | El algoritmo se fija en RS256 antes de elegir la clave |
| Descarga de claves desde un servidor del atacante | Dirección derivada solo de la configuración; sin `iss`, `jku` ni `x5u` del token |
| Inundación de tokens con `kid` desconocidos que agota el plazo | Una descarga a la vez, una por minuto, las demás fallan cerrado |
| Cuenta de proveedor con correo no verificado | `email_verified` verdadero obligatorio; correo exacto en minúsculas |
| Fuga del token o del correo | Solo el motivo de lista cerrada en registros; sin correo en respuestas |
| Distinguir por qué falló un token | La misma respuesta 401 para todos los motivos |
| Fallo de configuración o de claves | Falla cerrado; el verificador simulado nunca con configuración real |

## Assumptions & Open Questions

- Supuesto: el punto de claves públicas de Cognito es de acceso público por HTTPS y su dirección se deriva de la región y del grupo.
- Abierto: la biblioteca de JWT y su versión se fijan en Code Generation; debe permitir fijar el algoritmo y recibir la clave por separado.
