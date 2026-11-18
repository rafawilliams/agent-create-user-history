# Units Generation — Plan y preguntas

Plan: agrupar los cuatro componentes de `components.md` (WebApp, AccessControl, StoryGenerator y ModelGateway) en unidades de trabajo que se puedan construir y probar por separado, con un mapa de dependencias entre ellas. Este paso no decide el orden de construcción ni qué entregar primero; eso lo decide Delivery Planning. En Practices Discovery afirmaste construir primero un corte delgado de punta a punta (esqueleto ambulante: una versión mínima que corre de principio a fin), así que la primera unidad debe ser ese corte.

## Q1. [Arquitectura] ¿Cómo se agrupan los componentes en unidades?

Contexto: se parte del corte delgado de punta a punta afirmado en Practices Discovery. Después hay que completar el resto del trabajo.

- A. La primera unidad es el corte delgado de punta a punta (pantalla mínima, servicio y una llamada al modelo) y después hay una unidad por componente que amplía cada parte (recomendado)
- B. Una unidad por componente desde el inicio, sin un corte delgado previo
- C. Una unidad por historia de usuario (US1.1 a US7.1)
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Arquitectura] ¿La infraestructura y el despliegue automático son una unidad aparte?

Contexto: la infraestructura se define con Terraform y el despliegue es automático a un único entorno al integrar en `main` (`team-practices.md`). Esto decide si es una unidad propia o se reparte.

- A. Sí, una unidad aparte de empaquetado e infraestructura
- B. No, cada unidad aporta su parte de infraestructura
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Arquitectura] ¿Cómo se despliegan las unidades?

Contexto: StoryGenerator, AccessControl y ModelGateway se llaman entre sí en cada solicitud; la interfaz se sirve aparte.

- A. Un despliegue para la interfaz y otro para el servicio, que agrupa StoryGenerator, AccessControl y ModelGateway (recomendado)
- B. Cada componente del servicio se despliega por separado
- C. Todo se despliega junto
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q4. [Arquitectura] ¿Se pueden construir en paralelo las unidades que no dependen entre sí?

Contexto: si hay unidades sin dependencia directa, se pueden construir al mismo tiempo, cada una en su copia del proyecto.

- A. Sí, se permite el paralelismo entre unidades independientes
- B. No, se construyen una a una en orden de dependencias
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Plan Approval

Plan propuesto de 6 unidades, que cubre los 4 componentes más la infraestructura:

- u1-walking-skeleton (service): corte delgado de punta a punta; no depende de ninguna unidad.
- u2-model-gateway (library): acceso al modelo, con Amazon Titan y Claude Sonnet y la evaluación de modelos; depende de u1.
- u3-story-generator (service): generación de la historia y el Markdown; depende de u1.
- u4-access-control (service): inicio de sesión con Gmail u Outlook y verificación de sesión; depende de u1.
- u5-web-app (ui): pantallas de acceso y principal; depende de u1.
- u6-infrastructure (packaging): infraestructura con Terraform y despliegue automático; depende de u1.

Despliegue: la interfaz y el servicio (que agrupa StoryGenerator, AccessControl y ModelGateway) por separado. Las unidades u2 a u6 no dependen entre sí, así que pueden construirse en paralelo.

- Approve Plan
- Revise Plan

[Answer]: Approve Plan

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
