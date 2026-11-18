# Reliability Design — u4-access-control

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa. El MVP no tiene objetivo formal de disponibilidad (decisión confirmada en u1).

## Cognito o las claves no disponibles (NFR1.5)

- Con la copia de claves de menos de 1 hora, la verificación sigue funcionando aunque la descarga falle: los tokens cuyo `kid` está en la copia se verifican normalmente.
- Con la copia de más de 1 hora y la descarga caída, o con un `kid` que no está en la copia, la verificación falla cerrado (`keys_unavailable` o `bad_signature` según el caso) y el servicio responde 401. Nunca se acepta un token sin comprobar su firma.
- Recuperarse es automático: la siguiente descarga exitosa (como máximo una por minuto) restablece la copia.

## Error interno (NFR1.6)

Toda la verificación corre dentro de un único manejador: una excepción inesperada se convierte en sesión inválida con el motivo `unknown`, sin traza ni detalle en la respuesta, y queda registrada solo con ese motivo. Falla cerrado.

## Independencia (NFR1.7)

Cada solicitud se verifica por separado: un token inválido no afecta a los siguientes. La única interacción es la renovación de claves, que está acotada y no bloquea.

## Datos y recuperación (NFR1.8)

No hay datos que respaldar: la sesión es un token que emite Cognito y la configuración es de despliegue. Si falla el servicio, se vuelve a desplegar desde `main`; si caduca una sesión, se inicia sesión de nuevo. No hay interruptor de circuito en el MVP.

## Assumptions & Open Questions

- Supuesto: una hora de copia es suficiente para cubrir una caída corta de Cognito y suficientemente corta para que una rotación de claves se note.
- Abierto: el SLO se define antes de ofrecer el servicio a más de 5 personas (condición de u1).
