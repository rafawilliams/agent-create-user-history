# Reliability Requirements — u4-access-control

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa. El MVP no tiene objetivo formal de disponibilidad (decisión confirmada en u1); la fiabilidad de u4 es el comportamiento ante fallos del proveedor de identidad.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR1.5 | Si Cognito (las claves públicas) no está disponible, la verificación sigue funcionando con la copia en memoria mientras tenga menos de 1 hora, y falla cerrado con SESSION_INVALID cuando la copia es más vieja o no tiene la clave | Pruebas con el servidor de claves caído y una copia de 10 minutos (sirve) y de 2 horas (rechaza) | `rules.md` BR4.7, BR4.5 |
| NFR1.6 | Un error inesperado dentro de la verificación se trata como sesión inválida (falla cerrado), sin traza ni detalle en la respuesta, y queda registrado solo con el motivo `unknown` | Una prueba fuerza una excepción en la verificación y comprueba el 401 y el registro | `rules.md` BR4.5 |
| NFR1.7 | Cada solicitud de verificación es independiente: un fallo no afecta a las demás | Una prueba intercala tokens inválidos y válidos y comprueba que los válidos siguen pasando | `requirements.md` NFR1 |
| NFR1.8 | No hay datos que respaldar: la sesión es un token y la configuración es de despliegue; recuperarse de un fallo es volver a iniciar sesión o volver a desplegar | No aplica respaldo | `requirements.md` NFR4 |

## Assumptions & Open Questions

- Supuesto: no hay interruptor de circuito en el MVP.
- Abierto: el SLO se define antes de ofrecer el servicio a más de 5 personas (condición de u1).
