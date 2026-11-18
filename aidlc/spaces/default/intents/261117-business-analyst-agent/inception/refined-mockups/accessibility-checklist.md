# Accessibility Checklist — Business Analyst Agent

Documentos de entrada: `wireframes.md`, `user-flow.md`, `stories.md`, `requirements.md` y `team-practices.md`. Detalle por componente: `interaction-spec.md`.

Objetivo: WCAG 2.1 nivel AA y uso completo solo con teclado (NFR6 de `requirements.md`; `rough-mockups-questions.md`, Q7). Se aplica a los dos temas, claro y oscuro (`refined-mockups-questions.md`, Q2). Los puntos están sin marcar porque se verifican sobre la interfaz construida, en Construction.

## Perceptible

- [ ] El texto normal tiene contraste de al menos 4.5:1 y el texto grande de al menos 3:1, en tema claro y en tema oscuro.
- [ ] Los componentes de interfaz (bordes de campos, botones, iconos) tienen contraste de al menos 3:1.
- [ ] Ningún estado se indica solo con color: errores, avisos y confirmaciones llevan icono y texto (RF Q6, Q7).
- [ ] Todo icono con significado tiene texto alternativo; los decorativos se ocultan a los lectores de pantalla.
- [ ] El idioma de la página está declarado como español.

## Operable

- [ ] Todas las funciones se pueden usar solo con teclado: escribir el título, generar, cambiar de pestaña, copiar, reintentar, iniciar y cerrar sesión.
- [ ] El foco es visible en todos los elementos interactivos y sigue un orden lógico (encabezado, título, contexto, generar, pestañas, copiar).
- [ ] No hay trampas de teclado, incluido el menú del encabezado en móvil.
- [ ] Las pestañas se cambian con las flechas y Tab entra al panel.
- [ ] El tamaño táctil de botones y pestañas es de al menos 44 por 44 píxeles (NFR7).
- [ ] Ninguna acción tiene límite de tiempo, salvo el de 60 segundos de la generación, que muestra un error con "Reintentar" (FR5.2).

## Comprensible

- [ ] Todo campo tiene una etiqueta visible, no solo texto de ejemplo.
- [ ] Los mensajes de error nombran el problema y cómo corregirlo (título vacío, más de 200 caracteres, título ambiguo).
- [ ] El texto escrito se conserva tras un error (FR5.2).
- [ ] El botón de generar no cambia el contexto por sí solo: la acción requiere pulsarlo (sin envío automático).
- [ ] La navegación y la ubicación de los controles son iguales en todos los estados de S2.

## Robusto

- [ ] Se usan elementos nativos (botones, campos) siempre que es posible; ARIA solo donde no basta.
- [ ] Carga y copiado se anuncian con regiones de estado (`aria-live="polite"`); los errores del servicio y del acceso, con `role="alert"`.
- [ ] Las pestañas usan los roles `tablist`, `tab` y `tabpanel`.
- [ ] El mensaje de error de un campo se asocia con `aria-describedby`.
- [ ] Hay un solo `h1` por pantalla y las regiones `header` y `main` están presentes.

## Pruebas de accesibilidad previstas

- [ ] Análisis automático con una herramienta como axe o Lighthouse, en los dos temas.
- [ ] Recorrido completo solo con teclado, en escritorio y en móvil con teclado externo.
- [ ] Prueba con un lector de pantalla (NVDA en Windows o VoiceOver).
- [ ] Zoom al 200 % sin pérdida de contenido ni de funciones.

## Assumptions & Open Questions

- Abierto: qué lector de pantalla y qué navegadores se usan para la prueba manual.
- Abierto: cómo se registran los resultados de esta lista en el CI, dado que la cobertura mínima de pruebas ya está fijada en `team-practices.md`.
