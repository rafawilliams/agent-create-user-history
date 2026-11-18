# CI/CD Pipeline — u4-access-control

Documentos de entrada: `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: u4 reutiliza el flujo de GitHub Actions de u1 (un entorno, despliegue al integrar en `main`).

## Qué agrega u4 al flujo de CI

| Etapa del flujo | Qué agrega u4 | Puerta (si falla) |
|-----------------|---------------|-------------------|
| 1. Estilo y tipos | Black y Ruff sobre el código de u4 (NFR8.4) | Bloquea la integración |
| 2. Pruebas y cobertura | Las pruebas de u4 corren con TDD (NFR8.1) y el piso de 80 % se mide en la suite completa. Los tokens de prueba se firman con un par de claves RSA generado en las pruebas; nunca se llama a Cognito. Incluyen: algoritmo "none" y simétricos, sin `kid`, `kid` desconocido, firma alterada (NFR5.1); emisor, audiencia, tipo, fechas con tolerancia y máximo de 8 horas, sin `exp` o sin fechas de inicio (NFR5.2); `email_verified` falso o ausente, correo con otra capitalización, punto de Gmail y alias "+" (NFR5.3); configuración incompleta, claves no disponibles, copia vencida y el verificador simulado nunca con configuración real (NFR5.4); descarga de claves desde la dirección derivada, `iss` y `jku` ignorados, redirección a otro host, respuesta de más de 64 KB, JWKS mal formado (NFR5.7); la regla única del `kid` (NFR5.1, NFR1.5); renovación una por minuto con el servidor de claves caído y 100 tokens de `kid` desconocido (NFR1.2, NFR1.3, NFR3.2); 5 verificaciones en paralelo (NFR3.1); lista de 50 y de 51 correos y quitar un correo entre dos solicitudes (NFR3.3, NFR5.6); registros sin token, correo ni `sub`, y la misma respuesta 401 para todos los motivos (NFR4.2, NFR4.4); un error interno que falla cerrado (NFR1.6, NFR1.7); la verificación de menos de 20 ms con la mediana de 20 repeticiones, repetida hasta 3 veces antes de fallar (NFR1.1, NFR1.4) | Bloquea la integración |
| 3. Verificaciones de Terraform | `terraform fmt`, `validate` y `plan` de los recursos de Cognito cuando `u6-infrastructure` los agregue | Bloquea la integración |
| 4. Verificaciones de seguridad del diseño | La búsqueda de patrones de claves de AWS que posee `u6-infrastructure`; una prueba de u4 de que el código y la configuración no contienen secretos (NFR5.5); y, con la configuración real presente, que el plan no define el verificador simulado | Bloquea la integración |
| 5 y 6. Despliegue y prueba de humo | Con el verificador real, la prueba de humo de `u6-infrastructure` comprueba que una solicitud sin sesión recibe SESSION_INVALID y que un token inválido recibe la misma respuesta; la prueba de éxito con inicio de sesión real es manual. Para distinguir un verificador configurado de uno con `not_configured`, la prueba de humo comprueba además que el `authOutcome` del rechazo sea `missing` o `bad_signature` y no `not_configured` | No aplica a u4 |

## Revisión manual de u4 en AWS

La persona comprueba una vez, al desplegar: el inicio de sesión con una cuenta de la lista (llega a la pantalla principal y genera una historia), con una cuenta fuera de la lista (ve el mensaje de acceso no autorizado), el cierre de sesión, y que `email_verified` llega verdadero con Google y con Microsoft. Este resultado no corre en CI y se registra en `docs/`.

## Retroceso

u4 no tiene despliegue propio: se retrocede con la función de generación (volver a aplicar la revisión anterior con Terraform, ver el flujo de u1). Si el grupo de usuarios o las federaciones fallan, se vacía la variable de Terraform de la configuración del grupo y el flujo la aplica: el servicio vuelve al estado seguro (rechaza toda solicitud). No se cambian a mano las variables que posee Terraform. No hay datos que revertir (NFR4.1). El cambio coordinado de las listas cerradas de u1 se revierte con Git junto con el resto; el grupo de usuarios tiene protección contra la eliminación y se destruye solo de forma explícita.

## Secretos y credenciales

La aplicación cliente de Cognito no tiene secreto (NFR5.5). Las credenciales de las federaciones de Google y de Microsoft son variables sensibles de Terraform que se pasan por el entorno de quien despliega o por los secretos de GitHub Actions; nunca van al repositorio. El flujo sigue autenticándose en AWS con la federación de identidad de GitHub de u1.

## Assumptions & Open Questions

- Abierto: cómo se entregan las credenciales de las federaciones al flujo de despliegue (secretos de GitHub o a mano); lo decide `u6-infrastructure`.
- Supuesto: el flujo de u1 ejecuta la suite completa en la etapa 2, así que las pruebas de u4 entran sin cambios en el flujo.
