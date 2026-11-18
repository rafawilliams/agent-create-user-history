# CI/CD Pipeline — u6-infrastructure

Documentos de entrada: `security-design.md`, `infrastructure-specification.md`, `tech-stack-decisions.md` y la canalización existente (`.github/workflows/ci.yml`). No hubo preguntas en esta etapa.

## Arranque manual (una sola vez, por la persona)

El orden evita la dependencia circular: la dirección de retorno que Google y Microsoft necesitan es la del dominio de Cognito, que se conoce de antemano porque su prefijo es fijo en el código (`https://<prefijo>.auth.us-east-1.amazoncognito.com/oauth2/idpresponse`); no depende de la distribución ni del primer despliegue.

1. Con credenciales administrativas, aplicar `infra/bootstrap/` informando `github_repository` y `state_bucket_name`: crea el depósito de estado, el proveedor OIDC, el límite de permisos y los roles de plan y de aplicación. Guardar su estado local fuera del repositorio (está ignorado por git).
2. Verificar las cuotas de la cuenta antes del primer despliegue y pedir su ampliación si hace falta: ejecuciones concurrentes de Lambda (AWS exige dejar al menos 10 sin reservar, por lo que reservar 5 necesita una cuota de 15 o más; si no se amplía, se fija `reserved_concurrency` en `-1`, que `infra/variables.tf` ya prevé) y tiempo máximo de integración de la pasarela REST (58 000 ms; sin ampliación el tope es de 29 000 ms y el `apply` falla). Confirmar también el acceso de la cuenta al modelo de Bedrock.
3. Leer el prefijo del dominio de Cognito en la variable `cognito_domain_prefix` de `infra/variables.tf` (valor por defecto fijo, con un sufijo propio del proyecto); si el prefijo ya está tomado en la región, la persona lo cambia en ese archivo antes de seguir. Con él, crear la aplicación de Google y la de Microsoft Entra con la dirección de retorno `https://<prefijo>.auth.us-east-1.amazoncognito.com/oauth2/idpresponse` y copiar sus identificadores y secretos.
4. En GitHub: crear los secretos `TF_VAR_google_client_id`, `TF_VAR_google_client_secret`, `TF_VAR_microsoft_client_id` y `TF_VAR_microsoft_client_secret` (los nombres de las variables de entorno de Terraform distinguen mayúsculas y minúsculas), la variable `TF_VAR_allowed_emails` y las variables `AWS_PLAN_ROLE_ARN`, `AWS_APPLY_ROLE_ARN` y `STATE_BUCKET_NAME`.
5. Proteger `main`: solo por solicitud, con la comprobación de CI obligatoria, sin envíos directos y sin excepción de administradores. La persona lo confirma aquí: el `GITHUB_TOKEN` de los flujos no tiene permiso para leer esa configuración y no se usa un token con permisos de administración.
6. Integrar en `main` la solicitud con el código de infraestructura: el primer `deploy.yml` hace el primer `apply` y la publicación de la pantalla.

Antes del paso 4, la canalización solo valida: `ci.yml` omite el plan (guarda `AWS_PLAN_ROLE_ARN`) y el trabajo de `deploy.yml` se omite con un aviso mientras `AWS_APPLY_ROLE_ARN` no exista, de modo que un push a `main` no falla en rojo por falta de arranque.

## Flujos

| Flujo | Cuándo | Pasos | Falla si |
|-------|--------|-------|----------|
| `ci.yml` | Solicitudes y `main` | Servicio (formato, análisis y pruebas con cobertura de 80 %), pantalla (de u5) y Terraform: `fmt -check`, `validate`, `terraform test`, `check_plan.py`, Checkov, acciones fijadas por hash y patrones de secretos; `plan` con el rol de lectura solo para solicitudes del propio repositorio (forks se omiten) con valores ficticios de secretos | Cualquier paso falla (bloquea la integración) |
| `deploy.yml` | Solo `main`, un trabajo, grupo de concurrencia `deploy` | Guarda de arranque (se omite con un aviso si falta `AWS_APPLY_ROLE_ARN`); `init` con `-backend-config` del depósito de `STATE_BUCKET_NAME`; `plan -out` sobre el commit fusionado; `check_plan.py`; `apply` del mismo plan; compilación y publicación de la pantalla (primero los archivos con hash con caché larga, sin borrar los antiguos (`aws s3 sync` sin `--delete`; la limpieza queda fuera del MVP), y por último `index.html` con `no-cache`) e invalidación de `/index.html`; las variables `VITE_` salen de `terraform output -raw` tras el `apply`; prueba de humo | Falla el plan, la comprobación o la prueba de humo (el flujo queda en rojo) |

## Prueba de humo

Un script posterior al despliegue comprueba: la raíz de la pantalla responde 200 con la política de contenido exacta y las demás cabeceras; el preflight de `/v1/stories` y de `/v1/session` responde con el origen exacto de la distribución, los métodos y las cabeceras permitidas; y `POST /v1/stories` sin token responde 401 con el cuerpo de error de C1. No llama al modelo ni inicia sesión.

## Retroceso

- **Servicio:** el flujo captura antes del `apply` la versión a la que apunta el alias `live`; si la prueba de humo falla, hace un segundo `apply` con `live_version` igual a esa versión.
- **Pantalla:** se vuelve a desplegar el commit anterior; el depósito versionado conserva las versiones anteriores de `index.html`.
- **Primer despliegue:** si falla, no hay versión previa a la que volver: se corrige hacia adelante en una nueva solicitud (o la persona destruye lo creado a mano).
- **Terraform:** se revierte el commit en una nueva solicitud y se aplica; las eliminaciones o reemplazos de recursos protegidos las aplica la persona a mano si son intencionales.

## Secretos y credenciales

La canalización usa identidad federada de GitHub (sin claves en el repositorio); los secretos y las variables viven en GitHub y llegan como variables sensibles de Terraform; el plan que se aplica no se sube como artefacto ni se imprime con valores sensibles.

## Assumptions & Open Questions

- Supuesto: los nombres de los secretos y variables de GitHub de este documento son los que Code Generation implementa.
- Nota: `ci.yml` hace `init -backend=false`, por lo que el plan de las solicitudes se calcula contra un estado vacío (muestra todo como creación): sirve para `check_plan.py` (tipos permitidos, sensibilidad) pero no detecta eliminaciones; esas las detecta `deploy.yml` con el estado real.
- Abierto: la persona debe ejecutar el arranque manual antes del primer despliegue; hasta entonces la canalización solo valida (`fmt`, `validate`, `terraform test`, `check_plan.py` y Checkov) y no despliega.
