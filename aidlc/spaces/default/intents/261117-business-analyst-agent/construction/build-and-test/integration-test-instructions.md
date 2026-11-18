# Instrucciones de pruebas de integración — Build and Test (estrategia Standard)

Las pruebas de integración de este proyecto son las pruebas de límite entre unidades que ya existen dentro de las suites completas. No se agregó ninguna prueba nueva en esta etapa. Se ejecutan como subconjunto con nombre y no se cuentan dos veces en los totales (`test-results.md`).

## Configuración y ejecución

| Parte | Comando | Resultado de esta etapa |
|-------|---------|-------------------------|
| Servicio | `cd backend && python -m pytest tests/test_composition.py tests/test_access_control.py tests/test_story_generation.py -q` | 69 passed, código de salida 0 |
| Pantalla | `cd web && npx vitest run src/__tests__/bootstrap.test.tsx src/__tests__/screens.test.tsx` | 38 passed (3 + 35), código de salida 0 |

Para ver el detalle por prueba, añadir `-v` (pytest) o `--reporter=verbose` (Vitest). Para filtrar una prueba: `-k "<texto>"` o `-t "<texto>"`.

Datos de prueba: modelos simulados (`FakeModelClient`), un servidor de claves simulado y pares de claves RSA generados dentro de las pruebas (`tests/auth_helpers.py`), y un cliente del servicio y una biblioteca de inicio de sesión simulados en la pantalla. Ninguna prueba llama a AWS, a Cognito ni a un modelo.

Objetivo de cobertura: el piso de 80 % de líneas se mide con la suite completa (no con este subconjunto): 99,68 % en el servicio y 98,4 % en la pantalla.

## Límites entre unidades cubiertos

| Límite | Prueba(s) que lo ejercitan | Qué demuestran | Dónde corre |
|--------|----------------------------|----------------|-------------|
| Manejador ↔ servicio ↔ puerto del modelo (u1, u3, u2) | `test_story_generation.py` (servicio completo con modelo simulado: título, contexto, JSON, Markdown, tiempos, un solo reintento, códigos de error) | El servicio llama al puerto `ModelClient` con el plazo restante, interpreta el JSON y arma el Markdown; cada tipo de error del modelo da el código de C1 | Node/pytest, sin red |
| Servicio ↔ verificador de tokens de Cognito (u1, u4) | `test_access_control.py` (verificador real con claves RSA de prueba, lista de correos, 401 idéntico para cada motivo, 403 para cuenta no permitida, registros sin token ni correo) | La composición enlaza el verificador real con la configuración de Cognito y falla cerrado sin ella | pytest, sin red (servidor de claves simulado) |
| Composición del verificador por entorno (u1, u4) | `test_composition.py` | El verificador simulado solo se enlaza con `APP_ENV` local o test y bandera explícita; en los demás casos se falla cerrado | pytest |
| Cliente web ↔ contratos C1 y C2 (u5 ↔ u1, u3, u4) | `screens.test.tsx` (flujo S1/S2 completo con el cliente del servicio simulado: errores por código, corte de 60 s, `RATE_LIMITED`, sesión vencida, copia temporal, cierre de sesión) y `bootstrap.test.tsx` (arranque con la configuración pública) | La pantalla mapea cada código de C1 a su mensaje y reacciona a `SESSION_INVALID` y `ACCOUNT_NOT_ALLOWED` | **jsdom (emulador de DOM) en Node: es evidencia de integración, no de navegador real** |

## Límites que se revisaron leyendo el código (solo lectura)

Estos límites no los cubre una prueba automática que mezcle ambas unidades; se compararon a mano y se registran en `build-and-test-summary.md` (filas `X1` a `X10`, más `X7b`):

| Límite | Resultado |
|--------|-----------|
| Variables de entorno que fija Terraform ↔ las que lee el servicio | coinciden (8 nombres); además `app.tftest.hcl::function_environment_has_the_identity_settings_and_no_simulated_session` pasa |
| CORS de la pasarela (`infra/main.tf`) ↔ CORS del manejador | coinciden: `GET,POST,DELETE,OPTIONS` y `Authorization,Content-Type` |
| Códigos de error de C1 ↔ tabla de la pantalla | los 10 códigos se tratan; uno desconocido cae en el fallo genérico |
| Nombres de proveedor `Google` y `Microsoft` (Cognito) ↔ verificador | coinciden (se compara sin distinguir mayúsculas) |
| Variables `VITE_` ↔ configuración de la pantalla ↔ `deploy.yml` | coinciden (5 nombres) |
| Política de contenido `connect-src` ↔ llamadas reales de la pantalla | cubre el origen del servicio, el dominio de Cognito y `cognito-idp` |
| Empaquetado de la función ↔ dependencias del servicio | Coincide tras el regreso 1: el paquete real incluye `jwt` y `cryptography` (X7 `Met`; `terraform test` `package.tftest.hcl` y `test_real_package.py`). El arranque real en Lambda queda `Unverified` (X7b) |

## Qué falta para una integración real (fuera de esta etapa)

Con una cuenta de AWS desplegada: inicio de sesión real con Cognito, Google y Microsoft; una llamada real al modelo de Bedrock; cabeceras servidas por CloudFront; `OPTIONS` y `POST /v1/stories` sin token contra la pasarela (`infra/scripts/smoke_test.sh`); cinco solicitudes simultáneas y el límite de la pasarela. Todo eso figura como `Unverified` en el resumen, con la acción que debe hacer la persona.
