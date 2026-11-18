# Vision de negocio

## Proposito
`agent-ha-devops` es un script de linea de comandos que automatiza la redaccion de historias de usuario. Toma un Excel con titulos de funcionalidades y devuelve otro Excel con una descripcion y criterios de aceptacion generados por Claude.

## Funcionalidad clave
- Entrada: Excel con columna `Titulo` (`generador_historias.py`, `COLUMNA_TITULO`).
- Por cada titulo: descripcion "Como [rol], quiero [accion], para [beneficio]" y 3 a 5 criterios, en formato Gherkin (Dado/Cuando/Entonces) cuando es posible (`PROMPT_SISTEMA`).
- Salida: Excel con columnas `Titulo`, `Descripcion`, `Criterios de Aceptacion`.
- Un fallo en un titulo no detiene el lote: la fila se escribe con `ERROR: ...`.

## Usuarios
Analistas de negocio o equipos de producto que preparan backlog (inferido del prompt y README; no hay otra documentacion).

## Limites actuales
Solo uso local por CLI, un usuario, sin interfaz web ni API. Relevante para el intent: el Business Analyst Agent nuevo (React + API Gateway + Lambda + Bedrock) reemplazaria este flujo por uno web; este codigo es la referencia funcional del prompt y del formato de salida.
