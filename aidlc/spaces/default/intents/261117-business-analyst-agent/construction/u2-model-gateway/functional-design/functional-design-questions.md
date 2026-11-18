# Functional Design — u2-model-gateway — Preguntas

Contexto: u1 ya dejó un acceso mínimo a Amazon Bedrock (Claude Sonnet 4.6 por defecto, verificado de punta a punta). u2 lo completa: elegir el modelo por configuración entre Amazon Titan y Claude Sonnet, traducir fallos y tiempos de espera, y evaluar los dos modelos con títulos de ejemplo (US7.1: AC7.1.1 a AC7.1.3). Estas preguntas cierran las decisiones que el diseño no puede tomar solo.

## Q1. [Producto] ¿Con qué criterio se decide entre Amazon Titan y Claude Sonnet tras la evaluación?

Contexto: el criterio sigue abierto desde `requirements.md` (FR7.1). Sin él, la evaluación no puede terminar en una decisión.

- A. Calidad de la historia revisada a mano (formato correcto y relación con el título), y a igualdad, el modelo más rápido
- B. Calidad revisada a mano, y a igualdad, el modelo más barato
- C. Solo el cumplimiento del formato de forma automática (empieza con "Como analista de negocio", 2 a 3 criterios en Gherkin en español)
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q2. [Producto] ¿Con qué títulos de ejemplo se evalúa?

Contexto: la evaluación necesita un conjunto fijo de títulos que se repita para ambos modelos (AC7.1.1). El proyecto ya tiene un Excel de ejemplo (`entrada_ejemplo.xlsx`) del script anterior, que no se modifica.

- A. Los títulos de `entrada_ejemplo.xlsx`, leídos tal cual
- B. Una lista nueva de unos 10 títulos escritos en un archivo de texto del proyecto
- C. Una lista corta de 5 títulos que yo propongo y tú apruebas antes de evaluar
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q3. [Operaciones] ¿Dónde se guarda el resultado de la evaluación y la decisión?

Contexto: AC7.1.2 pide que exista un registro con el resultado de cada modelo y la decisión. El servicio no guarda datos de personas, pero estos son títulos de ejemplo del equipo.

- A. Un archivo Markdown versionado en el proyecto (por ejemplo `docs/evaluacion-modelos.md`)
- B. Solo en el registro del flujo de trabajo del proyecto (la carpeta de la unidad), sin archivo en el código
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Arquitectura] ¿Qué hacer cuando un modelo no está habilitado en la cuenta al evaluarlo?

Contexto: AC7.1.3. Ya ocurrió con Claude Sonnet 5.5 y el formulario de uso de Anthropic. Un modelo no habilitado devuelve un error de acceso.

- A. Se registra el bloqueo con el mensaje de AWS y queda pendiente solicitar el acceso, sin descartar el modelo; la evaluación sigue con los demás
- B. La evaluación se detiene hasta que todos los modelos estén habilitados
- C. Not yet defined
- X. Other (please specify)

[Answer]: A
