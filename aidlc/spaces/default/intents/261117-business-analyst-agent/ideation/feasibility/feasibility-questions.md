# Feasibility & Constraints — Preguntas

## Q1. [Plataforma AWS] ¿Qué cuenta de AWS se usará y tiene acceso a Amazon Bedrock con Claude Sonnet?

Contexto: sin acceso al modelo en Bedrock el agente no puede generar historias; es la dependencia técnica más importante del MVP.

- A. Hay una cuenta AWS existente con acceso a Bedrock ya habilitado para Claude Sonnet
- B. Hay una cuenta AWS existente, pero Bedrock / Claude Sonnet aún no está habilitado
- C. Todavía no hay cuenta AWS para este proyecto
- D. Not yet defined
- X. Other (please specify)

[Answer]: X: podemos usar un modelo de amazon titan

## Q2. [Plataforma AWS] ¿En qué región de AWS debe ejecutarse?

Contexto: la disponibilidad de Claude Sonnet en Bedrock y la residencia de los datos dependen de la región.

- A. us-east-1 (N. Virginia)
- B. us-west-2 (Oregón)
- C. Una región específica por política de la organización (indícala en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Arquitectura] ¿Con qué sistemas existentes debe integrarse el MVP? (select all that apply)

Contexto: cada integración añade trabajo y riesgo. Esta pregunta no asume ninguna; solo se registran las que elijas.

- A. Ninguno: el analista escribe el título en la interfaz y copia el Markdown a Jira
- B. Jira (por ejemplo, para crear la historia directamente)
- C. Un sistema de identidad corporativo (SSO)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Seguridad] ¿Cómo debe controlarse el acceso al agente?

Contexto: define si la interfaz y la API necesitan autenticación en el MVP.

- A. Sin autenticación: uso interno en un entorno controlado
- B. Inicio de sesión corporativo (SSO)
- C. Una clave de API simple para llamar al servicio
- D. Not yet defined
- X. Other (please specify)

[Answer]: X: login con gmail/outlook

## Q5. [Cumplimiento] ¿Hay requisitos regulatorios o datos sensibles en los títulos de funcionalidad?

Contexto: los títulos se enviarán a un modelo de lenguaje; si pueden contener información confidencial, cambian las restricciones de seguridad y de residencia de datos.

- A. No: no hay requisitos regulatorios ni datos sensibles
- B. Son datos internos confidenciales que no deben salir de la cuenta AWS de la organización
- C. Hay requisitos regulatorios específicos (por ejemplo, residencia de datos); indícalos en Other
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q6. [Entrega] ¿Cuál es el perfil técnico del equipo que construirá el MVP?

Contexto: define el riesgo de aprendizaje de React, AWS Lambda y Bedrock. Este proyecto ya tiene un agente en Python.

- A. Experiencia en React y en AWS serverless (Lambda, API Gateway)
- B. Experiencia en React, pero poca en AWS serverless
- C. Experiencia principalmente en Python, con poca en React y AWS serverless
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q7. [Entrega] ¿Qué restricciones de plazo y presupuesto tiene el MVP?

Contexto: define cuánto alcance cabe en la primera versión y si hay límite de costo en AWS.

- A. Plazo corto (pocas semanas) y costo de AWS mínimo
- B. Sin fecha fija, pero con un tope de costo de AWS
- C. Hay una fecha de demostración fija (indícala en Other)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q8. [Entrega] ¿Hay bloqueos organizacionales conocidos?

Contexto: aprobaciones o prioridades en competencia pueden retrasar el MVP aunque la parte técnica sea viable.

- A. Ninguno conocido
- B. Se necesita aprobación de seguridad o arquitectura antes de usar Bedrock
- C. Hay prioridades en competencia o un congelamiento de cambios
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q9. [Plataforma AWS] ¿Cómo se relaciona Amazon Titan con Claude Sonnet, el modelo de la descripción inicial?

Contexto: en Q1 respondiste que se puede usar un modelo de Amazon Titan. La descripción inicial pedía Claude Sonnet en Bedrock, y la calidad del texto y del Gherkin generado depende del modelo.

- A. Titan reemplaza a Claude Sonnet en el MVP
- B. Titan es una alternativa si Claude Sonnet no está disponible; Claude Sonnet sigue siendo la preferida
- C. Se evaluarán ambos modelos y se decide después
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q10. [Plataforma AWS] ¿Ya existe una cuenta de AWS para este proyecto?

Contexto: en Q1 no quedó claro si hay una cuenta con Bedrock disponible. De esto depende si hace falta solicitarla o habilitar modelos antes de empezar.

- A. Sí, existe una cuenta AWS y Bedrock ya está habilitado
- B. Sí, existe una cuenta AWS, pero hay que habilitar el modelo en Bedrock
- C. No, todavía no hay cuenta AWS
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
