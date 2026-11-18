# Estructura del codigo

## Organizacion
Repositorio plano, sin paquetes ni subcarpetas de codigo.

| Ruta | Clasificacion | Notas |
|---|---|---|
| `generador_historias.py` | Servicio/UseCase + Controller (CLI) + Utility | Unico modulo, 117 lineas |
| `requirements.txt` | Configuration | 4 dependencias sin version |
| `.env.example` | Configuration | Plantilla de `ANTHROPIC_API_KEY` |
| `.gitignore` | Configuration | Ignora `.env`, `__pycache__/`, `*.pyc`, `salida.xlsx`, `~$*.xlsx` y el bloque AI-DLC |
| `README.md` | Documentacion | Uso, configuracion, manejo de errores |
| `entrada_ejemplo.xlsx`, `salida_ejemplo.xlsx` | Static/Asset | Datos de ejemplo (binarios, no leidos) |
| `salida.xlsx` | Static/Asset (ignorado) | Salida generada localmente |

## Dentro de `generador_historias.py`
- Constantes: `COLUMNA_TITULO`, `MODELO`, `PROMPT_SISTEMA`.
- `limpiar_texto(texto)`: normaliza espacios.
- `generar_historia(client, titulo)`: llamada a Claude y parseo JSON.
- `procesar(ruta_entrada, ruta_salida)`: orquestacion y E/S Excel.
- `main()`: valida `sys.argv` (exactamente 2 argumentos).

## Patrones
Funciones de modulo, sin clases; hints de tipo; mensajes y prompts en espanol; sin pruebas.
