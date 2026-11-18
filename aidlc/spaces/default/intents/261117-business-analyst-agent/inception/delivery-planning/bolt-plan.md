# Bolt Plan — Business Analyst Agent

Documentos de entrada: `requirements.md`, `stories.md`, `mockups.md`, `components.md`, `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`, `contract-summary.md` y `team-practices.md`. Respuestas: `delivery-planning-questions.md` (DP Qn).

Una **Bolt** es una pasada de construcción sobre una parte del trabajo (una o más unidades) que termina en algo que corre. Una **unidad** es una pieza del trabajo de `unit-of-work.md` (U1 a U6). El **esqueleto ambulante** es la versión mínima que corre de principio a fin, construida primero para probar que las piezas se conectan antes de las funciones reales. **WSJF** es una puntuación de valor y urgencia frente al tamaño del trabajo (ver `risk-and-sequencing-rationale.md`).

Este plan guía el orden de entrega; el motor de construcción toma el orden real del mapa de dependencias de las unidades. Tamaño: una Bolt por unidad, 6 Bolts (DP Q1). Se construye una tras otra (DP Q4). Orden: esqueleto ambulante, infraestructura temprano y luego el modelo, la generación, la interfaz y el control de acceso (DP Q2).

## Secuencia de Bolts

| Orden | Bolt | Unidad | Esqueleto ambulante | Historias que cubre |
|-------|------|--------|---------------------|--------------------|
| 1 | B1 | U1 u1-walking-skeleton | Sí | parte de US2.1 |
| 2 | B2 | U6 u6-infrastructure | No | US6.1 y US7.1 (permisos) |
| 3 | B3 | U2 u2-model-gateway | No | US7.1, US5.1 (fallos del modelo) |
| 4 | B4 | U3 u3-story-generator | No | US1.1, US2.1, US3.1, US4.1, US5.1 |
| 5 | B5 | U5 u5-web-app | No | US1.1, US4.1, US5.1, US6.1 |
| 6 | B6 | U4 u4-access-control | No | US6.1 |

La secuencia respeta el mapa de dependencias: U2 a U6 dependen solo de U1, así que cualquier orden después de U1 es válido (`unit-of-work-dependency.md`). No hay desviación respecto del orden topológico.

## B1 — Esqueleto ambulante (U1 u1-walking-skeleton)

- **Unidades:** U1.
- **Esqueleto ambulante:** sí. Es la primera unidad en el orden de dependencias.
- **Definition of Done:** una pantalla mínima donde se escribe un título, un servicio mínimo y una llamada real al modelo en Amazon Bedrock que devuelve una historia en Markdown; las interfaces C3 y C4, el modelo simulado y el servicio simulado con la forma de C1, tal como pide `contract-summary.md` (Reglas de propiedad); pruebas que se escribieron antes del código (TDD) y pasan.
- **Confidence hypothesis:** si esto corre de punta a punta, las piezas se conectan y el acceso al modelo funciona en la cuenta (DP Q5 indicó que ya está habilitado). Falsa si la llamada a Bedrock falla o supera el límite de tiempo.
- **Demo esperada:** escribir "Recuperar contraseña" en la pantalla mínima y ver la historia en Markdown que devuelve el modelo.
- **Comprobación real de punta a punta:** una ejecución del esqueleto que llame al modelo de verdad. El comando concreto de verificación se propone al primer punto de control, porque el proyecto no tiene hoy ninguna prueba ni comando de verificación ejecutable (`code-quality-assessment.md`).

## B2 — Infraestructura (U6 u6-infrastructure)

- **Unidades:** U6.
- **Definition of Done:** infraestructura en AWS con Terraform para la interfaz y el servicio, permisos para llamar al modelo y para los proveedores de identidad, despliegue automático a un único entorno al integrar en `main`, linter y pruebas en CI, pasos de retroceso y una prueba de humo posterior (`team-practices.md`).
- **Confidence hypothesis:** el esqueleto ambulante se puede desplegar de forma repetible y el límite de tiempo del servicio permite los 60 segundos (riesgo que señaló la revisión de Contract Design). Falsa si el despliegue exige pasos manuales o el servicio corta antes de 60 segundos.
- **Demo esperada:** integrar un cambio en `main` y ver el esqueleto actualizado en el entorno de AWS.
- **Por qué temprano:** la persona eligió desplegar pronto (DP Q2).

## B3 — Acceso al modelo (U2 u2-model-gateway)

- **Unidades:** U2.
- **Definition of Done:** el acceso al modelo con soporte para Amazon Titan y Claude Sonnet y cambio por configuración; traducción de los fallos del modelo a errores propios; la evaluación de ambos modelos con títulos de ejemplo, con el resultado registrado y la decisión sobre cuál usar (US7.1).
- **Confidence hypothesis:** al menos uno de los dos modelos genera el Gherkin en español con la calidad que pide el MVP (80 % de Gherkin válido a la primera, revisado a mano). Falsa si ninguno llega a ese nivel.
- **Demo esperada:** una tabla comparativa de los dos modelos con los mismos títulos de ejemplo y la decisión.

## B4 — Generación (U3 u3-story-generator)

- **Unidades:** U3.
- **Definition of Done:** generación completa: reglas de entrada y de título ambiguo, armado de la petición con el prompt de configuración, interpretación de la respuesta y Markdown final con rol "analista de negocio" y 2 a 3 criterios en Gherkin en español, manejo de respuestas inválidas y del máximo de 60 segundos, sin registrar contenido.
- **Confidence hypothesis:** la historia generada cumple los criterios de aceptación de US1.1 a US5.1 con el modelo elegido en B3. Falsa si el resultado necesita edición manual frecuente.
- **Demo esperada:** generar historias para 5 títulos de ejemplo, incluido uno ambiguo y uno de más de 200 caracteres.

## B5 — Interfaz (U5 u5-web-app)

- **Unidades:** U5.
- **Definition of Done:** las pantallas de acceso y principal con todos sus estados (`mockups.md`), pestañas, copiado, mensajes de carga y de error, accesibilidad WCAG 2.1 AA, móvil y tema claro y oscuro.
- **Confidence hypothesis:** una persona puede completar el flujo de escribir el título y copiar el Markdown a Jira sin ayuda. Falsa si un analista necesita explicación para usarla.
- **Demo esperada:** el flujo completo desde la pantalla: título, resultado, copiar y pegar en Jira.

## B6 — Control de acceso (U4 u4-access-control)

- **Unidades:** U4.
- **Definition of Done:** inicio de sesión con Gmail u Outlook, cierre de sesión y verificación de la sesión en el servicio antes de generar.
- **Confidence hypothesis:** solo una persona con sesión válida puede generar historias, y el inicio de sesión funciona con las dos cuentas. Falsa si algún proveedor no completa el inicio de sesión o si el servicio genera sin sesión.
- **Demo esperada:** entrar con una cuenta de Gmail y otra de Outlook, generar una historia y cerrar la sesión; una llamada sin sesión es rechazada.

## Assumptions & Open Questions

- Supuesto: hasta B6 el servicio usa el verificador de sesión simulado de U1; eso significa que durante B1 a B5 el agente no exige inicio de sesión real. Para la demostración de dos semanas conviene que B6 esté lista; la secuencia elegida la deja al final (DP Q2).
- Hipótesis: 6 Bolts caben en dos semanas (SD Q11). Es una estimación sin base de capacidad medida; se revisa al terminar B1.
- Abierto: el comando de verificación de cada punto de control; se propone al primer punto de control.
- Abierto: la herramienta de CI/CD, necesaria para B2 (`team-practices.md`).
