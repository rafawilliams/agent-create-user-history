# Unit Test Instructions — u1-walking-skeleton

Estrategia de pruebas: Standard (5 a 8 pruebas por componente, más pruebas de integración de los límites clave). Metodología: TDD; cada prueba se escribe antes del código, se ejecuta en rojo y luego se implementa lo mínimo para que pase.

## Requisitos previos

- Python 3.11 o superior y un entorno virtual en la raíz del proyecto.
- Node.js 20 o superior con npm (para las pruebas de `web/`).
- Sin credenciales de AWS: las pruebas automáticas no llaman al modelo real ni a ningún servicio de AWS.

## Configuración de las herramientas

| Parte | Herramienta | Configuración |
|-------|-------------|---------------|
| Servicio | `pytest` y `pytest-cov` | `backend/pyproject.toml` |
| Servicio | Black y Ruff | `backend/pyproject.toml` |
| Pantalla | Vitest y Testing Library | `web/vite.config.ts` |
| Pantalla | Prettier y ESLint | `web/` |

Instalación de las dependencias de desarrollo (una vez):

```bash
python -m pip install -r backend/requirements-dev.txt
cd web && npm install
```

Comandos verificados en Step 3 (el ejecutor arranca sin pruebas): `python -m pytest backend/tests -q` (sale con "no tests ran") y `npm --prefix web run test -- --run src/__tests__` (sale con "No test files found"). Nota: en Git Bash de Windows, `npm --prefix web install` busca el `package.json` en la raíz; la instalación se hace desde `web/`. Las dependencias de Python se instalaron en el intérprete de usuario porque la creación del entorno virtual falló en esta máquina (no se pudo copiar `python.exe`).

## Comandos para ejecutar las pruebas de ESTA unidad

Las pruebas de la unidad están en `backend/tests/` y `web/src/__tests__/`; el comando se limita a esas rutas.

```bash
python -m pytest backend/tests -q
```

```bash
npm --prefix web run test -- --run src/__tests__
```

Cada comando corre solo los archivos de esta unidad. Ninguno es un comando general del proyecto.

## Cobertura

- **Piso:** 80 % de cobertura de líneas (`team.md`, `mvp`). Es un piso del proyecto entero: lo comprueba Build and Test sobre la suite completa del proyecto ensamblado. Una ejecución con el umbral puede fallar por el umbral aunque todas las pruebas pasen; por eso se ejecuta en un comando aparte, sin pasos después, y nunca se baja el umbral para que pase.

```bash
python -m pytest backend/tests -q --cov=backend/story_service --cov-report=term-missing --cov-fail-under=80
```

- **Objetivo de esta unidad:** 80 % o más en `backend/story_service` y en `web/src`, con el mismo piso. Una caída por debajo del piso se informa como una brecha, no se oculta.

## Comando de comprobación de punta a punta (manual)

Ejecuta el servicio completo en local contra el modelo real de Amazon Bedrock y comprueba que el Markdown empieza con "Como analista de negocio". Requiere credenciales de AWS válidas en la máquina y acceso al modelo en us-east-1; no se ejecuta en la suite automática.

```bash
python -m story_service.local_run "Recuperar contraseña"
```

(con `APP_ENV=local` y `ALLOW_SIMULATED_SESSION=true` en el entorno, desde `backend/`). La decisión de adoptarlo como comando de verificación del punto de control queda con la persona.

## Dobles de prueba (mocking)

- El modelo se simula con el modelo simulado de la unidad (`fakes.py`), que devuelve una respuesta fija o un `ModelError` configurado.
- El verificador de sesión usa el verificador simulado y el que falla cerrado.
- El reloj del plazo es inyectable, para probar el plazo de 55 s sin esperar.
- El cliente de `bedrock-runtime` se sustituye con un doble de prueba; nunca se llama a AWS.
- En la pantalla, la llamada a la API se simula; no hay red real.

## Datos de prueba

- Títulos de ejemplo: "Recuperar contraseña", un título vacío, uno de solo espacios y uno de 201 caracteres.
- Respuestas del modelo: una válida que empieza con "Como analista de negocio", una con espacios y saltos de línea al inicio, una en minúsculas ("como analista de negocio") y una vacía.
- Los datos viven dentro de los archivos de prueba; no hay datos guardados ni archivos de datos externos.

## Pruebas que no corren en esta etapa

- El comando de punta a punta contra Bedrock (necesita credenciales de AWS).
- Las comprobaciones de `terraform plan` y la prueba de humo del despliegue (necesitan la cuenta de AWS y el estado remoto de Terraform de `u6-infrastructure`).
