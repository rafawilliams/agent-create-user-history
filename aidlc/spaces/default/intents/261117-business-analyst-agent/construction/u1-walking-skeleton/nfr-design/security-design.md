# Security Design — u1-walking-skeleton

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. Respuestas: `nfr-design-questions.md` (ND Qn).

## Autenticación y el verificador simulado (NFR5.2)

El servicio llama al verificador de sesión a través de la interfaz `SessionVerifier` (contrato C3). Cómo se elige el verificador:

1. Un solo punto de arranque (la composición del servicio) decide qué verificador se usa; el resto del código solo ve la interfaz.
2. El verificador simulado solo se enlaza si el servicio corre con el valor de entorno `APP_ENV` igual a `local` o a `test`, **y** además se pide de forma explícita con `ALLOW_SIMULATED_SESSION` verdadero.
3. Con cualquier otro valor de `APP_ENV`, o sin él, el servicio se considera desplegado: si no hay un verificador real configurado, no se enlaza ninguno y toda solicitud se rechaza con SESSION_INVALID (falla cerrado).
4. El valor por defecto de `ALLOW_SIMULATED_SESSION` es falso.
5. Condición de retiro verificable: una prueba automática comprueba que, con `APP_ENV` distinto de `local` y `test`, el servicio nunca enlaza el verificador simulado; y que la configuración desplegada por `u6-infrastructure` no define `ALLOW_SIMULATED_SESSION`.

## Protección de datos (NFR4.1, NFR4.2, NFR4.3)

- **Sin persistencia:** el servicio no tiene ningún almacén de datos; el título y el resultado viven solo en la memoria de la solicitud.
- **Registros solo de errores y métricas:** los registros estructurados usan una lista cerrada de campos: `requestId`, código de resultado, duración y identificador del modelo. Ningún campo guarda el título, el contexto ni el Markdown. Cualquier otro campo se descarta.
- **Credenciales fuera de los registros:** la cabecera `Authorization` no se copia a ningún registro; el `requestId` es un identificador aleatorio sin datos personales.
- **Registro de invocaciones del modelo:** se mantiene desactivado en la cuenta de AWS, porque por defecto puede capturar el contenido (NFR4.2). Lo configura `u6-infrastructure`.
- **Transporte:** solo HTTPS entre la interfaz, el servicio y el modelo.

## Tratamiento del título como dato no confiable (NFR4.4)

El servicio recorta los espacios del título, rechaza el que esté vacío (TITLE_EMPTY) y el que supere 200 caracteres (TITLE_TOO_LONG), y lo inserta en la petición al modelo dentro de un delimitador fijo, como contenido y no como instrucción. El texto de las instrucciones va aparte, en la configuración (ADR-003). Un título que pida cambiar las instrucciones no debe alterar el formato de salida; la defensa completa (por ejemplo, la verificación del resultado) la construye `u3-story-generator`.

## Secretos (NFR5.1)

- En el entorno desplegado, el servicio obtiene sus permisos mediante el rol de ejecución de AWS, con permiso mínimo para invocar el modelo configurado; no hay claves en el código ni en los archivos versionados.
- En local, usa las credenciales del perfil de AWS de quien lo ejecuta, que no se guardan en el proyecto. El archivo `.env` local sigue ignorado por git.

## Límite de uso (NFR3.2)

Por la decisión ND Q1, el límite por persona por día se difiere hasta que exista el control de acceso (`u4-access-control`). Hasta entonces el esqueleto aplica un límite de tasa global (ver `scalability-design.md`).

## Superficie de ataque y mitigaciones

| Amenaza | Mitigación en el diseño |
|---------|------------------------|
| Acceso sin sesión al modelo | Falla cerrado: sin verificador real, el servicio desplegado rechaza toda solicitud |
| Fuga de contenido en registros | Lista cerrada de campos; registro de invocaciones del modelo desactivado |
| Inyección en el título | Delimitador fijo y separación de las instrucciones; validación de longitud |
| Filtración de credenciales | Rol de AWS en despliegue; sin claves en el código; la cabecera no se registra |
| Abuso de costo | Límite de tasa global y concurrencia acotada |

## Assumptions & Open Questions

- Abierto: nombre exacto de las variables de entorno (se fijan en Code Generation).
- Abierto: política de CORS y almacenamiento de la credencial en la interfaz (`u4-access-control` y `u5-web-app`).
