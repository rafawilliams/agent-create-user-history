# Intent Capture — Preguntas

## Sources

- [desc] Initial description: "Construir un Business Analyst Agent.\n\nObjetivo:\nGenerar historias de usuario y criterios de aceptación a partir de un título funcional.\n\nEntrada:\n- Título de funcionalidad\n\nSalida:\n- Historia de usuario\n- Formato: Como [rol], quiero [acción], para [beneficio]\n- 2 a 3 criterios de aceptación\n- Gherkin válido\n- Resultado en Markdown\n\nTecnología:\n- Frontend React\n- API Gateway\n- Lambda\n- Amazon Bedrock Claude Sonnet\n- Sin persistencia para MVP\n\nRequerimientos:\n- Determinar automáticamente el rol.\n- Determinar acción y beneficio.\n- Validar formato Gherkin.\n- Responder en español.\n- Generar Markdown listo para Jira."
- [scope] Workflow-selected scope: `mvp`.

## Q1. [Producto] ¿Qué problema de negocio resuelve este agente?

Contexto: el pedido describe qué hace el agente (generar historias y criterios), pero no el problema que hoy tiene el equipo. De esto depende cómo se mide si el agente vale la pena.

- A. Escribir historias de usuario y criterios de aceptación a mano toma demasiado tiempo
- B. Las historias que se escriben hoy son inconsistentes entre analistas (formato, calidad, Gherkin)
- C. Faltan analistas de negocio y se necesita cubrir esa capacidad con una herramienta
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q2. [Producto] ¿Quién va a usar el agente y qué dolor tiene hoy?

Contexto: define para quién se optimiza el texto generado y el flujo de la interfaz.

- A. Analistas de negocio / Product Owners internos que hoy redactan las historias a mano
- B. Equipos de desarrollo que necesitan historias más claras antes de implementar
- C. Clientes o usuarios externos de la organización
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Producto] ¿Cómo sabremos que la primera versión funciona bien? (select all that apply)

Contexto: sin una medida concreta no se puede decidir si el MVP está terminado.

- A. Tiempo para obtener una historia lista para pegar en Jira (por ejemplo, menos de 1 minuto)
- B. Porcentaje de historias cuyo Gherkin pasa la validación a la primera
- C. Porcentaje de historias que el analista acepta sin editar o con cambios menores
- D. Not yet defined
- X. Other (please specify)

[Answer]: A, B

## Q4. [Producto] ¿Qué motiva construir esto ahora?

Contexto: ayuda a priorizar y a justificar el esfuerzo del MVP.

- A. Oportunidad: probar el uso de Amazon Bedrock con Claude Sonnet en un caso real de negocio
- B. Ahorro de tiempo del equipo de análisis
- C. Estandarizar la calidad de las historias de usuario
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q5. [Producto] ¿Quiénes son las personas interesadas y quién decide el alcance o la prioridad?

Contexto: se registran solo los roles que tú confirmes; no se inventan interesados.

- A. Yo decido el alcance y la prioridad; no hay otros decisores identificados
- B. Hay un patrocinador o líder de producto que decide, y yo coordino (indica el rol en Other)
- C. Hay varios interesados (analistas, desarrollo, QA) que influyen (indica los roles en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q6. [Producto] ¿Hay requisitos de comunicación o una cadencia de reporte?

Contexto: define si hace falta reportar avances a alguien durante el MVP.

- A. Ninguno por ahora
- B. Reporte periódico a un patrocinador (indica la frecuencia en Other)
- C. Demostración al equipo al terminar el MVP
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q7. [Producto] ¿Qué NO debe hacer esta primera versión? (select all that apply)

Contexto: el plan ya está elegido (`mvp`). Esta pregunta es sobre el producto, no sobre el plan: qué se deja fuera para mantener el MVP pequeño. No se asumirá ninguna exclusión que no elijas.

- A. No guardar nada: sin historial ni persistencia de historias generadas
- B. No integrarse directamente con Jira (solo generar Markdown listo para pegar)
- C. No procesar varias funcionalidades a la vez (una por solicitud)
- D. None
- X. Other (please specify)

[Answer]: C, X: dynamodb

## Q8. [Desarrollo] ¿Cómo se relaciona este agente con el agente actual que genera historias desde un Excel?

Contexto: este proyecto ya contiene un agente en Python que crea historias de usuario a partir de un Excel. Esto decide si el nuevo agente lo reemplaza, convive con él o se construye aparte.

- A. Es un agente nuevo e independiente; el actual no se toca
- B. El nuevo agente reemplaza al actual
- C. Conviven y comparten lógica (por ejemplo, el prompt o la validación de Gherkin)
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q9. [Producto] ¿Qué rol tiene el patrocinador que decide el alcance y la prioridad?

Contexto: en Q5 indicaste que hay un patrocinador o líder de producto, pero no su rol. Solo se registrará el rol que confirmes.

- A. Product Owner
- B. Líder de análisis de negocio
- C. Gerente o líder de tecnología
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q10. [Producto] ¿Con qué frecuencia se reporta el avance al patrocinador?

Contexto: en Q6 indicaste un reporte periódico, pero no su frecuencia.

- A. Semanal
- B. Quincenal
- C. Al cierre de cada etapa del plan
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
