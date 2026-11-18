# Performance Requirements — u1-walking-skeleton

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (NR Qn).

Cada requisito hereda el ID de Inception y le agrega un subnúmero (NFR1.1, NFR1.2, ...).

| ID | Requisito | Medida | Fuente |
|----|-----------|--------|--------|
| NFR1.1 | El servicio devuelve la historia, o un error, en menos de 60 segundos desde que recibe la solicitud | Tiempo de extremo a extremo menor que 60 s; a los 60 s o más la solicitud es un fallo (GENERATION_TIMEOUT) | `requirements.md` NFR1; `contract-summary.md` (Tiempos y reintentos) |
| NFR1.2 | La llamada al modelo se corta a los 50 segundos | Corte del acceso al modelo a 50 s, de modo que el servicio responde con un error claro antes de los 60 s | `contract-summary.md` (CD Q5) |
| NFR1.3 | El esqueleto debe completar la demostración real (título de ejemplo a Markdown con el modelo real) en menos de 1 minuto | Una ejecución local contra el modelo real tarda menos de 60 s | `requirements.md` NFR1 (meta del MVP); `functional-spec.md` (cómo se comprueba) |
| NFR1.4 | La duración de cada generación se mide y se registra | Una métrica de duración por solicitud, sin el contenido del título ni de la historia | NR Q2 (métricas); `requirements.md` NFR4 |
| NFR1.5 | Un tiempo agotado se informa con el código GENERATION_TIMEOUT (HTTP 504) y `retryable` verdadero | La respuesta de error lleva ese código y esa indicación | `rules.md` BR1.4 |
| NFR1.6 | El servicio hace como máximo un reintento automático ante un fallo pasajero del modelo, y solo si queda tiempo dentro de los 60 segundos | A lo sumo un reintento; el segundo intento usa como corte el tiempo restante, no 50 s; no hay reintento tras un tiempo de espera agotado | `contract-summary.md` (CD Q6) |

## Notas

- El tiempo de cada llamada al modelo depende del modelo y de la región (us-east-1); el corte de 50 s protege el máximo de 60 s.
- El límite de tiempo del servicio HTTP en AWS frente a los 60 segundos sigue sin confirmarse; se verifica al construir la infraestructura (`external-dependency-map.md`, E4). Si el límite fuera menor, hay que cambiar NFR1.1 y el contrato C1.
- Un valor concreto de "responder antes de los 60 segundos" para el servicio (por ejemplo, 55 s) se fija en NFR Design; aquí solo se exige que quede por debajo de los 60 s de la interfaz.

## Assumptions & Open Questions

- Supuesto: el esqueleto no tiene requisitos de rendimiento de la interfaz más allá de NFR1.3; los de la interfaz completa los fija la unidad `u5-web-app`.
- Abierto: valor de corte del servicio entre 50 y 60 segundos.
- Abierto: límite de tiempo del servicio HTTP de AWS (E4).
