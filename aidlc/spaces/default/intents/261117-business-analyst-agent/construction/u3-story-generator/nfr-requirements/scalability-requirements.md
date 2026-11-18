# Scalability Requirements — u3-story-generator

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR3.1 | u3 no guarda estado entre solicitudes ni usa variables compartidas modificables, de modo que 5 solicitudes simultáneas no se afectan entre sí | Una prueba lanza 5 solicitudes en paralelo con modelos simulados y comprueba que cada una devuelve su propio `requestId` y su propio Markdown, sin mezclarse | `requirements.md` NFR3 |
| NFR3.2 | La capacidad concurrente (tope de 5 ejecuciones y límite de tasa) la imponen el servicio y la infraestructura de u1 y u6; u3 no agrega límites propios | La traza de NFR3 de u1 y u6 cubre el tope; en u3 no hay contadores ni colas | `requirements.md` NFR3; diseño de u1 |
| NFR3.3 | El uso por persona y por día lo mide u4-access-control cuando exista identidad; u3 no cuenta solicitudes por persona | No aplica a u3; queda diferido a u4 (desviación registrada en el diseño de u1) | `requirements.md` NFR3 |

## Assumptions & Open Questions

- Supuesto: el uso del MVP es ocasional de hasta 5 personas; no se prevé crecimiento.
