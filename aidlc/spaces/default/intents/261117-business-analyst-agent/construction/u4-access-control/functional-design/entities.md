# Entities — u4-access-control

Documentos de entrada: `unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md` y `contract-summary.md`. Respuestas: `functional-design-questions.md` (FD Qn). Base: las entidades `Session` y `SessionInvalid` que u1 dejó con la forma del contrato C3, y que u4 implementa de verdad. Los nombres siguen el código nuevo, en inglés.

Ninguna entidad se guarda (NFR4): la sesión es un token sin estado que emite Amazon Cognito y que el servicio verifica en cada solicitud.

```yaml
entities:
  - name: Session
    description: La sesión válida que el servicio deduce de la credencial de la solicitud (contrato C3 y C2).
    owner: AccessControl
    attributes:
      - name: sessionId
        logical_type: text
        required: true
        constraints: [claim jti del token y, si no lo trae, el claim sub; no es un dato de la persona]
      - name: accountId
        logical_type: text
        required: true
        constraints: [claim sub del token (identificador estable de la cuenta en el grupo de usuarios); nunca el correo]
      - name: provider
        logical_type: text
        required: true
        allowed_values: [google, microsoft]
      - name: expiresAt
        logical_type: datetime
        required: true
        constraints: [el menor entre el claim exp y la hora de autenticación más 8 horas (BR4.4)]
    constraints:
      - Los atributos son los de C3; el servicio no guarda la sesión: la deduce del token en cada solicitud.
    relationships: []

  - name: SessionInvalid
    description: El resultado de verificar una credencial que no sirve (contrato C3).
    owner: AccessControl
    attributes:
      - name: reason
        logical_type: text
        required: true
        allowed_values: [missing, malformed, bad_signature, wrong_issuer, wrong_audience, expired, wrong_token_use, keys_unavailable, not_configured, account_not_allowed, unknown]
    constraints:
      - El motivo es de lista cerrada y propio; nunca copia texto del token ni del proveedor.
      - El servicio traduce account_not_allowed a ACCOUNT_NOT_ALLOWED y los demás motivos a SESSION_INVALID (BR4.3, BR4.5).
    relationships: []

  - name: AllowedAccount
    description: Un correo permitido para entrar, mantenido en la configuración del despliegue.
    owner: AccessControl
    attributes:
      - name: email
        logical_type: text
        required: true
        unique: true
        constraints: [en minúsculas, sin espacios; la comparación es exacta sobre el texto en minúsculas, sin normalizar puntos ni alias (BR4.3)]
    constraints:
      - La lista completa vive en la configuración (unos 5 correos); no se guarda en el servicio ni se registra.
    relationships: []

  - name: IdentityProviderConfig
    description: La configuración del grupo de usuarios de Cognito que el servicio necesita para verificar tokens.
    owner: AccessControl
    attributes:
      - name: region
        logical_type: text
        required: true
      - name: userPoolId
        logical_type: text
        required: true
      - name: appClientId
        logical_type: text
        required: true
        constraints: [debe coincidir con la audiencia del token]
    constraints:
      - No contiene secretos: el emisor y las claves públicas se deducen de la región y del grupo.
      - Si falta cualquiera de los tres valores, el servicio no verifica sesiones y rechaza toda solicitud (BR4.5).
    relationships: []
```

## Resumen

u4 trabaja con cuatro entidades: `Session` y `SessionInvalid` (con la forma de C3), `AllowedAccount` (la lista de correos permitidos, en configuración) y `IdentityProviderConfig` (los tres valores de Cognito). Nada de esto se guarda.

## Assumptions & Open Questions

- Supuesto: el correo es un dato de la persona; se usa solo para compararlo con la lista y nunca se registra ni se devuelve (NFR4).
- Abierto: nombres exactos de las variables de configuración; se fijan en Code Generation.
