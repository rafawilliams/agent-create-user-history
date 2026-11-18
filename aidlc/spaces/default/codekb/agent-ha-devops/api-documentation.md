# Documentacion de API

## API expuesta
Ninguna API HTTP. Solo interfaz de linea de comandos.

### CLI
`python generador_historias.py <entrada.xlsx> <salida.xlsx>`
- Argumentos: exactamente dos; de lo contrario imprime el uso y sale con codigo 1.
- Entrada: Excel con columna `Titulo` (si falta, `ValueError` listando las columnas).
- Salida: Excel con columnas `Titulo`, `Descripcion`, `Criterios de Aceptacion`.
- Entorno: `ANTHROPIC_API_KEY` (de entorno o `.env`).

## Contratos internos
- `limpiar_texto(texto: str) -> str`
- `generar_historia(client: Anthropic, titulo: str) -> dict` con claves `descripcion` (str) y `criterios` (lista de str). Lanza si el JSON es invalido o faltan claves.
- `procesar(ruta_entrada: str, ruta_salida: str) -> None`
- `main()`

## API consumida
Anthropic Messages API via SDK: `client.messages.create(model="claude-sonnet-5-5", max_tokens=1024, system=PROMPT_SISTEMA, messages=[{role:user, content:"Titulo de la funcionalidad: <titulo>"}])`. Respuesta esperada: texto JSON `{"descripcion": str, "criterios": [str]}`. Sin autenticacion propia mas alla de la API key; sin reintentos ni timeout explicito.
