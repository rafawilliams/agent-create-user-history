# Tech Stack Decisions — u1-walking-skeleton

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (NR Qn).

Cada decisión indica si está confirmada por la persona o si es una propuesta de esta etapa.

## Decisiones confirmadas

| Tema | Decisión | Fuente |
|------|----------|--------|
| Nube y región | AWS, región us-east-1 | `feasibility-questions.md` Q2 |
| Modelo | Amazon Bedrock; el esqueleto se prueba con Claude Sonnet; la elección definitiva entre Amazon Titan y Claude Sonnet se hace en `u2-model-gateway` | `functional-design-questions.md` Q1; `feasibility-questions.md` Q9 |
| Interfaz | React con MUI (Material Design), tema claro y oscuro | `refined-mockups-questions.md` Q1 a Q3 |
| Servicio | Código del servicio en Python, detrás de un API Gateway y en una función Lambda | Pedido original; `team-practices.md`; perfil del equipo (`feasibility-questions.md` Q6) |
| Infraestructura | Terraform; despliegue automático a un único entorno al integrar en `main` | `practices-discovery-questions.md` Q3 y Q4 |
| Formato y análisis estático | Black y Ruff para Python; Prettier y ESLint para JavaScript y TypeScript; el linter en CI bloquea la integración | `practices-discovery-questions.md` Q7 |
| Pruebas | TDD, con un mínimo de 80 % de cobertura de líneas ejecutado en CI antes de integrar | `practices-discovery-questions.md` Q5 y Q6 |
| Idioma del código | Nombres de funciones y variables en inglés | `practices-discovery-questions.md` Q8 |

## Requisitos de mantenibilidad y pruebas (NFR8)

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR8.1 | El código del esqueleto se escribe con TDD: cada prueba se escribe antes del código que la satisface, se ejecuta en rojo y luego se implementa lo mínimo para que pase | `team-practices.md` (Testing Posture); `requirements.md` NFR8 |
| NFR8.2 | El esqueleto alcanza un mínimo de 80 % de cobertura de líneas, y las pruebas se ejecutan en CI antes de integrar | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.3 | El código del esqueleto pasa Black y Ruff (Python) y Prettier y ESLint (JavaScript y TypeScript) sin errores | `team-practices.md` (Code Style); `requirements.md` NFR8 |
| NFR8.4 | Los nombres de funciones y variables del código nuevo están en inglés | `team-practices.md` (Code Style) |

Las pruebas cubren como mínimo el camino feliz y dos casos de error o de borde por cada componente (guía de Construction), por ejemplo: título vacío, fallo del modelo y respuesta fuera de contrato (`functional-spec.md`, W2 a W4). Una prueba no puede ser trivial (por ejemplo, una afirmación siempre verdadera).

## Propuestas de esta etapa (a confirmar)

| Tema | Propuesta | Razón |
|------|-----------|-------|
| Pruebas del servicio | pytest con medición de cobertura | Es el estándar de Python y `team-practices.md` lo dejó como sugerencia pendiente |
| Pruebas de la interfaz | Vitest con React Testing Library | Encaja con una interfaz React construida con un empaquetador moderno; `team-practices.md` dejó la herramienta pendiente |
| Acceso a Bedrock desde Python | El SDK oficial de AWS para Python | Es la forma estándar de llamar a Bedrock; el código actual usa el SDK de Anthropic, que no aplica aquí |
| Versión de Python y de Node | Una versión con soporte vigente de cada una, fijada en el repositorio | El código actual no fija versiones (`code-quality-assessment.md`) |
| Fijado de dependencias | Versiones fijadas en los archivos de dependencias del código nuevo | `team-practices.md` lo dejó pendiente |

## Lo que no cambia

El script actual en Python que genera historias desde un Excel no se modifica (ADR-004): conserva su propio `requirements.txt` y su uso del SDK de Anthropic hasta que se acepte el MVP.

## Assumptions & Open Questions

- Abierto: confirmar o cambiar las propuestas de la segunda tabla antes de Code Generation.
- Abierto: herramienta de CI/CD, que sigue pendiente (`team-practices.md`).
- Supuesto: la función Lambda es el modo de ejecución del servicio por el pedido original; no se evaluó otra alternativa en esta etapa.
