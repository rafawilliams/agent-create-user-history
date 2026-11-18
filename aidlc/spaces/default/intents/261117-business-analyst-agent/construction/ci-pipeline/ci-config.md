# CI Pipeline — Configuración

Documentos de entrada: `code-summary.md` de las seis unidades, `build-and-test-summary.md` y `test-results.md`, y el `ci-pipeline-questions.md` de esta etapa (Q1 y Q2). La canalización ya existe: la construyeron u1, u5 y u6 en Code Generation; esta etapa la documenta, fija sus puertas de calidad y comprueba que cubre lo que Build and Test ejecutó.

## Sources

- [Q1] Trabajos obligatorios para integrar: `backend`, `web` e `infra`. [Q2] Checkov bloquea desde el principio.
- [scope] Decisiones anteriores de la persona: herramienta GitHub Actions, un solo entorno en us-east-1, ramas cortas por cambio integradas en `main` con squash y con revisión (`team.md`); sin repositorio de artefactos.
- [scope] `.github/workflows/ci.yml` y `deploy.yml` tal como quedaron al cerrar Build and Test.

## Herramienta y flujo

| Aspecto | Configuración |
|---------|---------------|
| Herramienta | GitHub Actions; todas las acciones fijadas a un hash de commit de 40 caracteres (`infra/scripts/check_pins.py` lo comprueba en CI) |
| Disparadores de `ci.yml` | Solicitudes de integración y envíos a `main` |
| Despliegue | `deploy.yml`, solo en `main`, con guarda `AWS_APPLY_ROLE_ARN` (se omite con un aviso antes del arranque manual): plan, comprobación y aplicación del mismo plan, publicación de la pantalla, prueba de humo y reversión del alias |
| Identidad en AWS | Federación OIDC de GitHub sin claves: rol de plan (solo `sts:GetCallerIdentity`, `sub` de `pull_request`) y rol de aplicación (`sub` de `main`) |
| Repositorio de artefactos | Ninguno: el paquete de la función lo construye `infra/scripts/build_lambda_package.py` en cada ejecución y lo sube Terraform; la pantalla va a un depósito privado de S3 |
| Estrategia de ramas | Ramas cortas por cambio, squash a `main`, revisión antes de integrar (`team.md`); `main` protegida a mano en el arranque (`infra/README.md`) |

## Trabajos de `ci.yml`

| Trabajo | Qué ejecuta | Comando de Build and Test que refleja |
|---------|-------------|----------------------------------------|
| `backend` (obligatorio) | Black, Ruff y pytest con cobertura mínima de 80 % sobre `backend/` | `cd backend && python -m pytest tests -q --cov=story_service --cov-fail-under=80`, `black --check`, `ruff check` |
| `web` (obligatorio) | Prettier, ESLint, `tsc` y `vite build` con valores ficticios de `VITE_*`, Vitest con cobertura mínima de 80 %, `check:bundle` (400 KB gzip), `check:secrets`, `check:inline` y `npm audit --omit=dev --audit-level=high` | Los mismos comandos de `web/` |
| `infra` (obligatorio) | Construcción del paquete de la función, `terraform fmt -check`, `validate` y `terraform test` en `infra/` y `infra/bootstrap/`, `check_pins.py`, `check_secrets.py`, prueba real del paquete (`REQUIRE_REAL_PACKAGE=1`) y Checkov | Los mismos comandos de Terraform y de los scripts |
| `infra-scripts` | Black, Ruff y pytest con cobertura mínima de 80 % de `infra/scripts/` | `cd infra/scripts && python -m pytest -q --cov=. --cov-fail-under=80` |
| `infra-plan` | `terraform plan` contra un estado vacío con el rol de plan y valores ficticios de secretos, y `check_plan.py`; solo para solicitudes del propio repositorio y con `AWS_PLAN_ROLE_ARN` | Revisión previa del plan (no la ejecutó Build and Test: necesita AWS) |
| `security` | Comprobaciones del diseño: sin `ALLOW_SIMULATED_SESSION` desplegado y sin registro de invocaciones de Bedrock | Ya cubiertas por las afirmaciones de `terraform test` |

## Lo que la canalización no puede probar

La canalización nunca ejecutó en GitHub: los dos archivos parsean como YAML pero no se corrió `actionlint` ni un flujo real. Checkov y `pip --platform` en el ejecutor de GitHub se ejecutarán por primera vez allí.

## Assumptions & Open Questions

- Supuesto: los nombres de los trabajos de arriba son los que se marcan como comprobaciones obligatorias en la protección de `main`; la persona la configura a mano en el arranque.
- Abierto: el primer `plan` real y el primer paso de Checkov pueden pedir ajustes (lista de omisiones, permisos del rol de plan); si Checkov falla la primera vez, Q2 pide corregirlo en una solicitud aparte antes de integrar.
