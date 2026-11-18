# Security Requirements — u2-model-gateway

Documentos de entrada: `functional-spec.md`, `rules.md`, `requirements.md`, `contract-summary.md` y `technology-stack.md`. No hubo preguntas en esta etapa: los valores salen de decisiones ya confirmadas en `requirements.md`, en `u1-walking-skeleton` (verificado de punta a punta) y en las reglas de esta unidad.

u2 es una biblioteca dentro del servicio: no tiene red propia ni autenticación de personas. Su superficie de seguridad es lo que llama a Amazon Bedrock, lo que registra y lo que escribe el comando de evaluación.

## Requisitos

| ID | Requisito | Criterio de prueba | Fuente |
|----|-----------|--------------------|--------|
| NFR4.1 | El acceso al modelo no guarda títulos, historias ni respuestas del modelo: la respuesta pasa en memoria y se devuelve. Solo el comando de evaluación escribe un archivo, con títulos de ejemplo inventados | Una prueba comprueba que el acceso no escribe archivos ni estado compartido; otra, que el comando de evaluación solo escribe `docs/evaluacion-modelos.md` | `requirements.md` NFR4; `rules.md` BR2.9 |
| NFR4.2 | Los registros del acceso al modelo contienen solo el tipo de error, el motivo de la lista cerrada, el identificador del modelo y la duración; nunca la petición, el texto de la respuesta, el título ni el detalle de AWS (ARN, identificadores de cuenta) | Una prueba comprueba que, tras un fallo con un texto de AWS que lleva un ARN, ningún registro ni mensaje contiene ese texto | `requirements.md` NFR4; `rules.md` BR2.4 |
| NFR4.3 | El archivo de evaluación y el comando de evaluación solo usan los 5 títulos de ejemplo inventados y aprobados por la persona; no contienen datos reales de personas ni de la empresa | La lista de títulos aprobada queda escrita en un archivo de títulos que la persona edita y aprueba antes de correr; el comando se niega a correr si el archivo no tiene exactamente 5 títulos o no tiene la marca de aprobación; una prueba lo comprueba | `rules.md` BR2.9 |
| NFR5.1 | Ninguna credencial, clave ni identificador de cuenta aparece en el código ni en los archivos versionados; el acceso usa la cadena de credenciales estándar de AWS (rol de la función en AWS, perfil local de quien ejecuta) | Una búsqueda automática en el repositorio no encuentra patrones de claves de AWS; las pruebas no contienen credenciales | `requirements.md` NFR5; `construction.md` (Security) |
| NFR5.2 | El permiso de ejecución del servicio permite invocar solo los modelos configurados, sin comodines sobre todos los modelos | Lo verifica `u6-infrastructure` (traspaso: recibe la lista de modelos de `ModelProfile` y revisa que el permiso no use comodines sobre todos los modelos); hay una prueba de que el acceso rechaza un identificador de otro proveedor (BR2.2) | `requirements.md` NFR5; `rules.md` BR2.2 |
| NFR5.3 | Un identificador de modelo no soportado se rechaza al armar el acceso, antes de cualquier llamada a AWS, para que una variable de entorno mal escrita no llame a un modelo inesperado | Una prueba da un identificador de otro proveedor y comprueba que no hay ninguna llamada a AWS y que el error nombra el valor | `rules.md` BR2.2 |

## Consideraciones de amenazas

| Amenaza | Cómo la cubren los requisitos |
|---------|-------------------------------|
| Fuga de contenido por los registros de errores | NFR4.2 |
| Fuga de datos de la cuenta de AWS en un mensaje o en el archivo de evaluación | NFR4.2 y NFR4.3 (el motivo es de lista cerrada) |
| Credenciales en el código o en el repositorio | NFR5.1 |
| Un modelo no previsto con permisos amplios | NFR5.2 y NFR5.3 |

## Assumptions & Open Questions

- Supuesto: el modo de ejecución local de la evaluación usa las credenciales del perfil de AWS de quien lo ejecuta, como ya hace el comando de u1.
- Abierto: los permisos finales del servicio sobre los modelos de Titan y de Claude los define `u6-infrastructure`.
