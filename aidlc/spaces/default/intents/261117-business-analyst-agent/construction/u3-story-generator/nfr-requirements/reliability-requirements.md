# Reliability Requirements — u3-story-generator

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa. El MVP no tiene objetivo formal de disponibilidad (decisión confirmada en u1); la fiabilidad de u3 es de comportamiento ante fallos, no de porcentaje.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR1.6 | Una respuesta del modelo sin la estructura esperada (no es JSON, faltan campos, menos de 2 o más de 3 criterios, campo vacío o de más de 300 caracteres, texto alrededor del JSON, idioma no español) se informa como INVALID_MODEL_RESPONSE reintentable y nunca devuelve texto parcial | Una prueba por cada caso: el servicio devuelve el error y ningún campo del resultado | `rules.md` BR3.6, BR3.7; AC5.1.3 |
| NFR1.7 | Un fallo del acceso al modelo o un plazo agotado se informa con el código y la indicación de reintento de la tabla de errores de u1, y u3 nunca devuelve un resultado vacío o parcial | Pruebas con cada tipo de error del modelo comprueban el código, el HTTP y `retryable` | `rules.md` BR3.10; AC5.1.2 |
| NFR1.8 | Un error inesperado dentro de u3 se convierte en un error de contrato sin traza ni detalle interno y queda registrado sin contenido | Una prueba fuerza una excepción interna y comprueba la respuesta y el registro | `rules.md` BR3.10; NFR4.2 |
| NFR1.9 | u3 no pierde el título de la persona: la pantalla lo conserva; u3 no guarda nada, así que no hay recuperación de datos ni respaldos | Cubierto por u5-web-app (AC5.1.2); en u3 no aplica respaldo porque no hay datos | `requirements.md` NFR4 |

## Assumptions & Open Questions

- Supuesto: no hay interruptor de circuito en el MVP; cada solicitud falla de forma independiente con un error claro.
- Abierto: el SLO se define antes de ofrecer el servicio a más de 5 personas (condición ya fijada en u1).
