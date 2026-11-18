# Evidencia de descubrimiento de prácticas (borrador inicial)

## Qué se inspeccionó

- Artefactos de ingeniería inversa en `aidlc/spaces/default/codekb/agent-ha-devops/`: `code-quality-assessment.md` y `technology-stack.md` (leídos completos); el resto existe (`architecture.md`, `business-overview.md`, `dependencies.md`, `code-structure.md`, etc.) y no se consultó para estas prácticas.
- Historial git (solo lectura): `git log --oneline -20` (2 commits: `f746b07` y `d1e2029`), `git branch -a` (`main`, `fix/gitignore-salida-typo` y sus equivalentes en `origin`), `git rev-parse HEAD` (`d1e20291ee1e2be333c2ed51ac8886e40be3d863`), `git ls-files`.
- Archivos versionados: `.env.example`, `.gitignore`, `README.md`, `entrada_ejemplo.xlsx`, `generador_historias.py`, `requirements.txt`, `salida_ejemplo.xlsx`.
- No se leyó `.env`, ni `.venv/`, `.claude/` o el espacio de trabajo `aidlc/` más allá de lo indicado.

## Qué se infirió

- Con solo 2 commits, no hay estrategia de ramas ni de revisión demostrable; `main` es la rama principal y existe una rama corta de corrección, lo que sugiere trabajo por ramas cortas, pero es un indicio débil.
- No existe CI/CD, IaC, contenedores, linter, formateador, pruebas ni cobertura: todas las secciones de práctica técnica salen como PROPUESTA basada en los defaults de `org.md`.
- Mensajes de commit sin convención común (inglés con `Fix`, español sin prefijo).
- `.env` ignorado por git y `.env.example` versionado: única práctica de secretos observable.

## Incertidumbre sin resolver (para la entrevista)

1. Rama de integración y estrategia de ramas (¿trunk-based con squash o flujo con PR y revisión?).
2. Metodología de pruebas (tdd, bdd, atdd o test-after), herramientas y piso de cobertura.
3. Entornos del MVP (¿staging y producción, o uno solo?), herramienta de IaC y de CI/CD, política de aprobación de producción.
4. Esqueleto ambulante: si se aplica y la política de autonomía de Construcción.
5. Estilo de código: formateadores/linters y el idioma de identificadores del código nuevo.
6. Convención de mensajes de commit y fijación de versiones de dependencias.
7. Restricciones duras (ALWAYS/NEVER) que el equipo quiera imponer: ninguna declarada hasta ahora.

## Decisiones de la entrevista

Respuestas confirmadas por la persona (Q1-Q8):

| Pregunta | Respuesta elegida |
|---|---|
| Q1 Estrategia de ramas y revisión | B: ramas cortas, squash-merge a `main`, revisión de código antes de fusionar |
| Q2 Esqueleto ambulante | A: construir primero un corte delgado de extremo a extremo |
| Q3 Despliegue | C: despliegue automático a un único entorno al integrar en `main` |
| Q4 Infraestructura como código | C: Terraform para la infraestructura de AWS |
| Q5 Metodología de pruebas | B: TDD (cada prueba antes del código) |
| Q6 Cobertura y CI | A: mínimo 80 % de cobertura de líneas y ejecución en CI antes de integrar |
| Q7 Formato y linters | A: Black + Ruff (Python), Prettier + ESLint (JS/TS); el linter en CI bloquea la integración |
| Q8 Idioma de identificadores | B: nombres de funciones y variables del código nuevo en inglés |

Incertidumbre que sigue sin resolver:

1. Autonomía de Construcción (continuar automáticamente o revisar cada punto de control): aún sin respuesta; no se presupone.
2. Convención de mensajes de commit: no cubierta por la entrevista.
3. Herramientas de prueba concretas y servicio de CI/CD: no decididos.
4. Política de aprobación de producción: no definida (un solo entorno).
5. Fijación de versiones de dependencias: no discutida.
6. Restricciones duras ALWAYS/NEVER: la persona no declaró ninguna.
