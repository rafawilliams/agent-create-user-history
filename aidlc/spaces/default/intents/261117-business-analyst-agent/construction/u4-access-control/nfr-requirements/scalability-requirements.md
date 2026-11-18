# Scalability Requirements — u4-access-control

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa.

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR3.1 | La verificación no guarda estado por solicitud y la copia de claves públicas es la única memoria compartida; 5 verificaciones simultáneas devuelven cada una su propio resultado | Una prueba lanza 5 verificaciones en paralelo con tokens distintos (válidos e inválidos) y comprueba el resultado de cada una, y que la copia de claves no se corrompe con la renovación simultánea | `requirements.md` NFR3 |
| NFR3.2 | La renovación de la copia de claves es segura entre hilos: solo una renovación a la vez y como máximo una por minuto (NFR1.3) | Una prueba con 20 verificaciones simultáneas de un `kid` desconocido comprueba una sola renovación | `rules.md` BR4.7 |
| NFR3.3 | El número de cuentas permitidas está acotado (unas 5; hasta 50 como máximo del diseño) para que la lista en variable de entorno siga siendo manejable; más personas requieren rediseñar la gestión de cuentas | Una prueba carga 50 correos y comprueba la comparación; una lista de más de 50 se rechaza al iniciar con un error de configuración | `requirements.md` NFR3 |
| NFR3.4 | El tope de 5 ejecuciones simultáneas y el límite de tasa los imponen u1 y u6; u4 no agrega límites propios y el uso por persona y por día (límite de 20) lo habilita u4 al dar identidad, pero su aplicación queda para una versión posterior | No aplica a u4 | `requirements.md` NFR3; desviación registrada en el diseño de u1 |

## Assumptions & Open Questions

- Supuesto: el uso es ocasional de hasta 5 personas.
- Abierto: el límite de 20 solicitudes por persona por día (NFR3 de u1) puede apoyarse ahora en el identificador de cuenta de la sesión, pero requeriría un contador con estado; se decide después del MVP.
