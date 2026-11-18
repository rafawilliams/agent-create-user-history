# Tech Stack Decisions — u6-infrastructure

Documentos de entrada: `requirements.md`, `contract-summary.md`, `technology-stack.md` y `security-requirements.md` de u6. Respuestas: `nfr-requirements-questions.md` (Q1 a Q3).

## Sources

- [Q1] Secretos de GitHub. [Q2] Variable de GitHub. [Q3] Bloqueo nativo en S3.
- [scope] `team.md` (Terraform, GitHub Actions, un entorno, us-east-1); `infra/` existente de u1 (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`) y `.github/workflows/ci.yml`.
- [scope] `functional-spec` y `rules`: u6 no tiene diseño funcional ni reglas propias (unidad de empaquetado).

## Decisiones

| Tema | Decisión | Razón |
|------|----------|-------|
| Infraestructura como código | Terraform 1.11 o superior (el bloqueo nativo de S3 es estable desde esa versión) con el proveedor `aws`, versión con rango acotado y archivo de bloqueo versionado; se actualizan `required_version` en `infra/versions.tf` y la versión de `ci.yml` (hoy 1.9.8) | Práctica del equipo; Q3 |
| Raíces de Terraform | Dos raíces: `infra/bootstrap/` (se aplica una vez a mano con credenciales de la persona: depósito de estado, proveedor OIDC, los dos roles de la canalización y el límite de permisos) e `infra/` (la aplicación, aplicada por la canalización con el rol de aplicación) | NFR5.4 y NFR5.6: el rol que despliega no puede modificar lo que lo gobierna |
| Estado | Backend `s3` con `use_lockfile = true`, cifrado y versionado; sin tabla de DynamoDB | Q3 |
| CI/CD | `ci.yml` (solicitudes y `main`): `terraform fmt -check`, `validate`, `terraform test`, `check_plan.py`, Checkov y, para solicitudes del propio repositorio, `plan` con el rol de lectura y valores ficticios de secretos. `deploy.yml` solo en `main`: `plan` y `apply` sobre el commit fusionado con el rol de aplicación, sin reutilizar un plan de una solicitud | NFR5.2, NFR5.3; u1 |
| Identidad de la canalización | Proveedor OIDC de GitHub en IAM, rol de plan (lectura, `sub` de `pull_request`) y rol de aplicación (`sub` de `main`), con límite de permisos | NFR5.2 a NFR5.4 |
| Pruebas de infraestructura | `terraform test` con `command = plan` y proveedor simulado (políticas con `jsonencode`, datos de cuenta con `override_data`); `infra/scripts/check_plan.py` sobre `terraform show -json` para ausencias, sensibilidad y eliminaciones; sin llamar a AWS | NFR8; convención de verificación de `security-requirements.md` |
| Revisión estática de seguridad | Checkov con versión fijada y omisiones documentadas una a una | NFR5; u1 |
| Secretos | Variables de Terraform `sensitive = true` alimentadas por `TF_VAR_*` desde secretos de GitHub (Google y Microsoft); la lista de correos desde una variable de GitHub, validada en Terraform | Q1, Q2; NFR4.3 |
| Prueba de humo | Un script (`curl`) tras el despliegue: la raíz de la pantalla responde 200 con las cabeceras exactas, el preflight del servicio responde con el origen exacto y `POST /v1/stories` sin token responde 401 con el cuerpo de error de C1 | `team.md` (Deployment); u1 |
| Retroceso | Servicio: el alias `live` apunta a la versión anterior de la función; pantalla: se vuelve a desplegar el commit anterior (versionado del depósito); Terraform: se revierte el commit y se aplica | `team.md` (Deployment) |
| Eliminaciones protegidas | `check_plan.py` hace fallar el despliegue ante `delete` o reemplazo de los tipos protegidos (grupo de usuarios, distribución, depósitos, función); la persona los aplica a mano si el cambio es intencional | NFR8 |
| Región | us-east-1 | Decisión del proyecto |

## Requisitos de calidad de la implementación

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR8.1 | Cada afirmación de seguridad de `security-requirements.md` se escribe primero como prueba (de `terraform test` o de `check_plan.py`) en rojo y luego se implementa; `terraform fmt -check` y `terraform validate` pasan; la suite corre sin credenciales de AWS | La suite falla si una afirmación no se cumple y se ejecuta en CI antes de integrar | NFR8 |
| NFR8.2 | El despliegue siempre aplica el plan hecho sobre el commit fusionado en `main` y falla antes del `apply` si el plan elimina o reemplaza un recurso protegido o contiene un tipo de recurso no permitido | Una prueba de `check_plan.py` con planes de ejemplo (con eliminación, con tipo no permitido y limpio) y la revisión de `deploy.yml` | NFR8; u1 |

## Assumptions & Open Questions

- Supuesto: las versiones exactas de Terraform, del proveedor y de Checkov se eligen en Code Generation con las vigentes y probadas.
- Supuesto: el plan simulado comprueba atributos declarados, no su efecto real en AWS: la efectividad del límite de permisos y de la cuota de la pasarela solo se confirma al desplegar.
- Abierto: el arranque manual necesita credenciales administrativas de la persona una sola vez; su lista de verificación se escribe en Code Generation.
