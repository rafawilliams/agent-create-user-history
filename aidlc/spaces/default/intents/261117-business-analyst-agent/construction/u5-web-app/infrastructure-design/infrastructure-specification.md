# Infrastructure Specification — u5-web-app

Documentos de entrada: `performance-design.md`, `security-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: el alojamiento (depósito privado más red de contenido, pasarela REST ampliada a 60 s) lo decidió la persona en u1 y las políticas de seguridad vienen de NFR5.4 y NFR5.5.

## Sources

- [scope] Decisiones de infraestructura de u1 (depósito privado más red de contenido) y de u4 (grupo de usuarios de Cognito creado por u6).
- [scope] `performance-design.md` (presupuesto, caché), `security-design.md` (política de contenido, direcciones de retorno) y `contract-summary.md` (requisitos de alojamiento de la interfaz).
- [scope] `scalability-design`, `reliability-design` y `observability-design`: no se producen para una unidad de tipo ui; la capacidad, la disponibilidad y los registros del servicio son de u1 y u6.

## Deployment

| Facet | Choice | Rationale |
|-------|--------|-----------|
| Modelo de alojamiento | Sitio estático: un depósito privado de Amazon S3 detrás de una distribución de Amazon CloudFront con control de acceso al origen; sin servidor propio | Decisión de u1; sin cómputo que operar |
| Dirección | El nombre que asigna CloudFront (`*.cloudfront.net`) con su certificado por defecto; HTTPS obligatorio y HTTP redirigido a HTTPS; sin dominio propio en el MVP (la versión mínima de TLS no es configurable, ver la fila de CloudFront) | NFR5.4; sencillez y costo |
| Contenido | La salida de `vite build` (`web/dist`): `index.html` y archivos con nombre de contenido (hash) | NFR1.3 |
| Caché | `index.html` con `Cache-Control: no-cache` (se revalida siempre); los archivos con hash con `public, max-age=31536000, immutable`; no hay rutas de aplicación, la raíz del sitio es la única página | Despliegues sin versiones mezcladas |
| Versión de la pantalla | Una sola; el depósito tiene versionado de objetos activo (de u1) | Retroceso |
| Configuración de la pantalla | Las variables `VITE_` (región, grupo, dominio, cliente de Cognito y origen del servicio) se fijan en la compilación a partir de salidas de Terraform; no hay secretos | NFR5.1 |
| Entornos | Uno solo, al integrar en `main` | Práctica del equipo |
| IaC | Terraform en `infra/` (de u6); u5 no crea recursos por su cuenta | Práctica del equipo |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---------|------|---------------|-------|
| Amazon S3 (depósito `web`, de u1) | Guarda los archivos de la pantalla | Privado, acceso público bloqueado, versionado activo, cifrado por defecto; solo la distribución lo lee | Sin registros de acceso (NFR4.2) |
| Amazon CloudFront (distribución `web`, de u1) | Sirve la pantalla por HTTPS | Objeto raíz `index.html`; origen S3 con control de acceso al origen; política de cabeceras de respuesta con la política de contenido exacta de NFR5.4, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` y `frame-ancestors 'none'`; HTTPS con el certificado de CloudFront. Con el certificado por defecto `*.cloudfront.net` CloudFront no permite elegir la versión mínima de TLS (la fija él mismo); exigir TLS 1.2 requeriría un dominio propio y un certificado de ACM, que quedan fuera del MVP: es un riesgo aceptado y se declara a la persona | Sin registros de acceso ni WAF en el MVP |
| Política de cabeceras de respuesta | Entrega las cabeceras de seguridad de la pantalla | Recurso propio de Terraform asociado al comportamiento por defecto; incluye `connect-src` con el origen del servicio, el dominio de Cognito y `cognito-idp.<región>.amazonaws.com` (esta última se confirma en Code Generation y se quita de NFR5.4 y de la política si ningún flujo de la biblioteca la usa) | NFR5.4; los orígenes se derivan como indica el orden de creación |
| Amazon Cognito (cliente público, de u4 y u6) | Inicia y cierra la sesión | Direcciones de retorno y de cierre: la raíz de la distribución, valor exacto; proveedores llamados `Google` y `Microsoft` | Depende de la dirección de CloudFront (Terraform la toma de la distribución) |
| API Gateway REST (de u1) | Recibe C1 y C2 de la pantalla | CORS con el origen exacto de la distribución en cada recurso que llama la pantalla (`/v1/stories` y `/v1/session`): solicitud previa (OPTIONS) con `Allow-Methods` igual a `GET,POST,DELETE,OPTIONS` y `Allow-Headers` igual a `Authorization,Content-Type`, y `Access-Control-Allow-Origin` también en las respuestas de error de la pasarela (401, 403, 429, 5xx) y en las de la función | Origen permitido igual al de `web_origin` |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|-----------------|------------|----------------|-----------------|
| Depósito y distribución de la pantalla | u1-walking-skeleton (diseño) / u6-infrastructure (Terraform) | u5-web-app | u5 publica archivos con la identidad de la canalización de despliegue; nadie más escribe en el depósito |
| Cliente público de Cognito | u4-access-control (especificación) / u6-infrastructure (creación) | u5-web-app | La pantalla usa solo ese cliente, sin secreto |
| Política de cabeceras de respuesta | u6-infrastructure | u5-web-app | Contiene la política de contenido de NFR5.4 |

## Requisitos para u6-infrastructure

| Criterio | Qué se afirma en el plan |
|----------|--------------------------|
| Depósito privado | Acceso público bloqueado; política que solo permite lectura a la distribución |
| Cabeceras | La política de cabeceras incluye exactamente la política de contenido de NFR5.4 y las demás cabeceras de esta tabla |
| Direcciones de Cognito | Retorno y cierre iguales a `https://<dominio de la distribución>/` y sin direcciones locales en el grupo desplegado |
| Proveedores | Nombres `Google` y `Microsoft` |
| CORS del servicio | Preflight en `/v1/stories` y `/v1/session` con `GET,POST,DELETE,OPTIONS` y `Authorization,Content-Type`; origen exacto de la distribución; la cabecera también en las respuestas de error de la pasarela; una prueba de humo del preflight con ese origen |
| TLS | No se afirma una versión mínima de TLS (certificado por defecto de CloudFront); solo HTTPS y redirección de HTTP |
| Orden de Terraform sin ciclos | `terraform validate` y `plan` no reportan ciclos: el origen del servicio de `connect-src` se construye como `https://<id de la API REST>.execute-api.<región>.amazonaws.com` (depende solo del recurso REST, no de la etapa ni del despliegue); el dominio alojado de Cognito es un recurso independiente del cliente; la distribución depende de ambos, la política de cabeceras de la distribución, y el cliente de Cognito y el CORS de la pasarela dependen del dominio de la distribución |

## Orden de creación (sin ciclos)

1. Recurso REST de la API (solo su identificador) y dominio alojado de Cognito.
2. Política de cabeceras de respuesta y distribución (usan el identificador de la API y el dominio de Cognito).
3. Cliente público de Cognito, CORS y respuestas de error de la pasarela, función y etapa (usan el dominio de la distribución).
4. Compilación y publicación de la pantalla con las salidas ya conocidas.

## Notas para u6-infrastructure

- La pasarela no tiene autorizador (el 401 lo emite el servicio) y u1 solo define la respuesta `THROTTLED`: u6 añade las respuestas de pasarela `DEFAULT_4XX` y `DEFAULT_5XX` con `Access-Control-Allow-Origin` del origen exacto.
- La variable `VITE_` del origen del servicio usa exactamente el host `https://<id de la API REST>.execute-api.<región>.amazonaws.com` (la etapa va en la ruta, no en el host), el mismo que `connect-src`.

## Assumptions & Open Questions

- Riesgo aceptado (a confirmar con la persona): sin dominio propio la versión mínima de TLS de la distribución no se puede fijar en 1.2.

- Supuesto: el dominio de CloudFront no cambia entre despliegues (la distribución no se recrea); si se recreara, cambian las direcciones de Cognito y las cabeceras en el mismo plan.
- Abierto: el dominio propio y los registros de acceso quedan fuera del MVP.
