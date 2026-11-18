# Scalability Design — u1-walking-skeleton

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. Respuestas: `nfr-design-questions.md` (ND Qn).

## Arquitectura de escalado

El servicio no guarda estado entre solicitudes (`entities.md`), así que cada solicitud se atiende de forma independiente y varias pueden correr a la vez sin coordinación. Esa es la base para atender las solicitudes simultáneas del MVP (NFR3.1).

## Capacidad y concurrencia (NFR3.1)

- **Capacidad objetivo:** 5 solicitudes simultáneas sin errores atribuibles al servicio; "sin errores atribuibles al servicio" significa que ninguna respuesta tiene código MODEL_FAILURE, INVALID_MODEL_RESPONSE ni GENERATION_TIMEOUT por causa del propio servicio (los fallos del modelo se cuentan aparte).
- **Tope de concurrencia:** el servicio limita su concurrencia a un máximo de 5 ejecuciones simultáneas. Esto acota también el costo del modelo.
- **Más de 5 simultáneas:** las solicitudes que no caben se rechazan con RATE_LIMITED (HTTP 429, `retryable` verdadero), según ND Q2; no se encolan.

## Límite de tasa global (NFR3.2, ND Q1)

Por la decisión ND Q1, el límite de 20 solicitudes por persona por día no se aplica en el esqueleto: se difiere hasta que exista el control de acceso, que da una identidad por persona (`u4-access-control`). Mientras tanto, el esqueleto aplica un límite de tasa global en la pasarela HTTP, sin guardar datos propios en el servicio: una propuesta inicial de 5 solicitudes por segundo en ráfaga y 1 de forma sostenida, a confirmar en `u6-infrastructure`. Un rechazo por límite devuelve el código RATE_LIMITED.

## Desviación deliberada de NFR3.2 (registrada)

La respuesta confirmada en NR Q3/Q4 fijaba un límite de 20 solicitudes por persona por día. ND Q1 (respuesta B, `fd6adc30`) lo difiere: el esqueleto no lo cumple, y esto es una **desviación deliberada y rastreable**, no un cumplimiento.

- **Por qué:** un contador diario por persona exige estado y una identidad real; el esqueleto no tiene ninguno (NFR4.1 y verificador simulado).
- **Obligación traspasada:** `u4-access-control` debe entregar la identidad por persona y el límite de 20 por día, con un criterio de prueba propio. Debe anotarse en el plan de esa unidad antes de su diseño funcional.
- **Riesgo aceptado mientras tanto:** un solo origen puede agotar la capacidad global (límite de tasa y tope de 5); con 5 personas conocidas y uso ocasional se acepta durante el MVP.
- **NFR3.3:** se mide el total de solicitudes; la dimensión por persona llega con `u4-access-control`.

## Mecanismos y rechazos previos al código (NFR3.1)

Hay dos rechazos que ocurren **antes** de que corra el código del servicio:

1. El límite de tasa de la pasarela HTTP (propuesta: límite de uso del propio servicio de AWS).
2. El tope de 5 ejecuciones simultáneas (propuesta: concurrencia reservada de la función, que hace que la plataforma rechace el exceso).

Consecuencias de diseño: estos rechazos no ejecutan código propio, así que **no** generan el `requestId` del servicio ni incrementan `requests_total` / `errors_total` del servicio. La pasarela devuelve una respuesta fija con la forma del error de C1 (`code` RATE_LIMITED, `message`, `retryable` verdadero) y sin `requestId`; se vigilan con las métricas de la propia pasarela y de la plataforma. Las pruebas de aceptación de NFR3.1 verifican la forma de esa respuesta en el entorno desplegado de `u6-infrastructure`.

## Cambio de contrato requerido: RATE_LIMITED

El código RATE_LIMITED (HTTP 429, `retryable` verdadero) no existe aún en C1 (`contract-summary.md`) ni en la tabla W3 de `functional-spec.md`. Es un cambio aditivo de contrato. Queda registrado como requisito a cumplir: se añade a C1 y a W3 al inicio de Code Generation de esta unidad (pruebas primero, TDD), y `u5-web-app` lo trata como un error reintentable más. Hasta entonces el contrato publicado no lo incluye.

## Medición del uso (NFR3.3)

Cada solicitud incrementa un contador de solicitudes (ver `observability-design.md`), que sirve para vigilar el uso frente al límite futuro por persona.

## Umbrales de capacidad

| Umbral | Valor | Acción |
|--------|-------|--------|
| Rechazos por límite de tasa | Más de 0 en un día de uso normal | Revisar el límite; el MVP no prevé más de 5 personas |
| Uso por encima de 5 personas | Cualquiera | Rediseñar la capacidad (fuera del MVP) |

## Assumptions & Open Questions

- Supuesto: los valores de tasa (5 por segundo en ráfaga, 1 sostenida) son una propuesta de esta etapa, no una respuesta de la persona.
- Abierto: los límites de concurrencia de los servicios de AWS involucrados, que se confirman en `u6-infrastructure`.
