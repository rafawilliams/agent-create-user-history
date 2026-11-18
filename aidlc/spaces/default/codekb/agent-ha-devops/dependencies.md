# Dependencias

## Externas (requirements.txt, todas sin version)
- pandas: `pd.read_excel`, `DataFrame`, `to_excel`.
- openpyxl: motor de lectura/escritura `.xlsx` de pandas (no se importa directamente).
- anthropic: clase `Anthropic`, `messages.create`.
- python-dotenv: `load_dotenv`.

## Servicios externos
- Anthropic Messages API (red, requiere `ANTHROPIC_API_KEY`).

## Internas
Ninguna: modulo unico, sin imports entre ficheros ni referencias circulares.

## Observaciones
Sin versiones fijadas ni lockfile; riesgo de cambios incompatibles al reinstalar. No se hizo auditoria de vulnerabilidades (no se ejecutaron herramientas).
