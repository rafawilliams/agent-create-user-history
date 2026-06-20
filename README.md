# Generador de Historias de Usuario

Script en Python que lee un archivo Excel con una columna `Titulo` y genera,
usando la API de Claude (Anthropic), un Excel de salida con:

- **Titulo**
- **Descripcion** (formato "Como [rol], quiero [accion], para [beneficio]")
- **Criterios de Aceptacion** (3 a 5 criterios, en formato Gherkin cuando aplica)

## Requisitos

- Python 3.9+
- Una API key de Anthropic (https://console.anthropic.com/)

## Instalacion

```bash
pip install -r requirements.txt
```

## Configuracion

1. Copia el archivo `.env.example` a `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env` y coloca tu API key:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

El archivo `.env` esta excluido del control de versiones (ver `.gitignore`).

## Uso

```bash
python generador_historias.py entrada.xlsx salida.xlsx
```

- `entrada.xlsx`: Excel de entrada, debe contener una columna llamada `Titulo`.
- `salida.xlsx`: Excel de salida que se generara con las historias de usuario.

### Ejemplo

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

## Manejo de errores

Si ocurre un error al generar la historia para un titulo especifico (por
ejemplo, problemas de conexion o de API key), la fila correspondiente se
incluye en el Excel de salida con el mensaje de error en la columna
`Descripcion`, y el script continua con el resto de los titulos.

## Estructura del proyecto

```
.
├── generador_historias.py   # Script principal
├── requirements.txt         # Dependencias
├── .env.example              # Plantilla de variables de entorno
├── .gitignore
└── README.md
```
