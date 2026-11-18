## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-19T01:00:00Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Minor | backend/story_service/token_verifier.py > `_number` y `_check_claims` | `_number` rechaza booleanos y textos pero acepta `NaN` e `Infinity` (`json.loads` los produce como `float`). Comprobado: `_number(float('nan'))` devuelve `nan`. Con `exp: NaN` la comparación `now > exp + 60` es falsa y el vencimiento nunca se aplica; con `auth_time: NaN` tampoco se aplica el tope de 8 horas. Solo es explotable con un token firmado por Cognito, así que es defensa en profundidad, pero contradice la regla de fechas no numéricas. | Hacer que `_number` devuelva `None` cuando `math.isfinite(value)` es falso, y añadir una prueba parametrizada con `NaN` e `Infinity` en `exp`, `iat`, `nbf` y `auth_time`. | New |
| R-02 | Minor | backend/story_service/token_verifier.py > paso 3 (encabezado) y backend/tests/test_token_verifier.py | El encabezado `crit` no se rechaza: PyJWT 2.10.1 acepta un token con `crit: ["exp"]` y el verificador lo deja pasar (RFC 7515 pide rechazar extensiones críticas desconocidas). `jku`, `x5u` y `jwk` sí se ignoran sin efecto porque la clave sale solo del `kid` y del almacén, pero ninguna prueba lo demuestra: no hay casos de `jku`, `x5u`, `jwk`, `crit` ni de `kid` duplicado. | Rechazar con `bad_signature` (o `malformed`) un encabezado con `crit`, y añadir pruebas de inyección de `jku`/`x5u`/`jwk`/`crit` que confirmen que la clave sigue saliendo solo del almacén. | New |
| R-03 | Minor | backend/story_service/jwks_store.py > `JwksStore.__init__` (`clock=time.monotonic`) y `get_key` | La edad de la copia (1 hora) se mide con `time.monotonic`. En un entorno Lambda congelado y reanudado, ese reloj puede no avanzar mientras está suspendido, de modo que una copia de más de 1 hora podría seguir usándose, lo que contradice la regla de que nunca se use. La razón de usar un reloj monótono para el límite de un intento por minuto no aplica igual a la caducidad. | Medir la edad de la copia con un reloj de pared (por ejemplo `time.time`), o documentar y probar el comportamiento tras una suspensión; el límite de un intento por minuto puede seguir con el reloj monótono. | New |
| R-04 | Minor | backend/story_service/jwks_store.py > `HttpsJwksFetcher.__call__` | Los 3 segundos son un plazo por operación de socket, no un plazo total: `response.read(MAX_RESPONSE_BYTES + 1)` con un servidor que envíe bytes con cuentagotas puede tardar mucho más de 3 s (hasta tope de 64 KB), y mantiene el cerrojo de intento único, de modo que las demás solicitudes fallan con `keys_unavailable` mientras tanto. El origen es AWS, así que el riesgo es bajo. | Aplicar un plazo total (por ejemplo medir el tiempo transcurrido entre lecturas parciales y abortar pasados 3 s) o registrar la limitación como riesgo aceptado en `code-summary.md`. | New |
| R-05 | Minor | backend/story_service/config.py > `_identity_from_env` y `build_session_verifier` | Un valor de Cognito mal formado (región o grupo con formato roto) se convierte en `None` en silencio. Si además `APP_ENV` es `local`/`test` con la bandera activa, se usa el verificador simulado aunque la persona haya configurado Cognito, algo más amplio que "solo sin esa configuración". En despliegue (`infra/main.tf` fija `APP_ENV = "prod"` y no define la bandera) no hay ruta al simulado, así que el riesgo se limita a local. | Distinguir "ausente" de "presente pero inválido": con valores presentes e inválidos fallar cerrado con `not_configured` sin caer al simulado, y cubrirlo con una prueba. | New |
| R-06 | Minor | backend/story_service/token_verifier.py > `_provider` | El proveedor se deduce con `startswith("google")`/`startswith("microsoft")` sobre `identities[0].providerName`. El claim lo emite Cognito (no lo controla quien presenta el token), así que no es suplantable, pero el prefijo aceptaría nombres como `GoogleOtro` y depende de que `u6-infrastructure` nombre los proveedores exactamente así. | Comparar con igualdad exacta (`google`, `microsoft`) en minúsculas, o con una lista cerrada de nombres, y dejar la correspondencia con u6 como pendiente explícita. | New |
| R-07 | Minor | aidlc/spaces/default/intents/261117-business-analyst-agent/construction/u4-access-control/code-generation/code-summary.md > Reparación > Corrección | El resumen dice que la descarga "lanza TimeoutError al pasar 3 s en total", pero el plazo no es duro. El reloj solo se consulta después de que `opener.open` vuelve y después de cada `read`. Dentro de `open` el timeout de 3 s de urllib se aplica por separado a la conexión TCP, al handshake TLS y a la lectura de cabeceras, y la resolución DNS no tiene tope. Cada salto de una redirección al mismo servidor abre otra conexión con su propio timeout de 3 s, aunque el reloj es el mismo. Cada `read` bloqueante puede durar hasta 3 s antes de que se compruebe el plazo, de modo que el peor caso sigue siendo de varios segundos (de 6 s en adelante). El cerrojo queda acotado, pero no a 3 s. | Declarar en el resumen (y en la nota de NFR1.2) que el plazo es de 3 s comprobado entre operaciones y que el peor caso es la suma de timeouts por operación. Aceptarlo explícitamente o, si se exige 3 s duros, imponer un límite real con un hilo o un `socket.settimeout` que se reduzca con el tiempo restante. | New |
| R-08 | Minor | backend/tests/test_jwks_store.py > test_time_spent_connecting_counts_towards_the_total_deadline y _DripResponse | Ninguna prueba cubre los casos donde el plazo no se puede cumplir: un salto de redirección que consuma tiempo, ni un `read` único que dure más de 3 s. `_DripResponse.read` limita el tamaño a 100 bytes, de modo que la prueba del tope de 64 KB no ejercita los trozos reales de 4096 bytes. El recorte `MAX_RESPONSE_BYTES + 1 - total` solo se ve en trozos de 100, y el límite exacto de 64 KB con trozos de 4096 solo lo cubre la prueba anterior con BytesIO. Las 5 pruebas pueden fallar por la razón correcta (comprobado por lectura: quitar la comprobación tras conectar o tras leer rompe las pruebas 1 y 2), y el reloj inyectado evita esperas reales. | Opcional: añadir una prueba de redirección con reloj compartido y hacer que `_DripResponse` respete el tamaño pedido para ejercitar trozos de 4096. Documentar la limitación del punto anterior. | New |

> R-01 Not re-checked this round

> R-02 Not re-checked this round

> R-03 Not re-checked this round

> R-04 Not re-checked this round

> R-05 Not re-checked this round

> R-06 Not re-checked this round

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `cd backend && python -m pytest tests -q` | 563 passed in 4.84 s | Coincide con lo declarado en el resumen (563). No se ejecutó la medición de cobertura (99,68 %), por lo que esa cifra se toma de lo declarado. |

### Summary

La reparación es correcta en lo esencial: el reloj arranca antes de abrir la conexión y se comprueba tras conectar y tras cada lectura. El tope de 64 KB es exacto (64 KB pasa, +1 falla, sin error de uno). TimeoutError cae en `keys_unavailable` por el `except Exception` de `_refresh`, la copia no se toca, el cerrojo se libera en `finally` y no se registran datos sensibles. El plazo no es duro: urllib aplica 3 s por operación y la resolución DNS no tiene tope. Esto debe declararse como limitación aceptada, porque el resumen presenta un plazo total de 3 s que el código no garantiza. Las pruebas son deterministas y las 563 pasan.
