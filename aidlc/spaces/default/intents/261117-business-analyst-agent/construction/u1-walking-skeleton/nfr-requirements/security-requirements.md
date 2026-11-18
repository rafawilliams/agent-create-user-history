# Security Requirements — u1-walking-skeleton

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (NR Qn).

Cada requisito hereda el ID de Inception y le agrega un subnúmero.

## Autenticación y autorización

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR5.2 | El verificador de sesión simulado solo se usa en ejecuciones locales y en pruebas automáticas, y solo cuando se configura de forma explícita. Un entorno desplegado sin un verificador real configurado rechaza toda solicitud con SESSION_INVALID (falla cerrado). La concesión se retira cuando `u4-access-control` agrega la verificación real: el criterio verificable es que ningún entorno desplegado tenga el verificador simulado enlazado | `rules.md` BR1.5; `requirements.md` NFR5; `contract-summary.md` (ADR-006) |

Un código que se salta una comprobación de autenticación debe marcarse (guía de seguridad de Construction): esta concesión queda documentada aquí y en `rules.md` BR1.5, y acotada a local y pruebas.

## Protección de datos

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR4.1 | El servicio no guarda títulos ni historias en ningún almacén de datos (sin persistencia) | `requirements.md` NFR4; `intent-statement.md` |
| NFR4.2 | Los registros del servicio y de los servicios de AWS que usa contienen solo errores y métricas, sin el contenido de los títulos ni de las historias; esto incluye el registro de invocaciones del modelo, que por defecto puede capturar el contenido y debe quedar desactivado | `requirements.md` NFR4; `contract-summary.md` (revisión de seguridad) |
| NFR4.3 | La cabecera `Authorization` y cualquier credencial no se escriben en los registros; el identificador de la solicitud (`requestId`) no lleva datos personales | `contract-summary.md` (revisión R-02 de seguridad) |
| NFR4.4 | El título se trata como dato no confiable: se valida (no vacío, hasta 200 caracteres) y no puede cambiar las instrucciones, el formato ni el idioma del resultado | `rules.md` BR1.3; `requirements.md` FR1.2, FR2.5 |

## Secretos

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR5.1 | Ninguna credencial, clave de API ni secreto aparece en el código ni en los archivos versionados; el servicio usa los permisos de AWS del entorno y, en local, las credenciales del perfil de AWS de quien lo ejecuta | `requirements.md` NFR5; `team-practices.md` (Deployment); `phases/construction.md` (Security) |

## Límite de uso

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR3.2 | El servicio limita las solicitudes a 20 por persona por día; sin una identidad real, el esqueleto lo aplica por origen de la solicitud y se afina cuando llegue el control de acceso | NR Q3 y Q4; `requirements.md` NFR3 |

## Consideraciones de amenazas

- **Acceso abierto al modelo:** mientras el control de acceso no esté construido, el servicio desplegado rechaza toda solicitud (NFR5.2), así que no hay exposición de costo por el esqueleto.
- **Inyección en el título:** un título con instrucciones no debe alterar el formato de salida (NFR4.4); la defensa completa la construye `u3-story-generator`.
- **Contenido en registros:** el registro de invocaciones del modelo y los registros de la pasarela HTTP pueden capturar contenido por defecto; NFR4.2 exige verificar que estén configurados sin contenido.
- **Transporte:** las comunicaciones usan HTTPS (la interfaz y el servicio se despliegan por separado).

## Assumptions & Open Questions

- Abierto: la forma de detectar "entorno desplegado" para el fallo cerrado (se resuelve en Code Generation).
- Abierto: política de CORS entre la interfaz y el servicio, y dónde guarda la interfaz la credencial de sesión (llegan con `u4-access-control` y `u5-web-app`).
