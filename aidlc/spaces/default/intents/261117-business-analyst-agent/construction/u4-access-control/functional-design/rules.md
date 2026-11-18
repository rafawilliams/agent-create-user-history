# Rules — u4-access-control

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Entidades: `entities.md`. Respuestas: `functional-design-questions.md` (FD Qn).

u4 reemplaza el verificador simulado de u1 por una verificación real contra Amazon Cognito (FD Q1). La pantalla (u5) inicia el flujo con Cognito; el servicio solo verifica el token que recibe en cada solicitud.

```yaml
rules:
  - id: BR4.1
    statement: Se inicia sesión con Gmail u Outlook a través de un grupo de usuarios de Amazon Cognito.
    category: policy
    applies_to: Session
    trigger: Cuando la persona elige Gmail u Outlook en la pantalla de acceso
    logic: >
      SI la persona elige Gmail ENTONCES la pantalla lleva a Cognito con el proveedor
      Google; SI elige Outlook ENTONCES con el proveedor Microsoft. Al volver con éxito,
      la pantalla recibe un token de sesión de Cognito y llega a la pantalla principal
      (u5-web-app). El proveedor queda en la sesión como google o microsoft.
    violation: Un inicio de sesión que no pase por Cognito, o que deje entrar sin token, incumple esta regla.
    source: FR6.1

  - id: BR4.2
    statement: El servicio acepta una credencial solo si es un token de identidad válido de este grupo de usuarios.
    category: authorization
    applies_to: Session
    trigger: Cuando el servicio recibe una solicitud con una credencial Bearer
    logic: >
      SI el token no está presente ENTONCES el motivo es missing. SI no tiene la forma de
      un token firmado ENTONCES malformed. Solo se acepta el algoritmo RS256 que usa
      Cognito: cualquier otro algoritmo del encabezado (incluido "none" y los simétricos)
      es bad_signature; un token sin identificador de clave (kid) es bad_signature; un kid
      que no está en la copia de claves ni aparece tras la renovación de BR4.7 es
      bad_signature. SI la firma no coincide con la clave del kid ENTONCES bad_signature. SI el emisor no es el del grupo ENTONCES
      wrong_issuer. SI la audiencia no es el cliente de la aplicación ENTONCES
      wrong_audience. SI no es un token de identidad ENTONCES wrong_token_use. SI pasó su
      fecha de vencimiento (exp), o se emitió en el futuro (iat), o su "no antes de" (nbf)
      aún no llegó, con una tolerancia de reloj de 60 segundos para los tres, ENTONCES
      expired. En cualquiera de estos casos el resultado es
      SessionInvalid con ese motivo y el servicio responde SESSION_INVALID (401) sin llamar
      al modelo. SI todo coincide ENTONCES el resultado es una Session.
    violation: Aceptar un token de otro grupo, de otra aplicación, vencido o sin firma válida incumple esta regla.
    source: FR6.1

  - id: BR4.3
    statement: Solo pueden entrar las cuentas de la lista de correos permitidos.
    category: authorization
    applies_to: AllowedAccount
    trigger: Cuando el token es válido
    logic: >
      El token debe traer los claims "email" y "email_verified", este último con el valor
      booleano verdadero. SI falta cualquiera, o "email_verified" es falso o de otro tipo,
      ENTONCES la cuenta no se permite. La comparación del correo con la lista es exacta
      sobre el texto en minúsculas, sin normalizar puntos, alias con "+" ni alias de
      Microsoft: la lista contiene el correo tal como aparece en el token. SI el correo no
      está en la lista de correos permitidos de la configuración, o la cuenta no se
      permite, ENTONCES el resultado es SessionInvalid con el motivo account_not_allowed y
      el servicio responde ACCOUNT_NOT_ALLOWED (HTTP 403, no reintentable) con un mensaje
      claro en español; la pantalla se queda en el acceso y permite elegir otra cuenta.
      Lo mismo vale para GET y DELETE de `/v1/session`: una cuenta no permitida recibe 403.
      SI la lista está vacía ENTONCES nadie entra. Cuenta de Microsoft: el proveedor puede
      entregar un correo sin verificar o controlado por quien administra un tenant; por
      eso solo se permite si el token trae "email_verified" verdadero. Requisito para u6:
      configurar la federación de Microsoft de Cognito (el mapeo de atributos) para que el
      token entregue "email_verified" verdadero solo cuando el proveedor verificó el
      correo; si no se puede garantizar, Outlook queda bloqueado hasta que se resuelva, y
      se anota como riesgo de la entrega. Riesgo residual aceptado (supuesto abierto): quien
      controle una cuenta de proveedor con un correo permitido entra.
    violation: Dejar entrar una cuenta que no está en la lista, o aceptar un correo sin verificar, incumple esta regla.
    source: FR6.1; decisión FD Q2

  - id: BR4.4
    statement: Una sesión dura 8 horas.
    category: constraint
    applies_to: Session.expiresAt
    trigger: Cuando se emite o se verifica un token
    logic: >
      El servicio impone el máximo: un token cuya hora de autenticación (auth_time, o
      iat si no la trae) sea de más de 8 horas atrás es expired aunque su exp sea
      posterior. Como requisito para u6: el grupo de usuarios emite tokens de identidad de
      8 horas como máximo y el token de renovación vence a las 8 horas, y la pantalla no
      renueva más allá de ese límite. Pasado ese tiempo la persona inicia sesión de nuevo.
      Una generación que ya empezó no se corta por el vencimiento. El servicio no renueva
      sesiones.
    violation: Una sesión que siga válida pasadas 8 horas incumple esta regla.
    source: decisión FD Q3

  - id: BR4.5
    statement: Sin sesión válida, nada se genera, y ante un fallo de la verificación se rechaza (falla cerrado).
    category: authorization
    applies_to: Session
    trigger: Cuando el servicio recibe una solicitud de generación
    logic: >
      SI la verificación da SessionInvalid, o no se puede completar (falta la
      configuración del grupo de usuarios: not_configured; las claves públicas no se
      pueden obtener y no hay copia vigente: keys_unavailable; una clave de la copia sigue
      sirviendo mientras la copia tenga menos de 1 hora, y con la renovación caída y una
      copia de más de 1 hora se rechaza: keys_unavailable) ENTONCES el servicio
      responde SESSION_INVALID (401) y no llama al modelo. El verificador simulado de u1
      se retira: solo se usa con APP_ENV local o test y la bandera explícita, y nunca
      cuando la configuración real está presente. Un visitante sin sesión que intenta
      generar es llevado por la pantalla a la pantalla de acceso (u5-web-app).
    violation: Generar una historia sin sesión válida, o usar el verificador simulado con la configuración real presente, incumple esta regla.
    source: FR6.1

  - id: BR4.6
    statement: Cerrar la sesión descarta la credencial y termina la sesión en Cognito.
    category: policy
    applies_to: Session
    trigger: Cuando la persona cierra la sesión
    logic: >
      SI la persona cierra la sesión ENTONCES la pantalla descarta el token y termina la
      sesión en Cognito, y el contrato C2 `DELETE /v1/session` responde 204 con una sesión
      válida o 401 sin ella. El token ya emitido no se puede revocar en el servicio (no
      guarda estado) y sigue siendo técnicamente válido hasta su vencimiento de 8 horas;
      esa limitación se acepta para el MVP como riesgo aceptado (un token robado sirve
      hasta 8 horas). Compensación: la lista de correos se consulta en cada solicitud, así
      que quitar un correo de la lista corta su acceso en la siguiente solicitud.
    violation: Dejar el token en la pantalla después de cerrar la sesión incumple esta regla.
    source: FR6.1

  - id: BR4.7
    statement: Las claves públicas del grupo de usuarios se obtienen y se renuevan sin guardar datos de personas.
    category: constraint
    applies_to: IdentityProviderConfig
    trigger: Cuando se verifica la firma de un token
    logic: >
      El servicio guarda en memoria una copia de las claves públicas del grupo, por
      instancia, y la renueva si el token pide una clave desconocida, como máximo una vez
      por minuto. SI las claves no se pueden obtener y la copia no tiene la clave pedida
      ENTONCES keys_unavailable (BR4.5). La copia solo contiene claves públicas.
    violation: Aceptar un token sin comprobar su firma porque las claves no estaban disponibles incumple esta regla.
    source: FR6.1

  - id: BR4.8
    statement: El correo y el token no se registran ni se devuelven.
    category: constraint
    applies_to: Session
    trigger: Cuando se verifica o se rechaza una sesión
    logic: >
      SIEMPRE que se verifica o rechaza una sesión, ENTONCES el registro lleva solo el
      resultado (ok o el motivo de lista cerrada) y la duración; nunca el token, el correo
      ni el identificador de la cuenta. La respuesta de C2 devuelve la sesión con el
      identificador de cuenta y el proveedor, no el correo.
    violation: Un registro con el correo o con el token incumple esta regla.
    source: NFR4
```

## Resumen

| Regla | Qué fija | Categoría | Fuente |
|-------|----------|-----------|--------|
| BR4.1 | Inicio de sesión con Gmail u Outlook por Cognito | policy | FR6.1 |
| BR4.2 | Solo se acepta un token válido de este grupo | authorization | FR6.1 |
| BR4.3 | Solo entran los correos de la lista | authorization | FR6.1, FD Q2 |
| BR4.4 | Una sesión dura 8 horas | constraint | FD Q3 |
| BR4.5 | Sin sesión válida no se genera; falla cerrado | authorization | FR6.1 |
| BR4.6 | Cerrar la sesión descarta la credencial | policy | FR6.1 |
| BR4.7 | Claves públicas con copia en memoria y renovación | constraint | FR6.1 |
| BR4.8 | Ni el correo ni el token se registran | constraint | NFR4 |

## Assumptions & Open Questions

- Decidido (FD Q1): Amazon Cognito; (FD Q2): lista de correos permitidos; (FD Q3): 8 horas.
- Cambios de contrato (aditivos), registrados en `contract-summary.md` al inicio de Code Generation: el código `ACCOUNT_NOT_ALLOWED` (HTTP 403) en C1 y C2, y los valores del motivo de `SessionInvalid` en C3.
- Abierto: la lista de correos permitidos la da la persona (cuáles son) y la carga `u6-infrastructure` en la configuración del despliegue.
