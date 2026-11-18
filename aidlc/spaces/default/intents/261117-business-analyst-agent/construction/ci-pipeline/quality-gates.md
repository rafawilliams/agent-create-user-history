# CI Pipeline — Puertas de calidad

Documentos de entrada: `ci-config.md`, `build-and-test-summary.md`, `test-results.md` y `ci-pipeline-questions.md` (Q1 y Q2).

## Sources

- [Q1] Obligatorios: `backend`, `web` e `infra`. [Q2] Checkov bloquea desde el principio.
- [scope] Pisos y metas de calidad de `team.md` y de los `Testing Contract` de las unidades (cobertura de líneas de 80 %, formateadores y analizadores).

## Puertas que bloquean la integración en `main`

| Puerta | Trabajo | Falla si |
|--------|---------|----------|
| Estilo del servicio | `backend` | Black o Ruff encuentran diferencias o errores |
| Pruebas y cobertura del servicio | `backend` | Falla una prueba o la cobertura de líneas es menor de 80 % |
| Estilo y tipos de la pantalla | `web` | Prettier, ESLint o `tsc` fallan |
| Pruebas y cobertura de la pantalla | `web` | Falla una prueba o la cobertura de líneas es menor de 80 % |
| Presupuesto de carga | `web` | La carga inicial supera 400 KB gzip o incluye la vista previa (`check:bundle`) |
| Secretos y scripts en línea del paquete | `web` | `check:secrets` o `check:inline` fallan |
| Auditoría de producción | `web` | `npm audit --omit=dev --audit-level=high` encuentra hallazgos |
| Formato y validez de Terraform | `infra` | `fmt -check` o `validate` fallan en `infra/` o `infra/bootstrap/` |
| Afirmaciones de Terraform | `infra` | Falla alguna afirmación de `terraform test` (97 hoy) |
| Paquete de la función | `infra` | El paquete no contiene `jwt` ni `cryptography`, no es de Linux o supera los límites de Lambda |
| Acciones fijadas y secretos | `infra` | `check_pins.py` o `check_secrets.py` fallan |
| Revisión estática de seguridad | `infra` | Checkov falla (Q2: bloquea desde el principio) |

## Puertas que informan y no bloquean (Q1)

| Puerta | Trabajo | Qué informa |
|--------|---------|-------------|
| Scripts de infraestructura | `infra-scripts` | Estilo y pruebas de `check_plan.py`, `check_pins.py`, `check_secrets.py` y de empaquetado (110 pruebas, piso de 80 %); las pruebas de los scripts solo corren aquí, de modo que con Q1 un cambio que las rompa no bloquea la integración (el trabajo `infra` usa los scripts pero no los prueba) |
| Plan contra estado vacío | `infra-plan` | Estructura del plan y `check_plan.py` (omitido en forks y sin rol de plan) |
| Verificaciones de seguridad del diseño | `security` | Ausencia de `ALLOW_SIMULATED_SESSION` y del registro de invocaciones de Bedrock |

## Cobertura frente a Build and Test

Las puertas que bloquean ejecutan los mismos comandos que registró Build and Test, con estos resultados al cerrar la etapa: servicio 563 pruebas con 99,68 %, pantalla 186 con 98,4 %, 97 afirmaciones de Terraform (en `infra`, que bloquea) y 110 pruebas de scripts con 97,65 % (en `infra-scripts`, que con Q1 no bloquea). Lo que ninguna puerta cubre (y Build and Test dejó sin verificar): el inicio de sesión real con Cognito, Google y Microsoft, el arranque de la función en AWS, la cabecera servida por CloudFront, el comportamiento en un navegador real, la calidad de las historias con el modelo real (NFR2) y la evaluación de modelos.

## Assumptions & Open Questions

- Brecha declarada de Q1: las pruebas de los scripts de infraestructura (que protegen `check_plan.py`, `check_pins.py` y el paquete) están en `infra-scripts`, que no bloquea; si la persona quiere que bloqueen, basta marcar también `infra-scripts` como obligatorio.
- Abierto: con Q1 el trabajo `infra-plan` no bloquea, de modo que un cambio cuyo plan falle podría integrarse; la persona puede volverlo obligatorio cuando el rol de plan exista y el plan se haya ejecutado una vez en CI.
