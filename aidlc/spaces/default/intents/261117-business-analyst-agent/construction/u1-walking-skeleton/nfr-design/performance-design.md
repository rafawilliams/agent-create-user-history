# Performance Design — u1-walking-skeleton

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. Respuestas: `nfr-design-questions.md` (ND Qn).

## Presupuesto de tiempo (NFR1.1, NFR1.2)

| Corte | Valor | Quién lo aplica | Fuente |
|-------|-------|-----------------|--------|
| Llamada al modelo | 50 segundos | El acceso al modelo, con un tiempo de espera propio | `contract-summary.md` (CD Q5) |
| Respuesta del servicio | 55 segundos como máximo | El servicio, con un plazo que corre desde que recibe la solicitud | ND Q3 |
| Espera de la interfaz | 60 segundos | La interfaz | `requirements.md` NFR1 |

Diseño: el servicio fija un plazo absoluto al recibir la solicitud (instante de inicio más 55 segundos, medido con un reloj monótono) y lo pasa a cada paso. El tiempo de espera de la llamada al modelo es el menor entre 50 segundos y el tiempo que queda hasta el plazo. Si el plazo se agota, el servicio responde GENERATION_TIMEOUT (HTTP 504, `retryable` verdadero) antes de que la interfaz corte a los 60 segundos.

## Reintento (NFR1.6)

El servicio reintenta como máximo una vez, solo ante un fallo pasajero del modelo (`transient` o `unavailable`) y solo si queda tiempo en el plazo. El segundo intento usa como tiempo de espera el tiempo restante, no 50 segundos. Con un tiempo de espera agotado (`timeout`) no se reintenta, porque ya no queda tiempo útil. Un reintento solo se justifica tras un fallo rápido.

## Medición (NFR1.3, NFR1.4)

Cada solicitud mide su duración de extremo a extremo y la emite como una métrica de duración (ver `observability-design.md`). El esqueleto demuestra NFR1.3 con una ejecución real contra el modelo y una medición manual del tiempo total.

## Reuso de conexiones y arranque

- El cliente del modelo se crea una vez por instancia del servicio y se reutiliza entre solicitudes, para no pagar el establecimiento de conexión en cada una.
- No se usa caché: el servicio no guarda títulos ni historias (NFR4.1), y cada título es distinto; no habría aciertos.
- El arranque en frío del servicio suma tiempo a la primera solicitud tras un periodo sin uso; cae dentro del plazo de 55 segundos y no se mitiga en el MVP.

## Código de error de tiempo (NFR1.5)

GENERATION_TIMEOUT con HTTP 504 y `retryable` verdadero, como define C1 y la tabla de `functional-spec.md` (W3).

## Assumptions & Open Questions

- Abierto: el límite de tiempo de integración de la pasarela HTTP de AWS suele rondar los 29-30 segundos y puede no permitir 55 s. Criterio de revisión: si `u6-infrastructure` no puede confirmar un tiempo de espera de al menos 55 s en la pasarela elegida, se rediseña el presupuesto (por ejemplo, otro punto de entrada que admita esperas largas) antes de aceptar el esqueleto; no se acorta en silencio el corte de 50 s del modelo.
- Supuesto: el reloj monótono del entorno de ejecución es suficientemente preciso para un plazo de segundos.
