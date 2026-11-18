# Logical Components — u3-story-generator

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

Vista por componentes de dónde se aplican los patrones de diseño no funcional. u3 es código dentro de la función de generación (u1); no se despliega por separado ni agrega infraestructura propia.

## Inventario lógico

| Componente lógico | Qué es | Patrones que se aplican | Dominio de falla |
|-------------------|--------|------------------------|------------------|
| Validador de entrada | Recorta, normaliza y valida título y contexto; decide si se pide contexto | Orden de comprobaciones baratas primero; sin llamada al modelo en un rechazo (NFR1.3, NFR4.4) | Una solicitud: devuelve un error de validación |
| Armador de la petición | Junta las instrucciones fijas con el contenido del analista | Delimitadores con neutralización; instrucciones aparte (NFR4.3) | Una solicitud |
| Intérprete de la respuesta | Valida tamaño, JSON, campos, criterios e idioma | Etapas de rechazo; sin texto parcial (NFR1.6, NFR4.5) | Una solicitud: INVALID_MODEL_RESPONSE |
| Armador del Markdown | Escapa, y arma el encabezado, la historia, la lista y el bloque de código con el Gherkin | Escape fuera del bloque; cerco largo dentro (NFR4.6) | Sin estado |
| Manejador de errores | Convierte un fallo del modelo o interno en un error de contrato | Tabla de errores de u1; sin detalle interno (NFR1.7, NFR1.8) | Una solicitud |
| Aporte al registro | Código de resultado y duración propia | Solo esos dos datos, sin contenido (NFR4.2) | Si falla, la solicitud sigue |
| Acceso al modelo (u2) | La llamada a Bedrock | Fuera de u3; ver su diseño | Externo a u3 |

## Radio de impacto

- Un fallo de u3 afecta solo a la solicitud en curso.
- u3 no tiene estado ni almacenamiento: ningún fallo deja datos corruptos (NFR4.1, NFR3.1).
- La pantalla y la infraestructura de u1 y u6 no se ven afectadas por un error de u3 más allá de su respuesta de error.

## Recursos compartidos

- Las instrucciones (configuración) y las expresiones regulares compiladas son de solo lectura y se comparten entre solicitudes sin riesgo (NFR3.1).
- El tope de ejecuciones y el límite de tasa son de u1 y u6 (NFR3.2); el uso por persona es de u4 (NFR3.3).

## Puente con Infrastructure Design

u3 no necesita recursos nuevos. Infrastructure Design debe: no agregar permisos para u3 (no habla con AWS), mantener las instrucciones como variable de configuración de texto sin credenciales (NFR5.2), y reflejar la lista cerrada de códigos de resultado y el campo de duración propia en los registros del servicio.

## Assumptions & Open Questions

- Abierto: los nombres definitivos de los módulos se fijan en Code Generation.
