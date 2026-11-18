# Security Requirements — u5-web-app

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (Q1 a Q3).

## Sources

- [Q1] Biblioteca de OpenID Connect para el inicio de sesión (oidc-client-ts).
- [scope] `requirements.md` NFR4 y NFR5; `rules.md` BR5.5, BR5.6, BR5.8 y BR5.10; seguridad de u4 (token de identidad con RS256, 8 horas, sin revocación).

## Requisitos

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR4.1 | El token de identidad vive solo en memoria: la biblioteca de inicio de sesión se configura con `userStore` igual a `WebStorageStateStore` sobre `InMemoryWebStorage` y con `stateStore` por omisión en sessionStorage; no se escribe en localStorage, sessionStorage, cookies ni en la dirección de la página. El access token y el refresh token quedan solo dentro de ese objeto en memoria, no se envían a ninguna parte y no hay renovación automática | Prueba que, tras un inicio de sesión simulado, localStorage y sessionStorage no contienen el token ni su contenido (solo el verificador y el estado durante la redirección) y que no hay renovación silenciosa configurada | Q1; `rules.md` BR5.10 |
| NFR4.2 | Ni la consola ni ningún registro del navegador contienen el token, el título, el contexto ni el Markdown; los errores se registran, si se registran, solo con el código del servicio | Prueba que espía `console.*` durante un flujo completo con un token y un título de prueba y comprueba que no aparecen | NFR4; `rules.md` BR5.4 |
| NFR4.3 | La vista previa nunca ejecuta HTML del texto: no se interpreta HTML en bruto, solo se permiten enlaces `http`, `https` y `mailto` con `rel="noopener noreferrer"`, y las imágenes no se cargan | Pruebas con un Markdown que trae una etiqueta de script, un controlador de evento en línea, un enlace `javascript:` y una imagen remota: no hay elementos ni solicitudes de red resultantes | `rules.md` BR5.5; Q2 de diseño |
| NFR4.4 | La copia temporal de título y contexto (sessionStorage) existe solo durante la redirección por sesión vencida; se borra al restaurar con la misma cuenta, al fallar o cancelarse el inicio, con ACCOUNT_NOT_ALLOWED y al cerrar sesión | Pruebas de cada una de esas salidas que comprueban que la clave no queda en sessionStorage | `rules.md` BR5.6 y BR5.8 |
| NFR5.5 | El cierre de sesión usa metadatos explícitos de Cognito (el descubrimiento no publica `end_session_endpoint`): emisor `https://cognito-idp.<región>.amazonaws.com/<grupo>`, puntos de autorización y token en el dominio del grupo, y cierre en `https://<dominio>/logout?client_id=<cliente>&logout_uri=<dirección de retorno exacta>`; antes de redirigir se llama a `removeUser()` y se borra la copia temporal | Pruebas: tras cerrar sesión el almacén en memoria está vacío, localStorage y sessionStorage no contienen el token y la navegación va exactamente a la dirección de cierre de Cognito esperada | `rules.md` BR5.8; Q1 |
| NFR5.1 | El cliente de Cognito es público (sin secreto) y el paquete publicado no contiene secretos ni claves: solo la dirección del servicio, la región, el dominio y el identificador del cliente de Cognito, que son públicos | Comprobación en CI que busca patrones de claves de AWS y de secretos en `dist/`; prueba de que la configuración solo toma variables `VITE_` públicas | NFR5 |
| NFR5.2 | El inicio de sesión valida `state` y usa PKCE (S256); al volver se borran de la dirección `code` y `state` con `history.replaceState`; la dirección de retorno es el valor exacto configurado | Pruebas: con un `state` distinto o ausente el inicio falla y los botones siguen disponibles; después del intercambio la dirección no contiene `code` ni `state` | `rules.md` BR5.10 |
| NFR5.3 | Las dependencias se instalan con `npm ci` desde el archivo de bloqueo; la biblioteca de inicio de sesión y la de Markdown se declaran con versión exacta; `npm audit --omit=dev --audit-level=high` falla la integración (las dependencias de desarrollo se auditan en un informe aparte que no bloquea), y un hallazgo sin parche se acepta solo con una excepción documentada | La comprobación en CI ejecuta `npm ci` y esa auditoría; `package.json` usa versiones exactas para esas dos | Q1 |
| NFR5.4 | El hospedaje sirve la pantalla por HTTPS con esta política de contenido exacta: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' <origen del servicio> https://<dominio del grupo>.auth.<región>.amazoncognito.com https://cognito-idp.<región>.amazonaws.com; img-src 'self' data:; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`. `unsafe-inline` solo en estilos es un riesgo aceptado porque MUI con emotion inyecta etiquetas de estilo en tiempo de ejecución; los scripts siguen sin permitir código en línea. El requisito queda registrado en `contract-summary.md` (sección de requisitos de alojamiento) para que lo implemente u6-infrastructure | Prueba del plan de Terraform y de humo en u6 que comprueba la cabecera exacta; en u5, una prueba que inspecciona `dist/index.html` y falla ante cualquier `<script>` sin `src`, y que el paquete no usa `eval` | NFR4 y NFR5; `rules.md` BR5.5 |

## Consideraciones de amenazas

| Amenaza | Requisitos que la cubren |
|---------|--------------------------|
| Robo del token por un script de la página | NFR4.1 y NFR5.4 |
| Sesión de Cognito que sigue activa tras cerrar sesión | NFR5.5 |
| Código malicioso en el texto del modelo o del título (XSS) | NFR4.3 y NFR5.4 |
| Redirección con `state` falsificado | NFR5.2 |
| Dependencia comprometida (inicio de sesión o Markdown) | NFR5.3 |
| Fuga de contenido de la persona por consola o por el almacenamiento | NFR4.2 y NFR4.4 |
| Secretos en el paquete | NFR5.1 |

## Assumptions & Open Questions

- Supuesto: el token de 8 horas sin revocación en el servidor (riesgo aceptado en u4) hace que el cierre efectivo dependa del cierre de sesión de Cognito (BR5.8).
- Supuesto: la biblioteca guarda el estado de la redirección en sessionStorage, que es la única excepción a "nada en el navegador" y no contiene el token.
- Abierto: NFR5.4 (política de contenido) es de u6-infrastructure y se verifica allí.
