# Especificación funcional — u5-web-app

## Sources

- [Q1] Token solo en memoria. [Q2] Vista previa sin HTML en bruto. [Q3] Conservar lo escrito al vencer la sesión.
- [scope] Historias US1.1, US4.1, US5.1 y US6.1; contratos C1 y C2; unidad `ui` de `unit-of-work.md`.

## Alcance

u5 completa la pantalla que u1 dejó mínima: acceso (S1), pantalla principal (S2) con título y contador, contexto, generación con carga y reintento, resultado en dos pestañas con copiado, vencimiento de sesión y cierre de sesión. El servicio y su contrato no cambian; el grupo de usuarios de Cognito, el dominio y las direcciones de retorno son de u6-infrastructure.

## Flujo

1. Sin token se ve S1 (BR5.7). Con la respuesta de Cognito se guarda el token en memoria y se pasa a S2 (AC6.1.1).
2. En S2 la persona escribe el título; al pulsar "Generar historia" se aplica BR5.1 y se llama a C1 con el token (AC1.1.1).
3. Con NEEDS_CONTEXT aparece el contexto (BR5.3); con éxito, el resultado (BR5.5); con fallo, el reintento (BR5.4); con SESSION_INVALID, el vencimiento (BR5.6).
4. Cerrar sesión limpia todo (BR5.8).

## Responsabilidades por módulo (sin código)

| Módulo | Responsabilidad | Reglas |
|---|---|---|
| auth | Iniciar el flujo con Cognito, guardar el token en memoria, avisar de su vencimiento | BR5.6, BR5.7 |
| api | Añadir el token a C1 y C2, traducir códigos del servicio a estados de pantalla | BR5.3, BR5.4 |
| ScreenState | Un solo estado a la vez y sus transiciones | BR5.2 |
| result view | Pestañas, vista previa segura, copiado | BR5.5 |
| draft store | Copia temporal de título y contexto al vencer la sesión | BR5.6, BR5.8 |

## Cobertura de criterios

| Historia | Criterios | Reglas |
|---|---|---|
| US1.1 | AC1.1.1 a AC1.1.4 | BR5.1, BR5.2, BR5.3 |
| US4.1 | AC4.1.1 a AC4.1.4 | BR5.5 |
| US5.1 | AC5.1.1 a AC5.1.4 | BR5.2, BR5.4 |
| US6.1 | AC6.1.1 a AC6.1.3 | BR5.7, BR5.8, BR5.10 |

AC5.1.4 (resultado en menos de 60 segundos) depende del servicio; la pantalla garantiza el corte a los 60 s y el aviso.

## Assumptions & Open Questions

None.
