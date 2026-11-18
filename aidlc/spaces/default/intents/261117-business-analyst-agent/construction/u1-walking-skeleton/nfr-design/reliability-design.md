# Reliability Design — u1-walking-skeleton

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. Respuestas: `nfr-design-questions.md` (ND Qn).

## Objetivo de disponibilidad

Sin objetivo formal en el MVP (`reliability-requirements.md`, NR Q1). El diseño no incluye alta disponibilidad entre zonas ni conmutación por fallo: el servicio es una función sin estado que la plataforma ejecuta donde haya capacidad, y recuperar es volver a desplegar y reintentar.

Condición concreta para revisar la falta de SLO: antes de ofrecer el servicio a más de 5 personas, o si el MVP se mantiene en uso más de un mes, se define un SLO cuantificado con porcentaje y ventana (la guía de operación lo exige).

## Patrones de resiliencia

| Patrón | Diseño | Requisito |
|--------|--------|-----------|
| Tiempo de espera en cada llamada externa | El modelo se corta a 50 s; el servicio, a 55 s | NFR1.1, NFR1.2 |
| Reintento acotado | Un solo reintento ante `transient` o `unavailable`, solo si queda tiempo; sin reintento tras `timeout` | NFR1.6 |
| Falla cerrado | Sin verificador de sesión real en un entorno desplegado, se rechaza toda solicitud | NFR5.2 |
| Errores informados, nunca silenciosos | Cada `ModelError` se traduce al código de C1 con `retryable`, según la tabla de `functional-spec.md` | NFR1.5 |

## Interruptor de circuito

No se diseña un interruptor de circuito en el MVP: con hasta 5 personas y uso ocasional, un fallo prolongado del modelo se descubre por las métricas y por las propias personas. Un fallo del modelo no se propaga: cada solicitud falla de forma independiente con un error claro.

## Degradación

Sin respuesta de reserva ni modelo de respaldo: si el modelo falla, la interfaz muestra el error del servicio como texto. No hay modo de solo lectura que ofrecer, porque el servicio no tiene datos que leer.

## Salud y verificación

El servicio no expone un punto de salud propio en el esqueleto. La salud se vigila con las métricas de solicitudes y de errores por código (`observability-design.md`). Una prueba de humo posterior a cada despliegue la define `u6-infrastructure`.

## Respaldo y recuperación

No hay datos que respaldar. Recuperarse es volver a desplegar el servicio desde `main`; los pasos de retroceso los define `u6-infrastructure`.

## Assumptions & Open Questions

- Abierto: fecha o criterio para definir el SLO (ver arriba).
- Abierto: los pasos de retroceso del despliegue.
