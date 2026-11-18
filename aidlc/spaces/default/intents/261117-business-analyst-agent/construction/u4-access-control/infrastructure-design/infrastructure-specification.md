# Infrastructure Specification — u4-access-control

Documentos de entrada: `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: las decisiones (Cognito, lista de correos, 8 horas) ya están confirmadas. u4 es código dentro de la función de generación de u1; lo que necesita de AWS es el grupo de usuarios de Amazon Cognito, que este documento especifica y que `u6-infrastructure` crea con Terraform. Los valores marcados "propuesta" no los confirmó la persona.

## Deployment

| Facet | Choice | Rationale |
|-------|--------|-----------|
| Modelo de cómputo | Dentro de la función de AWS Lambda de u1; sin función ni servicio nuevo | u4 forma parte del despliegue del servicio (`unit-of-work.md`) |
| Identidad | Un grupo de usuarios de Amazon Cognito en us-east-1 con los proveedores Google y Microsoft federados | Decisión FD Q1 |
| Aplicación cliente | Una aplicación cliente **sin secreto**, con flujo de código de autorización y PKCE; las direcciones de retorno y de cierre de sesión son solo la de la distribución de la pantalla; la dirección local de desarrollo va en un grupo de desarrollo aparte, no en el desplegado | La pantalla es una aplicación de navegador: no puede guardar un secreto (NFR5.5) |
| Vigencia | Token de identidad y token de acceso de 8 horas como máximo y token de renovación de 8 horas; la pantalla no renueva más allá del límite | BR4.4; decisión FD Q3 |
| Dominio de inicio de sesión | El dominio alojado de Cognito con un prefijo propio del proyecto (propuesta); dominio propio fuera del MVP | Sencillez y costo |
| Red | Sin VPC propia; la función descarga las claves públicas por HTTPS a la dirección pública del grupo | Sin recursos privados que proteger |
| Almacenamiento | Ninguno (NFR4.1): sin base de datos ni tabla de sesiones; la lista de correos es una variable de entorno | Sin persistencia |
| Entornos | Uno solo, al integrar en `main` | Práctica del equipo |
| IaC | Terraform, en el mismo proyecto de `infra/` | Práctica del equipo |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---------|------|---------------|-------|
| Amazon Cognito (grupo de usuarios) | Emite y firma los tokens y publica las claves | Registro propio desactivado (solo federación de Google y Microsoft); correo como atributo; vigencias de 8 horas; sin MFA propio (lo da el proveedor); protección contra la eliminación | La cuenta de AWS debe tener Cognito habilitado; el costo para unas 5 personas está dentro del nivel gratuito |
| Federación con Google | Proveedor de identidad de Google | Credenciales del cliente OAuth que la persona crea en la consola de Google; mapeo de `email` y `email_verified` | Paso manual de la persona; las credenciales se guardan como variable sensible de Terraform, nunca en el repositorio |
| Federación con Microsoft | Proveedor de identidad de Microsoft | Credenciales de la aplicación que la persona registra en Microsoft Entra; mapeo de `email` y de `email_verified` para que sea verdadero solo cuando el proveedor verificó el correo (BR4.3) | Paso manual; riesgo: si no se puede garantizar `email_verified`, Outlook queda bloqueado hasta resolverlo |
| AWS Lambda (de u1) | Ejecuta u4 | Variables de entorno de texto (sin secretos): región, identificador del grupo, identificador de la aplicación cliente y la lista de correos permitidos (separada por comas, hasta 50) | Sin permisos nuevos: u4 solo hace una descarga HTTPS pública (NFR5.5) |
| API Gateway REST (de u1) | Entrada HTTPS | Se agregan las rutas `GET /v1/session` y `DELETE /v1/session` (contrato C2) a la misma integración de la función, con las mismas políticas de CORS y de límite de tasa | CORS: el preflight (OPTIONS) de las dos rutas nuevas permite los métodos GET, POST, DELETE y OPTIONS y los encabezados `Authorization` y `Content-Type` solo para el origen de la distribución de la pantalla; las respuestas que genera la función (401, 403) llevan CORS desde la función, y las que genera la propia pasarela (429 por límite de tasa, 4XX y 5XX por defecto) deben llevar las mismas cabeceras CORS mediante respuestas de pasarela configuradas; sin ellas el navegador las vería como un error de red. Este cambio de Terraform lo asigna `u6-infrastructure` junto con las rutas nuevas |
| CloudWatch (de u1) | Registros y métricas | Los campos `authOutcome` y `authDurationMs` y el código ACCOUNT_NOT_ALLOWED son valores del registro por solicitud; sin métricas ni filtros nuevos | NFR4.5, NFR1.9 |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|-----------------|------------|----------------|-----------------|
| Grupo de usuarios y aplicación cliente de Cognito | u4-access-control (especificación) / u6-infrastructure (creación) | u5-web-app (inicio y cierre de sesión), u3-story-generator (vía C3) | La pantalla usa solo la aplicación cliente pública; el servicio solo descarga las claves públicas |
| Función de generación y pasarela REST | u1-walking-skeleton | u3, u4 | La función es una; u4 extiende su código |
| Variables de entorno de la función | u6-infrastructure | u1, u3, u4 | Solo texto, sin credenciales |

## Criterios verificables que `u6-infrastructure` debe cumplir

u4 especifica el grupo de usuarios y `u6-infrastructure` lo crea; para que la especificación obligue, la etapa 3 del flujo (plan de Terraform) afirma lo siguiente y falla si no se cumple:

| Criterio | Qué se afirma en el plan |
|----------|--------------------------|
| Sin registro propio | El grupo solo permite a los administradores crear usuarios; el registro autoservicio está desactivado |
| Aplicación cliente sin secreto | La aplicación cliente no genera secreto de cliente |
| Flujo con PKCE | Solo el flujo de código de autorización; sin flujo implícito |
| Vigencias | Tokens de identidad y de acceso de 8 horas como máximo y token de renovación de 8 horas |
| Direcciones de retorno y de cierre | Solo la de la distribución de la pantalla desplegada; la dirección local de desarrollo no entra en el grupo desplegado |
| Protección contra eliminación | Activada en el grupo de usuarios |
| Federaciones | Solo Google y Microsoft, con el mapeo de `email` y `email_verified` |
| Revocación | Revocación de tokens de renovación activada (el token de identidad ya emitido sigue siendo válido hasta 8 horas tras cerrar la sesión: riesgo aceptado, BR4.6) |

Si `u6-infrastructure` no los cumple, o hasta que los cree, NFR5.2 y NFR5.5 se consideran cubiertos solo en parte en lo que depende de la infraestructura.

## Entrega de la configuración al verificador

- **Región:** la variable de región de u4 es la del grupo de usuarios (us-east-1), la misma que usa para derivar la dirección de las claves y el emisor; no es la variable de región de Bedrock.
- **Emisor esperado:** `https://cognito-idp.<región>.amazonaws.com/<identificador del grupo>`, derivado solo de la configuración.
- **Lista de correos:** hasta 50 correos en una variable de entorno de texto; el total de las variables de entorno de una función tiene un límite de 4 kilobytes, que 50 correos largos pueden acercar (se verifica al desplegar). La lista vive en una variable de Terraform que no se versiona (se pasa por el entorno de quien despliega o por los secretos del flujo), para no guardar correos en el repositorio.
- **Nivel del grupo:** el nivel básico de Cognito sin la función avanzada de seguridad (propuesta); el costo de las federaciones con Google y con Microsoft se revisa al crear el grupo.

## Si Microsoft no puede dar `email_verified` verdadero

Microsoft Entra normalmente no emite esa afirmación en el token de identidad y Cognito no puede inventarla. Alternativa decidida para el MVP: se despliega con Google y Outlook queda aplazado hasta resolverlo (por ejemplo, aceptando un reclamo opcional de Entra); la decide la persona al desplegar. No se relaja `email_verified` para dejar entrar a Outlook.

## Qué cambia al desplegarse u4

Con el verificador real configurado, el entorno desplegado deja de rechazar toda solicitud: una persona de la lista que inicie sesión puede generar historias. Hasta entonces el servicio desplegado falla cerrado (SESSION_INVALID). La verificación de extremo a extremo en AWS (inicio de sesión real, generación, cierre) solo es posible con los pasos manuales de las dos federaciones; esa prueba la hace la persona al desplegar.

## Costo (orientativo, propuesta)

Cognito para unas 5 personas con federación queda dentro del nivel gratuito; u4 no agrega costo de cómputo.

## Assumptions & Open Questions

- Abierto: las credenciales de Google y de Microsoft las crea la persona; sin ellas, `terraform apply` del grupo de usuarios queda a medias.
- Abierto: la lista de correos permitidos (cuáles son) la da la persona.
- Supuesto: el prefijo del dominio de Cognito y las direcciones de retorno son propuestas de esta etapa y las fija `u6-infrastructure`.
