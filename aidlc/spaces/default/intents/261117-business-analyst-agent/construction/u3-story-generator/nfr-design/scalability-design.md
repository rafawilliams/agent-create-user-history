# Scalability Design — u3-story-generator

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

## Sin estado (NFR3.1)

u3 es lógica pura sin estado: ninguna variable de módulo cambia durante una solicitud. Los valores compartidos (las expresiones regulares compiladas y la plantilla de instrucciones) son de solo lectura. Cada solicitud usa solo sus propias variables, por lo que 5 solicitudes simultáneas no se afectan.

Una prueba lanza 5 solicitudes en paralelo con modelos simulados que devuelven historias distintas y comprueba que cada resultado corresponde a su título y a su `requestId`.

## Capacidad y límites (NFR3.2, NFR3.3)

- **Tope de 5 ejecuciones y límite de tasa:** los imponen la infraestructura de u1 y u6 (ver sus diseños); u3 no agrega contadores, colas ni límites.
- **Uso por persona y por día:** lo mide u4-access-control cuando exista identidad; u3 no cuenta solicitudes por persona. Es la medición por persona de NFR3.3, diferida a u4; la desviación del límite de 20 por día (NFR3.2 de u1) está registrada en el diseño de u1.

## Assumptions & Open Questions

- Supuesto: el uso es ocasional de hasta 5 personas; no se diseña escalado adicional.
