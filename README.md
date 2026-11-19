# Business Analyst Agent

Aplicación web que convierte el título de una funcionalidad en una historia de usuario lista para pegar en Jira: una historia en formato «Como [rol], quiero [acción], para [beneficio]» y de 2 a 3 criterios de aceptación en Gherkin, en español, como Markdown.

- **Pantalla:** React + MUI, con inicio de sesión de Amazon Cognito (Google y Microsoft), vista previa y copiado del resultado.
- **Servicio:** API Gateway + Lambda (Python) + Amazon Bedrock (Claude Sonnet por defecto), en `us-east-1`. Sin base de datos: no se guarda nada.
- **Acceso:** solo las personas de una lista de correos permitidos; el servicio verifica el token de Cognito en cada solicitud.
- **Infraestructura:** Terraform y GitHub Actions (CI en cada solicitud de integración; despliegue al integrar en `main`).

El script de Excel original (`generador_historias.py`) sigue disponible y no depende de lo anterior: ver [Script de Excel](#script-de-excel-generador_historiaspy).

## Estructura

```
.
├── backend/                 # Servicio Lambda (paquete story_service) y sus pruebas
├── web/                     # Pantalla React + MUI (Vite)
├── infra/                   # Terraform de la aplicación, arranque manual (bootstrap/) y scripts de CI
├── .github/workflows/       # ci.yml y deploy.yml
├── docs/                    # Listas de títulos para evaluar modelos y calidad de las historias
├── aidlc/                   # Registro del flujo AI-DLC (requisitos, diseño, decisiones, pruebas)
└── generador_historias.py   # Script de Excel original
```

## Desarrollo local

Requisitos: Python 3.12+, Node.js 20+ y Terraform.

**Servicio** (`backend/`):

```bash
cd backend
pip install -r requirements-dev.txt
cp .env.example .env        # sin valores reales; ver los comentarios del archivo
python -m pytest tests -q --cov=story_service --cov-fail-under=80
```

**Pantalla** (`web/`):

```bash
cd web
npm ci
cp .env.example .env        # VITE_*: salidas de Terraform (api_url, Cognito)
npm run dev                 # servidor local
npm test                    # pruebas (Vitest)
npm run coverage            # cobertura (mínimo 80 %)
npm run lint && npm run format:check && npm run build
npm run check:bundle        # carga inicial bajo 400 KB gzip
```

**Infraestructura** (`infra/`, sin cuenta de AWS):

```bash
cd infra
terraform init -backend=false
terraform fmt -check -recursive && terraform validate
terraform test              # proveedor simulado
```

## Calidad y CI

`ci.yml` corre en cada solicitud de integración. Bloquean la integración los trabajos de servicio, pantalla e infraestructura (formato, validación, `terraform test`, acciones fijadas por hash, secretos y Checkov). Los de scripts de infraestructura, plan y verificaciones de seguridad solo informan. Cobertura mínima de líneas: 80 %. Desarrollo con TDD; identificadores del código en inglés.

## Despliegue

Un solo entorno en `us-east-1`. Antes del primer despliegue hay un arranque manual, una sola vez (estado de Terraform, rol de GitHub por OIDC, cuotas, aplicaciones de Google y Microsoft, secretos de GitHub y protección de `main`): ver [`infra/README.md`](infra/README.md). Después, `deploy.yml` planifica, aplica, publica la pantalla y hace una prueba de humo al integrar en `main`.

## Estado

Construido y probado en local y en CI. Pendiente antes de operar: el arranque manual y el primer despliegue; la evaluación con el modelo real de Bedrock y el inicio de sesión real con Google y Microsoft; el límite diario por persona (NFR3.2, no construido) y enmendar NFR4.5 (8 KB frente a 16 KB). El detalle está en `aidlc/spaces/default/intents/261117-business-analyst-agent/construction/build-and-test/build-and-test-summary.md`.

---

## Script de Excel (generador_historias.py)

Script en Python que lee un archivo Excel con una columna `Titulo` y genera,
usando la API de Claude (Anthropic), un Excel de salida con:

- **Titulo**
- **Descripcion** (formato "Como [rol], quiero [accion], para [beneficio]")
- **Criterios de Aceptacion** (3 a 5 criterios, en formato Gherkin cuando aplica)

### Requisitos

- Python 3.9+
- Una API key de Anthropic (https://console.anthropic.com/)

### Instalacion

```bash
pip install -r requirements.txt
```

### Configuracion

1. Copia el archivo `.env.example` a `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env` y coloca tu API key:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

El archivo `.env` esta excluido del control de versiones (ver `.gitignore`).

### Uso

```bash
python generador_historias.py entrada.xlsx salida.xlsx
```

- `entrada.xlsx`: Excel de entrada, debe contener una columna llamada `Titulo`.
- `salida.xlsx`: Excel de salida que se generara con las historias de usuario.

#### Ejemplo

Excel de entrada (`entrada.xlsx`):

| Titulo                              |
|--------------------------------------|
| Iniciar sesion en la plataforma      |
| Recuperar contrasena olvidada        |
| Exportar reporte de ventas a PDF     |

Ejecucion:

```bash
python generador_historias.py entrada.xlsx salida.xlsx
```

Salida (`salida.xlsx`) con columnas `Titulo`, `Descripcion` y
`Criterios de Aceptacion` generadas por Claude para cada fila.

### Manejo de errores

Si ocurre un error al generar la historia para un titulo especifico (por
ejemplo, problemas de conexion o de API key), la fila correspondiente se
incluye en el Excel de salida con el mensaje de error en la columna
`Descripcion`, y el script continua con el resto de los titulos.

### Estructura del proyecto

```
.
├── generador_historias.py   # Script principal
├── requirements.txt         # Dependencias
├── .env.example              # Plantilla de variables de entorno
├── .gitignore
└── README.md
```
