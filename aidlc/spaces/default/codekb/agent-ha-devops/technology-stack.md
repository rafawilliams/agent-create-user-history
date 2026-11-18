# Stack tecnologico

| Elemento | Detalle | Evidencia |
|---|---|---|
| Lenguaje | Python 3.9+ (segun README); version real del `.venv` no verificada | README.md |
| Gestor de paquetes | pip | requirements.txt |
| Datos | pandas, openpyxl (sin versiones) | requirements.txt |
| IA | SDK `anthropic`; modelo `claude-sonnet-5-5`, `max_tokens=1024` | generador_historias.py |
| Configuracion | python-dotenv, variable `ANTHROPIC_API_KEY` | .env.example |
| Formato I/O | Excel `.xlsx` | generador_historias.py |
| Contenedores, IaC, CI/CD, frontend | No existen | raiz del repo |

Versiones: ninguna dependencia esta fijada; las versiones instaladas viven en `.venv/`, que no se analizo.
