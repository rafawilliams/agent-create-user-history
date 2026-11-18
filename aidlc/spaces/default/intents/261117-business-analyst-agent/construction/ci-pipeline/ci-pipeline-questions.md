# CI Pipeline — Preguntas

Contexto: la canalización de CI ya existe y la construyeron las unidades: `.github/workflows/ci.yml` con seis trabajos (`backend`, `web`, `infra-scripts`, `infra`, `infra-plan`, `security`) y `deploy.yml` para el despliegue. Esta etapa documenta la configuración y las puertas de calidad y verifica que cubren lo que Build and Test ejecutó. Ya están decididas por ti en etapas anteriores: la herramienta (GitHub Actions), la estrategia de ramas (ramas cortas por cambio, integradas en `main` con squash y con revisión) y que no hay repositorio de artefactos (el paquete de la función lo construye CI y lo sube Terraform; la pantalla va a un depósito de S3). Quedan dos decisiones sobre las puertas de calidad.

## Q1. [Producto] ¿Qué trabajos de CI son obligatorios para integrar en `main`?

Contexto: las puertas de calidad son los trabajos que GitHub exige como «comprobaciones obligatorias» antes de permitir la integración (la protección de `main` se configura a mano en el arranque).

- A. Los seis trabajos (`backend`, `web`, `infra-scripts`, `infra`, `infra-plan`, `security`): ningún cambio entra a `main` si alguno falla. `infra-plan` se omite en cambios de forks y mientras no exista el rol de plan
- B. Solo `backend`, `web` y `infra`: los otros tres informan pero no bloquean
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q2. [Calidad] ¿Checkov bloquea la integración desde el primer día?

Contexto: Checkov (dentro del trabajo `infra`) nunca se ha ejecutado: las 31 omisiones documentadas de `infra/.checkov.yaml` se escribieron por expectativa y puede marcar hallazgos en su primera ejecución en CI.

- A. Bloquea desde el principio: si falla la primera vez, se ajusta la lista de omisiones o el código en una solicitud aparte antes de integrar
- B. Informativo las primeras ejecuciones (no bloquea) y pasa a bloquear cuando la persona lo decida, una vez ajustada la lista
- C. Not yet defined
- X. Other (please specify)

[Answer]: A
