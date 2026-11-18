# Infrastructure Specification — u6-infrastructure

Documentos de entrada: `security-design.md` de u6, `components.md`, `contract-summary.md` (incluida su sección de alojamiento de la interfaz) y el código existente de `infra/`. No hubo preguntas en esta etapa: el alojamiento, la identidad y la seguridad ya están decididos por u1, u4, u5 y NFR Requirements y NFR Design de u6. Esta especificación reúne todo en un inventario de lo que u6 construye.

## Sources

- [scope] `security-design.md` de u6 (dos raíces, identidades, límite de permisos, estado remoto, secretos).
- [scope] Especificaciones de infraestructura de u1 (servicio y pantalla), u4 (Cognito) y u5 (alojamiento y CORS), tal como están resumidas en `contract-summary.md` y en `infra/` existente.
- [scope] `scalability-design`, `reliability-design` y `observability-design`: no se producen para una unidad de empaquetado; la capacidad (5 personas), los plazos y los registros son valores que se configuran aquí (NFR1.1, NFR3.1, NFR4.2).

- [scope] `performance-design`, `logical-components` y `functional-spec`: u6 es una unidad de empaquetado y no los produce (solo `security-design.md` y la trazabilidad); el rendimiento, los plazos y la división de componentes vienen de las unidades que u6 aloja y aquí solo se configuran sus valores.

## Deployment

| Facet | Choice | Rationale |
|-------|--------|-----------|
| Modelo | Sin servidores: Lambda, API Gateway REST, S3 con CloudFront y Cognito; ninguna instancia ni red propia | Uso ocasional de 5 personas; sin estado |
| Región y entorno | us-east-1, un solo entorno que se despliega al integrar en `main` | Decisiones del proyecto y de `team.md` |
| Raíces de Terraform | `infra/bootstrap/` (manual, una vez) e `infra/` (canalización) | `security-design.md`: el rol que despliega no gobierna sus propias identidades |
| Estado | Raíz `infra/`: depósito de S3 con `use_lockfile`; raíz de arranque: estado local respaldado fuera del repositorio | NFR5.6 |
| Orden de creación | API REST y dominio de Cognito, luego política de cabeceras y distribución, luego cliente de Cognito, CORS y etapa, y al final la compilación y publicación de la pantalla | Sin ciclos (u5) |
| Despliegue de la aplicación | `deploy.yml` en `main`: plan, comprobación y aplicación del mismo plan; luego publicación de la pantalla y prueba de humo | NFR5.7, NFR8.2 |
| Retroceso | Servicio: segundo `apply` con `live_version` igual a la versión previa; pantalla: volver a desplegar el commit anterior; Terraform: revertir el commit y aplicar | `team.md` (Deployment) |
| Almacenamiento de datos | Ninguno: no hay base de datos ni tablas; los únicos depósitos de S3 son el de la pantalla y el de estado (sin datos de las personas) | NFR4.1 |
| Nombres | Prefijo `business-analyst-agent` para todos los recursos y los roles de la aplicación | Acota los permisos del rol de aplicación |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---------|------|---------------|-------|
| AWS Lambda | Servicio de generación (u1 a u4) | Python, 512 MB, tiempo de 57 s, concurrencia reservada de 5, alias `live`, variables: `APP_ENV` igual a `prod`, `BEDROCK_MODEL_ID`, `CORS_ALLOWED_ORIGIN` (el origen de la distribución), `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID` y `ALLOWED_EMAILS`; sin `ALLOW_SIMULATED_SESSION` | Ya existe en `infra/main.tf`; u6 agrega las variables de Cognito y de correos |
| Amazon API Gateway (REST) | Entrada HTTPS | Rutas `POST /v1/stories`, `GET` y `DELETE /v1/session` y preflight en ambos recursos; integración de 58 s; límite de 1 solicitud por segundo y ráfaga de 5; CORS con el origen exacto; respuestas de error de la pasarela (`THROTTLED`, `DEFAULT_4XX`, `DEFAULT_5XX`) con la cabecera de origen | Nuevo: el recurso `/v1/session`, el preflight y las respuestas por defecto |
| Amazon Bedrock | Modelo de IA | Solo la invocación del perfil de inferencia configurado; registro de invocaciones desactivado | Sin recurso de configuración de registro (NFR4.2) |
| Amazon Cognito | Identidad | Grupo sin registro propio y con protección contra eliminación, dominio alojado con prefijo propio, cliente público con PKCE y vigencias de 8 horas, proveedores `Google` y `Microsoft` con el mapeo de `email` y `email_verified` | Nuevo; secretos de las federaciones por variables sensibles |
| Amazon S3 y CloudFront | Pantalla | Depósito privado con control de acceso al origen, versionado y cifrado; distribución con HTTPS, objeto raíz `index.html`, política de cabeceras con la política de contenido exacta y caché por tipo de archivo | Existe en `infra/main.tf`; u6 agrega la política de cabeceras y la caché |
| Amazon CloudWatch | Registros y métricas | Grupo de registros con 14 días, métricas `requests_total`, `errors_total` y `generation_duration_ms`; sin alarmas | Ya existe |
| AWS IAM | Identidades | Rol de ejecución de la función con la política de NFR5.5; en la raíz de arranque: proveedor OIDC de GitHub, rol de plan, rol de aplicación y límite de permisos | Roles con prefijo de la aplicación |
| Amazon S3 (estado) | Estado de Terraform | Privado, versionado, cifrado, con bloqueo nativo y política que exige TLS | Creado por la raíz de arranque |

## Entradas y salidas de Terraform

| Tipo | Nombre | Origen o uso |
|------|--------|--------------|
| Variable | `region`, `name_prefix`, `bedrock_model_id`, `reserved_concurrency`, `live_version`, `throttle_rate_limit`, `throttle_burst_limit`, `integration_timeout_ms` | Ya existen en `infra/variables.tf` |
| Variable (nueva) | `allowed_emails` | Variable de GitHub; sensible, con la validación de NFR4.3 |
| Variable (nueva) | `google_client_id`, `google_client_secret`, `microsoft_client_id`, `microsoft_client_secret` | Secretos de GitHub (`TF_VAR_*`); sensibles |
| Variable (arranque) | `github_repository`, `state_bucket_name` | La persona las informa al ejecutar el arranque |
| Salida | `api_url` (incluye la etapa `/live`; es el valor de `VITE_API_URL`; el origen de `connect-src` es solo su host), `web_url`, `web_bucket`, `lambda_function_name` | Ya existen |
| Salida (nueva) | `cognito_region`, `cognito_user_pool_id`, `cognito_domain` y `cognito_client_id` | Alimentan `VITE_COGNITO_REGION`, `VITE_COGNITO_USER_POOL_ID`, `VITE_COGNITO_DOMAIN` y `VITE_COGNITO_CLIENT_ID` de la pantalla; el flujo de despliegue las lee con `terraform output -raw` tras el `apply` |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|-----------------|------------|----------------|-----------------|
| Función, pasarela, depósito y distribución de la pantalla | u6-infrastructure (creación) | u1, u3, u4, u5 | Solo la canalización con el rol de aplicación los modifica |
| Grupo de usuarios y cliente público de Cognito | u6-infrastructure (creación) | u4 (verificación) y u5 (inicio de sesión) | Cliente sin secreto; el servicio verifica y la pantalla inicia la sesión |
| Estado remoto y roles de la canalización | u6-infrastructure (arranque manual) | La canalización | Los roles de la canalización no pueden modificarlos |
| Variables y secretos de GitHub | La persona | u6 | Solo los lee la canalización; ningún valor real en el repositorio |

## Disposición del código y detalles de implementación

- `infra/`: `main.tf`, `variables.tf`, `outputs.tf` y `versions.tf` (existen), más `cognito.tf` (grupo, dominio, cliente y proveedores), `web_headers.tf` (política de cabeceras y caché), `api_session.tf` (recurso `/v1/session`, preflight y respuestas por defecto), `iam.tf` (rol de la función), `tests/*.tftest.hcl` (afirmaciones de `terraform test`) y `scripts/check_plan.py` con sus pruebas; `infra/bootstrap/` con su propio `main.tf`, `variables.tf`, `outputs.tf` y pruebas.
- Sin ciclo entre recursos: el origen de CORS de la función y de la pasarela es `https://<dominio de la distribución>`; la distribución depende de la política de cabeceras, que depende del identificador de la API REST y del dominio de Cognito, pero no de la etapa ni del despliegue de la pasarela.
- El `triggers` del despliegue de la pasarela incluye los recursos nuevos (`/v1/session`, preflight y respuestas por defecto) para que un cambio vuelva a desplegar la etapa.
- Las variables de Terraform se leen de `TF_VAR_<nombre en minúsculas>`; el nombre del depósito de estado se pasa con `-backend-config`.

## Criterios verificables

Son los de `security-requirements.md` (NFR5.1 a NFR5.9, NFR4.1 a NFR4.3, NFR3.1, NFR1.1), comprobados con `terraform test`, `check_plan.py`, Checkov y la lista de verificación del arranque; la prueba de humo comprueba la cabecera exacta de la pantalla, el preflight con el origen exacto y el rechazo de una solicitud sin token.

## Assumptions & Open Questions

- Las cuotas de la cuenta (concurrencia de Lambda de 15 o más para reservar 5 y tiempo de integración de la pasarela de 58 000 ms) y el acceso al modelo de Bedrock se verifican en el arranque manual antes del primer despliegue (`cicd-pipeline.md`), con `reserved_concurrency` igual a `-1` como alternativa; los valores del código (NFR3.1, NFR1.1) son los diseñados, y la cuota real es una condición de la cuenta.
- Supuesto: el prefijo del dominio de Cognito debe ser único en la región; se propone `business-analyst-agent` más un sufijo aleatorio fijo en el código.
- Abierto: las credenciales de Google y de Microsoft y la lista de correos las entrega la persona antes del primer despliegue.
