# Security Design — u3-story-generator

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

## Sin persistencia ni contenido en registros (NFR4.1, NFR4.2)

u3 no escribe archivos ni guarda estado: recibe valores, devuelve valores. Su aporte al registro es solo el código de resultado y la duración; las cadenas del analista (título, contexto), la respuesta del modelo y el Markdown nunca se pasan al registrador. Una prueba captura todos los registros de un caso feliz y de cada error y busca el título y el contexto de prueba.

## Entrada como dato (NFR4.3, NFR4.4)

- **Límites en el borde:** el título se recorta (espacios Unicode) y se mide en puntos de código: de 1 a 200; el contexto, hasta 500. La entrada completa de la solicitud no supera un tope de bytes (4 kilobytes) que u1 impone al cuerpo HTTP; u3 no lo duplica.
- **Normalización:** los saltos de línea y los caracteres de control del título y del contexto pasan a espacios antes de usarse.
- **Orden fijo de tratamiento de la entrada:** (1) recortar, (2) normalizar saltos de línea y caracteres de control a espacios, (3) validar longitudes, (4) neutralizar las marcas de apertura y cierre. La neutralización va después de la normalización para que un salto de línea no parta una marca, y se repite hasta que el contenido ya no contiene ninguna marca (un reemplazo no puede reconstruir otra marca anidada porque el texto de reemplazo no contiene el carácter con que empiezan las marcas).
- **Petición con delimitadores:** las instrucciones fijas (de configuración) van primero y el contenido del analista va después dentro de marcas fijas de apertura y cierre. Las marcas usan un carácter que el contenido normalizado reemplaza siempre, de modo que el contenido no puede cerrar el bloque de datos. Las instrucciones dicen que lo que hay entre las marcas es solo un dato.
- **Tope de bytes del cuerpo:** u1 limita el cuerpo HTTP; este diseño lo da por supuesto y u3 verifica además sus propios límites de caracteres, de modo que no depende de ese tope (supuesto sin respaldo en un artefacto compartido; se confirma en u6).
- **El formato no depende del modelo:** el rol, las palabras clave del Gherkin, la línea de idioma y la estructura las fija el servicio (BR3.5, BR3.9); un título que pida otro formato no puede cambiarlo.

## La respuesta del modelo es no confiable (NFR4.5)

Orden: (1) tamaño, (2) JSON con cerco opcional, (3) campos presentes y de hasta 300 caracteres, normalizados a una línea (los saltos pasan a espacios; no se rechaza por tener saltos), (4) de 2 a 3 criterios, (5) heurística de idioma sobre el texto normalizado y sin escapar, (6) escape al armar el Markdown (BR3.8).

1. Se rechaza una respuesta de más de 16 kilobytes medidos en bytes UTF-8 (el peor caso válido son 14 campos de 300 caracteres con acentos, que ocupan unos 8,6 kilobytes; el tope duplica ese margen para JSON con espacios).
2. Se acepta solo un JSON (con un cerco de código opcional), con los campos esperados y los límites de BR3.6; todo lo demás es INVALID_MODEL_RESPONSE.
3. Los campos se normalizan a una línea y se escapan al armar el Markdown fuera del bloque de código (BR3.8).
4. La heurística de idioma de BR3.7 rechaza una respuesta completa en otro idioma.

## Escape y bloque de código (NFR4.6)

- **Fuera del bloque de código:** se escapan los caracteres de Markdown y de HTML y los inicios de lista de BR3.8 (título del encabezado, historia, nombres de criterios en la lista).
- **Dentro del bloque de código:** el Gherkin queda tal cual; para que el contenido no cierre el bloque, el cerco usa más acentos graves que la secuencia más larga contenida (mínimo tres). Un Gherkin con tres acentos graves se cierra con cuatro o más.
- Una prueba con `<script>`, un enlace Markdown, "Exportar *todo* a [CSV]" y una secuencia de acentos graves comprueba cada caso.

## Secretos (NFR5.1, NFR5.2)

u3 no usa credenciales ni habla con AWS. Las instrucciones viven en una variable de configuración de texto (sin credenciales) y no se mezclan con valores sensibles; el servicio no las registra.

## Superficie de ataque y mitigaciones

| Amenaza | Mitigación |
|---------|-----------|
| Inyección de instrucciones por el título o el contexto | Delimitadores con neutralización, formato fijado por el servicio |
| HTML o enlaces en la respuesta del modelo | Escape fuera del bloque de código y rechazo de respuestas mayores de 16 kilobytes |
| Cierre del bloque de código desde dentro | Cerco más largo que cualquier secuencia contenida |
| Fuga de contenido en los registros | Solo código y duración, con prueba de captura de registros |
| Entrada muy grande | Límites de caracteres y tope de bytes del cuerpo (u1) |

## Assumptions & Open Questions

- Supuesto: la vista previa de u5-web-app escapa el HTML otra vez al mostrar el Markdown; u3 escapa en origen.
- Abierto: las marcas exactas de apertura y cierre del contenido se fijan en Code Generation.
