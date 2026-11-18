# Domain Design — Plan y preguntas

Plan: identificar los bloques de código que se van a escribir (componentes), qué entidades posee cada uno y cómo se llaman entre sí. Este paso no decide cómo se despliega (eso es Units Generation) ni la tecnología de cada bloque. La base es lo que ya sabemos: una interfaz web (`wireframes.md`, `mockups.md`), un servicio que genera la historia llamando a un modelo de IA, y el acceso con Gmail u Outlook (`requirements.md`, `stories.md`).

## Q1. [Arquitectura] ¿Cómo se divide la lógica de generación en el servicio?

Contexto: el servicio recibe el título, arma la petición al modelo, interpreta la respuesta y produce la historia con sus criterios. Se puede escribir como un solo bloque o como varios.

- A. Un solo componente de generación que arma la petición, interpreta la respuesta y produce la historia (recomendado: la lógica es pequeña y cambia en conjunto)
- B. Varios componentes: uno para armar la petición, otro para interpretar la respuesta y otro para dar formato
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Arquitectura] ¿El acceso al modelo de IA es un componente aparte?

Contexto: se van a evaluar Amazon Titan y Claude Sonnet y se decidirá después cuál usar (FR7.1). Un componente aparte permite cambiar de modelo sin tocar la lógica de generación.

- A. Sí, un componente de acceso al modelo, separado de la generación (recomendado)
- B. No, el acceso al modelo va dentro del componente de generación
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Arquitectura] ¿Dónde vive el texto de las instrucciones al modelo (el prompt)?

Contexto: el script actual lleva el prompt en el código (`PROMPT_SISTEMA`) y define el formato de salida con 3 a 5 criterios; el nuevo debe pedir 2 a 3 criterios en Gherkin en español.

- A. En el código del componente de generación, versionado junto con él
- B. En un archivo de configuración que se puede cambiar sin modificar el código de la lógica
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q4. [Arquitectura] ¿Cómo convive el agente nuevo con el script actual de Excel?

Contexto: indicaste que el agente actual se mantiene en uso hasta que el MVP sea aceptado. Esto decide si se comparte código o se deja intacto.

- A. El script actual queda intacto; el prompt y el formato se reutilizan copiándolos al código nuevo, en una carpeta aparte del mismo repositorio
- B. Se separa la lógica de generación del script actual para que lo usen tanto el script como el servicio nuevo
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q5. [Arquitectura] ¿Quién arma el Markdown final?

Contexto: la interfaz muestra la vista previa y el texto Markdown de la misma historia (FR4.2) y copia el Markdown (FR4.3).

- A. El servicio devuelve la historia y los criterios como datos, y la interfaz arma la vista previa y el Markdown
- B. El servicio devuelve el Markdown ya armado, y la interfaz solo lo muestra y lo formatea para la vista previa
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
