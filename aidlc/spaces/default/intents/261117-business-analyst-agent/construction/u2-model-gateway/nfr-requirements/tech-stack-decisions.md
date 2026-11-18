# Tech Stack Decisions — u2-model-gateway

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa.

Cada decisión indica si está confirmada o si es una propuesta de esta etapa.

## Decisiones confirmadas

| Tema | Decisión | Fuente |
|------|----------|--------|
| Nube, región y modelo | AWS, us-east-1, Amazon Bedrock; Claude Sonnet y Amazon Titan como modelos candidatos | `feasibility-questions.md` Q2 y Q9 |
| Lenguaje y pruebas | Python con pytest y cobertura; TDD con un mínimo de 80 % de cobertura de líneas en CI | `team-practices.md`; decisiones de `u1-walking-skeleton` |
| Estilo | Black y Ruff; nombres en inglés | `practices-discovery-questions.md` Q7 y Q8 |
| Acceso a Bedrock | El SDK oficial de AWS para Python con la API de conversación de Bedrock | `u1-walking-skeleton` (verificado de punta a punta con Claude Sonnet; con Amazon Titan está por verificar en la evaluación) |
| Criterio de decisión de la evaluación | Cumplimiento automático del formato | `functional-design-questions.md` Q1 |
| Registro de la evaluación | `docs/evaluacion-modelos.md` versionado en el proyecto | `functional-design-questions.md` Q3 |

## Requisitos de rendimiento y calidad del modelo

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR1.1 | Una llamada al modelo no espera más que el tiempo de espera que pide el servicio, incluidos valores con fracciones de segundo; pasado ese tiempo devuelve el error de tiempo agotado | Una prueba con un modelo simulado que tarda más de lo pedido comprueba que el acceso devuelve `timeout` dentro de ese tiempo, con un valor fraccionario | `requirements.md` NFR1; `rules.md` BR2.6 |
| NFR1.2 | El tiempo de espera por defecto de cada modelo es de 50 segundos (el corte del modelo que fijó el contrato C1); cada modelo puede tener su propio valor en la configuración, y ambos modelos usan 50 segundos hasta que una evaluación muestre otra cosa | Una prueba comprueba que, sin configuración, el tiempo de espera usado es 50 s para ambos perfiles; otra, que un valor de configuración lo cambia | `contract-summary.md` (C1 y la pregunta abierta de C4); `requirements.md` NFR1 |
| NFR1.4 | u2 no reintenta por su cuenta: una llamada es un solo intento, el cliente de AWS se configura con cero reintentos propios y el único reintento automático lo decide el servicio con el plazo restante (NFR1 de u1). El tiempo total de una llamada no supera el tiempo de espera pedido más una tolerancia de 1 segundo | Una prueba con un doble del cliente de AWS comprueba que ante un fallo pasajero se hace una sola llamada y que la configuración del cliente tiene cero reintentos; otra, que con un tiempo pedido de 2 s la llamada termina en 3 s o menos | `contract-summary.md` (C1: un solo reintento, del servicio); `requirements.md` NFR1 |
| NFR1.3 | La evaluación registra el tiempo de cada llamada a cada modelo, para decidir con evidencia si un modelo responde dentro del presupuesto de 50 segundos | El archivo de evaluación incluye el tiempo por modelo y título | `requirements.md` NFR1; `rules.md` BR2.8 |
| NFR2.1 | La evaluación mide, por modelo, cuántos de los 5 títulos producen una historia con el formato esperado a la primera; es el dato que alimenta la decisión y la meta de 80 % de `requirements.md` NFR2, que se verifica con el servicio completo en `u3-story-generator` | El archivo de evaluación incluye la puntuación de cada modelo | `requirements.md` NFR2; `rules.md` BR2.8 |

## Requisitos de mantenibilidad y pruebas (NFR8)

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR8.1 | El código de u2 se escribe con TDD: cada prueba antes del código, en rojo y luego lo mínimo para que pase | El plan de Code Generation registra la salida en rojo de cada ciclo antes de implementar | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.2 | u2 aporta el mínimo de 80 % de cobertura de líneas, y las pruebas se ejecutan en CI antes de integrar; el piso se mide en la suite completa del proyecto y además se informa la cobertura de los archivos de u2 | Build and Test ejecuta la suite con el umbral de 80 %; la cobertura de los archivos de u2 se informa aparte | `team-practices.md`; `requirements.md` NFR8 |
| NFR8.3 | El código de u2 pasa Black y Ruff sin errores | Black y Ruff en CI sin errores | `team-practices.md` (Code Style) |
| NFR8.4 | Los nombres de funciones y variables del código nuevo están en inglés | Revisión de código y Ruff donde aplique | `team-practices.md` (Code Style) |

Las pruebas cubren como mínimo el camino feliz y dos casos de error o de borde por componente: por ejemplo, cada tipo de error de Bedrock traducido, un identificador no soportado y un modelo bloqueado en la evaluación. Una prueba no puede ser trivial.

## Propuestas de esta etapa (a confirmar)

| Tema | Propuesta | Razón |
|------|-----------|-------|
| Identificador de Amazon Titan | El perfil de Titan para texto que figure como disponible en la cuenta; se fija en Code Generation al ver la lista de modelos de la cuenta | La cuenta ya mostró diferencias de acceso entre modelos (Sonnet 5.5 no disponible, Sonnet 4.5 heredado) |
| Dónde vive el comando de evaluación | Un módulo del propio paquete del servicio (`story_service`) que se ejecuta desde la línea de comandos, junto a `local_run` | Reutiliza el acceso al modelo y las instrucciones por defecto, y se prueba con el mismo ejecutor |
| Motivo de error de lista cerrada | Un tipo enumerado `reason` con los siete valores de `rules.md` BR2.3 | Permite distinguir bloqueo de parámetro rechazado sin copiar texto de AWS |

## Lo que no cambia

El script actual que genera historias desde un Excel no se modifica (ADR-004).

## Assumptions & Open Questions

- Decidido en esta etapa: la pregunta abierta de C4 sobre el tiempo de espera por modelo se cierra con 50 segundos para ambos hasta tener evidencia de la evaluación (NFR1.2); se registra en `contract-summary.md` al inicio de Code Generation junto con los demás cambios de C4.
- Abierto: confirmar el identificador de Titan y su disponibilidad (propuesta).
- Supuesto: la API de conversación de Bedrock funciona igual para Titan y Claude Sonnet; si Titan no la admite en la cuenta, se registra como bloqueo (BR2.10) o como fallo, no se descarta.
