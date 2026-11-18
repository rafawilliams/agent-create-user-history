# NFR Requirements — u5-web-app — Preguntas

Contexto: la interfaz ya tiene definido su comportamiento (`functional-spec.md`, `rules.md`) y hereda de los requisitos NFR1 (60 s), NFR3 (5 personas), NFR4 (privacidad), NFR5 (secretos), NFR6 (WCAG 2.1 AA), NFR7 (escritorio y móvil) y NFR8 (TDD, 80 %, formateadores). Quedan tres decisiones que fijan metas medibles o tecnología.

## Q1. [Tecnología] ¿Cómo implementa la pantalla el inicio de sesión con Cognito (código con PKCE)?

Contexto: BR5.10 exige verificador, estado, validación y limpieza de la dirección, con el token solo en memoria. Una biblioteca ahorra código propio pero agrega dependencias que se auditan (la seguridad del inicio de sesión depende de ellas).

- A. Código propio pequeño (unos pocos cientos de líneas) sobre el endpoint de Cognito, con pruebas escritas primero y sin dependencias nuevas
- B. Una biblioteca de OpenID Connect para navegador (por ejemplo oidc-client-ts), configurada para guardar el estado en memoria y sessionStorage solo durante la redirección
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q2. [Rendimiento] ¿Qué presupuesto de carga tiene la pantalla?

Contexto: con 5 personas y uso ocasional el rendimiento de carga importa poco, pero una cifra evita que MUI y la biblioteca de Markdown crezcan sin control. Se mide en CI con el resultado de `vite build`.

- A. Hasta 400 KB de JavaScript comprimido (gzip) en la carga inicial; la pantalla de acceso no carga la biblioteca de Markdown (se carga al mostrar un resultado)
- B. Hasta 250 KB de JavaScript comprimido en la carga inicial, con carga diferida de todo lo que no sea el acceso
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Compatibilidad] ¿Qué navegadores se prueban y soportan?

Contexto: NFR7 pide escritorio y móvil sin nombrar navegadores. El portapapeles asíncrono y PKCE (Web Crypto) requieren un contexto seguro (HTTPS).

- A. Las dos últimas versiones estables de Chrome, Edge, Firefox y Safari (escritorio), y Chrome en Android y Safari en iOS; sin soporte para Internet Explorer
- B. Solo las dos últimas versiones de Chrome y Edge (escritorio) y Chrome en Android
- C. Not yet defined
- X. Other (please specify)

[Answer]: B
