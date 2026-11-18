## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-17T19:12:00Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > tabla de requisitos y Consideraciones de amenazas | No hay ningún requisito sobre cómo se obtienen las claves públicas. Solo `tech-stack-decisions.md` dice "solicitud HTTPS" como propuesta. Falta fijar que la URL de claves se deriva únicamente de la región y del identificador del grupo configurados, y que nunca se toma del `iss`, de `jku` ni de `x5u` del token. Falta exigir HTTPS con validación de certificado, sin redirecciones a otros hosts, y un tope al tamaño de la respuesta. Es la superficie más sensible de un verificador de Cognito y no tiene fila con criterio de prueba. | Añadir un requisito de seguridad con sus pruebas: la URL derivada de la configuración, HTTPS con certificado verificado, `iss`/`jku` del token ignorados para la descarga, redirecciones y tamaño acotados, y un JWKS mal formado que da `keys_unavailable`. Reflejarlo en la tabla de amenazas. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > NFR5.1, NFR5.2, NFR5.3, NFR5.4, NFR5.6; y traceability.json > cobertura de NFR5 | El NFR5 de inception es "Secretos". Aquí NFR5.1, 5.2, 5.3, 5.4 y 5.6 son requisitos de verificación de token y lista de cuentas, no de secretos. Solo NFR5.5 hereda ese tema. El paso 5 de la etapa pide que cada requisito detallado herede el ID de inception que le corresponde. `traceability.json` marca NFR5 como OK, pero la cobertura real de secretos es una sola fila. | Renumerar las filas de autenticación bajo el NFR de inception que corresponda, o registrar el hueco como requisito nuevo con su origen (FR6.1). Ajustar `traceability.json` para que el OK de NFR5 se apoye solo en filas de secretos. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/performance-requirements.md > NFR1.2, NFR1.3; scalability-requirements.md > NFR3.2 | El límite de una renovación por minuto y de una a la vez solo se prueba con renovaciones exitosas. No se dice si una renovación fallida o con tiempo agotado cuenta como intento, ni qué hacen las solicitudes que esperan el bloqueo mientras otra descarga tarda 3 s. Con Cognito caído, un flujo de tokens con `kid` desconocido puede provocar descargas de 3 s repetidas y consumir el plazo de 55 s. | Fijar que un intento fallido cuenta para el límite de 1 por minuto y que las demás solicitudes no esperan más allá de la descarga en curso (reutilizan su resultado o fallan cerrado). Añadir una prueba con el servidor de claves caído y 100 tokens de `kid` desconocido. | Resolved (reviewer) |
| R-04 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/reliability-requirements.md > NFR1.6; observability-requirements.md > NFR4.5, NFR4.7 | NFR1.6 registra el motivo `unknown`, que no está en la lista cerrada de `SessionInvalid.reason` (`functional-design/entities.md` línea 40) ni en NFR4.5. | Decidir si `unknown` se agrega al contrato C3 y a las listas cerradas, o usar un motivo existente. Alinear NFR1.6, NFR4.5 y `entities.md`. | Resolved (reviewer) |
| R-05 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > NFR4.4 y Assumptions & Open Questions | Que `ACCOUNT_NOT_ALLOWED` (403) tenga un mensaje distinto revela, a quien ya tiene un token válido del grupo, que la firma pasó y que la cuenta no está en la lista. Es aceptable y la pantalla la necesita, pero no se declara como riesgo aceptado, y el criterio solo compara cuerpos, no códigos. | Anotar la divulgación como riesgo aceptado y precisar que se comparan cuerpo y código HTTP (401 idéntico para todos los motivos de token). | Resolved (reviewer) |
| R-06 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > NFR5.3, NFR5.6 | NFR5.6 ("se compara sin distinguir entre solicitudes") es poco claro y sin criterio. No se dice si la lista se normaliza a minúsculas al cargarla. No se menciona la comparación en tiempo constante (riesgo bajo, pero no descartado). | Reescribir NFR5.6, fijar la normalización de la lista al cargar y anotar por qué no se exige tiempo constante. | Resolved (reviewer) |
| R-07 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > NFR5.2 | No hay criterio para un token sin `exp` o sin `iat`, ni para la caída a `iat` cuando falta `auth_time` (BR4.4). | Añadir casos de prueba para `exp` ausente, `iat` ausente y la caída a `iat` en el máximo de 8 horas. | Resolved (reviewer) |
| R-08 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/reliability-requirements.md > NFR1.8; scalability-requirements.md > NFR3.4; security-requirements.md > NFR5.5 | Sin criterio de prueba medible: NFR1.8 "No aplica respaldo", NFR3.4 "No aplica a u4", y NFR5.5 se apoya en una búsqueda de patrones que el propio documento deja a la CI de `u6-infrastructure`. | Marcar NFR1.8 y NFR3.4 como notas, y precisar qué verifica u4 por sí misma en NFR5.5. | Resolved (reviewer) |
| R-09 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/performance-requirements.md > NFR1.1; tech-stack-decisions.md > Propuestas | La prueba de menos de 20 ms usa la mediana de 20 repeticiones, pero no declara qué hacer si falla en una CI lenta. | Declarar el método ante falsos fallos (repetir una vez o umbral de CI mayor) y que 20 ms es objetivo de diseño. | Unresolved |
| R-10 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > fila NFR5.7 | La fila NFR5.7 quedó separada de la tabla por una línea en blanco, por lo que en Markdown se renderiza como texto suelto y no como fila. | Quitar la línea en blanco antes de NFR5.7 para que forme parte de la tabla. | New |
| R-11 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/nfr-requirements/security-requirements.md > Consideraciones de amenazas | La tabla de amenazas no incluye NFR5.7 (descarga de claves desde un origen controlado por el atacante). | Añadir una fila de amenaza para la descarga de claves cubierta por NFR5.7. | New |

> R-01 Reviewer note: Existe NFR5.7 con URL derivada de región y grupo, sin `iss`/`jku`/`x5u`, certificado validado, sin redirecciones a otros hosts, tope de 64 KB, espera de 3 s y `keys_unavailable` ante JWKS mal formado o de otro algoritmo, con pruebas para cada caso.

> R-02 Reviewer note: La nota de numeración declara el origen en FR6.1 y que heredan NFR5 por cercanía; `traceability.json` apoya el OK en NFR5.5 y declara las demás filas como requisitos nuevos. Es una explicación honesta del hueco, aceptable.

> R-03 Reviewer note: NFR1.3 fija que el intento fallido cuenta, una a la vez, las demás solicitudes reutilizan o fallan cerrado, con prueba de 100 tokens de `kid` desconocido y con el servidor caído.

> R-04 Reviewer note: `unknown` está en la lista cerrada de `entities.md` línea 40, en NFR1.6 y en observability.

> R-05 Reviewer note: NFR4.4 declara el riesgo aceptado y compara cuerpo y código HTTP.

> R-06 Reviewer note: NFR5.6 reescrito: normalización a minúsculas al cargar y razón de no exigir tiempo constante.

> R-07 Reviewer note: NFR5.2 añade casos sin `exp`, sin `iat` ni `auth_time` y caída a `iat`.

> R-08 Reviewer note: NFR1.8 y NFR3.4 quedan como notas explícitas ("No aplica"); es aceptable. NFR5.5 declara que la comprobación de patrones es de CI de u6 y la propia u4 verifica que su configuración no tiene secretos.

> R-09 Reviewer note: NFR1.1 no cambió: sigue sin método ante falsos fallos en CI lenta ni la nota de que 20 ms es objetivo de diseño. No bloquea.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| (ninguna herramienta listada) | No ejecutada | Verificación manual: sub-IDs únicos, `traceability.json` cubre NFR1 a NFR8 y NFR5.7 está declarado. |

### Summary

Los tres puntos mayores de la iteración 1 están resueltos con criterios de prueba verificables; solo quedan detalles menores (R-09 y dos de formato y cobertura de la tabla de amenazas). No hay Critical ni Major abiertos.
