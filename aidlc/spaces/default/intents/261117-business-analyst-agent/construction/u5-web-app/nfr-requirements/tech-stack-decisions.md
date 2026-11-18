# Tech Stack Decisions — u5-web-app

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (Q1 a Q3).

## Sources

- [Q1] oidc-client-ts para el inicio de sesión. [Q2] Presupuesto de 400 KB y carga diferida de la vista previa. [Q3] Chrome y Edge.
- [scope] `team.md` (React, TypeScript, Prettier, ESLint, TDD, 80 %); diseño funcional de u5 (Q2 de diseño: biblioteca de Markdown sin HTML en bruto).

## Decisiones

| Tema | Decisión | Razón |
|------|----------|-------|
| Base | React 18, TypeScript, Vite, MUI 6 y Vitest con Testing Library (ya presentes desde u1) | Se mantiene lo que u1 dejó funcionando y probado |
| Inicio de sesión | `oidc-client-ts` con flujo de código, PKCE (S256), `response_type=code`, alcance `openid email`, `loadUserInfo` desactivado, `automaticSilentRenew` desactivado, `userStore` en memoria (`WebStorageStateStore` sobre `InMemoryWebStorage`), `stateStore` en sessionStorage solo durante la redirección, metadatos explícitos de Cognito y cierre en `/logout` con `logout_uri` exacto (NFR5.5); versión exacta | Q1: evita implementar a mano PKCE, `state` y el intercambio de código; se audita con `npm audit` (NFR5.3) |
| Vista previa | `react-markdown` sin plugin de HTML en bruto, con transformación de URL restringida a `http`, `https` y `mailto`, imágenes desactivadas, cargada con `React.lazy`; versión exacta | Q2 de diseño y NFR4.3; Q2 de presupuesto para la carga diferida |
| Pruebas de accesibilidad | `vitest-axe` en las pruebas de componentes, además de las pruebas de teclado y de roles | NFR6.1 |
| Cobertura | Vitest con `@vitest/coverage-v8` y umbral de 80 % de líneas en `vitest.config`/`vite.config.ts`, ejecutado en CI | NFR8.1 |
| Formato y análisis | Prettier y ESLint ya configurados; `tsc --noEmit` en la compilación | NFR8.2 |
| Navegadores | `browserslist` con las dos últimas versiones de Chrome y Edge y Chrome en Android | NFR7.2 |

## Requisitos de calidad de la implementación

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR6.1 | La pantalla cumple WCAG 2.1 AA y se usa solo con teclado: roles, etiquetas, orden de foco, foco al error y al contexto, regiones de estado y `role="alert"` según `accessibility-checklist.md`; los errores llevan icono y texto | Pruebas de componentes con `vitest-axe` sin violaciones en S1, S2 vacío, cargando, error, contexto y resultado; pruebas de teclado de las pestañas y de los botones; la revisión con lector de pantalla queda para Build and Test | NFR6; `rules.md` BR5.9 |
| NFR6.2 | Los dos temas (claro y oscuro) mantienen un contraste de 4.5:1 en el texto con la paleta por defecto de MUI | Revisión manual en Build and Test (la herramienta de pruebas no calcula contraste en jsdom); queda como verificación diferida | NFR6; `design-system-mapping.md` |
| NFR8.1 | El código se escribe con TDD y la cobertura de líneas de `web/` es de al menos 80 %, con un umbral que hace fallar `npm run coverage` | `npm run coverage` falla por debajo de 80 % y se ejecuta en CI antes de integrar | NFR8 |
| NFR8.2 | Prettier, ESLint y `tsc --noEmit` pasan sin errores; los identificadores van en inglés y el texto visible en español | `npm run lint`, `npm run format:check` y `npm run build` limpios | NFR8; `team.md` |

## Assumptions & Open Questions

- Supuesto: las versiones exactas de `oidc-client-ts` y `react-markdown` se eligen en Code Generation con las vigentes y probadas con `npm audit`.
- Abierto: el contraste de los dos temas (NFR6.2) se comprueba a mano en Build and Test.
