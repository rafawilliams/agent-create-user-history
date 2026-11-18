# Inventario de componentes

## generador_historias
- Tipo: modulo/script CLI Python (`generador_historias.py`).
- Responsabilidad: leer titulos de un Excel, generar historia de usuario y criterios con Claude, escribir el Excel de salida.
- Depende de: pandas, openpyxl (via pandas), anthropic, python-dotenv, stdlib `sys`, `re`, `json`; servicio externo Anthropic API.
- Funciones: `limpiar_texto`, `generar_historia`, `procesar`, `main`.

## Ficheros de datos y configuracion
No son componentes ejecutables: `entrada_ejemplo.xlsx`, `salida_ejemplo.xlsx`, `salida.xlsx`, `requirements.txt`, `.env.example` (detalle en code-structure.md).
