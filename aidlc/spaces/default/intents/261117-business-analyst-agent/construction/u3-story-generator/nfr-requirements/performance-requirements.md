# Performance Requirements — u3-story-generator

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa: los valores salen de decisiones ya confirmadas (plazos de C1, capacidad de `requirements.md`) y de las reglas de esta unidad.

u3 corre dentro del servicio de generación (u1). Toda su lógica propia (validar, armar la petición, interpretar la respuesta, armar el Markdown) es trabajo en memoria; el tiempo lo domina la llamada al modelo.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR1.1 | Con un título válido y un servicio sin fallos, el resultado llega dentro del plazo de 55 segundos del servicio y por tanto dentro de los 60 segundos de la interfaz | Una prueba con un modelo simulado que responde al instante comprueba el resultado; el comando local de punta a punta mide el tiempo total contra el modelo real y debe ser menor de 55 s | `requirements.md` NFR1; `contract-summary.md` (C1) |
| NFR1.2 | La lógica propia de u3 (validación, armado de la petición, validación del JSON y armado del Markdown) añade menos de 50 milisegundos por solicitud, sin contar la llamada al modelo | Una prueba mide el tiempo de u3 con un modelo simulado que responde al instante, con un título de 200 caracteres y un contexto de 500: menos de 50 ms | `requirements.md` NFR1 |
| NFR1.3 | Las validaciones que no necesitan el modelo (título vacío, título demasiado largo, contexto demasiado largo, petición de contexto) responden sin llamar al modelo y en menos de 50 milisegundos | Una prueba con un modelo simulado que falla si se llama comprueba que no hay llamada y mide el tiempo | `rules.md` BR3.1, BR3.2, BR3.3 |
| NFR1.4 | u3 usa el plazo restante que le da el servicio para la llamada al modelo y no agrega esperas propias ni reintentos propios | Una prueba comprueba que el tiempo de espera pedido al modelo es el plazo restante recibido y que hay una sola llamada ante un fallo | `requirements.md` NFR1; plazo y reintento de u1 |
| NFR1.5 | El tamaño de la respuesta que u3 acepta está acotado (JSON de pocos kilobytes: dos o tres criterios con campos de hasta 300 caracteres) para que la validación sea de tiempo constante en la práctica | Una prueba con una respuesta del tamaño máximo permitido mide el tiempo de validación y armado: menos de 50 ms | `rules.md` BR3.6 |

## Assumptions & Open Questions

- Supuesto: el modelo tarda segundos, así que los límites de 50 ms de u3 son holgados y solo detectan una regresión grave.
- Abierto: el tiempo real contra el modelo lo mide el comando de punta a punta; no hay meta de percentil porque el MVP lo usan hasta 5 personas.
