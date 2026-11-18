# Unit Test Instructions — u5-web-app

Estrategia de pruebas: Standard (5 a 8 pruebas por componente, más pruebas de integración de los límites clave). Metodología: TDD; cada prueba se escribe antes del código, se ejecuta en rojo y luego se implementa lo mínimo para que pase.

## Requisitos previos

- Node.js 20 o superior y las dependencias de la pantalla instaladas con `cd web && npm ci` (incluyen `oidc-client-ts`, `react-markdown` y `vitest-axe` una vez que el plan las agrega).
- Sin credenciales de AWS, sin acceso a Cognito y sin el servicio: las pruebas simulan `fetch`, la biblioteca de inicio de sesión, el portapapeles y el reloj.

## Configuración de las herramientas

| Parte | Herramienta | Configuración |
|-------|-------------|---------------|
| Pantalla | Vitest, Testing Library y `vitest-axe` | `web/vite.config.ts` (umbral de 80 % de líneas) |
| Pantalla | ESLint y Prettier | `web/eslint.config.js` y los scripts de `web/package.json` (ya existen) |

## Comandos para ejecutar las pruebas de ESTA unidad

Las pruebas de u5 están en `web/src/__tests__/` y junto a cada módulo nuevo; el comando corre todas las de la pantalla:

```bash
cd web && npx vitest run
```

Ninguno es un comando general del proyecto: el servicio tiene su propio comando y no cambia en esta unidad.

## Cobertura

- **Piso:** 80 % de cobertura de líneas (`team.md`, `mvp`) sobre `web/`. Lo comprueba Build and Test; una ejecución con el umbral puede fallar por el umbral aunque todas las pruebas pasen, por eso va en un comando aparte, sin pasos después, y nunca se baja el umbral.

```bash
cd web && npm run coverage
```

- **Objetivo de esta unidad:** 80 % o más en los archivos nuevos de la pantalla.

## Otras comprobaciones de la pantalla (manuales y de CI)

```bash
cd web && npm run format:check && npm run lint && npm run build && npm run check:bundle && npm run check:secrets && npm run check:inline && npm audit --omit=dev --audit-level=high
```

## Comando de punta a punta del proyecto (manual, ya aprobado)

```bash
cd backend && python -m pytest tests -q && python -m story_service.local_run --local "Recuperar contraseña"
```

No ejercita la pantalla. La verificación real de la pantalla con Cognito, Google y Microsoft solo es posible cuando `u6-infrastructure` cree el grupo de usuarios y la distribución y la persona entregue las credenciales de las federaciones.

## Dobles de prueba (mocking)

- `fetch` simulado con respuestas válidas, de cada código de error, cuerpos no JSON, respuestas tardías y red caída.
- La biblioteca de inicio de sesión simulada: retorno válido, con `state` distinto, con `error`, con cancelación y cierre.
- Reloj simulado para los 60 s, el vencimiento del token y el bloqueo de 30 s del límite de tasa; portapapeles simulado que acepta o rechaza.
- Nunca se llama a Cognito, a AWS ni al servicio.

## Datos de prueba

- Títulos inventados de 0, 1, 12, 200 y 201 caracteres, con espacios, emojis y caracteres especiales; un Markdown de prueba con el formato de la historia y otro con etiquetas de script, controladores de evento, enlaces `javascript:` e imágenes remotas.
- Todo vive dentro de los archivos de prueba; no hay datos guardados.

## Pruebas que no corren en esta etapa

- El inicio de sesión real con Google o Microsoft y el cierre de sesión de Cognito.
- La revisión de desbordamiento horizontal (360, 768 y 1920 píxeles) y de contraste de los dos temas, y el lector de pantalla: manuales en Build and Test.
- La cabecera de política de contenido y el despliegue: son de `u6-infrastructure`.
