# Reliability Requirements — u1-walking-skeleton

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (NR Qn).

## Objetivo de disponibilidad

**Sin objetivo formal en el MVP** (NR Q1): el servicio se ofrece al mejor esfuerzo. Esta es una decisión consciente de la persona para un MVP de uso ocasional y de hasta 5 personas. Queda sin SLO cuantificado; la guía de operación pide cuantificar los SLO con porcentajes y ventana, así que esta decisión debe revisarse antes de ofrecer el servicio a más personas.

No hay un requisito de Inception sobre disponibilidad al que colgar un identificador; por eso este objetivo no lleva un ID NFR y se registra aquí como decisión.

## Tolerancia a fallos

| ID | Requisito | Fuente |
|----|-----------|--------|
| NFR1.5 | Un fallo del modelo se informa con un código estable y una indicación de si se puede reintentar; nunca como un resultado vacío ni en silencio (`rules.md` BR1.4). La tabla de correspondencia entre el tipo de error del modelo y el código está en `functional-spec.md` (W3) | `rules.md` BR1.4; `phases/construction.md` (Error Handling) |
| NFR1.6 | El reintento automático es único y solo ante un fallo pasajero con tiempo restante | `contract-summary.md` (CD Q6) |
| NFR4.1 | Un fallo no deja datos a medio escribir porque el servicio no guarda nada | `requirements.md` NFR4 |

## Degradación

- Si el modelo no está disponible, el servicio devuelve un error y la pantalla lo muestra como texto; no hay modo degradado ni respuesta de reserva (el esqueleto no tiene otro modelo de respaldo).
- Si el verificador de sesión real no está configurado en un entorno desplegado, se rechaza toda solicitud (falla cerrado; NFR5.2).

## Copias de seguridad y recuperación

No hay datos que respaldar ni recuperar: el servicio no guarda estado (`requirements.md` NFR4). La recuperación ante una falla es volver a desplegar el servicio y reintentar la solicitud.

## Assumptions & Open Questions

- Abierto: si se agrega un SLO cuantificado antes de ofrecer el servicio a más de 5 personas.
- Abierto: los pasos de retroceso del despliegue (`team-practices.md`, Deployment) se definen en `u6-infrastructure`.
