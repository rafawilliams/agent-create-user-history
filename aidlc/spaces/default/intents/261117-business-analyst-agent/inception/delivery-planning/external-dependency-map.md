# External Dependency Map — Business Analyst Agent

Documentos de entrada: `requirements.md`, `unit-of-work.md`, `unit-of-work-dependency.md`, `contract-summary.md` y `team-practices.md`. Secuencia: `bolt-plan.md`. Respuestas: `delivery-planning-questions.md` (DP Qn).

Una **Bolt** es una pasada de construcción sobre una parte del trabajo que termina en algo que corre. Una dependencia externa es algo que está fuera del control del trabajo de construcción (una cuenta, un permiso, un registro en un tercero) y que puede frenar una Bolt.

| # | Dependencia externa | Dueño | Plazo | Bolts que bloquea | Si se retrasa |
|---|---------------------|-------|-------|-------------------|---------------|
| E1 | Acceso al modelo en Amazon Bedrock, en la cuenta de AWS de us-east-1 | La persona | Ya habilitado (DP Q5) | B1, B3 | Evaluar con el modelo simulado de U1 mientras se habilita; no se puede cerrar B1 sin una llamada real |
| E2 | Registro de la aplicación en Google y en Microsoft para el inicio de sesión | La persona (DP Q6) | Pocos días (DP Q6) | B6; la prueba completa de B5 | Construir B6 con cuentas de prueba o con el verificador simulado y cerrar B6 cuando llegue el registro |
| E3 | Herramienta de CI/CD para el despliegue automático | Sin dueño definido (`team-practices.md`, pendiente) | Sin definir | B2 | Desplegar a mano en B2 y automatizar cuando se elija la herramienta |
| E4 | Límite de tiempo del servicio HTTP en AWS frente a los 60 segundos del MVP | Se confirma en B2 | Se conoce al construir B2 | B2, B4 | Reducir el máximo de la generación o elegir otro mecanismo; implica cambiar el contrato C1 |

## Notas

- E1: en Feasibility la cuenta figuraba sin el modelo habilitado (`feasibility-questions.md`, Q10; `raid-log.md`, I1); en esta etapa la persona indicó que ya está habilitado (DP Q5), por lo que ese problema abierto queda resuelto. Conviene confirmarlo con una llamada real en B1.
- E2: el control de acceso (B6) va al final de la secuencia, lo que da margen para que el registro esté listo.
- E3: la herramienta de CI/CD sigue sin elegirse; sin ella, el despliegue automático de B2 no se puede completar.
- E4: es una restricción del servicio de AWS que no está en los artefactos; se registra como riesgo para verificarlo en B2.

## Assumptions & Open Questions

- Supuesto: E1 ya está habilitado, según la respuesta de la persona; no se ha comprobado con una llamada.
- Abierto: dueño y plazo de E3.
- Abierto: valor real del límite de tiempo de E4.
