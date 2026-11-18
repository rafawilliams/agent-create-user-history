# CI/CD Pipeline — u5-web-app

Documentos de entrada: `performance-design.md`, `security-design.md`, `infrastructure-specification.md` y la canalización de u1 (GitHub Actions, `.github/workflows/ci.yml`). No hubo preguntas en esta etapa.

## Qué agrega u5 al flujo de CI

El trabajo de la pantalla en `ci.yml` ejecuta, en orden y con `npm ci` desde el archivo de bloqueo (NFR5.3):

| Paso | Comando | Falla si |
|------|---------|----------|
| Formato | `npm run format:check` | Prettier encuentra diferencias |
| Análisis | `npm run lint` | ESLint reporta errores |
| Tipos y compilación | `npm run build` (`tsc --noEmit` y `vite build`) | Hay errores de tipos o de compilación |
| Pruebas y cobertura | `npm run coverage` | Falla una prueba o la cobertura de líneas es menor a 80 % (NFR8.1) |
| Presupuesto | `npm run check:bundle` | La carga inicial supera 400 KB gzip o incluye la vista previa (NFR1.3) |
| Auditoría | `npm audit --omit=dev --audit-level=high` | Hay hallazgos altos o críticos en producción (NFR5.3) |
| Secretos | `npm run check:secrets`: recorre `web/dist/` y falla si encuentra `AKIA[0-9A-Z]{16}`, `ASIA[0-9A-Z]{16}`, `aws_secret_access_key`, `client_secret` o una clave privada (`-----BEGIN`) | Aparece alguno (NFR5.1) |
| Scripts en línea | `npm run check:inline`: lee `web/dist/index.html` y falla si una etiqueta `<script>` no tiene `src` | Hay un `<script>` sin `src` (NFR5.4) |

Code Generation de u5 añade a `web/package.json` los scripts `check:bundle`, `check:secrets` y `check:inline` y el umbral de 80 % en la configuración de Vitest, y cambia `ci.yml` para invocarlos (hoy ejecuta `npx prettier`, `npx eslint` y `npx vitest` directamente, sin `npm run build`). En los pull requests el CI compila con valores ficticios y públicos de las variables `VITE_` (por ejemplo, `https://example.invalid`), porque Terraform no se aplica allí; la validación de configuración de la pantalla falla por variables ausentes, no por valores ficticios.

## Despliegue de la pantalla

El despliegue lo ejecuta la canalización de u6-infrastructure al integrar en `main`, después de `terraform apply` (que fija las variables `VITE_` desde las salidas de Terraform): compila la pantalla, sube los archivos con hash con caché larga, sube `index.html` con `no-cache` al final y crea una invalidación de `/index.html`. La prueba de humo consulta la raíz del sitio y comprueba que responde 200 con la cabecera de política de contenido exacta.

## Retroceso

El depósito tiene versionado activo: para volver atrás se despliega de nuevo la compilación del commit anterior (misma canalización) o se restauran las versiones previas de `index.html` y se invalida la caché. Los archivos con hash no se borran en el despliegue, por lo que una `index.html` anterior sigue encontrando sus archivos.

## Secretos y credenciales

La compilación de la pantalla no usa secretos. La canalización accede a AWS con la identidad federada de GitHub definida en u6; nunca con claves guardadas en el repositorio.

## Assumptions & Open Questions

- Supuesto: los pasos de CI de la pantalla se agregan a `ci.yml` en Code Generation de u5, y el despliegue en u6.
- Abierto: la política de limpieza de archivos antiguos del depósito queda después del MVP.
