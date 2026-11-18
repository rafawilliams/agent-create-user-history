# Performance Requirements — u4-access-control

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa: los valores salen de decisiones ya confirmadas (plazos de C1, 5 personas) y de las reglas de esta unidad.

u4 verifica la sesión en cada solicitud antes de generar; su coste se suma al plazo de 55 segundos del servicio.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR1.1 | La verificación de una sesión (firma, emisor, audiencia, tipo, vigencia y lista de correos) con las claves ya en memoria tarda menos de 20 milisegundos | Una prueba mide la verificación con un token firmado de prueba y las claves en memoria: mediana de 20 repeticiones tras un calentamiento menor de 20 ms | `requirements.md` NFR1; BR4.2 |
| NFR1.2 | La obtención de las claves públicas (solo cuando la copia está vacía, vencida o falta la clave) tiene un tiempo de espera de 3 segundos y no consume más de 3 s del plazo de 55 s del servicio; con un fallo, la verificación falla cerrado sin reintentos propios | Una prueba con un servidor de claves simulado que no responde comprueba que la verificación termina en 3 s o menos con `keys_unavailable` | `rules.md` BR4.7, BR4.5 |
| NFR1.3 | La renovación de la copia de claves se hace como máximo una vez por minuto, exitosa o fallida (un intento fallido o con tiempo agotado cuenta para el límite), y como máximo una a la vez; las demás solicitudes no esperan: reutilizan el resultado de la descarga en curso o fallan cerrado con `keys_unavailable`, de modo que un flujo de tokens inválidos no consume el plazo de 55 s | Pruebas con 100 tokens de un `kid` desconocido en un minuto (una sola renovación) y con el servidor de claves caído (una sola descarga de 3 s, las demás fallan de inmediato) | `rules.md` BR4.7 |
| NFR1.4 | u4 no añade esperas ni reintentos propios: devuelve el resultado de la verificación de inmediato | Una prueba comprueba que no hay más de una llamada de red por verificación y ninguna cuando la copia sirve | `requirements.md` NFR1 |

## Assumptions & Open Questions

- Supuesto: el uso es ocasional de hasta 5 personas; la obtención de claves ocurre en pocas ocasiones (arranque en frío o rotación).
- Abierto: el tiempo real contra Cognito se mide en la prueba de punta a punta de `u6-infrastructure`.
