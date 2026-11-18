# Logical Components — u4-access-control

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

Vista por componentes de dónde se aplican los patrones de diseño no funcional. u4 es código dentro de la función de generación (u1); no se despliega por separado. Lo que sí necesita de la infraestructura es el grupo de usuarios de Cognito, que crea u6.

## Inventario lógico

| Componente lógico | Qué es | Patrones que se aplican | Dominio de falla |
|-------------------|--------|------------------------|------------------|
| Lector de configuración | Región, grupo, cliente de la aplicación y lista de correos del entorno | Valida al iniciar; lista de hasta 50 correos; sin configuración: falla cerrado (NFR5.4, NFR3.3) | Al inicializar: sin configuración válida toda solicitud se rechaza |
| Verificador de token | Orden fijo de la verificación | RS256 fijado, claims, 60 s de tolerancia, 8 horas desde la autenticación (NFR5.1, NFR5.2) | Una solicitud |
| Almacén de claves públicas | Copia en memoria con renovación | Dirección derivada de la configuración, HTTPS, 64 KB, 3 s, una a la vez y una por minuto (NFR5.7, NFR1.2, NFR1.3, NFR3.2) | Aislado: su caída hace fallar cerrado a quien necesita la descarga |
| Lista de cuentas | Comparación exacta en minúsculas con `email_verified` | Se consulta en cada solicitud (NFR5.3, NFR5.6) | Una solicitud |
| Traductor de resultados | Convierte el resultado a SESSION_INVALID o ACCOUNT_NOT_ALLOWED | Misma respuesta para todos los motivos de token (NFR4.4) | Una solicitud |
| Aporte al registro | `authOutcome` y `authDurationMs` | Sin token, correo ni `sub` (NFR4.2, NFR4.5) | Si falla, la solicitud sigue |
| Cognito (servicio externo) | Emite y firma los tokens y publica las claves | Su caída solo afecta a quien necesita una descarga | Externo |

## Radio de impacto

- Un token inválido afecta solo a su solicitud (NFR1.7).
- Una caída de Cognito afecta a las sesiones cuya clave no está en la copia o cuando la copia pasó de 1 hora; con la copia vigente, las sesiones existentes siguen funcionando (NFR1.5).
- Sin configuración, u4 rechaza toda solicitud: el servicio queda protegido, no abierto.

## Recursos compartidos

- La copia de claves es por instancia y de solo lectura salvo su reemplazo atómico (NFR3.1).
- El grupo de usuarios de Cognito, la aplicación cliente (sin secreto, con PKCE), la federación con Google y Microsoft, la vigencia de 8 horas de los tokens de identidad y de renovación, y el mapeo de `email_verified` de Microsoft son de `u6-infrastructure`.

## Puente con Infrastructure Design

Infrastructure Design debe: crear el grupo de usuarios y la aplicación cliente sin secreto; fijar la vigencia de 8 horas de los tokens de identidad y de renovación; configurar la federación de Google y de Microsoft y el mapeo de atributos para que `email_verified` sea verdadero solo cuando el proveedor lo verificó; entregar a la función la región, el identificador del grupo, el cliente de la aplicación y la lista de correos como variables de entorno; y no agregar permisos de AWS para u4 (solo descarga una dirección pública).

## Cobertura de requisitos sin patrón propio

- NFR1.1 a NFR1.4: `performance-design.md`; NFR1.5 a NFR1.8: `reliability-design.md`; NFR3.1 a NFR3.4: `scalability-design.md`; NFR4.1 a NFR4.4 y NFR5.1 a NFR5.7: `security-design.md`.
- NFR2, NFR6 y NFR7 no aplican a u4; NFR8.1 a NFR8.4 no son patrones de diseño: los verifican Code Generation (pruebas primero) y Build and Test (umbral de cobertura en CI).

## Assumptions & Open Questions

- Abierto: nombres definitivos de los módulos y de las variables de entorno; se fijan en Code Generation.
