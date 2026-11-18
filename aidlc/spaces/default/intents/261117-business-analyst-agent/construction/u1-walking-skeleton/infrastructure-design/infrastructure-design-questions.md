# Infrastructure Design — u1-walking-skeleton — Preguntas

Contexto: el esqueleto es una pantalla mínima, una pasarela HTTP, una función y el modelo en Amazon Bedrock, en us-east-1, con Terraform, un único entorno y despliegue automático al integrar en `main`. Estas preguntas cierran tres decisiones que el diseño no puede tomar solo.

## Q1. [Operaciones] ¿Qué herramienta de CI/CD ejecuta las pruebas, el linter y el despliegue?

Contexto: es un punto pendiente desde las prácticas del equipo. El repositorio ya está en Git; el despliegue debe correr pruebas, cobertura de 80 % y linters antes de integrar.

- A. GitHub Actions
- B. AWS CodePipeline con CodeBuild
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Arquitectura] ¿Cómo se aloja la pantalla mínima?

Contexto: es una pantalla estática de React. Con un solo entorno y 5 personas, interesa lo más simple y barato.

- A. Un depósito de almacenamiento privado detrás de una distribución de red de contenido (HTTPS)
- B. Amazon Amplify Hosting
- C. Solo en local durante el esqueleto; el alojamiento se hace con `u5-web-app`
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Arquitectura] ¿Qué punto de entrada se usa para la API, dado que el servicio puede tardar hasta 55 segundos?

Contexto: las pasarelas HTTP de AWS tienen un límite de integración que suele rondar los 29-30 segundos y no siempre es ampliable. La revisión anterior pidió resolver esto sin acortar en silencio el corte de 50 segundos del modelo.

- A. Pasarela REST con el límite de integración ampliado a 60 segundos mediante la cuota de la cuenta (si la cuenta lo permite)
- B. URL de función de la propia función, con modo de respuesta en flujo, sin pasarela
- C. Pasarela HTTP estándar y aceptar el límite de unos 30 segundos, bajando el corte del modelo
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
