# Unit Test Instructions — u6-infrastructure

Estrategia de pruebas: Standard. Metodología: TDD; cada prueba se escribe antes del código, se ejecuta en rojo y luego se implementa lo mínimo para que pase.

## Requisitos previos

- Terraform 1.11 o superior (en esta máquina hay 1.16.3) y acceso al registro de Terraform para `terraform init -backend=false` (descarga de proveedores, sin credenciales de AWS).
- Python 3.11 o superior con `pytest` y `pytest-cov` (ya instalados por u1) para los scripts de `infra/scripts/`.
- Sin credenciales de AWS: las afirmaciones usan proveedor simulado y los datos de cuenta se simulan con valores explícitos; no se ejecuta `plan` ni `apply`.

## Configuración de las herramientas

| Parte | Herramienta | Configuración |
|-------|-------------|---------------|
| Terraform | `terraform test` con `mock_provider "aws"` | `infra/tests/*.tftest.hcl` y `infra/bootstrap/tests/*.tftest.hcl` |
| Scripts | `pytest` y `pytest-cov` | `infra/scripts/pytest.ini` (o `pyproject.toml`) con el piso de 80 % |
| Scripts | Black y Ruff | Misma configuración que `backend/pyproject.toml` |

## Comandos para ejecutar las pruebas de ESTA unidad

```bash
cd infra && terraform init -backend=false && terraform test
```

```bash
cd infra/bootstrap && terraform init -backend=false && terraform test
```

```bash
cd infra/scripts && python -m pytest -q
```

Ninguno es un comando general del proyecto: el servicio y la pantalla tienen los suyos y no cambian.

## Cobertura

- **Piso:** 80 % de cobertura de líneas (`team.md`, `mvp`) sobre los scripts de Python; el código de Terraform se cubre con las afirmaciones del plan. Lo comprueba Build and Test sobre el proyecto ensamblado, en un comando aparte y sin bajar el umbral:

```bash
cd infra/scripts && python -m pytest -q --cov=. --cov-report=term-missing --cov-fail-under=80
```

## Otras comprobaciones

```bash
cd infra && terraform fmt -check -recursive && terraform validate
```

## Comando de punta a punta del proyecto (manual, ya aprobado)

```bash
cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"
```

No ejercita la infraestructura. La verificación real (arranque, `plan` y `apply` con el rol de la canalización, Cognito con Google y Microsoft y la prueba de humo) solo es posible con la cuenta de AWS y las credenciales de la persona.

## Dobles de prueba (mocking)

- `mock_provider "aws"` con `override_data` para los datos de cuenta y de región; las políticas de IAM y de confianza se escriben con `jsonencode`.
- Planes de ejemplo en JSON para los scripts de Python; nunca se llama a AWS ni a GitHub desde las pruebas.

## Datos de prueba

- Correos inventados (0, 1, 50 y 51 entradas), valores ficticios de identificadores y secretos y un repositorio de ejemplo; todo vive dentro de los archivos de prueba.

## Pruebas que no corren en esta etapa

- `terraform plan` y `terraform apply` contra AWS, el arranque y el despliegue.
- La verificación de cuotas, del acceso al modelo, de la protección de `main` y de la prueba de humo: manuales, en el arranque y en el primer despliegue.
- Checkov: corre en CI.
