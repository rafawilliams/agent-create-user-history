# Performance Design — u5-web-app

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: las decisiones de rendimiento quedaron fijadas por Q2 (presupuesto de 400 KB) y Q3 (navegadores) de NFR Requirements.

## Sources

- [Q2] 400 KB de JavaScript comprimido en la carga inicial. [Q3] Chrome y Edge.
- [scope] `performance-requirements.md` NFR1.1 a NFR1.3, NFR3.1, NFR7.1 y NFR7.2.

- [scope] `scalability-requirements`, `reliability-requirements` y `observability-requirements`: no se producen para una unidad de tipo ui (solo rendimiento, seguridad y pila tecnológica); la capacidad (NFR3), la disponibilidad y los registros del servicio son de u1 y u6, y la pantalla no tiene diseño propio de escalado, resiliencia ni observabilidad más allá de lo anotado aquí.

## Diseño

| Tema | Decisión | Requisitos |
|------|----------|------------|
| Corte de espera | Un único temporizador de 60 s con `AbortController` en el cliente de C1; al vencer se aborta, se descarta cualquier respuesta tardía y se pasa a failed. No hay reintento automático: el cliente no tiene bucle de reintento y el botón "Reintentar" necesita un clic | NFR1.1 |
| Indicador de carga | El estado `generating` se fija de forma síncrona en el manejador del clic, antes de llamar al cliente, y desactiva botón y campos en el mismo renderizado; no depende de un temporizador ni de la respuesta | NFR1.2 |
| Un solo envío | Un indicador en una referencia (no en el estado) impide que dos clics seguidos en el mismo ciclo envíen dos solicitudes. Se activa al empezar y se libera en un `finally` al terminar la solicitud (éxito, fallo o abortada); el temporizador de 60 s y el `AbortController` se crean por solicitud y se limpian en el mismo `finally`; una respuesta que llega después de abortar, o con la sesión ya vencida, se compara con el número de solicitud vigente y se descarta | NFR1.2 |
| Carga diferida | Solo la vista previa con `react-markdown` se importa con `React.lazy` y se muestra con `Suspense` (con el texto de carga "Cargando vista previa") dentro de la pestaña "Vista previa"; las pestañas, la vista de Markdown y el botón de copiar son parte de la carga inicial y no dependen de ese paquete. Una barrera de errores rodea la vista previa: si la importación falla se muestra el aviso "No se pudo cargar la vista previa. Usa la pestaña Markdown." y un botón para reintentar la importación (se vuelve a crear la importación diferida, porque la promesa rechazada queda en caché) | NFR1.3 |
| Partición del paquete | Vite separa en grupos propios React, MUI y `oidc-client-ts` para aprovechar el caché del navegador; el grupo de la vista previa nunca se importa de forma estática | NFR1.3 |
| Medición | `npm run check:bundle` lee `dist/index.html`, sigue los `script` y `modulepreload` referenciados, suma el tamaño gzip y falla por encima de 400 KB o si el grupo de la vista previa (`react-markdown`) aparece entre los archivos de la carga inicial; con el cambio de alcance de la carga diferida, la carga inicial incluye ya las pestañas y el botón de copiar | NFR1.3 |
| Sin llamadas propias | No hay sondeos ni renovación automática: las únicas solicitudes son generar (C1), comprobar sesión al volver del acceso (C2, GET), cerrar sesión (C2, DELETE) y las de la biblioteca de inicio de sesión al volver del acceso (intercambio de código) | NFR3.1 |
| Tamaño táctil y ancho | El tema de MUI define `minHeight` y `minWidth` de 44 px para botones y campos; en móvil los botones usan ancho completo mediante los puntos de corte por defecto | NFR7.1 |
| Navegadores | `browserslist` con las dos últimas versiones de Chrome y Edge y Chrome en Android; Vite compila a ese destino | NFR7.2 |

## Presupuestos

| Recurso | Presupuesto | Cómo se comprueba |
|---------|-------------|-------------------|
| JavaScript de la carga inicial | 400 KB gzip | `check:bundle` |
| Espera máxima por generación | 60 s | Prueba con reloj simulado |
| Aparición del indicador de carga | Mismo ciclo de renderizado del clic | Prueba con cliente que nunca responde |

## Assumptions & Open Questions

- Supuesto: el paquete actual pesa unos 108 KB gzip sin `oidc-client-ts` ni `react-markdown`, por lo que el presupuesto de 400 KB deja margen.
- Abierto: el desbordamiento horizontal a 360, 768 y 1920 píxeles se revisa a mano en Build and Test (jsdom no calcula diseño).
