# Security Requirements — u4-access-control

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa. Esta es la unidad de identidad: su superficie de seguridad es el token, la lista de correos y las claves públicas.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR5.1 | El servicio verifica la firma del token solo con el algoritmo RS256 y con la clave pública del `kid`; rechaza "none", los algoritmos simétricos, un token sin `kid` y un `kid` desconocido tras la renovación | Pruebas con un token firmado con otro algoritmo, un token "none", uno sin `kid`, uno con `kid` desconocido y uno con la firma alterada: todos dan SESSION_INVALID | `rules.md` BR4.2 |
| NFR5.2 | El servicio comprueba emisor, audiencia (el cliente de la aplicación), tipo de token (identidad) y vigencia (exp, iat y nbf con 60 s de tolerancia, y un máximo de 8 horas desde la autenticación) | Pruebas con cada claim incorrecto, con un token vencido, uno con `iat` en el futuro, uno con `nbf` futuro, uno de más de 8 horas desde `auth_time`, uno sin `auth_time` pero con `iat` de más de 8 horas (cae a `iat`), uno sin `exp`, uno sin `iat` ni `auth_time` (rechazado), y uno dentro de la tolerancia | `rules.md` BR4.2, BR4.4 |
| NFR5.3 | Solo entra una cuenta cuyo token trae `email` y `email_verified` verdadero (booleano) y cuyo correo, en minúsculas, está exactamente en la lista permitida; cualquier otro caso es ACCOUNT_NOT_ALLOWED (403) | Pruebas con `email_verified` falso, ausente, texto, correo ausente, correo con otra capitalización, con punto de Gmail distinto y con alias "+", y lista vacía | `rules.md` BR4.3 |
| NFR5.4 | Cualquier fallo o falta de configuración de la verificación (sin grupo de usuarios configurado, claves no disponibles con copia vencida de más de 1 hora) rechaza la solicitud: el servicio falla cerrado y nunca usa el verificador simulado con la configuración real presente | Pruebas con configuración incompleta, claves no disponibles y copia vencida; y una prueba de que el verificador simulado no se enlaza si hay configuración real, ni con `APP_ENV` distinto de local y test | `rules.md` BR4.5; BR1.5 de u1 |
| NFR4.1 | u4 no guarda sesiones ni datos de personas: la sesión es un token sin estado y la lista de correos y la configuración viven en variables de entorno; la única copia en memoria es la de claves públicas | Una prueba comprueba que u4 no escribe archivos ni estado de sesión | `requirements.md` NFR4 |
| NFR4.2 | Los registros de u4 contienen solo el resultado (`ok` o el motivo de lista cerrada) y la duración; nunca el token, el correo, el identificador de la cuenta ni la lista de correos | Una prueba captura todos los registros durante un caso feliz y cada motivo de rechazo y busca el token, el correo y el `sub` de prueba | `rules.md` BR4.8; `requirements.md` NFR4 |
| NFR4.3 | La respuesta de `/v1/session` devuelve el identificador de cuenta y el proveedor, nunca el correo ni el token | Una prueba comprueba que el cuerpo de GET no contiene el correo de prueba ni el token | `rules.md` BR4.8; C2 |
| NFR4.4 | Los mensajes de error son propios y no revelan por qué falló el token: todos los motivos de rechazo de firma, emisor, audiencia, tipo y vigencia dan el mismo mensaje SESSION_INVALID; solo ACCOUNT_NOT_ALLOWED tiene un mensaje distinto | Una prueba compara el cuerpo y el código HTTP (401) de la respuesta para cada motivo de rechazo del token y comprueba que son idénticos; ACCOUNT_NOT_ALLOWED (403) revela, a quien ya tiene un token válido del grupo, que la cuenta no está en la lista: es un riesgo aceptado porque la pantalla necesita ese mensaje | `rules.md` BR4.2, BR4.3 |
| NFR5.5 | Ningún secreto va en el código ni en los archivos versionados: el servicio no usa secretos (solo claves públicas y valores de configuración); el grupo de usuarios y la aplicación cliente no incluyen un secreto de cliente en el servicio | Una búsqueda automática de patrones de claves no encuentra ninguno; la configuración de u4 no tiene secretos | `requirements.md` NFR5; `construction.md` (Security) |
| NFR5.6 | La lista de correos permitidos se lee de la configuración en cada solicitud (o se recarga del entorno), se normaliza a minúsculas al cargarla y se compara con el correo del token: quitar un correo corta su acceso en la siguiente solicitud (compensa que no hay revocación de tokens). No se exige comparación en tiempo constante: la lista no es un secreto y el riesgo de temporización es bajo | Una prueba cambia la lista entre dos solicitudes con el mismo token y comprueba que la segunda se rechaza | `rules.md` BR4.6 |

| NFR5.7 | Las claves públicas se descargan solo de la dirección HTTPS que se deriva de la región y del identificador del grupo configurados; nunca de `iss`, `jku` ni `x5u` del token; con validación del certificado, sin seguir redirecciones a otros servidores, con un tope de 64 kilobytes en la respuesta y un tiempo de espera de 3 s; un conjunto de claves mal formado, sin la clave pedida o con un algoritmo distinto de RS256 da `keys_unavailable` | Pruebas con un token cuyo `iss` y `jku` apuntan a otro servidor (no se descarga de ahí), una redirección a otro host (se rechaza), una respuesta mayor de 64 KB, un JWKS mal formado y uno con una clave de otro algoritmo | `rules.md` BR4.7 |

Nota sobre la numeración: el NFR5 de inception es "Secretos". Los requisitos de autenticación y de lista de cuentas (NFR5.1 a NFR5.4, NFR5.6 y NFR5.7) no tienen un requisito propio en `requirements.md`: nacen de FR6.1 (acceso) y heredan NFR5 por ser el más cercano. `traceability.json` apoya el OK de NFR5 en NFR5.5 (secretos) y declara estas filas como requisitos nuevos con origen FR6.1.

## Consideraciones de amenazas

| Amenaza | Requisitos que la cubren |
|---------|--------------------------|
| Token falsificado o con algoritmo alterado | NFR5.1 |
| Token de otro grupo o aplicación, vencido o reutilizado fuera de plazo | NFR5.2 |
| Cuenta de proveedor con correo no verificado o ajeno | NFR5.3 |
| Acceso por fallo de configuración o de las claves | NFR5.4 |
| Fuga del token o del correo por registros o respuestas | NFR4.2 y NFR4.3 |
| Enumeración de la causa del rechazo | NFR4.4 |
| Token robado | NFR5.6 (compensación) y la limitación aceptada de 8 horas |

## Assumptions & Open Questions

- Supuesto: el riesgo residual de que quien controle una cuenta de proveedor con un correo permitido entre está aceptado para el MVP.
- Abierto: la comprobación de patrones de claves de AWS en CI es de la etapa de CI de `u6-infrastructure`.
