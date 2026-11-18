# NFR Requirements — u6-infrastructure — Preguntas

Contexto: u6 crea con Terraform todo lo que las otras unidades especificaron (el servicio, la pasarela, la pantalla estática, el grupo de usuarios de Cognito con las federaciones de Google y Microsoft, la canalización de despliegue y el estado remoto). Ya están decididos: GitHub Actions, un solo entorno en us-east-1, un rol de lectura para `plan` y otro de aplicación solo desde `main`, estado remoto con depósito de arranque manual, sin dominio propio, sin alarmas. Quedan tres decisiones de seguridad que cambian cómo se guardan los secretos y datos de las personas.

## Q1. [Seguridad] ¿Dónde viven las credenciales OAuth de Google y de Microsoft que necesita Cognito?

Contexto: el recurso de proveedor de identidad de Cognito exige el secreto de cliente en su configuración, así que acabará dentro del estado de Terraform (cifrado, en el depósito de estado) sea cual sea el origen.

- A. Secretos cifrados de GitHub, pasados a Terraform como variables sensibles (`TF_VAR_*`); no se guardan en el repositorio ni en AWS Secrets Manager
- B. AWS Secrets Manager (la persona los crea una vez) y Terraform los lee con un dato de lectura; agrega un servicio y su costo, y el valor igual queda en el estado
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Seguridad] ¿Dónde se guarda la lista de correos permitidos (hasta 50)?

Contexto: u4 la lee de una variable de entorno de la función; son direcciones de personas, no secretos, pero conviene no exponerlas en el repositorio.

- A. Una variable de GitHub Actions (no un secreto) que Terraform recibe como variable sensible; no se guarda en archivos del repositorio
- B. Un archivo `.tfvars` versionado en el repositorio privado
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Seguridad] ¿Cómo se bloquea el estado de Terraform?

Contexto: el depósito de estado (versionado y cifrado) se crea con un paso manual único. Hay un solo equipo de una persona y un despliegue por integración en `main`, pero dos ejecuciones simultáneas podrían corromper el estado.

- A. Bloqueo nativo de Terraform en el propio depósito de S3 (`use_lockfile`), sin tabla de DynamoDB
- B. Tabla de DynamoDB para el bloqueo (método clásico), con su costo y un recurso más que crear a mano
- C. Not yet defined
- X. Other (please specify)

[Answer]: A
