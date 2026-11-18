# Performance Design — u4-access-control

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

## Camino rápido (NFR1.1, NFR1.4)

Con las claves en memoria, la verificación es trabajo local sin red: decodificar el token, una verificación de firma RSA, comparar los claims y buscar el correo en una lista corta. Sin esperas, sin reintentos y sin llamadas de red (NFR1.4). El objetivo de diseño es menos de 20 milisegundos; las pruebas usan la mediana de 20 repeticiones tras un calentamiento, repiten hasta 3 veces ante un falso fallo en un ejecutor lento y tratan los 20 ms como un objetivo de diseño.

## Camino lento: descarga de claves (NFR1.2, NFR1.3)

La descarga solo ocurre con la copia vacía, vencida (más de 1 hora) o sin la clave pedida (rotación o `kid` desconocido). Su coste está acotado:

- Tiempo de espera de 3 segundos, sin reintentos propios, y tope de 64 kilobytes.
- Una descarga a la vez y una por minuto en total, exitosa o fallida: las demás solicitudes no esperan: fallan cerrado de inmediato con `keys_unavailable`.
- El peor caso para una solicitud es una sola espera de 3 segundos dentro del plazo de 55 segundos del servicio; las siguientes solicitudes con un `kid` desconocido fallan de inmediato durante el minuto.

## Arranque en frío

La primera verificación tras un arranque en frío descarga las claves (hasta 3 segundos). Es un coste aceptado en el MVP; no se precalienta la copia.

## Assumptions & Open Questions

- Supuesto: los 20 ms y los 3 s son holgados frente al tiempo del modelo y solo detectan una regresión grave.
- Abierto: el tiempo real contra Cognito se mide en la prueba de punta a punta de `u6-infrastructure`.
