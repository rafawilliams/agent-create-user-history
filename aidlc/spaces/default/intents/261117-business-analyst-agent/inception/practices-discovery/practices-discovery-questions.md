# Practices Discovery — Preguntas

## Q1. [Entrega] ¿Cómo integran los cambios en la rama principal?

Contexto: el repositorio solo tiene 2 commits lineales, sin PRs, así que no se puede deducir la práctica. La rama de integración propuesta es `main`.

- A. Ramas cortas por cambio que se integran a `main` con squash-merge, sin revisión obligatoria
- B. Ramas cortas por cambio que se integran a `main` con squash-merge, con una revisión de código antes de integrar
- C. Se trabaja directamente sobre `main`
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q2. [Entrega] ¿Construir primero un corte delgado de punta a punta? Un esqueleto ambulante es una versión mínima que corre de principio a fin, construida primero para probar que las piezas se conectan antes de las funciones reales.

Contexto: aquí el corte sería una pantalla mínima, el servicio en AWS y una llamada al modelo de IA que devuelva una historia.

- A. Sí, construir el corte delgado primero
- B. No, construir las funciones directamente
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Entrega] ¿Cómo se despliega el MVP en AWS?

Contexto: hoy no hay CI/CD ni entornos desplegados; el script actual corre en local.

- A. Despliegue automático a un entorno de prueba (staging) al integrar en `main`, y a producción con una aprobación manual aparte
- B. Un solo entorno por ahora, con despliegue manual
- C. Despliegue automático a un único entorno al integrar en `main`
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q4. [Entrega] ¿Con qué herramienta se define la infraestructura en AWS?

Contexto: define cómo se describen y despliegan la API, la función y los permisos. El equipo tiene experiencia principalmente en Python.

- A. AWS CDK
- B. AWS SAM
- C. Terraform
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q5. [Calidad] ¿Cuándo se escriben las pruebas respecto del código?

Contexto: hoy no hay pruebas. La práctica por defecto es escribirlas después de implementar cada capa.

- A. Después de implementar cada capa (test-after)
- B. Antes del código, escribiendo primero cada prueba (TDD)
- C. Escenarios Gherkin primero, y pruebas unitarias después de implementar (mixto)
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q6. [Calidad] ¿Qué cobertura de pruebas se exige antes de integrar?

Contexto: para el alcance `mvp` la práctica por defecto es un mínimo de 80 % de cobertura de líneas, ejecutado en CI antes de integrar. Hoy no hay configuración de cobertura ni CI.

- A. Mínimo de 80 % de cobertura de líneas y ejecución en CI antes de integrar
- B. Otro porcentaje o criterio (indícalo en Other)
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q7. [Desarrollo] ¿Qué formateadores y linters se usan?

Contexto: hoy no hay ninguno configurado. La propuesta usa Black y Ruff para Python y Prettier y ESLint para JavaScript y TypeScript.

- A. Esos cuatro, y el linter en CI bloquea la integración si falla
- B. Esos cuatro, pero el linter solo avisa y no bloquea
- C. Ninguno por ahora
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q8. [Desarrollo] ¿En qué idioma se nombran las funciones y variables del código nuevo?

Contexto: el código existente usa nombres descriptivos en español.

- A. En español, como el código actual
- B. En inglés
- C. En inglés en el código, y en español en los textos que ve el usuario
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
