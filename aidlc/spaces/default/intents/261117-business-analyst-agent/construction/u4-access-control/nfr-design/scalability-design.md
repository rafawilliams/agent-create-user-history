# Scalability Design — u4-access-control

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

## Sin estado salvo la copia de claves (NFR3.1)

La verificación no guarda nada por solicitud. La única memoria compartida es la copia de las claves públicas por instancia. Su actualización es atómica: se construye el conjunto nuevo completo y se reemplaza la referencia de una vez, de modo que una verificación en curso nunca ve un conjunto a medio escribir. Las lecturas no se bloquean.

## Renovación segura entre hilos (NFR3.2)

Un solo cerrojo de intento único protege la renovación: quien lo toma descarga; quien no lo toma no espera: si la copia actual tiene la clave y es vigente la usa; si no, falla cerrado de inmediato con `keys_unavailable`. El instante del último intento (exitoso o no) se guarda con la copia para aplicar el límite de uno por minuto.

## Cuentas acotadas (NFR3.3)

La lista de correos permitidos es de hasta 50 entradas; se lee del entorno y se normaliza en cada solicitud (50 comparaciones de texto, coste despreciable). Más de 50, o una entrada que no parece un correo, es un error de configuración al iniciar. Más personas requieren gestionar las cuentas en el grupo de usuarios o con un almacén, lo que se rediseñaría después del MVP.

## Capacidad y uso por persona (NFR3.4)

El tope de 5 ejecuciones y el límite de tasa son de u1 y u6; u4 no agrega límites. Con identidad por persona ya disponible (`accountId`), el límite diario de 20 (NFR3.2 de u1) podría apoyarse en ella, pero necesita un contador con estado; queda fuera del MVP y se decide después.

## Assumptions & Open Questions

- Supuesto: el uso es ocasional de hasta 5 personas.
