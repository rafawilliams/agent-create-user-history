# Security Design — u6-infrastructure

Documentos de entrada: `security-requirements.md`, `tech-stack-decisions.md` y `contract-summary.md`; el código existente de `infra/` y `.github/workflows/ci.yml`. No hubo preguntas en esta etapa: las decisiones de seguridad las fijaron Q1 a Q3 de NFR Requirements y los requisitos NFR5.1 a NFR5.9. Esta unidad es de empaquetado: su diseño es la estructura de las dos raíces de Terraform, las identidades y las comprobaciones.

## Sources

- [Q1] Secretos de GitHub. [Q2] Variable de GitHub para los correos. [Q3] Bloqueo nativo del depósito de S3.
- [scope] `security-requirements.md` NFR1.1, NFR3.1, NFR4.1 a NFR4.3 y NFR5.1 a NFR5.9; `tech-stack-decisions.md` (dos raíces, `check_plan.py`, `terraform test`).

- [scope] `performance-requirements`, `scalability-requirements`, `reliability-requirements` y `observability-requirements`: no se producen para una unidad de empaquetado (solo seguridad y pila tecnológica); la capacidad, los plazos y los registros del servicio son de u1, u3 y u4, y aquí solo se configuran sus valores (NFR1.1, NFR3.1, NFR4.2). `functional-spec`: u6 no tiene diseño funcional (sin lógica de aplicación).

## Estructura de las dos raíces

| Raíz | Quién la aplica | Qué crea | Estado |
|------|-----------------|----------|--------|
| `infra/bootstrap/` | La persona, una sola vez, con credenciales administrativas | El depósito de estado, el proveedor OIDC de GitHub, el límite de permisos, el rol de plan y el rol de aplicación | Local, ignorado por git y respaldado por la persona fuera del repositorio; se reconstruye con `terraform import` (NFR5.6) |
| `infra/` | La canalización: `plan` con el rol de plan en las solicitudes y `plan` más `apply` con el rol de aplicación en `main` | La función y su rol, la pasarela, la pantalla (depósito, distribución, política de cabeceras), el grupo de usuarios de Cognito con sus federaciones y las métricas | Remoto en el depósito de S3 con bloqueo nativo |

El rol de aplicación no puede modificar nada de la raíz `infra/bootstrap/` (NFR5.4), de modo que quien controla la canalización no controla las identidades que la gobiernan.

## Identidades de la canalización (NFR5.2, NFR5.3)

| Elemento | Diseño |
|----------|--------|
| Proveedor OIDC | Uno para `token.actions.githubusercontent.com` con `aud` igual a `sts.amazonaws.com` |
| Rol de plan | Confianza con `sub` igual a `repo:<organización>/<repositorio>:pull_request` y `aud`; permiso único `sts:GetCallerIdentity` (el plan de las solicitudes corre con `init -backend=false`, contra un estado vacío, y no necesita leer recursos); denegaciones explícitas de las lecturas que devuelven secretos (`cognito-idp:DescribeIdentityProvider` y `GetIdentityProviderByIdentifier`, `lambda:GetFunction`, `GetFunctionConfiguration` y `GetFunctionUrlConfig`, `secretsmanager:*`, `ssm:GetParameter*`) y de la lectura de los objetos del depósito de estado; sin escritura en recursos |
| Rol de aplicación | Confianza con `sub` igual a `repo:<organización>/<repositorio>:ref:refs/heads/main` y `aud`; permisos: crear y administrar solo los recursos de la aplicación, con el límite de permisos |
| Forks | El trabajo de plan solo corre cuando el repositorio de origen de la solicitud es el propio (`github.event.pull_request.head.repo.full_name` igual a `github.repository`); las solicitudes de forks no reciben identidad ni secretos y se omiten |
| Secretos en el plan | El plan de las solicitudes recibe valores ficticios de los secretos de las federaciones y la lista de correos; los reales solo existen en `deploy.yml` |
| Código ejecutable | `check_plan.py` falla si aparecen fuentes de datos `external` o aprovisionadores `local-exec` o `remote-exec` |
| Estado y secretos | El rol de plan no lee el estado (que contiene el secreto de las federaciones), de modo que el código de una solicitud no puede extraerlo con ese rol; el rol de aplicación solo se asume desde `main` |

## Límite de permisos y rol de aplicación (NFR5.4)

- El límite es una política administrada que permite solo los servicios de la aplicación (Lambda, API Gateway, S3 y CloudFront de la pantalla, Cognito, CloudWatch Logs y métricas, y los roles de la función) y deniega IAM fuera de esos roles.
- Hay dos límites: el de los roles que Terraform crea (solo `logs:CreateLogStream`, `logs:PutLogEvents` y `bedrock:InvokeModel`, sin IAM ni S3) y el techo del propio rol de aplicación. Ambos y la política del rol de aplicación llevan una denegación (`DenyUnboundedRoles`) de `iam:CreateRole` e `iam:PutRolePermissionsBoundary` cuando el límite no es el esperado, con lo que ningún rol creado puede quedar sin límite.
- El rol de aplicación tiene el límite puesto. Su política permite `iam:CreateRole` solo si la solicitud lleva la condición `iam:PermissionsBoundary` igual al límite; `iam:AttachRolePolicy`, `iam:PutRolePolicy`, `iam:UpdateAssumeRolePolicy` y `iam:PassRole` están acotados al prefijo del nombre de rol de la aplicación (`business-analyst-agent-*`), y `PassRole` solo hacia Lambda.
- Servicios que permiten el límite y la política del rol de aplicación (cada uno con sus acciones de creación, lectura, modificación y borrado de los recursos de la aplicación, acotadas por el prefijo de nombres o por el depósito de la pantalla): `lambda` (función, alias, permisos), `apigateway` (API REST, recursos, métodos, integraciones, respuestas de pasarela, despliegue, etapa y ajustes), `s3` (depósito de la pantalla, su política y la publicación de archivos; como el depósito usa un prefijo de nombre y no un nombre fijo, sus permisos se acotan con un patrón de nombre), `cloudfront` (distribución, control de acceso al origen, política de cabeceras y `CreateInvalidation`), `cognito-idp` (grupo, cliente, dominio y proveedores de identidad), `logs` (grupo de registros y filtros de métricas), `cloudwatch` (métricas de la aplicación), `bedrock:InvokeModel` (solo para la política del rol de la función, con los recursos de NFR5.5), el acceso al objeto de estado del depósito de estado (lectura, escritura y borrado del estado y del `.tflock`) y las acciones del ciclo de vida de los roles con prefijo, incluidas las de lectura que el refresco usa (`iam:GetRolePolicy`, `iam:ListRolePolicies`, `iam:ListAttachedRolePolicies`, `iam:ListInstanceProfilesForRole`) (`iam:CreateRole`, `DeleteRole`, `GetRole`, `TagRole`, `UpdateRole`, `AttachRolePolicy`, `DetachRolePolicy`, `PutRolePolicy`, `DeleteRolePolicy`, `UpdateAssumeRolePolicy`, `PassRole`). La configuración de la cuenta de la pasarela para los registros y `iam:CreateServiceLinkedRole` no se permiten: se evitan en el diseño (sin registro de acceso de la pasarela) y, si hicieran falta, los crea la persona.
- Denegaciones explícitas: modificar o borrar el límite, el proveedor OIDC, los dos roles de la canalización y el depósito de estado, y quitar el límite de un rol (`iam:DeleteRolePermissionsBoundary`).

## Estado remoto (NFR5.6)

| Aspecto | Diseño |
|---------|--------|
| Depósito | Privado, acceso público bloqueado, versionado, cifrado con la clave administrada por S3 y política que exige TLS |
| Bloqueo | `use_lockfile = true`: el bloqueo es un objeto `.tflock` junto al estado |
| Permisos | Rol de aplicación: lectura, escritura y borrado del objeto de estado y del `.tflock`; rol de plan: ningún acceso al depósito de estado; el rol de aplicación tiene `s3:ListBucket` sobre el depósito, que el backend de Terraform necesita, limitado con la condición `StringLikeIfExists` sobre `s3:prefix` (así una lectura de un estado o de un `.tflock` que aún no existe devuelve 404 y no 403 en el primer `init`) a una lista explícita de prefijos: el del estado (clave fija del backend, por ejemplo `business-analyst-agent/`) y el prefijo `env:/` que `init` consulta para los espacios de trabajo; ninguno tiene otras acciones sobre el depósito mismo (política, versionado, cifrado, borrado, listado de versiones fuera del prefijo) |
| Falta del depósito | La configuración del backend no tiene alternativa local: si el depósito no existe, `init` falla y la canalización se detiene |

## Secretos y datos de las personas (NFR5.1, NFR4.3)

| Dato | Origen | Dónde queda |
|------|--------|-------------|
| Credenciales OAuth de Google y de Microsoft | Secretos cifrados de GitHub (`TF_VAR_*`) | Variables de Terraform con `sensitive = true`; el secreto de cliente queda en el estado cifrado (limitación del proveedor) |
| Lista de correos permitidos | Variable de GitHub | Variable de Terraform sensible con validación (hasta 50, minúsculas, formato de correo, sin duplicados vacíos); llega a la función como variable de entorno de texto (dato personal de acceso restringido) |
| Identificadores públicos (región, grupo, cliente, dominio) | Salidas de Terraform | Variables `VITE_` de la compilación de la pantalla; sin secretos |

`check_plan.py` verifica en `terraform show -json` que esas variables son sensibles (solo la estructura del plan, nunca los valores, por lo que los valores ficticios de las solicitudes no producen ruido); tiene una lista de tipos de recurso permitidos (`aws_lambda_*`, `aws_api_gateway_*`, `aws_cloudwatch_log_*`, `aws_cloudwatch_*` de métricas, `aws_s3_bucket*` solo del depósito de la pantalla, `aws_cloudfront_*`, `aws_cognito_*`, roles y políticas de IAM con el prefijo de la aplicación) y una lista de tipos protegidos contra eliminación o reemplazo (`aws_cognito_user_pool`, `aws_cloudfront_distribution`, `aws_s3_bucket`, `aws_lambda_function`); una comprobación de patrones revisa que no haya claves ni secretos literales en `infra/`; los `.tfvars` con valores reales están en `.gitignore`.

## Permisos de la función y del servicio (NFR5.5, NFR4.2, NFR4.1, NFR3.1, NFR1.1)

| Tema | Diseño |
|------|--------|
| Rol de ejecución de la función | Una política escrita con `jsonencode`: `bedrock:InvokeModel` sobre el ARN exacto del perfil de inferencia y sobre el modelo base con comodín de región limitado al identificador del modelo (el perfil enruta entre regiones); permisos de escritura de su propio grupo de registros; nada de IAM, Cognito ni S3 |
| Registros | Retención de 14 días; sin registro de invocaciones de Bedrock; sin registros de acceso de la distribución ni del depósito de la pantalla |
| Almacenes | Solo existen el depósito de la pantalla y el de estado; `check_plan.py` mantiene una lista de tipos de recurso permitidos y falla ante cualquier otro (tabla, base de datos, depósito adicional) |
| Límites de uso y de tiempo | Límite de la pasarela de 1 solicitud por segundo sostenida y ráfaga de 5; concurrencia reservada de 5 (AWS exige dejar al menos 10 ejecuciones sin reservar en la cuenta: es un supuesto de cuota que se confirma al desplegar); tiempos de 55 s (servicio, en el código), 57 s (función) y 58 s (integración de la pasarela) |

## Cognito y hospedaje (NFR5.8, NFR5.9)

Los recursos se escriben para cumplir una por una las afirmaciones de `security-requirements.md`: grupo sin registro propio y con protección contra eliminación, cliente público sin secreto con flujo de código y PKCE, vigencias de 8 horas, retorno y cierre solo con la dirección de la distribución, proveedores `Google` y `Microsoft` con el mapeo de `email` y `email_verified`; depósito privado con control de acceso al origen, política de cabeceras con la política de contenido exacta, `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy` y `frame-ancestors 'none'`, y CORS del servicio con el origen exacto, `GET,POST,DELETE,OPTIONS`, `Authorization,Content-Type` y las respuestas de error de la pasarela (`DEFAULT_4XX` y `DEFAULT_5XX`). Las dependencias entre recursos siguen el orden sin ciclos de u5 (la API REST y el dominio de Cognito primero; luego la política de cabeceras y la distribución; luego el cliente de Cognito y el CORS).

## Canalización (NFR5.7)

| Flujo | Se ejecuta | Qué hace |
|-------|------------|----------|
| `ci.yml` | Solicitudes y `main` | `terraform fmt -check`, `validate`, `terraform test`, `check_plan.py` sobre un plan, Checkov, comprobación de acciones fijadas por hash y de patrones de secretos; `plan` con el rol de lectura solo para solicitudes del propio repositorio |
| `deploy.yml` | Solo `main` | Se omite con un aviso mientras no exista la variable `AWS_APPLY_ROLE_ARN` (antes del arranque); en un solo trabajo y con el grupo de concurrencia `deploy` (sin cancelar ejecuciones en curso): `terraform plan -out` sobre el commit fusionado, `check_plan.py` sobre ese mismo plan y `terraform apply` de ese mismo archivo, que nunca se sube como artefacto ni se imprime con valores sensibles (solo el resumen); después compila y publica la pantalla y ejecuta la prueba de humo; si la prueba falla, el flujo termina en rojo, captura antes del `apply` la versión que apunta el alias `live` y, si la prueba falla, hace un segundo `apply` con la variable `live_version` igual a esa versión previa (así Terraform y el alias no derivan y el siguiente `apply` no vuelve a promover la versión mala); termina en rojo y avisa que la pantalla debe volver a desplegarse a mano desde el commit anterior |
| Reglas del repositorio | Lista de verificación del arranque | `main` protegida: solo por solicitud con CI obligatoria, sin envíos directos y sin excepción de administradores; la persona lo confirma en el arranque (el `GITHUB_TOKEN` de los flujos no puede leer esa configuración) |

Las versiones: Terraform 1.11 o superior en `required_version` y en los flujos, proveedor `aws` con rango acotado y archivo de bloqueo versionado, y cada `uses:` fijado a un hash de 40 caracteres con la versión como comentario.

## Assumptions & Open Questions

- Supuesto: `<organización>/<repositorio>` se toma de variables del arranque (el nombre real del repositorio de GitHub); la persona lo informa al ejecutar el arranque.
- Supuesto: el plan simulado no comprueba el efecto real del límite de permisos ni la cuota de la pasarela; se confirman al desplegar.
- Abierto: el texto exacto de la lista de verificación del arranque se escribe en Code Generation.
