## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-17T21:00:00Z
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

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `cd backend && python -m pytest tests -q` | 541 passed in 6.62 s | Coincide con lo declarado en `code-summary.md`; sin llamadas de red. `fail_under = 80` sigue intacto en `pyproject.toml`. No se ejecutó la medición de cobertura (el 99,68 % no se verificó de forma independiente). |
| Comprobación local de PyJWT 2.10.1 (sin red) | `crit` y `jku`/`jwk` aceptados por `decode_complete`; `_number(nan)` devuelve `nan` | Respaldan los dos primeros hallazgos Minor. |

### Summary

El verificador sigue el orden fijo (algoritmo y `kid` antes de elegir clave, firma antes de claims, emisor, audiencia, `token_use`, fechas con 60 s y tope de 8 h, correo booleano estricto), la regla única del `kid` y el cerrojo de intento único están bien implementados y probados, el mismo 401 sirve para todo rechazo de token, el 403 es solo `account_not_allowed`, ningún registro lleva token, correo ni `sub`, y un entorno desplegado no puede llegar al verificador simulado. No hay hallazgos Critical ni Major; los puntos Minor son endurecimientos (NaN en fechas, `crit`, reloj de la copia, plazo total de descarga, fallo cerrado con configuración inválida, proveedor exacto). El resumen de código es honesto (BR4.1 diferido, desviación del `kid` declarada).
