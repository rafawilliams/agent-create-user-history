# Tech Stack Decisions — u4-access-control

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa.

Cada decisión indica si está confirmada o si es una propuesta de esta etapa.

## Decisiones confirmadas

| Tema | Decisión | Fuente |
|------|----------|--------|
| Identidad | Amazon Cognito con Google y Microsoft como proveedores; el servicio verifica el token | `functional-design-questions.md` Q1 |
| Cuentas | Lista de correos permitidos en la configuración | `functional-design-questions.md` Q2 |
| Sesión | 8 horas | `functional-design-questions.md` Q3 |
| Lenguaje y pruebas | Python dentro de la función del servicio (u1), con pytest y cobertura | `team-practices.md`; decisiones de u1 |
| Estilo | Black y Ruff; nombres en inglés | `practices-discovery-questions.md` Q7 y Q8 |

## Requisitos de mantenibilidad y pruebas (NFR8)

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR8.1 | El código de u4 se escribe con TDD: cada prueba antes del código, en rojo y luego lo mínimo para que pase | El plan de Code Generation registra la salida en rojo de cada ciclo | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.2 | u4 aporta el mínimo de 80 % de cobertura de líneas; las pruebas corren en CI antes de integrar y el piso se mide en la suite completa; la cobertura de los archivos de u4 se informa aparte | Build and Test ejecuta la suite con el umbral de 80 % | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.3 | El código de u4 pasa Black y Ruff sin errores | Black y Ruff en CI | `team-practices.md` |
| NFR8.4 | Los nombres de funciones y variables del código nuevo están en inglés | Revisión de código y Ruff donde aplique | `team-practices.md` |

Las pruebas cubren como mínimo el camino feliz y dos casos de error o de borde por componente. Los tokens de prueba se firman con un par de claves RSA generado dentro de las pruebas: nunca se llama a Cognito ni a AWS desde las pruebas automáticas.

## Propuestas de esta etapa (a confirmar)

| Tema | Propuesta | Razón |
|------|-----------|-------|
| Verificación de tokens | Una biblioteca de JWT mantenida para Python (con soporte de RS256 y claves JWK) en lugar de escribir la verificación a mano | Evita errores de criptografía propia; se fija la versión en `backend/requirements.txt` |
| Obtención de claves | La biblioteca estándar de Python (solicitud HTTPS al punto de claves públicas del grupo) con la copia en memoria | Sin dependencias adicionales |
| Configuración | Variables de entorno: región, identificador del grupo, identificador del cliente de la aplicación y la lista de correos permitidos separada por comas | Sin secretos y editable por despliegue |
| Estructura del código | Un módulo para la verificación de tokens, otro para la lista de cuentas y otro para las claves, dentro de `story_service` | Cada regla de `rules.md` se prueba de forma aislada |

## Assumptions & Open Questions

- Abierto: la versión fijada de la biblioteca de JWT se decide en Code Generation y se anota en el resumen.
- Abierto: confirmar con la persona la lista de correos permitidos (cuáles son).
