# Decisions — Business Analyst Agent

Documentos de entrada: `requirements.md`, `stories.md`, `architecture.md`, `component-inventory.md` y `team-practices.md`. Catálogo: `components.md`. Respuestas: `domain-design-questions.md` (DD Qn).

## ADR-001: Un solo componente de generación

- **Context** — El servicio recibe el título, arma la petición, interpreta la respuesta y produce la historia. La lógica es pequeña y las tres partes cambian juntas cuando se ajusta el formato (FR2, FR3, FR4). Se partió de la pregunta DD Q1.
- **Decision** — Un solo componente, `StoryGenerator`, reúne el armado de la petición, la interpretación de la respuesta y el armado del Markdown. Lo decidió la persona en DD Q1 (opción recomendada).
- **Consequences** — Positivas: menos piezas y menos interfaces que mantener con un equipo de perfil Python y un plazo corto (`feasibility-assessment.md`); un solo lugar para probar las reglas de formato. Negativas: el componente puede crecer si el formato se complica; habría que dividirlo después. Seguridad y cumplimiento: el componente trata el título como dato no confiable (FR2.5) y no registra el contenido (NFR4).
- **Alternatives Rejected** — Varios componentes (petición, interpretación, formato): más separación, pero más interfaces para una lógica pequeña que cambia en conjunto; es fácil de pasar a esa forma más adelante, así que no compensa hoy.

## ADR-002: Acceso al modelo en un componente aparte

- **Context** — Se evaluarán Amazon Titan y Claude Sonnet y se decidirá después cuál usar (FR7.1; `feasibility-assessment.md`). El servicio del modelo es una dependencia externa que puede fallar o tardar (FR5.2).
- **Decision** — `ModelGateway` aísla el acceso a Amazon Bedrock y permite cambiar el modelo sin tocar `StoryGenerator`. Lo decidió la persona en DD Q2 (opción recomendada).
- **Consequences** — Positivas: se puede cambiar o evaluar el modelo con un cambio de configuración; las pruebas de `StoryGenerator` usan un modelo simulado (TDD, `team-practices.md`). Negativas: una pieza más y una interfaz más. Seguridad y cumplimiento: las credenciales del modelo no están en el código (NFR5) y la región queda fija en us-east-1 (restricción de `requirements.md`).
- **Alternatives Rejected** — Acceso al modelo dentro de `StoryGenerator`: menos piezas, pero cambiar de modelo exigiría tocar la lógica de generación y complica las pruebas.

## ADR-003: Instrucciones al modelo (prompt) en configuración

- **Context** — El script actual lleva el prompt en el código y pide 3 a 5 criterios; el nuevo debe pedir 2 a 3 en Gherkin en español (`business-overview.md`, `code-structure.md`; FR2.3, FR3.1). La calidad del Gherkin depende del texto de las instrucciones y de cada modelo (NFR2).
- **Decision** — El prompt vive en un archivo de configuración y se lee desde `StoryGenerator`; no está escrito dentro del código. Lo decidió la persona en DD Q3.
- **Consequences** — Positivas: se pueden afinar las instrucciones al comparar modelos sin cambiar la lógica. Negativas: la configuración se versiona y se prueba aparte; un cambio de prompt puede degradar el resultado sin que falle una prueba de código. Seguridad y cumplimiento: la configuración no contiene secretos y un cambio de prompt pasa por revisión como el resto del código (`team-practices.md`).
- **Alternatives Rejected** — Prompt dentro del código: más simple y versionado junto con la lógica, pero cada ajuste de instrucciones obliga a cambiar y desplegar código.

## ADR-004: El script actual queda intacto y el código nuevo va aparte

- **Context** — El agente actual (script en Python que genera historias desde un Excel) se mantiene en uso hasta que el MVP sea aceptado (`scope-document.md`; `business-overview.md`). Hay un solo módulo con 117 líneas, sin pruebas (`code-structure.md`).
- **Decision** — El script actual no se modifica. El prompt y el formato de salida se reutilizan copiándolos al código nuevo, que va en una carpeta aparte del mismo repositorio. Lo decidió la persona en DD Q4.
- **Consequences** — Positivas: ningún riesgo para el agente en uso; el código nuevo puede cumplir las prácticas nuevas (TDD, linters, nombres en inglés) sin refactorizar el script. Negativas: hay un texto de prompt duplicado hasta que se retire el script. Seguridad y cumplimiento: se mantiene la separación de credenciales; el script sigue con su archivo `.env` local y el código nuevo usa permisos de la nube (NFR5).
- **Alternatives Rejected** — Compartir la lógica con el script actual: evita duplicar, pero obliga a refactorizar un script en uso sin pruebas y a cambiar de proveedor del modelo en un código que se va a retirar.

## ADR-005: El servicio arma el Markdown final

- **Context** — La interfaz muestra la vista previa y el Markdown de la misma historia (FR4.2) y copia el Markdown (FR4.3). El resultado debe tener un formato uniforme (problema de `intent-statement.md`).
- **Decision** — `StoryGenerator` devuelve el Markdown ya armado y `WebApp` solo lo muestra y lo formatea para la vista previa. Lo decidió la persona en DD Q5.
- **Consequences** — Positivas: el formato uniforme se garantiza en un solo lugar y se prueba allí; la interfaz no tiene reglas de formato. Negativas: la vista previa se obtiene interpretando el Markdown en la interfaz; si en el futuro hay otros clientes que necesiten los campos por separado, habrá que ampliar la respuesta. Seguridad y cumplimiento: el contenido del título que tenga caracteres de Markdown no debe romper el formato ni ejecutarse como contenido activo (FR4.4); se sanea al mostrar la vista previa.
- **Alternatives Rejected** — Que la interfaz arme el Markdown a partir de datos estructurados: separa mejor los datos de la presentación, pero duplicaría la lógica de formato en la interfaz.

## ADR-006: La sesión se verifica en el servicio, no solo en la interfaz

- **Context** — Sin sesión iniciada no se pueden generar historias (FR6.1, US6.1) y cada llamada al modelo tiene costo (restricción de costo mínimo, `requirements.md`). Esta decisión la propone el análisis para cumplir FR6.1; la persona no la respondió.
- **Decision** — `AccessControl` verifica la sesión en el servicio antes de que `StoryGenerator` genere, además del flujo de inicio de sesión en `WebApp`.
- **Consequences** — Positivas: nadie puede generar historias llamando al servicio sin pasar por la interfaz. Negativas: cada solicitud tiene una verificación adicional. Seguridad y cumplimiento: la regla de qué cuentas de Gmail u Outlook pueden entrar sigue abierta; mientras no se defina, cualquier cuenta válida podría generar costo (`raid-log.md`, riesgo RK5).
- **Alternatives Rejected** — Verificar solo en la interfaz: más simple, pero la interfaz se puede saltar y deja el modelo abierto a cualquiera que conozca la dirección del servicio.

## Assumptions & Open Questions

- ADR-006 es una propuesta del análisis, no una respuesta de la persona; se confirma o cambia en el gate.
- Abierto: regla de quién puede iniciar sesión (afecta ADR-006).
- Abierto: criterio para elegir entre Amazon Titan y Claude Sonnet (afecta ADR-002 y ADR-003).
