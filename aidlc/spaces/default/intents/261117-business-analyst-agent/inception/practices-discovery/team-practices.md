# Prácticas del equipo

> Prácticas afirmadas por la persona en la entrevista de descubrimiento (Q1-Q8). Lo que sigue sin resolver se marca explícitamente como pendiente.

## Way of Working

- **Integration branch**: main
- **Estrategia de ramas**: ramas cortas por cambio, integradas en `main` mediante squash-merge. Para los worktrees de Construcción, base `main` y destino `main`.
- **Revisión de código**: toda integración en `main` pasa por una revisión de código antes de fusionarse.
- **Convención de commits**: sin convención afirmada (la entrevista no la cubrió). Pendiente.

## Walking Skeleton

- Se construye primero un corte delgado de extremo a extremo (esqueleto ambulante) antes de ampliar el resto del trabajo.
- Primer corte integrado mínimo de referencia: pantalla React mínima, API Gateway, una Lambda y una llamada a Amazon Bedrock que devuelva una historia de usuario de extremo a extremo.
- Pendiente: la persona aún no ha respondido si Construcción debe continuar automáticamente o revisar cada punto de control; esa decisión no se presupone aquí.

## Testing Posture

- **Methodology**: tdd
- **Methodology evidence**: La persona afirmó TDD en la entrevista (Q5): cada prueba se escribe antes del código. El repositorio no tiene pruebas hoy (`code-quality-assessment.md`: presencia de pruebas `poor`), así que no hay práctica previa que contradiga la elección.
- **Ordering**: Escribir cada prueba antes del código que la satisface, ejecutarla en rojo y luego implementar lo mínimo para que pase.
- **Cobertura y ejecución**: mínimo 80 % de cobertura de líneas, y las pruebas se ejecutan en CI antes de integrar.
- **Herramientas de prueba**: no afirmadas (pytest y la herramienta estándar de React/TypeScript siguen como sugerencia, a decidir en el diseño). Pendiente.
- **Pruebas existentes**: ninguna que deba mantenerse verde; `generador_historias.py` no tiene pruebas.

## Deployment

- Despliegue automático a un único entorno al integrar en `main`.
- Herramienta de infraestructura como código: Terraform para la infraestructura de AWS.
- Objetivo del trabajo nuevo (contexto): React + API Gateway + Lambda + Amazon Bedrock en AWS.
- Retroceso y verificación: todo despliegue documenta pasos de rollback y una prueba de humo posterior (guardarraíl de `phases/operation.md`).
- Secretos: `.env` local ignorado por git; en AWS, IAM y un gestor de secretos, nunca credenciales en el código.
- Pendiente: herramienta de CI/CD y política de aprobación para un futuro entorno de producción (con un solo entorno no se definió).

## Code Style

- Formateadores y linters: Black y Ruff para Python; Prettier y ESLint para JS/TS.
- El linter se ejecuta en CI y su fallo bloquea la integración.
- Idioma de identificadores: los nombres de funciones y variables del código nuevo van en inglés (el código existente usa español y no se renombra por esta regla).
- Pendiente: fijar versiones de dependencias (`requirements.txt` hoy sin versiones); no se discutió en la entrevista.
