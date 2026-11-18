# Performance Requirements — u5-web-app

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. Respuestas: `nfr-requirements-questions.md` (Q1 a Q3).

## Sources

- [Q2] Presupuesto de carga de 400 KB de JavaScript comprimido.
- [Q3] Chrome y Edge (últimas dos versiones) en escritorio y Chrome en Android.
- [scope] `requirements.md` NFR1, NFR3 y NFR7; `contract-summary.md` (cadena de plazos 55, 57, 58 y 60 s).

## Requisitos

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR1.1 | La pantalla corta la espera a los 60 segundos y muestra el error de BR5.4; no hay reintentos automáticos: cada clic envía una sola solicitud | Prueba con reloj simulado: a los 60 s se aborta y aparece el mensaje; con un fallo no se envía una segunda solicitud sin un clic | NFR1; `rules.md` BR5.2 y BR5.4 |
| NFR1.2 | Al pulsar "Generar historia" con un título válido, el estado de carga con texto aparece en el mismo ciclo de renderizado del clic, antes de que se resuelva la llamada al servicio, y no hay otra espera propia de la pantalla | Prueba con cliente de servicio simulado que no responde nunca: justo después del clic el indicador está en pantalla y el botón desactivado (sin esperar temporizadores) | NFR1 (la meta de 60 s es del servicio) |
| NFR1.3 | El JavaScript de la carga inicial no supera 400 KB comprimidos (gzip); la carga inicial son los archivos JavaScript que `index.html` referencia y sus `modulepreload`, y la biblioteca de Markdown y su vista previa se cargan solo al mostrar un resultado | Un script local `npm run check:bundle` (corre sin CI) recorre las referencias de `dist/index.html` tras `vite build`, suma el tamaño gzip y falla por encima de 400 KB o si el paquete de la vista previa está en la carga inicial; el CI de u6 lo ejecuta después | Q2 |
| NFR3.1 | El hospedaje de la pantalla es estático y no consulta al servicio por su cuenta: solo hay llamadas por acción de la persona (generar, cerrar sesión y comprobar sesión al volver del acceso); al volver del acceso las únicas solicitudes permitidas son las de la biblioteca de inicio de sesión (intercambio de código en el punto de token de Cognito) y GET /v1/session | Prueba: sin acción de la persona no se hace ninguna solicitud de red; al volver del acceso las solicitudes son exactamente esas | NFR3 (5 personas, uso ocasional) |
| NFR7.1 | Los botones y campos interactivos tienen un tamaño táctil de al menos 44 por 44 píxeles definido en el tema de MUI (`minHeight` y `minWidth`) y la interfaz se usa sin desplazamiento horizontal de 360 a 1920 píxeles de ancho | Automática: una prueba de componentes comprueba que el tema define `minHeight` y `minWidth` de 44 px para los botones y que los botones de móvil usan ancho completo. Diferida (no automática): jsdom no calcula diseño, por lo que el desbordamiento a 360, 768 y 1920 píxeles se revisa a mano en Chrome y Edge en Build and Test | NFR7; `rules.md` BR5.9 |
| NFR7.2 | Se prueban y se soportan las últimas dos versiones estables de Chrome y Edge en escritorio y Chrome en Android; no se promete compatibilidad con otros navegadores | La lista de navegadores queda en `browserslist` del proyecto y en la documentación de prueba; la revisión manual de Build and Test usa esos navegadores | Q3 |

## Assumptions & Open Questions

- Supuesto: Firefox y Safari pueden funcionar, pero no se prueban ni se corrigen en el MVP (decisión de Q3).
- Supuesto: la meta de 60 s del resultado (NFR1) depende del servicio; la pantalla solo garantiza el corte y el aviso.
- Abierto: la medición del presupuesto de 400 KB se hace con el resultado de `vite build` en CI, que se define en la etapa de CI de `u6-infrastructure`.
