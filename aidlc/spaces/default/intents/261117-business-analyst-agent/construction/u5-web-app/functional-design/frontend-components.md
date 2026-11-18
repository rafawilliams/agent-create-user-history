# Componentes de la interfaz — u5-web-app

## Sources

- [scope] `interaction-spec.md`, `design-system-mapping.md` y `accessibility-checklist.md` de Refined Mockups (el detalle de estados, roles y mapeo a MUI vive allí y no se repite).
- [Q1] Token solo en memoria. [Q2] Vista previa sin HTML en bruto. [Q3] Conservar lo escrito al vencer la sesión.

## Jerarquía

| Componente | Muestra | Reglas | Criterios |
|---|---|---|---|
| App | Elige entre S1 y S2 según el estado de la pantalla (ENT-002) | BR5.7 | AC6.1.1, AC6.1.2 |
| LoginButtons | "Continuar con Gmail" y "Continuar con Outlook", mensaje de acceso | BR5.7 | AC6.1.1, AC6.1.3 |
| AppHeader y LogoutButton | Nombre del agente y "Cerrar sesion" (menú en móvil) | BR5.8 | AC6.1.1 |
| TitleField | Título con contador N / 200 y error bajo el campo | BR5.1 | AC1.1.2, AC1.1.3 |
| ContextField | Contexto de hasta 500 caracteres, con el foco al aparecer | BR5.3 | AC1.1.4 |
| GenerateButton | "Generar historia"; desactivado mientras se genera | BR5.2 | AC1.1.1, AC5.1.1 |
| StatusMessage | Carga, fallo con "Reintentar", sesión vencida, cuenta sin acceso | BR5.4, BR5.6 | AC5.1.1, AC5.1.2, AC5.1.3 |
| ResultTabs | "Vista previa" y "Markdown" con el mismo contenido | BR5.5 | AC4.1.1 |
| CopyButton | "Copiar Markdown" y la confirmación "Markdown copiado" | BR5.5 | AC4.1.2, AC4.1.3, AC4.1.4 |

## Datos y llamadas

La pantalla usa C1 (POST /v1/stories) y C2 (GET y DELETE /v1/session) con el token en memoria (ENT-001). Los estados de pantalla son los de ENT-002 y la copia temporal es ENT-003. Los componentes no guardan nada fuera de la memoria, salvo esa copia (BR5.6).

## Assumptions & Open Questions

None.
