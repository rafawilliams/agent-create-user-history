# Scope Definition — Preguntas

## Q1. [Producto] ¿Cuáles de estas capacidades podrían esperar a una segunda versión? (select all that apply)

Contexto: la descripción inicial pide cuatro cosas: determinar rol, acción y beneficio automáticamente, generar 2 a 3 criterios en Gherkin, validar el formato Gherkin y entregar Markdown listo para Jira. Esta pregunta busca qué es imprescindible (Must have) y qué es negociable para el MVP. Solo se difiere lo que elijas.

- A. La validación automática del formato Gherkin
- B. La determinación automática del rol (el analista lo escribiría o elegiría)
- C. Ninguna: todas son imprescindibles para el MVP
- D. Not yet defined
- X. Other (please specify)

[Answer]: A, B

## Q2. [Producto] ¿Qué debe poder hacer el analista en la pantalla del MVP? (select all that apply)

Contexto: la descripción inicial solo dice que hay una interfaz en React; esto define su alcance mínimo.

- A. Escribir el título de la funcionalidad y ver la historia generada
- B. Copiar el Markdown con un botón
- C. Editar el texto generado antes de copiarlo
- D. Not yet defined
- X. Other (please specify)

[Answer]: A, B

## Q3. [Producto] ¿Qué debe pasar si el Gherkin generado no es válido?

Contexto: el modelo de IA puede generar un Gherkin con errores; esto define el comportamiento esperado frente a ese caso.

- A. Regenerar automáticamente un número limitado de veces y, si sigue fallando, mostrar un error
- B. Mostrar el resultado con una advertencia de que el Gherkin no es válido
- C. Mostrar solo un error, sin resultado
- D. Not yet defined
- X. Other (please specify)

[Answer]: A (superada por Q9: sin validación en el MVP, esta respuesta no aplica a la primera versión)

## Q4. [Producto] ¿Qué debe pasar si el título es muy corto o ambiguo?

Contexto: de un título como "Login" no se puede deducir con certeza el rol, la acción y el beneficio.

- A. El agente genera una historia con lo que entiende, sin hacer preguntas
- B. El agente pide más contexto al analista antes de generar
- C. El agente rechaza el título con un mensaje que explica qué falta
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q5. [Producto] ¿Qué resultado hace aceptable el MVP?

Contexto: en Intent Capture se eligieron dos métricas (tiempo hasta una historia lista para Jira y Gherkin válido a la primera) pero sin una meta. Como la validación automática del Gherkin espera a la segunda versión (Q9), el Gherkin válido se comprobaría revisando a mano un conjunto de títulos de prueba. Estas opciones son propuestas; elige una o indica la tuya.

- A. Menos de 1 minuto por historia y Gherkin válido a la primera en al menos 90% de los títulos de prueba revisados a mano
- B. Menos de 1 minuto por historia y Gherkin válido a la primera en al menos 80% de los títulos de prueba revisados a mano
- C. Definir la meta después de evaluar los modelos
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q6. [Producto] ¿Qué pasa con el agente actual que genera historias desde un Excel mientras se construye el nuevo?

Contexto: en Intent Capture indicaste que el nuevo agente reemplaza al actual; falta saber qué ocurre con el actual y con la entrada por Excel.

- A. Se mantiene en uso hasta que el nuevo MVP sea aceptado
- B. Se retira cuando el nuevo agente se despliegue
- C. Su retiro queda fuera de este alcance (otra iniciativa)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q7. [Entrega] ¿En qué orden prefieres construir las capacidades?

Contexto: hay una dependencia técnica fuerte (habilitar el modelo en Bedrock) y la evaluación de dos modelos. El orden cambia cuándo se ve algo funcionando.

- A. Riesgo primero: habilitar el modelo y evaluar Amazon Titan y Claude Sonnet antes de la interfaz
- B. Valor primero: un flujo mínimo de punta a punta lo antes posible y evaluar los modelos después
- C. Dependencias primero: cuenta y acceso, luego el servicio y al final la interfaz
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q8. [Entrega] ¿Hay una fecha límite concreta para el MVP o para alguna capacidad?

Contexto: en Feasibility indicaste un plazo corto, pero no una fecha.

- A. No hay una fecha límite concreta
- B. Hay una fecha para una demostración del MVP (indícala en Other)
- C. Hay fechas distintas por capacidad (indícalas en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q9. [Producto] ¿La validación del Gherkin entra o no en el MVP?

Contexto: hay dos respuestas que chocan. En Q1 elegiste que la validación automática del Gherkin puede esperar a una segunda versión. En Q3 elegiste que, si el Gherkin no es válido, el agente lo regenere automáticamente, y eso requiere validarlo. La descripción inicial también pide validar el formato Gherkin.

- A. La validación entra en el MVP (se corrige Q1: solo el rol automático puede esperar)
- B. La validación espera a la segunda versión: el MVP muestra el Gherkin tal como lo genera el modelo (Q3 no aplica)
- C. Entra solo una validación mínima que detecta errores y muestra una advertencia, sin regenerar
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q10. [Producto] Si la determinación automática del rol espera a la segunda versión, ¿cómo se define el rol en el MVP?

Contexto: en Q1 elegiste que el rol automático puede esperar, pero la descripción inicial indica que la única entrada es el título de la funcionalidad.

- A. El analista escribe el rol junto con el título
- B. El agente usa siempre un rol genérico fijo (por ejemplo, "usuario")
- C. El rol sigue siendo automático en el MVP (se corrige Q1)
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q11. [Entrega] ¿Cuándo es la demostración del MVP?

Contexto: en Q8 indicaste que hay una fecha para una demostración, pero no cuándo es. Define cuánto cabe en la primera versión.

- A. En una semana
- B. En dos semanas
- C. En un mes
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
