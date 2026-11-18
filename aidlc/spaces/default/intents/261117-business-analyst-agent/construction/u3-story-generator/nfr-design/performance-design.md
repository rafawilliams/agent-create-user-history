# Performance Design — u3-story-generator

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

## Presupuesto de tiempo (NFR1.1, NFR1.4)

u3 no fija plazos propios: usa el plazo absoluto de 55 segundos que u1 abre al recibir la solicitud. La llamada al modelo recibe el menor entre el corte del modelo (50 s) y el tiempo restante. u3 pasa ese tiempo restante a u2 y no agrega esperas, reintentos ni colas.

## Orden de las comprobaciones (NFR1.3)

Las comprobaciones baratas van antes de llamar al modelo, en este orden, y la primera que falla corta la solicitud sin llamar al modelo:

1. Título vacío o demasiado largo (BR3.1).
2. Contexto demasiado largo (BR3.3).
3. Título que pide contexto sin contexto (BR3.2).
4. Armado de la petición y llamada al modelo.

Todo el trabajo antes de la llamada es en memoria y de coste constante (cadenas de hasta 200 y 500 caracteres).

## Trabajo propio acotado (NFR1.2, NFR1.5)

- La respuesta del modelo se lee de una cadena de como máximo 16 kilobytes medidos en bytes UTF-8 (NFR4.5; el peor caso válido ocupa unos 8,6 kilobytes); mayor tamaño es inválida sin analizarla.
- El análisis del JSON, la validación de campos (hasta 300 caracteres, de 2 a 3 criterios), la heurística de idioma y el armado del Markdown son lineales en el tamaño y trabajan una sola pasada.
- Los tres presupuestos de 50 milisegundos (NFR1.2, NFR1.3 y NFR1.5) se miden en pruebas con un reloj monótono, con 20 repeticiones tras una de calentamiento; se informa la mediana y el máximo, y una mediana mayor de 50 ms o un máximo mayor de 200 ms es un fallo de la prueba. Se miden en la misma máquina de desarrollo y en CI; el arranque en frío de la función no entra en estas pruebas.

## Reuso

No hay caché: el contenido no se guarda (NFR4.1) y cada título es distinto. Las expresiones regulares de escape y de validación se compilan una sola vez al cargar el módulo.

## Medición (NFR1.10)

El registro de duración que ya emite u1 incluye, aparte de la duración de la llamada al modelo, la duración de la lógica de u3. u3 la calcula con el reloj monótono alrededor de su propio trabajo y la entrega al servicio; el servicio la incluye en el campo de duración permitido (u1 acepta una lista cerrada de campos; se agrega `u3DurationMs` como un campo nuevo de la lista cerrada, sin contenido).

## Assumptions & Open Questions

- Supuesto: el tiempo del modelo domina; los 50 ms de u3 detectan una regresión grave, no una meta de rendimiento.
- Decidido: el campo de duración propia se llama `u3DurationMs` (ver `observability-design.md`).
