# Unit of Work — Business Analyst Agent

Documentos de entrada: `components.md`, `decisions.md`, `requirements.md` y `stories.md`. Respuestas: `units-generation-questions.md` (UG Qn). Dependencias: `unit-of-work-dependency.md`. Historias por unidad: `unit-of-work-story-map.md`.

El plan se aprobó en Plan Approval de `units-generation-questions.md`: un corte delgado de punta a punta primero (UG Q1; esqueleto ambulante afirmado en `team-practices.md`), una unidad por componente que amplía cada parte, y una unidad aparte de infraestructura (UG Q2). La interfaz y el servicio se despliegan por separado (UG Q3).

## Unidades

| Unit ID | Directory | Kind | Complejidad | Despliegue |
|---------|-----------|------|-------------|------------|
| U1 | u1-walking-skeleton | service | M | Independiente: es la primera versión que corre de punta a punta |
| U2 | u2-model-gateway | library | S | Embebida en el servicio |
| U3 | u3-story-generator | service | M | Compartida: forma parte del despliegue del servicio |
| U4 | u4-access-control | service | M | Compartida: forma parte del despliegue del servicio |
| U5 | u5-web-app | ui | M | Independiente: despliegue de la interfaz |
| U6 | u6-infrastructure | packaging | M | Independiente: define y despliega los dos despliegues |

## U1 — u1-walking-skeleton

- **Descripción:** el corte delgado de punta a punta: una pantalla mínima donde se escribe un título, el servicio y una llamada al modelo que devuelve una historia en Markdown. Es la primera versión que se puede ejecutar de principio a fin.
- **Límites:** contiene versiones mínimas de WebApp, StoryGenerator y ModelGateway, suficientes para ejercitar el camino completo. No incluye inicio de sesión, validación completa, pestañas ni manejo de errores completo; eso lo agregan las demás unidades.
- **Responsabilidades:** demostrar que las piezas se conectan antes de construir las funciones reales; fijar las interfaces entre componentes que usarán las demás unidades.
- **Componentes:** WebApp, StoryGenerator, ModelGateway (versión mínima).
- **Notas:** `components.md` y `decisions.md` (ADR-001 a ADR-005) limitan cómo se agrupan los componentes; esta unidad respeta esos límites. La comprobación de que corre de punta a punta se fija en Delivery Planning.

## U2 — u2-model-gateway

- **Descripción:** el acceso completo al modelo de IA a través de Amazon Bedrock, con soporte para Amazon Titan y Claude Sonnet y el cambio entre ellos por configuración.
- **Límites:** solo llama al modelo y traduce sus fallos y tiempos de espera; no interpreta el contenido de la respuesta.
- **Responsabilidades:** seleccionar el modelo configurado (FR7.1), llamar al modelo y devolver su respuesta, traducir fallos a errores propios (FR5.2); ejecutar la evaluación de Titan frente a Claude Sonnet con los títulos de ejemplo (US7.1).
- **Componentes:** ModelGateway.
- **Notas:** ADR-002. Las credenciales no van en el código (NFR5).

## U3 — u3-story-generator

- **Descripción:** la generación completa de la historia y del Markdown final.
- **Límites:** recibe el título y el contexto, y devuelve el Markdown; no maneja la identidad ni habla directamente con Bedrock.
- **Responsabilidades:** reglas de entrada y de título ambiguo (FR1), armado de la petición con el prompt de configuración (FR2, FR3; ADR-003), interpretación de la respuesta y Markdown (FR4; ADR-005), manejo de respuestas inválidas y del máximo de 60 segundos (FR5), sin registrar contenido (NFR4).
- **Componentes:** StoryGenerator.
- **Notas:** ADR-001, ADR-003 y ADR-005. Se prueba con un modelo simulado definido en U1 (TDD, `team-practices.md`).

## U4 — u4-access-control

- **Descripción:** inicio de sesión con Gmail u Outlook y verificación de la sesión en el servicio.
- **Límites:** gestiona identidad y sesión; no conoce las reglas de generación.
- **Responsabilidades:** iniciar y cerrar la sesión y verificar la sesión en cada solicitud de generación (FR6.1; ADR-006).
- **Componentes:** AccessControl.
- **Notas:** la regla de qué cuentas pueden entrar sigue abierta (`requirements.md`).

## U5 — u5-web-app

- **Descripción:** las pantallas de acceso y principal con todos sus estados.
- **Límites:** muestra y valida en pantalla; no arma el Markdown (ADR-005) ni decide la identidad.
- **Responsabilidades:** pantallas S1 y S2 con sus estados (`mockups.md`), validación de entrada en pantalla (FR1), pestañas, botón de copiar, mensajes de carga y de error (FR4, FR5), accesibilidad WCAG 2.1 AA y móvil (NFR6, NFR7).
- **Componentes:** WebApp.
- **Notas:** usa MUI (Material Design) con tema claro y oscuro (`design-system-mapping.md`).

## U6 — u6-infrastructure

- **Descripción:** la infraestructura en AWS con Terraform y el despliegue automático a un único entorno al integrar en `main`.
- **Límites:** empaquetado y definición de infraestructura; no contiene lógica de la aplicación.
- **Responsabilidades:** los dos despliegues (interfaz y servicio), los permisos para llamar al modelo y para la configuración de los proveedores de identidad, el despliegue automático con linter y pruebas en CI, los pasos de retroceso y la prueba de humo posterior (`team-practices.md`, Deployment).
- **Componentes:** ninguno (empaquetado).
- **Notas:** las credenciales viven en un gestor de secretos o en permisos de la nube (NFR5); región us-east-1.

## Assumptions & Open Questions

- Supuesto: U1 contiene versiones mínimas de tres componentes; las unidades U2 a U5 las amplían sin reescribirlas. Si resultara que alguna unidad exige rehacer parte de U1, se revisa la decomposición.
- Abierto: qué prueba de punta a punta demuestra que U1 corre (la fija Delivery Planning).
- Abierto: la herramienta de CI/CD, necesaria para U6 (`team-practices.md` la deja pendiente).
- Abierto: regla de qué cuentas de Gmail u Outlook pueden entrar (afecta U4 y U6).
