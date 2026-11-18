# Functional Design — u4-access-control — Preguntas

Contexto: u4 reemplaza el verificador de sesión simulado de u1 por una verificación real, y permite iniciar y cerrar sesión con Gmail u Outlook (US6.1: AC6.1.1 a AC6.1.3; contratos C2 y C3). Hoy, el servicio desplegado rechaza toda solicitud porque no hay verificador real. Estas preguntas cierran la regla de quién entra y cómo se verifica.

## Q1. [Arquitectura] ¿Con qué mecanismo se inicia sesión con Gmail y Outlook?

Contexto: el servicio no guarda datos (sin base de datos) y el equipo usa AWS. Cognito es el servicio de identidad de AWS y puede federar con Google y Microsoft.

- A. Amazon Cognito (un grupo de usuarios con Google y Microsoft como proveedores); el servicio verifica la firma y la vigencia del token que emite Cognito
- B. Un flujo de inicio de sesión propio en la función, con un token de sesión firmado por el servicio
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Producto] ¿Qué cuentas pueden entrar? (regla abierta desde `requirements.md`)

Contexto: cada generación cuesta una llamada al modelo y el MVP es para hasta 5 personas. Sin persistencia, la lista permitida vive en configuración.

- A. Solo una lista de correos permitidos (unas 5 personas) que se mantiene en la configuración del despliegue; cualquier otra cuenta ve un mensaje de acceso no autorizado
- B. Cualquier cuenta de Gmail u Outlook
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Operaciones] ¿Cuánto dura una sesión?

Contexto: pasado ese tiempo, el servicio responde SESSION_INVALID y la persona vuelve a iniciar sesión. Una generación en curso no se corta.

- A. 8 horas, luego se inicia sesión de nuevo
- B. 1 hora con renovación silenciosa mientras se use la pantalla
- C. 24 horas
- D. Not yet defined
- X. Other (please specify)

[Answer]: A
