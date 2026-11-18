# Tech Stack Decisions — u3-story-generator

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa.

Cada decisión indica si está confirmada o si es una propuesta de esta etapa.

## Decisiones confirmadas

| Tema | Decisión | Fuente |
|------|----------|--------|
| Lenguaje y entorno | Python dentro de la función del servicio (u1), con pytest y cobertura | `team-practices.md`; decisiones de u1 |
| Estilo | Black y Ruff; nombres en inglés | `practices-discovery-questions.md` Q7 y Q8 |
| Respuesta del modelo | JSON validado por el servicio, que arma el Markdown (ADR-005) | `functional-design-questions.md` Q3 |
| Estructura del Markdown | Un único bloque de código con el Gherkin completo | `functional-design-questions.md` Q4 |
| Contexto | Hasta 500 caracteres, pedido una sola vez | `functional-design-questions.md` Q2 |
| Acceso al modelo | A través de la interfaz `ModelClient` de u2; u3 no habla con Bedrock | `unit-of-work.md` |

## Requisitos de mantenibilidad y pruebas (NFR8)

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR8.1 | El código de u3 se escribe con TDD: cada prueba antes del código, en rojo y luego lo mínimo para que pase | El plan de Code Generation registra la salida en rojo de cada ciclo | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.2 | u3 aporta el mínimo de 80 % de cobertura de líneas; las pruebas corren en CI antes de integrar y el piso se mide en la suite completa; la cobertura de los archivos de u3 se informa aparte | Build and Test ejecuta la suite con el umbral de 80 % | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.3 | El código de u3 pasa Black y Ruff sin errores | Black y Ruff en CI | `team-practices.md` |
| NFR8.4 | Los nombres de funciones y variables del código nuevo están en inglés | Revisión de código y Ruff donde aplique | `team-practices.md` |
| NFR2.1 | El conjunto de títulos de prueba de NFR2 incluye títulos válidos de distintas áreas, uno corto ("Login"), uno largo de 200 caracteres, uno con caracteres de Markdown y uno que intenta dirigir al modelo; se registra a mano cuántos producen un Gherkin válido a la primera, con una meta de 80 % | La lista de títulos y el registro de la revisión manual existen en `docs/` y la persona los revisa | `requirements.md` NFR2; AC3.1.2 |

Las pruebas cubren como mínimo el camino feliz y dos casos de error o de borde por componente. Una prueba no puede ser trivial.

## Propuestas de esta etapa (a confirmar)

| Tema | Propuesta | Razón |
|------|-----------|-------|
| Estructura del código | Módulos separados para validación de entrada, armado de la petición, validación de la respuesta y armado del Markdown, dentro de `story_service` | Cada regla de `rules.md` se prueba de forma aislada |
| Lectura del JSON | La biblioteca estándar de Python | Sin dependencias nuevas |
| Umbral de contexto (ajuste a la respuesta Q1, **pendiente de confirmar con la persona**) | Menos de 2 palabras o menos de 12 caracteres, en lugar de las 3 palabras que eligió, porque 3 palabras pediría contexto para "Recuperar contraseña" | Coherencia con el ejemplo de AC2.1.1 |
| Revisión manual de NFR2 | La revisa la persona; "Gherkin válido" significa que usa la línea `# language: es`, Característica, Escenario, Dado, Cuando y Entonces en ese orden y es legible sin corrección | Define el criterio de la meta de 80 % |
| Conjunto de títulos de NFR2 | Un archivo versionado en `docs/` con unos 10 títulos inventados, que la persona aprueba como los de u2 | Mismo método y sin datos reales |

## Assumptions & Open Questions

- Abierto: el conjunto de títulos de NFR2 y quién hace la revisión manual (pregunta abierta de `requirements.md`).
- Abierto: confirmar con la persona el umbral de 2 palabras.
